# Golden Paths — one-command deploys

A **golden path** is a self-contained AWS SAM app that deploys one agent's governed tool route in
a single `sam deploy`, with a smoke test and a teardown. It is the fastest way for a solution
architect to stand up a real, governed endpoint in a customer account and prove the controls
(deny-by-default, the human gate, the append-only audit) live — before wiring connectors or IdP.

| Agent | Path | Deploy |
|---|---|---|
| 01 Revenue-Cycle & Denial | `golden-path-01-revenue-cycle/` | `./build.sh && sam deploy --guided` → `./smoke_test.sh` |

The flagship golden path is the documented reference; the other seven deploy through the nested
CloudFormation quick-deploy (`cloudformation/quickstart.yaml` via `scripts/deploy.sh`) or Terraform
(`terraform/`), which provision the full per-agent isolated stack (own VPC, KMS, Cognito, audit,
gateway, agent). Use the golden path for a fast proof; use the full stacks for an isolated
per-agent environment. See `../GETTING-STARTED.md` and `../docs/DEPLOYMENT-MODELS.md`.
