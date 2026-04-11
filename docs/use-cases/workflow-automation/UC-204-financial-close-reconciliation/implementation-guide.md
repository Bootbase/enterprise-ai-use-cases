---
layout: use-case-detail
title: "Implementation Guide — Autonomous Financial Close and Account Reconciliation with Agentic AI"
uc_id: "UC-204"
uc_title: "Autonomous Financial Close and Account Reconciliation with Agentic AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Workflow Automation"
category_icon: "settings"
industry: "Cross-Industry (Financial Services, Manufacturing, Technology, Retail, Professional Services, Healthcare)"
complexity: "High"
status: "detailed"
slug: "UC-204-financial-close-reconciliation"
permalink: /use-cases/UC-204-financial-close-reconciliation/implementation-guide/
---

## Build Goal

The delivery team builds an AI-augmented financial close system that auto-reconciles accounts, prepares standard journal entries, flags material variances with draft commentary, and routes exceptions to human reviewers — all within a SOX-compliant audit trail. The first production release covers account reconciliation (auto-matching and auto-certification), recurring journal entry preparation, and basic variance flagging for a single legal entity. Intercompany elimination, consolidation, multi-entity rollout, and statutory reporting remain outside the first release. The system integrates with the organization's ERP as the general ledger system of record and runs within a close management platform that owns the task checklist and approval workflow. [S1][S2][S4]

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Close management platform (FloQast, Trintech Cadency, or SAP AFC) hosting agent logic as extensions or workflows | Purpose-built platforms provide the close checklist, dependency graph, approval routing, and audit trail out of the box. FloQast serves 3,500+ customers on this model. [S1][S8] |
| **Model access** | Amazon Bedrock (Claude 3.5 Sonnet) for commentary and exception triage; platform-native ML models for transaction matching | FloQast's production stack uses Claude on Bedrock. Transaction matching requires high-throughput, low-latency inference that ML classifiers handle more efficiently than LLMs. [S1] |
| **Orchestration runtime** | Platform-native close task scheduler with dependency enforcement | The financial close is a sequential, gated process. Close platforms encode task dependencies and approval chains natively. SAP AFC exposes a Scheduling Provider Interface for custom task integration. [S5][S10] |
| **Core connectors** | ERP REST API (SAP OData, Oracle REST, NetSuite SuiteQL) + bank feed ingestion (BAI2/MT940 or banking API) | Direct ERP connectivity eliminates CSV intermediaries. Automated bank feeds remove the highest-friction manual step in reconciliation. [S5][S10] |
| **Evaluation / tracing** | Platform audit trail + OpenTelemetry for agent-level tracing; Bedrock Guardrails for content safety on LLM outputs | Audit trail is a SOX requirement, not optional. Bedrock Guardrails filter LLM outputs before they reach working papers. FloQast's architecture uses Bedrock Guardrails for content safety. [S1][S7] |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | Data foundation and ERP integration | ERP connector pulling GL trial balance, sub-ledger detail, and bank statements into the close platform. Data validation layer confirming extract completeness (row counts, control totals, period markers). Account master enriched with risk classification and materiality thresholds. |
| 2 | Reconciliation automation | ML matching model trained on 6–12 months of historical reconciliation data. Auto-match engine processing bank reconciliations and high-volume sub-ledger accounts. Auto-certification rules for low-risk accounts. Exception queue with supporting detail for human reviewers. |
| 3 | Journal entry and variance analysis | Journal entry agent preparing recurring entries (accruals, deferrals, allocations) from templates and prior-period patterns. Variance agent comparing actuals to budget/prior period and drafting commentary using Claude. Approval routing for both entry types. |
| 4 | Pilot close and SOX readiness | Full close cycle for one legal entity using the automated system in parallel with the manual process. Audit trail validation with internal audit. Match-rate and exception-rate measurement against release gates. Cutover decision based on pilot results. |

## Core Contracts

### State And Output Schemas

The reconciliation agent operates on a standardized account reconciliation record that tracks the lifecycle from open to certified. This contract ensures every reconciliation carries its supporting evidence and audit metadata regardless of account type.

