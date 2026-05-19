import time
import subprocess
import tempfile
import os
import re
from typing import Optional, Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_permission, check_resource_permission
from app.models.component import Component, ComponentHistory
from app.models.user import SysUser

router = APIRouter(prefix="/components", tags=["组件"])

# ===== 类型与状态常量 =====
VALID_TYPES = {"sql", "python", "shell", "datax"}

# 状态定义
STATUS_DRAFT = "draft"
STATUS_DEVELOPING = "developing"
STATUS_TESTING = "testing"
STATUS_REVIEWING = "reviewing"
STATUS_TESTED = "tested"
STATUS_ONLINE = "online"
STATUS_OFFLINE = "offline"
STATUS_PAUSED = "paused"
STATUS_DEPRECATED = "deprecated"
STATUS_ARCHIVED = "archived"

# 所有有效状态
VALID_STATUSES = {
    STATUS_DRAFT, STATUS_DEVELOPING, STATUS_TESTING,
    STATUS_REVIEWING, STATUS_TESTED, STATUS_ONLINE,
    STATUS_OFFLINE, STATUS_PAUSED, STATUS_DEPRECATED, STATUS_ARCHIVED,
}

# 用户可手动设置的状态（不包括自动状态 draft/online）
MANUAL_STATUSES = {
    STATUS_DEVELOPING, STATUS_TESTING, STATUS_REVIEWING,
    STATUS_TESTED, STATUS_OFFLINE, STATUS_PAUSED,
    STATUS_DEPRECATED, STATUS_ARCHIVED,
}

# 自动流转状态
AUTO_STATUSES = {STATUS_DRAFT, STATUS_ONLINE}

# 允许编辑/删除的状态
EDITABLE_STATUSES = {STATUS_DRAFT, STATUS_DEVELOPING, STATUS_TESTING, STATUS_REVIEWING, STATUS_TESTED, STATUS_OFFLINE, STATUS_PAUSED, STATUS_DEPRECATED}
DELETABLE_STATUSES = {STATUS_DRAFT, STATUS_OFFLINE, STATUS_DEPRECATED, STATUS_ARCHIVED}

# 状态显示名
STATUS_LABELS = {
    STATUS_DRAFT: "草稿",
    STATUS_DEVELOPING: "开发中",
    STATUS_TESTING: "测试中",
    STATUS_REVIEWING: "审核中",
    STATUS_TESTED: "已测试",
    STATUS_ONLINE: "已上线",
    STATUS_OFFLINE: "已下线",
    STATUS_PAUSED: "已暂停",
    STATUS_DEPRECATED: "已废弃",
    STATUS_ARCHIVED: "已归档",
}

# 状态颜色
STATUS_COLORS = {
    STATUS_DRAFT: "#86909C",
    STATUS_DEVELOPING: "#2B5AED",
    STATUS_TESTING: "#FF7D00",
    STATUS_REVIEWING: "#14B8A6",
    STATUS_TESTED: "#A3C644",
    STATUS_ONLINE: "#00B42A",
    STATUS_OFFLINE: "#C9CDD4",
    STATUS_PAUSED: "#F53F3F",
    STATUS_DEPRECATED: "#6B7280",
    STATUS_ARCHIVED: "#722ED1",
}

# 状态流转规则: {当前状态: [允许的目标状态]}
STATUS_TRANSITIONS = {
    STATUS_DRAFT: [STATUS_DEVELOPING, STATUS_TESTING, STATUS_DEPRECATED, STATUS_ARCHIVED],
    STATUS_DEVELOPING: [STATUS_TESTING, STATUS_PAUSED, STATUS_DEPRECATED],
    STATUS_TESTING: [STATUS_REVIEWING, STATUS_TESTED, STATUS_PAUSED, STATUS_DEPRECATED],
    STATUS_REVIEWING: [STATUS_TESTED, STATUS_PAUSED, STATUS_DEVELOPING],
    STATUS_TESTED: [STATUS_ONLINE, STATUS_PAUSED, STATUS_TESTING],  # online 通过发布操作
    STATUS_ONLINE: [STATUS_OFFLINE, STATUS_PAUSED],
    STATUS_OFFLINE: [STATUS_ONLINE, STATUS_ARCHIVED, STATUS_PAUSED, STATUS_DEVELOPING],
    STATUS_PAUSED: [],  # 恢复时回到 previous_status，不走 transitions
    STATUS_DEPRECATED: [STATUS_ARCHIVED],
    STATUS_ARCHIVED: [],  # 归档后不可修改
}


# ===== Schemas =====
class ComponentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: str
    description: Optional[str] = None
    config_json: Dict[str, Any] = Field(default_factory=dict)
    params: Optional[List[Dict[str, Any]]] = Field(default=None)
    folder_id: Optional[int] = None
    dqc_rule_ids: Optional[List[int]] = None
    # 便捷字段：IDE 直接传 code + datasource_id，后端合并进 config_json
    code: Optional[str] = None
    datasource_id: Optional[int] = None


class ComponentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = None
    params: Optional[List[Dict[str, Any]]] = None
    folder_id: Optional[int] = None
    dqc_rule_ids: Optional[List[int]] = None
    code: Optional[str] = None
    datasource_id: Optional[int] = None


