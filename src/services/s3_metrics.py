from __future__ import annotations

from typing import Any

from src.aws.client_factory import AWSClientFactory


class S3MetricsService:
    def __init__(self) -> None:
        self.factory = AWSClientFactory()

    def get_request_metrics(self, bucket_name: str) -> dict[str, Any]:
        return {
            "status": "not_implemented",
            "bucket_name": bucket_name,
            "message": "Implement CloudWatch or aggregated metrics lookup",
        }

    def get_transfer_summary(self, bucket_name: str) -> dict[str, Any]:
        return {
            "status": "not_implemented",
            "bucket_name": bucket_name,
            "message": "Implement transfer summary lookup",
        }
