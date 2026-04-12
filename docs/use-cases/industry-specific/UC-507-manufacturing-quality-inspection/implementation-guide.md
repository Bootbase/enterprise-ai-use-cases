---
layout: use-case-detail
title: "Implementation Guide — Autonomous Manufacturing Quality Inspection and Defect Remediation with Agentic AI Vision"
uc_id: "UC-507"
uc_title: "Autonomous Manufacturing Quality Inspection and Defect Remediation with Agentic AI Vision"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Manufacturing"
complexity: "High"
status: "detailed"
slug: "UC-507-manufacturing-quality-inspection"
permalink: /use-cases/UC-507-manufacturing-quality-inspection/implementation-guide/
---

## Build Goal

A delivery team is building an edge-deployed visual inspection system for a single production line that detects and classifies surface defects at line speed, writes disposition results to MES, and provides a human review interface for borderline cases. The first production release covers supervised defect detection for the top 10–15 known defect classes, with anomaly detection in shadow mode. Root cause correlation and closed-loop process correction are Phase 2 deliverables. Full multi-line rollout and model self-retraining are outside the first release.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Edge runtime** | NVIDIA Jetson AGX Orin (275 TOPS, 60W) running JetPack 6.x with TensorRT | Handles YOLOv8 at 75+ FPS at INT8. Industrial-grade temperature range. 2M+ developer ecosystem with strong model zoo support. [S7] |
| **Model framework** | Ultralytics YOLOv8 (detection) + PyTorch autoencoder (anomaly), exported to TensorRT or OpenVINO IR | YOLOv8 provides state-of-the-art detection accuracy with efficient INT8 inference. OpenVINO is proven at BMW for AIQX. [S1] |
| **Orchestration** | Python 3.11+ microservices with MQTT (Eclipse Mosquitto) event bus | Sub-200ms pipeline latency requirement rules out HTTP-based orchestration. MQTT is standard in industrial IoT and handles pub/sub routing between agents efficiently. |
| **Image acquisition** | GigE Vision or Camera Link cameras with Aravis or Vimba SDK | GigE Vision is the dominant industrial camera protocol. Aravis is open-source and supports hardware triggering synchronized with PLC. |
| **Observability** | Prometheus client on edge; Grafana dashboards; MinIO for image storage | Tracks inference latency, confidence distributions, throughput, and drift metrics. MinIO stores inspection images locally with cloud sync for retraining. |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 — Station setup (weeks 1–4) | Camera, lighting, and edge hardware installed on one inspection station. Image capture pipeline validated at production speed. | Camera mount and lighting rig. GigE Vision capture service. PLC trigger integration. Baseline image dataset (5,000+ images per defect class). |
| 2 — Detection model (weeks 5–10) | Supervised defect detection model trained, optimized, and deployed to edge. Shadow mode: runs alongside human inspection without gating the line. | Labeled training dataset. YOLOv8 model trained and exported to TensorRT. Inference service on Jetson. Shadow mode comparison dashboard. |
| 3 — MES integration and human review (weeks 11–14) | Inspection results written to MES. Borderline cases routed to quality engineer dashboard. Anomaly detection model running in shadow mode. | OPC-UA adapter for MES writeback. Human review web app. Autoencoder anomaly model in shadow mode. Audit trail storage. |
| 4 — Pilot production (weeks 15–20) | System gating the line for the top defect classes. Human review for borderline cases. Metrics validated against pilot gates before full rollout. | Production cutover runbook. Fallback procedure to manual inspection. Pilot KPI dashboard. Go/no-go evaluation report. |

## Core Contracts

### State And Output Schemas

The inspection result is the core data contract between the detection agent, classification logic, MES, and human review queue. Every inspection produces exactly one result per part.