class RunComponentRequest(BaseModel):
    runtime_params: Optional[Dict[str, str]] = None


class RunSqlRequest(BaseModel):
    datasource_id: int
    sql: str


def _json_val(v):
    if v is None or isinstance(v, (int, float, bool, str)):
        return v
    return str(v)


def _serialize(c: Component, user_map: dict = None) -> dict:
    status = c.status
    cfg = c.config_json or {}
    s = {
        "id": c.id,
        "name": c.name,
        "type": c.type,
        "description": c.description,
        "config_json": cfg,
        "version": c.version,
        "status": status,
        "status_label": STATUS_LABELS.get(status, status),
        "status_color": STATUS_COLORS.get(status, "#86909C"),
        "ds_task_code": c.ds_task_code,
        "folder_id": c.folder_id if hasattr(c, 'folder_id') else None,
        "sort_order": c.sort_order if hasattr(c, 'sort_order') else 0,
        "code": cfg.get({'sql': 'sql', 'python': 'script', 'shell': 'script', 'datax': 'script'}.get(c.type, 'sql'), '') or '',
        "datasource_id": cfg.get('datasource_id'),
        "created_by": c.created_by,
        "created_by_name": user_map.get(c.created_by).username if user_map and c.created_by and user_map.get(c.created_by) else None,
        "previous_status": c.previous_status,
        "dqc_rule_ids": c.dqc_rule_ids or [],
        "params": c.params or [],
        "created_at": str(c.created_at) if c.created_at else None,
        "updated_at": str(c.updated_at) if c.updated_at else None,
    }
    return s


def _get_or_404(db: Session, comp_id: int) -> Component:
    c = db.query(Component).filter(Component.id == comp_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="组件不存在")
    return c


def _save_history(db: Session, c: Component, comment: str = None):
    """保存组件当前状态到历史快照表"""
    hist = ComponentHistory(
        component_id=c.id,
        version=c.version or 1,
        name=c.name,
        type=c.type,
        description=c.description,
        config_json=c.config_json or {},
        params=c.params or [],
        status=c.status,
        created_by=c.created_by,
        comment=comment,
    )
    db.add(hist)
def _check_workflow_refs(db: Session, comp_id: int):
    """检查组件是否被工作流引用，若有则抛出 400"""
    from app.models.workflow import Workflow
    refs = db.query(Workflow.name).filter(
        Workflow.steps_json.contains(f'"component_id": {comp_id}'),
        Workflow.status.notin_(["offline", "archived"]),
    ).all()
    if refs:
        names = "、".join(r.name for r in refs[:5])
        raise HTTPException(
            status_code=400,
            detail=f"组件被以下工作流引用，请先下线相关工作流：{names}",
        )




def _run_sql(db: Session, datasource_id: int, sql: str):
    """复用的 SQL 执行逻辑，返回 dict。仅允许只读 SELECT。"""
    from app.models.datasource import DataSource
    import sqlalchemy as sa

    # 只允许 SELECT 语句，禁止 DDL/DML
    stripped = sql.strip().upper()
    if not stripped.startswith("SELECT"):
        raise HTTPException(400, "仅允许 SELECT 查询语句")
    # 禁止多语句（分号）
    if ";" in sql:
        raise HTTPException(400, "不允许包含分号")

    ds = db.query(DataSource).filter(DataSource.id == datasource_id).first()
    if not ds:
        raise HTTPException(404, "数据源不存在")

    from app.core.db_adapter import sqlalchemy_url
    url = sqlalchemy_url(ds)
    connect_args = {"connect_timeout": 10} if (ds.type or "").lower() in ("mysql", "postgresql") else {}
    engine = sa.create_engine(url, pool_pre_ping=True, connect_args=connect_args)
    start = time.time()
    try:
        with engine.connect() as conn:
            res = conn.execute(sa.text(sql))
            duration_ms = int((time.time() - start) * 1000)
            if res.returns_rows:
                columns = list(res.keys())
                rows = [[_json_val(v) for v in row] for row in res.fetchmany(2000)]
                return {
                    "type": "table",
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "duration_ms": duration_ms,
                }
            else:
                conn.commit()
                return {
                    "type": "rowcount",
                    "affected": res.rowcount,
                    "duration_ms": duration_ms,
                }
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"SQL 执行失败: {e}", exc_info=True)
        raise HTTPException(400, "SQL 执行失败，请检查语法或数据源配置")
    finally:
        engine.dispose()


