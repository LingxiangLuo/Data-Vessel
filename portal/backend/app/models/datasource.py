from sqlalchemy import Column, BigInteger, String, Integer, Text, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class DataSource(Base):
    __tablename__ = "data_source"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    type = Column(String(32), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    database_name = Column(String(128), nullable=False)
    username = Column(String(128))
    password = Column(String(255))
    description = Column(Text)
    status = Column(Integer, default=1)
    last_check_time = Column(DateTime)
    created_by = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