```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from decimal import Decimal

class ReconciliationStatus(str, Enum):
    OPEN = "open"
    MATCHED = "matched"
    EXCEPTION = "exception"
    CERTIFIED = "certified"

class ReconciliationRecord(BaseModel):
    """Core state object for a single account reconciliation."""
    account_id: str
    period: str                          # e.g. "2026-03"
    gl_balance: Decimal
    supporting_balance: Decimal          # sub-ledger, bank, or IC counterpart
    variance: Decimal
    match_confidence: float = Field(ge=0.0, le=1.0)
    status: ReconciliationStatus
    risk_tier: str                       # "low", "medium", "high"
    auto_certified: bool = False
    exception_reason: str | None = None
    matched_items: list[str] = []        # IDs of matched transaction pairs
    preparer: str | None = None
    approver: str | None = None
    certified_at: datetime | None = None
    audit_trail_ref: str | None = None   # pointer to immutable log entry
```

### Tool Interface Pattern

Agents interact with the ERP and close platform through a constrained tool interface. Each tool has a declared scope and the orchestrator enforces that agents only call tools relevant to their sub-process. The reconciliation agent, for example, can read GL data and write match results but cannot post journal entries.

```python
from anthropic import Anthropic

# Tool definitions constrain what the reconciliation agent can do.
# The close platform enforces these boundaries at the API layer.

reconciliation_tools = [
    {
        "name": "fetch_gl_detail",
        "description": "Retrieve GL line items for an account and period from the ERP.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "period": {"type": "string"},
            },
            "required": ["account_id", "period"],
        },
    },
    {
        "name": "fetch_bank_transactions",
        "description": "Retrieve bank statement lines for matching against GL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bank_account_id": {"type": "string"},
                "date_from": {"type": "string", "format": "date"},
                "date_to": {"type": "string", "format": "date"},
            },
            "required": ["bank_account_id", "date_from", "date_to"],
        },
    },
    {
        "name": "record_match",
        "description": "Record a matched pair of GL and supporting transactions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gl_item_id": {"type": "string"},
                "supporting_item_id": {"type": "string"},
                "confidence": {"type": "number"},
                "match_reason": {"type": "string"},
            },
            "required": ["gl_item_id", "supporting_item_id", "confidence"],
        },
    },
]
```

## Orchestration Outline

The close orchestrator runs the close as a dependency graph. Each close task (reconciliation, journal entry, variance review) is a node with defined predecessors and successors. The orchestrator checks completion status and approval gates before advancing to the next task. Agents within each task follow a retrieve-process-validate-write cycle.

```python
# Simplified close orchestration loop.
# In production, the close platform (FloQast, Trintech, SAP AFC)
# manages this graph natively.

async def run_close_cycle(entity_id: str, period: str):
    # Phase 1: Data extraction and validation
    extracts = await pull_erp_data(entity_id, period)
    validation = validate_extracts(extracts)  # row counts, control totals
    if not validation.passed:
        raise CloseBlockedError(f"Extract validation failed: {validation.errors}")

    # Phase 2: Reconciliation
    accounts = await get_accounts_for_reconciliation(entity_id, period)
    for account in accounts:
        result = await reconciliation_agent.reconcile(account, extracts)
        if result.status == "exception":
            await route_to_human_queue(result)
        elif result.auto_certified:
            await log_certification(result)  # immutable audit trail

    # Phase 3: Journal entries (depends on reconciliation completion)
    await wait_for_gate("reconciliation_complete", entity_id, period)
    entries = await journal_agent.prepare_recurring_entries(entity_id, period)
    await route_entries_for_approval(entries)

    # Phase 4: Variance analysis (depends on journals posted)
    await wait_for_gate("journals_approved", entity_id, period)
    variances = await variance_agent.analyze(entity_id, period)
    await route_commentary_for_review(variances)

    # Phase 5: Trial balance certification
    await wait_for_gate("all_tasks_complete", entity_id, period)
    await request_controller_signoff(entity_id, period)
```

## Prompt And Guardrail Pattern

The variance commentary agent uses a structured system prompt that constrains output to factual, data-grounded explanations. The prompt forces the model to reference specific numbers from the input data and to flag uncertainty rather than fabricate explanations.

```text
You are a financial close assistant generating variance commentary for
management review.

Rules:
- Reference specific dollar amounts and percentages from the provided data.
- Compare the current period to the comparison basis (budget, forecast,
  or prior period) as specified in each request.
- State the likely driver based on the data provided. If the data does not
  clearly explain the variance, say "driver requires investigation" rather
  than guessing.
- Do not invent transactions, customers, or events not present in the data.
- Keep commentary to 2-3 sentences per variance item.
- Use plain business language. No jargon, no hedging phrases.

Output format:
For each flagged variance, return:
  account: <account name and number>
  variance: <amount and percentage>
  commentary: <2-3 sentence explanation>
  confidence: <high / medium / low>
```

