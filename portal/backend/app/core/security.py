from datetime import datetime, timedelta, timezone
from typing import Optional

import hashlib
import time

import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import SysUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_scheme = HTTPBearer(auto_error=False)

_COOKIE_NAME = "access_token"

# Token 黑名单（内存 + Redis）
# 使用 dict 存储 {token_hash: exp_timestamp}，定期清理过期的条目
_token_blacklist: dict[str, float] = {}


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()[:32]


def _cleanup_expired_tokens() -> None:
    """清理内存中已过期的 token 黑名单条目"""
    now = time.time()
    expired = [h for h, exp in _token_blacklist.items() if exp < now]
    for h in expired:
        _token_blacklist.pop(h, None)


def add_to_blacklist(token: str) -> None:
    """将 token 加入黑名单；利用 token 自身的 exp 作为 TTL"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )
        exp = payload.get("exp", time.time() + 3600)
    except Exception:
        exp = time.time() + 3600
    ttl = max(1, int(exp - time.time()))
    h = _token_hash(token)
    _token_blacklist[h] = exp
    # 定期清理过期条目（每 100 次写入触发一次）
    if len(_token_blacklist) % 100 == 0:
        _cleanup_expired_tokens()
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        r.setex(f"token_blacklist:{h}", ttl, "1")
    except Exception:
        pass


def is_token_blacklisted(token: str) -> bool:
    h = _token_hash(token)
    if h in _token_blacklist:
        if _token_blacklist[h] > time.time():
            return True
        # 已过期，清理
        _token_blacklist.pop(h, None)
        return False
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        return r.exists(f"token_blacklist:{h}") == 1
    except Exception:
        return False


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
):
    # 优先读 httponly cookie，其次读 Authorization header（兼容 API 客户端）
    token: Optional[str] = None
    cookie_token = request.cookies.get(_COOKIE_NAME)
    if cookie_token:
        token = cookie_token
    elif credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

    if is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证已失效")

    username = _decode_token(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证凭据")

    user = db.query(SysUser).filter(SysUser.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


def verify_service_token(token: str) -> bool:
    """校验服务间调用 token（DS SHELL 任务调用 Portal API 时使用）"""
    if not token:
        return False
    expected = getattr(settings, "DQC_SERVICE_TOKEN", "")
    if not expected:
        return False
    return token == expected


def get_service_user(db: Session) -> Optional[SysUser]:
    """获取系统服务用户（用于服务间调用的权限降级）"""
    # 优先查找名为 "system" 的用户，否则找第一个管理员
    user = db.query(SysUser).filter(SysUser.username == "system").first()
    if not user:
        user = db.query(SysUser).filter(SysUser.role == "admin").first()
    return user
