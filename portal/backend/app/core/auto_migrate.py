"""自动化数据库迁移：检测模型与数据库 schema 差异，自动修复。

与 migrations.py 分工：
- auto_migrate.py：自动处理「新增表」「新增列」（99% 的场景）
- migrations.py：手动处理「数据迁移」「列类型变更」「复杂索引变更」

在 main.py 启动时自动调用，或在 deploy-to-test.sh 中显式调用。"""

import logging
from typing import Set

from sqlalchemy import inspect, text
from sqlalchemy.dialects.mysql import DATETIME, JSON

from app.core.database import Base, engine

logger = logging.getLogger(__name__)


def auto_migrate():
    """自动创建缺失的表，自动添加缺失的列。幂等可重复执行。"""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    # 1. 自动创建缺失的表
    _create_missing_tables(existing_tables)

    # 2. 自动添加缺失的列
    _add_missing_columns(inspector, existing_tables)


def _create_missing_tables(existing_tables: Set[str]):
    """使用 Base.metadata.create_all() 自动创建所有缺失的表。"""
    missing = set(Base.metadata.tables.keys()) - existing_tables
    if not missing:
        return

    logger.info(f"[auto_migrate] 创建缺失的表: {missing}")
    Base.metadata.create_all(bind=engine, tables=[
        Base.metadata.tables[t] for t in missing
    ])
    logger.info(f"[auto_migrate] 表创建完成: {missing}")


def _add_missing_columns(inspector, existing_tables: Set[str]):
    """遍历所有已存在的表，检查是否有模型中定义但数据库中不存在的列。"""
    for table_name, table_obj in Base.metadata.tables.items():
        if table_name not in existing_tables:
            continue  # 新表已在 create_all 中处理

        existing_columns = {c["name"] for c in inspector.get_columns(table_name)}

        for column in table_obj.columns:
            if column.name in existing_columns:
                continue

            _add_column(table_name, column)


def _add_column(table_name: str, column):
    """为指定表添加单个列，生成兼容 MySQL 的 ALTER TABLE 语句。"""
    col_name = column.name
    col_type = column.type

    # 基础类型映射
    type_str = str(col_type)

    # 处理特殊类型
    if isinstance(col_type, JSON):
        type_str = "JSON"
    elif isinstance(col_type, DATETIME):
        type_str = "DATETIME"
    elif hasattr(col_type, "length") and col_type.length:
        type_str = f"{col_type.__visit_name__.upper()}({col_type.length})"

    # 构建列定义
    nullable = "NULL" if column.nullable else "NOT NULL"
    default = ""
    if column.default is not None and hasattr(column.default, "arg"):
        arg = column.default.arg
        if isinstance(arg, str):
            default = f" DEFAULT '{arg}'"
        else:
            default = f" DEFAULT {arg}"

    comment = f" COMMENT '{column.comment}'" if column.comment else ""

    ddl = (
        f"ALTER TABLE {table_name} "
        f"ADD COLUMN {col_name} {type_str} {nullable}{default}{comment}"
    )

    with engine.connect() as conn:
        try:
            conn.execute(text(ddl))
            conn.commit()
            logger.info(f"[auto_migrate] {table_name}.{col_name} 列已添加 ({type_str})")
        except Exception:
            logger.exception(f"[auto_migrate] {table_name}.{col_name} 列添加失败: {ddl}")
            raise
