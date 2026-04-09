# UC-057: Autonomous Manufacturing Quality Inspection and Defect Remediation with Agentic AI Vision Systems

## Metadata

| Field            | Value                        |
|------------------|------------------------------|
| **ID**           | UC-057                       |
| **Category**     | Industry-Specific            |
| **Industry**     | Manufacturing (Automotive, Electronics, Aerospace, Consumer Goods) |
| **Complexity**   | High                         |
| **Status**       | `research`                   |

---

## Problem Statement

Manufacturing quality inspection is the last major production bottleneck that still depends overwhelmingly on human eyesight. Across the global manufacturing sector, the **cost of poor quality averages 20% of total revenue** — for a manufacturer generating USD 10 billion in annual sales, nearly USD 2 billion is consumed by scrap, rework, warranty claims, recalls, and the inspection labor itself (American Society for Quality). The root cause is structural: human visual inspectors operating at production-line speed achieve only **80% defect detection accuracy** and miss **up to 90% of microscopic or sub-surface defects** (Voxel51 Visual AI in Manufacturing 2025 Landscape; Jidoka Technologies). At Audi's Neckarsulm plant alone, the body shop produces **300 car bodies per shift, each with approximately 5,000 spot welds** — totaling **1.5 million spot welds inspected per shift** (Audi MediaCenter). At BMW Group Plant Regensburg, **1,400 vehicles per day** pass through assembly, each requiring configuration-specific quality checks across paint, body, trim, and final assembly (BMW Group Press). Foxconn's electronics assembly lines produce millions of PCBs per day for clients including Apple, Dell, and HP, where solder joint defects measured in micrometers determine whether a USD 1,200 device ships or scraps.

The economics of manual inspection are punishing. In automotive, a single undetected weld spatter that causes a field failure can trigger recalls costing **USD 500M–1.3B** — Toyota's 2009–2010 recall crisis cost **USD 1.3 billion** in direct losses plus billions more in market cap destruction. In electronics, Foxconn's pre-AI PCB inspection lines required teams of 30–50 inspectors per line working in 8-hour shifts under magnification, with fatigue-driven accuracy degradation of 15–25% by mid-shift. In aerospace, a missed composite delamination in a turbine blade or fuselage panel is a potential catastrophic failure — the FAA's AD (Airworthiness Directive) system mandates zero tolerance, and manual ultrasonic/radiographic inspection of a single aircraft engine takes **40–80 hours** (GE Aviation).

The agentic opportunity is not just "better cameras" — that has existed for a decade in the form of rule-based machine vision (Cognex, Keyence, SICK). The paradigm shift in 2024–2026 is the move from **passive detection** (flag a defect, alert a human, wait for manual disposition) to **autonomous closed-loop quality control** where multi-agent AI systems detect a defect, diagnose its root cause by correlating upstream process parameters (temperature, pressure, feed rate, tool wear), decide the corrective action (recalibrate machine, adjust process parameters, halt the line, route the part for rework vs. scrap), and execute it — all within the production cycle time. At Audi Neckarsulm, the Weld Splatter Detection (WSD) system, built with **Siemens Industrial Edge and the Industrial AI Suite**, detects weld spatter on car body underbodies in real time, projects a light pattern directly onto each affected spot, and **directs a grinding robot to remove the spatter autonomously — no human in the loop** (Audi MediaCenter 2024; Automotive Manufacturing Solutions 2025). Audi's ProcessGuardAI, also built with Siemens, monitors paint-shop processes in real time and autonomously adjusts dosage in pretreatment and detects anomalies in cathodic dip coating (CDC), with series production rollout planned for **Q2 2026**. At Siemens' own Amberg Electronics Plant in Germany, edge-deployed AI achieves **99.9% production quality** by predicting component defects before they occur and **dynamically recalibrating production settings** in real time (Arm Newsroom; Siemens Industrial AI). BMW's AIQX (AI Quality Next) platform deploys camera- and sensor-based AI quality checks across **every BMW plant globally**, and their GenAI4Q pilot at Regensburg uses generative AI to build a bespoke inspection catalog for each vehicle based on its specific configuration and production history, **reducing vehicle defects by up to 60%** and **cutting manual inspection time by 50%** (BMW Group Press; Chief AI Officer). Foxconn deployed AI vision systems across its PCB production lines, **reducing manual inspection time by 70% and cutting defect rates by 45%** (Voxel51 2025). Tesla uses AI-powered vision systems in its Gigafactories to inspect battery cell welds and body panel alignments at production speed.

