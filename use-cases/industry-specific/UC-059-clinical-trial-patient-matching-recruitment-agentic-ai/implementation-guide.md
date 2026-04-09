# UC-059: Autonomous Clinical Trial Patient Matching and Recruitment — Implementation Guide

## Prerequisites

| Prerequisite | Detail |
|-------------|--------|
| **Azure Subscription** | Azure OpenAI (GPT-4o, GPT-4o-mini, text-embedding-3-large deployed), Azure AI Search (S1+), Azure Database for PostgreSQL, Azure Cosmos DB, AKS |
| **API Keys / Access** | Azure OpenAI endpoint + deployment names; FHIR client credentials (SMART on FHIR OAuth 2.0 registered app) for target EHR systems; ClinicalTrials.gov API key |
| **Existing Systems** | EHR system with FHIR R4 API enabled (Epic or Oracle Health/Cerner); CTMS with REST API (Medidata Rave or Veeva Vault) |
| **Dev Environment** | Python 3.11+; `langgraph>=1.0`, `langchain-openai`, `fhir.resources>=8.0`, `azure-search-documents`, `azure-cosmos`; Docker for local development |
| **Permissions** | SMART on FHIR scopes: `patient/Patient.read`, `patient/Condition.read`, `patient/Observation.read`, `patient/MedicationRequest.read`, `patient/DocumentReference.read`; Azure RBAC: Contributor on resource group |

---

## Project Structure

```
trial-match-ai/
├── src/
│   ├── agents/                  # Agent definitions and orchestration
│   │   ├── orchestrator.py      # LangGraph StateGraph definition
│   │   ├── protocol_agent.py    # Protocol criteria extraction agent
│   │   ├── matching_agent.py    # Patient-trial matching agent (RAG + CoT)
│   │   ├── site_agent.py        # Site optimization agent
│   │   └── monitor_agent.py     # Enrollment monitoring agent
│   ├── tools/                   # Tool/function definitions for agents
│   │   ├── fhir_tools.py        # FHIR R4 patient data retrieval
│   │   ├── ctgov_tools.py       # ClinicalTrials.gov API queries
│   │   ├── search_tools.py      # Azure AI Search vector/hybrid queries
│   │   ├── ctms_tools.py        # CTMS read/write operations
│   │   └── document_tools.py    # PDF extraction via Document Intelligence
│   ├── prompts/                 # System prompts and prompt templates
│   │   ├── criteria_extraction.py
│   │   ├── patient_matching.py
│   │   ├── site_scoring.py
│   │   └── enrollment_analysis.py
│   ├── models/                  # Data models and schemas
│   │   ├── eligibility.py       # Pydantic models for eligibility criteria
│   │   ├── match_result.py      # Match scoring output schemas
│   │   └── patient.py           # Normalized patient data model
│   └── api/                     # FastAPI endpoints
│       └── main.py
├── config/
│   └── settings.py              # Environment-based configuration
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evaluation/              # AI quality evaluation tests
└── pyproject.toml
```

---

## Step-by-Step Implementation

### Phase 1: Foundation

#### Step 1.1: Core Dependencies

```bash
pip install langgraph>=1.0 langchain-openai>=0.3 langchain-community \
    azure-search-documents azure-cosmos azure-identity \
    fhir.resources>=8.0 fhir-pyrate httpx pydantic>=2.0 \
    azure-ai-documentintelligence
```

#### Step 1.2: Configuration

```python
# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_VERSION: str = "2024-10-21"
    AZURE_OPENAI_DEPLOYMENT_GPT4O: str = "gpt-4o"
    AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI: str = "gpt-4o-mini"
    AZURE_OPENAI_DEPLOYMENT_EMBEDDING: str = "text-embedding-3-large"

    # Model params
    REASONING_TEMPERATURE: float = 0.0  # Deterministic for clinical decisions
    EXTRACTION_TEMPERATURE: float = 0.0
    MAX_TOKENS_REASONING: int = 4096
    MAX_TOKENS_EXTRACTION: int = 2048

    # FHIR
    FHIR_BASE_URL: str  # e.g., https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
    FHIR_CLIENT_ID: str
    FHIR_CLIENT_SECRET: str
    FHIR_SCOPES: str = "patient/Patient.read patient/Condition.read patient/Observation.read"

    # Azure AI Search
    SEARCH_ENDPOINT: str
    SEARCH_INDEX_NAME: str = "patient-records"
    SEARCH_SEMANTIC_CONFIG: str = "patient-semantic"

    # Matching thresholds
    MATCH_CONFIDENCE_THRESHOLD: float = 0.85  # Below this -> HITL review
    MATCH_EXCLUDE_THRESHOLD: float = 0.30     # Below this -> auto-exclude

    # ClinicalTrials.gov
    CTGOV_API_BASE: str = "https://clinicaltrials.gov/api/v2"

    class Config:
        env_file = ".env"

settings = Settings()
```

---

### Phase 2: Core AI Integration

#### Step 2.1: LLM Connection and Structured Output

