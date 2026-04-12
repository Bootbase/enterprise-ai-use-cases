---
layout: use-case-detail
title: "Evaluation — Autonomous Water Network Leak Detection and Non-Revenue Water Reduction"
uc_id: "UC-517"
uc_title: "Autonomous Water Network Leak Detection and Non-Revenue Water Reduction"
detail_type: "evaluation"
detail_title: "Evaluation"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Water / Utilities"
complexity: "High"
status: "detailed"
slug: "UC-517-water-network-leak-detection"
permalink: /use-cases/UC-517-water-network-leak-detection/evaluation/
---

## Decision Summary

The evidence for AI-driven water leak detection is strong. Multiple named utilities have deployed production systems and published measurable NRW reductions — EPCOR cut NRW from 27% to roughly 10%, VA SYD reduced NRW from 10% to under 8%, and Northumbrian Water achieved a 37% leakage reduction across 15 targeted DMAs. The technology works across acoustic, flow-based, and satellite modalities. The business case holds when a utility's NRW exceeds approximately 15% and sensor infrastructure investment can be recovered within 3–5 years from reduced water production costs. Utilities below 10% NRW will see diminishing returns unless regulatory pressure mandates further reduction.

## Published Evidence

| Deployment / Source | Published Metric | What It Shows |
|---------------------|------------------|---------------|
| EPCOR / FIDO Tech (San Tan Valley, AZ) | NRW reduced from 27% to ~10%; 250+ leaks found in year one across 4,554 sensors | Acoustic AI at scale delivers major NRW reduction in a US distribution network |
| VA SYD / Siemens SIWA (Malmö, Sweden) | NRW reduced from 10% to under 8%; detects leaks as small as 0.5 L/s | Flow anomaly AI works even in already-efficient networks; effective on low-loss-rate leaks |
| Thames Water / FIDO (London, UK) | 92% classification accuracy; 13 of 13 FIDO-led work orders resulted in successful digs | AI-directed work orders eliminate wasted excavations; 100% field success rate in this trial |
| Northumbrian Water / FIDO (UK) | 37% average leakage reduction across 15 DMAs; 110 leaks located; 2.45 Ml/d total reduction | Acoustic AI scales across multiple DMAs with consistent results |
| SES Water / ASTERRA (UK) | 24% water loss reduction; 94% of leaks found were non-surfacing; 0.9 Ml/d saved | Satellite SAR detects leaks invisible from the surface — a different detection modality that complements acoustics |
| North Kingstown, RI / ASTERRA | 50 leaks confirmed (44 utility-side); $204K value on $177K investment; 10.4-month payback | Satellite approach delivers positive ROI within one year even for a small municipal utility |

## Assumptions And Scenario Model

The following model represents a mid-size US utility. Published metrics are noted; other values are estimated from industry data.

| Assumption | Value | Basis |
|------------|-------|-------|
| Service population | 250,000 customers | Mid-size utility; representative of US municipal water systems |
| Distribution network length | 3,000 km (1,860 mi) | Estimated from industry average of ~12 km per 1,000 connections |
| Current NRW rate | 22% | US average is 19.5% (published, Bluefield Research); adjusted upward for aging infrastructure |
| Water production cost | $3.50 per 1,000 gallons | Estimated; varies by region ($2–$6 typical range) |
| Annual water loss volume | ~1.2 billion gallons | Derived from NRW rate and estimated system input volume |
| Sensor deployment density | 1 acoustic sensor per 500 m of pipe in high-loss DMAs | Consistent with FIDO deployments; EPCOR deployed 4,554 sensors across 160 sq mi |
| Target NRW after full deployment | 12% (from 22%) | Conservative; EPCOR achieved ~10%, but starting from a higher baseline |

## Expected Economics

