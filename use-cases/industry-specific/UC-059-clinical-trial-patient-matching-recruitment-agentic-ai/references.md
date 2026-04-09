# UC-059: Autonomous Clinical Trial Patient Matching and Recruitment — References

## Case Studies

| Company / Project | Industry | Relevance | Link |
|------------------|----------|-----------|------|
| ConcertAI Accelerated Clinical Trials (ACT) | Pharmaceutical / CRO | Enterprise agentic AI platform for end-to-end trial automation; 10-20 month timeline reduction; launched SCOPE 2026 | https://www.concertai.com/act |
| Tempus TIME + Patient Query | Pharmaceutical / Oncology | Production deployment across 8 trials, 9,875 patients; 94.39% accuracy; 72% auto-screen-out rate | https://www.tempus.com/resources/content/articles/improving-patient-matching-efficiency-with-an-ai-powered-platform-2/ |
| Deep 6 AI (acquired by Tempus) | Healthcare / Clinical Research | AI-powered EHR mining for patient matching; 3x faster accrual; 750+ provider sites; acquired by Tempus March 2025 | https://deep6.ai/how-it-works/ |
| Mount Sinai PRISM (Triomics OncoLLM) | Healthcare / Oncology | First NCI-designated cancer center in NYC to deploy systemwide AI trial matching; January 2026 | https://www.mountsinai.org/about/newsroom/2026/mount-sinai-launches-ai-powered-clinical-trial-matching-platform-to-expand-access-to-cancer-research |
| IQVIA + NVIDIA Multi-Agent AI | Pharmaceutical / CRO | Multi-agent orchestrator for clinical trial start-up; data review from 7 weeks to 2 weeks | https://www.iqvia.com/blogs/2025/11/driving-faster-clinical-timelines-and-patient-impact-with-agentic-ai |
| Dyania Health | Healthcare / Oncology | 96% accuracy; 170x speed improvement at Cleveland Clinic | https://www.aha.org/aha-center-health-innovation-market-scan/2025-10-21-how-ai-transforming-clinical-trials |
| Deep Intelligent Pharma (DIP) | Pharmaceutical | Multi-agent intelligence for patient identification and screening; claims up to 1000% efficiency gains with >99% accuracy | https://www.dip-ai.com/use-cases/en/the-best-AI-patient-recruitment |

---

## Technical Documentation

| Resource | Type | What It Covers | Link |
|----------|------|---------------|------|
| FHIR R4 Patient Resource Specification | Official Spec | Patient resource structure, demographics, extensions for race/ethnicity | https://hl7.org/fhir/R4/patient.html |
| ClinicalTrials.gov FHIR API | Official API | Accessing trial data (eligibility criteria, study metadata) via FHIR R4 | https://clinicaltrials.gov/data-api/fhir |
| SMART on FHIR Authorization | Official Spec | OAuth 2.0 flows for EHR API access (backend services, patient launch) | https://docs.smarthealthit.org/ |
| Azure OpenAI Structured Outputs | Official Docs | JSON mode and Pydantic model-based structured output for reliable extraction | https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/structured-outputs |
| LangGraph Documentation | Official Docs | StateGraph, checkpointing, human-in-the-loop, conditional edges | https://langchain-ai.github.io/langgraph/ |
| Azure AI Search Hybrid Search | Official Docs | Combining BM25 lexical + vector semantic search; semantic ranking | https://learn.microsoft.com/en-us/azure/search/hybrid-search-overview |
| fhir.resources Python Package | Library Docs | Pydantic-based FHIR R4 resource models for Python | https://github.com/glichtner/fhir.resources |
| Cerner Ignite FHIR R4 Patient API | Official Docs | Oracle Health (Cerner) FHIR R4 implementation specifics | https://fhir.cerner.com/millennium/r4/base/individuals/patient/ |

---

## Architecture References

