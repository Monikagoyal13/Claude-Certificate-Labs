# Testing Rules

- Every behavior change requires tests — no code change ships without covering test updates.
- Use pytest as the test framework.
- Use sentence-style test names (e.g. `test_shipping_is_free_above_the_threshold`), not abbreviations.
- Tests should cover boundaries (e.g. exactly at a threshold, empty input, zero).
- Tests should cover both sides of important conditions (e.g. member vs. non-member, valid vs. invalid input).
- `pytest -q` must pass before considering the work complete.
