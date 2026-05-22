# Data-Vessel 领域上下文

数据中台门户（DMP Portal），金融行业离线数据统一工作台。Portal 是唯一的控制面，DolphinScheduler 仅作为执行器。

---

## 核心领域术语

### Component（组件）

用户创建的可复用任务单元，最小开发单元。

**新建流程**：用户点击"新建 SQL 组件"后，系统直接在编辑器中打开一个临时草稿标签页（类似 IDE 的 Untitled）。用户可以先写 SQL 再保存，保存时才弹出命名/选择文件夹对话框，真正创建到数据库。

**保存要求**：首次保存时必须填写组件名称、选择所属文件夹、选择数据源。保存后状态为 `draft`。

**类型（type）**：
- `sql` — SQL 查询/执行
- `python` — Python 脚本
- `shell` — Shell 脚本
- `datax` — 数据同步任务

**配置（config_json）**：按类型不同结构不同：
- SQL: `{ datasource_id, sql, timeout }`
- Python/Shell: `{ script, timeout }`
- DataX: `{ reader, writer, source_id, target_id, ... }`

**参数（params）**：运行时占位符定义，如 `[{"key": "dt", "value": "${yyyymmdd-7}"}]`。与 `config_json` 的区别：`config_json` 是组件的固定配置，`params` 是每次运行可能变化的值（如日期）。执行前由参数引擎替换为实际值。

**状态（status）**：`draft` → `tested` → `online` → `offline`。只有 4 个状态。

**版本（version）**：每次发布自动递增。Component 有独立版本控制，修改后不会自动同步到引用它的 Workflow。

**Worker 组路由**：`worker_group` 字段（`default` | `sync-worker` | `sql-worker`），控制任务在哪个 Worker 节点上执行。**字段尚未添加** ⏳

### Workflow（工作流）

由多个 Component 组成的有向无环图（DAG）。

**结构**：
- `dag_json` — DAG 节点（Component 引用）+ 连线（edges）
- `steps_json` — 旧版线性步骤（兼容保留）

**状态（status）**：`draft` → `tested` → `online` → `offline`。

**调度状态（schedule_status）**：`ONLINE` / `OFFLINE`。控制 DolphinScheduler 的定时调度开关，与 `status` 是两回事。`status=online` 表示已发布到 DS 可执行；`schedule_status=ONLINE` 表示定时调度已开启。

**最大运行时间**：`max_running_time`（分钟），0 = 默认 24h（不配置时的兜底值）。**字段尚未添加** ⏳

**跳过日期**：`skip_dates`（JSON 数组，如 `["2024-01-01", "2024-01-02"]`），需要跳过的业务日期。**字段尚未添加** ⏳

**生效日期**：`effective_start_date` / `effective_end_date`，调度有效期范围。**字段尚未添加** ⏳

**标签**：`tags`（JSON 数组），用于工作流列表筛选。**字段尚未添加** ⏳

### DataSource（数据源）

统一的数据库连接实体。不分"来源库"/"目标库"类型，所有场景共用同一张表。用户创建后，由 Component（SQL/DataX）和 DQC Rule 引用。

**测试库配置**：支持 `test_connection_info` 字段（或 `test_datasource_id` 外键指向另一 DataSource），测试运行时 DSL 翻译层将数据源替换为测试库连接。**字段尚未添加，替换逻辑尚未实现** ⏳

### Publish（发布）

将 Portal 的 Workflow 同步到 DolphinScheduler，使其可在 DS 侧执行。发布成功后 Workflow `status` 变为 `online`。

发布流程包含：组件翻译为 TaskDefinition、创建工作流 ProcessDefinition、同步数据源密码、分配任务编码、设置调度规则。

### DSL（翻译流水线）

Portal 内部模型到 DS 原生格式的翻译层。
- Component → DS TaskDefinition JSON
- Workflow → DS ProcessDefinition（taskDefinitionJson + taskRelationJson）
- DataX 不走 DS 原生 DataX 节点，翻译为 SHELL 节点 + heredoc 内嵌 JSON

### Param Engine（参数引擎）

执行前替换参数占位符，对标 DataWorks 调度参数体系。

**两种时间基准**：
- **`${...}`** — 基于**业务日期**（T-1，数据的日期），精度为天。支持年/月/周/天偏移。`${yyyymmdd}` 等价于 `$bizdate`。
- **`$[...]`** — 基于**定时时间**（T，任务运行的日期），精度为秒。支持天/小时/分钟偏移。`$[yyyymmddhh24miss]` 等价于 `$cyctime`。**二期实现** ⏳

**系统内置参数**：
- `$bizdate` — 业务日期，`yyyymmdd` 格式
- `$cyctime` — 定时时间，`yyyymmddhh24miss` 格式
- `$gmtdate` — 当前日期，`yyyymmdd` 格式
- `$bizmonth` — 业务月份，有特殊逻辑：若业务日期与当前时间同月则取上月，否则取业务日期所在月

**偏移计算**：
- `${yyyymmdd-7}` — 业务日期前 7 天
- `$[yyyymmdd-1]` — 定时时间前 1 天
- `$[hh24-1/24]` — 定时时间前 1 小时
- `$[mi-15/24/60]` — 定时时间前 15 分钟

**高级用法**：
- **字符串拼接**：`${yyyymm}01` 获取月初
- **引擎函数二次处理**：在 SQL 中用 `DATEADD`、`REPLACE` 等函数对参数返回值再加工（如获取上月最后一天）
- **补数据场景**：手动选择业务日期后，`${...}` 基于该日期，`$[...]` 基于该日期+1 天

**自定义参数**：Component 的 `params` 中定义，值可引用其他参数（按定义顺序解析，不支持前向引用）；手动运行时可传入 `runtime_overrides` 覆盖。

