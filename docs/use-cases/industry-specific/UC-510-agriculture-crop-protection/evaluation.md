---
layout: use-case-detail
title: "Evaluation — Autonomous Agricultural Crop Protection and Precision Treatment"
uc_id: "UC-510"
uc_title: "Autonomous Agricultural Crop Protection and Precision Treatment"
detail_type: "evaluation"
detail_title: "Evaluation"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Agriculture"
complexity: "High"
status: "detailed"
slug: "UC-510-agriculture-crop-protection"
permalink: /use-cases/UC-510-agriculture-crop-protection/evaluation/
---

## Decision Summary

This is a strong use case with primary evidence from a production deployment at commercial scale. John Deere's See & Spray system treated 5 million acres in 2025 with published herbicide savings of approximately 50% and a measurable yield uplift. BASF xarvio and Syngenta Cropwise confirm that AI-driven crop monitoring scales across tens of millions of hectares globally. The business case holds when the operation is large enough to absorb equipment and subscription costs — roughly 500+ hectares of row crops — and where chemical input costs represent a material share of operating expense. [S1][S4][S8]

## Published Evidence

| Deployment / Source | Published Metric | What It Shows |
|---------------------|------------------|---------------|
| John Deere See & Spray, 2025 season | 5 million acres treated; approximately 50% non-residual herbicide reduction; 31 million gallons of herbicide mix saved | Plant-level weed detection and targeted spraying delivers measurable input savings at commercial scale. [S1] |
| John Deere See & Spray field studies, 2025 | Average yield gain of 2 bushels per acre (upper range 4.8 bu/acre) versus broadcast spraying | Targeted application reduces crop injury from herbicide contact, producing a net yield benefit beyond input savings. [S1] |
| John Deere See & Spray, 2024 season | 59% average herbicide savings across customer base | Consistent savings across multiple growing seasons confirm the durability of the technology, not just a single-season result. [S1] |
| BASF xarvio platform | 130,000+ users, 20 million hectares under management; 250+ annual validation trials | AI crop models combining weather, satellite, and 30 years of agronomic data can deliver field-specific protection recommendations across diverse geographies. [S8] |
| Syngenta Cropwise platform | 100 million hectares monitored across 30+ countries; opened to third-party developers in 2025 | Satellite-based crop monitoring scales globally with broad equipment and advisor ecosystem integration. [S4] |
| Frontiers in Agronomy systematic review, 2026 | Disease detection models achieve 95%+ accuracy for specific diseases; detection 2-3 weeks before visible symptoms | Academic validation that CV-based detection can catch crop diseases significantly earlier than human scouting. [S7] |

## Assumptions And Scenario Model

| Assumption | Value | Basis |
|------------|-------|-------|
| Farm size | 2,000 hectares of row crops (soybeans) | Mid-size commercial operation; large enough to justify equipment investment; representative of precision ag adopters. |
| Baseline herbicide cost | $80-120 per hectare per season (estimated) | Varies by crop, region, and weed pressure; soybean herbicide programs in the US Midwest typically fall in this range. |
| Herbicide reduction rate | 50% of broadcast volume | Published by John Deere across 5 million acres in 2025. Conservative relative to the 59% reported in 2024. [S1] |
| Yield improvement | 2 bushels per acre (estimated $20-24/acre at $10-12/bu soybean prices) | Published average from John Deere field studies. Yield benefit is additive to herbicide savings. [S1] |
| Equipment and subscription cost | $1-5 per acre depending on fallow versus in-crop mode (estimated) | John Deere's per-acre pricing model; alternative is unlimited annual license for high-use operations. [S1][S2] |
| Satellite monitoring cost | Near-zero marginal cost for Sentinel-2 imagery; $2-5 per hectare per season for commercial high-resolution providers (estimated) | Sentinel-2 is freely available from ESA. Commercial providers like Planet charge subscription fees for higher cadence and resolution. |

## Expected Economics

