---
layout: use-case-detail
title: "Evaluation — UC-050: Autonomous Adverse Event Report Processing in Pharmacovigilance"
uc_id: "UC-050"
uc_title: "Autonomous Adverse Event Report Processing in Pharmacovigilance"
detail_type: "evaluation"
detail_title: "Evaluation"
category: "Industry-Specific"
status: "detailed"
slug: "uc-050-pharma-adverse-event-processing"
permalink: /use-cases/uc-050-pharma-adverse-event-processing/evaluation/
---

## Evaluation Overview

The public evidence base for AI in pharmacovigilance is uneven. The strongest implementation detail comes from:

- Peer-reviewed feasibility work, especially Pfizer's pilot on AI-assisted case intake
- Vendor case studies with operational metrics, especially Tech Mahindra and ArisGlobal
- Product releases that reveal which sub-problems vendors isolated into separate agents

The right evaluation posture is two-layered:

1. Use published metrics to understand where AI is already working in production or near-production
2. Treat every ROI number for this use case as scenario-based unless the source publishes audited operating data

This document does both. Published metrics stay clearly labeled as published. Financial projections are marked `estimated`.

---

## Baseline (Before AI)

The baseline below uses the existing research brief as the operating assumption set for a sponsor or CRO processing 2,000 ICSRs per month.

| Metric | Value | Source |
|--------|-------|--------|
| **Processing Time** | `2-4 hours/case` | Research brief |
| **Triage Deadline** | `24 hours from awareness` | Research brief |
| **Cost per Case** | `~$132.60 estimated` | `3.0 hours x $44.20/hr` median staff cost |
| **Monthly Labor Cost at 2,000 Cases** | `~$265,200 estimated` | `2,000 x $132.60` |
| **Human FTE Capacity Needed** | `25-50 FTE-months estimated` | `2,000 cases x 2-4 hours` / `160` productive hours/FTE/month |

---

## Published Results (After AI)

| Metric | Before AI | Published AI Result | Change |
|--------|-----------|---------------------|--------|
| **Intake data accuracy** | Manual entry with known inconsistency | `90%` data extraction accuracy (ArisGlobal Advanced Intake) | Major improvement in standardized intake |
| **Cost reduction** | Full manual case intake process | `30-50%` cost reduction (Tech Mahindra) | Material operating leverage if validated locally |
| **Turnaround** | Hours per case | "Hours to minutes" (Tech Mahindra) | Large cycle-time compression |
| **Valid-case rate** | Manual review required for all | `>95%` valid case rate (Tech Mahindra) | Better early routing and intake precision |
| **Compliance timeliness** | Manual queues at risk during surges | `98%` compliance timeliness (Tech Mahindra) | Strong indicator for deadline-sensitive PV operations |
| **Operational capacity** | Roughly `2-4` cases/day per specialist | `150-200` cases/day (Tech Mahindra) | Shows why queue-based AI cells are attractive for spikes |
| **Case extraction feasibility** | Not automated | `0.72-0.74` F1 (Pfizer pilot) | Confirms technical feasibility, but not autonomy |
| **Case validity classification** | Manual intake review | `81%` correct validity prediction (Pfizer pilot) | Good enough to assist routing, not enough to skip review everywhere |

---

## Quality Assessment

### What the AI Already Does Well

| Capability | Evidence | Interpretation |
|------------|----------|----------------|
| **Structured intake from messy source text** | ArisGlobal reports `90%` extraction accuracy; Pfizer's top vendors reached `0.72-0.74` composite F1 | Extraction is mature enough to automate the first pass on routine cases |
| **Case intake routing and prioritization** | Tech Mahindra reports `>95%` valid-case rates and `98%` compliance timeliness | AI is strongest when paired with explicit routing criteria and queueing logic |
| **Scaling routine volume** | Tech Mahindra reports `150-200` cases/day | The clearest value is capacity expansion without linear headcount growth |
| **Translation as a separable workflow** | ArisGlobal productized translation as its own NavaX service | Teams discovered translation is a clean specialization boundary |

