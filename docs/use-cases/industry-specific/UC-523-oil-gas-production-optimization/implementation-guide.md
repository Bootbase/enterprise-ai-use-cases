---
layout: use-case-detail
title: "Implementation Guide — Autonomous Upstream Oil & Gas Production Optimization"
uc_id: "UC-523"
uc_title: "Autonomous Upstream Oil & Gas Production Optimization"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "🏭"
industry: "Oil & Gas"
complexity: "High"
status: "detailed"
slug: "UC-523-oil-gas-production-optimization"
permalink: /use-cases/UC-523-oil-gas-production-optimization/implementation-guide/
---

## Build Goal

Deliver an AI-driven production optimization system that ingests real-time well sensor data, generates lift setpoint recommendations using hybrid physics-ML models, and writes approved changes back to SCADA. The first production boundary covers gas-lift optimization on a single field (50-200 wells) in advisory mode, with a path to closed-loop control after a 90-day validation period. ESP optimization, predictive equipment health, and multi-field rollout remain outside the first release.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.11+ on Kubernetes (EKS or AKS) | Dominant language for petroleum engineering ML; cloud-managed K8s simplifies scaling across fields |
| **Model access** | Custom hybrid models (PyTorch for neural components, scipy for physics solvers); no LLM dependency | Lift optimization requires sub-second numerical inference, not generative AI; physics priors are non-negotiable |
| **Orchestration runtime** | Apache Kafka for event streaming; custom Python orchestrator with OR-Tools constraint solver | Must handle 10,000+ sensor events/second and enforce field-level physical constraints (gas capacity, manifold pressure) |
| **Core connectors** | OPC-UA client (opcua-asyncio); AVEVA PI Web API client; SAP PM REST adapter | These are the three systems every action touches: SCADA for control, PI for history, SAP for maintenance |
| **Evaluation / tracing** | MLflow for model versioning and experiment tracking; Grafana + Prometheus for operational metrics | Need to track predicted-vs-actual production per well per model version; standard O&G operations teams know Grafana |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 — Data Foundation (8 weeks) | Streaming pipeline from SCADA to feature store; historical backfill from PI | OPC-UA ingest service, Kafka topics, feature store schema, well state API, data quality monitors |
| 2 — Model Development (10 weeks) | Trained gas-lift optimization models for pilot field; baseline production benchmarks | Hybrid physics-ML model per well, training pipeline, backtesting harness, model registry in MLflow |
| 3 — Advisory Deployment (8 weeks) | Engineers receive real-time lift recommendations on dashboard; no autonomous control | Engineer dashboard, recommendation API, alert routing, audit logging, SCADA read-only integration |
| 4 — Closed-Loop Pilot (12 weeks) | Autonomous setpoint adjustments on 20-50 wells with engineer override; production uplift measured | SCADA write-back service, operating envelope enforcement, safety interlock validation, A/B test framework |

## Core Contracts

### State And Output Schemas

Each well's state is updated every 1-5 minutes from SCADA sensors. The optimization service consumes well state and returns a setpoint recommendation with predicted production impact.

```python
from pydantic import BaseModel, Field
from datetime import datetime

class WellState(BaseModel):
    well_id: str
    timestamp: datetime
    tubing_pressure_psi: float
    casing_pressure_psi: float
    flow_rate_bopd: float
    gas_injection_rate_mscfd: float
    watercut_pct: float
    esp_frequency_hz: float | None = None  # None for gas-lift wells
    downhole_temperature_f: float
    choke_position_pct: float

class SetpointRecommendation(BaseModel):
    well_id: str
    timestamp: datetime
    recommended_gas_rate_mscfd: float = Field(ge=0)
    predicted_oil_rate_bopd: float
    predicted_uplift_bopd: float
    confidence: float = Field(ge=0.0, le=1.0)
    model_version: str
    requires_approval: bool  # True if outside operating envelope
    envelope_violation: str | None = None
```

### Tool Interface Pattern

The orchestrator exposes controlled actions to the optimization loop. Each tool validates against the well's operating envelope before execution.

```python
class ScadaWriteBack:
    """Writes setpoint commands to SCADA via OPC-UA.
    Enforces operating envelope and logs all actions."""

    def __init__(self, opcua_client, envelope_store, audit_log):
        self.client = opcua_client
        self.envelopes = envelope_store
        self.log = audit_log

    async def adjust_gas_lift(
        self, well_id: str, target_rate_mscfd: float, recommendation: SetpointRecommendation
    ) -> dict:
        envelope = self.envelopes.get(well_id)
        if not envelope.contains(gas_rate=target_rate_mscfd):
            self.log.record(well_id, "BLOCKED", "outside_envelope", recommendation)
            return {"status": "blocked", "reason": "envelope_violation"}

        node_id = f"ns=2;s={well_id}.GasLift.Setpoint"
        await self.client.write_value(node_id, target_rate_mscfd)
        self.log.record(well_id, "EXECUTED", "gas_lift_adjust", recommendation)
        return {"status": "executed", "new_setpoint": target_rate_mscfd}
```

