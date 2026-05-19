# Data Platform MVP · 数据中台

<p align="center">
  <img src="https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js" alt="Vue 3">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/DolphinScheduler-3.2-0078D4" alt="DolphinScheduler">
  <img src="https://img.shields.io/badge/DataX-3.x-FF6A00" alt="DataX">
  <img src="https://img.shields.io/badge/Vue_Flow-1.x-7B68EE" alt="Vue Flow">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License">
</p>

> 面向中小团队的轻量级一站式数据中台，覆盖数据开发、工作流编排、运维监控、数据资产全链路。

---

## 目录

- [功能概览](#功能概览)
- [信息架构](#信息架构)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [本地开发](#本地开发)
- [核心功能](#核心功能)
- [API 文档](#api-文档)
- [常见问题](#常见问题)
- [设计取舍](#设计取舍)
- [安全注意事项](#安全注意事项)
- [License](#license)

---

## 功能概览

| 模块 | 说明 |
|---|---|
| **工作台** | 任务运行概览、成功率趋势、快捷入口 |
| **工作流开发** | DAG 画布编辑器（Vue Flow），拖拽连线，支持并行分支和汇聚，右键跳过节点 |
| **代码开发** | SQL/Python/Shell IDE，Monaco Editor，目录树，表名/字段智能补全，一键发布为节点 |
| **数据同步** | 可视化字段映射，DataX 驱动，支持全量/增量，一键建表 |
| **运行实例** | KPI 卡片，竖向时间线子任务，运行中 pulse 动效，日志查看，重跑 |
| **数据资产** | 表级元数据浏览，字段搜索，数据血缘 |
| **系统监控** | 各服务健康状态，DS Worker 资源占用 |

<details>
<summary>点击查看截图</summary>

### 数据源管理
![数据源管理](docs/screenshots/datasource-management.png)

### 数据同步 · 字段映射
![同步任务字段映射](docs/screenshots/sync-task-mapping.png)

### 代码开发 · SQL IDE
![SQL IDE](docs/screenshots/sql-ide.png)

### 组件管理
![组件管理](docs/screenshots/component-management.png)

### 工作流开发（DAG）
![工作流编辑](docs/screenshots/workflow-editor.png)

### 运行实例
![运行记录](docs/screenshots/execution-history.png)

### 数据血缘
![数据血缘](docs/screenshots/data-lineage.png)

### 数据资产
![数据资产](docs/screenshots/data-assets.png)

### 系统监控
![系统监控](docs/screenshots/system-monitor.png)

</details>

---

## 信息架构

```
工作台

数据开发
  ├─ 工作流开发    DAG 画布，拖拽编排，发布到 DolphinScheduler
  ├─ 代码开发      SQL/Python/Shell IDE，Monaco Editor
  └─ 数据同步      DataX 离线同步，可视化字段映射

运维中心
  ├─ 运行实例      任务执行历史，时间线子任务，日志，重跑
  └─ 告警通知      （开发中）

数据资产
  ├─ 数据表        表级元数据，行数/大小/注释
  ├─ 字段资产      跨表字段搜索
  └─ 数据血缘      血缘图谱

系统管理
  ├─ 数据源管理    MySQL 连接管理，连接测试
  └─ 系统监控      服务健康状态，DS Worker 资源
```

---

## 技术架构

```
                    Browser
                       │ HTTP :80
              ┌────────▼────────┐
              │     Nginx       │  静态资源 + 反向代理
              └──┬──────────────┘
        /api/*   │
   ┌─────────────▼─┐
   │ Portal Backend│  FastAPI
   │   FastAPI     │
   └────┬─────┬────┘
        │     │
   ┌────▼─┐ ┌─▼──────────────────┐
   │ MySQL│ │ DolphinScheduler   │──── DataX Jobs
   │ 8.0  │ │ (调度 + 执行引擎)  │
   └──────┘ └────────────────────┘
                 │
            Redis 7 (DS 分布式协调)
```

### 技术栈

| 组件 | 版本 | 职责 |
|---|---|---|
| **Vue 3** + Arco Design | 3.x | 前端 SPA |
| **Vue Flow** | 1.x | 工作流 DAG 画布 |
| **Monaco Editor** | latest | SQL/Python/Shell 代码编辑器 |
| **FastAPI** | 0.115+ | Portal 后端 REST API |
| **SQLAlchemy** | 2.x | ORM，MySQL 连接 |
| **MySQL** | 8.0 | 元数据库 |
| **Redis** | 7-alpine | DolphinScheduler 分布式协调 |
| **DolphinScheduler** | 3.2.2 | 工作流调度引擎 |
| **DataX** | 3.x | 离线数据同步框架 |
| **Nginx** | 1.25 | 统一入口网关 |

### 项目结构

```
data-platform-mvp/
├── docker-compose.yml
├── nginx/nginx.conf
├── portal/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/          # 路由层（workflow/component/datasource...）
│   │   │   ├── core/         # DSL Translator, DS Client, DataX Builder
│   │   │   └── models/       # SQLAlchemy 模型
│   │   └── main.py
│   └── frontend/
│       └── src/
│           ├── components/dag/   # DAG 画布组件（Vue Flow）
│           ├── views/            # 页面
│           ├── api/index.ts      # 接口封装
│           └── router/
└── scripts/                  # 运维脚本
```

---

## 快速开始

### 环境要求

- Docker 24+ & Docker Compose v2
- 服务器 ≥ 8 核 16 GB
- 开放端口：`80`（唯一对外端口）

### 一键部署

```bash
# 1. 克隆项目
git clone https://github.com/barryLiu199/data-platform-mvp.git
cd data-platform-mvp

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，修改所有密码

# 3. 构建并启动
docker compose up -d --build

# 4. 等待服务就绪（首次约 3-5 分钟）
docker compose ps

# 5. 访问
# Portal: http://<your-ip>
# 默认账号: admin / admin123
```

### 环境变量

| 变量 | 说明 |
|---|---|
| `MYSQL_ROOT_PASSWORD` | MySQL root 密码 |
| `REDIS_PASSWORD` | Redis 密码 |
| `PORTAL_SECRET_KEY` | JWT 签名密钥（≥32字符） |
| `DS_ADMIN_PASSWORD` | DolphinScheduler 管理员密码 |
| `PORTAL_BASE_URL` | 外网访问地址（如 `http://your-ip`） |

### 服务器更新部署

```bash
# 服务器上执行
bash /opt/deploy.sh
```

---

## 本地开发

### 后端

```bash
cd portal/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 前端

```bash
cd portal/frontend
npm install
npm run dev
```

---

## 核心功能

### 工作流开发（DAG）

- 左侧组件面板，拖拽已上线组件到画布
- 连线建立依赖关系，支持并行分支（一对多）和汇聚（多对一）
- 右键节点：跳过/取消跳过/删除
- 工具栏：保存、测试、发布（同步到 DolphinScheduler）、手动运行、自动布局
- 发布时自动进行环检测，有环则拒绝

### 代码开发 · IDE

- SQL/Python/Shell 多语言，目录树三级嵌套
- SQL 智能补全：关键字、函数、表名、字段名（实时拉取元数据）
- 选中部分 SQL 单独执行，结果表格展示
- 一键发布为「组件」供工作流复用

### 数据同步

- 可视化字段映射（拖拽连线），支持常量/调度变量
- 全量/增量同步，自动生成 DataX JSON
- 一键建表（DDL 预览后执行）
- 由 DolphinScheduler 驱动执行

### 运行实例

- KPI 卡片：成功率、运行中数量、异常数
- 运行中任务 pulse 动效
- 展开实例查看竖向时间线子任务
- 任务日志查看（深色终端风格）
- 一键重跑

---

## API 文档

启动后访问：`http://<your-ip>/docs`

---

## 常见问题

**Q: DolphinScheduler 启动慢？**

A: standalone 模式首次启动约 2-3 分钟，查看日志：
```bash
docker logs -f dmp-ds
```

**Q: 工作流发布失败？**

A: 确认所有节点的组件状态为「已上线」，且 DS 服务健康（系统监控页面查看）。

**Q: 如何重置 admin 密码？**

```bash
docker exec -it dmp-mysql mysql -uroot -p portal_db \
  -e "UPDATE sys_user SET password='\$2b\$12\$...' WHERE username='admin';"
```

---

## 设计取舍

| 决策 | 原因 |
|---|---|
| Portal First + Headless DS | Portal 是唯一 UI 和真相源，DS 作为无头执行引擎 |
| DataX 翻译为 DS SHELL 节点 | 不依赖 DS 原生 DataX 节点，避免版本耦合 |
| 单节点 DS standalone | 降低运维复杂度，适合中小团队 |
| 直连 information_schema | 替代 OpenMetadata，减少 3GB 内存占用 |
| Nginx 唯一对外端口 | 安全隔离，所有内部服务走容器内网 |

---

## 安全注意事项

1. **修改所有默认密码**：`.env` 中所有密码使用强密码（≥16位）
2. **配置 HTTPS**：生产环境通过 HTTPS 访问
3. **限制 CORS**：修改 `portal/backend/main.py` 中的 `allow_origins`
4. **不要提交 `.env`**：已在 `.gitignore` 中排除

---

## License

MIT
