from __future__ import annotations

from datetime import date
from typing import Any

from src.aws.client_factory import AWSClientFactory


class CostExplorerService:
    def __init__(self, factory: AWSClientFactory | None = None) -> None:
        self.factory = factory or AWSClientFactory()

    def get_cost_overview(self, months: int = 3) -> dict[str, Any]:
        return self._get_cost_and_usage(months=months)

    def get_cost_by_service(self, months: int = 3) -> dict[str, Any]:
        return self._get_cost_and_usage(
            months=months,
            group_by=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            group_label="SERVICE",
        )

    def get_monthly_cost_by_service(self, months: int = 3) -> dict[str, Any]:
        return self.get_cost_by_service(months=months)

    def get_cost_by_account(self, months: int = 3) -> dict[str, Any]:
        return self._get_cost_and_usage(
            months=months,
            group_by=[{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}],
            group_label="LINKED_ACCOUNT",
        )

    def get_cost_by_tag(self, tag_key: str, months: int = 3) -> dict[str, Any]:
        return self._get_cost_and_usage(
            months=months,
            group_by=[{"Type": "TAG", "Key": tag_key}],
            group_label=f"TAG:{tag_key}",
        )

    def get_cost_trend(self, months: int = 3) -> dict[str, Any]:
        return self.get_cost_overview(months=months)

    def get_cost_forecast(self, months: int = 3) -> dict[str, Any]:
        start = date.today()
        end = _add_months(start, max(months, 1))
        try:
            ce = self.factory.create_client("ce", region_name="us-east-1")
            response = ce.get_cost_forecast(
                TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
                Metric="UNBLENDED_COST",
                Granularity="MONTHLY",
            )
        except Exception as error:
            return _error_payload(error, months=months)

        return {
            "status": "ok",
            "months": months,
            "time_period": {"start": start.isoformat(), "end": end.isoformat()},
            "forecast": response,
        }

    def _get_cost_and_usage(
        self,
        months: int,
        group_by: list[dict[str, str]] | None = None,
        group_label: str | None = None,
    ) -> dict[str, Any]:
        start, end = _monthly_date_range(months)
        request: dict[str, Any] = {
            "TimePeriod": {"Start": start.isoformat(), "End": end.isoformat()},
            "Granularity": "MONTHLY",
            "Metrics": ["UnblendedCost"],
        }
        if group_by:
            request["GroupBy"] = group_by

        try:
            ce = self.factory.create_client("ce", region_name="us-east-1")
            response = ce.get_cost_and_usage(**request)
        except Exception as error:
            return _error_payload(error, months=months, group_by=group_label)

        payload: dict[str, Any] = {
            "status": "ok",
            "months": months,
            "time_period": {"start": start.isoformat(), "end": end.isoformat()},
            "results": response.get("ResultsByTime", []),
        }
        if group_label:
            payload["group_by"] = group_label
        return payload


def _monthly_date_range(months: int) -> tuple[date, date]:
    end = date.today().replace(day=1)
    start = _add_months(end, -max(months, 1))
    return start, end


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return value.replace(year=year, month=month)


def _error_payload(
    error: Exception,
    months: int,
    group_by: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": "error",
        "months": months,
        "error_type": type(error).__name__,
        "message": str(error),
    }
    if group_by:
        payload["group_by"] = group_by
    return payload
