import hashlib
import hmac


def sign_session_id(session_id: str, secret: str) -> str:
    signature = hmac.new(secret.encode(), session_id.encode(), hashlib.sha256).hexdigest()
    return f"{session_id}.{signature}"


def verify_session_token(token: str | None, secret: str) -> str | None:
    if not token or "." not in token:
        return None
    session_id, supplied_signature = token.rsplit(".", 1)
    expected = hmac.new(secret.encode(), session_id.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(supplied_signature, expected):
        return None
    return session_id
