"""DS 任务日志元数据模型"""
from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class DSTaskLog(Base):
    """DS 任务实例日志元数据

    日志内容存储在文件系统，本表仅保存元数据和解析后的统计信息。
    """
    __tablename__ = "ds_task_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_instance_id = Column(BigInteger, nullable=False, unique=True, index=True)
    process_instance_id = Column(BigInteger, nullable=False, index=True)
    task_name = Column(String(255), nullable=False)
    task_type = Column(String(50), nullable=False)  # SHELL / SQL / PYTHON / etc.
    task_state = Column(String(50), nullable=True)  # RUNNING / SUCCESS / FAILURE

    # 文件存储
    storage_path = Column(String(512), nullable=True, comment="日志文件路径")

    # 统计信息
    total_lines = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    warn_count = Column(Integer, default=0, nullable=False)
    info_count = Column(Integer, default=0, nullable=False)
    debug_count = Column(Integer, default=0, nullable=False)

    # 增量拉取偏移
    last_fetched_line = Column(Integer, default=0, nullable=False, comment="已拉取到最后行号")

    # DataX 结构化统计
    summary_json = Column(JSON, nullable=True, comment="DataX 统计等结构化数据")

    # 归档状态
    is_archived = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
