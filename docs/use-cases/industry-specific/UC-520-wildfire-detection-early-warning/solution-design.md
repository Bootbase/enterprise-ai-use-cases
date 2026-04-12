---
layout: use-case-detail
title: "Solution Design — Autonomous Wildfire Detection and Early Warning"
uc_id: "UC-520"
uc_title: "Autonomous Wildfire Detection and Early Warning"
detail_type: "solution-design"
detail_title: "Solution Design"
category: "Industry-Specific"
category_icon: "🔥"
industry: "Emergency Management / Utilities"
complexity: "High"
status: "detailed"
slug: "UC-520-wildfire-detection-early-warning"
permalink: /use-cases/UC-520-wildfire-detection-early-warning/solution-design/
---

## What This Design Covers

A multi-modal wildfire detection system that fuses ground-based camera networks, IoT gas sensors, and satellite imagery through AI models to detect wildland fire ignitions within minutes. The design covers the operating model from sensor ingestion through alert validation to dispatch integration, with emphasis on where AI decides, where deterministic systems enforce, and where human operators retain authority. It does not cover fire behavior prediction, suppression logistics, or post-fire assessment.

## Recommended Operating Model

| Decision Area | Recommendation |
|---------------|----------------|
| **Autonomy Model** | AI-assisted detection with human-in-the-loop confirmation. AI generates candidate alerts with location and confidence score; trained watchstanders confirm before dispatch notification. |
| **System of Record** | IRWIN (Integrated Reporting of Wildland Fire Information) for incident data; utility SCADA for grid state. The detection platform is an alerting layer, not a system of record. |
| **Human Decision Points** | Alert confirmation (watchstander), dispatch commitment (dispatch center), Public Safety Power Shutoff authorization (utility operations) |
| **Primary Value Driver** | Reducing detection-to-dispatch latency from 30-60 minutes to under 10 minutes, enabling suppression while fires are under 1 acre |

## Architecture

### System Diagram

```
                      ┌─────────────────────────────┐
                      │     Satellite Imagery        │
                      │  (GOES / FireSat / VIIRS)    │
                      └──────────┬──────────────────┘
                                 │
┌──────────────────┐   ┌────────▼────────┐   ┌──────────────────┐
│  Camera Network  │──▸│  Ingestion &    │◂──│  IoT Gas Sensors │
│  (PTZ + NIR)     │   │  Normalization  │   │  (LoRaWAN mesh)  │
└──────────────────┘   └────────┬────────┘   └──────────────────┘
                                │
                       ┌────────▼────────┐
                       │  AI Detection   │
                       │  Engine         │
                       │  (smoke/heat    │
                       │   classifiers)  │
                       └────────┬────────┘
                                │
                       ┌────────▼────────┐
                       │  Alert Fusion   │
                       │  & Scoring      │
                       │  (multi-sensor  │
                       │   correlation)  │
                       └────────┬────────┘
                                │
                       ┌────────▼────────┐
                       │  Watchstander   │
                       │  Console        │
                       │  (confirm /     │
                       │   dismiss)      │
                       └───┬─────────┬───┘
                           │         │
              ┌────────────▼──┐  ┌───▼──────────────┐
              │  CAD / IRWIN  │  │  Utility SCADA   │
              │  (dispatch)   │  │  (PSPS triggers) │
              └───────────────┘  └──────────────────┘
```

### Component Responsibilities

| Component | Role | Notes |
|-----------|------|-------|
| **Camera network** | Captures 360-degree HD + near-infrared imagery on 60-120 second sweep cycles | Pano AI stations sweep every 60s; ALERTCalifornia every 2 min. Range: 10-60 miles depending on conditions. |
| **IoT sensor mesh** | Detects combustion gases (H2, CO) and particulates in dense canopy where cameras lack line-of-sight | Dryad Silvanet uses LoRaWAN mesh with solar-powered nodes. Supplements cameras, does not replace them. |
| **Satellite imagery processor** | Provides broad-area thermal anomaly detection from geostationary (GOES, 5-min revisit) and LEO (FireSat, 20-min target) sources | Useful for remote areas without camera coverage. Lower spatial resolution than cameras. |
| **AI detection engine** | Runs smoke/flame classifiers on camera frames and sensor telemetry; produces candidate detections with confidence scores | Deep learning models (CNN-based, trained on 1B+ images at Pano AI). Temporal differencing reduces false positives from clouds, dust, steam. |
| **Alert fusion and scoring** | Correlates detections across modalities, triangulates location from multiple camera bearings, assigns composite confidence | Multi-sensor correlation raises alert confidence and reduces false positive rate below any single-sensor threshold. |
| **Watchstander console** | Human operator reviews AI-generated alerts with camera imagery, confirms or dismisses, adds context for dispatch | Critical for maintaining trust with fire agencies. Pano AI reports 90%+ accuracy including human verification. |

## End-to-End Flow

| Step | What Happens | Owner |
|------|--------------|-------|
| 1 | Camera completes 360-degree sweep; frames ingested into detection pipeline. IoT sensors stream gas readings. Satellite processor checks latest thermal scan. | Sensor infrastructure |
| 2 | AI classifiers score each frame/reading for smoke, flame, or thermal anomaly. Candidate detections above threshold enter fusion layer. | AI detection engine |
| 3 | Fusion layer correlates candidates across sensors and camera bearings. Triangulates geographic coordinates. Assigns composite confidence score and estimated fire heading. | Alert fusion service |
| 4 | Watchstander receives alert with camera imagery, map pin, confidence score, and weather context. Confirms fire or dismisses as false positive (cloud, dust, prescribed burn). | Trained watchstander |
| 5 | Confirmed alert dispatched to CAD system and/or IRWIN. For utility zones, alert also routes to SCADA operations for PSPS evaluation. | CAD / dispatch center / utility ops |

