from __future__ import annotations

from typing import Any

from src.aws.client_factory import AWSClientFactory


def _metric_response(bucket_name: str, metric_name: str, note: str) -> dict[str, Any]:
    return {
        "status": "requires_metric_configuration",
        "bucket_name": bucket_name,
        "metric_name": metric_name,
        "message": note,
    }


class S3MetricsService:
    def __init__(self, factory: AWSClientFactory | None = None) -> None:
        self.factory = factory or AWSClientFactory()

    def get_request_metrics(self, bucket_name: str) -> dict[str, Any]:
        return _metric_response(
            bucket_name,
            "AllRequests",
            "S3 request metrics require CloudWatch request metrics or Storage Lens to be enabled.",
        )

    def get_transfer_summary(self, bucket_name: str) -> dict[str, Any]:
        return _metric_response(
            bucket_name,
            "BytesDownloaded/BytesUploaded",
            "Transfer summaries require CloudWatch metrics, Storage Lens, access logs, or Cost Explorer.",
        )
