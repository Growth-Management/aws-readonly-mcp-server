from src.server.config import load_settings


def test_load_settings_defaults() -> None:
    settings = load_settings()
    assert settings.aws_region
    assert settings.default_lookback_months >= 1
