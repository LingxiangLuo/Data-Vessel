from sqlalchemy import Column, BigInteger, String, Integer, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class SysUser(Base):
    __tablename__ = "sys_user"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    real_name = Column(String(64))
    email = Column(String(128))
    phone = Column(String(20))
    role = Column(String(32), default="user")
    status = Column(Integer, default=1)
    avatar = Column(String(512), nullable=True)
    dept_id = Column(BigInteger, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    oauth_provider = Column(String(32), nullable=True)   # dingtalk / feishu / wecom
    oauth_openid = Column(String(128), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
