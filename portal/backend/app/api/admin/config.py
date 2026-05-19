from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_permission

router = APIRouter()

_SENSITIVE_FIELDS = {"password", "secret", "access_key", "secret_key", "token", "api_key", "credential"}


def _redact(value: dict) -> dict:
    if not isinstance(value, dict):
        return value
    return {
        k: "***" if k in _SENSITIVE_FIELDS and v else (_redact(v) if isinstance(v, dict) else v)
        for k, v in value.items()
    }


class SysConfigUpdate(BaseModel):
    value: dict
    description: Optional[str] = None


@router.get("/config/{key}")
def get_config(
    key: str,
    db: Session = Depends(get_db),
    _=Depends(require_permission("system:config")),
):
    from app.models.sys_config import SysConfig
    row = db.query(SysConfig).filter(SysConfig.key == key).first()
    if not row:
        return {"key": key, "value": None}
    return {"key": row.key, "value": _redact(row.value), "description": row.description}


@router.put("/config/{key}")
def set_config(
    key: str,
    body: SysConfigUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permission("system:config")),
):
    from app.models.sys_config import SysConfig
    row = db.query(SysConfig).filter(SysConfig.key == key).first()
    if not row:
        row = SysConfig(key=key)
        db.add(row)
    row.value = body.value
    if body.description is not None:
        row.description = body.description
    db.commit()
    return {"ok": True}


@router.post("/config/smtp/test")
def test_smtp(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("system:config")),
):
    from app.core.notifier import send_email
    email = getattr(current_user, "email", None)
    if not email:
        raise HTTPException(400, "当前用户未设置邮箱")
    ok = send_email(email, "SMTP 测试邮件", "<p>SMTP 配置测试成功！</p>")
    if not ok:
        raise HTTPException(500, "邮件发送失败，请检查 SMTP 配置")
    return {"ok": True, "sent_to": email}
