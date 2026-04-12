---
layout: use-case-detail
title: "Implementation Guide — Autonomous Wildfire Detection and Early Warning"
uc_id: "UC-520"
uc_title: "Autonomous Wildfire Detection and Early Warning"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "🔥"
industry: "Emergency Management / Utilities"
complexity: "High"
status: "detailed"
slug: "UC-520-wildfire-detection-early-warning"
permalink: /use-cases/UC-520-wildfire-detection-early-warning/implementation-guide/
---

## Build Goal

Deliver a wildfire detection platform that ingests camera imagery, IoT sensor telemetry, and satellite thermal data, runs AI smoke/heat classifiers, fuses multi-sensor detections into scored alerts, and routes confirmed alerts to fire dispatch (CAD) and utility operations (SCADA). The first production boundary covers camera-based detection with watchstander confirmation for a single utility or fire agency territory. IoT sensor integration and satellite fusion are Phase 2-3 additions. Fire behavior modeling and suppression logistics are out of scope.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.11+ on containerized GPU nodes (NVIDIA T4/A10) | PyTorch and ONNX Runtime are the standard inference runtimes for smoke detection CNNs; GPU required for real-time frame processing across dozens of cameras |
| **Model access** | Custom CNN smoke classifier exported to ONNX, served via Triton Inference Server | Proprietary models trained on domain-specific datasets (smoke vs. cloud/dust/fog). No general-purpose LLM needed for core detection. |
| **Orchestration runtime** | Apache Kafka for event streaming + FastAPI for alert management API | Camera frames arrive as a continuous stream; Kafka handles backpressure across hundreds of stations. FastAPI serves the watchstander console and CAD integration endpoints. |
| **Core connectors** | IRWIN Resources API v9 (REST), CAD vendor API (varies), SCADA OPC-UA or MQTT | IRWIN is the federal standard for wildland fire data exchange. CAD integration is vendor-specific (Hexagon, Tyler/New World, Motorola). |
| **Evaluation / tracing** | MLflow for model versioning + Grafana/Prometheus for operational metrics | Track detection latency, false positive rate, and per-camera health. MLflow manages seasonal model retraining cycles. |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 | Camera ingestion pipeline and baseline smoke classifier running on test stations | Camera frame ingestion service, ONNX smoke classifier, frame storage, detection event schema |
| 2 | Watchstander console and alert management with CAD integration for one jurisdiction | Alert fusion service, watchstander web console, CAD API adapter, confirmed-alert pipeline |
| 3 | IoT sensor ingestion and multi-sensor fusion; satellite thermal overlay | LoRaWAN gateway adapter, sensor event normalization, satellite hotspot ingestor (GOES NGFS), fusion scoring engine |
| 4 | Pilot with one utility or fire agency territory; production hardening | End-to-end monitoring, SLA dashboards, failover testing, model retraining pipeline, operational runbooks |

## Core Contracts

### State And Output Schemas

The detection pipeline produces a `DetectionEvent` for each candidate, which the fusion layer promotes to a `FusedAlert` with triangulated coordinates and composite confidence.

```python
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class SensorModality(str, Enum):
    CAMERA = "camera"
    IOT_GAS = "iot_gas"
    SATELLITE = "satellite"

class DetectionEvent(BaseModel):
    event_id: str
    timestamp: datetime
    modality: SensorModality
    station_id: str
    confidence: float          # 0.0–1.0 from classifier
    bearing_deg: float | None  # camera bearing to smoke
    latitude: float | None     # estimated or station location
    longitude: float | None
    frame_url: str | None      # S3 URL for camera frame

class FusedAlert(BaseModel):
    alert_id: str
    timestamp: datetime
    detection_events: list[str]       # contributing event IDs
    composite_confidence: float       # fused score
    latitude: float
    longitude: float
    heading_deg: float | None         # estimated fire heading
    nearest_infrastructure: str | None
    watchstander_status: str          # pending | confirmed | dismissed
    cam_imagery_urls: list[str]
```

### Tool Interface Pattern

