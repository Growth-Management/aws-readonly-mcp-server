from __future__ import annotations

import json
import os
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

        if not path.startswith("/tools/"):
            self._send_json(HTTPStatus.NOT_FOUND, {"status": "not_found", "path": path})
            return

        if not self._is_authorized():
            self._send_json(HTTPStatus.UNAUTHORIZED, {"status": "unauthorized"})
            return

        server = create_server()
        routes = {
            "/tools/get_caller_identity": lambda: server.get_caller_identity(),
            "/tools/list_s3_buckets": lambda: server.list_s3_buckets(),
            "/tools/get_s3_cost_summary": lambda: server.get_s3_cost_summary(
                months=_int_query(query, "months", 3)
            ),
            "/tools/get_monthly_cost_by_service": lambda: server.get_monthly_cost_by_service(
                months=_int_query(query, "months", 3)
            ),
            "/tools/list_ec2_instances": lambda: server.list_ec2_instances(),
            "/tools/list_ec2_volumes": lambda: server.list_ec2_volumes(),
            "/tools/list_rds_db_instances": lambda: server.list_rds_db_instances(),
            "/tools/get_ses_basic_health": lambda: server.get_ses_basic_health(),
            "/tools/list_trusted_advisor_checks": lambda: server.list_trusted_advisor_checks(
                language=_str_query(query, "language", "ja")
            ),
        }

        if path in routes:
            self._send_json(HTTPStatus.OK, routes[path]())
            return

        bucket_routes = {
            "/tools/get_s3_bucket_details": server.get_s3_bucket_details,
            "/tools/get_s3_bucket_security": server.get_s3_bucket_security,
            "/tools/get_s3_request_metrics": server.get_s3_request_metrics,
            "/tools/get_s3_transfer_summary": server.get_s3_transfer_summary,
        }
        if path in bucket_routes:
            bucket_name = _str_query(query, "bucket_name", "")
            if not bucket_name:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"status": "bad_request", "message": "bucket_name query parameter is required"},
                )
                return
            self._send_json(HTTPStatus.OK, bucket_routes[path](bucket_name))
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
        body = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
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


if __name__ == "__main__":
    run_http_server()
