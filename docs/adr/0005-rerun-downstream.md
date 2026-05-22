---
name: rerun-downstream
description: 强制重跑下游方案选型
date: 2026-05-22
status: accepted
---

# ADR 0005: 强制重跑下游

## 背景

DataWorks 支持「强制重跑下游」：将选中的实例及其下游全部置为未运行状态并重新调度。Portal 必须对标此功能。

## 决策

采用 **基于血缘自研** 的方案（A 路径）。

### Phase 1

- 支持直接下游（1 层）
- 通过 `workflow_dependency` 找到下游 Workflow
- 按拓扑排序串行执行
- 限制：最近 7 天 + 最多 20 个下游 Workflow

### Phase 2

- 扩展到全链条（递归所有层级下游）
- 支持跨天依赖的重跑

### 实现方式

对每个需要重跑的 Workflow，找到对应日期的 instance，调用 DS API 重跑。不复用 DS Complement（语义不对）。

## 拒绝的方案

- **仅重跑当前 Workflow**：不满足 DataWorks 对标要求
- **复用 DS Complement 模拟**：Complement 生成新 instance，不是「重跑」原有 instance

## 关键约束

- 需要 `workflow_dependency` 表维护跨 Workflow 依赖关系
- 限制最近 7 天 + 最多 20 个下游，防止误操作
- 操作记录到审计日志
