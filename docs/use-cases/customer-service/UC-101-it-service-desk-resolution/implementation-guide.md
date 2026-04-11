---
layout: use-case-detail
title: "Implementation Guide — Autonomous IT Service Desk Resolution with Agentic AI"
uc_id: "UC-101"
uc_title: "Autonomous IT Service Desk Resolution with Agentic AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Customer Service"
category_icon: "headphones"
industry: "Cross-Industry (Technology, Financial Services, Manufacturing, Pharmaceutical, Professional Services)"
complexity: "High"
status: "detailed"
slug: "UC-101-it-service-desk-resolution"
permalink: /use-cases/UC-101-it-service-desk-resolution/implementation-guide/
---

## Build Goal

Build a production workflow that autonomously resolves the top L1 IT service desk requests — password resets, account unlocks, and software provisioning — without replacing the incumbent ITSM platform. The first release should cover a single ITSM instance, one identity provider, one endpoint management platform, and a short list of runbook-bound intents. It should prove safe identity mutation control, sub-minute resolution, and no security regression before wider rollout. L3 incidents, security investigations, and hardware procurement stay outside the first release. [S1][S2][S3]

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.12 service with FastAPI workers | Good fit for webhook-driven intake from Slack and Teams, async I/O for parallel identity and ITSM calls, and current model SDKs. |
| **Model access** | OpenAI Responses API with `gpt-5.4-mini` as default classifier and `gpt-5.4` for multi-step troubleshooting | The smaller model handles high-volume L1 classification at lower latency. The larger model is reserved for cases that require multi-turn reasoning. [S11] |
| **Orchestration runtime** | LangGraph | The workflow is a state machine with fixed branches (classify, retrieve, plan, gate, execute, escalate) and explicit handoff points. [S13] |
| **Core connectors** | ServiceNow Table API, Microsoft Graph API (Entra ID and Intune), Slack/Teams bot SDK | These seams already own the data and actions the AI needs. The build should wrap them, not duplicate them. [S8][S9][S10] |
| **Evaluation / tracing** | Application traces joined to ITSM ticket work notes and SLA metrics | Analysts already trust the ITSM record. Join traces to that surface instead of building a separate operations UI. |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | Reliable intake and state foundation | Channel bot (Slack/Teams), ticket-state schema, ITSM ticket loader, work-note writeback, replay dataset of labeled historical tickets, supported-intent taxonomy |
| 2 | Grounded classification and control | Knowledge retrieval service, typed action proposal schema, deterministic gate, identity verification check, negative-path tests for out-of-scope and low-confidence cases |
| 3 | Safe identity and provisioning pilot | Password reset adapter (Microsoft Graph), account unlock adapter, software assignment adapter (Intune), human handoff payload, supervised live pilot on shadow traffic |
| 4 | Measured production rollout | KPI dashboard (autonomous resolution rate, MTTR, CSAT), threshold-tuning process, rollback controls, category-by-category release plan |

## Core Contracts

### State And Output Schemas

The core contract is the action proposal emitted by the model after it reads the ticket, retrieved runbook, and employee context. Treat the proposal as untrusted until the gate approves it. Structured outputs prevent downstream adapters from re-parsing free text. [S12]

```python
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field


class ActionProposal(BaseModel):
    intent: Literal[
        "password_reset",
        "account_unlock",
        "software_provision",
        "access_grant",
        "vpn_troubleshoot",
        "knowledge_answer",
        "escalate",
    ]
    runbook_basis: str
    confidence: float = Field(ge=0.0, le=1.0)
    employee_reply: str
    action_payload: dict
    escalation_reason: str | None = None


client = OpenAI()

proposal = client.responses.parse(
    model="gpt-5.4-mini",
    input=[
        {"role": "system", "content": planner_prompt},
        {"role": "user", "content": employee_message},
    ],
    text_format=ActionProposal,
).output_parsed
```

Keep `action_payload` narrow. If an adapter needs more inputs than the gate can inspect, the tool boundary is too broad.

### Tool Interface Pattern

Expose one tool per IT action. Do not expose raw identity provider or ITSM clients to the model. The password reset adapter below uses the Microsoft Graph API, which requires delegated permissions with an administrator role and returns a `202 Accepted` with a location header for status polling. [S9]

```python
from msgraph import GraphServiceClient
from msgraph.generated.users.item.authentication.methods.item.reset_password.reset_password_post_request_body import (
    ResetPasswordPostRequestBody,
)
from pydantic import BaseModel

PASSWORD_METHOD_ID = "28c10230-6103-485e-b985-444c60001490"


class PasswordResetArgs(BaseModel):
    user_principal_name: str
    generate_password: bool = True


async def reset_password(
    graph_client: GraphServiceClient, args: PasswordResetArgs
) -> dict:
    request_body = ResetPasswordPostRequestBody()
    result = await (
        graph_client.users.by_user_id(args.user_principal_name)
        .authentication.methods.by_authentication_method_id(PASSWORD_METHOD_ID)
        .reset_password.post(request_body)
    )
    return {
        "status": "accepted",
        "new_password": result.new_password if result else None,
    }
```

