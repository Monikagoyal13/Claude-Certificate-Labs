# NorthPeak Outfitters — Services Monorepo

Backend services behind the storefront. `src/auth/` verifies API tokens, `src/payments/` charges
customers, `src/orders/` places orders.

## General rules

- Follow the project's existing Python style; keep functions pure where appropriate.
- Validate inputs; public functions have type hints, a docstring, and a test.
- Money values are `Decimal`, never `float`.
- Every behavior change needs a test; `pytest -q` must pass.

## Path-specific rules

Claude Code layers this root file with the nearest directory's own `CLAUDE.md` for the file you
are editing — strict rules live next to the code they govern, not here:

- `src/auth/CLAUDE.md` — SECURITY-CRITICAL: never weaken a credential check.
- `src/orders/CLAUDE.md` — order conventions (token first, Decimal money).
- `src/payments/CLAUDE.md` — MONEY-CRITICAL: verify token, reject bad amounts.
