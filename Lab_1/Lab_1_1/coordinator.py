import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

from subagents import run_classifier, run_crm_enricher, run_drafter, run_validator

TEST_TICKET = (
    "From: sarah.chen@globalcorp.com\n"
    "Subject: Cannot access SSO login — entire team locked out\n"
    "Our team of 40 has been unable to log in via SSO since 09:00 this morning. "
    "We have a client demo in 3 hours. This is completely blocking us."
)
CUSTOMER_EMAIL = "sarah.chen@globalcorp.com"

classification = run_classifier(TEST_TICKET)
print(f"[Classifier] {json.dumps(classification, indent=2)}\n")

crm = run_crm_enricher(CUSTOMER_EMAIL, classification)
print(f"[CRM Enricher] {json.dumps(crm, indent=2)}\n")

draft = run_drafter(TEST_TICKET, classification, crm)
print(f"[Drafter]\n{draft}\n")

verdict = run_validator(draft, classification, crm)
print(f"[Validator] {verdict}")
