from __future__ import annotations

from typing import Any

from src.server.config import load_settings


class AWSClientFactory:
    """Creates AWS clients.

    Replace the placeholder methods with real boto3 session and client logic.
    Prefer AssumeRole-based sessions for production use.
    """

    def __init__(self) -> None:
        self.settings = load_settings()

    def create_session(self) -> dict[str, Any]:
        return {
            "status": "not_implemented",
            "role_arn": self.settings.aws_role_arn,
            "region": self.settings.aws_region,
        }

    def create_client(self, service_name: str) -> dict[str, Any]:
        return {
            "status": "not_implemented",
            "service_name": service_name,
            "region": self.settings.aws_region,
        }
