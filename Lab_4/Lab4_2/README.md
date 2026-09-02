# Lab 4.2 — Enforcing Structure: `tool_use` Schemas with Validation & Retry

Scenario: a recruiting candidate-screening evaluator that must return, for every application, a
guaranteed-valid `{name, recommendation, score, reason}` record — never free text — so a
recruiter dashboard can sort, filter, and alert on it without parsing prose.

This lab builds that reliability in three layers, one exercise each:

1. **Shape** — a `tool_use` JSON Schema forces every response into the exact object shape.
2. **Meaning** — a hand-written `validate()` catches cross-field policy the schema can't express.
3. **Self-healing** — a retry loop feeds validation failures back to the model as a
   `tool_result(is_error=True)`, bounded so it always terminates.

## Setup

```
pip install -r requirements.txt
cp .env.example .env        # paste a real ANTHROPIC_API_KEY into .env
export $(grep -v '^#' .env | xargs)
```

`ANTHROPIC_MODEL` defaults to `claude-sonnet-4-5` (the PDF's stated default, `claude-sonnet-4-6`,
is not a real model id at the time this lab was built — substituted and noted here rather than
silently changed).

## The target record

```json
{"name": "string", "recommendation": "strong_hire | hire | no_hire", "score": "integer 0-10", "reason": "string"}
```

Cross-field policy — **not expressible in JSON Schema**, enforced only in code:
- `recommendation == "strong_hire"` ⇒ `score >= 8`
- `recommendation == "no_hire"` ⇒ `score <= 4`

## Exercise 1 — `exercise_1_tool_schema.py` (force structured output)

`EVALUATE_TOOL["input_schema"]` describes the record with JSON Schema `type`/`enum`/
`minimum`/`maximum`/`required`. The call sets
`tool_choice={"type": "tool", "name": "record_evaluation"}`, which forces the model to call that
tool — its arguments (`block.input`) *are* the structured object. No `json.loads`, no regex, no
markdown-fence stripping.

Run: `python exercise_1_tool_schema.py` — prints one JSON line per candidate (3 candidates: a
strong hire, a weak one, and a borderline one), each with all four fields populated.

**Why this is more reliable than "reply in JSON":** the API itself rejects a tool call whose
arguments don't match the schema's types/enum/range, so malformed shape is impossible, not just
unlikely. What the schema *cannot* express — `strong_hire ⇒ score >= 8` — is exactly what
Exercise 2 exists for.

## Exercise 2 — `exercise_2_validation.py` (schema + semantic validation)

`validate(payload) -> (ok: bool, errors: list[str])`:
- Defensive at the top: `isinstance(payload, dict)` first, so a malformed caller input can't
  crash it.
- Per-field checks: `name` non-empty string, `recommendation` in the enum set, `score` an
  integer in `0..10`, `reason` non-empty string.
- The `bool`-is-`int` trap: Python's `isinstance(True, int)` is `True`, so `score=True` would
  silently pass an `isinstance(score, int)` check and be treated as `1`. Guarded explicitly:
  `is_int = isinstance(score, int) and not isinstance(score, bool)`.
- Cross-field policy, checked only when `is_int` (so a non-integer score doesn't also throw a
  confusing policy error): `strong_hire` needs `score >= 8`, `no_hire` needs `score <= 4`.
