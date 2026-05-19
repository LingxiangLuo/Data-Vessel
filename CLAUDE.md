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
cd portal/frontend && npm run dev

# 前端类型检查
cd portal/frontend && npx vue-tsc --noEmit

# 前端构建验证
cd portal/frontend && npx vite build

# 后端本地启动
cd portal/backend && uvicorn main:app --reload --port 8000

# 后端语法检查
cd portal/backend && python3 -m compileall -q -d . -x '/\.venv/' .

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

```bash
# 1. 切分支
git checkout main && git pull origin main
git checkout -b feat/xxx

# 2. 本地测试
cd portal/backend && python3 -m compileall -q -d . -x '/\.venv/' .
cd portal/backend && ruff check .
cd portal/frontend && npm run build

# 3. 代码审查 — 每次非平凡修改后主动触发 quick-code-reviewer
#    3+ 文件 / auth / 新 API → deep-code-reviewer

# 4. 手动部署验证
bash scripts/deploy-to-test.sh

# 5. 合并到 main
git checkout main
git merge feat/xxx --no-ff
git push origin main
git branch -d feat/xxx
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
- 合并前 / 发 PR 前 → `release-engineer`
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
git tag -a v1.2.0 -m "feat: DQC Phase 1 + 参数系统"
git push origin v1.2.0
```

## 回滚策略

| 场景 | 回滚方式 |
|------|---------|
| 部署后 5 分钟内发现严重 bug | `git revert HEAD` + 重新部署上一个 tag |
| 数据库 migration 导致问题 | 手动执行 down-migration（需提前准备） |
| 容器启动失败 | `docker compose down && docker compose up -d` |

## GitHub 下载加速

```bash
curl -L -O "https://gh-proxy.com/https://github.com/user/repo/releases/download/v1.0/file.tar.gz"
```
