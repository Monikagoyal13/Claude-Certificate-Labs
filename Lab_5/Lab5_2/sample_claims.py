"""Mock insurance claims for Lab 5.2 (Resilient Systems).

All values are fictional dummy data - synthetic member ids, no PHI, no real
medical records. CLM-001 and CLM-003 are well-formed and should sail through
the pipeline; CLM-002 is for an inactive member and is deliberately malformed
so it fails validation.
"""

COVERED_PROCEDURES = {"CPT-99213", "CPT-99214", "CPT-93000"}

CLAIMS = [
    {
        "claim_id": "CLM-001",
        "member_id": "M-501",
        "member_active": True,
        "procedure_code": "CPT-99213",
        "amount": 150.00,
        "narrative": (
            "Member M-501 seen for a routine office visit, established "
            "patient, level 3 evaluation and management (CPT-99213). "
            "Total billed amount $150.00."
        ),
    },
    {
        "claim_id": "CLM-002",
        "member_id": "M-777",
        "member_active": False,
        "procedure_code": "CPT-99214",
        "amount": 220.00,
        "narrative": (
            "Member M-777 seen for a follow-up office visit, established "
            "patient, level 4 evaluation and management (CPT-99214). "
            "Total billed amount $220.00. Note: member's coverage lapsed "
            "at the end of the prior billing cycle."
        ),
    },
    {
        "claim_id": "CLM-003",
        "member_id": "M-501",
        "member_active": True,
        "procedure_code": "CPT-93000",
        "amount": 2500.00,
        "narrative": (
            "Member M-501 seen for a diagnostic electrocardiogram "
            "(CPT-93000) following a referral for chest pain. Total "
            "billed amount $2500.00."
        ),
    },
]
