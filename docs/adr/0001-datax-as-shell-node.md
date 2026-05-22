# 0001. DataX 不走 DolphinScheduler 原生 DataX 节点

**状态**: accepted
**日期**: 2026-05-21

## 上下文

DataX 是阿里开源的数据同步工具。DolphinScheduler 原生支持 DataX 任务类型，用户可以在 DS 界面上直接配置 DataX 的 reader/writer。

## 决策

Portal 里的 DataX 组件**不**翻译为 DS 原生 DataX 节点，而是翻译为 SHELL 节点 + heredoc 内嵌 JSON，通过命令行调用 `datax.py`。

## 后果

**正面**：
- 避免 DS 版本升级时 DataX 插件接口变更导致的兼容问题
- 完全控制 DataX job.json 的生成逻辑，不受 DS 字段限制
- 密码解密在 Portal 侧完成，DS 侧不持有明文密码

**负面**：
- 需要自行管理 DataX 运行环境（Python、JVM、内存参数）
- 日志格式与 DS 原生节点不同，需要额外处理
- 丧失了 DS 界面对 DataX 任务的图形化展示能力

## 备选方案（为什么没选）

**方案 A：DS 原生 DataX 节点**
- 问题：DS 的 DataX 插件对字段类型支持有限，且每次 DS 升级需验证插件兼容性
- 问题：DS 原生节点要求密码以明文或特定加密方式存储在 DS 侧，与 Portal 的加密体系冲突

**方案 B：自定义 DS 任务插件**
- 问题：需要维护 DS 插件的 Java 代码，增加技术栈复杂度
- 问题：DS 升级时需同步升级插件
