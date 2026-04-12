---
layout: use-case-detail
title: "Implementation Guide — Autonomous Mineral Processing Optimization"
uc_id: "UC-519"
uc_title: "Autonomous Mineral Processing Optimization"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "⛏️"
industry: "Mining & Metals"
complexity: "High"
status: "detailed"
slug: "UC-519-mineral-processing-optimization"
permalink: /use-cases/UC-519-mineral-processing-optimization/implementation-guide/
---

## Build Goal

Deliver an AI advisory system that ingests real-time sensor data from a single concentrator circuit, classifies incoming ore, predicts circuit performance, and recommends set-point adjustments to operators every one to five minutes. The first production release covers comminution and flotation at one concentrator line. Leaching circuits, cross-site model transfer, and fully closed-loop auto-execution are deferred to later phases.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.11+ on an industrial edge appliance (Dell Edge Gateway or HPE Edgeline) | Python ecosystem dominates ML tooling; edge appliance provides the sub-minute inference latency the plant requires |
| **Model access** | XGBoost for tabular process data; PyTorch + torchvision for froth image classification | XGBoost matches the Freeport TROI architecture (ensemble of decision trees with metallurgical feature engineering); CNN needed only for froth cameras |
| **Orchestration runtime** | Apache Airflow (or Prefect) for training pipelines; custom event loop for real-time inference on edge | Training is batch and runs in cloud on a schedule; inference is a tight loop triggered by new sensor readings |
| **Core connectors** | OPC-UA client (opcua-asyncio); PI Web API client for historian reads; OPC-UA write-back for set-points | OPC-UA is the industry standard across DCS vendors; PI Web API provides REST access to years of historical data |
| **Evaluation / tracing** | MLflow for experiment tracking and model registry; Grafana + Prometheus for operational metrics | MLflow tracks model versions and performance across ore types; Grafana gives operators and metallurgists visual confirmation |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 — Data foundation (8–10 weeks) | Historian connected to AI layer; historical dataset validated and labeled | OPC-UA gateway configured; PI Web API adapter; historical data pipeline with ore-type labels from LIMS back-annotation; data quality report |
| 2 — Model development (8–12 weeks) | Ore classifier and circuit predictor trained and validated offline | Feature engineering pipeline; trained XGBoost models for ore classification and recovery/energy prediction; offline validation report showing accuracy against held-out test periods |
| 3 — Advisory pilot (6–8 weeks) | Operators see recommendations on dashboard; system collects accept/reject feedback | Operator dashboard; real-time inference pipeline on edge; recommendation logging; predicted-vs-actual tracking |
| 4 — Validated operation (ongoing) | Recommendation acceptance rate above 70%; first ore-type recipes promoted to auto-execute within validated envelopes | Recipe store; auto-execute framework with envelope guards; model retraining pipeline; drift monitoring |

## Core Contracts

### State And Output Schemas

The central data contract is the inference request — a snapshot of current circuit state — and the recommendation response. These flow between the edge inference service and the operator dashboard.

```python
from pydantic import BaseModel, Field
from datetime import datetime

class CircuitState(BaseModel):
    """Snapshot of current sensor readings across the circuit."""
    timestamp: datetime
    # Comminution
    sag_power_draw_kw: float
    sag_speed_pct: float
    feed_rate_tph: float
    feed_size_p80_mm: float
    cyclone_overflow_p80_um: float
    # Flotation
    rougher_air_flow_m3h: float
    rougher_reagent_dose_gpt: float  # grams per tonne
    froth_depth_mm: float
    # On-line analyzer
    feed_grade_pct: float | None = None  # XRF, may be unavailable
    # Derived
    ore_type_id: int = Field(description="Classified ore type (1-N)")
    ore_type_confidence: float

class Recommendation(BaseModel):
    """Set-point adjustment recommended by the optimizer."""
    timestamp: datetime
    ore_type_id: int
    changes: list[SetPointChange]
    predicted_recovery_pct: float
    predicted_energy_kwh_per_t: float
    predicted_throughput_tph: float
    confidence: float
    within_validated_envelope: bool  # True = eligible for auto-execute

class SetPointChange(BaseModel):
    tag: str            # DCS tag name, e.g. "SAG_SPEED_SP"
    current_value: float
    recommended_value: float
    unit: str
```

### Tool Interface Pattern

The optimizer interacts with the plant exclusively through the OPC-UA write-back adapter. Each write is a single set-point change with a confirmation handshake.

```python
from asyncua import Client as OpcUaClient

class DCSWriteBackAdapter:
    """Writes approved set-points to DCS via OPC-UA with confirmation."""

    def __init__(self, opc_url: str, namespace: int):
        self.opc_url = opc_url
        self.ns = namespace

    async def write_setpoint(self, tag: str, value: float) -> bool:
        async with OpcUaClient(url=self.opc_url) as client:
            node = client.get_node(f"ns={self.ns};s={tag}")
            await node.write_value(value)
            # Read back to confirm DCS accepted the value
            confirmed = await node.read_value()
            return abs(confirmed - value) < 0.01
```

