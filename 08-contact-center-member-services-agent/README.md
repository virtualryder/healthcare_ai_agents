# Agent 08 — Contact Center / Member Services
### HPP AI Agent Suite · status: **Demonstrated + Deployable-by-design** (built) · completes the suite

> Answers member inquiries — claim status (X12 276/277), benefits/eligibility (270/271) —
> logs interactions, and intakes grievances, drafting tone-matched, health-literate,
> Section 1557-accessible responses on **Amazon Connect**. It verifies member identity before
> any account-specific disclosure; interaction logging and grievance creation are **gated
> writes**. The agent answers and drafts; a rep approves the record.

**Why it matters.** Member-services volume spikes around denials and benefits questions (the
same CO-197 denials Agent 01 works); deflecting routine inquiries with grounded, verified
answers improves member experience and frees staff. Amazon Connect is the natural CCaaS
substrate. Sources: `../gtm/HPP-DECK-SOURCES.md`.

## What it does

| Step | Node | System of record (via gateway) |
|---|---|---|
| Verify the member | `verify_member` | Identity (`identity.verify_member`) |
| Retrieve | `retrieve` | Contact center, claim status (276/277), eligibility (270/271) |
| Draft the response | `draft_response` | Bedrock / Anthropic via the LLM factory |
| Verify before a human sees it | `compliance_check` | grounding · PHI · health-literacy |
| **Rep review gate** | `review_gate` | Member-Services Rep approves |
| Answer + log / file grievance / escalate | `finalize` | Contact center (`log_interaction` / `create_grievance`, gated) |

Outcomes: `ANSWER_AND_LOG`, `FILE_GRIEVANCE`, `VERIFY_IDENTITY` (no disclosure without a
verified member), `ESCALATE` (inactive coverage). Responses are held to a 6th–8th grade
health-literacy bar. The agent is **not granted** `payer.submit_appeal` — it can start the
process for a member, but a denials specialist submits.

## Run the demo (no API key)
```bash
pip install -e ../platform_core && pip install langgraph streamlit
export EXTRACT_MODE=demo
python demo/demo_run.py     # claim status / benefits / grievance / verify-identity / inactive-coverage
streamlit run app.py
```

## Tests
```bash
PYTHONPATH=../platform_core:..:.  python -m pytest tests -q
```

## Docs
- `docs/aws-deployment-guide.md` · `docs/integration-guide.md` · `docs/compliance.md` · `docs/roi-analysis.md`
- `demo/DEMO-LIVE.md` — Bedrock + Amazon Connect runbook
