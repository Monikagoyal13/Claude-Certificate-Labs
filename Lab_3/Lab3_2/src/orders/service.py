"""Order placement for NorthPeak Outfitters."""
from auth.tokens import verify_token_v1


def place_order(token: str, items: list[dict]) -> dict:
    """Place an order for the given items after verifying the caller's token."""
    if not verify_token_v1(token):
        raise PermissionError("invalid token")
    return {"items": items, "count": len(items)}
