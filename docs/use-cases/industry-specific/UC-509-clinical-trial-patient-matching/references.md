---
layout: use-case-detail
title: "References — Autonomous Clinical Trial Patient Matching and Recruitment with Agentic AI"
uc_id: "UC-509"
uc_title: "Autonomous Clinical Trial Patient Matching and Recruitment with Agentic AI"
detail_type: "references"
detail_title: "References"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Pharmaceutical / Life Sciences"
complexity: "High"
status: "detailed"
slug: "UC-509-clinical-trial-patient-matching"
permalink: /use-cases/UC-509-clinical-trial-patient-matching/references/
---

## Source Quality Notes

The evidence base for this case study is strong. Two primary deployment sources — TrialGPT (NIH, peer-reviewed in Nature Communications) and Dyania Health at Cleveland Clinic (institutional press releases with specific metrics) — provide credible, named, production-scale results. Tempus provides first-party accuracy metrics from its own platform evaluation. The AHA market scan aggregates multiple vendor results but relies partly on vendor-reported figures. Tufts CSDD enrollment statistics are widely cited industry benchmarks. The FDA diversity guidance is authoritative regulatory documentation. The CDS Hooks specification is an official HL7 standard. No source in this register is a pure vendor marketing page without named metrics.

## Source Register

| ID | Type | Source | Why It Was Used | Link |
|----|------|--------|-----------------|------|
| S1 | Primary research | Jin et al., "Matching patients to clinical trials with large language models," Nature Communications, 2024 | Core accuracy benchmarks (87.3% criterion-level, 42.6% time reduction, >90% recall); TrialGPT architecture and error analysis | [Nature Communications](https://www.nature.com/articles/s41467-024-53081-z) |
| S2 | Primary deployment | NIH press release, "NIH-developed AI algorithm matches potential volunteers to clinical trials," 2024 | Summary of TrialGPT clinical impact; 40% screening time reduction with maintained accuracy; Director's Challenge Award context | [NIH News Release](https://www.nih.gov/news-events/news-releases/nih-developed-ai-algorithm-matches-potential-volunteers-clinical-trials) |
| S3 | Primary deployment | Cleveland Clinic Newsroom, "Cleveland Clinic Accelerates Clinical Trial Recruitment with Dyania Health's AI Platform," 2025 | Named production deployment: melanoma trial (96% accuracy, 170x speed), DepleTTR-CM trial (1.2M records, 115% identification rate increase); enterprise rollout details | [Cleveland Clinic Newsroom](https://newsroom.clevelandclinic.org/2025/08/27/cleveland-clinic-accelerates-clinical-trial-recruitment-with-roll-out-of-dyania-healths-artificial-intelligence-platform-across-health-system) |
| S4 | Primary deployment | Cleveland Clinic Newsroom, "AI-Driven Chart Review Accurately Identifies Potential Rare Disease Trial Participants," 2026 | Follow-up deployment metrics: 96.2% accuracy on 7,700 questions, 99% NPV, 100% justification accuracy; diversity outcome (36.6% vs 7.1% Black patients) | [Cleveland Clinic Newsroom](https://newsroom.clevelandclinic.org/2026/03/03/ai-driven-chart-review-accurately-identifies-potential-rare-disease-trial-participants-in-new-study) |
| S5 | Vendor evaluation | Tempus, "Improving Patient Matching Efficiency with an AI-Powered Platform," 2025 | Tempus Patient Query metrics: 94.39% accuracy, 72% ineligible screened out, 27.31% more eligible patients identified across 8 trials | [Tempus](https://www.tempus.com/resources/content/articles/improving-patient-matching-efficiency-with-an-ai-powered-platform-2/) |
| S6 | Analysis | AHA Center for Health Innovation, "How AI Is Transforming Clinical Trials," 2025 | Industry landscape: BEKHealth (93% accuracy, 3x faster), market trends, CB Insights data on recruitment cycle compression | [AHA Market Scan](https://www.aha.org/aha-center-health-innovation-market-scan/2025-10-21-how-ai-transforming-clinical-trials) |
| S7 | Domain standard | FDA, "Diversity Action Plans to Improve Enrollment of Participants from Underrepresented Populations in Clinical Studies," 2024 | FDORA Section 3602 requirements for diversity action plans; regulatory context for diversity-aware ranking design | [FDA Guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/diversity-action-plans-improve-enrollment-participants-underrepresented-populations-clinical-studies) |
| S8 | Analysis | Applied Clinical Trials Online / Tufts CSDD, "Enrollment Performance: Weighing the Facts" | Screen failure rate (36.3%), dropout rates (19.1%), site enrollment failures (11% zero enrollment, 37% under-enrollment), daily delay cost ($800K) | [Applied Clinical Trials](https://www.appliedclinicaltrialsonline.com/view/enrollment-performance-weighing-facts) |
| S9 | Official docs | HL7 International, "CDS Hooks v2.0.1 — STU 2 Release 2" | Technical specification for EHR-integrated clinical decision support; architecture reference for real-time trial alert integration | [CDS Hooks](https://cds-hooks.hl7.org/) |

## Claim Map

| Claim Or Section | Source IDs |
|------------------|------------|
| 87.3% criterion-level accuracy, 42.6% screening time reduction (TrialGPT) | S1, S2 |
| 96% accuracy, 170x speed improvement at Cleveland Clinic (Dyania Health) | S3 |
| 99% negative predictive value, 96.2% accuracy on 7,700 trial-specific questions | S4 |
| 36.6% Black patients identified by AI vs. 7.1% through traditional screening | S4 |
| 29 of 30 AI-identified patients missed by traditional recruitment | S4 |
| 94.39% accuracy, 72% ineligible screened out (Tempus) | S5 |
| 93% accuracy, 3x faster identification (BEKHealth) | S6 |
| Screen failure rate baseline 30–36%, daily delay cost $600K–$800K | S8 |
| 80% of trials delayed by enrollment, $6,500+ per enrolled patient | S8 |
| FDA diversity action plan requirements under FDORA | S7 |
| FHIR R4 and CDS Hooks integration architecture | S9 |
| Recommended operating model: AI screens, human confirms | S1, S3, S4 |
| Criterion-level verdicts with evidence citations (design approach) | S1 |
| De-identification before LLM processing (control model) | S4 |
| Expected 25–50% enrollment timeline reduction | S3, S6 |
| Implementation cost and payback estimates | S3, S5, S6, S8 |
