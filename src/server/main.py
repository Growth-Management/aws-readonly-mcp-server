from __future__ import annotations

import json
import os
from datetime import date, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from src.aws.client_factory import AWSClientFactory
from src.services.cost_explorer import CostExplorerService
from src.services.ec2_inventory import EC2InventoryService
from src.services.rds_inventory import RDSInventoryService
from src.services.s3_costs import S3CostService
from src.services.s3_inventory import S3InventoryService
from src.services.s3_metrics import S3MetricsService
from src.services.s3_security import S3SecurityService
from src.services.ses_health import SESHealthService
from src.services.trusted_advisor import TrustedAdvisorService

from .action_definitions import get_action_definition, list_action_definitions
from .config import load_settings


class MCPServer:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.aws_factory = AWSClientFactory(self.settings)
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

    def get_monthly_cost_by_service(self, months: int = 3) -> dict[str, Any]:
        return self.cost_explorer.get_monthly_cost_by_service(months=months)

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

    def list_actions(self) -> list[dict[str, Any]]:
        return list_action_definitions()

    def list_mcp_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "get_caller_identity",
                "description": "Return the AWS caller identity used by the server.",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "list_s3_buckets",
                "description": "List S3 buckets visible to the configured read-only role.",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "get_s3_bucket_details",
                "description": (
                    "Return read-only metadata and operational settings for one S3 bucket."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {"bucket_name": {"type": "string"}},
                    "required": ["bucket_name"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "get_s3_bucket_security",
                "description": (
                    "Return read-only public access, ACL, policy, and encryption details."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {"bucket_name": {"type": "string"}},
                    "required": ["bucket_name"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "get_s3_cost_summary",
                "description": (
                    "Return S3-related Cost Explorer usage and cost grouped by usage type."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {"months": {"type": "integer", "default": 3}},
                    "additionalProperties": False,
                },
            },
            {
                "name": "get_monthly_cost_by_service",
                "description": "Return monthly Cost Explorer totals grouped by AWS service.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"months": {"type": "integer", "default": 3}},
                    "additionalProperties": False,
                },
            },
            {
                "name": "list_ec2_instances",
                "description": "List EC2 instances visible in the configured region.",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "list_ec2_volumes",
                "description": "List EBS volumes visible in the configured region.",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "list_rds_db_instances",
                "description": "List RDS DB instances visible in the configured region.",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "get_ses_basic_health",
                "description": (
                    "Return SES identity count, sandbox/production access, and send quota basics."
                ),
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "list_trusted_advisor_checks",
                "description": (
                    "List Trusted Advisor checks for cost, security, performance, "
                    "fault tolerance, and service limits."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {"language": {"type": "string", "default": "ja"}},
                    "additionalProperties": False,
                },
            },
            {
                "name": "get_s3_request_metrics",
                "description": "Report whether S3 request metrics are available for a bucket.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"bucket_name": {"type": "string"}},
                    "required": ["bucket_name"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "get_s3_transfer_summary",
                "description": "Report whether S3 transfer metrics are available for a bucket.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"bucket_name": {"type": "string"}},
                    "required": ["bucket_name"],
                    "additionalProperties": False,
                },
            },
        ]

    def handle_action_request(self, request: dict[str, Any]) -> dict[str, Any]:
        action = request.get("action")
        params = request.get("params", {}) or {}

        if action == "list_actions":
            return {"status": "ok", "actions": self.list_actions()}

        if action == "get_action_definition":
            action_name = params.get("action_name")
            if not action_name:
                return {"status": "error", "message": "action_name is required"}
            definition = get_action_definition(str(action_name))
            if definition is None:
                return {"status": "error", "message": f"unknown_action:{action_name}"}
            return {"status": "ok", "action_definition": definition}

        return {"status": "error", "message": f"unknown_action:{action}"}

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

        if tool_name == "get_caller_identity":
            payload = self.get_caller_identity()
        elif tool_name == "list_s3_buckets":
            payload = self.list_s3_buckets()
        elif tool_name == "get_s3_bucket_details":
            bucket_name = arguments.get("bucket_name") or arguments.get("bucket")
            if not bucket_name:
                return self._tool_error(request_id, "bucket_name is required")
            payload = self.get_s3_bucket_details(str(bucket_name))
        elif tool_name == "get_s3_bucket_security":
            bucket_name = arguments.get("bucket_name") or arguments.get("bucket")
            if not bucket_name:
                return self._tool_error(request_id, "bucket_name is required")
            payload = self.get_s3_bucket_security(str(bucket_name))
        elif tool_name == "get_s3_cost_summary":
            payload = self.get_s3_cost_summary(int(arguments.get("months", 3)))
        elif tool_name == "get_monthly_cost_by_service":
            payload = self.get_monthly_cost_by_service(int(arguments.get("months", 3)))
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
        elif tool_name == "get_s3_request_metrics":
            bucket_name = arguments.get("bucket_name") or arguments.get("bucket")
            if not bucket_name:
                return self._tool_error(request_id, "bucket_name is required")
            payload = self.get_s3_request_metrics(str(bucket_name))
        elif tool_name == "get_s3_transfer_summary":
            bucket_name = arguments.get("bucket_name") or arguments.get("bucket")
            if not bucket_name:
                return self._tool_error(request_id, "bucket_name is required")
            payload = self.get_s3_transfer_summary(str(bucket_name))
        else:
            return self._mcp_error(request_id, -32602, f"Unknown tool: {tool_name}")

        return self._mcp_result(request_id, self._tool_content(payload))

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


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "AWSReadonlyMCP/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path in {"/", "/health"}:
            self._send_json(HTTPStatus.OK, create_server().healthcheck())
            return

        if not self._is_authorized():
            self._send_json(HTTPStatus.UNAUTHORIZED, {"status": "unauthorized"})
            return

        server = create_server()

        if path == "/mcp/actions":
            self._send_json(HTTPStatus.OK, {"status": "ok", "actions": server.list_actions()})
            return

        simple_routes = {
            "/tools/get_caller_identity": server.get_caller_identity,
            "/tools/list_s3_buckets": server.list_s3_buckets,
            "/tools/list_ec2_instances": server.list_ec2_instances,
            "/tools/list_ec2_volumes": server.list_ec2_volumes,
            "/tools/list_rds_db_instances": server.list_rds_db_instances,
            "/tools/get_ses_basic_health": server.get_ses_basic_health,
        }
        if path in simple_routes:
            self._send_json(HTTPStatus.OK, simple_routes[path]())
            return

        if path == "/tools/get_s3_cost_summary":
            self._send_json(
                HTTPStatus.OK,
                server.get_s3_cost_summary(_int_query(query, "months", 3)),
            )
            return

        if path == "/tools/get_monthly_cost_by_service":
            self._send_json(
                HTTPStatus.OK,
                server.get_monthly_cost_by_service(_int_query(query, "months", 3)),
            )
            return

        if path == "/tools/list_trusted_advisor_checks":
            self._send_json(
                HTTPStatus.OK,
                server.list_trusted_advisor_checks(_str_query(query, "language", "ja")),
            )
            return

        bucket_routes = {
            "/tools/get_s3_bucket_details": server.get_s3_bucket_details,
            "/tools/get_s3_bucket_security": server.get_s3_bucket_security,
            "/tools/get_s3_request_metrics": server.get_s3_request_metrics,
            "/tools/get_s3_transfer_summary": server.get_s3_transfer_summary,
        }
        if path in bucket_routes:
            bucket_name = self._first_query_value(query, "bucket") or self._first_query_value(
                query, "bucket_name"
            )
            if not bucket_name:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"status": "error", "message": "bucket is required"},
                )
                return
            self._send_json(HTTPStatus.OK, bucket_routes[path](bucket_name))
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"status": "not_found", "path": path})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/mcp":
            self._send_json(HTTPStatus.NOT_FOUND, {"status": "not_found", "path": path})
            return

        if not self._is_authorized():
            self._send_json(HTTPStatus.UNAUTHORIZED, {"status": "unauthorized"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length).decode("utf-8")
            request = json.loads(body) if body else {}
        except (json.JSONDecodeError, ValueError):
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
            )
            return

        server = create_server()
        if "action" in request:
            self._send_json(HTTPStatus.OK, server.handle_action_request(request))
            return

        response = server.handle_mcp_request(request)
        if response is None:
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return

        self._send_json(HTTPStatus.OK, response)

    def log_message(self, format: str, *args: Any) -> None:
        if os.getenv("LOG_LEVEL", "INFO").upper() != "ERROR":
            super().log_message(format, *args)

    def _is_authorized(self) -> bool:
        expected_token = create_server().settings.mcp_auth_token
        if not expected_token:
            return False

        auth_header = self.headers.get("Authorization", "")
        return auth_header == f"Bearer {expected_token}"

    def _first_query_value(self, query: dict[str, list[str]], name: str) -> str | None:
        values = query.get(name, [])
        return values[0] if values else None

    def _send_json(self, status_code: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, default=_json_default, sort_keys=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _str_query(query: dict[str, list[str]], key: str, default: str) -> str:
    values = query.get(key)
    return values[0] if values else default


def _int_query(query: dict[str, list[str]], key: str, default: int) -> int:
    values = query.get(key)
    if not values:
        return default
    try:
        return int(values[0])
    except ValueError:
        return default


def run_http_server() -> None:
    port = int(os.getenv("PORT", "8080"))
    httpd = ThreadingHTTPServer(("0.0.0.0", port), RequestHandler)
    httpd.serve_forever()


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


if __name__ == "__main__":
    run_http_server()
