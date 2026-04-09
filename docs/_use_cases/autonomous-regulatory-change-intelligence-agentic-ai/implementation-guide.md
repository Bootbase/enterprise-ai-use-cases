---
layout: use-case-detail
title: "Implementation Guide — UC-041: Autonomous Regulatory Change Intelligence and Compliance Orchestration with Agentic AI"
uc_id: "UC-041"
uc_title: "Autonomous Regulatory Change Intelligence and Compliance Orchestration with Agentic AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Knowledge Management"
status: "detailed"
slug: "autonomous-regulatory-change-intelligence-agentic-ai"
permalink: /use-cases/autonomous-regulatory-change-intelligence-agentic-ai/implementation-guide/
---

## Prerequisites

| Prerequisite | Detail |
|--------------|--------|
| **Azure Subscription** | Azure OpenAI (GPT-4o, GPT-4o-mini, text-embedding-3-large), Azure AI Search (S1+), Azure Service Bus, Azure Blob Storage, Azure SQL Database, Azure Container Apps or AKS |
| **API Keys / Access** | Azure OpenAI endpoint with GPT-4o and GPT-4o-mini deployments; Azure AI Search admin key; regulatory feed API keys (CUBE, Wolters Kluwer, or equivalent) |
| **Existing Systems** | GRC platform (ServiceNow GRC, RSA Archer, or MetricStream) with REST API access; policy management system (SharePoint or equivalent) |
| **Dev Environment** | Python 3.11+, `langgraph`, `langchain-openai`, `azure-search-documents`, `pydantic`, `httpx` |
| **Permissions** | Managed Identity with Cognitive Services OpenAI User role; Azure AI Search contributor; Service Bus sender/receiver; GRC platform API credentials (service account with read/write to obligation register) |

## Project Structure

```
reg-change-intelligence/
├── src/
│   ├── agents/              # Agent definitions and orchestration
│   │   ├── scanner.py       # Horizon Scanner Agent
│   │   ├── extractor.py     # Obligation Extraction Agent
│   │   ├── assessor.py      # Applicability Assessment Agent
│   │   ├── gap_analyzer.py  # Gap Analysis Agent
│   │   ├── policy_drafter.py # Policy Drafting Agent
│   │   └── pipeline.py      # LangGraph pipeline orchestration
│   ├── tools/               # Tool/function definitions for agents
│   │   ├── regulatory_feed.py    # Regulatory source connectors
│   │   ├── obligation_store.py   # Obligation register CRUD
│   │   ├── knowledge_base.py     # Azure AI Search RAG tools
│   │   ├── grc_connector.py      # GRC platform integration
│   │   └── policy_store.py       # Policy document retrieval
│   ├── prompts/             # System prompts and prompt templates
│   │   ├── extraction.py    # Obligation extraction prompts
│   │   ├── assessment.py    # Applicability assessment prompts
│   │   └── drafting.py      # Policy drafting prompts
│   ├── models/              # Data models and schemas
│   │   ├── obligation.py    # Obligation Pydantic models
│   │   ├── assessment.py    # Assessment result models
│   │   └── pipeline_state.py # LangGraph state definition
│   └── api/                 # API endpoints
│       └── routes.py        # FastAPI endpoints for human review
├── config/
│   └── settings.py          # Configuration (env vars, thresholds)
├── tests/
│   ├── test_extraction.py   # Extraction accuracy tests
│   ├── test_assessment.py   # Applicability assessment tests
│   └── eval/                # Gold-set evaluation suites
│       └── obligations_gold.json
└── pyproject.toml
```

## Step-by-Step Implementation

### Phase 1: Foundation

#### Step 1.1: Core Dependencies

```bash
pip install langgraph langchain-openai azure-search-documents azure-identity \
    azure-servicebus pydantic httpx fastapi uvicorn
```

#### Step 1.2: Data Models

