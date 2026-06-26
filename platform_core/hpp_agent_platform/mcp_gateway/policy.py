"""
MCP authorization policy — the heart of the AgentCore Gateway decision for HPP.

Deny-by-default with **least privilege as an intersection**: a tool call is
permitted only if BOTH the calling agent is granted the tool AND the acting
workforce user (biller, PA nurse, UM physician, member-services rep, care
manager) is entitled to it. An agent can never do more than the human on whose
behalf it acts — even if the agent's own grant list is broader.

  permitted(tool) ⇔ tool ∈ AGENT_TOOL_GRANTS[agent] ∩ ⋃ ROLE_ENTITLEMENTS[user_roles]

High-risk (write / irreversible) tools additionally require a human approval
record before execution. Reads do not. The clinically or financially
consequential actions in a provider/payer setting — submitting a claim to a
clearinghouse, issuing a utilization-management determination, signing a clinical
note — are modeled as high-risk and, in several cases, deliberately *withheld*
from the agent entirely so a licensed human owns the decision. This is the
technical expression of the "AI assists, a human decides" posture that CMS, the
AMA, and state UM-transparency laws expect of automated review.

In production these tables are expressed as Amazon Bedrock AgentCore Gateway
targets + AgentCore Identity scopes (or API Gateway + Lambda authorizer + STS +
Cognito + Cedar/OPA) fed by the organization's IdP. Here they are explicit Python
so the intersection semantics are testable and unambiguous. Tool names
("<connector_kind>.<operation>") map 1:1 to AgentCore Gateway target names.

References: Bedrock AgentCore Gateway / Identity
  https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html
  https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity.html
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Tuple

# ── Tool registry: tool name -> (connector_kind, method, high_risk) ───────────
# high_risk=True => write/irreversible => human-approval gate before execution.
TOOL_REGISTRY: Dict[str, Tuple[str, str, bool]] = {
    # EHR / FHIR / Amazon HealthLake
    "ehr.get_patient_summary":        ("ehr", "get_patient_summary", False),
    "ehr.get_encounter":              ("ehr", "get_encounter", False),
    "ehr.get_clinical_docs":          ("ehr", "get_clinical_docs", False),
    "ehr.draft_note":                 ("ehr", "draft_note", True),                 # write (draft to chart)
    # Patient accounting / practice management
    "pas.get_account":                ("pas", "get_account", False),
    "pas.get_claim":                  ("pas", "get_claim", False),
    "pas.update_case":                ("pas", "update_case", True),                # write (case-mgmt system)
    # Clearinghouse / X12 837/835/277
    "clearinghouse.validate_claim":   ("clearinghouse", "validate_claim", False),  # 837 pre-submission scrub
    "clearinghouse.check_claim_status": ("clearinghouse", "check_claim_status", False),  # 277
    "clearinghouse.submit_claim":     ("clearinghouse", "submit_claim", True),     # write/irreversible
    # Payer portal / X12 270/271/278/276/277 / Da Vinci FHIR
    "payer.check_eligibility":        ("payer", "check_eligibility", False),       # 270/271
    "payer.check_pa_requirement":     ("payer", "check_pa_requirement", False),    # Da Vinci CRD
    "payer.submit_pa":                ("payer", "submit_pa", True),                # 278 / Da Vinci PAS — write
    "payer.check_pa_status":          ("payer", "check_pa_status", False),
    "payer.submit_appeal":            ("payer", "submit_appeal", True),            # write
    "payer.check_claim_status":       ("payer", "check_claim_status", False),      # 276/277
    "payer.draft_um_recommendation":  ("payer", "draft_um_recommendation", True),  # write (recommendation only)
    "payer.issue_determination":      ("payer", "issue_determination", True),      # write/irreversible (medical director)
    # Coding / NCCI / medical necessity (encoder, CMS edits)
    "coding.suggest_codes":           ("coding", "suggest_codes", False),
    "coding.validate_codes":          ("coding", "validate_codes", False),         # NCCI/MUE edits
    "coding.check_medical_necessity": ("coding", "check_medical_necessity", False),  # LCD/NCD
    # Clinical criteria (MCG / InterQual)
    "clinicalcriteria.evaluate":      ("clinicalcriteria", "evaluate", False),
    "clinicalcriteria.get_guideline": ("clinicalcriteria", "get_guideline", False),
    # Care management / population health
    "careplan.get_care_plan":         ("careplan", "get_care_plan", False),
    "careplan.identify_gaps":         ("careplan", "identify_gaps", False),        # risk strat / care gaps
    "careplan.update_care_plan":      ("careplan", "update_care_plan", True),      # write
    # Scheduling / appointments
    "scheduling.get_availability":    ("scheduling", "get_availability", False),
    "scheduling.book_appointment":    ("scheduling", "book_appointment", True),    # write
    # Registration / patient estimate (No Surprises Act Good Faith Estimate)
    "registration.get_registration":  ("registration", "get_registration", False),
    "registration.create_registration": ("registration", "create_registration", True),  # write
    "registration.estimate_cost":     ("registration", "estimate_cost", False),    # deterministic GFE
    # Knowledge base (medical policy / coverage policy / clinical guidelines)
    "kb.search_policy":               ("kb", "search_policy", False),
    "kb.get_article":                 ("kb", "get_article", False),
    # Identity / consent (incl. 42 CFR Part 2 sensitive-data consent)
    "identity.verify_patient":        ("identity", "verify_patient", False),
    "identity.verify_member":         ("identity", "verify_member", False),
    "consent.check":                  ("consent", "check", False),
    "consent.record":                 ("consent", "record", True),                 # write
    # Intelligent document processing (Amazon Bedrock Data Automation)
    "idp.extract_document":           ("idp", "extract_document", False),
    "idp.classify_document":          ("idp", "classify_document", False),
    # Contact center (Amazon Connect)
    "contactcenter.get_member":       ("contactcenter", "get_member", False),
    "contactcenter.log_interaction":  ("contactcenter", "log_interaction", True),  # write
    "contactcenter.create_grievance": ("contactcenter", "create_grievance", True), # write
}

HIGH_RISK_TOOLS: FrozenSet[str] = frozenset(t for t, (_, _, hr) in TOOL_REGISTRY.items() if hr)

# ── What each AGENT is allowed to call (its job description as code) ───────────
# Note the deliberate omissions: agents may PREPARE but not COMMIT the clinically
# or financially consequential action. The revenue-cycle agent cannot
# submit_claim (a biller submits); the UM agent cannot issue_determination (a
# medical director decides); no agent holds issue_determination at all.
AGENT_TOOL_GRANTS: Dict[str, FrozenSet[str]] = {
    "01-revenue-cycle-denial": frozenset({
        "clearinghouse.validate_claim", "clearinghouse.check_claim_status",
        "payer.check_claim_status", "payer.submit_appeal",
        "pas.get_claim", "pas.get_account", "pas.update_case",
        "coding.validate_codes", "coding.check_medical_necessity",
        "ehr.get_clinical_docs", "idp.extract_document", "kb.search_policy",
    }),  # NOTE: no clearinghouse.submit_claim — claim submission is a biller decision
    "02-prior-authorization": frozenset({
        "payer.check_pa_requirement", "payer.submit_pa", "payer.check_pa_status",
        "clinicalcriteria.evaluate", "clinicalcriteria.get_guideline",
        "coding.check_medical_necessity",
        "ehr.get_patient_summary", "ehr.get_clinical_docs",
        "idp.extract_document", "kb.search_policy",
    }),
    "03-clinical-administration": frozenset({
        "ehr.get_patient_summary", "ehr.get_encounter", "ehr.get_clinical_docs",
        "ehr.draft_note", "careplan.get_care_plan", "scheduling.get_availability",
        "kb.search_policy", "idp.extract_document", "consent.check",
    }),  # NOTE: draft_note is a draft only — a clinician signs; no order entry
    "04-patient-access": frozenset({
        "scheduling.get_availability", "scheduling.book_appointment",
        "registration.get_registration", "registration.create_registration",
        "registration.estimate_cost", "payer.check_eligibility",
        "identity.verify_patient", "consent.check", "kb.search_policy",
    }),
    "05-utilization-management": frozenset({
        "clinicalcriteria.evaluate", "clinicalcriteria.get_guideline",
        "coding.check_medical_necessity", "payer.check_pa_status",
        "payer.draft_um_recommendation", "ehr.get_clinical_docs", "kb.search_policy",
    }),  # NOTE: no payer.issue_determination — adverse determination is a medical-director decision
    "06-payment-integrity-coding": frozenset({
        "coding.suggest_codes", "coding.validate_codes", "coding.check_medical_necessity",
        "pas.get_claim", "pas.update_case", "clearinghouse.validate_claim",
        "ehr.get_clinical_docs", "kb.search_policy",
    }),  # NOTE: no recoupment/submit — flags for human payment-integrity review only
    "07-care-management-pophealth": frozenset({
        "careplan.get_care_plan", "careplan.identify_gaps", "careplan.update_care_plan",
        "ehr.get_patient_summary", "kb.search_policy", "consent.check",
    }),
    "08-contact-center-member-services": frozenset({
        "contactcenter.get_member", "contactcenter.log_interaction",
        "contactcenter.create_grievance", "payer.check_claim_status",
        "payer.check_eligibility", "identity.verify_member", "consent.check",
        "kb.search_policy",
    }),
}

# ── What each USER ROLE is entitled to (the workforce member's real permissions) ─
# Base roles mirror an agent's grant set. Elevated roles additionally hold the
# withheld, irreversible authority (submit a claim, issue a UM determination,
# sign a note) — so an agent acting for a base role can never reach them.
ROLE_ENTITLEMENTS: Dict[str, FrozenSet[str]] = {
    "DENIALS_SPECIALIST": frozenset({
        "clearinghouse.validate_claim", "clearinghouse.check_claim_status",
        "payer.check_claim_status", "payer.submit_appeal",
        "pas.get_claim", "pas.get_account", "pas.update_case",
        "coding.validate_codes", "coding.check_medical_necessity",
        "ehr.get_clinical_docs", "idp.extract_document", "kb.search_policy",
    }),
    "DENIALS_MANAGER": frozenset({  # specialist + the irreversible claim submission
        "clearinghouse.validate_claim", "clearinghouse.check_claim_status",
        "clearinghouse.submit_claim", "payer.check_claim_status", "payer.submit_appeal",
        "pas.get_claim", "pas.get_account", "pas.update_case",
        "coding.validate_codes", "coding.check_medical_necessity",
        "ehr.get_clinical_docs", "idp.extract_document", "kb.search_policy",
    }),
    "PA_COORDINATOR": frozenset({
        "payer.check_pa_requirement", "payer.submit_pa", "payer.check_pa_status",
        "clinicalcriteria.evaluate", "clinicalcriteria.get_guideline",
        "coding.check_medical_necessity", "ehr.get_patient_summary",
        "ehr.get_clinical_docs", "idp.extract_document", "kb.search_policy",
    }),
    "CLINICAL_STAFF": frozenset({
        "ehr.get_patient_summary", "ehr.get_encounter", "ehr.get_clinical_docs",
        "ehr.draft_note", "careplan.get_care_plan", "scheduling.get_availability",
        "kb.search_policy", "idp.extract_document", "consent.check",
    }),
    "PROVIDER": frozenset({  # clinical staff set; a provider co-signs notes downstream
        "ehr.get_patient_summary", "ehr.get_encounter", "ehr.get_clinical_docs",
        "ehr.draft_note", "careplan.get_care_plan", "scheduling.get_availability",
        "kb.search_policy", "idp.extract_document", "consent.check",
    }),
    "PATIENT_ACCESS_REP": frozenset({
        "scheduling.get_availability", "scheduling.book_appointment",
        "registration.get_registration", "registration.create_registration",
        "registration.estimate_cost", "payer.check_eligibility",
        "identity.verify_patient", "consent.check", "kb.search_policy",
    }),
    "UM_NURSE": frozenset({
        "clinicalcriteria.evaluate", "clinicalcriteria.get_guideline",
        "coding.check_medical_necessity", "payer.check_pa_status",
        "payer.draft_um_recommendation", "ehr.get_clinical_docs", "kb.search_policy",
    }),
    "UM_MEDICAL_DIRECTOR": frozenset({  # nurse set + the irreversible determination
        "clinicalcriteria.evaluate", "clinicalcriteria.get_guideline",
        "coding.check_medical_necessity", "payer.check_pa_status",
        "payer.draft_um_recommendation", "payer.issue_determination",
        "ehr.get_clinical_docs", "kb.search_policy",
    }),
    "CODING_SPECIALIST": frozenset({
        "coding.suggest_codes", "coding.validate_codes", "coding.check_medical_necessity",
        "pas.get_claim", "pas.update_case", "clearinghouse.validate_claim",
        "ehr.get_clinical_docs", "kb.search_policy",
    }),
    "CARE_MANAGER": frozenset({
        "careplan.get_care_plan", "careplan.identify_gaps", "careplan.update_care_plan",
        "ehr.get_patient_summary", "kb.search_policy", "consent.check",
    }),
    "MEMBER_SERVICES_REP": frozenset({
        "contactcenter.get_member", "contactcenter.log_interaction",
        "contactcenter.create_grievance", "payer.check_claim_status",
        "payer.check_eligibility", "identity.verify_member", "consent.check",
        "kb.search_policy",
    }),
    "BILLER": frozenset({  # the workforce role that actually submits claims
        "clearinghouse.validate_claim", "clearinghouse.check_claim_status",
        "clearinghouse.submit_claim", "pas.get_claim", "pas.get_account",
        "kb.search_policy",
    }),
}


@dataclass
class PolicyDecision:
    allowed: bool
    tool: str
    reason: str
    requires_approval: bool = False
    connector_kind: str = ""
    method: str = ""
    effective_scope: List[str] = field(default_factory=list)  # exactly this tool


def user_entitlements(roles: Iterable[str]) -> FrozenSet[str]:
    out: set = set()
    for r in roles:
        out |= ROLE_ENTITLEMENTS.get(r, frozenset())
    return frozenset(out)


def decide(agent_id: str, user_roles: Iterable[str], tool: str) -> PolicyDecision:
    """Deny-by-default authorization with least-privilege intersection."""
    if tool not in TOOL_REGISTRY:
        return PolicyDecision(False, tool, f"unknown tool {tool!r}")

    connector_kind, method, high_risk = TOOL_REGISTRY[tool]
    agent_grants = AGENT_TOOL_GRANTS.get(agent_id, frozenset())
    if tool not in agent_grants:
        return PolicyDecision(False, tool,
                              f"agent {agent_id!r} is not granted {tool!r} (agent over-reach denied)",
                              connector_kind=connector_kind, method=method)

    ent = user_entitlements(user_roles)
    if tool not in ent:
        return PolicyDecision(False, tool,
                              f"acting user (roles={list(user_roles)}) is not entitled to {tool!r} "
                              f"(an agent may never exceed the user's own permissions)",
                              connector_kind=connector_kind, method=method)

    return PolicyDecision(
        True, tool,
        "permitted by agent grant ∩ user entitlement",
        requires_approval=tool in HIGH_RISK_TOOLS,
        connector_kind=connector_kind, method=method,
        effective_scope=[tool],
    )
