# Data-Vessel 功能实现方案

## 设计原则

1. **DS 能力优先**：凡 DS 3.4.1 API 已提供的功能，Portal 只做透传/薄封装，不自研替代方案
2. **状态本地缓存**：实例状态以 Portal 本地数据库为准，DS 为辅助数据源，通过 Alert + 轮询同步
3. **用户体验一致性**：所有运维操作（重跑/终止/置成功）在 Portal 内完成，无需跳转 DS 界面
4. **渐进式实现**：P0 功能保证 MVP 可用，P1/P2 功能按迭代逐步补齐

---

## 1. 实例管理系统（P0）

### 1.1 功能描述

实例管理是运维中心的核心功能，包含：
- 实例列表（支持 Tab 筛选 trigger_type）
- 实例操作（重跑、终止、置成功、重跑下游、取消等待）
- 实例详情（信息面板 + 运维态 DAG + 任务列表）
- 批量操作（批量重跑、批量终止、批量置成功）

### 1.2 用户体验设计

**列表页** (`/ops/instances`):
```
┌─────────────────────────────────────────────────────────────┐
│  [全部] [定时] [手动] [补数据] [测试]        [筛选 ▼] [刷新] │
├─────────────────────────────────────────────────────────────┤
│ □  工作流名称    业务日期    类型      状态    开始时间   时长   操作 │
│ □  wf_order_daily 2024-01-15 schedule  success  08:00:00  5min   [日志][重跑]    │
│ □  wf_user_sync   2024-01-15 manual    fail     09:30:00  2min   [日志][重跑][置成功]│
│ □  wf_report_gen  2024-01-14 backfill  running  10:00:00  --     [日志][终止]    │
└─────────────────────────────────────────────────────────────┘
```

**状态颜色**：submit(灰) / waiting(灰) / running(蓝) / pause(黄) / success(绿) / fail(红) / timeout(橙) / kill(灰) / skipped(紫)

**操作按钮动态显示**：
- `submit`/`waiting`: 取消等待
- `running`: 终止运行
- `success`: 查看日志、重跑、重跑下游
- `fail`/`timeout`: 查看日志、重跑、重跑下游、置成功
- `kill`: 查看日志、重跑
- `pause`: 恢复运行、终止运行

**批量操作**：选中多行后底部出现工具栏，仅允许同一 Workflow 且状态兼容的实例操作。

### 1.3 后端实现方案

#### 数据库模型

```python
# app/models/workflow_instance.py
class WorkflowInstance(Base):
    __tablename__ = "workflow_instance"

    id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer, ForeignKey("workflow.id"), nullable=False)
    ds_instance_id = Column(BigInteger)           # DS ProcessInstance ID
    ds_process_code = Column(BigInteger, nullable=False)
    biz_date = Column(Date, nullable=False)
    trigger_type = Column(String(20), nullable=False)  # schedule/manual/test/backfill
    status = Column(String(20), nullable=False, default="submit")
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_ms = Column(BigInteger)
    params_json = Column(JSON)
    complement_id = Column(BigInteger)
    backfill_chain_id = Column(String(64))
    created_by = Column(Integer, ForeignKey("sys_user.id"))
    is_synced = Column(Boolean, default=False)
    last_sync_at = Column(DateTime)
    skip_reason = Column(String(255))
    dry_run = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    workflow = relationship("Workflow")
    tasks = relationship("TaskInstance", back_populates="workflow_instance", cascade="all, delete-orphan")

class TaskInstance(Base):
    __tablename__ = "task_instance"

    id = Column(Integer, primary_key=True)
    workflow_instance_id = Column(Integer, ForeignKey("workflow_instance.id"), nullable=False)
    component_id = Column(Integer, ForeignKey("component.id"))
    ds_task_instance_id = Column(BigInteger)
    ds_task_code = Column(BigInteger, nullable=False)
    task_name = Column(String(255), nullable=False)
    task_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_ms = Column(BigInteger)
    retry_times = Column(Integer, default=0)
    max_retry_times = Column(Integer, default=0)
    log_path = Column(String(512))
    log_content = Column(Text)
    log_last_line = Column(Integer, default=0)
    worker_host = Column(String(255))
    worker_group = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    workflow_instance = relationship("WorkflowInstance", back_populates="tasks")
    component = relationship("Component")
```

#### API 设计

