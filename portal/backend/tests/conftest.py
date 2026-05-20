"""pytest fixtures: SQLite in-memory DB + FastAPI TestClient + seed data"""
import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890")
os.environ.setdefault("DQC_SERVICE_TOKEN", "test-service-token")
os.environ.setdefault("COOKIE_SECURE", "false")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Patch the module-level engine before any app code imports it
import app.core.database as _db_module
_db_module.engine = _test_engine
_db_module.SessionLocal = sessionmaker(bind=_test_engine)

# Patch BigInteger → Integer for SQLite so autoincrement works across all models
import sqlalchemy as _sa
_sa.BigInteger = _sa.Integer

# Prevent MySQL-specific migrations from running in SQLite test env
import app.core.migrations as _migrations_module
import app.core.auto_migrate as _auto_migrate_module
_migrations_module.run_all_migrations = lambda: None
_auto_migrate_module.auto_migrate = lambda: None

# Prevent lifespan seed functions from running (they use SessionLocal without explicit ids)
_main_module_seed_patch = lambda: None

# Import main.py to trigger all model imports + Base.metadata.create_all
# (main.py calls Base.metadata.create_all at module level when alembic fails)
import main as _main_module
_main_module._seed_roles_and_permissions = _main_module_seed_patch
_main_module._ensure_admin = _main_module_seed_patch
_main_module._ensure_default_project = _main_module_seed_patch
_main_module.Base.metadata.create_all(bind=_test_engine)

# Disable Secure cookie flag in tests so TestClient (HTTP) sends cookies
from app.core.config import settings as _settings
_settings.COOKIE_SECURE = False

# Seed basic roles/permissions so permission checks work in tests
from app.core.database import SessionLocal
_db = SessionLocal()
from app.core.security import hash_password

