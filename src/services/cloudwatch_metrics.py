from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from src.aws.client_factory import AWSClientFactory


class CloudWatchMetricsService:
    def __init__(self, factory: AWSClientFactory | None = None) -> None:
        self.factory = factory or AWSClientFactory()

    def get_cloudwatch_metric_summary(self, service_name: str | None = None) -> dict[str, Any]:
        request: dict[str, Any] = {}
        if service_name:
            request["Namespace"] = service_name

        try:
            cloudwatch = self.factory.create_client("cloudwatch")
            response = cloudwatch.list_metrics(**request)
        except Exception as error:
            return _error_payload(error, service_name=service_name)

        return {
            "status": "ok",
            "service_name": service_name,
            "metrics": response.get("Metrics", []),
            "next_token": response.get("NextToken"),
        }

    def get_idle_resource_signals(self, service_name: str | None = None) -> dict[str, Any]:
        start, end = _time_window()
        summary = self.get_cloudwatch_metric_summary(service_name=service_name)
        if summary.get("status") != "ok":
            return summary

        return {
            "status": "ok",
            "service_name": service_name,
            "time_window": {"start": start.isoformat(), "end": end.isoformat()},
            "metrics_seen": len(summary.get("metrics", [])),
            "message": "Idle resource heuristics require service-specific metric evaluation.",
        }

    def get_service_metric_baseline(self, service_name: str) -> dict[str, Any]:
        start, end = _time_window()
        summary = self.get_cloudwatch_metric_summary(service_name=service_name)
        if summary.get("status") != "ok":
            return summary

        return {
            "status": "ok",
            "service_name": service_name,
            "time_window": {"start": start.isoformat(), "end": end.isoformat()},
            "metrics": summary.get("metrics", []),
        }


def _time_window(hours: int = 24) -> tuple[datetime, datetime]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    return start, end


def _error_payload(error: Exception, service_name: str | None = None) -> dict[str, Any]:
    return {
        "status": "error",
        "service_name": service_name,
        "error_type": type(error).__name__,
        "message": str(error),
    }
