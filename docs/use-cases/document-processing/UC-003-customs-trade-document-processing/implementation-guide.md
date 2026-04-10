---
layout: use-case-detail
title: "Implementation Guide — Autonomous Customs Declaration and Trade Document Processing"
uc_id: "UC-003"
uc_title: "Autonomous Customs Declaration and Trade Document Processing"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Document Processing"
category_icon: "file-text"
industry: "Logistics / Global Trade"
complexity: "High"
status: "detailed"
slug: "UC-003-customs-trade-document-processing"
permalink: /use-cases/UC-003-customs-trade-document-processing/implementation-guide/
---

## Build Goal

Build a declaration-drafting service that receives trade documents and shipment context, produces a broker-reviewable customs draft with evidence and confidence, validates it against one country filing interface, and writes the result back into the team’s existing customs platform. The first release should stay narrow: one customs regime, one broker team, repeat import flows, and a bounded set of product families. Broader multi-country coverage comes later through additional filing adapters and tariff packs.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python service with FastAPI on Azure Container Apps or AWS ECS | Python has the cleanest path for OCR, retrieval, and workflow tooling while remaining easy to integrate with broker systems |
| **Model access** | OpenAI Responses API with structured outputs | The workflow needs typed declaration drafts, not prose. Structured outputs reduce downstream parser fragility |
| **Orchestration runtime** | LangGraph | Conditional routing is the core requirement: extract, retrieve, draft, validate, then either file or escalate |
| **Core connectors** | Customs platform adapter, HMRC CDS APIs, tariff dataset adapter, sanctions screening connector | First release should use one fully testable government interface and one official tariff feed |
| **Evaluation / tracing** | LangSmith-style trace store plus warehouse tables for reviewed declarations | Customs teams need replayable traces, override analytics, and per-field accuracy review |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | Controlled intake and reference-data foundation | Document intake, OCR/layout extraction, shipment correlation, tariff snapshot loader, broker override store |
| 2 | Reliable extraction and draft generation | Structured extraction schema, candidate retrieval, declaration draft output, confidence scoring, review queue |
| 3 | Filing-safe country adapter | Country-specific validation, adapter payload builder, push or pull notification handling, writeback into customs platform |
| 4 | Pilot with measurable broker outcomes | Shadow mode, broker override capture, regression dataset, tuned thresholds, controlled auto-stage of routine drafts |

## Core Contracts

### State And Output Schemas

The main contract is a declaration draft, not a raw LLM answer. Every extracted value must carry provenance so a broker can see which document supported it. Keep the contract small. If a field matters for filing, classification, or preference, model it explicitly. If it does not, do not ask the model to invent structure for it.

```python
from pydantic import BaseModel, Field
from typing import Literal
from openai import OpenAI


class EvidenceRef(BaseModel):
    document_id: str
    page: int
    snippet: str


class HSRecommendation(BaseModel):
    jurisdiction: Literal["GB", "EU"]
    commodity_code: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class DeclarationDraft(BaseModel):
    invoice_number: str | None = None
    incoterm: str | None = None
    origin_country: str | None = None
    hs_candidates: list[HSRecommendation]
    supporting_evidence: list[EvidenceRef]
    requires_broker_review: bool
    review_reason: str | None = None


client = OpenAI()
draft = client.responses.parse(
    model="gpt-4.1",
    input="Create a customs declaration draft from the supplied OCR output and tariff candidates.",
    text_format=DeclarationDraft,
).output_parsed
```

### Tool Interface Pattern

Tools should expose business operations with narrow scopes. Do not give the model direct credentials to customs systems. Give it read tools for context and one controlled write tool that only stages a draft for review or filing after deterministic validation.

```python
from langchain_core.tools import tool


@tool
def get_tariff_candidates(jurisdiction: str, search_text: str) -> list[dict]:
    """Return a bounded candidate set from tariff data and prior broker decisions."""
    return tariff_service.lookup(
        jurisdiction=jurisdiction,
        search_text=search_text,
        limit=8,
    )


@tool
def stage_declaration_case(case_id: str, draft: dict) -> dict:
    """Write a draft to the customs platform for broker review."""
    validated = declaration_validator.validate_draft(draft)
    return customs_platform.stage_case(case_id=case_id, draft=validated)
```

## Orchestration Outline

