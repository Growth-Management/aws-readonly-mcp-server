from __future__ import annotations

from typing import Any

from src.aws.client_factory import AWSClientFactory


class SESHealthService:
    def __init__(self, factory: AWSClientFactory | None = None) -> None:
        self.factory = factory or AWSClientFactory()

    def get_basic_health(self) -> dict[str, Any]:
        try:
            sesv2 = self.factory.create_client("sesv2")
            account = sesv2.get_account()
            identities = sesv2.list_email_identities().get("EmailIdentities", [])
        except Exception as error:
            return {"status": "error", "error_type": type(error).__name__, "message": str(error)}

        return {
            "status": "ok",
            "production_access_enabled": account.get("ProductionAccessEnabled"),
            "send_quota": account.get("SendQuota", {}),
            "identity_count": len(identities),
            "identities": [
                {
                    "identity_name": identity.get("IdentityName"),
                    "identity_type": identity.get("IdentityType"),
                    "sending_enabled": identity.get("SendingEnabled"),
                    "verification_status": identity.get("VerificationStatus"),
                }
                for identity in identities
            ],
        }
