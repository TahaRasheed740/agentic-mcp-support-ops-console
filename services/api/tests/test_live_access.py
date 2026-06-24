import pytest

from tracedesk_api.config import Settings
from tracedesk_api.live_access import (
    LiveAccessDenied,
    live_investigation_capability,
    verify_live_investigation_access,
)


def test_live_access_defaults_to_disabled() -> None:
    settings = Settings()

    enabled, reason = live_investigation_capability(settings)

    assert enabled is False
    assert "disabled" in reason


def test_live_access_requires_anthropic_key_when_enabled() -> None:
    settings = Settings(live_investigations_enabled=True, anthropic_api_key=None)

    with pytest.raises(LiveAccessDenied, match="ANTHROPIC_API_KEY"):
        verify_live_investigation_access(settings)


def test_live_access_allows_local_development_without_code() -> None:
    settings = Settings(
        app_env="development",
        live_investigations_enabled=True,
        anthropic_api_key="test-key",
    )

    verify_live_investigation_access(settings)


def test_live_access_blocks_production_even_when_enabled_with_key() -> None:
    settings = Settings(
        app_env="production",
        live_investigations_enabled=True,
        anthropic_api_key="test-key",
    )

    enabled, reason = live_investigation_capability(settings)

    assert enabled is False
    assert "replay-only" in reason


def test_live_access_allows_local_development_when_enabled_and_key_present() -> None:
    settings = Settings(
        app_env="development",
        live_investigations_enabled=True,
        anthropic_api_key="test-key",
    )

    verify_live_investigation_access(settings)
