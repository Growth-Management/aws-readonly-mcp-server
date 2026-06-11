from src.server.main import create_server


def test_healthcheck_returns_ok() -> None:
    server = create_server()
    result = server.healthcheck()
    assert result["status"] == "ok"
    assert "aws_region" in result
