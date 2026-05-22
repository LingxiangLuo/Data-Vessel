# Issue Tracker

本项目使用本地 Markdown 文件作为 issue tracker，存储在 `.scratch/` 目录下。

## 位置

- `.scratch/issues/` — 待处理 issue
- `.scratch/completed/` — 已完成 issue

## 操作方式

创建 issue：
```bash
echo "# ISSUE-XXX: 标题

**状态**: needs-triage
**创建**: YYYY-MM-DD

描述..." > .scratch/issues/ISSUE-XXX-title.md
```

推进状态：
```bash
# needs-triage → ready-for-agent
# ready-for-agent → in-progress
# in-progress → completed（完成后移到 .scratch/completed/）
```

## 状态定义

见 `triage-labels.md`。
