"""SyncTask API（兼容端点，已废弃）

所有业务逻辑已迁移到 Component API。保留 /sync-tasks/preview 和 /sync-tasks/test-connection
供外部兼容调用，内部委托给 Component 的新端点。
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import SysUser

router = APIRouter(prefix="/sync-tasks", tags=["同步任务(已废弃)"])


class FieldMapping(BaseModel):
    kind: Optional[str] = "column"
    src: str
    dst: str
    type: Optional[str] = None


class DataXPreviewRequest(BaseModel):
    source_id: int
    target_id: int
    source_table: str
    target_table: str
    sync_type: str = "full"
    increment_column: Optional[str] = None
    field_mapping: Optional[List[FieldMapping]] = None
    where_clause: Optional[str] = None
    split_pk: Optional[str] = None
    write_mode: Optional[str] = "insert"
    channel: Optional[int] = 3
    pre_sql: Optional[List[str]] = None
    post_sql: Optional[List[str]] = None


class TestConnectionRequest(BaseModel):
    datasource_id: int
    table: Optional[str] = None


@router.post("/preview")
def preview_unsaved(
    req: DataXPreviewRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """兼容端点：委托给 /components/preview-datax"""
    from app.core.datax_builder import build_datax_job
    from app.models.datasource import DataSource

    src = db.query(DataSource).filter(DataSource.id == req.source_id).first()
    dst = db.query(DataSource).filter(DataSource.id == req.target_id).first()
    if not src or not dst:
        raise HTTPException(status_code=400, detail="数据源不存在")
    try:
        job = build_datax_job(
            source_ds=src,
            source_table=req.source_table,
            target_ds=dst,
            target_table=req.target_table,
            field_mapping=[m.model_dump() for m in (req.field_mapping or [])],
            sync_type=req.sync_type,
            increment_column=req.increment_column,
            where_clause=req.where_clause,
            split_pk=req.split_pk,
            write_mode=req.write_mode or "insert",
            channel=req.channel or 3,
            pre_sql=req.pre_sql,
            post_sql=req.post_sql,
            mask_password=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"datax": job}


@router.post("/test-connection")
def test_connection(
    req: TestConnectionRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """测试数据源连接 & 表存在性"""
    from app.models.datasource import DataSource
    ds = db.query(DataSource).filter(DataSource.id == req.datasource_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")
    from app.core.db_adapter import test_connection as adapter_test
    ok, msg = adapter_test(ds, table=req.table)
    return {"ok": ok, "message": msg}
