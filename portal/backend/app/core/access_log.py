"""Access Log 中间件 — 记录所有 HTTP 请求的访问日志"""

import time
import logging
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.request_id import get_request_id

logger = logging.getLogger("access")


class AccessLogMiddleware(BaseHTTPMiddleware):
    """记录每个 HTTP 请求的访问信息：
    method, path, status_code, duration_ms, client_ip, user_agent, request_id
    """

    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = None
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            duration_ms = int((time.monotonic() - start) * 1000)
            client_ip = (
                request.headers.get("X-Forwarded-For", "")
                .split(",")[0]
                .strip()
                or request.client.host
                if request.client
                else "-"
            )
            req_id = response.headers.get("X-Request-ID") if response else (get_request_id() or "-")
            logger.info(
                "%(method)s %(path)s %(status)d %(duration)dms %(ip)s %(ua)s req=%(request_id)s",
                {
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "duration": duration_ms,
                    "ip": client_ip,
                    "ua": request.headers.get("User-Agent", "-"),
                    "request_id": req_id,
                },
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                    "user_agent": request.headers.get("User-Agent", "-"),
                    "request_id": req_id,
                },
            )
        return response
