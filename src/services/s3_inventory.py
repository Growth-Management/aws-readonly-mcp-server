from __future__ import annotations

from typing import Any

from src.aws.client_factory import AWSClientFactory


def _error_response(error: Exception, **extra: Any) -> dict[str, Any]:
    return {"status": "error", "error_type": type(error).__name__, "message": str(error), **extra}


class S3InventoryService:
    def __init__(self, factory: AWSClientFactory | None = None) -> None:
        self.factory = factory or AWSClientFactory()

    def list_buckets(self) -> dict[str, Any]:
        try:
            response = self.factory.create_client("s3").list_buckets()
        except Exception as exc:
            return _error_response(exc)

        buckets = [
            {
                "name": bucket["Name"],
                "creation_date": bucket["CreationDate"].isoformat(),
            }
            for bucket in response.get("Buckets", [])
        ]
        return {"status": "ok", "bucket_count": len(buckets), "buckets": buckets}

    def get_bucket_details(self, bucket_name: str) -> dict[str, Any]:
        try:
            s3 = self.factory.create_client("s3")
            location = s3.get_bucket_location(Bucket=bucket_name).get("LocationConstraint")
            tagging = _safe_call(s3.get_bucket_tagging, Bucket=bucket_name)
            versioning = _safe_call(s3.get_bucket_versioning, Bucket=bucket_name)
            lifecycle = _safe_call(s3.get_bucket_lifecycle_configuration, Bucket=bucket_name)
            encryption = _safe_call(s3.get_bucket_encryption, Bucket=bucket_name)
            logging = _safe_call(s3.get_bucket_logging, Bucket=bucket_name)
        except Exception as exc:
            return _error_response(exc, bucket_name=bucket_name)

        return {
            "status": "ok",
            "bucket_name": bucket_name,
            "region": location or "us-east-1",
            "tags": tagging,
            "versioning": versioning,
            "lifecycle": lifecycle,
            "encryption": encryption,
            "logging": logging,
        }


def _safe_call(func: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        return {"status": "ok", "data": func(**kwargs)}
    except Exception as error:  # pragma: no cover - exercised against AWS
        return {
            "status": "access_denied_or_unavailable",
            "error_type": type(error).__name__,
            "message": str(error),
        }
