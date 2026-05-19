from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_permission

router = APIRouter()


class RoleCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    permission_codes: List[str] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_codes: Optional[List[str]] = None


@router.get("/roles")
def list_roles(
    db: Session = Depends(get_db),
    _=Depends(require_permission("role:manage")),
):
    from app.models.role import SysRole, SysRolePermission, SysPermission
    roles = db.query(SysRole).all()
    result = []
    for r in roles:
        perms = (
            db.query(SysPermission)
            .join(SysRolePermission, SysRolePermission.permission_id == SysPermission.id)
            .filter(SysRolePermission.role_id == r.id)
            .all()
        )
        result.append({
            "id": r.id,
            "code": r.code,
            "name": r.name,
            "description": r.description,
            "is_system": r.is_system,
            "permissions": [{"id": p.id, "code": p.code, "name": p.name} for p in perms],
        })
    return result


@router.post("/roles", status_code=201)
def create_role(
    body: RoleCreate,
    db: Session = Depends(get_db),
    _=Depends(require_permission("role:manage")),
):
    from app.models.role import SysRole, SysRolePermission, SysPermission
    if db.query(SysRole).filter(SysRole.code == body.code).first():
        raise HTTPException(400, "角色代码已存在")
    role = SysRole(code=body.code, name=body.name, description=body.description)
    db.add(role)
    db.flush()
    for code in body.permission_codes:
        perm = db.query(SysPermission).filter(SysPermission.code == code).first()
        if perm:
            db.add(SysRolePermission(role_id=role.id, permission_id=perm.id))
    db.commit()
    return {"id": role.id, "code": role.code}


@router.put("/roles/{role_id}")
def update_role(
    role_id: int,
    body: RoleUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permission("role:manage")),
):
    from app.models.role import SysRole, SysRolePermission, SysPermission
    role = db.query(SysRole).filter(SysRole.id == role_id).first()
    if not role:
        raise HTTPException(404, "角色不存在")
    if role.is_system:
        raise HTTPException(400, "系统内置角色不可修改")
    if body.name is not None:
        role.name = body.name
    if body.description is not None:
        role.description = body.description
    if body.permission_codes is not None:
        db.query(SysRolePermission).filter(SysRolePermission.role_id == role_id).delete()
        for code in body.permission_codes:
            perm = db.query(SysPermission).filter(SysPermission.code == code).first()
            if perm:
                db.add(SysRolePermission(role_id=role_id, permission_id=perm.id))
    db.commit()
    return {"ok": True}


@router.delete("/roles/{role_id}")
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("role:manage")),
):
    from app.models.role import SysRole, SysRolePermission, SysUserRole
    role = db.query(SysRole).filter(SysRole.id == role_id).first()
    if not role:
        raise HTTPException(404, "角色不存在")
    if role.is_system:
        raise HTTPException(400, "系统内置角色不可删除")
    db.query(SysRolePermission).filter(SysRolePermission.role_id == role_id).delete()
    db.query(SysUserRole).filter(SysUserRole.role_id == role_id).delete()
    db.delete(role)
    db.commit()
    return {"ok": True}


@router.get("/permissions")
def list_permissions(
    db: Session = Depends(get_db),
    _=Depends(require_permission("role:manage")),
):
    from app.models.role import SysPermission
    perms = db.query(SysPermission).all()
    return [{"id": p.id, "code": p.code, "name": p.name, "resource_type": p.resource_type, "action": p.action} for p in perms]
