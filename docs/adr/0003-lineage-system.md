---
name: lineage-system
description: 血缘系统设计方案（字段级血缘 + 跨 Workflow 依赖）
date: 2026-05-22
status: accepted
---

# ADR 0003: 血缘系统

## 背景

DataWorks 支持任务血缘分析（上下游依赖）。Portal 需要：
1. 组件内字段级血缘（SQLGlot 解析）
2. 跨 Workflow 依赖发现（用于补数据下游扩展、强制重跑下游）

## 决策

### 组件内字段级血缘

通过 SQLGlot 解析 SQL 组件，提取字段级的 source → transform → target 关系。

**表结构**：
- `lineage_node` — 字段级血缘节点
- `lineage_edge` — 字段级血缘边

**触发时机**：
1. 组件保存时（主力触发）
2. 工作流发布时（完整校验）
3. 定时扫描（兜底）
4. 手动触发（可选）

### 跨 Workflow 依赖

通过表级血缘自动发现 Workflow 之间的依赖关系。

**表结构**：
- `workflow_dependency` — 跨 Workflow 依赖（upstream_workflow_id, downstream_workflow_id, source_table, target_table, confidence, is_manual）

**发现方式**：
- SQL：SQLGlot 直接解析，高置信度
- DataX：直接读取 reader.table / writer.table，高置信度
- Python：代码扫描 + SQLGlot，~70% 准确率
- Shell：正则扫描，~40% 准确率
- 低置信度血缘允许用户手动纠正

**循环依赖检测**：
- 保存 dependency 时 — 实时防御
- 补数据提交前 — 最终校验
- 血缘定时扫描后 — 修正遗漏

## 拒绝的方案

- 不在 `workflow_dependency` 中持久化字段级血缘（避免存储爆炸）
- 字段级影响分析通过「表级定位 Workflow → 实时 SQLGlot 解析」实现

## 新增表

- `lineage_node` / `lineage_edge` — 字段级血缘
- `workflow_dependency` — 跨 Workflow 依赖
- `http_api_cursor` — HTTP API 增量同步游标
- `lineage_snapshot` — 血缘历史快照