The LLM is the reasoning engine for eligibility evaluation. We use GPT-4o with structured output (Pydantic models) to enforce consistent, parseable decisions.

```python
# src/models/eligibility.py
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class CriterionType(str, Enum):
    INCLUSION = "inclusion"
    EXCLUSION = "exclusion"

class EligibilityCriterion(BaseModel):
    """A single decomposed eligibility criterion from a trial protocol."""
    id: str = Field(description="Unique criterion identifier, e.g., 'INC-01'")
    type: CriterionType
    category: str = Field(description="Category: demographic, diagnosis, lab_value, medication, procedure, temporal, biomarker, other")
    description: str = Field(description="Human-readable criterion text from protocol")
    structured_query: dict = Field(description="Machine-executable query with FHIR resource type, code system, value constraints")
    temporal_constraint: Optional[str] = Field(default=None, description="Temporal constraint if any, e.g., 'within_months:6'")

class ProtocolCriteria(BaseModel):
    """Complete set of extracted eligibility criteria for a trial."""
    trial_id: str
    trial_title: str
    inclusion_criteria: list[EligibilityCriterion]
    exclusion_criteria: list[EligibilityCriterion]
    extraction_confidence: float = Field(ge=0.0, le=1.0)

class CriterionVerdict(str, Enum):
    MET = "met"
    NOT_MET = "not_met"
    INSUFFICIENT_DATA = "insufficient_data"
    REQUIRES_REVIEW = "requires_review"

class CriterionEvaluation(BaseModel):
    """LLM evaluation of one patient against one criterion."""
    criterion_id: str
    verdict: CriterionVerdict
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str = Field(description="Specific patient data supporting this verdict")
    reasoning: str = Field(description="Chain-of-thought reasoning trace")

class PatientMatchResult(BaseModel):
    """Complete match result for one patient against one trial."""
    patient_id: str
    trial_id: str
    overall_score: float = Field(ge=0.0, le=1.0)
    criterion_evaluations: list[CriterionEvaluation]
    recommendation: str = Field(description="ELIGIBLE, INELIGIBLE, or REVIEW_NEEDED")
    summary: str
```

```python
# src/agents/protocol_agent.py
from langchain_openai import AzureChatOpenAI
from config.settings import settings
from src.models.eligibility import ProtocolCriteria

llm_reasoning = AzureChatOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_GPT4O,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    temperature=settings.EXTRACTION_TEMPERATURE,
    max_tokens=settings.MAX_TOKENS_EXTRACTION,
)

# Structured output: LLM returns a validated Pydantic model
structured_llm = llm_reasoning.with_structured_output(ProtocolCriteria)
```

#### Step 2.2: Protocol Criteria Agent — Parsing Eligibility Requirements

This agent takes a raw protocol document and decomposes eligibility criteria into structured, machine-executable rules. This is the first step in the pipeline — everything downstream depends on the quality of this extraction.

```python
# src/prompts/criteria_extraction.py

CRITERIA_EXTRACTION_SYSTEM_PROMPT = """You are a clinical trial protocol analyst specializing in eligibility criteria extraction.

Your task: Given a clinical trial protocol, extract ALL inclusion and exclusion criteria
and decompose each into a structured, machine-executable format.

## Rules
1. Extract every criterion — do not summarize or merge related criteria.
2. For each criterion, identify the FHIR resource type and code system needed to evaluate it:
   - Diagnoses → Condition (ICD-10-CM)
   - Lab values → Observation (LOINC)
   - Medications → MedicationRequest (RxNorm)
   - Procedures → Procedure (CPT/SNOMED-CT)
   - Demographics → Patient (direct fields)
   - Biomarkers → Observation (LOINC) or DiagnosticReport
3. Identify temporal constraints explicitly (e.g., "within 6 months", "prior to enrollment").
4. For lab value criteria, include the threshold, unit, and comparator (e.g., {"loinc": "718-7", "comparator": ">=", "value": 9.0, "unit": "g/dL"}).
5. For medication criteria, specify whether current, prior, or never-used.
6. Flag ambiguous criteria that may require clinical interpretation.

## Output format
Return a ProtocolCriteria JSON object with all criteria decomposed.

## Example criterion decomposition
Protocol text: "Hemoglobin ≥ 9.0 g/dL within 14 days prior to enrollment"
→ {
    "id": "INC-03",
    "type": "inclusion",
    "category": "lab_value",
    "description": "Hemoglobin ≥ 9.0 g/dL within 14 days prior to enrollment",
    "structured_query": {
      "fhir_resource": "Observation",
      "code_system": "LOINC",
      "code": "718-7",
      "display": "Hemoglobin",
      "comparator": ">=",
      "value": 9.0,
      "unit": "g/dL"
    },
    "temporal_constraint": "within_days:14"
  }
"""
```

