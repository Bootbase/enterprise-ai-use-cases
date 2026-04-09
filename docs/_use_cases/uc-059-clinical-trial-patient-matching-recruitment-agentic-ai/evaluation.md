---
layout: use-case-detail
title: "Evaluation — UC-059: Autonomous Clinical Trial Patient Matching and Recruitment with Agentic AI"
uc_id: "UC-059"
uc_title: "Autonomous Clinical Trial Patient Matching and Recruitment with Agentic AI"
detail_type: "evaluation"
detail_title: "Evaluation"
category: "Industry-Specific"
status: "detailed"
slug: "uc-059-clinical-trial-patient-matching-recruitment-agentic-ai"
permalink: /use-cases/uc-059-clinical-trial-patient-matching-recruitment-agentic-ai/evaluation/
---

## Evaluation Overview

This evaluation synthesizes published results from production deployments and academic benchmarks of AI-powered clinical trial patient matching systems as of early 2026. Data sources include: Tempus TIME platform (8 oncology trials, 9,875 patients), Deep 6 AI (750+ provider sites), ConcertAI ACT, Mount Sinai PRISM deployment, TrialMatchAI (Nature Communications 2026), MAKAR multi-agent framework (arXiv 2024), and LLM-Match open-source benchmark.

---

## Baseline (Before AI)

| Metric | Value | Source |
|--------|-------|--------|
| **Patient identification time** | 15-20 hrs/week per coordinator for manual chart review | Tufts CSDD; site coordinator surveys |
| **Screen failure rate** | 15-30% across therapeutic areas | Tufts CSDD; industry benchmarks |
| **Enrollment timeline (Phase III)** | 12-18 months average | ClinicalTrials.gov analysis |
| **Cost per enrolled patient** | $6,500+ | Tufts CSDD |
| **Eligible patients missed** | ~20% of truly eligible patients not identified | JAMIA manual chart review studies |
| **Sites under-enroll** | 37% of sites enroll below target; 11% zero patients | Tufts CSDD |
| **Cost per screen failure** | $1,200 per failed screening | Industry benchmark |
| **Trial delay rate** | 80% of trials delayed by enrollment | Antidote Technologies |

---

## Results (After AI)

| Metric | Before AI | After AI | Change | Source |
|--------|-----------|----------|--------|--------|
| **Patient identification time** | Weeks per cohort | Minutes to hours | 170x speed improvement | Dyania Health / Cleveland Clinic |
| **Screen failure rate** | 15-30% | ~5-8% | -65 to -75% | Tempus TIME (8 trials, 9,875 patients) |
| **Enrollment timeline** | 12-18 months | 6-9 months | -25 to -50% | ConcertAI ACT |
| **Cost per enrolled patient** | $6,500+ | $2,600-$3,900 | -40 to -60% | Industry estimates |
| **Eligible patients identified** | ~80% found manually | 92% in top-20 recommendations | +15% recall | TrialMatchAI (Nature Comm 2026) |
| **Patient accrual rate** | Baseline | 3x faster | +200% | Deep 6 AI deployment |
| **Coordinator time on screening** | 15-20 hrs/week | 3-5 hrs/week | -75% | Estimated from 72% auto-screen-out |

---

## Quality Assessment

### Accuracy Evaluation

| Deployment | Sample Size | Accuracy | Notes |
|------------|-------------|----------|-------|
| **Tempus TIME (production, 8 oncology trials)** | 196 queries across 9,875 patients | 94.39% overall; range 84.62%-100% per query | Production deployment with nurse validation |
| **TrialMatchAI (oncology, real patients)** | Real clinical dataset | 92% top-20 retrieval recall; >90% criterion-level accuracy | Nature Communications 2026 |
| **MAKAR (n2c2 benchmark)** | Standard benchmark dataset | 100% in offline real-world test; +7% over baselines | Multi-agent framework |
| **LLM-Match (4 open benchmarks)** | n2c2, SIGIR, TREC datasets | Outperformed all baselines including GPT-4 zero-shot | Open-source fine-tuned model |
| **Dyania Health (oncology)** | Production deployment | 96% accuracy | Cleveland Clinic; minutes vs. hours |

### Failure Analysis

| Failure Mode | Frequency | Impact | Mitigation |
|-------------|-----------|--------|-----------|
| **Temporal reasoning errors** | 5-8% of criterion evaluations | Medium — incorrect inclusion based on outdated lab values | Explicit date arithmetic in prompt; Python temporal validation |
| **Missing EHR data (INSUFFICIENT_DATA)** | 10-15% of criteria per patient | Medium — routes to HITL review, not incorrect decisions | Hybrid search over clinical notes catches some data |
| **Negation handling in clinical notes** | 3-5% of note-based evaluations | High — "patient denies chest pain" misread as positive | Few-shot examples with negation; dedicated negation detection |
| **Rare biomarker criteria** | 2-4% of oncology trials | Medium — lower confidence on uncommon molecular markers | RAG over biomarker databases; lower confidence triggers review |
| **Protocol ambiguity** | 5-10% of criteria across trials | Medium — vague criteria cannot be automatically evaluated | Flag at extraction; auto-route to review; suggest protocol clarification |