The orchestration should be explicit and boring. Start from shipment intake, produce extraction output, retrieve trade knowledge, draft the declaration, run deterministic validation, then branch. Never let the model decide whether a filing adapter call is safe. The validator decides that.

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(DeclarationState)
workflow.add_node("extract_docs", extract_docs)
workflow.add_node("retrieve_rules", retrieve_rules)
workflow.add_node("draft_declaration", draft_declaration)
workflow.add_node("validate", validate_declaration)
workflow.add_node("stage_review", stage_review)
workflow.add_node("file_ready_case", file_ready_case)

workflow.set_entry_point("extract_docs")
workflow.add_edge("extract_docs", "retrieve_rules")
workflow.add_edge("retrieve_rules", "draft_declaration")
workflow.add_edge("draft_declaration", "validate")
workflow.add_conditional_edges(
    "validate",
    lambda state: "file_ready_case" if state.ready_to_file else "stage_review",
)
workflow.add_edge("stage_review", END)
workflow.add_edge("file_ready_case", END)
```

## Prompt And Guardrail Pattern

The system prompt should act like a customs analyst working from supplied evidence only. The key guardrail is not “be accurate.” The key guardrail is “choose only from the retrieved tariff candidates and state when evidence is insufficient.”

```text
You are preparing a customs declaration draft for broker review.

Rules:
- Use only the shipment facts, OCR evidence, tariff candidates, and origin rules provided.
- Never invent a commodity code, origin claim, or preference claim.
- If the correct code cannot be supported from the supplied evidence, set
  requires_broker_review=true and explain the gap.
- If proof of origin is missing, do not claim preference.
- If a sanctions or denied-party match is unresolved, do not mark the case ready to file.
- Return structured data only. No narrative outside the schema.
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| Customs platform adapter | Read shipment context, item master history, prior broker overrides, and write staged drafts back | Keep this adapter idempotent. The customs platform is the operational anchor and audit trail for the broker team |
| HMRC CDS adapter | Submit declarations, amendments, cancellations, and supporting documents; process push or pull notifications | HMRC treats the service as asynchronous. Build around acknowledgement and notification handling rather than assuming synchronous success |
| Tariff data adapter | Load official tariff datasets and snapshot them by effective date | Declarable commodity hierarchies and tariff measures change. Every filed draft needs the tariff version it was evaluated against |
| EU security filing adapter | Add ENS-specific data preparation for ICS2 where the shipper or lane requires it | ENS flows are not the same as import declaration flows. Keep them as separate contracts and tests |
| Screening connector | Call sanctions or restricted-party screening and return structured match status | Screening outputs should remain deterministic and independently reviewable from LLM reasoning |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Extraction accuracy | Gold dataset of real invoices, packing lists, transport docs, and origin docs scored field-by-field against broker-reviewed truth | ≥ 97% exact match for invoice number, quantities, value, and origin-country extraction on in-scope traffic |
| HS classification quality | Compare top-1 and top-3 recommendations against broker-approved codes for repeat SKUs and repeat lanes | ≥ 92% top-1 accuracy to 6 digits, ≥ 98% top-3 coverage on in-scope traffic |
| Filing safety | Replay approved cases through validators and adapter contract tests, then compare staged payloads to accepted government responses | Zero unsafe auto-submissions in pilot and no schema rejects caused by AI-generated fields |
| Exception routing | Inject origin gaps, quota exposure, sanctions matches, and ambiguous descriptions into test cases | 100% of high-risk cases routed to broker review |
| Learning loop quality | Measure whether broker overrides reduce future override rates on the same SKU and supplier combination | Override rate on repeat SKUs falls month over month after memory is enabled |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start in shadow mode for one customs regime, one broker team, and a narrow list of repeat SKUs. Show the broker the draft and evidence, but do not auto-stage filings until the quality gates are stable |
| **Fallback path** | Keep the existing manual declaration path intact. If OCR, model, tariff retrieval, or adapters fail, the case drops to manual handling with no dependency on AI availability |
| **Observability** | Trace candidate codes returned, documents cited, validator failures, notification outcomes, broker overrides, and post-filing rejects. Customs teams need case replay, not just model latency dashboards |
| **Operations ownership** | Trade compliance owns thresholds and exception policy. Platform engineering owns adapters and runtime. Broker operations owns override workflows and acceptance criteria |
