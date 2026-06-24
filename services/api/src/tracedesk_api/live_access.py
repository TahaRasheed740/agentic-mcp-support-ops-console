from __future__ import annotations

import hmac

from tracedesk_api.config import Settings


class LiveAccessDenied(PermissionError):
    pass


def verify_live_investigation_access(settings: Settings, supplied_code: str | None) -> None:
    if not settings.anthropic_api_key:
        raise LiveAccessDenied("Live investigations require ANTHROPIC_API_KEY")

    configured_code = _clean(settings.live_investigation_access_code)
    if settings.app_env.lower() == "production" and not configured_code:
        raise LiveAccessDenied(
            "Live investigations are disabled in production until LIVE_INVESTIGATION_ACCESS_CODE is set."
        )

    if configured_code and not _matches(configured_code, supplied_code):
        raise LiveAccessDenied("Live investigations require a valid access code.")


def _matches(expected: str, supplied: str | None) -> bool:
    supplied_code = _clean(supplied)
    if supplied_code is None:
        return False
    return hmac.compare_digest(expected, supplied_code)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
