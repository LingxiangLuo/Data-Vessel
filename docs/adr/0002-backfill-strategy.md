---
name: backfill-strategy
description: Portal 补数据（Backfill）方案选型
date: 2026-05-22
status: accepted
---

# ADR 0002: 补数据方案

## 背景

DataWorks 支持对周期任务执行补数据操作（重跑历史/未来日期范围的数据）。Portal 需要对标此功能。

## 决策

采用 **DS 原生 Complement + Portal 自研下游扩展** 的混合方案。

### 「当前 Workflow」：DS 原生 Complement

Portal 调用 DS API `POST /executors/start-workflow-instance?execType=COMPLEMENT_DATA`：
- DS 自动链式生成 instance（每天一个 ProcessInstance）
- DS 自动管理日期序列和跨天依赖
- 支持串行/并行、正序/倒序、失败策略、空跑

### 「当前 Workflow + 下游」：Portal 自研

- 通过 `workflow_dependency` 表找到所有下游 Workflow
- 按拓扑排序依次调用 DS Complement
- 执行策略：
  - **默认**：Workflow 间串行 + Workflow 内并行（均衡模式）
  - **可选 1**：全串行（最保守）
  - **可选 2**：按天并行链条（每天 A→B→C 串行，不同天并行）
  - **不提供**：全并行（会导致下游读到上游未完成的脏数据）

## 拒绝的方案

| 方案 | 拒绝原因 |
|------|----------|
| Portal 按天生成独立实例 | 开发量大，需要自己管理依赖和状态，DS Complement 已完美覆盖 |
| 复用 DS Complement 模拟重跑 | Complement 会生成新 instance，不是「重跑」原有 instance，语义不对 |

## 关键约束

- DS 不感知跨 ProcessDefinition 的依赖关系，Workflow 间依赖由 Portal 维护
- 补数据限制：最近 7 天 + 最多 20 个下游 Workflow
- 业务日期规则：manual/test 填 CURDATE()，backfill 填用户选择日期，schedule 填 DS 计划日期