```python
# app/api/instance.py

@router.get("")
async def list_instances(
    workflow_id: int = None,
    trigger_type: str = None,      # schedule/manual/test/backfill
    status: str = None,
    biz_date_start: date = None,
    biz_date_end: date = None,
    backfill_chain_id: str = None,
    search: str = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """
    查询实例列表（优先本地数据库，DS 未同步的实例通过 ds_proxy 透传补充）
    """
    query = db.query(WorkflowInstance).join(Workflow)

    # 权限过滤：developer/analyst 只能看自己有权限的 Workflow 的实例
    if not current_user.is_admin:
        query = query.filter(Workflow.id.in_(accessible_workflow_ids(current_user, db)))

    if workflow_id:
        query = query.filter(WorkflowInstance.workflow_id == workflow_id)
    if trigger_type:
        query = query.filter(WorkflowInstance.trigger_type == trigger_type)
    if status:
        query = query.filter(WorkflowInstance.status == status)
    if biz_date_start:
        query = query.filter(WorkflowInstance.biz_date >= biz_date_start)
    if biz_date_end:
        query = query.filter(WorkflowInstance.biz_date <= biz_date_end)
    if backfill_chain_id:
        query = query.filter(WorkflowInstance.backfill_chain_id == backfill_chain_id)
    if search:
        query = query.filter(Workflow.name.ilike(f"%{search}%"))

    total = query.count()
    items = query.order_by(WorkflowInstance.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()

    return {"total": total, "items": [instance.to_dict() for instance in items]}


@router.post("/{instance_id}/rerun")
async def rerun_instance(
    instance_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """
    重跑实例：调用 DS REPEAT_RUNNING，生成新 instance
    """
    instance = db.query(WorkflowInstance).get(instance_id)
    require_permission("instance:rerun", instance.workflow_id, current_user)

    # 调用 DS API
    ds_client = await DSClient.get_instance()
    result = await ds_client.post(
        f"/projects/{ds_client.project_code}/executors/execute",
        data={
            "workflowInstanceId": instance.ds_instance_id,
            "executeType": "REPEAT_RUNNING",
        }
    )

    # 记录审计日志
    await audit_log(db, current_user, "instance.rerun", instance)

    return {"ok": True, "message": "重跑已提交"}


@router.post("/{instance_id}/kill")
async def kill_instance(
    instance_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """
    终止实例：调用 DS STOP
    """
    instance = db.query(WorkflowInstance).get(instance_id)
    require_permission("instance:kill", instance.workflow_id, current_user)

    ds_client = await DSClient.get_instance()
    await ds_client.post(
        f"/projects/{ds_client.project_code}/executors/execute",
        data={
            "workflowInstanceId": instance.ds_instance_id,
            "executeType": "STOP",
        }
    )

    # 乐观更新本地状态（DS Alert 会最终确认）
    instance.status = "kill"
    instance.end_time = datetime.now()
    db.commit()

    await audit_log(db, current_user, "instance.kill", instance)
    return {"ok": True}


@router.post("/{instance_id}/set-success")
async def set_instance_success(
    instance_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """
    置成功：将失败/超时的 WorkflowInstance 标记为 success
    DS 不支持 Workflow 级别的置成功，需要逐个 Task 调用 force-success，
    然后 Portal 本地标记 WorkflowInstance 状态
    """
    instance = db.query(WorkflowInstance).get(instance_id)
    require_permission("instance:set_success", instance.workflow_id, current_user)

    if instance.status not in ("fail", "timeout"):
        raise HTTPException(400, "仅失败或超时的实例可置成功")

    # 1. 获取该实例的所有失败 Task
    failed_tasks = db.query(TaskInstance).filter(
        TaskInstance.workflow_instance_id == instance_id,
        TaskInstance.status.in_(["fail", "timeout"])
    ).all()

    # 2. 对每个失败 Task 调用 DS force-success
    ds_client = await DSClient.get_instance()
    for task in failed_tasks:
        await ds_client.post(
            f"/projects/{ds_client.project_code}/task-instances/{task.ds_task_instance_id}/force-success"
        )
        task.status = "success"

    # 3. 更新 WorkflowInstance 状态
    instance.status = "success"
    instance.end_time = datetime.now()
    db.commit()

    await audit_log(db, current_user, "instance.set_success", instance)
    return {"ok": True}


@router.post("/{instance_id}/rerun-downstream")
async def rerun_instance_downstream(
    instance_id: int,
    start_node_code: int = Body(...),  # DS TaskDefinition code
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """
    从指定节点重跑该实例及下游：调用 DS execute-task
    """
    instance = db.query(WorkflowInstance).get(instance_id)
    require_permission("instance:rerun_downstream", instance.workflow_id, current_user)

    ds_client = await DSClient.get_instance()
    await ds_client.post(
        f"/projects/{ds_client.project_code}/executors/execute-task",
        data={
            "workflowInstanceId": instance.ds_instance_id,
            "startNodeList": str(start_node_code),
            "taskDependType": "TASK_POST",  # 下游依赖
        }
    )

    await audit_log(db, current_user, "instance.rerun_downstream", instance)
    return {"ok": True}


@router.post("/batch-action")
async def batch_instance_action(
    instance_ids: List[int] = Body(...),
    action: str = Body(...),  # rerun / kill / set_success
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """
    批量操作：同一 Workflow + 状态兼容的实例
    """
    instances = db.query(WorkflowInstance).filter(WorkflowInstance.id.in_(instance_ids)).all()

    # 校验：必须同一 Workflow
    workflow_ids = {i.workflow_id for i in instances}
    if len(workflow_ids) > 1:
        raise HTTPException(400, "批量操作仅支持同一 Workflow 的实例")

    # 校验：状态兼容
    valid_transitions = {
        "rerun": ["success", "fail", "timeout", "kill"],
        "kill": ["submit", "waiting", "running", "pause"],
        "set_success": ["fail", "timeout"],
    }
    for inst in instances:
        if inst.status not in valid_transitions.get(action, []):
            raise HTTPException(400, f"实例 {inst.id} 状态 {inst.status} 不支持 {action}")

    # 调用 DS batch-execute（如支持）或逐个调用
    ds_client = await DSClient.get_instance()
    ds_instance_ids = [i.ds_instance_id for i in instances]

    if action == "kill":
        await ds_client.post(
            f"/projects/{ds_client.project_code}/executors/batch-execute",
            data={
                "workflowInstanceIds": ",".join(map(str, ds_instance_ids)),
                "executeType": "STOP",
            }
        )
    else:
        # rerun / set_success 逐个处理
        for inst in instances:
            if action == "rerun":
                await rerun_instance(inst.id, db, current_user)
            elif action == "set_success":
                await set_instance_success(inst.id, db, current_user)

    await audit_log(db, current_user, f"instance.batch_{action}", None, {"count": len(instances)})
    return {"ok": True, "affected": len(instances)}
```

#### DS 集成点

