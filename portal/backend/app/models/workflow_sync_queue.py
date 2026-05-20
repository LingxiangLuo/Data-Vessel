"""工作流 DS 同步队列表 — outbox 模式"""
from sqlalchemy import Column, BigInteger, String, Integer, Text, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class WorkflowSyncQueue(Base):
    """工作流与 DS 同步的 outbox 队列

    Portal 不再直接调用 DS API，而是将操作写入本表，
    由后台调度器异步消费、重试，解耦 DS 强依赖。
    """
    __tablename__ = "workflow_sync_queue"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    workflow_id = Column(BigInteger, nullable=False, index=True)
    action = Column(String(32), nullable=False)  # publish / online / offline / delete
    status = Column(String(32), default="pending", nullable=False)  # pending / processing / success / failed
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime)
