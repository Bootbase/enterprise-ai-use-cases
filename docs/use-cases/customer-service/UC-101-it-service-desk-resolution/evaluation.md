---
layout: use-case-detail
title: "Evaluation — Autonomous IT Service Desk Resolution with Agentic AI"
uc_id: "UC-101"
uc_title: "Autonomous IT Service Desk Resolution with Agentic AI"
detail_type: "evaluation"
detail_title: "Evaluation"
category: "Customer Service"
category_icon: "headphones"
industry: "Cross-Industry (Technology, Financial Services, Manufacturing, Pharmaceutical, Professional Services)"
complexity: "High"
status: "detailed"
slug: "UC-101-it-service-desk-resolution"
permalink: /use-cases/UC-101-it-service-desk-resolution/evaluation/
---

## Decision Summary

This is a strong enterprise AI use case with unusually direct evidence. Multiple named deployments report autonomous resolution rates between 35% and 88%, sub-minute resolution times, and high employee satisfaction. The evidence is mostly vendor-published (Moveworks customer stories) rather than independent benchmark research, but the deployments are named, the metrics are specific, and the volume claims are large enough to be operationally meaningful. The business case holds when three conditions are met: the organization has a high enough L1 ticket volume to justify integration work, the identity and endpoint systems expose APIs for the target actions, and runbook quality is good enough to ground the AI's classification and resolution decisions. [S2][S3][S4]

## Published Evidence

| Deployment / Source | Published Metric | What It Shows |
|---------------------|------------------|---------------|
| Broadcom / Moveworks | 88% autonomous resolution rate (up from 10% at launch), 75,000+ IT issues resolved, employees receive support in under 60 seconds instead of days, 40% cost reduction in ticket services, $1.4M in savings | A large enterprise can reach very high autonomous resolution rates over time. The ramp from 10% to 88% shows that AI service desk quality improves with deployment maturity. [S2] |
| Nutanix / Moveworks | 54% autonomous resolution rate, 7-second average MTTR, 30,000+ tickets resolved autonomously, 90% employee satisfaction, deployed in 7 weeks | Sub-minute MTTR is achievable for routine IT requests. High employee satisfaction shows that autonomous resolution does not inherently degrade the experience. [S3] |
| Equinix / Moveworks | 68% deflection rate, 43% autonomous resolution, 82% of tickets routed by AI at 96% accuracy, 96% employee satisfaction | Even partial automation (43% resolution plus AI-assisted routing) creates meaningful capacity relief and high satisfaction when the triage quality is strong. [S4] |
| MetricNet benchmarks | Tier 1 cost: $22/ticket, Desktop Support: $70/ticket, Tier 3: $104/ticket, industry CSAT: 83.8% | Establishes the cost baseline for manual IT service desk operations. The gap between $22/ticket and sub-$2 AI resolution cost is the primary economic driver. [S5] |

## Assumptions And Scenario Model

| Assumption | Value | Basis |
|------------|-------|-------|
| Annual L1/L2 ticket volume | 96,000 tickets (8,000/month) | Estimated. Consistent with the research brief's 10,000-employee reference at 0.8 tickets per employee per month. [S1] |
| Current average resolution time | 2 hours 50 minutes | Published. HappySignals Global IT Experience Benchmark. [S7] |
| Current cost per L1 ticket | $22 | Published. MetricNet 2024 benchmark for Tier 1 service desk. [S5] |
| Password resets as share of volume | 30% | Estimated. Conservative midpoint of the Gartner 20-50% range cited in the research brief. [S1][S6] |
| Steady-state autonomous resolution rate | 50% | Estimated. Conservative relative to Broadcom (88%) and Nutanix (54%), and realistic for a first-year deployment with a limited intent set. [S2][S3] |
| AI cost per resolved ticket | $1.50 | Estimated. Accounts for model inference, orchestration overhead, and identity API calls. Higher than customer-facing chatbot costs due to identity mutation complexity. |

## Expected Economics

| Factor | Value | Note |
|--------|-------|------|
| **Current cost** | ~$2.1M per year | Estimated. 96,000 tickets x $22 per ticket (MetricNet Tier 1 benchmark). [S5] |
| **Expected steady-state cost** | ~$1.2M-$1.4M per year | Estimated. 50% of tickets resolved at $1.50 AI cost; remaining 50% still handled by analysts at $22 per ticket. |
| **Expected benefit** | ~$700K-$900K annual savings | Estimated. Driven by eliminating analyst handle time on routine L1 requests plus reduced misrouting rework. |
| **Implementation cost** | ~$350K-$600K one-time | Estimated. Covers ITSM and identity provider integration, runbook content cleanup, security review, replay-set creation, and pilot operations. |
| **Payback view** | ~5-8 months | Estimated. Requires the deployment to reach the 50% automation assumption and maintain identity mutation safety. |

## Quality, Risk, And Failure Modes

| Area | Strength / Risk | Control Or Mitigation |
|------|-----------------|-----------------------|
| Password resets and account unlocks | Strength. These are the highest-volume, most standardized L1 tasks. Published deployments consistently show these as the first category to reach high autonomous resolution rates. [S2][S3][S6] | Start the pilot with identity actions only. They are the easiest to validate and produce the fastest employee experience improvement. |
| Identity mutation safety | Risk. Resetting the wrong user's password or granting unauthorized access creates a direct security incident. [S9] | Gate every identity write with exact employee-ID match, identity verification status, and action-specific rules. Never process identity mutations for privileged accounts without human approval. |
| Runbook quality and drift | Risk. If runbooks are outdated, scattered, or inconsistent, the AI will ground its reasoning on wrong procedures. | Give IT operations ownership of runbook tagging, effective dates, and retrieval quality. Regression-test against runbook-heavy scenarios in every release. |
| Credential exposure | Risk. Password resets return temporary credentials that must never appear in logs, work notes, or conversation history. [S15][S16] | Redact temporary passwords before writing work notes. Deliver credentials through a secure, time-limited channel (e.g., direct message with auto-expiry). |
| Evidence quality | Mixed. The deployment evidence is strong enough for pilot sizing, but it comes primarily from one vendor's (Moveworks) customer stories. Independent benchmarks would strengthen confidence. | Use published evidence to size the opportunity, then require local replay and supervised pilot data before scaling. |

## Rollout KPI Set

| KPI | Why It Matters | Pilot Gate |
|-----|----------------|------------|
| Autonomous resolution rate on supported intents | Shows whether the workflow is actually escaping the analyst queue | >= 30% in supervised pilot, trending toward >= 50% before broader release |
| Mean time to resolution (AI-resolved tickets) | Captures the employee-visible speed improvement | < 2 minutes (vs. 2h 50m baseline) |
| Identity mutation accuracy | Hard safety metric for password resets, unlocks, and access changes | 0 unauthorized identity writes |
| Ticket misrouting rate | Measures whether AI classification is improving or degrading routing quality | < 8% (vs. 15-25% baseline) |
| Employee satisfaction (CSAT) | Prevents a cost-only rollout that damages employee experience | Within 5 points of the human baseline, or above |

## Open Questions

- Which L1 intent categories in the target enterprise have clean, current runbooks that are ready for retrieval, and which require content remediation before the AI can use them?
- Does the organization's identity provider support the specific API operations needed (password reset, group membership, app assignment) with sufficient granularity and permission scoping?
- What identity verification flow is acceptable before an AI-initiated password reset — SSO session validation, MFA challenge, or manager approval?
- How will the organization handle burst load during major incidents (e.g., company-wide VPN outage generating thousands of simultaneous tickets)?
- What local error budget would IT leadership accept before preferring lower automation and more human handling?
