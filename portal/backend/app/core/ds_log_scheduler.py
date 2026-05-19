"""DS 日志后台调度器

职责：
- 每 5s 拉取 RUNNING 任务增量日志
- 每 60s 归档已完成任务
- 解析日志级别和 DataX 统计
"""
import asyncio
import os
import re
import gzip
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.core.ds_client import get_ds_client
from app.core.database import SessionLocal
from app.models.ds_task_log import DSTaskLog

logger = logging.getLogger("ds_log")

# 存储路径配置
_LOG_BASE_PATH = os.environ.get("DS_LOG_STORAGE_PATH", "/app/logs/ds")
_LOG_RETENTION_DAYS = int(os.environ.get("DS_LOG_RETENTION_DAYS", "90"))

scheduler: Optional[AsyncIOScheduler] = None

# 日志级别正则
_LOG_LEVEL_RE = re.compile(r"\[(INFO|WARN|ERROR|DEBUG)\]|\b(INFO|WARN|ERROR|DEBUG)\b", re.IGNORECASE)

# DataX 统计正则
_DATAX_STATS_RE = re.compile(
    r"Read\s+(\d+)\s+records,\s+Write\s+(\d+)\s+records|"
    r"Total\s+(\d+)\s+records,\s+Speed\s+([\d.]+)\s+(\w+/s)|"
    r"Error\s+record\(s\):\s+(\d+)",
    re.IGNORECASE,
)


def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _log_file_path(task_instance_id: int, dt: datetime = None) -> str:
    """生成日志文件路径: /app/logs/ds/{year}/{month}/{day}/{task_instance_id}.log"""
    dt = dt or datetime.now()
    return os.path.join(
        _LOG_BASE_PATH,
        str(dt.year),
        f"{dt.month:02d}",
        f"{dt.day:02d}",
        f"{task_instance_id}.log",
    )


def _parse_log_line(line: str) -> str:
    """解析单行日志的级别，返回小写级别名"""
    m = _LOG_LEVEL_RE.search(line)
    if m:
        return (m.group(1) or m.group(2)).upper()
    return "INFO"


def _parse_datax_stats(lines: List[str]) -> Optional[Dict[str, Any]]:
    """从 DataX 日志中提取统计信息"""
    stats = {
        "read_records": 0,
        "write_records": 0,
        "speed": None,
        "speed_unit": None,
        "error_records": 0,
    }
    found = False
    for line in lines:
        m = _DATAX_STATS_RE.search(line)
        if m:
            found = True
            if m.group(1):
                stats["read_records"] = int(m.group(1))
            if m.group(2):
                stats["write_records"] = int(m.group(2))
            if m.group(3):
                stats["read_records"] = int(m.group(3))
            if m.group(4):
                stats["speed"] = float(m.group(4))
            if m.group(5):
                stats["speed_unit"] = m.group(5)
            if m.group(6):
                stats["error_records"] = int(m.group(6))
    return stats if found else None


