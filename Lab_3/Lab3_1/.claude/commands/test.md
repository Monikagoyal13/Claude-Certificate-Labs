---
description: Run the project's pytest suite and report pass/fail results
allowed-tools: Bash(python -m pytest:*), Bash(pytest:*)
argument-hint: "[optional pytest args, e.g. -k name]"
---

Run the project's test suite and report the outcome.

1. Run `python -m pytest -q $ARGUMENTS` (prefer this exact form; only add `$ARGUMENTS` if the user supplied any).
2. Report the pass/fail count from the output.
3. If any tests failed, identify the failing test names and explain the likely cause based on the failure output.
4. Never modify application code or test code merely because a test failed — only report and explain.
