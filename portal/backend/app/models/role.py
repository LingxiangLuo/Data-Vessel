from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.core.database import Base


class SysRole(Base):
    __tablename__ = "sys_role"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(64), nullable=False)
    description = Column(String(255), nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class SysPermission(Base):
    __tablename__ = "sys_permission"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(128), unique=True, nullable=False)
    name = Column(String(64), nullable=False)
    resource_type = Column(String(64), nullable=True)
    action = Column(String(32), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class SysRolePermission(Base):
    __tablename__ = "sys_role_permission"

    role_id = Column(BigInteger, ForeignKey("sys_role.id"), primary_key=True)
    permission_id = Column(BigInteger, ForeignKey("sys_permission.id"), primary_key=True)


class SysUserRole(Base):
    __tablename__ = "sys_user_role"

    user_id = Column(BigInteger, ForeignKey("sys_user.id"), primary_key=True)
    role_id = Column(BigInteger, ForeignKey("sys_role.id"), primary_key=True)
    granted_by = Column(BigInteger, nullable=True)
    granted_at = Column(DateTime, server_default=func.now())
