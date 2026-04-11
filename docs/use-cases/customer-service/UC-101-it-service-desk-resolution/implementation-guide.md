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

Build a production service that accepts employee support requests from the existing channels, enriches them with trusted context, produces a typed plan, and either executes a small approved action set or hands the ticket to the right analyst with a complete summary. The first boundary should cover one ITSM instance, one identity provider, one endpoint tool, and the top three repetitive intents. Privileged access changes and L3 incidents stay outside the first release. [S1][S6][S7][S8][S9][S10]

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.12+ with FastAPI | Good connector ecosystem and straightforward Pydantic contracts |
| **Model access** | OpenAI Responses API | One API surface for structured outputs, tool calling, and conversational turns. [S13][S14][S15][S16] |
| **Orchestration runtime** | LangGraph | Clear state-machine control for `enrich -> plan -> verify -> execute or handoff`. [S17] |
| **Core connectors** | ServiceNow REST, Okta Management API, Microsoft Graph device actions | Covers the minimum production write path for tickets, account unlock or reset, and managed-device recovery. [S6][S7][S8][S9][S10] |
| **Evaluation / tracing** | Structured trace store plus ticket-linked analytics | The release gate depends on replaying the exact plan, retrieved evidence, gate decision, and tool outcome. |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | Stable intake and ticket context | Channel gateway, ITSM event listener, ticket envelope schema, KB ingestion pipeline, historical ticket export for evaluation |
| 2 | Reliable planning and answer generation | Typed plan schema, system prompt, retrieval layer, shadow-mode planner, handoff summary generator |
| 3 | Safe write path for first-release actions | Internal control-plane API, ServiceNow writeback, Okta unlock or password-reset adapter, Intune reboot adapter, idempotency handling |
| 4 | Pilot and controlled execution | Resolver-group rollout, shadow-to-live release gates, dashboards, kill switch, on-call ownership, analyst feedback loop |

## Core Contracts

### State And Output Schemas

The planner output is the core contract. The model should emit one supported intent, one proposed action, the confidence for that action, and the evidence used to justify it. That gives the control plane something deterministic to validate and gives reviewers something concrete to label. [S1][S14][S15]

```python
from enum import Enum
from pydantic import BaseModel, Field

class ResolutionAction(str, Enum):
    ANSWER_ONLY = "answer_only"
    RESET_PASSWORD = "reset_password"
    UNLOCK_USER = "unlock_user"
    REBOOT_DEVICE = "reboot_device"
    ESCALATE = "escalate"

class TicketPlan(BaseModel):
    intent: str = Field(min_length=1)
    action: ResolutionAction
    confidence: float = Field(ge=0.0, le=1.0)
    verification_required: bool = True
    kb_article_ids: list[str] = []
    justification: str = Field(min_length=1)
    user_message: str = Field(min_length=1)
```

### Tool Interface Pattern

Do not expose raw admin APIs or shell access to the model. Expose a small internal control-plane endpoint that accepts a ticket ID, one allowlisted action, and the minimum subject identifiers required to execute it. The control plane owns auth, entitlement checks, retries, and audit writeback. [S6][S7][S8][S9][S10]

```python
from langchain_core.tools import tool
import requests

@tool
def execute_low_risk_action(
    ticket_id: str,
    action: str,
    subject_id: str,
    device_id: str | None = None,
) -> dict:
    """Execute one approved service-desk action through the internal gate."""
    response = requests.post(
        "https://it-automation.internal/v1/actions",
        json={
            "ticket_id": ticket_id,
            "action": action,
            "subject_id": subject_id,
            "device_id": device_id,
        },
        headers={"Authorization": "Bearer $CONTROL_PLANE_TOKEN"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
```

## Orchestration Outline

The runtime should treat every ticket like a short-lived workflow, not an open-ended agent session. A typical path is: receive the event, enrich context, retrieve KB passages, ask the model for a typed plan, validate the plan against deterministic rules, execute one action if approved, then write the outcome back to the ticket. If any prerequisite fails, stop and produce a human handoff. [S6][S7][S13][S15][S16][S17]

