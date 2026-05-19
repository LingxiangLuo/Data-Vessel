from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.core.security import get_current_user, verify_service_token, get_service_user
from app.models.workflow import Workflow
from app.core.permissions import require_permission, check_resource_permission
from app.core.dqc_engine import execute_rule
from app.models.dqc_rule import DqcRule
from app.models.dqc_check import DqcCheck
from app.models.datasource import DataSource
from app.models.user import SysUser

router = APIRouter(prefix="/dqc-rules", tags=["数据质量规则"])


# ===== Schemas =====

class DqcRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    datasource_id: int
    table_name: str = Field(..., min_length=1, max_length=128)
    column_name: Optional[str] = Field(None, max_length=128)
    rule_type: str = Field(..., min_length=1, max_length=32)
    operator: str = Field(..., min_length=1, max_length=16)
    threshold: str = Field(..., min_length=1, max_length=64)
    threshold_max: Optional[str] = Field(None, max_length=64)
    is_strong: bool = False
    enabled: bool = True
    notify_channel_ids: Optional[List[int]] = None
    extra_config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class DqcRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    datasource_id: Optional[int] = None
    table_name: Optional[str] = Field(None, min_length=1, max_length=128)
    column_name: Optional[str] = Field(None, max_length=128)
    rule_type: Optional[str] = Field(None, min_length=1, max_length=32)
    operator: Optional[str] = Field(None, min_length=1, max_length=16)
    threshold: Optional[str] = Field(None, min_length=1, max_length=64)
    threshold_max: Optional[str] = Field(None, max_length=64)
    is_strong: Optional[bool] = None
    enabled: Optional[bool] = None
    notify_channel_ids: Optional[List[int]] = None
    extra_config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


# ===== Helpers =====

def _serialize_rule(r: DqcRule, db: Session) -> dict:
    # 加载数据源名称
    ds_name = None
    if r.datasource_id:
        ds = db.query(DataSource).filter(DataSource.id == r.datasource_id).first()
        ds_name = ds.name if ds else None

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
        "datasource_id": r.datasource_id,
        "datasource_name": ds_name,
        "table_name": r.table_name,
        "column_name": r.column_name,
        "rule_type": r.rule_type,
        "operator": r.operator,
        "threshold": r.threshold,
        "threshold_max": r.threshold_max,
        "is_strong": r.is_strong,
        "enabled": r.enabled,
        "notify_channel_ids": channel_ids,
        "notify_channel_names": channel_names,
        "extra_config": r.extra_config,
        "description": r.description,
        "created_by": r.created_by,
        "created_at": str(r.created_at) if r.created_at else None,
        "updated_at": str(r.updated_at) if r.updated_at else None,
    }


