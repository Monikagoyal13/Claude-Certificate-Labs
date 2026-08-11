# payments/ — MONEY-CRITICAL

- Always verify the token before charging.
- Reject non-positive amounts and amounts over the $10,000 limit with a clear `ValueError`.
- Amounts are `Decimal`, never `float` — floating point must never represent money here.
- Every change to `charge()` needs a test covering both an accepted charge and a rejected one.