### DQC（数据质量）

对标阿里 DataWorks 的数据质量子系统。

**DqcRule**：规则定义。`rule_type` 包括 `row_count`、`null_percent`、`custom_sql` 等 14 种。绑定到 DataSource + 表 + 列。

**DqcCheck**：单次规则执行的结果记录。

**DqcReport**：按配置定时聚合 DqcCheck 结果生成的报告。通知走邮件/飞书/钉钉/企微 Webhook。

**触发方式**：组件执行时自动触发关联的 DQC 规则（`is_strong=true` 时检查结果失败会阻塞下游节点）；APScheduler 定时生成报告。

### Outbox（同步队列）

`WorkflowSyncQueue` — 异步 DS 同步队列。工作流发布/上线/下线等状态变更先入队，由后台调度器消费并同步到 DS。10 秒轮询，指数退避重试。

---

## 系统架构

### DS 版本与部署策略

- **目标版本**：DolphinScheduler 3.4.1（从 3.2.2 升级）
- **升级驱动力**：稳定性修复 + 更完善的 complement API + CVE 安全补丁
- **升级计划**：先在内网测试环境验证（`192.168.1.3`），确认 DS 数据迁移脚本无问题后，通知用户安排停机窗口执行升级
- **部署模式**：支持单机（standalone）和集群两种模式，由用户选择
- **注册中心**：PostgreSQL JDBC 模式（`registry.type=jdbc`），替代 ZooKeeper
- **元数据存储**：PostgreSQL（与 Portal 共用实例，独立 database）
- **单一 DS 实例**：不存在多 DS 集群场景

### DS 3.4.1 与 3.2.2 的关键差异（影响 Portal 设计）

**1. 补数据架构重构**
- API 层与 Master 层通过 RPC（`IWorkflowControlClient`）分离，补数据请求从 API 同步调用 Master
- `complementDependentMode=ALL_DEPENDENT` 在 3.4.1 中为空实现（`// todo`），**Portal 跨 Workflow 补数据必须完全自研**
- 补数据时间参数 `scheduleTime` 支持两种格式：日期范围 JSON（`complementStartDate`/`complementEndDate`）或手动列表（`complementScheduleDateList`）
- Portal 建议使用手动列表模式，精确控制日期

**2. Workflow 状态精简**
- 3.2.2 的 `ExecutionStatus`（26 种）→ 3.4.1 的 `WorkflowExecutionStatus`（10 种）
- 新增中间状态：`READY_PAUSE`、`READY_STOP`、`SERIAL_WAIT`、`FAILOVER`
- 每个状态显式声明 `finalState`/`needFailover` 等元属性

**3. HTTP Alert payload 格式**
- Alert 消息体是 `WorkflowAlertContent` JSON **数组**（`[{...}, {...}]`）
- 包含字段：`workflowInstanceId`、`workflowDefinitionCode`、`workflowExecutionStatus`、`commandType`、`workflowStartTime` 等
- 故障转移告警还包含 `taskCode`、`taskName`、`retryTimes` 等任务级字段

**4. WorkerGroup 增强**
- 新增项目级 WorkerGroup 绑定（`POST /projects/{code}/worker-group`）
- 新增 `WorkerGroupChangeNotifier` 支持动态变更通知

**5. 调用方式变化**
- 补数据/暂停/停止/重跑等操作通过 RPC 同步调用，不再依赖数据库 Command 表异步触发
- Portal 调用时需设置合理超时（建议 30s），并通过返回的 `workflowInstanceId` 查询后续状态保证幂等

### 数据库存储架构

同一个 PostgreSQL 实例，三个独立 database：
- `portal_db` — Portal 业务数据
- `dolphinscheduler` — DS 元数据
- `ds_registry` — DS JDBC 注册中心（服务发现表）

Portal **只通过 REST API 与 DS 交互**，不直接读写 DS 数据库表。解耦优先，实时性通过轮询 + 缓存解决。

### Portal-DS 通信架构

**命令方向（Portal → DS）**：`DSClient` 通过 REST API 直接调用 DS，完成 ProcessDefinition/Schedule 的创建、更新、上线、下线、启动实例、补数据等操作。

**事件方向（DS → Portal）**：采用「DS HTTP Alert Plugin 推送 + Portal 轮询兜底」的双轨方案。
- **实时推送**：DS 任务实例状态变更时，通过 HTTP Alert 回调 `POST /api/notifications/ds-webhook`
  - **Payload 格式**：`WorkflowAlertContent` JSON 数组，包含 `workflowInstanceId`、`workflowExecutionStatus`、`commandType`、`workflowStartTime` 等
  - **触发时机**：Workflow 进入终态（SUCCESS/FAILURE/STOP）、Worker 故障转移、任务超时
- **兜底轮询**：`instance_sync_scheduler.py` 每 30-60 秒拉取 DS `/process-instances`，校准本地数据（**尚未实现**）
- **目标**：Portal 内展示最近运行记录、状态、日志、支持重跑，无需跳转 DS 界面

---

## 运行模式

### 触发类型

| 类型 | 用途 | 参数来源 | 数据隔离 |
|------|------|----------|----------|
| **schedule** | 定时调度自动生成 | 系统参数 + 组件定义 | 写生产表 |
| **manual** | 立即执行一次 | 用户可覆盖参数 | 写生产表 |
| **test** | 验证逻辑，不污染数据 | 用户可覆盖参数 | 写测试库（配置化临时库） |
| **backfill** | 重跑历史/未来日期范围 | 按日期自动生成 | 写生产表 |

### 测试运行隔离

