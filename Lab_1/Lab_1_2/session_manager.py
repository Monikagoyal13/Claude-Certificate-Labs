import json
import os
import sys
import uuid

import anthropic
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(override=True)

client = anthropic.Anthropic()

SESSIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions")


def new_session():
    return {
        "id": uuid.uuid4().hex[:6],
        "parent_id": None,
        "messages": [],
        "summary": "",
    }


def add_user(session, text):
    session["messages"].append({"role": "user", "content": text})


def add_assistant(session, text):
    session["messages"].append({"role": "assistant", "content": text})


def save_session(session):
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    path = os.path.join(SESSIONS_DIR, f"{session['id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2)
    print(f"  [save] {len(session['messages'])} messages saved to {path}")
    return path


def resume_session(session_id):
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"No saved session found for id '{session_id}' at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fork_session(parent):
    return {
        "id": uuid.uuid4().hex[:6],
        "parent_id": parent["id"],
        "messages": list(parent["messages"]),
        "summary": parent["summary"],
    }


def summarize_session(session, keep_recent=2):
    messages = session["messages"]
    older = messages[:-keep_recent] if keep_recent else messages
    recent = messages[-keep_recent:] if keep_recent else []

    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in older)

    digest = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=(
            "You are compressing a SOC investigation transcript into a structured digest. "
            "Output exactly three sections, in this order: 'DECISIONS:', 'FACTS:', 'OPEN:'. "
            "Under DECISIONS, list actions taken or agreed. Under FACTS, list concrete "
            "evidence. Under OPEN, list unresolved questions. You must NEVER drop or "
            "paraphrase concrete values — IP addresses, hostnames, usernames, file hashes, "
            "alert IDs, and legal-hold IDs must appear verbatim in the digest."
        ),
        messages=[{"role": "user", "content": transcript}],
    ).content[0].text.strip()

    session["messages"] = recent
    session["summary"] = digest
    return digest


if __name__ == "__main__":
    print("=== DEMO 1: SAVE & RESUME (shift change) ===")
    print("\n-- Day 1, 02:47 EST: Sarah Chen (Tier-1, night shift) --")
    session = new_session()
    add_user(session, "Alert NG-2027-1142 triggered: 8.3GB outbound transfer from research-analyst-laptop-04 to 203.0.113.47 (Singapore, AS65000) at 02:47 EST.")
    add_assistant(session, "Ran SIEM query: no active VPN session during transfer window. Badge swipe log shows owner Maya Iyer left the office at 18:22 EST, well before the transfer.")
    add_user(session, "Leading hypotheses so far: (1) compromised credentials used remotely without VPN, (2) insider exfiltration via unattended unlocked session.")
    saved_id = session["id"]
    save_session(session)
    del session
    print("  (shift ends — session object deleted)")

    print("\n-- Day 2, 08:00 EST: Mike Torres (Tier-2 lead, day shift) --")
    resumed = resume_session(saved_id)
    print(f"  [resume] loaded session {resumed['id']} with {len(resumed['messages'])} messages:")
    for m in resumed["messages"]:
        print(f"    {m['role']}: {m['content']}")

    print("\n\n=== DEMO 2: FORK (parallel hypotheses) ===")
    branch_a = fork_session(resumed)
    branch_b = fork_session(resumed)

    add_user(branch_a, "Branch A - insider threat: pulling HR records for Maya Iyer; flagged a recent voluntary-departure notice filed 3 days before the alert.")
    add_user(branch_b, "Branch B - external APT: captured a memory image of research-analyst-laptop-04; process tree shows an unexpected persistence entry (scheduled task) not present in the gold image.")

    save_session(branch_a)
    save_session(branch_b)

    print(f"\n  branch_a: id={branch_a['id']} parent_id={branch_a['parent_id']} messages={len(branch_a['messages'])}")
    print(f"  branch_b: id={branch_b['id']} parent_id={branch_b['parent_id']} messages={len(branch_b['messages'])}")

    a_texts = [m["content"] for m in branch_a["messages"]]
    b_texts = [m["content"] for m in branch_b["messages"]]
    print(f"  branch_a's HR message present in branch_b? {'Branch A' in ' '.join(b_texts) and 'HR' in ' '.join(b_texts)}")
    print(f"  branch_b's memory-image message present in branch_a? {any('memory image' in t for t in a_texts)}")
    print("  (fork uses list(parent['messages']) — branches diverge independently, confirmed above)")

    print("\n\n=== DEMO 3: SUMMARIZE (bound memory footprint) ===")
    evidence_session = new_session()
    add_user(evidence_session, "Alert NG-2027-1142 opened. Asset: research-analyst-laptop-04.")
    add_assistant(evidence_session, "Captured memory image, SHA256 hash: 9f8a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f.")
    add_user(evidence_session, "Quarantined research-analyst-laptop-04 from the network at 09:15 EST per containment procedure.")
    add_assistant(evidence_session, "Escalated to Legal; case placed under legal hold, hold ID L-2027-44.")
    add_user(evidence_session, "Confirmed outbound IP 203.0.113.47 resolves to a known bulletproof-hosting ASN (AS65000).")
    add_assistant(evidence_session, "Reviewed badge swipe logs: owner Maya Iyer left office at 18:22 EST, no VPN session active during the 02:47 EST transfer.")
    add_user(evidence_session, "HR confirmed Maya Iyer filed a voluntary departure notice 3 days prior to the incident.")
    add_assistant(evidence_session, "Open question: was the departure notice retaliatory or unrelated coincidence? Needs HR interview.")
    add_user(evidence_session, "Latest update: still awaiting EDR full forensic report on research-analyst-laptop-04.")
    add_assistant(evidence_session, "Next step: schedule interview with Maya Iyer and legal counsel present, per hold L-2027-44 requirements.")

    digest = summarize_session(evidence_session, keep_recent=2)
    print(f"\n  messages after summarize: {len(evidence_session['messages'])} (kept most recent 2)")
    print("\n-- DIGEST --")
    print(digest)

    for token in ("NG-2027-1142", "L-2027-44", "9f8a2b3c4d5e6f70", "203.0.113.47"):
        present = token in digest
        print(f"  concrete value survived? {token}: {present}")
