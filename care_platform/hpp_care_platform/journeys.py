"""
Care & Claims journeys — saga definitions that span agents.

Each journey is a saga whose steps are governed tool calls owned by the relevant
agent. Authority never widens: every step calls the SAME gateway with the SAME
acting-user claims, so a withheld tool stays denied and a high-risk write suspends
the journey at the human gate. These mirror the cross-agent value: a denial that
becomes an appeal and a member notification; an admission that becomes a discharge
draft, a care-plan update, and a follow-up visit; a new member onboarded end to end.
"""
from __future__ import annotations

from typing import Any, Dict

from .canonical import claim_from_payload, subject_from_member
from .consent import ConsentLedger
from .events import ComplianceEventBus
from .govern import GovernedActions
from .saga import JourneySuspended, Saga, Step


def _approval_for(ctx: Dict[str, Any], step: str):
    return (ctx.get("approvals") or {}).get(step)


def denial_to_resolution(gov: GovernedActions, bus: ComplianceEventBus) -> Saga:
    """Agent 01 → 06 → 01 → 08: load denial, validate coding, appeal (gated), notify member (gated)."""
    claims = {"sub": "rcm-1", "custom:hpp_role": "DENIALS_SPECIALIST"}
    mem_claims = {"sub": "msr-1", "custom:hpp_role": "MEMBER_SERVICES_REP"}

    def load(ctx):
        r = gov.call(claims=claims, agent_id="01-revenue-cycle-denial", tool="pas.get_claim",
                     args={"claim_ref": ctx["claim_ref"]})
        ctx["claim"] = claim_from_payload(r.result or {})

    def validate(ctx):
        gov.call(claims={"sub": "coder-1", "custom:hpp_role": "CODING_SPECIALIST"},
                 agent_id="06-payment-integrity-coding", tool="coding.validate_codes",
                 args={"cpt": ctx["claim"].cpt, "icd10": ctx["claim"].icd10})

    def appeal(ctx):
        r = gov.call(claims=claims, agent_id="01-revenue-cycle-denial", tool="payer.submit_appeal",
                     args={"claim_ref": ctx["claim_ref"], "level": 1},
                     approval=_approval_for(ctx, "appeal"))
        if r.decision == "PENDING_APPROVAL":
            raise JourneySuspended("appeal", "denials-specialist approval required")
        ctx["appeal_ref"] = (r.result or {}).get("appeal_ref")

    def notify(ctx):
        r = gov.call(claims=mem_claims, agent_id="08-contact-center-member-services",
                     tool="contactcenter.log_interaction",
                     args={"channel": "outbound", "member_ref": ctx.get("member_ref", "MBR-30551")},
                     approval=_approval_for(ctx, "notify"))
        if r.decision == "PENDING_APPROVAL":
            raise JourneySuspended("notify", "member-services rep approval required")

    return Saga("denial_to_resolution", [
        Step("load", "01-revenue-cycle-denial", load),
        Step("validate", "06-payment-integrity-coding", validate),
        Step("appeal", "01-revenue-cycle-denial", appeal),
        Step("notify", "08-contact-center-member-services", notify),
    ], bus)


def admission_to_followup(gov: GovernedActions, bus: ComplianceEventBus) -> Saga:
    """Agent 05 → 03 → 07 → 04: UM review, discharge draft (gated), care-plan update (gated), follow-up (gated)."""
    def um(ctx):
        gov.call(claims={"sub": "um-1", "custom:hpp_role": "UM_NURSE"},
                 agent_id="05-utilization-management", tool="clinicalcriteria.evaluate",
                 args={"service": "inpatient admission", "meets": True})

    def discharge(ctx):
        r = gov.call(claims={"sub": "ma-1", "custom:hpp_role": "CLINICAL_STAFF"},
                     agent_id="03-clinical-administration", tool="ehr.draft_note",
                     args={"encounter_ref": ctx.get("encounter_ref", "ENC-88231")},
                     approval=_approval_for(ctx, "discharge"))
        if r.decision == "PENDING_APPROVAL":
            raise JourneySuspended("discharge", "clinician sign-off required")

    def care_plan(ctx):
        r = gov.call(claims={"sub": "cm-1", "custom:hpp_role": "CARE_MANAGER"},
                     agent_id="07-care-management-pophealth", tool="careplan.update_care_plan",
                     args={"patient_ref": ctx.get("subject_ref", "PT-40012")},
                     approval=_approval_for(ctx, "care_plan"))
        if r.decision == "PENDING_APPROVAL":
            raise JourneySuspended("care_plan", "care-manager sign-off required")

    def followup(ctx):
        r = gov.call(claims={"sub": "access-1", "custom:hpp_role": "PATIENT_ACCESS_REP"},
                     agent_id="04-patient-access", tool="scheduling.book_appointment",
                     args={"service": "follow-up", "slot": "2026-07-01T11:15"},
                     approval=_approval_for(ctx, "followup"))
        if r.decision == "PENDING_APPROVAL":
            raise JourneySuspended("followup", "access-rep approval required")

    return Saga("admission_to_followup", [
        Step("um_review", "05-utilization-management", um),
        Step("discharge", "03-clinical-administration", discharge),
        Step("care_plan", "07-care-management-pophealth", care_plan),
        Step("followup", "04-patient-access", followup),
    ], bus)


def new_member_onboarding(gov: GovernedActions, bus: ComplianceEventBus) -> Saga:
    """Agent 04 → 04 → 07: verify member eligibility, register (gated), identify care gaps."""
    access = {"sub": "access-1", "custom:hpp_role": "PATIENT_ACCESS_REP"}

    def eligibility(ctx):
        r = gov.call(claims=access, agent_id="04-patient-access", tool="payer.check_eligibility",
                     args={"member_ref": ctx.get("member_ref", "MBR-30551")})
        ctx["subject"] = subject_from_member(r.result or {})

    def register(ctx):
        r = gov.call(claims=access, agent_id="04-patient-access", tool="registration.create_registration",
                     args={"patient_ref": ctx.get("subject_ref", "PT-40099")},
                     approval=_approval_for(ctx, "register"))
        if r.decision == "PENDING_APPROVAL":
            raise JourneySuspended("register", "access-rep approval required")

    def gaps(ctx):
        gov.call(claims={"sub": "cm-1", "custom:hpp_role": "CARE_MANAGER"},
                 agent_id="07-care-management-pophealth", tool="careplan.identify_gaps",
                 args={"patient_ref": ctx.get("subject_ref", "PT-40012")})

    return Saga("new_member_onboarding", [
        Step("eligibility", "04-patient-access", eligibility),
        Step("register", "04-patient-access", register),
        Step("care_gaps", "07-care-management-pophealth", gaps),
    ], bus)


JOURNEYS = {
    "denial_to_resolution": denial_to_resolution,
    "admission_to_followup": admission_to_followup,
    "new_member_onboarding": new_member_onboarding,
}
