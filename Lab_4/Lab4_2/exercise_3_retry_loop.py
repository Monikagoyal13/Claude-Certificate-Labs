"""Exercise 3 — Retry-and-feedback loop that self-corrects (Lab 4.2, S4).

On an invalid tool call, the loop appends the assistant's turn and a
tool_result(is_error=True) carrying the validator's error string, so the
model sees exactly what was wrong and can correct itself on the next
attempt. Capped by max_attempts so a stubborn case can't run forever.

Run offline first (no API key needed, no network calls):
    python exercise_3_retry_loop.py --demo
Then live:
    python exercise_3_retry_loop.py
"""
import os
import sys
from types import SimpleNamespace

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


def _tool_use_block(resp):
    return next((b for b in resp.content if b.type == "tool_use"), None)


def assess_with_retry(candidate: str, max_attempts: int = 3, client=None):
    """Loop tool-call -> validate -> (on failure) feed error back, up to max_attempts."""
    client = client or Anthropic()
    messages = [{"role": "user", "content": f"Evaluate this candidate:\n{candidate}"}]
    last_payload, last_errors = None, ["no attempts made"]

    for attempt in range(1, max_attempts + 1):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=300,
            tools=[EVALUATE_TOOL],
            tool_choice={"type": "tool", "name": "record_evaluation"},
            messages=messages,
        )
        tool_use = _tool_use_block(resp)
        if tool_use is None:
            raise RuntimeError("model did not call record_evaluation")

        ok, errors = validate(tool_use.input)
        last_payload, last_errors = tool_use.input, errors

        if ok:
            print(f"attempt {attempt}: valid")
            return tool_use.input, []

        print(f"attempt {attempt}: invalid -> {errors}")
        messages.append({"role": "assistant", "content": resp.content})
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "is_error": True,
                        "content": (
                            "Validation failed: "
                            + "; ".join(errors)
                            + ". Call record_evaluation again with corrected values."
                        ),
                    }
                ],
            }
        )

    return last_payload, last_errors


class _FakeToolUseBlock(SimpleNamespace):
    type = "tool_use"


class _FakeResponse(SimpleNamespace):
    pass


def _fake_client_for_demo():
    """A stand-in Anthropic client that scripts two fixed attempts, no network calls."""
    scripted = [
        {"name": "Alex Park", "recommendation": "strong_hire", "score": 5, "reason": "Strong technical background."},
        {"name": "Alex Park", "recommendation": "strong_hire", "score": 9, "reason": "Strong technical background, corrected score."},
    ]
    calls = {"n": 0}

    class _FakeMessages:
        def create(self, **kwargs):
            payload = scripted[min(calls["n"], len(scripted) - 1)]
            calls["n"] += 1
            block = _FakeToolUseBlock(type="tool_use", id=f"toolu_demo_{calls['n']}", input=payload)
            return _FakeResponse(content=[block])

    return SimpleNamespace(messages=_FakeMessages())


def demo() -> None:
    """Step through the loop with two scripted attempts, no API key or network needed."""
    client = _fake_client_for_demo()
    payload, errors = assess_with_retry("Alex Park (demo, scripted)", max_attempts=3, client=client)
    print(f"\nfinal payload: {payload}")
    print(f"final errors: {errors}")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        candidate = (
            "Alex Park: 10 years of experience, led a major system re-architecture, "
            "excellent references, strong technical interview performance."
        )
        payload, errors = assess_with_retry(candidate, max_attempts=3)
        print(f"\nfinal payload: {payload}")
        print(f"final errors: {errors}")