Despite these production-grade deployments, **77% of AI vision implementations in manufacturing remain stuck at prototype or pilot scale** (Voxel51 2025). The barrier is not the model — it is the full agentic loop: integrating vision inference with Manufacturing Execution Systems (MES), Programmable Logic Controllers (PLCs), Statistical Process Control (SPC) systems, and ERP at line speed, while maintaining the audit trail and traceability that automotive (IATF 16949), aerospace (AS9100), medical device (ISO 13485), and food (FSSC 22000) quality standards demand. **Deloitte projects that 25% of enterprises using GenAI will deploy autonomous AI agents in 2025, doubling to 50% by 2027** (Deloitte 2025). The AI Inspection Market is projected to grow from **USD 33.07 billion in 2025 to USD 102.42 billion by 2032**, at a CAGR of 17.5% (MarketsandMarkets). The automotive AI quality inspection segment alone is projected at **USD 515 million in 2025 → USD 2.99 billion by 2035** (Precedence Research). The companies that close the loop — from detection to autonomous remediation — will define the next generation of manufacturing competitiveness.

---

## Business Impact

| Dimension       | Description                               |
|-----------------|-------------------------------------------|
| **Cost**        | Cost of poor quality averages 20% of revenue across manufacturing (ASQ). Toyota's 2009–2010 recall: USD 1.3B direct cost. Manual inspection labor: 30–50 inspectors per high-volume line at USD 40K–70K/year each, plus supervisors, calibration, and re-inspection. Foxconn reported 70% reduction in manual inspection time after AI deployment. BMW achieved 50% reduction in manual inspection time with AIQX. Siemens Amberg: 30% reduction in unplanned downtime, 15% increase in asset utilization, 20% productivity increase across manufacturing network. Scrap cost reduction: AI-driven quality systems have cut defect rates by up to 90% (Siemens), translating to millions saved in rework, scrap, and warranty claims. The AI Inspection Market: USD 33.07B (2025) → USD 102.42B (2032). |
| **Time**        | Manual visual inspection: 5–30 seconds per part depending on complexity; AI vision: < 200 milliseconds per part (100–150× faster). Manual ultrasonic inspection of a single aerospace engine: 40–80 hours; AI-augmented: target < 8 hours. Audi WSD: autonomous weld spatter detection and robotic grinding within the production cycle time (no line stoppage). BMW GenAI4Q: bespoke inspection catalog generated per vehicle in seconds vs. static paper checklists. Siemens edge AI: defect prediction and process recalibration in milliseconds, before the defective part reaches final inspection. |
| **Error Rate**  | Human visual inspection accuracy: ~80% overall; misses up to 90% of microscopic defects (sub-50-micrometer solder voids, hairline cracks, sub-surface delaminations). Fatigue-driven degradation: 15–25% accuracy loss by mid-shift. Inter-inspector variability: two inspectors examining the same part reach different conclusions 10–20% of the time. AI vision accuracy: 99%+ detection rate in production (Jidoka Technologies); Siemens Amberg achieves 99.9% production quality. BMW AIQX: 60% reduction in escaped defects reaching customers. Google Cloud Visual Inspection AI: up to 10× higher accuracy than general ML platforms, trainable with as few as 10 labeled images. |
| **Scale**       | Audi Neckarsulm: 1.5 million spot welds per shift across 300 car bodies. BMW Regensburg: 1,400 vehicles/day. Foxconn: millions of PCBs/day across dozens of lines for Apple, Dell, HP. Tesla Gigafactories: continuous battery cell and body panel inspection at production speed. Siemens Amberg: AI monitoring 10,000+ machines with 7–10 day failure prediction horizon. Global manufacturing output: USD 16.4 trillion (2024, World Bank). Automotive alone: 85 million vehicles/year globally, each with 3,000–6,000 welds and hundreds of painted surfaces, trim pieces, and electronic assemblies requiring inspection. |
| **Risk**        | Product recalls: Toyota USD 1.3B (2009–2010), Takata airbag recall USD 24B+ industry-wide, Samsung Galaxy Note 7 USD 5.3B. Regulatory: IATF 16949 (automotive), AS9100 (aerospace), ISO 13485 (medical devices), FDA 21 CFR Part 820 (medical), FSSC 22000 (food) all mandate documented quality inspection with traceability. Liability: a missed defect in aerospace or medical devices creates catastrophic failure risk — FAA Airworthiness Directives, EU EASA, product liability litigation. Reputation: a single high-profile recall can destroy years of brand equity. AI-specific risks: false negatives (missed defects that escape), false positives (over-rejection increasing scrap), adversarial conditions (lighting changes, material variations, novel defect types), and model drift as production processes evolve — addressed via continuous monitoring, human-in-the-loop for critical decisions, and periodic model revalidation. |

