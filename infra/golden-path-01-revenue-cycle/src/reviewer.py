"""
Reviewer service Lambda — the authenticated two-person approval authority.

This component closes the approval-bypass finding AND drives the human gate of the Step
Functions workflow. With AUTH_REQUIRE_BOUND_APPROVAL=1 on the runtime functions, a high-risk
write executes ONLY against a bound, single-use token, and this service is the only thing that
mints one — under its OWN Cognito authorizer:

  1. The REVIEWER authenticates here independently (separate JWT authorizer context), so the
     reviewer identity is verified by the platform, never asserted by the requester's client.
  2. If a review_id is supplied, the exact pending write (tool, args, requester) and the Step
     Functions TaskToken are read from the HITL table — the reviewer approves precisely what the
     workflow paused on, not values echoed by a caller.
  3. We enforce approver role + reviewer != requester (mint_approval re-checks, fail-closed).
  4. We mint a token cryptographically BOUND to {agent, tool, canonical args, requester}, write
     the mint to the append-only audit, and — for the async workflow — resume the paused
     execution with SendTaskSuccess so finalize runs with the bound token.
"""
import json
import os

try:
    from hpp_agent_platform import approvals as _approvals
    from hpp_agent_platform.mcp_gateway.audit import GatewayAuditLog
    _IMPORT_ERR = None
except Exception as _e:  # pragma: no cover
    _approvals = None
    _IMPORT_ERR = str(_e)

AGENT_ID = "01-revenue-cycle-denial"
_APPROVER_ROLES = {r.strip() for r in os.getenv(
    "APPROVER_ROLES", "denial_specialist,DENIALS_SPECIALIST,reviewer,medical_director").split(",") if r.strip()}


def _resp(code, body):
    return {"statusCode": code, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}


def _roles(claims):
    raw = claims.get(os.getenv("AUTH_ROLE_CLAIM", "custom:hpp_role")) or claims.get("cognito:groups") or ""
    return {r.strip() for r in (raw.split(",") if isinstance(raw, str) else [str(x) for x in raw]) if r}


def _audit():
    table = os.getenv("AUDIT_TABLE")
    if table:  # pragma: no cover - requires AWS
        from hpp_agent_platform.audit_sinks import DynamoDBAppendOnlySink
        return GatewayAuditLog(sink=DynamoDBAppendOnlySink(table))
    return GatewayAuditLog()


def _denumber(o):
    """Coerce DynamoDB Decimals back to native int/float so the approval's args-binding hash
    matches the workflow's JSON-native args (else the bound token is rejected at finalize)."""
    from decimal import Decimal
    if isinstance(o, Decimal):
        return int(o) if o == o.to_integral_value() else float(o)
    if isinstance(o, dict):
        return {k: _denumber(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_denumber(v) for v in o]
    return o


def _load_pending(review_id):  # pragma: no cover - requires AWS
    """Read the exact pending write + Step Functions TaskToken the workflow paused on."""
    table = os.getenv("HITL_TABLE")
    if not (table and review_id):
        return None
    import boto3  # type: ignore
    item = boto3.resource("dynamodb").Table(table).get_item(Key={"review_id": review_id}).get("Item")
    return item


def _resume_workflow(task_token, token):  # pragma: no cover - requires AWS
    """Resume the paused execution; finalize then runs with the bound approval token."""
    import boto3  # type: ignore
    boto3.client("stepfunctions").send_task_success(
        taskToken=task_token, output=json.dumps({"token": token}))


def handler(event, context):
    path = (event.get("rawPath") or "")
    if path.endswith("/ping"):
        return _resp(200, {"status": "healthy", "service": "reviewer", "ready": _approvals is not None})
    if _approvals is None:
        return _resp(500, {"error": "platform_core not bundled", "detail": _IMPORT_ERR})

    body = json.loads(event.get("body") or "{}")
    review_id = body.get("review_id")
    pending = _load_pending(review_id)

    if pending:  # async workflow path — approve exactly what the workflow paused on
        tool, args = pending["tool"], _denumber(pending.get("args") or {})
        requester_sub = pending.get("requester_sub")
        task_token = pending.get("task_token")
    else:        # synchronous path — caller presents the write to approve
        tool, args = body.get("tool"), body.get("args") or {}
        requester_sub = body.get("requester_sub")
        task_token = None
    if not tool or not requester_sub:
        return _resp(400, {"error": "tool and requester_sub are required (or a resolvable review_id)"})

    claims = (((event.get("requestContext") or {}).get("authorizer") or {}).get("jwt") or {}).get("claims") or {}
    reviewer_sub = claims.get("sub")
    if not reviewer_sub:
        return _resp(401, {"error": "no authenticated reviewer"})
    if not (_roles(claims) & _APPROVER_ROLES):
        return _resp(403, {"error": "reviewer lacks an approver role", "need_one_of": sorted(_APPROVER_ROLES)})
    if reviewer_sub == requester_sub:
        return _resp(403, {"error": "separation of duties: reviewer must differ from requester"})

    try:
        token = _approvals.mint_approval(reviewer_sub=reviewer_sub, requester_sub=requester_sub,
                                         agent_id=AGENT_ID, tool=tool, args=args)
    except _approvals.ApprovalError as exc:
        return _resp(403, {"error": str(exc)})

    _audit().record({"decision": "APPROVAL_MINTED", "tool": tool, "agent_id": AGENT_ID,
                     "user": reviewer_sub, "approved_for": requester_sub, "args": args})

    resumed = False
    if task_token:  # pragma: no cover - requires AWS
        _resume_workflow(task_token, token)
        resumed = True

    return _resp(200, {"token": token, "tool": tool, "single_use": True,
                       "bound_to": "agent+tool+args+requester", "workflow_resumed": resumed})
