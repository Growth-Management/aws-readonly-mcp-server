from __future__ import annotations

from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.server.config import Settings, load_settings


class AWSClientFactory:
    """Creates AWS sessions and clients through the configured readonly role."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        self._session: boto3.Session | None = None

    def create_session(self) -> boto3.Session:
        if self._session is not None:
            return self._session

        base_session = boto3.Session(
            aws_access_key_id=self.settings.aws_access_key_id or None,
            aws_secret_access_key=self.settings.aws_secret_access_key or None,
            region_name=self.settings.aws_region,
        )

        if not self.settings.aws_role_arn:
            self._session = base_session
            return self._session

        sts_client = base_session.client("sts", region_name=self.settings.aws_region)
        assume_role_args: dict[str, Any] = {
            "RoleArn": self.settings.aws_role_arn,
            "RoleSessionName": self.settings.aws_role_session_name,
        }
        if self.settings.aws_external_id:
            assume_role_args["ExternalId"] = self.settings.aws_external_id

        response = sts_client.assume_role(**assume_role_args)
        credentials = response["Credentials"]
        self._session = boto3.Session(
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
            region_name=self.settings.aws_region,
        )
        return self._session

    def create_client(self, service_name: str) -> Any:
        return self.create_session().client(service_name, region_name=self.settings.aws_region)

    def get_caller_identity(self) -> dict[str, Any]:
        try:
            return self.create_client("sts").get_caller_identity()
        except (BotoCoreError, ClientError) as exc:
            return {
                "status": "error",
                "error_type": exc.__class__.__name__,
                "message": str(exc),
            }
