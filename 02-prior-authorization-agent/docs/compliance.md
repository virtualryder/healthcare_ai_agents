# Agent 02 — Compliance Mapping: Prior-Authorization

| Obligation | How this agent satisfies it |
|---|---|
| **HIPAA Privacy — minimum necessary** | Every system call passes the deny-by-default gateway with a tool-scoped token; the agent reads only the summary, docs, criteria, and policy it needs. |
| **HIPAA Security — audit controls** | Every decision is recorded in the append-only, PHI-masked audit log with lineage and the approving PA nurse. |
| **HIPAA / AWS BAA** | With `LLM_PROVIDER=bedrock`, the clinical rationale is drafted in-account on HIPAA-eligible Bedrock — no PHI egress. |
| **No autonomous coverage decision** | `payer.issue_determination` is granted to **no agent**; the agent assembles and (gated) submits, but the determination is the payer's. `payer.submit_pa` is high-risk and requires a verified PA-nurse approval. |
| **CMS-0057-F alignment** | The payer connector is Da Vinci-aligned: `check_pa_requirement` (CRD), packet assembly (DTR/PAS), `submit_pa` (278/PAS), `check_pa_status` — the FHIR surfaces the rule standardizes by Jan 1, 2027. |
| **Algorithmic-fairness posture** | Criteria evaluation is a flag/rank step; the four-fifths fairness screen (`governance/fairness`) applies, and no adverse action is automated. |
| **Grounded clinical assertions** | Grounding fails the rationale if any code, indication, or guideline is not traceable to the criteria result, necessity check, or guideline. |
| **State PA-transparency laws** | Turnaround/status monitoring (`check_pa_status`) and structured reasons support state gold-carding / transparency requirements. |

## Customer responsibilities
CSV for the intended use; IdP mapping of `PA_COORDINATOR` / `UM_MEDICAL_DIRECTOR`; live
connector validation (payer Da Vinci/278, criteria service, EHR); Guardrail configuration;
prompt/model change control (the prompt registry hash-pins the rationale prompt).
