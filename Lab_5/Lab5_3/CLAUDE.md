# Lab 5.3 — Trust & Traceability: Human Review, Confidence & Provenance

**Module:** CCA-F Module 5 — Context Management & Reliability (optional)
**Scenario:** An AI compliance reviewer scans a mock quarterly financial report (`sample_report.py`) for compliance issues — missing disclosures, risky language, numbers that don't reconcile — and produces findings a human compliance officer will act on.

## What this lab demonstrates

An AI finding is only useful in a regulated industry if a human can trust it. Three techniques make each finding trustworthy:

1. **Confidence calibration** — `confidence.py`'s `CONFIDENCE_THRESHOLD` (0.75) routes confirmed findings to `auto_clear` (>= threshold) or `human_review` (below it), so scarce reviewer attention goes only where the model is unsure.
2. **Tamper-proof provenance** — `reviewer.py` asks the model for only a line number, flag, and confidence; the exact quoted text is always attached locally via `sample_report.get_quote(line)`, so a citation can never be hallucinated. A line out of range is dropped as unverifiable.
3. **Confirmed vs. contested (four-eyes review)** — `main.py` runs two independent passes (`PROMPT_STRICT`, `PROMPT_GENERAL`) over the same report; `confidence.bucket()` treats a line flagged by both as confirmed (then routed by confidence) and a line flagged by only one as `contested`, surfaced for human judgment rather than resolved automatically.

## File layout

- `main.py` — runs both passes, buckets the results, prints AUTO-CLEAR / HUMAN REVIEW / CONTESTED.
- `reviewer.py` — `PROMPT_STRICT`/`PROMPT_GENERAL`, `review()`, the tolerant JSON-array parser, and local quote attachment.
- `confidence.py` — `CONFIDENCE_THRESHOLD` and `bucket()`.
- `sample_report.py` — mock report lines, `get_numbered_report()`, `get_quote()`.
- `Document/` — the source lab PDF content (as Markdown).

## Cross-cutting notes

- Confidence without provenance is an unverifiable guess; provenance without corroboration is a single fallible opinion. All three together are what make a finding calibrated, traceable, and corroborated.
- A JSON parse failure from the model is treated as zero findings, never a crash (`reviewer._parse_json_array`).
- Confirmed findings still have to clear the confidence threshold — agreement alone is not enough, since two passes can agree and both be unsure.
- Mock data only — a fictional company, no real financial data.
