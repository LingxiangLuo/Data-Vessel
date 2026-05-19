from sqlalchemy import Column, BigInteger, String, Integer, Text, DateTime, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class ComponentHistory(Base):
    """组件历史版本快照"""
    __tablename__ = "component_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    component_id = Column(BigInteger, nullable=False, index=True, comment="关联组件 ID")
    version = Column(Integer, nullable=False, comment="快照时的版本号")
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    description = Column(Text)
    config_json = Column(JSON, nullable=False, default=dict)
    params = Column(JSON, default=list)
    status = Column(String(50), nullable=False)
    created_by = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())
    comment = Column(String(255), comment="版本备注")


class Component(Base):
    """统一组件模型 — sql / python / shell / datax"""
    __tablename__ = "component"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # sql / python / shell / datax
    description = Column(Text)
    # 配置 JSON,按 type 不同含义不同:
    #   sql:    { datasource_id, sql, timeout }
    #   python: { script, timeout }
    #   shell:  { script, timeout }
    #   datax:  { reader, writer, source_id, target_id, ... }
    config_json = Column(JSON, nullable=False, default=dict)
    # 参数定义 [{"key": "dt", "value": "${bizdate}", "desc": "业务日期"}]
    params = Column(JSON, default=list)
    version = Column(Integer, default=1, nullable=False)
    # 状态机: draft -> tested -> online -> offline
    status = Column(String(50), default="draft", nullable=False)
    # 发布后映射到 DS Task code (Phase 5+ 填入)
    ds_task_code = Column(BigInteger)
    folder_id = Column(BigInteger, comment="所属文件夹 id")
    sort_order = Column(Integer, default=0, nullable=False, comment="同文件夹内排序")
    previous_status = Column(String(50), comment="暂停前的状态")
    dqc_rule_ids = Column(JSON, nullable=True, comment="关联的数据质量规则 ID 列表")
    created_by = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