The obligation model is the central data contract. Every agent reads or writes obligations in this schema.

```python
# src/models/obligation.py
from pydantic import BaseModel, Field
from enum import Enum
from datetime import date

class DeonticType(str, Enum):
    MUST = "must"
    SHALL = "shall"
    MAY = "may"
    MUST_NOT = "must_not"
    SHOULD = "should"

class Obligation(BaseModel):
    """A discrete regulatory obligation extracted from regulatory text."""
    id: str = Field(description="Unique obligation identifier")
    obligation_text: str = Field(description="Verbatim text of the obligation")
    deontic_type: DeonticType = Field(description="Modal type: must/shall/may/must_not/should")
    addressee: str = Field(description="Who the obligation applies to")
    predicate: str = Field(description="What the addressee must do or not do")
    conditions: list[str] = Field(default_factory=list, description="Conditions under which the obligation applies")
    effective_date: date | None = Field(default=None, description="When the obligation takes effect")
    cross_references: list[str] = Field(default_factory=list, description="Referenced articles/regulations")
    article_reference: str = Field(description="Source article/section number")
    source_regulation: str = Field(description="Title and identifier of the source regulation")
    jurisdiction: str = Field(description="Jurisdiction that issued the regulation")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence score")
    ambiguity_flag: bool = Field(default=False, description="True if deontic classification is uncertain")

class ApplicabilityResult(BaseModel):
    """Result of assessing whether an obligation applies to the firm."""
    obligation_id: str
    applicable: bool
    reasoning: str
    affected_entities: list[str] = Field(default_factory=list)
    affected_jurisdictions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
```

#### Step 1.3: Azure AI Search Setup

Initialize the regulatory knowledge base:

```python
# src/tools/knowledge_base.py
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex, SearchField, SearchFieldDataType

def create_regulatory_index(index_name: str) -> SearchIndex:
    """Define the schema for regulatory document storage and retrieval."""
    fields = [
        SearchField(name="id", type=SearchFieldDataType.String, key=True),
        SearchField(name="regulation_title", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="jurisdiction", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="document_type", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="publication_date", type=SearchFieldDataType.DateTimeOffset, filterable=True),
        SearchField(name="text_content", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="embedding", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), 
                    searchable=True, vector_search_dimensions=1536),
    ]
    
    return SearchIndex(name=index_name, fields=fields)
```

### Phase 2: Agent Implementation

#### Step 2.1: Horizon Scanner Agent

```python
# src/agents/scanner.py
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from datetime import datetime

class HorizonScannerState(TypedDict):
    """State for the horizon scanner agent."""
    feed_document: dict
    classification: Optional[str]
    confidence: float
    requires_processing: bool

async def classify_regulatory_document(state: HorizonScannerState) -> HorizonScannerState:
    """Classify a regulatory document by type, jurisdiction, urgency."""
    client = ChatOpenAI(model="gpt-4o-mini")
    
    prompt = f"""Classify this regulatory publication:
    
Title: {state['feed_document']['title']}
Source: {state['feed_document']['source']}
Summary: {state['feed_document']['summary']}

Determine:
- document_type: legislation | guidance | enforcement | consultation | other
- jurisdiction: [country/region]
- topic_areas: [list of regulatory domains]
- urgency: routine | elevated | urgent
- applicability_score: 0.0-1.0 probability this applies to financial services

Return JSON with classification and confidence score."""
    
    response = await client.ainvoke([
        {"role": "user", "content": prompt}
    ])
    
    # Parse response and update state
    state['classification'] = response.content
    state['requires_processing'] = state['confidence'] > 0.6
    
    return state
```

#### Step 2.2: Obligation Extraction Agent

