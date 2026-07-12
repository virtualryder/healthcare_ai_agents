# Clean-Account Acceptance Report — HPP AI Agent Suite (Golden Path 01)

Sanitized deployment evidence for the golden-path acceptance run claimed in the README.
Validation account ID and IAM user are redacted; raw CLI JSON is available on request.
All verification queries were read-only.

**Account:** `<VALIDATION-ACCOUNT-ID>` · **Region:** us-east-1 · **Run date:** 2026-06-29 (UTC) · **Independently re-verified:** 2026-07-07 via AWS CLI.

## 1. Stack lifecycle

| Stack | Created (UTC) | Deleted (UTC) | Mechanism |
|---|---|---|---|
| hpp-gp01-acc | Jun 29 21:01 | Jun 29 22:27 | SAM (5 `ExecuteChangeSet` CloudTrail events 21:01–21:29) |

Step Functions `StartExecution` events during the window confirm the human-gate workflow was
exercised at runtime (pause → bound approval → finalize), matching the acceptance-test gate
(`acceptance_test.sh`: self-approval, replay, tamper, and egress negative cases).

## 2. Durable WORM evidence (still inspectable)

The acceptance run's audit records are preserved in the Object-Locked WORM bucket
`hpp-gp01-acc-wormbucket-*`, which S3 Object Lock (GOVERNANCE) prevented from being deleted at
teardown — the control demonstrating itself. As of 2026-07-07 the bucket still holds the
sequenced audit JSON records (`audit/000000000001…` onward, timestamps Jun 29 21:11 UTC).
This bucket is deliberately retained as tamper-proof evidence; it can be purged with a
governance-bypass delete after retention lapses.

## 3. KMS deletion marker

The run's CMK ("CMK for HPP golden-path 01 (test)") was observed in `PendingDeletion`
(scheduled 2026-07-29) on verification day — AWS's own record that the key existed and was
scheduled for deletion as designed.

## 4. Teardown verification

Re-verified 2026-07-07: zero `hpp-*` CloudFormation stacks, DynamoDB tables, or Cognito user
pools remain. Residuals: the WORM bucket (deliberate, §2) and the shared SAM artifact bucket.

## 5. Scope note

This report covers the hardened Agent 01 golden path — the canonical deployment path. Agents
02–08 share the same platform controls (offline-tested; part of the 270-test suite — see MATURITY.yaml) and
deploy via the alternative nested-stack reference, which has not been through this acceptance
gate. See the README capability maturity matrix.

## 6. Method

Read-only CLI: `cloudformation list-stacks`, `cloudtrail lookup-events`, `kms describe-key`,
`dynamodb list-tables`, `s3api list-objects-v2`, `cognito-idp list-user-pools`. Portfolio-level
export: `Projects-DR/evidence/AWS-CLEAN-ACCOUNT-EVIDENCE-2026-07-07.md` (kept outside the repo).