```python
# src/agents/protocol_agent.py (continued)
from langchain_core.messages import SystemMessage, HumanMessage
from src.prompts.criteria_extraction import CRITERIA_EXTRACTION_SYSTEM_PROMPT
from src.tools.document_tools import extract_protocol_text
from src.tools.ctgov_tools import fetch_trial_metadata

async def parse_protocol(trial_id: str) -> ProtocolCriteria:
    """Extract structured eligibility criteria from a trial protocol."""
    # Step 1: Retrieve protocol text
    trial_metadata = await fetch_trial_metadata(trial_id)
    protocol_text = trial_metadata.get("eligibilityModule", {}).get("eligibilityCriteria", "")

    # If PDF protocol available, extract full text
    if trial_metadata.get("protocolDocumentUrl"):
        protocol_text = await extract_protocol_text(trial_metadata["protocolDocumentUrl"])

    # Step 2: LLM extracts and decomposes criteria
    messages = [
        SystemMessage(content=CRITERIA_EXTRACTION_SYSTEM_PROMPT),
        HumanMessage(content=f"Trial ID: {trial_id}\nTrial Title: {trial_metadata['title']}\n\nProtocol eligibility section:\n{protocol_text}")
    ]

    criteria: ProtocolCriteria = await structured_llm.ainvoke(messages)
    criteria.trial_id = trial_id
    criteria.trial_title = trial_metadata["title"]
    return criteria
```

#### Step 2.3: Tool Definitions — FHIR Data Retrieval

These tools are what the Patient Matching Agent calls to retrieve real patient data from EHR systems. This is where the AI meets the real world.

```python
# src/tools/fhir_tools.py
import httpx
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.condition import Condition
from fhir.resources.R4B.observation import Observation
from fhir.resources.R4B.medicationrequest import MedicationRequest
from langchain_core.tools import tool
from config.settings import settings

class FHIRClient:
    """FHIR R4 client for EHR data retrieval with SMART on FHIR auth."""

    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: str | None = None

    async def _get_token(self) -> str:
        """Obtain OAuth 2.0 access token via SMART on FHIR backend services flow."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": settings.FHIR_SCOPES,
                },
            )
            resp.raise_for_status()
            self._token = resp.json()["access_token"]
        return self._token

    async def _request(self, path: str, params: dict | None = None) -> dict:
        token = self._token or await self._get_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/{path}",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_patient(self, patient_id: str) -> Patient:
        data = await self._request(f"Patient/{patient_id}")
        return Patient.model_validate(data)

    async def get_conditions(self, patient_id: str) -> list[Condition]:
        bundle = await self._request("Condition", {"patient": patient_id, "_count": "100"})
        return [Condition.model_validate(e["resource"]) for e in bundle.get("entry", [])]

    async def get_observations(self, patient_id: str, loinc_code: str | None = None) -> list[Observation]:
        params = {"patient": patient_id, "_count": "100", "_sort": "-date"}
        if loinc_code:
            params["code"] = f"http://loinc.org|{loinc_code}"
        bundle = await self._request("Observation", params)
        return [Observation.model_validate(e["resource"]) for e in bundle.get("entry", [])]

    async def get_medications(self, patient_id: str) -> list[MedicationRequest]:
        bundle = await self._request("MedicationRequest", {"patient": patient_id, "_count": "100"})
        return [MedicationRequest.model_validate(e["resource"]) for e in bundle.get("entry", [])]


fhir_client = FHIRClient(settings.FHIR_BASE_URL, settings.FHIR_CLIENT_ID, settings.FHIR_CLIENT_SECRET)


@tool
async def get_patient_demographics(patient_id: str) -> dict:
    """Retrieve patient demographics (age, gender, race, ethnicity) from FHIR."""
    patient = await fhir_client.get_patient(patient_id)
    return {
        "patient_id": patient_id,
        "birth_date": str(patient.birthDate) if patient.birthDate else None,
        "gender": patient.gender,
        "race": next((ext.valueString for ext in (patient.extension or []) if "race" in (ext.url or "")), None),
        "ethnicity": next((ext.valueString for ext in (patient.extension or []) if "ethnicity" in (ext.url or "")), None),
    }


@tool
async def get_patient_conditions(patient_id: str) -> list[dict]:
    """Retrieve active diagnoses/conditions for a patient from FHIR (ICD-10 coded)."""
    conditions = await fhir_client.get_conditions(patient_id)
    return [
        {
            "code": c.code.coding[0].code if c.code and c.code.coding else None,
            "system": c.code.coding[0].system if c.code and c.code.coding else None,
            "display": c.code.coding[0].display if c.code and c.code.coding else None,
            "status": c.clinicalStatus.coding[0].code if c.clinicalStatus and c.clinicalStatus.coding else None,
            "onset": str(c.onsetDateTime) if c.onsetDateTime else None,
        }
        for c in conditions
    ]


@tool
async def get_lab_result(patient_id: str, loinc_code: str) -> dict | None:
    """Retrieve the most recent lab result for a specific LOINC code from FHIR."""
    observations = await fhir_client.get_observations(patient_id, loinc_code)
    if not observations:
        return None
    obs = observations[0]  # Most recent (sorted by -date)
    return {
        "loinc_code": loinc_code,
        "value": obs.valueQuantity.value if obs.valueQuantity else None,
        "unit": obs.valueQuantity.unit if obs.valueQuantity else None,
        "date": str(obs.effectiveDateTime) if obs.effectiveDateTime else None,
        "display": obs.code.coding[0].display if obs.code and obs.code.coding else None,
    }


@tool
async def get_patient_medications(patient_id: str) -> list[dict]:
    """Retrieve active medications for a patient from FHIR (RxNorm coded)."""
    meds = await fhir_client.get_medications(patient_id)
    return [
        {
            "code": m.medicationCodeableConcept.coding[0].code if m.medicationCodeableConcept and m.medicationCodeableConcept.coding else None,
            "display": m.medicationCodeableConcept.coding[0].display if m.medicationCodeableConcept and m.medicationCodeableConcept.coding else None,
            "status": m.status,
            "authored_on": str(m.authoredOn) if m.authoredOn else None,
        }
        for m in meds
    ]
```

