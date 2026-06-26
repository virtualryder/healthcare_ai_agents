# Per-agent stamp-out parameters

Every agent deploys from the **same** template set (`../quickstart.yaml` and its nested
stacks) — only the parameters change. Each agent gets its own isolated VPC, KMS key, Cognito
pool, audit table, WORM bucket, gateway, and state machine, so agents never share a security
or data boundary.

| Agent | Param file | Suggested VPC CIDR (avoid overlap in one account/Region) |
|---|---|---|
| 01 Revenue-Cycle & Denial | `01-revenue-cycle-denial.json` | 10.30.0.0/16 (template default) |
| 02 Prior-Authorization | `02-prior-authorization.json` | 10.31.0.0/16 (pass `VpcCidr`) |
| 03–08 | add `0N-<name>.json` | 10.32.0.0/16 … |

```bash
# Stamp out Agent 02 (same templates, different AgentId + CIDR):
scripts/deploy.sh 02-prior-authorization dev portable native s3://my-cfn-bucket/hpp 10.31.0.0/16
```
The CIDR is optional; pass it only when deploying multiple agents into the same account/Region.