- 每个 `DataSource` 配置 `test_connection_info`（或 `test_datasource_id` 外键）— **字段尚未添加**
- 测试运行时，DSL 翻译层将数据源替换为测试库连接 — **替换逻辑尚未实现**
- 测试库表结构由用户自行维护（需与生产一致）
- 测试实例不参与成功率统计，保留 7 天后自动清理

### 补数据（Backfill）方案

**「当前 Workflow」**：直接调用 DS Complement API（`execType=COMPLEMENT_DATA`）。
- DS 自动链式生成 instance（每天一个 ProcessInstance）
- DS 自动管理日期序列和跨天依赖
- 支持串行/并行、正序/倒序、失败策略、空跑

**「当前 Workflow + 下游」**：Portal 自研实现。
- 通过 `workflow_dependency` 表找到所有下游 Workflow
- 按拓扑排序依次调用 DS Complement
- 执行策略：
  - **默认**：Workflow 间串行 + Workflow 内并行（均衡模式）
  - **可选 1**：全串行（最保守）
  - **可选 2**：按天并行链条（每天 A→B→C 串行，不同天并行）
  - **不提供**：全并行（会导致下游读到上游未完成的脏数据）

### 补数据 UI 设计

**触发入口**：
1. 实例管理列表页顶部「补数据」按钮（选择 Workflow 后可用）
2. Workflow 详情页/编辑器内「补数据」按钮

**BackfillModal 组件**：

**步骤 1 — 选择日期**：
- 日期范围选择器（开始日期 ~ 结束日期），默认最近 7 天
- 支持「排除周末」快捷选项
- 限制：最近 7 天（可配置）

**步骤 2 — 选择下游范围**：
- 仅当前 Workflow（默认）
- 包含直接下游（1 层）— Phase 1
- 包含全部下游 — Phase 2
- 实时显示下游 Workflow 列表和数量，超过 20 个时阻止选择并提示

**步骤 3 — 执行策略**：
- Workflow 间串行 + Workflow 内并行（默认，均衡模式）
- 全串行
- 按天并行链条

**步骤 4 — 参数确认**：
- 展示自动生成的业务日期范围
- 允许覆盖全局参数（如 `$bizdate` 相关）
- 显示预估生成的实例数量

**提交后**：
- 生成唯一的 `backfill_chain_id`
- 跳转到实例管理页，自动筛选该 `backfill_chain_id`
- 显示进度条（实时轮询各 Workflow 的 complement 状态）

### 业务日期规则

| trigger_type | biz_date 规则 |
|--------------|---------------|
| `schedule` | DS Schedule 触发的计划日期 |
| `manual` | `CURDATE()` |
| `test` | `CURDATE()` |
| `backfill` | 用户选择的补数据日期 |

---

## 血缘系统

### 组件内字段级血缘

通过 SQLGlot 解析 SQL 组件，提取字段级的 source → transform → target 关系。

**表结构**：

```sql
CREATE TABLE lineage_node (
    id              SERIAL PRIMARY KEY,
    component_id    INT NOT NULL REFERENCES component(id),
    db_name         VARCHAR(128),
    table_name      VARCHAR(128) NOT NULL,
    column_name     VARCHAR(128) NOT NULL,
    node_type       VARCHAR(50) NOT NULL,   -- source / transform / target
    transform_logic TEXT,                   -- 转换逻辑（如 SQL 表达式）
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_ln_component ON lineage_node(component_id);
CREATE INDEX idx_ln_table ON lineage_node(db_name, table_name);

CREATE TABLE lineage_edge (
    id              SERIAL PRIMARY KEY,
    from_node_id    INT NOT NULL REFERENCES lineage_node(id),
    to_node_id      INT NOT NULL REFERENCES lineage_node(id),
    transform_type  VARCHAR(50),            -- select / join / aggregate / filter / etc.
    confidence      DECIMAL(3,2) DEFAULT 1.00, -- 置信度 0.00 ~ 1.00
    is_manual       BOOLEAN DEFAULT FALSE,  -- 是否人工纠正
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_le_from ON lineage_edge(from_node_id);
CREATE INDEX idx_le_to ON lineage_edge(to_node_id);
```

**触发时机**：
1. **组件保存时**（主力触发）— 实时解析 SQL，更新血缘
2. **工作流发布时**（完整校验）— 全量重新计算，校验一致性
3. **定时扫描**（兜底）— 后台任务周期性全量扫描
4. **手动触发**（可选）— 用户点击「分析血缘」按钮

### 跨 Workflow 依赖

通过表级血缘自动发现 Workflow 之间的依赖关系。

**表结构**：

```sql
CREATE TABLE workflow_dependency (
    id                      SERIAL PRIMARY KEY,
    upstream_workflow_id    INT NOT NULL REFERENCES workflow(id),
    downstream_workflow_id  INT NOT NULL REFERENCES workflow(id),
    source_table            VARCHAR(255) NOT NULL,    -- 上游表名
    target_table            VARCHAR(255) NOT NULL,    -- 下游表名
    confidence              DECIMAL(3,2) DEFAULT 1.00,
    is_manual               BOOLEAN DEFAULT FALSE,     -- 人工纠正
    discovered_at           TIMESTAMP DEFAULT NOW(),   -- 自动发现时间
    created_at              TIMESTAMP DEFAULT NOW(),
    UNIQUE(upstream_workflow_id, downstream_workflow_id, source_table, target_table)
);
CREATE INDEX idx_wd_upstream ON workflow_dependency(upstream_workflow_id);
CREATE INDEX idx_wd_downstream ON workflow_dependency(downstream_workflow_id);
```

