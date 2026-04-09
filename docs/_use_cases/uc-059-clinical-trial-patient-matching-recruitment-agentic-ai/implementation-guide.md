---
layout: use-case-detail
title: "Implementation Guide — UC-059: Autonomous Clinical Trial Patient Matching and Recruitment with Agentic AI"
uc_id: "UC-059"
uc_title: "Autonomous Clinical Trial Patient Matching and Recruitment with Agentic AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
status: "detailed"
slug: "uc-059-clinical-trial-patient-matching-recruitment-agentic-ai"
permalink: /use-cases/uc-059-clinical-trial-patient-matching-recruitment-agentic-ai/implementation-guide/
---

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
│   ├── agents/
│   │   ├── orchestrator.py      # LangGraph StateGraph definition
│   │   ├── protocol_agent.py    # Protocol criteria extraction agent
│   │   ├── matching_agent.py    # Patient-trial matching agent (RAG + CoT)
│   │   ├── site_agent.py        # Site optimization agent
│   │   └── monitor_agent.py     # Enrollment monitoring agent
│   ├── tools/
│   │   ├── fhir_tools.py        # FHIR R4 patient data retrieval
│   │   ├── ctgov_tools.py       # ClinicalTrials.gov API queries
│   │   ├── search_tools.py      # Azure AI Search vector/hybrid queries
│   │   ├── ctms_tools.py        # CTMS read/write operations
│   │   └── document_tools.py    # PDF extraction via Document Intelligence
│   ├── prompts/
│   │   ├── criteria_extraction.py
│   │   ├── patient_matching.py
│   │   ├── site_scoring.py
│   │   └── enrollment_analysis.py
│   ├── models/
│   │   ├── eligibility.py       # Pydantic models for eligibility criteria
│   │   ├── match_result.py      # Match scoring output schemas
│   │   └── patient.py           # Normalized patient data model
│   └── api/
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
    azure-ai-documentintelligence fastapi uvicorn
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

    # Azure AI Search
    SEARCH_ENDPOINT: str
    SEARCH_INDEX_NAME: str = "patient-records"
    SEARCH_SEMANTIC_CONFIG: str = "patient-semantic"

    # Matching thresholds
    MATCH_CONFIDENCE_THRESHOLD: float = 0.85  # Below this -> HITL review
    MATCH_EXCLUDE_THRESHOLD: float = 0.30     # Below this -> auto-exclude

    class Config:
        env_file = ".env"

settings = Settings()
```

---

### Phase 2: Data Models and LLM Connection

#### Step 2.1: Eligibility Models

Define Pydantic models that enforce the structure of eligibility criteria and match results. This prevents hallucination and ensures all LLM outputs are schema-valid.

```python
# src/models/eligibility.py
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class CriterionVerdict(str, Enum):
    MET = "met"
    NOT_MET = "not_met"
    INSUFFICIENT_DATA = "insufficient_data"
    REQUIRES_REVIEW = "requires_review"

class CriterionEvaluation(BaseModel):
    criterion_id: str
    verdict: CriterionVerdict
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str
    reasoning: str

class PatientMatchResult(BaseModel):
    patient_id: str
    trial_id: str
    overall_score: float = Field(ge=0.0, le=1.0)
    criterion_evaluations: list[CriterionEvaluation]
    recommendation: str  # ELIGIBLE, INELIGIBLE, or REVIEW_NEEDED
    summary: str
```

#### Step 2.2: LangGraph Agent Orchestrator

```python
# src/agents/orchestrator.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.models.eligibility import PatientMatchResult

builder = StateGraph(dict)

# Add agent nodes
builder.add_node("protocol_agent", protocol_criteria_node)
builder.add_node("matching_agent", patient_matching_node)
builder.add_node("site_agent", site_optimization_node)
builder.add_node("monitor_agent", enrollment_monitor_node)

# Add routing logic
builder.add_edge(START, "protocol_agent")
builder.add_edge("protocol_agent", "matching_agent")
builder.add_conditional_edges("matching_agent", route_by_confidence)
builder.add_edge("site_agent", "monitor_agent")
builder.add_edge("monitor_agent", END)

