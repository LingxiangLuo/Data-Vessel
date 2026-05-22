---
name: instance-sync
description: Portal-DolphinScheduler 实例状态同步方案
date: 2026-05-22
status: accepted
---

# ADR 0004: 实例状态同步

## 背景

Portal 需要获取 DS 任务实例的运行状态、日志等信息，用于运维中心展示。

## 决策

采用 **「DS HTTP Alert 推送 + Portal 轮询兜底」** 的双轨方案。

### 实时推送

DS 任务实例状态变更时，通过 HTTP Alert Plugin 回调 Portal `POST /api/ds/alerts`。
- 秒级事件通知
- 需要 DS 侧配置 Alert Group，URL 指向 Portal

### 兜底轮询

Portal 后台 `instance_sync_scheduler.py` 每 30-60 秒查询 DS `/process-instances` 和 `/task-instances`：
- 对比更新本地状态
- 校准 Alert 漏发或推送失败的情况

### 日志同步

通过 `log_last_line` 记录上次同步行号，增量拉取 DS `/log/detail`。

## 新增表

- `workflow_instance` — 工作流运行实例
- `task_instance` — 任务运行实例

## 状态映射

| DS 状态 | Portal 状态 |
|---------|-------------|
| SUBMITTED_SUCCESS | submit |
| RUNNING_EXECUTION | running |
| PAUSE | pause |
| STOP | kill |
| SUCCESS | success |
| FAILURE | fail |
| NEED_FAULT_TOLERANCE | timeout |

## 拒绝的方案

- 不直接读写 DS 数据库表（解耦优先）
- 不依赖 WebSocket/SSE（增加复杂度，轮询+Alert 足够）
