---
layout: use-case-detail
title: "Evaluation — Autonomous Clinical Trial Patient Matching and Recruitment with Agentic AI"
uc_id: "UC-509"
uc_title: "Autonomous Clinical Trial Patient Matching and Recruitment with Agentic AI"
detail_type: "evaluation"
detail_title: "Evaluation"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Pharmaceutical / Life Sciences"
complexity: "High"
status: "detailed"
slug: "UC-509-clinical-trial-patient-matching"
permalink: /use-cases/UC-509-clinical-trial-patient-matching/evaluation/
---

## Decision Summary

The business case for AI-assisted clinical trial patient matching is strong. Multiple independent deployments — TrialGPT at NIH, Dyania Health at Cleveland Clinic, and Tempus across oncology sites — report criterion-level accuracy between 87% and 96%, screening time reductions of 40–170x, and meaningful improvements in patient diversity. The evidence base is solid for oncology and cardiology; thinner for other therapeutic areas. The economics hold if a health system runs at least 5–10 active trials concurrently, given that each day of enrollment delay costs hundreds of thousands of dollars. The primary uncertainty is not whether AI matching works, but how reliably it transfers across EHR systems with varying data quality and documentation practices.

## Published Evidence

| Deployment / Source | Published Metric | What It Shows |
|---------------------|------------------|---------------|
| TrialGPT (NIH/NLM), Nature Communications 2024 | 87.3% criterion-level accuracy; 42.6% screening time reduction; >90% trial recall at 6% collection size | LLM-based matching approaches expert-level accuracy; clinicians using TrialGPT spent 40% less time with no accuracy loss |
| Dyania Health / Cleveland Clinic, melanoma trial 2025 | 96% accuracy in 2.5 minutes vs. 95% accuracy in 427 minutes (specialized nurse) | 170x speed improvement with comparable accuracy; AI reviewed what took a nurse 7+ hours in under 3 minutes |
| Dyania Health / Cleveland Clinic, DepleTTR-CM cardiomyopathy trial 2026 | 1.2M records screened in one week; 30 eligible patients identified vs. 14 over 90 days traditional; 99% negative predictive value; 96.2% accuracy across 7,700 questions | AI finds more eligible patients faster; 29 of 30 AI-identified patients were missed by traditional recruitment |
| Dyania Health / Cleveland Clinic, diversity outcome 2026 | 36.6% of AI-identified patients were Black vs. 7.1% through routine screening | AI screens the full population rather than only patients already connected to specialists, substantially improving diversity |
| Tempus Patient Query, oncology screening 2025 | 94.39% accuracy across 196 queries; 72% of ineligible patients screened out; 27.31% more eligible patients identified | AI pre-screening reduces coordinator workload by eliminating most ineligible candidates while surfacing patients that manual review misses |
| BEKHealth, EHR-based feasibility 2025 | 93% accuracy; 3x faster identification vs. manual chart review | NLP over unstructured clinical notes reaches usable accuracy for pre-screening across oncology, cardiology, and neurology |

## Assumptions And Scenario Model

| Assumption | Value | Basis |
|------------|-------|-------|
| Active trials per site | 10–20 concurrently | Mid-size academic medical center; Cleveland Clinic runs hundreds but smaller centers run fewer |
| Patients per trial needed | 50–200 (Phase II–III) | Industry averages from Tufts CSDD |
| Manual screening rate | 50–100 charts per coordinator per week | Published estimate from site coordination workflow studies |
| AI screening rate | 1,000–10,000 records per hour | Dyania Health screened 1.2M records in one week (~7,000/hour sustained) |
| Screen failure rate baseline | 30–36% | Tufts CSDD: overall average screen failure rate of 36.3% across Phase II–III trials |
| Cost per enrolled patient | $6,500+ (recruitment cost only) | Industry benchmark; excludes treatment and follow-up costs |
| Daily delay cost | $600K–$800K median | Tufts CSDD estimates; varies widely by therapeutic area and phase |

## Expected Economics

