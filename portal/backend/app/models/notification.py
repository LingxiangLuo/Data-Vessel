from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notification"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type = Column(String(16), nullable=False, default="info")  # alert / info
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    source = Column(String(32), nullable=False, default="ds")  # ds / portal
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