**发现方式**：
- **SQL 组件**：SQLGlot 直接解析，高置信度
- **DataX 组件**：直接读取 `reader.table` / `writer.table`，高置信度
- **Python 组件**：代码扫描 + SQLGlot，~70% 准确率
- **Shell 组件**：正则扫描，~40% 准确率
- **低置信度血缘**：允许用户手动纠正（`is_manual=true`）

**循环依赖检测**：
- 保存 dependency 时 — 实时防御，阻止脏数据入库
- 补数据提交前 — 最终校验，阻止成环的补数据链执行
- 血缘定时扫描后 — 修正遗漏，标记异常并通知管理员

### HTTP API 增量同步游标

```sql
CREATE TABLE http_api_cursor (
    id              SERIAL PRIMARY KEY,
    component_id    INT NOT NULL REFERENCES component(id),
    cursor_field    VARCHAR(128) NOT NULL,  -- 游标字段名
    cursor_value    VARCHAR(512) NOT NULL,  -- 当前游标值
    record_count    BIGINT DEFAULT 0,       -- 累计同步记录数
    last_sync_at    TIMESTAMP,              -- 上次同步时间
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(component_id, cursor_field)
);
```

### 血缘版本快照

```sql
CREATE TABLE lineage_snapshot (
    id              SERIAL PRIMARY KEY,
    workflow_id     INT REFERENCES workflow(id),
    component_id    INT REFERENCES component(id),
    snapshot_type   VARCHAR(20) NOT NULL,   -- auto_save / publish / manual
    snapshot_data   JSONB NOT NULL,         -- 完整的血缘图数据
    created_by      INT REFERENCES sys_user(id),
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_ls_workflow ON lineage_snapshot(workflow_id);
CREATE INDEX ls_component ON lineage_snapshot(component_id);
```

---

## 实例状态同步

### 表结构

**workflow_instance** — 工作流运行实例（对应 DS ProcessInstance）
```sql
CREATE TABLE workflow_instance (
    id              SERIAL PRIMARY KEY,
    workflow_id     INT NOT NULL REFERENCES workflow(id),
    ds_instance_id  BIGINT,                 -- DS ProcessInstance ID
    ds_process_code BIGINT NOT NULL,        -- DS ProcessDefinition code
    biz_date        DATE NOT NULL,          -- 业务日期
    trigger_type    VARCHAR(20) NOT NULL,   -- schedule / manual / test / backfill
    status          VARCHAR(20) NOT NULL,   -- submit / waiting / running / pause / kill / success / fail / timeout / skipped
    start_time      TIMESTAMP,
    end_time        TIMESTAMP,
    duration_ms     BIGINT,                 -- 运行时长（毫秒）
    params_json     JSONB,                  -- 本次运行的实际参数
    complement_id   BIGINT,                 -- DS Complement 批次 ID（补数据时）
    backfill_chain_id VARCHAR(64),          -- Portal 补数据链条 ID
    created_by      INT REFERENCES sys_user(id), -- 触发人（schedule 为 null）
    is_synced       BOOLEAN DEFAULT FALSE,  -- 是否已与 DS 完成状态同步
    last_sync_at    TIMESTAMP,              -- 上次同步时间
    skip_reason     VARCHAR(255),           -- 跳过原因（skip_dates 时）
    dry_run         BOOLEAN DEFAULT FALSE,  -- 是否空跑实例
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_wi_workflow_id ON workflow_instance(workflow_id);
CREATE INDEX idx_wi_status ON workflow_instance(status);
CREATE INDEX idx_wi_biz_date ON workflow_instance(biz_date);
CREATE INDEX idx_wi_trigger_type ON workflow_instance(trigger_type);
CREATE INDEX idx_wi_backfill_chain ON workflow_instance(backfill_chain_id);
CREATE INDEX idx_wi_ds_instance ON workflow_instance(ds_instance_id);
```

**task_instance** — 任务运行实例（对应 DS TaskInstance）
```sql
CREATE TABLE task_instance (
    id                  SERIAL PRIMARY KEY,
    workflow_instance_id INT NOT NULL REFERENCES workflow_instance(id),
    component_id        INT REFERENCES component(id),
    ds_task_instance_id BIGINT,             -- DS TaskInstance ID
    ds_task_code        BIGINT NOT NULL,    -- DS TaskDefinition code
    task_name           VARCHAR(255) NOT NULL,
    task_type           VARCHAR(50) NOT NULL, -- sql / python / shell / datax
    status              VARCHAR(20) NOT NULL,
    start_time          TIMESTAMP,
    end_time            TIMESTAMP,
    duration_ms         BIGINT,
    retry_times         INT DEFAULT 0,      -- 重试次数
    max_retry_times     INT DEFAULT 0,      -- 最大重试次数
    log_path            VARCHAR(512),
    log_content         TEXT,               -- 缓存的日志内容（终态时）
    log_last_line       INT DEFAULT 0,      -- 上次同步到的行号
    worker_host         VARCHAR(255),
    worker_group        VARCHAR(100),
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_ti_workflow_instance ON task_instance(workflow_instance_id);
CREATE INDEX idx_ti_component ON task_instance(component_id);
CREATE INDEX idx_ti_status ON task_instance(status);
CREATE INDEX idx_ti_ds_task ON task_instance(ds_task_instance_id);
```

### 状态映射

**Workflow 状态（3.4.1 共 10 种）**：

| DS 状态 | Portal 状态 | 终态 | 说明 |
|---------|-------------|------|------|
| `SUBMITTED_SUCCESS` | `submit` | ❌ | 已提交 |
| `RUNNING_EXECUTION` | `running` | ❌ | 运行中 |
| `READY_PAUSE` | `pause` | ❌ | 准备暂停（中间态） |
| `PAUSE` | `pause` | ✅ | 已暂停 |
| `READY_STOP` | `kill` | ❌ | 准备停止（中间态） |
| `STOP` | `kill` | ✅ | 已停止 |
| `FAILURE` | `fail` | ✅ | 失败 |
| `SUCCESS` | `success` | ✅ | 成功 |
| `SERIAL_WAIT` | `waiting` | ❌ | 串行等待 |
| `FAILOVER` | `running` | ❌ | 故障转移中 |