| Portal 操作 | DS API | 说明 |
|-------------|--------|------|
| 重跑实例 | `POST /executors/execute` (REPEAT_RUNNING) | 直接复用 |
| 终止实例 | `POST /executors/execute` (STOP) | 直接复用 |
| 暂停实例 | `POST /executors/execute` (PAUSE) | 直接复用 |
| 恢复暂停 | `POST /executors/execute` (RECOVER_SUSPENDED_PROCESS) | 直接复用 |
| 从失败恢复 | `POST /executors/execute` (START_FAILURE_TASK_PROCESS) | 直接复用 |
| 从节点重跑 | `POST /executors/execute-task` | 直接复用 |
| 置成功 | `POST /task-instances/{id}/force-success` | 3.4.1 新增，逐个 Task 调用 |
| 批量终止 | `POST /executors/batch-execute` | 直接复用 |
| 查询实例列表 | `GET /workflow-instances` | 本地缓存优先，DS 兜底 |
| 查询任务日志 | `GET /log/detail` | skipLineNum + limit 增量获取 |

### 1.4 前端实现方案

**组件拆分**：
- `InstanceList.vue` — 实例列表页（含 Tab、筛选、批量操作）
- `InstanceDetail.vue` — 实例详情页（信息 + DAG + 任务列表）
- `InstanceTable.vue` — 可复用的实例表格（支持复选框）
- `InstanceActionBar.vue` — 底部批量操作工具栏
- `OpsDagView.vue` — 运维态 DAG（见第 4 节）
- `TaskLogViewer.vue` — 日志查看器（见第 3 节）

**状态管理**（Pinia）：
```typescript
// stores/instance.ts
interface InstanceState {
  instances: WorkflowInstance[];
  selectedIds: number[];
  loading: boolean;
  activeTab: 'all' | 'schedule' | 'manual' | 'backfill' | 'test';
  filters: {
    workflow_id?: number;
    status?: string;
    biz_date_range?: [Date, Date];
  };
}
```

### 1.5 系统协调性

- **与 DS 状态同步**：实例状态以本地 `workflow_instance` 为准，DS Alert 推送变更，轮询兜底。操作（kill/rerun）后乐观更新本地状态，DS Alert 确认后最终一致。
- **与审计日志**：所有实例操作自动记录审计日志。
- **与权限系统**：`require_permission` 校验用户对 Workflow 的资源访问权限。

---

## 2. 补数据系统（P0）

### 2.1 功能描述

- 创建补数据任务（选择日期范围、下游范围、执行策略）
- 追踪补数据进度（按 Workflow 展示实例状态）
- 终止/重跑补数据链条

### 2.2 用户体验设计

**触发入口**：
1. 实例管理页顶部「补数据」按钮
2. Workflow 详情页「补数据」按钮

**BackfillModal（4 步向导）**：

```
步骤 1: 选择日期
┌─────────────────────────────────────────┐
│  日期范围: [2024-01-01] ~ [2024-01-07]  │
│  [x] 排除周末                            │
│  预计生成 7 个实例                        │
└─────────────────────────────────────────┘

步骤 2: 下游范围
┌─────────────────────────────────────────┐
│  (o) 仅当前 Workflow                     │
│  ( ) 包含直接下游 (1 层) — 发现 3 个下游  │
│  ( ) 包含全部下游 — 发现 12 个下游        │
│                                         │
│  ⚠️ 超过 20 个下游 Workflow 不支持       │
└─────────────────────────────────────────┘

步骤 3: 执行策略
┌─────────────────────────────────────────┐
│  (o) Workflow 间串行 + Workflow 内并行   │
│  ( ) 全串行                              │
│  ( ) 按天并行链条                        │
└─────────────────────────────────────────┘

步骤 4: 参数确认
┌─────────────────────────────────────────┐
│  业务日期范围: 2024-01-01 ~ 2024-01-07   │
│  下游 Workflow: wf_a, wf_b, wf_c         │
│  [高级] 全局参数覆盖:                     │
│    dt = ${yyyymmdd}                      │
│                                         │
│  [提交补数据]                            │
└─────────────────────────────────────────┘
```

**提交后**：
- 生成 `backfill_chain_id`（UUID）
- 跳转到实例管理页，自动筛选 `trigger_type=backfill` + `backfill_chain_id=xxx`
- 显示进度条：「3/7 完成，1 失败」

### 2.3 后端实现方案

#### 核心逻辑

