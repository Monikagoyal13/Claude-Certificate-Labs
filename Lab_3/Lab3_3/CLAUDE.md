# NorthPeak Outfitters — Refunds Service

The refunds service decides how much money goes back to a customer — a wrong number is a real
refund error, so every change deserves a test and a review.

## Working style: test-driven development

- Default loop for new behavior: write a **failing** test first, run it (RED), implement just
  enough to make it pass (GREEN), run again. Don't implement before the test exists.
- **Never weaken or delete a test to make the suite go green — fix the code.** A test that was
  edited to match buggy behavior is worse than no test at all.
- Public functions have type hints, a docstring, and validate their inputs.
- `pytest -q` must pass before considering the work complete.

## CI/CD

- `/pr-review` outputs only a strict `{decision, issues}` JSON object — no prose — so
  `scripts/review_gate.py` can gate a PR deterministically.
- The GitHub Action runs Claude headless (`claude -p ... --output-format json`) against the PR
  diff only, never the whole repo, and reads the API key from the `ANTHROPIC_API_KEY` secret —
  never commit it.
