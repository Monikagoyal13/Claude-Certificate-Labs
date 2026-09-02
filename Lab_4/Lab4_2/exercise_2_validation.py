"""Exercise 2 — Schema plus semantic validation (Lab 4.2, S4).

The JSON Schema is a syntax check (types, enum values, integer range). It
cannot express cross-field policy like "a strong_hire must score >= 8" —
that lives in validate(), the second gate after the schema.

Run offline first (no API key needed):
    python exercise_2_validation.py --check
Then live:
    python exercise_2_validation.py
"""
import os
import sys

from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
RECS = {"strong_hire", "hire", "no_hire"}

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


def validate(payload) -> tuple[bool, list[str]]:
    """Return (ok, errors). Defensive: never raise, accept anything as input."""
    errors = []
    if not isinstance(payload, dict):
        return False, ["payload is not an object"]

    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("name must be a non-empty string")

    rec = payload.get("recommendation")
    if rec not in RECS:
        errors.append(f"recommendation must be one of {sorted(RECS)}")

    score = payload.get("score")
    is_int = isinstance(score, int) and not isinstance(score, bool)
    if not is_int:
        errors.append("score must be an integer")
    elif not (0 <= score <= 10):
        errors.append("score must be between 0 and 10")

    reason = payload.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        errors.append("reason must be a non-empty string")

    if rec == "strong_hire" and is_int and score < 8:
        errors.append("a 'strong_hire' must score >= 8")
    if rec == "no_hire" and is_int and score > 4:
        errors.append("a 'no_hire' must score <= 4")

    return (len(errors) == 0), errors


def check() -> None:
    """Offline fixtures: no API key required."""
    good = {"name": "Priya Nair", "recommendation": "hire", "score": 7, "reason": "Solid fit."}
    ok, errors = validate(good)
    print(f"good record       -> ok={ok} errors={errors}")
    assert ok and errors == []

    bad_shape = {"name": "", "recommendation": "maybe", "score": 15, "reason": ""}
    ok, errors = validate(bad_shape)
    print(f"structurally bad   -> ok={ok} errors={errors}")
    assert not ok and len(errors) >= 3

    policy_violation = {
        "name": "Sam Ostrowski",
        "recommendation": "strong_hire",
        "score": 4,
        "reason": "Impressive portfolio.",
    }
    ok, errors = validate(policy_violation)
    print(f"policy violation   -> ok={ok} errors={errors}")
    assert not ok and errors == ["a 'strong_hire' must score >= 8"]

    print("\nall offline fixtures passed (3/3)")


def call_claude(candidate: str) -> dict:
    client = Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=300,
        tools=[EVALUATE_TOOL],
        tool_choice={"type": "tool", "name": "record_evaluation"},
        messages=[{"role": "user", "content": f"Evaluate this candidate:\n{candidate}"}],
    )
    for block in msg.content:
        if block.type == "tool_use":
            return block.input
    raise RuntimeError("model did not call record_evaluation")


if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    else:
        candidate = (
            "Alex Park: 10 years of experience, led a major system re-architecture, "
            "excellent references, strong technical interview performance."
        )
        payload = call_claude(candidate)
        ok, errors = validate(payload)
        print(f"payload: {payload}")
        print(f"valid: {ok}" if ok else f"invalid -> {errors}")
