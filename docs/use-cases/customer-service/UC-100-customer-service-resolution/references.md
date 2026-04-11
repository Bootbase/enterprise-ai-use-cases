---
layout: use-case-detail
title: "References — Autonomous Customer Service Resolution with Agentic AI"
uc_id: "UC-100"
uc_title: "Autonomous Customer Service Resolution with Agentic AI"
detail_type: "references"
detail_title: "References"
category: "Customer Service"
category_icon: "headphones"
industry: "Cross-Industry (FinTech, SaaS, E-Commerce)"
complexity: "High"
status: "detailed"
slug: "UC-100-customer-service-resolution"
permalink: /use-cases/UC-100-customer-service-resolution/references/
---

## Source Quality Notes

The strongest business evidence in this case study comes from named deployments and operator-issued releases: Klarna, SoFi, Tubi, and Synthesia. Those sources are useful because they describe production outcomes, but most of them are still company- or vendor-published rather than independent benchmark studies. The implementation guidance is stronger because it relies on current official product documentation from OpenAI, LangGraph, Zendesk, and Stripe. The control model uses public regulatory and guidance material from the European Commission and the ICO rather than unsupported legal interpretation. The scenario economics in `evaluation.md` remain estimated even where they are anchored in published pricing or wage data.

## Source Register

| ID | Type | Source | Why It Was Used | Link |
|----|------|--------|-----------------|------|
| S1 | Internal brief | UC-100 research brief | Baseline scope, operating constraints, in-scope channels, and target success metrics | [Research brief](./index.md) |
| S2 | Primary deployment | Klarna AI assistant press release distributed by PR Newswire | Published scale, speed, repeat-inquiry, and profit-improvement metrics for a live deployment | [PR Newswire release](https://www.prnewswire.com/news-releases/klarna-ai-assistant-handles-two-thirds-of-customer-service-chats-in-its-first-month-302072740.html) |
| S3 | Primary deployment | Sierra customer story: SoFi | Published containment and NPS improvement metrics for a regulated financial-services deployment | [SoFi case study](https://sierra.ai/customers/sofi) |
| S4 | Primary deployment | Sierra customer story: Tubi | Published containment, CSAT, and resolution-speed metrics for a media support operation | [Tubi case study](https://sierra.ai/customers/tubi) |
| S5 | Primary deployment | Intercom customer story: Synthesia | Published content-quality lesson, self-serve metrics, and hours saved in a live deployment | [Synthesia case study](https://www.intercom.com/customers/synthesia) |
| S6 | Official docs | Intercom Help: Fin Procedures explained | Supports the design pattern of combining natural-language instructions with rules, code, and secure system access | [Fin Procedures explained](https://www.intercom.com/help/en/articles/12495167-fin-procedures-explained) |
| S7 | Official docs | Intercom Help: Fin AI Agent outcomes | Supports outcome definitions and the published `$0.99` per successful outcome price | [Fin outcomes](https://www.intercom.com/help/en/articles/8205718-fin-ai-agent-outcomes) |
| S8 | Official docs | OpenAI models documentation | Supports the current `gpt-5.4` and `gpt-5.4-mini` model recommendation | [OpenAI models](https://developers.openai.com/api/docs/models) |
| S9 | Official docs | OpenAI structured outputs guide | Supports schema-bound outputs and the `responses.parse` pattern with Pydantic | [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs) |
| S10 | Official docs | OpenAI function calling guide | Supports the tool-calling loop used in the orchestration pattern | [Function calling](https://developers.openai.com/api/docs/guides/function-calling) |
| S11 | Official docs | LangGraph Graph API overview | Supports the state, node, and conditional-edge orchestration pattern | [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| S12 | Official docs | Zendesk Ticket Audits API | Supports the use of audits as the read-only operational history of ticket changes | [Zendesk Ticket Audits API](https://developer.zendesk.com/api-reference/ticketing/tickets/ticket_audits/) |
| S13 | Official docs | Zendesk Ticket Comments API | Supports the public and private comment writeback pattern used for customer replies and AI notes | [Zendesk Ticket Comments API](https://developer.zendesk.com/api-reference/ticketing/tickets/ticket_comments/) |
| S14 | Official docs | Zendesk Ticket Metrics API | Supports first-resolution and full-resolution timing for pilot measurement | [Zendesk Ticket Metrics API](https://developer.zendesk.com/api-reference/ticketing/tickets/ticket_metrics/) |
| S15 | Official docs | Stripe API: Create a refund | Supports the narrow refund adapter pattern and refund payload design | [Stripe refund API](https://docs.stripe.com/api/refunds/create?lang=python) |
| S16 | Official docs | Stripe API: Update a subscription | Supports controlled subscription-change actions and proration handling | [Stripe subscription update API](https://docs.stripe.com/api/subscriptions/update) |
| S17 | Official docs | Stripe API: Idempotent requests | Supports the recommendation to use idempotency keys on write adapters | [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests?lang=curl) |
| S18 | Official guidance | European Commission FAQ: Navigating the AI Act | Supports disclosure requirements for AI systems that interact directly with people | [Navigating the AI Act](https://digital-strategy.ec.europa.eu/en/faqs/navigating-ai-act) |
| S19 | Official guidance | ICO guidance: Data minimisation | Supports the recommendation to keep customer context limited to what is necessary | [ICO data minimisation](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/data-minimisation/) |
| S20 | Official guidance | ICO guidance: Storage limitation | Supports retention and deletion guidance for workflow state and logs | [ICO storage limitation](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/storage-limitation/) |
| S21 | Official statistics | U.S. Bureau of Labor Statistics: Customer Service Representatives | Supports the labor-cost baseline used in the scenario model | [BLS occupational outlook](https://www.bls.gov/ooh/office-and-administrative-support/customer-service-representatives.htm) |

## Claim Map

| Claim Or Section | Source IDs |
|------------------|------------|
| UC-100 operating constraints, first-release scope boundaries, and target metrics | S1 |
| Solution design: bounded autonomy with explicit human fallback | S1, S2, S3, S4, S6, S18 |
| Solution design: helpdesk remains the system of record and operator surface | S12, S13, S14 |
| Solution design: retrieval-first policy architecture and content quality dependency | S5, S6 |
| Solution design: narrow action adapters, deterministic gate, and idempotent write control | S15, S16, S17 |
| Solution design: disclosure and personal-data minimization controls | S18, S19, S20 |
| Implementation guide: OpenAI model choice and structured action proposal contract | S8, S9 |
| Implementation guide: tool-calling loop and state-graph orchestration | S10, S11 |
| Implementation guide: Zendesk writeback and KPI instrumentation pattern | S12, S13, S14 |
| Implementation guide: Stripe refund and subscription integration pattern | S15, S16, S17 |
| Evaluation: published containment, speed, and experience evidence | S2, S3, S4, S5 |
| Evaluation: labor-cost assumption and economic scenario model | S1, S7, S21 |
| Evaluation: privacy, disclosure, and retention risks | S18, S19, S20 |
