"""
Deterministic fixtures for every HPP system of record.

Each entry maps a connector method to either a static payload or a callable that
shapes a response from the call args. These are synthetic, non-PHI records
designed to exercise the full agent workflow offline — no real patient or member
data. Code sets (ICD-10, CPT, HCPCS) and the NPI shown are illustrative.
"""
from __future__ import annotations

from typing import Any, Dict

from .base import FixtureBackedConnector

# ── EHR / FHIR / Amazon HealthLake ───────────────────────────────────────────
_EHR = {
    "get_patient_summary": lambda a: {
        "patient_ref": a.get("patient_ref", "PT-40012"),
        "age": 58, "sex": "F", "active_problems": ["E11.9 Type 2 diabetes", "I10 Essential hypertension"],
        "active_meds": ["metformin", "lisinopril"], "allergies": ["penicillin"],
        "last_encounter": "2026-05-30",
    },
    "get_encounter": lambda a: {
        "encounter_ref": a.get("encounter_ref", "ENC-88231"),
        "type": "Office Visit (Established Patient)", "date": "2026-06-12",
        "cpt": "99214", "icd10": ["E11.9", "I10"], "provider_npi": "1234567893",
    },
    "get_clinical_docs": lambda a: {
        "encounter_ref": a.get("encounter_ref", "ENC-88231"),
        "documents": [
            {"doc_id": "DOC-1", "type": "Progress Note", "signed": True,
             "snippet": "Patient seen for diabetes follow-up; A1c reviewed; meds adjusted."},
            {"doc_id": "DOC-2", "type": "Order", "signed": True,
             "snippet": "A1c, comprehensive metabolic panel ordered."},
        ],
        "missing_for_billing": [],
    },
    "draft_note": lambda a: {"encounter_ref": a.get("encounter_ref"), "rendered": True,
                             "requires_clinician_signoff": True,
                             "note": "AI draft only; a licensed clinician must review and sign."},
}

# ── Patient accounting / practice management ─────────────────────────────────
_PAS = {
    "get_account": lambda a: {"account_ref": a.get("account_ref", "ACCT-77120"),
                              "guarantor_ref": "GUAR-5521", "balance": 248.00,
                              "financial_class": "Commercial", "plan": "BlueChoice PPO"},
    "get_claim": lambda a: {
        "claim_ref": a.get("claim_ref", "CLM-2026-55810"),
        "status": "Denied", "payer": "BlueChoice PPO", "billed": 312.00, "allowed": 0.0,
        "cpt": ["99214"], "icd10": ["E11.9", "I10"], "service_date": "2026-06-12",
        "denial_codes": ["CO-197"],  # precert/authorization absent
    },
    "update_case": lambda a: {"case_ref": a.get("case_ref", "CASE-30021"),
                              "status": a.get("status", "Updated"), "note_added": True},
}

# ── Clearinghouse / X12 837 / 277 ────────────────────────────────────────────
_CLEARINGHOUSE = {
    "validate_claim": lambda a: {
        "claim_ref": a.get("claim_ref", "CLM-2026-55810"),
        "clean": False,
        "edits": [
            {"edit": "CO-197", "severity": "high",
             "description": "Precertification/authorization absent for the billed service."},
            {"edit": "NPI-MATCH", "severity": "info",
             "description": "Rendering NPI matches roster."},
        ],
        "scrubber": "deterministic-837-preflight",
    },
    "check_claim_status": lambda a: {"claim_ref": a.get("claim_ref", "CLM-2026-55810"),
                                     "x12": "277", "status": "Denied", "category": "F2",
                                     "status_code": "585 Denial",
                                     "payer_control_number": "PCN-99812"},
    "submit_claim": lambda a: {"claim_ref": a.get("claim_ref"), "x12": "837",
                               "status": "Accepted", "ack": "999-A", "submitted_by": a.get("biller")},
}

