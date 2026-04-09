# UC-020: Autonomous Freight Logistics Orchestration with Agentic AI — Implementation Guide

## Prerequisites

| Prerequisite | Detail |
|--------------|--------|
| **Azure Subscription** | Azure OpenAI deployment with GPT-4o (structured outputs), Azure Service Bus, Azure Container Apps or AKS. [TD1] |
| **TMS Access** | API credentials for the target TMS (Navisphere, MercuryGate, or BluJay) with read/write permissions for shipments, orders, appointments, and tracking. [UC] |
| **NMFC Classification Data** | Licensed access to the National Motor Freight Classification tariff, exposed through an internal lookup API. [CS4] |
| **Email Access** | Microsoft Graph API or IMAP credentials for the inbound logistics email inbox. [CS1] |
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

The important boundary is between LLM agents that read, reason, and classify, and deterministic tools that price, book, schedule, and transmit. That split is what keeps the system auditable and the agents replaceable. [UC][TD1]

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


class OrderTender(BaseModel):
    reference_number: str | None = None
    origin: Location
    destination: Location
    pickup_date: str | None = None
    pickup_window: str | None = None
    delivery_date: str | None = None
    delivery_window: str | None = None
    weight_lbs: float | None = None
    pieces: int | None = None
    commodity_description: str
    equipment_type: Literal["van", "reefer", "flatbed", "other"] | None = None
    mode_selection: Literal["truckload", "ltl", "both"] | None = None
    special_requirements: list[str] = Field(default_factory=list)
    hazmat: bool = False
    temperature_requirements: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    requires_review: bool = False


class FreightClassification(BaseModel):
    nmfc_code: str
    freight_class: str
    commodity_description: str
    density_pcf: float | None = None
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    requires_review: bool = False
    alternative_codes: list[dict] = Field(
        default_factory=list,
        description="Top alternative NMFC codes if classification is uncertain",
    )


class TrackingUpdate(BaseModel):
    shipment_id: str
    status: Literal["in_transit", "delivered", "delayed", "exception", "at_pickup", "at_delivery"]
    current_location: str | None = None
    eta: str | None = None
    exception_detail: str | None = None
    carrier_contact: str | None = None
    update_source: Literal["voice_call", "email", "edi", "api", "portal"]
```

**Verification:** Invalid extra fields or missing required fields fail in unit tests before any live model call.

#### Step 1.2: Install the AI and connector dependencies

```bash
uv init freight-agents
uv add openai langgraph pydantic aiohttp tenacity azure-servicebus azure-identity
```

Use `langgraph` for agents that need multi-step tool-calling loops (freight classification, missed pickup resolution). Use `azure-servicebus` for event-driven coordination between agents. [TD1][TD2]

**Verification:** `uv run python -c "import openai, langgraph, pydantic, aiohttp, tenacity"` exits successfully.

---

### Phase 2: Core AI Integration

#### Step 2.1: Connect Azure OpenAI with strict structured outputs

The extraction agents are the foundation. If extraction is not schema-first, every downstream agent breaks. [TD1]

```python
import os

from openai import AzureOpenAI

from models.shipment import OrderTender


client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-08-01-preview",
)

ORDER_PARSER_SYSTEM_PROMPT = """
You are the order intake agent for a freight logistics platform.
Your job is to extract structured shipment data from emailed freight tenders.

Rules:
1. Extract only facts explicitly stated in the email or attachments.
2. If a field is ambiguous or missing, return null and set requires_review=true.
3. Do not infer freight class or NMFC codes.
4. Do not invent carrier names, facility addresses, or reference numbers.
5. When a shipper requests both truckload and LTL, set mode_selection="both".
6. Return only the schema-valid JSON object.
7. Set confidence based on how clearly the email states the required fields.
""".strip()