# ===== CRUD =====
@router.get("")
def list_components(
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    q = db.query(Component)
    if keyword:
        q = q.filter(Component.name.contains(keyword))
    if type:
        q = q.filter(Component.type == type)
    if status:
        q = q.filter(Component.status == status)
    total = q.count()
    items = q.order_by(Component.sort_order.asc(), Component.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    user_ids = {c.created_by for c in items if c.created_by}
    user_map = {}
    if user_ids:
        user_map = {u.id: u for u in db.query(SysUser).filter(SysUser.id.in_(user_ids)).all()}
    return {"total": total, "items": [_serialize(c, user_map) for c in items]}


@router.post("")
def create_component(
    req: ComponentCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    if req.type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"非法组件类型,允许:{','.join(sorted(VALID_TYPES))}")
    cfg = dict(req.config_json or {})
    if req.code is not None:
        key = 'sql' if req.type == 'sql' else 'script'
        cfg[key] = req.code
    if req.datasource_id is not None:
        cfg['datasource_id'] = req.datasource_id
    # datax 类型必填字段校验
    if req.type == "datax":
        missing = []
        for key in ("source_id", "target_id", "source_table", "target_table"):
            if not cfg.get(key):
                missing.append(key)
        if missing:
            raise HTTPException(status_code=400, detail=f"datax 组件缺少必填字段: {', '.join(missing)}")
    c = Component(
        name=req.name,
        type=req.type,
        description=req.description,
        config_json=cfg,
        params=req.params or [],
        folder_id=req.folder_id,
        dqc_rule_ids=req.dqc_rule_ids or [],
        status=STATUS_DRAFT,
        version=1,
        created_by=current_user.id,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _serialize(c)


# ===== 文件夹 CRUD（必须在 /{comp_id} 之前定义，避免路由冲突）=====
from app.models.component_folder import ComponentFolder


class FolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: str
    parent_id: Optional[int] = None


class FolderRename(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


def _folder_depth(db: Session, parent_id: Optional[int]) -> int:
    depth = 0
    pid = parent_id
    while pid is not None and depth < 3:
        f = db.query(ComponentFolder).filter(ComponentFolder.id == pid).first()
        if not f:
            break
        pid = f.parent_id
        depth += 1
    return depth


@router.get("/folders")
def list_folders(
    folder_type: Optional[str] = Query(None, alias="type"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    q = db.query(ComponentFolder)
    if folder_type:
        q = q.filter(ComponentFolder.type == folder_type)
    items = q.order_by(ComponentFolder.sort_order.asc(), ComponentFolder.id.asc()).all()
    return [{"id": f.id, "name": f.name, "type": f.type, "parent_id": f.parent_id, "sort_order": f.sort_order} for f in items]


@router.post("/folders")
def create_folder(
    req: FolderCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    if req.parent_id is not None:
        parent = db.query(ComponentFolder).filter(ComponentFolder.id == req.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="父文件夹不存在")
        depth = _folder_depth(db, req.parent_id)
        if depth >= 2:
            raise HTTPException(status_code=400, detail="最多支持 3 层嵌套")
    f = ComponentFolder(name=req.name, type=req.type, parent_id=req.parent_id)
    db.add(f)
    db.commit()
    db.refresh(f)
    return {"id": f.id, "name": f.name, "type": f.type, "parent_id": f.parent_id}


@router.put("/folders/{folder_id}")
def rename_folder(
    folder_id: int,
    req: FolderRename,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    f = db.query(ComponentFolder).filter(ComponentFolder.id == folder_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    f.name = req.name
    db.commit()
    return {"id": f.id, "name": f.name, "type": f.type, "parent_id": f.parent_id}


@router.delete("/folders/{folder_id}")
def delete_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    if db.query(ComponentFolder).filter(ComponentFolder.parent_id == folder_id).first():
        raise HTTPException(status_code=400, detail="请先删除子文件夹")
    if db.query(Component).filter(Component.folder_id == folder_id).first():
        raise HTTPException(status_code=400, detail="请先移走文件夹内的组件")
    f = db.query(ComponentFolder).filter(ComponentFolder.id == folder_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    db.delete(f)
    db.commit()
    return {"ok": True}


class DataXPreviewRequest(BaseModel):
    source_id: int
    target_id: int
    source_table: str
    target_table: str
    sync_type: str = "full"
    increment_column: Optional[str] = None
    field_mapping: list = []
    where_clause: Optional[str] = None
    split_pk: Optional[str] = None
    write_mode: Optional[str] = "insert"
    channel: Optional[int] = 3
    pre_sql: Optional[list] = None
    post_sql: Optional[list] = None


# ===== 临时 SQL 执行（无需保存为组件）=====
@router.post("/run-sql")
def run_sql_adhoc(
    req: RunSqlRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    """临时 SQL 执行，结果直接返回。额外校验数据源级读权限。"""
    from app.models.datasource import DataSource
    ds = db.query(DataSource).filter(DataSource.id == req.datasource_id).first()
    if not ds:
        raise HTTPException(404, "数据源不存在")
    if not check_resource_permission(db, current_user, "datasource", req.datasource_id, "read"):
        raise HTTPException(404, "数据源不存在")
    return _run_sql(db, req.datasource_id, req.sql)


@router.post("/preview-datax")
def preview_datax_unsaved(
    req: DataXPreviewRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """基于未保存的 datax 配置生成 DataX job.json（密码已打码）"""
    from app.models.datasource import DataSource
    from app.core.datax_builder import build_datax_job
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
            field_mapping=req.field_mapping,
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


@router.get("/{comp_id}")
def get_component(
    comp_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:read")),
):
    return _serialize(_get_or_404(db, comp_id))


@router.put("/{comp_id}")
def update_component(
    comp_id: int,
    req: ComponentUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    c = _get_or_404(db, comp_id)
    if c.status not in EDITABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"组件当前状态「{c.status}」不允许编辑",
        )
    updates = req.model_dump(exclude_unset=True)
    # Handle convenience fields
    code = updates.pop('code', None)
    ds_id = updates.pop('datasource_id', None)
    if code is not None or ds_id is not None:
        cfg = dict(c.config_json or {})
        if code is not None:
            key = 'sql' if c.type == 'sql' else 'script'
            cfg[key] = code
        if ds_id is not None:
            cfg['datasource_id'] = ds_id
        updates['config_json'] = cfg
    # datax 类型更新时校验必填字段
    if c.type == "datax" and 'config_json' in updates:
        new_cfg = updates['config_json'] or {}
        missing = []
        for k in ("source_id", "target_id", "source_table", "target_table"):
            if not new_cfg.get(k):
                missing.append(k)
        if missing:
            raise HTTPException(status_code=400, detail=f"datax 组件缺少必填字段: {', '.join(missing)}")
    # 保存历史快照（仅在配置有实质变更时）
    if any(k in updates for k in ("config_json", "params", "name", "description")):
        _save_history(db, c, comment="编辑保存")
    for key, value in updates.items():
        if key == "params" and value is None:
            c.params = []
        elif key == "dqc_rule_ids" and value is None:
            c.dqc_rule_ids = []
        else:
            setattr(c, key, value)
    if "config_json" in updates:
        c.status = STATUS_DRAFT
        c.version = (c.version or 1) + 1
    db.commit()
    db.refresh(c)
    return _serialize(c)


# ===== 历史版本 =====
@router.get("/{comp_id}/history")
def get_component_history(
    comp_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:read")),
):
    """获取组件历史版本列表"""
    _get_or_404(db, comp_id)
    rows = (
        db.query(ComponentHistory)
        .filter(ComponentHistory.component_id == comp_id)
        .order_by(ComponentHistory.version.desc())
        .all()
    )
    return {
        "total": len(rows),
        "items": [
            {
                "id": h.id,
                "component_id": h.component_id,
                "version": h.version,
                "name": h.name,
                "status": h.status,
                "status_label": STATUS_LABELS.get(h.status, h.status),
                "created_by": h.created_by,
                "created_at": str(h.created_at) if h.created_at else None,
                "comment": h.comment,
            }
            for h in rows
        ],
    }


@router.get("/{comp_id}/history/{version}")
def get_component_history_detail(
    comp_id: int,
    version: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:read")),
):
    """获取指定历史版本的完整内容"""
    _get_or_404(db, comp_id)
    h = (
        db.query(ComponentHistory)
        .filter(ComponentHistory.component_id == comp_id, ComponentHistory.version == version)
        .first()
    )
    if not h:
        raise HTTPException(status_code=404, detail="历史版本不存在")
    return {
        "id": h.id,
        "component_id": h.component_id,
        "version": h.version,
        "name": h.name,
        "type": h.type,
        "description": h.description,
        "config_json": h.config_json or {},
        "params": h.params or [],
        "status": h.status,
        "created_by": h.created_by,
        "created_at": str(h.created_at) if h.created_at else None,
        "comment": h.comment,
    }


class RollbackRequest(BaseModel):
    comment: Optional[str] = None


@router.post("/{comp_id}/history/{version}/rollback")
def rollback_component(
    comp_id: int,
    version: int,
    req: RollbackRequest = RollbackRequest(),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    """回滚组件到指定历史版本"""
    c = _get_or_404(db, comp_id)
    if c.status not in EDITABLE_STATUSES:
        raise HTTPException(status_code=400, detail=f"组件当前状态「{c.status}」不允许回滚")
    h = (
        db.query(ComponentHistory)
        .filter(ComponentHistory.component_id == comp_id, ComponentHistory.version == version)
        .first()
    )
    if not h:
        raise HTTPException(status_code=404, detail="历史版本不存在")
    # 先保存当前版本快照
    _save_history(db, c, comment=f"回滚前自动保存（目标版本 {version}）")
    # 回滚字段
    c.name = h.name
    c.description = h.description
    c.config_json = h.config_json or {}
    c.params = h.params or []
    c.status = STATUS_DRAFT
    c.version = (c.version or 1) + 1
    db.commit()
    db.refresh(c)
    return _serialize(c)


@router.delete("/{comp_id}")
def delete_component(
    comp_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    c = _get_or_404(db, comp_id)
    if c.status not in DELETABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"组件状态 {c.status},只有 draft/offline 状态允许删除;请先下线",
        )
    _check_workflow_refs(db, comp_id)
    # 清理关联的同步任务记录，避免删除后仍被数据源引用检查拦截
    from app.models.sync_task import SyncTask
    db.query(SyncTask).filter(SyncTask.component_id == comp_id).delete(synchronize_session=False)
    db.delete(c)
    db.commit()
    return {"message": "删除成功"}


# ===== 运行组件 =====
@router.post("/{comp_id}/run")
def run_component(
    comp_id: int,
    req: RunComponentRequest = RunComponentRequest(),
    datasource_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    """运行组件：SQL 直连执行返回结果，Python/Shell 用 subprocess 执行返回日志"""
    from app.core.param_engine import build_param_context, substitute_config

    c = _get_or_404(db, comp_id)
    cfg = c.config_json or {}

    # 参数替换
    ctx = build_param_context(c.params or [], req.runtime_params)
    cfg = substitute_config(cfg, ctx, c.type)

    code = (cfg.get("sql") or cfg.get("script") or cfg.get("code") or "").strip()
    if not code:
        raise HTTPException(400, "组件代码为空")

    start = time.time()

    if c.type == "sql":
        ds_id = datasource_id or cfg.get("datasource_id")
        if not ds_id:
            raise HTTPException(400, "未指定数据源，请在 URL 加 ?datasource_id=X 或在组件中配置")
        sql_result = _run_sql(db, ds_id, code)

        # === DQC 检查（SQL 组件执行成功后触发）===
        dqc_results = []
        dqc_failed_rules = []
        rule_ids = c.dqc_rule_ids or []
        if rule_ids:
            from app.models.dqc_rule import DqcRule
            from app.models.dqc_check import DqcCheck
            from app.core.dqc_engine import execute_rule
            from app.models.datasource import DataSource

            rules = db.query(DqcRule).filter(
                DqcRule.id.in_(rule_ids),
                DqcRule.enabled == True,
            ).all()
            for rule in rules:
                ds = db.query(DataSource).filter(DataSource.id == rule.datasource_id).first()
                if not ds:
                    continue
                dqc_res = execute_rule(rule, ds)
                # 保存检查记录
                check = DqcCheck(
                    rule_id=rule.id,
                    actual_value=dqc_res.get("actual_value"),
                    expected_value=f"{rule.operator} {rule.threshold}{f' ~ {rule.threshold_max}' if rule.threshold_max else ''}",
                    passed=dqc_res["passed"],
                    error_msg=dqc_res.get("error_msg"),
                )
                db.add(check)
                db.commit()
                dqc_results.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "passed": dqc_res["passed"],
                    "actual_value": dqc_res.get("actual_value"),
                    "is_strong": rule.is_strong,
                })
                if not dqc_res["passed"] and rule.is_strong:
                    dqc_failed_rules.append(rule.name)

        sql_result["dqc_checks"] = dqc_results
        sql_result["dqc_failed"] = bool(dqc_failed_rules)
        sql_result["dqc_failed_rules"] = dqc_failed_rules
        return sql_result

    elif c.type in ("python", "shell"):
        # 安全沙箱校验
        if c.type == "shell":
            # 禁止 shell 元字符：管道、重定向、命令替换、逻辑运算符、分号、换行
            if re.search(r"[;|&<>{}()$`\n\r]|&&|\|\|", code):
                raise HTTPException(400, "Shell 组件禁止包含危险字符（; | & < > { } ( ) $ ` && || 换行）")
        elif c.type == "python":
            # 禁止危险导入和函数（文本黑名单是尽力而为，长期应迁移到容器沙箱）
            dangerous = [
                "os", "sys", "subprocess", "socket", "importlib",
                "builtins", "__builtins__", "ctypes", "pathlib",
                "code", "codeop", "types", "inspect", "gc",
                "traceback", "linecache", "tokenize", "pickle",
                "marshal", "multiprocessing", "threading",
            ]
            dangerous_funcs = [
                "eval", "exec", "compile", "open", "input",
                "__import__", "getattr", "setattr", "delattr",
                "breakpoint", "type",
            ]
            for mod in dangerous:
                if re.search(rf"\bimport\s+{mod}\b|\bfrom\s+{mod}\b", code):
                    raise HTTPException(400, f"Python 组件禁止导入危险模块: {mod}")
            for fn in dangerous_funcs:
                if re.search(rf"\b{fn}\s*\(", code):
                    raise HTTPException(400, f"Python 组件禁止使用危险函数: {fn}")
                # 阻止通过变量别名间接调用（如 x = open; x(...)）
                if re.search(rf"\b{fn}\b\s*=", code):
                    raise HTTPException(400, f"Python 组件禁止将危险函数赋值给变量: {fn}")
            # 阻止通过 dunder 属性链反射逃逸（如 ().__class__.__base__.__subclasses__()）
            if re.search(r"__\w+__", code):
                raise HTTPException(400, "Python 组件禁止使用双下划线属性反射")

        if c.type == "python":
            with tempfile.NamedTemporaryFile(
                suffix=".py", mode="w", delete=False, encoding="utf-8"
            ) as f:
                f.write(code)
                tmp = f.name
            try:
                result = subprocess.run(
                    ["python3", tmp], capture_output=True, text=True, timeout=120
                )
            finally:
                os.unlink(tmp)
        else:
            result = subprocess.run(
                ["bash", "-c", code], capture_output=True, text=True, timeout=120
            )
        duration_ms = int((time.time() - start) * 1000)
        log = (result.stdout + result.stderr).strip() or "(无输出)"
        return {
            "type": "log",
            "ok": result.returncode == 0,
            "log": log,
            "exit_code": result.returncode,
            "duration_ms": duration_ms,
        }

    else:
        raise HTTPException(400, f"不支持直接运行的组件类型: {c.type}")


# ===== 状态机操作 =====
@router.post("/{comp_id}/test")
def test_component(
    comp_id: int,
    req: RunComponentRequest = RunComponentRequest(),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    from app.core.param_engine import build_param_context, substitute_config

    c = _get_or_404(db, comp_id)
    if c.status not in {STATUS_DRAFT, STATUS_TESTED}:
        raise HTTPException(status_code=400, detail=f"状态 {c.status} 下不允许测试")

    # 参数替换：对 test 也做一次替换，让用户看到效果
    cfg = c.config_json or {}
    ctx = build_param_context(c.params or [], req.runtime_params)
    cfg = substitute_config(cfg, ctx, c.type)

    c.status = STATUS_TESTED
    db.commit()
    db.refresh(c)
    return {"message": "测试通过", "resolved_config": cfg, **_serialize(c)}


@router.post("/{comp_id}/publish")
def publish_component(
    comp_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:publish")),
):
    c = _get_or_404(db, comp_id)
    if c.status != STATUS_TESTED:
        raise HTTPException(
            status_code=400,
            detail=f"只有 tested 状态可发布,当前状态 {c.status},请先测试",
        )
    c.status = STATUS_ONLINE
    db.commit()
    db.refresh(c)
    return {"message": "已发布", **_serialize(c)}


@router.post("/{comp_id}/quick-publish")
def quick_publish_component(
    comp_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:publish")),
):
    """IDE 一键发布：draft/tested 均可直接上线，跳过 tested 前置要求"""
    c = _get_or_404(db, comp_id)
    if c.status == STATUS_ONLINE:
        return {"message": "已是发布状态", **_serialize(c)}
    if c.status == STATUS_OFFLINE:
        raise HTTPException(400, "已下线组件请先将状态改回 draft 再发布")
    c.status = STATUS_ONLINE
    db.commit()
    db.refresh(c)
    return {"message": "已发布", **_serialize(c)}


@router.post("/{comp_id}/publish-as-workflow")
async def publish_component_as_workflow(
    comp_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:publish")),
):
    """将 datax 组件发布为单节点工作流，同步到 DS。"""
    import json
    c = _get_or_404(db, comp_id)
    if c.type != "datax":
        raise HTTPException(status_code=400, detail="只有 datax 类型组件可发布为工作流")

    cfg = c.config_json or {}
    source_id = cfg.get("source_id")
    target_id = cfg.get("target_id")
    if not source_id or not target_id:
        raise HTTPException(status_code=400, detail="组件缺少 source_id 或 target_id 配置")

    from app.models.datasource import DataSource
    source_ds = db.query(DataSource).filter(DataSource.id == source_id).first()
    target_ds = db.query(DataSource).filter(DataSource.id == target_id).first()
    if not source_ds or not target_ds:
        raise HTTPException(status_code=400, detail="组件关联的数据源已被删除")

    from app.core.datax_builder import build_datax_job
    try:
        datax_job = build_datax_job(
            source_ds=source_ds,
            source_table=cfg.get("source_table", ""),
            target_ds=target_ds,
            target_table=cfg.get("target_table", ""),
            field_mapping=cfg.get("field_mapping", []),
            sync_type=cfg.get("sync_type", "full"),
            increment_column=cfg.get("increment_column"),
            where_clause=cfg.get("where_clause"),
            split_pk=cfg.get("split_pk"),
            write_mode=cfg.get("write_mode", "insert"),
            channel=cfg.get("channel", 3),
            pre_sql=cfg.get("pre_sql"),
            post_sql=cfg.get("post_sql"),
            mask_password=False,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    new_raw_json = json.dumps(datax_job, ensure_ascii=False)
    cfg["rawJson"] = new_raw_json
    c.config_json = cfg
    c.status = STATUS_ONLINE
    db.commit()
    db.refresh(c)

    from app.models.workflow import Workflow
    from app.models.resource_access import SysResourceAccess

    # 查找已有 Workflow（通过 steps_json 引用 component_id）
    wf = db.query(Workflow).filter(
        Workflow.steps_json.contains(f'"component_id": {c.id}'),
    ).first()

    if wf:
        wf.steps_json = [{"component_id": c.id, "name": c.name}]
        wf.status = "draft"
    else:
        wf = Workflow(
            name=f"[同步] {c.name}",
            description=f"由组件 #{c.id} 自动生成的单节点工作流",
            tags=[],
            steps_json=[{"component_id": c.id, "name": c.name}],
            dag_json=None,
            cron_expression=None,
            schedule_status="OFFLINE",
            status="draft",
            version=1,
            priority=3,
            created_by=current_user.id,
        )
        db.add(wf)
        db.add(SysResourceAccess(
            resource_type="workflow",
            resource_id=wf.id,
            subject_type="user",
            subject_id=current_user.id,
            permission="admin",
            granted_by=current_user.id,
        ))

    db.flush()

    from app.api.workflow import _sync_to_ds
    pd_code = None
    try:
        pd_code, schedule_id = await _sync_to_ds(db, wf)
        wf.ds_process_code = pd_code
        wf.ds_schedule_id = schedule_id
        wf.status = "online"
    except Exception as e:
        db.rollback()
        if pd_code:
            from app.core.ds_client import get_ds_client
            try:
                await get_ds_client().delete_process_definition(pd_code)
            except Exception:
                pass
        raise HTTPException(status_code=502, detail=f"DS 同步失败：{e}")

    db.commit()
    return {
        "component_id": c.id,
        "workflow_id": wf.id,
        "ds_process_code": wf.ds_process_code,
    }


@router.post("/{comp_id}/offline")
def offline_component(
    comp_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:publish")),
):
    c = _get_or_404(db, comp_id)
    if c.status != STATUS_ONLINE:
        raise HTTPException(status_code=400, detail=f"只有 online 状态可下线,当前 {c.status}")
    _check_workflow_refs(db, comp_id)
    c.status = STATUS_OFFLINE
    db.commit()
    db.refresh(c)
    return {"message": "已下线", **_serialize(c)}


# ===== 手动状态设置 =====

class SetStatusRequest(BaseModel):
    status: str


@router.put("/{comp_id}/status")
def set_component_status(
    comp_id: int,
    req: SetStatusRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    """手动设置组件状态（仅允许 MANUAL_STATUSES 中的状态）"""
    c = _get_or_404(db, comp_id)
    new_status = req.status

    if new_status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"无效状态: {new_status}")

    if new_status in AUTO_STATUSES:
        raise HTTPException(status_code=400, detail=f"状态 {new_status} 为自动流转状态，不可手动设置")

    if c.status == STATUS_ARCHIVED:
        raise HTTPException(status_code=400, detail="已归档组件不可修改状态")

    # 处理暂停恢复（从 paused 转出去）
    if c.status == STATUS_PAUSED:
        # 恢复到 previous_status
        prev = getattr(c, 'previous_status', None) or STATUS_DEVELOPING
        c.status = prev
        try:
            c.previous_status = None
        except Exception:
            pass
        db.commit()
        db.refresh(c)
        return {"message": f"已恢复到 {STATUS_LABELS.get(prev, prev)}", **_serialize(c)}

    # 处理暂停：记录 previous_status
    if new_status == STATUS_PAUSED:
        try:
            c.previous_status = c.status
        except Exception:
            pass
        c.status = new_status
        db.commit()
        db.refresh(c)
        return {"message": "已暂停", **_serialize(c)}

    # 校验流转规则
    allowed = STATUS_TRANSITIONS.get(c.status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"状态流转非法: {STATUS_LABELS.get(c.status, c.status)} → {STATUS_LABELS.get(new_status, new_status)}"
        )

    c.status = new_status
    db.commit()
    db.refresh(c)
    return {"message": f"状态已更新为 {STATUS_LABELS.get(new_status, new_status)}", **_serialize(c)}


@router.post("/{comp_id}/resume")
def resume_component(
    comp_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    """从暂停状态恢复组件"""
    c = _get_or_404(db, comp_id)
    if c.status != STATUS_PAUSED:
        raise HTTPException(status_code=400, detail="组件未处于暂停状态")
    prev = getattr(c, 'previous_status', None) or STATUS_DEVELOPING
    c.status = prev
    try:
        c.previous_status = None
    except Exception:
        pass
    db.commit()
    db.refresh(c)
    return {"message": f"已恢复到 {STATUS_LABELS.get(prev, prev)}", **_serialize(c)}


# ===== 移动与排序 =====

class MoveComponentRequest(BaseModel):
    folder_id: Optional[int] = None
    sort_order: Optional[int] = None


class ReorderItem(BaseModel):
    id: int
    sort_order: int


class ReorderRequest(BaseModel):
    orders: list[ReorderItem]


class MoveFolderRequest(BaseModel):
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None


@router.put("/{comp_id}/move")
def move_component(
    comp_id: int,
    req: MoveComponentRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    """移动组件到指定文件夹并/或更新排序"""
    c = _get_or_404(db, comp_id)
    if req.folder_id is not None:
        if req.folder_id != 0:
            f = db.query(ComponentFolder).filter(ComponentFolder.id == req.folder_id).first()
            if not f:
                raise HTTPException(status_code=404, detail="目标文件夹不存在")
        c.folder_id = req.folder_id if req.folder_id != 0 else None
    if req.sort_order is not None:
        c.sort_order = req.sort_order
    db.commit()
    db.refresh(c)
    return {"message": "移动成功", **_serialize(c)}


@router.post("/reorder")
def reorder_components(
    req: ReorderRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    """批量更新组件排序"""
    for item in req.orders:
        c = db.query(Component).filter(Component.id == item.id).first()
        if c:
            c.sort_order = item.sort_order
    db.commit()
    return {"message": "排序已更新"}


@router.put("/folders/{folder_id}/move")
def move_folder(
    folder_id: int,
    req: MoveFolderRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    """移动文件夹到指定父文件夹并/或更新排序"""
    f = db.query(ComponentFolder).filter(ComponentFolder.id == folder_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    if req.parent_id is not None:
        if req.parent_id != 0:
            parent = db.query(ComponentFolder).filter(ComponentFolder.id == req.parent_id).first()
            if not parent:
                raise HTTPException(status_code=404, detail="目标父文件夹不存在")
            depth = _folder_depth(db, req.parent_id)
            if depth >= 2:
                raise HTTPException(status_code=400, detail="最多支持 3 层嵌套")
        f.parent_id = req.parent_id if req.parent_id != 0 else None
        # 重新计算 depth
        f.depth = _folder_depth(db, f.parent_id)
    if req.sort_order is not None:
        f.sort_order = req.sort_order
    db.commit()
    db.refresh(f)
    return {"id": f.id, "name": f.name, "type": f.type, "parent_id": f.parent_id, "depth": f.depth}


# ===== 编辑锁 =====
import json as _json
from datetime import datetime, timezone

LOCK_TTL = 300  # 5 分钟
LOCK_HEARTBEAT_INTERVAL = 60  # 心跳间隔（前端应小于此值）


def _get_redis():
    try:
        import redis, os
        from app.core.config import settings
        password = os.environ.get("REDIS_PASSWORD") or getattr(settings, "REDIS_PASSWORD", None)
        urls = [settings.REDIS_URL]
        if "localhost" in settings.REDIS_URL:
            urls.append(settings.REDIS_URL.replace("localhost", "redis"))
        for raw_url in urls:
            try:
                url = raw_url
                if password and "://" in url:
                    scheme, rest = url.split("://", 1)
                    url = f"{scheme}://:{password}@{rest}"
                r = redis.from_url(url, socket_connect_timeout=1, decode_responses=True)
                r.ping()
                return r
            except Exception:
                continue
        return None
    except Exception:
        return None


def _lock_key(comp_id: int) -> str:
    return f"component_lock:{comp_id}"


def _lock_info(user: SysUser) -> str:
    return _json.dumps({
        "user_id": user.id,
        "username": user.username,
        "locked_at": datetime.now(timezone.utc).isoformat(),
    })


@router.post("/{comp_id}/lock")
def acquire_lock(
    comp_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    """获取组件编辑锁"""
    _get_or_404(db, comp_id)
    r = _get_redis()
    key = _lock_key(comp_id)
    if r:
        # 检查是否已被自己持有
        val = r.get(key)
        if val:
            info = _json.loads(val)
            if info.get("user_id") == current_user.id:
                # 刷新 TTL
                r.expire(key, LOCK_TTL)
                return {"locked": True, "by_me": True, "ttl": LOCK_TTL}
            return {"locked": False, "by": info.get("username"), "message": f"组件正被 {info.get('username')} 编辑"}
        # 尝试获取锁（原子操作）
        ok = r.set(key, _lock_info(current_user), nx=True, ex=LOCK_TTL)
        if ok:
            return {"locked": True, "by_me": True, "ttl": LOCK_TTL}
        # 被他人抢到了
        val = r.get(key)
        info = _json.loads(val) if val else {}
        return {"locked": False, "by": info.get("username"), "message": f"组件正被 {info.get('username')} 编辑"}
    # 无 Redis 时降级为不锁（开发环境兼容）
    return {"locked": True, "by_me": True, "ttl": LOCK_TTL}


@router.delete("/{comp_id}/lock")
def release_lock(
    comp_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    """释放组件编辑锁"""
    _get_or_404(db, comp_id)
    r = _get_redis()
    key = _lock_key(comp_id)
    if r:
        val = r.get(key)
        if val:
            info = _json.loads(val)
            if info.get("user_id") == current_user.id:
                r.delete(key)
                return {"released": True}
            return {"released": False, "message": "锁由其他用户持有，无法释放"}
        return {"released": True, "message": "锁已过期或不存在"}
    return {"released": True}


@router.put("/{comp_id}/lock/heartbeat")
def heartbeat_lock(
    comp_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:write")),
):
    """编辑锁心跳续期"""
    _get_or_404(db, comp_id)
    r = _get_redis()
    key = _lock_key(comp_id)
    if r:
        val = r.get(key)
        if not val:
            return {"renewed": False, "message": "锁已过期"}
        info = _json.loads(val)
        if info.get("user_id") != current_user.id:
            return {"renewed": False, "by": info.get("username"), "message": "锁已被其他用户抢占"}
        r.expire(key, LOCK_TTL)
        return {"renewed": True, "ttl": LOCK_TTL}
    return {"renewed": True, "ttl": LOCK_TTL}


@router.get("/{comp_id}/lock")
def get_lock_status(
    comp_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("component:read")),
):
    """查询组件编辑锁状态"""
    _get_or_404(db, comp_id)
    r = _get_redis()
    key = _lock_key(comp_id)
    if r:
        val = r.get(key)
        if val:
            info = _json.loads(val)
            ttl = r.ttl(key)
            return {
                "locked": True,
                "by_me": info.get("user_id") == current_user.id,
                "user_id": info.get("user_id"),
                "username": info.get("username"),
                "locked_at": info.get("locked_at"),
                "ttl": ttl if ttl > 0 else 0,
            }
    return {"locked": False}
