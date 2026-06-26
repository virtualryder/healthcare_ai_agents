# Disaster Recovery — HPP AI Agent Suite

This runbook covers recovery of the suite from an availability or data-integrity event:
an Availability Zone or Region impairment, accidental data loss, or a corrupted/abandoned
agent execution. The design goal is that recovery never bypasses a human gate — a
suspended approval must come back as suspended, never auto-resolved.

## RPO / RTO targets (defaults; ratify per engagement SLA)

| Tier | Component | RPO | RTO |
|---|---|---|---|
| Critical | Append-only audit (DynamoDB + WORM S3) | ~5 min (PITR/continuous) | 1 hr |
| Critical | HITL approval state (DynamoDB + in-flight Step Functions) | ~5 min | 1 hr |
| Important | Connector framework / gateway service | N/A (stateless) | 1 hr |
| Important | Agent orchestration (LangGraph / Strands runtime) | N/A (stateless) | 2 hr |
| Standard | Prompt registry / governance artifacts (in-repo, versioned) | Source-controlled | 2 hr |

## What is stateful vs. stateless

**Stateful — must be restored to a consistent point:**
- **Audit (DynamoDB)** — append-only; Update/Delete denied by policy; Point-in-Time
  Recovery (PITR) enabled; KMS-encrypted. PITR is the recovery mechanism.
- **Audit WORM (S3)** — Object Lock in COMPLIANCE mode, 7-year default retention. WORM
  objects are immutable and cannot be deleted even by an admin during the retention
  window — this is the tamper-evidence guarantee and constrains recovery (you restore by
  re-pointing, not by rewriting).
- **HITL table (DynamoDB)** — pending approvals and their tokens; PITR enabled.
- **Step Functions executions** — in-flight state machines, especially those suspended at
  a `waitForTaskToken` human gate. The task token is the recovery-critical artifact.

**Stateless — redeploy from CloudFormation/source:**
- MCP authorization gateway (portable API GW + Cognito + STS, or AgentCore Gateway),
  connector Lambdas, the agent orchestration runtime, Bedrock Guardrail config (declared
  in the security stack), and KMS CMK (key material is durable; the stack reattaches it).

## Multi-AZ / multi-Region posture

- **Default (single-Region, Multi-AZ):** DynamoDB, S3, KMS, Step Functions, and Lambda are
  regional, Multi-AZ services — an AZ failure is absorbed with no action. The per-agent VPC
  (CIDRs `10.30.0.0/16` … `10.37.0.0/16`) spans multiple AZs via the network stack.
- **Region resilience (engagement option):** add DynamoDB PITR-based cross-Region restore
  or global tables, S3 Cross-Region Replication (preserving Object Lock), and a warm
  redeploy of the stateless stacks in the secondary Region. Region failover is an
  engagement decision, not a default — call it out honestly in the SLA.

## Restore procedure

1. **Declare DR.** Incident Commander confirms scope (AZ vs. Region vs. data loss) and
   the recovery target time.
2. **Stand up stateless infrastructure first.** Redeploy the CloudFormation stacks into
   the recovery target: `scripts/deploy.sh <AgentId> <env> <portable|agentcore>
   <native|container> s3://bucket/prefix <VpcCidr>`. This recreates network, security
   (KMS CMK, Guardrail, Cognito, least-privilege role), gateway, connectors, and the agent
   service. Confirm `cfn-lint`-clean templates staged to S3.
3. **Restore the audit (DynamoDB) via PITR** to the chosen recovery point. Re-attach the
   KMS CMK. Verify the table still denies Update/Delete after restore.
4. **Reattach / restore audit WORM (S3).** In-Region, the WORM bucket survives AZ loss
   untouched. Cross-Region, point the agent service at the replicated bucket; never attempt
   to rewrite Object Lock objects.
5. **Restore the HITL table via PITR.** This brings back pending approvals and their task
   tokens.
6. **Recover the human gate (suspended HITL state machines).** Suspended
   `waitForTaskToken` executions are the delicate part:
   - If executions survived (AZ event), they resume when the gateway/connectors return.
   - If executions were lost (Region event), **do not auto-approve.** Re-enqueue each
     pending item from the restored HITL table as a *fresh, still-suspended* approval so a
     named human re-reviews it. A determination or submission must never ship because of a
     recovery shortcut. Reconcile any token that cannot be matched as "requires manual
     re-review."
7. **Reconnect connectors** (fixture first, then live) and confirm gateway deny-by-default
   is enforcing.

## Validation after restore

- **Integrity:** audit table still denies Update/Delete; WORM retention intact; KMS
  encryption confirmed; no gap in the audit sequence beyond the RPO window.
- **Gate:** run the human-gate smoke test — drive one high-risk action (e.g., a denial
  draft or PA assembly) and confirm it suspends at the correct named gate and cannot
  proceed without approval.
- **Authorization:** confirm a tool call outside agent grant ∩ user entitlement is denied.
- **Governance:** run grounding verification and a red-team case to confirm the controls
  survived the restore.
- **Reconciliation:** every pre-incident pending approval is accounted for as approved,
  rejected, or re-enqueued — none silently lost or auto-resolved.
- **Close DR** only after the Privacy Officer confirms no integrity loss to the audit.
