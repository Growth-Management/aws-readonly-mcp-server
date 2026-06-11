from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from .config import load_settings


class MCPServer:
    def __init__(self) -> None:
        self.settings = load_settings()

    def healthcheck(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "app_env": self.settings.app_env,
            "aws_region": self.settings.aws_region,
        }

    def list_s3_buckets(self) -> dict[str, Any]:
        """Placeholder tool implementation.

        Replace this with a real AWS client call through a dedicated
        service layer and AWS wrapper.
        """
        return {
            "status": "not_implemented",
            "message": "list_s3_buckets is not implemented yet",
        }


def create_server() -> MCPServer:
    return MCPServer()


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "AWSReadonlyMCP/0.1"

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path in {"/", "/health"}:
            self._send_json(HTTPStatus.OK, create_server().healthcheck())
            return

        if path == "/tools/list_s3_buckets":
            if not self._is_authorized():
                self._send_json(HTTPStatus.UNAUTHORIZED, {"status": "unauthorized"})
                return

            self._send_json(HTTPStatus.NOT_IMPLEMENTED, create_server().list_s3_buckets())
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"status": "not_found", "path": path})

    def log_message(self, format: str, *args: Any) -> None:
        if os.getenv("LOG_LEVEL", "INFO").upper() != "ERROR":
            super().log_message(format, *args)

    def _is_authorized(self) -> bool:
        expected_token = create_server().settings.mcp_auth_token
        if not expected_token:
            return False

        auth_header = self.headers.get("Authorization", "")
        return auth_header == f"Bearer {expected_token}"

    def _send_json(self, status_code: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_http_server() -> None:
    port = int(os.getenv("PORT", "8080"))
    httpd = ThreadingHTTPServer(("0.0.0.0", port), RequestHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    run_http_server()
