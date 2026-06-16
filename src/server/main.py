from __future__ import annotations

import json
import os
import secrets
from datetime import date, datetime
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, Response, status

from src.aws.client_factory import AWSClientFactory
from src.services.cloudwatch_metrics import CloudWatchMetricsService
from src.services.cost_explorer import CostExplorerService
from src.services.ec2_inventory import EC2InventoryService
from src.services.rds_inventory import RDSInventoryService
from src.services.s3_costs import S3CostService
from src.services.s3_inventory import S3InventoryService
from src.services.s3_metrics import S3MetricsService
from src.services.s3_security import S3SecurityService
from src.services.ses_health import SESHealthService
from src.services.trusted_advisor import TrustedAdvisorService

from .config import load_settings

app = FastAPI(title="AWS Readonly MCP Server", version="0.1.0")


class MCPServer:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.aws_factory = AWSClientFactory(self.settings)
        self.cloudwatch_metrics = CloudWatchMetricsService(self.aws_factory)
        self.cost_explorer = CostExplorerService(self.aws_factory)
        self.ec2_inventory = EC2InventoryService(self.aws_factory)
        self.rds_inventory = RDSInventoryService(self.aws_factory)
        self.s3_costs = S3CostService(self.aws_factory)
        self.s3_inventory = S3InventoryService(self.aws_factory)
        self.s3_metrics = S3MetricsService(self.aws_factory)
        self.s3_security = S3SecurityService(self.aws_factory)
        self.ses_health = SESHealthService(self.aws_factory)
        self.trusted_advisor = TrustedAdvisorService(self.aws_factory)

    def healthcheck(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "app_env": self.settings.app_env,
            "aws_region": self.settings.aws_region,
            "enabled_services": self.settings.enabled_services,
        }

    def get_caller_identity(self) -> dict[str, Any]:
        return self.aws_factory.get_caller_identity()

    def list_s3_buckets(self) -> dict[str, Any]:
        return self.s3_inventory.list_buckets()

    def get_s3_bucket_details(self, bucket_name: str) -> dict[str, Any]:
        return self.s3_inventory.get_bucket_details(bucket_name)

    def get_s3_bucket_security(self, bucket_name: str) -> dict[str, Any]:
        return self.s3_security.get_bucket_security(bucket_name)

    def get_s3_cost_summary(self, months: int = 3) -> dict[str, Any]:
        return self.s3_costs.get_cost_summary(months=months)

    def get_s3_request_metrics(self, bucket_name: str) -> dict[str, Any]:
        return self.s3_metrics.get_request_metrics(bucket_name)

    def get_s3_transfer_summary(self, bucket_name: str) -> dict[str, Any]:
        return self.s3_metrics.get_transfer_summary(bucket_name)

    def get_cost_overview(self, months: int = 3) -> dict[str, Any]:
        return self.cost_explorer.get_cost_overview(months=months)

    def get_cost_by_service(self, months: int = 3) -> dict[str, Any]:
        return self.cost_explorer.get_cost_by_service(months=months)

    def get_monthly_cost_by_service(self, months: int = 3) -> dict[str, Any]:
        return self.cost_explorer.get_monthly_cost_by_service(months=months)

    def get_cost_by_account(self, months: int = 3) -> dict[str, Any]:
        return self.cost_explorer.get_cost_by_account(months=months)

    def get_cost_by_tag(self, tag_key: str, months: int = 3) -> dict[str, Any]:
        return self.cost_explorer.get_cost_by_tag(tag_key=tag_key, months=months)

    def get_cost_trend(self, months: int = 3) -> dict[str, Any]:
        return self.cost_explorer.get_cost_trend(months=months)

    def get_cost_forecast(self, months: int = 3) -> dict[str, Any]:
        return self.cost_explorer.get_cost_forecast(months=months)

    def get_cloudwatch_metric_summary(self, service_name: str | None = None) -> dict[str, Any]:
        return self.cloudwatch_metrics.get_cloudwatch_metric_summary(service_name=service_name)

    def get_idle_resource_signals(self, service_name: str | None = None) -> dict[str, Any]:
        return self.cloudwatch_metrics.get_idle_resource_signals(service_name=service_name)

    def get_service_metric_baseline(self, service_name: str) -> dict[str, Any]:
        return self.cloudwatch_metrics.get_service_metric_baseline(service_name=service_name)

    def list_ec2_instances(self) -> dict[str, Any]:
        return self.ec2_inventory.list_instances()

    def list_ec2_volumes(self) -> dict[str, Any]:
        return self.ec2_inventory.list_volumes()

    def list_rds_db_instances(self) -> dict[str, Any]:
        return self.rds_inventory.list_db_instances()

    def get_ses_basic_health(self) -> dict[str, Any]:
        return self.ses_health.get_basic_health()

    def list_trusted_advisor_checks(self, language: str = "ja") -> dict[str, Any]:
        return self.trusted_advisor.list_checks(language=language)

    def list_mcp_tools(self) -> list[dict[str, Any]]:
        return [
            _tool("get_caller_identity", "Return the AWS caller identity used by the server."),
            _tool("list_s3_buckets", "List S3 buckets visible to the configured read-only role."),
            _bucket_tool(
                "get_s3_bucket_details",
                "Return read-only metadata and operational settings for one S3 bucket.",
            ),
            _bucket_tool(
                "get_s3_bucket_security",
                "Return read-only public access, ACL, policy, and encryption details.",
            ),
            _months_tool(
                "get_s3_cost_summary",
                "Return S3-related Cost Explorer usage and cost grouped by usage type.",
            ),
            _months_tool("get_cost_overview", "Return monthly Cost Explorer totals."),
            _months_tool(
                "get_cost_by_service",
                "Return monthly Cost Explorer totals grouped by AWS service.",
            ),
            _months_tool(
                "get_monthly_cost_by_service",
                "Return monthly Cost Explorer totals grouped by AWS service.",
            ),
            _months_tool(
                "get_cost_by_account",
                "Return monthly Cost Explorer totals grouped by linked account.",
            ),
            {
                "name": "get_cost_by_tag",
                "description": (
                    "Return monthly Cost Explorer totals grouped by a cost allocation tag."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tag_key": {"type": "string"},
                        "months": {"type": "integer", "default": 3},
                    },
                    "required": ["tag_key"],
                    "additionalProperties": False,
                },
            },
            _months_tool("get_cost_trend", "Return monthly Cost Explorer trend data."),
            _months_tool("get_cost_forecast", "Return Cost Explorer forecast data."),
            {
                "name": "get_cloudwatch_metric_summary",
                "description": "List CloudWatch metrics, optionally filtered by namespace.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"service_name": {"type": "string"}},
                    "additionalProperties": False,
                },
            },
            {
                "name": "get_idle_resource_signals",
                "description": (
                    "Return coarse CloudWatch signal readiness for idle-resource analysis."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {"service_name": {"type": "string"}},
                    "additionalProperties": False,
                },
            },
            {
                "name": "get_service_metric_baseline",
                "description": "Return CloudWatch metric baseline data for one namespace.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"service_name": {"type": "string"}},
                    "required": ["service_name"],
                    "additionalProperties": False,
                },
            },
            _tool("list_ec2_instances", "List EC2 instances visible in the configured region."),
            _tool("list_ec2_volumes", "List EBS volumes visible in the configured region."),
            _tool(
                "list_rds_db_instances",
                "List RDS DB instances visible in the configured region.",
            ),
            _tool(
                "get_ses_basic_health",
                "Return SES identity count, sandbox/production access, and send quota basics.",
            ),
            {
                "name": "list_trusted_advisor_checks",
                "description": (
                    "List Trusted Advisor checks for cost, security, performance, fault "
                    "tolerance, and service limits."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {"language": {"type": "string", "default": "ja"}},
                    "additionalProperties": False,
                },
            },
            _bucket_tool(
                "get_s3_request_metrics",
                "Report whether S3 request metrics are available for a bucket.",
            ),
            _bucket_tool(
                "get_s3_transfer_summary",
                "Report whether S3 transfer metrics are available for a bucket.",
            ),
        ]

    def handle_mcp_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if request_id is None:
            return None

        if method == "initialize":
            return self._mcp_result(
                request_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "aws-readonly-mcp-server", "version": "0.1.0"},
                },
            )

        if method == "tools/list":
            return self._mcp_result(request_id, {"tools": self.list_mcp_tools()})

        if method == "tools/call":
            return self._handle_tool_call(request_id, params)

        return self._mcp_error(request_id, -32601, f"Method not found: {method}")

    def _handle_tool_call(self, request_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        tool_name = params.get("name")
        arguments = params.get("arguments", {}) or {}
        months = int(arguments.get("months", 3))

        if tool_name == "get_caller_identity":
            payload = self.get_caller_identity()
        elif tool_name == "list_s3_buckets":
            payload = self.list_s3_buckets()
        elif tool_name in {
            "get_s3_bucket_details",
            "get_s3_bucket_security",
            "get_s3_request_metrics",
            "get_s3_transfer_summary",
        }:
            bucket_name = arguments.get("bucket_name") or arguments.get("bucket")
            if not bucket_name:
                return self._tool_error(request_id, "bucket_name is required")
            payload = self._call_bucket_tool(str(tool_name), str(bucket_name))
        elif tool_name == "get_s3_cost_summary":
            payload = self.get_s3_cost_summary(months)
        elif tool_name == "get_cost_overview":
            payload = self.get_cost_overview(months)
        elif tool_name == "get_cost_by_service":
            payload = self.get_cost_by_service(months)
        elif tool_name == "get_monthly_cost_by_service":
            payload = self.get_monthly_cost_by_service(months)
        elif tool_name == "get_cost_by_account":
            payload = self.get_cost_by_account(months)
        elif tool_name == "get_cost_by_tag":
            tag_key = arguments.get("tag_key")
            if not tag_key:
                return self._tool_error(request_id, "tag_key is required")
            payload = self.get_cost_by_tag(str(tag_key), months)
        elif tool_name == "get_cost_trend":
            payload = self.get_cost_trend(months)
        elif tool_name == "get_cost_forecast":
            payload = self.get_cost_forecast(months)
        elif tool_name == "get_cloudwatch_metric_summary":
            service_name = arguments.get("service_name")
            payload = self.get_cloudwatch_metric_summary(
                str(service_name) if service_name else None
            )
        elif tool_name == "get_idle_resource_signals":
            service_name = arguments.get("service_name")
            payload = self.get_idle_resource_signals(str(service_name) if service_name else None)
        elif tool_name == "get_service_metric_baseline":
            service_name = arguments.get("service_name")
            if not service_name:
                return self._tool_error(request_id, "service_name is required")
            payload = self.get_service_metric_baseline(str(service_name))
        elif tool_name == "list_ec2_instances":
            payload = self.list_ec2_instances()
        elif tool_name == "list_ec2_volumes":
            payload = self.list_ec2_volumes()
        elif tool_name == "list_rds_db_instances":
            payload = self.list_rds_db_instances()
        elif tool_name == "get_ses_basic_health":
            payload = self.get_ses_basic_health()
        elif tool_name == "list_trusted_advisor_checks":
            payload = self.list_trusted_advisor_checks(str(arguments.get("language", "ja")))
        else:
            return self._mcp_error(request_id, -32602, f"Unknown tool: {tool_name}")

        return self._mcp_result(request_id, self._tool_content(payload))

    def _call_bucket_tool(self, tool_name: str, bucket_name: str) -> dict[str, Any]:
        if tool_name == "get_s3_bucket_details":
            return self.get_s3_bucket_details(bucket_name)
        if tool_name == "get_s3_bucket_security":
            return self.get_s3_bucket_security(bucket_name)
        if tool_name == "get_s3_request_metrics":
            return self.get_s3_request_metrics(bucket_name)
        return self.get_s3_transfer_summary(bucket_name)

    def _tool_error(self, request_id: Any, message: str) -> dict[str, Any]:
        payload = {"status": "error", "message": message}
        return self._mcp_result(request_id, {**self._tool_content(payload), "isError": True})

    def _tool_content(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        payload,
                        default=_json_default,
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                }
            ],
            "structuredContent": payload,
        }

    def _mcp_result(self, request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def _mcp_error(self, request_id: Any, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def create_server() -> MCPServer:
    return MCPServer()


def verify_bearer_token(authorization: str | None) -> None:
    expected_token = load_settings().mcp_auth_token
    if not expected_token:
        raise HTTPException(status_code=500, detail="server_token_not_configured")

    if not authorization:
        raise HTTPException(status_code=401, detail="missing_authorization_header")

    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(status_code=401, detail="invalid_authorization_scheme")

    token = authorization[len(prefix) :].strip()
    if not secrets.compare_digest(token, expected_token):
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/")
@app.get("/health")
def healthcheck() -> dict[str, Any]:
    return create_server().healthcheck()


@app.get("/tools")
def list_tools(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    verify_bearer_token(authorization)
    return {"tools": create_server().list_mcp_tools()}


@app.get("/tools/{tool_name}")
def call_tool(
    tool_name: str,
    request: Request,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    verify_bearer_token(authorization)
    arguments = _query_arguments(dict(request.query_params))
    response = create_server().handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
    )
    if response is None:
        raise HTTPException(status_code=404, detail="tool_not_found")
    if "error" in response:
        raise HTTPException(status_code=404, detail=response["error"]["message"])
    return response["result"].get("structuredContent", response["result"])


@app.post("/mcp")
async def mcp_endpoint(
    request: Request,
    authorization: str | None = Header(default=None),
) -> dict[str, Any] | Response:
    verify_bearer_token(authorization)

    try:
        body = await request.json()
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            },
        ) from error

    response = create_server().handle_mcp_request(body)
    if response is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return response


def _tool(name: str, description: str) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    }


def _bucket_tool(name: str, description: str) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": {"bucket_name": {"type": "string"}},
            "required": ["bucket_name"],
            "additionalProperties": False,
        },
    }


def _months_tool(name: str, description: str) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": {"months": {"type": "integer", "default": 3}},
            "additionalProperties": False,
        },
    }


def _query_arguments(query: dict[str, str]) -> dict[str, Any]:
    arguments: dict[str, Any] = dict(query)
    if "bucket" in arguments and "bucket_name" not in arguments:
        arguments["bucket_name"] = arguments["bucket"]
    if "months" in arguments:
        try:
            arguments["months"] = int(arguments["months"])
        except ValueError:
            arguments["months"] = 3
    return arguments


def run_http_server() -> None:
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("src.server.main:app", host="0.0.0.0", port=port)


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


if __name__ == "__main__":
    run_http_server()