| Resource | Type | What It Covers | Link |
|----------|------|---------------|------|
| AI Agents in Clinical Trials: Late-2025 State of the Art | Industry Analysis | Survey of agent architectures, benchmarks, and deployment status in clinical trials | https://medium.com/@leonidas/ai-agents-in-clinical-trials-late-2025-state-of-the-art-dd95432087b1 |
| Multiagent AI Systems in Health Care: Envisioning Next-Generation Intelligence | Review (PMC) | Multi-agent architectures for healthcare; coordination patterns; safety considerations | https://pmc.ncbi.nlm.nih.gov/articles/PMC12360800/ |
| LangGraph vs Semantic Kernel: Python AI Agents in 2026 | Comparison | Framework comparison for agent orchestration; LangGraph graph-based vs. Semantic Kernel plugin model | https://dev.to/theprodsde/langgraph-vs-semantic-kernel-python-ai-agents-in-2026-1p4g |
| Awesome AI Agents for Healthcare | Curated List | Comprehensive list of AI agent systems for healthcare applications, including clinical trial matching | https://github.com/AgenticHealthAI/Awesome-AI-Agents-for-Healthcare |
| FHIR-based Clinical Trial Recruitment Support System | Implementation Study | FHIR R4 eligibility criteria implementation for automated patient screening in cardiology | https://pmc.ncbi.nlm.nih.gov/articles/PMC9619584/ |

---

## Code Repositories & Examples

| Repository | Language | What It Demonstrates | Link |
|-----------|----------|---------------------|------|
| cbib/TrialMatchAI | Python | End-to-end RAG-based clinical trial matching with fine-tuned LLMs; hybrid search; criterion-level evaluation | https://github.com/cbib/TrialMatchAI |
| smart-on-fhir/client-py | Python | SMART on FHIR client library for Python; OAuth 2.0 flows; resource querying | https://github.com/smart-on-fhir/client-py |
| glichtner/fhir.resources | Python | Pydantic-based FHIR R4/R5 resource models; validation; serialization | https://github.com/glichtner/fhir.resources |
| AgenticHealthAI/Awesome-AI-Agents-for-Healthcare | Multi | Curated list of healthcare AI agent repos, papers, and tools | https://github.com/AgenticHealthAI/Awesome-AI-Agents-for-Healthcare |

---

## Conference Talks & Videos

| Title | Event | Speaker | Date | Link |
|-------|-------|---------|------|------|
| ConcertAI ACT Launch: Agentic AI for Clinical Trials | SCOPE 2026 (Orlando) | ConcertAI | February 2026 | https://www.concertai.com/news/concertai-launches-accelerated-clinical-trials-leveraging-agentic-ai-to-streamline-trial-timelines |
| IQVIA + NVIDIA: Building AI Agents for Clinical Research | NVIDIA GTC / IQVIA | IQVIA | June 2025 | https://www.clinicalresearchnewsonline.com/news/2025/06/11/iqvia-nvidia-build-ai-agents-for-clinical-research |
| Is Agentic AI the Next Leap Forward for Clinical Trial Data Management? | Clinical Research News | Industry | March 2026 | https://www.clinicalresearchnewsonline.com/news/2026/03/20/is-agentic-ai-the--next-leap-forward--for-clinical-trial-data-management |
| Next Steps in Artificial Intelligence: Agentic AI | DIA Global Forum | DIA | August 2025 | https://globalforum.diaglobal.org/issue/august-2025/next-steps-in-artificial-intelligence-agentic-ai/ |

---

## Related Use Cases

| Use Case ID | Title | Relationship |
|-------------|-------|-------------|
| UC-050 | Autonomous Adverse Event Report Processing in Pharmacovigilance | Same industry (pharma); complementary use case — UC-050 handles post-market safety, UC-059 handles pre-market recruitment. Share FHIR integration patterns. |
| UC-055 | Autonomous Clinical Documentation and Medical Coding with Agentic AI | Adjacent healthcare domain; shares clinical NLP and EHR integration patterns; different application (care documentation vs. trial recruitment) |
| UC-001 | Autonomous Accounts Payable Invoice Processing | Different domain but shares the multi-agent orchestrator-worker pattern and document extraction architecture |
| UC-041 | Autonomous Regulatory Change Intelligence | Shares regulatory compliance patterns; trial matching must track evolving FDA guidance on AI and diversity requirements |

---

## Tools & Framework Documentation

| Tool / Framework | Version | Documentation | Link |
|-----------------|---------|--------------|------|
| LangGraph | 1.0+ | Official documentation — StateGraph, checkpointing, human-in-the-loop | https://langchain-ai.github.io/langgraph/ |
| langchain-openai | 0.3+ | Azure OpenAI integration for LangChain/LangGraph | https://python.langchain.com/docs/integrations/chat/azure_chat_openai/ |
| fhir.resources | 8.0+ | Pydantic-based FHIR resource models | https://pypi.org/project/fhir.resources/ |
| Azure AI Search | Latest | Hybrid search, vector search, semantic ranking | https://learn.microsoft.com/en-us/azure/search/ |
| Azure OpenAI Service | 2024-10-21 API | GPT-4o, structured outputs, provisioned throughput | https://learn.microsoft.com/en-us/azure/ai-services/openai/ |
| Azure AI Document Intelligence | Latest | PDF extraction, custom models for healthcare documents | https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/ |
| FHIR-PYrate | Latest | Python package for querying FHIR servers; returns pandas DataFrames | https://link.springer.com/article/10.1186/s12913-023-09498-1 |

