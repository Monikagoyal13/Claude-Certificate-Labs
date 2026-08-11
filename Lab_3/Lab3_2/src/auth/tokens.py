"""Token verification for NorthPeak Outfitters services."""

_VALID_PREFIX = "npk_live_"
_MIN_SUFFIX_LENGTH = 12


def verify_token(token: str) -> bool:
    """Return True if token is a well-formed live API token."""
    if not isinstance(token, str):
        return False
    return token.startswith(_VALID_PREFIX) and len(token) - len(_VALID_PREFIX) >= _MIN_SUFFIX_LENGTH


def verify_token_v1(token: str) -> bool:
    """Deprecated weak token check kept only until every caller migrates to verify_token."""
    return isinstance(token, str) and len(token) > 6