| Factor | Value | Note |
|--------|-------|------|
| **Current cost** | $6,500+ per enrolled patient; $1,200 per screen failure; $11.5M average Phase III recruitment budget | Published industry estimates |
| **Expected steady-state cost** | $2,000–$3,500 per enrolled patient (estimated) | Estimated: 40–50% reduction from faster identification and lower screen failure rate; coordinator time redirected from chart review to patient engagement |
| **Expected benefit** | 25–50% enrollment timeline reduction; screen failure rate below 10%; 2–3x more eligible candidates identified | Based on published Dyania Health and TrialGPT results; actual benefit depends on EHR data quality |
| **Implementation cost** | $500K–$1.5M first year (estimated) | Estimated: FHIR pipeline build, model integration, dashboard development, clinical validation, IRB approvals; lower if using commercial platform like Dyania Health or Tempus |
| **Payback view** | Under 12 months for sites running 10+ trials (estimated) | Estimated: one fewer month of enrollment delay on a single Phase III trial recovers $15–24M in avoided revenue loss; AI platform cost is a fraction of this |

## Quality, Risk, And Failure Modes

| Area | Strength / Risk | Control Or Mitigation |
|------|-----------------|-----------------------|
| Match accuracy | Strength: multiple deployments report 87–96% accuracy, approaching expert-level performance | Criterion-level verdicts with evidence citations; coordinator review before any outreach |
| Screening speed | Strength: 40–170x faster than manual review across published deployments | Monitor throughput SLA; alert on processing delays that could miss enrollment windows |
| EHR data quality | Risk: unstructured notes vary dramatically in completeness and terminology across institutions | Default to "uncertain" when evidence is absent; track per-site data quality metrics; exclude sites with poor documentation from autonomous screening |
| PHI exposure | Risk: clinical notes contain dense PHI; LLM processing creates data handling surface | HIPAA Safe Harbor de-identification before AI processing; BAA-covered infrastructure; audit logging; no PHI in model training |
| Criteria misinterpretation | Risk: ambiguous protocol language can cause systematic screening errors | Parsed criteria reviewed by clinical staff before screening; A/B comparison with manual screening during pilot; TrialGPT error analysis shows 30.7% of errors are reasoning mistakes |
| Population bias | Risk: AI may reflect historical referral patterns embedded in EHR data | Diversity-aware re-ranking; demographic parity monitoring; Cleveland Clinic data shows AI actually reduces bias by screening full population |
| Regulatory uncertainty | Risk: no specific FDA guidance on AI for trial recruitment; FDORA diversity action plan requirements still evolving | Design system as screening aid, not autonomous enrolller; maintain human confirmation at all decision points; document AI role in IRB submissions |

## Rollout KPI Set

| KPI | Why It Matters | Pilot Gate |
|-----|----------------|------------|
| Criterion-level accuracy (F1) | Core measure of match reliability; directly affects coordinator trust and screen failure rate | F1 ≥ 0.87 across eligible/excluded verdicts (matches TrialGPT published baseline) |
| Screen failure rate | End-to-end measure of whether AI pre-screening actually identifies enrollable patients | < 15% during pilot (vs. 30–36% baseline); target < 10% at steady state |
| Screening throughput | Measures whether AI delivers candidates fast enough to affect enrollment timelines | Ranked list within 48 hours of trial activation |
| Coordinator acceptance rate | Indicates whether AI-surfaced candidates are clinically relevant; low rate suggests poor matching | > 60% of top-20 candidates accepted by coordinator |
| Diversity index | Tracks demographic representation in AI-identified candidate pool vs. site catchment | No demographic group underrepresented by > 10 percentage points |
| Evidence grounding rate | Ensures AI citations are traceable and not hallucinated | 100% of sampled evidence citations map to actual patient record passages |

## Open Questions

- How does matching accuracy degrade when applied to EHR systems with lower documentation quality than academic medical centers like Cleveland Clinic?
- What is the minimum viable training data size for a new therapeutic area where existing deployments (oncology, cardiology) may not transfer well?
- How should parsed criteria be versioned and re-applied when protocol amendments change eligibility mid-enrollment?
- What level of AI transparency in the screening process satisfies institutional IRB requirements for informed consent documentation?
- How will the evolving regulatory landscape around FDA diversity action plans (post-FDORA, post-2025 DEI executive orders) affect the diversity re-ranking approach?
