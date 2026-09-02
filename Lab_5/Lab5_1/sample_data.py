"""Mock customer/order data for Lab 5.1 (Context Management).

All values are fictional dummy data - no PII, no real account data.
"""

CUSTOMERS = {
    "C-1001": {
        "customer_id": "C-1001",
        "name": "Aarti Sharma",
        "tier": "Gold",
    },
}

ORDERS = {
    "O-9001": {
        "order_id": "O-9001",
        "customer_id": "C-1001",
        "status": "Delivered",
        "placed_on": "2026-07-02",
        "total": "$142.50",
        "items": [
            {"sku": "SKU-1122", "name": "Wireless Mouse", "qty": 1},
            {"sku": "SKU-3344", "name": "USB-C Hub", "qty": 1},
        ],
    },
    "O-9002": {
        "order_id": "O-9002",
        "customer_id": "C-1001",
        "status": "Shipped",
        "placed_on": "2026-08-20",
        "total": "$89.00",
        "items": [
            {"sku": "SKU-5566", "name": "Mechanical Keyboard", "qty": 1},
        ],
    },
    "O-9003": {
        "order_id": "O-9003",
        "customer_id": "C-1001",
        "status": "Processing",
        "placed_on": "2026-08-29",
        "total": "$34.99",
        "items": [
            {"sku": "SKU-7788", "name": "Laptop Stand", "qty": 1},
            {"sku": "SKU-9900", "name": "Cable Organizer", "qty": 2},
        ],
    },
}

OPEN_STATUSES = {"Shipped", "Processing"}


def get_orders_for_customer(customer_id: str) -> list:
    """Return the raw (unoptimized) order records for a customer."""
    return [order for order in ORDERS.values() if order["customer_id"] == customer_id]


def get_open_orders_for_customer(customer_id: str) -> list:
    """Return only the still-open (not yet delivered) orders for a customer."""
    return [
        order
        for order in get_orders_for_customer(customer_id)
        if order["status"] in OPEN_STATUSES
    ]
