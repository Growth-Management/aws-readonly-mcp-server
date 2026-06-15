from __future__ import annotations

from typing import Any

from src.aws.client_factory import AWSClientFactory


def _safe_call(func: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        return {"status": "ok", "data": func(**kwargs)}
    except Exception as error:
        return {
            "status": "access_denied_or_unavailable",
            "error_type": type(error).__name__,
            "message": str(error),
        }


class S3SecurityService:
    def __init__(self, factory: AWSClientFactory | None = None) -> None:
        self.factory = factory or AWSClientFactory()

    def get_bucket_security(self, bucket_name: str) -> dict[str, Any]:
        s3 = self.factory.create_client("s3")
        return {
            "status": "ok",
            "bucket_name": bucket_name,
            "public_access_block": _safe_call(s3.get_public_access_block, Bucket=bucket_name),
            "policy_status": _safe_call(s3.get_bucket_policy_status, Bucket=bucket_name),
            "acl": _safe_call(s3.get_bucket_acl, Bucket=bucket_name),
            "encryption": _safe_call(s3.get_bucket_encryption, Bucket=bucket_name),
        }
