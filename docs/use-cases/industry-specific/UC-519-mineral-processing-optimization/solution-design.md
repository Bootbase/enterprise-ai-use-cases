---
layout: use-case-detail
title: "Solution Design — Autonomous Mineral Processing Optimization"
uc_id: "UC-519"
uc_title: "Autonomous Mineral Processing Optimization"
detail_type: "solution-design"
detail_title: "Solution Design"
category: "Industry-Specific"
category_icon: "⛏️"
industry: "Mining & Metals"
complexity: "High"
status: "detailed"
slug: "UC-519-mineral-processing-optimization"
permalink: /use-cases/UC-519-mineral-processing-optimization/solution-design/
---

## What This Design Covers

This design addresses AI-driven optimization of mineral processing circuits — comminution (crushing and grinding), flotation, and leaching — at hard-rock mining operations. The system ingests real-time sensor data, classifies incoming ore, predicts circuit performance, and recommends set-point adjustments across the entire processing chain every one to five minutes. Operators retain approval authority. The design boundary is the concentrator plant; autonomous haulage, geological exploration, and tailings management are out of scope.

## Recommended Operating Model

| Decision Area | Recommendation |
|---------------|----------------|
| **Autonomy Model** | Advisory with graduated closed-loop: start with operator-approved recommendations, promote proven ore-type recipes to auto-execute within safe envelopes |
| **System of Record** | DCS/SCADA remains the authoritative control system; the AI layer is an advisory overlay that writes back only through approved set-point channels |
| **Human Decision Points** | Operators approve recommendations outside pre-validated envelopes; plant managers approve new ore-type recipe promotions; maintenance engineers approve any change affecting equipment safety limits |
| **Primary Value Driver** | Closing the feedback gap between ore variability (minutes) and lab assay response (hours), enabling cross-circuit optimization that no single operator can track manually |

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PROCESSING PLANT                             │
│                                                                     │
│  ┌──────────┐   ┌──────────┐   ┌────────────┐   ┌──────────────┐  │
│  │ Crushers │──▶│ SAG/Ball │──▶│ Flotation  │──▶│  Concentrate │  │
│  │          │   │  Mills   │   │   Cells    │   │   Thickener  │  │
│  └────┬─────┘   └────┬─────┘   └─────┬──────┘   └──────────────┘  │
│       │sensors       │sensors        │sensors + froth cameras      │
│       ▼              ▼               ▼                             │
│  ┌─────────────────────────────────────────────────────┐           │
│  │              DCS / SCADA Layer                      │           │
│  │         (ABB, Honeywell, Siemens)                   │           │
│  └───────────────────┬─────────────────────────────────┘           │
│                      │ OPC-UA                                      │
└──────────────────────┼──────────────────────────────────────────────┘
                       ▼
              ┌────────────────┐
              │  Data Historian │ (OSIsoft PI / AVEVA)
              │  + Edge Gateway │
              └───────┬────────┘
                      │ REST / streaming
                      ▼
         ┌─────────────────────────┐
         │   AI Optimization Layer  │
         │                         │
         │  ┌───────────────────┐  │
         │  │ Ore Classifier    │  │  ← classifies incoming ore type
         │  ├───────────────────┤  │
         │  │ Circuit Predictor │  │  ← predicts recovery, energy, grade
         │  ├───────────────────┤  │
         │  │ Set-Point Optimizer│ │  ← recommends parameter adjustments
         │  ├───────────────────┤  │
         │  │ Recipe Store      │  │  ← validated envelopes per ore type
         │  └───────────────────┘  │
         └────────────┬────────────┘
                      │ recommendations
                      ▼
         ┌─────────────────────────┐
         │   Operator Dashboard    │  ← approve / override / escalate
         └────────────┬────────────┘
                      │ approved set-points
                      ▼
              DCS / SCADA writeback
