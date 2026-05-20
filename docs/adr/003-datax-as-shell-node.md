# ADR 003: DataX 组件翻译为 SHELL 节点

## 状态

已接受

## 背景

DolphinScheduler 原生支持 DataX 任务类型，但：
- DS 内嵌 DataX 版本与 Portal 独立演进的 DataX 版本可能不兼容
- 配置格式耦合

## 决策

DataX 组件不走 DS 原生 DataX 节点，翻译为 **SHELL 节点**，通过 heredoc 内嵌 DataX job.json，调用 `datax.py` 执行。

## 后果

### 正面
- Portal 完全控制 DataX 版本和配置
- 与 DS 版本解耦

### 负面
- 日志分散在 SHELL 节点输出中，不如原生 DataX 节点结构化
- 需要额外维护 `datax_builder.py` 的翻译逻辑
