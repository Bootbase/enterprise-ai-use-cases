---
layout: use-case-detail
title: "Implementation Guide — Autonomous Water Network Leak Detection and Non-Revenue Water Reduction"
uc_id: "UC-517"
uc_title: "Autonomous Water Network Leak Detection and Non-Revenue Water Reduction"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Water / Utilities"
complexity: "High"
status: "detailed"
slug: "UC-517-water-network-leak-detection"
permalink: /use-cases/UC-517-water-network-leak-detection/implementation-guide/
---

## Build Goal

Deliver a continuous leak detection system that ingests acoustic and flow sensor data across a utility's distribution network, classifies leaks with >90% accuracy, and generates prioritized repair work orders in the utility's asset management system. The first production release covers DMA-level flow monitoring network-wide plus acoustic sensor deployment in the three highest-loss DMAs. Full network acoustic coverage, satellite integration, and predictive pipe-burst models are deferred to later phases.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.11+ on containerized Linux (Docker / Kubernetes) | Standard for ML inference pipelines; broad library support for audio processing and time-series analysis |
| **Model access** | PyTorch for acoustic classifier; scikit-learn / statsmodels for flow anomaly detection | PyTorch handles the deep-learning acoustic model; lighter libraries fit the statistical flow analysis |
| **Orchestration runtime** | Apache Airflow or Prefect | Manages the periodic batch pipeline (sensor data pull → classify → prioritize → write work order); handles retries and alerting |
| **Core connectors** | OPC UA client (opcua-asyncio), ESRI ArcGIS REST API, IBM Maximo REST API | These are the three integration seams that must work from day one: SCADA, GIS, and asset management |
| **Evaluation / tracing** | MLflow for model tracking; Grafana + Prometheus for operational metrics | MLflow tracks acoustic model versions and accuracy over retraining cycles; Grafana provides real-time dashboards |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 — Foundation (weeks 1–6) | DMA flow ingestion pipeline operational; baseline night-flow profiles established for all DMAs | OPC UA connector to SCADA, time-series store, DMA baseline calculator, sensor health dashboard |
| 2 — Acoustic AI (weeks 7–14) | Acoustic classifier deployed for pilot DMAs; leak alerts surfaced on dashboard | Acoustic model training pipeline, sensor onboarding tooling, alert dashboard with GIS overlay |
| 3 — Prioritization + Work Orders (weeks 15–20) | Leak severity ranking operational; work orders auto-drafted in asset management system | Prioritization engine, Maximo/SAP PM API adapter, operator review workflow |
| 4 — Pilot Validation (weeks 21–26) | Six-month pilot in 3 DMAs validated against field repairs; accuracy and NRW reduction measured | Evaluation report, model retraining with confirmed repair data, go/no-go recommendation for full rollout |

## Core Contracts

### State And Output Schemas

The central data contract is the `LeakEvent` — produced by the detection engine and consumed by the prioritization and work order modules. Keeping this schema strict prevents downstream systems from receiving ambiguous or incomplete leak data.

```python
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class LeakSeverity(str, Enum):
    HIGH = "high"       # estimated > 5 L/s
    MEDIUM = "medium"   # estimated 0.5–5 L/s
    LOW = "low"         # estimated < 0.5 L/s

class DetectionMethod(str, Enum):
    ACOUSTIC = "acoustic"
    FLOW_ANOMALY = "flow_anomaly"
    SATELLITE = "satellite"

class LeakEvent(BaseModel):
    event_id: str = Field(description="Unique leak event identifier")
    detected_at: datetime
    latitude: float
    longitude: float
    accuracy_meters: float = Field(description="Location confidence radius")
    dma_id: str
    pipe_asset_id: str | None = Field(default=None, description="GIS asset ID if resolved")
    severity: LeakSeverity
    estimated_loss_lps: float = Field(description="Estimated loss in liters per second")
    confidence: float = Field(ge=0.0, le=1.0, description="Model confidence score")
    detection_method: DetectionMethod
    acoustic_file_ref: str | None = Field(default=None, description="Object store path to raw audio")
    requires_review: bool = Field(default=True)
```

### Tool Interface Pattern

The work order adapter writes to the asset management system. It is the only component authorized to create external records. The adapter validates the leak event, enriches it with GIS asset data, and posts a draft work order.

```python
import httpx
from leak_detection.schemas import LeakEvent

class MaximoWorkOrderAdapter:
    """Creates draft work orders in IBM Maximo from confirmed leak events."""

    def __init__(self, base_url: str, api_key: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"apikey": api_key, "Content-Type": "application/json"},
        )

    async def create_work_order(self, event: LeakEvent) -> str:
        payload = {
            "description": f"AI-detected leak — {event.severity.value} severity, "
                           f"~{event.estimated_loss_lps:.1f} L/s",
            "location": event.pipe_asset_id or f"{event.latitude},{event.longitude}",
            "wopriority": {"high": 1, "medium": 2, "low": 3}[event.severity.value],
            "status": "WAPPR",  # Waiting for Approval
            "classstructureid": "LEAK_REPAIR",
            "pluspcustomer": event.dma_id,
        }
        resp = await self.client.post("/maximo/api/os/mxwo", json=payload)
        resp.raise_for_status()
        return resp.json()["wonum"]
```

## Orchestration Outline

