from tracedesk_api.mcp_layer.contracts import AuthorizationContext


class ToolAuthorizationError(ValueError):
    pass


class ToolApprovalError(ValueError):
    pass


def require_scope(context: AuthorizationContext, scope: str) -> None:
    if scope not in context.scopes:
        raise ToolAuthorizationError(f"Required scope is missing: {scope}")


def require_approval(context: AuthorizationContext, approval_id: str) -> None:
    if approval_id not in context.approved_action_ids:
        raise ToolApprovalError("This state-changing operation requires human approval")
    if context.session_id is None:
        raise ToolApprovalError("Approved writes require an isolated demo session")
