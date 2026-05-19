from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_permission

router = APIRouter()


class ResourceAccessGrant(BaseModel):
    resource_type: str
    resource_id: int
    subject_type: str
    subject_id: int
    permission: str


class ResourceAccessRevoke(BaseModel):
    resource_type: str
    resource_id: int
    subject_type: str
    subject_id: int


_VALID_TYPES = {"workflow", "datasource", "component"}
_VALID_PERMS = {"read", "write", "admin"}
_VALID_SUBJECTS = {"user", "role"}


@router.get("/resource-access")
def list_resource_access(
    resource_type: str,
    resource_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("user:manage")),
):
    from app.models.resource_access import SysResourceAccess
    rows = db.query(SysResourceAccess).filter(
        SysResourceAccess.resource_type == resource_type,
        SysResourceAccess.resource_id == resource_id,
    ).all()
    return [
        {
            "id": r.id,
            "subject_type": r.subject_type,
            "subject_id": r.subject_id,
            "permission": r.permission,
            "granted_by": r.granted_by,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.post("/resource-access", status_code=201)
def grant_resource_access(
    body: ResourceAccessGrant,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("user:manage")),
):
    from app.models.resource_access import SysResourceAccess
    if body.resource_type not in _VALID_TYPES:
        raise HTTPException(400, f"无效的 resource_type: {body.resource_type}")
    if body.permission not in _VALID_PERMS:
        raise HTTPException(400, f"无效的 permission: {body.permission}")
    if body.subject_type not in _VALID_SUBJECTS:
        raise HTTPException(400, f"无效的 subject_type: {body.subject_type}")

    existing = db.query(SysResourceAccess).filter(
        SysResourceAccess.resource_type == body.resource_type,
        SysResourceAccess.resource_id == body.resource_id,
        SysResourceAccess.subject_type == body.subject_type,
        SysResourceAccess.subject_id == body.subject_id,
    ).first()

    if existing:
        existing.permission = body.permission
        existing.granted_by = current_user.id
    else:
        db.add(SysResourceAccess(
            resource_type=body.resource_type,
            resource_id=body.resource_id,
            subject_type=body.subject_type,
            subject_id=body.subject_id,
            permission=body.permission,
            granted_by=current_user.id,
        ))
    db.commit()
    return {"ok": True}


@router.delete("/resource-access")
def revoke_resource_access(
    body: ResourceAccessRevoke,
    db: Session = Depends(get_db),
    _=Depends(require_permission("user:manage")),
):
    from app.models.resource_access import SysResourceAccess
    deleted = db.query(SysResourceAccess).filter(
        SysResourceAccess.resource_type == body.resource_type,
        SysResourceAccess.resource_id == body.resource_id,
        SysResourceAccess.subject_type == body.subject_type,
        SysResourceAccess.subject_id == body.subject_id,
    ).delete()
    db.commit()
    return {"ok": True, "deleted": deleted}
