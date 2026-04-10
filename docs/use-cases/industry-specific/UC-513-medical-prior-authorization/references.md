---
layout: use-case-detail
title: "References — Autonomous Medical Prior Authorization Processing"
uc_id: "UC-513"
uc_title: "Autonomous Medical Prior Authorization Processing"
detail_type: "references"
detail_title: "References"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Healthcare"
complexity: "High"
status: "detailed"
slug: "UC-513-medical-prior-authorization"
permalink: /use-cases/UC-513-medical-prior-authorization/references/
---

## Source Quality Notes

The evidence base for this use case is strong on the provider and platform side, with three named deployments publishing specific metrics (Geisinger, UCHealth, Availity/Humana/athenahealth). Cohere Health provides aggregate platform-wide data across 15M+ submissions but does not break out individual customer results beyond Geisinger. The AMA physician survey and CAQH Index are well-established industry benchmarks that quantify the baseline burden. The Da Vinci PAS implementation guide and CMS-0057-F rule text are authoritative technical and regulatory sources. One gap: independent academic studies measuring AI PA automation outcomes in controlled settings are limited. Most published evidence comes from vendor partnerships, which may reflect favorable deployment conditions.

## Source Register

| ID | Type | Source | Why It Was Used | Link |
|----|------|--------|-----------------|------|
| S1 | Primary deployment | Geisinger Health Plan + Cohere Health partnership results | Named deployment with specific metrics: 63% denial reduction, 15% medical savings, 500K members | [Cohere Health: Geisinger case study](https://www.coherehealth.com/news/geisinger-cohere-drive-high-value-care) |
| S2 | Primary deployment | Cohere Health 2025 growth and platform metrics | Platform-wide scale data: 85% real-time approvals, 15M+ submissions, 94% provider satisfaction | [Cohere Health: 2025 growth announcement](https://www.coherehealth.com/news/cohere-health-record-growth-2025-clinical-intelligence) |
| S3 | Primary deployment | UCHealth + Waystar authorization automation results | Named deployment: 340% PA speed increase, 46% denial reduction at a large integrated system | [Waystar: customer results](https://www.waystar.com/our-platform/powerful-results/) |
| S4 | Primary deployment | Availity + Humana + athenahealth Da Vinci PAS pilot | Production FHIR-based PA implementation: 70% auto-approval, 26-hour turnaround, zero documentation-driven denials | [Availity: FHIR PA case study](https://www.availity.com/case-studies/end-to-end-prior-authorizations-using-fhir-apis/) |
| S5 | Industry survey | AMA 2024 Prior Authorization Physician Survey | Baseline burden quantification: 43 requests/week, 12 staff-hours, 87% report increased utilization | [Fix Prior Auth: 2024 AMA survey](https://fixpriorauth.org/2024-ama-prior-authorization-physician-survey) |
| S6 | Industry analysis | 2023 CAQH Index Report | Transaction cost benchmarks: $10.97 manual vs. $5.79 electronic; 35% electronic adoption rate | [CAQH Index Report](https://www.caqh.org/insights/caqh-index-report) |
| S7 | Domain standard | Da Vinci Prior Authorization Support (PAS) FHIR IG v2.1.0 | Technical specification for FHIR-based PA submission; defines CRD, DTR, PAS workflow | [HL7 Da Vinci PAS](https://hl7.org/fhir/us/davinci-pas/) |
| S8 | Regulation | CMS Interoperability and Prior Authorization Final Rule (CMS-0057-F) | Regulatory mandate for FHIR APIs, decision timelines, and PA metrics reporting | [CMS: CMS-0057-F Final Rule](https://www.cms.gov/priorities/burden-reduction/overview/interoperability/policies-regulations/cms-interoperability-prior-authorization-final-rule-cms-0057-f) |
| S9 | Analysis | Health Affairs: The AI Arms Race in Health Insurance Utilization Review | Analysis of risks when both providers and payers deploy AI for PA; discusses adversarial dynamics and regulatory gaps | [Health Affairs Journal](https://www.healthaffairs.org/doi/10.1377/hlthaff.2025.00897) |
| S10 | Industry survey | AMA: Physicians concerned AI increases prior authorization denials | 61% of physicians fear unregulated payer AI increases denials; 29% report PA-related serious adverse events | [AMA: AI and PA denials](https://www.ama-assn.org/practice-management/prior-authorization/how-ai-leading-more-prior-authorization-denials) |

## Claim Map

| Claim Or Section | Source IDs |
|------------------|------------|
| 43 PA requests/week, 12 staff-hours/week per practice, 87% report increased utilization | S5 |
| $10.97 manual vs. $5.79 electronic per PA transaction; 35% electronic adoption | S6 |
| 63% denial reduction, 15% medical savings at Geisinger (500K members) | S1 |
| 85% real-time approvals, 94% provider satisfaction, 15M+ submissions (Cohere platform) | S2 |
| 340% PA speed increase, 46% denial reduction (UCHealth + Waystar) | S3 |
| 70% auto-approval, 26-hour turnaround, zero documentation denials (Availity pilot) | S4 |
| Da Vinci CRD/DTR/PAS workflow specification and FHIR bundle structure | S7 |
| CMS-0057-F mandates: FHIR APIs, 72-hour urgent / 7-day standard decision timelines, public PA metrics by 2026-2027 | S8 |
| Provider-side vs. payer-side AI positioning and adversarial dynamics risk | S9 |
| 61% of physicians concerned about AI-driven denials; 29% report PA-related adverse events | S10 |
| Solution design: provider-side agent positioning avoids automated denial regulatory risk | S8, S9, S10 |
| Solution design: FHIR-first with X12 fallback architecture | S7, S8, S4 |
| Solution design: confidence-scored auto-submission with human escalation | S1, S2, S4 |
| Implementation guide: Da Vinci PAS bundle construction and EHR integration | S7, S4 |
| Evaluation: scenario model baseline costs and volumes | S5, S6 |
| Evaluation: expected denial reduction range (40%) | S1, S3 |
| Evaluation: payback period estimate (6-12 months) | S1, S2, S3, S6 |
| Evaluation: regulatory and bias risks | S8, S9, S10 |
