from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class WordRoot(Base):
    """词根管理 — 数据命名规范化"""
    __tablename__ = "word_root"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    en = Column(String(64), nullable=False, unique=True, comment="英文词根")
    cn = Column(String(64), nullable=False, comment="中文名")
    category = Column(String(32), nullable=False, default="business", comment="business/technical/metric")
    description = Column(String(255), nullable=True, comment="说明")
    example = Column(String(255), nullable=True, comment="示例用法")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
