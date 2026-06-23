import pytest

from tracedesk_api.mcp_layer.authorization import (
    ToolApprovalError,
    ToolAuthorizationError,
    require_approval,
    require_scope,
)
from tracedesk_api.mcp_layer.contracts import AuthorizationContext


def context(**updates: object) -> AuthorizationContext:
    values: dict[str, object] = {
        "request_id": "request_12345678",
        "persona_id": "persona_maya",
        "session_id": "session_12345678",
        "scopes": ["support:read"],
        "approved_action_ids": ["approval_12345678"],
    }
    values.update(updates)
    return AuthorizationContext.model_validate(values)


def test_scope_is_required() -> None:
    require_scope(context(), "support:read")
    with pytest.raises(ToolAuthorizationError, match="Required scope"):
        require_scope(context(), "operations:read")


def test_write_requires_matching_approval_and_session() -> None:
    require_approval(context(), "approval_12345678")
    with pytest.raises(ToolApprovalError, match="human approval"):
        require_approval(context(), "different_approval")
    with pytest.raises(ToolApprovalError, match="isolated demo session"):
        require_approval(context(session_id=None), "approval_12345678")