The close platform applies Bedrock Guardrails to filter LLM responses before they enter working papers. Guardrails reject outputs that contain speculative claims without data backing, references to entities or transactions not in the input context, or content that could be mistaken for audit opinions. [S1]

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| ERP GL extract | Connector that pulls trial balance, GL detail, and sub-ledger data at period end. Must support incremental pulls for mid-close updates. | SAP: use OData services or AFC Scheduling Provider Interface. Oracle: REST API with pagination. NetSuite: SuiteQL queries. Extract must include control totals for validation. [S5][S10] |
| Bank statement ingestion | Automated feed from banking partner (BAI2, MT940 format) or banking API (Plaid, MX). Parser normalizes statements into the platform's transaction schema. | Bank reconciliation is the highest-volume matching workload. Automated feeds eliminate the manual download-upload cycle that delays close start by 1–2 days. [S2][S4] |
| Journal entry posting | Bidirectional API: agent prepares entries in the close platform, approved entries post back to the ERP GL via API. | ERP must validate account codes, period open/close status, and posting authorization before accepting entries. Reject-and-retry logic handles validation failures without manual intervention. [S4] |
| Audit trail and SOX evidence | Append-only log capturing every agent action (match, certify, prepare entry), human decision (approve, reject, override), and system event (extract, post). | Log must be immutable and queryable by auditors. Each entry needs: timestamp, actor (agent or person), action, affected account, before/after state, and decision rationale. [S7] |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Transaction matching accuracy | Precision and recall against a labeled test set of 3+ months of historical reconciliations. Measure by account type (bank, sub-ledger, intercompany). | Precision ≥ 98%, recall ≥ 95% on bank reconciliations. Precision ≥ 97% on sub-ledger matching. No false auto-certifications on accounts with known exceptions in the test set. |
| Journal entry accuracy | Compare agent-prepared entries against actual posted entries from prior periods. Measure amount accuracy, account code correctness, and period assignment. | ≥ 99% of recurring entry amounts within $1 of actual. Zero entries posted to closed periods or invalid accounts. |
| Variance commentary quality | Controller blind review: score AI-drafted commentary on accuracy (does it cite correct numbers?), completeness (does it identify the likely driver?), and usefulness (would you send this to management?). | ≥ 80% of commentary items rated "acceptable without edit" by controllers. Zero items containing fabricated data points. |
| Exception routing precision | Measure false positive rate (items routed to humans that could have auto-cleared) and false negative rate (items auto-cleared that should have been flagged). | False negative rate < 0.5% (missed exceptions are the critical risk). False positive rate < 10% (too many false positives erode trust and waste reviewer time). |
| Audit trail completeness | Internal audit reviews a sample close cycle and verifies that every action has a log entry with required fields. | 100% of actions logged. Zero gaps in the decision chain from data extract through trial balance certification. |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Run the AI-augmented close in parallel with the manual close for 2–3 periods. Compare results account by account. Start with one legal entity and the highest-volume account types (bank reconciliations, AP/AR sub-ledger). Expand entity coverage after pilot validation. Trintech and HighRadius both recommend phased rollout starting with the reconciliation workload. [S2][S4] |
| **Fallback path** | The manual close process remains fully operational during parallel run. If the AI system fails to complete a task, the close orchestrator flags it and the accountant completes it manually. The close checklist tracks both automated and manual completions. No irreversible state changes occur without human approval. |
| **Observability** | Monitor: close task completion rate and time per task, auto-match rate by account type (trend alerts if rate drops > 5%), exception queue depth and aging, journal entry rejection rate from ERP validation, and audit trail event volume (sudden drops indicate logging failures). Alert the close controller if any task misses its SLA window. |
| **Operations ownership** | Finance operations owns the close process and close platform configuration. IT owns ERP connectors and infrastructure. The AI/ML team owns matching model retraining and LLM prompt maintenance. Internal audit owns control evidence review and SOX attestation. Retraining cadence: matching models refreshed quarterly using the latest 12 months of reconciliation data. |
