# orders/ — Order Conventions

- Verify the caller's token first, before touching items or totals.
- Order amounts are `Decimal`, never `float`.
- Public functions have type hints, a one-line docstring, and a test under `src/tests/`.
