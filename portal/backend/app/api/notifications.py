"""通知 API — Webhook 接收 + 前端查询"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.notification import Notification
from app.models.user import SysUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["通知"])


class NotificationCreate(BaseModel):
    type: str = "info"
    title: str
    content: Optional[str] = None
    source: str = "portal"


@router.get("")
def list_notifications(
    pageNo: int = 1,
    pageSize: int = 20,
    is_read: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    query = db.query(Notification)
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    total = query.count()
    items = query.order_by(desc(Notification.created_at)).offset((pageNo - 1) * pageSize).limit(pageSize).all()
    return {
        "list": [_to_dict(n) for n in items],
        "total": total,
        "unread": db.query(func.count(Notification.id)).filter(Notification.is_read == False).scalar() or 0,
    }


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    count = db.query(func.count(Notification.id)).filter(Notification.is_read == False).scalar() or 0
    return {"count": count}


@router.put("/{notif_id}/read")
def mark_read(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    n = db.query(Notification).filter(Notification.id == notif_id).first()
    if not n:
        raise HTTPException(404, "通知不存在")
    n.is_read = True
    db.commit()
    return {"msg": "ok"}


@router.put("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    db.query(Notification).filter(Notification.is_read == False).update({"is_read": True})
    db.commit()
    return {"msg": "ok"}


@router.post("/ds-webhook")
async def ds_webhook(request: Request, db: Session = Depends(get_db)):
    """DS 告警 Webhook 回调接收（无需认证）"""
    try:
        body = await request.json()
        logger.info("DS webhook received: %s", body)

        title = body.get("title", "DolphinScheduler 告警")
        content = body.get("content", "")
        alert_type = "alert"

        # DS webhook 格式可能是多种，尝试通用解析
        if isinstance(body, dict):
            if "msg" in body:
                title = body.get("title", title)
                content = body.get("msg", content)
            if "alertType" in body:
                alert_type = "alert" if body["alertType"] in ("FAILURE", "WARN") else "info"

        n = Notification(type=alert_type, title=title, content=content, source="ds")
        db.add(n)
        db.commit()
        return {"msg": "ok"}
    except Exception as e:
        logger.error("DS webhook error: %s", e)
        raise HTTPException(400, "Invalid webhook payload")


@router.post("")
def create_notification(
    data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    n = Notification(type=data.type, title=data.title, content=data.content, source=data.source)
    db.add(n)
    db.commit()
    return _to_dict(n)


def _to_dict(n: Notification) -> dict:
    return {
        "id": n.id,
        "type": n.type,
        "title": n.title,
        "content": n.content,
        "source": n.source,
        "is_read": n.is_read,
        "created_at": str(n.created_at) if n.created_at else None,
    }