---

## Current Process (Before AI)

1. **Inline visual inspection**: Human inspectors stationed at fixed points along the production line visually examine parts under controlled lighting. In automotive body shops, inspectors check welds, panel gaps, paint finish, and trim alignment. In electronics, inspectors use magnification loupes or microscopes to examine solder joints, component placement, and PCB traces. Inspection stations operate at takt time (45–90 seconds per vehicle in automotive, 2–10 seconds per PCB in electronics).
2. **Sampling-based statistical quality control (SQC)**: Not every part is inspected — statistical sampling plans (AQL tables per ISO 2859 / ANSI Z1.4) inspect 1-in-N parts. For a 1% AQL on a 10,000-unit lot, only 200 units are inspected. Defects in the uninspected 98% escape to customers or downstream assembly.
3. **Measurement and dimensional inspection**: Coordinate Measuring Machines (CMMs), calipers, gauges, and go/no-go fixtures verify critical dimensions. CMM inspection of a complex aerospace part takes 20–60 minutes. Results are logged in SPC systems (Minitab, InfinityQS, Hertzler Systems).
4. **Non-destructive testing (NDT)**: For critical structural components (aerospace, automotive safety parts, pressure vessels), ultrasonic testing (UT), radiographic testing (RT), magnetic particle inspection (MPI), and dye penetrant inspection (DPI) are performed by certified NDT technicians (ASNT Level II/III). A single UT scan of an aircraft engine disk takes hours.
5. **Defect logging and disposition**: When a defect is found, the inspector logs it in the MES (SAP ME, Siemens Opcenter, Rockwell Plex, Dassault DELMIA) or on paper. The part is tagged and routed to a Material Review Board (MRB) for disposition: rework, scrap, use-as-is, or return to supplier.
6. **Root cause analysis (manual)**: Quality engineers investigate escaped defects post-hoc using 8D reports, fishbone (Ishikawa) diagrams, and 5-Why analysis. They manually correlate the defect with upstream process parameters by pulling data from SCADA/historian systems (OSIsoft PI, Wonderware, Aveva), machine logs, and operator records. This investigation typically takes 2–5 days.
7. **Corrective action**: Process engineers manually adjust machine settings, tooling, or raw material specifications based on the root cause analysis. Changes go through a formal Engineering Change Order (ECO) process, which in regulated industries (automotive IATF 16949, aerospace AS9100) requires documentation, approval, and revalidation — adding weeks to months of delay before the fix reaches the production line.
8. **Supplier quality management**: Incoming material inspection (IMI) teams inspect raw materials and components from suppliers against specifications. Supplier quality issues are tracked via Supplier Corrective Action Requests (SCARs), with resolution cycles of 30–90 days.

