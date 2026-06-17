from __future__ import annotations

from src.aws.client_factory import AWSClientFactory


DEFAULT_NAMESPACES = [
    "AWS/EC2",
    "AWS/RDS",
    "AWS/S3",
    "AWS/SES",
]


class CloudWatchMetricsService:
    def __init__(self, factory: AWSClientFactory | None = None) -> None:
        self.factory = factory or AWSClientFactory()

    def get_metric_summary(self, namespace: str | None = None) -> dict[str, object]:
        try:
            cloudwatch = self.factory.create_client("cloudwatch")
            namespaces = [namespace] if namespace else DEFAULT_NAMESPACES
            summaries = [self._summarize_namespace(cloudwatch, item) for item in namespaces]
        except Exception as error:
            return {"status": "error", "error_type": type(error).__name__, "message": str(error)}

        return {"status": "ok", "namespace": namespace, "summaries": summaries}

    def _summarize_namespace(self, cloudwatch: object, namespace: str) -> dict[str, object]:
        paginator = cloudwatch.get_paginator("list_metrics")
        metric_names: set[str] = set()
        dimension_names: set[str] = set()
        scanned_metrics = 0

        for page in paginator.paginate(Namespace=namespace):
            for metric in page.get("Metrics", []):
                scanned_metrics += 1
                metric_name = metric.get("MetricName")
                if metric_name:
                    metric_names.add(str(metric_name))
                for dimension in metric.get("Dimensions", []):
                    dimension_name = dimension.get("Name")
                    if dimension_name:
                        dimension_names.add(str(dimension_name))

        return {
            "namespace": namespace,
            "metric_count": scanned_metrics,
            "metric_names": sorted(metric_names),
            "dimension_names": sorted(dimension_names),
        }