| Factor | Value | Note |
|--------|-------|------|
| **Current annual NRW cost** | ~$4.2M | Estimated: 1.2B gallons × $3.50/1,000 gal |
| **Target annual NRW cost** | ~$2.3M | Estimated: NRW reduced from 22% to 12%, proportional cost reduction |
| **Expected annual benefit** | ~$1.9M in recovered water revenue | Estimated; does not include avoided emergency break costs ($50K–$500K per incident) or deferred capital replacement |
| **Sensor infrastructure cost** | $1.5M–$2.5M (one-time) | Estimated: acoustic sensors at ~$200–$400 per unit for high-loss DMAs plus DMA flow meters; phased deployment reduces upfront capital |
| **Annual platform + maintenance** | $300K–$500K | Estimated: SaaS analytics license, sensor battery replacement, cellular connectivity, model retraining |
| **Payback period** | 12–18 months | Estimated; North Kingstown published 10.4-month payback on satellite alone; combined acoustic+flow should perform similarly or better |

## Quality, Risk, And Failure Modes

| Area | Strength / Risk | Control Or Mitigation |
|------|-----------------|-----------------------|
| **Detection accuracy** | Strength: 92%+ classification accuracy published by FIDO across multiple deployments | Periodic retraining on local confirmed repair data; monitor rolling accuracy and alert on degradation |
| **Plastic pipe detection** | Risk: acoustic sensors transmit poorly on PVC/PE pipes, which make up 30–40% of many networks | Mitigate with DMA flow balance as a second detection layer; satellite SAR is pipe-material-agnostic |
| **Sensor coverage gaps** | Risk: battery failure, vandalism, or connectivity loss creates blind spots | Heartbeat monitoring with 4-hour staleness alerts; redundant detection via DMA flow analysis |
| **False positives** | Risk: environmental noise (traffic, pumps, construction) can mimic leak signatures | Two-stage confirmation (AI + operator review) before dispatch; FIDO's noise filtering reduces false triggers |
| **Regulatory acceptance** | Strength: AWWA M36 methodology is the accepted audit framework; AI estimates supplement but do not replace the annual water audit | Cross-check AI NRW estimates against M36 audit results annually |
| **Vendor lock-in** | Risk: proprietary sensor formats and analytics platforms may limit future flexibility | Normalize sensor data at ingestion layer; contractually require data export in open formats |

## Rollout KPI Set

| KPI | Why It Matters | Pilot Gate |
|-----|----------------|------------|
| **NRW reduction (%)** | Primary outcome measure; directly tied to revenue recovery | ≥ 15% reduction in pilot DMAs within 6 months |
| **Leak detection precision** | High precision prevents wasted excavations and crew time | ≥ 90% of dispatched work orders find a confirmed leak |
| **Mean time to detection** | Faster detection means shorter leak run times and less water lost | Median detection within 72 hours of leak onset |
| **Sensor fleet uptime** | Blind spots undermine the continuous monitoring promise | ≥ 95% of deployed sensors reporting within expected interval |
| **Work order cycle time** | Measures end-to-end efficiency from detection to repair completion | Median 5 business days from alert to repair confirmation |
| **Cost per confirmed leak** | Validates that AI-directed detection is cheaper than manual survey campaigns | ≤ $500 per confirmed leak (vs. $1,000–$2,000 for traditional acoustic survey) |

## Open Questions

- How does acoustic classifier accuracy degrade on networks with predominantly plastic pipes, and at what plastic-pipe percentage should utilities default to flow-only detection?
- What is the optimal sensor density for networks of different ages and materials — is one sensor per 500 m sufficient for cast-iron networks but too sparse for PVC?
- Can satellite SAR detection replace acoustic sensors for trunk mains entirely, or does the 6–8 week satellite revisit cycle leave too large a gap for high-criticality pipes?
- How should utilities handle the capital funding gap for sensor infrastructure in rate-regulated environments — should sensor costs be treated as operational expense (SaaS model) or capitalized?
- What retraining frequency keeps the acoustic model accurate as the network's pipe inventory changes through replacement programs?
