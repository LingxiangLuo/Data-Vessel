"""系统健康检查 — 返回各服务的真实运行状态

替代 Monitor.vue 中硬编码的服务列表
"""
import asyncio
import socket
from typing import Dict, Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.ds_client import get_ds_client
from app.core.permissions import require_permission

router = APIRouter(prefix="/system", tags=["系统监控"])


def _tcp_alive(host: str, port: int, timeout: float = 1.5) -> bool:
    """TCP 端口探测,只能确认监听存在"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _redis_ping(host: str = "redis", port: int = 6379, timeout: float = 1.5) -> bool:
    """直接走 Redis 协议 PING — 已认证返回 +PONG;未认证返回 -NOAUTH,两者都说明进程存活"""
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.sendall(b"*1\r\n$4\r\nPING\r\n")
            data = sock.recv(64)
            return data.startswith(b"+PONG") or data.startswith(b"-NOAUTH")
    except OSError:
        return False


def _check_mysql(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@router.get("/services")
async def list_services(
    db: Session = Depends(get_db),
    _=Depends(require_permission("monitor:read")),
) -> Dict[str, Any]:
    """实时服务健康状态。MVP 架构 OpenMetadata 已废弃,不再上报"""
    mysql_ok = _check_mysql(db)
    redis_ok = _redis_ping()
    ds = get_ds_client()
    ds_ok = await ds.healthy()
    # Nginx 监听 80,从 Portal 容器内网视角探测
    nginx_ok = _tcp_alive("nginx", 80) or _tcp_alive("dmp-nginx", 80)

    services: List[Dict[str, Any]] = [
        {
            "key": "nginx",
            "name": "Nginx 网关",
            "desc": "反向代理 · 唯一对公网端口",
            "port": 80,
            "online": nginx_ok,
        },
        {
            "key": "portal-frontend",
            "name": "Portal 前端",
            "desc": "Vue3 + Arco Design",
            "port": 80,
            "online": nginx_ok,  # 前端走 nginx
        },
        {
            "key": "portal-backend",
            "name": "Portal 后端",
            "desc": "FastAPI · 容器内网",
            "port": 8000,
            "online": True,  # 此请求能响应即在线
        },
        {
            "key": "dolphinscheduler",
            "name": "DolphinScheduler",
            "desc": "工作流调度引擎 · 容器内网无 UI",
            "port": 12345,
            "online": ds_ok,
        },
        {
            "key": "mysql",
            "name": "MySQL",
            "desc": "元数据库",
            "port": 3306,
            "online": mysql_ok,
        },
        {
            "key": "redis",
            "name": "Redis",
            "desc": "缓存服务",
            "port": 6379,
            "online": redis_ok,
        },
    ]
    return {"services": services}


@router.get("/info")
async def system_info(_=Depends(require_permission("monitor:read"))) -> Dict[str, Any]:
    """动态系统信息 — 替代前端硬编码"""
    import os
    import platform
    import shutil

    cpu_count = os.cpu_count() or 0

    # 内存信息
    mem_total = 0
    mem_available = 0
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1]) * 1024
                elif line.startswith("MemAvailable:"):
                    mem_available = int(line.split()[1]) * 1024
    except Exception:
        pass

    # 磁盘
    disk_total = 0
    disk_used = 0
    try:
        usage = shutil.disk_usage("/")
        disk_total = usage.total
        disk_used = usage.used
    except Exception:
        pass

    # 系统运行时间
    uptime_seconds = 0
    try:
        with open("/proc/uptime") as f:
            uptime_seconds = int(float(f.read().split()[0]))
    except Exception:
        pass

    def fmt_bytes(b: int) -> str:
        if b >= 1024**3:
            return f"{b / 1024**3:.1f} GB"
        return f"{b / 1024**2:.0f} MB"

    def fmt_uptime(s: int) -> str:
        days = s // 86400
        hours = (s % 86400) // 3600
        if days > 0:
            return f"{days}d {hours}h"
        return f"{hours}h {(s % 3600) // 60}m"

    return {
        "os": platform.system() + " " + platform.release(),
        "platform": platform.platform(),
        "cpu_count": cpu_count,
        "memory_total": fmt_bytes(mem_total),
        "memory_available": fmt_bytes(mem_available),
        "memory_usage_pct": round((mem_total - mem_available) / mem_total * 100, 1) if mem_total else 0,
        "disk_total": fmt_bytes(disk_total),
        "disk_used": fmt_bytes(disk_used),
        "disk_usage_pct": round(disk_used / disk_total * 100, 1) if disk_total else 0,
        "uptime": fmt_uptime(uptime_seconds),
        "deploy_mode": "Docker Compose",
        "public_port": 80,
    }
