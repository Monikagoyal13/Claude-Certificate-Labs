---
description: Review current changes against the checklist
allowed-tools: Bash(git diff:*), Bash(git status:*), Read, Grep
argument-hint: "[optional path or scope]"
---

Review the uncommitted changes (focus: $ARGUMENTS) against this project's style and testing rules. This command is read-only — do not edit any files.

1. Run `git status` and `git diff` to see what changed. If `$ARGUMENTS` is supplied, focus on that path or scope.
2. Review the diff against the project's rules (`.claude/rules/style.md`, `.claude/rules/testing.md`). Check at least:
   - Correctness — does the change do what it appears to intend, with no obvious bugs?
   - Tests — is there a test covering the new/changed behavior, including boundaries and both sides of important conditions?
   - Type hints — do public functions have parameter and return type hints?
   - Docstrings — do public functions have a useful docstring?
   - Input validation — do public functions taking numeric arguments (prices, counts, quantities) reject negative or otherwise invalid values, per `style.md`?
3. Group every finding into one of three buckets:
   - **Blocker** — must fix (e.g. missing test for new behavior, incorrect logic).
   - **Suggestion** — should consider (e.g. missing docstring, unclear naming).
   - **Nit** — minor/stylistic (e.g. formatting, wording).
4. End with a concise one-line verdict, e.g. `Needs changes: 3` or `Looks good: 0 blockers, 0 suggestions, 0 nits`.
