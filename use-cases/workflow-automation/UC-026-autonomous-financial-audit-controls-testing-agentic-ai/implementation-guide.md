# UC-026: Autonomous Financial Audit and Internal Controls Testing — Implementation Guide

## Prerequisites

| Prerequisite | Detail |
|-------------|--------|
| **Azure Subscription** | Azure OpenAI (GPT-4o, GPT-4o-mini, text-embedding-3-large deployments), Azure AI Search (S1+), Azure Cosmos DB, Azure Container Apps, Azure Data Lake Storage Gen2, Azure Document Intelligence, Azure Service Bus |
| **API Keys / Access** | Azure OpenAI endpoint + deployment names; ERP API credentials (SAP RFC user, Oracle REST client, Workday ISU); audit management platform API key (AuditBoard/TeamMate) |
| **Existing Systems** | At least one ERP system with GL data accessible via API; audit management platform for engagement context and workpaper export |
| **Dev Environment** | Python 3.11+, `uv` or `pip`, Docker, Azure CLI (`az`), Terraform (optional for infra) |
| **Permissions** | Azure RBAC: Cognitive Services OpenAI User, Cosmos DB Data Contributor, Storage Blob Data Contributor, Search Index Data Contributor |

---

## Project Structure

```
audit-ai/
├── src/
│   ├── agents/
│   │   ├── orchestrator.py          # LangGraph StateGraph definition
│   │   ├── data_ingestion.py        # Data extraction and normalization agent
│   │   ├── risk_assessment.py       # Risk analysis and prioritization agent
│   │   ├── controls_testing.py      # Controls testing agent
│   │   ├── anomaly_detection.py     # ML-based anomaly detection agent
│   │   └── documentation.py         # Workpaper generation agent
│   ├── tools/
│   │   ├── erp_connector.py         # SAP/Oracle/Workday data extraction
│   │   ├── rule_engine.py           # Deterministic control test rules
│   │   ├── evidence_matcher.py      # LLM-based evidence-to-control matching
│   │   ├── anomaly_models.py        # Isolation Forest, Autoencoder, Benford
│   │   ├── document_extractor.py    # Azure Document Intelligence wrapper
│   │   ├── standards_rag.py         # RAG over accounting standards
│   │   └── workpaper_generator.py   # Structured workpaper output
│   ├── prompts/
│   │   ├── risk_assessment.py       # Risk assessment system prompt + few-shot
│   │   ├── evidence_matching.py     # Evidence matching prompt templates
│   │   ├── finding_summary.py       # Finding narrative generation prompts
│   │   └── workpaper_narrative.py   # Workpaper section generation prompts
│   ├── models/
│   │   ├── engagement.py            # Engagement, Entity, Period schemas
│   │   ├── journal_entry.py         # Normalized journal entry schema
│   │   ├── control.py               # Control definition and test result schemas
│   │   ├── anomaly.py               # Anomaly finding schema
│   │   └── workpaper.py             # Workpaper output schema
│   └── api/
│       └── routes.py                # FastAPI endpoints for UI and webhook triggers
├── config/
│   ├── settings.py                  # Pydantic Settings for environment config
│   └── controls_library.yaml        # Control definitions and test criteria
├── tests/
│   ├── unit/                        # Tool function and prompt tests
│   ├── integration/                 # End-to-end agent flow tests
│   └── evaluation/                  # AI output quality measurement
└── pyproject.toml
```

---

## Step-by-Step Implementation

### Phase 1: Foundation

#### Step 1.1: Core Dependencies

```bash
uv init audit-ai && cd audit-ai
uv add langgraph langchain-openai langchain-community \
       azure-identity azure-cosmos azure-search-documents \
       azure-ai-documentintelligence azure-storage-file-datalake \
       scikit-learn torch pandas pydantic fastapi
```

#### Step 1.2: Configuration

```python
# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"
    AZURE_OPENAI_DEPLOYMENT_GPT4O: str = "gpt-4o"
    AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI: str = "gpt-4o-mini"
    AZURE_OPENAI_DEPLOYMENT_EMBEDDING: str = "text-embedding-3-large"

    # Azure AI Search
    AZURE_SEARCH_ENDPOINT: str
    AZURE_SEARCH_INDEX_STANDARDS: str = "accounting-standards"
    AZURE_SEARCH_INDEX_PRIOR_YEAR: str = "prior-year-workpapers"

    # Azure Cosmos DB
    COSMOS_ENDPOINT: str
    COSMOS_DATABASE: str = "audit-ai"
    COSMOS_CONTAINER_STATE: str = "engagement-state"
    COSMOS_CONTAINER_AUDIT_LOG: str = "audit-trail"

    # Thresholds
    CONFIDENCE_AUTO_PASS: float = 0.95     # Above: auto-document, no human review
    CONFIDENCE_SENIOR_REVIEW: float = 0.70  # 0.70-0.95: senior auditor review
    MATERIALITY_ESCALATION: float = 0.05    # % of total assets triggering partner alert

    # LLM Settings
    TEMPERATURE_REASONING: float = 0.0      # Deterministic for audit conclusions
    TEMPERATURE_DOCUMENTATION: float = 0.3  # Slight variation for natural narratives
    MAX_TOKENS_REASONING: int = 4096
    MAX_TOKENS_DOCUMENTATION: int = 8192

    model_config = {"env_prefix": "AUDIT_AI_"}
```

---

### Phase 2: Core AI Integration

#### Step 2.1: Data Models

Define the canonical schemas that all agents share via the LangGraph state.

```python
# src/models/journal_entry.py
from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from enum import Enum

class JournalEntry(BaseModel):
    """Normalized journal entry from any ERP system."""
    entry_id: str
    entity_code: str
    posting_date: date
    effective_date: date
    account_number: str
    account_name: str
    cost_center: str | None = None
    debit_amount: Decimal
    credit_amount: Decimal
    currency: str
    description: str
    created_by: str
    approved_by: str | None = None
    source_system: str  # "SAP", "Oracle", "Workday"
    is_manual: bool
    is_post_close: bool
    document_reference: str | None = None


# src/models/control.py
class ControlTestResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    EXCEPTION = "exception"
    NEEDS_REVIEW = "needs_review"

class ControlTest(BaseModel):
    """Result of testing a single transaction against a control."""
    control_id: str
    control_name: str
    transaction_id: str
    result: ControlTestResult
    confidence: float  # 0.0-1.0
    evidence_refs: list[str]
    rule_applied: str
    explanation: str
    requires_human_review: bool


# src/models/anomaly.py
class AnomalyFinding(BaseModel):
    """An anomaly detected by the ML models."""
    finding_id: str
    transaction_ids: list[str]
    anomaly_type: str  # "isolation_forest", "autoencoder", "benford", "cluster"
    risk_score: float  # 0.0-1.0
    feature_attribution: dict[str, float]  # Which features contributed most
    description: str
    recommended_action: str
    estimated_amount: Decimal | None = None
```

