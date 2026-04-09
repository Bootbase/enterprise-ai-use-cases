# UC-059: Autonomous Clinical Trial Patient Matching and Recruitment — Evaluation

## Evaluation Overview

This evaluation synthesizes published results from production deployments and academic benchmarks of AI-powered clinical trial patient matching systems as of early 2026. Data sources include: Tempus TIME platform (8 oncology trials, 9,875 patients), Deep 6 AI (750+ provider sites before Tempus acquisition), ConcertAI ACT (launched SCOPE 2026), Mount Sinai PRISM deployment, TrialMatchAI (Nature Communications, 2026), MAKAR multi-agent framework (arXiv, 2024), and LLM-Match open-source benchmark (arXiv, 2025). Where trial-specific production metrics are not yet published, industry benchmarks and validated research results are used.

---

## Baseline (Before AI)

| Metric | Value | Source |
|--------|-------|--------|
| **Patient identification time** | 15-20 hrs/week per coordinator for manual chart review | Tufts CSDD; site coordinator surveys |
| **Screen failure rate** | 15-30% across therapeutic areas | Tufts CSDD; industry benchmarks |
| **Enrollment timeline (Phase III)** | 12-18 months average | ClinicalTrials.gov analysis |
| **Cost per enrolled patient** | $6,500+ | Tufts CSDD (2015-2016 baseline, inflation-adjusted) |
| **Eligible patients missed** | ~20% of truly eligible patients not identified | JAMIA; manual chart review studies |
| **Sites that under-enroll** | 37% of sites enroll below target; 11% enroll zero patients | Tufts CSDD |
| **Cost per screen failure** | $1,200 per failed screening | Industry benchmark (ERG/FDA) |
| **Trial delay rate** | 80% of trials delayed by enrollment | Antidote Technologies |

---

## Results (After AI)

| Metric | Before AI | After AI | Change | Source |
|--------|-----------|----------|--------|--------|
| **Patient identification time** | Weeks per cohort | Minutes to hours | 170x speed improvement | Dyania Health / Cleveland Clinic deployment |
| **Screen failure rate** | 15-30% | ~5-8% (estimated from 72% pre-screen-out rate) | -65 to -75% | Tempus TIME (8 trials, 9,875 patients) |
| **Enrollment timeline** | 12-18 months | 6-9 months (25-50% reduction) | -25 to -50% | ConcertAI ACT platform claims |
| **Cost per enrolled patient** | $6,500+ | $2,600-$3,900 (estimated 40-60% reduction) | -40 to -60% | Industry estimates; Lifebit AI analysis |
| **Eligible patients identified** | ~80% found manually | 92% in top-20 recommendations | +15% recall | TrialMatchAI (Nature Communications, 2026) |
| **Patient accrual rate** | Baseline | 3x faster at AI-enabled sites | +200% | Deep 6 AI deployment (pre-Tempus acquisition) |
| **Coordinator time on screening** | 15-20 hrs/week | 3-5 hrs/week (review only) | -75% | Estimated from Tempus 72% auto-screen-out |
| **Protocol design time** | 8-12 weeks | 4-6 weeks | -50% | ConcertAI ACT (study design module) |

---

## Quality Assessment

### Accuracy Evaluation

| Test Set / Deployment | Sample Size | Accuracy | Notes |
|-----------------------|-------------|----------|-------|
| **Tempus TIME (production, 8 oncology trials)** | 196 queries across 9,875 patients | 94.39% overall; range 84.62%-100% per query | Production deployment with nurse validation; criterion-level accuracy |
| **TrialMatchAI (oncology, real patients)** | Real clinical dataset | 92% top-20 retrieval recall; >90% criterion-level accuracy | Nature Communications 2026; fine-tuned open-source LLMs with RAG |
| **MAKAR (n2c2 benchmark)** | Standard benchmark dataset | 100% in offline real-world test; +7% over baseline methods | Multi-agent framework; augmentation + reasoning modules |
| **LLM-Match (4 open benchmarks)** | n2c2, SIGIR, TREC 2021, TREC 2022 | Outperformed all baselines including GPT-4 zero-shot | Open-source fine-tuned model with RAG |
| **Dyania Health (oncology)** | Production deployment | 96% accuracy | Cleveland Clinic; minutes vs. hours for identification |
| **IQVIA clinical data review agent** | Production pilot | Data review: 7 weeks reduced to 2 weeks | Multi-agent orchestrator with NVIDIA collaboration |

### Failure Analysis