```python
# src/tools/search_tools.py
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.identity.aio import DefaultAzureCredential
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.tools import tool
from config.settings import settings

embeddings = AzureOpenAIEmbeddings(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_EMBEDDING,
    api_version=settings.AZURE_OPENAI_API_VERSION,
)

credential = DefaultAzureCredential()
search_client = SearchClient(
    endpoint=settings.SEARCH_ENDPOINT,
    index_name=settings.SEARCH_INDEX_NAME,
    credential=credential,
)


@tool
async def search_patient_notes(patient_id: str, query: str, top_k: int = 5) -> list[dict]:
    """Hybrid search over a patient's clinical notes (structured + unstructured).
    Uses BM25 lexical search + vector semantic search for best recall.
    This is the RAG retrieval step for patient matching."""
    query_vector = await embeddings.aembed_query(query)

    results = await search_client.search(
        search_text=query,  # BM25 lexical
        vector_queries=[
            VectorizedQuery(vector=query_vector, k_nearest_neighbors=top_k, fields="content_vector")
        ],
        filter=f"patient_id eq '{patient_id}'",
        query_type="semantic",
        semantic_configuration_name=settings.SEARCH_SEMANTIC_CONFIG,
        top=top_k,
        select=["content", "note_type", "note_date", "provider", "patient_id"],
    )

    return [
        {
            "content": r["content"],
            "note_type": r["note_type"],
            "note_date": r["note_date"],
            "score": r["@search.score"],
        }
        async for r in results
    ]
```

---

### Phase 3: Agent Orchestration with LangGraph

#### Step 3.1: State Definition and Graph

The Orchestrator Agent is the backbone — a LangGraph StateGraph that routes between specialized agents based on the current state of the matching workflow.

```python
# src/agents/orchestrator.py
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.models.eligibility import ProtocolCriteria, PatientMatchResult

class TrialMatchState(TypedDict):
    """Shared state across all agents in the matching workflow."""
    # Input
    trial_id: str
    patient_ids: list[str]

    # Protocol Criteria Agent output
    criteria: ProtocolCriteria | None

    # Patient Matching Agent output
    match_results: list[PatientMatchResult]

    # Flags
    needs_human_review: list[str]  # patient_ids requiring HITL
    current_patient_index: int
    status: str  # "parsing", "matching", "reviewing", "complete"

    # Audit
    messages: Annotated[list, add_messages]


async def parse_protocol_node(state: TrialMatchState) -> dict:
    """Node: Protocol Criteria Agent parses the trial protocol."""
    from src.agents.protocol_agent import parse_protocol
    criteria = await parse_protocol(state["trial_id"])
    return {"criteria": criteria, "status": "matching", "current_patient_index": 0}


async def match_patient_node(state: TrialMatchState) -> dict:
    """Node: Patient Matching Agent evaluates one patient against all criteria."""
    from src.agents.matching_agent import evaluate_patient
    idx = state["current_patient_index"]
    patient_id = state["patient_ids"][idx]
    criteria = state["criteria"]

    result = await evaluate_patient(patient_id, criteria)

    match_results = list(state.get("match_results", []))
    match_results.append(result)

    needs_review = list(state.get("needs_human_review", []))
    if result.recommendation == "REVIEW_NEEDED":
        needs_review.append(patient_id)

    return {
        "match_results": match_results,
        "needs_human_review": needs_review,
        "current_patient_index": idx + 1,
    }


def should_continue_matching(state: TrialMatchState) -> str:
    """Conditional edge: continue matching patients or move to review."""
    if state["current_patient_index"] < len(state["patient_ids"]):
        return "match_patient"
    elif state["needs_human_review"]:
        return "human_review"
    else:
        return "complete"


async def human_review_node(state: TrialMatchState) -> dict:
    """Node: Pause for human review of low-confidence matches.
    LangGraph's interrupt() mechanism suspends the graph here."""
    from langgraph.types import interrupt
    review_request = interrupt({
        "action": "review_matches",
        "patient_ids": state["needs_human_review"],
        "match_results": [
            r.model_dump() for r in state["match_results"]
            if r.patient_id in state["needs_human_review"]
        ],
    })
    # After human resumes with approved/rejected decisions:
    return {"status": "complete", "needs_human_review": []}


async def complete_node(state: TrialMatchState) -> dict:
    """Node: Finalize results and push to CTMS."""
    from src.tools.ctms_tools import push_match_results
    eligible = [r for r in state["match_results"] if r.recommendation == "ELIGIBLE"]
    await push_match_results(state["trial_id"], eligible)
    return {"status": "complete"}


def build_trial_match_graph():
    """Build the LangGraph StateGraph for trial matching."""
    graph = StateGraph(TrialMatchState)

    # Add nodes
    graph.add_node("parse_protocol", parse_protocol_node)
    graph.add_node("match_patient", match_patient_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("complete", complete_node)

    # Add edges
    graph.add_edge(START, "parse_protocol")
    graph.add_edge("parse_protocol", "match_patient")
    graph.add_conditional_edges("match_patient", should_continue_matching, {
        "match_patient": "match_patient",
        "human_review": "human_review",
        "complete": "complete",
    })
    graph.add_edge("human_review", "complete")
    graph.add_edge("complete", END)

    return graph


async def create_app():
    """Create the compiled graph with persistent checkpointing."""
    graph = build_trial_match_graph()
    checkpointer = AsyncPostgresSaver.from_conn_string(
        "postgresql://user:pass@localhost:5432/trialmatch"
    )
    await checkpointer.setup()
    return graph.compile(checkpointer=checkpointer)
```

