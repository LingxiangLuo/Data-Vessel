from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class SysNotifyChannel(Base):
    __tablename__ = "sys_notify_channel"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    type = Column(String(32), nullable=False)  # email / feishu_webhook / dingtalk_webhook / wecom_webhook
    config = Column(JSON, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
