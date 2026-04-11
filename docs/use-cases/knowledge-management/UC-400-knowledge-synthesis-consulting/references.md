---
layout: use-case-detail
title: "References — Autonomous Knowledge Synthesis and Research Copilot for Management Consultants with Agentic AI"
uc_id: "UC-400"
uc_title: "Autonomous Knowledge Synthesis and Research Copilot for Management Consultants with Agentic AI"
detail_type: "references"
detail_title: "References"
category: "Knowledge Management"
category_icon: "book-open"
industry: "Professional Services (Management Consulting, Strategy, Audit & Advisory)"
complexity: "High"
status: "detailed"
slug: "UC-400-knowledge-synthesis-consulting"
permalink: /use-cases/UC-400-knowledge-synthesis-consulting/references/
---

## Source Quality Notes

The evidence base for this use case is unusually strong. Two sources stand out: McKinsey's own published metrics for Lilli (S1, S2) are first-party production data from a 43,000-employee deployment, and the Harvard-BCG experiment (S3) is a pre-registered randomized controlled trial with 758 participants — rare rigor for an enterprise AI study. The McKinsey Agents at Scale materials (S9, S10) are vendor-published but contain specific architectural detail. BCG's adoption and Deckster metrics (S6) come from executive interviews reported by Computerworld, a credible trade publication. The Bain and Deloitte sources (S7, S8) provide deployment context but lack published productivity metrics. The VentureBeat article (S12) is a technology-press report with direct McKinsey quotes on architecture choices. Where a claim relies on secondary analysis or derived calculation rather than a primary source, the other files note this explicitly.

## Source Register

