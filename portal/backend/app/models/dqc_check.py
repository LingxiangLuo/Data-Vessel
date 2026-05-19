from sqlalchemy import Column, BigInteger, String, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class DqcCheck(Base):
    """数据质量检查记录"""
    __tablename__ = "dqc_check"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    rule_id = Column(BigInteger, nullable=False, index=True)
    actual_value = Column(String(255), nullable=True)
    expected_value = Column(String(255), nullable=True)
    passed = Column(Boolean, nullable=False)
    error_msg = Column(Text, nullable=True)
    instance_id = Column(BigInteger, nullable=True)
    sample_data = Column(JSON, nullable=True)  # 失败采样数据 [{col: val, ...}]
    checked_at = Column(DateTime, server_default=func.now())