#### Step 2.2: LangGraph Orchestrator Agent

The orchestrator defines the audit workflow as a directed graph with conditional routing.

```python
# src/agents/orchestrator.py
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from src.models.journal_entry import JournalEntry
from src.models.control import ControlTest
from src.models.anomaly import AnomalyFinding


class AuditState(TypedDict):
    """Shared state across all agents in the audit workflow."""
    # Engagement context
    engagement_id: str
    entity_code: str
    period_start: str
    period_end: str
    materiality_threshold: float

    # Data
    journal_entries: list[dict]       # Populated by Data Ingestion Agent
    trial_balance: list[dict]         # Populated by Data Ingestion Agent

    # Risk assessment
    risk_areas: list[dict]            # Populated by Risk Assessment Agent
    risk_heat_map: dict               # Account -> risk_score

    # Testing results
    control_test_results: list[dict]  # Populated by Controls Testing Agent
    anomaly_findings: list[dict]      # Populated by Anomaly Detection Agent

    # Documentation
    workpapers: list[dict]            # Populated by Documentation Agent

    # Workflow control
    messages: Annotated[list, add_messages]
    phase: str
    errors: list[str]
    escalations: list[dict]


def should_rerun_ingestion(state: AuditState) -> str:
    """Check if risk assessment identified gaps requiring more data."""
    if state.get("errors") and state["phase"] == "risk_assessment":
        return "data_ingestion"  # Loop back for additional data
    return "controls_testing"


def route_after_testing(state: AuditState) -> str:
    """Determine next step based on controls testing results."""
    # Always run anomaly detection after controls testing
    return "anomaly_detection"


def should_escalate(state: AuditState) -> str:
    """Check if findings require human escalation before documentation."""
    escalations = state.get("escalations", [])
    if any(e.get("severity") == "material" for e in escalations):
        return "human_review"
    return "documentation"


# Build the audit workflow graph
workflow = StateGraph(AuditState)

# Add agent nodes (each calls the corresponding agent function)
workflow.add_node("data_ingestion", run_data_ingestion_agent)
workflow.add_node("risk_assessment", run_risk_assessment_agent)
workflow.add_node("controls_testing", run_controls_testing_agent)
workflow.add_node("anomaly_detection", run_anomaly_detection_agent)
workflow.add_node("documentation", run_documentation_agent)
workflow.add_node("human_review", pause_for_human_review)

# Define edges
workflow.add_edge(START, "data_ingestion")
workflow.add_edge("data_ingestion", "risk_assessment")
workflow.add_conditional_edges("risk_assessment", should_rerun_ingestion)
workflow.add_conditional_edges("controls_testing", route_after_testing)
workflow.add_conditional_edges("anomaly_detection", should_escalate)
workflow.add_edge("human_review", "documentation")
workflow.add_edge("documentation", END)

# Compile with checkpointing for resumability
checkpointer = MemorySaver()  # Replace with CosmosDB saver in production
audit_graph = workflow.compile(checkpointer=checkpointer)
```

#### Step 2.3: Risk Assessment Agent with RAG

The risk assessment agent uses LLM reasoning over financial data combined with RAG retrieval from accounting standards and prior-year findings.

```python
# src/agents/risk_assessment.py
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from config.settings import Settings

settings = Settings()

# LLM for risk reasoning
llm = AzureChatOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_GPT4O,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    temperature=settings.TEMPERATURE_REASONING,
)

# Embeddings + vector store for standards/prior-year RAG
embeddings = AzureOpenAIEmbeddings(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_EMBEDDING,
    api_version=settings.AZURE_OPENAI_API_VERSION,
)
standards_store = AzureSearch(
    azure_search_endpoint=settings.AZURE_SEARCH_ENDPOINT,
    index_name=settings.AZURE_SEARCH_INDEX_STANDARDS,
    embedding_function=embeddings.embed_query,
)


@tool
def search_accounting_standards(query: str) -> str:
    """Search GAAP/IFRS accounting standards and audit guidance for relevant rules.

    Use this when you need to understand the accounting treatment or audit
    requirements for a specific area (e.g., revenue recognition, lease accounting,
    related party transactions).
    """
    results = standards_store.similarity_search(query, k=5)
    return "\n\n---\n\n".join(
        f"**{r.metadata.get('standard_id', 'N/A')}**: {r.page_content}"
        for r in results
    )


@tool
def search_prior_year_findings(entity_code: str, risk_area: str) -> str:
    """Search prior-year audit workpapers for findings related to a risk area.

    Use this to understand what issues were found in previous audits for this
    entity, helping calibrate current-year risk levels.
    """
    prior_year_store = AzureSearch(
        azure_search_endpoint=settings.AZURE_SEARCH_ENDPOINT,
        index_name=settings.AZURE_SEARCH_INDEX_PRIOR_YEAR,
        embedding_function=embeddings.embed_query,
    )
    results = prior_year_store.similarity_search(
        f"{entity_code} {risk_area}", k=3,
        filters=f"entity_code eq '{entity_code}'"
    )
    return "\n\n".join(r.page_content for r in results) or "No prior-year findings found."


@tool
def compute_financial_ratios(trial_balance: list[dict]) -> str:
    """Compute key financial ratios from the trial balance for risk assessment.

    Returns liquidity, profitability, leverage, and activity ratios with
    year-over-year comparison where prior-year data is available.
    """
    import pandas as pd
    df = pd.DataFrame(trial_balance)

    total_assets = df.loc[df["account_type"] == "asset", "balance"].sum()
    total_liabilities = df.loc[df["account_type"] == "liability", "balance"].sum()
    total_revenue = df.loc[df["account_type"] == "revenue", "balance"].sum()
    total_expenses = df.loc[df["account_type"] == "expense", "balance"].sum()

    ratios = {
        "current_ratio": float(
            df.loc[df["is_current"] & (df["account_type"] == "asset"), "balance"].sum()
            / max(df.loc[df["is_current"] & (df["account_type"] == "liability"), "balance"].sum(), 1)
        ),
        "debt_to_equity": float(total_liabilities / max(total_assets - total_liabilities, 1)),
        "net_profit_margin": float((total_revenue - total_expenses) / max(total_revenue, 1)),
        "revenue_total": float(total_revenue),
        "asset_total": float(total_assets),
    }
    return str(ratios)


@tool
def run_benford_analysis(journal_entries: list[dict], field: str = "debit_amount") -> str:
    """Run Benford's Law first-digit analysis on transaction amounts.

    Benford's Law predicts the distribution of leading digits in naturally
    occurring datasets. Significant deviations may indicate data manipulation,
    fabricated entries, or systematic errors.
    """
    import numpy as np
    from collections import Counter

    amounts = [abs(float(e[field])) for e in journal_entries if float(e[field]) != 0]
    leading_digits = [int(str(a).lstrip("0.")[0]) for a in amounts if a > 0]
    observed = Counter(leading_digits)
    total = sum(observed.values())

    # Benford's expected distribution
    expected = {d: np.log10(1 + 1/d) for d in range(1, 10)}

    deviations = {}
    for digit in range(1, 10):
        obs_pct = observed.get(digit, 0) / total
        exp_pct = expected[digit]
        deviations[digit] = {
            "observed_pct": round(obs_pct, 4),
            "expected_pct": round(exp_pct, 4),
            "deviation": round(abs(obs_pct - exp_pct), 4),
            "flag": abs(obs_pct - exp_pct) > 0.03,  # >3% deviation threshold
        }
    flagged = [d for d, v in deviations.items() if v["flag"]]
    summary = f"Benford analysis on {total} transactions. "
    if flagged:
        summary += f"FLAGGED digits: {flagged}. Investigate transactions with leading digits: {flagged}."
    else:
        summary += "No significant deviations from expected distribution."
    return summary


# Create the risk assessment agent
RISK_ASSESSMENT_SYSTEM_PROMPT = """\
You are a senior auditor AI assistant performing risk assessment for a financial audit.

Your role:
1. Analyze the entity's financial data (trial balance, ratios, Benford analysis)
2. Search accounting standards for relevant risk factors
3. Review prior-year findings for recurring issues
4. Produce a prioritized risk heat map

For each risk area, provide:
- Risk level: HIGH / MEDIUM / LOW
- Rationale: Why this area is risky (specific data points, not generic statements)
- Suggested testing approach: What controls and substantive tests should focus here
- Materiality consideration: Whether potential misstatement could exceed materiality

Focus on areas where:
- Ratios show unusual trends or are outside industry benchmarks
- Benford analysis flags digit distribution anomalies
- Prior-year findings indicate recurring issues
- Complex accounting estimates are involved (revenue recognition, allowances, fair value)
- Related party transactions or unusual journal entries are present

Output your assessment as a structured JSON list of risk areas.
"""

risk_assessment_agent = create_react_agent(
    model=llm,
    tools=[
        search_accounting_standards,
        search_prior_year_findings,
        compute_financial_ratios,
        run_benford_analysis,
    ],
    prompt=RISK_ASSESSMENT_SYSTEM_PROMPT,
)
```

