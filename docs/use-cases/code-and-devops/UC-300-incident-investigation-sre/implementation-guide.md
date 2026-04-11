---
layout: use-case-detail
title: "Implementation Guide — Autonomous Incident Investigation with Agentic AI Site Reliability Engineers"
uc_id: "UC-300"
uc_title: "Autonomous Incident Investigation with Agentic AI Site Reliability Engineers"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Code & DevOps"
category_icon: "terminal"
industry: "Cross-Industry (SaaS, Internet Platforms, FinTech, Travel, E-Commerce)"
complexity: "High"
status: "detailed"
slug: "UC-300-incident-investigation-sre"
permalink: /use-cases/UC-300-incident-investigation-sre/implementation-guide/
---

## Build Goal

The delivery team builds an AI-powered investigation agent that monitors alerting channels, autonomously investigates production alerts using read-only access to the observability stack, and posts structured root-cause analyses into Slack within minutes. The first production release covers recurring infrastructure alerts — pod crash loops, latency spikes, error-rate threshold breaches, database saturation, and deployment-correlated regressions — for a single team's alerting channel. Cross-team correlation, auto-remediation, application-level business-metric alerts, and proactive anomaly detection remain outside the first release. [S1][S3]

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python service (FastAPI) hosting the agent loop, tool adapters, and Slack bot. Deployed as a long-running container on Kubernetes. | The agent runs continuously (24/7) and must process alerts with low latency. Python provides the best ecosystem for LLM SDKs, observability client libraries, and Kubernetes API clients. |
| **Model access** | Anthropic Claude API or OpenAI GPT-4 class API for hypothesis generation, evidence reasoning, and RCA synthesis. | Investigation requires multi-step reasoning across heterogeneous data (metrics, logs, traces, code diffs). Frontier models handle the context length and reasoning depth. Datadog and Cleric both use frontier LLMs. [S3][S9] |
| **Orchestration runtime** | LangGraph for the hypothesis-driven investigation loop. The agent graph branches on hypotheses, queries tools at each node, and prunes or deepens based on evidence. | The investigation pattern is a branching tree, not a linear chain. LangGraph's graph-based state machine maps directly to the "form hypothesis → query → validate → branch" pattern that Datadog describes as the core of Bits AI SRE. [S9] |
| **Core connectors** | Read-only API adapters for Datadog (metrics, logs, traces), Kubernetes API (pod state, events), deployment system (ArgoCD/GitHub Actions API for recent deploys), and Slack Bot API for posting results and receiving feedback. | These four connectors cover the minimum viable investigation: telemetry, infrastructure state, change history, and engineer interaction. BlaBlaCar's Cleric deployment integrates with Datadog, Kubernetes, PagerDuty, and Slack. [S1] |
| **Evaluation / tracing** | LangSmith for prompt/completion logging, tool-call tracing, and investigation quality dashboards. OpenTelemetry for agent runtime metrics (latency, error rate, queue depth). | Every investigation must be auditable — which tools were called, what evidence was returned, how the hypothesis evolved. Cleric uses LangSmith for this purpose. Datadog built an Agent Trace view for the same reason. [S2][S4] |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | Alert ingestion and tool connectivity | Slack bot receiving alerts from one team's alerting channel. Read-only adapters for Datadog API (metrics, logs, traces), Kubernetes API (pod state, events), and deployment system (recent deploys, commit history). Alert normalization and classification pipeline. |
| 2 | Investigation agent core | Hypothesis-driven investigation loop using LangGraph. Tool-calling interface for each adapter. Hypothesis tree with branching and pruning. Structured RCA output schema. Confidence scoring. Initial prompt and guardrail design. |
| 3 | Slack interaction and knowledge store | RCA posting to Slack with evidence links. Engineer feedback capture (thumbs up/down, edits). Knowledge store with past investigations and runbook retrieval. Investigation quality dashboard in LangSmith. |
| 4 | Pilot and calibration | Shadow mode: agent investigates alongside human SREs for 3–6 weeks. Side-by-side comparison of AI vs. human RCA quality. Confidence threshold calibration. False positive rate measurement. Go/no-go for autonomous posting. Cleric reached pilot validation in 3–6 weeks at BlaBlaCar. [S1] |

## Core Contracts

### State And Output Schemas

The investigation agent operates on a structured investigation record that tracks the lifecycle from alert ingestion through hypothesis testing to final RCA. This contract ensures every investigation carries its evidence chain and is reviewable by the on-call engineer.