try:
    from app.models.role import SysRole, SysPermission, SysRolePermission
    from app.models.user import SysUser

    # Create basic permissions (SQLite BigInteger + autoincrement needs explicit id)
    # Must match _BUILTIN_PERMISSIONS in main.py
    perm_codes = [
        (1, "user:manage", "用户管理", "user", "manage"),
        (2, "role:manage", "角色管理", "role", "manage"),
        (3, "system:config", "系统配置", "system", "config"),
        (4, "datasource:read", "数据源查看", "datasource", "read"),
        (5, "datasource:write", "数据源编辑", "datasource", "write"),
        (6, "component:read", "组件查看", "component", "read"),
        (7, "component:create", "组件创建", "component", "create"),
        (8, "component:write", "组件编辑", "component", "write"),
        (9, "component:publish", "组件发布/下线", "component", "publish"),
        (10, "workflow:read", "工作流查看", "workflow", "read"),
        (11, "workflow:create", "工作流创建", "workflow", "create"),
        (12, "workflow:write", "工作流编辑", "workflow", "write"),
        (13, "workflow:publish", "工作流发布/下线", "workflow", "publish"),
        (14, "sync:read", "数据同步查看", "sync", "read"),
        (15, "sync:write", "数据同步编辑", "sync", "write"),
        (16, "metadata:read", "数据资产查看", "metadata", "read"),
        (17, "metadata:write", "数据资产编辑", "metadata", "write"),
        (18, "monitor:read", "系统监控查看", "monitor", "read"),
        (19, "monitor:write", "监控规则编辑", "monitor", "write"),
        (20, "dqc:read", "数据质量查看", "dqc", "read"),
        (21, "dqc:write", "数据质量编辑", "dqc", "write"),
    ]
    for pid, code, name, rtype, action in perm_codes:
        if not _db.query(SysPermission).filter(SysPermission.code == code).first():
            _db.add(SysPermission(id=pid, code=code, name=name, resource_type=rtype, action=action))
    _db.flush()

    # Create admin role (all permissions)
    admin_role = _db.query(SysRole).filter(SysRole.code == "admin").first()
    if not admin_role:
        admin_role = SysRole(id=1, code="admin", name="管理员", description="拥有所有权限", is_system=True)
        _db.add(admin_role)
        _db.flush()

    # Create developer role (matching _BUILTIN_ROLES in main.py)
    dev_role = _db.query(SysRole).filter(SysRole.code == "developer").first()
    if not dev_role:
        dev_role = SysRole(id=2, code="developer", name="开发者", description="可管理数据源、组件、工作流", is_system=True)
        _db.add(dev_role)
        _db.flush()

    # Assign all permissions to admin
    for _pid, code, _name, _rtype, _action in perm_codes:
        perm = _db.query(SysPermission).filter(SysPermission.code == code).first()
        if perm:
            exists = _db.query(SysRolePermission).filter(
                SysRolePermission.role_id == admin_role.id,
                SysRolePermission.permission_id == perm.id,
            ).first()
            if not exists:
                _db.add(SysRolePermission(role_id=admin_role.id, permission_id=perm.id))

    # Assign developer permissions (matching _BUILTIN_ROLES["developer"])
    dev_perm_codes = [
        "datasource:read", "datasource:write",
        "component:read", "component:create", "component:write", "component:publish",
        "workflow:read", "workflow:create", "workflow:write", "workflow:publish",
        "sync:read", "sync:write",
        "metadata:read", "metadata:write", "monitor:read", "monitor:write",
        "dqc:read", "dqc:write",
    ]
    for code in dev_perm_codes:
        perm = _db.query(SysPermission).filter(SysPermission.code == code).first()
        if perm:
            exists = _db.query(SysRolePermission).filter(
                SysRolePermission.role_id == dev_role.id,
                SysRolePermission.permission_id == perm.id,
            ).first()
            if not exists:
                _db.add(SysRolePermission(role_id=dev_role.id, permission_id=perm.id))

    # Create analyst role
    analyst_role = _db.query(SysRole).filter(SysRole.code == "analyst").first()
    if not analyst_role:
        analyst_role = SysRole(id=3, code="analyst", name="分析师", description="可查看数据资产和运行实例", is_system=True)
        _db.add(analyst_role)
        _db.flush()
    analyst_perm_codes = ["metadata:read", "monitor:read", "workflow:read", "component:read"]
    for code in analyst_perm_codes:
        perm = _db.query(SysPermission).filter(SysPermission.code == code).first()
        if perm:
            exists = _db.query(SysRolePermission).filter(
                SysRolePermission.role_id == analyst_role.id,
                SysRolePermission.permission_id == perm.id,
            ).first()
            if not exists:
                _db.add(SysRolePermission(role_id=analyst_role.id, permission_id=perm.id))

    # Create viewer role
    viewer_role = _db.query(SysRole).filter(SysRole.code == "viewer").first()
    if not viewer_role:
        viewer_role = SysRole(id=4, code="viewer", name="只读用户", description="只能查看数据资产", is_system=True)
        _db.add(viewer_role)
        _db.flush()
    viewer_perm = _db.query(SysPermission).filter(SysPermission.code == "metadata:read").first()
    if viewer_perm:
        exists = _db.query(SysRolePermission).filter(
            SysRolePermission.role_id == viewer_role.id,
            SysRolePermission.permission_id == viewer_perm.id,
        ).first()
        if not exists:
            _db.add(SysRolePermission(role_id=viewer_role.id, permission_id=viewer_perm.id))

    _db.commit()
except Exception:
    _db.rollback()
    raise
finally:
    _db.close()


@pytest.fixture(autouse=True)
def _clean_global_state():
    """清理测试间的全局状态，防止交叉污染。"""
    from app.api.auth import _login_attempts, _user_login_attempts
    from app.core.security import _token_blacklist
    _login_attempts.clear()
    _user_login_attempts.clear()
    _token_blacklist.clear()
    yield


@pytest.fixture
def db_session():
    from app.core.database import SessionLocal as _SessionLocal
    session = _SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client():
    """FastAPI TestClient without authentication."""
    from fastapi.testclient import TestClient
    from app.core.database import get_db

    def _get_db_override():
        from app.core.database import SessionLocal as _SessionLocal
        db = _SessionLocal()
        try:
            yield db
        finally:
            db.close()

    _main_module.app.dependency_overrides[get_db] = _get_db_override

    with TestClient(_main_module.app) as c:
        yield c

    _main_module.app.dependency_overrides.clear()