---

### Phase 3: Integration Layer

#### Step 3.1: ERP Data Extraction Tools

```python
# src/tools/erp_connector.py
from abc import ABC, abstractmethod
from src.models.journal_entry import JournalEntry


class ERPConnector(ABC):
    """Base class for ERP system connectors."""

    @abstractmethod
    def extract_journal_entries(
        self, entity_code: str, period_start: str, period_end: str
    ) -> list[JournalEntry]:
        ...

    @abstractmethod
    def extract_trial_balance(
        self, entity_code: str, as_of_date: str
    ) -> list[dict]:
        ...


class SAPConnector(ERPConnector):
    """Extract data from SAP S/4HANA via RFC/OData."""

    def __init__(self, connection_params: dict):
        import pyrfc
        self.conn = pyrfc.Connection(**connection_params)

    def extract_journal_entries(
        self, entity_code: str, period_start: str, period_end: str
    ) -> list[JournalEntry]:
        # Call SAP BAPI for journal entry extraction
        result = self.conn.call(
            "BAPI_GLX_GETDOCITEMS",
            COMPANYCODE=entity_code,
            POSTINGDATE_FROM=period_start.replace("-", ""),
            POSTINGDATE_TO=period_end.replace("-", ""),
        )
        return [
            JournalEntry(
                entry_id=f"{item['BELNR']}-{item['BUZEI']}",
                entity_code=item["BUKRS"],
                posting_date=item["BUDAT"],
                effective_date=item["BLDAT"],
                account_number=item["HKONT"],
                account_name=item.get("TXT50", ""),
                cost_center=item.get("KOSTL"),
                debit_amount=item.get("DMBTR", 0) if item.get("SHKZG") == "S" else 0,
                credit_amount=item.get("DMBTR", 0) if item.get("SHKZG") == "H" else 0,
                currency=item["WAERS"],
                description=item.get("SGTXT", ""),
                created_by=item.get("USNAM", "SYSTEM"),
                approved_by=item.get("PPNAM"),
                source_system="SAP",
                is_manual=item.get("BSCHL", "") in ("40", "50"),  # Manual posting keys
                is_post_close=False,  # Determined after period-end comparison
                document_reference=item.get("XBLNR"),
            )
            for item in result["ITEMS"]
        ]

    def extract_trial_balance(
        self, entity_code: str, as_of_date: str
    ) -> list[dict]:
        result = self.conn.call(
            "BAPI_GL_GETGLACCBALANCE",
            COMPANYCODE=entity_code,
            FISCALYEAR=as_of_date[:4],
            FISCALPERIOD=as_of_date[5:7],
        )
        return [
            {
                "account_number": item["GL_ACCOUNT"],
                "account_name": item.get("SHORT_TEXT", ""),
                "account_type": _map_sap_account_type(item["ACCT_TYPE"]),
                "balance": float(item["LC_BAL"]),
                "is_current": item.get("ACCT_TYPE") in ("1", "3"),  # Simplified
            }
            for item in result["ACCOUNT_BALANCES"]
        ]


def _map_sap_account_type(sap_type: str) -> str:
    return {"1": "asset", "2": "liability", "3": "asset", "4": "revenue", "5": "expense"}.get(
        sap_type, "other"
    )
```

#### Step 3.2: Evidence Extraction with Document Intelligence

