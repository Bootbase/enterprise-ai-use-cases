---
layout: use-case-detail
title: "Evaluation — Autonomous Incident Investigation with Agentic AI Site Reliability Engineers"
uc_id: "UC-300"
uc_title: "Autonomous Incident Investigation with Agentic AI Site Reliability Engineers"
detail_type: "evaluation"
detail_title: "Evaluation"
category: "Code & DevOps"
category_icon: "terminal"
industry: "Cross-Industry (SaaS, Internet Platforms, FinTech, Travel, E-Commerce)"
complexity: "High"
status: "detailed"
slug: "UC-300-incident-investigation-sre"
permalink: /use-cases/UC-300-incident-investigation-sre/evaluation/
---

## Decision Summary

This is a strong use case with broad market validation and multiple production deployments to reference. The evidence base is unusually strong for an AI use case: Cleric AI's BlaBlaCar deployment provides granular operational metrics (553 investigations, 78% actionable, 3–6 week ramp per team), Microsoft's internal Azure SRE Agent deployment provides scale evidence (35,000+ incidents, 20,000+ engineering hours saved monthly), and AWS DevOps Agent preview customers report 94% root-cause accuracy and 75% MTTR reduction. What is missing is a published, independent ROI study with before-and-after labor cost data from a single named customer. The business case holds for any engineering organization running 50+ microservices with an on-call rotation and more than 500 alerts per month, provided the organization has API-accessible observability tools and is willing to invest in a 4–8 week shadow-mode pilot. [S1][S5][S6]

## Published Evidence

| Deployment / Source | Published Metric | What It Shows |
|---------------------|------------------|---------------|
| Cleric AI at BlaBlaCar (August 2024 – present) [S1] | 553 investigations tracked for the IAM team (Feb–Apr 2025). 78% contained actionable insights on core infrastructure alerts. 1,400 alerts/month covered (~10% of total volume). Perfect 5/5 engineer score within 3 weeks of joining a new team. 200+ engineers, 40+ teams, 5-person SRE team, 200+ deployments/day. | The most granular public deployment data for an AI SRE agent. Demonstrates that an AI SRE can reach useful accuracy in weeks with no prior domain-specific configuration, and that engineer trust can be earned incrementally by starting with a single team's alerting channel. |
| Microsoft Azure SRE Agent — internal deployment (GA March 2026) [S5] | 1,300+ agents deployed across Microsoft services. 35,000+ incidents mitigated. 20,000+ engineering hours saved monthly. Customer Ecolab reduced daily performance alerts from 30–40 to under 10. | Confirms that AI-driven incident investigation works at hyperscaler scale. The 20,000 hours/month figure implies roughly 120 FTE-equivalents of investigation labor displaced across Microsoft's operations. |
| AWS DevOps Agent — preview customers (GA March 2026) [S6] | Customers report up to 75% lower MTTR, 80% faster investigations, and 94% root-cause accuracy. Supports 3–5x faster incident resolution. Now extends to multi-cloud (AWS + Azure). | The 94% root-cause accuracy is the highest published figure from any AI SRE product in preview. Multi-cloud support (investigating Azure workloads from AWS) is a differentiator for hybrid environments. |
| Datadog Bits AI SRE (GA December 2025) [S3][S4] | Tested across 2,000+ customer environments. Investigations complete in 3–4 minutes (2x faster than initial release). Now accesses 10+ data sources including source code, RUM, database monitoring, and network path. | The 2,000+ customer environment breadth validates that the investigation pattern generalizes across diverse production architectures. The 3–4 minute investigation time sets the speed benchmark. |
| PagerDuty SRE Agent (GA October 2025) [S7] | Customers resolve incidents up to 50% faster. AIOps reduces alert noise by up to 91%. Spring 2026: SRE Agent evolves into a "virtual responder" integrated into on-call rotation. | PagerDuty's installed base (21,000+ customers) means the AI SRE pattern is reaching mainstream incident management, not just observability-native platforms. The "virtual responder" roadmap signals where the market is heading. |

## Assumptions And Scenario Model

