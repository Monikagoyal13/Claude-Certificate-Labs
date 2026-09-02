"""Demo 2 (Optimization) - trim raw tool output down to what the model needs.

A raw lookup_orders call against a real database returns full order records:
line items, SKUs, addresses, dozens of columns, hundreds of rows for an active
customer. Pasting all of that into the conversation burns tokens, buries the
few useful fields under noise, and pushes earlier turns (including the
[CASE FACTS] block) closer to eviction. optimize(tool, raw) keeps only the
fields the current intent needs, per a per-tool whitelist.
"""

import logging

logger = logging.getLogger(__name__)

# Fields we actually care about for each tool. Anything not in this list
# is dropped before the result reaches the model.
RELEVANT_FIELDS = {
    "lookup_orders": ["order_id", "status", "placed_on", "total"],
    "get_order_details": ["order_id", "status", "placed_on", "total", "items"],
}


def optimize(tool_name: str, raw_result):
    """Trim a tool's raw output to just the whitelisted fields.

    Preserves the input shape (list or dict). A tool with no whitelist entry
    passes through untouched, but is logged - an unconfigured tool slipping
    through with its full payload is exactly the failure mode this exists to
    prevent, so it should never happen silently.
    """
    keep = RELEVANT_FIELDS.get(tool_name)
    if keep is None:
        logger.warning(
            "optimize(): no RELEVANT_FIELDS entry for tool '%s' - "
            "passing raw result through unfiltered",
            tool_name,
        )
        return raw_result
    if isinstance(raw_result, list):
        return [{k: row[k] for k in keep if k in row} for row in raw_result]
    if isinstance(raw_result, dict):
        return {k: raw_result[k] for k in keep if k in raw_result}
    return raw_result
