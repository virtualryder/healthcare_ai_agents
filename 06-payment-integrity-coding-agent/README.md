# Agent 06 — Payment Integrity & Coding
### HPP AI Agent Suite · status: **Demonstrated + Deployable-by-design** (built)

> Suggests and validates codes (ICD-10, CPT/HCPCS), runs NCCI/MUE edits and a medical-
> necessity check, and **flags** overpayments, duplicates, and coding errors for a human
> payment-integrity reviewer. The agent **flags**; it never recoups, adjusts payment, or
> submits a claim. The only write is a gated review flag/note (`pas.update_case`).

**Why it matters.** Coding defects are a leading denial root cause (feeding Agent 01) and a
False Claims Act exposure surface; payment-integrity recoveries are a measurable payer
outcome. Grounding ensures a suggested code is traceable to documentation, not invented.
Sources: `../gtm/HPP-DECK-SOURCES.md`.

## What it does

| Step | Node | System of record (via gateway) |
|---|---|---|
| Load the claim + docs | `load_claim` | Patient accounting + EHR docs |
| Analyze coding | `analyze_coding` | Encoder (suggest), NCCI/MUE (`validate_codes`), LCD/NCD necessity, 837 scrub |
| Detect issues | `detect_issues` | (deterministic: bundling · upcoding · duplicate · necessity) |
| Draft the finding | `draft_finding` | Bedrock / Anthropic via the LLM factory |
| Verify before a human sees it | `compliance_check` | grounding · PHI |
| **Review gate** | `review_gate` | Payment-Integrity Reviewer confirms |
| Record flag / no action | `finalize` | Patient accounting (`pas.update_case`, gated) |

Findings: `CLEAN` (no write), `FLAG_OVERPAYMENT` (billed E/M exceeds documentation),
`FLAG_CODING` (NCCI/MUE edit), `FLAG_DUPLICATE`, `REQUEST_DOCS` (necessity not supported).
The agent is **not granted** `clearinghouse.submit_claim` or any recoupment authority.

## Run the demo (no API key)
```bash
pip install -e ../platform_core && pip install langgraph streamlit
export EXTRACT_MODE=demo
python demo/demo_run.py     # clean / overpayment / NCCI edit / duplicate / needs-docs
streamlit run app.py
```

## Tests
```bash
PYTHONPATH=../platform_core:..:.  python -m pytest tests -q
```

## Docs
- `docs/aws-deployment-guide.md` · `docs/integration-guide.md` · `docs/compliance.md` · `docs/roi-analysis.md`
- `demo/DEMO-LIVE.md` — Bedrock + real-connector runbook
