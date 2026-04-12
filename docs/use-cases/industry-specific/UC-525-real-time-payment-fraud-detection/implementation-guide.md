---
layout: use-case-detail
title: "Implementation Guide — Autonomous Real-Time Payment Fraud Detection"
uc_id: "UC-525"
uc_title: "Autonomous Real-Time Payment Fraud Detection"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Industry-Specific"
category_icon: "shield"
industry: "Banking / Payments"
complexity: "High"
status: "detailed"
slug: "UC-525-real-time-payment-fraud-detection"
permalink: /use-cases/UC-525-real-time-payment-fraud-detection/implementation-guide/
---

## Build Goal

Build a real-time ML scoring service that evaluates every payment authorization request against behavioral and network features, returns a risk score with reason codes within 50 ms, and routes ambiguous cases to analyst review. The first production release covers card-present and card-not-present transactions for a single issuer portfolio. Cross-channel unification (P2P, real-time payments) and consortium intelligence integration follow in later phases.

## Reference Stack

| Layer | Recommended Choice | Reason |
|-------|--------------------|--------|
| **Application runtime** | Python 3.11+ (training pipeline), C++/Rust gRPC service (inference) | Python for data science ergonomics; compiled inference service for sub-millisecond model evaluation |
| **Model access** | XGBoost (tabular scoring) + PyTorch Geometric (GNN embeddings) | XGBoost is the industry default for production fraud scoring; PyG handles graph-based relational features |
| **Orchestration runtime** | Apache Kafka + Apache Flink | Kafka for durable event streaming; Flink for stateful feature aggregation with exactly-once semantics |
| **Core connectors** | Redis Cluster (feature store), PostgreSQL (case management), ISO 8583 adapter (auth host integration) | Redis for microsecond feature reads; PostgreSQL for analyst workflow state; ISO adapter for card-network compatibility |
| **Evaluation / tracing** | MLflow (experiment tracking, model registry), Prometheus + Grafana (runtime metrics), OpenTelemetry (distributed tracing) | MLflow manages champion/challenger lifecycle; Prometheus tracks scoring latency and throughput; OTel traces end-to-end authorization path |

## Delivery Plan

| Phase | Outcome | Main Deliverables |
|-------|---------|-------------------|
| 1 — Feature foundation (6 weeks) | Streaming pipeline ingests transaction events and populates feature store with cardholder profiles and velocity aggregates | Kafka topics, Flink jobs for rolling aggregates (1h/24h/7d/30d windows), Redis feature store schema, backfill from historical data |
| 2 — Model development (8 weeks) | Trained XGBoost model scoring above 90% detection rate at <2% false-positive rate on holdout set | Feature engineering (200+ features), class-imbalance handling (SMOTE + undersampling), hyperparameter tuning, offline evaluation report |
| 3 — Scoring service + auth integration (6 weeks) | Scoring service deployed inline in authorization path, returning scores within 50 ms p99 | gRPC scoring service, ISO 8583 adapter, active-active deployment, deterministic fallback rules, load testing at 2x peak TPS |
| 4 — Pilot + case management (4 weeks) | Shadow scoring on live traffic, then controlled rollout with analyst review loop | Case management integration, analyst feedback pipeline, champion/challenger framework, go-live on 10% of card portfolio |

## Core Contracts

### State And Output Schemas

The scoring service accepts a feature vector and returns a risk assessment. The contract is kept minimal to reduce serialization overhead in the authorization path.

```python
from pydantic import BaseModel

class ScoringRequest(BaseModel):
    transaction_id: str
    card_token: str           # tokenized PAN, never raw card number
    merchant_id: str
    amount_cents: int
    currency: str
    channel: str              # "card_present" | "ecommerce" | "p2p"
    device_fingerprint: str | None
    timestamp_utc: str

class ReasonCode(BaseModel):
    feature: str              # e.g. "velocity_24h", "merchant_risk"
    contribution: float       # SHAP value or equivalent
    direction: str            # "increases_risk" | "decreases_risk"

class ScoringResponse(BaseModel):
    transaction_id: str
    risk_score: float         # 0.0 (safe) to 1.0 (fraud)
    decision: str             # "approve" | "decline" | "review"
    reason_codes: list[ReasonCode]  # top 5 contributing features
    model_version: str
    latency_ms: float
```

### Tool Interface Pattern

The scoring service exposes a single gRPC endpoint. The auth host calls it synchronously within the authorization window. No other system calls the scoring service directly during authorization.

```python
# Simplified inference handler — production version compiled to C++/Rust
import xgboost as xgb
import redis
import time

def score_transaction(request: ScoringRequest, model: xgb.Booster,
                      feature_store: redis.Redis) -> ScoringResponse:
    start = time.monotonic()

    # 1. Fetch precomputed features from Redis (<1 ms)
    features = feature_store.hgetall(f"profile:{request.card_token}")
    feature_vector = build_feature_vector(request, features)

    # 2. Score with XGBoost (<5 ms)
    dmatrix = xgb.DMatrix(feature_vector)
    score = float(model.predict(dmatrix)[0])

    # 3. Compute SHAP reason codes (<10 ms)
    reason_codes = compute_shap_reasons(model, dmatrix, top_k=5)

    # 4. Apply threshold bands
    decision = apply_thresholds(score)  # configurable per portfolio

    elapsed = (time.monotonic() - start) * 1000
    return ScoringResponse(
        transaction_id=request.transaction_id,
        risk_score=score,
        decision=decision,
        reason_codes=reason_codes,
        model_version=model.version,
        latency_ms=elapsed,
    )
```

