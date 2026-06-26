"""
Secrets accessor — thin indirection over the secret store.

Dev reads environment variables; production resolves from AWS Secrets Manager (or
SSM Parameter Store SecureString) via the agent's task role. Call sites never see
a raw credential literal, so rotating a connector credential (an EHR client
secret, a clearinghouse API key) is an infra action, not a code change.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional


@lru_cache(maxsize=128)
def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    # 1. environment (dev / CI)
    val = os.getenv(name)
    if val is not None:
        return val
    # 2. AWS Secrets Manager (production) — lazy import, soft-fail to default
    if os.getenv("SECRETS_BACKEND", "").strip().lower() == "aws":  # pragma: no cover
        try:
            import boto3  # type: ignore

            client = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION", "us-east-1"))
            return client.get_secret_value(SecretId=name)["SecretString"]
        except Exception:
            return default
    return default