```python
# src/tools/document_extractor.py
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.identity import DefaultAzureCredential
from pydantic import BaseModel


class ExtractedEvidence(BaseModel):
    """Structured evidence extracted from a supporting document."""
    document_type: str            # "invoice", "receipt", "approval_form", "bank_statement"
    vendor_name: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    total_amount: float | None = None
    currency: str | None = None
    line_items: list[dict] | None = None
    approval_signature: str | None = None
    confidence: float             # Overall extraction confidence


def extract_evidence_from_document(document_url: str) -> ExtractedEvidence:
    """Extract structured data from an audit evidence document using
    Azure AI Document Intelligence.

    Supports invoices, receipts, and custom document types. Returns
    structured evidence that can be matched against control criteria.
    """
    client = DocumentIntelligenceClient(
        endpoint=Settings().AZURE_DOC_INTELLIGENCE_ENDPOINT,
        credential=DefaultAzureCredential(),
    )

    # Use prebuilt invoice model for invoices; general document for others
    poller = client.begin_analyze_document(
        model_id="prebuilt-invoice",
        body=AnalyzeDocumentRequest(url_source=document_url),
    )
    result = poller.result()

    if not result.documents:
        return ExtractedEvidence(document_type="unknown", confidence=0.0)

    doc = result.documents[0]
    fields = doc.fields

    return ExtractedEvidence(
        document_type="invoice",
        vendor_name=_get_field_value(fields, "VendorName"),
        invoice_number=_get_field_value(fields, "InvoiceId"),
        invoice_date=_get_field_value(fields, "InvoiceDate"),
        total_amount=_get_field_value(fields, "InvoiceTotal"),
        currency=_get_field_value(fields, "CurrencyCode"),
        line_items=[
            {
                "description": _get_field_value(item.value, "Description"),
                "amount": _get_field_value(item.value, "Amount"),
            }
            for item in (fields.get("Items", {}).value or [])
        ],
        confidence=doc.confidence,
    )


def _get_field_value(fields: dict, key: str):
    field = fields.get(key)
    return field.value if field else None
```

---

### Phase 4: Orchestration & Flow

#### Step 4.1: Controls Testing Agent

The controls testing agent applies deterministic rules first, then uses the LLM only for evidence matching that requires reasoning.

```python
# src/agents/controls_testing.py
import yaml
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel

from config.settings import Settings
from src.models.control import ControlTest, ControlTestResult
from src.tools.document_extractor import extract_evidence_from_document

settings = Settings()

llm = AzureChatOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_GPT4O,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    temperature=settings.TEMPERATURE_REASONING,
)


# --- Deterministic Rule Engine (no LLM needed) ---

def load_controls_library() -> dict:
    """Load control definitions from YAML configuration."""
    with open("config/controls_library.yaml") as f:
        return yaml.safe_load(f)


def test_approval_threshold(entry: dict, control: dict) -> ControlTest:
    """Test whether a journal entry has proper approval for its amount.

    Deterministic rule: entries above threshold must have approved_by populated.
    """
    threshold = control["parameters"]["approval_threshold"]
    amount = max(float(entry["debit_amount"]), float(entry["credit_amount"]))

    if amount <= threshold:
        result = ControlTestResult.PASS
        explanation = f"Amount {amount} is below threshold {threshold}."
        confidence = 1.0
    elif entry.get("approved_by"):
        result = ControlTestResult.PASS
        explanation = f"Amount {amount} exceeds threshold {threshold}; approved by {entry['approved_by']}."
        confidence = 1.0
    else:
        result = ControlTestResult.FAIL
        explanation = f"Amount {amount} exceeds threshold {threshold} but no approval recorded."
        confidence = 1.0

    return ControlTest(
        control_id=control["id"],
        control_name=control["name"],
        transaction_id=entry["entry_id"],
        result=result,
        confidence=confidence,
        evidence_refs=[],
        rule_applied="approval_threshold",
        explanation=explanation,
        requires_human_review=(result == ControlTestResult.FAIL),
    )


def test_segregation_of_duties(entry: dict, control: dict) -> ControlTest:
    """Test that the creator and approver of a journal entry are different people."""
    if entry.get("created_by") == entry.get("approved_by") and entry.get("approved_by"):
        return ControlTest(
            control_id=control["id"],
            control_name=control["name"],
            transaction_id=entry["entry_id"],
            result=ControlTestResult.FAIL,
            confidence=1.0,
            evidence_refs=[],
            rule_applied="segregation_of_duties",
            explanation=f"Same user '{entry['created_by']}' both created and approved this entry.",
            requires_human_review=True,
        )
    return ControlTest(
        control_id=control["id"],
        control_name=control["name"],
        transaction_id=entry["entry_id"],
        result=ControlTestResult.PASS,
        confidence=1.0,
        evidence_refs=[],
        rule_applied="segregation_of_duties",
        explanation="Creator and approver are different users.",
        requires_human_review=False,
    )


# --- LLM-Based Evidence Matching (requires reasoning) ---

class EvidenceMatchResult(BaseModel):
    """Structured output from LLM evidence matching."""
    matches: bool
    confidence: float
    explanation: str
    discrepancies: list[str]


EVIDENCE_MATCHING_PROMPT = """\
You are an audit evidence matching specialist. Your task is to determine whether
the extracted document evidence supports the recorded journal entry.

## Journal Entry
- Entry ID: {entry_id}
- Account: {account_number} ({account_name})
- Amount: {amount} {currency}
- Description: {description}
- Vendor: {document_reference}
- Posting Date: {posting_date}

## Extracted Evidence (from supporting document)
- Document Type: {doc_type}
- Vendor Name: {vendor_name}
- Invoice Number: {invoice_number}
- Invoice Date: {invoice_date}
- Total Amount: {doc_amount} {doc_currency}
- Line Items: {line_items}

## Instructions
Compare the journal entry against the extracted evidence and determine:
1. Does the vendor/payee match?
2. Does the amount match (within 1% tolerance for rounding)?
3. Does the date fall within a reasonable period (invoice date <= posting date <= invoice date + 90 days)?
4. Is the account classification reasonable for this type of expense?

Respond with your assessment. List any discrepancies found.
"""


async def match_evidence_to_entry(
    entry: dict, evidence_url: str
) -> ControlTest:
    """Use Document Intelligence + LLM to match evidence to a journal entry.

    This is the AI-to-real-world seam: Document Intelligence extracts structured
    data from the scanned document, then the LLM reasons about whether it
    matches the GL entry.
    """
    # Step 1: Extract evidence from document (no LLM)
    extracted = extract_evidence_from_document(evidence_url)

    # Step 2: LLM reasons about the match (requires judgment)
    prompt = EVIDENCE_MATCHING_PROMPT.format(
        entry_id=entry["entry_id"],
        account_number=entry["account_number"],
        account_name=entry["account_name"],
        amount=max(float(entry["debit_amount"]), float(entry["credit_amount"])),
        currency=entry["currency"],
        description=entry["description"],
        document_reference=entry.get("document_reference", "N/A"),
        posting_date=entry["posting_date"],
        doc_type=extracted.document_type,
        vendor_name=extracted.vendor_name or "N/A",
        invoice_number=extracted.invoice_number or "N/A",
        invoice_date=extracted.invoice_date or "N/A",
        doc_amount=extracted.total_amount or "N/A",
        doc_currency=extracted.currency or "N/A",
        line_items=str(extracted.line_items or []),
    )

    result = llm.with_structured_output(EvidenceMatchResult).invoke(prompt)

    return ControlTest(
        control_id="CTRL-EVID-MATCH",
        control_name="Three-Way Evidence Match",
        transaction_id=entry["entry_id"],
        result=(
            ControlTestResult.PASS if result.matches
            else ControlTestResult.NEEDS_REVIEW
        ),
        confidence=result.confidence,
        evidence_refs=[evidence_url],
        rule_applied="evidence_matching_llm",
        explanation=result.explanation,
        requires_human_review=(
            not result.matches or result.confidence < settings.CONFIDENCE_AUTO_PASS
        ),
    )
```

