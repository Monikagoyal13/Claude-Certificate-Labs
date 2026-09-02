"""Lab 5.1 - Managing Context: Preservation, Optimization & Escalation.

Scenario: an e-commerce customer-support agent (multi-turn, multi-order
session) for a Gold-tier customer, Aarti Sharma (C-1001), who has three
orders on file (one delivered, one shipped, one processing).

Three demos, run in sequence:
  Demo 1 (S1, Preservation) - [CASE FACTS] survive 18 turns of small talk.
  Demo 2 (S1, Optimization) - tool output trimmed to a per-tool whitelist.
  Demo 3 (S2, Escalation)   - ambiguous requests get a clarifying question.
"""

import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

from case_facts import CaseFacts
from sample_data import ORDERS, get_open_orders_for_customer, get_orders_for_customer
from tool_optimizer import optimize

load_dotenv()

MODEL = os.environ.get("MODEL_NAME", "claude-sonnet-4-6")
client = Anthropic()

# The instruction that does the escalation work (Demo 3) plus the
# case-facts-are-authoritative instruction that backs Demo 1.
SYSTEM_BASE = (
    "You are a helpful support agent for an online retail company. "
    "Be concise. If a request is ambiguous (e.g. the customer has multiple "
    "open orders and didn't specify which), ASK a clarifying question "
    "instead of guessing. Always rely on the [CASE FACTS] block - those "
    "values are authoritative and you do not need to ask for them again."
)

TOOLS = [
    {
        "name": "lookup_orders",
        "description": "List all orders on file for a customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer id, e.g. C-1001.",
                }
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_order_details",
        "description": "Get the full details (including line items) for a single order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order id, e.g. O-9001.",
                }
            },
            "required": ["order_id"],
        },
    },
]


def run_tool(name: str, args: dict) -> str:
    """Execute a tool, optimize the result, return JSON for the model."""
    if name == "lookup_orders":
        raw = get_orders_for_customer(args["customer_id"])
    elif name == "get_order_details":
        raw = ORDERS.get(args["order_id"]) or {}
    else:
        raw = {"error": f"unknown tool {name}"}
    trimmed = optimize(name, raw)
    return json.dumps(trimmed)


def chat(messages: list, facts: CaseFacts) -> str:
    """Run one user turn to completion (including any tool-use round trips).

    `messages` is mutated in place so the caller keeps the full running
    history across turns. Returns the agent's final text reply.
    """
    system_prompt = SYSTEM_BASE
    facts_block = facts.as_system_block()
    if facts_block:
        system_prompt = system_prompt + "\n\n" + facts_block

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return "".join(
                block.text for block in response.content if block.type == "text"
            )

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = run_tool(block.name, block.input)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                }
            )
        messages.append({"role": "user", "content": tool_results})


def demo_1_case_facts():
    print("\n=== Demo 1: Preserve persistent case facts ===")
    facts = CaseFacts()
    facts.set("customer_id", "C-1001")
    facts.set("tier", "Gold")

    messages = []
    for turn in [
        "What are your store hours?",
        "How long does standard shipping usually take?",
        "What payment methods do you accept?",
        "Quick check - what is my customer ID and what tier am I?",
    ]:
        messages.append({"role": "user", "content": turn})
        reply = chat(messages, facts)
        print(f"USER: {turn}")
        print(f"AGENT: {reply}\n")


def demo_2_tool_optimization():
    print("\n=== Demo 2: Optimize tool outputs ===")
    raw = get_orders_for_customer("C-1001")
    trimmed = optimize("lookup_orders", raw)

    print("RAW:")
    print(json.dumps(raw, indent=2))
    print("\nOPTIMIZED:")
    print(json.dumps(trimmed, indent=2))

    facts = CaseFacts()
    facts.set("customer_id", "C-1001")
    facts.set("tier", "Gold")
    messages = [
        {
            "role": "user",
            "content": "List my orders - just status and total for each.",
        }
    ]
    reply = chat(messages, facts)
    print(f"\nAGENT: {reply}\n")


def demo_3_escalate_ambiguity():
    print("\n=== Demo 3: Escalate ambiguity instead of guessing ===")
    facts = CaseFacts()
    facts.set("customer_id", "C-1001")

    open_orders = get_open_orders_for_customer("C-1001")
    print(
        f"Customer has {len(open_orders)} open orders: "
        f"{[o['order_id'] for o in open_orders]}"
    )

    messages = [{"role": "user", "content": "Please cancel my order."}]
    reply = chat(messages, facts)
    print(f"AGENT: {reply}\n")


if __name__ == "__main__":
    demo_1_case_facts()
    demo_2_tool_optimization()
    demo_3_escalate_ambiguity()
