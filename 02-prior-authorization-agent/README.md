# Agent 02 — Prior-Authorization
### HPP AI Agent Suite · status: **Demonstrated + Deployable-by-design** (built)

> Determines whether a service needs prior authorization, gathers medical evidence,
> evaluates clinical criteria (MCG/InterQual), assembles the submission, monitors status,
> requests missing information, and escalates urgent cases. The agent **assembles and (on a
> PA nurse's approval) submits** the request — but the **coverage determination is always the
> payer's**; `payer.issue_determination` is withheld from every agent.

**Why it matters.** Physicians complete ~39 prior authorizations per week (≈13 hours); 94%
say PA delays care and 78% report it causes treatment abandonment (AMA, Dec 2024). 70% of
health plans are prioritizing agentic AI for UM/PA/claims and 93% of plan execs expect AI to
ease PA (Deloitte, Sep 2025). CMS-0057-F mandates FHIR PA APIs by Jan 1, 2027. Sources:
`../gtm/HPP-DECK-SOURCES.md`.

## What it does

| Step | Node | System of record (via gateway) |
|---|---|---|
| Is a PA required? | `check_requirement` | Payer (`payer.check_pa_requirement`, Da Vinci CRD) |
| Assemble evidence | `gather_evidence` | EHR summary + docs, medical-necessity (LCD/NCD), policy |
| Evaluate criteria | `evaluate_criteria` | MCG/InterQual (`clinicalcriteria.evaluate`, `get_guideline`) |
| Draft the clinical rationale | `assemble_packet` | Bedrock / Anthropic via the LLM factory |
| Verify before a human sees it | `compliance_check` | grounding · PHI · completeness |
| **Human gate** | `human_review_gate` | PA Nurse approves |
| Submit (278) / monitor / escalate | `finalize` | Payer (`payer.submit_pa`, gated; `check_pa_status`) |

## Run the demo (no API key)

```bash
pip install -e ../platform_core && pip install langgraph streamlit
export EXTRACT_MODE=demo
python demo/demo_run.py     # imaging (submit) / office visit (no PA) / urgent (escalate)
streamlit run app.py
```

## Tests
```bash
PYTHONPATH=../platform_core:..:.  python -m pytest tests -q
```

## Docs
- `docs/aws-deployment-guide.md` · `docs/integration-guide.md` · `docs/compliance.md` · `docs/roi-analysis.md`
- `demo/DEMO-LIVE.md` — Bedrock + real-connector runbook