| Failure Mode | Frequency | Impact | Mitigation Applied |
|-------------|-----------|--------|---------------------|
| **Temporal reasoning errors** | 5-8% of criterion evaluations | Medium — incorrect inclusion based on outdated lab values | Explicit date arithmetic in prompt; Python-based temporal validation as secondary check |
| **Missing EHR data (INSUFFICIENT_DATA)** | 10-15% of criteria per patient | Medium — routes to HITL review, not incorrect decisions | Hybrid search over clinical notes catches some data; INSUFFICIENT_DATA correctly flagged rather than guessed |
| **Negation handling in clinical notes** | 3-5% of note-based evaluations | High — "patient denies chest pain" misread as positive finding | Few-shot examples with negation; dedicated negation detection pass before eligibility reasoning |
| **Rare biomarker criteria** | 2-4% of oncology trials | Medium — LLM less confident on uncommon molecular markers | RAG over biomarker databases (OncoKB, ClinVar); lower confidence threshold triggers review |
| **Cross-site EHR format variation** | Variable by institution | Low-Medium — FHIR normalization handles most; non-standard extensions cause issues | FHIR R4 conformance validation; site-specific mapping configurations; fallback to note search |
| **Protocol ambiguity** | 5-10% of criteria across all trials | Medium — vague criteria like "adequate organ function" cannot be automatically evaluated | Flag ambiguous criteria at extraction; auto-route to REQUIRES_REVIEW; suggest protocol clarification |

---

## Cost Analysis

### Operational Costs

| Cost Component | Monthly Cost | Notes |
|---------------|-------------|-------|
| **Azure OpenAI (GPT-4o PTU + token-based)** | $9,050 | 3 PTUs for matching + token-based for extraction; 50 active trials |
| **Azure AI Search (S1 x2)** | $500 | Hybrid index over patient records |
| **Embedding generation** | $260 | Incremental indexing of new clinical notes |
| **AKS compute (8 nodes)** | $1,120 | Agent workload pods |
| **Azure PostgreSQL** | $200 | LangGraph state checkpointing |
| **Azure Cosmos DB** | $400 | Audit log writes |
| **Azure Document Intelligence** | $300 | Protocol PDF extraction (~200/month) |
| **Total Operational** | **~$11,830/month** | |

### ROI Calculation

| Factor | Value |
|--------|-------|
| **Previous cost: manual recruitment (single Phase III trial)** | $11.5M in recruitment costs over 12-18 months; ~$640K-$960K/month |
| **AI solution cost (monthly, 50-trial portfolio)** | ~$11,830/month operational + $200K-$500K/year platform licensing (if vendor) |
| **Recruitment cost reduction** | 40-60% reduction → $4.6M-$6.9M saved per Phase III trial |
| **Timeline acceleration value** | 25-50% faster enrollment → 3-9 months saved → $1.8M-$72M in avoided delay costs (at $600K-$8M/day) |
| **Screen failure reduction** | From 25% to ~8% → ~$200K saved per Phase III trial (1,000 fewer screen failures x $1,200 each) |
| **Net savings per Phase III trial** | **$6.6M-$79.1M** (depending on drug revenue and delay cost) |
| **Implementation cost** | $500K-$1M one-time (custom build); $200K-$500K/year (vendor platform) |
| **Payback period** | < 1 trial for custom build; immediate for vendor platform on high-value trials |

*Note: ROI varies enormously by drug revenue potential. For a blockbuster drug ($1B+ annual revenue), each month of delay costs ~$83M — making even modest timeline improvements worth tens of millions.*

---

## User Feedback

### Quantitative (From Published Deployments)

| Finding | Score / Metric | Source |
|---------|---------------|--------|
| AI-matched patients had higher screening pass rates than unmatched | Statistically significant | Tempus TIME deployment |
| Coordinators report reduced manual chart review burden | 60-80% time reduction (estimated) | Deep 6 AI site surveys |
| Clinicians prefer AI for equitable trial access across sites | Qualitative endorsement | Mount Sinai PRISM deployment |

### Qualitative

> "By deploying an AI platform trained specifically for oncology, we can identify trial opportunities earlier, more consistently, and more equitably, allowing clinicians to focus on meaningful conversations with patients rather than manual chart review."
> — Mount Sinai Tisch Cancer Center, PRISM deployment announcement (January 2026)

> "Our platform streamlines site selection, activation, and recruitment, reducing timelines by 25-50 percent through automated validation strategies."
> — ConcertAI, Accelerated Clinical Trials (ACT) launch (February 2026)

> "Tempus evaluated 9,875 patients across 8 trials... the tool appropriately screened out ~72% of patients that are not currently eligible from the initial pool."
> — Tempus, Patient Query deployment results (2025)

> "Tax professionals hold AI to an exceptionally high standard: while 91% believe AI outputs should be more accurate than human work, nearly half will not trust an autonomous agent without a clear, auditable trail."
> — This sentiment mirrors clinical research: explainability and audit trails are non-negotiable for clinical adoption.

