"""Exercise 3 — Generalizing beyond the examples shown (Lab 4.1, S2).

Adds a short principles block above the few-shot examples and tests the
prompt on four unseen, context-heavy edge cases where surface features
mislead a naive classifier.
"""
import os
import re

from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
ACTION_RE = re.compile(r"\b(REMOVE|REVIEW|ALLOW)\b\s*\|", re.IGNORECASE)

PRINCIPLES = """- REMOVE only for unambiguous violations: exposure of a PRIVATE person's
  data (doxxing), credible threats, or clearly illegal content. Stated
  intent ("just a joke") does not excuse doxxing.
- Already-public or official info (a company's press line) is not doxxing - ALLOW.
- REVIEW anything genuinely ambiguous: possible jokes, spam, escalating disputes.
- ALLOW speech that is merely rude, blunt, unpopular, boring, or off-topic.
- When unsure between REMOVE and REVIEW, choose REVIEW.

"""

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

PRINCIPLED_PROMPT = PRINCIPLES + FEW_SHOT_EXAMPLES + INSTRUCTION

EDGE_CASES = [
    ("A post shares a company's official public press-office phone number.", "ALLOW"),
    ("A private individual's home address was shared 'as a joke'.", "REMOVE"),
    ("Two friends are joking 'I'll destroy you' about a video game match.", "REVIEW"),
    ("A long, dull but strictly on-topic essay that nobody asked for was posted.", "ALLOW"),
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


def parse_action(text: str) -> str:
    """Extract the action off the 'ACTION | rationale' line, tolerating any preamble."""
    match = ACTION_RE.search(text)
    return match.group(1).upper() if match else "UNPARSEABLE"


if __name__ == "__main__":
    passed = 0
    print("--- PRINCIPLED PROMPT on unseen edge cases ---")
    for report, expected in EDGE_CASES:
        reply = call_claude(PRINCIPLED_PROMPT.format(report=report))
        action = parse_action(reply)
        ok = action == expected
        passed += ok
        shown = reply.replace("\n", " \\n ")
        print(f"  expected={expected:<7} got={action:<12} {'OK' if ok else 'WRONG'}  | {report}")
        print(f"    -> {shown[:100]}")
    print(f"\n  edge cases passed: {passed}/{len(EDGE_CASES)}")