### Bottlenecks & Pain Points

- **Human fatigue and inconsistency**: Inspectors lose 15–25% accuracy by mid-shift. Two inspectors examining the same part disagree 10–20% of the time. Night shifts and overtime exacerbate the problem. OSHA reports musculoskeletal disorders as the leading occupational injury in inspection roles.
- **Sampling misses systematic defects**: Statistical sampling catches random defects but misses systematic process drifts that affect every Nth part. A tool wear pattern affecting 3% of parts will pass a 1% AQL sampling plan undetected for days.
- **Reactive root cause analysis**: By the time a defect is detected, logged, investigated, and corrected, hundreds or thousands of defective parts have already been produced, shipped, or assembled into higher-level assemblies. The "detection-to-correction" latency is measured in days to weeks.
- **Siloed data systems**: Vision inspection, CMM, SPC, MES, SCADA/historian, and ERP systems are rarely integrated. A quality engineer manually exports data from 4–6 systems into Excel to correlate a defect with its root cause. No single system has the end-to-end view.
- **100% inspection is economically infeasible manually**: Inspecting every unit on a high-volume line (e.g., 5,000 PCBs/hour) requires an army of inspectors that no manufacturer can afford or retain. The result is sampling, which by definition lets defects escape.
- **Inflexible rule-based machine vision**: Legacy Cognex/Keyence vision systems use hand-programmed rules (blob detection, edge finding, template matching) that break when part geometry, surface finish, lighting, or defect morphology changes. Reprogramming for a new product variant takes weeks of vision engineering.
- **No closed-loop corrective action**: Even when a vision system detects a defect, the disposition decision and corrective action are manual. The camera flags it; a human decides what to do; another human adjusts the machine. The feedback loop is hours to days, not milliseconds.

---

## Desired Outcome (After AI)

A multi-agent agentic AI quality system deployed at the production-line edge where specialized agents autonomously execute the full quality loop — defect detection via deep-learning vision, root cause diagnosis via process parameter correlation, corrective action via closed-loop machine control, and traceability via MES integration — with human oversight for high-consequence decisions (line stoppage, batch quarantine, customer notification) and regulatory traceability (IATF 16949, AS9100, ISO 13485). The pattern that Audi WSD + ProcessGuardAI, Siemens Amberg, BMW AIQX + GenAI4Q, and Foxconn's AI vision deployment have validated at production scale.

The target multi-agent architecture (synthesized from Audi/Siemens, BMW, XMPRO, and Deloitte published frameworks):

