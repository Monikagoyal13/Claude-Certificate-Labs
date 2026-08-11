---
name: changelog-entry
description: >
  Use when the user wants to update the changelog, add a CHANGELOG entry, write
  release notes, or summarize a change for CHANGELOG.md — e.g. "update the
  changelog", "add a CHANGELOG entry", "write release notes", "summarize this
  change for the changelog".
---

# Changelog Entry

Turn the current code change into a Keep-a-Changelog entry.

## Steps

1. Run `git diff` (and `git status` if needed) to see what changed.
2. Understand the change: what behavior was added, changed, fixed, or removed. Ignore purely
   formatting-only changes (whitespace, comment rewording) unless they are the only change present.
3. Categorize the change under one of: `Added`, `Changed`, `Fixed`, `Removed`.
4. Write one concise, user-facing sentence per change — describe the effect for a user of the
   library, not the implementation detail.
5. Open `CHANGELOG.md`, creating it if it does not exist.
6. Prepend the new entry under a `## [Unreleased]` heading. If an `## [Unreleased]` section
   already exists, add the new bullet under the matching category heading within it instead of
   creating a duplicate section. Never delete or rewrite existing changelog entries.

## Output format

```markdown
## [Unreleased]

### Added
- Optional gift-wrap fee helper for orders.
```
