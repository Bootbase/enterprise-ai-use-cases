---
layout: use-case-detail
title: "References — Autonomous Agricultural Crop Protection and Precision Treatment"
uc_id: "UC-510"
uc_title: "Autonomous Agricultural Crop Protection and Precision Treatment"
detail_type: "references"
detail_title: "References"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Agriculture"
complexity: "High"
status: "detailed"
slug: "UC-510-agriculture-crop-protection"
permalink: /use-cases/UC-510-agriculture-crop-protection/references/
---

## Source Quality Notes

The business evidence for this use case is strongest on herbicide reduction and yield improvement, anchored by John Deere's published deployment data across 5 million acres. This is a vendor-published metric on its own product, but the scale and specificity (per-acre savings, gallons saved, multi-state field studies) make it directionally reliable. Platform adoption figures from BASF xarvio and Syngenta Cropwise are also vendor-reported but corroborated across multiple press releases and industry coverage. The technical architecture details for edge inference and camera systems come from a university extension publication based on manufacturer specifications. The systematic review from Frontiers in Agronomy provides independent academic validation of detection accuracy claims. Economic estimates for farm-level costs and payback are derived from published per-acre pricing and industry benchmarks, not from independent audits.

## Source Register

| ID | Type | Source | Why It Was Used | Link |
|----|------|--------|-----------------|------|
| S1 | Primary deployment | John Deere See & Spray 2025 deployment press release | Published 5M acre deployment, 50% herbicide reduction, 31M gallons saved, 2 bu/acre yield gain, and per-acre pricing model | [John Deere newsroom](https://www.deere.com/en/news/all-news/see-spray-technology-across-5-million-acres/) |
| S2 | Official docs | John Deere See & Spray Gen 2 product page | Technical specifications, supported crops, equipment compatibility, and boom configuration | [John Deere precision ag](https://www.deere.com/en/sprayers/see-spray-gen-2/) |
| S3 | Analysis | Mississippi State University Extension: See & Spray Technology (P3904) | Technical detail on 36-camera configuration, 20+ fps processing, NVIDIA GPU inference, 1M+ image training library, and 4-inch spray precision | [MSU Extension](https://extension.msstate.edu/publications/see-spray-technology) |
| S4 | Primary deployment | Syngenta Cropwise digital farming platform | Supports scale evidence: 100M hectares across digital solutions, 40,000+ users, open platform for third-party developers | [Syngenta digital farming](https://www.syngenta.com/products/digital-farming) |
| S5 | Domain standard | FAO global crop loss assessment (via Seed World) | Provides the baseline problem statement: up to 40% crop loss from pests and diseases, $220B annual trade losses | [Seed World](https://www.seedworld.com/canada/2021/06/03/pests-destroy-up-to-40-of-global-crops-and-cost-220-billion/) |
| S6 | Domain standard | ISO 11783 (ISOBUS) standard overview | Documents the ISOBUS protocol, task controller functionality (ISO 11783-10), and ISOXML prescription map data interchange format | [Wikipedia: ISO 11783](https://en.wikipedia.org/wiki/ISO_11783) |
| S7 | Analysis | Frontiers in Agronomy: Integrating UAVs, Satellite Remote Sensing, and Machine Learning in Precision Agriculture (2026) | Independent systematic review of 101 studies; provides validated accuracy metrics (95%+), detection timing (2-3 weeks pre-symptom), UAV cost ranges, and generalization challenges | [Frontiers in Agronomy](https://www.frontiersin.org/journals/agronomy/articles/10.3389/fagro.2025.1670380/full) |
| S8 | Primary deployment | BASF xarvio digital farming platform | Supports platform scale: 130,000+ users, 20M hectares, 250+ annual validation trials, 25+ years of agronomic models, 40+ equipment partner integrations | [xarvio](https://ag.xarvio.com/) |

## Claim Map

| Claim Or Section | Source IDs |
|------------------|------------|
| Solution design: semi-autonomous operating model with confidence-based auto-spray for weeds and agronomist review for disease | S1, S3 |
| Solution design: two-tier monitoring (satellite field-level plus equipment plant-level) | S4, S7 |
| Solution design: ISOXML as the cross-manufacturer integration contract | S6 |
| Solution design: edge-first inference architecture using equipment-mounted GPUs | S1, S3 |
| Implementation guide: YOLO-variant detection model with TensorRT export to NVIDIA Jetson | S3, S7 |
| Implementation guide: Sentinel-2 satellite imagery for NDVI/NDRE vegetation index monitoring | S7 |
| Implementation guide: ISOXML prescription map generation for task controller delivery | S6 |
| Evaluation: 50% herbicide reduction and 2 bu/acre yield gain at commercial scale | S1 |
| Evaluation: 130,000+ users and 20M hectares under AI-driven crop management | S8 |
| Evaluation: detection accuracy exceeding 95% for specific crop diseases | S7 |
| Evaluation: FAO baseline of 40% global crop loss and $220B annual cost | S5 |
| Evaluation: economic scenario model based on per-acre pricing and published savings | S1, S2 |
