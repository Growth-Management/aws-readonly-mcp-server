from __future__ import annotations

from typing import Any

from src.aws.client_factory import AWSClientFactory


class S3CostService:
    def __init__(self) -> None:
        self.factory = AWSClientFactory()

    def get_cost_summary(self, months: int = 3) -> dict[str, Any]:
        return {
            "status": "not_implemented",
            "months": months,
            "message": "Implement Cost Explorer integration for S3-related costs",
        }
