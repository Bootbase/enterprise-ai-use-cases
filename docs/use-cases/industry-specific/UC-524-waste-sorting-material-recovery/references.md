---
layout: use-case-detail
title: "References — Autonomous Waste Sorting and Material Recovery Optimization"
uc_id: "UC-524"
uc_title: "Autonomous Waste Sorting and Material Recovery Optimization"
detail_type: "references"
detail_title: "References"
category: "Industry-Specific"
category_icon: "recycle"
industry: "Waste Management / Circular Economy"
complexity: "High"
status: "detailed"
slug: "UC-524-waste-sorting-material-recovery"
permalink: /use-cases/UC-524-waste-sorting-material-recovery/references/
---

## Source Quality Notes

The evidence base for this use case is unusually strong. Three of the six primary sources are named production deployments with published performance metrics (AMP/SPSA, EverestLabs facility case studies, Greyparrot facility deployments). The Contrary Research analysis provides independently compiled business and technical data on AMP Robotics. The two remaining sources (AMP corporate site, ZenRobotics product pages) are vendor materials but include specific deployment numbers and technical specifications rather than generic marketing claims. The weakest area is cross-facility transfer learning — no source provides rigorous evidence on how well models trained at one MRF perform at another.

## Source Register

| ID | Type | Source | Why It Was Used | Link |
|----|------|--------|-----------------|------|
| S1 | Primary deployment | AMP / SPSA Virginia — largest US recycling project, 20-year contract, 540,000 tons/year | Anchor evidence for commercial viability and public-sector adoption at scale | [AMP SPSA announcement](https://ampsortation.com/articles/largest-us-recycling-project-spsa) |
| S2 | Analysis | Contrary Research — AMP Robotics business breakdown | Independent compilation of AMP technical specs, pricing ($300K purchase / $6K/month lease), cost-per-ton reduction ($95 to $65), deployment numbers, and competitive landscape | [Contrary Research: AMP Robotics](https://research.contrary.com/company/amp-robotics) |
| S3 | Primary deployment | EverestLabs MRF case studies — HDPE recovery, last-chance line savings, Alameda County Industries | Per-facility revenue and labor cost metrics from named deployments | [EverestLabs case studies](https://www.everestlabs.ai/) |
| S4 | Primary deployment | Greyparrot — 160+ analyzer units, 52 billion objects analyzed, facility-level results | Composition analytics deployment scale and accuracy; proves the analytics-only layer delivers standalone ROI | [Greyparrot](https://www.greyparrot.ai) |
| S5 | Vendor technical | AMP Robotics corporate — platform architecture (Vision, Neuron, Cortex, Clarity), 400+ systems, 150 billion items | Technical architecture details, pick rate (80+/min), accuracy (99%), system component descriptions | [AMP Robotics](https://ampsortation.com/) |
| S6 | Vendor technical | ZenRobotics (Terex) — 4th-gen robots, 500+ waste categories, Heavy Picker and Fast Picker specs | Multi-generation product maturity; 60-100% efficiency gain over previous generation; competitive reference point | [ZenRobotics](https://www.terex.com/zenrobotics) |
| S7 | Domain standard | EU Waste Framework Directive (revised October 2025) — recycling targets, EPR schemes, packaging waste regulation | Regulatory context for EU facilities; 65% municipal recycling by 2035; EPR fee structures driving demand for composition data | [EU Waste Framework Directive](https://environment.ec.europa.eu/topics/waste-and-recycling/waste-framework-directive_en) |
| S8 | Academic / industry | PLC-Controlled Intelligent Conveyor System with AI-Enhanced Vision for Efficient Waste Sorting (Applied Sciences, 2025) | Technical architecture reference for vision-PLC integration patterns used in the implementation guide | [MDPI Applied Sciences](https://www.mdpi.com/2076-3417/15/3/1550) |
| S9 | Vendor technical | Greyparrot — How It Works (product page) | Technical details: 111 material categories, 7 analytical layers, Sync API for third-party integration, retrofittable hardware | [Greyparrot How It Works](https://www.greyparrot.ai/how-it-works) |

## Claim Map

| Claim Or Section | Source IDs |
|------------------|------------|
| 80+ picks/min robotic throughput, 2x human speed | S2, S5 |
| 99% classification accuracy | S2, S5 |
| 400+ AI systems deployed globally, 150 billion items identified | S5 |
| 20-year SPSA contract, 540,000 tons/year, 20% diversion guarantee | S1 |
| $300K purchase price / $6K/month lease per robot | S2 |
| Processing cost reduction from ~$95/ton to ~$65/ton | S2 |
| 1-year payback period | S2 |
| $250K/year HDPE recovery, $400K/year last-chance line savings, 60% labor cost reduction | S3 |
| 160+ analyzer units, 52 billion objects analyzed, 98% accuracy, 111 categories | S4, S9 |
| 18% material recovery increase from composition analytics alone | S4 |
| 500+ waste categories identified by ZenRobotics 4th-gen; 60-100% efficiency gain | S6 |
| EU 65% municipal recycling target by 2035; EPR scheme expansion | S7 |
| Vision-PLC integration architecture (OPC UA, EtherCAT) | S8 |
| Greyparrot Sync API for third-party hardware/software integration | S9 |
| 3-4 FTEs displaced per robot across two shifts | S2 |
| Edge inference sub-15ms latency requirement | S8 (architecture reference); S5 (implied by 80 picks/min at belt speed) |
| Commodity price volatility risk (China 2018 import ban, $90 to $50/ton) | S2 |