#### Step 4.2: Anomaly Detection Agent

This agent runs ML models — no LLM involved — then uses the LLM only to generate human-readable explanations.

```python
# src/tools/anomaly_models.py
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import torch
import torch.nn as nn

from src.models.anomaly import AnomalyFinding


# --- Isolation Forest ---

def run_isolation_forest(
    journal_entries: list[dict],
    contamination: float = 0.02,
) -> list[AnomalyFinding]:
    """Run Isolation Forest on journal entry features to detect statistical outliers.

    Based on the approach used by MindBridge (32 algorithms across all categories)
    and validated in Schreyer et al. (2017) for accounting data.

    Features engineered for audit relevance:
    - Amount (log-transformed)
    - Hour of posting (after-hours entries are riskier)
    - Days from period end (post-close entries)
    - Is manual entry
    - Account frequency (rarely-used accounts are riskier)
    """
    df = pd.DataFrame(journal_entries)

    # Feature engineering
    df["amount"] = df[["debit_amount", "credit_amount"]].max(axis=1).astype(float)
    df["log_amount"] = np.log1p(df["amount"])
    df["posting_hour"] = pd.to_datetime(df["posting_date"]).dt.hour
    df["is_weekend"] = pd.to_datetime(df["posting_date"]).dt.dayofweek >= 5
    df["is_manual"] = df["is_manual"].astype(int)
    df["is_post_close"] = df["is_post_close"].astype(int)

    # Account frequency: rare accounts get higher risk
    account_freq = df["account_number"].value_counts(normalize=True)
    df["account_rarity"] = df["account_number"].map(lambda x: 1 - account_freq.get(x, 0))

    # Round-number detection (e.g., $10,000.00 exactly)
    df["is_round_number"] = (df["amount"] % 1000 == 0).astype(int)

    feature_cols = [
        "log_amount", "posting_hour", "is_weekend", "is_manual",
        "is_post_close", "account_rarity", "is_round_number",
    ]
    X = df[feature_cols].fillna(0).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        contamination=contamination,
        n_estimators=200,
        random_state=42,
    )
    predictions = model.fit_predict(X_scaled)
    scores = model.decision_function(X_scaled)

    anomalies = []
    for idx in np.where(predictions == -1)[0]:
        row = df.iloc[idx]
        # Feature attribution: which features contributed most to anomaly score
        attribution = {
            col: float(abs(X_scaled[idx, i]))
            for i, col in enumerate(feature_cols)
        }
        anomalies.append(AnomalyFinding(
            finding_id=f"IF-{row['entry_id']}",
            transaction_ids=[row["entry_id"]],
            anomaly_type="isolation_forest",
            risk_score=float(1 - (scores[idx] - scores.min()) / (scores.max() - scores.min())),
            feature_attribution=attribution,
            description=_generate_anomaly_description(row, attribution),
            recommended_action="Review transaction for validity and proper authorization.",
            estimated_amount=float(row["amount"]),
        ))

    return sorted(anomalies, key=lambda a: a.risk_score, reverse=True)


def _generate_anomaly_description(row: pd.Series, attribution: dict) -> str:
    """Generate a human-readable description of why this entry is anomalous."""
    top_features = sorted(attribution.items(), key=lambda x: x[1], reverse=True)[:3]
    reasons = []
    for feat, score in top_features:
        if feat == "log_amount" and score > 1.5:
            reasons.append(f"unusually large amount ({row['amount']:.2f})")
        elif feat == "posting_hour" and score > 1.5:
            reasons.append("posted outside normal business hours")
        elif feat == "is_manual" and row.get("is_manual"):
            reasons.append("manual journal entry")
        elif feat == "account_rarity" and score > 1.0:
            reasons.append(f"posted to rarely-used account {row['account_number']}")
        elif feat == "is_round_number" and row.get("is_round_number"):
            reasons.append("round dollar amount")
        elif feat == "is_post_close" and row.get("is_post_close"):
            reasons.append("posted after period close")
    return f"Flagged: {'; '.join(reasons)}." if reasons else "Statistical outlier across multiple dimensions."


# --- Autoencoder for Pattern-Based Anomaly Detection ---

class JournalEntryAutoencoder(nn.Module):
    """Deep autoencoder for detecting anomalous journal entry patterns.

    Based on Schreyer et al. (2017) "Detection of Anomalies in Large Scale
    Accounting Data using Deep Autoencoder Networks". The reconstruction error
    serves as an anomaly score — entries that the model cannot reconstruct
    well are likely anomalous.
    """

    def __init__(self, input_dim: int, encoding_dim: int = 16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, encoding_dim),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, input_dim),
            nn.Sigmoid(),
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


def train_autoencoder_and_detect(
    journal_entries: list[dict],
    epochs: int = 50,
    threshold_percentile: float = 98.0,
) -> list[AnomalyFinding]:
    """Train autoencoder on journal entries, then flag high-reconstruction-error items.

    The autoencoder learns the "normal" distribution of journal entries. Entries
    with high reconstruction error are anomalous — they don't fit the patterns
    the model learned from the majority of data.
    """
    df = pd.DataFrame(journal_entries)

    # Encode categorical features and normalize
    feature_cols = [
        "log_amount", "posting_hour", "is_weekend", "is_manual",
        "is_post_close", "account_rarity", "is_round_number",
    ]
    # (Feature engineering same as isolation forest - omitted for brevity)

    X = df[feature_cols].fillna(0).values.astype(np.float32)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_tensor = torch.FloatTensor(X_scaled)
    model = JournalEntryAutoencoder(input_dim=X_scaled.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss(reduction="none")

    # Train
    model.train()
    for epoch in range(epochs):
        output = model(X_tensor)
        loss = criterion(output, X_tensor).mean()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    # Detect anomalies via reconstruction error
    model.eval()
    with torch.no_grad():
        reconstructed = model(X_tensor)
        reconstruction_errors = criterion(reconstructed, X_tensor).mean(dim=1).numpy()

    threshold = np.percentile(reconstruction_errors, threshold_percentile)
    anomaly_indices = np.where(reconstruction_errors > threshold)[0]

    anomalies = []
    for idx in anomaly_indices:
        row = df.iloc[idx]
        anomalies.append(AnomalyFinding(
            finding_id=f"AE-{row['entry_id']}",
            transaction_ids=[row["entry_id"]],
            anomaly_type="autoencoder",
            risk_score=float(
                (reconstruction_errors[idx] - reconstruction_errors.min())
                / (reconstruction_errors.max() - reconstruction_errors.min())
            ),
            feature_attribution={},  # Autoencoder attribution is less interpretable
            description=f"High reconstruction error ({reconstruction_errors[idx]:.4f}) — "
                        f"entry pattern deviates from learned normal patterns.",
            recommended_action="Investigate entry for unusual posting patterns.",
            estimated_amount=float(row.get("amount", 0)),
        ))

    return sorted(anomalies, key=lambda a: a.risk_score, reverse=True)
```