def parse_order_email(email_text: str) -> OrderTender:
    completion = client.beta.chat.completions.parse(
        model=os.environ["AZURE_OPENAI_EXTRACT_MODEL"],
        temperature=0,
        messages=[
            {"role": "system", "content": ORDER_PARSER_SYSTEM_PROMPT},
            {"role": "user", "content": email_text},
        ],
        response_format=OrderTender,
    )
    return completion.choices[0].message.parsed
```

**Why this matters:** C.H. Robinson's order agent processes 5,500 truckload orders per day in under 90 seconds each. The schema-first approach is what makes this reliable at scale — the model fills a contract instead of generating free-form text. [CS1][CS3][TD1]

#### Step 2.2: Build the email classification agent

This is the router. Every inbound email must be classified before it reaches the right agent. C.H. Robinson's email classifier handles 11,000+ emails daily and can recognize when a shipper is asking for quotes on both truckload and LTL. [CS1][CS7]

```python
from typing import Literal

from pydantic import BaseModel, Field


class EmailClassification(BaseModel):
    transaction_type: Literal["quote_request", "order_tender", "tracking_inquiry",
                               "carrier_capacity", "appointment_change", "exception_report",
                               "general_inquiry"]
    confidence: float = Field(ge=0.0, le=1.0)
    contains_attachment: bool
    multi_mode: bool = Field(description="True if email mentions both TL and LTL")
    summary: str = Field(description="One-line summary for routing context")


EMAIL_CLASSIFIER_SYSTEM_PROMPT = """
You classify inbound logistics emails by transaction type.

Categories:
- quote_request: Customer asking for a freight price quote
- order_tender: Customer submitting a shipment order to book
- tracking_inquiry: Customer or carrier asking about shipment status
- carrier_capacity: Carrier offering available trucks or capacity
- appointment_change: Request to modify pickup or delivery appointment
- exception_report: Report of a problem (missed pickup, delay, damage)
- general_inquiry: Anything that doesn't fit the above

Also determine:
- Whether the email contains attachments (rate confirmations, BOLs, etc.)
- Whether the email mentions both truckload and LTL modes

Return only schema-valid JSON.
""".strip()


def classify_email(subject: str, body: str, sender: str) -> EmailClassification:
    email_text = f"From: {sender}\nSubject: {subject}\n\n{body}"
    completion = client.beta.chat.completions.parse(
        model=os.environ["AZURE_OPENAI_CLASSIFIER_MODEL"],
        temperature=0,
        messages=[
            {"role": "system", "content": EMAIL_CLASSIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": email_text},
        ],
        response_format=EmailClassification,
    )
    return completion.choices[0].message.parsed
```

#### Step 2.3: Build the freight classification agent with tool-calling

This agent must never invent an NMFC code. It calls a lookup tool to retrieve candidates, then reasons about which one fits. C.H. Robinson's classifier handles 2,000 shipments daily and achieves classification in 3 seconds after training. [CS4][CS8]

```python
import json
import os

from openai import AzureOpenAI


client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-08-01-preview",
)


SEARCH_NMFC_TOOL = {
    "type": "function",
    "function": {
        "name": "search_nmfc",
        "description": (
            "Search the National Motor Freight Classification tariff. "
            "Returns ranked NMFC codes with descriptions and freight classes."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Product description or keywords to search",
                },
                "density_pcf": {
                    "type": ["number", "null"],
                    "description": "Density in pounds per cubic foot, if known",
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}


CALCULATE_DENSITY_TOOL = {
    "type": "function",
    "function": {
        "name": "calculate_density",
        "description": "Calculate freight density from weight and dimensions.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "weight_lbs": {"type": "number"},
                "length_in": {"type": "number"},
                "width_in": {"type": "number"},
                "height_in": {"type": "number"},
            },
            "required": ["weight_lbs", "length_in", "width_in", "height_in"],
            "additionalProperties": False,
        },
    },
}


TOOL_REGISTRY = {
    "search_nmfc": lambda args: nmfc_service.search(**args),
    "calculate_density": lambda args: {
        "density_pcf": round(
            args["weight_lbs"]
            / (args["length_in"] * args["width_in"] * args["height_in"] / 1728),
            2,
        )
    },
}

