"""
Lab 2.1 - Exercise 3: Selection Control with tool_choice (S3)

WHAT THIS FILE PROVES
----------------------
Every incoming support ticket must first be classified into exactly ONE
routing category before anything else happens - deterministically, with no
drafting a reply and no chit-chat. `tool_choice` is the parameter that
controls how much freedom the model has on a given turn:

    {"type": "auto"}                                -> least constrained:
        the model may answer in plain text, call ANY tool, or call no tool
        at all.
    {"type": "any"}                                 -> must call SOME tool,
        but it is still the model's choice WHICH one (it could pick the
        wrong tool for the job).
    {"type": "tool", "name": "classify_ticket"}      -> must call exactly
        that tool. Fully deterministic - this is what a routing/triage step
        actually needs.

To make `auto` and `any` visibly drift from the forced mode, the model is
given a SECOND tool it can wander toward instead of classifying:
`draft_customer_reply`. Without a second tool to be tempted by, `any` and
`FORCED` would look identical and the exercise wouldn't prove anything.

RUNNING THIS FILE
-----------------
    python exercise_3_tool_choice.py
"""

import os
import sys

import anthropic
from dotenv import load_dotenv

# Windows' default console encoding (cp1252) can't print some characters
# Claude may return. Forcing UTF-8 avoids a crash on print().
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(override=True)

client = anthropic.Anthropic()

# Same convention as Exercises 1 & 2: read the model from ANTHROPIC_MODEL,
# defaulting to a real, current model id instead of the doc's placeholder.
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")


# ---------------------------------------------------------------------------
# 1. TOOL DEFINITIONS
# ---------------------------------------------------------------------------
# The triage classifier. Its label space is closed with an `enum`, so the
# category the model returns is always one of exactly these four values -
# never a free-text guess that a downstream router would have to sanitize.
CLASSIFY_TOOL = {
    "name": "classify_ticket",
    "description": "Classify a support ticket into exactly one routing category.",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["order_issue", "product_question", "return_request", "other"],
            },
            "reason": {"type": "string"},
        },
        "required": ["category", "reason"],
    },
}

# A second tool that has NOTHING to do with triage. It exists purely as a
# temptation: under auto/any the model is free to decide the customer's
# message deserves a drafted reply instead of a classification. If this were
# the only other tool in the world, `any` mode would behave exactly like
# FORCED mode and the exercise would prove nothing - the whole point is
# giving the model somewhere else to go.
DRAFT_REPLY_TOOL = {
    "name": "draft_customer_reply",
    "description": (
        "Draft a friendly reply message to send directly to the customer, "
        "answering or acknowledging their support ticket."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "reply_text": {
                "type": "string",
                "description": "The drafted reply to send to the customer.",
            },
        },
        "required": ["reply_text"],
    },
}

ALL_TOOLS = [CLASSIFY_TOOL, DRAFT_REPLY_TOOL]


# ---------------------------------------------------------------------------
# 2. THE THREE tool_choice MODES
# ---------------------------------------------------------------------------
modes = {
    # Least constrained: the model may reply in plain text, call
    # classify_ticket, call draft_customer_reply, or call nothing at all.
    "auto": {"type": "auto"},
    # Must call SOME tool this turn - but which one is still the model's
    # decision. It could still (wrongly) pick draft_customer_reply.
    "any": {"type": "any"},
    # Must call exactly classify_ticket. Fully deterministic - this is the
    # setting a real triage pipeline should actually use in production.
    "FORCED": {"type": "tool", "name": "classify_ticket"},
}


# ---------------------------------------------------------------------------
# 3. SAMPLE TICKETS
# ---------------------------------------------------------------------------
# Four realistic tickets spanning the four routing categories, including one
# ("other"/off-topic) that might tempt the model to just chat/draft a reply
# instead of classifying, since it doesn't cleanly match a support category.
SAMPLE_TICKETS = [
    "My order NP-100245 was supposed to arrive three days ago and tracking hasn't updated at all.",
    "Does the 4-person dome tent come in a lightweight version for backpacking?",
    "I'd like to return the hiking boots I bought last week, they don't fit.",
    "Just wanted to say I love the new store website redesign, great job!",
]


def run_ticket_under_mode(ticket_text: str, tool_choice: dict) -> dict:
    """
    Send one `ticket_text` to the model with BOTH tools available (so it has
    a real choice to make) under the given `tool_choice` setting, and return
    a small structured summary of what happened:

        {"called": None}                                   - no tool called,
            model replied in plain text (only possible under "auto")
        {"called": "classify_ticket", "category": ..., "reason": ...}
        {"called": "draft_customer_reply", "reply_text": ...}

    This lets run_all_modes() compare, ticket by ticket and mode by mode,
    whether a clean classification actually happened.
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        tools=ALL_TOOLS,
        tool_choice=tool_choice,
        messages=[{"role": "user", "content": ticket_text}],
    )

    for block in response.content:
        if block.type == "tool_use":
            if block.name == "classify_ticket":
                return {
                    "called": "classify_ticket",
                    "category": block.input.get("category"),
                    "reason": block.input.get("reason"),
                }
            if block.name == "draft_customer_reply":
                return {
                    "called": "draft_customer_reply",
                    "reply_text": block.input.get("reply_text"),
                }

    # No tool_use block found at all - the model answered in plain text.
    # This can only happen under {"type": "auto"}; "any" and "FORCED" both
    # guarantee a tool call.
    return {"called": None}


def run_all_modes() -> dict:
    """
    Run every ticket in SAMPLE_TICKETS under every mode in `modes`, printing
    what happened for each (ticket, mode) pair, then a final scoreboard of
    how many of the 4 tickets produced a clean classify_ticket call under
    each mode.

    Returns a dict {mode_name: classified_count} for use in the summary
    printed by the __main__ block.
    """
    classified_counts = {}

    for mode_name, tool_choice in modes.items():
        print(f"\n=== Mode: {mode_name}  (tool_choice={tool_choice}) ===")
        classified = 0

        for ticket in SAMPLE_TICKETS:
            result = run_ticket_under_mode(ticket, tool_choice)

            if result["called"] == "classify_ticket":
                classified += 1
                outcome = f"classify_ticket -> category={result['category']!r} reason={result['reason']!r}"
            elif result["called"] == "draft_customer_reply":
                outcome = f"draft_customer_reply -> reply_text={result['reply_text']!r}"
            else:
                outcome = "no tool called (plain text response)"

            print(f'  ticket: "{ticket}"')
            print(f"    -> {outcome}")

        classified_counts[mode_name] = classified
        print(f"  --- {mode_name}: {classified}/{len(SAMPLE_TICKETS)} tickets cleanly classified ---")

    return classified_counts


if __name__ == "__main__":
    counts = run_all_modes()

    print("\n=== Summary: clean classify_ticket calls out of {} tickets ===".format(len(SAMPLE_TICKETS)))
    for mode_name in modes:
        print(f"  {mode_name:8s}: {counts[mode_name]}/{len(SAMPLE_TICKETS)}")

    # The core lesson of this exercise: only FORCED is something a routing
    # pipeline can actually rely on. auto/any may work most of the time, but
    # "usually works" is not the same guarantee as "always works" - and a
    # triage step needs the guarantee.
    print(
        "\nTakeaway: use the NARROWEST tool_choice that still does the job. "
        "For a step that must be deterministic (like triage), that means "
        "forcing the specific tool - not auto, and not even any."
    )
