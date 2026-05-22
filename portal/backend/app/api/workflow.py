import logging
import os
import uuid
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permissions import get_accessible_ids, check_resource_permission, require_permission
from app.core.ds_client import get_ds_client
from app.core.encrypt import decrypt_password
from app.core.dsl_translator import translate_workflow, translate_workflow_dag
from app.models.workflow import Workflow
from app.models.component import Component
from app.models.datasource import DataSource
from app.models.dqc_rule import DqcRule
from app.models.user import SysUser
from app.models.workflow_sync_queue import WorkflowSyncQueue

router = APIRouter(prefix="/workflows", tags=["工作流"])


def _to_6_field_cron(cron_expr: str) -> str:
    """将 5 段 cron 补全为 6 段（DS 要求含秒字段）。

    - 已是 6 段则原样返回
    - 5 段则在前面补 `0` 作为秒字段
    - 其他段数保持原样（让 DS 返回错误）
    """
    parts = cron_expr.strip().split()
    if len(parts) == 5:
        return "0 " + " ".join(parts)
    return " ".join(parts)


# ===== 状态常量 =====
STATUS_DRAFT = "draft"
STATUS_TESTED = "tested"
STATUS_ONLINE = "online"
STATUS_OFFLINE = "offline"

EDITABLE_STATUSES = {STATUS_DRAFT, STATUS_TESTED, STATUS_OFFLINE}
DELETABLE_STATUSES = {STATUS_DRAFT, STATUS_OFFLINE}


# ===== Schemas =====
class WorkflowStep(BaseModel):
    component_id: int
    name: Optional[str] = None

class DagNode(BaseModel):
    id: str
    component_id: int
    name: Optional[str] = None
    position: Dict[str, float]  # {x, y}
    skip: bool = False

class DagEdge(BaseModel):
    id: str
    source: str
    target: str

class DagPayload(BaseModel):
    nodes: List[DagNode] = Field(default_factory=list)
    edges: List[DagEdge] = Field(default_factory=list)

class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    steps: List[WorkflowStep] = Field(default_factory=list)
    dag: Optional[DagPayload] = None
    cron_expression: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[int] = Field(default=3, ge=1, le=3)

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[WorkflowStep]] = None
    dag: Optional[DagPayload] = None
    cron_expression: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[int] = Field(default=None, ge=1, le=3)


def _serialize(w: Workflow, db: Optional[Session] = None, comp_map: dict = None) -> dict:
    """序列化 workflow,steps 中带上 component 详情

    comp_map 为外部批量查询的组件缓存；未提供且需要组件详情时内部查询。
    """
    steps = w.steps_json or []
    dag = w.dag_json

    # 收集所有需要的 component_id（steps + dag 合并）
    all_comp_ids = set()
    for s in steps:
        if s.get("component_id"):
            all_comp_ids.add(s["component_id"])
    if dag and dag.get("nodes"):
        for n in dag["nodes"]:
            if n.get("component_id"):
                all_comp_ids.add(n["component_id"])

    # 优先使用外部缓存，否则内部一次查询
    if comp_map is None and db is not None and all_comp_ids:
        comps = db.query(Component).filter(Component.id.in_(list(all_comp_ids))).all()
        comp_map = {c.id: c for c in comps}
    comp_map = comp_map or {}

    enriched_steps = []
    for idx, s in enumerate(steps):
        cid = s.get("component_id")
        c = comp_map.get(cid)
        enriched_steps.append({
            "order": idx,
            "component_id": cid,
            "name": s.get("name") or (c.name if c else f"step_{idx}"),
            "component_name": c.name if c else None,
            "component_type": c.type if c else None,
            "component_status": c.status if c else None,
        })

    # 计算下次执行时间
    next_fire_time = None
    if w.cron_expression:
        try:
            from croniter import croniter
            from datetime import datetime
            cron_expr = w.cron_expression.strip()
            parts = cron_expr.split()
            if len(parts) == 6:
                cron_expr = ' '.join(parts[1:])
            cron_expr = cron_expr.replace('?', '*')
            cron = croniter(cron_expr, datetime.now())
            next_fire_time = str(cron.get_next(datetime))
        except Exception as e:
            logging.getLogger(__name__).warning("cron parse error for workflow %s: %s", w.id, e)

    # DAG 节点补充 type
    if dag and dag.get("nodes"):
        enriched_nodes = [
            {**n, "type": comp_map[n["component_id"]].type if n.get("component_id") in comp_map else n.get("type", "sql")}
            for n in dag["nodes"]
        ]
        dag = {**dag, "nodes": enriched_nodes}

    return {
        "id": w.id,
        "name": w.name,
        "description": w.description,
        "tags": w.tags or [],
        "steps": enriched_steps,
        "dag": dag,
        "cron_expression": w.cron_expression,
        "schedule_status": w.schedule_status,
        "status": w.status,
        "version": w.version,
        "priority": w.priority or 3,
        "last_run_status": w.last_run_status,
        "last_run_time": str(w.last_run_time) if w.last_run_time else None,
        "last_run_duration": w.last_run_duration,
        "next_fire_time": next_fire_time,
        "ds_process_code": w.ds_process_code,
        "ds_schedule_id": w.ds_schedule_id,
        "created_at": str(w.created_at) if w.created_at else None,
        "updated_at": str(w.updated_at) if w.updated_at else None,
    }