```

### Component Responsibilities

| Component | Role | Notes |
|-----------|------|-------|
| DCS/SCADA layer | Executes all physical control; remains sole authority for equipment safety interlocks | Existing ABB, Honeywell, or Siemens systems; AI never bypasses interlocks |
| Data historian + edge gateway | Collects, tags, and buffers sensor streams; provides time-series query interface | OSIsoft PI or AVEVA; edge gateway handles intermittent connectivity at remote sites |
| Ore classifier | Identifies the current ore type from real-time sensor readings (hardness, mineralogy proxies, XRF) | Freeport-McMoRan's implementation identified 7 distinct ore types where operators assumed one |
| Circuit predictor | Forecasts recovery, concentrate grade, energy consumption, and throughput for given set-points and ore type | Ensemble of gradient-boosted decision trees trained on historical process data; 96% accuracy reported at Freeport |
| Set-point optimizer | Searches the parameter space for the set-point combination that maximizes a weighted objective (recovery, throughput, energy) | Constrained optimization subject to equipment limits and permit envelopes |
| Recipe store | Stores validated operating envelopes per ore type; gates which recommendations can auto-execute | Recipes promoted only after operator validation across multiple shifts |
| Operator dashboard | Displays current predictions, recommended changes, predicted impact, and confidence; captures accept/reject decisions | Feedback loop: rejected recommendations train the system on operator judgment |

## End-to-End Flow

| Step | What Happens | Owner |
|------|---------------|-------|
| 1 | Sensor data streams from crushers, mills, flotation cells, and on-line analyzers into the historian via OPC-UA at 1–10 second intervals | DCS/SCADA + historian |
| 2 | Ore classifier identifies the current ore type and feeds it to the circuit predictor | AI layer |
| 3 | Circuit predictor forecasts performance metrics for the current set-points and generates counterfactual predictions for alternative set-points | AI layer |
| 4 | Set-point optimizer selects the parameter combination that maximizes the objective function within equipment and permit constraints | AI layer |
| 5 | Recommendation appears on the operator dashboard with predicted impact and confidence score; operator approves, modifies, or rejects | Operator |
| 6 | Approved set-points write back to DCS/SCADA; the system logs the decision and monitors actual versus predicted performance for model retraining | DCS/SCADA + AI layer |

## AI Responsibilities and Boundaries

| Workflow Area | AI Does | Deterministic System Does | Human Owns |
|---------------|---------|---------------------------|------------|
| Ore classification | Classifies incoming feed from sensor proxies in real time | DCS enforces crusher gap limits regardless of classification | Geologist validates new ore-type categories before they enter the model |
| Comminution optimization | Recommends mill speed, water ratio, classifier cut point | DCS enforces mechanical safe-operating limits (max torque, bearing temperature) | Operator approves recommendations outside validated recipe envelopes |
| Flotation tuning | Recommends reagent dosage, air flow, froth depth targets using froth image analysis | Dosing pumps and air valves execute within calibrated ranges | Metallurgist reviews any recommendation to change reagent type |
| Cross-circuit balancing | Identifies throughput bottlenecks and proposes rebalancing across stages | Interlocks prevent unsafe feed rates between stages | Plant manager approves major throughput target changes |
| Recipe promotion | Flags stable operating envelopes for promotion to auto-execute | Recipe store enforces envelope boundaries deterministically | Plant manager signs off on each recipe promotion |

## Integration Seams

| System | Integration Method | Why It Matters |
|--------|--------------------|----------------|
| DCS/SCADA (ABB, Honeywell, Siemens) | OPC-UA server + dedicated write-back channel with confirmation handshake | The only path to actuators; OPC-UA is the industry standard for cross-vendor interoperability in process control |
| Data historian (OSIsoft PI / AVEVA) | PI Web API (REST) for reads; PI AF SDK for asset context and hierarchy | Historians already store years of tagged sensor data; avoids rebuilding the time-series infrastructure |
| On-line analyzers (XRF, particle size, froth cameras) | Vendor SDK or Modbus-to-OPC-UA gateway | These instruments close the assay feedback gap from hours to seconds; data quality here determines model accuracy |
| Mine planning system | Scheduled file or API pull of the weekly ore-block plan (grade, hardness, mineralogy) | Lets the AI anticipate ore changes before they arrive at the crusher, enabling proactive set-point adjustment |
| LIMS (laboratory information management) | Periodic assay results via REST or file export | Lab results serve as ground-truth labels for model retraining; 2–4 hour lag is acceptable for this purpose |

## Control Model

| Risk | Control |
|------|---------|
| Model recommends parameters outside equipment safe limits | DCS interlocks are hard-coded and independent of the AI layer; optimizer constraints mirror interlock values with a safety margin |
| Ore misclassification causes wrong recipe | Confidence threshold on classification; below threshold, system falls back to conservative default parameters and alerts the operator |
| Stale or missing sensor data feeds incorrect predictions | Data freshness checks on every inference cycle; if any critical sensor exceeds its staleness window, system holds last-known-good set-points and alerts |
| AI writes to DCS without operator awareness | All write-backs are logged with before/after values and operator attribution; auto-execute is limited to promoted recipes within validated envelopes |
| Model drift as ore body depletes or equipment ages | Continuous monitoring of predicted-versus-actual recovery; automated alert when prediction error exceeds a threshold for more than one shift |
| Proprietary process recipes exposed in cloud transfer | Edge inference for latency-sensitive models; cloud used only for model training on anonymized, aggregated data batches |

## Reference Technology Stack

| Layer | Default Choice | Reason | Viable Alternative |
|-------|----------------|--------|--------------------|
| **Model layer** | Gradient-boosted trees (XGBoost / LightGBM) | Proven in mineral processing (Freeport TROI achieved 96% accuracy); handles tabular sensor data well; fast inference on edge hardware | Deep neural nets for froth image analysis (CNN); physics-informed hybrid models |
| **Orchestration** | Edge compute appliance running inference + cloud for training and recipe management | Processing plants are remote with intermittent connectivity; inference must run locally with sub-minute latency | Fully on-premise if connectivity is unreliable; Azure IoT Edge or AWS Greengrass for hybrid |
| **Data integration** | OPC-UA gateway to historian; PI Web API for reads; OPC-UA write-back for set-points | Industry standard; works across ABB, Honeywell, Siemens DCS vendors | MQTT broker at edge with OPC-UA bridge for sites with modern DCS |
| **Observability** | Time-series dashboard (Grafana or PI Vision) tracking predicted vs. actual recovery, model confidence, and recommendation acceptance rate | Operators need visual confirmation that the AI is performing; metallurgists need trend analysis | Vendor-specific dashboards (ABB Ability, Schneider EcoStruxure) |

## Key Design Decisions

| Decision | Choice | Why It Fits This Use Case |
|----------|--------|---------------------------|
| Advisory-first with graduated autonomy | Start with human-approved recommendations; promote stable recipes to auto-execute over time | Mining operators have deep domain expertise and safety culture; trust must be earned before closed-loop control |
| Edge inference, cloud training | Run prediction and optimization models on-site; retrain and update models from cloud | Plant latency requirement is sub-minute; remote sites have unreliable connectivity; training can tolerate hours of delay |
| Ensemble of decision trees over deep learning for process data | XGBoost/LightGBM for tabular sensor data; CNN only for froth imaging | Decision trees match the tabular, feature-engineered nature of process data; they are interpretable, fast, and proven at Freeport and BHP |
| OPC-UA as the single integration standard | All sensor reads and set-point writes flow through OPC-UA | OPC Foundation has a dedicated Mining–Mineral Processing companion specification; avoids vendor lock-in across DCS platforms |
| Ore-type-aware recipe system | Maintain separate validated operating envelopes per classified ore type | Freeport discovered 7 distinct ore types where operators assumed one; per-type optimization is where the largest recovery gains originate |
