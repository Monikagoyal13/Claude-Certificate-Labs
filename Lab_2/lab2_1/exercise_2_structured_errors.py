"""
Lab 2.1 - Exercise 2: Structured Errors & Retries (S2)

WHAT THIS FILE PROVES
----------------------
NorthPeak's Orders backend is flaky. Some failures are TRANSIENT (a timeout,
a rate limit, a brief "server busy") and simply retrying usually works.
Others are PERMANENT (the order genuinely doesn't exist, or the id given was
malformed) and retrying is pointless - it will never succeed, it just adds
latency.

If a tool function RAISES a Python exception when the backend fails, the
whole agentic loop crashes right there - the model never even gets a chance
to see what went wrong, let alone react to it (retry, apologize, ask for a
correction). The fix used throughout this file: a tool must NEVER raise.
It always returns a structured "envelope" describing what happened:

    success -> {"isError": False, ...order fields}
    failure -> {"isError": True, "isRetryable": <bool>, "status": <int>, "error": <msg>}

A small retry loop then does the obvious thing with that envelope: retry
while isRetryable is True (with exponential backoff and a hard attempt cap),
and stop immediately the moment isRetryable is False.

RUNNING THIS FILE
-----------------
    python exercise_2_structured_errors.py --check   # offline self-test, no API calls
    python exercise_2_structured_errors.py            # live agent demo, 3 order ids
"""

import json
import os
import sys
import time

import anthropic
from dotenv import load_dotenv

# Windows' default console encoding (cp1252) can't print some characters
# Claude may return. Forcing UTF-8 avoids a crash on print().
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(override=True)

client = anthropic.Anthropic()

# Same convention as Exercise 1: read the model from ANTHROPIC_MODEL, but
# default to a real, current model id instead of the doc's placeholder.
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")


# ---------------------------------------------------------------------------
# 1. MOCK FLAKY BACKEND
# ---------------------------------------------------------------------------
class ServiceError(Exception):
    """
    Raised internally by the simulated `orders_service` backend to represent
    an HTTP-style failure. `status` is an HTTP status code (e.g. 404, 503)
    and `message` is a short human-readable explanation.

    This exception is only ever caught INSIDE call_order_tool() - it must
    never escape to the agentic loop or the model.
    """

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


# HTTP statuses worth retrying: request timeout, rate-limited, and various
# "the server is temporarily struggling" 5xx codes. Retrying one of these
# has a real chance of succeeding because the underlying problem is transient.
RETRYABLE = {408, 429, 500, 502, 503, 504}

# The two order ids we use to demonstrate PERMANENT failures. These always
# fail the same way, no matter how many times you call the service.
NOT_FOUND_ID = "NP-999999"          # a well-formed id that simply doesn't exist -> 404
MALFORMED_ID = "100245"             # missing the "NP-" prefix entirely -> 400

# Tracks how many times orders_service() has been called for each order id,
# so we can simulate "times out on the first call, succeeds on the second"
# deterministically (no randomness -> reproducible demo output).
_call_counts: dict = {}


def orders_service(order_id: str) -> dict:
    """
    Simulated backend call to NorthPeak's real Orders service.

    Deliberately scripted (not random) so every run of this file produces
    the same demo output:
      - MALFORMED_ID always raises a 400 (bad request - the id shape is wrong).
      - NOT_FOUND_ID always raises a 404 (the order genuinely doesn't exist).
      - every OTHER id times out (504) on its first call, then succeeds on
        the second call onward - demonstrating a transient failure that a
        retry loop can recover from.
    """
    _call_counts[order_id] = _call_counts.get(order_id, 0) + 1
    attempt_number = _call_counts[order_id]

    if order_id == MALFORMED_ID:
        # Permanent client error: the id doesn't match the NP-XXXXXX shape.
        # No amount of retrying fixes a malformed request.
        raise ServiceError(400, f"'{order_id}' is not a valid order id (expected NP-XXXXXX).")

    if order_id == NOT_FOUND_ID:
        # Permanent "not found": the backend understood the request just
        # fine, but there is no such order. Retrying returns the same 404
        # forever.
        raise ServiceError(404, f"No order found with id '{order_id}'.")

    if attempt_number == 1:
        # Simulate a transient backend hiccup on the very first attempt for
        # any other id, so the retry loop below has something real to recover
        # from.
        raise ServiceError(504, "Orders service timed out, please retry.")

    # Second and later attempts for a "normal" id succeed with canned data.
    return {
        "order_id": order_id,
        "status": "shipped",
        "items": ["4-Person Dome Tent"],
        "tracking": "1Z999AA10123456784",
    }