```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class HypothesisStatus(str, Enum):
    INVESTIGATING = "investigating"
    VALIDATED = "validated"
    REFUTED = "refuted"
    INCONCLUSIVE = "inconclusive"

class Hypothesis(BaseModel):
    """A single root-cause hypothesis with supporting evidence."""
    statement: str
    status: HypothesisStatus
    evidence: list[str] = []       # log excerpts, metric values, trace IDs
    sub_hypotheses: list["Hypothesis"] = []
    tool_calls: list[str] = []     # which tools were queried

class InvestigationResult(BaseModel):
    """Final output posted to Slack and stored in the knowledge store."""
    alert_id: str
    service: str
    alert_type: str                # e.g. "latency_spike", "crash_loop"
    severity: Severity
    root_cause: str                # one-sentence root cause
    confidence: float = Field(ge=0.0, le=1.0)
    hypothesis_tree: Hypothesis
    suggested_remediation: str
    evidence_links: list[str] = [] # URLs to dashboards, logs, traces
    investigation_duration_sec: int
    created_at: datetime
    feedback_score: int | None = None  # 1-5 from engineer
```

### Tool Interface Pattern

The investigation agent interacts with observability tools through scoped, read-only tool adapters. Each tool has a clear contract: what it accepts, what it returns, and what it cannot do. The agent cannot modify any production state through these tools.

```python
# Tool definitions for the investigation agent.
# All tools are read-only. No tool can modify production state.

investigation_tools = [
    {
        "name": "query_metrics",
        "description": "Query time-series metrics from the observability platform. "
                       "Returns metric values for a service over a time range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},        # e.g. Datadog metric query
                "service": {"type": "string"},
                "start": {"type": "string", "format": "date-time"},
                "end": {"type": "string", "format": "date-time"},
            },
            "required": ["query", "service", "start", "end"],
        },
    },
    {
        "name": "search_logs",
        "description": "Search logs for a service within a time range. "
                       "Returns matching log entries with timestamps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "service": {"type": "string"},
                "start": {"type": "string", "format": "date-time"},
                "end": {"type": "string", "format": "date-time"},
                "limit": {"type": "integer", "default": 100},
            },
            "required": ["query", "service", "start", "end"],
        },
    },
    {
        "name": "get_recent_deployments",
        "description": "List recent deployments for a service from the deployment "
                       "system. Returns commit hash, author, timestamp, and diff summary.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {"type": "string"},
                "hours_back": {"type": "integer", "default": 24},
            },
            "required": ["service"],
        },
    },
    {
        "name": "get_pod_state",
        "description": "Get current Kubernetes pod state for a service. Returns "
                       "pod status, restart count, events, and resource usage.",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "service": {"type": "string"},
            },
            "required": ["namespace", "service"],
        },
    },
]
```

## Orchestration Outline

The investigation follows a hypothesis-driven loop. The agent forms an initial hypothesis from the alert context, queries tools to test it, then branches deeper or pivots based on evidence. This mirrors how Datadog built Bits AI SRE: "recursively generates deeper root cause hypotheses until it exhausts the search space." [S9]

```python
# Simplified investigation loop using LangGraph pattern.

from langgraph.graph import StateGraph, END

async def investigate(state: InvestigationState) -> InvestigationState:
    # Step 1: Load context — recent deploys, past incidents, service topology
    context = await load_context(state.alert)

    # Step 2: Form initial hypothesis from alert type + context
    hypothesis = await llm.generate_hypothesis(state.alert, context)

    # Step 3: Hypothesis-driven loop — query, validate, branch
    while hypothesis.status == HypothesisStatus.INVESTIGATING:
        # Query relevant tools based on the hypothesis
        evidence = await run_tool_queries(hypothesis, state.tools)

        # Evaluate evidence against the hypothesis
        evaluation = await llm.evaluate_hypothesis(hypothesis, evidence)

        if evaluation.validated:
            hypothesis.status = HypothesisStatus.VALIDATED
        elif evaluation.needs_deeper:
            # Branch into sub-hypotheses
            sub = await llm.generate_sub_hypotheses(hypothesis, evidence)
            hypothesis.sub_hypotheses.extend(sub)
            hypothesis = sub[0]  # investigate deepest branch first
        else:
            hypothesis.status = HypothesisStatus.REFUTED
            hypothesis = next_uninvestigated(state.hypothesis_tree)
            if hypothesis is None:
                break

    # Step 4: Synthesize final RCA from the hypothesis tree
    rca = await llm.synthesize_rca(state.hypothesis_tree, state.alert)

    # Step 5: Post to Slack or escalate based on confidence
    if rca.confidence >= state.confidence_threshold:
        await post_to_slack(rca, state.channel)
    else:
        await escalate_to_oncall(rca, state.alert)

    return state.with_result(rca)
```

## Prompt And Guardrail Pattern

The investigation agent uses a system prompt that enforces structured reasoning, evidence-based conclusions, and clear boundaries on what the agent can and cannot claim.