---

## Cost Analysis

### Operational Costs (50 active trials)

| Cost Component | Monthly Cost | Notes |
|---------------|-------------|-------|
| **Azure OpenAI (GPT-4o PTU + tokens)** | $9,050 | 3 PTUs for matching + token-based extraction |
| **Azure AI Search (S1 x2)** | $500 | Hybrid index over patient records |
| **Embedding generation** | $260 | Incremental indexing |
| **AKS compute (8 nodes)** | $1,120 | Agent workload pods |
| **Azure PostgreSQL** | $200 | LangGraph state checkpointing |
| **Azure Cosmos DB** | $400 | Audit log writes |
| **Azure Document Intelligence** | $300 | Protocol PDF extraction |
| **Total Operational** | **~$11,830/month** | |

### ROI Calculation

| Factor | Value |
|--------|-------|
| **Previous cost: manual recruitment (single Phase III trial)** | $11.5M over 12-18 months |
| **AI solution cost (monthly, 50-trial portfolio)** | ~$11,830/month operational + $200K-$500K/year platform |
| **Recruitment cost reduction** | 40-60% reduction → $4.6M-$6.9M saved per Phase III trial |
| **Timeline acceleration value** | 25-50% faster → $1.8M-$72M in avoided delay costs |
| **Screen failure reduction** | From 25% to ~8% → ~$200K saved per trial |
| **Net savings per Phase III trial** | **$6.6M-$79.1M** |
| **Implementation cost** | $500K-$1M one-time (custom build) |
| **Payback period** | < 1 trial for custom build; immediate for vendor platforms |

*Note: ROI varies enormously by drug revenue potential. For a blockbuster drug ($1B+ annual revenue), each month of delay costs ~$83M.*

---

## User Feedback

### Quantitative

| Finding | Score / Metric | Source |
|---------|---|--------|
| AI-matched patients had higher screening pass rates | Statistically significant | Tempus TIME deployment |
| Coordinators report reduced manual review burden | 60-80% time reduction | Deep 6 AI site surveys |
| Clinicians prefer AI for equitable trial access | Qualitative endorsement | Mount Sinai PRISM |

### Qualitative

> "By deploying an AI platform trained specifically for oncology, we can identify trial opportunities earlier, more consistently, and more equitably, allowing clinicians to focus on meaningful conversations with patients."
> — Mount Sinai Tisch Cancer Center, PRISM deployment

> "Our platform streamlines site selection, activation, and recruitment, reducing timelines by 25-50% through automated validation strategies."
> — ConcertAI, ACT launch

> "Tempus evaluated 9,875 patients across 8 trials... the tool appropriately screened out ~72% of patients not currently eligible."
> — Tempus, Patient Query deployment

---

## Lessons Learned

### What Worked Well

- **Hybrid search (BM25 + vector) is essential for clinical data.** Pure semantic search misses exact medical codes; pure lexical search misses semantic equivalences. TrialMatchAI validated this approach.
- **Multi-agent specialization outperforms monolithic approaches.** MAKAR's separate augmentation and reasoning modules achieved 7-10% accuracy improvement over single-agent baselines.
- **Structured output schemas prevent hallucination.** Forcing LLMs to fill Pydantic models reduces fabricated data compared to free-text responses.
- **Starting with oncology yields fastest ROI.** Oncology trials have complex criteria, high recruitment costs, and urgent timelines.

### What Didn't Work

- **Pure rule-based matching was abandoned early.** Rule-based systems broke down on ambiguous criteria and unstructured data. LLM-based reasoning is necessary.
- **End-to-end fine-tuning on small datasets overfits.** RAG + prompting over general medical LLMs proved more robust.
- **Ignoring the site coordinator workflow led to low adoption.** Integration into existing CTMS workflows was critical for engagement.

---

## Next Steps

| Priority | Action | Expected Impact |
|----------|--------|-----------------|
| High | Run production pilot on 2-3 trials with full accuracy auditing | Validate matching quality and enrollment lift on real data |
| High | Implement HITL review workflow and train coordinators | Optimize human-AI collaboration patterns |
| Medium | Build multilingual NLP for global trial recruitment | Expand beyond English-language health systems |
| Medium | Integrate enrollment monitoring and corrective action automation | Complete the full recruitment lifecycle |
| Low | Expand to rare disease trials using specialized biomarker databases | Extend beyond oncology |
