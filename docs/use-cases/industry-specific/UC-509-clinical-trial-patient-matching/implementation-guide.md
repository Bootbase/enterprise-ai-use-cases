---
layout: use-case-detail
title: "Implementation Guide — Autonomous Clinical Trial Patient Matching and Recruitment with Agentic AI"
uc_id: "UC-509"
uc_title: "Autonomous Clinical Trial Patient Matching and Recruitment with Agentic AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Pharmaceutical / Life Sciences"
complexity: "High"
status: "detailed"
slug: "UC-509-clinical-trial-patient-matching"
permalink: /use-cases/UC-509-clinical-trial-patient-matching/implementation-guide/
---

## Build Goal

Deliver an AI-assisted patient screening system that takes a clinical trial protocol and an EHR population, produces ranked patient-trial matches with per-criterion evidence, and presents them to site coordinators for confirmation. The first production boundary covers a single health system's EHR (Epic or Cerner via FHIR R4), one to three active trial protocols, and a coordinator review dashboard. Multi-site federation, real-time CDS Hooks alerting at point of care, and automated outreach workflows remain outside the first release.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.11+ on containerized service (Docker/Kubernetes) | Standard for healthcare AI; strong FHIR client libraries (fhir.resources, fhirclient) |
| **Model access** | Claude API (Anthropic) via anthropic Python SDK | Long context window handles multi-page clinical notes; structured output for criterion-level extraction; tool use for multi-step matching |
| **Orchestration runtime** | LangGraph | Graph-based agent workflow with human-in-the-loop support; clean separation of criteria parsing, matching, and scoring steps |
| **Core connectors** | FHIR R4 client (SMART on FHIR), ClinicalTrials.gov API | Vendor-neutral EHR access; standardized trial protocol retrieval |
| **Evaluation / tracing** | LangSmith + pytest-based evaluation harness | Trace every criterion-level decision; regression testing against expert-labeled datasets |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | FHIR data pipeline operational; criteria parser validated | FHIR R4 data extraction service, HIPAA de-identification pipeline, criteria parsing agent with structured output, test suite against 20+ protocol criteria sets |
| 2 | Patient matching agent producing criterion-level verdicts | Matching agent with evidence extraction from structured and unstructured records, scoring engine, evaluation harness benchmarked against expert labels |
| 3 | Coordinator dashboard and CTMS integration | Review UI with per-criterion evidence display, accept/reject/defer workflow, CTMS writeback adapter, diversity monitoring reports |
| 4 | Pilot on 1–3 active trials with A/B comparison | Side-by-side evaluation against manual screening, screen failure rate measurement, coordinator feedback collection, release gate assessment |

## Core Contracts

### State And Output Schemas

The central data contract is the match result: a per-patient, per-trial structure that carries criterion-level verdicts with evidence. This schema drives the coordinator dashboard and CTMS writeback.

```python
from pydantic import BaseModel
from enum import Enum

class Verdict(str, Enum):
    ELIGIBLE = "eligible"
    EXCLUDED = "excluded"
    UNCERTAIN = "uncertain"

class CriterionResult(BaseModel):
    criterion_id: str          # e.g. "INC-03" or "EXC-07"
    criterion_text: str        # Original eligibility text
    verdict: Verdict
    confidence: float          # 0.0 to 1.0
    evidence: str              # Extracted text from EHR supporting the verdict
    source_resource: str       # FHIR resource ID or note reference

class PatientMatchResult(BaseModel):
    patient_id: str            # De-identified patient identifier
    trial_id: str              # NCT number from ClinicalTrials.gov
    overall_score: float       # Weighted aggregate of criterion scores
    criteria_results: list[CriterionResult]
    hard_exclusions: int       # Count of criteria with verdict=EXCLUDED
    uncertain_count: int       # Count of criteria needing coordinator review
```

### Tool Interface Pattern

The matching agent uses tools to retrieve patient data and evaluate criteria. Each tool is scoped to read-only access against de-identified records.

```python
from anthropic import Anthropic

# Tool definitions exposed to the matching agent
tools = [
    {
        "name": "get_patient_record",
        "description": "Retrieve de-identified patient record including demographics, "
                       "diagnoses, medications, labs, and recent clinical notes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {"type": "string"},
                "resource_types": {
                    "type": "array",
                    "items": {"type": "string",
                              "enum": ["Condition", "MedicationRequest",
                                       "Observation", "DocumentReference"]},
                }
            },
            "required": ["patient_id"]
        }
    },
    {
        "name": "evaluate_criterion",
        "description": "Evaluate a single eligibility criterion against patient data. "
                       "Returns verdict, confidence, and supporting evidence.",
        "input_schema": {
            "type": "object",
            "properties": {
                "criterion_id": {"type": "string"},
                "criterion_text": {"type": "string"},
                "patient_id": {"type": "string"}
            },
            "required": ["criterion_id", "criterion_text", "patient_id"]
        }
    },
]
```

