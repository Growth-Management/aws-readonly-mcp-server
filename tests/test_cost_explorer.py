from typing import Any

from src.services.cost_explorer import CostExplorerService


class FakeCostExplorerClient:
    def __init__(self) -> None:
        self.cost_and_usage_requests: list[dict[str, Any]] = []
        self.forecast_requests: list[dict[str, Any]] = []

    def get_cost_and_usage(self, **kwargs: Any) -> dict[str, Any]:
        self.cost_and_usage_requests.append(kwargs)
        return {"ResultsByTime": [{"TimePeriod": kwargs["TimePeriod"]}]}

    def get_cost_forecast(self, **kwargs: Any) -> dict[str, Any]:
        self.forecast_requests.append(kwargs)
        return {"Total": {"Amount": "10", "Unit": "USD"}}


class FakeFactory:
    def __init__(self) -> None:
        self.client = FakeCostExplorerClient()
        self.calls: list[tuple[str, str | None]] = []

    def create_client(self, service_name: str, region_name: str | None = None) -> FakeCostExplorerClient:
        self.calls.append((service_name, region_name))
        return self.client


def test_get_cost_by_service_groups_by_service() -> None:
    factory = FakeFactory()
    service = CostExplorerService(factory)  # type: ignore[arg-type]

    result = service.get_cost_by_service(months=6)

    assert result["status"] == "ok"
    assert result["group_by"] == "SERVICE"
    assert factory.calls == [("ce", "us-east-1")]
    request = factory.client.cost_and_usage_requests[0]
    assert request["Granularity"] == "MONTHLY"
    assert request["Metrics"] == ["UnblendedCost"]
    assert request["GroupBy"] == [{"Type": "DIMENSION", "Key": "SERVICE"}]


def test_get_cost_by_tag_groups_by_tag_key() -> None:
    factory = FakeFactory()
    service = CostExplorerService(factory)  # type: ignore[arg-type]

    result = service.get_cost_by_tag(tag_key="Department", months=3)

    assert result["status"] == "ok"
    assert result["group_by"] == "TAG:Department"
    request = factory.client.cost_and_usage_requests[0]
    assert request["GroupBy"] == [{"Type": "TAG", "Key": "Department"}]


def test_get_cost_forecast_uses_forecast_api() -> None:
    factory = FakeFactory()
    service = CostExplorerService(factory)  # type: ignore[arg-type]

    result = service.get_cost_forecast(months=2)

    assert result["status"] == "ok"
    assert factory.calls == [("ce", "us-east-1")]
    request = factory.client.forecast_requests[0]
    assert request["Metric"] == "UNBLENDED_COST"
    assert request["Granularity"] == "MONTHLY"
