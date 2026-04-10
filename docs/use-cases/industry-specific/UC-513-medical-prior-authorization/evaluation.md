---
layout: use-case-detail
title: "Evaluation — Autonomous Medical Prior Authorization Processing"
uc_id: "UC-513"
uc_title: "Autonomous Medical Prior Authorization Processing"
detail_type: "evaluation"
detail_title: "Evaluation"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Healthcare"
complexity: "High"
status: "detailed"
slug: "UC-513-medical-prior-authorization"
permalink: /use-cases/UC-513-medical-prior-authorization/evaluation/
---

## Decision Summary

The business case for AI-assisted prior authorization is strong, backed by multiple named deployments with published metrics. Geisinger Health Plan, UCHealth, and the Availity/Humana/athenahealth pilot each demonstrate material improvements in auto-approval rates, denial reduction, and processing speed. The CMS-0057-F rule creates regulatory tailwind by mandating FHIR APIs and standardized decision timelines by 2027. The primary risk is not whether the technology works but whether the payer integration landscape is mature enough to support FHIR-first submission at scale today. Organizations that start with high-volume, structurally simple procedure categories (imaging, outpatient surgery) and a hybrid FHIR + X12 approach will see the fastest payback.

## Published Evidence

| Deployment / Source | Published Metric | What It Shows |
|---------------------|------------------|---------------|
| Geisinger Health Plan + Cohere Health (500K members, 30K providers) | 63% denial rate reduction; 15% incremental medical savings; 95% digital submission rate; 70% faster care access | AI-driven PA platform materially reduces denials and accelerates care delivery at scale for a regional health plan |
| UCHealth + Waystar | 340% increase in PA processing speed; 46% reduction in authorization-related denials | Automation delivers multi-fold speed improvement and nearly halves denial rates at a large integrated health system |
| Cohere Health platform-wide (15M+ PA submissions) | 85% real-time authorization approvals; 94% provider satisfaction; 55% reduction in submission times | High auto-approval rates are achievable across a large, diverse provider network -- not limited to a single site |
| Availity + Humana + athenahealth (Da Vinci pilot) | 70% monthly auto-approval rate; 54% of requests required no authorization; average turnaround 26 hours; zero denials due to insufficient documentation | FHIR-based end-to-end PA submission works in production and eliminates documentation-driven denials |
| AMA 2024 Physician Survey (1,000 physicians) | 43 PA requests/week median; 12 staff-hours/week; 87% report PA increases overall utilization | Establishes the baseline burden that automation targets; confirms the problem is industry-wide, not site-specific |
| 2023 CAQH Index | $10.97 manual vs. $5.79 electronic per PA transaction (provider side); only 35% fully electronic | Quantifies the per-transaction savings opportunity and the low electronic adoption baseline |

## Assumptions And Scenario Model

The scenario below models a mid-size health system (400-bed hospital, 200 employed physicians, affiliated ambulatory network). All values are estimated unless noted.

| Assumption | Value | Basis |
|------------|-------|-------|
| Monthly PA volume | 3,500 requests | Estimated from AMA median of 43/week per physician across a 200-physician practice |
| Current manual cost per PA | $11.00 | CAQH 2023 Index published figure ($10.97 rounded) |
| Target auto-submission rate | 70% of requests | Conservative estimate; Availity pilot achieved 70% auto-approval; Cohere reports 85% |
| Cost per auto-submitted PA | $2.00 | Estimated: platform licensing + compute + residual staff review time; below CAQH electronic baseline of $5.79 |
| Cost per manually handled PA | $11.00 | Assumes exception cases retain current manual cost |
| Denial rate reduction | 40% | Conservative; Geisinger achieved 63%, UCHealth 46% |
| Revenue recovered per avoided denial | $350 | Estimated average reimbursement at risk per denied PA; varies widely by procedure |

## Expected Economics

