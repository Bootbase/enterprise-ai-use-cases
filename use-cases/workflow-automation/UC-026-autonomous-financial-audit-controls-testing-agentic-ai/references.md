# UC-026: Autonomous Financial Audit and Internal Controls Testing — References

## Case Studies

| Company / Project | Industry | Relevance | Link |
|-------------------|----------|-----------|------|
| EY — Enterprise-scale agentic AI in Assurance | Professional Services | Global rollout of multi-agent AI in EY Canvas; 130K professionals, 160K engagements, 1.4T journal entry lines/year; Azure + Microsoft Foundry + Fabric integration | [EY Newsroom (April 2026)](https://www.ey.com/en_us/newsroom/2026/04/ey-launches-enterprise-scale-agentic-ai-to-redefine-the-audit-experience-for-the-ai-era) |
| PwC — End-to-end AI audit automation | Professional Services | AI-native audit platform with intelligent agents for every audit step; Evidence Match agent for automated evidence extraction and validation; expected for calendar 2026 audits | [Accounting Today](https://www.accountingtoday.com/news/pwc-expects-end-to-end-ai-audit-automation-within-2026) |
| PwC — AI audit technology development | Professional Services | Detailed overview of AI tools in audit: planning, walkthroughs, evidence collection, testing, review | [PwC Newsroom](https://www.pwc.com/us/en/about-us/newsroom/press-releases/reimagining-audit-with-ai-technology.html) |
| KPMG — Clara AI smart audit platform on Azure | Professional Services | Azure AI Foundry-based modernization of audit; analyzes entire datasets; global deployment | [Microsoft Customer Story](https://www.microsoft.com/en/customers/story/25353-kpmg-international-azure) |
| KPMG — Workbench multi-agent AI platform | Professional Services | 50+ AI agents deployed, nearly 1,000 in development; Azure AI Foundry + Cosmos DB; agent-to-agent coordination | [KPMG US Media](https://kpmg.com/us/en/media/news/kpmg-launches-kpmg-workbench-a-multi-agent-ai-platform.html) |
| AuditBoard/Optro — Accelerate AI suite | GRC Software | Audit Agent for accelerated controls testing and documentation; continuous auditing and monitoring; 150+ enterprise system integrations | [AuditBoard/Optro Press Release](https://optro.ai/blog/auditboard-launches-accelerate-delivering-enterprise-grade-ai-automation-for-grc-teams) |
| MindBridge — AI-powered financial risk discovery | Audit Analytics | 260B+ transactions analyzed, 3,000+ ERP systems, 8,000+ GAAP rules, 32 detection algorithms; 100% population testing | [MindBridge Platform](https://www.mindbridge.ai/platform/) |
| Deloitte — Project 120 AI investment | Professional Services | $1.4B investment in AI capabilities; Zora AI for procurement | [Emerj — AI in Big Four](https://emerj.com/ai-in-the-accounting-big-four-comparing-deloitte-pwc-kpmg-and-ey/) |

---

## Technical Documentation

| Resource | Type | What It Covers | Link |
|----------|------|----------------|------|
| Azure OpenAI Structured Outputs | Official Docs | How to enforce JSON Schema responses from Azure OpenAI models using Pydantic; used for audit evidence matching and workpaper generation | [Microsoft Learn](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs) |
| Azure OpenAI Entity Extraction with Structured Outputs | Tutorial | Step-by-step guide for extracting structured entities from documents; applicable to audit evidence extraction | [Microsoft Learn](https://learn.microsoft.com/en-us/azure/developer/ai/how-to/extract-entities-using-structured-outputs) |
| Azure Document Intelligence | Product Docs | Prebuilt invoice model, custom models, layout-aware OCR for financial document processing | [Azure Product Page](https://azure.microsoft.com/en-us/products/ai-foundry/tools/document-intelligence) |
| Best Practices for Structured Extraction from Documents Using Azure OpenAI | Blog | Chunked processing, schema enforcement, confidence scoring for financial document pipelines | [Microsoft Tech Community](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/best-practices-for-structured-extraction-from-documents-using-azure-openai/4397282) |
| LangGraph — Workflows and Agents | Official Docs | StateGraph, conditional edges, tool-calling agents, checkpointing — core orchestration patterns used in this solution | [LangChain Docs](https://docs.langchain.com/oss/python/langgraph/workflows-agents) |
| LangGraph Agent Orchestration Framework | Product Page | Overview of LangGraph capabilities: graph-based multi-agent orchestration, state management, human-in-the-loop | [LangChain Product Page](https://www.langchain.com/langgraph) |
| PCAOB AS 2315 — Audit Sampling | Regulatory Standard | Authoritative guidance on statistical sampling in audits; defines sampling risk, sample size determination, and evaluation of results | [PCAOB](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2315) |
| Wolters Kluwer — Is Sampling Enough for Internal Controls Testing? | Analysis | Quantifies probability of missing control failures with sample-based testing (83% miss rate for monthly controls with 2 samples) | [Wolters Kluwer Expert Insights](https://www.wolterskluwer.com/en/expert-insights/audit-analytics-is-sampling-enough-for-internal-controls-testing) |

---

## Architecture References

| Resource | Type | What It Covers | Link |
|----------|------|----------------|------|
| Azure Architecture Center — Multi-Modal Content Processing | Reference Architecture | Pattern for extracting and mapping information from unstructured content using Azure Document Intelligence + OpenAI | [Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/idea/multi-modal-content-processing) |
| Agentic AI in Financial Services — Multi-Agent Patterns (AWS) | Design Guide | Choosing the right multi-agent pattern for financial services: supervisor, hierarchical, network topologies | [AWS Blog](https://aws.amazon.com/blogs/industries/agentic-ai-in-financial-services-choosing-the-right-pattern-for-multi-agent-systems/) |
| Multi-Agent Orchestration with Microsoft Semantic Kernel | Technical Blog | Enterprise multi-agent patterns using Semantic Kernel; comparison with LangGraph approach | [ElixirClaw AI](https://www.elixirclaw.ai/blog/multi-agent-with-microsoft-semantic-kernel) |
| IIA GTAG-3 — Continuous Auditing | Professional Guidance | Framework for implementing continuous auditing: concepts, technology requirements, integration with internal audit | [IIA Global](https://www.theiia.org/globalassets/documents/content/articles/guidance/gtag/gtag-3-continuous-auditing/gtag-3-continuous-auditing-2nd-edition.pdf) |
| MindBridge — Continuous Auditing with AI | Blog | Real-time accountability with AI-powered decision intelligence; continuous controls monitoring approach | [MindBridge Blog](https://www.mindbridge.ai/blog/continuous-auditing-real-time-accountability-with-ai-powered-decision-intelligence/) |
| RSM — Reimagine Internal Audit with Agentic AI | Insights | Practical guidance for implementing agentic AI in internal audit; stages of adoption | [RSM Insights](https://rsmus.com/insights/services/digital-transformation/agentic-ai-for-internal-audit.html) |

---

## Code Repositories & Examples

| Repository | Language | What It Demonstrates | Link |
|-----------|----------|---------------------|------|
| LangGraph (langchain-ai/langgraph) | Python | Multi-agent orchestration framework; StateGraph, checkpointing, tool-calling — the core framework used in this solution | [GitHub](https://github.com/langchain-ai/langgraph) |
| Marco Schreyer — AI for Accounting & Auditing | Python | Research code for autoencoder-based anomaly detection on accounting data; companion to Schreyer et al. papers | [GitHub](https://gitihubi.github.io/) |
| Azure OpenAI Samples | Python | Function calling, structured output, and RAG patterns with Azure OpenAI | [Microsoft Learn Samples](https://learn.microsoft.com/en-us/azure/developer/ai/how-to/extract-entities-using-structured-outputs) |

---

## Conference Talks & Videos

| Title | Event | Speaker | Date | Link |
|-------|-------|---------|------|------|
| Agentic AI in Internal Auditing | All Things Internal Audit Podcast | IIA Panel | 2025 | [IIA Podcast](https://www.theiia.org/en/content/podcast/all-things-internal-audit/2025/agentic-ai-in-internal-auditing/) |
| IIA GAM 2025 Recap: The AI-Powered Future of Internal Audit | IIA Great Audit Minds Conference | MindBridge | 2025 | [MindBridge Blog](https://www.mindbridge.ai/blog/iia-gam-2025-recap-the-ai-powered-future-of-internal-audit-is-here/) |

---

## Related Use Cases

| Use Case ID | Title | Relationship |
|------------|-------|-------------|
| UC-024 | Autonomous Financial Close and Account Reconciliation | Upstream process — financial close produces the GL data that this use case audits; quality of close data directly impacts audit findings |
| UC-025 | Autonomous Multi-Jurisdiction Tax Compliance and Filing | Adjacent domain — tax compliance and audit share ERP data sources and regulatory frameworks; explicitly out of scope for this use case |
| UC-041 | Autonomous Regulatory Change Intelligence | Complementary — regulatory change intelligence feeds updated accounting standards into this use case's RAG knowledge base |
| UC-001 | Autonomous AP Invoice Processing | Overlapping technology — AP invoice processing uses similar Document Intelligence + LLM extraction patterns; tested controls in this use case include AP three-way match |

---

## Tools & Framework Documentation

| Tool / Framework | Version | Documentation | Link |
|-----------------|---------|---------------|------|
| LangGraph | 0.3.x | Official documentation — StateGraph, agents, checkpointing, human-in-the-loop | [LangChain Docs](https://docs.langchain.com/oss/python/langgraph/workflows-agents) |
| Azure OpenAI Service | 2024-12-01-preview API | REST API reference, structured outputs, function calling | [Microsoft Learn](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs) |
| Azure AI Document Intelligence | 4.0 GA | Prebuilt invoice model, custom models, layout API | [Azure Product Docs](https://azure.microsoft.com/en-us/products/ai-foundry/tools/document-intelligence) |
| Azure AI Search | Latest | Hybrid search (keyword + semantic), vector indexing, RBAC | [Microsoft Learn](https://learn.microsoft.com/en-us/azure/search/) |
| Azure Cosmos DB | Latest | Python SDK, serverless mode, change feed for state management | [Microsoft Learn](https://learn.microsoft.com/en-us/azure/cosmos-db/) |
| scikit-learn (Isolation Forest) | 1.5.x | IsolationForest class — unsupervised anomaly detection | [scikit-learn Docs](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html) |
| PyTorch | 2.x | Autoencoder implementation for journal entry anomaly detection | [PyTorch Docs](https://pytorch.org/docs/stable/) |
| pyrfc (SAP RFC connector) | 3.x | Python connector for SAP RFC function calls (BAPI access) | [PyPI](https://pypi.org/project/pyrfc/) |

---

## Research Papers

| Title | Authors | Year | Relevance | Link |
|-------|---------|------|-----------|------|
| Detection of Anomalies in Large Scale Accounting Data using Deep Autoencoder Networks | Schreyer, Sattarov, Borth, Dengel, Reimer | 2017 | Foundational paper on using deep autoencoders for journal entry anomaly detection; tested on 2 real-world datasets with F1-scores of 32.93 and 16.95 | [arXiv:1709.05254](https://arxiv.org/abs/1709.05254) |
| Detection of Accounting Anomalies in the Latent Space using Adversarial Autoencoder Neural Networks | Schreyer, Sattarov, Schulze, Reimer, Borth | 2019 | Extended autoencoder approach with adversarial training for improved interpretability; validated by forensic accountants | [arXiv:1908.00734](https://arxiv.org/abs/1908.00734) |
| Enhancing Anomaly Detection in Financial Markets with an LLM-based Multi-Agent Framework | Multiple authors | 2024 | Multi-agent LLM framework for financial anomaly detection with specialized agents for data conversion, expert analysis, and report consolidation | [arXiv:2403.19735](https://arxiv.org/html/2403.19735v1) |
| Detecting Anomalies in Financial Data Using Machine Learning Algorithms | Multiple authors | 2022 | Comparison of 7 supervised and 2 unsupervised ML techniques (including Isolation Forest and autoencoders) for accounting anomaly detection | [MDPI Systems](https://www.mdpi.com/2079-8954/10/5/130) |
| Automating Supply Chain Disruption Monitoring via an Agentic AI Approach | Multiple authors | 2026 | Agentic AI architecture patterns applicable to monitoring and autonomous response; transferable patterns for continuous audit monitoring | [arXiv:2601.09680](https://arxiv.org/html/2601.09680v1) |
