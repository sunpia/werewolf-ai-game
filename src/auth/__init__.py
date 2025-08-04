"""Authentication module initialization."""

from .dependencies import get_current_user, get_current_user_optional

__all__ = ["get_current_user", "get_current_user_optional"]