```python
# src/agents/extractor.py
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
import json

class ExtractedObligation(BaseModel):
    """Schema for extracted obligations from regulatory text."""
    obligation_text: str
    deontic_type: str  # must | shall | may | must_not | should
    addressee: str
    predicate: str
    conditions: list[str]
    effective_date: Optional[str]
    cross_references: list[str]
    article_reference: str
    confidence: float

async def extract_obligations(regulation_text: str, max_tokens: int = 8000) -> list[ExtractedObligation]:
    """Extract discrete obligations from regulatory text."""
    client = ChatOpenAI(model="gpt-4o")
    
    # Chunk long regulations by article to stay within context
    chunks = chunk_by_article(regulation_text, max_tokens)
    all_obligations = []
    
    for chunk in chunks:
        prompt = f"""Extract all regulatory obligations from this text.

{chunk}

For each obligation, identify:
- The exact text (verbatim)
- Deontic type: must/shall/may/must_not/should
- Addressee (who it applies to)
- What they must/must not do
- Conditions and effective date
- Cross-references to other articles
- Confidence score (0.0-1.0)

Return as JSON array of obligations."""
    
        response = await client.ainvoke([
            {"role": "user", "content": prompt}
        ])
        
        # Parse structured output
        obligations = json.loads(response.content)
        all_obligations.extend([ExtractedObligation(**o) for o in obligations])
    
    return all_obligations
```

#### Step 2.3: Applicability Assessment Agent

```python
# src/agents/assessor.py
from src.models.obligation import ApplicabilityResult

async def assess_applicability(
    obligation: Obligation,
    regulatory_perimeter: dict,
    rag_context: str
) -> ApplicabilityResult:
    """Assess whether an obligation applies to the firm."""
    client = ChatOpenAI(model="gpt-4o")
    
    prompt = f"""Assess whether this obligation applies to our firm.

Obligation:
{obligation.obligation_text}

Addressee Definition: {obligation.addressee}
Deontic Type: {obligation.deontic_type}

Our Regulatory Perimeter:
- Licensed Activities: {regulatory_perimeter.get('activities', [])}
- Entity Types: {regulatory_perimeter.get('entity_types', [])}
- Jurisdictions: {regulatory_perimeter.get('jurisdictions', [])}
- Product Lines: {regulatory_perimeter.get('product_lines', [])}

Similar Past Assessments (from RAG):
{rag_context}

Determine:
1. Is the obligation applicable? (yes/no/partial)
2. If partial, which entities or jurisdictions?
3. Confidence score (0.0-1.0)
4. Reasoning with specific references to our perimeter

Return as JSON with structured assessment."""
    
    response = await client.ainvoke([
        {"role": "user", "content": prompt}
    ])
    
    assessment_data = json.loads(response.content)
    return ApplicabilityResult(**assessment_data)
```

### Phase 3: Orchestration with LangGraph

#### Step 3.1: Pipeline State Definition

```python
# src/models/pipeline_state.py
from typing import TypedDict, Optional
from src.models.obligation import Obligation, ApplicabilityResult

class RegulatoryChangePipelineState(TypedDict):
    """Complete state for a regulatory change processing pipeline."""
    regulation_id: str
    publication_date: str
    source_regulation: str
    jurisdiction: str
    raw_text: str
    classification: dict
    extracted_obligations: list[Obligation]
    applicability_assessments: list[ApplicabilityResult]
    gap_analysis: dict
    policy_redlines: list[dict]
    approval_status: str  # pending | approved | rejected | activated
    audit_trail: list[dict]
    human_review_queue: list[str]
```

#### Step 3.2: LangGraph Pipeline