**Task 状态（3.4.1 共 10 种）**：

| DS 状态 | Portal 状态 | 终态 | 说明 |
|---------|-------------|------|------|
| `SUBMITTED_SUCCESS` | `submit` | ❌ | 已提交 |
| `RUNNING_EXECUTION` | `running` | ❌ | 运行中 |
| `PAUSE` | `pause` | ✅ | 已暂停 |
| `FAILURE` | `fail` | ✅ | 失败 |
| `SUCCESS` | `success` | ✅ | 成功 |
| `NEED_FAULT_TOLERANCE` | `timeout` | ✅ | 超时（容错） |
| `KILL` | `kill` | ✅ | 被终止 |
| `DELAY_EXECUTION` | `waiting` | ❌ | 延迟执行 |
| `FORCED_SUCCESS` | `success` | ✅ | 强制成功 |
| `DISPATCH` | `submit` | ❌ | 已分发 |

### 同步机制

1. **实时推送**：DS HTTP Alert → `POST /api/notifications/ds-webhook`（**代码已存在，模型和调度器尚未实现**）
2. **兜底轮询**：`instance_sync_scheduler.py` 每 30-60 秒查询 DS `/process-instances`，对比更新本地状态（**尚未实现**）
3. **日志增量拉取**：通过 `log_last_line` 记录上次同步行号，增量拉取 DS `/log/detail`

---

## 编辑锁

完整优化方案，对标 DataWorks：

- **TTL 降低**：目标 60s（**代码当前 300s，待重构**），心跳保持 45s，崩溃后最多等待 60s 自动释放
- **锁状态查询**：显示锁定者用户名、锁定时间、剩余时间
- **强制解锁**：admin 可释放他人锁，锁所有者也可主动释放
- **过期提醒**：锁剩余 30s 时前端弹窗提示「点击续期」
- **申请编辑**：向锁定者发送消息/通知请求释放锁
- **只读同步**：查看锁定者正在编辑的内容（类似 Google Docs 查看模式）— **开发量较大，建议 Phase 2**

---

## 运维操作

### 跳过日期（Skip Dates）

通过 `workflow.skip_dates` 字段批量配置需要跳过的业务日期。

**实现方式（方案 C）**：
1. DS 正常触发生成 instance
2. Portal 轮询发现新 instance，检查 `biz_date` 是否在 `skip_dates` 中
3. 如果在跳过列表中，自动调用 DS API kill 该 instance
4. instance 状态标记为 `skipped`，记录原因

```python
# workflow_sync_scheduler.py
async def check_skip_dates(new_instance: WorkflowInstance):
    workflow = await db.get(Workflow, new_instance.workflow_id)
    if workflow.skip_dates and new_instance.biz_date.isoformat() in workflow.skip_dates:
        await ds_client.kill_process_instance(new_instance.ds_instance_id)
        new_instance.status = 'skipped'
        new_instance.end_time = datetime.now()
        await audit_log("instance.auto_skipped", new_instance.id)
```

- 不单独做「冻结实例」功能
- 跳过日期由 Portal 层控制，不依赖 DS 原生能力

### 空跑调度（Dry Run）

Workflow 继续定时生成实例，但实例不实际执行计算，立即返回成功。

**两种机制，各司其职**：

| 机制 | 适用场景 | 实现方式 |
|------|---------|---------|
| **DS Complement dryRun** | 补数据前验证配置 | 调 DS API 时传 `dryRun=true`，DS 不实际执行，返回验证结果 |
| **Portal DRY_RUN 注入** | 运行时空跑（定时/手动触发） | DSL 翻译时在脚本开头注入环境变量检查 |

**Portal DRY_RUN 注入方式**：
```bash
if [ "$DRY_RUN" = "true" ]; then
    echo "[DRY RUN] Skipping actual execution"
    exit 0
fi
```

- 所有触发类型（schedule/manual/backfill）生效
- 生成 instance、标记成功、不执行计算、不阻塞下游
- 由 Portal 层控制，通过全局参数传递 `DRY_RUN=true`

---

## 监控报警

### 任务状态监控

**触发条件**：
- **实例运行失败**（P0）— 立即告警
- **实例运行超时**（P0）— 超过 `workflow.max_running_time` 触发
- **到点未触发**（P1）— 超过定时时间仍未开始运行

**不做**：基线破线告警（DataWorks 智能基线，Portal 不对标）

### 告警配置

**表结构**：`task_alert_rule`
- `workflow_id` — 关联 Workflow（null = 全局规则）
- `alert_type` — `failure` / `timeout` / `not_triggered`
- `notify_channels` — 渠道数组（email / feishu / dingtalk / wecom）
- `notify_targets` — 接收人 ID 数组
- `is_enabled`, `created_at`, `updated_at`

**通知渠道**：复用 `notifier.py` 发送引擎（邮件/飞书/钉钉/企微 Webhook）
- **接收人**：DQC 和任务告警的接收人可以不同

### 告警收敛策略

- **首次失败**：立即告警
- **连续失败**：每日发摘要（避免轰炸）
- **成功恢复**：发送恢复通知

### 告警历史

**表结构**：

