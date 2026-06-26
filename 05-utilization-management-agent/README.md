# Agent 05 — Utilization Management / Medical Necessity
### HPP AI Agent Suite · status: **Demonstrated + Deployable-by-design** (built) · first payer-side agent

> Applies clinical criteria (MCG/InterQual), checks coverage (LCD/NCD), runs a four-fifths
> **fairness screen** on any flag/rank step, and prepares a **recommendation** for a medical
> director. The adverse-determination authority (`payer.issue_determination`) is **withheld
> from every agent** and held only by a `UM_MEDICAL_DIRECTOR` role — AI assists, a licensed
> human decides. **Even a "does not meet" recommendation is forwarded for a human
> determination; it never auto-denies.**

**Why it matters.** 70% of health plans are prioritizing agentic AI for utilization
management, prior authorization, and claims (Deloitte, Sep 2025). Algorithmic UM is under
active regulatory and litigation scrutiny — CMS requires that AI not make Medicare Advantage
coverage decisions and that a human make the determination. The withheld-determination
control and the fairness screen are what make a UM deployment defensible. Sources:
`../gtm/HPP-DECK-SOURCES.md`.

## What it does

| Step | Node | System of record (via gateway) |
|---|---|---|
| Gather clinical evidence | `gather_clinical` | EHR docs, PA status |
| Apply criteria | `evaluate_criteria` | MCG/InterQual + coverage (LCD/NCD) |
| Fairness screen | `fairness_screen` | EEOC four-fifths on a flag/rank cohort |
| Draft a recommendation | `draft_recommendation` | Bedrock / Anthropic via the LLM factory |
| Verify before a human sees it | `compliance_check` | grounding · PHI · fairness |
| **Medical-director gate** | `medical_director_gate` | Medical director decides |
| Forward recommendation / request info | `finalize` | Payer (`payer.draft_um_recommendation`, gated) |

The bright line: the agent produces a **recommendation** (`MEETS_CRITERIA` /
`DOES_NOT_MEET` / `NEEDS_MORE_INFO`); the **coverage determination** is the medical
director's. The agent is not granted `payer.issue_determination` at all — a test asserts even
a director's session cannot issue a determination *through the agent*.

## Run the demo (no API key)
```bash
pip install -e ../platform_core && pip install langgraph streamlit
export EXTRACT_MODE=demo
python demo/demo_run.py     # meets / does-not-meet(forwarded) / needs-info / fairness-flagged
streamlit run app.py
```

## Tests
```bash
PYTHONPATH=../platform_core:..:.  python -m pytest tests -q
```

## Docs
- `docs/aws-deployment-guide.md` · `docs/integration-guide.md` · `docs/compliance.md` · `docs/roi-analysis.md`
- `demo/DEMO-LIVE.md` — Bedrock + real-connector runbook
