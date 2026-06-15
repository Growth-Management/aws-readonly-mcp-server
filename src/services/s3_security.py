from __future__ import annotations

import json
from typing import Any, Callable

from botocore.exceptions import BotoCoreError, ClientError
from src.aws.client_factory import AWSClientFactory
from src.services.s3_inventory import NOT_CONFIGURED_ERROR_CODES


PUBLIC_ACL_URIS = {
    "http://acs.amazonaws.com/groups/global/AllUsers",
    "http://acs.amazonaws.com/groups/global/AuthenticatedUsers",
}


class S3SecurityService:
    def __init__(self, factory: AWSClientFactory | None = None) -> None:
        self.factory = factory or AWSClientFactory()

    def get_bucket_security(self, bucket_name: str) -> dict[str, Any]:
        bucket_name = bucket_name.strip()
        if not bucket_name:
            return {"status": "error", "message": "bucket_name is required"}

        s3_client = self.factory.create_client("s3")
        public_access_block = self._call_s3(
            lambda: s3_client.get_public_access_block(Bucket=bucket_name)
        )
        policy_status = self._call_s3(
            lambda: s3_client.get_bucket_policy_status(Bucket=bucket_name)
        )
        acl = self._call_s3(lambda: s3_client.get_bucket_acl(Bucket=bucket_name))
        encryption = self._call_s3(lambda: s3_client.get_bucket_encryption(Bucket=bucket_name))
        policy = self._call_s3(lambda: s3_client.get_bucket_policy(Bucket=bucket_name))

        findings = self._build_findings(public_access_block, policy_status, acl, encryption)

        return {
            "status": "ok",
            "bucket_name": bucket_name,
            "public_access_block": public_access_block,
            "policy_status": policy_status,
            "acl": self._summarize_acl(acl),
            "encryption": encryption,
            "policy": self._parse_policy(policy),
            "findings": findings,
        }

    def _call_s3(self, call: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        try:
            return {"status": "ok", "data": _strip_response_metadata(call())}
        except ClientError as exc:
            error = exc.response.get("Error", {})
            code = error.get("Code", exc.__class__.__name__)
            status = "not_configured" if code in NOT_CONFIGURED_ERROR_CODES else "error"
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

    def _summarize_acl(self, acl: dict[str, Any]) -> dict[str, Any]:
        if acl.get("status") != "ok":
            return acl

        grants = acl.get("data", {}).get("Grants", [])
        summarized_grants = []
        public_grants = []
        for grant in grants:
            grantee = grant.get("Grantee", {})
            permission = grant.get("Permission")
            uri = grantee.get("URI")
            summary = {
                "permission": permission,
                "type": grantee.get("Type"),
                "uri": uri,
                "display_name": grantee.get("DisplayName"),
                "id": grantee.get("ID"),
            }
            summarized_grants.append(summary)
            if uri in PUBLIC_ACL_URIS:
                public_grants.append(summary)

        return {
            "status": "ok",
            "owner": acl.get("data", {}).get("Owner"),
            "grant_count": len(summarized_grants),
            "grants": summarized_grants,
            "public_grants": public_grants,
            "has_public_grants": bool(public_grants),
        }

    def _parse_policy(self, policy: dict[str, Any]) -> dict[str, Any]:
        if policy.get("status") != "ok":
            return policy

        raw_policy = policy.get("data", {}).get("Policy")
        try:
            parsed_policy = json.loads(raw_policy) if raw_policy else None
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Bucket policy could not be parsed as JSON",
                "raw_policy": raw_policy,
            }

        return {
            "status": "ok",
            "policy": parsed_policy,
        }

    def _build_findings(
        self,
        public_access_block: dict[str, Any],
        policy_status: dict[str, Any],
        acl: dict[str, Any],
        encryption: dict[str, Any],
    ) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []

        if public_access_block.get("status") == "not_configured":
            findings.append(
                {
                    "severity": "medium",
                    "code": "public_access_block_not_configured",
                    "message": "Bucket-level Public Access Block is not configured.",
                }
            )
        elif public_access_block.get("status") == "ok":
            config = public_access_block.get("data", {}).get("PublicAccessBlockConfiguration", {})
            disabled = [key for key, value in config.items() if value is not True]
            if disabled:
                findings.append(
                    {
                        "severity": "medium",
                        "code": "public_access_block_not_fully_enabled",
                        "message": "Some Public Access Block settings are not enabled: "
                        + ", ".join(disabled),
                    }
                )

        if policy_status.get("status") == "ok" and policy_status.get("data", {}).get(
            "PolicyStatus", {}
        ).get("IsPublic"):
            findings.append(
                {
                    "severity": "high",
                    "code": "bucket_policy_public",
                    "message": "Bucket policy status indicates public access.",
                }
            )

        acl_summary = self._summarize_acl(acl)
        if acl_summary.get("has_public_grants"):
            findings.append(
                {
                    "severity": "high",
                    "code": "bucket_acl_public_grants",
                    "message": "Bucket ACL grants access to a public S3 group.",
                }
            )

        if encryption.get("status") == "not_configured":
            findings.append(
                {
                    "severity": "low",
                    "code": "bucket_encryption_not_configured",
                    "message": "Default bucket encryption is not configured.",
                }
            )

        return findings


def _strip_response_metadata(response: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in response.items() if key != "ResponseMetadata"}
