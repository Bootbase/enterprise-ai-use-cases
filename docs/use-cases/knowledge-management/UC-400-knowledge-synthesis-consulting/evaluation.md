---
layout: use-case-detail
title: "Evaluation — Autonomous Knowledge Synthesis and Research Copilot for Management Consultants with Agentic AI"
uc_id: "UC-400"
uc_title: "Autonomous Knowledge Synthesis and Research Copilot for Management Consultants with Agentic AI"
detail_type: "evaluation"
detail_title: "Evaluation"
category: "Knowledge Management"
category_icon: "book-open"
industry: "Professional Services (Management Consulting, Strategy, Audit & Advisory)"
complexity: "High"
status: "detailed"
slug: "UC-400-knowledge-synthesis-consulting"
permalink: /use-cases/UC-400-knowledge-synthesis-consulting/evaluation/
---

## Decision Summary

The business case for an internal knowledge synthesis platform in management consulting is strong and backed by production-scale evidence from McKinsey's Lilli deployment (75% firmwide adoption, 30% research time savings) and a rigorous randomized field experiment at BCG (758 consultants, 12.2% more tasks completed, 25.1% faster, 40%+ quality improvement on inside-frontier tasks). The evidence base is unusually deep for an enterprise AI use case: it includes first-party production metrics from the world's largest consulting firm and a Harvard-published controlled experiment. The business case holds if the firm can build a reliable retrieval layer over its proprietary corpus and enforce information barriers without degrading retrieval quality. The main risk is automation bias — the same BCG experiment showed a 19-percentage-point accuracy drop when consultants deferred to AI on tasks outside its capability boundary. [S1][S2][S3][S4]

## Published Evidence

| Deployment / Source | Published Metric | What It Shows |
|---------------------|------------------|---------------|
| McKinsey Lilli (firmwide since July 2023) [S1][S2] | 75% of ~43,000 employees active monthly; 500,000+ prompts/month; ~17 prompts/week per active user; 30% time savings in searching and synthesizing knowledge. | A knowledge synthesis platform achieves high sustained adoption when it demonstrably saves time on daily research tasks. The 30% figure is self-reported by McKinsey but is consistent across multiple public statements. |
| Harvard-BCG randomized experiment (758 consultants, GPT-4) [S3][S4] | +12.2% more tasks completed; 25.1% faster; 40%+ higher quality (human-rated). Lower-performing consultants gained 43% quality improvement; top performers gained 17%. | AI-assisted consultants significantly outperform unassisted ones on tasks within the model's capability boundary. The skill-leveling effect suggests the largest productivity gains accrue to junior consultants, who are the primary target for knowledge synthesis tools. |
| Harvard-BCG experiment — outside-frontier tasks [S3][S4] | Accuracy dropped from 84.5% (no AI) to ~65% (with AI) on a task requiring integration of quantitative and qualitative data. | AI assistance can degrade performance when consultants defer to confidently wrong outputs. This is the core risk that mandatory human review mitigates. |
| BCG follow-up study (480 consultants, GPT-4, 2024) [S13] | AI-assisted consultants reached 86% of data-scientist performance on coding tasks — a 49-percentage-point improvement over non-AI consultants. | GenAI can extend consultants' capabilities well beyond their training, but knowledge retention does not improve — the tool augments performance in the moment without building lasting skill. |
| BCG Deckster (firmwide since March 2024) [S6] | 450,000+ slide creations/edits; ~40% of associates use it weekly. | Slide-generation tools reach high adoption quickly when integrated into existing workflows. |
| BCG AI adoption (2024) [S6] | 90% of BCG employees use AI tools; 50% use AI daily; 70% of saved time reinvested in higher-value client work. | Firmwide adoption is achievable with training and cultural investment. The reinvestment figure suggests productivity gains translate to revenue, not headcount reduction. |

## Assumptions And Scenario Model

The scenario below models a mid-sized consulting firm (5,000 consultants, representative of a large national firm or a single region of a Big Four). All cost figures are estimates derived from published benchmarks.

| Assumption | Value | Basis |
|------------|-------|-------|
| Consultant headcount | 5,000 | Mid-sized firm or single region of a large firm. |
| Fully loaded consultant cost | $250/hour | Industry range $200–400/hour; midpoint for a blended junior-to-senior mix. |
| Weekly hours spent on research and synthesis per consultant | 15 hours (30% of 50-hour week) | Consistent with McKinsey's reported 30% research time and industry estimates of 30–50% for junior roles. [S1][S2] |
| Adoption rate at steady state | 70% of consultants active monthly | Conservative relative to McKinsey's 75%. [S1] |
| Time savings per active user | 20% of research hours (3 hours/week) | Conservative: McKinsey reports 30% savings; this assumes a less mature corpus and smaller firm scale. |
| Platform cost per query (LLM + retrieval + compute) | $0.08 fully loaded | At scale, multi-model routing keeps per-query costs below $0.10. McKinsey's index brief targets < $0.10. |
| Prompts per active user per week | 15 | McKinsey benchmark: 17/week. [S1] |

## Expected Economics