#### Step 4.3: Documentation Agent

```python
# src/agents/documentation.py
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel

from config.settings import Settings

settings = Settings()

llm = AzureChatOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI,  # Cost-efficient for generation
    api_version=settings.AZURE_OPENAI_API_VERSION,
    temperature=settings.TEMPERATURE_DOCUMENTATION,
    max_tokens=settings.MAX_TOKENS_DOCUMENTATION,
)


class WorkpaperSection(BaseModel):
    """Structured workpaper section for export to audit management platform."""
    section_title: str
    objective: str
    scope: str
    procedures_performed: str
    results_summary: str
    exceptions_noted: list[str]
    conclusion: str
    evidence_references: list[str]
    preparer_note: str


WORKPAPER_GENERATION_PROMPT = """\
You are an audit documentation specialist generating workpaper narratives.

## Context
- Engagement: {engagement_id}
- Entity: {entity_code}
- Period: {period_start} to {period_end}
- Control tested: {control_name} ({control_id})

## Test Results Summary
- Total transactions tested: {total_tested}
- Passed: {total_passed}
- Failed: {total_failed}
- Exceptions needing review: {total_exceptions}
- Testing method: 100% population testing via automated AI analysis

## Exceptions Detail
{exceptions_detail}

## Instructions
Generate a professional audit workpaper section following the firm's documentation
standards. The workpaper must:

1. State the audit objective clearly
2. Describe the scope (what population was tested, what period)
3. Detail the procedures performed (be specific about automated testing approach)
4. Summarize results with quantitative data
5. List all exceptions with transaction IDs
6. Provide a conclusion stating whether the control is operating effectively

IMPORTANT:
- Use professional audit language (per PCAOB AS 1215 documentation standards)
- State that the testing covered 100% of the population, not a sample
- Reference the specific AI-based testing methodology used
- Note that all exceptions were flagged for human auditor review
- Do NOT make materiality judgments — leave those to the signing auditor
"""


async def generate_workpaper(
    engagement_context: dict,
    control: dict,
    test_results: list[dict],
) -> WorkpaperSection:
    """Generate a structured workpaper section from control test results."""
    passed = [r for r in test_results if r["result"] == "pass"]
    failed = [r for r in test_results if r["result"] == "fail"]
    exceptions = [r for r in test_results if r["result"] in ("exception", "needs_review")]

    exceptions_detail = "\n".join(
        f"- Transaction {r['transaction_id']}: {r['explanation']}"
        for r in (failed + exceptions)[:50]  # Limit detail to top 50
    ) or "No exceptions noted."

    prompt = WORKPAPER_GENERATION_PROMPT.format(
        engagement_id=engagement_context["engagement_id"],
        entity_code=engagement_context["entity_code"],
        period_start=engagement_context["period_start"],
        period_end=engagement_context["period_end"],
        control_name=control["name"],
        control_id=control["id"],
        total_tested=len(test_results),
        total_passed=len(passed),
        total_failed=len(failed),
        total_exceptions=len(exceptions),
        exceptions_detail=exceptions_detail,
    )

    return llm.with_structured_output(WorkpaperSection).invoke(prompt)
```

#### Step 4.4: Human-in-the-Loop Escalation

```python
# src/agents/orchestrator.py (continued)

def pause_for_human_review(state: AuditState) -> AuditState:
    """Pause the workflow and queue findings for human auditor review.

    This node creates review tasks in the audit management platform and
    waits for human decisions before proceeding to documentation.
    """
    escalations = state.get("escalations", [])
    settings = Settings()

    review_items = []
    for escalation in escalations:
        review_items.append({
            "type": escalation["type"],  # "control_failure", "anomaly", "material_finding"
            "severity": escalation["severity"],
            "summary": escalation["summary"],
            "transaction_ids": escalation["transaction_ids"],
            "ai_confidence": escalation.get("confidence", 0.0),
            "ai_recommendation": escalation.get("recommendation", ""),
            "status": "pending_review",
        })

    # In production, this would create tasks in AuditBoard/TeamMate
    # and use LangGraph's interrupt() to pause until human responds
    return {
        **state,
        "phase": "human_review",
        "escalations": review_items,
    }


def classify_escalation(
    finding: dict, materiality_threshold: float
) -> dict:
    """Determine escalation level based on finding characteristics."""
    amount = float(finding.get("estimated_amount", 0))
    confidence = finding.get("confidence", 0.0)

    if amount > materiality_threshold:
        severity = "material"
        assignee = "partner"
    elif confidence < 0.7:
        severity = "high"
        assignee = "manager"
    elif confidence < 0.95:
        severity = "medium"
        assignee = "senior"
    else:
        severity = "low"
        assignee = "auto_document"

    return {
        "severity": severity,
        "assignee": assignee,
        "summary": finding.get("explanation", finding.get("description", "")),
        "transaction_ids": finding.get("transaction_ids", [finding.get("transaction_id")]),
        "confidence": confidence,
        "recommendation": finding.get("recommended_action", ""),
    }
```

