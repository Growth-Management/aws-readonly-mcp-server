from __future__ import annotations

import json
import os
from datetime import date, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from src.aws.client_factory import AWSClientFactory
from src.services.s3_inventory import S3InventoryService
from src.services.s3_security import S3SecurityService

from .config import load_settings


class MCPServer:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.aws_factory = AWSClientFactory(self.settings)

    def healthcheck(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "app_env": self.settings.app_env,
            "aws_region": self.settings.aws_region,
        }

    def get_caller_identity(self) -> dict[str, Any]:
        return self.aws_factory.get_caller_identity()

    def list_s3_buckets(self) -> dict[str, Any]:
        return S3InventoryService(self.aws_factory).list_buckets()

    def get_s3_bucket_details(self, bucket_name: str) -> dict[str, Any]:
        return S3InventoryService(self.aws_factory).get_bucket_details(bucket_name)

    def get_s3_bucket_security(self, bucket_name: str) -> dict[str, Any]:
        return S3SecurityService(self.aws_factory).get_bucket_security(bucket_name)

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

        if path == "/tools/get_caller_identity":
            if not self._is_authorized():
                self._send_json(HTTPStatus.UNAUTHORIZED, {"status": "unauthorized"})
                return

            self._send_json(HTTPStatus.OK, create_server().get_caller_identity())
            return

        if path == "/tools/list_s3_buckets":
            if not self._is_authorized():
                self._send_json(HTTPStatus.UNAUTHORIZED, {"status": "unauthorized"})
                return

            self._send_json(HTTPStatus.OK, create_server().list_s3_buckets())
            return

        if path == "/tools/get_s3_bucket_details":
            if not self._is_authorized():
                self._send_json(HTTPStatus.UNAUTHORIZED, {"status": "unauthorized"})
                return

            bucket_name = self._first_query_value(query, "bucket") or self._first_query_value(
                query, "bucket_name"
            )
            if not bucket_name:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"status": "error", "message": "bucket is required"},
                )
                return

            self._send_json(HTTPStatus.OK, create_server().get_s3_bucket_details(bucket_name))
            return

        if path == "/tools/get_s3_bucket_security":
            if not self._is_authorized():
                self._send_json(HTTPStatus.UNAUTHORIZED, {"status": "unauthorized"})
                return

            bucket_name = self._first_query_value(query, "bucket") or self._first_query_value(
                query, "bucket_name"
            )
            if not bucket_name:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"status": "error", "message": "bucket is required"},
                )
                return

            self._send_json(HTTPStatus.OK, create_server().get_s3_bucket_security(bucket_name))
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

        response = create_server().handle_mcp_request(request)
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
