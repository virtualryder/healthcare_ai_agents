# Deploy Runbook — Agent 03 (Clinical-Administration)

Step-by-step AWS deploy for a solution architect. Prereqs: `../../docs/AWS-ACCOUNT-PREREQUISITES.md`
(AWS BAA executed; Bedrock model access in-Region; KMS/Cognito; an S3 staging bucket). The
companion deployment handbook is `../../deliverables/agent-handbooks/03-clinical-administration-HANDBOOK.md`.

## 1. Prove it locally (no AWS, no API key)
```bash
cd 03-clinical-administration-agent && EXTRACT_MODE=demo python demo/demo_run.py     # from repo root
PYTHONPATH=../platform_core:..:.  python -m pytest tests -q
```

## 2. Deploy into a new AWS account
```bash
scripts/build_lambdas.sh 03-clinical-administration
scripts/deploy.sh 03-clinical-administration dev portable native s3://my-cfn-staging/hpp 10.32.0.0/16
```
Nests network / security (KMS + Bedrock Guardrail + Cognito `custom:hpp_role`) / data
(append-only audit + WORM) / connectors / gateway / agent-service. Per-agent params:
`infra/cloudformation/params/03-clinical-administration.json`. Terraform: `terraform apply -var-file=envs/03-clinical-administration.tfvars`.

## 3. Human-gate smoke test
1. Seed a Cognito user with the agent's reviewer role and sign in.
2. Drive a gated action; confirm it **suspends at the Clinician sign-off gate** and an item lands in the HITL table.
3. Approve (reviewer ≠ requester); confirm it proceeds and the approval is written to the
   **hash-chained append-only audit**. Reject; confirm it does **not** proceed.
4. Attempt an out-of-scope tool; confirm the gateway **denies by default**.

## 4. Go-live (engagement)
AWS BAA · IdP integrated (`AUTH_REQUIRE_JWT=1`, JWKS configured) · live connectors validated ·
Guardrail tuned · CSV/CSA · penetration test · HITRUST/SOC 2. See
`../../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.
