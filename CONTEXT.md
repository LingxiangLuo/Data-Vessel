# Data-Vessel 领域上下文

## 项目定位

数据中台门户（DMP Portal），统一控制面，对接 DolphinScheduler 作为调度引擎。

## 核心领域术语

| 术语 | 英文 | 定义 |
|------|------|------|
| 组件 | Component | 最小开发单元，类型：sql / python / shell / datax |
| 工作流 | Workflow | DAG 编排，由组件节点和连线组成 |
| 发布 | Publish | 将 Portal 工作流同步到 DolphinScheduler，创建 PD + Schedule |
| 上线 | Online | 组件/工作流状态为 online，表示已通过测试可运行 |
| 下线 | Offline | 停用状态，不再调度 |
| 测试 | Test | 验证组件/工作流可执行（当前部分类型为假测试，仅改状态） |
| DQC | Data Quality Check | 数据质量校验，14 种规则类型 |
| DSL | Domain Specific Language | Portal 内部模型到 DS TaskDefinition 的翻译 |
| Outbox | WorkflowSyncQueue | 异步 DS 同步队列，10 秒轮询，指数退避重试 |
| DataX | DataX | 阿里开源数据同步工具，Portal 内嵌为 SHELL 节点调用 |
| 参数引擎 | Param Engine | ${bizdate}、${yyyymmdd} 等占位符替换系统 |

## 状态机

### 组件（4 状态）
```
draft → tested → online → offline
  ↑                        |
  └────────────────────────┘
```

### 工作流（4 状态）
同组件。`schedule_status` 独立追踪调度状态（ONLINE/OFFLINE）。

## 权限模型

RBAC 4 角色：admin / developer / analyst / viewer
- admin 绕过所有权限检查
- 敏感端点叠加 `require_permission("xxx:yyy")`
- 资源级 ACL 通过 `SysResourceAccess` 实现

## 发布流程

```
Workflow (Portal)
  └→ dsl_translator.py → DS TaskDefinition JSON
  └→ publisher.py → ds_client.py (单例) → DS REST API
  └→ 成功后 online，失败重试，永久失败回滚 tested
```

## 关键约束

1. **Portal 是 DS 的唯一控制面** — 所有调度操作必须经过 Portal
2. **DataX 不走 DS 原生 DataX 节点** — 翻译为 SHELL + heredoc，避免版本耦合
3. **组件状态与 DS 状态弱一致** — 通过 outbox 异步同步，允许短暂不一致
4. **DQC 在 SHELL 节点中调用 Portal API** — 需要 `DQC_SERVICE_TOKEN`
