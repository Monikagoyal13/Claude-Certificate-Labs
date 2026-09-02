"""Exercise 1 — Force structured output with tool_use + JSON Schema (Lab 4.2, S3).

Defines the target evaluation record as a tool's input_schema, forces the model
to call that tool, and reads the structured payload straight off block.input —
no prose parsing, no markdown fences, no missing fields.
"""
import json
import os

from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

EVALUATE_TOOL = {
    "name": "record_evaluation",
    "description": "Record a structured screening evaluation for one job candidate.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Candidate name."},
            "recommendation": {
                "type": "string",
                "enum": ["strong_hire", "hire", "no_hire"],
                "description": "Screening recommendation.",
            },
            "score": {
                "type": "integer",
                "minimum": 0,
                "maximum": 10,
                "description": "Overall fit, 0 (poor) to 10 (excellent).",
            },
            "reason": {"type": "string", "description": "One-sentence justification."},
        },
        "required": ["name", "recommendation", "score", "reason"],
    },
}

CANDIDATES = [
    (
        "Priya Nair",
        "10 years of backend experience, led the re-architecture of a payments platform "
        "handling 50k requests/sec, strong references, clear communicator in the interview.",
    ),
    (
        "Sam Ostrowski",
        "Applied for a senior data engineer role but has no data engineering experience, "
        "struggled to answer basic SQL questions, and was 40 minutes late to the interview.",
    ),
    (
        "Jordan Lee",
        "2 years of relevant experience, solid fundamentals, communicates well but has never "
        "worked at the scale this role requires and would need significant ramp-up time.",
    ),
]


def evaluate_candidate(name: str, description: str) -> dict:
    """Call the model with the tool forced and return the structured evaluation."""
    client = Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=300,
        tools=[EVALUATE_TOOL],
        tool_choice={"type": "tool", "name": "record_evaluation"},
        messages=[
            {
                "role": "user",
                "content": f"Evaluate this candidate:\nName: {name}\nNotes: {description}",
            }
        ],
    )
    for block in msg.content:
        if block.type == "tool_use":
            return block.input
    raise RuntimeError("model did not call record_evaluation")


if __name__ == "__main__":
    for name, description in CANDIDATES:
        payload = evaluate_candidate(name, description)
        print(json.dumps(payload))