## Orchestration Outline

The real-time inference loop runs on the edge appliance. Every sensor update cycle (1–10 seconds for raw data, aggregated to 1-minute windows for inference), the loop reads current state, runs classification and prediction, and — if the optimizer finds a better operating point — pushes a recommendation to the dashboard.

```python
import asyncio
from historian_client import PIWebAPIClient
from models import OreClassifier, CircuitPredictor, SetPointOptimizer
from dashboard import publish_recommendation

async def inference_loop(
    historian: PIWebAPIClient,
    classifier: OreClassifier,
    predictor: CircuitPredictor,
    optimizer: SetPointOptimizer,
    interval_seconds: int = 60,
):
    while True:
        # 1. Read current circuit state from historian
        readings = await historian.get_current_values(tag_list=CIRCUIT_TAGS)
        state = CircuitState.from_sensor_readings(readings)

        # 2. Classify ore type
        state.ore_type_id, state.ore_type_confidence = classifier.predict(state)

        # 3. Predict performance under current set-points
        current_perf = predictor.predict(state)

        # 4. Search for better set-points within constraints
        recommendation = optimizer.optimize(
            state=state,
            current_performance=current_perf,
            constraints=EQUIPMENT_LIMITS,
        )

        # 5. Publish if improvement exceeds threshold
        if recommendation and recommendation.improvement_pct > MIN_IMPROVEMENT:
            await publish_recommendation(recommendation)

        await asyncio.sleep(interval_seconds)
```

## Prompt And Guardrail Pattern

This system uses structured ML models, not LLMs, for its core prediction and optimization loop. There is no free-text prompt. The guardrails are encoded as hard constraints in the optimizer.

```text
OPTIMIZER CONSTRAINTS (enforced programmatically, not via prompt):
- Every recommended value must fall within the DCS-defined min/max for that tag
- Equipment safety interlocks are mirrored with a 5% margin
  (e.g., if max SAG torque interlock = 1000 kNm, optimizer cap = 950 kNm)
- If ore_type_confidence < 0.7, use conservative default recipe
- If any critical sensor has data older than 5 minutes, hold current set-points
- Maximum single-step change per tag: 10% of operating range
  (prevents large swings that destabilize the circuit)
- All constraints are loaded from a versioned config file, not hard-coded
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| OPC-UA sensor ingestion | Async OPC-UA subscription client that buffers readings into 1-minute aggregation windows | Use opcua-asyncio library; subscribe to change notifications rather than polling to reduce network load; tag mapping stored in config |
| Historian back-fill | Batch pipeline to extract 2–3 years of historical process data from PI for model training | Use PI Web API interpolated queries at 1-minute intervals; align timestamps across tags; handle gaps from shutdowns |
| Froth camera integration | Edge-deployed CNN that classifies froth images and outputs bubble-size distribution and froth stability score | Camera vendors (Metso VisioFroth, Outotec) provide RTSP streams; inference at 1 fps is sufficient; output feeds into CircuitState |
| LIMS assay feedback | Scheduled pull of lab assay results (every 2–4 hours) to annotate historian data with ground-truth recovery and grade | Used solely for model retraining and prediction monitoring; not in the real-time path |
| Mine plan ingestion | Weekly file import of the ore-block schedule (CSV or XML from mine planning software) | Lets the AI anticipate ore type changes 4–8 hours ahead of arrival at the crusher |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Ore classification accuracy | Compare classifier output against LIMS-confirmed ore types over 30-day test period | ≥ 90% agreement with retrospective LIMS labels |
| Recovery prediction accuracy | Mean absolute error of predicted vs. actual recovery (from LIMS) across all ore types | MAE ≤ 0.5 percentage points for primary ore types |
| Recommendation quality | Predicted-vs-actual improvement when operators accept recommendations; measured over 60-day pilot | Actual improvement ≥ 70% of predicted improvement on average |
| Set-point safety | Zero write-back events that violate equipment constraints or trigger DCS interlocks | Zero violations over entire pilot period |
| Operator acceptance rate | Percentage of recommendations operators approve, tracked by shift and ore type | ≥ 50% acceptance rate within first 30 days; ≥ 70% by end of pilot |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start with one concentrator line at one mine site; run in shadow mode (recommendations logged but not displayed) for 2 weeks to validate predictions; then enable the operator dashboard; auto-execute only after 3+ months of stable advisory operation |
| **Fallback path** | Operators can disable AI recommendations from the dashboard at any time; DCS continues to run on existing manual set-points; all interlocks remain independent of the AI layer |
| **Observability** | Track predicted-vs-actual recovery per shift, recommendation acceptance rate, model confidence trends, and data freshness per sensor tag; alert on prediction error sustained above threshold for more than one shift |
| **Operations ownership** | Processing plant team owns day-to-day operation and recommendation approval; data science team (central or embedded) owns model retraining, drift monitoring, and recipe promotion; DCS vendor retains interlock responsibility |