def _get_or_404(db: Session, wf_id: int) -> Workflow:
    w = db.query(Workflow).filter(Workflow.id == wf_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return w


def _validate_steps(db: Session, steps: List[WorkflowStep]) -> List[Dict[str, Any]]:
    """校验所有 component 存在且发布,返回 steps_json 数据"""
    if not steps:
        return []
    comp_ids = [s.component_id for s in steps]
    comps = db.query(Component).filter(Component.id.in_(comp_ids)).all()
    comp_map = {c.id: c for c in comps}
    out = []
    for s in steps:
        c = comp_map.get(s.component_id)
        if not c:
            raise HTTPException(status_code=400, detail=f"组件 {s.component_id} 不存在")
        out.append({"component_id": s.component_id, "name": s.name or c.name})
    return out


def _enqueue_sync(db: Session, workflow_id: int, action: str) -> WorkflowSyncQueue:
    """将 DS 同步操作写入 outbox 队列；已存在 pending/processing 的同名任务则直接返回。"""
    existing = (
        db.query(WorkflowSyncQueue)
        .filter(
            WorkflowSyncQueue.workflow_id == workflow_id,
            WorkflowSyncQueue.action == action,
            WorkflowSyncQueue.status.in_(["pending", "processing"]),
        )
        .first()
    )
    if existing:
        return existing
    record = WorkflowSyncQueue(
        workflow_id=workflow_id,
        action=action,
        status="pending",
        retry_count=0,
        max_retries=3,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record



# ===== 运行信息同步 =====
async def _fetch_ds_instances(ds, pc: int, workflows: List[Workflow]):
    """分批并发从 DS 拉取每个 workflow 的最近实例"""
    async def _fetch_one(w: Workflow):
        try:
            inst = await ds.get(f"/projects/{pc}/process-instances", params={
                "pageNo": 1, "pageSize": 1,
                "processDefinitionCode": w.ds_process_code,
            })
            last = (inst or {}).get("totalList", [None])[0]
            return (w.id, last)
        except Exception as e:
            logging.getLogger(__name__).warning("sync workflow %s failed: %s", w.id, e)
            return (w.id, None)

    BATCH_SIZE = 10
    ds_results = []
    for i in range(0, len(workflows), BATCH_SIZE):
        batch = workflows[i : i + BATCH_SIZE]
        results = await asyncio.gather(*[_fetch_one(w) for w in batch])
        ds_results.extend(results)
    return ds_results


def _update_workflow_runs(db: Session, ds_results: List[tuple]):
    """根据 DS 返回数据更新 workflow 最近运行信息"""
    from datetime import datetime
    synced = 0
    for wf_id, last in ds_results:
        if not last:
            continue
        w = db.query(Workflow).filter(Workflow.id == wf_id).first()
        if not w:
            continue
        w.last_run_status = last.get("state")
        start_str = last.get("startTime")
        end_str = last.get("endTime")
        if start_str:
            try:
                w.last_run_time = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                w.last_run_time = None
        if start_str and end_str:
            try:
                fmt = "%Y-%m-%d %H:%M:%S"
                w.last_run_duration = int(
                    (datetime.strptime(end_str, fmt) - datetime.strptime(start_str, fmt)).total_seconds()
                )
            except Exception:
                pass
        synced += 1
    db.commit()
    return synced


async def _check_alert_rules(db: Session, workflows: List[Workflow]):
    """检查 workflow 运行结果是否触发告警规则"""
    from app.models.alert_rule import AlertRule
    from app.core.notifier import notify as do_notify
    rules = db.query(AlertRule).filter(AlertRule.enabled == True).all()
    alerted = 0
    for w in workflows:
        if not w.last_run_status:
            continue
        for rule in rules:
            if rule.target_type == "workflow" and rule.target_id != w.id:
                continue
            triggered = False
            if rule.trigger_type == "failure" and w.last_run_status == "FAILURE":
                triggered = True
            elif rule.trigger_type == "timeout" and rule.trigger_value:
                if w.last_run_duration and w.last_run_duration > rule.trigger_value:
                    triggered = True
            if triggered:
                event = {
                    "workflow_name": w.name,
                    "status": w.last_run_status,
                    "time": str(w.last_run_time) if w.last_run_time else "",
                    "duration": w.last_run_duration,
                }
                await do_notify(rule, event)
                alerted += 1
    return alerted


@router.post("/sync-last-run")
async def sync_last_run(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """批量从 DS 同步最近运行信息到 Portal 缓存字段"""
    workflows = db.query(Workflow).filter(Workflow.ds_process_code.isnot(None)).all()
    if not workflows:
        return {"synced": 0}
    try:
        ds = get_ds_client()
        pc = await ds._discover_project()
        if not pc:
            return {"synced": 0, "error": "DS project unavailable"}
    except Exception as e:
        logging.getLogger(__name__).warning("DS unavailable: %s", e)
        return {"synced": 0, "error": "DS unavailable"}

    ds_results = await _fetch_ds_instances(ds, pc, workflows)
    synced = await asyncio.to_thread(_update_workflow_runs, db, ds_results)
    alerted = 0
    try:
        alerted = await _check_alert_rules(db, workflows)
    except Exception as e:
        logging.getLogger(__name__).warning("alert check failed: %s", e)

    return {"synced": synced, "alerted": alerted}


# ===== CRUD =====
@router.get("")
def list_workflows(
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    q = db.query(Workflow)
    if keyword:
        q = q.filter(Workflow.name.contains(keyword))
    if status:
        q = q.filter(Workflow.status == status)
    if tag:
        # JSON contains 粗筛 + 应用层精确匹配，避免 "日报" 误匹配 "日报表"
        q = q.filter(Workflow.tags.contains(f'"{tag}"'))
        candidate_ids = [w.id for w in q.with_entities(Workflow.id, Workflow.tags).all() if tag in (w.tags or [])]
        q = db.query(Workflow).filter(Workflow.id.in_(candidate_ids)) if candidate_ids else q.filter(False)

    # 资源级 ACL 过滤
    accessible = get_accessible_ids(db, current_user, "workflow", "read")
    if accessible is not None:
        q = q.filter(Workflow.id.in_(accessible)) if accessible else q.filter(False)

    total = q.count()
    items = q.order_by(Workflow.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    # 批量预查所有 component，避免每个 workflow 单独查询（P3-4/5）
    all_comp_ids = set()
    for w in items:
        for s in (w.steps_json or []):
            if s.get("component_id"):
                all_comp_ids.add(s["component_id"])
        dag = w.dag_json
        if dag and dag.get("nodes"):
            for n in dag["nodes"]:
                if n.get("component_id"):
                    all_comp_ids.add(n["component_id"])
    comp_map = {}
    if all_comp_ids:
        comps = db.query(Component).filter(Component.id.in_(list(all_comp_ids))).all()
        comp_map = {c.id: c for c in comps}

    # 收集所有已使用的标签
    all_tags = set()
    for w in db.query(Workflow.tags).filter(Workflow.tags.isnot(None)).all():
        if w.tags:
            all_tags.update(w.tags)
    return {"total": total, "items": [_serialize(w, comp_map=comp_map) for w in items], "all_tags": sorted(all_tags)}


@router.post("")
def create_workflow(
    req: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("workflow:create")),
):
    steps_data = _validate_steps(db, req.steps)
    dag_data = None
    if req.dag and req.dag.nodes:
        dag_data = {"nodes": [n.model_dump() for n in req.dag.nodes], "edges": [e.model_dump() for e in req.dag.edges]}
        # 从 DAG 生成兼容的 steps_json（拓扑排序）
        steps_data = [{"component_id": n.component_id, "name": n.name} for n in req.dag.nodes if not n.skip]
    w = Workflow(
        name=req.name,
        description=req.description,
        tags=req.tags or [],
        steps_json=steps_data,
        dag_json=dag_data,
        cron_expression=req.cron_expression,
        schedule_status="OFFLINE",
        status=STATUS_DRAFT,
        version=1,
        priority=req.priority or 3,
        created_by=current_user.id,
    )
    db.add(w)
    db.flush()  # 获取 w.id

    # 自动授予创建者 admin 权限
    from app.models.resource_access import SysResourceAccess
    db.add(SysResourceAccess(
        resource_type="workflow",
        resource_id=w.id,
        subject_type="user",
        subject_id=current_user.id,
        permission="admin",
        granted_by=current_user.id,
    ))

    db.commit()
    db.refresh(w)
    return _serialize(w, db)


@router.get("/scheduled")
def list_scheduled_workflows(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """返回所有配置了 cron 的工作流（调度任务页面用）"""
    q = db.query(Workflow).filter(
        Workflow.cron_expression.isnot(None),
        Workflow.cron_expression != "",
    ).order_by(Workflow.id.desc())

    # 资源级 ACL 过滤（与 list_workflows 保持一致）
    accessible = get_accessible_ids(db, current_user, "workflow", "read")
    if accessible is not None:
        q = q.filter(Workflow.id.in_(accessible)) if accessible else q.filter(False)

    items = q.all()
    result = []
    for w in items:
        item = _serialize(w, db)
        try:
            from croniter import croniter
            from datetime import datetime
            cron = croniter(w.cron_expression, datetime.now())
            item["next_fire_time"] = str(cron.get_next(datetime))
        except Exception as e:
            logging.getLogger(__name__).warning("cron parse error for workflow %s: %s", w.id, e)
            item["next_fire_time"] = None
        result.append(item)
    return {"items": result, "total": len(result)}


@router.get("/{wf_id}")
def get_workflow(
    wf_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    w = _get_or_404(db, wf_id)
    if not check_resource_permission(db, current_user, "workflow", wf_id, "read"):
        raise HTTPException(status_code=404, detail="工作流不存在")
    return _serialize(w, db)


@router.put("/{wf_id}")
def update_workflow(
    wf_id: int,
    req: WorkflowUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("workflow:write")),
):
    w = _get_or_404(db, wf_id)
    if not check_resource_permission(db, current_user, "workflow", wf_id, "write"):
        raise HTTPException(status_code=404, detail="工作流不存在")
    if w.status not in EDITABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"工作流状态 {w.status},只有 draft/tested 状态允许编辑;请先下线",
        )
    updates = req.model_dump(exclude_unset=True)
    structural_change = False
    if "name" in updates:
        w.name = updates["name"]
    if "description" in updates:
        w.description = updates["description"]
    if "tags" in updates:
        w.tags = updates["tags"] or []
    if "cron_expression" in updates:
        w.cron_expression = updates["cron_expression"]
    if "priority" in updates:
        w.priority = updates["priority"]
    if "steps" in updates:
        steps_data = _validate_steps(db, [WorkflowStep(**s) for s in updates["steps"]])
        w.steps_json = steps_data
        structural_change = True
    if "dag" in updates and updates["dag"]:
        dag_raw = updates["dag"]
        dag_data = {"nodes": dag_raw.get("nodes", []), "edges": dag_raw.get("edges", [])}
        # 校验所有非 skip 节点的 component_id 存在且有效
        comp_ids = [n["component_id"] for n in dag_data["nodes"] if not n.get("skip")]
        if comp_ids:
            found = {c.id for c in db.query(Component.id).filter(Component.id.in_(comp_ids)).all()}
            missing = [cid for cid in comp_ids if cid not in found]
            if missing:
                raise HTTPException(status_code=400, detail=f"以下组件不存在: {missing}")
        w.dag_json = dag_data
        # 同步 steps_json
        w.steps_json = [{"component_id": n["component_id"], "name": n.get("name")} for n in dag_data["nodes"] if not n.get("skip")]
        structural_change = True
    if structural_change:
        w.status = STATUS_DRAFT
        w.version = (w.version or 1) + 1
    db.commit()
    db.refresh(w)
    return _serialize(w, db)


@router.delete("/{wf_id}")
async def delete_workflow(
    wf_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("workflow:write")),
):
    w = _get_or_404(db, wf_id)
    if not check_resource_permission(db, current_user, "workflow", wf_id, "admin"):
        raise HTTPException(status_code=404, detail="工作流不存在")
    if w.status not in DELETABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"工作流状态 {w.status},只有 draft/offline 状态允许删除;请先下线",
        )
    # 入队 DS 资源清理任务，后台异步执行
    _enqueue_sync(db, w.id, "delete")
    # 立即清理本地记录
    from app.models.resource_access import SysResourceAccess
    db.query(SysResourceAccess).filter(
        SysResourceAccess.resource_type == "workflow",
        SysResourceAccess.resource_id == wf_id,
    ).delete()
    # 清理关联的同步任务记录（按 ds_workflow_id 或 DAG 中的 component_id）
    from app.models.sync_task import SyncTask
    db.query(SyncTask).filter(SyncTask.ds_workflow_id == wf_id).delete(synchronize_session=False)
    dag = w.dag_json or {}
    for node in dag.get("nodes", []):
        cid = node.get("component_id")
        if cid:
            db.query(SyncTask).filter(SyncTask.component_id == cid).delete(synchronize_session=False)
    db.delete(w)
    db.commit()
    return {"message": "删除成功，DS 资源清理将在后台执行"}


# ===== 状态机操作 =====
@router.post("/{wf_id}/test")
def test_workflow(
    wf_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("workflow:write")),
):
    """测试工作流 — 检查所有 component 都已发布"""
    w = _get_or_404(db, wf_id)
    if not check_resource_permission(db, current_user, "workflow", wf_id, "write"):
        raise HTTPException(status_code=404, detail="工作流不存在")
    if w.status not in {STATUS_DRAFT, STATUS_TESTED}:
        raise HTTPException(status_code=400, detail=f"状态 {w.status} 下不允许测试")
    # 从 DAG 或 steps 提取 component_id
    if w.dag_json and w.dag_json.get("nodes"):
        comp_ids = [n["component_id"] for n in w.dag_json["nodes"] if not n.get("skip")]
    else:
        steps = w.steps_json or []
        comp_ids = [s.get("component_id") for s in steps]
    if not comp_ids:
        raise HTTPException(status_code=400, detail="工作流为空,请先添加步骤")
    comps = db.query(Component).filter(Component.id.in_(comp_ids)).all()
    comp_map = {c.id: c for c in comps}
    unpublished = []
    for cid in comp_ids:
        c = comp_map.get(cid)
        if not c:
            unpublished.append(f"组件{cid}(不存在)")
        elif c.status != "online":
            unpublished.append(f"{c.name}(当前 {c.status})")
    if unpublished:
        raise HTTPException(
            status_code=400,
            detail=f"以下组件未上线,无法测试: {', '.join(unpublished)}",
        )
    # === DAG 连通性检查 ===
    dag = w.dag_json or {}
    nodes = dag.get("nodes", [])
    edges = dag.get("edges", [])
    if nodes and edges:
        node_ids = {n.get("id") or f"node_{i}" for i, n in enumerate(nodes) if not n.get("skip")}
        adj = {nid: [] for nid in node_ids}
        in_degree = {nid: 0 for nid in node_ids}
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src in node_ids and tgt in node_ids:
                adj[src].append(tgt)
                in_degree[tgt] += 1
        # 孤立节点（无入无出）
        isolated = [nid for nid in node_ids if in_degree[nid] == 0 and len(adj[nid]) == 0]
        if isolated:
            raise HTTPException(status_code=400, detail=f"DAG 中存在孤立节点，请检查连线: {', '.join(isolated)}")
        # 环检测（拓扑排序）
        queue = [nid for nid in node_ids if in_degree[nid] == 0]
        visited = set()
        while queue:
            nid = queue.pop(0)
            visited.add(nid)
            for neighbor in adj.get(nid, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        if len(visited) != len(node_ids):
            raise HTTPException(status_code=400, detail="DAG 中存在环路，请检查节点连线")

    w.status = STATUS_TESTED
    db.commit()
    db.refresh(w)
    return {"message": "测试通过", **_serialize(w, db)}


@router.post("/{wf_id}/publish")
async def publish_workflow(
    wf_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("workflow:publish")),
):
    """发布工作流 — tested 才能发布,入队后台异步同步到 DS"""
    w = _get_or_404(db, wf_id)
    if not check_resource_permission(db, current_user, "workflow", wf_id, "write"):
        raise HTTPException(status_code=404, detail="工作流不存在")
    if w.status != STATUS_TESTED:
        raise HTTPException(
            status_code=400,
            detail=f"只有 tested 状态可发布,当前 {w.status},请先测试",
        )
    record = _enqueue_sync(db, w.id, "publish")
    # 乐观更新本地状态，DS 同步失败时调度器会回写
    w.status = STATUS_ONLINE
    w.schedule_status = "ONLINE"
    db.commit()
    db.refresh(w)
    return {
        "message": "已提交发布队列，后台同步中",
        "sync_status": record.status,
        "queue_id": record.id,
        **_serialize(w, db),
    }


@router.post("/{wf_id}/offline")
async def offline_workflow(
    wf_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("workflow:publish")),
):
    w = _get_or_404(db, wf_id)
    if not check_resource_permission(db, current_user, "workflow", wf_id, "write"):
        raise HTTPException(status_code=404, detail="工作流不存在")
    if w.status != STATUS_ONLINE:
        raise HTTPException(status_code=400, detail=f"只有 online 状态可下线,当前 {w.status}")
    record = _enqueue_sync(db, w.id, "offline")
    # 乐观更新本地状态
    w.status = STATUS_OFFLINE
    w.schedule_status = "OFFLINE"
    db.commit()
    db.refresh(w)
    return {
        "message": "已提交下线队列，后台同步中",
        "sync_status": record.status,
        "queue_id": record.id,
        **_serialize(w, db),
    }


