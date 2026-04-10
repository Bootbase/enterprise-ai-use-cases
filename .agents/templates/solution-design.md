---
layout: use-case-detail
title: "{Detail Title} — {UC Title}"
uc_id: "UC-{NNN}"
uc_title: "{UC Title}"
detail_type: "solution-design"
detail_title: "Solution Design"
category: "{Category}"
category_icon: "{icon}"
industry: "{Industry or Cross-Industry}"
complexity: "Low / Medium / High"
status: "detailed"
slug: "UC-{NNN}-{slug}"
permalink: /use-cases/UC-{NNN}-{slug}/solution-design/
---

## What This Design Covers

{One short paragraph. State the business problem, the recommended AI operating model, and the boundary of the design.}

## Recommended Operating Model

| Decision Area | Recommendation |
|---------------|----------------|
| **Autonomy Model** | {How autonomous the workflow should be} |
| **System of Record** | {Which incumbent system remains authoritative} |
| **Human Decision Points** | {Where humans approve, review, or override} |
| **Primary Value Driver** | {What creates the economics} |

## Architecture

### System Diagram

```mermaid
{Mermaid or ASCII diagram showing the main components and data flow}
```

### Component Responsibilities

| Component | Role | Notes |
|-----------|------|-------|
| {Component 1} | {Responsibility} | {Why it exists} |
| {Component 2} | {Responsibility} | {Why it exists} |
| {Component 3} | {Responsibility} | {Why it exists} |
| {Component 4} | {Responsibility} | {Why it exists} |

## End-to-End Flow

| Step | What Happens | Owner |
|------|---------------|-------|
| 1 | {Trigger and intake} | {System or role} |
| 2 | {AI analysis or extraction} | {System or role} |
| 3 | {Deterministic validation or decisioning} | {System or role} |
| 4 | {Writeback, action, or escalation} | {System or role} |
| 5 | {Audit or follow-up} | {System or role} |

## AI Responsibilities and Boundaries

| Workflow Area | AI Does | Deterministic System Does | Human Owns |
|---------------|---------|---------------------------|------------|
| {Area 1} | {AI task} | {System task} | {Human decision} |
| {Area 2} | {AI task} | {System task} | {Human decision} |
| {Area 3} | {AI task} | {System task} | {Human decision} |

## Integration Seams

| System | Integration Method | Why It Matters |
|--------|--------------------|----------------|
| {Core system 1} | {API / event / file / SDK} | {Business reason} |
| {Core system 2} | {API / event / file / SDK} | {Business reason} |
| {Core system 3} | {API / event / file / SDK} | {Business reason} |

## Control Model

| Risk | Control |
|------|---------|
| {Hallucination or extraction risk} | {Schema, retrieval, validation, or threshold} |
| {Operational or compliance risk} | {Approval gate, logging, segregation, or fallback} |
| {Data or security risk} | {Isolation, redaction, scoped tools, or policy} |

## Reference Technology Stack

| Layer | Default Choice | Reason | Viable Alternative |
|-------|----------------|--------|--------------------|
| **Model layer** | {Primary choice} | {Why} | {Alternative} |
| **Orchestration** | {Primary choice} | {Why} | {Alternative} |
| **Retrieval / memory** | {Primary choice} | {Why} | {Alternative} |
| **Observability** | {Primary choice} | {Why} | {Alternative} |

## Key Design Decisions

| Decision | Choice | Why It Fits This Use Case |
|----------|--------|---------------------------|
| {Decision 1} | {Choice} | {Reasoning} |
| {Decision 2} | {Choice} | {Reasoning} |
| {Decision 3} | {Choice} | {Reasoning} |
