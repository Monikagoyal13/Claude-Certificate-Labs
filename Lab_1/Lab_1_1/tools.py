import random

PRODUCT_AREAS = ["Billing", "Platform", "Integrations", "Security", "Onboarding"]
SEVERITIES = ["P1-Critical", "P2-High", "P3-Medium", "P4-Low"]
INTENTS = ["Bug", "Question", "Feature Request", "Billing Dispute"]

VOCAB = {
    "product_area": PRODUCT_AREAS,
    "severity": SEVERITIES,
    "intent": INTENTS,
}


def classify_ticket(ticket_text: str, fields_needed: list) -> dict:
    """Simulated classifier. In production this would call a real model or rules engine."""
    return {field: random.choice(VOCAB[field]) for field in fields_needed if field in VOCAB}
