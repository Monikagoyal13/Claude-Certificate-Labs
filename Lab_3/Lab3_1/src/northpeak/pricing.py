"""Pricing helpers for the NorthPeak Outfitters order flow."""

MEMBER_DISCOUNT_RATE = 0.10
FREE_SHIPPING_THRESHOLD = 75.00
STANDARD_SHIPPING_FEE = 6.99
EXPRESS_SHIPPING_FEE = 14.99


def member_discount(subtotal: float, is_member: bool) -> float:
    """Return the discount amount for a subtotal, based on membership status."""
    if subtotal < 0:
        raise ValueError("subtotal must not be negative")
    if not is_member:
        return 0.0
    return round(subtotal * MEMBER_DISCOUNT_RATE, 2)


def shipping_cost(subtotal: float, express: bool = False) -> float:
    """Return the shipping fee for a subtotal, waiving it above the free-shipping threshold."""
    if subtotal < 0:
        raise ValueError("subtotal must not be negative")
    if subtotal >= FREE_SHIPPING_THRESHOLD:
        return 0.0
    return EXPRESS_SHIPPING_FEE if express else STANDARD_SHIPPING_FEE


GIFT_WRAP_FEE_PER_ITEM = 2.50


def gift_wrap_fee(item_count: int) -> float:
    """Return the optional gift-wrap fee for the given number of items."""
    if item_count < 0:
        raise ValueError("item_count must not be negative")
    return round(GIFT_WRAP_FEE_PER_ITEM * item_count, 2)


def order_total(items: list[float], is_member: bool = False, express: bool = False) -> float:
    """Return the final order total after member discount and shipping are applied."""
    if any(price < 0 for price in items):
        raise ValueError("item prices must not be negative")
    subtotal = round(sum(items), 2)
    discount = member_discount(subtotal, is_member)
    shipping = shipping_cost(subtotal - discount, express)
    return round(subtotal - discount + shipping, 2)
