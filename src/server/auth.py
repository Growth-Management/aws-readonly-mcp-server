from __future__ import annotations

import hmac
import logging

logger = logging.getLogger(__name__)


def is_authorized(authorization_header: str | None, expected_token: str) -> bool:
    """Validate a minimal Authorization: Bearer token header."""
    if not expected_token:
        logger.error("MCP auth token is not configured")
        return False

    if not authorization_header:
        logger.warning("Rejected request without Authorization header")
        return False

    scheme, separator, supplied_token = authorization_header.partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not supplied_token.strip():
        logger.warning("Rejected request with malformed Authorization header")
        return False

    if not hmac.compare_digest(supplied_token.strip(), expected_token):
        logger.warning("Rejected request with invalid bearer token")
        return False

    return True
