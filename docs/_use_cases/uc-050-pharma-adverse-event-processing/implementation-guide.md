---
layout: use-case-detail
title: "Implementation Guide — UC-050: Autonomous Adverse Event Report Processing in Pharmacovigilance"
uc_id: "UC-050"
uc_title: "Autonomous Adverse Event Report Processing in Pharmacovigilance"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
status: "detailed"
slug: "uc-050-pharma-adverse-event-processing"
permalink: /use-cases/uc-050-pharma-adverse-event-processing/implementation-guide/
---

## Prerequisites

| Prerequisite | Detail |
|--------------|--------|
| **Azure subscription** | Azure OpenAI deployment that supports structured outputs, plus a queue and container runtime. |
| **Safety system sandbox** | Veeva Vault Safety sandbox with API access, intake inbox configuration, and non-production E2B transmission profile. |
| **Terminology access** | Licensed MedDRA and WHO Drug Dictionary services exposed through internal APIs. |
| **Dev environment** | Python 3.11+, `openai`, `langgraph`, `pydantic`, `requests`, `tenacity`, `lxml`, `rapidfuzz`. |
| **Permissions** | Access to source channels, safety sandbox, prompt/evaluation store, and audit log sink. |

---

## Project Structure

```text
pv-icsr-agent/
├── src/
│   ├── agents/
│   │   ├── graph.py                # LangGraph workflow
│   │   ├── extract.py              # Structured extraction worker
│   │   ├── coding.py               # MedDRA / WHO Drug worker
│   │   ├── duplicate.py            # Duplicate comparison worker
│   │   └── narrative.py            # Narrative drafting + QC
│   ├── tools/
│   │   ├── veeva.py                # Safety DB connector
│   │   ├── meddra.py               # Terminology lookup wrappers
│   │   ├── who_drug.py             # Product dictionary wrappers
│   │   └── xsd.py                  # E2B schema validation
│   ├── prompts/
│   │   ├── extract_system.txt
│   │   ├── coding_system.txt
│   │   ├── duplicate_system.txt
│   │   ├── narrative_system.txt
│   │   └── qc_system.txt
│   ├── models/
│   │   ├── intake.py               # Pydantic schemas
│   │   └── case_state.py           # Graph state types
│   └── eval/
│       ├── score_extraction.py
│       ├── score_duplicates.py
│       └── score_narratives.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evaluation/
└── README.md
```

The important boundary is not the folder tree. It is the contract line between:

- LLM workers that read, compare, or draft
- deterministic tools that search, validate, write, or transmit

That split is what makes the system auditable.

---

## Step-by-Step Implementation

### Phase 1: Foundation

#### Step 1.1: Install the AI and connector dependencies

```bash
uv init pv-icsr-agent
uv add openai langgraph pydantic requests tenacity lxml rapidfuzz
```

Use `langgraph` for orchestration, `openai` for Azure OpenAI structured outputs, `requests` for the safety-system seam, and `lxml` for local XSD prechecks. LangGraph is the main runtime because it gives you checkpointed state and interrupts, which are the two features a regulated HITL workflow needs most.

**Verification:** `uv run python -c "import openai, langgraph, pydantic, requests, lxml"` exits successfully.

#### Step 1.2: Define the case-state and extraction contracts first

Do this before writing any prompt. The extraction schema is the real API between the LLM and the rest of the system.

```python
from typing import Literal

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class EvidenceSpan(BaseModel):
    quote: str = Field(min_length=1)
    source_id: str
    start_char: int
    end_char: int


class MinimumCriteria(BaseModel):
    identifiable_patient: bool
    identifiable_reporter: bool
    suspect_product: bool
    adverse_event: bool


class IntakePacket(BaseModel):
    source_language: str | None = None
    seriousness: Literal["serious", "non_serious", "unknown"]
    minimum_criteria: MinimumCriteria
    suspect_products: list[str]
    adverse_events: list[str]
    patient_age: str | None = None
    patient_sex: str | None = None
    reporter_type: str | None = None
    narrative_summary: str
    evidence: list[EvidenceSpan]
    confidence: float = Field(ge=0.0, le=1.0)


class CaseState(TypedDict, total=False):
    case_id: str
    source_bundle: str
    intake: IntakePacket
    coding_result: dict
    duplicate_result: dict
    narrative_result: dict
    qc_result: dict
    review_reason: str
    review_decision: dict
    veeva_record_id: str
```

