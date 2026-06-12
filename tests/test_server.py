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
