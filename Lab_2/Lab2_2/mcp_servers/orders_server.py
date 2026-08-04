"""NorthPeak orders MCP server.

Exposes two tools over stdio:
  - get_order(order_id): look up a single order by its ID.
  - find_orders_by_email(email): list all orders for a customer email.

Data source: data/orders.json (resolved relative to the project root, i.e.
the parent of this file's directory), so the server works no matter which
folder Claude Code is started from.
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("northpeak-orders")

# data/orders.json lives at <project root>/data/orders.json
ORDERS_PATH = Path(__file__).resolve().parent.parent / "data" / "orders.json"


def _load_orders() -> dict:
    with open(ORDERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@mcp.tool()
def get_order(order_id: str) -> dict:
    """Return a single order by its ID (e.g. "NP-100245").

    The result includes status, items, tracking number, and customer email.
    Returns an error object if the order ID is not found.
    """
    orders = _load_orders()
    order = orders.get(order_id)
    if order is None:
        return {"error": f"No order found with id {order_id!r}"}
    return order


@mcp.tool()
def find_orders_by_email(email: str) -> list:
    """Return every order placed by the given customer email address.

    Matching is case-insensitive. Returns an empty list if none match.
    """
    orders = _load_orders()
    email_norm = email.strip().lower()
    return [o for o in orders.values() if o.get("email", "").lower() == email_norm]


if __name__ == "__main__":
    mcp.run()