graph = builder.compile(checkpointer=MemorySaver())
```

---

### Phase 3: FHIR and Azure Integration

#### Step 3.1: FHIR Patient Data Retrieval

```python
# src/tools/fhir_tools.py
from smart_client import SMARTClient
from fhir.resources.patient import Patient
from typing import Optional

async def get_patient_data(patient_id: str, fhir_client: SMARTClient) -> dict:
    """Retrieve patient demographics, conditions, observations, medications."""
    
    patient = fhir_client.resources('Patient').read(patient_id)
    conditions = fhir_client.resources('Condition').search(patient=patient_id).get()
    observations = fhir_client.resources('Observation').search(subject=patient_id).get()
    medications = fhir_client.resources('MedicationRequest').search(subject=patient_id).get()
    
    return {
        "patient": patient,
        "conditions": conditions,
        "observations": observations,
        "medications": medications
    }
```

#### Step 3.2: Azure AI Search Hybrid Query

```python
# src/tools/search_tools.py
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

async def hybrid_search_patient_records(
    query: str,
    embeddings: list[float],
    search_client: SearchClient,
    top_k: int = 10
) -> list:
    """Hybrid search: BM25 (lexical) + vector (semantic) search."""
    
    vector_query = VectorizedQuery(vector=embeddings, k_nearest_neighbors=top_k, fields="content_vector")
    
    results = search_client.search(
        search_text=query,
        vector_queries=[vector_query],
        select=["id", "patient_name", "clinical_notes", "@search.score"]
    )
    
    return list(results)
```

---

### Phase 4: Testing and Evaluation

#### Step 4.1: Unit Tests

```python
# tests/unit/test_eligibility.py
from src.models.eligibility import PatientMatchResult, CriterionVerdict

def test_match_result_schema():
    result = PatientMatchResult(
        patient_id="P001",
        trial_id="NCT123",
        overall_score=0.92,
        criterion_evaluations=[],
        recommendation="ELIGIBLE",
        summary="Patient meets all criteria"
    )
    assert result.overall_score >= 0.0 and result.overall_score <= 1.0
```

#### Step 4.2: Integration Tests

```python
# tests/integration/test_fhir_integration.py
@pytest.mark.asyncio
async def test_fhir_patient_retrieval(fhir_client):
    patient_data = await get_patient_data("test-patient-id", fhir_client)
    assert patient_data["patient"] is not None
    assert "conditions" in patient_data
    assert "medications" in patient_data
```

---

## Deployment

### Local Development

```bash
docker-compose up -d  # Starts PostgreSQL, Cosmos emulator, search service
uvicorn src.api.main:app --reload
```

### Kubernetes Deployment on AKS

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trial-match-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: trial-match-ai
  template:
    metadata:
      labels:
        app: trial-match-ai
    spec:
      containers:
      - name: trial-match-ai
        image: trial-match-ai:latest
        env:
        - name: AZURE_OPENAI_ENDPOINT
          valueFrom:
            secretKeyRef:
              name: azure-creds
              key: openai-endpoint
        ports:
        - containerPort: 8000
```

---

## Monitoring & Observability

| Metric | Tool | Alert Threshold |
|--------|------|-----------------|
| **Protocol parsing errors** | Application Insights | >1% of protocols in 1 hour |
| **Patient match latency (p99)** | Application Insights | >90 seconds |
| **FHIR API errors** | Network logs | >5% request failure rate |
| **Match confidence scores trending low** | Custom alert | Average < 0.70 over 24 hours |
| **Enrollment velocity vs. plan** | Dashboard | Site enrollment < 80% of target for 7 consecutive days |

---

## Common Pitfalls

| Pitfall | Mitigation |
|---------|-----------|
| Not starting with well-structured FHIR data | Validate FHIR compliance; may need data normalization layer |
| Using free-text LLM outputs without schema | Always use structured output / Pydantic models |
| Ignoring protocol ambiguity | Flag ambiguous criteria at extraction; auto-route to review |
| Not integrating into existing CTMS workflow | Embed match results directly in coordinator tools; show integration value early |
| Under-scoping to single institution | Build with multi-site EHR federation in mind from day one |
