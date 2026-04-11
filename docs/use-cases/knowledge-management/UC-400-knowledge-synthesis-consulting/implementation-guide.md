---
layout: use-case-detail
title: "Implementation Guide — Autonomous Knowledge Synthesis and Research Copilot for Management Consultants with Agentic AI"
uc_id: "UC-400"
uc_title: "Autonomous Knowledge Synthesis and Research Copilot for Management Consultants with Agentic AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Knowledge Management"
category_icon: "book-open"
industry: "Professional Services (Management Consulting, Strategy, Audit & Advisory)"
complexity: "High"
status: "detailed"
slug: "UC-400-knowledge-synthesis-consulting"
permalink: /use-cases/UC-400-knowledge-synthesis-consulting/implementation-guide/
---

## Build Goal

Deliver a production knowledge synthesis platform that a single practice area can use for day-to-day research within eight weeks, with information-barrier enforcement and citation traceability from day one. The first release covers conversational research retrieval over the proprietary corpus with inline citations, one specialized vertical agent (e.g., market sizing), and integration with PowerPoint for slide drafting. The agent marketplace, admin offloading agents, and multi-region deployment remain outside the first release.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.12+ on Azure Container Apps or AKS | McKinsey's platform runs on Azure; container-based deployment supports the multi-agent pattern and scales to tens of thousands of concurrent users. [S1][S11] |
| **Model access** | Azure OpenAI Service (GPT-4o for synthesis, GPT-4o-mini for routing) + Cohere Embed v3 for embeddings | Multi-model routing matches workload to capability. Cohere embeddings provide strong multilingual semantic matching, consistent with McKinsey's reported stack. [S11][S12] |
| **Orchestration runtime** | LangGraph with a coordinator-agent pattern | Supports the decompose-route-synthesize flow, agent registration, and state management across multi-step research tasks. [S10] |
| **Core connectors** | Azure AI Search (hybrid retrieval), Microsoft Graph API (PowerPoint/calendar), licensed data APIs (Capital IQ, Gartner, AlphaSense) | Azure AI Search supports document-level security filters natively, which is critical for information-barrier enforcement. |
| **Evaluation / tracing** | Langfuse for prompt tracing; OpenTelemetry for infrastructure spans | Full prompt-retrieval-output tracing is a compliance requirement. Langfuse provides a UI for reviewing individual traces; OpenTelemetry covers the infrastructure layer. [S10] |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 (Weeks 1–2) | Corpus ingestion pipeline operational; hybrid retrieval returning relevant results for test queries. | Document ingestion pipeline (SharePoint connector, text extraction, chunking, embedding). Azure AI Search index with engagement-level metadata and ABAC security filters. Retrieval quality benchmark against 50 curated test queries. |
| 2 (Weeks 3–5) | Coordinator agent and research retrieval agent producing cited synthesis for single-practice queries. | Coordinator agent decomposing queries into sub-tasks. Research retrieval agent with citation tracking (document ID, page number). Synthesis engine combining multi-source results with inline citations. Chat interface (web UI). |
| 3 (Weeks 6–7) | PowerPoint integration and one vertical agent operational. | Slide drafting agent generating firm-branded deck structures via Office API. One practice-area agent (e.g., market sizing) registered in the agent catalog. Information-barrier enforcement validated with compliance. |
| 4 (Week 8) | Pilot with one practice area; evaluation harness producing quality metrics. | Pilot deployment to 50–100 consultants in one practice area. Evaluation harness running citation accuracy, retrieval relevance, and barrier-compliance checks. Runbook and incident-response procedures documented. |

## Core Contracts

### State And Output Schemas

The coordinator agent maintains a session state that tracks the original query, decomposed sub-tasks, retrieval results per sub-task, and the final synthesis. The synthesis output is a structured object that separates cited claims from ungrounded suggestions.

```python
from pydantic import BaseModel

class Citation(BaseModel):
    document_id: str
    document_title: str
    page_number: int | None
    passage: str  # The specific text being cited
    source_type: str  # "proprietary_kb" | "third_party" | "expert_transcript"

class SynthesisBlock(BaseModel):
    claim: str
    citations: list[Citation]
    is_grounded: bool  # False if no supporting citation was found

class ResearchOutput(BaseModel):
    query: str
    sub_tasks: list[str]
    synthesis: list[SynthesisBlock]
    suggested_experts: list[str]  # Internal experts identified from document metadata
    retrieval_metadata: dict  # Timing, document count, barrier filters applied
```

### Tool Interface Pattern

Each agent exposes a narrow set of tools scoped to its responsibility. The retrieval tool enforces information barriers by requiring the caller's engagement context, which the access-control engine evaluates before returning results.

```python
from langchain_core.tools import tool

@tool
def search_knowledge_corpus(
    query: str,
    engagement_id: str,
    consultant_id: str,
    max_results: int = 7,
    source_filter: list[str] | None = None,
) -> list[dict]:
    """Search the proprietary knowledge corpus with information-barrier enforcement.

    The access-control engine filters results to only documents the consultant
    is permitted to see based on their engagement assignments. The LLM never
    receives documents that fail the barrier check.
    """
    # 1. Embed query using Cohere Embed v3
    # 2. Execute hybrid search (dense + BM25) against Azure AI Search
    # 3. Apply ABAC security filter: engagement_id + consultant_id
    # 4. Return top-k results with document metadata and page-level passages
    ...
```

## Orchestration Outline

The coordinator agent receives a consultant's query, decomposes it into sub-tasks, dispatches each to the appropriate specialist agent, collects results, and hands them to the synthesis engine. If a sub-task fails or returns low-confidence results, the coordinator can retry with a reformulated query or flag the gap to the consultant.