```python
from openai import OpenAI
from langgraph.graph import START, END, StateGraph

client = OpenAI()

def plan_ticket(state: dict) -> dict:
    response = client.responses.parse(
        model="gpt-5.4-mini",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": state["prompt_context"]},
        ],
        text_format=TicketPlan,
    )
    return {"plan": response.output_parsed}

graph = StateGraph(dict)
graph.add_node("enrich", enrich_context)
graph.add_node("plan", plan_ticket)
graph.add_node("verify", verify_guardrails)
graph.add_node("execute", execute_action_node)
graph.add_node("handoff", handoff_to_analyst)

graph.add_edge(START, "enrich")
graph.add_edge("enrich", "plan")
graph.add_conditional_edges("plan", route_plan, {"verify": "verify", "handoff": "handoff"})
graph.add_conditional_edges("verify", route_verified, {"execute": "execute", "handoff": "handoff"})
graph.add_edge("execute", END)
graph.add_edge("handoff", END)

workflow = graph.compile()
```

## Prompt And Guardrail Pattern

The system prompt should read like an operating policy. It must define the supported actions, the refusal conditions, and the requirement to use retrieved evidence only. It should also make clear that the model never asks for a password, MFA token, recovery code, or secret.

```text
You are the planner for an enterprise IT service desk.

You may choose only one action from the approved action enum.
Use only the ticket, employee, asset, and KB context provided to you.
Never ask the employee for a password, MFA code, recovery code, or token.
If identity verification has not already succeeded, do not select a write action.
If the request suggests a security incident, privilege escalation, or unsupported change,
select ESCALATE.
If the KB does not clearly support the action, select ESCALATE.
Output only JSON matching the TicketPlan schema.
```

Guardrails should sit outside the prompt too. Validate the schema, clamp the confidence range, verify the action against an allowlist, require a known ticket ID before tool use, and reject any attempt to reuse a tool outcome for a different ticket. Keep identity recovery in the identity system and keep authentication secrets out of the conversational layer. [S11][S15][S16]

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| **ITSM event and writeback** | Ticket listener plus internal wrapper for incident comment, work note, assignment, and closure updates | Keep the AI trail in the ticket itself. Avoid broad table writes from the orchestration service. [S6][S7] |
| **Identity actions** | Internal adapter that maps approved actions to Okta lifecycle and credential flows | Use a dedicated service account, verify employee context before the call, and log both request and outcome. [S8][S9] |
| **Endpoint recovery** | Managed-device adapter for reboot or sync on known employee devices | Require explicit device ownership in context and limit actions to Intune-managed endpoints in the first release. [S10] |
| **Knowledge retrieval** | Ingest runbooks and KB articles into a tagged retrieval index | Tag by resolver group, platform, and effective date so old guidance is filtered out. |
| **Channel identity mapping** | User-identity resolver between chat IDs, email addresses, and the directory identity | Ticket context is only trustworthy if the runtime can map a channel user to the right employee record. |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| **Plan accuracy** | Label 500+ historical tickets against the supported action set and compare model-selected action to analyst-reviewed ground truth | Precision >= 0.92 on in-scope action selection |
| **Tool use / writeback safety** | Run shadow mode on live tickets and verify every proposed write against the control-plane allowlist and ITSM audit trail | Zero unapproved state-changing calls |
| **Human escalation quality** | Review handoff packets for completeness: intent, retrieved evidence, attempted action, and blocked condition | >= 95% of escalations contain the required handoff fields |
| **Latency and user experience** | Measure median first response, median full resolution time, and ticket reopen rate for AI-resolved intents | First response < 3 seconds; automated resolution < 60 seconds; reopen rate <= human baseline |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start with one service desk, one region, and the top three repetitive intents. Run two to four weeks in shadow mode before enabling live execution. |
| **Fallback path** | Keep the existing queue routing intact. A kill switch should disable live actions and leave the planner in summarize-and-escalate mode only. |
| **Observability** | Trace the retrieved KB set, model plan, verification result, action request, action outcome, and ticket reopen signal under one ticket ID. |
| **Operations ownership** | Service-desk engineering owns the orchestration service; IAM and endpoint teams own the underlying action adapters and policy checks. |
| **Change control** | Expand the action catalog only after the pilot shows stable safety and reopen metrics. |
