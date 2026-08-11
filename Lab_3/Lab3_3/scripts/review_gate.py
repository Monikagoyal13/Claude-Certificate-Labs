"""Turn a Claude review verdict into a CI pass/fail exit code.

Usage:
    python scripts/review_gate.py <path-to-review.json>
    claude -p "..." --output-format json | python scripts/review_gate.py
"""
import json
import re
import sys

FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _strip_fences(text: str) -> str:
    """Remove surrounding markdown code fences, if present."""
    return FENCE_RE.sub("", text.strip()).strip()


def _unwrap(data):
    """Unwrap the --output-format json envelope, parsing a JSON-string `result` if present."""
    if isinstance(data, dict) and "result" in data and "decision" not in data:
        result = data["result"]
        if isinstance(result, str):
            return json.loads(_strip_fences(result))
        return result
    return data


def load_review(raw_text: str) -> dict:
    """Parse review JSON, tolerating markdown fences and the CLI's output envelope."""
    data = json.loads(_strip_fences(raw_text))
    return _unwrap(data)


def main() -> int:
    if len(sys.argv) > 1:
        raw_text = open(sys.argv[1], encoding="utf-8").read()
    else:
        raw_text = sys.stdin.read()

    review = load_review(raw_text)
    decision = review.get("decision")
    issues = review.get("issues", [])

    for issue in issues:
        print(f"[{issue.get('severity', 'nit')}] {issue.get('message', '')}")

    if decision == "approve":
        print("PASS: approve")
        return 0
    if decision == "request_changes":
        print("FAIL: request_changes")
        return 1

    print(f"FAIL: unrecognized decision {decision!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