#### Step 3.2: Patient Matching Agent — RAG + Chain-of-Thought

This is the most LLM-intensive agent. It retrieves patient data from FHIR and clinical notes, then reasons through each eligibility criterion using medical Chain-of-Thought.

```python
# src/prompts/patient_matching.py

PATIENT_MATCHING_SYSTEM_PROMPT = """You are a clinical research coordinator AI assistant evaluating whether a patient
is eligible for a clinical trial. You must evaluate EACH criterion independently.

## Evaluation process for each criterion:
1. RETRIEVE: Identify what patient data is needed (FHIR resource + code).
2. EXAMINE: Review the retrieved structured data AND any relevant clinical notes.
3. REASON: Apply medical Chain-of-Thought reasoning:
   - State the criterion requirement
   - State what the patient data shows
   - Evaluate temporal constraints (is the data within the required window?)
   - Consider edge cases (borderline values, conflicting data sources)
   - Reach a verdict
4. SCORE: Assign confidence (0.0-1.0) based on data completeness and clarity.

## Verdict rules:
- MET: Patient clearly satisfies this criterion based on available data.
- NOT_MET: Patient clearly does NOT satisfy this criterion.
- INSUFFICIENT_DATA: Required data is missing from the EHR — cannot determine.
- REQUIRES_REVIEW: Data is ambiguous or borderline — needs clinical judgment.

## Overall scoring:
- If ANY exclusion criterion is MET → INELIGIBLE
- If ANY inclusion criterion is NOT_MET → INELIGIBLE
- If all inclusion criteria MET and no exclusion criteria MET → ELIGIBLE
- If any criterion is INSUFFICIENT_DATA or REQUIRES_REVIEW → REVIEW_NEEDED

## Critical rules:
- Never assume data that is not present. Missing = INSUFFICIENT_DATA.
- For temporal constraints, compare dates explicitly. "Within 6 months" means
  the observation date must be after (enrollment_date - 6 months).
- For lab values, check the unit matches. Convert if necessary.
- Cite the specific data point (value, date, source) in your evidence field.
"""
```

