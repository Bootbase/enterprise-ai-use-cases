---
layout: use-case-detail
title: "Implementation Guide — Autonomous Freight Logistics Orchestration with Agentic AI"
uc_id: "UC-020"
uc_title: "Autonomous Freight Logistics Orchestration with Agentic AI"
detail_type: "implementation-guide"
detail_title: "Implementation Guide"
category: "Workflow Automation"
status: "detailed"
slug: "uc-020-freight-logistics-automation"
permalink: /use-cases/uc-020-freight-logistics-automation/implementation-guide/
---

## Prerequisites

| Prerequisite | Detail |
|--------------|--------|
| **Azure Subscription** | Azure OpenAI deployment with GPT-4o (structured outputs), Azure Service Bus, Azure Container Apps or AKS. |
| **TMS Access** | API credentials for the target TMS (Navisphere, MercuryGate, or BluJay) with read/write permissions for shipments, orders, appointments, and tracking. |
| **NMFC Classification Data** | Licensed access to the National Motor Freight Classification tariff, exposed through an internal lookup API. |
| **Email Access** | Microsoft Graph API or IMAP credentials for the inbound logistics email inbox. |
| **Dev Environment** | Python 3.11+, `openai`, `langgraph`, `pydantic`, `aiohttp`, `tenacity`, `azure-servicebus`. |

---

## Project Structure

```text
freight-agents/
├── src/
│   ├── agents/
│   │   ├── email_classifier.py        # Classifies inbound emails by transaction type
│   │   ├── quote_extractor.py         # Extracts shipment data from quote requests
│   │   ├── order_parser.py            # Parses emailed tenders into structured orders
│   │   ├── freight_classifier.py      # NMFC classification with tool-calling
│   │   ├── carrier_matcher.py         # Carrier selection logic
│   │   ├── tracking_agent.py          # Tracking status retrieval and updates
│   │   └── missed_pickup.py           # Dual-agent missed pickup resolution
│   ├── tools/
│   │   ├── tms.py                     # TMS connector (Navisphere / MercuryGate API)
│   │   ├── nmfc.py                    # NMFC classification lookup
│   │   ├── pricing.py                 # Dynamic Pricing Engine client
│   │   ├── carrier_capacity.py        # Real-time capacity center API
│   │   └── voice.py                   # Voice AI outreach (Azure Communication Services)
│   ├── prompts/
│   │   ├── email_classifier.txt
│   │   ├── quote_extractor.txt
│   │   ├── order_parser.txt
│   │   ├── freight_classifier.txt
│   │   └── missed_pickup_decider.txt
│   ├── models/
│   │   ├── shipment.py                # Pydantic schemas for shipment data
│   │   ├── quote.py                   # Quote request/response schemas
│   │   └── tracking.py               # Tracking update schemas
│   ├── workers/
│   │   ├── quote_worker.py            # Service Bus consumer for quote flow
│   │   ├── order_worker.py            # Service Bus consumer for order flow
│   │   └── exception_worker.py        # Service Bus consumer for exception flow
│   └── eval/
│       ├── score_extraction.py        # Extraction accuracy scoring
│       ├── score_classification.py    # NMFC classification accuracy
│       └── score_quotes.py            # Quote accuracy vs. manual baseline
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evaluation/
└── README.md
```

The important boundary is between LLM agents that read, reason, and classify, and deterministic tools that price, book, schedule, and transmit. That split is what keeps the system auditable and the agents replaceable.

---

## Step-by-Step Implementation

### Phase 1: Foundation

#### Step 1.1: Define the extraction contracts first

Do this before writing any prompt. The extraction schema is the real API between the LLM and the rest of the system.

```python
from typing import Literal
from pydantic import BaseModel, Field


class Location(BaseModel):
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    facility_name: str | None = None
    country: str = "US"


class QuoteRequest(BaseModel):
    origin: Location
    destination: Location
    pickup_date: str | None = None
    delivery_date: str | None = None
    weight_lbs: float | None = None
    commodity_description: str
    equipment_type: Literal["van", "reefer", "flatbed", "other"] | None = None
    mode_preference: Literal["truckload", "ltl", "both"] | None = None
    special_requirements: list[str] = Field(default_factory=list)
    hazmat: bool = False
    confidence: float = Field(ge=0.0, le=1.0)
    requires_review: bool = False
    raw_email_excerpt: str = Field(description="Key excerpt from source email for audit trail")
```

This contract is the contract with the rest of the system. The LLM must return valid JSON matching this schema, or the extraction fails.

#### Step 1.2: Build the email classifier first

The email classifier is the ingestion router. It must be fast and accurate.

