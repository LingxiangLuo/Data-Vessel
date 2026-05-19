from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_permission
from app.core.security import hash_password

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    password: str
    real_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    dept_id: Optional[int] = None
    role_codes: List[str] = []


class UserUpdate(BaseModel):
    real_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    dept_id: Optional[int] = None
    status: Optional[int] = None
    password: Optional[str] = None
    role_codes: Optional[List[str]] = None


@router.get("/users")
def list_users(
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(require_permission("user:manage")),
):
    from app.models.user import SysUser
    from app.models.role import SysUserRole, SysRole
    q = db.query(SysUser)
    if keyword:
        q = q.filter(
            SysUser.username.contains(keyword) | SysUser.real_name.contains(keyword)
        )
    total = q.count()
    users = q.offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for u in users:
        roles = (
            db.query(SysRole)
            .join(SysUserRole, SysUserRole.role_id == SysRole.id)
            .filter(SysUserRole.user_id == u.id)
            .all()
        )
        result.append({
            "id": u.id,
            "username": u.username,
            "real_name": u.real_name,
            "email": u.email,
            "phone": u.phone,
            "dept_id": u.dept_id,
            "status": u.status,
            "avatar": u.avatar,
            "last_login_at": u.last_login_at,
            "oauth_provider": u.oauth_provider,
            "created_at": u.created_at,
            "roles": [{"id": r.id, "code": r.code, "name": r.name} for r in roles],
        })
    return {"total": total, "items": result}


@router.post("/users", status_code=201)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("user:manage")),
):
    from app.models.user import SysUser
    from app.models.role import SysUserRole, SysRole
    if db.query(SysUser).filter(SysUser.username == body.username).first():
        raise HTTPException(400, "用户名已存在")
    user = SysUser(
        username=body.username,
        password=hash_password(body.password),
        real_name=body.real_name,
        email=body.email,
        phone=body.phone,
        dept_id=body.dept_id,
        status=1,
    )
    db.add(user)
    db.flush()
    for code in body.role_codes:
        role = db.query(SysRole).filter(SysRole.code == code).first()
        if role:
            db.add(SysUserRole(user_id=user.id, role_id=role.id, granted_by=current_user.id))
    db.commit()
    return {"id": user.id, "username": user.username}


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("user:manage")),
):
    from app.models.user import SysUser
    from app.models.role import SysUserRole, SysRole
    user = db.query(SysUser).filter(SysUser.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    if body.real_name is not None:
        user.real_name = body.real_name
    if body.email is not None:
        user.email = body.email
    if body.phone is not None:
        user.phone = body.phone
    if body.dept_id is not None:
        user.dept_id = body.dept_id
    if body.status is not None:
        user.status = body.status
    if body.password:
        user.password = hash_password(body.password)
    if body.role_codes is not None:
        db.query(SysUserRole).filter(SysUserRole.user_id == user_id).delete()
        for code in body.role_codes:
            role = db.query(SysRole).filter(SysRole.code == code).first()
            if role:
                db.add(SysUserRole(user_id=user_id, role_id=role.id, granted_by=current_user.id))
    db.commit()
    return {"ok": True}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("user:manage")),
):
    from app.models.user import SysUser
    from app.models.role import SysUserRole
    user = db.query(SysUser).filter(SysUser.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    if user.username == "admin":
        raise HTTPException(400, "不能删除内置管理员")
    if user.id == current_user.id:
        raise HTTPException(400, "不能删除自己的账号")
    db.query(SysUserRole).filter(SysUserRole.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"ok": True}
