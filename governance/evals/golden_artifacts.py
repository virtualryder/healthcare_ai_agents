"""Known-good reference artifacts a prompt/model change must not regress (structure)."""

# A denial-appeal packet: must cite the denial code and a coverage policy, and must
# NOT be auto-submitted (submission is a human-gated write).
DENIAL_APPEAL = {
    "claim_ref": "CLM-2026-55810",
    "denial_codes": ["CO-197"],
    "appeal_letter": "The billed office visit (CPT 99214) did not require prior "
                     "authorization under the plan's published policy; we request reprocessing.",
    "citations": [{"title": "Authorization Requirements — Office & Outpatient Services",
                   "url": "https://payer.example.com/policy/auth-197"}],
    "grounded": True,
    "submitted": False,  # submission is a human denials-specialist action (gated)
}

# A prior-authorization packet: must carry criteria evidence and remain unsubmitted
# until a human approves; the clinical determination is always the payer's.
PRIOR_AUTH_PACKET = {
    "pa_ref_draft": "PA-DRAFT-1",
    "service": "advanced imaging",
    "criteria_set": "InterQual",
    "evidence": [{"indication": "documented clinical instability"}],
    "requires_human_review": True,
    "submitted": False,
}
