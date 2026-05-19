"""数据源密码加密工具 — Fernet (AES-128-CBC + HMAC)"""
import base64
import hashlib

import logging

from cryptography.fernet import Fernet

from app.core.config import settings

logger = logging.getLogger(__name__)

_fernet: Fernet | None = None


def _get_fernet() -> Fernet | None:
    global _fernet
    if _fernet is not None:
        return _fernet
    key = settings.SECRET_KEY
    if not key:
        return None
    # Fernet 需要 32 字节 base64 编码的密钥
    digest = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(digest)
    _fernet = Fernet(fernet_key)
    return _fernet


def encrypt_password(plain: str | None) -> str | None:
    """加密明文密码；无密钥或明文为空时原样返回"""
    if not plain:
        return plain
    f = _get_fernet()
    if not f:
        return plain
    return f.encrypt(plain.encode()).decode()


def decrypt_password(cipher: str | None) -> str | None:
    """解密密码；无密钥或密文为空时原样返回"""
    if not cipher:
        return cipher
    f = _get_fernet()
    if not f:
        return cipher
    try:
        return f.decrypt(cipher.encode()).decode()
    except Exception as exc:
        # 如果解密失败，说明可能是未加密的旧数据，直接返回
        logger.warning("Password decryption failed (likely legacy plaintext): %s", exc)
        return cipher
