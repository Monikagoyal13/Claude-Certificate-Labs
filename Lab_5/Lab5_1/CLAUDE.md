# Lab 5.1 — Managing Context: Preservation, Optimization & Escalation

**Module:** CCA-F Module 5 — Context Management & Reliability
**Scenario:** An e-commerce customer-support agent (multi-turn, multi-order session) for Aarti Sharma (C-1001, Gold tier), who has three orders on file (one delivered, one shipped, one processing).

## What this lab demonstrates

A demo agent that behaves correctly at turn three degrades badly by turn eighteen unless it is explicitly engineered not to. This lab applies three production context-management techniques to one agent so the same code holds up at any session length:

1. **Preservation** — `case_facts.py` pins identity-class facts (customer id, tier) into a `[CASE FACTS]` block re-injected into the system prompt every turn, so critical facts survive even after the early messages that established them are trimmed.
2. **Optimization** — `tool_optimizer.py` routes every tool result through `optimize(tool_name, raw)` against a per-tool whitelist (`RELEVANT_FIELDS`), so a bulky order lookup shrinks to only the fields the current intent needs.
3. **Escalation** — `main.py`'s `SYSTEM_BASE` instructs the agent to ASK a clarifying question on ambiguous requests (e.g. "cancel my order" with two open orders) rather than guess.

## File layout

- `main.py` — chat loop (real Claude tool-use round trip), tool dispatch, and the three labelled demos (`demo_1_case_facts`, `demo_2_tool_optimization`, `demo_3_escalate_ambiguity`), run in sequence.
- `case_facts.py` — the `CaseFacts` store (Demo 1).
- `tool_optimizer.py` — the `RELEVANT_FIELDS` whitelist and `optimize()` (Demo 2).
- `sample_data.py` — mock `CUSTOMERS` / `ORDERS` data and lookup helpers.
- `Document/` — the source lab PDF content (as Markdown).

## Cross-cutting notes

- All three techniques reinforce each other: a verbose tool output can evict the case-facts block from context; missing case facts force the model to guess; and a guess on an ambiguous order is the mistake escalation exists to prevent. Removing any one of the three re-opens a failure mode the others were compensating for.
- The escalation rule lives in the **system prompt**, not as a code guard around a specific tool — a code guard on `cancel_order()` would only catch that one call path, while the model needs to apply "ask when ambiguous" to every intent.
- `optimize()` logs a warning (does not silently pass through) when a tool has no `RELEVANT_FIELDS` entry, so an unconfigured tool can't quietly leak its full raw payload into context.
- Mock data only — no PII, no real account data.
