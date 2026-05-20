"""Tests for app/core/permissions.py — require_permission dependency"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.core.permissions import require_permission


def _make_user(role: str = "user"):
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    user.role = role
    return user


def _make_db(has_permission: bool):
    """Build a mock db for require_permission testing.

    _is_admin is patched separately; this mock only handles the permission query.
    """
    db = MagicMock()
    perm_obj = MagicMock() if has_permission else None
    db.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = perm_obj
    return db


def _make_admin_db():
    """Mock db where _is_admin returns True via SysUserRole join query."""
    db = MagicMock()
    admin_row = MagicMock()
    db.query.return_value.join.return_value.filter.return_value.first.return_value = admin_row
    return db


def test_require_permission_granted():
    user = _make_user()
    db = _make_db(has_permission=True)
    dep = require_permission("component:write")
    with patch("app.core.permissions._is_admin", return_value=False):
        result = dep(current_user=user, db=db)
    assert result == user


def test_require_permission_denied():
    user = _make_user()
    db = _make_db(has_permission=False)
    dep = require_permission("component:write")
    with pytest.raises(HTTPException) as exc_info:
        with patch("app.core.permissions._is_admin", return_value=False):
            dep(current_user=user, db=db)
    assert exc_info.value.status_code == 403


def test_require_permission_admin_has_all():
    """role='admin' 字段直接通过，无需查权限表"""
    user = _make_user(role="admin")
    db = MagicMock()  # should not be queried for permissions
    dep = require_permission("system:config")
    result = dep(current_user=user, db=db)
    assert result == user
