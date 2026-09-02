# NorthPeak Community Trust & Safety Triage

Reported posts route to one of three actions:

- `REMOVE` → unambiguous violation: doxxing, credible threat, clearly illegal content.
- `REVIEW` → needs a human: likely spam, borderline harassment, ambiguous threats.
- `ALLOW` → rude/blunt/off-topic but not a violation; strong disagreement, sarcasm.

Tie-break: when unsure between `REMOVE` and `REVIEW`, choose `REVIEW` — the cost of a wrongful
takedown is not symmetric with the cost of sending an ambiguous case to a human.

## Three layers of precision (prompting only, no fine-tuning)

1. **Explicit criteria** fix the decision — a testable definition per label, plus the tie-break.
2. **Few-shot examples** fix the format — the exact `ACTION | rationale` shape, demonstrated,
   not just described.
3. **A principles block** fixes the intent — the boundary the model applies to context-heavy
   cases the examples never showed (public vs. private data, stated intent vs. actual effect).

Score format compliance with a strict regex on the `ACTION | rationale` line, never with
`split("|")[0]` — a preamble sentence would mis-score an otherwise-correct answer.
