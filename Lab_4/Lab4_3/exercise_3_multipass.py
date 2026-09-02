"""Exercise 3 — Multi-pass review for higher quality (Lab 4.3, S6).

Drafts a morning briefing from headlines in one shot (no standards given, so
it can realistically miss some), critiques it against explicit standards
(list problems, do NOT rewrite), then refines it to address every point.
Separating generate from judge catches what a single self-reviewing pass
misses.

Run:
    python exercise_3_multipass.py
"""
import os

from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

STANDARDS = (
    "Briefing standards: lead with the single most important development; balance "
    "positive and negative coverage fairly; be specific (numbers, who/what); stay "
    "neutral in tone; no speculation beyond the headlines; keep it under 120 words."
)

HEADLINES = [
    "Helix Robotics unveils new warehouse-automation arm, beating throughput benchmarks by 30%.",
    "Helix Robotics stock drops 8% after quarterly earnings miss analyst expectations.",
    "Regulators open a probe into Helix Robotics' overseas manufacturing practices.",
    "Helix Robotics announces a new partnership with a major logistics provider.",
    "Helix Robotics recalls a batch of assembly-line robots over a safety defect.",
    "Helix Robotics CEO named to industry's top-40-under-40 list.",
    "Helix Robotics reports record quarterly revenue, up 12% year over year.",
    "Analysts split on Helix Robotics' long-term outlook amid rising competition.",
]


def ask(client, prompt: str) -> str:
    msg = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in msg.content if b.type == "text").strip()


def draft(client, headlines) -> str:
    """First pass: write a briefing without being told the standards."""
    joined = "\n".join(f"- {h}" for h in headlines)
    prompt = f"Write a short morning briefing summarizing today's coverage from these headlines:\n{joined}"
    return ask(client, prompt)


def critique(client, headlines, draft_text: str) -> str:
    """Second pass: list concrete problems against STANDARDS. Do NOT rewrite."""
    joined = "\n".join(f"- {h}" for h in headlines)
    prompt = (
        f"{STANDARDS}\n\n"
        f"Headlines:\n{joined}\n\n"
        f"Draft briefing:\n{draft_text}\n\n"
        "Critique the draft against the standards above. List specific, actionable "
        "problems as short bullets (e.g. buries the regulatory probe, omits the "
        "12% figure, too long, leans positive). Do NOT rewrite - only list issues."
    )
    return ask(client, prompt)


def refine(client, headlines, draft_text: str, critique_text: str) -> str:
    """Third pass: apply the critique, output only the final briefing text."""
    joined = "\n".join(f"- {h}" for h in headlines)
    prompt = (
        f"{STANDARDS}\n\n"
        f"Headlines:\n{joined}\n\n"
        f"Draft briefing:\n{draft_text}\n\n"
        f"Critique to address:\n{critique_text}\n\n"
        "Rewrite the briefing so it fixes every point in the critique and meets the "
        "standards. Output only the final briefing text."
    )
    return ask(client, prompt)


if __name__ == "__main__":
    client = Anthropic()

    draft_text = draft(client, HEADLINES)
    print("=== DRAFT ===")
    print(draft_text)
    print(f"[{len(draft_text.split())} words]\n")

    critique_text = critique(client, HEADLINES, draft_text)
    print("=== CRITIQUE ===")
    print(critique_text)
    print()

    refined_text = refine(client, HEADLINES, draft_text, critique_text)
    print("=== REFINED ===")
    print(refined_text)
    print(f"[{len(refined_text.split())} words]")
