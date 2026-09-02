"""Demo 2 (Provenance, S6) - a Claude review pass with tamper-proof provenance.

The model returns only a line number, a flag, and a confidence score - never
the quoted text. The exact quote is always attached locally from the real
report data via sample_report.get_quote(), so a citation can never be
hallucinated. A malformed model response degrades to zero findings instead
of crashing the run.
"""

import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

from sample_report import get_quote

load_dotenv()

MODEL_NAME = os.environ.get("MODEL_NAME", "claude-sonnet-4-5")
_client = Anthropic()

PROMPT_STRICT = (
    "You are a strict compliance reviewer for quarterly financial reports. "
    "Flag ANY statement that could plausibly raise a compliance concern: "
    "missing or incomplete disclosures, undisclosed related-party terms, "
    "unsupported or promissory language, numbers that don't reconcile "
    "across the report, or vague statements about controls or litigation. "
    "Err on the side of flagging when in doubt.\n\n"
    "Respond with ONLY a JSON array, no prose, no markdown fences. Each "
    'element must have exactly these keys: "line" (integer, the line '
    'number from the numbered report), "flag" (short snake_case string '
    'naming the issue), "confidence" (number from 0 to 1, how sure you are '
    "this is a real compliance issue). Do not include the quoted text."
)

PROMPT_GENERAL = (
    "You are a general compliance reviewer for quarterly financial "
    "reports. Flag statements that a reasonable compliance officer would "
    "want to look at more closely - clear disclosure gaps, numbers that "
    "don't add up, or language that overstates certainty. Use your "
    "judgment; don't flag routine, well-supported statements.\n\n"
    "Respond with ONLY a JSON array, no prose, no markdown fences. Each "
    'element must have exactly these keys: "line" (integer, the line '
    'number from the numbered report), "flag" (short snake_case string '
    'naming the issue), "confidence" (number from 0 to 1, how sure you are '
    "this is a real compliance issue). Do not include the quoted text."
)

_PROMPTS = {"strict": PROMPT_STRICT, "general": PROMPT_GENERAL}


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def _parse_json_array(text: str) -> list:
    """Parse the model's JSON array, tolerantly.

    A parse failure becomes zero findings rather than a crash - one bad
    response shouldn't take down the run.
    """
    try:
        parsed = json.loads(_strip_json_fence(text))
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def review(report_text: str, mode: str) -> list:
    """Run one review pass over the report, return provenance-backed findings.

    Each returned finding has {line, quote, flag, confidence}. The quote is
    always attached locally from the real report - the model never
    supplies it - and any finding whose line is out of range is dropped as
    unverifiable.
    """
    system_prompt = _PROMPTS[mode]
    response = _client.messages.create(
        model=MODEL_NAME,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": report_text}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    raw_findings = _parse_json_array(text)

    cleaned = []
    for f in raw_findings:
        if not isinstance(f, dict):
            continue
        line = f.get("line")
        quote = get_quote(line)
        if not quote:
            continue  # line out of range -> drop (unverifiable)
        try:
            confidence = float(f.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        cleaned.append(
            {
                "line": int(line),
                "quote": quote,
                "flag": str(f.get("flag", "unspecified")),
                "confidence": confidence,
            }
        )
    return cleaned