The watchstander console exposes two actions: confirm (routes to CAD/SCADA) and dismiss (feeds back to model training as a labeled false positive).

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.post("/alerts/{alert_id}/confirm")
async def confirm_alert(alert_id: str, operator_notes: str = ""):
    alert = await alert_store.get(alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.watchstander_status = "confirmed"
    await dispatch_to_cad(alert)
    await check_utility_proximity(alert)  # triggers SCADA eval if near infrastructure
    await label_store.save(alert.detection_events, label="true_positive")
    return {"status": "confirmed", "dispatched": True}

@app.post("/alerts/{alert_id}/dismiss")
async def dismiss_alert(alert_id: str, reason: str = "false_positive"):
    alert = await alert_store.get(alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.watchstander_status = "dismissed"
    await label_store.save(alert.detection_events, label="false_positive", reason=reason)
    return {"status": "dismissed"}
```

## Orchestration Outline

The pipeline runs as three continuous stages: ingest, detect, fuse. Camera frames stream through Kafka; the detection engine consumes frames, runs inference, and produces detection events; the fusion service correlates events across stations and modalities within a sliding time window.

```python
# Simplified detection consumer (runs per GPU worker)
import onnxruntime as ort
from kafka import KafkaConsumer, KafkaProducer

session = ort.InferenceSession("smoke_classifier_v3.onnx")
consumer = KafkaConsumer("camera.frames", group_id="detector")
producer = KafkaProducer()

for message in consumer:
    frame = deserialize_frame(message.value)
    # Preprocess: resize, normalize, temporal diff against previous frame
    input_tensor = preprocess(frame, previous_frames[frame.station_id])
    confidence = session.run(None, {"input": input_tensor})[0][0]

    if confidence >= DETECTION_THRESHOLD:  # e.g., 0.65
        event = DetectionEvent(
            modality="camera",
            station_id=frame.station_id,
            confidence=float(confidence),
            bearing_deg=frame.pan_angle,
            frame_url=frame.s3_url,
            # ... remaining fields
        )
        producer.send("detection.events", event.model_dump_json().encode())

    previous_frames[frame.station_id] = frame
```

## Prompt And Guardrail Pattern

This system uses computer vision classifiers rather than LLM prompts for core detection. The guardrail layer is implemented as deterministic rules in the fusion service.

```text
FUSION RULES (deterministic, not prompted):

1. GEOFENCE CHECK: If detection coordinates fall within a registered
   exclusion zone (geothermal, industrial, active prescribed burn),
   suppress alert. Log suppression for audit.

2. CONFIDENCE GATE: Single-camera detections require confidence >= 0.75.
   Multi-camera corroborated detections require composite >= 0.60.

3. TEMPORAL FILTER: Require smoke presence in >= 2 consecutive sweeps
   (120s for 60s cameras) before generating alert. Eliminates transient
   clouds, dust plumes, and lens flare.

4. WATCHSTANDER SLA: Alert must be confirmed or dismissed within 3 min.
   If unacknowledged, escalate to supervisor and secondary watchstander.

5. DISPATCH THROTTLE: Maximum one alert per geographic cell (1km grid)
   per 15-minute window. Prevents duplicate dispatches for the same fire.
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| **CAD system** | REST adapter that translates FusedAlert to vendor-specific incident creation payload (Hexagon CAD, Tyler New World, Motorola PremierOne) | CAD APIs are not standardized. Budget for vendor-specific adapters. Most support XML-based incident import. Test with the target agency's CAD vendor early. |
| **IRWIN** | REST client for IRWIN Resources API v9 to create wildland fire incidents and update status | IRWIN uses OAuth2 authentication with DOI credentials. Requires agency sponsorship for API access. See IRWIN integration specification documentation. |
| **Utility SCADA** | Event bridge that pushes near-infrastructure detections to SCADA via OPC-UA or MQTT | Utility SCADA environments are air-gapped or heavily firewalled. Expect a DMZ relay pattern. Detection events should include distance-to-nearest-asset calculated from GIS asset registry. |
| **Weather data** | Ingest wind speed, humidity, and Red Flag warnings from RAWS stations (MesoWest API) and NWS API | Weather context drives alert prioritization. A detection in 50mph winds with 5% humidity is higher priority than calm conditions. |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| **Smoke detection recall** | Run classifier against labeled test set of known fire and non-fire frames (min 5,000 positive, 50,000 negative). Measure recall and precision. | Recall >= 90%, Precision >= 80% on test set |
| **End-to-end detection latency** | Measure time from frame capture to watchstander alert appearance, sampled across all active stations | P95 latency <= 120 seconds |
| **False positive rate (operational)** | Track dismissed alerts per camera per day over 30-day pilot period | <= 1 false alert per camera per day |
| **Watchstander confirmation time** | Measure time from alert appearance to confirm/dismiss action | P90 <= 3 minutes; P99 <= 5 minutes |
| **CAD delivery reliability** | Confirm that 100% of watchstander-confirmed alerts reach the target CAD system | Zero dropped confirmed alerts over 7-day test window |

## Deployment Notes

| Topic | Guidance |
|-------|---------|
| **Rollout approach** | Start with 5-10 camera stations in one high-risk zone with a single fire agency partner. Run in shadow mode (alerts generated but not dispatched) for 30 days to calibrate false positive rate. Then enable live dispatch integration for that zone. Expand station count and jurisdictions quarterly. |
| **Fallback path** | The system augments existing detection methods (911, lookout towers, aerial patrol). If the AI pipeline goes down, detection reverts to pre-existing manual methods. No degradation to current capability. |
| **Observability** | Per-station dashboards: camera health (uptime, sweep completion), detection latency, inference throughput. System-wide: alert volume, confirmation rate, false positive rate, CAD delivery success rate, model version and drift metrics. |
| **Operations ownership** | Detection platform team owns the AI pipeline, camera health monitoring, and model retraining. Fire agency dispatch owns watchstander staffing and alert confirmation SLA. Utility wildfire team owns SCADA integration and PSPS decision authority. |