```python
# app/api/backfill.py

@router.post("")
async def create_backfill(
    req: BackfillRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """
    创建补数据任务
    """
    workflow = db.query(Workflow).get(req.workflow_id)
    require_permission("backfill:create", workflow.id, current_user)

    # 生成链条 ID
    chain_id = generate_backfill_chain_id()

    # 获取下游 Workflow 列表
    downstream_workflows = []
    if req.include_downstream == "direct":
        downstream_workflows = get_direct_downstreams(workflow.id, db)
    elif req.include_downstream == "all":
        downstream_workflows = get_all_downstreams(workflow.id, db)

    # 限制检查
    all_workflows = [workflow] + downstream_workflows
    if len(all_workflows) > 20:
        raise HTTPException(400, f"下游 Workflow 数量 {len(all_workflows)} 超过限制 20")

    # 日期范围校验（最近 7 天）
    date_list = generate_date_list(req.start_date, req.end_date, req.exclude_weekend)
    if len(date_list) > 7:
        raise HTTPException(400, f"补数据日期范围超过 7 天")

    # 按拓扑排序执行
    ds_client = await DSClient.get_instance()

    if req.strategy == "serial_parallel":  # 默认：Workflow 间串行 + Workflow 内并行
        for wf in topological_sort(all_workflows):
            # 调用 DS Complement
            result = await ds_client.post(
                f"/projects/{ds_client.project_code}/executors/start-workflow-instance",
                data={
                    "workflowDefinitionCode": wf.ds_process_code,
                    "execType": "COMPLEMENT_DATA",
                    "scheduleTime": json.dumps({
                        "complementScheduleDateList": ",".join(
                            d.strftime("%Y-%m-%d %H:%M:%S") for d in date_list
                        )
                    }),
                    "runMode": "RUN_MODE_PARALLEL",  # Workflow 内并行
                    "failureStrategy": "CONTINUE",
                    "executionOrder": "ASC_ORDER",
                    "workerGroup": wf.worker_group or "default",
                }
            )

            # 记录本地实例（异步，等 DS Alert 或轮询创建）
            # complement 返回的是 instance ID 列表
            instance_ids = result.get("data", [])
            for instance_id in instance_ids:
                # 创建待同步记录
                await create_pending_instance(
                    db, workflow_id=wf.id,
                    ds_instance_id=instance_id,
                    backfill_chain_id=chain_id,
                    trigger_type="backfill",
                )

    elif req.strategy == "all_serial":
        # 全串行：逐个 Workflow 逐个日期串行
        ...

    elif req.strategy == "day_parallel":
        # 按天并行链条
        ...

    await audit_log(db, current_user, "backfill.create", None, {
        "chain_id": chain_id,
        "workflows": [w.id for w in all_workflows],
        "dates": [d.isoformat() for d in date_list],
    })

    return {"chain_id": chain_id, "workflow_count": len(all_workflows), "date_count": len(date_list)}
```

#### DS 集成点

| Portal 功能 | DS API | 说明 |
|-------------|--------|------|
| 当前 Workflow 补数据 | `POST /executors/start-workflow-instance` (COMPLEMENT_DATA) | 直接复用 |
| 下游 Workflow 补数据 | 同上，Portal 按拓扑排序依次调用 | 自研调度 |
| 终止补数据链条 | 遍历链条内所有 running 实例，逐个调用 STOP | 自研封装 |

### 2.4 系统协调性

- **与血缘系统**：补数据前通过 `workflow_dependency` 获取下游 Workflow，依赖血缘系统的准确性。
- **与实例同步**：补数据生成的 instance 通过 DS Alert 同步到本地，携带 `backfill_chain_id`。
- **与权限**：创建补数据需要 `backfill:create` 权限。

---

## 3. 日志查看器（P0）

### 3.1 功能描述

- 实时刷新运行中任务的日志
- 终态任务日志查看（支持搜索、高亮、级别过滤）
- 日志下载

### 3.2 用户体验设计

```
┌─────────────────────────────────────────────────────────────┐
│  任务: wf_order_daily > extract_order                        │
│  状态: running  [● 实时刷新中]                                │
├─────────────────────────────────────────────────────────────┤
│  [搜索...]  [全部] [INFO] [WARN] [ERROR]          [下载日志] │
├─────────────────────────────────────────────────────────────┤
│ 2024-01-15 08:00:01 [INFO]  Starting task extract_order    │
│ 2024-01-15 08:00:02 [INFO]  Connecting to datasource...    │
│ 2024-01-15 08:00:03 [WARN]  Slow query detected (2.3s)     │
│ 2024-01-15 08:00:05 [ERROR] Connection timeout            │  ← 红底高亮
│ 2024-01-15 08:00:05 [INFO]  Retrying (1/3)...              │
│ ...                                                          │
│ 共 1,234 行 | 匹配 "ERROR": 3 处                            │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 后端实现方案

```python
# app/api/instance.py (日志相关)