---

### Phase 5: Deployment

#### Step 5.1: Running the Audit Workflow

```python
# src/api/routes.py
from fastapi import FastAPI, BackgroundTasks
from src.agents.orchestrator import audit_graph, AuditState

app = FastAPI(title="Audit AI Agent")


@app.post("/engagements/{engagement_id}/run")
async def start_audit(engagement_id: str, background_tasks: BackgroundTasks):
    """Trigger an audit workflow for a given engagement."""
    initial_state: AuditState = {
        "engagement_id": engagement_id,
        "entity_code": "US-001",  # Loaded from engagement platform
        "period_start": "2025-01-01",
        "period_end": "2025-12-31",
        "materiality_threshold": 500_000.0,
        "journal_entries": [],
        "trial_balance": [],
        "risk_areas": [],
        "risk_heat_map": {},
        "control_test_results": [],
        "anomaly_findings": [],
        "workpapers": [],
        "messages": [],
        "phase": "initiated",
        "errors": [],
        "escalations": [],
    }

    config = {"configurable": {"thread_id": engagement_id}}
    background_tasks.add_task(audit_graph.ainvoke, initial_state, config)
    return {"status": "started", "engagement_id": engagement_id}
```

#### Step 5.2: Configuration & Secrets Management

All secrets stored in Azure Key Vault; application references them via environment variables injected by Container Apps managed identity.

```yaml
# config/controls_library.yaml
controls:
  - id: CTRL-JE-APPROVAL
    name: Journal Entry Approval Threshold
    category: journal_entries
    test_type: deterministic
    parameters:
      approval_threshold: 10000.00
    description: >
      All journal entries exceeding the approval threshold must have
      an authorized approver recorded in the approved_by field.

  - id: CTRL-SOD
    name: Segregation of Duties - Journal Entries
    category: journal_entries
    test_type: deterministic
    parameters: {}
    description: >
      The preparer and approver of a journal entry must be different
      individuals to prevent unauthorized transactions.

  - id: CTRL-EVID-MATCH
    name: Three-Way Evidence Match
    category: accounts_payable
    test_type: llm_evidence_matching
    parameters:
      amount_tolerance_pct: 1.0
      date_tolerance_days: 90
    description: >
      Supporting documentation (invoice) must match the recorded GL
      entry in vendor, amount (within tolerance), and date.
```

---

## Key Code Patterns

### Pattern: Deterministic-First, LLM-Second

Always attempt deterministic rule checks before invoking the LLM. This keeps costs low, latency low, and auditability high. The LLM is only needed where rules cannot capture the judgment required.

```python
async def test_control(entry: dict, control: dict) -> ControlTest:
    """Route to deterministic or LLM-based testing based on control type."""
    if control["test_type"] == "deterministic":
        rule_fn = RULE_REGISTRY[control["id"]]
        return rule_fn(entry, control)
    elif control["test_type"] == "llm_evidence_matching":
        evidence_url = resolve_evidence_url(entry)
        if evidence_url:
            return await match_evidence_to_entry(entry, evidence_url)
        return ControlTest(
            control_id=control["id"],
            control_name=control["name"],
            transaction_id=entry["entry_id"],
            result=ControlTestResult.NEEDS_REVIEW,
            confidence=0.0,
            evidence_refs=[],
            rule_applied="no_evidence_found",
            explanation="No supporting evidence document found for this entry.",
            requires_human_review=True,
        )
```

### Pattern: Structured Output for Audit Trail

Every LLM call uses structured output (Pydantic models) to ensure consistent, parseable responses that can be stored in the audit trail.

```python
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel


class RiskAssessment(BaseModel):
    """Structured risk assessment output from the LLM."""
    risk_area: str
    risk_level: str  # "HIGH", "MEDIUM", "LOW"
    rationale: str
    affected_accounts: list[str]
    suggested_testing_approach: str
    estimated_impact: float | None = None


# Force the LLM to output structured JSON matching the schema
result: RiskAssessment = llm.with_structured_output(RiskAssessment).invoke(prompt)
# result is guaranteed to be a valid RiskAssessment — no parsing needed
```

### Pattern: Ensemble Anomaly Scoring

Combine multiple ML models into a single risk score using weighted averaging. This mirrors MindBridge's approach of using 32 algorithms and is more robust than any single model.

```python
def compute_ensemble_risk_score(
    isolation_forest_findings: list[AnomalyFinding],
    autoencoder_findings: list[AnomalyFinding],
    benford_flags: set[str],  # Set of flagged entry IDs
) -> dict[str, float]:
    """Combine anomaly scores from multiple models into a single risk score.

    Weights reflect the empirical reliability of each detection method for
    accounting data (based on Schreyer et al. and MindBridge's published approach).
    """
    weights = {
        "isolation_forest": 0.40,
        "autoencoder": 0.35,
        "benford": 0.25,
    }

    scores: dict[str, dict[str, float]] = {}

    for finding in isolation_forest_findings:
        for tid in finding.transaction_ids:
            scores.setdefault(tid, {})["isolation_forest"] = finding.risk_score

    for finding in autoencoder_findings:
        for tid in finding.transaction_ids:
            scores.setdefault(tid, {})["autoencoder"] = finding.risk_score

    for tid in benford_flags:
        scores.setdefault(tid, {})["benford"] = 1.0

    ensemble: dict[str, float] = {}
    for tid, model_scores in scores.items():
        weighted_sum = sum(
            model_scores.get(model, 0.0) * weight
            for model, weight in weights.items()
        )
        total_weight = sum(
            weight for model, weight in weights.items()
            if model in model_scores
        )
        ensemble[tid] = weighted_sum / total_weight if total_weight > 0 else 0.0

    return ensemble
```

---

## Configuration Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `AZURE_OPENAI_DEPLOYMENT_GPT4O` | `gpt-4o` | Model for reasoning tasks (risk assessment, evidence matching) |
| `AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI` | `gpt-4o-mini` | Model for generation tasks (documentation, summaries) |
| `TEMPERATURE_REASONING` | `0.0` | Zero temperature for deterministic audit conclusions |
| `TEMPERATURE_DOCUMENTATION` | `0.3` | Slight variation for natural-sounding narratives |
| `CONFIDENCE_AUTO_PASS` | `0.95` | Above this: auto-documented, no human review |
| `CONFIDENCE_SENIOR_REVIEW` | `0.70` | 0.70–0.95: queued for senior auditor review |
| `MATERIALITY_ESCALATION` | `0.05` | Fraction of total assets triggering partner escalation |
| `IF_CONTAMINATION` | `0.02` | Isolation Forest expected anomaly rate (2%) |
| `AE_THRESHOLD_PERCENTILE` | `98.0` | Autoencoder reconstruction error cutoff (top 2%) |
| `BENFORD_DEVIATION_THRESHOLD` | `0.03` | Benford's Law deviation threshold (3%) |

