"""数据质量报告 API"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_permission
from app.core.dqc_report_generator import generate_report
from app.models.dqc_report import DqcReport, DqcReportHistory
from app.models.user import SysUser

router = APIRouter(prefix="/dqc-reports", tags=["数据质量报告"])


class ReportCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    rule_ids: Optional[List[int]] = None
    period_type: str = Field(default="daily")
    subscribers: Optional[List[Dict[str, Any]]] = None

    @field_validator("period_type")
    @classmethod
    def _check_period(cls, v: str) -> str:
        if v not in ("daily", "weekly"):
            raise ValueError("period_type 必须是 daily 或 weekly")
        return v


class ReportUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    rule_ids: Optional[List[int]] = None
    period_type: Optional[str] = None
    subscribers: Optional[List[Dict[str, Any]]] = None
    enabled: Optional[bool] = None


@router.get("")
def list_reports(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    items = db.query(DqcReport).order_by(DqcReport.id.desc()).all()
    return {
        "items": [
            {
                "id": r.id,
                "name": r.name,
                "period_type": r.period_type,
                "enabled": r.enabled,
                "last_sent_at": str(r.last_sent_at) if r.last_sent_at else None,
                "created_at": str(r.created_at) if r.created_at else None,
            }
            for r in items
        ],
        "total": len(items),
    }


@router.post("")
def create_report(
    req: ReportCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("dqc:write")),
):
    r = DqcReport(
        name=req.name,
        rule_ids=req.rule_ids,
        period_type=req.period_type,
        subscribers=req.subscribers or [],
        created_by=current_user.id,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return {"id": r.id, "name": r.name, "period_type": r.period_type, "enabled": r.enabled}


@router.get("/{report_id}")
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    r = db.query(DqcReport).filter(DqcReport.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="报告不存在")
    return {
        "id": r.id,
        "name": r.name,
        "rule_ids": r.rule_ids,
        "period_type": r.period_type,
        "subscribers": r.subscribers,
        "enabled": r.enabled,
        "last_sent_at": str(r.last_sent_at) if r.last_sent_at else None,
        "created_at": str(r.created_at) if r.created_at else None,
    }


@router.put("/{report_id}")
def update_report(
    report_id: int,
    req: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("dqc:write")),
):
    r = db.query(DqcReport).filter(DqcReport.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="报告不存在")
    updates = req.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return {"id": r.id, "name": r.name, "enabled": r.enabled}


@router.delete("/{report_id}")
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("dqc:write")),
):
    r = db.query(DqcReport).filter(DqcReport.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="报告不存在")
    db.delete(r)
    db.commit()
    return {"message": "已删除"}


@router.post("/{report_id}/preview")
def preview_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """预览报告内容（即时生成，不保存历史）"""
    r = db.query(DqcReport).filter(DqcReport.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="报告不存在")
    data = generate_report(db, rule_ids=r.rule_ids, period_type=r.period_type)
    return data


@router.get("/{report_id}/history")
def report_history(
    report_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    rows = (
        db.query(DqcReportHistory)
        .filter(DqcReportHistory.report_id == report_id)
        .order_by(DqcReportHistory.id.desc())
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "id": h.id,
                "period_start": str(h.period_start) if h.period_start else None,
                "period_end": str(h.period_end) if h.period_end else None,
                "status": h.status,
                "sent_at": str(h.sent_at) if h.sent_at else None,
            }
            for h in rows
        ],
        "total": len(rows),
    }
