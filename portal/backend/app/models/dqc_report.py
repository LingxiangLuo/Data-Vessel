"""数据质量报告模型"""
from sqlalchemy import Column, BigInteger, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class DqcReport(Base):
    """数据质量报告配置"""
    __tablename__ = "dqc_report"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    rule_ids = Column(JSON, nullable=True)  # null 表示全部规则
    period_type = Column(String(16), nullable=False, default="daily")  # daily / weekly
    subscribers = Column(JSON, nullable=True)  # [{"type": "user", "id": 1}, {"type": "email", "address": "a@b.com"}]
    enabled = Column(Boolean, default=True, nullable=False)
    last_sent_at = Column(DateTime, nullable=True)
    created_by = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DqcReportHistory(Base):
    """报告发送历史记录"""
    __tablename__ = "dqc_report_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    report_id = Column(BigInteger, ForeignKey("dqc_report.id", ondelete="CASCADE"), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    content_json = Column(JSON, nullable=True)  # 报告完整内容
    sent_at = Column(DateTime, server_default=func.now())
    status = Column(String(16), default="success")  # success / failed
    error_msg = Column(Text, nullable=True)
