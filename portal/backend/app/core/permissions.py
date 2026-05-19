"""RBAC 权限依赖装饰器 + 资源级 ACL 工具"""
from typing import List, Optional, Set
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user


def _is_admin(db: Session, user) -> bool:
    """判断用户是否为管理员（兼容旧 role 字段和新 RBAC 角色表）"""
    if getattr(user, "role", None) == "admin":
        return True
    from app.models.role import SysUserRole, SysRole
    return db.query(SysUserRole).join(
        SysRole, SysRole.id == SysUserRole.role_id
    ).filter(
        SysUserRole.user_id == user.id,
        SysRole.code == "admin",
    ).first() is not None


def require_permission(code: str):
    """返回一个 FastAPI 依赖，校验当前用户是否拥有指定权限码"""
    def dependency(
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        if _is_admin(db, current_user):
            return current_user

        from app.models.role import SysUserRole, SysRolePermission, SysPermission
        has = (
            db.query(SysPermission)
            .join(SysRolePermission, SysRolePermission.permission_id == SysPermission.id)
            .join(SysUserRole, SysUserRole.role_id == SysRolePermission.role_id)
            .filter(
                SysUserRole.user_id == current_user.id,
                SysPermission.code == code,
            )
            .first()
        )
        if not has:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要: {code}",
            )
        return current_user

    return dependency


def get_accessible_ids(
    db: Session,
    user,
    resource_type: str,
    min_permission: str = "read",
) -> Optional[Set[int]]:
    """
    返回当前用户对指定资源类型有访问权限的 resource_id 集合。
    返回 None 表示无限制（admin 或该资源类型尚无任何 ACL 记录）。

    min_permission 优先级: read < write < admin
    """
    if _is_admin(db, user):
        return None  # admin 不限制

    from app.models.resource_access import SysResourceAccess
    from app.models.role import SysUserRole

    _PERM_RANK = {"read": 0, "write": 1, "admin": 2}
    min_rank = _PERM_RANK.get(min_permission, 0)

    # 检查该资源类型是否有任何 ACL 记录；若无则默认全部可见
    has_any = db.query(SysResourceAccess).filter(
        SysResourceAccess.resource_type == resource_type
    ).first()
    if not has_any:
        return None  # 尚未配置 ACL，全部可见

    # 用户直接授权
    user_rows = db.query(SysResourceAccess).filter(
        SysResourceAccess.resource_type == resource_type,
        SysResourceAccess.subject_type == "user",
        SysResourceAccess.subject_id == user.id,
    ).all()

    # 通过角色授权
    role_ids = [r.role_id for r in db.query(SysUserRole).filter(SysUserRole.user_id == user.id).all()]
    role_rows = []
    if role_ids:
        role_rows = db.query(SysResourceAccess).filter(
            SysResourceAccess.resource_type == resource_type,
            SysResourceAccess.subject_type == "role",
            SysResourceAccess.subject_id.in_(role_ids),
        ).all()

    accessible: Set[int] = set()
    for row in user_rows + role_rows:
        if _PERM_RANK.get(row.permission, 0) >= min_rank:
            accessible.add(row.resource_id)

    return accessible


def check_resource_permission(
    db: Session,
    user,
    resource_type: str,
    resource_id: int,
    min_permission: str = "read",
) -> bool:
    """检查用户对单个资源是否有指定权限"""
    ids = get_accessible_ids(db, user, resource_type, min_permission)
    if ids is None:
        return True  # 无限制（admin 或无 ACL 记录）
    return resource_id in ids
