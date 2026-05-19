from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class SysResourceAccess(Base):
    __tablename__ = "sys_resource_access"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    resource_type = Column(String(64), nullable=False)   # workflow / datasource / component
    resource_id = Column(BigInteger, nullable=False)
    subject_type = Column(String(16), nullable=False)    # user / role
    subject_id = Column(BigInteger, nullable=False)
    permission = Column(String(16), nullable=False)      # read / write / admin
    granted_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