```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class Severity(str, Enum):
    COSMETIC = "cosmetic"
    FUNCTIONAL = "functional"
    SAFETY_CRITICAL = "safety_critical"

class Disposition(str, Enum):
    PASS = "pass"
    REWORK = "rework"
    SCRAP = "scrap"
    HUMAN_REVIEW = "human_review"

class DetectedDefect(BaseModel):
    defect_class: str = Field(description="Defect type from trained taxonomy")
    confidence: float = Field(ge=0.0, le=1.0)
    severity: Severity
    bbox: tuple[float, float, float, float] = Field(description="x1, y1, x2, y2 normalized")
    anomaly_score: float | None = Field(default=None, description="Unsupervised anomaly score if available")

class InspectionResult(BaseModel):
    part_id: str = Field(description="Unique part serial from MES/barcode")
    production_order: str
    station_id: str
    timestamp: datetime
    model_version: str
    defects: list[DetectedDefect]
    disposition: Disposition
    image_uri: str = Field(description="S3/MinIO path to captured image")
    inference_latency_ms: float
```

### Tool Interface Pattern

Each agent is a lightweight Python service that subscribes to MQTT topics and publishes results. The detection agent exposes a single inference endpoint called on every camera trigger.

```python
import paho.mqtt.client as mqtt
from ultralytics import YOLO

class DefectDetectionAgent:
    def __init__(self, model_path: str, mqtt_broker: str):
        self.model = YOLO(model_path, task="detect")
        self.client = mqtt.Client()
        self.client.connect(mqtt_broker)
        self.client.subscribe("inspection/trigger")
        self.client.on_message = self._on_trigger

    def _on_trigger(self, client, userdata, msg):
        """Called on PLC trigger. Captures frame, runs inference, publishes result."""
        frame = self._capture_frame()
        results = self.model.predict(frame, imgsz=640, conf=0.25, device=0)
        detections = self._parse_results(results)
        # Publish to downstream agents via MQTT
        client.publish("inspection/detections", detections.model_dump_json())

    def _capture_frame(self):
        # GigE Vision capture via Aravis SDK
        ...

    def _parse_results(self, results) -> InspectionResult:
        # Map YOLO detections to InspectionResult schema
        ...
```

## Orchestration Outline

The pipeline is event-driven. A PLC trigger fires when a part reaches the inspection station. The camera captures a frame, the detection agent runs inference, and results flow through MQTT topics to downstream agents. The entire pipeline must complete within 200ms to avoid buffering at line speed.

```python
# Simplified orchestration — each agent subscribes to its input topic
# and publishes to its output topic. No central orchestrator needed.

TOPIC_MAP = {
    "inspection/trigger":     "Camera capture + detection agent",
    "inspection/detections":  "Confidence router",
    "inspection/classify":    "Classification agent (high-confidence defects)",
    "inspection/review":      "Human review queue (borderline cases)",
    "inspection/disposition":  "MES writeback agent",
    "inspection/rootcause":   "Root cause correlation agent (Phase 2)",
}

# Confidence router logic (runs inside detection agent post-processing)
def route_by_confidence(result: InspectionResult) -> str:
    if not result.defects:
        return "inspection/disposition"  # PASS directly to MES
    max_conf = max(d.confidence for d in result.defects)
    if max_conf >= 0.95:
        return "inspection/classify"     # High-confidence defect
    elif max_conf >= 0.70:
        return "inspection/review"       # Borderline — human review
    else:
        return "inspection/review"       # Low confidence — human review
```

## Prompt And Guardrail Pattern

This use case is primarily computer vision, not language-model-based. The "prompt" equivalent is the model's training configuration and post-processing rules. Guardrails are enforced through deterministic logic, not prompt engineering.

