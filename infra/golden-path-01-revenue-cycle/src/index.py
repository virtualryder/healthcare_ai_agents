"""
Golden-path connector Lambda — the deployed HTTP tool route runs THROUGH the governed
MCP gateway, not around it. For POST /tool/{kind}/{method} it:
  1. takes the JWT-verified identity from the API Gateway authorizer context
     (the Cognito JWT authorizer already verified signature/iss/aud/exp at the edge),
  2. authorizes the call via the deny-by-default gateway (agent grant ∩ user entitlement),
  3. requires a BOUND approval token for high-risk writes (AUTH_REQUIRE_BOUND_APPROVAL=1),
  4. mints a scoped token, invokes the connector (fixture here), and
  5. writes a PHI-masked, hash-chained audit record to the durable append-only sink.

The function runs in private subnets with NO internet route; GET /egress-check proves it
(a public-internet connect must fail closed). `hpp_agent_platform` is vendored next to this
handler by build.sh before `sam build`.
"""
import json
import os
import socket


def _build_gateway():
    """Construct the gateway wired to DURABLE stores when the env points at them, so
    the deployed path ENFORCES what the README claims:
      * AUDIT_TABLE -> append-only DynamoDB audit sink (not in-memory)
      * JTI_TABLE   -> DynamoDB single-use guard (replay-safe across concurrent Lambdas)
      * AUTH_REQUIRE_BOUND_APPROVAL=1 -> only reviewer-service tokens authorize writes
    Falls back to in-memory stores for local/fixture runs."""
    from hpp_agent_platform.mcp_gateway import MCPGateway
    from hpp_agent_platform.mcp_gateway.audit import GatewayAuditLog
    audit = None
    if os.getenv("AUDIT_TABLE"):  # pragma: no cover - requires AWS
        from hpp_agent_platform.audit_sinks import DynamoDBAppendOnlySink
        audit = GatewayAuditLog(sink=DynamoDBAppendOnlySink(os.environ["AUDIT_TABLE"]))
    jti_store = None
    if os.getenv("JTI_TABLE"):  # pragma: no cover - requires AWS
        from hpp_agent_platform import approvals as _approvals
        jti_store = _approvals.DynamoDBJtiStore(os.environ["JTI_TABLE"])
    return MCPGateway(audit=audit, connector_mode=os.getenv("CONNECTOR_MODE", "fixture"),
                      jti_store=jti_store)


try:
    _GW = _build_gateway()
except Exception as _e:  # pragma: no cover
    _GW = None
    _IMPORT_ERR = str(_e)

AGENT_ID = "01-revenue-cycle-denial"


def _resp(code, body):
    return {"statusCode": code, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}


def _egress_check(host="1.1.1.1", port=443, timeout=2.0):
    """Prove the data-residency boundary: in a correctly-isolated deployment the runtime
    has NO route to the public internet, so this connect must fail closed. A 'REACHABLE'
    result means the network model is NOT enforced and the deployment must be rejected."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return {"public_internet_egress": "REACHABLE", "blocked": False,
                "verdict": "FAIL — runtime can egress to the internet"}
    except Exception as exc:
        return {"public_internet_egress": "BLOCKED", "blocked": True,
                "verdict": "PASS — no public egress path", "detail": type(exc).__name__}


def handler(event, context):
    path = (event.get("rawPath") or "")
    if path.endswith("/ping"):
        return _resp(200, {"status": "healthy", "gateway": bool(_GW)})
    if path.endswith("/egress-check"):
        return _resp(200, _egress_check())
    if _GW is None:
        return _resp(500, {"error": "platform_core not bundled", "detail": _IMPORT_ERR})

    pp = event.get("pathParameters") or {}
    kind, method = pp.get("kind"), pp.get("method")
    tool = f"{kind}.{method}"
    body = json.loads(event.get("body") or "{}")

    # identity from the verified JWT authorizer context (never trust the client body)
    claims = (((event.get("requestContext") or {}).get("authorizer") or {}).get("jwt") or {}).get("claims") or {}
    user_claims = {"sub": claims.get("sub"), "custom:hpp_role": claims.get("custom:hpp_role", "")}

    res = _GW.invoke(user_claims=user_claims, agent_id=AGENT_ID, tool=tool,
                     args=body.get("args") or {}, approval=body.get("approval"))
    return _resp(200 if res.decision != "DENY" else 403, {
        "decision": res.decision, "tool": tool, "audit_id": res.audit_id,
        "reason": res.reason, "result": res.result,
    })
