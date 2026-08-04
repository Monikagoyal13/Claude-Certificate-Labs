"""
Lab 2.1 - Exercise 1: Tool Interfaces (S1)

WHAT THIS FILE PROVES
----------------------
The model (Claude) never sees your Python implementation of a tool. When it
decides which tool to call, it only has THREE things to go on:
    1. the tool's `name`
    2. the tool's `description`
    3. the tool's `input_schema` (the typed parameters)

That means "the model picked the wrong tool" is almost always an INTERFACE
problem, not a model-capability problem. This script proves that by running
the exact same model, over the exact same six support questions, twice:

    - once against a WEAK toolset (vague names, overlapping descriptions,
      untyped params)
    - once against a STRONG toolset (object+action names, explicit
      "use this / do NOT use this" contrast, typed + regex-constrained params)

If the strong toolset scores noticeably higher than the weak one, that is
direct evidence that better interfaces - not a bigger/smarter model - is the
fix for unreliable tool selection.

SCENARIO
--------
We are building the support agent for NorthPeak Outfitters, a fictional
online outdoor-gear store. Two very different kinds of customer question can
arrive:
    - "Do you carry a 4-person tent?"      -> should route to a CATALOG tool
    - "Where is my order NP-100245?"       -> should route to an ORDER tool
Order IDs always look like NP-XXXXXX (regex ^NP-[0-9]{6}$).
"""

import os
import sys

import anthropic
from dotenv import load_dotenv

# Windows' default console encoding (cp1252) can't print some characters
# Claude may return (curly quotes, checkmarks, etc). Forcing UTF-8 output
# avoids a crash on print() without changing any actual logic.
sys.stdout.reconfigure(encoding="utf-8")

# Load ANTHROPIC_API_KEY (and optionally ANTHROPIC_MODEL) from a local .env
# file. override=True means values in .env win over any stale env vars
# already set in the shell.
load_dotenv(override=True)

client = anthropic.Anthropic()

# The lab doc says "every exercise file reads the model from ANTHROPIC_MODEL".
# We honor that, but default to a real, current model id (claude-sonnet-5)
# instead of the doc's placeholder ("claude-sonnet-4-6"), which does not exist.
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")


# ---------------------------------------------------------------------------
# 1. WEAK TOOLSET
# ---------------------------------------------------------------------------
# Intentionally bad interfaces, kept here ONLY as a comparison baseline.
# Every lever a tool designer has is set to its worst-practice value:
#   - name:        a bare, generic verb ("search", "lookup")
#   - description: says WHAT it searches, never WHEN to use it or when NOT to
#   - parameters:  a single loose, untyped-in-spirit field ("q", "id") with
#                  no format hint and no pattern/regex constraint
WEAK_TOOLS = [
    {
        "name": "search",  # <- vague verb, could mean "search anything"
        "description": "Search for stuff in the system.",  # <- no when/when-not
        "input_schema": {
            "type": "object",
            "properties": {
                # generic single-letter-ish field name, no description of format
                "q": {"type": "string"},
            },
            "required": ["q"],
        },
    },
    {
        "name": "lookup",  # <- vague verb, could mean "look up anything"
        "description": "Look something up.",  # <- no when/when-not
        "input_schema": {
            "type": "object",
            "properties": {
                # generic "id" - no hint this must look like NP-100245
                "id": {"type": "string"},
            },
            "required": ["id"],
        },
    },
]


# ---------------------------------------------------------------------------
# 2. STRONG TOOLSET
# ---------------------------------------------------------------------------
# The reference toolset from the lab handout. Each tool applies all three
# "levers" that make an interface reliable to route on:
#   - name:        OBJECT + ACTION ("search_products", "get_order_status"),
#                  never a bare verb
#   - description: says WHEN to use it, AND explicitly defers to the sibling
#                  tool for the case it does NOT handle (negative contrast)
#   - parameters:  typed and, where possible, constrained by a regex pattern
#                  so a malformed value can be rejected at the schema level
STRONG_TOOLS = [
    {
        # Object ("products") + action ("search") - unambiguous purpose.
        "name": "search_products",
        "description": (
            "Search the NorthPeak product CATALOG for items we sell (tents, "
            "sleeping bags, stoves, boots, etc.) by free-text query. Use this "
            "for availability, price, or whether a product exists. Do NOT "
            "use this to check something a customer already bought - for an "
            "existing purchase use get_order_status instead."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Free-text product query, e.g. '4 person tent'.",
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                },
            },
            "required": ["query"],
        },
    },
    {
        # Object ("order") + action ("get_status") - unambiguous purpose.
        "name": "get_order_status",
        "description": (
            "Retrieve the status of an EXISTING customer order by its order "
            "ID (shipping status, items, tracking). Use this whenever the "
            "customer gives an order number or references a purchase. Do NOT "
            "use this to browse the catalog - for products use "
            "search_products instead."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID in the format 'NP-XXXXXX'.",
                    # A malformed id (e.g. missing the "NP-" prefix, or a
                    # different digit count) is rejected right at the schema
                    # level, before it ever reaches real backend code.
                    "pattern": "^NP-[0-9]{6}$",
                },
            },
            "required": ["order_id"],
        },
    },
]


