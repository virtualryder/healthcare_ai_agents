# Agent 01 — container image honoring the AgentCore Runtime contract
# (ARM64, HTTP /invocations + /ping). Also runs the Streamlit demo.
FROM --platform=linux/arm64 python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 EXTRACT_MODE=demo PYTHONPATH=/app:/app/platform_core

# ── Secure by default ─────────────────────────────────────────────────────────
# The /invocations runtime path enforces a VERIFIED identity and a BOUND approval;
# it never trusts caller-supplied acting_user_claims / human_approval in the body.
#   AUTH_REQUIRE_JWT=1            -> serve.py (edge authorizer) + the gateway require a
#                                   cryptographically verified JWT; body claims are
#                                   replaced by the token's claims and fail closed (401)
#                                   when no valid token is presented. Supply the verifier
#                                   JWKS out-of-band via AUTH_JWKS / AUTH_JWKS_PATH, and
#                                   run an OIDC/JWT authorizer (AgentCore Identity, or
#                                   API GW / ALB + OIDC) in front of this container.
#   AUTH_REQUIRE_BOUND_APPROVAL=1 -> only a bound, single-use, separation-of-duties
#                                   approval token can authorize a high-risk write; a
#                                   bare {"approved": true, "reviewer": ...} is refused.
# The bundled Streamlit/CLI demo (EXTRACT_MODE=demo, no authorizer) needs an explicit
# `-e AUTH_REQUIRE_JWT=0` override — see 01-revenue-cycle-denial-agent/README.md
# ("Container auth contract"). We do NOT weaken the runtime contract for the demo.
ENV AUTH_REQUIRE_JWT=1 AUTH_REQUIRE_BOUND_APPROVAL=1

COPY platform_core /app/platform_core
COPY governance /app/governance
COPY 01-revenue-cycle-denial-agent /app/01-revenue-cycle-denial-agent

RUN pip install --no-cache-dir -e /app/platform_core \
 && pip install --no-cache-dir langgraph>=0.2 streamlit>=1.36

EXPOSE 8080 8501
# Runtime contract entrypoint (serve.py provides /invocations + /ping):
CMD ["python", "/app/01-revenue-cycle-denial-agent/agent/serve.py"]
