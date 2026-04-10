---
layout: use-case-detail
title: "Implementation Guide — Autonomous Medical Prior Authorization Processing"
uc_id: "UC-513"
uc_title: "Autonomous Medical Prior Authorization Processing"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Healthcare"
complexity: "High"
status: "detailed"
slug: "UC-513-medical-prior-authorization"
permalink: /use-cases/UC-513-medical-prior-authorization/implementation-guide/
---

## Build Goal

Deliver a system that detects PA-required orders in the EHR, assembles clinical evidence, matches it against payer medical necessity criteria, and auto-submits routine requests via Da Vinci PAS FHIR APIs. The first production boundary covers a single EHR platform, a limited set of high-volume procedure categories (imaging, outpatient surgery), and the top 5 payers by volume. Pharmacy benefit PA, peer-to-peer escalation, and multi-state regulatory configuration are deferred to later phases.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.12+ / FastAPI | Broad healthcare library ecosystem (fhir.resources, HL7 apy); async support for concurrent payer submissions |
| **Model access** | Anthropic Claude Sonnet via HIPAA BAA, or Azure OpenAI GPT-4o | Clinical NLP extraction and unstructured policy interpretation; HIPAA-eligible endpoints required for PHI |
| **Orchestration runtime** | LangGraph (Python) | Stateful graph with branching: auto-submit path vs. human queue vs. pend-and-retry; built-in checkpointing for long-running authorization cycles |
| **Core connectors** | HAPI FHIR Client (Java) or fhir.resources (Python) for FHIR R4; X12 278 via clearinghouse SDK (Availity, Change Healthcare) | Da Vinci PAS profile construction; X12 fallback for non-FHIR payers |
| **Evaluation / tracing** | LangSmith for LLM tracing; structured audit log to PostgreSQL | Every extraction, confidence score, and submission outcome must be auditable for compliance |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | EHR integration and PA detection | FHIR subscription for order events; CRD query adapter for top 5 payers; benefit eligibility check |
| 2 | Clinical evidence extraction and policy matching | NLP extraction pipeline for chart notes, labs, imaging; medical policy ingestion and vector index; confidence-scored matching |
| 3 | Automated submission and tracking | Da Vinci PAS bundle construction; X12 278 fallback; pend response handling; authorization status writeback to EHR |
| 4 | Pilot deployment and human review workflow | Exception queue UI; denial analyzer; staff training; production pilot with shadow mode before live auto-submission |

## Core Contracts

### State And Output Schemas

The PA request moves through a state machine: `detected` → `evidence_assembled` → `policy_matched` → `submitted` → `resolved` (approved / denied / appealed). Each transition is logged with timestamps and confidence scores.

```python
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class PAStatus(str, Enum):
    DETECTED = "detected"
    EVIDENCE_ASSEMBLED = "evidence_assembled"
    POLICY_MATCHED = "policy_matched"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    DENIED = "denied"
    PENDED = "pended"
    APPEALED = "appealed"

class ClinicalEvidence(BaseModel):
    diagnoses: list[str]          # ICD-10 codes extracted from encounter
    procedures: list[str]         # CPT/HCPCS codes from the order
    supporting_findings: str      # NLP-summarized clinical justification
    lab_values: dict[str, str]    # Relevant lab results (name → value)
    prior_treatments: list[str]   # Step-therapy or prior auth history
    confidence_score: float       # 0.0–1.0, extraction confidence

class PARequest(BaseModel):
    request_id: str
    patient_id: str
    payer_id: str
    ordering_provider: str
    procedure_codes: list[str]
    status: PAStatus
    evidence: ClinicalEvidence | None
    policy_match_score: float | None
    submission_id: str | None      # PAS trace ID or X12 control number
    created_at: datetime
    updated_at: datetime
```

### Tool Interface Pattern

The orchestration agent has access to scoped tools. Each tool is read-only or write-once with explicit side effects documented in the tool description.

```python
from langchain_core.tools import tool

@tool
def query_patient_record(patient_id: str, data_types: list[str]) -> dict:
    """Retrieve clinical data from the EHR via FHIR R4.

    Args:
        patient_id: FHIR Patient resource ID.
        data_types: List of FHIR resource types to fetch
                    (Condition, Observation, DiagnosticReport, MedicationRequest).

    Returns structured clinical data. Read-only; no EHR writes.
    """
    # FHIR R4 query via SMART-on-FHIR client
    ...

@tool
def check_medical_policy(payer_id: str, procedure_code: str, evidence: dict) -> dict:
    """Match clinical evidence against payer medical necessity criteria.

    Returns: policy_id, match_score (0.0-1.0), matched_criteria, gaps.
    Read-only; queries the medical policy vector store.
    """
    # Hybrid: structured CPT/ICD rule check + LLM semantic match
    ...

@tool
def submit_pa_request(pa_bundle: dict, payer_id: str) -> dict:
    """Submit a PA request via Da Vinci PAS FHIR API or X12 278 fallback.

    Returns: submission_id, initial_status, payer_response.
    Write operation; creates a submission record in the audit log.
    """
    # FHIR Bundle POST to payer PAS endpoint; X12 fallback via clearinghouse
    ...
```

## Orchestration Outline

The agent runs as a LangGraph state machine triggered by EHR order events. Each node performs one step; edges are conditional on confidence scores and payer responses.

