"""Demo 1 & 3 (Human Review S5 + Confirmed/Contested S5+S6) - bucket findings
from two independent review passes into auto_clear, human_review, contested.

A confirmed finding (flagged by both passes) is trustworthy enough to be
routed purely by confidence. A finding seen by only one pass has no
corroboration and is always surfaced as contested for a human, regardless
of confidence.
"""

CONFIDENCE_THRESHOLD = 0.75


def bucket(pass_a: list, pass_b: list) -> dict:
    """Group findings by line number and split into the three buckets."""
    by_line_a = {f["line"]: f for f in pass_a}
    by_line_b = {f["line"]: f for f in pass_b}
    all_lines = sorted(set(by_line_a) | set(by_line_b))

    auto_clear = []
    human_review = []
    contested = []
    for line in all_lines:
        a = by_line_a.get(line)
        b = by_line_b.get(line)

        if a and b:  # both passes flagged this line -> confirmed
            avg_conf = (a["confidence"] + b["confidence"]) / 2
            entry = {
                "line": line,
                "quote": a["quote"],
                "flag_pass_a": a["flag"],
                "flag_pass_b": b["flag"],
                "confidence": avg_conf,
            }
            if avg_conf >= CONFIDENCE_THRESHOLD:
                auto_clear.append(entry)
            else:
                human_review.append(entry)
        else:  # only one pass flagged it -> contested
            present = a or b
            contested.append(
                {
                    "line": line,
                    "quote": present["quote"],
                    "flag_pass_a": a["flag"] if a else None,
                    "flag_pass_b": b["flag"] if b else None,
                    "confidence": present["confidence"],
                }
            )

    return {
        "auto_clear": auto_clear,
        "human_review": human_review,
        "contested": contested,
    }
