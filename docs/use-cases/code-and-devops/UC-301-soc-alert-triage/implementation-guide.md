---
layout: use-case-detail
title: "Implementation Guide — Autonomous SOC Alert Triage and Incident Response with Agentic AI"
uc_id: "UC-301"
uc_title: "Autonomous Security Operations Center (SOC) Alert Triage and Incident Response with Agentic AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Code & DevOps"
category_icon: "terminal"
industry: "Cross-Industry (Financial Services, Technology, Healthcare, Retail, Energy, Government)"
complexity: "High"
status: "detailed"
slug: "UC-301-soc-alert-triage"
permalink: /use-cases/UC-301-soc-alert-triage/implementation-guide/
---

## Build Goal

Build a multi-agent SOC triage system that ingests alerts from the existing SIEM and EDR stack, autonomously classifies and investigates each alert, and either closes it with a documented rationale or escalates it to a human analyst with a complete evidence summary. The first production release covers Tier-1 triage automation and investigation for the top 10 alert types by volume, operating in shadow mode before graduating to autonomous closure and pre-approved containment actions. Full Tier-2 investigation automation, proactive threat hunting, and cross-organizational threat correlation remain outside the first release.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.12+ on containerized infrastructure (Kubernetes or serverless) | Python dominates the security tooling ecosystem. Most SIEM and EDR SDKs (Splunk SDK, Microsoft Sentinel SDK, CrowdStrike FalconPy) are Python-first. Containerized deployment supports both cloud and on-premises requirements. |
| **Model access** | Azure OpenAI (GPT-4o) or Anthropic Claude via API | Frontier reasoning capability required for multi-step investigation across heterogeneous security data. Azure OpenAI provides data residency options for regulated industries. Microsoft Security Copilot uses GPT-4 with security-specific grounding. [S5] |
| **Orchestration runtime** | LangGraph for multi-agent orchestration with tool-calling | Investigation workflows branch, loop, and escalate — not linear pipelines. LangGraph models each agent as a graph node with typed state transitions. Torq Socrates uses a similar multi-agent pattern with a central orchestrator dispatching to specialized agents. [S7] |
| **Core connectors** | SIEM API (Splunk REST / Sentinel KQL), EDR API (CrowdStrike FalconPy / Defender API), threat intel APIs (VirusTotal, MISP), identity API (Microsoft Graph / Okta) | Read-only access to the existing security stack. No rip-and-replace. Each connector is a tool the investigation agent can call. Prophet Security identifies five integration layers that the agent must span. [S14] |
| **Evaluation / tracing** | LangSmith for agent tracing and verdict quality tracking; OpenTelemetry for infrastructure observability | Every investigation must produce an auditable trace. LangSmith captures prompt/completion pairs, tool calls, and state transitions. Verdict accuracy is the primary quality metric. |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 — Foundation (weeks 1–4) | Alert ingestion pipeline operational. Top 10 alert types identified and baselined. Connectors to SIEM, EDR, and threat intel APIs working. | Alert ingestion webhook, SIEM/EDR connector adapters, alert schema normalization, historical alert analysis identifying top-10 types by volume and false-positive rate. |
| 2 — Shadow triage (weeks 5–10) | Triage agent classifies alerts in shadow mode alongside human analysts. Investigation agent queries evidence sources and produces verdicts. No autonomous actions taken. | Triage agent with classification model, investigation agent with tool-calling, enrichment agent with threat intel and MITRE mapping, shadow-mode comparison dashboard tracking AI vs. analyst agreement rate. |
| 3 — Autonomous triage (weeks 11–16) | Triage agent auto-closes confirmed false positives. Investigation agent produces escalation summaries for true positives. Response agent executes pre-approved low-risk containment. | Confidence threshold calibration, auto-close workflow with documented rationale, escalation summary format validated by analysts, response agent with bounded containment actions, feedback loop for analyst corrections. |
| 4 — Expansion (weeks 17–24) | Coverage expanded beyond top-10 alert types. Containment scope broadened based on pilot data. Detection tuning signals fed back to detection engineering. | Additional alert type coverage, expanded containment policy, detection tuning pipeline, compliance audit trail review, production runbook and on-call procedures. |

## Core Contracts

### State And Output Schemas

The alert verdict is the central contract. Every investigation produces a structured verdict that the confidence gate, response agent, and case management system all consume.