# ---------------------------------------------------------------------------
# 2. THE TWO CORE FUNCTIONS: envelope + retry
# ---------------------------------------------------------------------------
def call_order_tool(order_id: str) -> dict:
    """
    Wrap the raw (exception-throwing) `orders_service` call and turn its
    outcome into a plain-data envelope. This function MUST NEVER RAISE -
    that is the entire point of this exercise. Any ServiceError is caught
    here and converted into a dict the caller (and eventually the model) can
    reason about instead of crashing on.

    Returns:
        On success: {"isError": False, ...order fields}
        On failure: {"isError": True, "isRetryable": bool, "status": int, "error": str}
    """
    try:
        data = orders_service(order_id)
        # ** unpacks the order fields (order_id/status/items/tracking) directly
        # into the top level of the envelope alongside isError=False.
        return {"isError": False, **data}
    except ServiceError as err:
        return {
            "isError": True,
            # Whether this specific status code is worth retrying at all.
            "isRetryable": err.status in RETRYABLE,
            "status": err.status,
            "error": err.message,
        }


def run_with_retry(order_id: str, max_attempts: int = 4) -> dict:
    """
    Call `call_order_tool` up to `max_attempts` times, retrying ONLY when the
    envelope says the failure is retryable, using exponential backoff between
    attempts (0.2s, then 0.4s, then 0.8s, ...).

    Stops immediately (no more retries) as soon as either:
      - the call succeeds (isError is False), or
      - the envelope says isRetryable is False (a permanent error - retrying
        would never help), or
      - max_attempts has been reached (give up rather than retry forever).

    Always returns the last envelope produced by call_order_tool - the caller
    can tell success from failure via envelope["isError"].
    """
    delay = 0.2  # seconds; doubles after every retryable failure below

    for attempt in range(1, max_attempts + 1):
        result = call_order_tool(order_id)

        if not result["isError"]:
            # Success - no need to look at isRetryable at all.
            return result

        if result["isRetryable"] and attempt < max_attempts:
            # Transient failure and we still have attempts left: wait, then
            # try again. Exponential backoff (delay *= 2) means each retry
            # waits longer than the last, so we don't hammer a struggling
            # service with rapid-fire requests.
            time.sleep(delay)
            delay *= 2
            continue

        # Either a permanent error (isRetryable is False) or we've used up
        # every attempt - either way, stop and hand this envelope back as-is.
        return result

    # Unreachable in practice (the loop above always returns), but keeps
    # type-checkers happy about a guaranteed return value.
    return result


# ---------------------------------------------------------------------------
# 3. TOOL SCHEMA + LIVE AGENT LOOP
# ---------------------------------------------------------------------------
# Reuse the strong, regex-constrained order-lookup schema from Exercise 1 so
# both exercises stay consistent about what a well-designed order tool looks
# like.
ORDER_TOOL = {
    "name": "get_order_status",
    "description": (
        "Retrieve the status of an EXISTING customer order by its order ID "
        "(shipping status, items, tracking)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "Order ID in the format 'NP-XXXXXX'.",
                "pattern": "^NP-[0-9]{6}$",
            },
        },
        "required": ["order_id"],
    },
}

SYSTEM_PROMPT = (
    "You are a NorthPeak Outfitters customer-support agent. When asked about "
    "an order, call get_order_status. If the tool result has isError=true and "
    "status=404, tell the customer politely that no such order was found and "
    "ask them to double-check the order number. If the tool result has "
    "isError=true and status=400, tell the customer the order id looks "
    "malformed and ask them to re-send it in the format NP-XXXXXX - do NOT "
    "retry the call yourself. If the tool succeeds, summarize the order "
    "status, items, and tracking number for the customer."
)