| ID | Type | Source | Why It Was Used | Link |
|----|------|--------|-----------------|------|
| S1 | Primary deployment | McKinsey — "Meet Lilli, our generative AI tool" | Firmwide launch timeline, adoption metrics (72% active, 30% time savings), and feature description. | [McKinsey Blog](https://www.mckinsey.com/about-us/new-at-mckinsey-blog/meet-lilli-our-generative-ai-tool) |
| S2 | Primary deployment | McKinsey — "Rewiring the way McKinsey works with Lilli" | Detailed adoption metrics, 500,000+ monthly prompts, 40+ knowledge sources, and retrieval architecture overview. | [McKinsey Tech & AI](https://www.mckinsey.com/capabilities/tech-and-ai/how-we-help-clients/rewiring-the-way-mckinsey-works-with-lilli) |
| S3 | Academic research | Dell'Acqua et al. — "Navigating the Jagged Technological Frontier" (HBS Working Paper 24-013) | Randomized field experiment with 758 BCG consultants. Key findings: +12.2% tasks, 25.1% faster, 40%+ quality on inside-frontier tasks; 19pp accuracy drop on outside-frontier tasks. | [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4573321) |
| S4 | Analysis | Ethan Mollick — "Centaurs and Cyborgs on the Jagged Frontier" | Accessible summary of the Harvard-BCG experiment findings, including the centaur/cyborg collaboration patterns and skill-leveling effect. | [One Useful Thing](https://www.oneusefulthing.org/p/centaurs-and-cyborgs-on-the-jagged) |
| S6 | Analysis | Computerworld — "BCG execs: AI across the company increased productivity, 'employee joy'" | BCG adoption metrics (90% use AI, 50% daily), Deckster usage (450,000+ slide operations, 40% weekly associate adoption), custom GPT count (6,000+), and reinvestment of saved time. | [Computerworld](https://www.computerworld.com/article/3491334/bcg-execs-ai-across-the-company-increased-productivity-employee-joy.html) |
| S7 | Primary deployment | Bain & Company — "Bain makes pioneering deployments of state-of-the-art AI tools worldwide" | Bain Sage platform description, 12 GenAI tools deployed, 18,500 employees across 67 cities, OpenAI partnership. | [Bain Press Release](https://www.bain.com/about/media-center/press-releases/2023/bain--company-makes-pioneering-deployments-of-state-of-the-art-ai-tools-worldwide/) |
| S8 | Analysis | Consultancy.uk — "Deloitte rolls out generative AI tool PairD to EMEA employees" | Deloitte PairD launch timeline (UK pilot Oct 2023, EMEA rollout Dec 2023), 75,000 employees, internally developed, mandatory training requirement. | [Consultancy.uk](https://www.consultancy.uk/news/36277/deloitte-rolls-out-generative-ai-tool-paird-to-emea-employees) |
| S9 | Primary deployment | McKinsey — "Introducing our agents at scale product suite" (VivaTech 2025) | Agent marketplace concept, Agentic AI Mesh architecture announcement, and agent governance model. | [McKinsey Blog](https://www.mckinsey.com/about-us/new-at-mckinsey-blog/mckinsey-at-vivatech-introducing-our-agents-at-scale-product-suite) |
| S10 | Technical documentation | QuantumBlack — "How we enabled Agents at Scale with the Agentic AI Mesh" | Detailed architecture of the Agentic AI Mesh: six capabilities (agent discovery, AI asset registry, observability, auth, evaluations, fine-tuning), OpenTelemetry tracing, and governance approach. | [Medium / QuantumBlack](https://medium.com/quantumblack/how-we-enabled-agents-at-scale-in-the-enterprise-with-the-agentic-ai-mesh-baf4290daf48) |
| S11 | Primary deployment | McKinsey — "What McKinsey learned while creating its generative AI platform" | Architecture details: Cohere embeddings, OpenAI GPT-4 via Azure, LLM-agnostic design, multi-model routing, and lessons from building the platform. | [McKinsey Insights](https://www.mckinsey.com/capabilities/tech-and-ai/our-insights/what-mckinsey-learned-while-creating-its-generative-ai-platform) |
| S12 | Analysis | VentureBeat — "Consulting giant McKinsey unveils its own generative AI tool for employees: Lilli" | Technology choices (Cohere + OpenAI on Azure), retrieval mechanism (5–7 relevant artifacts per query), and security architecture. | [VentureBeat](https://venturebeat.com/ai/consulting-giant-mckinsey-unveils-its-own-generative-ai-tool-for-employees-lilli) |
| S13 | Academic research | BCG Henderson Institute — "Generative AI Instantly Elevates the Aptitude of Knowledge Workers" (2024) | Follow-up experiment with 480 BCG consultants: 49pp improvement on coding tasks with AI, but no knowledge retention. AI augments performance without building lasting skill. | [BCG Press Release](https://www.bcg.com/press/5september2024-generative-ai-knowledge-workers-consultants) |

## Claim Map

| Claim Or Section | Source IDs |
|------------------|------------|
| McKinsey Lilli adoption: 75% of ~43,000 employees active monthly, 500,000+ prompts/month | S1, S2 |
| 30% time savings in searching and synthesizing knowledge | S1, S2 |
| Lilli retrieves 5–7 most relevant artifacts with citations per query | S1, S12 |
| Lilli architecture: Cohere embeddings + OpenAI GPT-4 via Azure, LLM-agnostic design | S11, S12 |
| Harvard-BCG experiment: 758 consultants, +12.2% tasks, 25.1% faster, 40%+ quality | S3, S4 |
| Outside-frontier accuracy drop: 84.5% (no AI) → ~65% (with AI) | S3, S4 |
| Skill-leveling effect: lower performers gained 43%, top performers gained 17% | S3, S4 |
| Jagged frontier concept and automation bias risk | S3, S4 |
| BCG follow-up: 480 consultants, 49pp coding improvement, no knowledge retention | S13 |
| BCG Deckster: 450,000+ slide operations, 40% weekly associate adoption | S6 |
| BCG adoption: 90% use AI, 50% daily, 70% reinvested in client work | S6 |
| Bain Sage platform: 12 GenAI tools, 18,500 employees, OpenAI partnership | S7 |
| Deloitte PairD: 75,000 employees in EMEA, internally developed, Oct-Dec 2023 rollout | S8 |
| Agentic AI Mesh architecture: six capabilities, agent registry, OpenTelemetry | S9, S10 |
| Agent marketplace concept: distributed ownership with centralized compliance | S9, S10 |
| Multi-model routing and LLM-agnostic platform design | S11, S12 |
| Mandatory human review recommendation based on outside-frontier accuracy risk | S3, S4 |
| Scenario model: $250/hour consultant cost, 15 hours/week research time | S1, S2 (30% time figure); cost range is industry standard |
| Implementation cost estimate: $2–4M for Phase 1–4 | Design recommendation, not published |