```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class Verdict(str, Enum):
    TRUE_POSITIVE = "true_positive"
    FALSE_POSITIVE = "false_positive"
    INCONCLUSIVE = "inconclusive"

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertVerdict(BaseModel):
    alert_id: str
    verdict: Verdict
    confidence: float = Field(ge=0.0, le=1.0)
    severity: Severity
    mitre_techniques: list[str] = Field(
        description="MITRE ATT&CK technique IDs, e.g. T1566.001, T1078"
    )
    evidence_summary: str = Field(
        description="Structured summary of evidence gathered during investigation"
    )
    recommended_actions: list[str]
    escalation_reason: str | None = Field(
        default=None,
        description="Set when verdict is inconclusive or severity is critical"
    )
    investigated_at: datetime
    investigation_duration_seconds: float
```

### Tool Interface Pattern

Each security tool is exposed to the investigation agent as a typed function with scoped permissions. Tools are read-only by default; the response agent has a separate, policy-gated tool set for containment actions.

```python
from langchain_core.tools import tool

@tool
def query_siem_logs(
    query: str,
    time_range_hours: int = 24,
    max_results: int = 100,
) -> list[dict]:
    """Search SIEM logs using the platform's query language.

    Use SPL for Splunk, KQL for Sentinel, EQL for Elastic.
    Returns matching events with timestamps, source IPs,
    affected users, and event types. Read-only access only.
    """
    return siem_connector.search(query, time_range_hours, max_results)

@tool
def enrich_ioc(indicator: str, indicator_type: str) -> dict:
    """Enrich an indicator of compromise against threat intel feeds.

    Supported types: ip, domain, file_hash, url, email.
    Returns reputation score, known campaigns, first/last seen.
    """
    return threat_intel_connector.enrich(indicator, indicator_type)
```

## Orchestration Outline

The orchestration follows a triage, investigate, decide, act pattern. The triage agent runs first on every alert. Alerts that pass the false-positive filter are handed to the investigation agent, which calls tools iteratively until it has enough evidence to produce a verdict. The confidence gate then routes to either the response agent or human escalation.

```python
from langgraph.graph import StateGraph, END

def build_soc_triage_graph():
    graph = StateGraph(SOCTriageState)

    graph.add_node("triage", triage_agent)
    graph.add_node("investigate", investigation_agent)
    graph.add_node("enrich", enrichment_agent)
    graph.add_node("respond", response_agent)
    graph.add_node("escalate", escalation_handler)
    graph.add_node("close", auto_close_handler)

    graph.set_entry_point("triage")
    graph.add_conditional_edges("triage", route_after_triage, {
        "investigate": "investigate",
        "auto_close": "close",
    })
    graph.add_edge("investigate", "enrich")
    graph.add_conditional_edges("enrich", route_after_investigation, {
        "respond": "respond",
        "escalate": "escalate",
        "close": "close",
    })
    graph.add_edge("respond", END)
    graph.add_edge("escalate", END)
    graph.add_edge("close", END)

    return graph.compile()
```

## Prompt And Guardrail Pattern

The investigation agent system prompt enforces structured reasoning, evidence citation, and escalation rules. The prompt constrains the model to produce verdicts grounded in evidence rather than speculation.

