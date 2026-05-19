from sqlalchemy import Column, BigInteger, String, Text, DateTime, Integer
from sqlalchemy.sql import func

from app.core.database import Base


class Project(Base):
    """项目 — 平台级工作空间，v1 用于同步任务分组，未来可扩展到 workflow/component"""

    __tablename__ = "project"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, unique=True, comment="项目名称")
    code = Column(String(64), nullable=False, unique=True, comment="项目编码 — 用于 DS 工作流命名前缀")
    description = Column(Text, comment="项目描述")
    color = Column(String(16), default="#2B5AED", comment="项目主题色 — 系统按 id 分配 8 色调色板")
    status = Column(Integer, default=1, comment="1=启用 0=禁用")
    is_default = Column(Integer, default=0, comment="1=系统默认未分组项目，不可删")
    owner_id = Column(BigInteger, comment="负责人 user_id")
    created_by = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
