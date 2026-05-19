"""pytest fixtures: MySQL test DB + dependency overrides"""
import os
import uuid
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db

# 使用环境变量中的 DATABASE_URL，但指向独立测试库
_original_url = os.environ.get("DATABASE_URL", "mysql+pymysql://root:test@mysql:3306/portal_db")
# 替换数据库名为测试库
_test_db_name = f"portal_db_test_{uuid.uuid4().hex[:8]}"
_admin_url = _original_url.rsplit("/", 1)[0]  # 去掉数据库名，用于创建/删除库
_test_url = f"{_admin_url}/{_test_db_name}"

# 创建测试数据库
_admin_engine = create_engine(_admin_url)
with _admin_engine.connect() as conn:
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {_test_db_name} CHARACTER SET utf8mb4"))
    conn.commit()
_admin_engine.dispose()

# 创建测试引擎
_test_engine = create_engine(_test_url)
Base.metadata.create_all(bind=_test_engine)
TestSessionLocal = sessionmaker(bind=_test_engine)

# Patch app 的数据库连接
import app.core.database as _db_module
_db_module.engine = _test_engine
_db_module.SessionLocal = TestSessionLocal


@pytest.fixture
def db_session():
    """每个测试在 SAVEPOINT 中运行，应用层 commit 仅结束 SAVEPOINT，外层事务统一回滚。"""
    connection = _test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    # 开启嵌套事务，让应用代码里的 db.commit() 只提交到 SAVEPOINT
    session.begin_nested()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with DB session override."""
    from fastapi.testclient import TestClient
    from main import app

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """创建测试用户并返回（同时绑定 RBAC developer 角色）。"""
    from app.models.user import SysUser
    from app.models.role import SysRole, SysUserRole
    from app.core.security import hash_password

    user = SysUser(
        username="testuser",
        password=hash_password("TestPass123"),
        real_name="测试用户",
        role="developer",
        status=1,
    )
    db_session.add(user)
    db_session.flush()
    db_session.refresh(user)

    dev_role = db_session.query(SysRole).filter(SysRole.code == "developer").first()
    if dev_role:
        db_session.add(SysUserRole(user_id=user.id, role_id=dev_role.id))
        db_session.flush()

    return user


@pytest.fixture
def admin_user(db_session):
    """创建管理员测试用户并返回（同时绑定 RBAC admin 角色）。"""
    from app.models.user import SysUser
    from app.models.role import SysRole, SysUserRole
    from app.core.security import hash_password

    user = SysUser(
        username="testadmin",
        password=hash_password("AdminPass123"),
        real_name="测试管理员",
        role="admin",
        status=1,
    )
    db_session.add(user)
    db_session.flush()
    db_session.refresh(user)

    admin_role = db_session.query(SysRole).filter(SysRole.code == "admin").first()
    if admin_role:
        db_session.add(SysUserRole(user_id=user.id, role_id=admin_role.id))
        db_session.flush()

    return user


@pytest.fixture
def auth_client(client, test_user):
    """已登录的 TestClient（携带 cookie token）。"""
    from app.core.security import create_access_token

    token = create_access_token({"sub": test_user.username})
    client.cookies.set("access_token", token)
    return client


@pytest.fixture(autouse=True)
def _clear_in_memory_state():
    """每个测试前清除内存状态（限速、token 黑名单），避免测试间互相污染。"""
    import app.api.auth as _auth_module
    _auth_module._login_attempts.clear()
    _auth_module._user_login_attempts.clear()
    import app.core.security as _security_module
    _security_module._token_blacklist.clear()
    yield


@pytest.fixture
def sample_datasource(db_session, test_user):
    """创建一个测试数据源。"""
    from app.models.datasource import DataSource
    from app.models.resource_access import SysResourceAccess
    ds = DataSource(
        name="test_mysql",
        type="mysql",
        host="localhost",
        port=3306,
        database_name="test_db",
        username="root",
        password="encrypted_pass",
        description="测试数据源",
        created_by=test_user.id,
    )
    db_session.add(ds)
    db_session.flush()
    db_session.refresh(ds)
    db_session.add(SysResourceAccess(
        resource_type="datasource",
        resource_id=ds.id,
        subject_type="user",
        subject_id=test_user.id,
        permission="admin",
        granted_by=test_user.id,
    ))
    db_session.flush()
    return ds


@pytest.fixture
def sample_component(db_session, test_user):
    """创建一个测试 SQL 组件。"""
    from app.models.component import Component
    c = Component(
        name="test_sql_comp",
        type="sql",
        description="测试组件",
        config_json={"sql": "SELECT 1"},
        status="draft",
        version=1,
        created_by=test_user.id,
    )
    db_session.add(c)
    db_session.flush()
    db_session.refresh(c)
    return c


def pytest_sessionfinish(session, exitstatus):
    """测试结束后清理测试数据库。"""
    _admin_engine = create_engine(_admin_url)
    with _admin_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {_test_db_name}"))
        conn.commit()
    _admin_engine.dispose()
