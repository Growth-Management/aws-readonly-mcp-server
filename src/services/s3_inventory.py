from __future__ import annotations

from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from src.aws.client_factory import AWSClientFactory


class S3InventoryService:
    def __init__(self, factory: AWSClientFactory | None = None) -> None:
        self.factory = factory or AWSClientFactory()

    def list_buckets(self) -> dict[str, Any]:
        try:
            response = self.factory.create_client("s3").list_buckets()
        except (BotoCoreError, ClientError) as exc:
            return {
                "status": "error",
                "error_type": exc.__class__.__name__,
                "message": str(exc),
            }

        buckets = [
            {
                "name": bucket.get("Name"),
                "creation_date": bucket.get("CreationDate").isoformat()
                if bucket.get("CreationDate")
                else None,
            }
            for bucket in response.get("Buckets", [])
        ]
        return {
            "status": "ok",
            "bucket_count": len(buckets),
            "buckets": buckets,
        }

    def get_bucket_details(self, bucket_name: str) -> dict[str, Any]:
        return {
            "status": "not_implemented",
            "bucket_name": bucket_name,
        }
