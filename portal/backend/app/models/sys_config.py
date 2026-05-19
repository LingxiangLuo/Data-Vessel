from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class SysConfig(Base):
    __tablename__ = "sys_config"

    key = Column(String(128), primary_key=True)
    value = Column(JSON, nullable=True)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
