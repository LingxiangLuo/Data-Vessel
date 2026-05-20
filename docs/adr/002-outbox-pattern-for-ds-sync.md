# ADR 002: Outbox 模式解耦 DS 同步

## 状态

已接受

## 背景

工作流发布需要调用 DolphinScheduler REST API（创建/更新 ProcessDefinition、Schedule），这些操作：
- 网络不稳定，可能失败
- 需要重试
- 不能阻塞用户请求

## 决策

引入 `WorkflowSyncQueue` 表作为 outbox，API 只写入记录，后台 APScheduler 每 10 秒消费。

队列支持 5 种 action：publish / online / offline / release_schedule / delete

重试策略：指数退避（2^retry_count 分钟），max_retries=5

## 后果

### 正面
- 用户请求不阻塞，发布 API 立即返回
- DS 故障不影响 Portal 核心功能
- 自动重试，无需人工干预

### 负面
- 状态弱一致：Portal 状态可能与 DS 状态短暂不一致
- 需要处理乐观更新失败回滚（publish 后 online，失败回 tested）
- 多进程部署时可能重复消费（当前无分布式锁）