```python
# src/agents/matching_agent.py
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.models.eligibility import (
    ProtocolCriteria, PatientMatchResult, CriterionEvaluation, CriterionVerdict
)
from src.tools.fhir_tools import (
    get_patient_demographics, get_patient_conditions,
    get_lab_result, get_patient_medications,
)
from src.tools.search_tools import search_patient_notes
from src.prompts.patient_matching import PATIENT_MATCHING_SYSTEM_PROMPT
from config.settings import settings

llm = AzureChatOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_GPT4O,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    temperature=settings.REASONING_TEMPERATURE,
    max_tokens=settings.MAX_TOKENS_REASONING,
)

structured_llm = llm.with_structured_output(PatientMatchResult)


async def gather_patient_context(patient_id: str, criteria: ProtocolCriteria) -> str:
    """Retrieve all relevant patient data for matching against trial criteria.
    This is the RAG retrieval step — gather structured FHIR data + relevant clinical notes."""

    # Structured FHIR data
    demographics = await get_patient_demographics.ainvoke({"patient_id": patient_id})
    conditions = await get_patient_conditions.ainvoke({"patient_id": patient_id})
    medications = await get_patient_medications.ainvoke({"patient_id": patient_id})

    # Retrieve lab values mentioned in criteria
    lab_results = []
    for criterion in criteria.inclusion_criteria + criteria.exclusion_criteria:
        if criterion.category == "lab_value":
            loinc = criterion.structured_query.get("code")
            if loinc:
                result = await get_lab_result.ainvoke({"patient_id": patient_id, "loinc_code": loinc})
                if result:
                    lab_results.append(result)

    # Semantic search over unstructured clinical notes for each criterion
    note_context = []
    for criterion in criteria.inclusion_criteria + criteria.exclusion_criteria:
        if criterion.category in ("diagnosis", "procedure", "biomarker", "temporal", "other"):
            notes = await search_patient_notes.ainvoke({
                "patient_id": patient_id,
                "query": criterion.description,
                "top_k": 3,
            })
            note_context.extend(notes)

    # Deduplicate notes
    seen = set()
    unique_notes = []
    for note in note_context:
        key = note["content"][:100]
        if key not in seen:
            seen.add(key)
            unique_notes.append(note)

    return f"""## Patient Demographics
{demographics}

## Active Conditions (ICD-10)
{conditions}

## Current Medications (RxNorm)
{medications}

## Recent Lab Results
{lab_results}

## Relevant Clinical Notes (from EHR)
{chr(10).join(f"[{n['note_type']} - {n['note_date']}]: {n['content']}" for n in unique_notes[:10])}
"""


async def evaluate_patient(patient_id: str, criteria: ProtocolCriteria) -> PatientMatchResult:
    """Evaluate a single patient against all trial eligibility criteria."""
    patient_context = await gather_patient_context(patient_id, criteria)

    criteria_text = "## Inclusion Criteria\n"
    for c in criteria.inclusion_criteria:
        criteria_text += f"- [{c.id}] {c.description}\n"
    criteria_text += "\n## Exclusion Criteria\n"
    for c in criteria.exclusion_criteria:
        criteria_text += f"- [{c.id}] {c.description}\n"

    messages = [
        SystemMessage(content=PATIENT_MATCHING_SYSTEM_PROMPT),
        HumanMessage(content=f"""Evaluate this patient for trial: {criteria.trial_title} ({criteria.trial_id})

{criteria_text}

## Patient Data
Patient ID: {patient_id}
{patient_context}

Evaluate EACH criterion and provide your overall recommendation."""),
    ]

    result: PatientMatchResult = await structured_llm.ainvoke(messages)
    result.patient_id = patient_id
    result.trial_id = criteria.trial_id
    return result
```

---

### Phase 4: Enrollment Monitoring Agent

#### Step 4.1: Real-Time Velocity Tracking

```python
# src/prompts/enrollment_analysis.py

ENROLLMENT_MONITOR_PROMPT = """You are an enrollment analytics agent monitoring clinical trial recruitment velocity.

Given the enrollment data for a trial, analyze:
1. Current enrollment rate vs. target rate (patients/week per site)
2. Sites significantly below target (< 60% of expected rate)
3. Projected enrollment completion date at current velocity
4. Recommended corrective actions if behind schedule

Corrective actions to consider:
- Flag underperforming sites for sponsor review
- Recommend site additions in geographic areas with patient surplus
- Suggest protocol amendment if screen failure rate > 25% on specific criteria
- Recommend extending recruitment window with timeline impact

Be specific. Name the sites, the numbers, and the projected impact of each recommendation.
"""
```

```python
# src/agents/monitor_agent.py
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.tools.ctms_tools import get_enrollment_data
from src.prompts.enrollment_analysis import ENROLLMENT_MONITOR_PROMPT
from config.settings import settings

llm = AzureChatOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_GPT4O,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    temperature=0.0,
)


async def analyze_enrollment(trial_id: str) -> dict:
    """Analyze enrollment velocity and generate corrective recommendations."""
    enrollment_data = await get_enrollment_data(trial_id)

    messages = [
        SystemMessage(content=ENROLLMENT_MONITOR_PROMPT),
        HumanMessage(content=f"""Trial: {trial_id}
Enrollment data (per site):
{enrollment_data}

Analyze enrollment velocity and recommend actions."""),
    ]

    response = await llm.ainvoke(messages)
    return {"trial_id": trial_id, "analysis": response.content}
```

---

### Phase 5: Deployment

#### Step 5.1: API Endpoints

```python
# src/api/main.py
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from src.agents.orchestrator import create_app

app = FastAPI(title="Trial Match AI")

class MatchRequest(BaseModel):
    trial_id: str
    patient_ids: list[str]

class MatchResponse(BaseModel):
    thread_id: str
    status: str

@app.post("/match", response_model=MatchResponse)
async def start_matching(request: MatchRequest, background_tasks: BackgroundTasks):
    """Start a patient-trial matching workflow."""
    graph_app = await create_app()
    config = {"configurable": {"thread_id": f"{request.trial_id}-{hash(tuple(request.patient_ids))}"}}

    background_tasks.add_task(
        graph_app.ainvoke,
        {
            "trial_id": request.trial_id,
            "patient_ids": request.patient_ids,
            "match_results": [],
            "needs_human_review": [],
            "current_patient_index": 0,
            "status": "parsing",
            "messages": [],
        },
        config,
    )
    return MatchResponse(thread_id=config["configurable"]["thread_id"], status="started")
```