```sql
CREATE TABLE alert_history (
    id              SERIAL PRIMARY KEY,
    alert_rule_id   INT REFERENCES alert_rule(id),
    workflow_id     INT REFERENCES workflow(id),
    workflow_instance_id INT REFERENCES workflow_instance(id),
    trigger_type    VARCHAR(50) NOT NULL,   -- failure / timeout / not_triggered
    status          VARCHAR(20) NOT NULL DEFAULT 'triggered', -- triggered / sent / failed / acknowledged
    content         TEXT NOT NULL,          -- 告警内容
    notify_channels JSONB,                  -- 实际使用的通知渠道
    notify_targets  JSONB,                  -- 实际接收人列表
    sent_at         TIMESTAMP,              -- 发送时间
    error_msg       TEXT,                   -- 发送失败原因
    acknowledged_by INT REFERENCES sys_user(id),
    acknowledged_at TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_ah_rule ON alert_history(alert_rule_id);
CREATE INDEX idx_ah_workflow ON alert_history(workflow_id);
CREATE INDEX idx_ah_status ON alert_history(status);
CREATE INDEX idx_ah_created ON alert_history(created_at);
```

**展示页面**：运维中心「监控报警」子页面「告警历史」Tab
- 列表字段：触发时间、告警规则、关联 Workflow、触发类型、通知状态、操作（查看详情、标记已处理）
- 筛选：时间范围、Workflow、触发类型、通知状态
- 统计：今日告警数、未处理数、按规则分组

---

## 状态机

### 组件与工作流（4 状态）
```
draft → tested → online → offline
  ↑                        |
  └────────────────────────┘
```

`schedule_status`（仅 Workflow）独立追踪调度状态：`ONLINE` / `OFFLINE`。

---

## 权限模型

### 基础角色

RBAC 4 角色：admin / developer / analyst / viewer
- admin 绕过所有权限检查
- 敏感端点叠加 `require_permission("xxx:yyy")`
- 资源级 ACL 通过 `SysResourceAccess` 实现

### 运维中心权限矩阵

| 功能 | admin | developer | analyst | viewer |
|------|-------|-----------|---------|--------|
| **工作流管理** | 全部 | 编辑+发布+上线/下线/冻结 | 只读 | 只读 |
| **实例管理** | 全部 | 全部操作 | 重跑+终止 | 只读 |
| **补数据** | 全部 | 创建+终止 | 创建+终止 | ❌ |
| **监控报警** | 全部 | 配置 | 查看 | 只读 |
| **操作记录** | 查看全部 | 查看全部 | 查看自己的 | ❌ |

**操作按钮权限**：
- 重跑 / 终止：developer + analyst
- 置成功 / 重跑下游：developer + admin（影响范围大，analyst 不可）
- 强制解锁：admin 专属

### 自定义权限

Admin 通过调整角色权限模板（`sys_role_permission` 表）实现自定义权限，非用户自行调整个人权限。
- 角色模板变更即时生效
- 后端 API 做最终校验，前端隐藏按钮仅优化体验
- `admin` 角色绕过所有权限检查（硬编码）

---

---

## Worker Group（资源组）

**配置方式**：
- Standalone 模式：仅提供 `default`
- 集群模式：预定义枚举（`default` / `sync-worker` / `sql-worker`）+ 动态同步 DS Worker Group

**智能默认值**（按组件类型自动分配，用户可覆盖）：
| 组件类型 | 默认 Worker Group |
|----------|-------------------|
| SQL | `sql-worker` |
| DataX / SeaTunnel | `sync-worker` |
| Python / Shell | `default` |

**同步策略**：
- 不实时感知 DS Worker Group 变化
- 1 小时本地缓存 + 手动刷新按钮
- 发布时校验：Group 不存在时 DS 报错，Portal 捕获并提示用户

---

## 审计日志

**必须实现**，与业务代码同步开发，后期补成本极高。

**记录范围**：所有运维操作（发布、上线、下线、补数据、重跑、冻结、强制解锁、强制重跑下游等）

**Action 命名规范**：`{resource}.{action}`，如 `instance.rerun`、`workflow.publish`、`instance.set_success`、`workflow.force_unlock`。枚举在后端统一定义，避免前端硬编码。

**表结构**：

```sql
CREATE TABLE audit_log (
    id              SERIAL PRIMARY KEY,
    user_id         INT REFERENCES sys_user(id),
    action          VARCHAR(100) NOT NULL,  -- {resource}.{action}
    target_type     VARCHAR(50) NOT NULL,   -- workflow / component / instance / user / system
    target_id       VARCHAR(100),           -- 目标对象 ID（可为空）
    details         JSONB,                  -- 操作详情（旧值/新值、变更字段等）
    ip_address      VARCHAR(45),
    user_agent      VARCHAR(512),
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_al_user ON audit_log(user_id);
CREATE INDEX idx_al_action ON audit_log(action);
CREATE INDEX idx_al_target ON audit_log(target_type, target_id);
CREATE INDEX idx_al_created ON audit_log(created_at);
```

**查询能力**：按用户、时间范围、操作类型、目标对象筛选

**展示位置**：运维中心「操作记录」页面，支持导出

---

## 告警通知

**不做值班表轮班**，每个告警规则独立配置：
- 发送渠道：邮件 / 飞书 / 钉钉 / 企微 Webhook（可多选）
- 接收人：由用户自己设置，支持多接收人
- 不同规则可以配置不同的渠道和接收人

---

## 资源监控

**Portal 不做资源运维**，仅展示：
- Worker 节点在线/离线状态
- 各 Worker 上的任务分配情况

**详细集群资源监控**：接入 Prometheus + Grafana（独立部署，不在 Portal 内）

**单机模式**：实时监控本机 CPU/内存/磁盘状态

---

## 前端架构

### 运维中心导航结构

运维中心为**一级导航**（与「开发中心」并列）。