The detection pipeline runs as a scheduled batch every 15–60 minutes. Each run pulls new sensor data, runs classification, updates the leak event store, and triggers work order creation for newly confirmed leaks. Real-time streaming is a later optimization; batch is sufficient because leak run times are measured in hours, not seconds.

```python
from prefect import flow, task
from leak_detection.ingest import fetch_acoustic_data, fetch_dma_flows
from leak_detection.classify import AcousticClassifier, FlowAnomalyDetector
from leak_detection.prioritize import rank_leaks
from leak_detection.adapters.maximo import MaximoWorkOrderAdapter

@task
def ingest_sensors(since: str) -> tuple[list, list]:
    acoustic = fetch_acoustic_data(since=since)
    flows = fetch_dma_flows(since=since)
    return acoustic, flows

@task
def detect_leaks(acoustic_data, flow_data) -> list:
    acoustic_events = AcousticClassifier().classify_batch(acoustic_data)
    flow_events = FlowAnomalyDetector().detect_batch(flow_data)
    return acoustic_events + flow_events

@task
async def create_work_orders(events, adapter: MaximoWorkOrderAdapter):
    for event in events:
        if event.confidence >= 0.85 and event.severity in ("high", "medium"):
            wo_num = await adapter.create_work_order(event)
            log.info(f"Work order {wo_num} created for {event.event_id}")

@flow(name="leak-detection-cycle")
async def detection_cycle(since: str):
    acoustic, flows = ingest_sensors(since)
    events = detect_leaks(acoustic, flows)
    ranked = rank_leaks(events)
    adapter = MaximoWorkOrderAdapter(base_url=MAXIMO_URL, api_key=MAXIMO_KEY)
    await create_work_orders(ranked, adapter)
```

## Prompt And Guardrail Pattern

The acoustic classifier is a deep-learning model, not an LLM prompt. However, FIDO's architecture uses GPT-4 as a second-stage reasoning layer to interpret ambiguous acoustic signatures and explain classifications to operators. The system prompt constrains the LLM to acoustic interpretation only.

```text
You are a water leak acoustic analyst. You receive a spectrogram summary and
metadata (pipe material, diameter, pressure, ambient noise level) for a sensor
recording from a water distribution network.

Your job:
1. State whether the recording indicates a LEAK, NO_LEAK, or INCONCLUSIVE.
2. If LEAK, estimate severity: HIGH (>5 L/s), MEDIUM (0.5–5 L/s), or LOW (<0.5 L/s).
3. Note any confounding noise sources (pump, traffic, generator) that reduce confidence.
4. If INCONCLUSIVE, recommend a follow-up action (re-record, deploy correlator, manual check).

Rules:
- Never classify a recording as NO_LEAK if the confidence is below 0.7. Use INCONCLUSIVE instead.
- Do not speculate about pipe condition or remaining useful life.
- Output JSON matching the LeakEvent schema.
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| **SCADA / OPC UA** | Async OPC UA subscription client that reads DMA flow and pressure tags at 15-min intervals | Use `opcua-asyncio` library; map SCADA tag names to DMA IDs via a configuration file; handle reconnection on network drops |
| **GIS (ESRI ArcGIS)** | REST adapter that resolves lat/lon to nearest pipe asset ID and renders leak events as a feature layer | Query the ArcGIS Feature Service `/query` endpoint with a spatial filter; cache pipe network geometry locally to reduce API calls |
| **Asset Management (Maximo)** | Work order creation adapter with approval-status webhook listener for dispatch confirmation | Use Maximo OSLC REST API; set initial status to `WAPPR` (Waiting Approval) so operators must explicitly approve before crew dispatch |
| **Sensor fleet management** | Heartbeat monitor that flags sensors with no data in the last 4 hours | Critical for avoiding blind spots; alert the ops team when sensor coverage drops below threshold in any DMA |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| **Acoustic classification accuracy** | Compare AI classifications against field-verified outcomes on a rolling 90-day window | ≥ 90% precision and ≥ 85% recall |
| **Flow anomaly detection rate** | Count true-positive leaks detected by flow analysis that were confirmed by repair crews | ≥ 80% of confirmed leaks in monitored DMAs detected within 48 hours |
| **Work order quality** | Percentage of AI-drafted work orders that proceed to repair without requiring location correction | ≥ 85% location accuracy (dig within 2 meters of predicted point) |
| **False positive rate** | Percentage of dispatched work orders that find no leak at the indicated location | ≤ 10% false dispatch rate |
| **NRW reduction** | Compare DMA minimum night flow before and after pilot deployment | ≥ 15% reduction in pilot DMAs within 6 months |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start with 3 highest-NRW DMAs. Deploy DMA flow meters first (weeks 1–6), then acoustic sensors within those DMAs (weeks 7–14). Expand to next tier of DMAs after pilot validation at week 26. |
| **Fallback path** | If the AI system is unavailable, revert to periodic manual acoustic surveys on the pre-AI schedule. DMA flow meters continue to report through SCADA regardless of AI platform status. |
| **Observability** | Dashboard tracks: sensor fleet health (% reporting), model accuracy (rolling 90-day), NRW by DMA (daily trend), work order throughput (created/approved/completed). Alert on sensor dropout > 4 hours or accuracy drop below 85%. |
| **Operations ownership** | Utility NRW / leakage management team owns the platform. IT/OT team maintains SCADA and sensor network connectivity. Vendor (e.g., FIDO, Siemens) provides model updates and sensor hardware support under SLA. |
