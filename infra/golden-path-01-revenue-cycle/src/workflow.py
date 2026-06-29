"""
Denial-workflow dispatcher — the real Step Functions task logic for Agent 01.

The Standard state machine invokes this one function once per state, passing
``{"step": <name>, "state": <accumulating workflow state>}`` (plus a TaskToken for the
human gate). EVERY step that touches a system of record goes THROUGH the governed MCP
gateway, so the orchestration inherits deny-by-default authz, the bound-approval human
gate, scoped tokens, and the append-only PHI-masked audit — it never widens authority.

Steps:
  load_claim       -> pas.get_claim (read)
  analyze_denial   -> deterministic classification of the denial codes
  gather_evidence  -> clearinghouse.validate_claim + ehr.get_clinical_docs + kb.search_policy
  draft_appeal     -> deterministic grounded draft citing the gathered evidence
  compliance_check -> the draft must be grounded in gathered evidence; sets pending_write
  persist_review   -> waitForTaskToken: record {review_id, task_token, pending_write} to HITL
                      and pause; the reviewer service resumes the execution with a bound token
  finalize         -> payer.submit_appeal THROUGH the gateway using the bound approval token
                      (validates SoD + single-use + arg-binding); fixture mode does not transmit

`build.sh` vendors `hpp_agent_platform` next to this handler before `sam build`.
"""
import os
import uuid

AGENT_ID = "01-revenue-cycle-denial"


def _build_gateway():
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


def _persist_review(review_id, task_token, pending_write, requester_sub):  # pragma: no cover - AWS
    table = os.getenv("HITL_TABLE")
    if not table:
        return
    import boto3  # type: ignore
    boto3.resource("dynamodb").Table(table).put_item(Item={
        "review_id": review_id, "task_token": task_token, "status": "PENDING",
        "tool": pending_write["tool"], "args": pending_write["args"],
        "requester_sub": requester_sub,
    })


def run_step(step, state, *, gateway=None, task_token=None):
    """Pure, unit-testable workflow logic. Returns the merged state."""
    gw = gateway or _build_gateway()
    uc = state.get("user_claims") or {}
    claim_ref = state.get("claim_ref", "CLM-2026-55810")

    if step == "load_claim":
        r = gw.invoke(user_claims=uc, agent_id=AGENT_ID, tool="pas.get_claim",
                      args={"claim_ref": claim_ref})
        state["claim"] = r.result
        state["load_decision"] = r.decision
        return state

    if step == "analyze_denial":
        codes = (state.get("claim") or {}).get("denial_codes") or []
        state["analysis"] = {
            "denial_codes": codes,
            "appealable": bool(codes),
            "reason": "precertification/authorization absent" if "CO-197" in codes else "clinical review",
        }
        return state

    if step == "gather_evidence":
        evidence = {}
        for tool, args in (
            ("clearinghouse.validate_claim", {"claim_ref": claim_ref}),
            ("ehr.get_clinical_docs", {"encounter_ref": state.get("encounter_ref", "ENC-88231")}),
            ("kb.search_policy", {"query": "precertification appeal policy"}),
        ):
            r = gw.invoke(user_claims=uc, agent_id=AGENT_ID, tool=tool, args=args)
            evidence[tool] = {"decision": r.decision, "result": r.result}
        state["evidence"] = evidence
        return state

    if step == "draft_appeal":
        claim = state.get("claim") or {}
        cites = sorted((state.get("evidence") or {}).keys())
        state["appeal"] = {
            "claim_ref": claim_ref,
            "level": 1,
            "text": (f"Appeal for {claim_ref}: the denial {claim.get('denial_codes')} is contested. "
                     f"Supporting evidence: {', '.join(cites)}."),
            "citations": cites,
            "requires_human_approval": True,
        }
        return state

    if step == "compliance_check":
        appeal = state.get("appeal") or {}
        grounded = bool(appeal.get("citations"))  # the draft must cite gathered evidence
        state["compliance"] = {"grounded": grounded, "phi_masked": True, "ok": grounded}
        if grounded:
            # The exact write the human will approve and finalize will execute — identical args,
            # so the bound approval token binds to precisely this call.
            state["pending_write"] = {
                "tool": "payer.submit_appeal",
                "args": {"claim_ref": claim_ref, "level": 1, "reviewer": uc.get("sub")},
            }
        return state

    if step == "persist_review":
        pw = state.get("pending_write") or {}
        review_id = str(uuid.uuid4())
        _persist_review(review_id, task_token, pw, uc.get("sub"))
        state["review_id"] = review_id
        return state  # execution pauses here (waitForTaskToken) until the reviewer resumes it

    if step == "finalize":
        pw = state.get("pending_write") or {}
        approval = state.get("approval")  # {"token": ...} delivered by the reviewer service
        r = gw.invoke(user_claims=uc, agent_id=AGENT_ID, tool=pw.get("tool", "payer.submit_appeal"),
                      args=pw.get("args") or {}, approval=approval)
        state["finalize"] = {"decision": r.decision, "audit_id": r.audit_id,
                             "allowed": r.allowed, "result": r.result}
        return state

    raise ValueError(f"unknown workflow step: {step}")


def handler(event, context):
    step = event["step"]
    state = event.get("state") or {}
    return run_step(step, state, task_token=event.get("task_token"))
