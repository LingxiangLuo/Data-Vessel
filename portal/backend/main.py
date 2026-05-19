import sys
import os
import logging
import secrets
import bcrypt
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.logging_config import setup_logging
from app.core.request_id import RequestIdMiddleware

# 开发环境用彩色文本，生产环境可设 JSON_FORMAT=true
json_logs = os.environ.get("JSON_FORMAT", "").lower() in ("1", "true", "yes")
setup_logging(json_format=json_logs)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.database import engine, Base, SessionLocal
from app.core.config import settings
from app.core.security import hash_password

# ─── 启动时安全校验 ──────────────────────────────────────────────────────────
if not getattr(settings, "DQC_SERVICE_TOKEN", ""):
    logging.warning("DQC_SERVICE_TOKEN 未配置，服务间调用将不可用。请在 .env 中设置强随机值。")

from app.core.migrations import run_all_migrations
from app.core.auto_migrate import auto_migrate
from app.api import auth, datasources, sync_tasks, dashboard, ds_proxy, notifications, component, workflow, system, metadata, project
from app.models.component import ComponentHistory  # noqa: F401
from app.models.component_folder import ComponentFolder  # noqa: F401
from app.models.role import SysRole, SysPermission, SysRolePermission, SysUserRole  # noqa: F401
from app.models.resource_access import SysResourceAccess  # noqa: F401
from app.models.oauth_config import SysOAuthConfig  # noqa: F401
from app.models.sys_config import SysConfig  # noqa: F401
from app.models.sys_notify_channel import SysNotifyChannel  # noqa: F401
from app.models.dqc_rule import DqcRule  # noqa: F401
from app.models.dqc_check import DqcCheck  # noqa: F401
from app.models.dqc_report import DqcReport, DqcReportHistory  # noqa: F401

# 数据库迁移：优先使用 Alembic
import subprocess
alembic_ok = False
try:
    result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
    if result.returncode == 0:
        alembic_ok = True
    else:
        logging.warning(f"Alembic 迁移失败: {result.stderr}")
except FileNotFoundError:
    logging.warning("Alembic 未安装，跳过 Alembic 迁移")
except Exception as e:
    logging.warning(f"Alembic 迁移异常: {e}")

# Alembic 不可用时降级到 create_all（仅开发环境）
if not alembic_ok:
    Base.metadata.create_all(bind=engine)
run_all_migrations()


# ─── 种子数据：4 个内置角色 + 权限列表 ──────────────────────────────────────

_BUILTIN_PERMISSIONS = [
    ("user:manage",       "用户管理",       "user",       "manage"),
    ("role:manage",       "角色管理",       "role",       "manage"),
    ("system:config",     "系统配置",       "system",     "config"),
    ("datasource:read",   "数据源查看",     "datasource", "read"),
    ("datasource:write",  "数据源编辑",     "datasource", "write"),
    ("component:read",    "组件查看",       "component",  "read"),
    ("component:create",  "组件创建",       "component",  "create"),
    ("component:write",   "组件编辑",       "component",  "write"),
    ("component:publish", "组件发布/下线",  "component",  "publish"),
    ("workflow:read",     "工作流查看",     "workflow",   "read"),
    ("workflow:create",   "工作流创建",     "workflow",   "create"),
    ("workflow:write",    "工作流编辑",     "workflow",   "write"),
    ("workflow:publish",  "工作流发布/下线","workflow",   "publish"),
    ("sync:read",         "数据同步查看",   "sync",       "read"),
    ("sync:write",        "数据同步编辑",   "sync",       "write"),
    ("metadata:read",     "数据资产查看",   "metadata",   "read"),
    ("metadata:write",    "数据资产编辑",   "metadata",   "write"),
    ("monitor:read",      "系统监控查看",   "monitor",    "read"),
    ("monitor:write",     "监控规则编辑",   "monitor",    "write"),
    ("dqc:read",          "数据质量查看",   "dqc",        "read"),
    ("dqc:write",         "数据质量编辑",   "dqc",        "write"),
]

_BUILTIN_ROLES = {
    "admin": {
        "name": "管理员",
        "description": "拥有所有权限",
        "permissions": [p[0] for p in _BUILTIN_PERMISSIONS],
    },
    "developer": {
        "name": "开发者",
        "description": "可管理数据源、组件、工作流、数据同步",
        "permissions": [
            "datasource:read", "datasource:write",
            "component:read", "component:create", "component:write", "component:publish",
            "workflow:read", "workflow:create", "workflow:write", "workflow:publish",
            "sync:read", "sync:write",
            "metadata:read", "metadata:write", "monitor:read", "monitor:write",
            "dqc:read", "dqc:write",
        ],
    },
    "analyst": {
        "name": "分析师",
        "description": "可查看数据资产和运行实例",
        "permissions": ["metadata:read", "monitor:read", "workflow:read", "component:read"],
    },
    "viewer": {
        "name": "只读用户",
        "description": "只能查看数据资产",
        "permissions": ["metadata:read"],
    },
}