## Orchestration Outline

The optimization loop runs per field on a configurable cycle (default: every 5 minutes). It fetches current well states, runs inference, applies field constraints, and dispatches actions.

```python
async def optimization_cycle(field_id: str, config: FieldConfig):
    # 1. Fetch current state for all wells in field
    well_states = await feature_store.get_field_state(field_id)

    # 2. Run per-well lift optimization models
    recommendations = []
    for state in well_states:
        model = model_registry.get_model(state.well_id, state.lift_type)
        rec = model.predict_optimal_setpoint(state)
        recommendations.append(rec)

    # 3. Apply field-level constraints (shared gas capacity, quotas)
    constrained = field_constraint_solver.solve(
        recommendations=recommendations,
        gas_capacity_mscfd=config.total_gas_capacity,
        max_wells_adjusted_per_cycle=config.max_adjustments,
    )

    # 4. Dispatch: autonomous for in-envelope, alert for out-of-envelope
    for rec in constrained:
        if rec.requires_approval:
            await alert_service.send_to_engineer(rec)
        else:
            await scada_writeback.adjust_gas_lift(
                rec.well_id, rec.recommended_gas_rate_mscfd, rec
            )

    # 5. Log cycle results for audit and model monitoring
    await audit_log.record_cycle(field_id, constrained)
```

## Prompt And Guardrail Pattern

This system does not use LLM-based prompts. The AI components are numerical optimization models (hybrid physics-ML) that produce structured setpoint recommendations. Guardrails are enforced through operating envelopes and deterministic constraint solvers.

```text
OPERATING ENVELOPE (per well, set by production engineer):
- Gas injection rate: [min_mscfd, max_mscfd]
- Tubing pressure: [min_psi, max_psi]
- Casing pressure: [min_psi, max_psi]
- Maximum rate change per cycle: delta_max_mscfd

FIELD CONSTRAINTS (set by field operations manager):
- Total gas-lift compressor capacity: total_mscfd
- Maximum simultaneous well adjustments per cycle: N
- Regulatory production quota: max_field_bopd

ESCALATION RULES:
- Recommendation outside envelope → route to engineer dashboard
- Equipment health score below threshold → create maintenance alert
- Predicted-vs-actual error > 10% for 4 consecutive cycles → hold actions, flag model for review
- Sensor data quality flag on any input → skip well this cycle
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| **SCADA / OPC-UA** | Bidirectional OPC-UA client: subscribe to sensor nodes for reads; write setpoint nodes for control | Use opcua-asyncio library; write-back requires SCADA vendor coordination to whitelist the optimization system as a control client; test on simulation server before live SCADA |
| **AVEVA PI System** | REST client against PI Web API for historical backfill and contextual lookups (decline curves, past interventions) | PI Web API returns JSON; paginate large queries (>100K points); use PI Asset Framework hierarchy to map wells to fields |
| **SAP PM / Maximo** | REST adapter to create maintenance work orders when equipment health models flag predicted failures | Map AI severity scores to SAP priority codes; include predicted failure window and recommended action in work order description |
| **OSDU / PRODML** | OSDU REST API client for well master data (completions, lift type, operating history) | OSDU adoption varies by operator; build adapter with fallback to direct PI or file-based well master import for operators not yet on OSDU |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| **Lift optimization accuracy** | Compare AI-recommended gas rate vs. engineer-selected rate on 50+ wells over 30 days; measure predicted-vs-actual oil rate (MAPE) | MAPE < 5% on predicted oil rate; AI recommendations match or beat engineer decisions on >80% of wells |
| **Equipment health detection** | Inject 20+ known historical failure patterns into test data; measure precision and recall of anomaly detection | Precision > 85%, recall > 90% for critical failure modes (ESP burnout, gas-lift valve stuck) |
| **Setpoint safety** | Fuzz test with out-of-range sensor values and extreme recommendations; verify envelope enforcement and SCADA interlock behavior | Zero commands issued outside operating envelope; zero safety interlock bypasses |
| **Field constraint compliance** | Run optimization cycle with constrained gas capacity (50% of normal); verify total allocated gas does not exceed limit | Total gas allocation within 1% of capacity limit across all test scenarios |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start with one field (50-200 wells) in advisory mode for 90 days; graduate to closed-loop on wells where AI recommendations consistently outperform or match engineer decisions; expand field-by-field using transfer learning from initial models |
| **Fallback path** | Disable SCADA write-back at any time; wells revert to last human-set setpoints; advisory mode continues independently of control path; no dependency on AI for safe well operation |
| **Observability** | Track per-well: predicted vs. actual oil rate, gas-lift efficiency (bbl/Mscf), equipment health score trend; track per-field: total production uplift vs. baseline, gas-lift consumption reduction, number of autonomous vs. manual adjustments; alert on model drift (MAPE > 8% sustained for 24 hours) |
| **Operations ownership** | Production engineering team owns the optimization system in production; data engineering team owns the ingest pipeline and feature store; ML engineering team owns model retraining and deployment; field operations retains authority over SCADA infrastructure and safety interlocks |