左侧菜单按功能模块划分：
```
运维中心
├── 工作流管理 — Workflow 列表、DAG 查看、发布/上线/下线/冻结
├── 实例管理 — 所有运行实例（Tab 区分触发类型）
│   ├── 定时实例
│   ├── 手动实例
│   ├── 补数据实例
│   └── 测试实例
├── 补数据 — 创建补数据任务、查看进度、终止/重跑
├── 监控报警 — 告警规则配置、告警历史
└── 操作记录 — 审计日志
```

**设计原则**：
- 实例管理用 Tab 区分 `trigger_type`，操作按钮根据实例状态动态显示
- 补数据为独立页面（批量任务管理，不适合放在单个 Workflow 详情页）

### 实例管理列表

**列表字段**：复选框、工作流名称、业务日期、触发类型（tag）、状态、开始时间、运行时长、操作、更多（▼展开）
- 补数据链条信息（`backfill_chain_id`、`complement_id`、链条进度）折叠在「更多」展开行中，主列表不常驻

**状态操作映射**：
| 状态 | 操作按钮 |
|------|----------|
| `submit` / `waiting` | 取消等待 |
| `running` | 终止运行 |
| `success` | 查看日志、重跑、重跑下游 |
| `fail` | 查看日志、重跑、重跑下游、置成功 |
| `timeout` | 查看日志、重跑、重跑下游、置成功 |
| `kill` | 查看日志、重跑 |
| `pause` | 恢复运行、终止运行 |

**操作语义说明**：
- **重跑**：重新执行该 Workflow 实例（生成新 instance，旧 instance 保留）
- **重跑下游**：仅对该 Workflow 内 DAG 的下游节点生效（DS `START_CURRENT_TASK_EXECUTE`），非跨 Workflow 的「强制重跑下游」
- **置成功**：将失败/超时的实例状态强制改为 success，不阻塞下游（DS 不支持，Portal 需本地标记 + 下游依赖放行）
- **终止运行**：调用 DS kill API，状态变为 `kill`（终态）
- **取消等待**：对尚未开始的实例，从 DS 队列中移除

**「强制重跑下游」（跨 Workflow）**：通过血缘系统找到所有下游 Workflow，按拓扑排序依次重跑。限制：最近 7 天 + 最多 20 个下游 Workflow。analyst 角色不可执行。

**批量操作**：支持批量重跑、批量置成功、批量终止
- 限制：仅允许同一 Workflow 且状态兼容的实例批量操作，避免误操作

### 日志查看器

**实时刷新**：running 状态每 3 秒轮询增量日志，终态停止自动刷新

**展示限制**：
- running 状态：无限制 append，20000 行软上限（超过后提示「日志过长，建议下载查看」）
- 终态：首次加载最多 5000 行 + 虚拟滚动
- 支持 `.log` 文件下载

**搜索与高亮**：
- 前端本地搜索框，支持正则/普通文本搜索，Enter 跳转到下一个匹配
- 自动错误高亮：包含 `ERROR` / `Exception` / `Traceback` 的行红底显示
- 日志级别过滤：INFO / WARN / ERROR 三级筛选（通过行首正则匹配，如 `^\d{4}-\d{2}-\d{2}.*\[ERROR\]`）
- 搜索命中高亮：匹配文本黄色背景

**扩展性**：设计为通用日志组件，预留接口支持后续对接其他组件（如 Airflow、自定义脚本）的日志统一管理

### DAG 图交互

**展示位置**：实例详情页内嵌（上方信息 + 下方 DAG + 底部任务列表）。

**节点状态颜色**：
| 状态 | 颜色 |
|------|------|
| success | 绿色 |
| fail | 红色 |
| running | 蓝色 |
| waiting / submit | 灰色 |

**右键菜单**（根据节点状态动态显示）：
| 节点状态 | 菜单项 |
|----------|--------|
| success | 查看日志、重跑该节点 |
| fail | 查看日志、重跑该节点、置成功、重跑该节点及下游 |
| running | 查看日志、终止该节点 |
| waiting / submit | —（只读） |

**上下游查看**：DAG 高亮模式切换（全部 / 上游路径 / 下游路径 / 仅当前），不做独立展开面板。

### 运维态 DAG（实例详情页）

编辑态 DAG（Workflow 编辑器）与运维态 DAG（实例详情页）是两套组件：

**编辑态** (`DagCanvas.vue`)：支持增删节点、连线、配置属性。
**运维态** (`OpsDagView.vue`)：只读展示，带实时状态着色。

**运维态特有功能**：
- **状态着色**：节点边框/背景按任务状态着色（success 绿 / fail 红 / running 蓝 / waiting 灰）
- **失败路径高亮**：从根节点到失败节点的整条路径加粗红色显示
- **右键菜单**（见上表）：查看日志、重跑该节点、置成功、重跑该节点及下游、终止该节点
- **单击高亮上下游**：单击节点后，非上游/下游的节点置灰，突出显示依赖链路
- **进度条**：running 状态的节点显示旋转进度指示器
- **任务统计**：DAG 右上角显示「X 成功 / Y 失败 / Z 运行中」

### 工作流列表筛选

运维中心首页基础能力。工作流 > 20 个后无筛选无法使用。

**筛选条件**：
- 工作流名称（模糊搜索）
- 责任人（下拉选择）
- 状态（online / offline / draft / tested）
- 最近运行状态（最近 24h 成功 / 失败 / 未运行 / 无记录）
- 调度周期（天 / 小时 / 分钟 / 周 — 解析 DS Cron 表达式）
- 标签（用户自定义标签，支持多选）

**默认排序**：按最近修改时间倒序
**支持自定义排序和筛选条件保存**

### 节点级调度属性

每个 DAG 节点（Component 引用）可独立配置以下属性，在 Workflow 编辑器中通过节点右键「属性」设置：

