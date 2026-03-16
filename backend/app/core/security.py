"""
Security module — re-exported from core/__init__.py for convenience.
This file contains the higher-level current_user dependency.
"""

from app.core import (  # noqa: F401
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    oauth2_scheme,
    login_limiter,
)
