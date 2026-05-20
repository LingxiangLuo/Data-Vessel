# ADR 004: 组件状态机裁剪为 4 状态

## 状态

已接受（2026-05-20）

## 背景

原状态机有 10 个状态：draft/developing/testing/reviewing/tested/paused/online/deprecated/offline/archived

但实际只有 4 个状态有后端门控，其余 6 个是纯标签，无业务约束。

## 决策

删除 6 个无用状态，统一为 4 状态机：

```
draft → tested → online → offline
```

迁移映射：
- developing → draft
- testing/reviewing/paused → tested
- deprecated/archived → offline

同时删除 `previous_status` 列和手动状态转换端点。

## 后果

### 正面
- 代码简化，减少维护负担
- UI 状态流转可视化更直观
- 避免用户困惑于无业务意义的状态

### 负面
- 丢失历史状态粒度（如无法区分 "测试中" 和 "已测试"）
- 需要数据迁移（已通过 migration 处理）
