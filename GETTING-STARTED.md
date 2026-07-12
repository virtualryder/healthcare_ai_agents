# Getting Started — HPP AI Agent Suite

Three steps, in order. Steps 1–2 need **no AWS account and no API key**; Step 3 deploys into a
**new AWS account** with copy-paste commands. A solution architect or customer can follow this
top to bottom.

---

## Step 1 — Prove it on your laptop (no AWS, no API key)

```bash
# Python 3.10+; from the repo root
pip install -e platform_core
pip install langgraph streamlit          # langgraph optional (graph tests skip without it)

# Run the flagship agent end-to-end, deterministically (fixtures, no model call):
cd 01-revenue-cycle-denial-agent
EXTRACT_MODE=demo python demo/demo_run.py     # three denial paths: appeal / resubmit / escalate
streamlit run app.py                          # optional dashboard at http://localhost:8501
cd ..
```

Each of the eight agents has the same `demo/demo_run.py` and `app.py`. Swap `01-…` for any of
`02-…` through `08-…`.

> **LLM provider.** These demos are deterministic (fixtures, no model call). When a live model *is*
> invoked, the provider **defaults to in-account Amazon Bedrock** (`LLM_PROVIDER=bedrock`, under the
> AWS BAA, with Guardrails). The external Anthropic API is gated behind an explicit
> `ALLOW_EXTERNAL_LLM=1` opt-in (non-PHI/dev only), so a bare `LLM_PROVIDER` change cannot silently
> egress PHI off AWS. Agents 01–02 carry the real LLM path; agents 03–08 are deterministic reference
> workflows.

## Step 2 — Run the full test suite (no API key)

```bash
bash scripts/run_tests.sh
# → platform + governance, then each agent in isolation → "ALL SUITES PASSED" (270 tests as of 2026-07-10)
```

This proves the governance controls — deny-by-default authorization, the human gate, PHI
masking, grounding, red-team injection/exfil/authz-bypass, and the four-fifths fairness screen —
all with no API key. The withheld authorities are enforced in code and verified here (e.g. a
test asserts the agent cannot issue a UM determination).

## Step 3 — Deploy into a new AWS account

**Canonical path (acceptance-gated):** the Agent 01 SAM golden path — one command, with a smoke
test and teardown (validated in [`evidence/CLEAN-ACCOUNT-ACCEPTANCE.md`](evidence/CLEAN-ACCOUNT-ACCEPTANCE.md)):

```bash
cd infra/golden-path-01-revenue-cycle && ./build.sh && sam deploy --guided && ./smoke_test.sh
```

**Alternative multi-agent reference (not acceptance-gated):** the nested-CloudFormation route in
**[`docs/DEPLOY-QUICKSTART.md`](docs/DEPLOY-QUICKSTART.md)** — empty account → running governed
agent in two commands:

```bash
scripts/build_lambdas.sh 01-revenue-cycle-denial
scripts/deploy.sh 01-revenue-cycle-denial dev portable native s3://my-cfn-staging/hpp 10.30.0.0/16
```

This nests the network / security (KMS + Bedrock Guardrail + Cognito) / data (append-only audit +
WORM) / connectors / gateway / agent-service stacks into one customer-isolated environment.
Prefer Terraform? `infra/terraform/` is at parity (`terraform apply -var-file=envs/<agent>.tfvars`).

> **Before any PHI:** an AWS Business Associate Agreement must be executed. Steps 1–2 use only
> synthetic fixtures and no PHI. Production-readiness (CSV/CSA, IdP integration, live-connector
> validation, penetration test, HITRUST) is the engagement — see the go-live checklist in the
> deploy quickstart.

---

## Where things live
| You want… | Go to |
|---|---|
| The thesis & 8-agent overview | `README.md` |
| One agent's build (demo, tests, docs) | `0N-<agent>/README.md` |
| Architecture & request path | `docs/SUITE-ARCHITECTURE.md` |
| Deploy steps (new AWS account) | `infra/golden-path-01-revenue-cycle/` (canonical) · `docs/DEPLOY-QUICKSTART.md` (alternative reference) |
| IaC (CloudFormation / Terraform) | `infra/cloudformation/` · `infra/terraform/` |
| AWS-native Step Functions rebuilds | `aws-native-reference/` |
| Governance controls | `governance/` |
| Decks, ROI calculator, demo storyboard | `decks/` · `gtm/` |
| Consulting offerings | `offerings/` |
| Ops runbooks | `runbooks/` |
| Honest status & changelog | `SUITE-STATUS.md` |