def run_agent_turn(user_message: str) -> None:
    """
    Run one full agentic conversation turn for `user_message`, routing every
    get_order_status tool call through run_with_retry (so transient failures
    are retried automatically and permanent ones stop immediately), and
    printing the final assistant reply.

    This mirrors the same stop_reason loop pattern used in Lab 1.2's
    agent_with_hooks.py: append the assistant turn to `messages` BEFORE
    branching on stop_reason, then handle tool_use by collecting all
    tool_result blocks into one follow-up user message.
    """
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            tools=[ORDER_TOOL],
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            final_text = "".join(
                block.text for block in response.content if block.type == "text"
            )
            print(f"Agent: {final_text}")
            return

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use" and block.name == "get_order_status":
                    order_id = block.input["order_id"]
                    # The envelope from run_with_retry never raises - it is
                    # always safe JSON to hand back as a tool_result, whether
                    # it represents success or a (possibly retried) failure.
                    envelope = run_with_retry(order_id)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(envelope),
                            # Marking is_error lets the model's own reasoning
                            # distinguish "here is your order data" from
                            # "this call failed" without us having to parse
                            # the JSON body just to know that much.
                            "is_error": envelope["isError"],
                        }
                    )
            messages.append({"role": "user", "content": tool_results})
            continue

        print(f"Unhandled stop_reason: {response.stop_reason}")
        return


# ---------------------------------------------------------------------------
# 4. OFFLINE SELF-CHECK (--check) - proves the envelope logic without
#    spending any API tokens
# ---------------------------------------------------------------------------
def run_offline_check() -> None:
    print("=== Offline self-check (no API calls) ===\n")

    # --- Case 1: a "good" id that times out once, then succeeds on retry ---
    good_id = "NP-100245"
    first_call = call_order_tool(good_id)
    print(f"1) First call to a good id ({good_id}):")
    print(f"   {first_call}")
    assert first_call["isError"] is True
    assert first_call["isRetryable"] is True
    assert first_call["status"] == 504
    print("   OK: isError=True, isRetryable=True, status=504 (transient timeout)\n")

    retried = run_with_retry(good_id)
    print(f"   run_with_retry({good_id}) result:")
    print(f"   {retried}")
    assert retried["isError"] is False
    print("   OK: retry loop recovered - isError=False on the second attempt\n")

    # --- Case 2: a well-formed id that simply does not exist (404) ---
    not_found = call_order_tool(NOT_FOUND_ID)
    print(f"2) Not-found id ({NOT_FOUND_ID}):")
    print(f"   {not_found}")
    assert not_found["isError"] is True
    assert not_found["isRetryable"] is False
    assert not_found["status"] == 404
    print("   OK: isError=True, isRetryable=False, status=404 (permanent - do not retry)\n")

    # --- Case 3: a malformed id (400) ---
    malformed = call_order_tool(MALFORMED_ID)
    print(f"3) Malformed id ({MALFORMED_ID}):")
    print(f"   {malformed}")
    assert malformed["isError"] is True
    assert malformed["isRetryable"] is False
    assert malformed["status"] == 400
    print("   OK: isError=True, isRetryable=False, status=400 (permanent - do not retry)\n")

    print("All offline checks passed.")


if __name__ == "__main__":
    if "--check" in sys.argv:
        run_offline_check()
    else:
        print("=== LIVE DEMO: three failure shapes over the real agent loop ===")

        print("\n--- (A) Transient timeout that succeeds on retry ---")
        run_agent_turn("Where is my order NP-100245?")

        print("\n--- (B) Permanent 404: order does not exist ---")
        run_agent_turn(f"Can you check on my order {NOT_FOUND_ID}?")

        print("\n--- (C) Permanent 400: malformed order id ---")
        run_agent_turn(f"What's the status of order {MALFORMED_ID}?")
