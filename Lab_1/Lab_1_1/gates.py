class PipelineGateError(Exception):
    pass


def gate_classification(ctx) -> None:
    if not ctx.classification_complete():
        missing = [
            name
            for name, value in (
                ("product_area", ctx.product_area),
                ("severity", ctx.severity),
                ("intent", ctx.intent),
            )
            if value is None
        ]
        raise PipelineGateError(
            f"Classification incomplete — missing fields: {', '.join(missing)}. "
            "Rerun the Classifier before proceeding."
        )


def gate_enrichment(ctx) -> None:
    if not ctx.enrichment_complete():
        missing = [
            name
            for name, value in (
                ("account_tier", ctx.account_tier),
                ("sla_tier", ctx.sla_tier),
            )
            if value is None
        ]
        raise PipelineGateError(
            f"Enrichment incomplete — missing fields: {', '.join(missing)}. "
            "Rerun the CRM Enricher before proceeding."
        )


def gate_draft(ctx) -> None:
    if not ctx.draft_complete():
        raise PipelineGateError(
            "Draft incomplete — draft_response is None. Rerun the Drafter before proceeding."
        )
