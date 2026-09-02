"""Exercise 1 — Explicit criteria to cut false positives (Lab 4.1, S1).

Compares a vague moderation prompt against one with explicit, testable criteria
and a tie-break rule, scoring overall accuracy and wrongful "remove" calls on
eight labeled reports.
"""
import os
import re

from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
ACTION_RE = re.compile(r"\b(REMOVE|REVIEW|ALLOW)\b", re.IGNORECASE)

VAGUE_PROMPT = """Decide the moderation action for this reported post:
remove, review, or allow.

Report: {report}

Answer with one word only."""

EXPLICIT_PROMPT = """You are a Trust & Safety triage assistant. Choose the action using these
exact definitions:
- remove: a clear, unambiguous violation - doxxing or exposure of private
  personal data, a credible threat against a specific person, or clearly
  illegal content. Reserve this for cases with no reasonable doubt.
- review: may violate policy but needs a human - likely spam, borderline
  harassment, ambiguous threats said in jest, heated arguments.
- allow: rude, blunt, off-topic, or unpopular but not a violation.

If unsure between remove and review, choose review - do not remove unless
the violation is unambiguous.

Report: {report}

Answer with one word only: remove, review, or allow."""

REPORTS = [
    ("A user posted another member's home address, phone number, and employer.", "REMOVE"),
    ("A user wrote 'I will find you and hurt you' directed at a named member after a dispute.", "REMOVE"),
    ("A member said: 'This policy is totally wrong and whoever wrote it is lazy.'", "ALLOW"),
    ("Two users are in a heated argument, calling each other's opinions 'garbage' and 'idiotic'.", "REVIEW"),
    ("A user sarcastically wrote 'let's just burn the whole building down lol' about an event ending.", "REVIEW"),
    ("An account posted the same discount link in 40 different threads within an hour.", "REVIEW"),
    ("A user strongly disagreed: 'Your take on the schedule change is completely misguided.'", "ALLOW"),
    ("A post shares a screenshot of a private group chat revealing another member's medical condition.", "REMOVE"),
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
    """Extract REMOVE/REVIEW/ALLOW from a model reply, tolerating extra words."""
    match = ACTION_RE.search(text)
    return match.group(1).upper() if match else "UNPARSEABLE"


def score(template: str, label: str) -> None:
    correct = 0
    false_removes = 0
    print(f"\n--- {label} ---")
    for report, expected in REPORTS:
        reply = call_claude(template.format(report=report))
        action = parse_action(reply)
        is_correct = action == expected
        correct += is_correct
        if action == "REMOVE" and expected != "REMOVE":
            false_removes += 1
        print(f"  expected={expected:<7} got={action:<12} {'OK' if is_correct else 'WRONG'}  | {report[:60]}")
    print(f"  accuracy: {correct}/{len(REPORTS)}   false REMOVE calls: {false_removes}")


if __name__ == "__main__":
    score(VAGUE_PROMPT, "VAGUE PROMPT")
    score(EXPLICIT_PROMPT, "EXPLICIT PROMPT")