@pytest.fixture
def test_user():
    """Create (or reuse) a test user in the database."""
    from app.core.database import SessionLocal as _SessionLocal
    from app.models.user import SysUser
    from app.models.role import SysUserRole, SysRole
    db = _SessionLocal()
    try:
        existing = db.query(SysUser).filter(SysUser.username == "testuser").first()
        if existing:
            # Reset password in case a previous test changed it
            existing.password = hash_password("TestPass123")
            # Ensure RBAC link exists
            dev_role = db.query(SysRole).filter(SysRole.code == "developer").first()
            if dev_role:
                link = db.query(SysUserRole).filter(
                    SysUserRole.user_id == existing.id,
                    SysUserRole.role_id == dev_role.id,
                ).first()
                if not link:
                    db.add(SysUserRole(user_id=existing.id, role_id=dev_role.id))
            db.commit()
            db.refresh(existing)
            yield existing
            return

        user = SysUser(
            id=1,
            username="testuser",
            password=hash_password("TestPass123"),
            real_name="Test User",
            role="developer",
            status=1,
        )
        db.add(user)
        db.flush()

        dev_role = db.query(SysRole).filter(SysRole.code == "developer").first()
        if dev_role:
            db.add(SysUserRole(user_id=user.id, role_id=dev_role.id))

        db.commit()
        db.refresh(user)
        yield user
    finally:
        db.close()


@pytest.fixture
def auth_client(client, test_user):
    """FastAPI TestClient with authentication cookie.

    Bypasses the real login endpoint to avoid Secure-cookie / CSRF
    cross-request issues under pytest's module-import ordering.
    """
    import secrets
    from app.core.security import create_access_token

    token = create_access_token(data={"sub": test_user.username})
    client.cookies.set("access_token", token)

    csrf = secrets.token_urlsafe(32)
    client.cookies.set("csrf_token", csrf)
    client.headers["X-CSRF-Token"] = csrf

    return client


@pytest.fixture
def sample_component():
    """Create (or reuse) a test SQL component."""
    from app.core.database import SessionLocal as _SessionLocal
    from app.models.component import Component
    db = _SessionLocal()
    try:
        existing = db.query(Component).filter(Component.name == "test_sql_comp").first()
        if existing:
            # Reset status in case a previous test changed it
            existing.status = "draft"
            existing.folder_id = None
            db.commit()
            db.refresh(existing)
            yield existing
            return
        comp = Component(
            name="test_sql_comp",
            type="sql",
            description="Test SQL component",
            config_json={"sql": "SELECT 1", "datasource_id": None},
            status="draft",
            version=1,
        )
        db.add(comp)
        db.flush()
        db.refresh(comp)
        yield comp
    finally:
        db.close()


@pytest.fixture
def sample_folder():
    """Create (or reuse) a test component folder."""
    from app.core.database import SessionLocal as _SessionLocal
    from app.models.component_folder import ComponentFolder
    db = _SessionLocal()
    try:
        existing = db.query(ComponentFolder).filter(ComponentFolder.name == "test_folder").first()
        if existing:
            yield existing
            return
        f = ComponentFolder(name="test_folder", type="sql")
        db.add(f)
        db.flush()
        db.refresh(f)
        yield f
    finally:
        db.close()


@pytest.fixture
def sample_datasource():
    """Create (or reuse) a test MySQL datasource with ACL."""
    from app.core.database import SessionLocal as _SessionLocal
    from app.models.datasource import DataSource
    from app.models.resource_access import SysResourceAccess
    db = _SessionLocal()
    try:
        existing = db.query(DataSource).filter(DataSource.name == "test_mysql").first()
        if existing:
            # Ensure ACL exists for testuser
            acl = db.query(SysResourceAccess).filter(
                SysResourceAccess.resource_type == "datasource",
                SysResourceAccess.resource_id == existing.id,
                SysResourceAccess.subject_type == "user",
                SysResourceAccess.subject_id == 1,
            ).first()
            if not acl:
                db.add(SysResourceAccess(
                    resource_type="datasource",
                    resource_id=existing.id,
                    subject_type="user",
                    subject_id=1,
                    permission="admin",
                    granted_by=1,
                ))
                db.commit()
            yield existing
            return
        ds = DataSource(
            name="test_mysql",
            type="mysql",
            host="127.0.0.1",
            port=3306,
            database_name="test_db",
            username="root",
            password="encrypted_pass",
        )
        db.add(ds)
        db.flush()
        db.refresh(ds)
        # Grant testuser admin access so resource ACL checks pass
        db.add(SysResourceAccess(
            resource_type="datasource",
            resource_id=ds.id,
            subject_type="user",
            subject_id=1,
            permission="admin",
            granted_by=1,
        ))
        db.commit()
        yield ds
    finally:
        db.close()