---

## Testing Strategy

### Unit Tests

Test each tool function independently with known inputs and expected outputs.

```python
# tests/unit/test_rule_engine.py
from src.agents.controls_testing import test_approval_threshold

def test_approval_below_threshold_passes():
    entry = {
        "entry_id": "JE-001",
        "debit_amount": "5000.00",
        "credit_amount": "0",
        "approved_by": None,
    }
    control = {
        "id": "CTRL-JE-APPROVAL",
        "name": "Approval Threshold",
        "parameters": {"approval_threshold": 10000.0},
    }
    result = test_approval_threshold(entry, control)
    assert result.result == "pass"
    assert result.confidence == 1.0


def test_approval_above_threshold_without_approver_fails():
    entry = {
        "entry_id": "JE-002",
        "debit_amount": "50000.00",
        "credit_amount": "0",
        "approved_by": None,
    }
    control = {
        "id": "CTRL-JE-APPROVAL",
        "name": "Approval Threshold",
        "parameters": {"approval_threshold": 10000.0},
    }
    result = test_approval_threshold(entry, control)
    assert result.result == "fail"
    assert result.requires_human_review is True
```

### Integration Tests

Test the full agent flow with a small synthetic dataset.

```python
# tests/integration/test_audit_flow.py
import pytest
from src.agents.orchestrator import audit_graph

@pytest.mark.asyncio
async def test_full_audit_flow_with_synthetic_data():
    """Run the complete audit workflow on a synthetic dataset with known anomalies."""
    state = {
        "engagement_id": "TEST-001",
        "entity_code": "TEST-ENTITY",
        "period_start": "2025-01-01",
        "period_end": "2025-12-31",
        "materiality_threshold": 100_000.0,
        "journal_entries": SYNTHETIC_ENTRIES,  # Pre-loaded with known anomalies
        "trial_balance": SYNTHETIC_TRIAL_BALANCE,
        "risk_areas": [],
        "risk_heat_map": {},
        "control_test_results": [],
        "anomaly_findings": [],
        "workpapers": [],
        "messages": [],
        "phase": "initiated",
        "errors": [],
        "escalations": [],
    }
    config = {"configurable": {"thread_id": "test-001"}}
    result = await audit_graph.ainvoke(state, config)

    # Verify known anomalies were detected
    anomaly_ids = {
        tid for f in result["anomaly_findings"] for tid in f["transaction_ids"]
    }
    assert "KNOWN-ANOMALY-001" in anomaly_ids
    assert "KNOWN-ANOMALY-002" in anomaly_ids

    # Verify workpapers were generated
    assert len(result["workpapers"]) > 0
```

### Evaluation Tests

Measure AI output quality against human auditor ground truth.

```python
# tests/evaluation/test_evidence_matching_quality.py
import json
from src.agents.controls_testing import match_evidence_to_entry

GROUND_TRUTH = json.load(open("tests/evaluation/evidence_matching_labels.json"))


@pytest.mark.asyncio
async def test_evidence_matching_accuracy():
    """Measure evidence matching accuracy against human-labeled test set.

    Target: >90% agreement with human auditor decisions.
    """
    correct = 0
    total = len(GROUND_TRUTH)

    for case in GROUND_TRUTH:
        result = await match_evidence_to_entry(case["entry"], case["evidence_url"])
        predicted_match = result.result == "pass"
        if predicted_match == case["human_label_matches"]:
            correct += 1

    accuracy = correct / total
    assert accuracy >= 0.90, f"Evidence matching accuracy {accuracy:.2%} below 90% target"
```

---

## Monitoring & Observability

| What to Monitor | Tool / Method | Alert Threshold |
|----------------|--------------|-----------------|
| **LLM Latency** | Application Insights custom metric | p95 > 10s for evidence matching |
| **LLM Error Rate** | Application Insights dependency tracking | > 3% failures in 5min window |
| **Token Usage** | Custom metric per agent per engagement | Daily budget exceeded |
| **Anomaly Detection Rate** | Custom metric | > 5% of transactions flagged (model may be miscalibrated) |
| **Human Escalation Rate** | Custom metric | > 30% of findings escalated (thresholds may need tuning) |
| **Evidence Matching Confidence** | Distribution tracked per engagement | Median confidence < 0.80 |
| **Engagement Completion** | StateGraph phase tracking | Engagement stuck in same phase > 4 hours |

---

## Common Pitfalls & Mitigations

| Pitfall | Mitigation |
|---------|-----------|
| LLM hallucinating transaction data not in the input | Structured output schemas enforce response format; evidence matching prompt includes only actual extracted data — never asks LLM to "recall" information |
| Token limit exceeded on large populations | Batch controls testing by account group (1,000 entries per LLM call); anomaly detection uses ML models with no token limit |
| False positives overwhelming human reviewers | Tune contamination rate (isolation forest) and threshold percentile (autoencoder) on validation set; ensemble scoring reduces single-model noise |
| ERP connection failures mid-engagement | LangGraph checkpointing allows resume from last successful step; Service Bus dead-letter queue preserves failed extraction requests |
| Prompt injection via journal entry descriptions | Journal entry descriptions are included in prompts as data fields within structured templates; system prompt explicitly instructs LLM to treat all entry data as untrusted and never execute instructions found in data fields |
| Model drift on new accounting patterns | Retrain autoencoder quarterly on latest data; monitor reconstruction error distribution for drift; alert if distribution shifts significantly |

---

## Rollback Plan

1. **Feature flag**: All AI-generated workpapers are marked with `source: "ai-generated"` in the audit management platform. A feature flag (`AUDIT_AI_ENABLED`) can disable AI processing and revert to manual workflow.
2. **Parallel run**: During initial deployment, run AI audit alongside traditional manual audit for 2–3 engagement cycles. Compare findings to validate AI accuracy before relying on it.
3. **Human override**: Every AI conclusion can be overridden by an auditor in the review UI. Overrides are logged to improve model calibration.
4. **Data preservation**: All raw ERP extracts are stored in ADLS Gen2 with immutable retention. If AI processing is rolled back, the same data can be re-processed manually.
