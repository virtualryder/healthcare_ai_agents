# HPP AI Agent Suite — AWS Total Cost of Ownership Model

> An SA-ready structure for estimating the AWS run cost of a deployed agent, plus a worked
> example with stated assumptions and an ROI-worksheet outline that nets run cost against the
> value model in `COST-ROI-MODEL.md`. All dollar figures here are **illustrative placeholders
> for SA sizing** — they are not a quote and must be priced against the customer's Region,
> volumes, and the AWS Pricing Calculator. Demand-side statistics are source-class tagged and
> traced to `../gtm/HPP-DECK-SOURCES.md`.

## Cost components

The deployed architecture is in-account and isolated per agent. The principal AWS run-cost
drivers are:

| Component | AWS service | Cost driver |
|---|---|---|
| LLM inference | Amazon Bedrock (HIPAA-eligible, under BAA) + Guardrails | Input/output tokens per transaction × volume; guardrail evaluations |
| Agent orchestration | AWS Step Functions (`waitForTaskToken` HITL) or AgentCore Runtime / ECS Fargate | State transitions (native) or vCPU/GB-hours (container) |
| FHIR data | Amazon HealthLake | Stored GB + FHIR API requests |
| Document extraction | Amazon Bedrock Data Automation | Pages/documents processed |
| Member/patient channel | Amazon Connect (Agents 04, 08) | Per-minute usage + telephony |
| Audit + HITL state | DynamoDB (append-only) + S3 Object Lock WORM | Write/read units + stored GB (WORM retained for retention period) |
| Encryption | AWS KMS | Keys + request volume |
| Identity | Amazon Cognito / IAM Identity Center | MAUs / federation |
| Networking | VPC, in-account Bedrock endpoint (PrivateLink), Flow Logs, NAT | Endpoint-hours, data processed, log volume |
| Connectors | Lambda (connector framework) | Invocations + GB-seconds |
| Observability | CloudWatch | Logs, metrics, alarms |

## Worked estimate — Agent 01, one agent, illustrative

**Stated assumptions (SA must replace per customer):**
- Volume: 1.2M annual claims, ~11.8% initial denial rate `[industry-research]` ≈ 141,600
  denied claims/yr ≈ ~11,800/month entering the agent.
- Per-transaction inference: denial triage + grounded appeal draft ≈ one moderate Bedrock
  call (assume ~6K input + ~2K output tokens) plus guardrail evaluation.
- `LLM_PROVIDER=bedrock`, reached over AWS PrivateLink under the customer's AWS BAA — no external AI API egress.
- Native Step Functions deploy with `waitForTaskToken` HITL (not a long-running container).
- Single Region; one isolated VPC per agent; WORM retention per the customer's record policy.

| Component | Illustrative monthly basis | Note |
|---|---|---|
| Bedrock inference | tokens/txn × ~11,800 txn | Dominant variable; price by chosen model + Region |
| Bedrock Guardrails | ~11,800 evaluations | Per-policy evaluation pricing |
| Step Functions | state transitions × ~11,800 | Native HITL path; low per-unit |
| DynamoDB (audit + HITL) | write/read units for ~11,800 records | On-demand sized to volume |
| S3 Object Lock (WORM) | cumulative audit GB over retention | Grows with retained history |
| HealthLake | FHIR stored GB + requests | Sized to chart/claim context pulled |
| Lambda (connectors) | invocations + GB-s | Per connected system |
| KMS / Cognito / CloudWatch | keys, MAUs, logs | Largely fixed baseline |
| VPC endpoint + Flow Logs + NAT | endpoint-hours + data | Per-agent isolation baseline |

> **Run-cost total: $[PLACEHOLDER]/month** — to be computed in the AWS Pricing Calculator
> from the customer's token sizing, volume, Region, and retention policy. Inference and
> Bedrock Guardrails are the swing factors; the isolation baseline (VPC endpoint, KMS,
> CloudWatch) is largely fixed and is amortized across agents as the portfolio grows.

## Numeric estimate — Pilot vs Production (illustrative)

> **MODEL ASSUMPTION — illustrative estimate** built from published us-east-1 on-demand list
> prices as of mid-2026; prices and token economics change frequently; validate with the AWS
> Pricing Calculator and your AWS account team before quoting. **Bedrock token volume is the
> dominant, workload-dependent variable** — every Bedrock line below is the sensitivity driver.
> No figure here is a quote.

The narrative structure above stays authoritative for *what* drives cost; this table puts
concrete monthly dollars against it for two reference scenarios.

**Scenario assumptions:**

