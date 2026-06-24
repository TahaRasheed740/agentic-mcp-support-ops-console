from __future__ import annotations

from tracedesk_api.config import Settings


class LiveAccessDenied(PermissionError):
    pass


def live_investigation_capability(settings: Settings) -> tuple[bool, str]:
    if not settings.live_investigations_enabled:
        return (
            False,
            "Live Claude investigations are disabled for this deployment. Use recorded replays.",
        )
    if not settings.anthropic_api_key:
        return False, "Live investigations require ANTHROPIC_API_KEY."
    if settings.app_env.lower() == "production":
        return (
            False,
            "Production is configured for replay-only public access. Live Claude runs are local-only.",
        )
    return True, "Live Claude investigations are available in this local environment."


def verify_live_investigation_access(settings: Settings) -> None:
    enabled, reason = live_investigation_capability(settings)
    if not enabled:
        raise LiveAccessDenied(reason)
