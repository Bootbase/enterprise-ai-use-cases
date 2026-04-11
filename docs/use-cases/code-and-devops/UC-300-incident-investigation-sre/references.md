---
layout: use-case-detail
title: "References — Autonomous Incident Investigation with Agentic AI Site Reliability Engineers"
uc_id: "UC-300"
uc_title: "Autonomous Incident Investigation with Agentic AI Site Reliability Engineers"
detail_type: "references"
detail_title: "References"
category: "Code & DevOps"
category_icon: "terminal"
industry: "Cross-Industry (SaaS, Internet Platforms, FinTech, Travel, E-Commerce)"
complexity: "High"
status: "detailed"
slug: "UC-300-incident-investigation-sre"
permalink: /use-cases/UC-300-incident-investigation-sre/references/
---

## Source Quality Notes

The evidence base for this use case is anchored by one detailed customer case study (S1 — Cleric at BlaBlaCar, with granular investigation metrics) and three hyperscaler/platform GA announcements (S5 — Azure SRE Agent, S6 — AWS DevOps Agent, S7 — PagerDuty) that provide scale and performance claims. Cleric's BlaBlaCar case study (S1) is the strongest source for operational metrics — it reports specific investigation counts, actionable rates, ramp timelines, and engineer feedback scores from a named customer over a 9-month deployment. Microsoft's Azure SRE Agent (S5) provides the strongest scale evidence with internally deployed metrics (35,000+ incidents, 20,000+ hours saved monthly), though these are vendor-published figures for the vendor's own services. AWS DevOps Agent (S6) reports the highest root-cause accuracy (94%) but this comes from preview customers, not independently verified production deployments. Datadog's engineering blog (S9) is the most technically detailed source on how a hypothesis-driven AI SRE agent is built, but performance claims are directional rather than precisely quantified. PagerDuty (S7) and incident.io (S8) are vendor product pages useful for feature comparison and market context. The Gartner Cool Vendors report (S10) is an authoritative analyst endorsement but the full report is gated.

## Source Register

