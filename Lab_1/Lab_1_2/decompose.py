import json
import sys

import anthropic
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(override=True)

client = anthropic.Anthropic()

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def ask_claude(system, user, max_tokens, model=DEFAULT_MODEL):
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text.strip()


def run_fixed_intel_digest(overnight_feed, asset_inventory):
    iocs_raw = ask_claude(
        system=(
            "Extract every indicator of compromise as a JSON list of "
            "{type, value, context} objects where type is one of ip/hash/domain/cve. "
            "Return ONLY the JSON array."
        ),
        user=overnight_feed,
        max_tokens=1024,
    )

    matches = ask_claude(
        system=(
            "You are given a list of IoCs and NorthGate Capital's asset inventory. "
            "List every IoC that matches something NorthGate owns or uses. "
            "One bullet per match. If none match, say 'No matches.'"
        ),
        user=f"IoCs:\n{iocs_raw}\n\nAsset inventory:\n{asset_inventory}",
        max_tokens=512,
    )

    exec_brief = ask_claude(
        system=(
            "Write a three-bullet executive brief for the SOC manager's 08:00 standup. "
            "Each bullet must name the asset and the recommended next action."
        ),
        user=f"IoCs:\n{iocs_raw}\n\nMatches:\n{matches}",
        max_tokens=512,
    )

    return {"iocs": iocs_raw, "matches": matches, "exec_brief": exec_brief}


TRIAGE_BRANCHES = {
    "phishing": (
        "You are a phishing-response analyst. Containment: disable clicked links/attachments "
        "and reset any exposed credentials. Evidence: preserve the email headers, sender "
        "infrastructure, and any harvested-credential landing page. Escalate if executives or "
        "finance staff were targeted, or credentials were confirmed entered."
    ),
    "malware": (
        "You are a malware-response analyst. Containment: isolate the infected host from the "
        "network. Evidence: capture the binary hash, persistence mechanism, and process tree. "
        "Escalate if the malware family has known ransomware or wiper behavior."
    ),
    "lateral_movement": (
        "You are a lateral-movement analyst. Containment: disable the compromised credentials "
        "and segment the affected hosts. Evidence: collect authentication logs and the chain of "
        "hosts accessed. Escalate if movement reaches a domain controller or trading system."
    ),
    "data_exfiltration": (
        "You are a data-exfiltration analyst. Containment: quarantine the source host and block "
        "the destination IP. Evidence: log the transfer volume, destination, and time window. "
        "Escalate immediately if the data involves client PII, trading positions, or occurs "
        "outside business hours without an active VPN session."
    ),
    "brute_force": (
        "You are a brute-force/credential-attack analyst. Containment: lock the targeted "
        "accounts and rate-limit or block the source IP. Evidence: capture failed-login counts, "
        "targeted usernames, and source ASN. Escalate if any attempt succeeded or an executive "
        "account was targeted."
    ),
    "false_positive": (
        "You are a triage analyst confirming benign activity. Containment: none required. "
        "Evidence: note why the activity is benign (expected user behavior, known maintenance "
        "window, etc.). Escalate only if new evidence contradicts the false-positive call."
    ),
}


def classify_alert(alert_text):
    labels = ", ".join(TRIAGE_BRANCHES.keys())
    label = ask_claude(
        system=(
            f"Classify this SOC alert into exactly one of these labels: {labels}. "
            "Reply with ONLY the label, nothing else."
        ),
        user=alert_text,
        max_tokens=20,
    ).strip().lower()

    if label not in TRIAGE_BRANCHES:
        return "false_positive"
    return label


def run_adaptive_triage(alert_text):
    branch = classify_alert(alert_text)
    answer = ask_claude(
        system=TRIAGE_BRANCHES[branch],
        user=alert_text,
        max_tokens=512,
    )
    return {"branch": branch, "answer": answer}


if __name__ == "__main__":
    OVERNIGHT_FEED = (
        "02:10 EST - Suspicious hash a3f5e1c9b7d2 (Trojan.GenKD) seen beaconing to "
        "185.220.101.42.\n"
        "02:47 EST - Outbound transfer to external IP 203.0.113.47 (Singapore, AS65000) "
        "from research-analyst-laptop-04.\n"
        "03:15 EST - CVE-2024-31337 actively exploited in the wild against exposed VPN "
        "appliances.\n"
        "03:40 EST - Domain totally-legit-updates.biz flagged as a phishing-kit host."
    )

    ASSET_INVENTORY = (
        "research-analyst-laptop-04 (owner: Maya Iyer, Sr. Equity Research)\n"
        "vpn-gateway-01 (NorthGate primary VPN appliance, same model as CVE-2024-31337 target)\n"
        "trading-prod-01, trading-prod-02 (trading servers)\n"
        "market-data-relay-01 (Reuters/Bloomberg relay)"
    )

    print("=== FIXED THREAT-INTEL DIGEST ===")
    digest = run_fixed_intel_digest(OVERNIGHT_FEED, ASSET_INVENTORY)
    print("\n-- IoCs --")
    print(digest["iocs"])
    print("\n-- Matches --")
    print(digest["matches"])
    print("\n-- Exec Brief --")
    print(digest["exec_brief"])

    print("\n\n=== ADAPTIVE ALERT TRIAGE ===")

    ALERTS = {
        "NG-2027-1142 (expected: data_exfiltration)": (
            "Alert NG-2027-1142: research-analyst-laptop-04 (owner Maya Iyer) transferred "
            "8.3GB to external IP 203.0.113.47 (Singapore, AS65000) at 02:47 EST, outside "
            "business hours, with no active VPN session."
        ),
        "phishing report (expected: phishing)": (
            "User reports receiving an email from 'IT-Helpdesk@northgate-capita1.com' "
            "(note the typo'd domain) asking them to reset their password via a linked "
            "external form. The user clicked the link but is unsure if they entered "
            "credentials."
        ),
        "brute-force alert (expected: brute_force)": (
            "SIEM detected 4,800 failed login attempts across 30 employee accounts in 10 "
            "minutes, all originating from a single external IP 198.51.100.200. No "
            "successful logins recorded yet."
        ),
    }

    for label, alert_text in ALERTS.items():
        result = run_adaptive_triage(alert_text)
        print(f"\n-- {label} --")
        print(f"branch: {result['branch']}")
        print(f"answer: {result['answer']}")