def _seed_roles_and_permissions():
    from app.models.role import SysRole, SysPermission, SysRolePermission
    db = SessionLocal()
    try:
        for code, name, resource_type, action in _BUILTIN_PERMISSIONS:
            if not db.query(SysPermission).filter(SysPermission.code == code).first():
                db.add(SysPermission(code=code, name=name, resource_type=resource_type, action=action))
        db.flush()

        for role_code, role_info in _BUILTIN_ROLES.items():
            role = db.query(SysRole).filter(SysRole.code == role_code).first()
            if not role:
                role = SysRole(
                    code=role_code,
                    name=role_info["name"],
                    description=role_info["description"],
                    is_system=True,
                )
                db.add(role)
                db.flush()

            existing_perm_ids = {
                rp.permission_id
                for rp in db.query(SysRolePermission).filter(SysRolePermission.role_id == role.id).all()
            }
            for perm_code in role_info["permissions"]:
                perm = db.query(SysPermission).filter(SysPermission.code == perm_code).first()
                if perm and perm.id not in existing_perm_ids:
                    db.add(SysRolePermission(role_id=role.id, permission_id=perm.id))

        db.commit()
    finally:
        db.close()


_seed_roles_and_permissions()


# 确保管理员账号存在并关联 RBAC admin 角色
def _ensure_admin():
    from app.models.user import SysUser
    from app.models.role import SysRole, SysUserRole
    db = SessionLocal()
    try:
        admin = db.query(SysUser).filter(SysUser.username == "admin").first()
        if not admin and settings.ADMIN_INIT_PASSWORD:
            admin = SysUser(
                username="admin",
                password=hash_password(settings.ADMIN_INIT_PASSWORD),
                real_name="系统管理员",
                role="admin",
                status=1,
            )
            db.add(admin)
            db.flush()

        # 如果没有 admin 用户且未创建，跳过后续关联
        if not admin:
            db.commit()
            return

        # 确保 admin 用户关联了 RBAC admin 角色
        admin_role = db.query(SysRole).filter(SysRole.code == "admin").first()
        if admin_role:
            exists = db.query(SysUserRole).filter(
                SysUserRole.user_id == admin.id,
                SysUserRole.role_id == admin_role.id,
            ).first()
            if not exists:
                db.add(SysUserRole(user_id=admin.id, role_id=admin_role.id))

        # 保持 legacy role 字段与 RBAC 一致
        if admin.role != "admin":
            admin.role = "admin"
        if admin.status != 1:
            admin.status = 1

        db.commit()
    finally:
        db.close()


def _ensure_default_project():
    from app.api.project import ensure_default_project
    db = SessionLocal()
    try:
        ensure_default_project(db)
    finally:
        db.close()


_ensure_admin()
_ensure_default_project()

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # CSP：仅允许同源资源，禁止内联脚本，禁止不安全的来源
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "frame-ancestors 'none';"
        )
        return response


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF 防护中间件

    对使用 cookie 认证的状态变更请求验证 CSRF token。
    豁免：
      - GET/HEAD/OPTIONS（只读方法）
      - 无 auth cookie 的请求（未登录）
      - 使用 Bearer token 的请求（API 客户端）
      - /api/auth/* 路径（登录/登出/OAuth 本身）
    """
    EXEMPT_PATHS = {"/api/auth/login", "/api/auth/logout", "/api/auth/oauth", "/api/auth/csrf", "/api/health"}

    async def dispatch(self, request: Request, call_next):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(p) for p in self.EXEMPT_PATHS):
            return await call_next(request)

        # 有 Bearer token 的请求不需要 CSRF（API 客户端场景）
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            return await call_next(request)

        # 无 auth cookie 的请求不需要 CSRF（未登录）
        access_token = request.cookies.get("access_token")
        if not access_token:
            return await call_next(request)

        # 验证 CSRF token
        csrf_cookie = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("X-CSRF-Token")
        if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_cookie, csrf_header):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token 验证失败，请重新登录"},
            )

        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.dqc_scheduler import start_scheduler, shutdown_scheduler
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title="数据中台 MVP",
    description="金融行业离线数据中台统一门户 API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFProtectionMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS is not None else ["http://localhost:5173", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-CSRF-Token", "X-Request-ID"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(datasources.router, prefix="/api")
app.include_router(sync_tasks.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(ds_proxy.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(component.router, prefix="/api")
app.include_router(workflow.router, prefix="/api")
app.include_router(system.router, prefix="/api")
app.include_router(metadata.router, prefix="/api")
app.include_router(project.router, prefix="/api")

from app.api import alert_rules
app.include_router(alert_rules.router, prefix="/api")

from app.api import word_roots
app.include_router(word_roots.router, prefix="/api")

from app.api import admin
app.include_router(admin.router, prefix="/api")

from app.api import dqc_rules
app.include_router(dqc_rules.router, prefix="/api")

from app.api import dqc_reports
app.include_router(dqc_reports.router, prefix="/api")

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "portal-backend"}
