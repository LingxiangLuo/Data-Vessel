# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

数据中台门户，前端 Vue 3 + Arco Design，后端 FastAPI + SQLAlchemy，调度引擎对接 DolphinScheduler。

- 前端：`portal/frontend/` — Vite + Vue 3 + TypeScript + Arco Design
- 后端：`portal/backend/` — FastAPI + uvicorn，启动时自动执行 schema migration
- 部署：Docker Compose，nginx 统一入口（**8888 端口**），内网测试服务器 `192.168.1.3`

## 常用命令

```bash
# 前端本地开发
cd portal/frontend && rtk npm run dev

# 前端类型检查
cd portal/frontend && rtk npx vue-tsc --noEmit

# 前端构建验证
cd portal/frontend && rtk npx vite build

# 后端本地启动
cd portal/backend && uvicorn main:app --reload --port 8000

# 后端语法检查
cd portal/backend && rtk err python3 -m compileall -q -d . -x '/\.venv/' .

# 后端 lint（ruff）
cd portal/backend && rtk ruff check .

# 后端测试（全部）
cd portal/backend && rtk pytest tests/

# 后端测试（单个文件）
cd portal/backend && rtk pytest tests/test_dsl_translator.py -v

# 手动部署到测试服务器（任意分支均可）
bash scripts/deploy-to-test.sh

# 常用参数
bash scripts/deploy-to-test.sh --backend-only   # 仅部署后端
bash scripts/deploy-to-test.sh --frontend-only  # 仅部署前端
bash scripts/deploy-to-test.sh --skip-check     # 跳过语法检查
bash scripts/deploy-to-test.sh --force          # 强制全量重建（无缓存）
```

## 分支策略

- `main` — 唯一长期分支，始终可部署，**禁止直接 push**
- `feat/<name>` — 功能分支，基于 main 切出
- `fix/<description>` — 紧急修复分支
- 分支生命周期：创建 → 开发 → 测试验证 → PR → 合并 → **立即删除**

## 功能开发流程

需求澄清和编码阶段遵循全局 CLAUDE.md 的 Matt Pocock 流水线：
- 需求澄清 → `/grill-with-docs`（更新 `CONTEXT.md`，按需创建 ADR）
- 方案拆解 → `/to-prd` → `/to-issues`
- 编码 → `/tdd`（垂直切片）；复杂 bug → `/diagnose`

```bash
# 1. 切分支
rtk git checkout main && rtk git pull origin main
rtk git checkout -b feat/xxx

# 2. 本地验证
cd portal/backend && rtk err python3 -m compileall -q -d . -x '/\.venv/' .
cd portal/backend && rtk ruff check .
cd portal/frontend && rtk npx vite build

# 3. 代码审查 — 每次非平凡修改后主动触发 quick-code-reviewer
#    3+ 文件 / auth / 新 API → deep-code-reviewer

# 4. 手动部署验证
bash scripts/deploy-to-test.sh
#    部署完成后触发 test-engineer 验证（测试环境 http://192.168.1.3）

# 5. 合并到 main
rtk git checkout main
rtk git merge feat/xxx --no-ff
rtk git push origin main
rtk git branch -d feat/xxx
```

## CI/CD

当前无自动化 CI/CD，部署通过本地脚本手动执行到测试服务器。

## 测试服务器连接

| 项目 | 值 |
|------|-----|
| IP | `192.168.1.3` |
| 用户名 | `root` |
| 认证方式 | SSH 密钥（Ed25519） |
| 私钥文件 | `~/.ssh/test_server_key` |

```bash
# SSH 连接
ssh -i ~/.ssh/test_server_key root@192.168.1.3

# 常用容器操作
ssh -i ~/.ssh/test_server_key root@192.168.1.3 'docker ps'
ssh -i ~/.ssh/test_server_key root@192.168.1.3 'docker compose restart dmp-portal-api'
ssh -i ~/.ssh/test_server_key root@192.168.1.3 'docker logs -f dmp-portal-api'
```

