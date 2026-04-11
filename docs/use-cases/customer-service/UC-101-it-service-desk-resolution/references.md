---
layout: use-case-detail
title: "References — Autonomous IT Service Desk Resolution with Agentic AI"
uc_id: "UC-101"
uc_title: "Autonomous IT Service Desk Resolution with Agentic AI"
detail_type: "references"
detail_title: "References"
category: "Customer Service"
category_icon: "headphones"
industry: "Cross-Industry (Technology, Financial Services, Manufacturing, Pharmaceutical, Professional Services)"
complexity: "High"
status: "detailed"
slug: "UC-101-it-service-desk-resolution"
permalink: /use-cases/UC-101-it-service-desk-resolution/references/
---

## Source Quality Notes

The strongest deployment evidence comes from three named Moveworks customer stories: Broadcom, Nutanix, and Equinix. These are vendor-published, not independent benchmark studies, but they describe production deployments at named enterprises with specific metrics. The cost baseline relies on MetricNet benchmarking data, which is an established industry source for IT service desk economics. The implementation guidance relies on official product documentation from Microsoft (Graph API, Intune), ServiceNow (Table API), Okta (SCIM), OpenAI, and LangGraph. The control model uses public regulatory guidance from the European Commission and ICO. The password reset cost figure ($70 per incident) is widely attributed to Forrester Research and cited across multiple industry sources. The scenario economics in `evaluation.md` remain estimated even where they are anchored in published benchmarks.

## Source Register

| ID | Type | Source | Why It Was Used | Link |
|----|------|--------|-----------------|------|
| S1 | Internal brief | UC-101 research brief | Baseline scope, operating constraints, ticket volume assumptions, and target success metrics | [Research brief](./index.md) |
| S2 | Primary deployment | Broadcom / Moveworks customer story | Published autonomous resolution rate (88%), cost reduction (40%), $1.4M savings, and 75,000+ tickets resolved | [Broadcom case study](https://www.moveworks.com/us/en/customers/broadcom-integrates-it-knowledge-base-with-moveworks-ai) |
| S3 | Primary deployment | Nutanix / Moveworks customer story | Published MTTR (7 seconds), autonomous resolution (54%), 90% employee satisfaction, and 7-week deployment timeline | [Nutanix case study](https://www.moveworks.com/us/en/customers/nutanix-reduces-mttr-with-moveworks-ai-implementation-strategy) |
| S4 | Primary deployment | Equinix / Moveworks customer story | Published deflection (68%), autonomous resolution (43%), 96% routing accuracy, and 96% employee satisfaction | [Equinix case study](https://www.moveworks.com/case-studies/equinix) |
| S5 | Analysis | MetricNet service desk cost per ticket benchmarks | Published Tier 1 ($22), Desktop Support ($70), and Tier 3 ($104) cost-per-ticket benchmarks for scenario modeling | [MetricNet cost per ticket](https://www.metricnet.com/service-desk-cost-per-ticket-motm/) |
| S6 | Analysis | Forrester Research / industry citations on password reset cost | Published $70 per password reset figure, widely cited across IT operations industry | [Password reset cost analysis](https://jumpcloud.com/blog/password-reset-cost) |
| S7 | Analysis | HappySignals Global IT Experience Benchmark 2024 | Published employee productivity loss data (2h 19min for large organizations) used to validate resolution-time baseline | [HappySignals benchmark](https://www.happysignals.com/global-it-experience-benchmark-2024) |
| S8 | Official docs | ServiceNow Table API documentation | Supports the ITSM ticket lifecycle integration pattern (create, update, work notes, close) | [ServiceNow Table API](https://www.servicenow.com/docs/bundle/yokohama-api-reference/page/integrate/inbound-rest/concept/c_TableAPI.html) |
| S9 | Official docs | Microsoft Graph API: authenticationMethod resetPassword | Supports the password reset adapter pattern, required permissions, and request/response contract | [Microsoft Graph password reset](https://learn.microsoft.com/en-us/graph/api/authenticationmethod-resetpassword?view=graph-rest-1.0) |
| S10 | Official docs | Microsoft Intune Graph API overview | Supports software assignment, device compliance queries, and endpoint management integration | [Intune Graph API](https://learn.microsoft.com/en-us/graph/intune-concept-overview) |
| S11 | Official docs | OpenAI models documentation | Supports the current model recommendation for classification and planning tasks | [OpenAI models](https://developers.openai.com/api/docs/models) |
| S12 | Official docs | OpenAI structured outputs guide | Supports schema-bound outputs and the `responses.parse` pattern with Pydantic | [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs) |
| S13 | Official docs | LangGraph overview documentation | Supports the state-graph orchestration pattern with nodes, edges, and conditional routing | [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) |
| S14 | Official docs | Okta SCIM provisioning documentation | Supports user provisioning and app assignment integration for Okta-based identity environments | [Okta SCIM](https://developer.okta.com/docs/concepts/scim/) |
| S15 | Official guidance | European Commission FAQ: Navigating the AI Act | Supports disclosure requirements for AI systems that interact directly with employees | [Navigating the AI Act](https://digital-strategy.ec.europa.eu/en/faqs/navigating-ai-act) |
| S16 | Official guidance | ICO guidance: Data minimisation | Supports the recommendation to keep employee context and credential data handling to the minimum necessary | [ICO data minimisation](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/data-minimisation/) |
| S17 | Industry recognition | Moveworks recognized as Challenger in 2025 Gartner Magic Quadrant for AI in ITSM | Validates vendor maturity and market position for AI-powered IT service desk solutions | [Moveworks Gartner MQ](https://www.moveworks.com/us/en/resources/blog/moveworks-in-gartner-ai-magic-quadrant-for-itsm) |
| S18 | Official docs | OpenAI function calling guide | Supports the tool-calling loop used in the orchestration pattern | [Function calling](https://developers.openai.com/api/docs/guides/function-calling) |

## Claim Map

| Claim Or Section | Source IDs |
|------------------|------------|
| UC-101 operating constraints, ticket volume assumptions, and target metrics | S1 |
| Solution design: bounded autonomy for L1 intents with deterministic gate and human fallback | S1, S2, S3, S4 |
| Solution design: ITSM platform remains the system of record and operator surface | S8 |
| Solution design: password resets as primary value driver (20-50% of volume, $70 each) | S1, S5, S6 |
| Solution design: identity provider and endpoint management integration seams | S9, S10, S14 |
| Solution design: disclosure, data minimization, and audit controls | S15, S16 |
| Implementation guide: OpenAI model choice and structured action proposal contract | S11, S12 |
| Implementation guide: tool-calling loop and state-graph orchestration | S13, S18 |
| Implementation guide: password reset adapter using Microsoft Graph API | S9 |
| Implementation guide: ServiceNow ticket lifecycle integration | S8 |
| Implementation guide: Intune software provisioning integration | S10 |
| Evaluation: published autonomous resolution, MTTR, and satisfaction evidence | S2, S3, S4 |
| Evaluation: cost-per-ticket baseline and economic scenario model | S1, S5, S6, S7 |
| Evaluation: credential exposure and identity mutation safety risks | S9, S15, S16 |
| Evaluation: vendor maturity and market validation | S17 |
