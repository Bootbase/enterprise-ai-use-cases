---
layout: use-case-detail
title: "Solution Design — UC-059: Autonomous Clinical Trial Patient Matching and Recruitment with Agentic AI"
uc_id: "UC-059"
uc_title: "Autonomous Clinical Trial Patient Matching and Recruitment with Agentic AI"
detail_type: "solution-design"
detail_title: "Solution Design"
category: "Industry-Specific"
status: "detailed"
slug: "uc-059-clinical-trial-patient-matching-recruitment-agentic-ai"
permalink: /use-cases/uc-059-clinical-trial-patient-matching-recruitment-agentic-ai/solution-design/
---

## Solution Overview

This solution deploys a multi-agent AI system that autonomously orchestrates clinical trial patient matching — from parsing complex eligibility criteria in trial protocols to scanning structured and unstructured EHR data, scoring patient-trial matches with explainable reasoning, and monitoring enrollment velocity across sites.

The architecture follows a plan-and-execute multi-agent pattern. A central Orchestrator Agent coordinates four specialized worker agents:

1. **Protocol Criteria Agent** — decomposes eligibility requirements into machine-executable rules
2. **Patient Matching Agent** — uses RAG over EHR data with medical Chain-of-Thought reasoning
3. **Site Optimization Agent** — predicts enrollment performance using historical data
4. **Enrollment Monitor Agent** — tracks recruitment velocity and triggers corrective actions

This pattern was chosen because clinical trial matching requires multiple distinct reasoning capabilities (clinical NLP, eligibility logic, predictive analytics, operational monitoring) that benefit from agent specialization, while a shared state graph ensures coordination and auditability.

The system integrates with EHR platforms (Epic, Oracle Health/Cerner) via HL7 FHIR R4 APIs, retrieves trial definitions from ClinicalTrials.gov, and feeds results into Clinical Trial Management Systems (Medidata Rave, Veeva Vault). LangGraph provides graph-based orchestration with checkpointing and human-in-the-loop gates.

---

## Architecture

### Component Overview

| # | Component | Technology | Role |
|---|-----------|------------|------|
| 1 | Orchestrator Agent | LangGraph StateGraph | Routes tasks, manages shared state, enforces HITL gates |
| 2 | Protocol Criteria Agent | Azure OpenAI GPT-4o | Extracts/decomposes I/E criteria from PDF protocols |
| 3 | Patient Matching Agent | Azure OpenAI GPT-4o + Azure AI Search | RAG over EHR data with medical Chain-of-Thought reasoning |
| 4 | Site Optimization Agent | Azure OpenAI GPT-4o | Predictive site scoring, feasibility assessment |
| 5 | Enrollment Monitor Agent | Azure OpenAI GPT-4o | Velocity tracking, anomaly detection, corrective actions |
| 6 | EHR Data Layer | FHIR R4 APIs | Structured patient data retrieval |
| 7 | Unstructured NLP | Azure AI Document Intelligence | Clinical note extraction and embedding |
| 8 | Vector Store | Azure AI Search (hybrid) | Semantic + lexical search over patient records |
| 9 | CTMS Integration | REST APIs | Bidirectional sync with Medidata/Veeva |
| 10 | Audit & Compliance | Azure Cosmos DB | Immutable decision logs and reasoning traces |

---

## Data Flow

```
1. [Trigger]    → New trial protocol or patient data arrives
2. [Parse]      → Protocol Criteria Agent extracts I/E criteria → JSON rules
3. [Retrieve]   → Patient Matching Agent queries FHIR + vector search (RAG)
4. [Reason]     → LLM evaluates each patient using medical Chain-of-Thought
5. [Score]      → Patients ranked by composite match score; sub-threshold flagged for review
6. [Optimize]   → Site Optimization Agent scores sites by enrollment velocity, proximity, diversity
7. [Monitor]    → Enrollment Monitor Agent tracks velocity vs. plan; triggers alerts
8. [HITL Gate]  → Low-confidence matches routed to clinical team for approval
9. [Sync]       → Approved matches pushed to CTMS; audit log written
```

---

## Agent Pattern

| Aspect | Choice |
|--------|--------|
| **Pattern** | Multi-Agent Orchestrator-Worker with RAG |
| **Orchestration** | Graph-based (LangGraph StateGraph with conditional edges) |
| **Human-in-the-Loop** | Confidence-gated escalation (matches < 0.85 routed to clinical reviewer) |
| **State Management** | Persistent checkpointed state (LangGraph with PostgreSQL backend) |
| **Autonomy Level** | Semi-autonomous (matching and monitoring autonomous; human approval for patient outreach) |

### Why This Pattern?

Multi-agent orchestrator-worker was chosen because clinical trial matching requires four distinct capabilities:

1. **Protocol parsing** requires document understanding and medical terminology extraction
2. **Patient matching** requires RAG over heterogeneous EHR data with clinical reasoning
3. **Site optimization** requires statistical modeling over historical enrollment data
4. **Enrollment monitoring** requires continuous time-series analysis with alerting

This mirrors production architectures at IQVIA and the research architecture of MAKAR. ClinicalAgent research demonstrated that multi-agent architectures outperform monolithic LLM approaches on clinical trial tasks.

---

## Integration Points