```text
You are a SOC investigation agent. Your job is to determine whether
a security alert is a true positive, false positive, or inconclusive.

RULES:
- Base your verdict ONLY on evidence you gather from available tools.
- Cite specific log entries, IOC matches, or telemetry findings.
- If you cannot gather sufficient evidence after exhausting available
  tools, return verdict "inconclusive" — never guess.
- Map observed techniques to MITRE ATT&CK IDs where applicable.
- For true positives, recommend specific containment actions.
- NEVER execute containment actions yourself. Report findings only.
- Flag if the alert involves a critical asset or privileged account.

OUTPUT FORMAT:
Return a JSON object matching the AlertVerdict schema with all fields
populated. The evidence_summary must reference specific log entries
or IOC lookups, not general statements.
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| SIEM alert ingestion | Webhook receiver that normalizes alerts from Splunk (HEC format), Sentinel (Logic App), or Elastic (Watcher) into a common alert schema. | Each SIEM has a different alert payload format. Build a thin normalization layer per SIEM, not a universal parser. Start with the primary SIEM only. Palo Alto XSIAM supports 1,000+ integrations natively; a custom build covers the top 3–4 SIEMs. [S2] |
| EDR telemetry queries | Read-only connector using the EDR vendor's SDK (FalconPy for CrowdStrike, Defender API for Microsoft, SentinelOne API). Returns process trees, command-line arguments, and file activity for entities in the alert. | Scope API credentials to read-only. Use service accounts with minimum required permissions. Rate-limit queries to avoid throttling during alert storms. [S3] |
| Threat intel enrichment | Aggregation layer that fans out IOC lookups to VirusTotal, MISP, and commercial threat intel feeds. Returns the highest-confidence match with campaign attribution where available. | Cache enrichment results for 1 hour to reduce API costs and latency. Swimlane Hero AI uses dedicated Threat Intelligence and MITRE ATT&CK agents for this step. [S9] |
| Containment via SOAR or direct API | Response agent calls SOAR playbooks (Cortex XSOAR, Splunk SOAR) or direct vendor APIs to execute containment. Each action type has a policy gate checking asset criticality and approval requirements. | Containment is the highest-risk integration. Gate every action behind a policy check. Log the full decision chain. Make every action reversible. Start with only 2–3 containment types: block IP, isolate endpoint, suspend credential. [S7] |
| Case management writeback | API connector that creates incident records in ServiceNow or Jira with the verdict, evidence summary, and audit trail. Updates case status as the investigation progresses. | Use the ticketing system's structured fields (severity, category, affected CI) rather than dumping text into a description field. This enables compliance reporting downstream. [S14] |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Triage accuracy | Compare AI verdicts against expert analyst verdicts on a labeled dataset of 500+ historical alerts. Measure precision, recall, and F1 score for true-positive identification. | F1 ≥ 0.95 for true-positive detection. False-negative rate < 2%. CrowdStrike validated Charlotte AI at >98% accuracy against Falcon Complete expert decisions. [S3] |
| Investigation quality | Blind review: have Tier-2 analysts score AI investigation summaries on a 1–5 scale for completeness, accuracy, and actionability. Sample 50+ investigations per week during pilot. | Average analyst rating ≥ 4.0/5.0. Microsoft Security Copilot measured 7% accuracy improvement and 68% reduction in incident reopening. [S5] |
| False positive suppression | Measure the percentage reduction in alerts reaching human analysts before and after AI deployment. Track analyst-overridden auto-closures as a signal of false negative leakage. | ≥ 80% reduction in alerts requiring human review. Override rate < 3%. XSIAM customers report 85% alert volume reduction. [S1] |
| Containment safety | Track all automated containment actions. Measure rollback rate (actions reversed because they caused unintended disruption). | Rollback rate < 1%. Zero containment actions on critical assets without human approval during pilot. |
| End-to-end latency | Measure time from alert ingestion to verdict (MTTD) and from verdict to containment action (MTTR). | MTTD < 5 minutes. MTTR < 15 minutes for automated responses. Google SecOps Triage Agent averages 60-second investigations. [S6] |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start in shadow mode (Phase 2): AI produces verdicts but takes no action. Compare against analyst decisions for 4–6 weeks. Graduate to autonomous triage for alert types where accuracy exceeds 95% agreement. Add containment actions incrementally, starting with lowest-risk types. Torq reports 90 days from deployment to SOC autonomy for new customers. [S7] |
| **Fallback path** | If the AI is unavailable or producing degraded results, alerts route directly to the human triage queue as they did before deployment. The SIEM alerting pipeline is unchanged — the AI is an additional consumer, not a replacement for the existing alert path. Disable autonomous closure and containment with a single feature toggle. |
| **Observability** | Trace every investigation end-to-end: alert ingestion timestamp, each tool call and response, verdict, confidence score, response action, and total duration. Alert on: verdict latency exceeding 10 minutes, confidence scores trending downward, false-negative rate exceeding 2%, containment rollback rate exceeding 1%. Dashboard showing daily triage volume, auto-close rate, escalation rate, and analyst override rate. |
| **Operations ownership** | SOC engineering team owns the AI pipeline in production. SOC analysts own the feedback loop and verdict quality review. Detection engineering owns the tuning signals pipeline. Security architecture owns the containment policy and access controls. Quarterly review with compliance for audit trail adequacy. |