| 服务 | 内网地址 |
|------|---------|
| Portal Backend API | `http://172.20.0.7:8000` |
| Nginx 前端 | `http://192.168.1.3` |
| DolphinScheduler | `http://192.168.1.3:12345/dolphinscheduler` |

## 代码审查

- 修改单函数/小 bug fix → `quick-code-reviewer`（主动触发）
- 跨 3+ 文件 / 涉及 auth/权限/数据库模型 → `deep-code-reviewer`
- 部署后 → `test-engineer`

## 后端约定

- **新增表/列**：`app/core/auto_migrate.py` 启动时自动检测并创建（`Base.metadata.create_all()` + `ALTER TABLE ADD COLUMN`）
- **复杂迁移**（列类型变更、数据迁移、索引变更）：`app/core/migrations.py` 中手写 migration 函数
- **启动顺序**：后端容器启动时依次调用 `alembic upgrade head` → `auto_migrate()` → `run_all_migrations()`
- 新增 API 端点后需在 `main.py` 注册路由
- 权限控制：敏感端点叠加 `Depends(require_permission("xxx:yyy"))`，不改 `get_current_user`

## 前端约定

- API 函数统一在 `src/api/index.ts`，不在组件里直接 axios
- 路由定义在 `src/router/index.ts`，admin 子路由需加 `meta.permission`
- 组件库：Arco Design（`@arco-design/web-vue`），不引入其他 UI 库
- **无 `@/` 路径别名**，用相对路径

## 核心子系统架构

### 认证与安全

认证采用双模式：浏览器走 httponly cookie（`access_token`），API 客户端走 Bearer token，两种方式在 `app/core/security.py:get_current_user` 中统一处理。

- **CSRF 防护**：`main.py:CSRFProtectionMiddleware` 对携带 cookie 的非只读请求校验 `X-CSRF-Token` 请求头与 cookie 中的 `csrf_token` 是否一致；Bearer token 请求豁免
- **Token 黑名单**：登出后 token 加入内存字典 `_token_blacklist`（进程重启后失效，属已知限制）
- **权限体系**：RBAC，4 个内置角色（admin/developer/analyst/viewer），启动时在 `main.py` 中 seed。`require_permission("xxx:yyy")` 作为 FastAPI 依赖注入，admin 角色绕过所有权限检查
- **必须配置**：`DQC_SERVICE_TOKEN` 环境变量，缺失时服务间调用不可用（启动时打 warning）

### DSL 翻译流水线

Portal 是 DolphinScheduler 的唯一控制面。发布流程：

```
Component (sql/python/shell/datax)
    └→ app/core/dsl_translator.py → DS TaskDefinition JSON
Workflow (DAG 节点 + 连线)
    └→ dsl_translator.py → DS ProcessDefinition (taskDefinitionJson + taskRelationJson)
    └→ app/core/ds_client.py (单例，维护 DS session) → DS REST API
```

DataX 组件不走 DS 原生 DataX 节点，而是翻译为 SHELL 节点 + heredoc 内嵌 JSON 调用 `datax.py`，避免版本耦合。`datax_builder.py` 负责把同步任务模型翻译成 DataX job.json。

### 参数引擎

`app/core/param_engine.py` 在任务执行前替换参数占位符，对标 DataWorks 调度参数体系：
- 系统内置：`${bizdate}`（T-1）、`${cyctime}`、`${gmtdate}`
- 日期格式：`${yyyymmdd}`、`${yyyy-mm-dd}`、`${yyyymmdd-7}`（偏移）
- 自定义参数：组件中定义，值可引用其他参数；手动运行时可覆盖

### DQC 数据质量子系统

- `app/core/dqc_engine.py`：按规则类型生成校验 SQL（`row_count`/`null_percent`/`custom_sql` 等 14 种），通过 `db_adapter.py` 在目标数据源上执行
- `app/core/dqc_scheduler.py`：APScheduler 后台线程，lifespan 启动/关闭，按 DqcReport 配置定时生成报告
- `app/core/dqc_report_generator.py`：聚合检查结果生成报告；通知走 `notifier.py`（邮件/飞书/钉钉/企微 Webhook）

