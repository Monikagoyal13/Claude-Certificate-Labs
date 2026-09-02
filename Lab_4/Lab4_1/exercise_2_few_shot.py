"""Exercise 2 — Few-shot examples to lock consistent output (Lab 4.1, S2).

Compares a zero-shot format instruction against the same instruction plus
three labeled examples, scoring strict "ACTION | rationale" format compliance
on four reports.
"""
import os
import re

from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
FORMAT_RE = re.compile(r"^(REMOVE|REVIEW|ALLOW) \| .+", re.MULTILINE)

INSTRUCTION = """Decide the moderation action (REMOVE, REVIEW, or ALLOW) and give one
short rationale. Respond in exactly this format: 'ACTION | rationale'.

Report: {report}"""

FEW_SHOT_EXAMPLES = """Report: A user posted another member's home address and employer.
REMOVE | Doxxing - exposes private personal data with no reasonable doubt.

Report: A member said a popular opinion was "totally wrong and lazy".
ALLOW | Blunt criticism of an idea, not a policy violation.

Report: A thread has escalating personal insults between two users.
REVIEW | Possible harassment that needs a human judgment call.

"""

ZERO_SHOT_PROMPT = INSTRUCTION
FEW_SHOT_PROMPT = FEW_SHOT_EXAMPLES + INSTRUCTION

REPORTS = [
    "A user shared screenshots revealing a coworker's home address after an argument.",
    "A member wrote 'this feature update is garbage, whoever shipped it should be embarrassed.'",
    "Multiple users are exchanging escalating insults after a disagreement about a match result.",
    "An account is repeatedly posting identical crypto investment links across many threads.",
]


def call_claude(prompt: str) -> str:
    """Call the model once with a single user message and return the text reply."""
    client = Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def score(template: str, label: str) -> None:
    compliant = 0
    print(f"\n--- {label} ---")
    for report in REPORTS:
        reply = call_claude(template.format(report=report))
        ok = bool(FORMAT_RE.search(reply))
        compliant += ok
        shown = reply.replace("\n", " \\n ")
        print(f"  {'OK ' if ok else 'FAIL'} | {shown[:90]}")
    print(f"  format compliance: {compliant}/{len(REPORTS)}")


if __name__ == "__main__":
    score(ZERO_SHOT_PROMPT, "ZERO-SHOT")
    score(FEW_SHOT_PROMPT, "FEW-SHOT")
