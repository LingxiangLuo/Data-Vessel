# Domain 文档布局规则

## CONTEXT.md

- **位置**: 项目根目录 `/CONTEXT.md`
- **作用**: 领域术语字典（glossary），消除同词异义、同名异指
- **维护者**: `grill-with-docs` 初建，主 agent 在 tdd 过程中增量更新
- **格式**: Markdown，每个术语一个 `###` 标题，包含：定义、同义词、反义词、相关术语链接
- **更新时机**: 遇到新领域术语时立即更新，不等下次 grill

## ADR (Architecture Decision Records)

- **位置**: `docs/adr/NNNN-title.md`
- **命名**: 四位递增序号 + kebab-case 标题，如 `0001-use-ds-as-scheduler.md`
- **触发条件**: 必须同时满足以下三条才写：
  1. 难以逆转（改主意成本高）
  2. 不看上下文会困惑（未来维护者会问"为什么选 A 不选 B"）
  3. 真实权衡（有明确的备选方案，不是显然的选择）
- **格式模板**:
  ```markdown
  # NNNN. 标题

  **状态**: proposed | accepted | deprecated | superseded by [NNNN-title](link)
  **日期**: YYYY-MM-DD

  ## 上下文

  ## 决策

  ## 后果

  ## 备选方案（为什么没选）
  ```