```text
You are an SRE investigation agent. When an alert fires, you investigate
the root cause by querying observability tools and forming hypotheses.

Rules:
- Always start with the alert payload and recent context (deployments,
  past incidents for this service, known failure modes).
- Form a specific, testable hypothesis before querying any tool.
  State what you expect to find and why.
- After each tool query, state whether the evidence supports, refutes,
  or is inconclusive for your hypothesis. Do not skip this step.
- If a hypothesis is refuted, pivot to an alternative. Do not force-fit
  evidence to a disproven theory.
- Limit your investigation to 15 tool calls. If you cannot reach a
  root cause within this budget, report your best hypothesis with
  a low confidence score and escalate.
- Never fabricate evidence. Every metric value, log line, and trace ID
  must come from a tool call result.
- Never take production write actions (rollback, restart, scale,
  feature flag toggle). You may suggest them with rationale.
- If the alert involves authentication, PII-bearing logs, or security
  signals, flag it for security review and stop investigation.
- Output a structured RCA with: root cause (one sentence), confidence
  (0.0-1.0), hypothesis chain, evidence links, and suggested
  remediation.
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| Observability API adapter | Read-only adapter for the primary observability platform (Datadog, Prometheus/Grafana, CloudWatch, or New Relic). Must support metric queries, log search, trace retrieval, and dashboard links. | Datadog provides a well-documented REST API and Python SDK (`datadog-api-client`). For Prometheus, use the HTTP API for instant and range queries. For CloudWatch, use `boto3` with read-only IAM policies. Bits AI SRE now accesses metrics, logs, traces, dashboards, changes, source code, RUM, database monitoring, network path, and continuous profiler — start with the first four and expand. [S3][S4] |
| Kubernetes state adapter | Read-only adapter querying the Kubernetes API for pod status, events, resource usage, and restart history. Namespace-scoped RBAC with no write permissions. | Use the official `kubernetes` Python client with a ServiceAccount that has `get`, `list`, and `watch` permissions on pods, events, and deployments. BlaBlaCar runs a fully containerized architecture on Kubernetes with Istio, and Kubernetes state is a primary signal in every Cleric investigation. [S1] |
| Deployment correlation adapter | Read-only adapter pulling recent deployments, commit history, and feature flag changes from the deployment system (ArgoCD, GitHub Actions, or GitLab CI). | For ArgoCD, use the REST API to list recent syncs. For GitHub Actions, use the GitHub REST API (`/repos/{owner}/{repo}/actions/runs`). AWS DevOps Agent integrates with GitHub Actions and GitLab CI/CD for the same purpose. [S6] |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Root-cause accuracy | Senior SRE blind review of a sample of AI-generated RCAs against the actual root cause identified during incident resolution. Score each RCA as correct, partially correct, or incorrect. | ≥ 70% of RCAs rated "correct" or "partially correct" by reviewing SRE. AWS DevOps Agent reports 94% root-cause accuracy in preview — target 70% as the minimum pilot gate and improve from there. [S6] |
| Actionable rate | Percentage of investigations where the on-call engineer reports at least one actionable insight (correct root cause, useful evidence link, or time-saving context). Measured via engineer feedback. | ≥ 70% actionable rate. Cleric reports 78% at BlaBlaCar for core infrastructure alerts. [S1] |
| Investigation speed | Time from alert ingestion to RCA posting in Slack. Measured end-to-end including all tool calls. | Median investigation time ≤ 5 minutes. Datadog Bits AI SRE completes investigations in 3–4 minutes. [S4] |
| False escalation rate | Percentage of alerts the agent escalates to humans that a senior SRE would have resolved without escalation. Indicates the agent is too conservative. | < 30% false escalation rate during pilot. This threshold should decrease as the knowledge store accumulates. |
| Tool-call safety | Audit every tool call the agent makes during the pilot. Verify that no tool call modifies production state and no tool call accesses data outside its RBAC scope. | Zero production write actions. Zero out-of-scope data access. |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start with a single team's alerting channel in shadow mode: the agent investigates every alert but posts results to a private review channel, not the live alerting channel. The on-call engineer reviews AI RCAs alongside their own investigation. After 3–6 weeks of shadow mode with acceptable accuracy (≥ 70% actionable), switch to live posting. Expand team by team. Cleric followed this exact pattern at BlaBlaCar: Chaos app first, then Database Reliability, then IAM, then Engage — each added after the previous team validated quality. [S1] |
| **Fallback path** | The agent augments the existing on-call process — it does not replace it. If the agent is unavailable, the alert still reaches the on-call engineer through the normal PagerDuty/Opsgenie/incident.io flow. Disable live posting with a feature flag and the process reverts to the pre-AI state with zero disruption. |
| **Observability** | Monitor: investigation latency p50/p95/p99, tool-call error rate, LLM API latency and token usage, investigation queue depth (alert storm detection), engineer feedback scores (7-day rolling average), and knowledge store hit rate (how often past investigations inform current ones). Alert if investigation latency p95 exceeds 10 minutes or if actionable rate drops below 60%. |
| **Operations ownership** | The SRE or platform engineering team owns the agent deployment and tool adapter maintenance. The on-call rotation remains unchanged — the agent is a teammate, not a replacement. Model prompt tuning and confidence threshold calibration should be reviewed monthly during the first quarter, then quarterly. The team that owns the observability stack owns the API adapter reliability. |