## Orchestration Outline

The workflow follows a three-stage pipeline: parse protocol criteria, match patients against criteria, then score and rank results. The orchestration graph handles batching (many patients × many criteria) and routes uncertain verdicts to the coordinator queue.

```python
from langgraph.graph import StateGraph, END

def build_matching_graph():
    graph = StateGraph(MatchingState)

    graph.add_node("parse_criteria", parse_criteria_node)
    graph.add_node("extract_patient_data", extract_patient_data_node)
    graph.add_node("match_criteria", match_criteria_node)
    graph.add_node("score_and_rank", score_and_rank_node)
    graph.add_node("diversity_rerank", diversity_rerank_node)
    graph.add_node("coordinator_review", coordinator_review_node)

    graph.set_entry_point("parse_criteria")
    graph.add_edge("parse_criteria", "extract_patient_data")
    graph.add_edge("extract_patient_data", "match_criteria")
    graph.add_edge("match_criteria", "score_and_rank")
    graph.add_edge("score_and_rank", "diversity_rerank")
    graph.add_edge("diversity_rerank", "coordinator_review")
    graph.add_edge("coordinator_review", END)

    return graph.compile()
```

## Prompt And Guardrail Pattern

The matching agent receives a system prompt that constrains it to evidence-based reasoning over de-identified patient data. The prompt enforces structured output and explicit uncertainty handling.

```text
You are a clinical trial eligibility screening assistant. Your task is to
evaluate whether a patient meets a specific trial eligibility criterion.

Rules:
- Base your verdict ONLY on evidence present in the patient record provided.
- If the patient record does not contain information relevant to a criterion,
  return verdict "uncertain" — never assume or infer missing data.
- For each verdict, cite the specific FHIR resource or clinical note passage
  that supports your conclusion.
- Never fabricate clinical details, lab values, or diagnoses.
- Never recommend enrollment — only assess criterion-level eligibility.
- Output your response in the specified JSON schema.

Respond with a JSON object containing:
- criterion_id: the criterion identifier
- verdict: one of "eligible", "excluded", "uncertain"
- confidence: float between 0.0 and 1.0
- evidence: the relevant text from the patient record
- source_resource: the FHIR resource ID or note section
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| EHR data extraction | FHIR R4 client with SMART on FHIR OAuth 2.0 authorization; batch extraction of Condition, MedicationRequest, Observation, and DocumentReference resources | Use fhirclient library; implement pagination for large patient populations; apply HIPAA Safe Harbor de-identification before storing in patient data lake |
| ClinicalTrials.gov protocol ingestion | REST client to pull protocol XML/JSON; criteria parsing agent to decompose into structured rules | Cache protocols locally; detect amendments via version tracking; re-parse and re-screen when criteria change |
| CTMS enrollment writeback | REST adapter for Medidata Rave or Veeva Vault CTMS; write confirmed matches with screening status | Map internal patient IDs to CTMS subject identifiers; log all writes for audit trail; handle CTMS-side validation errors gracefully |
| Coordinator review UI | Web dashboard (React or equivalent) showing ranked candidates with expandable per-criterion evidence | Support accept/reject/defer actions; capture free-text feedback on uncertain criteria; export screening reports for IRB |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Criterion-level accuracy | Compare AI verdicts against expert clinician labels on 200+ patient-criterion pairs; measure precision, recall, F1 per verdict class | F1 ≥ 0.87 for eligible/excluded; uncertain recall ≥ 0.95 (prefer false uncertainty over false exclusion) |
| Screen failure rate | Track patients confirmed by AI + coordinator who subsequently fail formal screening | Screen failure rate < 10% (vs. 30–36% baseline) |
| Screening throughput | Measure time from trial activation to ranked candidate list delivered | Candidate list within 48 hours of trial activation (vs. weeks baseline) |
| Diversity compliance | Compare demographic distribution of AI-identified candidates against site catchment area demographics | No demographic group underrepresented by more than 10 percentage points vs. catchment |
| Evidence grounding | Audit 100 randomly sampled evidence citations; verify each maps to an actual passage in the source record | 100% of citations traceable to source; 0 fabricated evidence passages |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start with 1–3 oncology or cardiology trials at a single site; run AI screening in parallel with manual screening for 4–6 weeks; compare match quality and screen failure rates before replacing manual process |
| **Fallback path** | Manual chart review by site coordinators remains available at all times; AI system can be bypassed per-trial via CTMS configuration flag; no enrollment depends solely on AI |
| **Observability** | Trace every criterion-level evaluation in LangSmith; alert on confidence score distribution shifts (may indicate EHR data quality degradation or criteria drift); monitor screening throughput SLA |
| **Operations ownership** | Clinical informatics team owns FHIR pipeline and de-identification; AI/ML engineering team owns matching agent and scoring engine; site coordination team owns dashboard and enrollment workflow |
