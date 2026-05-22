# Triage 状态标签

五个状态角色，每个 issue 必须处于其中之一。

| 状态 | 含义 | 谁负责推进 |
|------|------|-----------|
| `needs-triage` | 刚创建，尚未评估 | Agent（运行 `/triage`） |
| `ready-for-agent` | 已评估，需求清晰，可开始编码 | Agent 领取后变为 `in-progress` |
| `in-progress` | 正在实现中 | 当前负责的 Agent |
| `needs-review` | 实现完成，等待代码审查或用户确认 | Agent 标记后移交 |
| `completed` | 已合并/已部署 | 自动归档到 `.scratch/completed/` |

## 状态流转规则

```
needs-triage → ready-for-agent → in-progress → needs-review → completed
      ↑_________________________________________________________|
      （用户反馈或发现新问题时回退到 needs-triage）
```

## 状态变更标记方式

在 issue 文件的 frontmatter 中更新 `status:` 字段。