```python
# src/agents/pipeline.py
from langgraph.graph import StateGraph, END
from typing import Literal

def create_regulatory_change_pipeline() -> StateGraph:
    """Build the multi-agent regulatory change pipeline."""
    
    graph = StateGraph(RegulatoryChangePipelineState)
    
    # 1. Classification node
    async def classify_node(state):
        classification = await classify_regulatory_document(state['raw_text'])
        state['classification'] = classification
        if not classification.get('requires_processing'):
            return {"next_step": "archive"}
        return {"next_step": "extraction"}
    
    graph.add_node("classify", classify_node)
    
    # 2. Obligation extraction node
    async def extraction_node(state):
        obligations = await extract_obligations(state['raw_text'])
        state['extracted_obligations'] = obligations
        return {"next_step": "assess_applicability"}
    
    graph.add_node("extract", extraction_node)
    
    # 3. Applicability assessment node
    async def applicability_node(state):
        perimeter = await load_regulatory_perimeter()
        assessments = []
        for obligation in state['extracted_obligations']:
            # RAG retrieval of similar past assessments
            rag_context = await retrieve_similar_assessments(obligation)
            assessment = await assess_applicability(obligation, perimeter, rag_context)
            assessments.append(assessment)
            
            # Low-confidence assessments escalate to human review
            if assessment.confidence < 0.80:
                state['human_review_queue'].append(obligation.id)
        
        state['applicability_assessments'] = assessments
        return {"next_step": "gap_analysis"}
    
    graph.add_node("assess", applicability_node)
    
    # 4. Gap analysis node
    async def gap_analysis_node(state):
        applicable_obligations = [a for a in state['applicability_assessments'] if a.applicable]
        gap_analysis = await analyze_gaps(applicable_obligations)
        state['gap_analysis'] = gap_analysis
        
        if gap_analysis.get('gaps_found'):
            return {"next_step": "draft_policy"}
        else:
            return {"next_step": "log_compliance"}
    
    graph.add_node("gap_analysis", gap_analysis_node)
    
    # 5. Policy drafting node
    async def policy_drafting_node(state):
        gaps = state['gap_analysis'].get('gaps', [])
        redlines = []
        for gap in gaps:
            redline = await draft_policy_redline(gap, state)
            redlines.append(redline)
            # All policy changes require human review
            state['human_review_queue'].append(gap['id'])
        
        state['policy_redlines'] = redlines
        state['approval_status'] = 'pending'
        return {"next_step": "workflow_routing"}
    
    graph.add_node("draft_policy", policy_drafting_node)
    
    # 6. Workflow orchestration node
    async def workflow_node(state):
        # Route through approval chain: Legal → Business → Compliance Committee
        workflow_task = await create_workflow_task(state)
        state['audit_trail'].append({
            "timestamp": datetime.now().isoformat(),
            "action": "routed_for_approval",
            "task_id": workflow_task['id']
        })
        return {"next_step": "human_review"}
    
    graph.add_node("workflow", workflow_node)
    
    # 7. Human review node
    async def human_review_node(state):
        # Interrupt: wait for human approval
        return {"next_step": "check_approval"}
    
    graph.add_node("human_review", human_review_node)
    
    # 8. Approval check and evidence assembly
    async def activate_node(state):
        # Publish policy updates
        for redline in state['policy_redlines']:
            await publish_policy_update(redline)
        
        # Trigger training
        await trigger_training(state['policy_redlines'])
        
        # Assemble audit evidence
        evidence = await assemble_audit_evidence(state)
        state['audit_trail'].extend(evidence)
        state['approval_status'] = 'activated'
        
        return {"next_step": "end"}
    
    graph.add_node("activate", activate_node)
    
    graph.add_node("archive", END)
    graph.add_node("log_compliance", END)
    
    # Conditional edges
    graph.add_conditional_edges(
        "classify",
        lambda x: x.get("next_step", "extract"),
        {"archive": "archive", "extraction": "extract"}
    )
    
    graph.add_edge("extract", "assess")
    graph.add_edge("assess", "gap_analysis")
    graph.add_conditional_edges(
        "gap_analysis",
        lambda x: x.get("next_step"),
        {"draft_policy": "draft_policy", "log_compliance": "log_compliance"}
    )
    graph.add_edge("draft_policy", "workflow")
    graph.add_edge("workflow", "human_review")
    graph.add_edge("human_review", "activate")
    
    # Set start node
    graph.set_entry_point("classify")
    
    return graph.compile()
```