**Verification:** invalid extra fields or missing required fields fail in unit tests before any live model call.

---

### Phase 2: Core AI Integration

#### Step 2.1: Connect Azure OpenAI with strict structured outputs

This node is the foundation of the entire workflow. If you do not lock extraction to a schema, downstream validation gets noisy fast. Azure's structured outputs are designed for exactly this pattern.

```python
import os

from openai import AzureOpenAI

from models.intake import IntakePacket


client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-08-01-preview",
)

EXTRACTION_SYSTEM_PROMPT = """
You are the intake extraction worker for a pharmacovigilance system.
Populate the IntakePacket schema from the source bundle.

Rules:
1. Only extract facts supported by quoted evidence.
2. If a field is not explicit, return null or an empty list.
3. Do not infer causality.
4. Do not invent MedDRA or WHO Drug codes.
5. Return only schema-valid output.
""".strip()


def run_extraction(bundle_text: str) -> IntakePacket:
    completion = client.beta.chat.completions.parse(
        model=os.environ["AZURE_OPENAI_EXTRACT_MODEL"],
        temperature=0,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": bundle_text},
        ],
        response_format=IntakePacket,
    )
    return completion.choices[0].message.parsed
```

**Why this matters:** the model's job is now "fill this contract," not "write something useful." That change removes most downstream parsing code and makes reviewer diffing practical.

#### Step 2.2: Define the graph, not just a chat loop

Graph orchestration is the right fit because the case has state, approval pauses, retries, and branch points. LangGraph's `StateGraph`, checkpointing, and interrupts are the critical APIs here.

```python
from typing import Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from models.case_state import CaseState
from agents.extract import run_extraction
from agents.coding import run_coding_worker
from agents.duplicate import run_duplicate_worker
from agents.narrative import run_narrative_worker, run_qc_worker


def extract_node(state: CaseState) -> CaseState:
    return {"intake": run_extraction(state["source_bundle"])}


def route_after_extract(state: CaseState) -> Literal["coding", "human_review"]:
    intake = state["intake"]
    if intake.seriousness == "serious" or intake.confidence < 0.90:
        return "human_review"
    return "coding"


def coding_node(state: CaseState) -> CaseState:
    return {"coding_result": run_coding_worker(state["intake"])}


def duplicate_node(state: CaseState) -> CaseState:
    return {"duplicate_result": run_duplicate_worker(state)}


def narrative_node(state: CaseState) -> CaseState:
    return {"narrative_result": run_narrative_worker(state)}


def qc_node(state: CaseState) -> CaseState:
    return {"qc_result": run_qc_worker(state)}


def route_after_qc(state: CaseState) -> Literal["write_case", "human_review"]:
    if state["qc_result"]["requires_human_review"]:
        return "human_review"
    return "write_case"


def human_review_node(state: CaseState) -> Command[Literal["write_case", END]]:
    decision = interrupt(
        {
            "case_id": state.get("case_id"),
            "review_reason": state.get("review_reason", "Regulatory review required"),
            "draft": {
                "intake": state.get("intake"),
                "coding": state.get("coding_result"),
                "duplicate": state.get("duplicate_result"),
                "narrative": state.get("narrative_result"),
                "qc": state.get("qc_result"),
            },
        }
    )
    if not decision["approved"]:
        return Command(update={"review_decision": decision}, goto=END)
    return Command(update={"review_decision": decision}, goto="write_case")


builder = StateGraph(CaseState)
builder.add_node("extract", extract_node)
builder.add_node("coding", coding_node)
builder.add_node("duplicate", duplicate_node)
builder.add_node("narrative", narrative_node)
builder.add_node("qc", qc_node)
builder.add_node("human_review", human_review_node)
builder.add_node("write_case", lambda state: state)

builder.add_edge(START, "extract")
builder.add_conditional_edges("extract", route_after_extract)
builder.add_edge("coding", "duplicate")
builder.add_edge("duplicate", "narrative")
builder.add_edge("narrative", "qc")
builder.add_conditional_edges("qc", route_after_qc)
builder.add_edge("write_case", END)

graph = builder.compile(checkpointer=MemorySaver())
```