@router.post("/{wf_id}/run")
async def run_workflow(
    wf_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("workflow:write")),
):
    """手动运行工作流 — 通过 DS 触发"""
    w = _get_or_404(db, wf_id)
    if not check_resource_permission(db, current_user, "workflow", wf_id, "write"):
        raise HTTPException(status_code=404, detail="工作流不存在")
    if w.status not in {STATUS_ONLINE, STATUS_TESTED}:
        raise HTTPException(status_code=400, detail=f"状态 {w.status} 下不允许运行,需先测试/发布")
    if not w.ds_process_code:
        raise HTTPException(status_code=400, detail="工作流未同步到 DS,请先发布")
    ds = get_ds_client()
    result = await ds.start_process_instance(w.ds_process_code)
    if result is None:
        raise HTTPException(status_code=502, detail="DS 触发运行失败")
    return {
        "message": "已触发运行",
        "workflow_id": w.id,
        "ds_process_code": w.ds_process_code,
        "ds_response": result,
    }


# ===== 实例详情（含 DQC 质量检查结果） =====

@router.get("/{wf_id}/instances/{instance_id}")
async def get_instance_detail(
    wf_id: int,
    instance_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """获取工作流实例详情，包含任务列表和 DQC 质量检查结果。"""
    w = _get_or_404(db, wf_id)
    if not check_resource_permission(db, current_user, "workflow", wf_id, "read"):
        raise HTTPException(status_code=404, detail="工作流不存在")

    ds = get_ds_client()
    pc = await ds.project_code()
    if not pc:
        raise HTTPException(status_code=502, detail="DS 服务不可用")

    # 获取流程实例详情
    inst = await ds.get(f"/projects/{pc}/process-instances/{instance_id}")
    if not inst:
        raise HTTPException(status_code=404, detail="实例不存在")

    # 获取任务实例列表
    tasks = await ds.get_task_instances(instance_id)

    # 识别 DQC 任务并关联质量检查结果
    from app.models.dqc_rule import DqcRule
    from app.models.dqc_check import DqcCheck

    dqc_results = []
    for task in tasks:
        name = task.get("name", "")
        if not name.startswith("DQC:"):
            continue
        # 优先从名称中提取 rule_id（新格式 DQC:{rule_id}:{rule_name}[强/弱]）
        rule = None
        body = name[4:]
        if ":" in body:
            maybe_id, _ = body.split(":", 1)
            if maybe_id.isdigit():
                rule = db.query(DqcRule).filter(DqcRule.id == int(maybe_id)).first()
        # 回退：旧格式按规则名匹配
        if not rule:
            rule_name = body.replace("[强]", "").replace("[弱]", "").strip()
            if rule_name.endswith("..."):
                rule_name = rule_name[:-3]
            rule = db.query(DqcRule).filter(DqcRule.name == rule_name).first()
            if not rule:
                rule = (
                    db.query(DqcRule)
                    .filter(DqcRule.name.contains(rule_name))
                    .order_by(DqcRule.id.desc())
                    .first()
                )
        if not rule:
            logging.getLogger(__name__).warning("DQC task %s matched no rule", name)
            continue

        # 查找对应的检查记录（按时间窗口匹配：实例执行前后 2 分钟）
        check = None
        start_time = task.get("startTime")
        if start_time:
            from datetime import datetime, timedelta
            try:
                task_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                check = (
                    db.query(DqcCheck)
                    .filter(
                        DqcCheck.rule_id == rule.id,
                        DqcCheck.checked_at >= task_dt - timedelta(minutes=2),
                        DqcCheck.checked_at <= task_dt + timedelta(minutes=2),
                    )
                    .order_by(DqcCheck.id.desc())
                    .first()
                )
            except Exception as e:
                logging.getLogger(__name__).warning("DQC check time parse failed: %s", e)
        if not check:
            # 回退：取该规则最近的一次检查
            check = (
                db.query(DqcCheck)
                .filter(DqcCheck.rule_id == rule.id)
                .order_by(DqcCheck.id.desc())
                .first()
            )

        dqc_results.append({
            "task_name": name,
            "task_state": task.get("state"),
            "rule_id": rule.id,
            "rule_name": rule.name,
            "is_strong": rule.is_strong,
            "passed": check.passed if check else None,
            "actual_value": check.actual_value if check else None,
            "expected_value": check.expected_value if check else None,
            "sample_data": check.sample_data if check else None,
            "checked_at": str(check.checked_at) if check and check.checked_at else None,
        })

    return {
        "instance": {
            "id": inst.get("id"),
            "state": inst.get("state"),
            "start_time": inst.get("startTime"),
            "end_time": inst.get("endTime"),
            "duration": inst.get("duration"),
        },
        "tasks": [
            {
                "id": t.get("id"),
                "name": t.get("name"),
                "state": t.get("state"),
                "type": t.get("taskType"),
                "start_time": t.get("startTime"),
                "end_time": t.get("endTime"),
                "duration": t.get("duration"),
            }
            for t in tasks
        ],
        "dqc_results": dqc_results,
    }


# ===== 调度开关 =====
@router.post("/{wf_id}/schedule/online")
async def schedule_online(
    wf_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("workflow:publish")),
):
    w = _get_or_404(db, wf_id)
    if not check_resource_permission(db, current_user, "workflow", wf_id, "write"):
        raise HTTPException(status_code=404, detail="工作流不存在")
    if w.status != STATUS_ONLINE:
        raise HTTPException(status_code=400, detail="工作流需先发布上线才能开启调度")
    if not w.cron_expression:
        raise HTTPException(status_code=400, detail="未配置 cron 表达式,请先编辑")
    record = _enqueue_sync(db, w.id, "online")
    # 乐观更新本地状态
    w.schedule_status = "ONLINE"
    db.commit()
    db.refresh(w)
    return {
        "message": "已提交调度上线队列，后台同步中",
        "sync_status": record.status,
        "queue_id": record.id,
        **_serialize(w, db),
    }


