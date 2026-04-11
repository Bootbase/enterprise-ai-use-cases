---
layout: use-case-detail
title: "Implementation Guide — Autonomous Customer Service Resolution with Agentic AI"
uc_id: "UC-100"
uc_title: "Autonomous Customer Service Resolution with Agentic AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Customer Service"
category_icon: "headphones"
industry: "Cross-Industry (FinTech, SaaS, E-Commerce)"
complexity: "High"
status: "detailed"
slug: "UC-100-customer-service-resolution"
permalink: /use-cases/UC-100-customer-service-resolution/implementation-guide/
---

## Build Goal

Build a production workflow that resolves the top repetitive chat and email intents without replacing the incumbent helpdesk. The first release should cover a single helpdesk, billing platform, and order or account service plus a short list of policy-bound intents. It should prove safe write control, faster resolution, and no material experience regression before wider rollout. Voice, fraud review, and long-tail case handling stay outside the first release. [S1][S2][S5]

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.12 service with FastAPI workers | Good fit for webhook-driven intake, async I/O, and the current model and orchestration SDKs. |
| **Model access** | OpenAI Responses API with `gpt-5.4-mini` as the default planner and `gpt-5.4` for harder cases | The current models guidance explicitly positions `gpt-5.4` for harder reasoning and smaller 5.4 variants for lower-latency workloads. [S8] |
| **Orchestration runtime** | LangGraph | This workflow is a state machine with fixed branches and explicit handoff points. |
| **Core connectors** | Zendesk ticket APIs, Stripe billing APIs, and internal order or account adapters | These seams already own the data and actions the AI needs; the build should wrap them rather than duplicate them. |
| **Evaluation / tracing** | Application traces joined to helpdesk audits and ticket metrics | Operators already trust the helpdesk record. Join traces to that surface instead of inventing a second operations UI. |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | Reliable intake and state foundation | Webhook receiver, conversation-state schema, ticket loader, private-note writeback, replay dataset, and supported-intent taxonomy |
| 2 | Grounded planning and control | Policy retrieval service, typed action proposal schema, deterministic gate, disclosure rules, and negative-path tests |
| 3 | Safe transactional pilot | Refund and subscription adapters, order and account lookups, human handoff payload, and supervised live pilot routing |
| 4 | Measured production rollout | KPI dashboard, threshold-tuning process, rollback controls, retention policy, and category-by-category release plan |

## Core Contracts

### State And Output Schemas

The core contract is the action proposal emitted by the model after it reads the current ticket, retrieved policy, and trusted system context. Treat the proposal as untrusted until the gate approves it. Structured outputs prevent downstream services from re-parsing free text. [S9]

```python
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field


class ActionProposal(BaseModel):
    intent: Literal[
        "order_status",
        "refund",
        "subscription_change",
        "account_update",
        "escalate",
    ]
    policy_basis: str
    confidence: float = Field(ge=0.0, le=1.0)
    customer_reply: str
    action_payload: dict
    escalation_reason: str | None = None


client = OpenAI()

proposal = client.responses.parse(
    model="gpt-5.4-mini",
    input=[
        {"role": "system", "content": planner_prompt},
        {"role": "user", "content": customer_message},
    ],
    text_format=ActionProposal,
).output_parsed
```

Keep `action_payload` narrow. If a tool needs more inputs than the gate can inspect easily, the tool boundary is too broad.

### Tool Interface Pattern

Expose one tool per business action. Do not expose raw billing, order, or helpdesk clients to the model. Stripe supports idempotent POST retries, so every write adapter should accept or generate an idempotency key. [S15][S16][S17]

```python
from typing import Literal
from uuid import uuid4

import stripe
from pydantic import BaseModel, Field


class RefundArgs(BaseModel):
    payment_intent: str
    amount_cents: int = Field(gt=0)
    reason: Literal["requested_by_customer", "duplicate", "fraudulent"]
    idempotency_key: str = Field(default_factory=lambda: str(uuid4()))


stripe_client = stripe.StripeClient(api_key=STRIPE_SECRET_KEY)


def create_refund(args: RefundArgs) -> dict:
    refund = stripe_client.v1.refunds.create(
        {
            "payment_intent": args.payment_intent,
            "amount": args.amount_cents,
            "reason": args.reason,
        },
        {"idempotency_key": args.idempotency_key},
    )
    return {"refund_id": refund.id, "status": refund.status}
```

