# Lab 5.2 — Resilient Systems: Error Propagation & Large Codebase Exploration

CCA-F | Module 5 · ~45 minutes hands-on · Python 3.10+ · `anthropic` + `python-dotenv`

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
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

Cost is minimal — the intake subagent is the only stage that calls the API (one short JSON extraction per claim); validation and adjudication are deterministic Python. `sample_claims.py` contains three fictional claims (synthetic member ids M-501/M-777) — no PHI, no real medical records.

To reset between runs, delete `scratchpad.json` by hand — the script never deletes it itself.

## Demos

All three techniques are interleaved into one coordinator loop (`main.py`), exercised together on every run.

### Demo 1 — StageResult error envelope (`agents.py`)

Every subagent (`run_intake`, `run_validation`, `run_adjudication`) returns a `StageResult(stage, ok, data, error)` instead of raising. `run_intake` is the only stage that calls Claude, and the only one with a `try/except Exception` — any failure there becomes `StageResult(ok=False, error=...)`, never an unhandled exception.

**What good looks like:** CLM-001 and CLM-003 print `intake...ok validation...ok adjudication...ok`; CLM-002 prints `validation...FAIL (member_not_active)` — a named error, not a stack trace — and the pipeline keeps going.

### Demo 2 — Scratchpad as audit trail (`scratchpad.py`)

Every stage result is written to `scratchpad.json` via `pad.log(claim_id, stage, payload)`, flushed to disk immediately. After a run:

```bash
cat scratchpad.json
```

**What good looks like:** three entries, one per claim, each with a `status`, a `findings` list (one record per stage that ran), and — for CLM-002 — a `failure_reason` naming the stage and error.

### Demo 3 — Crash-recovery skip rule (`main.py`)

On startup the coordinator checks `pad.status(claim_id)` for each claim and skips anything already `done` or `failed`.

```bash
python main.py   # run 1 — processes all three claims
python main.py   # run 2 — everything is already done/failed, skipping
```

**What good looks like:** run 1 ends with `done: 2  failed: 1  skipped: 0`; run 2 prints three `(already ..., skipping)` lines and ends with `done: 0  failed: 0  skipped: 3`.

To simulate a real crash, hit Ctrl+C mid-run and re-run — claims already checkpointed are skipped, the rest resume cleanly.

## Reflection

See `Document/Lab_5_2_Resilient_Systems_CCA-F.md` §5 for the full self-check questions and common-mistakes table.