@router.post("/{wf_id}/schedule/offline")
async def schedule_offline(
    wf_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("workflow:publish")),
):
    w = _get_or_404(db, wf_id)
    if not check_resource_permission(db, current_user, "workflow", wf_id, "write"):
        raise HTTPException(status_code=404, detail="工作流不存在")
    if w.status != STATUS_ONLINE:
        raise HTTPException(status_code=400, detail="工作流需先发布上线才能操作调度")
    if not w.ds_schedule_id:
        raise HTTPException(status_code=400, detail="工作流未配置调度")
    record = _enqueue_sync(db, w.id, "release_schedule")
    w.schedule_status = "OFFLINE"
    db.commit()
    db.refresh(w)
    return {
        "message": "已提交调度下线队列，后台同步中",
        "sync_status": record.status,
        "queue_id": record.id,
        **_serialize(w, db),
    }


@router.get("/{wf_id}/sync-status")
def get_sync_status(
    wf_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """查询工作流的后台同步状态"""
    w = _get_or_404(db, wf_id)
    if not check_resource_permission(db, current_user, "workflow", wf_id, "read"):
        raise HTTPException(status_code=404, detail="工作流不存在")
    records = (
        db.query(WorkflowSyncQueue)
        .filter(WorkflowSyncQueue.workflow_id == wf_id)
        .order_by(WorkflowSyncQueue.created_at.desc())
        .limit(5)
        .all()
    )
    return {
        "workflow_id": wf_id,
        "status": w.status,
        "schedule_status": w.schedule_status,
        "ds_process_code": w.ds_process_code,
        "ds_schedule_id": w.ds_schedule_id,
        "pending_actions": [
            {
                "id": r.id,
                "action": r.action,
                "status": r.status,
                "retry_count": r.retry_count,
                "max_retries": r.max_retries,
                "error_message": r.error_message,
                "created_at": str(r.created_at) if r.created_at else None,
                "completed_at": str(r.completed_at) if r.completed_at else None,
            }
            for r in records
        ],
    }


@router.post("/cron-preview")
async def cron_preview(body: dict):
    """给定 CRON 表达式，返回未来 5 次执行时间"""
    from croniter import croniter
    from datetime import datetime as dt
    cron = body.get("cron_expression", "")
    if not cron or not cron.strip():
        return {"times": []}
    parts = cron.strip().split()
    if len(parts) == 6:
        parts = parts[1:]
    cron5 = " ".join(parts).replace("?", "*")
    try:
        ci = croniter(cron5, dt.now())
        times = [ci.get_next(dt).strftime("%Y-%m-%d %H:%M") for _ in range(5)]
    except Exception:
        return {"times": [], "error": "无效的 CRON 表达式"}
    return {"times": times}