## Orchestration Outline

The workflow follows a fixed path: load the ticket, classify intent, retrieve the matching runbook, ask the model for a typed proposal, run the gate, then either execute or hand off. LangGraph makes the branches explicit. [S13][S18]

```python
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class TicketState(TypedDict, total=False):
    ticket_id: str
    employee_text: str
    intent: str
    proposal: dict
    gate_result: Literal["approved", "review", "denied"]


builder = StateGraph(TicketState)
builder.add_node("load_ticket", load_ticket)
builder.add_node("classify", classify_intent)
builder.add_node("retrieve_runbook", retrieve_runbook)
builder.add_node("plan", plan_action)
builder.add_node("gate", run_policy_gate)
builder.add_node("execute", execute_action)
builder.add_node("handoff", handoff_to_analyst)
builder.add_node("reply", write_employee_reply)

builder.add_edge(START, "load_ticket")
builder.add_edge("load_ticket", "classify")
builder.add_edge("classify", "retrieve_runbook")
builder.add_edge("retrieve_runbook", "plan")
builder.add_edge("plan", "gate")
builder.add_conditional_edges(
    "gate",
    route_after_gate,
    {"approved": "execute", "review": "handoff", "denied": "handoff"},
)
builder.add_edge("execute", "reply")
builder.add_edge("reply", END)
builder.add_edge("handoff", END)

workflow = builder.compile()
```

## Prompt And Guardrail Pattern

The system prompt should read like an IT operations rulebook. It defines authority, refusal conditions, supported intents, and the requirement to return only the approved schema. Keep runbook passages and thresholds out of the static prompt; inject them as retrieved context so IT operations can update procedures without redeploying the workflow. [S12][S15]

```text
You are the action planner for the IT service desk.

Rules:
1. Use only retrieved runbook content and trusted tool results.
2. Never promise a password reset, access grant, or software install until the gate approves it.
3. If identity is unverified, confidence is below 0.80, or the employee asks for a human, return intent="escalate".
4. If the request involves privileged access, security incidents, or hardware, escalate.
5. Never include temporary passwords, tokens, or secrets in the employee reply.
6. Return only a valid ActionProposal object.

Supported intents:
- password_reset
- account_unlock
- software_provision
- access_grant
- vpn_troubleshoot
- knowledge_answer
- escalate
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| ITSM ticket lifecycle | Ticket loader, work-note writer, SLA query, and ticket closer via ServiceNow Table API | Use the ITSM platform as the canonical audit trail. Every AI action writes a structured work note with the action proposed, gate decision, and result. [S8] |
| Identity mutations | Password reset and account unlock adapters via Microsoft Graph API | The password reset endpoint requires delegated permissions with Authentication Administrator role. Never log the returned temporary password. [S9] |
| Software provisioning | App assignment adapter via Intune Graph API or SCCM task sequence trigger | Check device compliance status before assigning software. Confirm installation state after deployment. [S10] |
| Knowledge retrieval | Ingestion pipeline for runbooks and known-error articles, plus a retrieval endpoint filtered by category and application | Tag articles by application, platform, and effective date. Stale runbooks are the primary source of incorrect AI guidance. |
| Channel integration | Slack and Teams bot that creates or links tickets and relays AI responses | The bot is a thin layer. All resolution logic runs server-side through the orchestration graph. |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Intent classification accuracy | Replay labeled historical tickets and score intent plus category assignment | >= 92% exact match on supported intents |
| Runbook grounding | Check that every non-escalation proposal cites an active runbook article that actually supports the proposed action | >= 95% grounded proposals in the replay set |
| Identity mutation safety | Run negative scenarios: wrong user, unverified identity, expired account, privileged target | 0 unauthorized identity writes in staging or supervised pilot |
| Escalation quality | Review escalated cases for transcript completeness, runbook context, and failure reason | >= 90% reviewer agreement that the handoff was sufficient for analyst continuation |
| Operational impact | Compare autonomous resolution rate, MTTR, and employee satisfaction against the pre-AI baseline | Autonomous resolution >= 35% in pilot; MTTR under 2 minutes for resolved tickets; no CSAT drop > 5 points |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start in shadow mode (AI proposes, analyst executes) for two weeks, then supervised live traffic for password resets only, then add intents one at a time after each passes the evaluation harness. |
| **Fallback path** | Any model outage, retrieval failure, gate denial, or adapter error generates an immediate human handoff. The ticket stays in the ITSM system with full context preserved. |
| **Observability** | Persist a workflow trace ID in the ITSM work note. Use ITSM-native SLA metrics and resolution timers as the operator-facing record. Alert on gate denial spikes and adapter error rates. |
| **Operations ownership** | IT operations owns the supported-intent taxonomy, runbook quality, confidence thresholds, and escalation policy. Platform engineering owns orchestration, connectors, and runtime reliability. |
| **Data handling** | Never log temporary passwords, reset tokens, or MFA secrets. Keep workflow state minimal. Align log retention to enterprise data policy and SOC 2 requirements. [S15][S16] |
