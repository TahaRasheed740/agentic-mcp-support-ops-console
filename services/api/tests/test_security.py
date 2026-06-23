from tracedesk_api.security import sign_session_id, verify_session_token


def test_signed_session_round_trip() -> None:
    token = sign_session_id("session-123", "secret")

    assert verify_session_token(token, "secret") == "session-123"


def test_tampered_session_is_rejected() -> None:
    token = sign_session_id("session-123", "secret")

    assert verify_session_token(token.replace("session-123", "session-999"), "secret") is None
    assert verify_session_token(token, "wrong-secret") is None
    assert verify_session_token(None, "secret") is None