| Factor | Value | Note |
|--------|-------|------|
| **Current herbicide cost** | $160,000-240,000 per season for 2,000 ha | Estimated at $80-120/ha; varies by weed pressure and product choice |
| **Expected herbicide savings** | $80,000-120,000 per season | 50% reduction; published by John Deere at scale [S1] |
| **Expected yield benefit** | $40,000-48,000 per season | 2 bu/acre gain on 2,000 ha at $10-12/bu soybean; published by John Deere [S1] |
| **Technology cost** | $20,000-50,000 per season | Estimated; covers per-acre fees, satellite subscriptions, and maintenance; depends on pricing model |
| **Net annual benefit** | $70,000-118,000 per season | Estimated; herbicide savings plus yield gain minus technology cost |
| **Equipment capital cost** | $150,000-350,000 one-time (if purchasing new precision sprayer) | Estimated; cost depends on whether upgrading existing equipment or purchasing new See & Spray-equipped sprayer |
| **Payback view** | 1.5-4 seasons | Estimated; faster payback for larger operations with higher weed pressure and existing compatible equipment |

## Quality, Risk, And Failure Modes

| Area | Strength / Risk | Control Or Mitigation |
|------|-----------------|-----------------------|
| Detection accuracy for common weeds | Strength: 90%+ accuracy demonstrated on major weed species with 1M+ training images. [S3][S7] | Seasonal revalidation with locally labeled samples; per-species accuracy tracking. |
| Detection of novel or rare weed species | Risk: Models trained on common species may miss or misclassify uncommon weeds not well represented in training data. | Confidence thresholding routes uncertain detections to review; manual scouting covers gaps during the first seasons. |
| Disease detection reliability | Risk: Disease symptoms are more visually variable than weed morphology; early-stage symptoms are subtle. [S7] | Disease detections always route to agronomist review; do not enable automatic treatment for disease without human confirmation. |
| Regional and seasonal model generalization | Risk: Models trained in one geography or season may degrade 12-18% when transferred to different agroecological zones. [S7] | Collect locally labeled data during each deployment; retrain or fine-tune before each growing season. |
| Equipment compatibility and ISOBUS compliance | Strength: ISO 11783 is the established cross-manufacturer standard; prescription maps work across brands. [S6] | Validate ISOXML output on target equipment before field deployment; maintain test harness for at least two equipment brands. |
| Connectivity in rural environments | Risk: Many farms lack reliable broadband; satellite imagery download and model updates require connectivity. | Edge-first architecture minimizes real-time connectivity needs; batch sync satellite data and model updates during available windows. |

## Rollout KPI Set

| KPI | Why It Matters | Pilot Gate |
|-----|----------------|------------|
| Weed detection precision | False positives waste herbicide; too many erode trust and negate savings | >= 90% on target weed species |
| Herbicide volume reduction versus broadcast baseline | The primary economic driver; must be measurable in the first season | >= 30% reduction on pilot fields |
| Yield on treated fields versus broadcast control | Confirms that targeted application does not leave uncontrolled weeds that reduce yield | No statistically significant yield loss versus broadcast; target net gain |
| Prescription map equipment compatibility | ISOXML must load and execute correctly on the pilot sprayer | 100% successful task execution on pilot equipment |
| Agronomist review queue volume | If too many detections route to review, the system creates work instead of saving it | Less than 15% of total detections routed to manual review |

## Open Questions

- How quickly can a detection model trained on one farm's weed population generalize to neighboring farms with different soil types and tillage practices?
- What is the minimum viable training dataset size for a new crop type to achieve the 90% precision threshold needed for automatic spraying?
- How should prescription maps handle field edges and headlands where GPS accuracy degrades and spray overlap risks increase?
- Can satellite-based anomaly detection reliably replace drone scouting for mid-season disease monitoring, or is the 10m Sentinel-2 resolution insufficient for early-stage detection?
- What regulatory changes are needed in jurisdictions that require licensed advisor sign-off before AI-recommended treatments can be applied automatically?
