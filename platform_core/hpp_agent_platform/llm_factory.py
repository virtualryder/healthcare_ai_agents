"""
Provider-abstracted LLM factory for the HPP agent suite.

One factory, two providers, two model tiers:

    PROVIDERS (env: LLM_PROVIDER)
      anthropic  (default)  ChatAnthropic via the Anthropic API.
      bedrock               ChatBedrockConverse via a VPC interface endpoint —
                            inference stays inside the organization's AWS account
                            under an AWS BAA. THIS is the configuration that makes
                            the PHI-residency story true (no patient data egress to
                            an external AI API) and the tier Amazon Bedrock
                            AgentCore Runtime uses. Amazon Bedrock is HIPAA-eligible
                            under the AWS BAA — see docs/COMPLIANCE-CONTROL-MAPPINGS.md.

    TIERS (role argument)
      narrative  Claude Sonnet — appeal letters, PA clinical rationales, chart
                 summaries, member-facing explanations: anything a clinician,
                 payer reviewer, or patient reads.
      fast       Claude Haiku — high-volume denial-reason classification, code
                 suggestion, intent routing, extraction-assist where latency /
                 unit cost dominate.

Bedrock Guardrails: set BEDROCK_GUARDRAIL_ID (+ optional BEDROCK_GUARDRAIL_VERSION,
default DRAFT) and every Bedrock call is wrapped with the configured guardrail
(PHI filters, denied topics, contextual grounding checks). Guardrails are a
deployment control — configure them in IaC (infra/cloudformation/security,
infra/terraform/modules/security) and reference the ID here.
Ref: https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html

Env reference:
    LLM_PROVIDER                anthropic | bedrock      (default anthropic)
    ANTHROPIC_API_KEY           required for anthropic provider
    CLAUDE_NARRATIVE_MODEL      default claude-sonnet-4-6
    CLAUDE_FAST_MODEL           default claude-haiku-4-5
    BEDROCK_NARRATIVE_MODEL_ID  default anthropic.claude-sonnet-4-6-20260601-v1:0
    BEDROCK_FAST_MODEL_ID       default anthropic.claude-haiku-4-5-20251001
    BEDROCK_REGION              default us-east-1
    BEDROCK_GUARDRAIL_ID        optional in dev — REQUIRED in production
    BEDROCK_GUARDRAIL_VERSION   default DRAFT
    ENVIRONMENT                 production|prod -> guardrail is mandatory
    REQUIRE_BEDROCK_GUARDRAIL   1|true|yes -> guardrail is mandatory
"""
from __future__ import annotations

import logging
import os
from typing import Any, Literal

logger = logging.getLogger(__name__)

Role = Literal["narrative", "fast"]

ANTHROPIC_MODELS = {
    "narrative": os.getenv("CLAUDE_NARRATIVE_MODEL", "claude-sonnet-4-6"),
    "fast": os.getenv("CLAUDE_FAST_MODEL", "claude-haiku-4-5"),
}
BEDROCK_MODELS = {
    "narrative": os.getenv("BEDROCK_NARRATIVE_MODEL_ID", "anthropic.claude-sonnet-4-6-20260601-v1:0"),
    "fast": os.getenv("BEDROCK_FAST_MODEL_ID", "anthropic.claude-haiku-4-5-20251001"),
}


def provider() -> str:
    return os.getenv("LLM_PROVIDER", "anthropic").strip().lower()


def get_llm(role: Role = "narrative", temperature: float = 0.0, max_tokens: int = 4096) -> Any:
    """
    Return a chat model for the requested tier on the configured provider.

    The return type is a LangChain chat model in both branches, so calling code is
    provider-agnostic. Imports are lazy: langchain-aws is only required when
    LLM_PROVIDER=bedrock.
    """
    if provider() == "bedrock":
        from langchain_aws import ChatBedrockConverse  # lazy — optional dep

        kwargs: dict[str, Any] = dict(
            model=BEDROCK_MODELS[role],
            temperature=temperature,
            max_tokens=max_tokens,
            region_name=os.getenv("BEDROCK_REGION", "us-east-1"),
        )
        guardrail_id = os.getenv("BEDROCK_GUARDRAIL_ID", "")
        if guardrail_id:
            kwargs["guardrail_config"] = {
                "guardrailIdentifier": guardrail_id,
                "guardrailVersion": os.getenv("BEDROCK_GUARDRAIL_VERSION", "DRAFT"),
            }
        else:
            require = (
                os.getenv("REQUIRE_BEDROCK_GUARDRAIL", "").strip().lower() in ("1", "true", "yes")
                or os.getenv("ENVIRONMENT", "").strip().lower() in ("production", "prod")
            )
            if require:
                raise RuntimeError(
                    "Bedrock provider active WITHOUT Guardrails (BEDROCK_GUARDRAIL_ID unset) "
                    "in a production environment. Configure a guardrail (infra/cloudformation/"
                    "security or infra/terraform/modules/security) and set BEDROCK_GUARDRAIL_ID, "
                    "or unset ENVIRONMENT/REQUIRE_BEDROCK_GUARDRAIL for dev."
                )
            logger.warning(
                "Bedrock provider active WITHOUT Guardrails (BEDROCK_GUARDRAIL_ID unset). "
                "Production deployments must configure a guardrail — see infra/."
            )
        return ChatBedrockConverse(**kwargs)

    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=ANTHROPIC_MODELS[role],
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
