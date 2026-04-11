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

The strongest external evidence for UC-101 comes from named production deployments at IBM and Moveworks customers. Those sources are useful because they report live operational metrics, but most are still company- or vendor-published rather than independent benchmark studies. That means the published numbers should be treated as directional evidence that the workflow class is real, not as universal performance targets. The implementation guidance is stronger because it rests on current official documentation from ServiceNow, Okta, Microsoft, OpenAI, and LangGraph. The economic model in `evaluation.md` is intentionally estimated and conservative; it combines the internal brief, public wage data, and current model pricing rather than claiming a published ROI benchmark.

## Source Register

| ID | Type | Source | Why It Was Used | Link |
|----|------|--------|-----------------|------|
| S1 | Internal brief | UC-101 research brief | Baseline scope, constraints, target metrics, and incumbent-system assumptions | [Research brief](./index.md) |
| S2 | Primary deployment | IBM case study: `AskIT` | Supports production-scale internal support automation and published successful-handling metrics | [IBM AskIT case study](https://www.ibm.com/case-studies/cio-watsonx-askit) |
| S3 | Primary deployment | Broadcom customer story | Supports the published `88%` autonomous resolution figure for employee-support workflows | [Broadcom + Moveworks](https://www.moveworks.com/us/en/customers/broadcom-integrates-it-knowledge-base-with-moveworks-ai) |
| S4 | Primary deployment | Equinix customer story | Supports routing-speed, routing-accuracy, and ticket-lifespan improvement claims | [Equinix + Moveworks](https://www.moveworks.com/us/en/customers/equinix-disappears-it-queue-with-moveworks-triage-ticketing-system) |
| S5 | Primary deployment / vendor solution page | Moveworks identity and access management page | Supports the Achieve password-reset metric and Verisk account-issue volume metric for identity-heavy support work | [Moveworks IAM](https://www.moveworks.com/us/en/solutions/identity-access-management) |
| S6 | Official docs | ServiceNow REST API Explorer learning module | Supports the use of narrow REST-based reads and writes against the ITSM system of record | [ServiceNow REST API Explorer](https://developer.servicenow.com/print_page.do?category=learning-module&identifier=app_store_learnv2_rest_xanadu_introduction_to_the_rest_api_explorer%2Cservicenow_application_developer&module=learning+plan&release=xanadu) |
| S7 | Official docs | ServiceNow Scripted REST APIs learning module | Supports the recommendation to hide broad ITSM privileges behind a small internal API surface | [ServiceNow Scripted REST APIs](https://developer.servicenow.com/print_page.do?category=course-module&identifier=app_store_learnv2_rest_xanadu_scripted_rest_apis%2Capp_store_learnv2_rest_xanadu_scripted_rest_api_error_objects&module=course&release=xanadu) |
| S8 | Official docs | Okta User Lifecycle API | Supports account lifecycle actions such as unlock and activation being executed by the identity platform rather than by the model | [Okta User Lifecycle API](https://developer.okta.com/docs/api/openapi/okta-management/management/tag/UserLifecycle/) |
| S9 | Official docs | Okta User Credentials API | Supports password-reset and credential-management flows staying inside the IdP-native API surface | [Okta User Credentials API](https://developer.okta.com/docs/api/openapi/okta-management/management/tag/UserCred/) |
| S10 | Official docs | Microsoft Graph `rebootNow` action for managed devices | Supports managed-device recovery as a narrow endpoint action in the first release | [Microsoft Graph rebootNow](https://learn.microsoft.com/en-us/graph/api/intune-devices-manageddevice-rebootnow?view=graph-rest-1.0) |
| S11 | Official guidance | NIST SP 800-63B, Digital Identity Guidelines | Supports keeping identity verification and recovery controls outside conversational improvisation | [NIST SP 800-63B](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-63b.pdf) |
| S12 | Official statistics | U.S. Bureau of Labor Statistics: Computer Support Specialists | Supports the labor-cost anchor used in the scenario model | [BLS Occupational Outlook](https://www.bls.gov/ooh/computer-and-information-technology/computer-support-specialists.htm) |
| S13 | Official docs | OpenAI models documentation | Supports the current `gpt-5.4` and `gpt-5.4-mini` model recommendation | [OpenAI models](https://developers.openai.com/api/docs/models) |
| S14 | Official docs | OpenAI API pricing | Supports the estimated per-ticket compute-cost model in `evaluation.md` | [OpenAI pricing](https://openai.com/api/pricing/) |
| S15 | Official docs | OpenAI structured outputs guide | Supports the typed `TicketPlan` contract and schema-bound planner pattern | [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs) |
| S16 | Official docs | OpenAI function calling guide | Supports the tool-calling loop used between the planner and control-plane tools | [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling) |
| S17 | Official docs | LangGraph Graph API overview | Supports the explicit state-graph orchestration pattern in the implementation guide | [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) |

## Claim Map

| Claim Or Section | Source IDs |
|------------------|------------|
| UC-101 baseline scope, constraints, and first-release boundary | S1 |
| Solution design: bounded autonomy for routine identity, device, and KB-backed L1 work | S1, S2, S3, S4, S5 |
| Solution design: incumbent ITSM remains the system of record and audit surface | S1, S6, S7 |
| Solution design: identity verification stays outside the conversational model and inside the IdP flow | S8, S9, S11 |
| Solution design: endpoint recovery as a narrow, managed-device action | S1, S10 |
| Implementation guide: structured planner contract and OpenAI-based planning loop | S13, S15, S16 |
| Implementation guide: LangGraph workflow with deterministic verify and execute branches | S17 |
| Implementation guide: ServiceNow, Okta, and Microsoft Graph integration pattern | S6, S7, S8, S9, S10 |
| Evaluation: published production evidence for autonomous or accelerated employee support | S2, S3, S4, S5 |
| Evaluation: labor-cost and per-ticket operating-cost scenario model | S1, S12, S13, S14 |
| Evaluation: evidence limitations and rollout-risk framing | S1, S2, S3, S4, S5, S11 |
