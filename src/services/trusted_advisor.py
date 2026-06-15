from __future__ import annotations

from typing import Any

from src.aws.client_factory import AWSClientFactory

TRUSTED_ADVISOR_CATEGORIES = {
    "cost_optimizing",
    "security",
    "performance",
    "fault_tolerance",
    "service_limits",
}


class TrustedAdvisorService:
    def __init__(self, factory: AWSClientFactory | None = None) -> None:
        self.factory = factory or AWSClientFactory()

    def list_checks(self, language: str = "ja") -> dict[str, Any]:
        try:
            support = self.factory.create_client("support", region_name="us-east-1")
            checks = support.describe_trusted_advisor_checks(language=language).get("checks", [])
        except Exception as error:
            return {
                "status": "error",
                "error_type": type(error).__name__,
                "message": str(error),
                "note": "Trusted Advisor API requires a support plan that exposes "
                "the AWS Support API.",
            }

        filtered = [
            {
                "id": check.get("id"),
                "name": check.get("name"),
                "category": check.get("category"),
                "description": check.get("description"),
            }
            for check in checks
            if check.get("category") in TRUSTED_ADVISOR_CATEGORIES
        ]
        return {"status": "ok", "check_count": len(filtered), "checks": filtered}
