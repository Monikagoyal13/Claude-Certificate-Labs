import json

import anthropic
from dotenv import load_dotenv

from tool_hooks import DEMO_TOOLS, arg_validation_hook, logging_hook, print_audit_log, protected_asset_hook, run_tool

load_dotenv(override=True)

client = anthropic.Anthropic()

MODEL = "claude-opus-4-8"

HOOKS = [logging_hook, arg_validation_hook, protected_asset_hook]

TOOLS = [
    {
        "name": "quarantine_host",
        "description": "Isolate a host from the network via EDR.",
        "input_schema": {
            "type": "object",
            "properties": {"hostname": {"type": "string"}},
            "required": ["hostname"],
        },
    },
    {
        "name": "block_ip",
        "description": "Add an IP address to the firewall deny-list.",
        "input_schema": {
            "type": "object",
            "properties": {"ip": {"type": "string"}},
            "required": ["ip"],
        },
    },
    {
        "name": "query_siem",
        "description": "Run a query against the SIEM for supporting evidence.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]

SYSTEM_PROMPT = (
    "You are a Tier-1 SOC analyst copilot at NorthGate Capital, a $4B AUM asset manager. "
    "You have tools to quarantine hosts, block IPs, and query the SIEM. Take the response "
    "actions requested. Some actions may be BLOCKED by policy — if a tool result starts with "
    "'BLOCKED by policy:', do NOT retry that action; accept the block and move on. When all "
    "requested actions have been attempted, write a short incident summary that clearly states "
    "which actions succeeded and which were blocked (and why)."
)

TASK = (
    "Alert NG-2027-1142: research-analyst-laptop-04 (owner Maya Iyer) exfiltrated 8.3GB to "
    "203.0.113.47 outside business hours. Please: "
    "(1) quarantine research-analyst-laptop-04, "
    "(2) block the suspicious IP 203.0.113.47, and "
    "(3) as a precaution, also quarantine trading-prod-01 so the attacker cannot pivot to our "
    "trading systems."
)

audit_log = []
messages = [{"role": "user", "content": TASK}]

iteration = 0
while True:
    iteration += 1
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        messages=messages,
    )
    print(f"[iteration {iteration}] stop_reason = {response.stop_reason}")

    messages.append({"role": "assistant", "content": response.content})

    if response.stop_reason == "end_turn":
        final_text = "".join(block.text for block in response.content if block.type == "text")
        print("\nFinal response:\n" + final_text)
        break

    if response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  -> tool_use: {block.name}({block.input})")
                result = run_tool(block.name, block.input, DEMO_TOOLS[block.name], HOOKS, audit_log)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    }
                )
        messages.append({"role": "user", "content": tool_results})
        continue

    print(f"Unhandled stop_reason: {response.stop_reason}")
    break

print_audit_log(audit_log)
