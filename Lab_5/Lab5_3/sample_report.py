"""Mock quarterly financial report for Lab 5.3 (Trust & Traceability).

One statement per line, 1-indexed. A mix of clean disclosures and a few
deliberately flaggable issues (missing disclosure, risky language, a number
inconsistency) so both review passes have real things to find. Entirely
fictional - no real company, no real financial data.
"""

REPORT_LINES = [
    "Q3 revenue increased to $42.1 million, up 8% from the prior quarter.",
    "Operating expenses were $31.4 million, consistent with prior guidance.",
    "The Board approved a related-party transaction with a director's firm "
    "for consulting services; terms and value were not disclosed.",
    "Net income for the quarter was $6.2 million, or $0.18 per diluted share.",
    "Management believes the company's growth trajectory is essentially "
    "guaranteed for the next five years.",
    "Cash and cash equivalents at quarter end totaled $18.7 million.",
    "The company recorded a one-time restructuring charge of $2.0 million "
    "related to the closure of a regional office.",
    "Total assets were reported as $210.5 million, while the sum of "
    "reported asset categories in the notes totals $204.9 million.",
    "The audit committee reviewed and approved all related-party "
    "transactions during the quarter, consistent with company policy.",
    "There were no material changes to the company's internal controls "
    "over financial reporting during the quarter.",
    "The company is involved in ongoing litigation, the outcome of which "
    "management does not expect to have a material impact.",
    "Guidance for the next quarter is being withheld pending completion of "
    "a strategic review.",
]


def get_numbered_report() -> str:
    """Return the report as a numbered text block, ready to send to the model."""
    return "\n".join(f"{i}: {line}" for i, line in enumerate(REPORT_LINES, start=1))


def get_quote(line) -> str | None:
    """Return the exact source line for a given 1-indexed line number.

    Returns None if the line number is missing, non-numeric, or out of
    range - the caller must treat that as an unverifiable finding and
    drop it.
    """
    try:
        line = int(line)
    except (TypeError, ValueError):
        return None
    if line < 1 or line > len(REPORT_LINES):
        return None
    return REPORT_LINES[line - 1]