def _append_log_file(path: str, content: str) -> int:
    """追加写入日志文件，返回写入的行数"""
    _ensure_dir(path)
    lines = content.splitlines()
    with open(path, "a", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
    return len(lines)


def _read_log_file(path: str, offset: int = 0, limit: int = 1000) -> List[str]:
    """读取日志文件，支持偏移和限制"""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    start = max(0, offset)
    end = min(len(lines), start + limit)
    return [line.rstrip("\n") for line in lines[start:end]]


def _search_log_file(path: str, keyword: str, context: int = 2) -> List[Dict[str, Any]]:
    """全文搜索日志文件，返回匹配行及前后上下文"""
    lines = _read_log_file(path, 0, 100000)
    results = []
    kw_lower = keyword.lower()
    matched_indices = [i for i, line in enumerate(lines) if kw_lower in line.lower()]
    for idx in matched_indices:
        start = max(0, idx - context)
        end = min(len(lines), idx + context + 1)
        results.append({
            "line_no": idx + 1,
            "lines": lines[start:end],
            "match_idx": idx - start,
        })
    return results


# ------------------------------------------------------------------
# 调度任务
# ------------------------------------------------------------------

async def _poll_running_logs():
    """每 5s 执行：拉取 RUNNING 任务的增量日志"""
    ds = get_ds_client()
    db = SessionLocal()
    try:
        # 查询 DS 中正在运行的流程实例
        instances = await ds.get_process_instances(state="RUNNING_EXECUTION", page_size=200)
        if not instances:
            return

        # 收集所有任务实例
        all_task_instances: List[Dict[str, Any]] = []
        for inst in instances:
            inst_id = inst.get("id")
            if not inst_id:
                continue
            tasks = await ds.get_task_instances(inst_id, page_size=200)
            for t in tasks:
                t["_process_instance_id"] = inst_id
            all_task_instances.extend(tasks)

        for task in all_task_instances:
            task_id = task.get("id")
            if not task_id:
                continue

            # 获取或创建 DSTaskLog 记录
            log_record = (
                db.query(DSTaskLog)
                .filter(DSTaskLog.task_instance_id == task_id)
                .first()
            )
            if not log_record:
                log_record = DSTaskLog(
                    task_instance_id=task_id,
                    process_instance_id=task.get("_process_instance_id"),
                    task_name=task.get("name", ""),
                    task_type=task.get("taskType", ""),
                    task_state=task.get("state"),
                    storage_path=_log_file_path(task_id),
                )
                db.add(log_record)
                db.flush()

            # 增量拉取日志
            skip_line = log_record.last_fetched_line or 0
            try:
                log_content = await ds.get_log_detail(task_id, skip_line=skip_line, limit=10000)
            except Exception as e:
                logger.warning("Fetch log for task %s failed: %s", task_id, e)
                continue

            if not log_content or log_content.strip() == "":
                continue

            # 写入文件
            lines_added = await asyncio.to_thread(_append_log_file, log_record.storage_path, log_content)
            if lines_added == 0:
                continue

            # 解析新增日志
            new_lines = log_content.splitlines()
            for line in new_lines:
                level = _parse_log_line(line)
                if level == "ERROR":
                    log_record.error_count += 1
                elif level == "WARN":
                    log_record.warn_count += 1
                elif level == "DEBUG":
                    log_record.debug_count += 1
                else:
                    log_record.info_count += 1

            log_record.total_lines += lines_added
            log_record.last_fetched_line = skip_line + lines_added
            log_record.updated_at = datetime.now()

            # 解析 DataX 统计（仅 SHELL/DataX 类型）
            if log_record.task_type in ("SHELL", "DATAX"):
                stats = _parse_datax_stats(new_lines)
                if stats:
                    existing = log_record.summary_json or {}
                    existing.update(stats)
                    log_record.summary_json = existing

        db.commit()
    except Exception:
        db.rollback()
        logger.exception("DS log poll failed")
    finally:
        db.close()


async def _archive_completed_logs():
    """每 60s 执行：归档已完成任务，清理过期日志"""
    ds = get_ds_client()
    db = SessionLocal()
    try:
        # 查询未归档的 DSTaskLog
        active_logs = (
            db.query(DSTaskLog)
            .filter(DSTaskLog.is_archived == False)
            .all()
        )
        if not active_logs:
            return

        # 批量查询任务状态
        task_ids = [log.task_instance_id for log in active_logs]
        # DS 没有批量查询 task instance 状态的接口，逐个查询
        for log_record in active_logs:
            try:
                # 通过 process instance 列表反查状态
                # 简化：直接尝试再拉一次日志，如果任务已完成则标记归档
                # 更准确的做法是通过 DS API 查询 task instance 状态
                task_state = log_record.task_state or ""
                if task_state in ("SUCCESS", "FAILURE", "KILL", "STOP"):
                    log_record.is_archived = True
                    log_record.updated_at = datetime.now()
                    continue

                # 尝试从 DS 获取最新状态
                # 由于 DS API 限制，这里通过日志内容判断：
                # 如果连续两次拉取都为空且任务已运行较长时间，则标记归档
                last_update = log_record.updated_at or log_record.created_at
                if last_update and (datetime.now() - last_update).total_seconds() > 3600:
                    log_record.is_archived = True
                    log_record.updated_at = datetime.now()
            except Exception:
                logger.exception("Archive check failed for task %s", log_record.task_instance_id)

        db.commit()

        # 清理过期日志文件
        await asyncio.to_thread(_cleanup_old_logs)
    except Exception:
        db.rollback()
        logger.exception("DS log archive failed")
    finally:
        db.close()


def _cleanup_old_logs():
    """删除超过保留期的日志文件"""
    cutoff = datetime.now() - timedelta(days=_LOG_RETENTION_DAYS)
    if not os.path.exists(_LOG_BASE_PATH):
        return
    for root, _dirs, files in os.walk(_LOG_BASE_PATH):
        for fname in files:
            if not fname.endswith(".log"):
                continue
            fpath = os.path.join(root, fname)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                if mtime < cutoff:
                    # 30 天以上压缩为 .gz
                    age_days = (datetime.now() - mtime).days
                    if age_days > 30 and not fpath.endswith(".gz"):
                        gz_path = fpath + ".gz"
                        with open(fpath, "rb") as f_in:
                            with gzip.open(gz_path, "wb") as f_out:
                                f_out.writelines(f_in)
                        os.remove(fpath)
                    elif age_days > _LOG_RETENTION_DAYS:
                        os.remove(fpath)
                        gz_path = fpath + ".gz"
                        if os.path.exists(gz_path):
                            os.remove(gz_path)
            except Exception:
                logger.warning("Cleanup failed for %s", fpath)


# ------------------------------------------------------------------
# 生命周期管理
# ------------------------------------------------------------------

def start_log_scheduler():
    global scheduler
    if scheduler is not None:
        return
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _poll_running_logs,
        trigger=IntervalTrigger(seconds=5),
        id="ds_log_poll",
        replace_existing=True,
    )
    scheduler.add_job(
        _archive_completed_logs,
        trigger=IntervalTrigger(seconds=60),
        id="ds_log_archive",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("DS log scheduler started")


def shutdown_log_scheduler():
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("DS log scheduler shutdown")


# ------------------------------------------------------------------
# 对外工具函数（供 API 使用）
# ------------------------------------------------------------------

def get_log_lines(task_instance_id: int, offset: int = 0, limit: int = 1000) -> List[str]:
    """获取指定任务的日志行（同步，供 API 调用）"""
    db = SessionLocal()
    try:
        log_record = (
            db.query(DSTaskLog)
            .filter(DSTaskLog.task_instance_id == task_instance_id)
            .first()
        )
        if not log_record or not log_record.storage_path:
            return []
        path = log_record.storage_path
        # 检查是否存在 .gz 版本
        gz_path = path + ".gz"
        if os.path.exists(gz_path) and not os.path.exists(path):
            with gzip.open(gz_path, "rt", encoding="utf-8") as f:
                lines = f.readlines()
            start = max(0, offset)
            end = min(len(lines), start + limit)
            return [line.rstrip("\n") for line in lines[start:end]]
        return _read_log_file(path, offset, limit)
    finally:
        db.close()


def search_log_lines(task_instance_id: int, keyword: str) -> List[Dict[str, Any]]:
    """搜索指定任务的日志"""
    db = SessionLocal()
    try:
        log_record = (
            db.query(DSTaskLog)
            .filter(DSTaskLog.task_instance_id == task_instance_id)
            .first()
        )
        if not log_record or not log_record.storage_path:
            return []
        path = log_record.storage_path
        gz_path = path + ".gz"
        if os.path.exists(gz_path) and not os.path.exists(path):
            with gzip.open(gz_path, "rt", encoding="utf-8") as f:
                lines = [line.rstrip("\n") for line in f.readlines()]
            results = []
            kw_lower = keyword.lower()
            matched_indices = [i for i, line in enumerate(lines) if kw_lower in line.lower()]
            for idx in matched_indices:
                start = max(0, idx - 2)
                end = min(len(lines), idx + 3)
                results.append({
                    "line_no": idx + 1,
                    "lines": lines[start:end],
                    "match_idx": idx - start,
                })
            return results
        return _search_log_file(path, keyword)
    finally:
        db.close()


def get_log_stats(task_instance_id: int) -> Optional[Dict[str, Any]]:
    """获取日志统计信息"""
    db = SessionLocal()
    try:
        log_record = (
            db.query(DSTaskLog)
            .filter(DSTaskLog.task_instance_id == task_instance_id)
            .first()
        )
        if not log_record:
            return None
        return {
            "task_instance_id": log_record.task_instance_id,
            "task_name": log_record.task_name,
            "task_type": log_record.task_type,
            "task_state": log_record.task_state,
            "total_lines": log_record.total_lines,
            "error_count": log_record.error_count,
            "warn_count": log_record.warn_count,
            "info_count": log_record.info_count,
            "debug_count": log_record.debug_count,
            "summary": log_record.summary_json,
            "is_archived": log_record.is_archived,
            "updated_at": str(log_record.updated_at) if log_record.updated_at else None,
        }
    finally:
        db.close()