def _get_ds_or_404(db: Session, ds_id: int) -> DataSource:
    ds = db.query(DataSource).filter(DataSource.id == ds_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return ds


async def _send_notifications(db: Session, rule: DqcRule, actual_value: str):
    """规则检查失败后发送通知"""
    channel_ids = getattr(rule, "notify_channel_ids", None) or []
    if not channel_ids:
        return

    from app.models.sys_notify_channel import SysNotifyChannel
    channels = db.query(SysNotifyChannel).filter(SysNotifyChannel.id.in_(channel_ids)).all()

    title = f"⚠️ 数据质量规则异常: {rule.name}"
    content = (
        f"**规则**: {rule.name}\n"
        f"**表**: {rule.table_name}\n"
        f"**字段**: {rule.column_name or '-'}\n"
        f"**规则类型**: {rule.rule_type}\n"
        f"**预期**: {rule.operator} {rule.threshold}{f' ~ {rule.threshold_max}' if rule.threshold_max else ''}\n"
        f"**实际值**: {actual_value or 'NULL'}\n"
        f"**状态**: ❌ 未通过"
    )

    for ch in channels:
        try:
            cfg = ch.config or {}
            if ch.type == "feishu_webhook":
                url = cfg.get("webhook_url", "")
                if url:
                    from app.core.notifier import send_feishu_webhook
                    await send_feishu_webhook(url, title, content)
            elif ch.type == "dingtalk_webhook":
                url = cfg.get("webhook_url", "")
                if url:
                    from app.core.notifier import send_dingtalk_webhook
                    await send_dingtalk_webhook(url, title, content, secret=cfg.get("secret"))
            elif ch.type == "wecom_webhook":
                url = cfg.get("webhook_url", "")
                if url:
                    from app.core.notifier import send_wecom_webhook
                    await send_wecom_webhook(url, title, content)
            elif ch.type == "email":
                emails = cfg.get("email", [])
                if isinstance(emails, str):
                    emails = [emails]
                if emails:
                    import asyncio
                    from app.core.notifier import send_email
                    for email in emails:
                        await asyncio.to_thread(send_email, email, title, content.replace("\n", "<br>"))
        except Exception:
            pass


# ===== CRUD =====

@router.get("")
def list_rules(
    datasource_id: Optional[int] = Query(None),
    table_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """规则列表"""
    q = db.query(DqcRule)
    if datasource_id:
        q = q.filter(DqcRule.datasource_id == datasource_id)
    if table_name:
        q = q.filter(DqcRule.table_name == table_name)
    rules = q.order_by(desc(DqcRule.id)).all()
    return {"items": [_serialize_rule(r, db) for r in rules], "total": len(rules)}


@router.get("/{rule_id}")
def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    r = db.query(DqcRule).filter(DqcRule.id == rule_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="规则不存在")
    return _serialize_rule(r, db)


@router.post("")
def create_rule(
    req: DqcRuleCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("dqc:write")),
):
    _get_ds_or_404(db, req.datasource_id)
    if not check_resource_permission(db, current_user, "datasource", req.datasource_id, "read"):
        raise HTTPException(status_code=404, detail="数据源不存在")
    r = DqcRule(
        name=req.name,
        datasource_id=req.datasource_id,
        table_name=req.table_name,
        column_name=req.column_name,
        rule_type=req.rule_type,
        operator=req.operator,
        threshold=req.threshold,
        threshold_max=req.threshold_max,
        is_strong=req.is_strong,
        enabled=req.enabled,
        notify_channel_ids=req.notify_channel_ids or [],
        extra_config=req.extra_config,
        description=req.description,
        created_by=current_user.id,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return _serialize_rule(r, db)


@router.put("/{rule_id}")
def update_rule(
    rule_id: int,
    req: DqcRuleUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("dqc:write")),
):
    r = db.query(DqcRule).filter(DqcRule.id == rule_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="规则不存在")
    updates = req.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return _serialize_rule(r, db)


@router.delete("/{rule_id}")
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("dqc:write")),
):
    r = db.query(DqcRule).filter(DqcRule.id == rule_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="规则不存在")
    db.delete(r)
    db.commit()
    return {"message": "已删除"}


@router.patch("/{rule_id}/toggle")
def toggle_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("dqc:write")),
):
    r = db.query(DqcRule).filter(DqcRule.id == rule_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="规则不存在")
    r.enabled = not r.enabled
    db.commit()
    db.refresh(r)
    return _serialize_rule(r, db)


def _verify_workflow_service_token(token: str, db: Session) -> bool:
    """验证 per-workflow 服务 token，避免全局 token 泄露到 DS"""
    if not token:
        return False
    wf = db.query(Workflow).filter(Workflow.service_token == token).first()
    return wf is not None


