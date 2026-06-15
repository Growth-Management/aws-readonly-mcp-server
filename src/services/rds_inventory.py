from __future__ import annotations

from typing import Any

from src.aws.client_factory import AWSClientFactory


class RDSInventoryService:
    def __init__(self, factory: AWSClientFactory | None = None) -> None:
        self.factory = factory or AWSClientFactory()

    def list_db_instances(self) -> dict[str, Any]:
        try:
            rds = self.factory.create_client("rds")
            paginator = rds.get_paginator("describe_db_instances")
            instances: list[dict[str, Any]] = []
            for page in paginator.paginate():
                for instance in page.get("DBInstances", []):
                    instances.append(
                        {
                            "db_instance_identifier": instance.get("DBInstanceIdentifier"),
                            "engine": instance.get("Engine"),
                            "db_instance_class": instance.get("DBInstanceClass"),
                            "status": instance.get("DBInstanceStatus"),
                            "allocated_storage_gib": instance.get("AllocatedStorage"),
                            "multi_az": instance.get("MultiAZ"),
                            "storage_encrypted": instance.get("StorageEncrypted"),
                        }
                    )
        except Exception as error:
            return {"status": "error", "error_type": type(error).__name__, "message": str(error)}

        return {"status": "ok", "db_instance_count": len(instances), "db_instances": instances}
