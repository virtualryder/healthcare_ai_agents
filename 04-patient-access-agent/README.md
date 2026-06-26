# Agent 04 — Patient Access
### HPP AI Agent Suite · status: **Demonstrated + Deployable-by-design** (built)

> Handles scheduling, registration, benefits verification (X12 270/271), cost estimates,
> referral status, and follow-up. Patient cost estimates come from a **deterministic** tool
> (`registration.estimate_cost`, No Surprises Act Good Faith Estimate) — never the LLM — and
> member-facing text passes a 6th–8th grade health-literacy / Section 1557 pre-flight. The
> agent verifies patient identity before disclosing any account/benefit detail, and every
> write (book, register) passes the human-approval gate.

**Why it matters.** Access friction drives leakage and no-shows; eligibility/registration
errors are a top upstream cause of the denials Agent 01 cleans up (e.g. CO-27 coverage,
registration defects). The No Surprises Act requires Good Faith Estimates for self-pay/
uninsured patients. Sources: `../gtm/HPP-DECK-SOURCES.md`.

## What it does

| Step | Node | System of record (via gateway) |
|---|---|---|
| Verify the patient | `verify_identity` | Identity (`identity.verify_patient`) |
| Check benefits | `check_eligibility` | Payer (`payer.check_eligibility`, X12 270/271) |
| Estimate cost | `estimate_cost` | Registration (`registration.estimate_cost`, deterministic GFE) |
| Offer appointment options | `get_availability` | Scheduling |
| Member-facing message | `prepare_summary` | Bedrock / Anthropic via the LLM factory |
| Verify before a human sees it | `compliance_check` | grounding · PHI · health-literacy |
| **Human gate** | `human_review_gate` | Access Rep approves |
| Book + register / estimate / escalate | `finalize` | Scheduling + Registration (gated writes) |

Task types: `schedule` (book + register), `benefits` (read-only), `estimate` (Good Faith
Estimate, no identity needed). Unverified identity → `VERIFY_IDENTITY`; inactive coverage →
`ESCALATE`.

## Run the demo (no API key)
```bash
pip install -e ../platform_core && pip install langgraph streamlit
export EXTRACT_MODE=demo
python demo/demo_run.py     # book / benefits / verify-identity / GFE-only / inactive-coverage
streamlit run app.py
```

## Tests
```bash
PYTHONPATH=../platform_core:..:.  python -m pytest tests -q
```

## Docs
- `docs/aws-deployment-guide.md` · `docs/integration-guide.md` · `docs/compliance.md` · `docs/roi-analysis.md`
- `demo/DEMO-LIVE.md` — Bedrock + real-connector runbook
