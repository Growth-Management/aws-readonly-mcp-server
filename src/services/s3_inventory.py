from __future__ import annotations

from typing import Any

from src.aws.client_factory import AWSClientFactory


class S3InventoryService:
    def __init__(self) -> None:
        self.factory = AWSClientFactory()

    def list_buckets(self) -> dict[str, Any]:
        return {
            "status": "not_implemented",
            "message": "Implement S3 bucket listing via AWS client layer",
        }

    def get_bucket_details(self, bucket_name: str) -> dict[str, Any]:
        return {
            "status": "not_implemented",
            "bucket_name": bucket_name,
        }