```python
from langgraph.graph import StateGraph, END

def build_research_workflow():
    graph = StateGraph(ResearchState)

    graph.add_node("decompose", decompose_query)
    graph.add_node("retrieve", parallel_agent_retrieval)
    graph.add_node("synthesize", synthesize_with_citations)
    graph.add_node("review_gaps", check_for_gaps)

    graph.set_entry_point("decompose")
    graph.add_edge("decompose", "retrieve")
    graph.add_edge("retrieve", "synthesize")
    graph.add_conditional_edges(
        "synthesize",
        has_ungrounded_claims,
        {True: "review_gaps", False: END},
    )
    graph.add_edge("review_gaps", END)

    return graph.compile()
```

## Prompt And Guardrail Pattern

The system prompt establishes the role, constraints, and output format. The critical guardrails are: never fabricate a citation, never surface content from a walled engagement, and always flag ungrounded claims.

```text
You are a research assistant for management consultants at [Firm Name].
Your role is to find and synthesize relevant knowledge from the firm's
proprietary corpus and licensed third-party sources.

Rules:
- Every factual claim MUST include an inline citation to a specific document
  and page number from the retrieved results.
- If you cannot find a supporting source for a claim, label it
  "[UNGROUNDED]" and explain why you believe it may be true.
- NEVER fabricate document titles, page numbers, or quotations.
- NEVER reference documents that were not returned by the retrieval system.
- If the query touches a topic where you have no retrieved evidence,
  say so directly and suggest which practice area or expert might help.
- Maintain a professional, concise tone suitable for senior partner review.

Output format:
- Start with a 2-3 sentence executive summary.
- Follow with detailed findings organized by sub-topic.
- End with a list of suggested internal experts and any evidence gaps.
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| Knowledge corpus ingestion | Incremental sync pipeline from SharePoint/Documentum to Azure AI Search. Extracts text from PowerPoint, PDF, Word, and Excel. Chunks documents at section boundaries (not fixed token windows). Tags each chunk with engagement ID, practice area, date, sensitivity label, and author. | Run on a schedule (e.g., hourly) with change-detection. Prioritize recently filed engagement artifacts. Handle the long tail of legacy formats (PPT, XLS) with Apache Tika or Azure AI Document Intelligence. |
| Information-barrier configuration | A compliance-managed registry mapping engagement IDs to barrier groups. The retrieval layer reads this registry at query time and applies it as a security filter in Azure AI Search. | Barrier configurations must be updated when engagement staffing changes. Integrate with the firm's staffing system (e.g., SAP SuccessFactors, internal staffing tool) for real-time role feeds. |
| PowerPoint generation | Slide drafting agent calls Microsoft Graph API to create presentations from firm-branded templates. Inserts charts, tables, and prose blocks into predefined slide layouts. | BCG's Deckster uses 800–900 firm-approved templates. [S6] Start with 10–20 high-use templates for the pilot practice area. Validate output with the firm's brand team. |
| Third-party data connectors | API adapters for Capital IQ, Gartner, IBISWorld, and AlphaSense. Each adapter normalizes responses into the citation schema and respects licensing terms (rate limits, caching restrictions). | License agreements may restrict how third-party data appears in AI-generated output. Review each license before building the connector. |
| Audit logging | Every prompt, retrieved document list, barrier-filter result, model invocation, and final output is written to an immutable audit log. | Use Azure Event Hubs or a dedicated logging pipeline. Retention period per firm policy and regulatory requirements. The log must be queryable by compliance for investigations. |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Citation accuracy | For 200 test queries, verify that every inline citation resolves to a real document containing the cited content. Measure hallucinated-citation rate. | Hallucinated-citation rate < 1%. |
| Retrieval relevance | Human evaluation of top-7 retrieved documents for 100 queries, scored on a 1–5 relevance scale. Compare against keyword-search baseline. | Mean relevance score > 3.5 (vs. baseline). Retrieval must outperform keyword search on at least 80% of test queries. |
| Information-barrier compliance | Adversarial test suite: 50 queries designed to probe barrier boundaries. Verify zero cross-barrier document leakage. | Zero barrier violations. Any single violation blocks release. |
| Synthesis quality | Blind evaluation by 10 senior consultants comparing AI-synthesized briefs to manually produced briefs on the same topic. Score on completeness, accuracy, and usefulness. | AI synthesis rated "useful" or better on > 70% of evaluations. |
| Latency | End-to-end response time for single-turn research queries (from query submission to full synthesis display). | P95 latency < 30 seconds for research queries; < 5 seconds for simple lookups. |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start with one practice area (50–100 consultants) in one region. Expand to adjacent practice areas after 4 weeks if evaluation gates pass. McKinsey's Lilli piloted with ~7,000 employees before firmwide rollout. [S1] Plan for 3–6 months from pilot to firmwide availability. |
| **Fallback path** | The existing keyword-search knowledge base and partner-email workflow remain available throughout rollout. If the AI platform is degraded, consultants revert to manual research. No irreversible process changes in the pilot phase. |
| **Observability** | Trace every request end-to-end: query → decomposition → retrieval (with barrier filter results) → synthesis → output. Alert on hallucinated-citation rate exceeding 2%, barrier-filter failures, and P95 latency exceeding 45 seconds. Dashboard for adoption metrics (MAU, prompts/week, time-to-first-citation). |
| **Operations ownership** | The firm's AI/ML platform team owns infrastructure and model operations. The knowledge management team owns corpus quality and ingestion pipelines. Compliance owns barrier configurations. Each practice area owns its vertical agents in the marketplace. |
