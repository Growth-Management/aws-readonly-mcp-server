from src.server.main import create_server


def test_healthcheck_returns_ok() -> None:
    server = create_server()
    result = server.healthcheck()
    assert result["status"] == "ok"
    assert "aws_region" in result


def test_mcp_lists_expected_tools() -> None:
    server = create_server()
    tool_names = {tool["name"] for tool in server.list_mcp_tools()}

    assert "get_caller_identity" in tool_names
    assert "list_s3_buckets" in tool_names
    assert "get_s3_bucket_details" in tool_names
    assert "get_s3_bucket_security" in tool_names
    assert "get_s3_bucket_size_summary" in tool_names
    assert "get_cloudwatch_metric_summary" in tool_names


def test_list_actions_returns_expected_actions() -> None:
    server = create_server()
    action_names = {action["name"] for action in server.list_actions()}

    assert "get_caller_identity" in action_names
    assert "get_s3_bucket_details" in action_names
    assert "get_s3_bucket_size_summary" in action_names
    assert "get_monthly_cost_by_service" in action_names
    assert "get_cloudwatch_metric_summary" in action_names
    assert "list_ec2_instances" in action_names


def test_handle_action_request_lists_actions() -> None:
    server = create_server()
    response = server.handle_action_request({"action": "list_actions", "params": {}})

    assert response["status"] == "ok"
    assert any(action["name"] == "get_s3_bucket_details" for action in response["actions"])


def test_handle_action_request_gets_action_definition() -> None:
    server = create_server()
    response = server.handle_action_request(
        {"action": "get_action_definition", "params": {"action_name": "get_s3_bucket_details"}}
    )

    assert response["status"] == "ok"
    assert response["action_definition"]["name"] == "get_s3_bucket_details"


def test_mcp_initialize_response() -> None:
    server = create_server()
    response = server.handle_mcp_request(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )

    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert response["result"]["capabilities"] == {"tools": {}}


def test_mcp_tool_call_requires_bucket_name() -> None:
    server = create_server()
    response = server.handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "get_s3_bucket_details", "arguments": {}},
        }
    )

    assert response is not None
    assert response["result"]["isError"] is True
    assert "bucket_name is required" in response["result"]["content"][0]["text"]


def test_mcp_tool_call_routes_cloudwatch_metric_summary(monkeypatch) -> None:
    server = create_server()

    def fake_summary(namespace=None):
        return {"status": "ok", "namespace": namespace, "summaries": []}

    monkeypatch.setattr(server.cloudwatch_metrics, "get_metric_summary", fake_summary)
    response = server.handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_cloudwatch_metric_summary",
                "arguments": {"namespace": "AWS/EC2"},
            },
        }
    )

    assert response is not None
    content = response["result"]["structuredContent"]
    assert content["status"] == "ok"
    assert content["namespace"] == "AWS/EC2"


def test_mcp_tool_call_routes_s3_bucket_size_summary(monkeypatch) -> None:
    server = create_server()

    def fake_summary(bucket_name=None, days=7):
        return {"status": "ok", "bucket_name": bucket_name, "days": days, "buckets": []}

    monkeypatch.setattr(server.s3_storage_metrics, "get_bucket_size_summary", fake_summary)
    response = server.handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "get_s3_bucket_size_summary",
                "arguments": {"bucket_name": "example-bucket", "days": 3},
            },
        }
    )

    assert response is not None
    content = response["result"]["structuredContent"]
    assert content["status"] == "ok"
    assert content["bucket_name"] == "example-bucket"
    assert content["days"] == 3