## Orchestration Outline

The control flow has two speeds: the synchronous authorization path (under 50 ms) and the asynchronous enrichment path (seconds to minutes).

**Authorization path:** Auth host receives ISO 8583 message, extracts transaction fields, calls scoring service via gRPC, receives score + decision, applies to authorization response. If the scoring service is unreachable within 20 ms timeout, the auth host falls back to deterministic rules.

**Enrichment path:** Every settled transaction is published to Kafka. Flink jobs update cardholder velocity profiles, merchant risk scores, and device reputation in the feature store. Confirmed fraud labels (from chargebacks, analyst decisions, or cardholder reports) flow back into the training pipeline.

```python
# Flink-style pseudocode for velocity feature updates
from pyflink.datastream import StreamExecutionEnvironment

env = StreamExecutionEnvironment.get_execution_environment()

transactions = env.add_source(kafka_consumer("transactions"))

# Compute rolling velocity aggregates per cardholder
velocity_updates = (
    transactions
    .key_by(lambda txn: txn.card_token)
    .window(TumblingEventTimeWindows.of(Time.hours(1)))
    .aggregate(VelocityAggregator())  # count, sum, avg amount, unique merchants
)

# Write updated profiles to Redis feature store
velocity_updates.add_sink(redis_sink("profile:{card_token}"))
```

## Prompt And Guardrail Pattern

This is an ML scoring system, not an LLM application. The equivalent of prompt design is the feature engineering and threshold configuration that govern model behavior.

```text
# Scoring configuration — controls model behavior without code changes

[thresholds]
approve_below = 0.15       # auto-approve if score < 0.15
decline_above = 0.85       # auto-decline if score > 0.85
review_band = [0.15, 0.85] # route to analyst queue

[guardrails]
max_auto_decline_amount_cents = 500000  # $5,000: above this, always review
high_value_merchant_categories = ["6012", "6051", "7995"]  # MCC codes requiring extra scrutiny
new_card_cooling_period_hours = 48     # stricter thresholds for cards active < 48h
fallback_on_timeout = "rules_engine"   # deterministic rules if scoring unavailable

[explainability]
min_reason_codes = 3       # every decision includes at least 3 contributing features
shap_method = "tree"       # TreeSHAP for XGBoost; fast enough for inline computation
```

Guardrail logic is deterministic and runs after the ML score. The model does not override these constraints. Amount limits, MCC-based rules, and cooling periods are enforced by the auth host regardless of the model score.

## Integration Notes

| Integration Area | What To Build | Implementation Note |
|------------------|---------------|---------------------|
| **ISO 8583 auth adapter** | Adapter that extracts transaction fields from ISO 8583 messages into the scoring request schema | Must handle all message variants (0100/0200 authorization, 0400 reversal); latency budget for adapter: under 5 ms |
| **Feature store write path** | Flink jobs that update cardholder, merchant, and device profiles on every settled transaction | Use exactly-once semantics; backfill from 12+ months of historical transactions before go-live |
| **Case management push** | REST adapter that sends enriched case objects (score, reasons, cardholder history, transaction context) to the analyst queue | Pre-assemble all context the analyst needs; reduce analyst handle time by eliminating manual data gathering |
| **Label feedback loop** | Pipeline that ingests confirmed fraud labels (chargebacks, analyst decisions, cardholder reports) and maps them to original transactions | Label latency varies: chargebacks arrive 30-90 days post-transaction; analyst labels within hours; design for late-arriving labels |

## Evaluation Harness

| Area To Test | How To Measure It | Release Gate |
|--------------|-------------------|--------------|
| **Fraud detection rate** | Precision and recall on labeled holdout set (90-day window); track by channel (card-present, ecommerce, P2P) | Recall >= 90% at precision >= 50% (matches FICO/Featurespace production benchmarks) |
| **False decline rate** | Measure legitimate transactions scored above decline threshold; compare against rule-engine baseline | False-positive rate reduced by >= 40% vs. rules baseline before full rollout |
| **Scoring latency** | p50, p95, p99 latency measured at the scoring service boundary; end-to-end authorization latency measured at auth host | p99 scoring latency <= 50 ms; no measurable increase in end-to-end authorization time |
| **Model stability** | Population Stability Index (PSI) on score distribution; monitored daily | PSI < 0.1 (stable); alert at 0.1; automatic champion/challenger trigger at 0.2 |
| **Explainability coverage** | Percentage of decline decisions with >= 3 valid reason codes | 100% of declines include reason codes that map to customer-facing messages |

## Deployment Notes

| Topic | Guidance |
|-------|----------|
| **Rollout approach** | Start with shadow scoring (score every transaction but do not act on scores) for 2 weeks to validate accuracy against production outcomes. Then controlled rollout: 10% of portfolio, then 50%, then 100%. Each stage requires fraud ops sign-off on detection rate and false-decline metrics |
| **Fallback path** | If scoring service latency exceeds 20 ms timeout or service is unreachable, auth host activates deterministic rule engine. Rules are maintained in parallel during the first 6 months of ML operation. Rollback to full rule-based operation is a config change, not a code deployment |
| **Observability** | Dashboard: scoring latency (p50/p95/p99), throughput (TPS), score distribution histogram, false-positive rate (rolling 24h), model version in production. Alerts: latency breach, throughput drop, score distribution shift (PSI > 0.1), feature store staleness |
| **Operations ownership** | Fraud operations owns threshold tuning and analyst workflow. ML engineering owns model training, deployment, and monitoring. Platform engineering owns Kafka/Flink/Redis infrastructure. All three teams participate in weekly model performance review |
