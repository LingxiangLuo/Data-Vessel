"""Request ID 中间件：为每个 HTTP 请求生成唯一追踪 ID，注入日志和响应头。"""

import contextvars
import uuid
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# 线程安全的 request_id 存储（支持 async 上下文）
_request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)


def get_request_id() -> Optional[str]:
    """获取当前上下文的 request_id。"""
    return _request_id_ctx.get()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    为每个请求生成 UUID，并：
    1. 注入日志上下文（所有该请求内的日志自动带 request_id）
    2. 在响应头中返回 X-Request-ID（便于客户端关联）
    3. 优先读取客户端传入的 X-Request-ID（支持链路追踪透传）
    """

    async def dispatch(self, request: Request, call_next):
        # 优先使用客户端传入的 request_id（支持链路透传）
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = _request_id_ctx.set(req_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            _request_id_ctx.reset(token)
