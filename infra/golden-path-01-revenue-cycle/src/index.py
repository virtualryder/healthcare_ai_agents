"""
Golden-path connector Lambda — the deployed HTTP tool route runs THROUGH the governed
MCP gateway, not around it. For POST /tool/{kind}/{method} it:
  1. takes the JWT-verified identity from the API Gateway authorizer context
     (the Cognito JWT authorizer already verified signature/iss/aud/exp at the edge),
  2. authorizes the call via the deny-by-default gateway (agent grant ∩ user entitlement),
  3. requires a bound approval for high-risk writes,
  4. mints a scoped token, invokes the connector (fixture here), and
  5. writes a PHI-masked, hash-chained audit record.
`hpp_agent_platform` is vendored next to this handler by `build.sh` before `sam build`.
"""
import json

try:
    from hpp_agent_platform.mcp_gateway import MCPGateway
    _GW = MCPGateway(connector_mode="fixture")
except Exception as _e:  # pragma: no cover
    _GW = None
    _IMPORT_ERR = str(_e)

AGENT_ID = "01-revenue-cycle-denial"


def _resp(code, body):
    return {"statusCode": code, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}


def handler(event, context):
    path = (event.get("rawPath") or "")
    if path.endswith("/ping"):
        return _resp(200, {"status": "healthy", "gateway": bool(_GW)})
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