## AI Responsibilities and Boundaries

| Workflow Area | AI Does | Deterministic System Does | Human Owns |
|---------------|---------|---------------------------|------------|
| **Smoke detection** | Classify camera frames for smoke presence, assign confidence, estimate bearing | Enforce minimum confidence threshold before alerting watchstander | Confirm or dismiss alert after visual review |
| **Multi-sensor fusion** | Correlate camera, sensor, and satellite detections; triangulate coordinates | Apply geofencing rules (exclude known industrial sites, geothermal vents, prescribed burn zones) | Override geofence exclusions during unexpected conditions |
| **Alert routing** | Recommend dispatch priority based on proximity to structures, wind speed, fuel type | Route to correct CAD jurisdiction based on geographic coordinates | Authorize resource commitment and dispatch level |
| **Utility grid integration** | Flag detections near transmission/distribution infrastructure | Trigger PSPS evaluation workflow in SCADA | Authorize de-energization decisions |

## Integration Seams

| System | Integration Method | Why It Matters |
|--------|--------------------|----------------|
| **Computer-Aided Dispatch (CAD)** | API push of confirmed alerts with coordinates, confidence, imagery URL | Fire agencies will not adopt a detection system that requires a separate console outside their existing dispatch workflow |
| **IRWIN** | REST API (Resources API v9) for incident creation and data exchange | Federal wildland fire incident reporting requires IRWIN as the data exchange hub across agencies |
| **Utility SCADA** | Event bus or API integration to push near-infrastructure detections | Enables real-time PSPS decisions based on actual fire proximity rather than forecast-only models |
| **Weather data feeds** | Ingest from RAWS stations and NWS APIs for wind speed, humidity, Red Flag warnings | Wind and fuel moisture context is essential for alert prioritization and false-positive suppression |

## Control Model

| Risk | Control |
|------|---------|
| **False positive alert fatigue** | Multi-sensor correlation raises confidence threshold; known false-positive sources (geothermal, industrial) geofenced; watchstander confirms all alerts before dispatch |
| **Missed detection (false negative)** | Overlapping camera coverage zones ensure no single camera failure creates a blind spot; satellite layer provides backup for camera-sparse regions |
| **Privacy in WUI zones** | Camera resolution and storage policies configured to exclude identifiable residential detail; compliance with state surveillance regulations |
| **Sensor network failure** | Solar + battery redundancy; cellular + satellite dual-path backhaul; system degrades gracefully to available modalities |
| **AI model drift** | Continuous retraining on confirmed detections and dismissed false positives; seasonal model variants for snow, dust, fog conditions |

## Reference Technology Stack

| Layer | Default Choice | Reason | Viable Alternative |
|-------|----------------|--------|--------------------|
| **Sensor hardware** | Pano AI camera stations (PTZ + NIR, 60s sweep) | Production-proven at 50M+ acres across 18 states; 15+ utility customers | ALERTCalifornia / Digital Path cameras (1,200+ deployed in CA) |
| **IoT sensor layer** | Dryad Silvanet (LoRaWAN gas sensors) | Purpose-built for dense canopy where cameras lack line-of-sight; 50+ installations worldwide | Custom RAWS-based particulate sensors |
| **Satellite detection** | NOAA NGFS (GOES-based, 5-min CONUS scan) | Federal infrastructure, no per-query cost, approaching operational status in 2026 | FireSat constellation (5x5m resolution, 20-min revisit; full constellation by 2030) |
| **AI inference** | CNN-based smoke classifiers with temporal differencing | Proven architecture for real-time smoke detection; trainable on billion-image datasets | YOLO-family detectors (YOLOv8+) for combined detection and localization |
| **Observability** | Centralized detection dashboard with per-camera health, alert latency, and false-positive tracking | Operators need single-pane visibility across hundreds of sensor stations | Grafana + Prometheus for custom deployments |

## Key Design Decisions

| Decision | Choice | Why It Fits This Use Case |
|----------|--------|---------------------------|
| **Human-in-the-loop confirmation** | All AI alerts require watchstander confirmation before dispatch | Fire agencies will not accept automated dispatch. Trust is built through demonstrated accuracy with human validation. Pano AI and ALERTCalifornia both use this model. |
| **Multi-modal sensor fusion over single-modality** | Combine cameras, IoT sensors, and satellite rather than relying on one type | No single modality covers all conditions. Cameras fail in dense smoke; IoT sensors are range-limited; satellites have resolution limits. Fusion reduces false negatives and raises confidence. |
| **Edge-first processing for cameras** | Run initial smoke classification at or near the camera station | Reduces backhaul bandwidth by transmitting only candidate detections. Critical for remote sites with limited cellular connectivity. |
| **Geofenced exclusion zones** | Maintain a registry of known non-fire heat/smoke sources | Geothermal fields, industrial stacks, and active prescribed burns generate smoke that would otherwise flood operators with false alerts. ALERTCalifornia had to learn to exclude the Sonoma County Geysers. |