| Factor | Value | Note |
|--------|-------|------|
| **Current annual PA cost** | ~$462,000 | Estimated: 3,500/month x 12 x $11.00 per manual transaction |
| **Expected steady-state cost** | ~$198,000 | Estimated: 70% auto-submitted at $2.00 + 30% manual at $11.00 |
| **Annual labor savings** | ~$264,000 | Estimated: difference between current and steady-state processing cost |
| **Denial-related revenue recovery** | ~$588,000/year | Estimated: 3,500/month x 12% baseline denial rate x 40% reduction x $350 per avoided denial |
| **Platform + integration cost (Year 1)** | $300,000–$500,000 | Estimated: vendor licensing, EHR integration, medical policy ingestion, staff training; wide range due to EHR certification timelines |
| **Payback view** | 6–12 months | Estimated: labor savings + denial recovery offset implementation cost within first year; published ROI data from Waystar and Cohere suggests 3-6 month payback at higher volumes |

## Quality, Risk, And Failure Modes

| Area | Strength / Risk | Control Or Mitigation |
|------|-----------------|-----------------------|
| **Evidence extraction accuracy** | Strength: clinical NLP on structured EHR data (labs, ICD codes) is high-accuracy; Risk: unstructured chart notes may contain ambiguous or contradictory information | Confidence scoring with human escalation below threshold; structured fields validated against EHR discrete data; extraction accuracy tracked weekly |
| **Payer integration maturity** | Risk: not all payers support Da Vinci PAS FHIR APIs yet; X12 278 adoption is also incomplete | FHIR-first build with X12 fallback via clearinghouse; prioritize top 5 payers by volume for initial integration; CMS-0057-F forces payer adoption by 2027 |
| **Medical policy staleness** | Risk: payers update medical necessity criteria without notice; stale policies cause incorrect matches | Scheduled policy refresh with version tracking; alert on match-score drift; fallback to human review when policy version is outdated |
| **Regulatory landscape** | Risk: several states (Texas, Arizona, Maryland) prohibit AI as sole basis for coverage denials; new legislation is active | System operates on provider side (submitting, not denying); compliance risk is lower but must track state-level restrictions on automated appeals |
| **Bias and equity** | Risk: training data may reflect existing disparities in PA approval rates across demographics | Monitor auto-submission rates and outcomes by patient demographics; flag statistically significant disparities for clinical review |
| **Payer-side AI denials** | Risk: payers may deploy their own AI to auto-deny, creating an adversarial dynamic | Denial analyzer tracks payer-specific denial patterns; provider-side AI strengthens submissions to counter known denial triggers; this risk is outside system control but observable |

## Rollout KPI Set

| KPI | Why It Matters | Pilot Gate |
|-----|----------------|------------|
| **Auto-submission rate** | Measures how much manual work is eliminated; primary efficiency driver | >= 50% in pilot (target 70% steady-state) |
| **Auto-submitted denial rate** | Confirms AI-submitted requests are not denied at higher rates than manual | Within 2 percentage points of manual baseline |
| **Median time to payer decision** | Validates speed improvement for patients and clinicians | < 48 hours for auto-submitted cases |
| **Staff hours on PA per week** | Direct measure of labor burden reduction | 30%+ reduction from 12-hour baseline |
| **Extraction accuracy (F1)** | Ensures clinical evidence is correctly assembled | >= 0.90 on diagnoses; >= 0.85 on supporting findings |
| **Provider satisfaction score** | Tracks whether clinicians trust and adopt the system | >= 80% positive in post-pilot survey |

## Open Questions

- How quickly will payers implement Da Vinci PAS FHIR APIs in response to CMS-0057-F? The transition timeline determines how long the X12 fallback path remains necessary and how much integration complexity persists.
- What is the right confidence threshold for auto-submission? Too conservative wastes the automation benefit; too aggressive increases denial risk. Threshold tuning requires payer-specific calibration.
- Will payer-side AI adjudication create an escalating adversarial dynamic? If payers deploy AI to auto-deny while providers deploy AI to auto-submit, the net effect on patient care and administrative cost is unclear.
- How should the system handle multi-state provider networks where PA regulations differ by jurisdiction? A single confidence threshold and auto-submission policy may not be legally sufficient across all states.
