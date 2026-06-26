# Agent 03 — Clinical-Administration
### HPP AI Agent Suite · status: **Demonstrated + Deployable-by-design** (built)

> Summarizes charts, prepares visits, coordinates referrals, drafts discharge documentation,
> handles the clinical inbox and follow-up, and coordinates care transitions. Every clinical
> artifact is a **draft for a licensed clinician to review and sign** — the agent holds
> `ehr.draft_note` (a gated draft write) but **no order-entry or note-signing authority**, and
> it checks consent (incl. **42 CFR Part 2** SUD records) before producing anything.

**Why it matters.** Documentation and inbox burden are leading drivers of clinician burnout;
>80% of health-system execs are prioritizing agentic AI for clinical operations and care
delivery (Deloitte, Sep 2025). 21st Century Cures information-blocking rules require timely
EHI access — summaries surface, never withhold, lawful information. Sources:
`../gtm/HPP-DECK-SOURCES.md`.

## What it does

| Step | Node | System of record (via gateway) |
|---|---|---|
| Load the chart | `load_chart` | EHR/FHIR (summary, encounter, docs) + care plan |
| Consent gate | `check_consent` | Consent (`consent.check`, 42 CFR Part 2 aware) |
| Produce the artifact | `produce_artifact` | Bedrock / Anthropic via the LLM factory |
| Verify before a human sees it | `compliance_check` | grounding · PHI · health-literacy (patient-facing) |
| **Clinician sign-off gate** | `clinician_review_gate` | Clinician reviews & signs |
| File draft / prep ready / escalate | `finalize` | EHR (`ehr.draft_note`, gated) |

Task types: `chart_summary`, `visit_prep` (read-only brief, no write), `referral`,
`discharge_summary` and `inbox_followup` (patient-facing — held to a 6th–8th grade
health-literacy bar). A 42 CFR Part 2 record without consent routes straight to escalation.

## Run the demo (no API key)
```bash
pip install -e ../platform_core && pip install langgraph streamlit
export EXTRACT_MODE=demo
python demo/demo_run.py     # summary(file) / visit_prep(read-only) / discharge / Part-2(escalate)
streamlit run app.py
```

## Tests
```bash
PYTHONPATH=../platform_core:..:.  python -m pytest tests -q
```

## Docs
- `docs/aws-deployment-guide.md` · `docs/integration-guide.md` · `docs/compliance.md` · `docs/roi-analysis.md`
- `demo/DEMO-LIVE.md` — Bedrock + real-connector runbook
