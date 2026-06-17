from datetime import datetime, timezone

from src.services.s3_storage_metrics import S3StorageMetricsService


class FakePaginator:
    def paginate(self, **kwargs):
        metric_name = kwargs["MetricName"]
        bucket_name = kwargs.get("Dimensions", [{}])[0].get("Value", "example-bucket")
        if metric_name == "BucketSizeBytes":
            storage_types = ["StandardStorage"]
        else:
            storage_types = ["AllStorageTypes"]
        return [
            {
                "Metrics": [
                    {
                        "Namespace": "AWS/S3",
                        "MetricName": metric_name,
                        "Dimensions": [
                            {"Name": "BucketName", "Value": bucket_name},
                            {"Name": "StorageType", "Value": storage_type},
                        ],
                    }
                    for storage_type in storage_types
                ]
            }
        ]


class FakeCloudWatchClient:
    def get_paginator(self, name):
        assert name == "list_metrics"
        return FakePaginator()

    def get_metric_statistics(self, MetricName, Dimensions, **kwargs):
        storage_type = {dimension["Name"]: dimension["Value"] for dimension in Dimensions}[
            "StorageType"
        ]
        if MetricName == "BucketSizeBytes" and storage_type == "StandardStorage":
            average = 1073741824.0
        elif MetricName == "NumberOfObjects" and storage_type == "AllStorageTypes":
            average = 42.0
        else:
            average = 0.0
        return {
            "Datapoints": [
                {"Timestamp": datetime(2026, 6, 16, tzinfo=timezone.utc), "Average": average}
            ]
        }


class FakeFactory:
    def create_client(self, service_name):
        assert service_name == "cloudwatch"
        return FakeCloudWatchClient()


def test_get_bucket_size_summary_for_bucket() -> None:
    service = S3StorageMetricsService(FakeFactory())

    result = service.get_bucket_size_summary(bucket_name="example-bucket", days=3)

    assert result["status"] == "ok"
    assert result["bucket_name"] == "example-bucket"
    assert result["days"] == 3
    assert result["metric_count"] == 2
    assert result["bucket_count"] == 1
    assert result["buckets"] == [
        {
            "bucket_name": "example-bucket",
            "size_bytes_by_storage_type": {"StandardStorage": 1073741824.0},
            "object_count_by_storage_type": {"AllStorageTypes": 42.0},
            "latest_timestamps": {
                "BucketSizeBytes": datetime(2026, 6, 16, tzinfo=timezone.utc),
                "NumberOfObjects": datetime(2026, 6, 16, tzinfo=timezone.utc),
            },
            "total_size_bytes": 1073741824.0,
            "total_size_gib": 1.0,
            "total_object_count": 42.0,
        }
    ]
