from __future__ import annotations

from datetime import date
from typing import Any

from src.aws.client_factory import AWSClientFactory


class CostExplorerService:
    def __init__(self, factory: AWSClientFactory | None = None) -> None:
        self.factory = factory or AWSClientFactory()

    def get_monthly_cost_by_service(self, months: int = 3) -> dict[str, Any]:
        end = date.today().replace(day=1)
        start = _add_months(end, -months)
        try:
            ce = self.factory.create_client("ce", region_name="us-east-1")
            response = ce.get_cost_and_usage(
                TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )
        except Exception as error:
            return {
                "status": "error",
                "months": months,
                "error_type": type(error).__name__,
                "message": str(error),
            }

        return {"status": "ok", "months": months, "results": response.get("ResultsByTime", [])}


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return value.replace(year=year, month=month)