This is the core design point: the graph decides control flow; the model only decides within a narrowly scoped node.

#### Step 2.3: Bind domain tools where the model genuinely needs lookup

Do not expose the safety database as a giant generic toolset. Give each worker only the tools it needs.

[... implementation code continues ...]

---

## Configuration Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `AZURE_OPENAI_EXTRACT_MODEL` | none | Deployment used for schema-first extraction. |
| `AZURE_OPENAI_TOOL_MODEL` | none | Deployment used for tool-calling workers. |
| `AZURE_OPENAI_NARRATIVE_MODEL` | none | Deployment used for narrative drafting. |
| `EXTRACTION_TEMPERATURE` | `0.0` | Keep extraction deterministic. |
| `NARRATIVE_TEMPERATURE` | `0.2` | Allow slight linguistic flexibility without drifting facts. |
| `AUTO_ROUTE_CONFIDENCE` | `0.90` | Minimum extraction confidence for touchless routing. |
| `DUPLICATE_REVIEW_FLOOR` | `0.60` | Lower bound for human duplicate review. |
| `MAX_SOURCE_CHARS` | `24000` | Upper bound passed into a single worker call before chunking. |
| `VEEVA_API_VERSION` | `v15.0` | Veeva Vault API version. |
| `CHECKPOINT_BACKEND` | `sqlite` | Replace in-memory examples with durable storage in production. |

---

## Testing Strategy

### Unit Tests

Test deterministic logic aggressively:

- minimum-criteria rules
- field mapping to the safety database
- escalation policy
- XSD validation wrappers
- tool result parsing

### Integration Tests

Use a real Azure OpenAI deployment and a safety sandbox:

- live extraction against canned reports
- live terminology lookup
- record creation and attachment upload in the sandbox
- outbound XML validation without transmission

### Evaluation Tests

Do not stop at "the call succeeded." Score the AI output against a labeled gold set.

Track at least:

- field-level extraction accuracy
- case-validity classification accuracy
- MedDRA coding top-1 / top-3 match rate
- duplicate detection precision and recall
- narrative reviewer edit distance
- percentage of cases auto-routed vs escalated

---

## Monitoring & Observability

| What to Monitor | Tool / Method | Alert Threshold |
|-----------------|---------------|-----------------|
| **Extraction schema failures** | Structured logging on parse exceptions | `>1%` of cases in 15 minutes |
| **Escalation rate** | Graph-state metrics | Sudden rise above calibrated baseline |
| **Duplicate-review uncertainty** | Custom worker metric | `>25%` of routine cases |
| **Safety writeback failures** | Connector logs | Any sustained non-zero error rate |
| **E2B validation failures** | XML validation queue | Immediate alert for any production case |
| **Token usage per case** | Azure/OpenAI usage logs | Deviation from pilot baseline |

---

## Common Pitfalls & Mitigations

| Pitfall | Mitigation |
|---------|------------|
| Letting the model decide submission rules | Keep regulatory gating in deterministic code. |
| Exposing too many tools to one worker | Give each worker only the tools it needs. |
| Writing model output straight into the safety system | Use an explicit mapping layer and sandbox first. |
| Using one prompt for extraction, coding, and narrative | Split workers by task and validate each separately. |
| Ignoring evidence provenance | Persist evidence spans with every extracted field. |
| Treating validation as a one-time project | Re-run the gold set whenever prompts, tools, or models change. |

---

## Rollback Plan

If quality drops or a validation issue appears:

1. Disable the touchless route flag so every case pauses after extraction.
2. Keep AI in suggestion-only mode for coding and narrative generation.
3. Continue using the safety inbox and manual case processing as the system of record.
4. Preserve all prompts, traces, and reviewer corrections from the failed batch for root-cause analysis.
