import pytest

from tracedesk_api.config import Settings
from tracedesk_api.live_access import LiveAccessDenied, verify_live_investigation_access


def test_live_access_requires_anthropic_key() -> None:
    settings = Settings(anthropic_api_key=None)

    with pytest.raises(LiveAccessDenied, match="ANTHROPIC_API_KEY"):
        verify_live_investigation_access(settings, supplied_code=None)


def test_live_access_allows_local_development_without_code() -> None:
    settings = Settings(app_env="development", anthropic_api_key="test-key")

    verify_live_investigation_access(settings, supplied_code=None)


def test_live_access_requires_configured_code_in_production() -> None:
    settings = Settings(app_env="production", anthropic_api_key="test-key")

    with pytest.raises(LiveAccessDenied, match="disabled in production"):
        verify_live_investigation_access(settings, supplied_code=None)


def test_live_access_requires_matching_code_when_configured() -> None:
    settings = Settings(
        app_env="production",
        anthropic_api_key="test-key",
        live_investigation_access_code="private-demo-code",
    )

    with pytest.raises(LiveAccessDenied, match="valid access code"):
        verify_live_investigation_access(settings, supplied_code="wrong")

    verify_live_investigation_access(settings, supplied_code=" private-demo-code ")