| Factor | Value | Note |
|--------|-------|------|
| **Current cost of research time** | ~$975M/year | 5,000 consultants × 15 hours/week × 50 weeks × $250/hour. This is the addressable labor pool, not a savings target. Estimated. |
| **Expected steady-state savings** | ~$136M/year in redeployable research capacity | 3,500 active users × 3 hours saved/week × 50 weeks × $250/hour. This is labor redeployed to higher-value work, not a cash saving. Estimated. |
| **Platform operating cost** | ~$2.2M/year | 3,500 users × 15 prompts/week × 50 weeks × $0.08/query = $2.1M. Add ~$100K for infrastructure overhead. Estimated. |
| **Implementation cost (Phase 1–4)** | $2–4M | 8-week build with a team of 6–10 engineers plus corpus ingestion, compliance setup, and pilot management. Estimated based on comparable enterprise RAG projects. |
| **Payback view** | Under 1 year | Implementation cost recovered within first year of operation. The economics improve as corpus quality and adoption increase. Estimated. |

## Quality, Risk, And Failure Modes

| Area | Strength / Risk | Control Or Mitigation |
|------|-----------------|-----------------------|
| Evidence quality | **Strength**: Production-scale evidence from McKinsey (43,000 users) and a controlled experiment at BCG (758 consultants). This is among the strongest evidence bases for any enterprise AI use case. | Use McKinsey's reported metrics as upper-bound benchmarks, not guarantees. Your firm's adoption will depend on corpus quality and cultural readiness. |
| Citation accuracy | **Risk**: Hallucinated citations in client deliverables are career-ending. The LLM may fabricate document titles, page numbers, or quotations that sound plausible. | Synthesis engine verifies every citation against retrieved content before output. Hallucinated-citation rate monitored continuously with a release gate of < 1%. |
| Automation bias | **Risk**: The Harvard-BCG experiment showed consultants trust AI even when it is confidently wrong, leading to a 19pp accuracy drop on outside-frontier tasks. [S3][S4] | Mandatory human review for client deliverables. Training consultants on the "jagged frontier" concept. Visible confidence indicators on AI outputs. |
| Information-barrier breach | **Risk**: A single cross-barrier document leak can trigger litigation and terminate a client relationship. This is the highest-severity failure mode in consulting. | Barriers enforced at the retrieval layer — the LLM never sees walled content. Zero-tolerance release gate: any single barrier violation blocks deployment. Quarterly compliance audit of barrier configurations. |
| Corpus quality and staleness | **Risk**: The knowledge base decays if engagement teams do not file artifacts. Retrieval quality degrades with stale or poorly tagged content. | Incremental sync pipeline with freshness metadata. Retrieval results display document age. Knowledge management team curates and retires stale content on a defined schedule. AI-assisted tagging to reduce filing burden. |
| IP leakage to model vendors | **Risk**: Proprietary engagement content reaching a vendor's training pipeline would be a catastrophic breach. | Enterprise LLM contracts with data-processing agreements prohibiting training on I/O. Embedding indices encrypted at rest and tenant-isolated. Regular contract and compliance review. |
| Cost escalation at scale | **Risk**: At 500,000+ prompts/month, inference costs compound. Multi-modal queries (document + chart analysis) cost more. | Multi-model routing sends simple queries to cheaper models. Per-query cost monitoring with alerts. Negotiate volume-based enterprise LLM pricing. |

## Rollout KPI Set

| KPI | Why It Matters | Pilot Gate |
|-----|----------------|------------|
| Monthly active users (% of pilot cohort) | Adoption is the leading indicator of value. If consultants do not use the platform, no other metric matters. | >= 50% of pilot cohort active in month 1; >= 70% by month 3. |
| Prompts per active user per week | Frequency indicates whether the platform is becoming part of daily workflow, not a novelty. | >= 10 prompts/week per active user by month 2. |
| Hallucinated-citation rate | The single most important quality metric. A high rate destroys trust and exposes the firm to reputational risk. | < 1% on continuous monitoring. Any sustained rate > 2% triggers rollout pause. |
| Information-barrier violations | Zero-tolerance metric. A single violation is a potential compliance and legal incident. | Zero violations. Any violation triggers immediate investigation and potential rollout suspension. |
| Time saved per session (self-reported) | Connects platform usage to the business case. | >= 5 minutes average, benchmarked against McKinsey's ~6 minutes. [S1] |
| Retrieval relevance (sampled human evaluation) | Ensures the retrieval layer is returning genuinely useful documents, not just semantically similar ones. | Mean relevance score > 3.5/5.0 on monthly sample of 100 queries. |

## Open Questions

- How much does corpus quality vary across practice areas, and which practice areas have enough well-tagged content to serve as the pilot? Firms with inconsistent knowledge management will see lower retrieval quality in under-curated domains.
- What is the real-world hallucination rate on proprietary knowledge questions where the model has no external training data to fall back on? Published benchmarks are mostly on public-domain tasks.
- How do information-barrier enforcement rules interact with the "legitimate cross-engagement learning" tension described in the problem statement? Overly strict barriers suppress knowledge sharing; overly permissive barriers create legal risk. The right boundary is a compliance judgment, not a technical one.
- Does AI-assisted research reduce skill development for junior consultants over time? The BCG follow-up study found no knowledge retention from AI-assisted task completion. [S13] Firms may need to design training rotations that preserve skill-building alongside AI augmentation.
- How should the agent marketplace be governed as it scales to hundreds of practice-area agents? McKinsey's approach (centralized compliance, distributed ownership) works at their scale, but smaller firms may need different governance models.