1. **Vision Inspection Agent** — runs deep-learning inference (CNN, Vision Transformer, or foundation model) on camera/sensor streams at line speed (< 200ms per frame). Detects, classifies, and precisely localizes defect types (scratches, dents, porosity, weld spatter, solder voids, misalignment, surface contamination, dimensional deviation). Trained on as few as 10–300 labeled images per defect class (Google Cloud Visual Inspection AI benchmark). Deployed on edge compute (NVIDIA Jetson, Siemens Industrial Edge, AWS Panorama) to meet < 200ms latency at the point of inspection.
2. **Process Correlation Agent** — ingests real-time telemetry from SCADA/historian (OPC UA, OSIsoft PI), PLC (Siemens S7, Allen-Bradley, Mitsubishi), and MES (SAP ME, Siemens Opcenter, Rockwell Plex). When the Vision Agent flags a defect, this agent correlates it with upstream process variables (temperature, pressure, feed rate, tool cycle count, raw material lot, operator shift) to identify probable root cause — replacing the manual 5-Why / 8D investigation that takes days.
3. **Corrective Action Agent** — based on the root cause diagnosis, determines the appropriate corrective action within pre-validated guardrails: adjust machine parameter (e.g., weld current +-5%), trigger tool change, recalibrate sensor, re-route part for rework, or escalate to human (line stop, batch quarantine). Low-risk corrections (parameter tweaks within validated bounds) are executed autonomously via PLC write-back; high-risk actions (line stop, scrap batch, supplier notification) require human approval.
4. **Traceability Agent** — logs every detection, diagnosis, and action to the MES and Quality Management System (QMS) with full audit trail: timestamp, part serial/lot, defect classification with confidence score, images, correlated process parameters, action taken, model version, and operator override (if any). Generates regulatory-compliant quality records (PPAP, control plans, inspection reports) for IATF 16949, AS9100, or ISO 13485 auditors.
5. **Continuous Learning Agent** — monitors model performance metrics (precision, recall, false positive/negative rates) in production. Flags model drift when defect distributions shift (new product variant, new supplier material, seasonal environmental change). Triggers retraining pipeline with human-reviewed new ground truth labels. Manages model versioning and A/B deployment on edge devices.
6. **Orchestrator Agent** — coordinates the multi-agent workflow, manages priority (safety-critical defects override throughput targets), handles agent failures (fallback to human inspection if Vision Agent confidence drops below threshold), and provides the real-time quality dashboard for plant managers and quality engineers.

The end state: **100% inline inspection** (every unit, every surface, every weld — not sampling) at production speed, with **defect detection accuracy > 99%** (vs. 80% human), **root cause identification in seconds** (vs. days), and **autonomous corrective action within the production cycle time** (vs. weeks). Escaped defects to customers drop by 60–90%. Scrap and rework costs drop by 30–50%. Quality engineering headcount is redeployed from reactive firefighting to proactive process improvement.

### Success Criteria

| Metric                                  | Target                                                                                              |
|-----------------------------------------|-----------------------------------------------------------------------------------------------------|
| Defect detection accuracy               | > 99% (vs. 80% human baseline; Siemens Amberg benchmark: 99.9%)                                    |
| Inspection coverage                     | 100% inline (every unit inspected; vs. 1–5% sampling baseline)                                     |
| Inference latency per frame             | < 200 milliseconds at the edge (production line speed; Voxel51 benchmark)                           |
| False positive rate (over-rejection)    | < 2% (vs. 5–15% with rule-based machine vision)                                                    |
| Root cause identification time          | < 5 minutes (vs. 2–5 days manual 8D/5-Why baseline)                                                |
| Detection-to-correction latency         | < 1 production cycle (autonomous closed-loop; vs. days-to-weeks manual baseline)                    |
| Escaped defects to customer             | 60–90% reduction (BMW AIQX benchmark: 60% reduction in escaped defects)                            |
| Scrap and rework cost reduction         | 30–50% (Siemens benchmark: defect rates cut by up to 90%)                                          |
| Manual inspection labor reduction       | 50–70% (BMW: 50%, Foxconn: 70%)                                                                    |
| Unplanned downtime reduction            | 30% (Siemens Amberg benchmark)                                                                     |
| Model retraining cycle                  | < 1 week from drift detection to redeployment (vs. months for rule-based vision reprogramming)      |
| Regulatory audit compliance             | 100% traceability of every inspection decision with full audit trail (IATF 16949, AS9100, ISO 13485) |
| Human-in-the-loop                       | 100% of line-stop, batch-quarantine, and customer-notification decisions approved by human           |

---

## Stakeholders