```python
from openai import AzureOpenAI
from pydantic import BaseModel, Field


class EmailClassification(BaseModel):
    transaction_type: str = Field(description="quote|order|tracking|capacity")
    confidence: float = Field(ge=0.0, le=1.0)
    sender_domain: str
    is_urgent: bool


async def classify_email(email_body: str, subject: str) -> EmailClassification:
    client = AzureOpenAI()
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are a freight logistics email classifier. Classify inbound emails as:
- quote: Customer requesting a price quote for freight
- order: Customer placing an order (tender) for freight pickup
- tracking: Customer asking for shipment status/tracking
- capacity: Carrier offering truck capacity/posting loads

Be conservative with confidence scores. If you're unsure, set confidence < 0.8.""",
            },
            {"role": "user", "content": f"Subject: {subject}\n\n{email_body}"},
        ],
        response_format=EmailClassification,
    )
    return response.choices[0].message.parsed
```

#### Step 1.3: Build deterministic tools before agents

The TMS connector, NMFC lookup, and pricing engine are deterministic. Build and test these first.

```python
# tools/tms.py - Example TMS connector (Navisphere)
import aiohttp
from typing import Optional


class NavisphereConnector:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key

    async def create_booking(self, shipment: dict) -> dict:
        """Create a booking in Navisphere. Returns booking ID."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/bookings",
                json=shipment,
                headers=headers,
            ) as resp:
                return await resp.json()

    async def get_carrier_availability(self, origin: str, destination: str) -> list:
        """Query available carriers for a lane."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/carriers/available",
                params={"origin": origin, "destination": destination},
                headers=headers,
            ) as resp:
                return await resp.json()
```

#### Step 1.4: Build the first agent: Quote Extractor

Start with the highest-volume, highest-ROI agent.

```python
# agents/quote_extractor.py
import json
from openai import AzureOpenAI
from models.quote import QuoteRequest


async def extract_quote_request(email_body: str, attachments: list = None) -> QuoteRequest:
    """Extract a quote request from an email."""
    client = AzureOpenAI()

    # For high-volume, use structured outputs for guaranteed valid JSON
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are a freight logistics specialist. Extract shipping details from customer emails.
                
Be conservative with confidence scores:
- 0.95+: Clear, unambiguous
- 0.85-0.95: Minor clarifications might be needed
- 0.70-0.85: Significant assumptions made
- <0.70: Set requires_review=true

If any required field is missing or unclear, set confidence lower and set requires_review=true.""",
            },
            {
                "role": "user",
                "content": f"""Email:\n{email_body}

Attachments: {attachments if attachments else 'None'}

Extract the shipment details.""",
            },
        ],
        response_format=QuoteRequest,
    )

    quote = response.choices[0].message.parsed

    # Route to human review if confidence is low
    if quote.requires_review or quote.confidence < 0.85:
        print(f"Routing to human review: confidence={quote.confidence}")
        # In production, this would queue to a human review system

    return quote
```

#### Step 1.5: Build message queue consumers

Use Azure Service Bus for decoupling agents from TMS API latency.

```python
# workers/quote_worker.py
import asyncio
from azure.servicebus.aio import ServiceBusClient
from agents.quote_extractor import extract_quote_request
from tools.pricing import DynamicPricingEngine
from tools.tms import NavisphereConnector


async def process_quote_message(message):
    """Consumer for quote requests from Service Bus."""
    email_body = message.body.get("email_body")
    quote_request = await extract_quote_request(email_body)

    # Call pricing engine
    pricing = DynamicPricingEngine(api_key="...")
    quote_response = await pricing.get_quote(quote_request)

    # Return quote to customer
    # In production, send via email/API/portal
    print(f"Quote for {quote_request.origin} -> {quote_request.destination}: ${quote_response.total_price}")


async def main():
    async with ServiceBusClient.from_connection_string(
        "Endpoint=sb://your-namespace.servicebus.windows.net/;..."
    ) as client:
        async with client.get_queue_receiver("quotes") as receiver:
            async for message in receiver:
                await process_quote_message(message)
                await message.complete()


asyncio.run(main())
```

### Phase 2: Multi-Agent Orchestration

#### Step 2.1: Build the orchestrator with LangGraph