| 属性 | 默认值 | 说明 |
|------|--------|------|
| **失败重试次数** | 0 | 失败后自动重试次数（0 = 不重试） |
| **失败重试间隔** | 1 分钟 | 每次重试的间隔时间 |
| **超时时间** | 继承 Workflow | 单节点运行超时（分钟），覆盖 Workflow 级别的 `max_running_time` |
| **出错自动重跑** | 否 | 失败后是否自动重新执行该节点 |
| **Worker Group** | 继承组件类型默认 | 覆盖该节点的执行 Worker Group |
| **优先级** | MEDIUM | HIGHEST / HIGH / MEDIUM / LOW / LOWEST |

这些属性通过 DSL 翻译写入 DS TaskDefinition 的 `taskParams` 中。

```sql
CREATE TABLE workflow_node_config (
    id                  SERIAL PRIMARY KEY,
    workflow_id         INT NOT NULL REFERENCES workflow(id),
    component_id        INT NOT NULL REFERENCES component(id),
    retry_times         INT DEFAULT 0,
    retry_interval      INT DEFAULT 60,       -- 秒
    timeout_minutes     INT,                  -- null = 继承 Workflow
    auto_rerun_on_fail  BOOLEAN DEFAULT FALSE,
    worker_group        VARCHAR(100),
    priority            VARCHAR(20) DEFAULT 'MEDIUM',
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    UNIQUE(workflow_id, component_id)
);
```

### 工作流版本管理

**版本生成**：每次发布（Publish）Workflow 时，自动递增版本号（`version` 字段 +1），保存当前 DAG、调度配置、节点属性的快照到 `workflow_version` 表。

**版本列表**：Workflow 详情页内嵌「版本历史」Tab，展示：
- 版本号、发布时间、发布人、变更摘要（自动对比上一版本生成）
- 支持查看任意版本的历史 DAG（只读）
- 支持版本间对比（高亮显示 DAG 结构差异、配置变更）

**版本回滚**：选择历史版本 → 恢复到该版本（创建新版本，复制旧版本内容）。回滚后状态为 `draft`，需重新发布才能上线。

```sql
CREATE TABLE workflow_version (
    id              SERIAL PRIMARY KEY,
    workflow_id     INT NOT NULL REFERENCES workflow(id),
    version         INT NOT NULL,             -- 版本号（从 1 开始递增）
    dag_json        JSONB NOT NULL,           -- DAG 快照
    schedule_config JSONB,                   -- 调度配置快照
    node_configs    JSONB,                   -- 节点属性配置快照（workflow_node_config 聚合）
    change_summary  TEXT,                    -- 变更摘要（自动生成）
    published_by    INT REFERENCES sys_user(id),
    published_at    TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_wv_workflow ON workflow_version(workflow_id);
CREATE INDEX idx_wv_version ON workflow_version(workflow_id, version);
```

### 生效日期

Workflow 调度支持配置生效日期范围：
- **生效开始日期**：默认创建当日，可选未来日期
- **生效结束日期**：默认空（永久有效），可设为未来某日期

到达结束日期后，DS Schedule 自动下线（`schedule_status=OFFLINE`），不再生成新实例。在生效日期范围外的 instance 不执行（类似 skip_dates 处理）。

### 运维概览

非华丽大屏，简洁数据卡片。进入页面刷新 + 每 60 秒自动刷新 + 手动刷新按钮。

**核心卡片**（4 张）：
- 昨日实例成功率（统计口径：定时实例，排除测试/手动/补数据）
- 正在运行的实例数（全部 trigger_type 实时计数）
- 待处理告警数（未恢复的失败/超时告警）
- 今日失败数（00:00 至今，全部 trigger_type）

**扩展卡片**：
- 即将超时预警（运行时长接近 `max_running_time`）— 最有价值的预警卡片
- 进行中补数据任务数
- 失败 Workflow Top5（最近 7 天）

**交互**：全部卡片支持点击跳转，每个都是运维入口
- 昨日成功率 → 实例管理（昨天全部实例）
- 失败 Top5 → 对应 Workflow 实例列表
- 待处理告警 → 监控报警页面

### 暂不做（Phase 2）

- **数据质量监控页**：DQC 是独立模块，当前 Portal 尚未深度集成。等 DQC 规则数量 > 10 条后再做独立页面
- **编辑锁只读同步**（Google Docs 模式）：开发量极大，需实时同步编辑器内容，优先级低
- **调度日历/交易日历**：支持自定义工作日历（排除节假日），影响实例生成逻辑
- **上下文参数传递**：上下游节点间传递参数（如上游节点输出 → 下游节点输入）
- **跨周期依赖**：今天实例依赖昨天实例的完成状态，需特殊的依赖检测逻辑
- **基线破线告警**：DataWorks 智能基线，Portal 不对标
- **$[...] 定时时间参数语法**：参数引擎二期功能

---

## 关键约束

1. **Portal 是 DS 的唯一控制面** — 所有调度操作必须经过 Portal
2. **DataX 不走 DS 原生 DataX 节点** — 翻译为 SHELL + heredoc，避免版本耦合
3. **组件状态与 DS 状态弱一致** — 通过 outbox 异步同步，允许短暂不一致
4. **DQC 在 SHELL 节点中调用 Portal API** — 需要 `DQC_SERVICE_TOKEN` 环境变量
5. **组件和工作流有独立版本控制** — 组件修改不会自动同步到引用它的工作流，需用户确认更新
6. **Portal 与 DS 只通过 REST API 交互** — 不直接读写 DS 数据库，解耦优先
7. **跨 Workflow 依赖在 Portal 层维护** — DS 不感知 ProcessDefinition 之间的依赖关系
