---
name: portal-ds-bidirectional-sync
description: Portal 与 DolphinScheduler 双向通信方案选型
date: 2026-05-21
status: accepted
---

# ADR 0001: Portal-DolphinScheduler 双向通信方案

## 背景

当前 Portal 与 DS 是纯单向通信：Portal 通过 `DSClient` 调用 DS REST API 完成发布/上线/下线，然后通过 `WorkflowSyncQueue`（10s 轮询本地 outbox 表）补偿失败。DS 对 Portal 完全无感知，任务执行状态不在 Portal 内呈现。

用户希望在 Portal 内获得接近 DataWorks 运维中心的体验（查看实例运行状态、日志、重跑），这需要 DS 向 Portal 反向推送事件。

## 决策

采用 **方案 A（实例状态轮询）+ 方案 B（DS HTTP Alert 回调）** 组合。

### 方案 A：实例状态轮询

Portal 后台增加 `instance_sync_scheduler.py`，每 30-60 秒轮询 DS `/process-instances` 和 `/task-instances`，将运行状态写入 Portal 数据库。

- **作用**：兜底同步，覆盖 Alert 漏发、历史查询、页面首次加载
- **代价**：30-60s 延迟，可控的资源消耗

### 方案 B：DS HTTP Alert → Portal WebHook

利用 DS 2.x+ 内置的 HTTP Alert Plugin，配置告警 URL 指向 `POST /api/ds/alerts`：

- **触发时机**：任务实例状态变更（成功、失败、超时）
- **Portal 端点**：接收 DS 推送的 `projectCode, processId, taskId, state, logPath` 等
- **效果**：秒级事件通知，无需轮询等待

## 拒绝的方案

| 方案 | 拒绝原因 |
|------|----------|
| C. 自定义 DS Alert Plugin（Java）| 需要 Java 构建环境，维护独立插件包，收益不足以抵消成本 |
| D. 独立 Gateway 中间层 | 自托管场景多一个服务 = 多一套运维负担；当前 DS API 调用量不大，直接调用足够 |

## 影响

1. **新增 API 端点**：`POST /api/ds/alerts`（接收 DS 告警推送）
2. **新增调度器**：`instance_sync_scheduler.py`（轮询实例状态）
3. **新增数据表**：`workflow_instance` / `task_instance`（存储从 DS 同步的运行记录）
4. **DS 侧配置**：告警组中增加 HTTP 类型告警实例，URL 指向 Portal

## 后续

- 不要试图在 Portal 中完全复刻 DataWorks 运维中心的所有能力（DS 是独立执行面，非自研调度）
- 务实的目标：最近 10 次运行记录、成功/失败/耗时、日志查看、重跑触发
