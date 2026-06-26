"""
Compliance control mappings — which platform control satisfies which obligation.

Each entry ties a healthcare regulatory regime to the concrete platform/AWS
control that addresses it, plus the maturity (Implemented / Configurable /
Customer). A CISO, privacy officer, or HITRUST assessor reads this to see why the
architecture is defensible; a solution architect reads it to know what they must
still configure per customer. Authoritative sources are tracked in SOURCES.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ControlMapping:
    regime: str
    obligation: str
    platform_control: str
    aws_service: str
    status: str  # Implemented | Configurable | Customer


MAPPINGS: List[ControlMapping] = [
    ControlMapping("HIPAA Privacy Rule (45 CFR 164.5xx)", "Minimum necessary use/disclosure of PHI",
                   "Deny-by-default gateway + least-privilege intersection + scoped tokens per tool",
                   "Bedrock AgentCore Gateway/Identity (or API GW + Cognito + STS)", "Implemented"),
    ControlMapping("HIPAA Security Rule (45 CFR 164.312)", "Access control, audit controls, integrity",
                   "Append-only PHI-masked audit; tamper-evident trail; encryption; per-call attribution",
                   "DynamoDB (deny Update/Delete) + S3 Object Lock WORM + KMS + CloudTrail", "Configurable"),
    ControlMapping("HIPAA / AWS BAA", "PHI processed only under a Business Associate Agreement",
                   "In-account Bedrock inference (no external API egress); BAA-eligible services only",
                   "Amazon Bedrock (HIPAA-eligible) + VPC endpoints + Guardrails", "Configurable"),
    ControlMapping("HITECH Act", "Breach notification; strengthened enforcement",
                   "PHI masking at every log/audit boundary; no raw identifiers in traces",
                   "governance + phi masker + CloudWatch", "Implemented"),
    ControlMapping("42 CFR Part 2", "Heightened protection of SUD treatment records",
                   "Sensitive-data consent check before disclosure; part2 flag on consent connector",
                   "Gateway consent.check + segmented data class + KMS", "Configurable"),
    ControlMapping("CMS-0057-F Interoperability & Prior Auth", "FHIR PA/Provider/Patient/Payer APIs; PA denial reasons",
                   "Da Vinci-aligned payer connector (CRD/DTR/PAS); structured PA assembly + status",
                   "HealthLake (FHIR) + API Gateway + Lambda", "Configurable"),
    ControlMapping("No Surprises Act", "Good Faith Estimate; balance-billing protections",
                   "Deterministic cost-estimate tool (registration.estimate_cost) with GFE basis + disclaimer",
                   "Gateway + deterministic rules + Step Functions", "Implemented"),
    ControlMapping("Section 1557 / ADA (45 CFR Part 92)", "Accessible, nondiscriminatory member communication",
                   "Accessibility + health-literacy pre-flight on patient-facing output",
                   "governance/accessibility + CI (axe-core)", "Implemented"),
    ControlMapping("21st Century Cures Act (info-blocking)", "No improper interference with EHI access/exchange",
                   "Read tools surface, never withhold, lawful EHI; security-trimmed retrieval with audit",
                   "HealthLake + Knowledge Bases ACL propagation + CloudTrail", "Configurable"),
    ControlMapping("CMS rules on AI in UM / MA prior auth", "AI may assist but a human decides; no algorithmic denial",
                   "issue_determination withheld from all agents; HITL gate; fairness screen on flag/rank",
                   "Gateway policy + governance/fairness + Step Functions waitForTaskToken", "Implemented"),
    ControlMapping("NIST AI RMF 1.0 / model governance", "Govern/Map/Measure/Manage AI risk",
                   "Grounding verification; prompt registry; evals; red team; fairness; HITL gates",
                   "governance/* + CloudWatch", "Implemented"),
    ControlMapping("HITRUST CSF / SOC 2", "Assessable security & privacy control set",
                   "Control mappings as evidence; deterministic governance suite runnable in CI",
                   "governance + AWS Artifact + Security Hub", "Configurable"),
    ControlMapping("PCI DSS (patient-pay)", "Protect cardholder data in patient payment flows",
                   "Card masking (Luhn); no card data in prompts/audit; tokenized payment connector",
                   "Gateway + phi masker + payment provider", "Configurable"),
]


def by_regime(regime: str) -> List[ControlMapping]:
    return [m for m in MAPPINGS if m.regime.lower().startswith(regime.lower())]
