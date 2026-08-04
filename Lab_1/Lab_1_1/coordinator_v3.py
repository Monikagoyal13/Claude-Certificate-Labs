import sys

sys.stdout.reconfigure(encoding="utf-8")

from context import TicketContext
from gates import PipelineGateError, gate_classification, gate_draft, gate_enrichment
from subagents import run_classifier, run_crm_enricher, run_drafter, run_validator

TEST_TICKET = (
    "From: sarah.chen@globalcorp.com\n"
    "Subject: Cannot access SSO login — entire team locked out\n"
    "Our team of 40 has been unable to log in via SSO since 09:00 this morning. "
    "We have a client demo in 3 hours. This is completely blocking us."
)

ctx = TicketContext(
    ticket_id="TICKET-001",
    raw_ticket=TEST_TICKET,
    customer_email="sarah.chen@globalcorp.com",
)

try:
    classification = run_classifier(ctx.raw_ticket)
    ctx.product_area = classification["product_area"]
    ctx.severity = classification["severity"]
    ctx.intent = classification["intent"]
    print(f"[Classifier] product_area={ctx.product_area}, severity={ctx.severity}, intent={ctx.intent}\n")

    gate_classification(ctx)
    print("Gate 1 passed\n")

    crm = run_crm_enricher(ctx.customer_email, classification)
    ctx.account_tier = crm["account_tier"]
    ctx.sla_tier = crm["sla_tier"]
    ctx.account_manager = crm["account_manager"]
    print(f"[CRM Enricher] account_tier={ctx.account_tier}, sla_tier={ctx.sla_tier}, account_manager={ctx.account_manager}\n")

    gate_enrichment(ctx)
    print("Gate 2 passed\n")

    ctx.draft_response = run_drafter(ctx.raw_ticket, classification, crm)
    print(f"[Drafter]\n{ctx.draft_response}\n")

    gate_draft(ctx)
    print("Gate 3 passed\n")

    ctx.validation_result = run_validator(ctx.draft_response, classification, crm)
    print(f"[Validator] {ctx.validation_result}\n")

    print("=== Final TicketContext ===")
    print(ctx)

except PipelineGateError as e:
    print(f"[PIPELINE BLOCKED] {e}")
