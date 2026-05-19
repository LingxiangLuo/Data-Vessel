"""自动化数据库 schema 差异检测（只检测，不执行 DDL）。

与 migrations.py / Alembic 分工：
- Alembic：唯一的 schema 变更来源（CREATE TABLE / ALTER TABLE / CREATE INDEX）
- auto_migrate.py：启动时检测模型与数据库差异，发现未同步的表/列时打 warning，提醒开发者写 migration
- migrations.py：手动处理「数据迁移」「列类型变更」「复杂索引变更」

在 main.py 启动时自动调用。"""

import logging
from typing import Set, List

from sqlalchemy import inspect

from app.core.database import Base, engine

logger = logging.getLogger(__name__)


def auto_migrate():
    """检测模型与数据库 schema 差异，只打日志不执行 DDL。"""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    # 1. 检测缺失的表
    missing_tables = _detect_missing_tables(existing_tables)

    # 2. 检测缺失的列
    missing_columns = _detect_missing_columns(inspector, existing_tables)

    if missing_tables or missing_columns:
        logger.warning(
            "[auto_migrate] 检测到 schema 差异，请通过 Alembic 写 migration 同步："
            f"缺失表: {missing_tables or '无'}, "
            f"缺失列: {missing_columns or '无'}"
        )
    else:
        logger.info("[auto_migrate] schema 检测完成，无差异")


def _detect_missing_tables(existing_tables: Set[str]) -> List[str]:
    """检测 Base.metadata 中有但数据库中缺失的表。"""
    missing = sorted(set(Base.metadata.tables.keys()) - existing_tables)
    if missing:
        logger.warning(f"[auto_migrate] 数据库缺失以下表（请写 Alembic migration）: {missing}")
    return missing


def _detect_missing_columns(inspector, existing_tables: Set[str]) -> List[str]:
    """检测已存在表中缺失的列。"""
    missing = []
    for table_name, table_obj in Base.metadata.tables.items():
        if table_name not in existing_tables:
            continue

        existing_columns = {c["name"] for c in inspector.get_columns(table_name)}

        for column in table_obj.columns:
            if column.name in existing_columns:
                continue
            missing.append(f"{table_name}.{column.name}")

    if missing:
        logger.warning(
            f"[auto_migrate] 数据库缺失以下列（请写 Alembic migration）: {missing}"
        )
    return missing
