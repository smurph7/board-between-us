import hashlib
import secrets


def generate_access_token() -> str:
    """Generate a private token suitable for inclusion in a player URL."""
    return secrets.token_urlsafe(32)


def generate_telegram_link_token() -> str:
    """Generate a Telegram deep-link and private-board token."""
    return secrets.token_urlsafe(32)


def hash_access_token(token: str) -> str:
    """Return a stable SHA-256 hash for database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
