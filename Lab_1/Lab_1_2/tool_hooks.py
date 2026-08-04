import ipaddress

PROTECTED_HOSTS = [
    "trading-prod-01",
    "trading-prod-02",
    "market-data-relay-01",
    "market-data-relay-02",
    "exec-laptop-ceo",
    "exec-laptop-cfo",
]

PROTECTED_IPS = [
    "198.51.100.10",  # Reuters market-data
    "198.51.100.11",  # Bloomberg terminal
    "192.0.2.55",  # prime-broker API
    "192.0.2.56",  # clearing-house webhook
]


def logging_hook(tool_name, tool_input):
    print(f"  [log] {tool_name}({list(tool_input.keys())})")
    return True, ""


def arg_validation_hook(tool_name, tool_input):
    if tool_name == "block_ip":
        ip = tool_input.get("ip")
        if not ip:
            return False, "arg_validation: block_ip requires 'ip'"
        try:
            ipaddress.IPv4Address(ip)
        except ValueError:
            return False, f"arg_validation: '{ip}' is not a valid IPv4 address"
    elif tool_name == "quarantine_host":
        if not tool_input.get("hostname"):
            return False, "arg_validation: quarantine_host requires 'hostname'"
    elif tool_name == "disable_user":
        if not tool_input.get("username"):
            return False, "arg_validation: disable_user requires 'username'"
    return True, ""


def protected_asset_hook(tool_name, tool_input):
    if tool_name == "quarantine_host":
        hostname = tool_input.get("hostname", "")
        if hostname in PROTECTED_HOSTS:
            return False, f"protected_asset: '{hostname}' is a protected production host"
    elif tool_name == "block_ip":
        ip = tool_input.get("ip", "")
        if ip in PROTECTED_IPS:
            return False, f"protected_asset: '{ip}' is a protected market-data/broker IP"
    elif tool_name == "disable_user":
        username = tool_input.get("username", "")
        if username in ("ceo", "cfo", "ciso") or username.endswith("@northgate-exec"):
            return False, f"protected_asset: '{username}' is an executive account requiring dual approval"
    return True, ""


def run_tool(tool_name, tool_input, tool_fn, hooks, audit_log):
    for hook in hooks:
        allowed, reason = hook(tool_name, tool_input)
        if not allowed:
            audit_log.append(
                {"tool": tool_name, "input": tool_input, "status": "BLOCKED", "reason": reason}
            )
            print(f"  [BLOCKED] {tool_name}({tool_input}) — {reason}")
            return f"BLOCKED by policy: {reason}"

    audit_log.append(
        {"tool": tool_name, "input": tool_input, "status": "allowed", "reason": ""}
    )
    return tool_fn(tool_input)


def print_audit_log(audit_log):
    print("\n=== AUDIT LOG ===")
    for i, entry in enumerate(audit_log, start=1):
        reason = f" — {entry['reason']}" if entry["reason"] else ""
        print(f"{i}. [{entry['status']}] {entry['tool']}({entry['input']}){reason}")


def _sim_block_ip(tool_input):
    return f"[Firewall] IP {tool_input.get('ip')} added to deny-list (simulated)"


def _sim_quarantine_host(tool_input):
    return f"[EDR] Host {tool_input.get('hostname')} isolated from network (simulated)"


def _sim_disable_user(tool_input):
    return f"[IAM] User {tool_input.get('username')} disabled (simulated)"


def _sim_query_siem(tool_input):
    return f"[SIEM] Query '{tool_input.get('query')}' returned 0 new matches (simulated)"


DEMO_TOOLS = {
    "block_ip": _sim_block_ip,
    "quarantine_host": _sim_quarantine_host,
    "disable_user": _sim_disable_user,
    "query_siem": _sim_query_siem,
}


if __name__ == "__main__":
    hooks = [logging_hook, arg_validation_hook, protected_asset_hook]
    audit_log = []

    attempts = [
        ("quarantine_host", {"hostname": "research-analyst-laptop-04"}),  # ALLOWED
        ("quarantine_host", {"hostname": "trading-prod-01"}),  # policy-block
        ("block_ip", {"ip": "not-an-ip"}),  # arg-validation block
        ("disable_user", {"username": ""}),  # arg-validation block
        ("disable_user", {"username": "ceo"}),  # exec-account block
    ]

    for tool_name, tool_input in attempts:
        print(f"\nAttempting: {tool_name}({tool_input})")
        result = run_tool(tool_name, tool_input, DEMO_TOOLS[tool_name], hooks, audit_log)
        print(f"  -> {result}")

    print_audit_log(audit_log)
