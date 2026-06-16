from fastapi.testclient import TestClient

from src.server.main import app, create_server


def test_healthcheck_returns_ok() -> None:
    server = create_server()
    result = server.healthcheck()
    assert result["status"] == "ok"
    assert "aws_region" in result


def test_fastapi_healthcheck_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_mcp_lists_expected_tools() -> None:
    server = create_server()
    tool_names = {tool["name"] for tool in server.list_mcp_tools()}

    assert "get_caller_identity" in tool_names
    assert "list_s3_buckets" in tool_names
    assert "get_s3_bucket_details" in tool_names
    assert "get_s3_bucket_security" in tool_names
    assert "get_cost_by_service" in tool_names
    assert "get_cloudwatch_metric_summary" in tool_names


def test_mcp_initialize_response() -> None:
    server = create_server()
    response = server.handle_mcp_request(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )

    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert response["result"]["capabilities"] == {"tools": {}}


def test_fastapi_mcp_requires_bearer_token(monkeypatch) -> None:
    monkeypatch.setenv("MCP_AUTH_TOKEN", "test-token")
    client = TestClient(app)

    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "missing_authorization_header"


def test_fastapi_mcp_initialize_with_bearer_token(monkeypatch) -> None:
    monkeypatch.setenv("MCP_AUTH_TOKEN", "test-token")
    client = TestClient(app)

    response = client.post(
        "/mcp",
        headers={"Authorization": "Bearer test-token"},
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    )

    assert response.status_code == 200
    assert response.json()["result"]["serverInfo"]["name"] == "aws-readonly-mcp-server"


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


def test_mcp_tool_call_requires_service_name_for_baseline() -> None:
    server = create_server()
    response = server.handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_service_metric_baseline", "arguments": {}},
        }
    )

    assert response is not None
    assert response["result"]["isError"] is True
    assert "service_name is required" in response["result"]["content"][0]["text"]
