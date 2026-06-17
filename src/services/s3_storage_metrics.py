from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from src.aws.client_factory import AWSClientFactory

S3_NAMESPACE = "AWS/S3"
STORAGE_METRIC_NAMES = ("BucketSizeBytes", "NumberOfObjects")
DEFAULT_LOOKBACK_DAYS = 7
SECONDS_PER_DAY = 86400


class S3StorageMetricsService:
    def __init__(self, factory: AWSClientFactory | None = None) -> None:
        self.factory = factory or AWSClientFactory()

    def get_bucket_size_summary(
        self,
        bucket_name: str | None = None,
        days: int = DEFAULT_LOOKBACK_DAYS,
    ) -> dict[str, Any]:
        try:
            cloudwatch = self.factory.create_client("cloudwatch")
            metrics = self._list_storage_metrics(cloudwatch, bucket_name=bucket_name)
            summaries = self._build_bucket_summaries(cloudwatch, metrics, days=max(1, days))
        except Exception as error:
            return {
                "status": "error",
                "error_type": type(error).__name__,
                "message": str(error),
            }

        return {
            "status": "ok",
            "bucket_name": bucket_name,
            "days": max(1, days),
            "metric_count": len(metrics),
            "bucket_count": len(summaries),
            "buckets": summaries,
        }

    def _list_storage_metrics(
        self,
        cloudwatch,
        bucket_name: str | None = None,
    ) -> list[dict[str, Any]]:
        paginator = cloudwatch.get_paginator("list_metrics")
        metrics: list[dict[str, Any]] = []

        for metric_name in STORAGE_METRIC_NAMES:
            paginate_args: dict[str, Any] = {"Namespace": S3_NAMESPACE, "MetricName": metric_name}
            if bucket_name:
                paginate_args["Dimensions"] = [{"Name": "BucketName", "Value": bucket_name}]

            for page in paginator.paginate(**paginate_args):
                for metric in page.get("Metrics", []):
                    dimensions = _dimensions_by_name(metric.get("Dimensions", []))
                    if "BucketName" not in dimensions or "StorageType" not in dimensions:
                        continue
                    if bucket_name and dimensions["BucketName"] != bucket_name:
                        continue
                    metrics.append(
                        {
                            "metric_name": metric_name,
                            "bucket_name": dimensions["BucketName"],
                            "storage_type": dimensions["StorageType"],
                            "dimensions": [
                                {"Name": "BucketName", "Value": dimensions["BucketName"]},
                                {"Name": "StorageType", "Value": dimensions["StorageType"]},
                            ],
                        }
                    )

        return metrics

    def _build_bucket_summaries(
        self,
        cloudwatch,
        metrics: list[dict[str, Any]],
        days: int,
    ) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "bucket_name": "",
                "size_bytes_by_storage_type": {},
                "object_count_by_storage_type": {},
                "latest_timestamps": {},
            }
        )

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)

        for metric in metrics:
            datapoint = self._latest_datapoint(
                cloudwatch,
                metric_name=metric["metric_name"],
                dimensions=metric["dimensions"],
                start_time=start_time,
                end_time=end_time,
            )
            if not datapoint:
                continue

            bucket_name = metric["bucket_name"]
            storage_type = metric["storage_type"]
            value = datapoint.get("Average")
            if value is None:
                continue

            summary = grouped[bucket_name]
            summary["bucket_name"] = bucket_name
            timestamp = datapoint.get("Timestamp")
            if timestamp is not None:
                summary["latest_timestamps"][metric["metric_name"]] = timestamp

            if metric["metric_name"] == "BucketSizeBytes":
                summary["size_bytes_by_storage_type"][storage_type] = value
            elif metric["metric_name"] == "NumberOfObjects":
                summary["object_count_by_storage_type"][storage_type] = value

        summaries = []
        for summary in grouped.values():
            size_bytes = summary["size_bytes_by_storage_type"]
            object_counts = summary["object_count_by_storage_type"]
            summary["total_size_bytes"] = sum(size_bytes.values())
            summary["total_size_gib"] = round(summary["total_size_bytes"] / (1024**3), 3)
            summary["total_object_count"] = sum(object_counts.values())
            summaries.append(summary)

        return sorted(summaries, key=lambda item: item["bucket_name"])

    def _latest_datapoint(
        self,
        cloudwatch,
        metric_name: str,
        dimensions: list[dict[str, str]],
        start_time: datetime,
        end_time: datetime,
    ) -> dict[str, Any] | None:
        response = cloudwatch.get_metric_statistics(
            Namespace=S3_NAMESPACE,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=start_time,
            EndTime=end_time,
            Period=SECONDS_PER_DAY,
            Statistics=["Average"],
        )
        datapoints = response.get("Datapoints", [])
        if not datapoints:
            return None
        fallback = datetime.min.replace(tzinfo=timezone.utc)
        return max(datapoints, key=lambda item: item.get("Timestamp", fallback))


def _dimensions_by_name(dimensions: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(dimension["Name"]): str(dimension["Value"])
        for dimension in dimensions
        if "Name" in dimension and "Value" in dimension
    }