| Role                                            | Interest                                                                                          |
|-------------------------------------------------|---------------------------------------------------------------------------------------------------|
| VP / Director of Quality                        | Escaped defect rate, customer complaints (PPM), recall risk, IATF 16949 / AS9100 audit readiness |
| Plant Manager                                   | OEE (Overall Equipment Effectiveness), throughput, scrap rate, unplanned downtime                |
| Quality Engineers                               | Root cause analysis speed, SPC trend visibility, corrective action effectiveness                  |
| Production / Manufacturing Engineers            | Process parameter optimization, tool wear prediction, changeover time                            |
| Line Operators / Inspectors                     | Reduced repetitive strain, meaningful work (exception handling vs. staring at parts all day)      |
| Maintenance / Reliability Engineers             | Predictive maintenance integration, unplanned downtime reduction                                 |
| Supplier Quality Engineers                      | Incoming material quality visibility, SCAR automation, supplier performance tracking             |
| IT / OT Convergence Team                        | Edge infrastructure, OPC UA connectivity, cybersecurity (IEC 62443), MES integration             |
| Chief Operating Officer (COO)                   | Cost of poor quality reduction, manufacturing competitiveness, capacity utilization               |
| Regulatory / Compliance (IATF, AS9100, FDA)     | Inspection traceability, validated systems (IQ/OQ/PQ for FDA), audit evidence                    |
| EHS (Environment, Health & Safety)              | Reduced inspector ergonomic injuries (MSDs), hazardous environment inspection (foundries, paint shops) |
| Customers (OEMs, tier-1 buyers)                 | Incoming quality (PPM), warranty claims, PPAP documentation                                      |
| CFO                                             | Cost of poor quality (20% of revenue baseline), scrap/rework reduction, recall liability          |

---

## Constraints

