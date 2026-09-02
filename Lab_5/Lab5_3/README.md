# Lab 5.3 — Trust & Traceability: Human Review, Confidence & Provenance

CCA-F | Module 5 (optional) · ~45 minutes hands-on · Python 3.10+ · `anthropic` + `python-dotenv`

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env   # then paste your key into .env
```

`.env`:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
MODEL_NAME=claude-sonnet-4-5
```

Run:

```bash
python main.py
```

Only the two review passes call the API; the bucketing logic (`confidence.py`) and the report data (`sample_report.py`) are pure Python. `sample_report.py` is a fictional quarterly report — no real company or financial data.

## Demos

### Demo 1 — Confidence calibration & routing (`confidence.py`)

`CONFIDENCE_THRESHOLD = 0.75`. A confirmed finding (flagged by both passes) at or above the threshold auto-clears; below it, it routes to human review.

**Try it:** lower `CONFIDENCE_THRESHOLD` to `0.5` and re-run — more findings auto-clear. Raise it to `0.9` — more route to human review.

### Demo 2 — Provenance (`reviewer.py`, `sample_report.py`)

The model returns only a line number, flag, and confidence — never the quote. `reviewer.review()` attaches the exact quote from `sample_report.get_quote(line)`.

**Try it:** edit a line in `sample_report.py` and re-run — the quote in the output changes to match, because it's read from the source, not from the model.

### Demo 3 — Confirmed vs. contested (`main.py`, `confidence.py`)

Two passes run with different prompts (`PROMPT_STRICT`, `PROMPT_GENERAL`). A line flagged by both is confirmed and routed by confidence; a line flagged by only one is `contested`, showing both passes' flags (one may be `None`).

## Reading the output

```
python main.py
```

prints three buckets:

- **AUTO-CLEAR** — confirmed by both passes, average confidence >= 0.75.
- **HUMAN REVIEW** — confirmed by both passes, but below the confidence threshold.
- **CONTESTED** — flagged by only one pass; both passes' flags are shown so a human can adjudicate.

Every finding in every bucket carries its exact source line and quote, verifiable in one click.

## Reflection

See `Document/Lab_5_3_Trust_Traceability_CCA-F.md` §5 for the full self-check questions and common-mistakes table.