### 前端权限控制

两层：
- **路由级**：`src/router/index.ts:beforeEach` 检查 `to.meta.permission`，无权限跳 `/403`
- **元素级**：`src/directives/permission.ts` 的 `v-permission` 指令 + `useUserStore().hasPermission(code)`

权限列表在登录后从 `/api/auth/me/permissions` 拉取，存于 Pinia `useUserStore`。

## Git 代理

```bash
git config http.proxy http://127.0.0.1:7890
git config https.proxy http://127.0.0.1:7890
```

## 提交规范

```
<type>(<scope>): <description>

<type>
  feat     新功能
  fix      Bug 修复
  refactor 重构
  chore    杂项（脚本、配置）
  docs     文档

<scope> 可选
  backend  后端
  frontend 前端
  deploy   部署
  dqc      数据质量
  dsl      翻译器

示例：
  feat(dqc): 添加波动率校验规则 diff_percent
  fix(frontend): SqlDev.vue 参数编辑器空值处理
  chore(deploy): deploy-to-test.sh 增加数据库迁移
```

## 版本发布

```bash
# main → tag → 生产部署
rtk git tag -a v1.2.0 -m "feat: DQC Phase 1 + 参数系统"
rtk git push origin v1.2.0
```

## 回滚策略

| 场景 | 回滚方式 |
|------|---------|
| 部署后 5 分钟内发现严重 bug | `git revert HEAD` + 重新部署上一个 tag |
| 数据库 migration 导致问题 | 手动执行 down-migration（需提前准备） |
| 容器启动失败 | `docker compose down && docker compose up -d` |

## Agent skills

本项目已配置 Matt Pocock Engineering Skills 流水线。

### 核心文档

| 文档 | 位置 | 作用 |
|------|------|------|
| `CONTEXT.md` | 项目根目录 | 领域术语字典 |
| `docs/adr/NNNN-title.md` | `docs/adr/` | 架构决策记录 |
| `docs/agents/issue-tracker.md` | `docs/agents/` | issue tracker 位置 |
| `docs/agents/triage-labels.md` | `docs/agents/` | triage 状态标签 |
| `docs/agents/domain.md` | `docs/agents/` | 文档布局规则 |
| `docs/agents/AGENT-BRIEF.md` | `docs/agents/` | agent brief 规范 |
| `docs/agents/OUT-OF-SCOPE.md` | `docs/agents/` | 已拒绝方案知识库 |

### 可用技能

| 技能 | 触发时机 |
|------|---------|
| `/grill-with-docs` | 需求澄清，对齐领域语言，更新 CONTEXT.md |
| `/tdd` | 编码实现（垂直切片测试驱动） |
| `/diagnose` | 复杂 bug 排查 |
| `/improve-codebase-architecture` | 架构改进（发现隐藏耦合、模块边界模糊时） |
| `/to-issues` | 需求拆解为 issue |
| `/to-prd` | 将需求写成 PRD |
| `/triage` | issue 分类 |

### 会话开始检查清单

1. 读取 `docs/agents/issue-tracker.md` 确认 issue tracker 位置
2. 当前目录下有没有 `CONTEXT.md`？没有则新功能开始前先 `/grill-with-docs`
3. 有没有 `ready-for-agent` 状态的 issue？有则从那里继续
4. 有没有未读的 handoff 文档（`$TMPDIR` 下）？有则先读

### 初始化状态

- [x] `docs/agents/` 目录已创建（issue-tracker、triage-labels、domain、AGENT-BRIEF、OUT-OF-SCOPE）
- [x] `.scratch/` 本地 issue tracker 目录已创建
- [x] `CONTEXT.md` 领域术语字典已创建
- [ ] `docs/adr/` 待补充首个 ADR

## GitHub 下载加速

```bash
curl -L -O "https://gh-proxy.com/https://github.com/user/repo/releases/download/v1.0/file.tar.gz"
```