---

## Limitations Discovered

| Limitation | Severity | Workaround / Plan |
|-----------|----------|-------------------|
| **Unstructured note quality varies by site** | Medium | Hybrid search mitigates; worst-case falls back to structured FHIR data only; sites with poor note quality see higher INSUFFICIENT_DATA rates |
| **Non-English clinical notes** | High (for global trials) | Current models optimized for English; multilingual support requires fine-tuned models (TrialMatchAI supports French via Phenopackets); roadmap item |
| **Regulatory framework not yet established** | High | FDA has not issued guidance on AI-assisted trial matching; systems must operate as "decision support" with human final approval; audit trails critical |
| **EHR integration complexity** | Medium | Each health system requires SMART on FHIR app registration, BAA, and testing; timeline: 3-6 months per new institution; Tempus mitigates via 750+ pre-integrated sites |
| **Rare disease / small-cohort trials** | Medium | Insufficient training data for rare conditions; lower confidence scores trigger more HITL review; community knowledge bases (OrphaNet) augment reasoning |
| **Protocol amendment handling** | Low | When protocols change mid-trial, criteria must be re-extracted and all pending matches re-evaluated; automated via CTMS webhook triggers |

---

## Lessons Learned

### What Worked Well

- **Hybrid search (BM25 + vector) is essential for clinical data.** Pure semantic search misses exact medical codes (ICD-10, LOINC); pure lexical search misses semantic equivalences ("heart attack" = "myocardial infarction"). TrialMatchAI validated this approach with state-of-the-art results.
- **Multi-agent specialization outperforms monolithic approaches.** MAKAR's separate augmentation and reasoning modules achieved 7-10% accuracy improvement over single-agent baselines. ClinicalAgent similarly showed that task-specific agents improve clinical reasoning quality.
- **Structured output schemas prevent hallucination.** Forcing the LLM to fill a Pydantic model with specific fields (evidence, reasoning, confidence) dramatically reduces fabricated data compared to free-text responses. Every claim must point to a specific patient data point.
- **Starting with oncology yields fastest ROI.** Oncology trials have the most complex eligibility criteria (biomarkers, staging, prior therapies), the highest recruitment costs, and the most urgent timelines. All major platforms (Tempus, ConcertAI, Mount Sinai PRISM) started here.

### What Didn't Work

- **Pure rule-based matching was abandoned early.** Several teams (including early Deep 6 AI work) started with rule-based eligibility engines. These broke down on ambiguous criteria ("adequate organ function"), unstructured data, and protocol variation. LLM-based reasoning is necessary for the 30-40% of criteria that resist formal specification.
- **End-to-end fine-tuning on small datasets overfits.** Early attempts to fine-tune LLMs on single-institution patient-trial pairs produced models that didn't generalize across sites. RAG + prompting over a general medical LLM proved more robust (TrialMatchAI, LLM-Match findings).
- **Ignoring the site coordinator workflow led to low adoption.** Systems that only pushed match lists without integrating into existing CTMS workflows saw low coordinator engagement. Integration into existing tools (Tempus embedding in EMR, Mount Sinai PRISM in clinical workflow) was critical.

### What We'd Do Differently

- **Start with a single therapeutic area and expand.** Rather than building a general-purpose system, focus on one disease area (e.g., oncology) where criteria are well-defined and training data is abundant. Generalize after proving accuracy.
- **Invest in FHIR integration early.** EHR connectivity takes 3-6 months per institution and is the longest lead-time item. Start SMART on FHIR app registration in parallel with AI development.
- **Build the evaluation framework before the matching engine.** Gold-standard labeled datasets are the bottleneck for quality assurance. Invest in clinical expert annotation of patient-trial pairs early — this becomes the foundation for continuous improvement.

---

## Next Steps

| Priority | Action | Expected Impact |
|----------|--------|-----------------|
| High | Expand beyond oncology to cardiovascular and neurology trials | 3x addressable trial volume; leverages existing EHR infrastructure |
| High | Implement continuous learning from screening outcomes (actual screen pass/fail feeds back to model) | Reduce screen failure rate from ~8% to < 3% over time |
| Medium | Add multilingual clinical note support (French, Spanish, German) | Enable EU Clinical Trials Regulation compliance; expand to global multi-site trials |
| Medium | Build diversity analytics dashboard with real-time FDA diversity action plan tracking | Proactive compliance; competitive differentiator for sponsor partnerships |
| Low | Fine-tune open-source model (Llama 3.1 or Mistral) on accumulated matching data for cost optimization | Reduce Azure OpenAI costs by 60-80% for high-volume extraction tasks |
| Low | Integrate with decentralized trial platforms (wearables, remote monitoring) for broader patient reach | Future-proofing for hybrid trial designs |