### Where the AI Still Struggles

| Capability | Evidence | Why It Matters |
|------------|----------|----------------|
| **Edge-case extraction** | Pfizer notes AE verbatim was among the lowest-scoring entity types | The difficult cases are exactly the ones reviewers care about most |
| **Autonomous case validity** | Best vendor reached `81%` correct valid/invalid case prediction | Good for pre-triage, not for removing controlled review |
| **End-to-end autonomy claims** | Public vendors publish intake and translation metrics, but much less on fully autonomous causality assessment | The market is telling you where confidence is high enough to automate |
| **Cross-case duplicate ambiguity** | Vendors emphasize duplicate matching as a feature, but quality metrics are sparse | Keep duplicate handling behind a review threshold |

---

## Cost Analysis

### Operational Costs

The operating envelope below is `estimated`. Public sources publish percentage gains, not platform invoices, so the numbers are derived from the research brief's 2,000-case monthly scenario.

| Cost Component | Monthly Cost | Notes |
|----------------|-------------|-------|
| **Residual specialist review** | `$90k-$130k estimated` | Assumes the AI removes 50-65% of routine effort but serious and ambiguous cases still route to humans |
| **LLM and AI platform** | `$10k-$20k estimated` | Structured extraction, coding, duplicate review, and narrative generation across the monthly case load |
| **Queue, storage, tracing, retrieval** | `$5k-$12k estimated` | Connectors, search, state persistence, and audit retention |
| **Total Operational** | **`$105k-$162k estimated`** | Consistent with the labor envelope and published efficiency claims |

### ROI Calculation

This is a scenario model, not a vendor promise.

| Factor | Value |
|--------|-------|
| **Previous Cost (monthly)** | `$265,200 estimated` from the brief's median labor assumptions |
| **AI Solution Cost (monthly)** | `$105k-$162k estimated` |
| **Net Savings (monthly)** | `$103k-$160k estimated` |
| **Implementation Cost** | `$500k-$750k estimated` for integration, validation package, gold-set creation, and rollout |
| **Payback Period** | `~3-7 months estimated` |

---

## Lessons Learned

### What Worked Well

- Specialized workers beat broad prompts. Tech Mahindra describes a multi-agent architecture, and ArisGlobal is productizing separate intake, translation, and orchestration agents.
- Translation is a strong automation boundary. Teams found this task clean enough to isolate as a dedicated service.
- Schema-first extraction is the stabilizer. Azure's structured outputs map exactly to the need for repeatable intake packets and QC checklists.
- Human review remains a feature, not a fallback. LangGraph's interrupts are a good technical match for the way PV reviewers already work.

### What Didn't Work

- One score does not describe PV quality. Pfizer's pilot shows why: good composite F1 still hid weaker performance on specific entities.
- "Autonomous end-to-end PV" is usually overstated in public materials. Published numbers focus on intake throughput, translation, and efficiency.
- Over-broad tool access is counterproductive. The more the model can do in one loop, the harder the system becomes to validate.

---

## Next Steps

| Priority | Action | Expected Impact |
|----------|--------|-----------------|
| High | Run a sponsor-owned pilot on `500-1,000` routine cases with full gold-set scoring | Validates touchless rate and extraction quality on real portfolio data |
| High | Implement serious-case interrupt and reviewer resume flow first | Makes the system safe enough to trial in a regulated environment |
| Medium | Add dedicated translation and duplicate-review workers | Improves multilingual handling and reviewer efficiency |
| Medium | Capture reviewer edits and feed them back into evaluation sets | Improves calibration without promising unsupervised learning in production |
| Low | Expand from one safety platform seam to additional connectors | Reuse the same AI core across Veeva, ArisGlobal, or Argus estates |
