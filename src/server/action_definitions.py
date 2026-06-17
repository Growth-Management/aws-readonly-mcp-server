from __future__ import annotations

from typing import Any


def _schema(
    properties: dict[str, Any] | None = None,
    required: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties or {},
        "required": required or [],
        "additionalProperties": False,
    }


ACTION_DEFINITIONS: dict[str, dict[str, Any]] = {
    "get_caller_identity": {
        "name": "get_caller_identity",
        "description": "Return the AWS caller identity used by the MCP server.",
        "input_schema": _schema(),
    },
    "list_s3_buckets": {
        "name": "list_s3_buckets",
        "description": "List S3 buckets visible to the configured read-only AWS credentials.",
        "input_schema": _schema(),
    },
    "get_s3_bucket_details": {
        "name": "get_s3_bucket_details",
        "description": "Get read-only metadata and configuration details for one S3 bucket.",
        "input_schema": _schema(
            {"bucket_name": {"type": "string", "description": "The S3 bucket name."}},
            ["bucket_name"],
        ),
    },
    "get_s3_bucket_security": {
        "name": "get_s3_bucket_security",
        "description": (
            "Get public access, ACL, bucket policy, and encryption information for "
            "one S3 bucket."
        ),
        "input_schema": _schema(
            {"bucket_name": {"type": "string", "description": "The S3 bucket name."}},
            ["bucket_name"],
        ),
    },
    "get_s3_cost_summary": {
        "name": "get_s3_cost_summary",
        "description": "Get an S3-oriented cost summary for the requested lookback window.",
        "input_schema": _schema(
            {"months": {"type": "integer", "minimum": 1, "default": 3}}
        ),
    },
    "get_s3_request_metrics": {
        "name": "get_s3_request_metrics",
        "description": (
            "Get S3 request metric availability and recent metric datapoints for "
            "one bucket."
        ),
        "input_schema": _schema(
            {"bucket_name": {"type": "string", "description": "The S3 bucket name."}},
            ["bucket_name"],
        ),
    },
    "get_s3_transfer_summary": {
        "name": "get_s3_transfer_summary",
        "description": (
            "Get S3 transfer metric availability and recent metric datapoints for "
            "one bucket."
        ),
        "input_schema": _schema(
            {"bucket_name": {"type": "string", "description": "The S3 bucket name."}},
            ["bucket_name"],
        ),
    },
    "get_monthly_cost_by_service": {
        "name": "get_monthly_cost_by_service",
        "description": "Get monthly AWS costs grouped by service using Cost Explorer.",
        "input_schema": _schema(
            {"months": {"type": "integer", "minimum": 1, "default": 3}}
        ),
    },
    "list_ec2_instances": {
        "name": "list_ec2_instances",
        "description": "List EC2 instances visible in the configured region.",
        "input_schema": _schema(),
    },
    "list_ec2_volumes": {
        "name": "list_ec2_volumes",
        "description": "List EBS volumes visible in the configured region.",
        "input_schema": _schema(),
    },
    "list_rds_db_instances": {
        "name": "list_rds_db_instances",
        "description": "List RDS DB instances visible in the configured region.",
        "input_schema": _schema(),
    },
    "get_ses_basic_health": {
        "name": "get_ses_basic_health",
        "description": (
            "Return SES identity count, sandbox/production access, and send quota "
            "basics."
        ),
        "input_schema": _schema(),
    },
    "list_trusted_advisor_checks": {
        "name": "list_trusted_advisor_checks",
        "description": (
            "List Trusted Advisor checks for cost, security, performance, fault "
            "tolerance, and service limits."
        ),
        "input_schema": _schema(
            {
                "language": {
                    "type": "string",
                    "default": "ja",
                    "description": "Trusted Advisor response language.",
                }
            }
        ),
    },
}


def list_action_definitions() -> list[dict[str, Any]]:
    return list(ACTION_DEFINITIONS.values())


def get_action_definition(action_name: str) -> dict[str, Any] | None:
    return ACTION_DEFINITIONS.get(action_name)
