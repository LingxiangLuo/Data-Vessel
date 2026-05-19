import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# 确保 app 包在路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import Base

# 导入所有模型以确保元数据完整
from app.models.user import SysUser  # noqa: F401
from app.models.datasource import DataSource  # noqa: F401
from app.models.component import Component  # noqa: F401
from app.models.component_folder import ComponentFolder  # noqa: F401
from app.models.sync_task import SyncTask  # noqa: F401
from app.models.workflow import Workflow  # noqa: F401
from app.models.word_root import WordRoot  # noqa: F401
from app.models.role import SysRole, SysPermission, SysRolePermission, SysUserRole  # noqa: F401
from app.models.resource_access import SysResourceAccess  # noqa: F401
from app.models.oauth_config import SysOAuthConfig  # noqa: F401
from app.models.sys_config import SysConfig  # noqa: F401
from app.models.sys_notify_channel import SysNotifyChannel  # noqa: F401
from app.models.project import Project  # noqa: F401

# this is the Alembic Config object
config = context.config

# 从 settings 动态注入数据库 URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
