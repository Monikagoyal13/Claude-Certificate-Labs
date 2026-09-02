"""Lab 5.3 - Trust & Traceability: Human Review, Confidence & Provenance.

Scenario: an AI compliance reviewer scans a quarterly financial report
twice, with different prompts, and produces three buckets a human
compliance officer can trust: AUTO-CLEAR, HUMAN REVIEW, and CONTESTED.
"""

from confidence import CONFIDENCE_THRESHOLD, bucket
from reviewer import review
from sample_report import get_numbered_report


def _print_bucket(title: str, entries: list) -> None:
    print(f"\n=== {title} ({len(entries)}) ===")
    if not entries:
        print("  (none)")
        return
    for e in entries:
        if "flag_pass_a" in e and "flag_pass_b" in e and e["flag_pass_a"] and e["flag_pass_b"]:
            flag_desc = f"flag={e['flag_pass_a']!r} (both passes agree)"
        else:
            flag_desc = f"flag_pass_a={e.get('flag_pass_a')!r} flag_pass_b={e.get('flag_pass_b')!r}"
        print(f"  line {e['line']}: {flag_desc} confidence={e['confidence']:.2f}")
        print(f"    quote: \"{e['quote']}\"")


def main() -> None:
    report_text = get_numbered_report()

    print("Running strict pass...")
    pass_a = review(report_text, mode="strict")
    print("Running general pass...")
    pass_b = review(report_text, mode="general")

    buckets = bucket(pass_a, pass_b)

    print(f"\nConfidence threshold: {CONFIDENCE_THRESHOLD}")
    _print_bucket("AUTO-CLEAR", buckets["auto_clear"])
    _print_bucket("HUMAN REVIEW", buckets["human_review"])
    _print_bucket("CONTESTED", buckets["contested"])


if __name__ == "__main__":
    main()
