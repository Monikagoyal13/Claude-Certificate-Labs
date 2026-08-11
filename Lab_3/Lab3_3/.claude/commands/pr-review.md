---
description: Review the current diff and emit a strict {decision, issues} JSON verdict for CI
allowed-tools: Bash(git diff:*), Bash(git status:*), Read, Grep
argument-hint: "[optional path or scope]"
---

Review the uncommitted changes (focus: $ARGUMENTS) against this project's `CLAUDE.md` rules
(test-driven development; never weaken or delete a test to go green; type hints, docstrings,
input validation). This command is read-only — do not edit any files.

1. Run `git status` and `git diff` to see what changed. If `$ARGUMENTS` is supplied, focus on
   that path or scope.
2. Check at least: correctness, test coverage (including boundaries and both sides of important
   conditions), whether any existing test was weakened or deleted to make the suite pass, type
   hints, and docstrings.
3. Output ONLY the following JSON object — no prose before or after it, no markdown fences:

```
{
  "decision": "approve" | "request_changes",
  "issues": [ { "severity": "blocker" | "warning" | "nit", "message": "..." } ]
}
```

- `decision` is `"request_changes"` if there is at least one `blocker`, otherwise `"approve"`.
- `issues` may be an empty list when there is nothing to flag.
