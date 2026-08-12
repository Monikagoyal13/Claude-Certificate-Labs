"""Refund logic for NorthPeak Outfitters."""

RETURN_WINDOW_DAYS = 30
RESTOCKING_FEE_RATE = 0.15


def within_return_window(days_since_delivery: int) -> bool:
    """Return True if days_since_delivery falls within the 30-day return window."""
    if days_since_delivery < 0:
        raise ValueError("days_since_delivery must not be negative")
    return days_since_delivery <= RETURN_WINDOW_DAYS


def refund_amount(price: float, days_since_delivery: int, opened: bool = False) -> float:
    """Return the refund for a price within the return window, else 0.

    Opened items are refunded at 85% of the price (a 15% restocking fee).
    """
    if price < 0:
        raise ValueError("price must not be negative")
    if not within_return_window(days_since_delivery):
        return 0.0
    if opened:
        return round(price * (1 - RESTOCKING_FEE_RATE), 2)
    return round(price, 2)