| ID | Type | Source | Why It Was Used | Link |
|----|------|--------|-----------------|------|
| S1 | Primary deployment | Cleric AI — BlaBlaCar Case Study (2025) | Primary deployment evidence: 553 investigations, 78% actionable rate, 1,400 alerts/month, 3–6 week ramp per team, perfect 5/5 engineer score, 200+ engineers, 40+ teams, 5-person SRE team. The most granular public deployment data for an AI SRE agent. | [Cleric — BlaBlaCar Case Study](https://cleric.ai/resources/case-studies/how-the-worlds-leading-community-based-travel-network-is-transforming-incident-response-with-ai) |
| S2 | Vendor announcement | Cleric — Self-Learning AI SRE Launch (December 2025) | Company background: $9.8M seed funding led by Vertex Ventures US, Gartner Cool Vendor 2025, operational memory architecture, LangSmith tracing, 20–30% engineering capacity reclaimed claim. | [Cleric — 9 Months In: BlaBlaCar and Cleric](https://cleric.ai/blog/how-blablacar-and-cleric-are-reimagining-incident-response-with-ai) |
| S3 | Vendor announcement | Datadog — Introducing Bits AI SRE (December 2025 GA) | Product reference: 2,000+ customer environments tested, hypothesis-driven investigation, Slack integration, investigation workflow, "what used to take more than 30 minutes of manual triage now happens in minutes." | [Datadog — Introducing Bits AI SRE](https://www.datadoghq.com/blog/bits-ai-sre/) |
| S4 | Vendor announcement | Datadog — Bits AI SRE Deeper Reasoning Update (March 2026) | Performance update: 2x faster investigations (3–4 minutes), expanded data sources (source code, RUM, database monitoring, network path, continuous profiler), Agent Trace view, workflow automation actions. | [Datadog — Meet the new Bits AI SRE](https://www.datadoghq.com/blog/bits-ai-sre-deeper-reasoning/) |
| S5 | Primary deployment | Microsoft — Azure SRE Agent GA (March 2026) | Scale evidence: 1,300+ agents deployed internally, 35,000+ incidents mitigated, 20,000+ engineering hours saved monthly. Customer evidence: Ecolab reduced daily alerts from 30–40 to under 10. Architecture: knowledge memory, sub-agents, MCP integration, token-based pricing. | [Microsoft — Azure SRE Agent GA Announcement](https://techcommunity.microsoft.com/blog/appsonazureblog/announcing-general-availability-for-the-azure-sre-agent/4500682) |
| S6 | Vendor announcement | AWS — DevOps Agent GA (March 2026) | Performance claims: 75% lower MTTR, 80% faster investigations, 94% root-cause accuracy (preview customers). Multi-cloud support (AWS + Azure). Integrations with CloudWatch, Datadog, Dynatrace, New Relic, Splunk, GitHub Actions, GitLab CI/CD. | [AWS — DevOps Agent GA Announcement](https://aws.amazon.com/blogs/mt/announcing-general-availability-of-aws-devops-agent/) |
| S7 | Vendor announcement | PagerDuty — End-to-End AI Agent Suite Launch (October 2025) | Market context: industry's first end-to-end AI agent suite. SRE Agent, Scribe Agent, Insights Agent. Customers resolve incidents up to 50% faster. AIOps reduces alert noise by 91%. Spring 2026: SRE Agent as virtual responder. 150+ platform enhancements. | [PagerDuty — AI Agent Suite Launch](https://www.pagerduty.com/?page_id=96831) |
| S8 | Vendor product page | incident.io — AI SRE (2025–2026) | Feature comparison: multi-agent investigation, Slack-native operation, PR-level root cause identification, automated fix generation, 5x faster resolution claim. Design partners include Airbnb, Etsy, Zendesk. | [incident.io — AI SRE](https://incident.io/ai-sre) |
| S9 | Technical blog | Datadog — How We Built an AI SRE Agent (January 2026) | Technical architecture: hypothesis-driven investigation methodology, branching hypothesis trees, causal relationship focus, recursive sub-hypothesis generation, LLM-as-judge evaluation, MCP tool integration. The most detailed public description of how an AI SRE agent's investigation loop works. | [Datadog — How We Built Bits AI SRE](https://www.datadoghq.com/blog/building-bits-ai-sre/) |
| S10 | Analyst report | Gartner — Cool Vendors in AI for SRE and Observability (October 2025) | Analyst validation: Gartner identified AI for SRE as a distinct capability area. Report helps I&O leaders identify providers using AI to enhance SRE practices, improve reliability, and reduce cognitive load. Cleric named as a Cool Vendor. | [Cleric — Gartner Cool Vendor Announcement](https://cleric.ai/blog/cleric-named-a-cool-vendor-in-the-2025-gartner-cool-vendors) |

## Claim Map

| Claim Or Section | Source IDs |
|------------------|------------|
| BlaBlaCar: 553 investigations, 78% actionable rate, 1,400 alerts/month, 200+ engineers, 5-person SRE team, perfect 5/5 engineer score in 3 weeks | S1 |
| Cleric: $9.8M seed funding, Gartner Cool Vendor 2025, 20–30% engineering capacity reclaimed, operational memory architecture | S2, S10 |
| Datadog Bits AI SRE: 2,000+ customer environments, hypothesis-driven investigation, 30+ minutes manual triage reduced to minutes | S3 |
| Bits AI SRE: 2x faster (3–4 minutes), expanded data sources (10+), Agent Trace view, workflow automation | S4 |
| Azure SRE Agent: 1,300+ agents deployed, 35,000+ incidents mitigated, 20,000+ engineering hours saved monthly, Ecolab customer | S5 |
| AWS DevOps Agent: 75% lower MTTR, 80% faster investigations, 94% root-cause accuracy, multi-cloud support | S6 |
| PagerDuty: 50% faster resolution, 91% alert noise reduction, SRE Agent as virtual responder roadmap | S7 |
| incident.io: multi-agent investigation, Slack-native, PR-level root cause, design partners Airbnb/Etsy/Zendesk | S8 |
| Hypothesis-driven investigation architecture: branching tree, causal relationship focus, recursive sub-hypotheses, LLM-as-judge evaluation | S9 |
| Investigation time target of 2–5 minutes | S1, S4, design recommendation |
| Read-only access by default, human-approved remediation | S1, S5, S6, design recommendation |
| Slack/Teams as primary interaction surface | S1, S3, S7, S8, design recommendation |
| 20–30% SRE capacity reclaimed; $400K–$1.2M annual investigation labor for 100-engineer team | S2, design recommendation informed by S1, S5 |
| 3–6 month payback; $100K–$300K implementation cost | Design recommendation, informed by S1, S5, S6 |
| ≥ 70% actionable rate as pilot gate | Design recommendation, informed by S1 (78% BlaBlaCar baseline) |