```python
from langgraph.graph import StateGraph, END

def build_pa_graph():
    graph = StateGraph(PARequest)

    graph.add_node("detect_pa", detect_pa_requirement)
    graph.add_node("assemble_evidence", extract_clinical_evidence)
    graph.add_node("match_policy", evaluate_medical_necessity)
    graph.add_node("submit", submit_to_payer)
    graph.add_node("handle_response", process_payer_response)
    graph.add_node("route_to_human", enqueue_for_staff_review)

    graph.set_entry_point("detect_pa")
    graph.add_conditional_edges("detect_pa", lambda s: "assemble_evidence" if s.status == "detected" else END)
    graph.add_edge("assemble_evidence", "match_policy")
    graph.add_conditional_edges("match_policy", route_by_confidence)  # >=0.85 → submit, <0.85 → human
    graph.add_edge("submit", "handle_response")
    graph.add_conditional_edges("handle_response", route_by_payer_decision)  # approved→END, pended→assemble, denied→human

    return graph.compile(checkpointer=PostgresSaver())
```

The confidence threshold (0.85 default) is configurable per payer and procedure category. Shadow mode runs the full pipeline but routes all cases to human review, logging what would have been auto-submitted.

## Prompt And Guardrail Pattern

The evidence assembly prompt instructs the LLM to extract specific clinical facts, not to interpret or recommend treatment. Output is structured JSON validated against the `ClinicalEvidence` schema.

```text
You are a clinical documentation analyst. Your task is to extract factual
clinical information from patient records to support a prior authorization
request.

EXTRACT ONLY:
- Active diagnoses (ICD-10 codes and descriptions)
- Relevant lab values with dates and reference ranges
- Imaging findings and impressions
- Prior treatments attempted for this condition
- Duration and severity of the condition

DO NOT:
- Recommend treatments or suggest clinical decisions
- Interpret whether the treatment is medically necessary
- Fabricate clinical findings not present in the source records
- Include patient identifiers beyond what is needed for the PA request

If a required data element is not found in the record, return null for that
field -- do not infer or estimate missing values.

Output format: JSON matching the ClinicalEvidence schema.
```

Guardrails: the orchestrator validates LLM output against the Pydantic schema before proceeding. Extraction confidence below 0.7 halts auto-submission and routes to human review. All LLM inputs and outputs are logged to the audit trail with no PHI in external telemetry.

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| **EHR order events** | FHIR Subscription (R4) on ServiceRequest and MedicationRequest resources; CDS Hooks `order-select` and `order-sign` for real-time CRD triggers | Epic requires App Orchard registration and OAuth2 launch flow; Oracle Health uses Ignite APIs; expect 12-24 weeks for bidirectional production certification per EHR vendor |
| **Payer CRD/DTR/PAS** | Da Vinci CRD client for coverage checks; DTR engine for questionnaire-driven evidence collection; PAS client for FHIR Claim bundle submission | Not all payers support Da Vinci PAS yet; build X12 278 fallback via clearinghouse (Availity, Change Healthcare); CMS-0057-F mandates FHIR API support by January 2027 |
| **Medical policy ingestion** | Scheduled crawl or API pull of payer-published medical necessity criteria; parse into structured rules + vector-indexed unstructured text | Payers publish criteria in PDF, HTML, and proprietary portal formats; plan for per-payer parsing adapters; version policies with effective dates to avoid stale matches |
| **Authorization writeback** | FHIR PUT to update the EHR authorization record with approval number, expiration date, and approved units | Writeback permissions require EHR vendor approval; test thoroughly in sandbox before production; handle partial approvals and modified authorizations |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| **Clinical evidence extraction accuracy** | Compare NLP-extracted diagnoses, labs, and findings against clinician-reviewed gold standard on 200+ cases | F1 score >= 0.92 for diagnoses; >= 0.88 for supporting findings |
| **Medical policy match correctness** | Measure agreement between AI confidence score and human reviewer determination (approve/deny/insufficient) | Cohen's kappa >= 0.80 on 500+ matched cases |
| **Auto-submission safety** | Track denial rate for AI-auto-submitted requests vs. staff-submitted requests during shadow period | Auto-submitted denial rate within 2 percentage points of staff-submitted baseline |
| **End-to-end cycle time** | Measure time from order entry to payer decision for auto-submitted vs. manual submissions | Median auto-submitted cycle time < 48 hours (vs. 4+ day manual baseline) |
| **Escalation appropriateness** | Review cases routed to human queue; measure whether escalation was warranted | False escalation rate < 15%; missed escalation rate < 2% |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start in shadow mode: run full pipeline on all PA requests but route 100% to human review; log what would have been auto-submitted; after 4-6 weeks with acceptable metrics, enable auto-submission for high-confidence imaging PAs only; expand procedure categories incrementally |
| **Fallback path** | Kill switch disables auto-submission and routes all requests to the existing manual workflow; staff revert to current payer portals, fax, and phone; no data loss because EHR remains system of record |
| **Observability** | Trace every LLM call (input tokens, output, latency, confidence); alert on extraction confidence drift (rolling 7-day average below threshold); dashboard showing auto-submission rate, denial rate, and payer response time by payer and procedure category |
| **Operations ownership** | Revenue cycle team owns production support and exception queue staffing; IT owns EHR integration and infrastructure; clinical informatics owns medical policy ingestion and extraction accuracy monitoring |