CLASSIFIER_SYSTEM_PROMPT = """
You are the freight classification agent. You determine NMFC codes for LTL shipments.

Tools available:
- search_nmfc: Look up NMFC codes by product description and optional density
- calculate_density: Calculate density from weight and dimensions

Rules:
1. Always call search_nmfc before selecting a code. Never guess a code.
2. If weight and dimensions are provided, calculate density first.
3. Consider product material, density, handling characteristics, stowability, and liability.
4. If the description is ambiguous, return top 3 candidates with confidence scores and set requires_review=true.
5. Explain your reasoning: what product characteristics drove the classification.
6. Return JSON with: nmfc_code, freight_class, commodity_description, density_pcf, reasoning, confidence, requires_review, alternative_codes.
""".strip()


def classify_freight(commodity_description: str, weight_lbs: float | None = None,
                     dimensions: dict | None = None) -> dict:
    user_content = f"Commodity: {commodity_description}"
    if weight_lbs:
        user_content += f"\nWeight: {weight_lbs} lbs"
    if dimensions:
        user_content += f"\nDimensions: {dimensions['length']}x{dimensions['width']}x{dimensions['height']} inches"

    messages = [
        {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    while True:
        response = client.chat.completions.create(
            model=os.environ["AZURE_OPENAI_TOOL_MODEL"],
            temperature=0,
            parallel_tool_calls=False,
            tools=[SEARCH_NMFC_TOOL, CALCULATE_DENSITY_TOOL],
            messages=messages,
        )

        message = response.choices[0].message
        if not getattr(message, "tool_calls", None):
            return json.loads(message.content)

        messages.append(message.model_dump())

        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            result = TOOL_REGISTRY[tool_call.function.name](args)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": json.dumps(result),
            })
```

This agent gets exactly two tools because its job is narrow: look up NMFC codes and calculate density. That constraint is what prevents hallucinated classification codes. [TD1][TD4]

---

### Phase 3: Integration Layer

#### Step 3.1: Connect to the TMS through an explicit connector layer

Keep all TMS interactions in one module so every agent write path goes through auditable, testable code. The model never gets direct API-building privileges.

```python
import os
from typing import Any

import aiohttp


