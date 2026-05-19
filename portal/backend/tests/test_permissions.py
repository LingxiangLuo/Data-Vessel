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
    """
    Builds a mock db that handles two query chains used by require_permission:

    1. _is_admin: db.query(SysUserRole).join(SysRole, cond).filter(...).first()
       → must return None so user is NOT treated as admin

    2. permission check: db.query(SysPermission).join(SysRolePermission, cond)
                          .join(SysUserRole, cond).filter(...).first()
       → returns a MagicMock (truthy) when has_permission=True, else None

    MagicMock chains share the same `.join()` mock, so we distinguish by call count:
    first call to .join() is from _is_admin (1 join), second is permission check (2 joins).
    We use side_effect on the nested chain to control .first() by depth.
    """
    from app.models.role import SysUserRole, SysRole, SysPermission

    db = MagicMock()
    perm_obj = MagicMock() if has_permission else None

    def query_side_effect(model):
        q = MagicMock()
        if model is SysUserRole:
            # _is_admin: .join(SysRole).filter(...).first() → None (not admin)
            q.join.return_value.filter.return_value.first.return_value = None
        elif model is SysPermission:
            # permission check: .join(...).join(...).filter(...).first()
            q.join.return_value.join.return_value.filter.return_value.first.return_value = perm_obj
        return q

    db.query.side_effect = query_side_effect
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
    result = dep(current_user=user, db=db)
    assert result == user


def test_require_permission_denied():
    user = _make_user()
    db = _make_db(has_permission=False)
    dep = require_permission("component:write")
    with pytest.raises(HTTPException) as exc_info:
        dep(current_user=user, db=db)
    assert exc_info.value.status_code == 403


def test_require_permission_admin_has_all():
    """role='admin' 字段直接通过，无需查权限表"""
    user = _make_user(role="admin")
    db = MagicMock()  # should not be queried for permissions
    dep = require_permission("system:config")
    result = dep(current_user=user, db=db)
    assert result == user
