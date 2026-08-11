"""Refund logic for NorthPeak Outfitters."""

RETURN_WINDOW_DAYS = 30


def within_return_window(days_since_delivery: int) -> bool:
    """Return True if days_since_delivery falls within the 30-day return window."""
    if days_since_delivery < 0:
        raise ValueError("days_since_delivery must not be negative")
    return days_since_delivery <= RETURN_WINDOW_DAYS


def refund_amount(price: float, days_since_delivery: int) -> float:
    """Return the refund for a price within the return window, else 0."""
    if price < 0:
        raise ValueError("price must not be negative")
    if not within_return_window(days_since_delivery):
        return 0.0
    return round(price, 2)
