from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_permission
from app.core.notifier import notify, send_feishu_webhook, send_dingtalk_webhook, send_wecom_webhook, send_email, test_channel
from app.models.alert_rule import AlertRule
from app.models.workflow import Workflow
from app.models.user import SysUser

router = APIRouter(prefix="/alert-rules", tags=["监控规则"])


# ===== Schemas =====
class AlertRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    target_type: str = Field(default="all")  # all / workflow
    target_id: Optional[int] = None
    trigger_type: str  # failure / timeout / consecutive_failure
    trigger_value: Optional[int] = None
    notify_type: Optional[str] = None  # 旧字段兼容，新规则可为空
    notify_config: Optional[dict] = None  # 旧字段兼容
    notify_channel_ids: Optional[List[int]] = None  # 新字段，引用 sys_notify_channel
    enabled: bool = True


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    trigger_type: Optional[str] = None
    trigger_value: Optional[int] = None
    notify_type: Optional[str] = None
    notify_config: Optional[dict] = None
    notify_channel_ids: Optional[List[int]] = None
    enabled: Optional[bool] = None


class TestNotifyReq(BaseModel):
    notify_type: Optional[str] = None
    notify_config: Optional[dict] = None
    channel_id: Optional[int] = None  # 测试指定渠道
    channel_ids: Optional[List[int]] = None  # 批量测试


def _serialize(r: AlertRule, db: Session) -> dict:
    target_name = None
    if r.target_type == "workflow" and r.target_id:
        w = db.query(Workflow).filter(Workflow.id == r.target_id).first()
        target_name = w.name if w else f"工作流#{r.target_id}"

    # 加载渠道名称
    channel_ids = getattr(r, "notify_channel_ids", None) or []
    channel_names = []
    if channel_ids:
        try:
            from app.models.sys_notify_channel import SysNotifyChannel
            channels = db.query(SysNotifyChannel.name).filter(
                SysNotifyChannel.id.in_(channel_ids)
            ).all()
            channel_names = [c.name for c in channels]
        except Exception:
            pass

    return {
        "id": r.id,
        "name": r.name,
        "target_type": r.target_type,
        "target_id": r.target_id,
        "target_name": target_name,
        "trigger_type": r.trigger_type,
        "trigger_value": r.trigger_value,
        "notify_type": r.notify_type,
        "notify_config": r.notify_config,
        "notify_channel_ids": channel_ids,
        "notify_channel_names": channel_names,
        "enabled": r.enabled,
        "created_at": str(r.created_at) if r.created_at else None,
        "updated_at": str(r.updated_at) if r.updated_at else None,
    }


# ===== CRUD =====
@router.get("")
def list_rules(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    rules = db.query(AlertRule).order_by(AlertRule.id.desc()).all()
    return {"items": [_serialize(r, db) for r in rules], "total": len(rules)}


@router.post("")
def create_rule(
    req: AlertRuleCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("monitor:write")),
):
    r = AlertRule(
        name=req.name,
        target_type=req.target_type,
        target_id=req.target_id,
        trigger_type=req.trigger_type,
        trigger_value=req.trigger_value,
        notify_type=req.notify_type or (req.notify_config.get("type") if req.notify_config else ""),
        notify_config=req.notify_config or {},
        notify_channel_ids=req.notify_channel_ids or [],
        enabled=req.enabled,
        created_by=current_user.id,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return _serialize(r, db)


@router.put("/{rule_id}")
def update_rule(
    rule_id: int,
    req: AlertRuleUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("monitor:write")),
):
    r = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not r:
        raise HTTPException(404, "规则不存在")
    updates = req.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return _serialize(r, db)


@router.delete("/{rule_id}")
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("monitor:write")),
):
    r = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not r:
        raise HTTPException(404, "规则不存在")
    db.delete(r)
    db.commit()
    return {"message": "已删除"}


@router.patch("/{rule_id}/toggle")
def toggle_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("monitor:write")),
):
    r = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not r:
        raise HTTPException(404, "规则不存在")
    r.enabled = not r.enabled
    db.commit()
    db.refresh(r)
    return _serialize(r, db)


@router.post("/test-notify")
async def test_notify(
    req: TestNotifyReq,
    current_user: SysUser = Depends(get_current_user),
):
    """测试通知渠道是否可达"""
    title = "🔔 测试通知"
    content = "这是一条测试消息，如果你收到了说明通知配置正确。"

    # 优先：测试指定渠道
    if req.channel_id:
        ok = await test_channel(req.channel_id)
        if not ok:
            raise HTTPException(502, "通知发送失败，请检查渠道配置")
        return {"message": "测试通知已发送"}

    if req.channel_ids:
        results = []
        for cid in req.channel_ids:
            ok = await test_channel(cid)
            results.append({"channel_id": cid, "ok": ok})
        return {"results": results}

    # 降级：旧方式（直接填 type + config）
    if not req.notify_type or not req.notify_config:
        raise HTTPException(400, "请提供 notify_type 和 notify_config，或指定 channel_id")

    if req.notify_type == "feishu_webhook":
        url = req.notify_config.get("webhook_url", "")
        if not url:
            raise HTTPException(400, "webhook_url 不能为空")
        ok = await send_feishu_webhook(url, title, content)
    elif req.notify_type == "dingtalk_webhook":
        url = req.notify_config.get("webhook_url", "")
        if not url:
            raise HTTPException(400, "webhook_url 不能为空")
        ok = await send_dingtalk_webhook(url, title, content, secret=req.notify_config.get("secret"))
    elif req.notify_type == "wecom_webhook":
        url = req.notify_config.get("webhook_url", "")
        if not url:
            raise HTTPException(400, "webhook_url 不能为空")
        ok = await send_wecom_webhook(url, title, content)
    elif req.notify_type == "email":
        email = req.notify_config.get("email", "")
        if not email:
            raise HTTPException(400, "email 不能为空")
        ok = send_email(email, title, content.replace("\n", "<br>"))
    else:
        raise HTTPException(400, f"不支持的通知类型: {req.notify_type}")

    if not ok:
        raise HTTPException(502, "通知发送失败，请检查配置")
    return {"message": "测试通知已发送"}