# ── Payer portal / X12 270/271/278/276/277 / Da Vinci ────────────────────────
_PAYER = {
    "check_eligibility": lambda a: {"member_ref": a.get("member_ref", "MBR-30551"),
                                    "x12": "271",
                                    # an X12 271 may report inactive/terminated coverage
                                    "active": a.get("member_ref", "MBR-30551") != "MBR-INACTIVE",
                                    "plan": "BlueChoice PPO",
                                    "copay": 30.00, "deductible_remaining": 450.00},
    "check_pa_requirement": lambda a: {"service": a.get("service", "72148"),
                                       "pa_required": str(a.get("service", "72148")).upper()
                                                      not in {"99212", "99213", "99214", "99215"},
                                       "source": "Da Vinci CRD",
                                       "note": "E/M office visits do not require PA; advanced imaging, "
                                               "select procedures, and specialty drugs typically do."},
    "submit_pa": lambda a: {"pa_ref": "PA-2026-7741", "x12": "278", "status": "Submitted",
                            "submitted_by": a.get("coordinator"), "expected_turnaround_days": 7},
    "check_pa_status": lambda a: {"pa_ref": a.get("pa_ref", "PA-2026-7741"),
                                  "status": "Approved", "valid_through": "2026-12-31"},
    "submit_appeal": lambda a: {"appeal_ref": "APL-2026-1180", "claim_ref": a.get("claim_ref"),
                                "level": a.get("level", 1), "status": "Submitted",
                                "submitted_by": a.get("reviewer"), "decision_due": "2026-07-15"},
    "check_claim_status": lambda a: {"claim_ref": a.get("claim_ref", "CLM-2026-55810"),
                                     "x12": "277", "status": "Denied", "denial_codes": ["CO-197"]},
    "draft_um_recommendation": lambda a: {"case_ref": a.get("case_ref", "UM-44120"),
                                          "recommendation": a.get("recommendation", "MEETS_CRITERIA"),
                                          "rendered": True, "requires_medical_director": True,
                                          "note": "Recommendation only; a medical director issues any adverse determination."},
    "issue_determination": lambda a: {"case_ref": a.get("case_ref"), "determination": a.get("determination"),
                                      "by": a.get("medical_director"), "issued": "2026-06-24"},
}

# ── Coding / NCCI / medical necessity ────────────────────────────────────────
_CODING = {
    "suggest_codes": lambda a: {"encounter_ref": a.get("encounter_ref", "ENC-88231"),
                                "suggested_cpt": ["99214"], "suggested_icd10": ["E11.9", "I10"],
                                "confidence": 0.93, "requires_coder_review": True},
    "validate_codes": lambda a: {"cpt": a.get("cpt", ["99214"]), "icd10": a.get("icd10", ["E11.9", "I10"]),
                                 "ncci_edits": [], "mue_violations": [], "modifier_issues": [],
                                 "valid": True},
    "check_medical_necessity": lambda a: {"cpt": a.get("cpt", ["99214"]),
                                          "icd10": a.get("icd10", ["E11.9"]),
                                          "policy": "LCD-L34567", "supported": True,
                                          "source": "CMS LCD/NCD coverage database"},
}

# ── Clinical criteria (MCG / InterQual) ──────────────────────────────────────
_CRITERIA = {
    "evaluate": lambda a: {"service": a.get("service", "inpatient admission"),
                           "criteria_set": "InterQual", "meets_criteria": True,
                           "matched_indications": ["clinical instability documented"],
                           "requires_clinician_review": True},
    "get_guideline": lambda a: {"guideline_id": a.get("guideline_id", "MCG-IP-DM"),
                                "title": "Inpatient admission — clinical indications",
                                "url": "https://guidelines.example.org/MCG-IP-DM"},
}

# ── Care management / population health ──────────────────────────────────────
_CAREPLAN = {
    "get_care_plan": lambda a: {"patient_ref": a.get("patient_ref", "PT-40012"),
                                "program": "Chronic Care Management",
                                "goals": ["A1c < 7.0", "BP < 130/80"], "next_review": "2026-07-20"},
    "identify_gaps": lambda a: {"patient_ref": a.get("patient_ref", "PT-40012"),
                                "open_gaps": ["Diabetic eye exam overdue", "Nephropathy screening due"],
                                "risk_score_hcc": 1.24, "rising_risk": True},
    "update_care_plan": lambda a: {"patient_ref": a.get("patient_ref"), "updated": True,
                                   "requires_care_manager_signoff": True},
}

# ── Scheduling ───────────────────────────────────────────────────────────────
_SCHEDULING = {
    "get_availability": lambda a: {"service": a.get("service", "endocrinology"),
                                   "slots": ["2026-06-29T09:00", "2026-06-30T13:30", "2026-07-01T11:15"]},
    "book_appointment": lambda a: {"appointment_ref": "APT-3391", "service": a.get("service"),
                                   "slot": a.get("slot", "2026-06-29T09:00"), "status": "Confirmed"},
}

# ── Registration / patient estimate (No Surprises Act GFE) ───────────────────
_REGISTRATION = {
    "get_registration": lambda a: {"patient_ref": a.get("patient_ref", "PT-40012"),
                                   "demographics_complete": True, "insurance_on_file": True},
    "create_registration": lambda a: {"patient_ref": "PT-40099", "status": "Registered"},
    "estimate_cost": lambda a: {"service": a.get("service", "99214"), "plan": "BlueChoice PPO",
                                "allowed": 142.00, "estimated_patient_responsibility": 30.00,
                                "basis": "Good Faith Estimate (No Surprises Act)",
                                "disclaimer": "Estimate only; actual cost depends on services rendered."},
}