| Assumption | Value | Basis |
|------------|-------|-------|
| Monthly alert volume | 2,000–10,000 alerts/month per environment | Mid-sized SaaS with 50–200 microservices. BlaBlaCar generates approximately 14,000 alerts/month across all teams, of which Cleric covers 1,400 (10%) in the first production phase. [S1] |
| On-call investigation time per alert | 15–45 minutes per alert (manual) | Industry range. Datadog states "what used to take more than 30 minutes of manual triage." AWS DevOps Agent customers report 80% faster investigations, implying a 30+ minute baseline. [S3][S6] |
| SRE/on-call labor cost | $150K–$250K fully loaded per SRE | US market. Senior SRE compensation routinely exceeds $200K. On-call premiums add 10–20% for teams with regular night/weekend rotation. |
| Investigation capacity reclaimed | 20–30% of SRE/on-call time | Cleric reports early customers reclaiming 20–30% of total engineering capacity previously lost to repetitive troubleshooting. [S2] |
| AI investigation time per alert | 2–5 minutes | Cleric averages under 2 minutes at BlaBlaCar. Datadog Bits AI SRE completes investigations in 3–4 minutes. [S1][S4] |
| Pilot ramp time | 3–6 weeks per team | Cleric reached pilot validation in 6 weeks with the IAM team and 3 weeks with the Engage team at BlaBlaCar. [S1] |

## Expected Economics

| Factor | Value | Note |
|--------|-------|------|
| **Current cost** | $400K–$1.2M annually in on-call investigation labor for a 100-engineer team | Estimated. 4–8 SREs spending 20–30% of time on investigation at $150K–$250K loaded cost. Plus on-call tooling: $54K–$58K/year for PagerDuty Business or incident.io. Does not include the incident impact cost ($15K–$35K per major incident, far higher for P1s). |
| **Expected steady-state cost** | $150K–$400K annually (AI platform + reduced investigation labor + LLM inference) | Estimated. Platform license or managed service: $50K–$200K/year depending on alert volume (Azure SRE Agent uses token-based pricing; Cleric and Datadog price per environment). LLM inference per investigation is small relative to labor cost. Remaining labor: SREs focus on reliability engineering rather than reactive investigation. |
| **Expected benefit** | $250K–$800K annual savings in investigation labor plus faster MTTR reducing incident impact costs | Estimated. Primary savings from 20–30% SRE capacity reclaimed. Secondary: faster MTTR reduces customer-visible downtime, SLA credit payouts, and revenue loss. Tertiary: reduced on-call burnout improves SRE retention in a market where replacing an SRE costs $50K–$75K in recruiting and ramp time. |
| **Implementation cost** | $100K–$300K for Phase 1–2 (build or buy decision) | Estimated. Buy path (Cleric, Datadog Bits AI, Azure SRE Agent, AWS DevOps Agent): platform license plus 4–8 weeks of integration work. Build path: 2–3 engineer-months for the investigation agent plus tool adapters, plus ongoing maintenance. Most organizations should buy — the investigation pattern is well-understood and multiple production-grade products exist. |
| **Payback view** | 3–6 months from pilot start | Estimated. Faster than most enterprise AI use cases because the value is immediate (each investigation saves 15–30 minutes of senior engineer time) and the pilot is lightweight (single team, read-only access, no process change). BlaBlaCar moved from pilot to production expansion within 6 months. [S1] |

## Quality, Risk, And Failure Modes

