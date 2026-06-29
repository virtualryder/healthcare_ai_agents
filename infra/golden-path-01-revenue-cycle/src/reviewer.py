"""
Reviewer service Lambda — the authenticated two-person approval authority.

This is the component that closes the golden-path approval-bypass finding. With
AUTH_REQUIRE_BOUND_APPROVAL=1 set on the connector Lambda, the gateway accepts a
high-risk write ONLY against a bound, single-use approval token. This service is the
only thing that mints one, and it does so under its OWN Cognito authorizer:

  1. The REVIEWER authenticates here independently (separate JWT authorizer context),
     so the reviewer identity is verified by the platform — never asserted by the
     requester's client.
  2. We enforce that the reviewer holds an approver role and is NOT the requester
     (separation of duties; mint_approval re-checks this and fails closed).
  3. We mint a token cryptographically BOUND to the exact {agent, tool, canonical
     args, requester}. It cannot be retargeted to a different claim/tool/args.
  4. The mint is written to the same append-only, PHI-masked audit trail.

In production the pending request (agent/tool/args/requester) is read from the HITL
table by request_id rather than echoed in the body; the body form here keeps the
reference deployable without a separate queue.
"""
import json
import os

try:
    from hpp_agent_platform import approvals as _approvals
    from hpp_agent_platform.mcp_gateway import MCPGateway
    from hpp_agent_platform.mcp_gateway.audit import GatewayAuditLog
    _IMPORT_ERR = None
except Exception as _e:  # pragma: no cover
    _approvals = None
    _IMPORT_ERR = str(_e)

AGENT_ID = "01-revenue-cycle-denial"
_APPROVER_ROLES = {r.strip() for r in os.getenv(
    "APPROVER_ROLES", "denial_specialist,reviewer,medical_director").split(",") if r.strip()}


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


def handler(event, context):
    path = (event.get("rawPath") or "")
    if path.endswith("/ping"):
        return _resp(200, {"status": "healthy", "service": "reviewer", "ready": _approvals is not None})
    if _approvals is None:
        return _resp(500, {"error": "platform_core not bundled", "detail": _IMPORT_ERR})

    body = json.loads(event.get("body") or "{}")
    tool = body.get("tool")
    args = body.get("args") or {}
    requester_sub = body.get("requester_sub")
    if not tool or not requester_sub:
        return _resp(400, {"error": "tool and requester_sub are required"})

    # Reviewer identity comes from THIS endpoint's verified JWT authorizer — not the body.
    claims = (((event.get("requestContext") or {}).get("authorizer") or {}).get("jwt") or {}).get("claims") or {}
    reviewer_sub = claims.get("sub")
    if not reviewer_sub:
        return _resp(401, {"error": "no authenticated reviewer"})
    if not (_roles(claims) & _APPROVER_ROLES):
        return _resp(403, {"error": "reviewer lacks an approver role", "need_one_of": sorted(_APPROVER_ROLES)})
    if reviewer_sub == requester_sub:
        return _resp(403, {"error": "separation of duties: reviewer must differ from requester"})

    try:
        token = _approvals.mint_approval(
            reviewer_sub=reviewer_sub, requester_sub=requester_sub,
            agent_id=AGENT_ID, tool=tool, args=args,
        )
    except _approvals.ApprovalError as exc:
        return _resp(403, {"error": str(exc)})

    _audit().record({
        "decision": "APPROVAL_MINTED", "tool": tool, "agent_id": AGENT_ID,
        "user": reviewer_sub, "approved_for": requester_sub, "args": args,
    })
    return _resp(200, {"token": token, "tool": tool, "bound_to": "agent+tool+args+requester",
                       "single_use": True})