---

## Research Papers

| Title | Authors | Year | Relevance | Link |
|-------|---------|------|-----------|------|
| TrialMatchAI: An End-to-End AI-powered Clinical Trial Recommendation System | Delmas et al. | 2025-2026 | RAG + fine-tuned LLM architecture; 92% top-20 recall; >90% criterion accuracy; open-source | https://www.nature.com/articles/s41467-026-70509-w |
| Enhancing Clinical Trial Patient Matching through Knowledge Augmentation and Reasoning with Multi-Agents (MAKAR) | Authors (arXiv) | 2024 | Multi-agent framework with augmentation + reasoning modules; 100% accuracy in offline test; +7% over baselines | https://arxiv.org/abs/2411.14637 |
| ClinicalAgent: Clinical Trial Multi-Agent System with Large Language Model-based Reasoning | Authors (arXiv) | 2024 | First multi-agent framework for clinical trial tasks; GPT-4 + ReAct; 0.79 PR-AUC on outcome prediction | https://arxiv.org/abs/2404.14777 |
| LLM-Match: An Open-Sourced Patient Matching Model Based on LLMs and RAG | Li et al. | 2025 | Open-source fine-tuned model with RAG; outperforms GPT-4 zero-shot on n2c2, SIGIR, TREC benchmarks | https://arxiv.org/abs/2503.13281 |
| PRISM: Patient Records Interpretation for Semantic Clinical Trial Matching | Authors (npj Digital Medicine) | 2024 | LLM-based semantic matching system; deployed at Mount Sinai | https://www.nature.com/articles/s41746-024-01274-7 |
| Matching Patients to Clinical Trials with Large Language Models | Jin et al. (Nature Communications) | 2024 | Foundational paper on LLM-based patient-trial matching; benchmark establishment | https://www.nature.com/articles/s41467-024-53081-z |
| Cohort Discovery: A Survey on LLM-Assisted Clinical Trial Recruitment | Authors (arXiv) | 2025 | Comprehensive survey of LLM approaches to trial recruitment; taxonomy of methods | https://arxiv.org/abs/2506.15301 |
| AI and Innovation in Clinical Trials | Authors (npj Digital Medicine) | 2025 | Review of AI applications across clinical trial lifecycle; regulatory considerations | https://www.nature.com/articles/s41746-025-02048-5 |
| AI in Clinical Trials Market Research 2026 | GlobeNewsWire | 2026 | Market projected to reach $18.62B by 2040; key players: IQVIA, Medidata, Phesi | https://www.globenewswire.com/news-release/2026/03/02/3247122/28124/en/AI-in-Clinical-Trials-Market-Research-2026-Market-to-Reach-18-62-Billion-by-2040 |

---

## Market & Industry Reports

| Resource | Publisher | What It Covers | Link |
|----------|----------|---------------|------|
| How AI Is Transforming Clinical Trials | American Hospital Association | Overview of AI adoption in clinical trials; Dyania Health/Cleveland Clinic case study | https://www.aha.org/aha-center-health-innovation-market-scan/2025-10-21-how-ai-transforming-clinical-trials |
| Agentic AI: A Game Changer in Clinical Trials | Everest Group | Multi-agent AI architectures for clinical trials; industry adoption analysis | https://www.everestgrp.com/blog/agentic-artificial-intelligence-ai-a-game-changer-in-clinical-trials.html |
| AI Clinical Trial Optimization Guide 2026 | Lifebit | Comprehensive guide to AI in trial optimization; cost and timeline benchmarks | https://lifebit.ai/blog/ai-clinical-trial-optimization-guide-2026/ |
| Oncology Trial Systems Debut at SCOPE 2026 | Clinical Trials Arena | SCOPE 2026 conference coverage; ConcertAI ACT and competing platforms | https://www.clinicaltrialsarena.com/news/oncology-trial-systems-debut-at-scope-2026-as-ai-adoption-accelerates/ |
| Tempus Acquires Deep 6 AI | Tempus | Acquisition expanding Tempus platform to 750+ provider sites | https://www.tempus.com/news/pr/tempus-announces-acquisition-of-deep-6-ai/ |
