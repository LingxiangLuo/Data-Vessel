from sqlalchemy import Column, BigInteger, String, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class DqcRule(Base):
    """数据质量规则定义"""
    __tablename__ = "dqc_rule"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    datasource_id = Column(BigInteger, nullable=False, index=True)
    table_name = Column(String(128), nullable=False)
    column_name = Column(String(128), nullable=True)
    rule_type = Column(String(32), nullable=False)
    operator = Column(String(16), nullable=False)
    threshold = Column(String(64), nullable=False)
    threshold_max = Column(String(64), nullable=True)
    is_strong = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True, nullable=False)
    notify_channel_ids = Column(JSON, nullable=True)
    extra_config = Column(JSON, nullable=True)  # custom_sql, pattern, min_value, max_value 等
    component_id = Column(BigInteger, nullable=True, index=True, comment="来源组件 ID")
    description = Column(Text)
    created_by = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
