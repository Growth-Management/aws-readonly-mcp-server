from src.services.cloudwatch_metrics import CloudWatchMetricsService


class FakePaginator:
    def paginate(self, Namespace):
        return [
            {
                "Metrics": [
                    {
                        "Namespace": Namespace,
                        "MetricName": "CPUUtilization",
                        "Dimensions": [{"Name": "InstanceId", "Value": "i-123"}],
                    },
                    {
                        "Namespace": Namespace,
                        "MetricName": "NetworkIn",
                        "Dimensions": [{"Name": "InstanceId", "Value": "i-123"}],
                    },
                ]
            }
        ]


class FakeCloudWatchClient:
    def get_paginator(self, name):
        assert name == "list_metrics"
        return FakePaginator()


class FakeFactory:
    def create_client(self, service_name):
        assert service_name == "cloudwatch"
        return FakeCloudWatchClient()


def test_get_metric_summary_for_namespace() -> None:
    service = CloudWatchMetricsService(FakeFactory())

    result = service.get_metric_summary(namespace="AWS/EC2")

    assert result["status"] == "ok"
    assert result["namespace"] == "AWS/EC2"
    assert result["summaries"] == [
        {
            "namespace": "AWS/EC2",
            "metric_count": 2,
            "metric_names": ["CPUUtilization", "NetworkIn"],
            "dimension_names": ["InstanceId"],
        }
    ]
