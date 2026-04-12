---
layout: use-case-detail
title: "References — Autonomous Wildfire Detection and Early Warning"
uc_id: "UC-520"
uc_title: "Autonomous Wildfire Detection and Early Warning"
detail_type: "references"
detail_title: "References"
category: "Industry-Specific"
category_icon: "🔥"
industry: "Emergency Management / Utilities"
complexity: "High"
status: "detailed"
slug: "UC-520-wildfire-detection-early-warning"
permalink: /use-cases/UC-520-wildfire-detection-early-warning/references/
---

## Source Quality Notes

Primary evidence comes from named production deployments: Pano AI (50M+ acres, 15+ utilities), ALERTCalifornia/CAL FIRE (1,200+ cameras statewide), and Hawaiian Electric (78 stations). These are the strongest sources. Pano AI's metrics (735 fires detected, >50% first-known) come from company-published data backed by named utility customers and fire agency partnerships. ALERTCalifornia's 38% pre-911 detection rate is published by UC San Diego and confirmed by the Governor's office. The GAO provides an independent federal assessment of detection technology categories. Economic cost data comes from the U.S. Joint Economic Committee. Satellite-layer evidence (NOAA NGFS, FireSat) is secondary — these systems are pre-operational or early-deployment. Dryad Networks' IoT sensor evidence is based on company press releases with named deployments but limited published performance metrics.

## Source Register

| ID | Type | Source | Why It Was Used | Link |
|----|------|--------|-----------------|------|
| S1 | Primary deployment | Pano AI — company site and deployment data | Core evidence for camera-based AI detection at scale: 50M+ acres, 15+ utilities, 735 fires detected in 2025, 90%+ accuracy with human verification | [Pano AI](https://www.pano.ai) |
| S2 | Primary deployment | ALERTCalifornia — UC San Diego / CAL FIRE camera network | State-scale deployment evidence: 1,200+ cameras, 38% of fires detected before first 911 call | [ALERTCalifornia](https://alertcalifornia.org/) |
| S3 | Primary deployment | Salesforce Ventures — Pano AI profile | Business metrics: $100M+ contracted revenue, 30M+ acres, 1B+ training images, 4 wildfire seasons of data | [How Pano AI Is Building the Front Line of Wildfire Defense](https://salesforceventures.com/perspectives/how-pano-ai-is-building-the-front-line-of-wildfire-defense/) |
| S4 | Primary deployment | Hawaiian Electric — wildfire camera deployment announcement | Concrete cost benchmark: $14M for 78 stations (156 cameras), 50% federally funded, ALERTWest/Digital Path technology | [Hawaiian Electric Wildfire Camera Deployment](https://www.hawaiianelectric.com/hawaiian-electric-deploys-high-resolution-video-cameras-with-artificial-intelligence-for-early-detection-of-wildfires) |
| S5 | Primary deployment | Xcel Energy — Pano AI deployment in Minnesota | Utility deployment evidence: 38 planned camera systems, Colorado test case with fire contained to 3 acres | [Xcel Energy Brings AI-Driven Wildfire Detection to Minnesota](https://newsroom.xcelenergy.com/news/xcel-energy-brings-ai-driven-wildfire-detection-to-minnesota) |
| S6 | Primary deployment | FireSat / Earth Fire Alliance — first wildfire images | Satellite detection layer: 5x5m resolution, prototype launched March 2025, 50+ satellites by 2030, projected $1B+ annual U.S. savings | [FireSat First Wildfire Images](https://www.earthfirealliance.org/press-release/firesat-first-wildfire-images) |
| S7 | Primary deployment | Dryad Networks — 2024 growth press release | IoT sensor deployment evidence: 50+ installations, Thailand and South Africa deals, LoRaWAN gas sensor technology | [Dryad Networks Record Growth in 2024](https://www.businesswire.com/news/home/20250115881322/en/Dryad-Networks-Leads-the-Charge-in-Global-Wildfire-Mitigation-With-Record-Growth-in-2024) |
| S8 | Analysis | GovTech — Pano AI technical profile | Technical architecture details: 60-second camera sweeps, 10 frames per rotation, human verification workflow, 90%+ accuracy claim | [Startup Uses AI, Panoramic Cameras for Wildfire Detection](https://www.govtech.com/public-safety/startup-uses-ai-panoramic-cameras-for-wildfire-detection) |
| S9 | Analysis | U.S. Joint Economic Committee — wildfire economic cost report | Annual U.S. wildfire cost estimate: $394-893 billion including property, health, suppression, and insurance | [Climate-Exacerbated Wildfires Cost Report](https://www.jec.senate.gov/public/index.cfm/democrats/2023/10/climate-exacerbated-wildfires-cost-the-u-s-between-394-to-893-billion-each-year-in-economic-costs-and-damages) |
| S10 | Domain standard | IRWIN — Integrated Reporting of Wildland Fire Information | Federal wildland fire data exchange standard; CAD integration specification; Resources API v9 | [IRWIN on Wildfire.gov](https://www.wildfire.gov/application/irwin-integrated-reporting-wildfire-information) |
| S11 | Official docs | T-Mobile — Pano AI 5G connectivity partnership | 5G backhaul architecture for remote camera stations; rural coverage enabling real-time HD video transmission | [T-Mobile 5G Powers Pano AI Wildfire Detection](https://www.t-mobile.com/news/network/t-mobile-5g-powers-pano-ai-wildfire-detection-system) |
| S12 | Analysis | U.S. GAO — Science & Tech Spotlight: Wildfire Detection Technologies | Independent federal comparison of satellite, camera, IoT sensor, and drone detection modalities with benefits and limitations | [GAO Wildfire Detection Technologies](https://www.gao.gov/products/gao-25-108161) |

## Claim Map

| Claim Or Section | Source IDs |
|------------------|------------|
| 735 fires detected in 2025; >50% first-known alert; 50M+ acres monitored | S1, S3 |
| 90%+ detection accuracy including human verification | S1, S8 |
| 1,200+ cameras across California; 38% of fires detected before 911 | S2 |
| $14M for 78 stations; ~$180K per-station cost benchmark; 50% federally funded | S4 |
| Xcel Energy 38 planned cameras; Colorado fire contained to 3 acres | S5 |
| FireSat 5x5m resolution; prototype March 2025; projected $1B+ annual savings | S6 |
| Dryad Silvanet LoRaWAN gas sensors; 50+ installations worldwide | S7 |
| Camera 60-second sweep cycle; 10 frames per rotation; human watchstander workflow | S8 |
| $394-893 billion annual U.S. wildfire economic cost | S9 |
| IRWIN as federal wildland fire data exchange; CAD integration via Resources API v9 | S10 |
| 5G backhaul for remote camera connectivity; T-Mobile rural coverage | S11 |
| GAO comparison of satellite, camera, sensor modalities; best technology mix still being assessed | S12 |
| Washington DNR: 95% of fires kept below 10 acres over 3 years | S1 |
| 1B+ training images across 4 wildfire seasons; $100M+ contracted revenue | S3 |
| NOAA NGFS detected 19 fires in Oklahoma March 2025; estimated $850M property protected | S12 |
| PG&E bankruptcy driven by $30B in wildfire liabilities | S9 |