# ---------------------------------------------------------------------------
# 3. TEST CASES
# ---------------------------------------------------------------------------
# Six realistic support questions. Each has an "intent" - CATALOG or ORDER -
# rather than a hardcoded tool name, because the weak and strong toolsets use
# DIFFERENT tool names for the same underlying intent ("search" vs.
# "search_products", "lookup" vs. "get_order_status"). The INTENT_TO_TOOL maps
# below translate an intent into the correct tool name for whichever toolset
# is currently being scored, so the same six questions can be scored fairly
# against both toolsets. A couple of cases are written to be slightly
# trickier (an order id mentioned inline in a sentence, a product question
# with no order id at all) to genuinely stress-test routing rather than only
# using the two textbook examples from the lab handout.
CATALOG = "CATALOG"
ORDER = "ORDER"

# Which literal tool name corresponds to each intent, per toolset.
WEAK_INTENT_TO_TOOL = {CATALOG: "search", ORDER: "lookup"}
STRONG_INTENT_TO_TOOL = {CATALOG: "search_products", ORDER: "get_order_status"}

TEST_CASES = [
    {
        "question": "Do you carry a four-person tent?",
        # Pure catalog / availability question, no order reference at all.
        "intent": CATALOG,
    },
    {
        "question": "Where is my order NP-100245?",
        # Explicit order id given -> existing-order lookup.
        "intent": ORDER,
    },
    {
        "question": "What's the price on your 30-degree sleeping bags?",
        # Catalog/pricing question, still no order id.
        "intent": CATALOG,
    },
    {
        "question": "Can you check the tracking on NP-100311 for me?",
        # Order id mentioned inline in a casual sentence, not as a clean
        # standalone token - stresses whether the model still extracts it.
        "intent": ORDER,
    },
    {
        "question": "Do you sell hiking boots in men's size 11?",
        # Another catalog question, different product category.
        "intent": CATALOG,
    },
    {
        "question": "My last purchase, order number NP-100190, hasn't shipped yet - what's going on?",
        # Order id embedded mid-sentence with extra surrounding narrative.
        "intent": ORDER,
    },
]


def call_with_toolset(question: str, tools: list) -> str:
    """
    Send ONE support `question` to the model with the given `tools` list and
    return the name of the tool it chose to call.

    We force `tool_choice={"type": "any"}` - the model MUST call some tool
    on this turn. That is deliberate: this harness measures WHICH tool gets
    picked, not WHETHER a tool gets picked at all (that's Exercise 3's job).

    Returns the tool name as a string, or "<no tool called>" in the
    unexpected case that the model still didn't call anything.
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        tools=tools,
        tool_choice={"type": "any"},  # must call SOME tool - see docstring
        messages=[{"role": "user", "content": question}],
    )

    # A response can contain multiple content blocks (e.g. text + tool_use).
    # We only care about the first tool_use block, since tool_choice="any"
    # guarantees at least one is present.
    for block in response.content:
        if block.type == "tool_use":
            return block.name

    return "<no tool called>"  # defensive fallback, should not happen with "any"


def run_harness(tools: list, label: str, intent_to_tool: dict) -> int:
    """
    Run every case in TEST_CASES against `tools`, print OK/MISS per question,
    and return the number of correctly-routed questions (out of len(TEST_CASES)).

    `label` is just a human-readable name ("WEAK" / "STRONG") used in the
    printed output so the two runs are easy to tell apart.

    `intent_to_tool` maps each case's abstract intent (CATALOG/ORDER) to the
    literal tool name that toolset uses for it - this is what lets the same
    six questions be scored fairly against two toolsets with different names.
    """
    print(f"\n=== Running {label} toolset ===")
    score = 0

    for case in TEST_CASES:
        question = case["question"]
        expected = intent_to_tool[case["intent"]]

        picked = call_with_toolset(question, tools)
        correct = picked == expected

        if correct:
            score += 1

        status = "OK  " if correct else "MISS"
        print(f"[{status}] \"{question}\"")
        print(f"         expected={expected}  picked={picked}")

    print(f"--- {label} score: {score}/{len(TEST_CASES)} ---")
    return score


if __name__ == "__main__":
    # The core lesson of this exercise: same model, same six questions - the
    # ONLY thing that changes between these two runs is the tool interface
    # itself (names/descriptions/schemas). Any accuracy difference we see is
    # therefore caused by interface design, not model capability.
    weak_score = run_harness(WEAK_TOOLS, "WEAK", WEAK_INTENT_TO_TOOL)
    strong_score = run_harness(STRONG_TOOLS, "STRONG", STRONG_INTENT_TO_TOOL)

    print("\n=== Summary ===")
    print(f"Weak toolset:   {weak_score}/{len(TEST_CASES)}")
    print(f"Strong toolset: {strong_score}/{len(TEST_CASES)}")