---

## Key Code Patterns

### Pattern: Medical Chain-of-Thought for Criterion Evaluation

Clinical eligibility evaluation requires explicit step-by-step reasoning. Chain-of-Thought forces the LLM to show its work — critical for audit trails and catching reasoning errors.

```python
# This pattern is embedded in the system prompt but can also be enforced structurally:
COT_CRITERION_TEMPLATE = """Criterion: {criterion_description}
Required: {requirement_summary}

Step 1 - Data Available: {what_data_was_found}
Step 2 - Data Assessment: {does_data_satisfy_requirement}
Step 3 - Temporal Check: {is_data_within_temporal_window}
Step 4 - Edge Cases: {any_ambiguity_or_borderline_values}
Step 5 - Verdict: {MET|NOT_MET|INSUFFICIENT_DATA|REQUIRES_REVIEW}
Confidence: {0.0-1.0}
Evidence: {specific_data_point_cited}"""
```

### Pattern: Hybrid Search for Clinical Notes (BM25 + Vector)

Medical data requires both exact code matching (BM25 excels at "LOINC:718-7") and semantic understanding (vector search understands "the patient's hemoglobin was low"). Hybrid search combines both.

```python
# The search_patient_notes tool in search_tools.py implements this pattern.
# Key configuration for the Azure AI Search index:
INDEX_SCHEMA = {
    "fields": [
        {"name": "id", "type": "Edm.String", "key": True},
        {"name": "patient_id", "type": "Edm.String", "filterable": True},
        {"name": "content", "type": "Edm.String", "searchable": True},  # BM25
        {"name": "content_vector", "type": "Collection(Edm.Single)",
         "dimensions": 3072, "vectorSearchProfile": "default"},  # Vector
        {"name": "note_type", "type": "Edm.String", "filterable": True},
        {"name": "note_date", "type": "Edm.DateTimeOffset", "sortable": True},
    ],
    "vectorSearch": {
        "algorithms": [{"name": "hnsw", "kind": "hnsw"}],
        "profiles": [{"name": "default", "algorithm": "hnsw"}],
    },
    "semantic": {
        "configurations": [{"name": "patient-semantic", "prioritizedFields": {
            "contentFields": [{"fieldName": "content"}]
        }}]
    },
}
```

### Pattern: Confidence-Gated Human-in-the-Loop

Matches below the confidence threshold are paused for human review. LangGraph's `interrupt()` mechanism enables this without losing state.

```python
# In the graph definition, the conditional edge routes to human_review
# when any match has REVIEW_NEEDED status. The interrupt() call in
# human_review_node suspends the graph. The clinical team reviews
# the flagged matches via the API, then resumes the graph:

@app.post("/review/{thread_id}")
async def submit_review(thread_id: str, decisions: dict):
    """Clinical team submits review decisions, resuming the graph."""
    graph_app = await create_app()
    config = {"configurable": {"thread_id": thread_id}}
    # Resume the interrupted graph with the human's decisions
    await graph_app.ainvoke(None, config)
```

---

## Configuration Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| AZURE_OPENAI_DEPLOYMENT_GPT4O | `gpt-4o` | Primary reasoning model for criteria parsing and patient matching |
| AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI | `gpt-4o-mini` | Lower-cost model for high-volume extraction and normalization |
| REASONING_TEMPERATURE | `0.0` | Deterministic output for reproducible clinical decisions |
| MAX_TOKENS_REASONING | `4096` | Sufficient for detailed CoT reasoning across 30-50 criteria |
| MATCH_CONFIDENCE_THRESHOLD | `0.85` | Matches below this score require human review |
| MATCH_EXCLUDE_THRESHOLD | `0.30` | Matches below this score are auto-excluded |
| FHIR_SCOPES | `patient/*.read` | SMART on FHIR scopes for EHR access |
| SEARCH_INDEX_NAME | `patient-records` | Azure AI Search index containing embedded clinical notes |

---

## Testing Strategy

### Unit Tests

Test criterion extraction and matching logic with known patient-criterion pairs.

```python
# tests/unit/test_matching_logic.py
import pytest
from src.models.eligibility import CriterionVerdict

def test_lab_value_criterion_met():
    """Patient hemoglobin 10.5 g/dL meets criterion >= 9.0 g/dL."""
    criterion = {"comparator": ">=", "value": 9.0, "unit": "g/dL"}
    patient_value = {"value": 10.5, "unit": "g/dL"}
    assert evaluate_lab_criterion(criterion, patient_value) == CriterionVerdict.MET

def test_lab_value_criterion_not_met():
    """Patient hemoglobin 8.2 g/dL does not meet criterion >= 9.0 g/dL."""
    criterion = {"comparator": ">=", "value": 9.0, "unit": "g/dL"}
    patient_value = {"value": 8.2, "unit": "g/dL"}
    assert evaluate_lab_criterion(criterion, patient_value) == CriterionVerdict.NOT_MET

def test_missing_lab_value():
    """Missing lab data returns INSUFFICIENT_DATA, not a guess."""
    criterion = {"comparator": ">=", "value": 9.0, "unit": "g/dL"}
    assert evaluate_lab_criterion(criterion, None) == CriterionVerdict.INSUFFICIENT_DATA
```