def _resolve_user_or_service(
    request: Request,
    db: Session = Depends(get_db),
) -> SysUser:
    """校验用户 token 或服务 token；服务 token 时返回 system 用户"""
    from app.core.security import _decode_token, is_token_blacklisted
    from app.models.user import SysUser

    svc_token = request.headers.get("X-Service-Token")
    if svc_token:
        # 优先验证 per-workflow token（安全，不泄露全局 token）
        if _verify_workflow_service_token(svc_token, db):
            user = get_service_user(db)
            if user:
                return user
        # 回退到全局 token（向后兼容）
        if verify_service_token(svc_token):
            user = get_service_user(db)
            if user:
                return user

    # 回退到普通用户认证 —— 手动解析 token，不通过 Depends（避免 Depends 对象传入）
    token: Optional[str] = None
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        token = cookie_token
    else:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(status_code=401, detail="未登录")

    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="认证已失效")

    username = _decode_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="无效的认证凭据")

    user = db.query(SysUser).filter(SysUser.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


# ===== Execution =====

@router.post("/{rule_id}/check")
async def run_check(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(_resolve_user_or_service),
):
    """手动触发质量检查（支持服务间调用）"""
    # 如果是普通用户，校验 dqc:write 权限
    if current_user.username != "system":
        if not check_resource_permission(db, current_user, "dqc", rule_id, "write"):
            raise HTTPException(status_code=403, detail="无权限执行质量检查")

    rule = db.query(DqcRule).filter(DqcRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    ds = _get_ds_or_404(db, rule.datasource_id)
    # 服务调用跳过数据源 ACL（服务 token 已代表系统授权）
    if current_user.username != "system":
        if not check_resource_permission(db, current_user, "datasource", rule.datasource_id, "read"):
            raise HTTPException(status_code=404, detail="数据源不存在")

    result = execute_rule(rule, ds)

    # 保存检查记录
    check = DqcCheck(
        rule_id=rule.id,
        actual_value=result.get("actual_value"),
        expected_value=f"{rule.operator} {rule.threshold}{f' ~ {rule.threshold_max}' if rule.threshold_max else ''}",
        passed=result["passed"],
        error_msg=result.get("error_msg"),
    )
    db.add(check)
    db.commit()
    db.refresh(check)

    # 发送通知（仅失败时）
    if not result["passed"]:
        await _send_notifications(db, rule, result.get("actual_value"))

    return {
        "actual_value": result.get("actual_value"),
        "passed": result["passed"],
        "error_msg": result.get("error_msg"),
        "check_id": check.id,
    }


# ===== History =====

@router.get("/{rule_id}/history")
def rule_history(
    rule_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """单个规则的检查历史"""
    checks = (
        db.query(DqcCheck)
        .filter(DqcCheck.rule_id == rule_id)
        .order_by(desc(DqcCheck.id))
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "id": c.id,
                "rule_id": c.rule_id,
                "actual_value": c.actual_value,
                "expected_value": c.expected_value,
                "passed": c.passed,
                "error_msg": c.error_msg,
                "checked_at": str(c.checked_at) if c.checked_at else None,
            }
            for c in checks
        ],
        "total": len(checks),
    }


@router.get("/checks/all")
def list_checks(
    rule_id: Optional[int] = Query(None),
    passed: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """全局检查记录列表"""
    q = db.query(DqcCheck)
    if rule_id:
        q = q.filter(DqcCheck.rule_id == rule_id)
    if passed is not None:
        q = q.filter(DqcCheck.passed == passed)
    checks = q.order_by(desc(DqcCheck.id)).limit(limit).all()
    return {
        "items": [
            {
                "id": c.id,
                "rule_id": c.rule_id,
                "actual_value": c.actual_value,
                "expected_value": c.expected_value,
                "passed": c.passed,
                "error_msg": c.error_msg,
                "checked_at": str(c.checked_at) if c.checked_at else None,
            }
            for c in checks
        ],
        "total": len(checks),
    }


@router.get("/checks/stats")
def check_stats(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """质量大盘统计"""
    from datetime import datetime, timedelta
    since = datetime.now() - timedelta(days=days)

    total = db.query(DqcCheck).filter(DqcCheck.checked_at >= since).count()
    passed = db.query(DqcCheck).filter(DqcCheck.checked_at >= since, DqcCheck.passed == True).count()
    failed = total - passed

    # TOP 问题表（按失败次数）
    from sqlalchemy import func as sa_func
    top_failed = (
        db.query(DqcRule.table_name, sa_func.count(DqcCheck.id).label("cnt"))
        .join(DqcCheck, DqcRule.id == DqcCheck.rule_id)
        .filter(DqcCheck.checked_at >= since, DqcCheck.passed == False)
        .group_by(DqcRule.table_name)
        .order_by(desc("cnt"))
        .limit(10)
        .all()
    )

    # 每日趋势
    from sqlalchemy import case
    daily = (
        db.query(
            sa_func.date(DqcCheck.checked_at).label("day"),
            sa_func.count(DqcCheck.id).label("total"),
            sa_func.sum(case((DqcCheck.passed == True, 1), else_=0)).label("passed"),
        )
        .filter(DqcCheck.checked_at >= since)
        .group_by(sa_func.date(DqcCheck.checked_at))
        .order_by("day")
        .all()
    )

    return {
        "summary": {"total": total, "passed": passed, "failed": failed},
        "top_failed_tables": [{"table": t.table_name, "failed_count": t.cnt} for t in top_failed],
        "daily_trend": [
            {"day": str(d.day), "total": d.total, "passed": d.passed or 0, "failed": d.total - (d.passed or 0)}
            for d in daily
        ],
    }
