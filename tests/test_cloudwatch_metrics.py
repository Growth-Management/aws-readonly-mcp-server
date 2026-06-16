from typing import Any

from src.services.cloudwatch_metrics import CloudWatchMetricsService


class FakeCloudWatchClient:
    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []

    def list_metrics(self, **kwargs: Any) -> dict[str, Any]:
        self.requests.append(kwargs)
        return {
            "Metrics": [
                {
                    "Namespace": kwargs.get("Namespace", "AWS/EC2"),
                    "MetricName": "CPUUtilization",
                }
            ]
        }


class FakeFactory:
    def __init__(self) -> None:
        self.client = FakeCloudWatchClient()
        self.calls: list[str] = []

    def create_client(self, service_name: str) -> FakeCloudWatchClient:
        self.calls.append(service_name)
        return self.client


def test_get_cloudwatch_metric_summary_filters_by_namespace() -> None:
    factory = FakeFactory()
    service = CloudWatchMetricsService(factory)  # type: ignore[arg-type]

    result = service.get_cloudwatch_metric_summary(service_name="AWS/EC2")

    assert result["status"] == "ok"
    assert result["service_name"] == "AWS/EC2"
    assert factory.calls == ["cloudwatch"]
    assert factory.client.requests == [{"Namespace": "AWS/EC2"}]


def test_get_idle_resource_signals_counts_metrics() -> None:
    factory = FakeFactory()
    service = CloudWatchMetricsService(factory)  # type: ignore[arg-type]

    result = service.get_idle_resource_signals(service_name="AWS/RDS")

    assert result["status"] == "ok"
    assert result["service_name"] == "AWS/RDS"
    assert result["metrics_seen"] == 1
    assert "time_window" in result


def test_get_service_metric_baseline_requires_namespace_data() -> None:
    factory = FakeFactory()
    service = CloudWatchMetricsService(factory)  # type: ignore[arg-type]

    result = service.get_service_metric_baseline(service_name="AWS/S3")

    assert result["status"] == "ok"
    assert result["service_name"] == "AWS/S3"
    assert result["metrics"][0]["Namespace"] == "AWS/S3"