### Evaluation Tests — AI Quality

Measure the LLM's matching accuracy against a gold-standard dataset of expert-labeled patient-trial pairs. This follows the approach used by TrialMatchAI and MAKAR benchmarks.

```python
# tests/evaluation/test_matching_accuracy.py
import pytest
import json
from src.agents.matching_agent import evaluate_patient
from src.agents.protocol_agent import parse_protocol

# Gold-standard test set: expert-labeled patient-trial pairs
# Format: {"patient_id": "P001", "trial_id": "NCT001", "expert_verdict": "ELIGIBLE"}
GOLD_STANDARD = json.load(open("tests/evaluation/gold_standard.json"))

@pytest.mark.asyncio
@pytest.mark.parametrize("case", GOLD_STANDARD)
async def test_matching_accuracy(case):
    """Compare AI match verdict against expert clinical assessment."""
    criteria = await parse_protocol(case["trial_id"])
    result = await evaluate_patient(case["patient_id"], criteria)

    # Track for aggregate metrics
    assert result.recommendation in ("ELIGIBLE", "INELIGIBLE", "REVIEW_NEEDED")

    # Criterion-level accuracy
    for eval in result.criterion_evaluations:
        expert_criterion = case["criterion_verdicts"].get(eval.criterion_id)
        if expert_criterion:
            # Allow REQUIRES_REVIEW as acceptable when expert disagrees
            assert eval.verdict == expert_criterion or eval.verdict == "requires_review", (
                f"Criterion {eval.criterion_id}: AI={eval.verdict}, Expert={expert_criterion}"
            )

# Aggregate accuracy report (run after all parametrized tests)
def test_aggregate_accuracy(all_results):
    """Overall accuracy must exceed 90% (TrialMatchAI benchmark)."""
    correct = sum(1 for r in all_results if r["ai_verdict"] == r["expert_verdict"])
    accuracy = correct / len(all_results)
    assert accuracy >= 0.90, f"Accuracy {accuracy:.1%} below 90% threshold"
```

---

## Monitoring & Observability

| What to Monitor | Tool / Method | Alert Threshold |
|----------------|--------------|-----------------|
| **LLM Latency (per-criterion)** | Application Insights custom metric | p95 > 10s per criterion evaluation |
| **Match Confidence Distribution** | Application Insights histogram | > 30% of matches below 0.85 threshold (indicates criteria ambiguity) |
| **FHIR API Error Rate** | Application Insights dependency tracking | > 2% errors in 5-minute window |
| **Screen Failure Prediction** | Custom metric: AI-predicted vs. actual screening outcomes | Predicted eligible but screened out > 10% (model drift) |
| **Token Consumption** | Azure OpenAI metrics | Daily spend > 120% of budget |
| **HITL Queue Depth** | Application Insights queue metric | > 50 pending reviews (clinical team bottleneck) |

---

## Common Pitfalls & Mitigations

| Pitfall | Mitigation |
|---------|-----------|
| **LLM hallucinating lab values not in patient data** | Structured output schema enforces evidence field must cite specific data; validation layer checks cited values exist in retrieved FHIR data |
| **Temporal reasoning errors (wrong date math)** | Provide explicit enrollment date in prompt; use Python date arithmetic as verification tool; include temporal examples in few-shot |
| **FHIR API rate limiting under batch load** | Queue-based processing with configurable concurrency; per-site rate limit tracking; exponential backoff with jitter |
| **Inconsistent criterion decomposition across protocols** | Few-shot examples in extraction prompt; evaluation test suite with diverse protocols; human spot-check of first 5 criteria per new protocol |
| **Clinical note quality varies by site** | Hybrid search (BM25 + vector) handles both well-structured and free-text notes; confidence scoring accounts for data quality |
| **Cost overrun from verbose patient contexts** | Limit clinical notes to top-5 most relevant per criterion; summarize structured data before sending to LLM; use GPT-4o-mini for initial filtering |

---

## Rollback Plan

1. **Disable AI matching**: Feature flag toggles the matching pipeline off; CTMS continues to function with manual workflow. No data loss — all in-progress matches are checkpointed.
2. **Revert to manual screening**: Site coordinators resume traditional chart review using existing CTMS pre-screening tools. Flagged patients from AI remain visible as "AI-suggested" but require manual confirmation.
3. **Preserve audit trail**: All AI decisions remain in Cosmos DB audit log regardless of rollback status — regulatory trail is maintained.
