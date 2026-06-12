from src.server.config import load_settings


def test_load_settings_defaults() -> None:
    settings = load_settings()
    assert settings.aws_region
    assert settings.default_lookback_months >= 1
    assert settings.aws_role_session_name == "aws-readonly-mcp"
    assert settings.aws_access_key_id == ""
    assert settings.aws_secret_access_key == ""