| Area | Strength / Risk | Control Or Mitigation |
|------|-----------------|-----------------------|
| Investigation accuracy | Strength: hypothesis-driven investigation with tool-grounded evidence produces explainable, verifiable RCAs. Cleric achieved 78% actionable rate and perfect engineer scores within 3 weeks. AWS DevOps Agent reports 94% root-cause accuracy. [S1][S6] | Track actionable rate and engineer feedback scores weekly. Target ≥ 70% actionable as the pilot gate. Investigate drops below 60% as a model or prompt issue, not a fundamental limitation. |
| Trust and adoption | Risk: on-call engineers may ignore or dismiss AI-generated RCAs if early investigations are low quality, creating a "cry wolf" pattern that is hard to reverse. | Start in shadow mode with a private review channel. Only switch to live posting after the team validates quality. Cleric's BlaBlaCar rollout followed this pattern — Chaos app first, then Database Reliability, then IAM — each team opted in after seeing results from the previous team. [S1] |
| Data privacy in logs | Risk: logs and traces routinely contain customer PII, request payloads, and authentication tokens. The AI agent processes these during investigation. | The agent queries logs through the same API and RBAC controls that human engineers use. Existing log redaction and masking policies apply. For regulated industries (FinTech, healthcare SaaS), the agent should run within the customer's cloud boundary with no telemetry exfiltration. Azure SRE Agent and AWS DevOps Agent operate as managed services within the customer's cloud account. [S5][S6] |
| Alert storm degradation | Risk: during a major outage, hundreds of correlated alerts fire simultaneously. If the agent investigates each one independently, it wastes inference budget and produces redundant RCAs. | Deduplication and correlation at the ingestion layer. Group correlated alerts into a single investigation. Prioritize highest-severity alerts. PagerDuty AIOps reduces alert noise by up to 91% before the investigation agent sees them. [S7] |
| LLM cost at scale | Risk: high alert volumes (10,000+/month) with frontier model pricing could make per-investigation inference cost material. | Monitor token usage per investigation. Set a tool-call budget (15 calls per investigation as a starting point). For high-volume environments, use smaller models for initial triage and escalate to frontier models only for complex investigations. Azure SRE Agent uses token-based pricing (AAUs per million tokens). [S5] |
| Remediation authority creep | Risk: after initial success, pressure to expand from read-only investigation to autonomous remediation without proper guardrails. | Keep remediation authority expansion as a deliberate, policy-bounded decision. Pre-approve specific low-risk actions (pod restart, horizontal scale-up) only after validating the investigation accuracy for those alert types. Maintain a full audit trail. Never bypass change management for high-risk actions. [S5][S6] |

## Rollout KPI Set

| KPI | Why It Matters | Pilot Gate |
|-----|----------------|------------|
| Actionable investigation rate | The primary quality metric. Measures whether the AI's output is useful to the on-call engineer, not just technically correct. An investigation is "actionable" if the engineer reports at least one useful insight. | ≥ 70% of investigations rated actionable by the on-call engineer. BlaBlaCar baseline: 78%. [S1] |
| Investigation time (p50 / p95) | Speed is the core value proposition. If the AI investigation takes longer than human triage, it adds no value. | p50 ≤ 5 minutes, p95 ≤ 10 minutes. Datadog Bits AI SRE benchmark: 3–4 minutes. [S4] |
| MTTR reduction for covered alert types | Measures the downstream impact on incident resolution, not just investigation speed. Includes the time from investigation to remediation completion. | ≥ 30% MTTR reduction for alert types covered by the agent. AWS DevOps Agent preview: 75% MTTR reduction. Use 30% as a conservative pilot gate. [S6] |
| Engineer feedback score | Qualitative measure of trust and perceived value. More nuanced than actionable rate — captures whether the engineer would want the agent to continue investigating alerts for their team. | ≥ 4.0 out of 5.0 average score on sampled investigations. Cleric reached 5/5 within 3 weeks at BlaBlaCar. [S1] |
| Alert coverage expansion rate | Measures how quickly the agent can handle new alert types without explicit configuration. Indicates the effectiveness of the operational memory and learning loop. | ≥ 1 new alert type covered per month per team after initial pilot. Track against Cleric's baseline: 10% of total alert volume within the first production phase. [S1] |

## Open Questions

- What is the minimum microservice count and alert volume that justifies the investment? Organizations with fewer than 20 services and 200 alerts/month may not generate enough investigation volume to offset platform costs or build a useful knowledge store.
- How does investigation accuracy degrade for application-level business-metric alerts (e.g., "conversion rate dropped 5%") compared to infrastructure alerts (e.g., "pod crash loop")? Infrastructure alerts have more deterministic root causes; business-metric alerts may require product context the agent does not have.
- Can the operational memory be shared across teams without leaking team-specific context? A Kubernetes pod restart pattern is universal, but a specific team's deployment cadence or known-flaky service list is local knowledge. The knowledge store architecture must handle this scoping.
- How do regulated industries (FinTech under SOX, healthcare SaaS under HIPAA) handle the compliance requirements of an AI agent with read access to production logs containing PII? Published deployments (BlaBlaCar, Datadog customers, Ecolab) are not in heavily regulated verticals.
- What is the steady-state false positive rate for AI-generated RCAs, and how quickly does it decline with operational memory? No published source provides a longitudinal false-positive curve beyond the initial pilot period.