class TMSClient:
    """Connector for the Transportation Management System (Navisphere / MercuryGate)."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def create_shipment(self, shipment_data: dict[str, Any]) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/shipments",
                headers=self._headers(),
                json=shipment_data,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def get_shipment(self, shipment_id: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/v1/shipments/{shipment_id}",
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def update_tracking(self, shipment_id: str, tracking_data: dict[str, Any]) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{self.base_url}/api/v1/shipments/{shipment_id}/tracking",
                headers=self._headers(),
                json=tracking_data,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def set_appointment(self, shipment_id: str, appointment_data: dict[str, Any]) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/shipments/{shipment_id}/appointments",
                headers=self._headers(),
                json=appointment_data,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def get_carrier_options(self, lane: dict[str, Any]) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/carriers/match",
                headers=self._headers(),
                json=lane,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                response.raise_for_status()
                result = await response.json()
                return result["carriers"]
```

#### Step 3.2: Map AI output to TMS fields explicitly

Do not write `model_dump()` directly into the TMS. Create a deterministic translation layer.

```python
from models.shipment import OrderTender


def map_order_to_tms_fields(order: OrderTender, classification: dict | None = None) -> dict:
    tms_fields = {
        "reference_number": order.reference_number,
        "origin": {
            "city": order.origin.city,
            "state": order.origin.state,
            "zip": order.origin.zip_code,
            "facility": order.origin.facility_name,
        },
        "destination": {
            "city": order.destination.city,
            "state": order.destination.state,
            "zip": order.destination.zip_code,
            "facility": order.destination.facility_name,
        },
        "pickup_date": order.pickup_date,
        "delivery_date": order.delivery_date,
        "weight_lbs": order.weight_lbs,
        "pieces": order.pieces,
        "commodity": order.commodity_description,
        "equipment_type": order.equipment_type,
        "mode": order.mode_selection or "truckload",
        "hazmat": order.hazmat,
        "special_requirements": order.special_requirements,
        "ai_confidence": order.confidence,
        "ai_requires_review": order.requires_review,
    }

    if classification:
        tms_fields["nmfc_code"] = classification["nmfc_code"]
        tms_fields["freight_class"] = classification["freight_class"]

    return tms_fields
```

---

### Phase 4: Orchestration & Flow

#### Step 4.1: Event-driven coordination with Service Bus

Agents are triggered by events, not by a central graph. Each agent type has its own queue. This matches how freight logistics actually works: quoting, booking, tracking, and exception handling run in parallel on different timelines.

```python
import json
import os

from azure.servicebus.aio import ServiceBusClient


CONN_STR = os.environ["AZURE_SERVICEBUS_CONNECTION_STRING"]


async def publish_event(queue_name: str, event: dict) -> None:
    async with ServiceBusClient.from_connection_string(CONN_STR) as client:
        sender = client.get_queue_sender(queue_name=queue_name)
        async with sender:
            from azure.servicebus import ServiceBusMessage
            message = ServiceBusMessage(json.dumps(event))
            await sender.send_messages(message)


async def process_inbound_email(email: dict) -> None:
    """Route classified email to the appropriate agent queue."""
    from agents.email_classifier import classify_email

    classification = classify_email(
        subject=email["subject"],
        body=email["body"],
        sender=email["sender"],
    )

    routing_map = {
        "quote_request": "quote-agent-queue",
        "order_tender": "order-agent-queue",
        "tracking_inquiry": "tracking-agent-queue",
        "carrier_capacity": "capacity-agent-queue",
        "appointment_change": "appointment-agent-queue",
        "exception_report": "exception-agent-queue",
        "general_inquiry": "human-review-queue",
    }

    target_queue = routing_map[classification.transaction_type]

    if classification.confidence < 0.85:
        target_queue = "human-review-queue"

    await publish_event(target_queue, {
        "email": email,
        "classification": classification.model_dump(),
    })
```

#### Step 4.2: Build the order processing pipeline

This is the most common flow. An email arrives, gets classified as an order tender, parsed into structured data, classified (if LTL), matched to a carrier, and booked in the TMS. C.H. Robinson achieves this in 90 seconds. [CS3]

```python
from agents.order_parser import parse_order_email
from agents.freight_classifier import classify_freight
from tools.tms import TMSClient, map_order_to_tms_fields


async def process_order(email: dict, tms: TMSClient) -> dict:
    """End-to-end order processing: parse → classify → book."""

    # Step 1: Extract structured order from email
    order = parse_order_email(email["body"])

    # Step 2: If LTL, classify freight
    classification = None
    if order.mode_selection == "ltl":
        classification = classify_freight(
            commodity_description=order.commodity_description,
            weight_lbs=order.weight_lbs,
        )

        # Escalate if classification is uncertain
        if classification.get("requires_review"):
            return {"status": "pending_review", "reason": "classification_uncertain",
                    "order": order.model_dump(), "classification": classification}

    # Step 3: Check if extraction needs human review
    if order.requires_review or order.confidence < 0.92:
        return {"status": "pending_review", "reason": "extraction_uncertain",
                "order": order.model_dump()}

    # Step 4: Map to TMS fields and create shipment
    tms_fields = map_order_to_tms_fields(order, classification)
    result = await tms.create_shipment(tms_fields)

    return {"status": "booked", "shipment_id": result["shipment_id"],
            "order": order.model_dump()}
```

#### Step 4.3: Build the missed pickup resolution agent (dual-agent pattern)

This is the most sophisticated agent in the fleet. Two agents work in parallel: one calls carriers to gather information, and another decides what to do. C.H. Robinson reports this automates 95% of missed pickup checks. [CS9]

```python
from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from pydantic import BaseModel
from typing_extensions import TypedDict


class MissedPickupState(TypedDict, total=False):
    shipment_id: str
    carrier_name: str
    carrier_phone: str
    pickup_date: str
    customer_id: str
    call_result: dict
    resolution: dict
    escalated: bool


class PickupResolution(BaseModel):
    action: Literal["reschedule_same_carrier", "dispatch_alternate", "escalate_to_human"]
    reasoning: str
    new_pickup_date: str | None = None
    alternate_carrier_id: str | None = None
    confidence: float


RESOLUTION_SYSTEM_PROMPT = """
You are the missed pickup decision agent. A carrier failed to pick up an LTL shipment.
Based on the call result from the carrier, decide the best resolution.

