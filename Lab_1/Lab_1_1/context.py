from dataclasses import dataclass
from typing import Optional


@dataclass
class TicketContext:
    # Required at intake
    ticket_id: str
    raw_ticket: str
    customer_email: str

    # Populated by Classifier
    product_area: Optional[str] = None
    severity: Optional[str] = None
    intent: Optional[str] = None

    # Populated by CRM Enricher
    account_tier: Optional[str] = None
    sla_tier: Optional[str] = None
    account_manager: Optional[str] = None

    # Populated by Drafter and Validator
    draft_response: Optional[str] = None
    validation_result: Optional[str] = None

    def classification_complete(self) -> bool:
        return all(
            field is not None
            for field in (self.product_area, self.severity, self.intent)
        )

    def enrichment_complete(self) -> bool:
        return self.account_tier is not None and self.sla_tier is not None

    def draft_complete(self) -> bool:
        return self.draft_response is not None