## Orchestration Outline

Keep the workflow explicit: load the ticket, retrieve policy, ask the model for a typed proposal, run the gate, then either execute or hand off. LangGraph fits because it makes the branches visible. [S10][S11]

```python
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class ConversationState(TypedDict, total=False):
    ticket_id: int
    customer_text: str
    proposal: dict
    gate_result: Literal["approved", "review", "denied"]


builder = StateGraph(ConversationState)
builder.add_node("load_ticket", load_ticket)
builder.add_node("retrieve_policy", retrieve_policy)
builder.add_node("plan", plan_action)
builder.add_node("gate", run_policy_gate)
builder.add_node("execute", execute_action)
builder.add_node("handoff", handoff_to_human)
builder.add_node("reply", write_customer_reply)

builder.add_edge(START, "load_ticket")
builder.add_edge("load_ticket", "retrieve_policy")
builder.add_edge("retrieve_policy", "plan")
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

Do not let orchestration logic drift into prompt text. The graph decides when the workflow can continue. The prompt decides how the model should reason inside one step.

## Prompt And Guardrail Pattern

The system prompt should read like an operating rulebook. It should define authority, refusal conditions, supported intents, and the requirement to return only the approved schema. Keep policy passages and thresholds out of the static prompt where possible; inject them as retrieved context or configuration so support operations can change them without redeploying the workflow. [S6][S9][S18]

```text
You are the action planner for the support team.

Rules:
1. Use only retrieved policy and trusted tool results.
2. Never promise a refund, subscription change, or account update until the gate approves it.
3. If identity is unverified, confidence is below 0.75, or the customer asks for a human, return intent="escalate".
4. If the customer is distressed, threatening, or making a legal complaint, escalate.
5. Return only a valid ActionProposal object.

Supported intents:
- order_status
- refund
- subscription_change
- account_update
- escalate
```

The high-value guardrails belong outside the model. The prompt should reference them, not replace them.

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| Helpdesk intake and writeback | Webhook receiver, ticket loader, public reply writer, and private note writer | Use the incumbent helpdesk as the canonical case trail so operators do not have to reconcile multiple systems. |
| Policy content pipeline | Product and market tagged policy ingestion plus retrieval index | Do not treat content cleanup as a later optimization. |
| Billing mutation layer | Refund and subscription adapters with one method per allowed action | Use Stripe's native refund and subscription endpoints and enforce idempotency on POST requests. |
| Identity and customer context | Read-only account, order, and entitlement lookups | The model should consume identity status from trusted systems and never perform proofing itself. |
| Reporting join | Job that joins workflow traces to first-resolution and full-resolution ticket metrics | Zendesk already exposes the timings needed to compare AI and human outcomes. |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Intent and next-action selection | Replay labeled production tickets and score both intent and proposed action | `>= 90%` exact match on supported intents and next actions |
| Policy grounding | Check that every non-escalation proposal points to an active policy passage that actually allows the action | `>= 95%` grounded proposals in the replay set |
| Tool-use safety | Run negative scenarios for ineligible refunds, invalid subscription changes, and missing identity state | `0` disallowed writes in staging or supervised pilot |
| Human handoff quality | Review escalated cases for transcript completeness, policy context, and failure reason | `>= 90%` reviewer agreement that the handoff was sufficient |
| Operational impact | Compare first-resolution time, reopen rate, containment, and CSAT against the human baseline | No CSAT drop larger than `5` points and measurable speed improvement before broader rollout |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start in shadow mode, then supervised live traffic for one region and one intent bundle, then widen only after replay plus pilot gates are met. |
| **Fallback path** | Any model outage, retrieval failure, gate denial, or adapter error should generate an immediate human handoff and preserve the transcript in the same ticket. |
| **Observability** | Persist a workflow trace ID in a private note, then use helpdesk audits and metrics as the operator-facing record. |
| **Operations ownership** | Support operations owns supported intents, thresholds, content quality, and escalation policy. Platform engineering owns orchestration, connectors, and runtime reliability. |
| **Data handling** | Keep workflow state minimal, align log retention to the enterprise policy, and avoid storing customer payloads longer than the operational need requires. |