| Constraint              | Detail                                                                                                                                                                                                                                                                                                                                                                                                                                                |
|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Data Privacy**        | Proprietary product designs, process parameters, and defect data are trade secrets. Models must run on-premises or in a dedicated cloud tenancy with no third-party model training on production data. Edge inference preferred to minimize data egress. Customer-specific product data (e.g., Apple's component specifications at Foxconn) is governed by strict NDAs. GDPR applies to any worker performance data captured incidentally by vision systems (EU sites). |
| **Latency**             | Inference must complete within the production takt time: < 200ms per frame for high-speed lines (electronics: 2–10s takt; automotive body shop: 45–90s takt). Edge deployment mandatory — cloud round-trip latency (50–200ms) is unacceptable for closed-loop control. For corrective PLC write-back, deterministic latency < 10ms is required (OPC UA real-time via TSN). Batch processes (paint curing, heat treatment) have more latency tolerance (seconds to minutes). |
| **Budget**              | Edge compute hardware: USD 5K–50K per inspection station (NVIDIA Jetson AGX Orin, Siemens Industrial Edge IPC, Intel-based edge). Camera systems: USD 2K–20K per station (industrial GigE, CoaXPress, or line-scan cameras; hyperspectral for specialized applications: USD 50K+). Software licensing: Siemens Industrial AI Suite, Google Cloud Visual Inspection AI, Landing AI LandingLens, or open-source (PyTorch + custom). Total per-line deployment: USD 100K–500K. ROI payback expected within 6–18 months from scrap/rework reduction and inspector labor reallocation. |
| **Existing Systems**    | Must integrate with existing MES (SAP ME, Siemens Opcenter, Rockwell Plex, Dassault DELMIA, MPDV Hydra), SCADA/historian (OSIsoft PI / AVEVA PI, Wonderware, Ignition), PLC (Siemens S7-1500, Allen-Bradley ControlLogix, Mitsubishi Q/iQ-R), ERP (SAP S/4HANA, Oracle Cloud), QMS (ETQ Reliance, MasterControl, Veeva Vault Quality, SAP QM), and SPC systems (Minitab, InfinityQS, Hertzler). Cannot require ripping out existing vision systems (Cognex, Keyence) — must layer deep learning on top or run in parallel. OPC UA is the standard integration protocol for OT connectivity. |
| **Compliance**          | Automotive: IATF 16949 (quality management), VDA 6.3 (process audit), AIAG PPAP/APQP, customer-specific requirements (CSRs) from OEMs. Aerospace: AS9100 (quality), NADCAP (special processes — welding, NDT, heat treat). Medical devices: ISO 13485, FDA 21 CFR Part 820, EU MDR 2017/745, computerized system validation (CSV/CSA per GAMP 5). Food: FSSC 22000, HACCP, FDA FSMA. All require documented inspection procedures, validated measurement systems (MSA / Gage R&R), full traceability of inspection decisions, and change control for any modifications to inspection methods. AI model changes must follow the validated change control process. EU AI Act: manufacturing quality inspection AI is not classified as high-risk under Annex III, but some applications (worker safety, medical devices) may fall under high-risk classification requiring conformity assessment. |
| **Scale**               | Automotive body shop: 300–1,400 vehicles/day per plant, 3,000–6,000 welds per vehicle. Electronics: 5,000–50,000 PCBs/hour per line. Aerospace: lower volume but extreme inspection depth (100% NDT on safety-critical parts). Multi-plant deployment: a global OEM operates 20–60 plants worldwide; the solution must be deployable, manageable, and updatable across all sites with centralized model management and localized edge inference. Model must handle 50–500+ defect classes across product variants without per-variant retraining from scratch. |

---

## Scope Boundaries

### In Scope

- Deep-learning visual inspection for surface defects (scratches, dents, porosity, contamination, discoloration), dimensional deviations, assembly errors (missing components, misalignment, wrong orientation), weld quality (spatter, undercut, porosity, incomplete fusion), solder joint quality (bridges, cold joints, voids, insufficient/excess solder), and paint/coating defects (orange peel, runs, sags, inclusions, color mismatch)
- Closed-loop autonomous corrective action for pre-validated, low-risk process parameter adjustments (weld current, laser power, press tonnage, temperature setpoint, feed rate) via PLC write-back
- Real-time root cause correlation linking detected defects to upstream process parameters, tool wear, raw material lots, and environmental conditions
- Edge-deployed inference (< 200ms latency) on NVIDIA Jetson, Siemens Industrial Edge, or equivalent edge compute platforms
- MES integration (SAP ME, Siemens Opcenter, Rockwell Plex) for part traceability, defect logging, and disposition routing
- SPC integration for automated control chart updates and process capability monitoring (Cp, Cpk, Pp, Ppk)
- Model lifecycle management: training, validation, deployment, monitoring, drift detection, and retraining with human-reviewed ground truth
- Regulatory-compliant audit trail and documentation for IATF 16949, AS9100, ISO 13485, and FDA 21 CFR Part 820
- Multi-plant centralized model management with localized edge inference
- Human-in-the-loop for high-consequence decisions: line stop, batch quarantine, product hold, customer notification, and model retraining approval

### Out of Scope

- Autonomous line stoppage without human approval for safety-critical products (aerospace, medical devices — regulatory non-starter for fully autonomous halt)
- Predictive maintenance of production equipment (related but separate domain — covered by Siemens Senseye, PTC ThingWorx, Uptake, SparkCognition, GE Predix in dedicated PdM use cases)
- Supply chain quality risk prediction and supplier selection (separate procurement/supply chain use case)
- Product design optimization and generative design (separate CAD/PLM domain — Autodesk, Siemens NX, PTC Creo)
- Worker safety monitoring and PPE compliance detection (separate EHS use case using computer vision but different problem domain)
- Customer warranty analytics and field failure prediction (downstream quality domain — separate use case)
- Fully autonomous robotic assembly (this use case covers inspection and corrective parameter adjustment, not the assembly itself)
- Pre-deep-learning rule-based machine vision (Cognex VisionPro, Keyence CV-X series rule-based modes) — those are upstream components that the agentic system layers on top of, not the use case itself
- Consumer goods brand protection and counterfeit detection (different problem domain)