- Returns a tuple, never raises — so a caller (like Exercise 3's retry loop) can always inspect
  the result and decide what to do next, instead of wrapping every call in `try/except`.

Run offline first (no API key, no network call):
```
python exercise_2_validation.py --check
```
This asserts three fixtures: a good record, a structurally-bad record (empty name, bad enum,
score 15 — should fail on 3+ separate checks), and a structurally-valid-but-policy-violating
record (`strong_hire` scored 4 — should fail on exactly the cross-field rule, nothing else).

Then live: `python exercise_2_validation.py` — evaluates one real candidate and validates the
actual model output.

## Exercise 3 — `exercise_3_retry_loop.py` (retry-and-feedback loop)

`assess_with_retry(candidate, max_attempts=3)`:
1. Call the model with the tool forced, same as Exercise 1.
2. Validate the resulting payload.
3. If valid, return immediately with `errors=[]`.
4. If invalid, append the assistant's turn (`resp.content`, so the model's own prior tool call
   stays in context) and then a user turn containing a single `tool_result` block:
   - `tool_use_id` **must** echo the failed call's id, or the API rejects the turn.
   - `is_error: True` — this is what tells the model "this specific tool call failed," distinct
     from an ordinary user message, which would lose the link back to the tool call it's about.
   - `content` — the validator's joined error string plus an explicit instruction to call the
     tool again with corrected values.
5. Repeat, up to `max_attempts`. If the cap is hit, return the last payload plus its errors
   rather than looping forever — a genuinely stuck case must terminate and let the caller decide
   whether to escalate to a human.

Offline demo (no API key, no network call — a fake client scripts two fixed responses so the
feedback mechanism is visible mechanically):
```
python exercise_3_retry_loop.py --demo
```
Expected: attempt 1 is a scripted `strong_hire` scored 5 → flagged with
`["a 'strong_hire' must score >= 8"]`; attempt 2 is a scripted corrected payload (score 9) → the
loop stops and reports valid.

Live: `python exercise_3_retry_loop.py` — evaluates one real, strong candidate description; a
capable model usually gets it right on attempt 1.

## Actual results (this run)

All three scripts ran against the live API (`claude-sonnet-4-5`), no fabricated output.

**Exercise 1** — three real payloads, all structurally valid (4/4 fields, correct types, score
in range):
```
{"name": "Priya Nair",     "recommendation": "strong_hire", "score": 9, "reason": "..."}
{"name": "Sam Ostrowski",  "recommendation": "no_hire",      "score": 1, "reason": "..."}
{"name": "Jordan Lee",     "recommendation": "no_hire",      "score": 5, "reason": "..."}
```
Notable finding: **Jordan Lee's real model output was a policy violation** — `no_hire` scored
`5`, but the rule requires `no_hire ⇒ score <= 4`. The JSON Schema had no way to catch this (it's
structurally perfect); this is exactly the live, real-world case Exercise 2's validator is for.
Exercise 1 has no validator wired in (by design — that's Exercise 2's job), so this record would
have gone to the dashboard uncaught if this were the whole pipeline.

**Exercise 2 `--check`** — all 3 offline fixtures passed:
```
good record       -> ok=True  errors=[]
structurally bad   -> ok=False errors=['name must be a non-empty string', "recommendation must be one of [...]", 'score must be between 0 and 10', 'reason must be a non-empty string']
policy violation   -> ok=False errors=["a 'strong_hire' must score >= 8"]
```

**Exercise 2 live** — real model output for "Alex Park" was both structurally valid and
policy-consistent on the first try: `strong_hire`, score `9` → `valid: True`.

**Exercise 3 `--demo`** — the scripted feedback loop worked exactly as designed: attempt 1
(`strong_hire`/score 5) flagged with `["a 'strong_hire' must score >= 8"]`, fed back as a
`tool_result(is_error=True)`, attempt 2 (`strong_hire`/score 9) returned valid. No network calls.

**Exercise 3 live** — the real model got it right on `attempt 1: valid` for the strong "Alex
Park" candidate, so the retry path itself wasn't exercised on this run (consistent with the
PDF's own expectation: "a strong candidate typically passes on attempt 1"). The retry mechanism
was verified via `--demo` instead, since a live run isn't guaranteed to fail on attempt 1.

## Design notes / deviations from the PDF

- `ANTHROPIC_MODEL` defaults to `claude-sonnet-4-5`, not the PDF's `claude-sonnet-4-6` (not a
  real model id).
- Each script stays self-contained (duplicates `EVALUATE_TOOL` and `validate()`) per the lab's
  own spec that each exercise is "one self-contained Python script."