| Assumption | **Pilot** (1 agent, dept-scale) | **Production** (8-agent suite) |
|---|---|---|
| Governed requests/month | ~10,000 (e.g., Agent 01 denial triage for one facility) | ~400,000 (payer/provider back-office volumes are transaction-, not chat-, shaped) |
| Active users (MAU) | ~50 staff | ~2,000 staff |
| Bedrock tokens/month | ~5M input + ~1M output | ~250M input + ~50M output |
| Model class | Mid-tier Claude (Sonnet-class): ~$3.00/M input, ~$15.00/M output tokens `[MODEL ASSUMPTION]` | same |
| Architecture | Serverless reference path (API Gateway HTTP API → Lambda → Step Functions `waitForTaskToken` HITL → Bedrock under BAA), private-by-default (VPC interface endpoints even in pilot) | same, plus production hardening (NAT, WAF, CloudFront) |
| Per-request shape | ~2 API calls, ~5 Lambda invocations, ~15 Step Functions state transitions, ~10 DynamoDB writes + 20 reads (audit + HITL state) | same |

| Line item | Basis | **Pilot ($/mo)** | **Production ($/mo)** |
|---|---|---:|---:|
| **Bedrock inference** ← *sensitivity driver* | Sonnet-class; 5M in + 1M out (pilot) / 250M in + 50M out (prod) | **30** | **1,500** |
| Bedrock Guardrails ← *scales with request volume* | Content filters, prompt-side; ~2 text units/request @ ~$0.75/1K units | 15 | 600 |
| Lambda (connectors + framework) | ~5 invocations/request; 512 MB × ~800 ms | 1 | 14 |
| API Gateway (HTTP API) | ~2 calls/request @ ~$1.00/M | 1 | 1 |
| Step Functions (Standard) | ~15 state transitions/request (HITL path) @ ~$25/M | 4 | 150 |
| DynamoDB (on-demand) | ~10 WRU + 20 RRU/request (append-only audit + HITL) + storage | 1 | 10 |
| S3 + Object Lock (WORM audit) | 5 GB pilot / 200 GB prod, grows with retention | 2 | 7 |
| KMS | $1/CMK (4 pilot / 6 prod) + ~20 requests/request @ $0.03/10K | 5 | 30 |
| Cognito | MAU-based (~$0.015/MAU); 50 pilot / 2,000 prod | 1 | 30 |
| CloudWatch | Logs ingest + metrics + dashboards | 3 | 50 |
| VPC interface endpoints | ~$7.30/endpoint-mo + data; 5 pilot / 8 prod (Bedrock PrivateLink, KMS, STS, Logs…) | 36 | 68 |
| NAT Gateway | Prod only; ~$33/mo + ~100 GB processed | — | 37 |
| WAF | Prod only; web ACL + 5 rules + request fees | — | 10 |
| CloudFront | Prod only; member/patient web channel, low-GB tier | — | 10 |
| **TOTAL** | | **~$99/mo** | **~$2,517/mo** |

**Sensitivity (one line):** 2× Bedrock token volume ≈ **+$1,500/mo** at production scale
(inference is ~60% of the production total); every other line moves slowly.

Not priced above (add per customer usage): **HealthLake** (stored GB + FHIR requests), **Bedrock
Data Automation** (per page/document), **Amazon Connect** (per-minute, Agents 04/08) — these are
real for the agents that use them and can each add hundreds per month at volume. Rounding: whole
dollars; sub-dollar lines shown as $1. Annualized production (excl. HealthLake/BDA/Connect):
~$30.2K/yr.

**What's NOT included:** personnel (reviewers, platform ops), ProServe/SI delivery fees, data
egress at scale, AWS enterprise support plan, non-prod environments (dev/test/staging — commonly
+30–60% of the prod infra baseline, minimal Bedrock in demo mode).

## Multi-agent scaling

A second agent reuses the shared `platform_core` control plane (gateway, PHI masker, audit,
governance) and adds mostly its own inference, orchestration, and connector cost. The
per-agent fixed isolation baseline does recur (each agent gets its own VPC/KMS/audit in the
CloudFormation, CIDRs 10.30–10.37), but the governance build is not re-paid — that is the TCO
expression of the platform thesis.

## ROI worksheet outline

Net the value model against run cost and SI fees:

```
(A) Modeled annual value         from COST-ROI-MODEL.md / agent docs/roi-analysis.md
                                   = Recovered revenue + Rework cost avoided
(B) Annual AWS run cost          = monthly run-cost total × 12   (this model)
(C) SI fees                      = Assessment + POC + Pilot + Managed Service (placeholders)
(D) Net first-year value         = A − B − C
(E) Steady-state annual value    = A − B − (Managed Service annual)
(F) Payback period               = (C + setup) / monthly net run-rate
```

Populate (A) from the per-agent value model, (B) from the AWS Pricing Calculator using the
sizing above, and (C) from the offering price bands. Present (D), (E), and (F) on the one-page
CFO summary. Demand context: >80% of health-system execs and 70% of health plans are
prioritizing agentic AI in exactly these workflows `[industry-research]` — the question for the
customer is governed run cost versus value, which this worksheet makes explicit.

## Honesty note

These are planning figures. Production run cost is confirmed only after live-connector
validation and observed token usage in the pilot. No figure here is a quote.

---
**Value side:** see [ROI-CASE-STUDY.md](ROI-CASE-STUDY.md) for a fully worked, illustrative ROI example with totals.
