import json

import anthropic
from dotenv import load_dotenv

load_dotenv(override=True)

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-5-20250929"


def _parse_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    return json.loads(cleaned)


def run_classifier(ticket: str) -> dict:
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=(
            "Classify the support ticket into product_area, severity, and intent. "
            "product_area is one of: Billing, Platform, Integrations, Security, Onboarding. "
            "severity is one of: P1-Critical, P2-High, P3-Medium, P4-Low. "
            "intent is one of: Bug, Question, Feature Request, Billing Dispute. "
            "Respond only in JSON with exactly these three keys, no other text."
        ),
        messages=[{"role": "user", "content": ticket}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return _parse_json(text)


def run_crm_enricher(customer_email: str, classification: dict) -> dict:
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=(
            "Simulate a CRM lookup for a B2B SaaS customer. Given a customer email and their "
            "ticket classification, fabricate a plausible CRM record. Respond only in JSON with "
            "exactly these keys: account_tier, sla_tier, account_manager, contract_value."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"Customer email: {customer_email}\n"
                    f"Ticket classification: {json.dumps(classification)}"
                ),
            }
        ],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return _parse_json(text)


def run_drafter(ticket: str, classification: dict, crm: dict) -> str:
    context = (
        f"Ticket:\n{ticket}\n\n"
        f"Classification: {json.dumps(classification)}\n\n"
        f"CRM data: {json.dumps(crm)}"
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=(
            "Draft a professional first-response email to the customer for this support ticket. "
            "Reference the customer's SLA tier explicitly. The reply should be ready for a human "
            "reviewer to send or edit."
        ),
        messages=[{"role": "user", "content": context}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def run_validator(draft: str, classification: dict, crm: dict) -> str:
    context = (
        f"Draft response:\n{draft}\n\n"
        f"Expected product area: {classification.get('product_area')}\n"
        f"Customer SLA tier: {crm.get('sla_tier')}\n"
        f"Customer account tier: {crm.get('account_tier')}"
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=(
            "Check that the draft response references the correct product area, matches the "
            "customer's SLA tier, and meets professional SLA tone requirements. Reply with "
            "exactly 'APPROVED' if all checks pass, otherwise list the specific issues."
        ),
        messages=[{"role": "user", "content": context}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
