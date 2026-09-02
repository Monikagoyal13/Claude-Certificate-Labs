# Lab 5.1 — Managing Context: Preservation, Optimization & Escalation

CCA-F | Module 5 · ~45 minutes hands-on · Python 3.10+ · `anthropic` + `python-dotenv`

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # then paste your key into .env
```

`.env`:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
MODEL_NAME=claude-sonnet-4-6
```

Run everything:

```bash
python main.py
```

Costs are minimal — a full run is about a dozen short turns plus two tool calls. `sample_data.py` contains one fictional customer (Aarti Sharma, C-1001, Gold tier) and three dummy orders — no PII, no real account data.

## Demos

`main.py` runs all three demos in sequence, each printed under its own banner.

### Demo 1 — Persistent case facts (`demo_1_case_facts`)

Pins `customer_id` and `tier` into a `CaseFacts` store, then runs three unrelated small-talk turns (store hours, shipping, payment) followed by "what is my customer ID and what tier am I?". The `[CASE FACTS]` block (`case_facts.py`) is re-injected into the system prompt on every turn, so the agent answers correctly even though no earlier turn ever stated those values in the conversation itself.

**What good looks like:** the final reply names `C-1001` and `Gold` verbatim, without a tool call.

### Demo 2 — Tool output optimization (`demo_2_tool_optimization`)

Prints the RAW `lookup_orders` result (full order records, including line items) next to the OPTIMIZED result after `optimize()` (`tool_optimizer.py`) trims it to the `RELEVANT_FIELDS` whitelist (`order_id`, `status`, `placed_on`, `total`), then has the agent answer using only the optimized version.

**What good looks like:** the OPTIMIZED block is visibly smaller than RAW, and the agent's reply uses only the whitelisted fields.

### Demo 3 — Ambiguity escalation (`demo_3_escalate_ambiguity`)

Aarti has two open orders (O-9002 Shipped, O-9003 Processing). The customer sends a bare "Please cancel my order." with no order id specified. The `SYSTEM_BASE` system prompt in `main.py` instructs the agent to ASK on ambiguity instead of guessing.

**What good looks like:** the agent looks up the open orders and replies with a clarifying question naming both order ids — not a unilateral cancellation.

## Try breaking it

- Comment out the `facts_block` append in `chat()` and re-run Demo 1 — the agent will lose track of the customer id/tier.
- Remove the "if a request is ambiguous ... ASK" sentence from `SYSTEM_BASE` and re-run Demo 3 — the agent will typically guess an order instead of asking.

## Reflection

See `Document/Lab_5_1_Context_Management_CCA-F.md` §5 for the full self-check questions and common-mistakes table.