Options:
1. reschedule_same_carrier: If carrier confirms they can pick up within 24 hours
2. dispatch_alternate: If carrier cannot pick up or is unreliable for this lane
3. escalate_to_human: If the situation is complex (hazmat, high-value, customer escalation)

Consider:
- Urgency of the shipment (delivery deadline)
- Carrier's explanation and reliability history
- Whether an alternate carrier is available for this lane
- Customer tier and SLA requirements

Return JSON with: action, reasoning, new_pickup_date (if rescheduling), alternate_carrier_id (if dispatching), confidence.
""".strip()


def call_carrier_node(state: MissedPickupState) -> MissedPickupState:
    """Voice AI agent calls carrier to gather missed pickup details."""
    from tools.voice import call_carrier_about_pickup

    call_result = call_carrier_about_pickup(
        carrier_phone=state["carrier_phone"],
        shipment_id=state["shipment_id"],
        pickup_date=state["pickup_date"],
    )
    return {"call_result": call_result}


def decide_resolution_node(state: MissedPickupState) -> MissedPickupState:
    """LLM agent reasons about the best resolution given carrier's response."""
    context = (
        f"Shipment: {state['shipment_id']}\n"
        f"Carrier: {state['carrier_name']}\n"
        f"Original pickup date: {state['pickup_date']}\n"
        f"Call result: {state['call_result']}"
    )

    completion = client.beta.chat.completions.parse(
        model=os.environ["AZURE_OPENAI_TOOL_MODEL"],
        temperature=0,
        messages=[
            {"role": "system", "content": RESOLUTION_SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ],
        response_format=PickupResolution,
    )

    resolution = completion.choices[0].message.parsed
    return {"resolution": resolution.model_dump()}


def route_resolution(state: MissedPickupState) -> str:
    resolution = state["resolution"]
    if resolution["action"] == "escalate_to_human" or resolution["confidence"] < 0.85:
        return "human_escalation"
    return "execute_resolution"


def execute_resolution_node(state: MissedPickupState) -> MissedPickupState:
    """Execute the chosen resolution: reschedule or dispatch alternate."""
    # Implementation calls TMS to reschedule or dispatch alternate carrier
    return state


def human_escalation_node(state: MissedPickupState) -> MissedPickupState:
    """Pause for human review of the resolution decision."""
    interrupt({
        "shipment_id": state["shipment_id"],
        "call_result": state["call_result"],
        "proposed_resolution": state["resolution"],
    })
    return {"escalated": True}


# Build the dual-agent graph
builder = StateGraph(MissedPickupState)
builder.add_node("call_carrier", call_carrier_node)
builder.add_node("decide_resolution", decide_resolution_node)
builder.add_node("execute_resolution", execute_resolution_node)
builder.add_node("human_escalation", human_escalation_node)

builder.add_edge(START, "call_carrier")
builder.add_edge("call_carrier", "decide_resolution")
builder.add_conditional_edges("decide_resolution", route_resolution)
builder.add_edge("execute_resolution", END)
builder.add_edge("human_escalation", END)

missed_pickup_graph = builder.compile()
```

This is the pattern where LangGraph shines: the dual-agent coordination has state, branching, and a human escalation path. Within each agent the scope is narrow, but the graph manages the handoff. [TD2][TD3][CS9]

---

### Phase 5: Evaluation and Deployment

#### Step 5.1: Build the evaluation set before expanding automation

C.H. Robinson's approach was to start with the highest-volume customers and expand as agents proved reliable. The evaluation set must cover the real diversity of freight emails. [CS1][CS7]

Build at least:

- 500 truckload quote request emails (varying formats, attachments, multi-stop)
- 500 order tender emails (with and without reference numbers, special requirements)
- 200 LTL shipments for NMFC classification (common and unusual commodities)
- 100 carrier capacity emails
- 100 exception/tracking emails
- 50 ambiguous emails that should route to human review

#### Step 5.2: Keep deployment event-driven

Each agent type runs as a Service Bus consumer. Scaling is independent per queue — quote agents can scale up during spot market peaks without affecting tracking agents.

```yaml
# Azure Container Apps scaling rule example
resources:
  - name: quote-agent
    properties:
      template:
        scale:
          minReplicas: 2
          maxReplicas: 20
          rules:
            - name: servicebus-quote-queue
              custom:
                type: azure-servicebus
                metadata:
                  queueName: quote-agent-queue
                  messageCount: "50"
```

---

## Key Code Patterns

### Pattern: Schema-first extraction with confidence scoring

```python
def extract_and_validate(email_text: str) -> OrderTender:
    order = parse_order_email(email_text)
    # Schema enforcement catches structural errors
    # Confidence scoring catches semantic uncertainty
    if order.confidence < 0.92:
        order.requires_review = True
    return order
```

This is the single highest-leverage pattern. C.H. Robinson processes 5,500 orders/day because extraction is schema-first, not free-form. [CS3][TD1]

### Pattern: Tool-grounded classification (never invent a code)

```python
def validate_classification(result: dict) -> None:
    """Ensure the classification came from a tool lookup, not hallucination."""
    if not result.get("nmfc_code"):
        raise ValueError("Classification must include an NMFC code from search_nmfc")
    if result.get("confidence", 0) < 0.80 and not result.get("requires_review"):
        raise ValueError("Low-confidence classifications must be flagged for review")
```

The model selects from NMFC lookup results. It does not generate codes from training data. [CS4][TD4]

### Pattern: Phased rollout with widening automation envelope

```python
class AutomationPolicy:
    """Controls which transactions are auto-processed vs. human-reviewed."""

    def __init__(self, phase: str = "conservative"):
        self.thresholds = {
            "conservative": {"min_confidence": 0.95, "max_value": 10000, "allowed_modes": ["truckload"]},
            "moderate": {"min_confidence": 0.92, "max_value": 50000, "allowed_modes": ["truckload", "ltl"]},
            "expanded": {"min_confidence": 0.88, "max_value": 100000, "allowed_modes": ["truckload", "ltl", "intermodal"]},
        }[phase]

    def can_auto_process(self, order: OrderTender, estimated_value: float) -> bool:
        return (
            order.confidence >= self.thresholds["min_confidence"]
            and estimated_value <= self.thresholds["max_value"]
            and (order.mode_selection or "truckload") in self.thresholds["allowed_modes"]
            and not order.hazmat
            and not order.requires_review
        )
```

C.H. Robinson started with 2,268 truckload customers on quoting and expanded to 5,200+ as the agent proved reliable. [CS1][CS7]

---

## Prompt Templates

### Quote Extraction

```text
System:
You extract structured freight quote requests from customer emails.

Output contract:
- Return only the QuoteRequest schema.
- Set confidence based on how clearly the email states required fields.
- If the shipper mentions both truckload and LTL, set mode_preference="both".
- Extract the key email excerpt that contains the shipment details for audit.
- Do not guess zip codes, facility names, or reference numbers.
- If the email is vague (e.g., "need a truck next week"), set requires_review=true.
```

### Freight Classification

```text
System:
You determine NMFC codes for LTL freight shipments.
You must call search_nmfc before selecting any code.

Rules:
1. Calculate density if weight and dimensions are provided.
2. Search NMFC by product description and density.
3. Select the most specific code that matches the commodity.
4. If multiple codes could apply, return alternatives with confidence scores.
5. Explain your reasoning: material, density, handling, stowability.
6. Never return a code that was not in the search results.
```

### Missed Pickup Decision

```text
System:
You decide how to resolve a missed LTL freight pickup.
The carrier has been contacted and their response is provided.

Decision framework:
1. If carrier confirms pickup within 24 hours AND shipment is not time-critical → reschedule
2. If carrier cannot pick up OR has missed pickups on this lane before → dispatch alternate
3. If shipment is hazmat, high-value, or customer has escalated → escalate to human
4. Consider delivery deadline proximity when choosing between options.

Return your decision with clear reasoning.
```

---

## Configuration Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `AZURE_OPENAI_EXTRACT_MODEL` | none | Deployment for schema-first extraction (GPT-4o recommended). |
| `AZURE_OPENAI_CLASSIFIER_MODEL` | none | Deployment for email classification (GPT-4o-mini sufficient). |
| `AZURE_OPENAI_TOOL_MODEL` | none | Deployment for tool-calling agents (freight classification, resolution). |
| `EXTRACTION_TEMPERATURE` | `0.0` | Keep extraction deterministic. |
| `CLASSIFIER_TEMPERATURE` | `0.0` | Keep classification deterministic. |
| `AUTO_PROCESS_CONFIDENCE` | `0.92` | Minimum confidence for touchless order processing. |
| `CLASSIFICATION_REVIEW_THRESHOLD` | `0.80` | Below this, freight classification routes to human. |
| `EMAIL_CLASSIFY_CONFIDENCE` | `0.85` | Below this, email routes to general inbox for manual triage. |
| `MAX_EMAIL_CHARS` | `16000` | Upper bound on email text passed to extraction agents. |
| `TMS_API_BASE_URL` | none | TMS API endpoint. |
| `AZURE_SERVICEBUS_CONNECTION_STRING` | none | Service Bus connection for event-driven coordination. |

---

## Testing Strategy

### Unit Tests

Test deterministic logic aggressively:

- Field mapping from AI schemas to TMS fields
- Confidence threshold routing logic
- Email classification routing map
- NMFC tool result parsing
- Automation policy rules

```python
def test_low_confidence_order_routes_to_review():
    order = OrderTender(
        origin=Location(city="Chicago", state="IL"),
        destination=Location(city="Dallas", state="TX"),
        commodity_description="Mixed electronics",
        confidence=0.75,
        requires_review=False,
    )
    policy = AutomationPolicy(phase="moderate")
    assert not policy.can_auto_process(order, estimated_value=5000)


def test_hazmat_always_routes_to_review():
    order = OrderTender(
        origin=Location(city="Houston", state="TX"),
        destination=Location(city="Atlanta", state="GA"),
        commodity_description="Industrial solvents",
        hazmat=True,
        confidence=0.99,
        requires_review=False,
    )
    policy = AutomationPolicy(phase="expanded")
    assert not policy.can_auto_process(order, estimated_value=5000)
```

### Integration Tests

Use a real Azure OpenAI deployment and TMS sandbox:

- Live email extraction against canned freight emails
- Live NMFC classification against known commodity descriptions
- Shipment creation and retrieval in the TMS sandbox
- End-to-end order flow from email to booking

```python
async def test_order_parsing_round_trip(tms_sandbox: TMSClient):
    email_body = """
    Hi, please book the following:
    Origin: ABC Warehouse, 123 Main St, Chicago IL 60601
    Dest: XYZ Distribution, 456 Oak Ave, Dallas TX 75201
    Pickup: Monday 3/15
    Weight: 42,000 lbs
    Commodity: Automotive parts (Class 85)
    Equipment: 53' dry van
    Ref: PO-2026-1234
    """
    result = await process_order({"body": email_body}, tms_sandbox)
    assert result["status"] == "booked"
    assert result["order"]["origin"]["city"] == "Chicago"
```

### Evaluation Tests

Score AI output against labeled datasets. This is where you measure whether the AI is actually correct, not just whether the API call succeeded.

```python
def score_extraction_accuracy(predicted: OrderTender, gold: dict) -> dict[str, float]:
    """Compare extracted order against human-labeled ground truth."""
    fields_checked = 0
    fields_correct = 0

    for field in ["origin.city", "destination.city", "weight_lbs", "equipment_type",
                  "mode_selection", "hazmat", "pickup_date"]:
        fields_checked += 1
        parts = field.split(".")
        pred_val = getattr(predicted, parts[0]) if len(parts) == 1 else getattr(getattr(predicted, parts[0]), parts[1])
        gold_val = gold[parts[0]] if len(parts) == 1 else gold[parts[0]][parts[1]]
        if pred_val == gold_val:
            fields_correct += 1

    return {
        "field_accuracy": fields_correct / fields_checked,
        "confidence_calibration": abs(predicted.confidence - (fields_correct / fields_checked)),
    }
```

Track at least:

- Field-level extraction accuracy per email format
- NMFC classification top-1 match rate against expert labels
- Email classification accuracy across transaction types
- Quote accuracy vs. manual pricing specialist
- Percentage of orders auto-processed vs. escalated
- Missed pickup resolution success rate

---

## Monitoring & Observability

| What to Monitor | Tool / Method | Alert Threshold |
|-----------------|---------------|-----------------|
| **Extraction parse failures** | Structured logging on schema violations | `>2%` of orders in 15 minutes |
| **Email classification confidence** | Custom metric on classification scores | Average drops below `0.90` |
| **NMFC classification escalation rate** | Graph-state metrics | Sudden rise above `25%` baseline |
| **Quote response latency** | Application Insights | p95 > 60 seconds |
| **Order processing latency** | Application Insights | p95 > 3 minutes |
| **TMS write failures** | Connector error logs | Any sustained non-zero error rate |
| **Token usage per transaction** | Azure OpenAI usage metrics | Deviation > 2x from baseline |
| **Service Bus queue depth** | Azure Monitor | Backlog > 500 messages on any agent queue |

---

## Common Pitfalls & Mitigations

| Pitfall | Mitigation |
|---------|------------|
| LLM hallucinating NMFC codes or carrier names | Tool-grounded classification; never let the model generate codes from training data. [CS4][TD4] |
| Extraction looks correct but confidence is miscalibrated | Score confidence against gold set accuracy; recalibrate thresholds regularly. |
| Token limit exceeded on long email threads | Truncate to most recent email in thread; pass only the latest tender, not the full conversation history. |
| Rate limiting under spot market peaks | Provisioned throughput for high-volume agents (quoting, orders); standard for lower-volume agents. |
| Customer-specific pricing leaking across accounts | Isolate pricing context per request; never include other customers' rates in the prompt. [UC] |
| Deploying too many agent types at once | Start with one agent (quoting), prove ROI, then expand. C.H. Robinson took this phased approach. [CS1][CS7] |

---

## Rollback Plan

If quality drops or a critical error is detected:

1. Switch affected agent to "suggestion-only" mode: AI still processes but all output routes to human review queue.
2. Disable the auto-processing flag so no orders are booked without human confirmation.
3. The TMS remains the system of record — all manual processes continue to work because agents augment, not replace, the platform.
4. Preserve all agent traces (prompts, inputs, outputs, tool calls) from the failed period for root-cause analysis.
5. Re-run the evaluation set against the failing agent to identify whether the issue is prompt drift, model degradation, or integration failure.
