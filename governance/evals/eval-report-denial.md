# Agent 01 (Revenue-Cycle & Denial) — scored eval report

**Result:** PASS · **Cases:** 20 · Predictions from the REAL Agent 01 classifier (`agent.nodes.analyze_denial`); appeal-draft grounding via `governance/grounding.py`; PHI-leak via the platform masker.

Benchmark runs on **labeled synthetic denials** — there is no clean public, PHI-free denial API. The real source is the customer's **X12 835/277** remittance (clearinghouse) or **AWS HealthLake Claim/ClaimResponse (FHIR)** under a BAA; see the connector scaffold `platform_core/hpp_agent_platform/connectors/denials.py`.

| Metric | Value | Threshold | Status |
|---|---|---|---|
| denial_reason_accuracy | 1.0 | >= 0.9 | PASS |
| recoverable_recall | 1.0 | >= 0.95 | PASS |
| entity_f1 | 1.0 | >= 0.85 | PASS |
| grounding_rate | 1.0 | >= 0.9 | PASS |
| phi_leak_rate | 0.0 | <= 0.0 | PASS |
| appeal_completeness | 1.0 | >= 0.95 | PASS |
| duplicate_accuracy | 1.0 | >= 0.9 | PASS |

**Recoverable confusion:** TP=15 FP=0 FN=0 TN=5 (recall is weighted highest — missing a recoverable denial is a wrongful write-off, the money harm).

This report is the quality-evidence artifact for the assurance packet: it shows the agent's denial classification measured against a labeled benchmark with a **PHI-leak hard gate (= 0)**. Human retains claim submission. Regenerate with `python -m governance.evals.score_denial`.