```python
# agents/orchestrator.py
from langgraph.graph import StateGraph, START, END
from typing import TypedDict


class LogisticsState(TypedDict):
    email_id: str
    email_body: str
    classification: dict
    extracted_data: dict
    booking_id: str | None
    escalation_reason: str | None


def classify_step(state: LogisticsState) -> LogisticsState:
    """Step 1: Classify email"""
    classification = classify_email(state["email_body"])
    state["classification"] = classification
    return state


def extract_step(state: LogisticsState) -> LogisticsState:
    """Step 2: Extract data based on classification"""
    if state["classification"]["type"] == "quote":
        extracted = extract_quote_request(state["email_body"])
    elif state["classification"]["type"] == "order":
        extracted = extract_order(state["email_body"])
    # ... more types
    state["extracted_data"] = extracted
    return state


def route_step(state: LogisticsState) -> str:
    """Step 3: Route to appropriate agent"""
    if state["extracted_data"].get("requires_review"):
        return "escalate"
    return state["classification"]["type"]


def quote_step(state: LogisticsState) -> LogisticsState:
    """Handle quote flow"""
    quote_request = state["extracted_data"]
    pricing = DynamicPricingEngine(...)
    quote = pricing.get_quote(quote_request)
    # Send response...
    return state


def order_step(state: LogisticsState) -> LogisticsState:
    """Handle order flow"""
    order = state["extracted_data"]
    nmfc_code = freight_classifier.classify(order.commodity_description)
    carrier = carrier_matcher.select(order.origin, order.destination)
    booking = tms.create_booking(order)
    state["booking_id"] = booking.id
    return state


# Build graph
workflow = StateGraph(LogisticsState)
workflow.add_node("classify", classify_step)
workflow.add_node("extract", extract_step)
workflow.add_node("quote", quote_step)
workflow.add_node("order", order_step)
workflow.add_node("escalate", lambda s: s)  # Placeholder for human escalation

workflow.add_edge(START, "classify")
workflow.add_edge("classify", "extract")
workflow.add_conditional_edges("extract", route_step, {
    "quote": "quote",
    "order": "order",
    "escalate": "escalate",
})
workflow.add_edge("quote", END)
workflow.add_edge("order", END)
workflow.add_edge("escalate", END)

app = workflow.compile()
```

#### Step 2.2: Add evaluation / testing

Before deploying to production, build evaluation scoring:

```python
# eval/score_extraction.py
import json
from difflib import SequenceMatcher


def score_quote_extraction(extracted: dict, ground_truth: dict) -> float:
    """Score extraction accuracy by comparing extracted vs. gold standard."""
    
    required_fields = ["origin", "destination", "weight_lbs", "commodity_description"]
    
    matches = 0
    for field in required_fields:
        extracted_val = extracted.get(field)
        true_val = ground_truth.get(field)
        
        if field in ["origin", "destination"]:
            # Compare city + state
            extracted_loc = f"{extracted_val.get('city')} {extracted_val.get('state')}"
            true_loc = f"{true_val.get('city')} {true_val.get('state')}"
            similarity = SequenceMatcher(None, extracted_loc, true_loc).ratio()
        else:
            similarity = 1.0 if extracted_val == true_val else 0.0
        
        matches += similarity
    
    return matches / len(required_fields)


# Run evaluation on test set
test_emails = load_test_emails("data/test_quotes.json")
scores = [score_quote_extraction(extract_quote_request(email), gold_standard) 
          for email, gold_standard in test_emails]
print(f"Mean extraction accuracy: {sum(scores) / len(scores):.2%}")
```

### Phase 3: Deployment

Deploy to Azure Container Apps with auto-scaling per agent type.

---

## Key Design Decisions

1. **Structured Outputs**: Use Azure OpenAI's structured output mode to guarantee valid JSON. Never parse LLM text outputs.
2. **Tool-Grounded Classification**: LLM classification agents must use tool calls for deterministic lookups (NMFC codes, rate cards). Never let the LLM hallucinate these.
3. **Confidence Scoring**: Every extraction must include a confidence score. Route low-confidence work to humans automatically.
4. **Message Queues**: Decouple agents from TMS API latency using Azure Service Bus. Agents write to queues; workers consume asynchronously.
5. **Audit Trails**: Include the raw email excerpt and reasoning in every extraction for regulatory defensibility.
6. **Start Narrow, Expand**: Begin with the highest-volume agent (quote extraction). Add agents one at a time, each proven on production volume before moving to the next.

---

## Monitoring & Observability

```python
# Production monitoring
import logging
from opentelemetry import metrics

logger = logging.getLogger(__name__)
meter = metrics.get_meter(__name__)

# Latency histogram
latency_histogram = meter.create_histogram("agent.latency_ms")

# Accuracy gauge
accuracy_gauge = meter.create_gauge("agent.accuracy")

# Escalation counter
escalation_counter = meter.create_counter("agent.escalations")
```

Track these metrics continuously to identify bottlenecks and validate ROI.
