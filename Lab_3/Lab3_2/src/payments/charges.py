"""Payment charging for NorthPeak Outfitters."""
from decimal import Decimal

from auth.tokens import verify_token_v1


def charge(token: str, amount: Decimal) -> dict:
    """Charge amount to the customer after verifying the caller's token."""
    if not verify_token_v1(token):
        raise PermissionError("invalid token")
    if amount <= 0:
        raise ValueError("amount must be positive")
    return {"charged": amount}
