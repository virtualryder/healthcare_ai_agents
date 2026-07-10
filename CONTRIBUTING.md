# Contributing

## Repository conventions
- **Each agent is an independent deployable** with its own top-level `agent/` and `tools/`
  packages. Because those names repeat across agents, run tests **per agent** (see
  `scripts/run_tests.sh`) — a single pytest invocation across multiple agents collides.
- **No agent calls a vendor SDK directly.** All system-of-record access goes through the MCP
  authorization gateway (`platform_core/hpp_agent_platform/mcp_gateway/`). New tools are
  registered in `policy.py` (`TOOL_REGISTRY`, `AGENT_TOOL_GRANTS`, `ROLE_ENTITLEMENTS`).
- **Consequential authorities stay withheld.** An agent may prepare/draft/flag/recommend; a
  human commits. Do not grant an agent a tool that submits a claim, issues a determination,
  signs a note, or recoups a payment.
- **Prompts are hash-pinned.** Change a prompt → regenerate its `governance/prompt_manifest.json`
  entry and bump the version. `governance/tests/test_all_prompts_pinned.py` enforces this.

## Before you push
```bash
make test           # 258 tests (as of 2026-07-10), no API key
make lint-cfn       # CloudFormation clean
python -m py_compile $(find platform_core governance 0*-*-agent -name '*.py')
```

## Adding an agent
Mirror an existing agent: `agent/{state,nodes,graph,core,persistence,serve,prompts}.py`,
`tools/gateway_tools.py`, `data/fixtures/`, `demo/`, `tests/`, `docs/` (4), `README.md`,
`requirements.txt`, `Dockerfile`, `.env.example`. Register grants/roles in `policy.py`, add the
prompts to the manifest, add the agent to `scripts/run_tests.sh`, and stamp its CloudFormation
params (`infra/cloudformation/params/<agent>.json`, distinct VPC CIDR).

## Disclaimer
This is a decision-support accelerator, not a validated/certified product. See `README.md`.