@router.get("/tasks/{task_instance_id}/log")
async def get_task_log(
    task_instance_id: int,
    skip_line: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    获取任务日志（增量模式）
    """
    task = db.query(TaskInstance).get(task_instance_id)

    ds_client = await DSClient.get_instance()
    result = await ds_client.get(
        f"/projects/{ds_client.project_code}/log/detail",
        params={
            "taskInstanceId": task.ds_task_instance_id,
            "skipLineNum": skip_line,
            "limit": limit,
        }
    )

    # DS 返回格式: { "data": { "lineNum": 1234, "message": "日志内容" } }
    log_data = result.get("data", {})
    lines = log_data.get("message", "").split("\n")
    next_line = log_data.get("lineNum", skip_line)

    return {
        "lines": lines,
        "next_line": next_line,
        "has_more": len(lines) >= limit,
    }
```

### 3.4 前端实现方案

```typescript
// 日志轮询 Hook
function useTaskLog(taskInstanceId: number, isRunning: boolean) {
  const [lines, setLines] = useState<string[]>([]);
  const [nextLine, setNextLine] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [levelFilter, setLevelFilter] = useState<"all" | "info" | "warn" | "error">("all");

  // 增量拉取
  useEffect(() => {
    if (!isRunning) return;
    const interval = setInterval(async () => {
      const res = await api.get(`/instances/tasks/${taskInstanceId}/log`, {
        params: { skip_line: nextLine, limit: 200 }
      });
      setLines(prev => [...prev, ...res.data.lines]);
      setNextLine(res.data.next_line);
    }, 3000);
    return () => clearInterval(interval);
  }, [taskInstanceId, isRunning, nextLine]);

  // 过滤 + 搜索
  const filteredLines = useMemo(() => {
    let result = lines;
    if (levelFilter !== "all") {
      const levelPattern = new RegExp(`\\[${levelFilter.toUpperCase()}\\]`, "i");
      result = result.filter(l => levelPattern.test(l));
    }
    if (searchQuery) {
      result = result.filter(l => l.includes(searchQuery));
    }
    return result;
  }, [lines, levelFilter, searchQuery]);

  return { lines: filteredLines, searchQuery, setSearchQuery, levelFilter, setLevelFilter };
}
```

### 3.5 DS 集成点

| Portal 功能 | DS API | 说明 |
|-------------|--------|------|
| 获取日志 | `GET /log/detail` | skipLineNum + limit 增量获取 |
| 下载日志 | `GET /log/download-log` | 直接复用 |

---

## 4. 运维态 DAG（P0）

### 4.1 功能描述

实例详情页内嵌的只读 DAG 图，带实时状态着色和运维操作。

### 4.2 用户体验设计

```
┌─────────────────────────────────────────────────────────────┐
│ 实例: wf_order_daily #12345  [success]                       │
├─────────────────────────────────────────────────────────────┤
│  [全部] [上游路径] [下游路径] [仅当前]                        │
├─────────────────────────────────────────────────────────────┤
│                    ┌─────────┐                              │
│                    │ extract │ success                       │
│                    └────┬────┘                              │
│              ┌──────────┼──────────┐                        │
│         ┌────┴────┐    │    ┌────┴────┐                    │
│         │transform│ success  │  load   │ success            │
│         └────┬────┘         └─────────┘                    │
│              │                                               │
│         ┌────┴────┐                                         │
│         │ report  │ fail  ← 红底闪烁                        │
│         └─────────┘                                         │
├─────────────────────────────────────────────────────────────┤
│  任务列表                                                    │
│  [extract] success  08:00:00  2min  [日志]                   │
│  [transform] success 08:02:00  1min  [日志]                  │
│  [load] success     08:03:00  1min  [日志]                   │
│  [report] fail      08:04:00  30s   [日志][重跑][置成功]    │
└─────────────────────────────────────────────────────────────┘
```

**右键菜单**（根据节点状态）：
- success: 查看日志、重跑该节点
- fail: 查看日志、重跑该节点、置成功、重跑该节点及下游
- running: 查看日志、终止该节点
- waiting/submit: 只读

### 4.3 前端实现方案

```vue
<!-- OpsDagView.vue -->
<template>
  <VueFlow
    :nodes="nodes"
    :edges="edges"
    :node-types="nodeTypes"
    @node-context-menu="onNodeContextMenu"
    @node-click="onNodeClick"
  >
    <template #node-custom="{ data }">
      <DagNode
        :label="data.task_name"
        :status="data.status"
        :is-highlighted="highlightedNodes.has(data.id)"
        :is-dimmed="dimmedNodes.has(data.id)"
      />
    </template>
  </VueFlow>

  <!-- 右键菜单 -->
  <ContextMenu v-if="contextMenu.visible" :position="contextMenu.position">
    <MenuItem v-for="item in contextMenuItems" :key="item.action" @click="handleAction(item)">
      {{ item.label }}
    </MenuItem>
  </ContextMenu>
</template>

<script setup>
const props = defineProps({
  workflowInstanceId: Number,
  dagJson: Object,        // Workflow 的 DAG 结构
  taskInstances: Array,   // 该实例的所有 TaskInstance
});

// 节点状态着色
const nodes = computed(() => {
  return props.dagJson.nodes.map(node => {
    const task = props.taskInstances.find(t => t.ds_task_code === node.task_code);
    return {
      id: String(node.id),
      type: 'custom',
      position: node.position,
      data: {
        task_name: task?.task_name || node.name,
        status: task?.status || 'waiting',
        task_instance_id: task?.id,
      },
      style: {
        borderColor: statusColor(task?.status),
        backgroundColor: statusBgColor(task?.status),
      }
    };
  });
});

// 单击高亮上下游
function onNodeClick(node) {
  const upstream = getUpstreamNodes(node.id, props.dagJson.edges);
  const downstream = getDownstreamNodes(node.id, props.dagJson.edges);
  highlightedNodes.value = new Set([node.id, ...upstream, ...downstream]);
  dimmedNodes.value = new Set(
    props.dagJson.nodes.map(n => n.id).filter(id => !highlightedNodes.value.has(id))
  );
}

// 右键菜单项根据状态动态生成
const contextMenuItems = computed(() => {
  const task = selectedTask.value;
  if (!task) return [];

  const items = [{ label: '查看日志', action: 'view_log' }];

  if (task.status === 'success') {
    items.push({ label: '重跑该节点', action: 'rerun_node' });
  } else if (task.status === 'fail') {
    items.push(
      { label: '重跑该节点', action: 'rerun_node' },
      { label: '置成功', action: 'force_success' },
      { label: '重跑该节点及下游', action: 'rerun_downstream' },
    );
  } else if (task.status === 'running') {
    items.push({ label: '终止该节点', action: 'kill_node' });
  }
  return items;
});
</script>
```

### 4.4 DS 集成点

| Portal 功能 | DS API | 说明 |
|-------------|--------|------|
| 重跑该节点 | `POST /executors/execute-task` | startNodeList = 该节点 code |
| 重跑该节点及下游 | `POST /executors/execute-task` | startNodeList = 该节点 code, taskDependType=TASK_POST |
| 终止该节点 | DS 不支持单节点 kill | Portal 需特殊处理（或调用 Workflow STOP） |

**注意**：DS 3.4.1 不支持「终止单个任务节点」，只能终止整个 WorkflowInstance。如果用户点击「终止该节点」，Portal 的实际行为应该是终止整个实例，并在确认对话框中明确告知用户。

---

## 5. 监控报警系统（P1）

### 5.1 功能描述

- 告警规则配置（按 Workflow 或全局）
- 告警触发（失败/超时/到点未触发）
- 告警历史查看
- 通知发送（邮件/飞书/钉钉/企微）

### 5.2 后端实现方案

#### 告警触发机制

```python
# app/core/alert_engine.py

async def check_instance_failure(instance: WorkflowInstance):
    """实例失败触发告警"""
    rules = db.query(AlertRule).filter(
        or_(
            AlertRule.workflow_id == instance.workflow_id,
            AlertRule.workflow_id.is_(None)  # 全局规则
        ),
        AlertRule.alert_type == "failure",
        AlertRule.is_enabled == True,
    ).all()

    for rule in rules:
        await trigger_alert(rule, instance, "failure")

async def check_instance_timeout(instance: WorkflowInstance):
    """实例超时触发告警"""
    workflow = db.query(Workflow).get(instance.workflow_id)
    if not workflow.max_running_time:
        return

    running_duration = (datetime.now() - instance.start_time).total_seconds() / 60
    if running_duration > workflow.max_running_time:
        rules = db.query(AlertRule).filter(
            or_(AlertRule.workflow_id == instance.workflow_id, AlertRule.workflow_id.is_(None)),
            AlertRule.alert_type == "timeout",
            AlertRule.is_enabled == True,
        ).all()
        for rule in rules:
            await trigger_alert(rule, instance, "timeout")

async def check_not_triggered():
    """到点未触发检查（后台定时任务，每分钟执行）"""
    # 查询 schedule_status=ONLINE 的 Workflow
    # 检查当前时间是否超过期望触发时间 + 容忍窗口（如 15 分钟）
    # 如果该 Workflow 在期望时间点没有生成 running/submit 状态的实例，触发告警
    ...

async def trigger_alert(rule: AlertRule, instance: WorkflowInstance, trigger_type: str):
    """触发告警并发送通知"""
    # 1. 创建告警历史记录
    alert_history = AlertHistory(
        alert_rule_id=rule.id,
        workflow_id=instance.workflow_id,
        workflow_instance_id=instance.id,
        trigger_type=trigger_type,
        status="triggered",
        content=build_alert_content(rule, instance, trigger_type),
        notify_channels=rule.notify_channels,
        notify_targets=rule.notify_targets,
    )
    db.add(alert_history)
    db.commit()

    # 2. 发送通知
    for channel in rule.notify_channels:
        try:
            notifier = get_notifier(channel)
            await notifier.send(
                targets=rule.notify_targets,
                title=f"[告警] Workflow {instance.workflow.name} {trigger_type}",
                content=alert_history.content,
            )
            alert_history.status = "sent"
        except Exception as e:
            alert_history.status = "failed"
            alert_history.error_msg = str(e)

    db.commit()
```

#### 告警收敛

```python
# app/core/alert_engine.py

async def should_send_alert(rule: AlertRule, instance: WorkflowInstance) -> bool:
    """判断是否应该发送告警（避免轰炸）"""
    # 首次失败：立即发送
    # 连续失败：每日发摘要
    # 成功恢复：发送恢复通知

    recent_alerts = db.query(AlertHistory).filter(
        AlertHistory.alert_rule_id == rule.id,
        AlertHistory.workflow_id == instance.workflow_id,
        AlertHistory.created_at >= datetime.now() - timedelta(hours=24),
    ).order_by(AlertHistory.created_at.desc()).all()

    if not recent_alerts:
        return True  # 首次失败，立即发送

    last_alert = recent_alerts[0]

    # 如果上次是今天已经发送过，且不是恢复通知，则不发送
    if last_alert.created_at.date() == datetime.now().date() and last_alert.trigger_type == "failure":
        return False  # 今日已发送过，等每日摘要

    return True
```

### 5.3 DS 集成点

| Portal 功能 | DS API | 说明 |
|-------------|--------|------|
| 实例失败检测 | DS Alert HTTP 回调 + 本地轮询 | 混合方案 |
| 实例超时检测 | Portal 本地定时任务检查 | 自研 |
| 到点未触发 | Portal 本地定时任务检查 | 自研 |
| 通知发送 | `notifier.py` 邮件/IM | 已有能力 |

---

## 6. 审计日志（P1）

### 6.1 功能描述

记录所有运维操作，支持查询和导出。

### 6.2 后端实现方案

```python
# app/core/audit.py

from enum import Enum

class AuditAction(str, Enum):
    WORKFLOW_PUBLISH = "workflow.publish"
    WORKFLOW_ONLINE = "workflow.online"
    WORKFLOW_OFFLINE = "workflow.offline"
    WORKFLOW_FORCE_UNLOCK = "workflow.force_unlock"
    INSTANCE_RERUN = "instance.rerun"
    INSTANCE_KILL = "instance.kill"
    INSTANCE_SET_SUCCESS = "instance.set_success"
    INSTANCE_RERUN_DOWNSTREAM = "instance.rerun_downstream"
    BACKFILL_CREATE = "backfill.create"
    BACKFILL_KILL = "backfill.kill"

async def audit_log(
    db: Session,
    user: SysUser,
    action: AuditAction,
    target: Any = None,
    details: dict = None,
    request: Request = None,
):
    """记录审计日志"""
    log = AuditLog(
        user_id=user.id,
        action=action.value,
        target_type=target.__tablename__ if hasattr(target, "__tablename__") else (details or {}).get("target_type"),
        target_id=str(target.id) if target and hasattr(target, "id") else None,
        details=details or {},
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(log)
    db.commit()

# 装饰器模式（推荐）
def audit(action: AuditAction):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            db = kwargs.get("db")
            current_user = kwargs.get("current_user")
            request = kwargs.get("request")

            result = await func(*args, **kwargs)

            # 异步记录审计日志（不阻塞响应）
            asyncio.create_task(audit_log(
                db, current_user, action,
                target=kwargs.get("instance") or kwargs.get("workflow"),
                request=request,
            ))
            return result
        return wrapper
    return decorator

# 使用示例
@router.post("/{instance_id}/rerun")
@audit(AuditAction.INSTANCE_RERUN)
async def rerun_instance(...):
    ...
```

### 6.3 前端实现方案

```vue
<!-- AuditLog.vue -->
<template>
  <div>
    <a-form :model="filters" layout="inline">
      <a-form-item label="操作人">
        <UserSelect v-model="filters.user_id" />
      </a-form-item>
      <a-form-item label="操作类型">
        <a-select v-model="filters.action" :options="actionOptions" />
      </a-form-item>
      <a-form-item label="时间范围">
        <a-range-picker v-model="filters.date_range" />
      </a-form-item>
      <a-form-item>
        <a-button type="primary" @click="search">查询</a-button>
        <a-button @click="exportLogs">导出</a-button>
      </a-form-item>
    </a-form>

    <a-table :columns="columns" :data="logs" :pagination="pagination">
      <template #action="{ record }">
        <a-tag :color="actionColor(record.action)">{{ record.action }}</a-tag>
      </template>
    </a-table>
  </div>
</template>
```

---

## 7. 血缘系统（P1）

### 7.1 功能描述

- 组件内字段级血缘（SQLGlot 解析）
- 跨 Workflow 表级依赖自动发现
- 血缘可视化（DAG 形式展示）
- 影响分析（字段变更影响范围）

### 7.2 后端实现方案

#### SQLGlot 血缘解析

```python
# app/core/lineage_parser.py

import sqlglot
from sqlglot.lineage import lineage

def parse_sql_lineage(component_id: int, sql: str, db_name: str) -> List[LineageNode]:
    """
    使用 SQLGlot 解析 SQL，提取字段级血缘
    """
    try:
        # 解析 SQL
        parsed = sqlglot.parse_one(sql)

        # 提取 SELECT 列
        for col in parsed.find_all(sqlglot.exp.Alias):
            column_name = col.alias
            source_columns = []

            # 追溯来源字段
            for source in lineage(column_name, sql).source.columns:
                source_columns.append({
                    "db": db_name,
                    "table": source.table,
                    "column": source.name,
                })

            # 创建节点
            target_node = LineageNode(
                component_id=component_id,
                db_name=db_name,
                table_name=get_target_table(parsed),
                column_name=column_name,
                node_type="target",
                transform_logic=str(col),
            )

            for src in source_columns:
                source_node = find_or_create_node(component_id, src["db"], src["table"], src["column"])
                LineageEdge(
                    from_node_id=source_node.id,
                    to_node_id=target_node.id,
                    transform_type="select",
                    confidence=1.0,
                )

    except Exception as e:
        logger.warning(f"SQLGlot 解析失败: {e}")
        return []
```

#### 跨 Workflow 依赖发现

```python
# app/core/workflow_dependency_discovery.py

def discover_workflow_dependencies(workflow_id: int, db: Session) -> List[WorkflowDependency]:
    """
    自动发现 Workflow 之间的依赖关系
    """
    workflow = db.query(Workflow).get(workflow_id)
    dag = json.loads(workflow.dag_json)

    # 1. 收集当前 Workflow 的所有输出表
    output_tables = set()
    for node in dag["nodes"]:
        component = db.query(Component).get(node["component_id"])
        tables = extract_output_tables(component)
        output_tables.update(tables)

    # 2. 遍历所有其他 Workflow，检查是否有输入表匹配当前 Workflow 的输出表
    other_workflows = db.query(Workflow).filter(Workflow.id != workflow_id).all()
    dependencies = []

    for other in other_workflows:
        other_dag = json.loads(other.dag_json)
        for node in other_dag["nodes"]:
            component = db.query(Component).get(node["component_id"])
            input_tables = extract_input_tables(component)

            for out_table in output_tables:
                if out_table in input_tables:
                    dep = WorkflowDependency(
                        upstream_workflow_id=workflow_id,
                        downstream_workflow_id=other.id,
                        source_table=out_table,
                        target_table=out_table,
                        confidence=1.0 if component.type in ("sql", "datax") else 0.7,
                    )
                    dependencies.append(dep)

    return dependencies

def extract_output_tables(component: Component) -> Set[str]:
    """提取组件的输出表"""
    if component.type == "sql":
        return extract_sql_output_tables(component.config_json["sql"])
    elif component.type == "datax":
        return {component.config_json["writer"]["table"]}
    elif component.type == "python":
        return extract_python_tables(component.config_json["script"])
    elif component.type == "shell":
        return extract_shell_tables(component.config_json["script"])
    return set()
```

### 7.3 前端实现方案

```vue
<!-- DataLineage.vue -->
<template>
  <div class="lineage-page">
    <a-tabs>
      <a-tab-pane key="field" title="字段血缘">
        <VueFlow :nodes="fieldNodes" :edges="fieldEdges" />
      </a-tab-pane>
      <a-tab-pane key="workflow" title="Workflow 依赖">
        <VueFlow :nodes="workflowNodes" :edges="workflowEdges" />
      </a-tab-pane>
    </a-tabs>

    <!-- 影响分析面板 -->
    <a-drawer v-model:visible="impactPanelVisible" title="影响分析">
      <p>修改字段 <strong>{{ selectedField }}</strong> 将影响：</p>
      <a-tree :data="impactTree" />
    </a-drawer>
  </div>
</template>
```

---

## 8. 工作流版本管理（P2）

### 8.1 后端实现方案

```python
# app/api/workflow.py

@router.post("/{wf_id}/publish")
async def publish_workflow(
    wf_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """
    发布 Workflow：同步到 DS + 创建版本快照
    """
    workflow = db.query(Workflow).get(wf_id)

    # 1. 创建版本快照
    version = WorkflowVersion(
        workflow_id=workflow.id,
        version=workflow.version + 1,
        dag_json=workflow.dag_json,
        schedule_config=get_schedule_config(workflow),
        node_configs=get_node_configs(workflow.id, db),
        change_summary=generate_change_summary(workflow, db),
        published_by=current_user.id,
        published_at=datetime.now(),
    )
    db.add(version)

    # 2. 递增版本号
    workflow.version += 1

    # 3. 同步到 DS（通过 publisher + outbox）
    ...

    db.commit()
    return {"version": workflow.version}

@router.post("/{wf_id}/rollback")
async def rollback_workflow(
    wf_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """
    回滚到指定版本：创建新版本，复制旧版本内容
    """
    workflow = db.query(Workflow).get(wf_id)
    target_version = db.query(WorkflowVersion).get(version_id)

    # 复制旧版本内容到新版本
    new_version = WorkflowVersion(
        workflow_id=workflow.id,
        version=workflow.version + 1,
        dag_json=target_version.dag_json,
        schedule_config=target_version.schedule_config,
        node_configs=target_version.node_configs,
        change_summary=f"回滚到版本 {target_version.version}",
        published_by=current_user.id,
        published_at=datetime.now(),
    )
    db.add(new_version)

    # 更新 Workflow 当前内容
    workflow.dag_json = target_version.dag_json
    workflow.status = "draft"
    workflow.version += 1

    db.commit()
    return {"version": workflow.version}
```

---

## 9. 节点级调度属性（P2）

### 9.1 后端实现方案

节点属性存储在 `workflow_node_config` 表，DSL 翻译时合并到 TaskDefinition 的 `taskParams` 中。

```python
# app/core/dsl_translator.py

def build_task_definition(node: DagNode, workflow: Workflow, db: Session) -> dict:
    """构建 DS TaskDefinition，合并节点级属性"""
    component = db.query(Component).get(node.component_id)
    node_config = db.query(WorkflowNodeConfig).filter_by(
        workflow_id=workflow.id,
        component_id=component.id,
    ).first()

    task_params = {
        "resourceList": [],
        "localParams": [],
        "dependence": {},
        ...
    }

    # 合并节点级属性
    if node_config:
        if node_config.retry_times > 0:
            task_params["retryTimes"] = node_config.retry_times
            task_params["retryInterval"] = node_config.retry_interval
        if node_config.timeout_minutes:
            task_params["timeout"] = node_config.timeout_minutes
        if node_config.worker_group:
            task_params["workerGroup"] = node_config.worker_group
        if node_config.priority:
            task_params["taskPriority"] = node_config.priority

    return {
        "code": node.task_code,
        "name": node.name,
        "taskType": component.type,
        "taskParams": task_params,
        ...
    }
```

---

## 附录：DS API 调用速查表

### Executor API

| 操作 | 端点 | 方法 | 关键参数 |
|------|------|------|----------|
| 启动工作流 | `/executors/start-workflow-instance` | POST | workflowDefinitionCode, execType=START_PROCESS |
| 补数据 | `/executors/start-workflow-instance` | POST | workflowDefinitionCode, execType=COMPLEMENT_DATA, scheduleTime |
| 暂停 | `/executors/execute` | POST | workflowInstanceId, executeType=PAUSE |
| 终止 | `/executors/execute` | POST | workflowInstanceId, executeType=STOP |
| 重跑 | `/executors/execute` | POST | workflowInstanceId, executeType=REPEAT_RUNNING |
| 恢复暂停 | `/executors/execute` | POST | workflowInstanceId, executeType=RECOVER_SUSPENDED_PROCESS |
| 从失败恢复 | `/executors/execute` | POST | workflowInstanceId, executeType=START_FAILURE_TASK_PROCESS |
| 从节点重跑 | `/executors/execute-task` | POST | workflowInstanceId, startNodeList, taskDependType |
| 批量执行 | `/executors/batch-execute` | POST | workflowInstanceIds, executeType |

### ProcessInstance API

| 操作 | 端点 | 方法 | 关键参数 |
|------|------|------|----------|
| 查询列表 | `/workflow-instances` | GET | workflowDefinitionCode, stateType, startDate, endDate |
| 查询详情 | `/workflow-instances/{id}` | GET | id |
| 删除 | `/workflow-instances/{id}` | DELETE | id |
| 批量删除 | `/workflow-instances/batch-delete` | POST | workflowInstanceIds |

### TaskInstance API

| 操作 | 端点 | 方法 | 关键参数 |
|------|------|------|----------|
| 查询列表 | `/task-instances` | GET | workflowInstanceId, stateType, startDate, endDate |
| 置成功 | `/task-instances/{id}/force-success` | POST | id |

### Logger API

| 操作 | 端点 | 方法 | 关键参数 |
|------|------|------|----------|
| 获取日志 | `/log/detail` | GET | taskInstanceId, skipLineNum, limit |
| 下载日志 | `/log/download-log` | GET | taskInstanceId |

### Scheduler API

| 操作 | 端点 | 方法 | 关键参数 |
|------|------|------|----------|
| 上线 | `/schedules/{id}/online` | POST | id |
| 下线 | `/schedules/{id}/offline` | POST | id |
| 预览 Cron | `/schedules/preview` | POST | schedule.crontab |