```text
DETECTION GUARDRAILS:
- Confidence threshold for auto-disposition: 0.95 (tunable per defect class)
- Anomaly score threshold for unknown defect escalation: configurable per station
- Maximum false positive rate target: < 2% (measured weekly, triggers retraining if exceeded)
- All safety-critical defect classes require confidence >= 0.98 for auto-scrap
- Parts with ANY anomaly score above threshold route to human review regardless
  of supervised detection confidence

DISPOSITION RULES (deterministic, not AI):
- safety_critical + confidence >= 0.98 → SCRAP
- safety_critical + confidence < 0.98 → HUMAN_REVIEW
- functional + confidence >= 0.95 → REWORK
- cosmetic + confidence >= 0.95 → PASS (with quality note)
- Any detection with confidence 0.70–0.95 → HUMAN_REVIEW
```

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| MES writeback (OPC-UA) | OPC-UA client that writes InspectionResult to MES node for each part. Reads production order and part serial at station entry. | Use python-opcua or asyncua library. Map InspectionResult fields to MES-specific node IDs. Test with MES vendor's OPC-UA simulator before production. Most MES platforms (SAP ME, Opcenter, Plex) support OPC-UA natively. [S12] |
| PLC trigger synchronization | GigE Vision hardware trigger wired to PLC digital output. Camera capture service listens for trigger signal. | Trigger timing must account for part travel speed and camera exposure. Calibrate trigger offset per station during Phase 1. Use PLC rising-edge detection for deterministic timing. |
| Human review dashboard | Web application displaying borderline inspection images with model overlay, confidence scores, and one-click disposition buttons. | Serve from edge node or local server. Quality engineers need sub-second page loads. Store human decisions as training labels for model improvement. Build with simple stack (FastAPI + HTMX or React). |
| Image and result storage | MQTT-to-MinIO pipeline on edge. Nightly sync to cloud storage for retraining dataset. | Retain all images for at least 90 days (IATF 16949 traceability). Compress with WebP or AVIF for storage efficiency. Tag with part_id, production_order, disposition, model_version. [S11] |
| Model retraining pipeline | Cloud-based pipeline triggered on schedule or drift detection. Pulls new labeled data from cloud storage, retrains, validates, and pushes updated TensorRT model to edge. | Use Siemens pattern: train in cloud, deploy to edge. Validation gate: new model must match or exceed current model on holdout set before deployment. Blue-green model deployment on edge to avoid downtime. [S6] |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| Detection accuracy (per defect class) | Holdout test set of 500+ labeled images per class. Measure mAP@0.5 and per-class recall/precision. | mAP@0.5 >= 0.90; per-class recall >= 0.95 for safety-critical defects; precision >= 0.98 (false positive rate < 2%). |
| Inference latency | Measure end-to-end time from camera trigger to MQTT publish on production hardware under production lighting. P99 latency. | P99 < 200ms for detection; P99 < 50ms for classification. |
| Anomaly detection (shadow mode) | Inject known-defective parts not in training set. Measure anomaly score distribution separation between good and novel-defect parts. | AUROC >= 0.85 on novel defect detection during shadow mode. |
| MES writeback reliability | Count successful vs. failed MES writes over 1-week pilot. Measure write latency. | 99.9% write success rate; P99 write latency < 500ms. |
| Human review queue throughput | Measure queue depth and average time-to-review during pilot. Target: quality engineer can process borderline cases without becoming a bottleneck. | Queue depth < 50 parts at any time; average review time < 15 seconds per part. |
| Escaped defect rate | Track customer-reported defects for parts that passed AI inspection during pilot vs. historical baseline. | Escaped defect rate lower than historical sampling-based inspection baseline. |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start with one inspection station on one line. Run 2–4 weeks in shadow mode (AI inspects but does not gate the line; human inspection continues in parallel). Compare AI vs. human decisions to validate accuracy. Switch to AI-gated mode only after pilot gates are met. Expand station-by-station. BMW took this approach across 30 plants. [S1] |
| **Fallback path** | Every station has a physical bypass switch. If the edge node fails or inference latency exceeds threshold, the line automatically reverts to manual inspection or rule-based machine vision (Cognex/Keyence). Fallback must activate within 30 seconds. IATF 16949 requires documented backup inspection methods. [S11] |
| **Observability** | Dashboard tracks: inference latency (P50/P99), confidence score distributions, false positive rate, anomaly score trends, edge node health (GPU temp, memory), MES write success rate. Alert on: latency spike, confidence distribution shift (model drift), edge node offline, MES write failures. |
| **Operations ownership** | Quality engineering owns defect taxonomy, disposition rules, and model accuracy targets. Manufacturing engineering owns camera/lighting hardware, PLC integration, and line-side support. Data/ML engineering owns model training pipeline, drift detection, and edge deployment. IT/OT owns network, MES integration, and security. |
