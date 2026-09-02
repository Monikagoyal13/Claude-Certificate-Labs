# NorthPeak Recruiting — Candidate-Screening Evaluator

Each application becomes a structured evaluation feeding a recruiter dashboard, so the output
must be machine-readable (same four fields, same types, every time) and policy-consistent (a
`strong_hire` scored 5 must never slip through).

## The target record

```
{"name": str, "recommendation": "strong_hire" | "hire" | "no_hire", "score": int 0-10, "reason": str}
```

Cross-field policy (not expressible in JSON Schema): `strong_hire` ⇒ `score >= 8`; `no_hire` ⇒
`score <= 4`.

## Three layers of reliability (see `README.md` for full detail)

1. **Tool schema** (`EVALUATE_TOOL.input_schema` + forced `tool_choice`) fixes the shape — every
   response is a typed object read straight off `block.input`, never parsed from prose.
2. **`validate(payload)`** fixes the meaning — cross-field policy the schema can't express, kept
   in code, returning `(ok, errors)` rather than raising.
3. **The retry loop** fixes the failure mode — a validation error is fed back as a
   `tool_result(is_error=True)` so the model corrects itself, bounded by `max_attempts` so the
   loop always terminates.

Schema without validation lets policy-violating records through. Validation without the retry
loop just rejects them. Together: structured, correct, and self-healing within a bounded budget.