### Phase 4: API & Human Review Interface

```python
# src/api/routes.py
from fastapi import FastAPI, HTTPException
from src.api.routes import router

app = FastAPI(title="Regulatory Change Intelligence")

@app.get("/review-queue")
async def get_review_queue():
    """Get list of items requiring human review."""
    queue = await load_human_review_queue()
    return {"items": queue, "count": len(queue)}

@app.post("/assess/{obligation_id}/approve")
async def approve_assessment(obligation_id: str, feedback: str = ""):
    """Compliance officer approves an assessment."""
    assessment = await load_assessment(obligation_id)
    assessment.approved = True
    assessment.reviewer_feedback = feedback
    await save_assessment(assessment)
    return {"status": "approved", "obligation_id": obligation_id}

@app.post("/policy/{policy_id}/approve")
async def approve_policy_redline(policy_id: str, comments: str = ""):
    """Compliance officer approves a policy redline."""
    policy = await load_policy_redline(policy_id)
    policy.approved = True
    policy.review_comments = comments
    await save_policy_redline(policy)
    # Resume pipeline with approved redline
    return {"status": "approved", "policy_id": policy_id}

app.include_router(router)
```

### Phase 5: Testing & Evaluation

#### Step 5.1: Create Gold Set

```python
# tests/eval/build_gold_set.py
"""
Build evaluation set of hand-labeled obligations from 10-20 regulations.
Each regulation should be fully annotated with:
- obligation text
- deontic type
- addressee
- predicate
- conditions
- effective date
- cross-references

This gold set is used to measure and improve extraction accuracy.
"""

gold_set = [
    {
        "regulation": "MiFID II / Article 21",
        "obligation_text": "Investment firms shall disclose the costs of the financial instrument...",
        "deontic_type": "shall",
        "addressee": "investment firms",
        "predicate": "disclose costs of financial instruments",
        "conditions": "when providing a financial service",
        "effective_date": "2018-01-03",
        "cross_references": ["MiFID II Implementing Directive Article 32"]
    },
    # ... more gold examples
]
```

#### Step 5.2: Accuracy Evaluation

```python
# tests/test_extraction.py
import json
from src.agents.extractor import extract_obligations

async def test_extraction_accuracy():
    """Measure extraction accuracy against gold set."""
    gold_set = load_gold_set()
    
    for gold_regulation in gold_set:
        extracted = await extract_obligations(gold_regulation['text'])
        
        # Compute precision and recall
        precision = compute_precision(extracted, gold_regulation['obligations'])
        recall = compute_recall(extracted, gold_regulation['obligations'])
        f1 = 2 * (precision * recall) / (precision + recall)
        
        assert precision > 0.85, f"Precision {precision} below threshold"
        assert recall > 0.80, f"Recall {recall} below threshold"
        print(f"{gold_regulation['id']}: P={precision:.2%}, R={recall:.2%}, F1={f1:.2%}")
```

## Deployment Checklist

- [ ] Configure Azure OpenAI deployments (GPT-4o, GPT-4o-mini)
- [ ] Set up Azure AI Search and seed regulatory corpus
- [ ] Create GRC platform service account with appropriate permissions
- [ ] Set up Azure Service Bus for event-driven orchestration
- [ ] Build and test gold set (20 regulations, 500+ obligations)
- [ ] Achieve >= 85% precision on extraction
- [ ] Configure confidence thresholds based on historical data
- [ ] Set up human review queue API and UI
- [ ] Test end-to-end pipeline with sample regulations
- [ ] Configure monitoring and alerting (Application Insights)
- [ ] Document standard operating procedures for compliance team
- [ ] Train compliance officers on platform usage
- [ ] Go-live with phased rollout (one jurisdiction at a time)
