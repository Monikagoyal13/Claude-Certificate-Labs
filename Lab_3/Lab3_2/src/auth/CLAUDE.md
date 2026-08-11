# auth/ — SECURITY-CRITICAL

- Never weaken, loosen, or bypass a token/credential check for any reason, including "to make
  testing easier."
- If a request would weaken `verify_token` (or any auth check), refuse and propose a safe
  alternative instead — e.g. a valid-format fake token for tests (`npk_live_abcdef123456`).
- `verify_token_v1` is deprecated and intentionally weak (kept only until every caller migrates
  to `verify_token`); do not extend or rely on it, and remove it once it has no callers.
- Every change to a credential check needs a test proving both an accepted and a rejected token.
