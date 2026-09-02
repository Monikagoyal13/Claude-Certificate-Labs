# Lab 5.2 — Resilient Systems: Error Propagation & Large Codebase Exploration

**Module:** CCA-F Module 5 — Context Management & Reliability
**Scenario:** A healthcare claims processing pipeline (intake → validation → adjudication) over three sample claims. CLM-001 and CLM-003 are well-formed; CLM-002 is for an inactive member and is deliberately malformed so it fails validation.

## What this lab demonstrates

Multi-agent pipelines fail two ways in production: silently (a subagent raises and the coordinator catches nothing useful) or catastrophically (a nightly run dies partway through and a restart re-does finished work). This lab fixes both with three composable pieces:

1. **Error propagation** — `agents.py` wraps every subagent (`run_intake`, `run_validation`, `run_adjudication`) so it returns a `StageResult(stage, ok, data, error)` envelope and never raises into the coordinator. `run_intake` is the only stage that calls the API and the only place with a `try/except Exception`.
2. **Disk-backed scratchpad** — `scratchpad.py`'s `Scratchpad` class logs every stage's finding to `scratchpad.json`, keyed by `claim_id`, flushing to disk after every single mutation. It is both the audit trail and the checkpoint.
3. **Crash-recovery skip rule** — `main.py`'s coordinator loop checks `pad.status(claim_id)` before processing each claim and skips anything already `done` or `failed`, so a Ctrl+C-and-restart (or a real crash) resumes exactly where it stopped.

## File layout

- `main.py` — coordinator: `process_claim()` walks the three stages in order and checkpoints after each; `main()` applies the skip rule and prints a `done/failed/skipped` summary.
- `agents.py` — `StageResult` dataclass and the three subagents.
- `scratchpad.py` — the `Scratchpad` audit/checkpoint store.
- `sample_claims.py` — mock `CLAIMS` (CLM-001/002/003) and `COVERED_PROCEDURES`.
- `Document/` — the source lab PDF content (as Markdown).

## Cross-cutting notes

- Each of the three pieces is useless without the other two: the envelope makes failures explicit but the scratchpad is what makes them auditable and restart-safe; the scratchpad only tells the truth if subagents never raise; crash recovery only works if every mutation flushed before the crash.
- `scratchpad.json` is never deleted from code — reset is a manual, deliberate action (`rm scratchpad.json`), not an automatic one, to avoid silently discarding an audit trail.
- The coordinator skips on **both** `done` and `failed` — retrying a failed claim automatically risks re-billing or duplicate side effects; failures are meant to be triaged by a human.
- Mock data only — synthetic member ids, no PHI, no real medical records.
