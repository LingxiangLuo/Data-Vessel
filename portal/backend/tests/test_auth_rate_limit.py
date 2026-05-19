"""Tests for login rate limiting in app/api/auth.py"""
import time
import pytest
from unittest.mock import patch
from fastapi import HTTPException

# Force Redis to be unavailable so tests use in-memory fallback
with patch("app.api.auth._get_redis", return_value=None):
    pass

from app.api.auth import (
    _check_login_rate,
    _record_failed_login,
    _clear_login_attempts,
    _login_attempts,
)


@pytest.fixture(autouse=True)
def clear_attempts():
    _login_attempts.clear()
    yield
    _login_attempts.clear()


def test_no_lockout_below_limit():
    ip = "10.0.0.1"
    with patch("app.api.auth._get_redis", return_value=None):
        for _ in range(4):
            _record_failed_login(ip)
        _check_login_rate(ip)  # should not raise


def test_lockout_after_max_attempts():
    ip = "10.0.0.2"
    with patch("app.api.auth._get_redis", return_value=None):
        for _ in range(5):
            _record_failed_login(ip)
        with pytest.raises(HTTPException) as exc_info:
            _check_login_rate(ip)
        assert exc_info.value.status_code == 429


def test_clear_resets_lockout():
    ip = "10.0.0.3"
    with patch("app.api.auth._get_redis", return_value=None):
        for _ in range(5):
            _record_failed_login(ip)
        _clear_login_attempts(ip)
        _check_login_rate(ip)  # should not raise after clear


def test_expired_attempts_not_counted():
    ip = "10.0.0.4"
    with patch("app.api.auth._get_redis", return_value=None):
        # Inject old timestamps directly
        old_time = time.time() - 400  # older than LOGIN_LOCKOUT_SECONDS=300
        _login_attempts[ip] = [old_time] * 5
        _check_login_rate(ip)  # should not raise — all expired
