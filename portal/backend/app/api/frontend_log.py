"""前端错误上报接口"""
import logging
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/log", tags=["日志"])

logger = logging.getLogger("frontend")


class FrontendLogEntry(BaseModel):
    level: str = Field(default="error", pattern=r"^(error|warn|info)$")
    message: str
    stack: Optional[str] = None
    url: Optional[str] = None
    user_agent: Optional[str] = None
    source: Optional[str] = None  # vue-runtime / axios / manual


@router.post("/frontend")
async def log_frontend(
    entry: FrontendLogEntry,
    request: Request,
):
    """接收前端上报的错误/警告/信息日志"""
    extra = {
        "client_ip": request.client.host if request.client else "-",
        "user_agent": entry.user_agent or request.headers.get("User-Agent", "-"),
        "url": entry.url,
        "source": entry.source or "unknown",
    }
    msg = f"[Frontend {entry.source or 'unknown'}] {entry.message}"
    if entry.stack:
        msg += f"\nStack: {entry.stack}"

    if entry.level == "error":
        logger.error(msg, extra=extra)
    elif entry.level == "warn":
        logger.warning(msg, extra=extra)
    else:
        logger.info(msg, extra=extra)

    return {"status": "ok"}