# ── Knowledge base (medical / coverage policy) ───────────────────────────────
_KB = {
    "search_policy": lambda a: [
        {"doc_id": "PAYER-MED-197", "title": "Authorization Requirements — Office & Outpatient Services",
         "snippet": "CO-197 denials cite an absent precertification or authorization for the billed service.",
         "url": "https://payer.example.com/policy/auth-197", "effective": "2026-01-01"},
        {"doc_id": "CMS-LCD-L34567", "title": "Local Coverage Determination — E/M Office Visits",
         "snippet": "Documentation must support the level of service billed.",
         "url": "https://www.cms.gov/medicare-coverage-database/L34567", "effective": "2025-10-01"},
    ],
    "get_article": lambda a: {"doc_id": a.get("doc_id", "PAYER-MED-197"),
                              "title": "Authorization Requirements — Office & Outpatient Services",
                              "body": "When CO-197 is returned, confirm whether the service required prior "
                                      "authorization. If not required, appeal with the payer's own published "
                                      "policy; if required, request a retro-authorization where the plan allows.",
                              "url": "https://payer.example.com/policy/auth-197", "effective": "2026-01-01"},
}

# ── Identity / consent (incl. 42 CFR Part 2) ─────────────────────────────────
_IDENTITY = {
    "verify_patient": lambda a: {"verified": bool(a.get("assertion")), "patient_ref": "PT-40012",
                                 "assurance_level": "IAL2" if a.get("assertion") else "NONE"},
    "verify_member": lambda a: {"verified": bool(a.get("assertion")), "member_ref": "MBR-30551",
                                "assurance_level": "IAL2" if a.get("assertion") else "NONE"},
}
_CONSENT = {
    "check": lambda a: {"subject_ref": a.get("subject_ref", "PT-40012"),
                        "scope": a.get("scope", "treatment_payment_operations"),
                        # A 42 CFR Part 2 (SUD) record requires explicit consent to disclose;
                        # absent it, the gateway-backed check returns granted=False so the agent escalates.
                        "part2_sensitive": bool(a.get("part2_sensitive")),
                        "granted": not bool(a.get("part2_sensitive")), "expires": "2027-01-01"},
    "record": lambda a: {"consent_id": "CNS-7781", "scope": a.get("scope", "disclosure"),
                         "granted": True, "recorded": "2026-06-24"},
}

# ── Intelligent document processing (Amazon Bedrock Data Automation) ─────────
_IDP = {
    "extract_document": lambda a: {"doc_type": a.get("doc_type", "clinical_attachment"),
                                   "fields": {"service_date": "[provided]", "ordering_provider": "[provided]"},
                                   "confidence": 0.9, "low_confidence_fields": []},
    "classify_document": lambda a: {"doc_id": a.get("doc_id", "DOC-1"),
                                    "doc_class": "Progress Note", "phi_present": True},
}

# ── Contact center (Amazon Connect) ──────────────────────────────────────────
_CONTACTCENTER = {
    "get_member": lambda a: {"member_ref": a.get("member_ref", "MBR-30551"),
                             "plan": "BlueChoice PPO", "status": "Active",
                             "open_items": ["Claim CLM-2026-55810 denied"]},
    "log_interaction": lambda a: {"interaction_id": "INT-99021", "channel": a.get("channel", "voice"),
                                  "logged": True},
    "create_grievance": lambda a: {"grievance_id": "GRV-4410", "category": a.get("category", "Claim denial"),
                                   "status": "Open", "ack_due": "2026-06-29",
                                   "requires_human_review": True},
}

_TABLES: Dict[str, Dict[str, Any]] = {
    "ehr": _EHR, "pas": _PAS, "clearinghouse": _CLEARINGHOUSE, "payer": _PAYER,
    "coding": _CODING, "clinicalcriteria": _CRITERIA, "careplan": _CAREPLAN,
    "scheduling": _SCHEDULING, "registration": _REGISTRATION, "kb": _KB,
    "identity": _IDENTITY, "consent": _CONSENT, "idp": _IDP, "contactcenter": _CONTACTCENTER,
}


def build_fixture(kind: str) -> FixtureBackedConnector:
    if kind not in _TABLES:
        raise ValueError(f"no fixture for connector kind {kind!r}")
    return FixtureBackedConnector(kind, _TABLES[kind])
