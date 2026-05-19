from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permissions import get_accessible_ids, check_resource_permission, require_permission
from app.core.encrypt import encrypt_password
from app.models.datasource import DataSource
from app.models.user import SysUser

router = APIRouter(prefix="/datasources", tags=["数据源"])

_SUPPORTED_DS_TYPES = {
    "mysql", "postgresql", "sqlserver", "oracle",
    "clickhouse", "mongodb", "redis", "hive",
}


class DataSourceCreate(BaseModel):
    name: str
    type: str  # mysql / postgresql / sqlserver / oracle / clickhouse / mongodb / redis / hive
    host: str
    port: int
    database_name: str
    username: Optional[str] = None
    password: Optional[str] = None
    description: Optional[str] = None

    @field_validator("type")
    @classmethod
    def _check_type(cls, v: str) -> str:
        if v.lower() not in _SUPPORTED_DS_TYPES:
            raise ValueError(f"不支持的数据源类型: {v}，允许: {', '.join(sorted(_SUPPORTED_DS_TYPES))}")
        return v.lower()


class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    description: Optional[str] = None


def _serialize(ds: DataSource) -> dict:
    return {
        "id": ds.id,
        "name": ds.name,
        "type": ds.type,
        "host": ds.host,
        "port": ds.port,
        "database_name": ds.database_name,
        "username": ds.username[0] + "****" if ds.username and len(ds.username) > 1 else ("****" if ds.username else ""),
        "description": ds.description,
        "status": ds.status,
        "last_check_time": str(ds.last_check_time) if ds.last_check_time else None,
        "created_at": str(ds.created_at) if ds.created_at else None,
    }


@router.get("")
def list_datasources(
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    query = db.query(DataSource)
    if keyword:
        query = query.filter(DataSource.name.contains(keyword))

    # 资源级 ACL 过滤
    accessible = get_accessible_ids(db, current_user, "datasource", "read")
    if accessible is not None:
        query = query.filter(DataSource.id.in_(accessible)) if accessible else query.filter(False)

    total = query.count()
    items = query.order_by(DataSource.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "items": [_serialize(ds) for ds in items]}


@router.post("")
def create_datasource(
    req: DataSourceCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("datasource:write")),
):
    data = req.model_dump()
    # 空密码也加密（存储空字符串的加密值），避免前端绕过
    if "password" in data:
        data["password"] = encrypt_password(data["password"] or "")
    ds = DataSource(**data, created_by=current_user.id)
    db.add(ds)
    db.flush()  # 获取 ds.id

    # 自动授予创建者 admin 权限
    from app.models.resource_access import SysResourceAccess
    db.add(SysResourceAccess(
        resource_type="datasource",
        resource_id=ds.id,
        subject_type="user",
        subject_id=current_user.id,
        permission="admin",
        granted_by=current_user.id,
    ))

    db.commit()
    db.refresh(ds)
    return _serialize(ds)


@router.get("/{ds_id}")
def get_datasource(
    ds_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    ds = db.query(DataSource).filter(DataSource.id == ds_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")
    if not check_resource_permission(db, current_user, "datasource", ds_id, "read"):
        raise HTTPException(status_code=404, detail="数据源不存在")
    return _serialize(ds)


@router.put("/{ds_id}")
def update_datasource(
    ds_id: int,
    req: DataSourceUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("datasource:write")),
):
    ds = db.query(DataSource).filter(DataSource.id == ds_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")
    if not check_resource_permission(db, current_user, "datasource", ds_id, "write"):
        raise HTTPException(status_code=404, detail="数据源不存在")
    for key, value in req.model_dump(exclude_unset=True).items():
        if key == "password":
            value = encrypt_password(value or "")
        setattr(ds, key, value)
    db.commit()
    db.refresh(ds)
    return _serialize(ds)


@router.delete("/{ds_id}")
def delete_datasource(
    ds_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("datasource:write")),
):
    ds = db.query(DataSource).filter(DataSource.id == ds_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")
    if not check_resource_permission(db, current_user, "datasource", ds_id, "admin"):
        raise HTTPException(status_code=404, detail="数据源不存在")
    # 检查是否被引用
    from app.models.component import Component
    from app.models.sync_task import SyncTask

    # 组件引用（config_json 中的 datasource_id / source_id / target_id）
    for comp in db.query(Component).filter(Component.config_json.isnot(None)).all():
        cfg = comp.config_json or {}
        if cfg.get("datasource_id") == ds_id or cfg.get("source_id") == ds_id or cfg.get("target_id") == ds_id:
            raise HTTPException(
                status_code=400,
                detail=f"数据源被组件「{comp.name}」引用，请先解除引用",
            )

    # 同步任务引用
    sync_ref = (
        db.query(SyncTask)
        .filter((SyncTask.source_id == ds_id) | (SyncTask.target_id == ds_id))
        .first()
    )
    if sync_ref:
        raise HTTPException(
            status_code=400,
            detail=f"数据源被同步任务「{sync_ref.name}」引用，请先解除引用",
        )

    # 清理 ACL 记录
    from app.models.resource_access import SysResourceAccess
    db.query(SysResourceAccess).filter(
        SysResourceAccess.resource_type == "datasource",
        SysResourceAccess.resource_id == ds_id,
    ).delete()
    db.delete(ds)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{ds_id}/test")
def test_connection(
    ds_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    ds = db.query(DataSource).filter(DataSource.id == ds_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")
    if not check_resource_permission(db, current_user, "datasource", ds_id, "read"):
        raise HTTPException(status_code=404, detail="数据源不存在")

    from app.core.db_adapter import test_connection as adapter_test
    ok, msg = adapter_test(ds)
    ds.status = 1 if ok else 0
    db.commit()
    return {"message": msg, "status": ds.status}
