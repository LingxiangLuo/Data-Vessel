from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class SysOAuthConfig(Base):
    __tablename__ = "sys_oauth_config"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    provider = Column(String(32), unique=True, nullable=False)  # dingtalk / feishu / wecom
    app_id = Column(String(128), nullable=True)
    app_secret = Column(String(255), nullable=True)
    redirect_uri = Column(String(512), nullable=True)
    enabled = Column(Boolean, default=False, nullable=False)
    extra_config = Column(JSON, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
