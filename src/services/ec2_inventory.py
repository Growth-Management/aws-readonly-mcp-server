from __future__ import annotations

from typing import Any

from src.aws.client_factory import AWSClientFactory


class EC2InventoryService:
    def __init__(self, factory: AWSClientFactory | None = None) -> None:
        self.factory = factory or AWSClientFactory()

    def list_instances(self) -> dict[str, Any]:
        try:
            ec2 = self.factory.create_client("ec2")
            paginator = ec2.get_paginator("describe_instances")
            instances: list[dict[str, Any]] = []
            for page in paginator.paginate():
                for reservation in page.get("Reservations", []):
                    for instance in reservation.get("Instances", []):
                        instances.append(
                            {
                                "instance_id": instance.get("InstanceId"),
                                "instance_type": instance.get("InstanceType"),
                                "state": instance.get("State", {}).get("Name"),
                                "launch_time": instance.get("LaunchTime").isoformat()
                                if instance.get("LaunchTime")
                                else None,
                                "tags": instance.get("Tags", []),
                            }
                        )
        except Exception as error:
            return {"status": "error", "error_type": type(error).__name__, "message": str(error)}

        return {"status": "ok", "instance_count": len(instances), "instances": instances}

    def list_volumes(self) -> dict[str, Any]:
        try:
            ec2 = self.factory.create_client("ec2")
            paginator = ec2.get_paginator("describe_volumes")
            volumes: list[dict[str, Any]] = []
            for page in paginator.paginate():
                for volume in page.get("Volumes", []):
                    volumes.append(
                        {
                            "volume_id": volume.get("VolumeId"),
                            "size_gib": volume.get("Size"),
                            "state": volume.get("State"),
                            "volume_type": volume.get("VolumeType"),
                            "encrypted": volume.get("Encrypted"),
                            "attachments": volume.get("Attachments", []),
                            "tags": volume.get("Tags", []),
                        }
                    )
        except Exception as error:
            return {"status": "error", "error_type": type(error).__name__, "message": str(error)}

        return {"status": "ok", "volume_count": len(volumes), "volumes": volumes}
