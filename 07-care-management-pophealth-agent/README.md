# Agent 07 — Care Management & Population Health
### HPP AI Agent Suite · status: **Demonstrated + Deployable-by-design** (built)

> Identifies care gaps, stratifies risk (HCC/RAF), surfaces SDOH factors, runs a four-fifths
> **fairness screen** on the risk-stratification step, and prepares outreach + care-plan
> updates for a care manager. Care-plan writes are **gated** (care-manager sign-off); a
> **42 CFR Part 2** (SUD) record without consent never produces outreach — it escalates. The
> care manager owns the plan.

**Why it matters.** Value-based and population-health programs depend on closing care gaps
and accurate risk capture; >80% of health-system execs are prioritizing agentic AI for care
delivery (Deloitte, Sep 2025). Ungoverned risk models raise Section 1557 nondiscrimination and
CMS risk-adjustment-integrity concerns — which the fairness screen and grounding controls
address. Sources: `../gtm/HPP-DECK-SOURCES.md`.

## What it does

| Step | Node | System of record (via gateway) |
|---|---|---|
| Load the patient + plan | `load_patient` | EHR summary + care plan |
| Consent gate | `check_consent` | Consent (`consent.check`, 42 CFR Part 2 aware) |
| Identify gaps + risk + SDOH | `identify_gaps` | Care management (`careplan.identify_gaps`) |
| Fairness screen | `fairness_screen` | EEOC four-fifths on a risk-strat cohort |
| Draft outreach + plan update | `draft_artifacts` | Bedrock / Anthropic via the LLM factory |
| Verify before a human sees it | `compliance_check` | grounding · PHI · health-literacy · fairness |
| **Care-manager gate** | `care_manager_gate` | Care manager signs off |
| Update plan / no action / escalate | `finalize` | Care management (`careplan.update_care_plan`, gated) |

Outcomes: `UPDATE_CARE_PLAN` (open gaps → gated write), `NO_GAPS` (no action), `ESCALATE`
(42 CFR Part 2 consent block). Outreach is patient-facing and held to a 6th–8th grade
health-literacy bar.

## Run the demo (no API key)
```bash
pip install -e ../platform_core && pip install langgraph streamlit
export EXTRACT_MODE=demo
python demo/demo_run.py     # update-plan / no-gaps / Part-2 escalate / fairness-flagged
streamlit run app.py
```

## Tests
```bash
PYTHONPATH=../platform_core:..:.  python -m pytest tests -q
```

## Docs
- `docs/aws-deployment-guide.md` · `docs/integration-guide.md` · `docs/compliance.md` · `docs/roi-analysis.md`
- `demo/DEMO-LIVE.md` — Bedrock + real-connector runbook
