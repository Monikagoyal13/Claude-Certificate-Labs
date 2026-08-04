import json

import anthropic
from dotenv import load_dotenv

from tools import classify_ticket

load_dotenv(override=True)

client = anthropic.Anthropic()

MODEL = "claude-sonnet-4-5-20250929"

TEST_TICKET = (
    "From: sarah.chen@globalcorp.com\n"
    "Subject: Cannot access SSO login — entire team locked out\n"
    "Our team of 40 has been unable to log in via SSO since 09:00 this morning. "
    "We have a client demo in 3 hours. This is completely blocking us."
)

tools = [
    {
        "name": "classify_ticket",
        "description": (
            "Classify a support ticket. Returns a dict with a value for each requested "
            "field: product_area, severity, and/or intent."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticket_text": {
                    "type": "string",
                    "description": "The full raw text of the support ticket to classify.",
                },
                "fields_needed": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Which classification fields to return. Valid values: "
                        "'product_area', 'severity', 'intent'."
                    ),
                },
            },
            "required": ["ticket_text", "fields_needed"],
        },
    }
]

messages = [
    {
        "role": "user",
        "content": (
            "Classify the following support ticket completely. You must determine all "
            "three fields — product_area, severity, and intent — using the classify_ticket "
            "tool as many times as needed until all three are confirmed. Do not stop until "
            "you have all three.\n\n"
            f"Ticket:\n{TEST_TICKET}"
        ),
    }
]

iteration = 0
while True:
    iteration += 1
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )
    print(f"[iteration {iteration}] stop_reason = {response.stop_reason}")

    messages.append({"role": "assistant", "content": response.content})

    if response.stop_reason == "end_turn":
        final_text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        print("\nFinal response:\n" + final_text)
        break

    if response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  -> tool_use: {block.name}({block.input})")
                result = classify_ticket(**block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    }
                )
        messages.append({"role": "user", "content": tool_results})
        continue

    # max_tokens or stop_sequence — not expected in this lab, but handle gracefully
    print(f"Unhandled stop_reason: {response.stop_reason}")
    break
