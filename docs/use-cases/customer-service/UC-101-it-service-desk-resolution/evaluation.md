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

This is a strong use case if the enterprise stays disciplined about scope. The published evidence shows that routine identity and employee-support requests can be automated or sharply accelerated in production, but the external evidence base is still concentrated in vendor-published customer stories rather than independent benchmarks. The case is strongest when the first release stays inside low-risk L1 work, keeps ITSM and identity systems authoritative, and measures success on safe autonomous resolution rather than on headline chatbot usage. [S1][S2][S3][S4][S5]

## Published Evidence

| Deployment / Source | Published Metric | What It Shows |
|---------------------|------------------|---------------|
| IBM CIO organization, `AskIT` virtual assistant | `75%` of inquiries handled successfully; about `26,000` contacts monthly | A large enterprise can run AI-first internal support at meaningful scale without routing every request to an analyst. |
| Broadcom + Moveworks | `88%` autonomous resolution rate reported in 2025 year-to-date tracking | Routine employee-support workflows can reach high automation when the operating surface is narrow and well integrated. |
| Equinix + Moveworks | `96%` routing accuracy; `82%` of tickets routed within `30 seconds`; average ticket lifespan down nearly one-third | Even before full auto-resolution, AI triage and routing materially improve speed and reduce queue waste. |
| Achieve + Moveworks | `95%` of password resets completely automated | Password reset is a credible first-release intent because it is repetitive, policy-bound, and API-addressable. |
| Verisk + Moveworks | `4,200` account issues resolved each month | Identity and access requests generate enough repeat volume to justify dedicated automation design. |

## Assumptions And Scenario Model

The scenario below models a `10,000`-employee enterprise service desk. Values are estimated unless the basis says published.

| Assumption | Value | Basis |
|------------|-------|-------|
| Monthly ticket volume | `8,000` tickets | Estimated from the UC-101 research brief baseline for a `10,000`-employee enterprise. [S1] |
| First-release eligible share | `55%` of tickets | Estimated. Restricts scope to identity issues, known device recovery, and KB-grounded self-service rather than all L1 work. Supported directionally by the published identity-automation examples. [S2][S4][S5] |
| Autonomous resolution on eligible tickets | `75%` | Estimated. Conservative relative to the stronger published identity-specific metrics and below the Broadcom headline rate. [S3][S4][S5] |
| Current fully loaded handling cost | `$17` per ticket | Estimated. Anchored to the research brief cost range and BLS wage data for computer user support specialists. [S1][S12] |
| AI-resolved ticket operating cost | `$0.80` per ticket | Estimated from current model pricing plus retrieval, orchestration, and residual support overhead; assumes a narrow action plan, not a long multi-agent session. [S13][S14] |

## Expected Economics

| Factor | Value | Note |
|--------|-------|------|
| **Current cost** | `~$1.63M/year` | Estimated: `96,000` tickets annually at `$17` each. Excludes employee downtime while waiting for help. |
| **Expected steady-state cost** | `~$0.99M/year` | Estimated: about `39,600` tickets resolved by automation at `$0.80`, with the remainder still handled manually at the baseline cost. |
| **Expected benefit** | `~$0.64M/year` labor savings | Estimated. This is service-desk operating savings only; it does not include regained employee productivity from faster resolution. |
| **Implementation cost** | `$350K-$550K` in year one | Estimated: orchestration service, connector work, KB cleanup, evaluation harness, and pilot operations. Wide range because incumbent-system complexity dominates. |
| **Payback view** | `~7-11 months` | Estimated from annual labor savings alone. Faster payback is possible if the enterprise has strong KB hygiene and already exposes the required APIs. |

## Quality, Risk, And Failure Modes

| Area | Strength / Risk | Control Or Mitigation |
|------|-----------------|-----------------------|
| **Identity workflows** | Strength: unlock and reset flows are repetitive and already API-driven; Risk: the wrong identity check turns a high-volume win into a security problem | Keep verification outside the model, require IdP state before any write, and never let the model collect secrets in chat. [S8][S9][S11] |
| **Knowledge quality** | Risk: bad or stale KB articles produce confident but wrong troubleshooting advice | Tag and version articles, monitor reopen rates by article, and route to human review when retrieval freshness is unknown. |
| **Ticket routing** | Strength: published evidence is strong on faster routing and queue reduction; Risk: over-automation can hide outage patterns if every ticket is treated independently | Add incident-swarm detection and switch to broadcast or queue-only mode during major events. [S4] |
| **Operational scope creep** | Risk: service desks often want to add software fulfillment and privilege changes too early | Freeze the first-release action catalog and expand only after shadow-mode and pilot gates are met. |
| **Evidence quality** | Risk: most public metrics are vendor-published and may overstate transferability to a weaker environment | Treat the published metrics as directional, not universal, and validate the local business case with a historical-ticket replay before production rollout. [S2][S3][S4][S5] |

## Rollout KPI Set

| KPI | Why It Matters | Pilot Gate |
|-----|----------------|------------|
| **Autonomous resolution rate on in-scope tickets** | Core measure of whether the automation catalog is actually working | `>= 65%` after the pilot period |
| **Unsafe action rate** | The most important safety metric for identity and endpoint writes | `0` unapproved or policy-breaking actions |
| **Median automated resolution time** | Tests whether the system is removing queue time rather than just shifting work | `< 60 seconds` for approved auto-executed intents |
| **Reopen rate for AI-resolved tickets** | Catches bad KB content, wrong plans, and fragile write paths | `<=` the human baseline for the same intent family |
| **Escalation packet completeness** | Determines whether analysts gain time or lose time on AI handoffs | `>= 95%` of escalations include intent, evidence, attempted action, and blocked reason |
| **Employee CSAT for AI-resolved tickets** | Confirms the user experience is actually better, not just cheaper | `>= 4.2/5.0` |

## Open Questions

- What share of historical tickets actually falls into the first-release action catalog once duplicate outage tickets are removed?
- Which identity-verification pattern is acceptable inside the employee channels for unlock and reset requests, and which requests must always bounce to a separate proofing flow?
- Does the incumbent ITSM configuration permit a narrow Scripted REST control plane, or will the enterprise need to adapt to existing automation assets and approval workflows?
- How much knowledge-base cleanup is required before the retrieval layer can be trusted for VPN, device, and software-support guidance?