| System | Integration Method | Direction | Purpose |
|--------|------------------- |-----------|---------|
| Epic EHR | FHIR R4 REST API (SMART on FHIR) | Read | Patient demographics, conditions, observations, medications, notes |
| Oracle Health (Cerner) | FHIR R4 REST API (Ignite) | Read | Same as Epic; Cerner-specific resource profiles |
| ClinicalTrials.gov | FHIR R4 API + REST API v2 | Read | Trial protocol retrieval, eligibility criteria |
| Medidata Rave CTMS | REST API | Bidirectional | Read enrollment targets; write match results |
| Veeva Vault CTMS | REST API | Bidirectional | Same as Medidata; Veeva-specific data model |
| Azure AI Document Intelligence | REST API | Read | Extract text from PDF protocols and lab reports |
| Azure AI Search | REST API + SDK | Bidirectional | Index/query embedded patient records and trial criteria |
| Azure Cosmos DB | SDK | Write | Immutable audit logs, decision reasoning traces |

---

## Tools & Frameworks

### AI / ML Stack

| Component | Technology | Why Chosen |
|-----------|-----------|------------|
| **LLM Provider** | Azure OpenAI Service | HIPAA BAA available; data residency controls; enterprise SLA |
| **Model (Reasoning)** | GPT-4o (2024-11-20) | Best clinical reasoning accuracy; supports structured output; 128K context |
| **Model (Extraction)** | GPT-4o-mini | Lower cost for high-volume criteria extraction |
| **Agent Framework** | LangGraph (v1.0+) | Graph-based with checkpointing, HITL gates, conditional routing |
| **Vector Database** | Azure AI Search (hybrid) | BM25 lexical search (medical codes) + semantic vector search |
| **Embedding Model** | text-embedding-3-large (3072d) | High-dimensional embeddings for clinical semantic nuances |
| **Document Intelligence** | Azure AI Document Intelligence | Extracts structured data from PDFs and scanned reports |

### Infrastructure Stack

| Component | Technology | Why Chosen |
|-----------|-----------|------------|
| **Compute** | Azure Kubernetes Service (AKS) | Pod-level network policies for HIPAA compliance |
| **State Store** | Azure Database for PostgreSQL | LangGraph checkpointer backend; transactional consistency |
| **Audit Store** | Azure Cosmos DB | Immutable append-only logs for regulatory audit trails |
| **Monitoring** | Azure Application Insights | End-to-end tracing of agent decisions and metrics |
| **Secret Management** | Azure Key Vault | FHIR client credentials, API keys, connection strings |

---

## Security & Compliance

| Concern | Approach |
|---------|----------|
| **Authentication** | SMART on FHIR (OAuth 2.0) for EHR access; Azure Managed Identity for inter-service |
| **Authorization** | FHIR scopes limit data access to specific resource types; RBAC on Azure resources |
| **Data at Rest** | AES-256 encryption with customer-managed keys (CMK); Cosmos DB server-side encryption |
| **Data in Transit** | TLS 1.3 for all FHIR API calls; Azure Private Endpoints; no patient data on public internet |
| **PII Handling** | De-identification (Safe Harbor method); patient IDs replaced with study pseudonyms |
| **Audit Trail** | Every LLM call logged with input hash, output, model version, reasoning trace; 21 CFR Part 11 compliant timestamps |
| **Model Governance** | Azure OpenAI content filters enabled; custom prompt guardrails; model version pinning |
| **Regulatory** | System designed for ICH-GCP compliance; audit trails support FDA inspection readiness |

---

## Scalability & Performance

| Dimension | Approach |
|-----------|----------|
| **Throughput** | 500 patient evaluations/hour per trial; 50 concurrent active trials across 200 sites |
| **Latency Target** | Single patient-trial match: p50 < 15s, p95 < 45s; batch 100K records: < 4 hours |
| **Scaling Strategy** | Horizontal pod autoscaling on AKS; separate groups for each agent type |
| **Rate Limits** | Azure OpenAI provisioned throughput (PTU); queue-based backpressure with Service Bus |
| **Caching** | Protocol criteria cached after parsing; FHIR snapshots cached 24 hours; embeddings in AI Search |

---

## Cost Estimate

| Component | Unit Cost | Monthly Estimate (50 active trials) |
|-----------|----------|--------------------------------------|
| **Azure OpenAI GPT-4o (PTU)** | ~$60/hr per PTU | $8,600 (3 PTUs, 60% avg utilization) |
| **Azure OpenAI GPT-4o-mini** | $0.15/1M input tokens | $450 |
| **Azure AI Search (S1)** | $250/month per unit | $500 (2 search units) |
| **text-embedding-3-large** | $0.13/1M tokens | $260 |
| **AKS (D4s_v5 nodes)** | ~$140/month per node | $1,120 (8 nodes) |
| **Azure Database for PostgreSQL** | ~$200/month (4 vCores) | $200 |
| **Azure Cosmos DB** | ~$0.25/RU/s/month | $400 |
| **Azure Document Intelligence** | $1.50/page | $300 |
| **Total** | | **~$11,830/month** |

*Compared to: $500K-$2M/month in manual recruitment costs for a Phase III trial portfolio. Platform ROI typically achieved within the first 1-2 trials.*

---

## Alternatives Considered

| Alternative | Pros | Cons | Why Not Chosen |
|-------------|------|------|----------------|
| **Vendor platform (ConcertAI, Tempus)** | Production-proven; includes proprietary RWD | Vendor lock-in; high licensing costs; limited customization | Best for sponsors without engineering capacity |
| **Pure RAG pipeline (no agents)** | Simpler; lower cost; proven for initial retrieval | Cannot handle multi-step temporal reasoning; limited to retrieval | Insufficient for end-to-end recruitment orchestration |
| **Fine-tuned open-source LLM** | No API costs; full data control | Requires ML engineering; clinical reasoning inferior | Better as a component than complete solution |
| **Rule-based system with NLP** | Fully auditable; no hallucination risk | Cannot handle ambiguous criteria; brittle to protocol variation | Clinical eligibility criteria too complex for pure rules |
