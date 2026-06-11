from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    aws_role_arn: str
    aws_region: str
    mcp_auth_token: str
    app_env: str = "development"
    log_level: str = "INFO"
    default_lookback_months: int = 3


def load_settings() -> Settings:
    return Settings(
        aws_role_arn=os.getenv("AWS_ROLE_ARN", ""),
        aws_region=os.getenv("AWS_REGION", "ap-northeast-1"),
        mcp_auth_token=os.getenv("MCP_AUTH_TOKEN", ""),
        app_env=os.getenv("APP_ENV", "development"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        default_lookback_months=int(os.getenv("DEFAULT_LOOKBACK_MONTHS", "3")),
    )
