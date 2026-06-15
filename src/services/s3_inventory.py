from __future__ import annotations

from typing import Any, Callable

from botocore.exceptions import BotoCoreError, ClientError
from src.aws.client_factory import AWSClientFactory

NOT_CONFIGURED_ERROR_CODES = {
    "NoSuchBucketPolicy",
    "NoSuchCORSConfiguration",
    "NoSuchLifecycleConfiguration",
    "NoSuchPublicAccessBlockConfiguration",
    "NoSuchTagSet",
    "NoSuchWebsiteConfiguration",
    "ReplicationConfigurationNotFoundError",
    "ServerSideEncryptionConfigurationNotFoundError",
}


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
        bucket_name = bucket_name.strip()
        if not bucket_name:
            return {"status": "error", "message": "bucket_name is required"}

        s3_client = self.factory.create_client("s3")
        location = self._call_s3(
            lambda: s3_client.get_bucket_location(Bucket=bucket_name),
            not_configured_status="unknown",
        )

        return {
            "status": "ok",
            "bucket_name": bucket_name,
            "region": self._normalize_region(location.get("data", {}).get("LocationConstraint"))
            if location.get("status") == "ok"
            else None,
            "location": location,
            "tags": self._call_s3(lambda: s3_client.get_bucket_tagging(Bucket=bucket_name)),
            "versioning": self._call_s3(
                lambda: s3_client.get_bucket_versioning(Bucket=bucket_name)
            ),
            "encryption": self._call_s3(
                lambda: s3_client.get_bucket_encryption(Bucket=bucket_name)
            ),
            "lifecycle": self._call_s3(
                lambda: s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            ),
            "logging": self._call_s3(lambda: s3_client.get_bucket_logging(Bucket=bucket_name)),
            "notification": self._call_s3(
                lambda: s3_client.get_bucket_notification_configuration(Bucket=bucket_name)
            ),
            "replication": self._call_s3(
                lambda: s3_client.get_bucket_replication(Bucket=bucket_name)
            ),
            "public_access_block": self._call_s3(
                lambda: s3_client.get_public_access_block(Bucket=bucket_name)
            ),
            "policy_status": self._call_s3(
                lambda: s3_client.get_bucket_policy_status(Bucket=bucket_name)
            ),
        }

    def _call_s3(
        self,
        call: Callable[[], dict[str, Any]],
        *,
        not_configured_status: str = "not_configured",
    ) -> dict[str, Any]:
        try:
            return {"status": "ok", "data": _strip_response_metadata(call())}
        except ClientError as exc:
            error = exc.response.get("Error", {})
            code = error.get("Code", exc.__class__.__name__)
            status = not_configured_status if code in NOT_CONFIGURED_ERROR_CODES else "error"
            if code in {"AccessDenied", "AllAccessDisabled"}:
                status = "access_denied"
            return {
                "status": status,
                "error_code": code,
                "message": error.get("Message", str(exc)),
            }
        except BotoCoreError as exc:
            return {
                "status": "error",
                "error_type": exc.__class__.__name__,
                "message": str(exc),
            }

    def _normalize_region(self, location_constraint: str | None) -> str:
        if location_constraint in {None, ""}:
            return "us-east-1"
        if location_constraint == "EU":
            return "eu-west-1"
        return location_constraint


def _strip_response_metadata(response: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in response.items() if key != "ResponseMetadata"}
