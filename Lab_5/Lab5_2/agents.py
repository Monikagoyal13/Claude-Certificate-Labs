"""Demo 1 (Error Propagation, S3) - the StageResult envelope and the three
claim-processing subagents.

A subagent that raises an exception into the coordinator is a subagent that
disappears: the structured details (which stage, which input, what kind of
failure) are lost. Every subagent here returns a StageResult - the failure
path is a first-class return value, never an exception that escapes.
"""

import json
import os
from dataclasses import asdict, dataclass
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv

from sample_claims import COVERED_PROCEDURES

load_dotenv()

MODEL_NAME = os.environ.get("MODEL_NAME", "claude-sonnet-4-5")
_client = Anthropic()

INTAKE_SYSTEM = (
    "You extract structured fields from a raw insurance claim narrative. "
    "Given the claim JSON (which already includes member_id, procedure_code, "
    "and amount), respond with ONLY a JSON object with exactly these keys: "
    '"member_id" (string), "procedure_code" (string), "amount" (number), '
    '"summary" (a one-sentence plain-English summary of the narrative). '
    "No prose, no markdown fences - just the raw JSON object."
)

# Adjudication thresholds, by billed amount.
APPROVE_MAX = 500.00
HOLD_FOR_REVIEW_MAX = 2000.00


@dataclass
class StageResult:
    """Envelope every subagent must return. Failures are first-class."""

    stage: str
    ok: bool
    data: Any = None
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _strip_json_fence(text: str) -> str:
    """Be forgiving about ```json ... ``` fences some models add."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def run_intake(claim: dict) -> StageResult:
    """Call Claude to produce a clean structured summary of the claim.

    This is the only stage that calls the API, so it is the most likely to
    fail (timeouts, malformed JSON, rate limits). The try/except wrap is
    deliberate and is the only place in this file that catches an exception -
    subagents never raise into the coordinator.
    """
    try:
        response = _client.messages.create(
            model=MODEL_NAME,
            max_tokens=400,
            system=INTAKE_SYSTEM,
            messages=[{"role": "user", "content": json.dumps(claim)}],
        )
        text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        parsed = json.loads(_strip_json_fence(text))
        return StageResult(stage="intake", ok=True, data=parsed)
    except Exception as exc:
        return StageResult(
            stage="intake", ok=False, error=f"{type(exc).__name__}: {exc}"
        )


def run_validation(claim: dict) -> StageResult:
    """Check policy rules. Fail fast and loudly with a named error code."""
    if not claim.get("member_active", False):
        return StageResult(stage="validation", ok=False, error="member_not_active")
    if claim.get("procedure_code") not in COVERED_PROCEDURES:
        return StageResult(
            stage="validation",
            ok=False,
            error=f"procedure_not_covered:{claim.get('procedure_code')}",
        )
    return StageResult(stage="validation", ok=True, data={"checks_passed": True})


def run_adjudication(claim: dict) -> StageResult:
    """Deterministic approve / hold-for-review / denied decision by amount."""
    amount = claim.get("amount", 0)
    if amount <= APPROVE_MAX:
        decision = "approve"
    elif amount <= HOLD_FOR_REVIEW_MAX:
        decision = "hold-for-review"
    else:
        decision = "denied"
    return StageResult(
        stage="adjudication",
        ok=True,
        data={"decision": decision, "amount": amount},
    )
