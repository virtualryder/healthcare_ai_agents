# Agent 01 — Revenue-Cycle & Denial Management
### Flagship reference agent · HPP AI Agent Suite (Health Providers & Plans)

> Reviews claims before submission, identifies missing documentation, determines the
> likely denial root cause, drafts a grounded appeal, tracks the payer response, and
> updates the case-management system — **without ever submitting a claim** (a biller
> does) and **without submitting an appeal until a denials specialist approves** at the
> gateway's human gate.

This is the suite's flagship and the recommended initial wedge: denials carry the
cleanest, most measurable CFO ROI in a provider organization. Initial denial rates
reached ~11.8% in 2024 and are climbing; in 2025 U.S. hospitals spent roughly **$18B
overturning denials** out of ~$43B on billing and collections, and **35–60% of denied
claims are never reworked** — permanent revenue loss. (Sources: `../gtm/HPP-DECK-SOURCES.md`.)

## What it does

| Step | Node | System of record (via gateway) |
|---|---|---|
| Load the denied/pre-submission claim | `load_claim` | Patient accounting (`pas`) |
| Determine root cause from CARC/RARC | `analyze_denial` | (deterministic CARC map) |
| Assemble evidence | `gather_evidence` | EHR docs, encoder (NCCI/MUE), medical-necessity (LCD/NCD), coverage policy |
| Draft a grounded appeal | `draft_appeal` | Bedrock / Anthropic via the LLM factory |
| Verify before a human sees it | `compliance_check` | grounding · PHI · health-literacy |
| **Human gate** | `human_review_gate` | Denials Specialist approves |
| Submit appeal / queue resubmit / escalate | `finalize` | Payer (`payer.submit_appeal`, gated), case-mgmt (`pas.update_case`) |

The bright line: the agent **drafts and assembles**; a licensed/credentialed human
**commits**. The agent is not granted `clearinghouse.submit_claim` at all.

## Run the demo (no API key)

```bash
pip install -e ../platform_core
pip install langgraph streamlit
export EXTRACT_MODE=demo
python demo/demo_run.py            # CLI: three denial paths (appeal / resubmit / escalate)
streamlit run app.py               # dashboard at http://localhost:8501
```

## Tests

```bash
PYTHONPATH=../platform_core:..:.  python -m pytest tests -q
```

## Live mode (Bedrock + real connectors)

Set `EXTRACT_MODE=live`, `LLM_PROVIDER=bedrock` (in-account inference under the AWS BAA;
configure `BEDROCK_GUARDRAIL_ID`), and point `PAS_BASE_URL` / `CLEARINGHOUSE_BASE_URL` /
`PAYER_BASE_URL` / `EHR_BASE_URL` at the organization's systems. No agent code changes —
the gateway and connector signatures are identical to demo. See `.env.example` and
`docs/aws-deployment-guide.md`.

## Docs
- `docs/aws-deployment-guide.md` — container + native deployment, AgentCore contract
- `docs/integration-guide.md` — connector mapping (Epic/Oracle Health, Change Healthcare/Availity, payer X12/FHIR)
- `docs/compliance.md` — HIPAA, CMS-0057-F, No Surprises Act control mapping for this agent
- `docs/roi-analysis.md` — denial economics and the value model
