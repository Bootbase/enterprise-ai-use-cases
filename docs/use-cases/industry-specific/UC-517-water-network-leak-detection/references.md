---
layout: use-case-detail
title: "References — Autonomous Water Network Leak Detection and Non-Revenue Water Reduction"
uc_id: "UC-517"
uc_title: "Autonomous Water Network Leak Detection and Non-Revenue Water Reduction"
detail_type: "references"
detail_title: "References"
category: "Industry-Specific"
category_icon: "briefcase"
industry: "Water / Utilities"
complexity: "High"
status: "detailed"
slug: "UC-517-water-network-leak-detection"
permalink: /use-cases/UC-517-water-network-leak-detection/references/
---

## Source Quality Notes

The evidence base for this case study is strong. Three primary deployment case studies (EPCOR, VA SYD, Thames Water) provide published production metrics from named utilities. Northumbrian Water and SES Water add further UK-based deployment evidence. ASTERRA's North Kingstown deployment includes a public municipal review with detailed financials. The Bluefield Research market study provides the US-wide NRW cost baseline. The AWWA M36 manual is the accepted industry standard for water loss accounting. Vendor-origin sources (FIDO, Siemens, ASTERRA) are used for deployment metrics they published about named customer engagements, not for unverified marketing claims.

## Source Register

| ID | Type | Source | Why It Was Used | Link |
|----|------|--------|-----------------|------|
| S1 | Primary deployment | Microsoft — FIDO AI acoustic leak detection (EPCOR, Thames Water, Querétaro) | Core deployment evidence: NRW reduction from 27% to 10% at EPCOR; 4,554 sensors; GPT-4 architecture detail | [Microsoft Source article](https://news.microsoft.com/source/features/sustainability/ai-tool-uses-sound-to-pinpoint-leaky-pipes-saving-precious-drinking-water/) |
| S2 | Primary deployment | Siemens — VA SYD SIWA Leak Finder case study | Flow anomaly detection architecture; NRW reduction from 10% to under 8%; OPC UA integration; 0.5 L/s sensitivity | [Siemens Insights article](https://www.siemens.com/en-us/company/insights/va-syd-water-artificial-intelligence/) |
| S3 | Primary deployment | WaterWorld — Aganova Nautilus deployment in Dublin (Uisce Éireann) | Free-swimming acoustic inspection of trunk mains; 35 km range; sub-meter accuracy; 10,000 km network context | [WaterWorld article](https://www.waterworld.com/smart-water-utility/article/55306670/ai-driven-leak-detection-deploying-smart-technology-in-dublins-critical-water-infrastructure) |
| S4 | Primary deployment | FIDO Tech — Thames Water case study | 92% accuracy; 35,000 files analyzed in 2.5 hours; 13/13 work orders successful | [FIDO case study](https://fido.tech/case-studies/thames-water-leak-team-gets-total-success-from-fido-led-work-orders/) |
| S5 | Primary deployment | SWAN Forum — Northumbrian Water / FIDO case study | 37% leakage reduction across 15 DMAs; 110 leaks; 2.45 Ml/d recovered | [SWAN Forum case study](https://swan-forum.com/case-studies/fido-nwl-case-study/) |
| S6 | Primary deployment | Oldcastle Infrastructure — CivilSense AI Midwest utility case study | AI located leak after three failed prior attempts; $213K/year saved; 350,000 gal/day recovered | [Oldcastle case study](https://oldcastleinfrastructure.com/study/new-ai-leak-detection-saves-water-utility/) |
| S7 | Primary deployment | SUEZ — SES Water satellite leak detection | 24% water loss reduction; 94% non-surfacing leaks; 0.9 Ml/d saved | [SUEZ case study](https://www.suez.com/en/uk/case-studies/suez-satellite-leak-detection-transforms-water-management-for-ses-water) |
| S8 | Primary deployment | North Kingstown, RI — ASTERRA satellite leak detection 2023–2025 review | 50 leaks confirmed; $204K value on $177K cost; 10.4-month payback | [North Kingstown executive summary](https://www.northkingstownri.gov/DocumentCenter/View/12371/Executive-Summary-Report-ASTERRA-Satellite-Leak-Detection-2023-2025-Review) |
| S9 | Analysis | Bluefield Research — US NRW market study | US utilities lose $6.4B/year; 19.5% average NRW; 2.2M miles of pipe; 2.7 trillion gallons lost annually | [Bluefield Research report](https://www.bluefieldresearch.com/ns/water-losses-cost-u-s-utilities-us6-4-billion-annually/) |
| S10 | Domain standard | AWWA — M36 Water Audits and Loss Control Programs (5th edition) | Industry-standard methodology for NRW accounting; defines real loss, apparent loss, and infrastructure leakage index | [AWWA store](https://store.awwa.org/M36-Water-Audits-and-Loss-Control-Programs-Fifth-Edition) |
| S11 | Official docs | US DOE FEMP — Water-Efficient Technology: Distribution System Leak Detection | Cost tiers for detection technologies ($–$$$); deployment guidance for federal facilities | [DOE FEMP page](https://www.energy.gov/femp/water-efficient-technology-opportunity-distribution-system-leak-detection) |

## Claim Map

| Claim Or Section | Source IDs |
|------------------|------------|
| US utilities lose $6.4B/year to NRW; 2.7 trillion gallons; average pipe age 45 years | S9 |
| EPCOR reduced NRW from 27% to ~10% with 4,554 acoustic sensors | S1 |
| FIDO acoustic classifier trained on 1.7M+ audio samples; >92% accuracy | S1, S4 |
| FIDO uses GPT-4 on Azure OpenAI for acoustic signature interpretation | S1 |
| VA SYD reduced NRW from 10% to under 8% using Siemens SIWA Leak Finder | S2 |
| SIWA connects via OPC UA; detects leaks as small as 0.5 L/s | S2 |
| Aganova Nautilus inspects up to 35 km per deployment with sub-meter accuracy | S3 |
| Dublin network loses 30%+ of treated water; 10,000 km of mains | S3 |
| Thames Water trial: 13/13 work orders successful; 35,000 files analyzed in 2.5 hours | S4 |
| Northumbrian Water: 37% leakage reduction across 15 DMAs; 2.45 Ml/d recovered | S5 |
| Midwest utility saved $213K/year; 350,000 gal/day recovered after three prior failed detection attempts | S6 |
| SES Water: 24% water loss reduction; 94% non-surfacing leaks found via satellite | S7 |
| North Kingstown: 50 leaks confirmed; $204K value on $177K cost; 10.4-month payback | S8 |
| AWWA M36 as the standard NRW audit methodology | S10 |
| Detection technology cost tiers ($200–$20,000+) depending on modality | S11 |
| Solution design: DMA-first deployment, multi-modal detection, human-in-the-loop dispatch | S1, S2, S5 (informed by deployment patterns) |
| Implementation guide: batch pipeline architecture; 15–60 min detection cycle | S1, S2, S4 (informed by published operational cadences) |
| Evaluation: payback period 12–18 months (estimated from S8 published 10.4 months and scenario model) | S8, S9 |
