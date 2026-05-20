"""工作流 DS 同步 outbox 调度器

消费 workflow_sync_queue 表，异步执行 DS 同步操作，失败自动重试。
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.ds_client import get_ds_client
from app.models.workflow_sync_queue import WorkflowSyncQueue
from app.models.workflow import Workflow

logger = logging.getLogger(__name__)

scheduler: Optional[AsyncIOScheduler] = None


def _to_6_field_cron(cron_expr: str) -> str:
    """将 5 段 cron 补全为 6 段（DS 要求含秒字段）。"""
    parts = cron_expr.strip().split()
    if len(parts) == 5:
        return "0 " + " ".join(parts)
    return " ".join(parts)


async def _do_publish(db: Session, record: WorkflowSyncQueue) -> None:
    """执行工作流发布：创建/更新 PD + 上线，成功后清理旧资源"""
    from app.services.publisher import WorkflowPublisher

    workflow = db.query(Workflow).filter(Workflow.id == record.workflow_id).first()
    if not workflow:
        raise ValueError(f"Workflow {record.workflow_id} not found")

    ds = get_ds_client()
    old_schedule_id = workflow.ds_schedule_id
    old_pd_code = workflow.ds_process_code

    publisher = WorkflowPublisher(db)
    pd_code, schedule_id = await publisher.publish(workflow)
    if not pd_code:
        raise RuntimeError("DS publish failed: no process code returned")

    workflow.ds_process_code = pd_code
    if schedule_id:
        workflow.ds_schedule_id = schedule_id

    await publisher.online(pd_code)

    workflow.status = "online"
    workflow.schedule_status = "ONLINE"
    db.commit()

    # 发布成功后再清理旧资源（此时失败只记 warning，不影响结果）
    if old_schedule_id and old_schedule_id != schedule_id:
        try:
            await ds.schedule_offline(old_schedule_id)
            await ds.delete_schedule(old_schedule_id)
        except Exception as e:
            logger.warning("Cleanup old schedule %s failed: %s", old_schedule_id, e)
    if old_pd_code and old_pd_code != pd_code:
        try:
            await ds.delete_process_definition(old_pd_code)
        except Exception as e:
            logger.warning("Cleanup old PD %s failed: %s", old_pd_code, e)


async def _do_online(db: Session, record: WorkflowSyncQueue) -> None:
    """执行调度上线：创建 schedule（如需）+ online schedule"""
    workflow = db.query(Workflow).filter(Workflow.id == record.workflow_id).first()
    if not workflow:
        raise ValueError(f"Workflow {record.workflow_id} not found")
    if not workflow.cron_expression:
        raise ValueError("Workflow has no cron expression")
    if not workflow.ds_process_code:
        raise ValueError("Workflow has no ds_process_code")

    ds = get_ds_client()

    # 没有 schedule 则先创建
    if not workflow.ds_schedule_id:
        schedule_id = await ds.create_schedule(
            workflow.ds_process_code, _to_6_field_cron(workflow.cron_expression)
        )
        if not schedule_id:
            raise RuntimeError("DS create schedule failed")
        workflow.ds_schedule_id = schedule_id
        db.flush()  # 持久化 ds_schedule_id，避免 retry 时重复创建

    ok = await ds.schedule_online(workflow.ds_schedule_id)
    if not ok:
        raise RuntimeError("DS schedule online failed")

    workflow.schedule_status = "ONLINE"
    db.commit()


async def _do_offline(db: Session, record: WorkflowSyncQueue) -> None:
    """执行工作流下线（schedule + process definition）"""
    workflow = db.query(Workflow).filter(Workflow.id == record.workflow_id).first()
    if not workflow:
        raise ValueError(f"Workflow {record.workflow_id} not found")

    ds = get_ds_client()
    if workflow.ds_schedule_id:
        try:
            await ds.schedule_offline(workflow.ds_schedule_id)
        except Exception as e:
            logger.warning("Schedule offline failed (may be already offline): %s", e)

    if workflow.ds_process_code:
        try:
            await ds.release_process_definition(workflow.ds_process_code, online=False)
        except Exception as e:
            logger.warning("PD release offline failed (may be already offline): %s", e)

    workflow.status = "offline"
    workflow.schedule_status = "OFFLINE"
    db.commit()


async def _do_release_schedule(db: Session, record: WorkflowSyncQueue) -> None:
    """仅下线 schedule，不修改 workflow.status（schedule_offline 专用）"""
    workflow = db.query(Workflow).filter(Workflow.id == record.workflow_id).first()
    if not workflow:
        raise ValueError(f"Workflow {record.workflow_id} not found")

    ds = get_ds_client()
    if workflow.ds_schedule_id:
        try:
            await ds.schedule_offline(workflow.ds_schedule_id)
        except Exception as e:
            logger.warning("Schedule offline failed (may be already offline): %s", e)

    workflow.schedule_status = "OFFLINE"
    db.commit()


async def _do_delete(db: Session, record: WorkflowSyncQueue) -> None:
    """执行 DS 侧清理"""
    workflow = db.query(Workflow).filter(Workflow.id == record.workflow_id).first()
    if not workflow:
        return  # 已删除，无需清理

    ds = get_ds_client()
    if workflow.ds_schedule_id:
        try:
            await ds.schedule_offline(workflow.ds_schedule_id)
            await ds.delete_schedule(workflow.ds_schedule_id)
        except Exception as e:
            logger.warning("DS schedule cleanup failed: %s", e)

    if workflow.ds_process_code:
        try:
            await ds.delete_process_definition(workflow.ds_process_code)
        except Exception as e:
            logger.warning("DS process def cleanup failed: %s", e)


_ACTION_HANDLERS = {
    "publish": _do_publish,
    "online": _do_online,
    "offline": _do_offline,
    "release_schedule": _do_release_schedule,
    "delete": _do_delete,
}


async def _consume_queue() -> None:
    """消费 outbox 队列"""
    db = SessionLocal()
    try:
        # 恢复超时的 processing 记录（进程崩溃后遗留）
        stale_cutoff = datetime.now() - timedelta(minutes=5)
        db.query(WorkflowSyncQueue).filter(
            WorkflowSyncQueue.status == "processing",
            WorkflowSyncQueue.updated_at < stale_cutoff,
        ).update({"status": "pending"}, synchronize_session=False)
        db.commit()

        # 获取待处理记录（按 updated_at 排序，避免高退避记录占满批次）
        records = (
            db.query(WorkflowSyncQueue)
            .filter(
                WorkflowSyncQueue.status.in_(["pending", "failed"]),
                WorkflowSyncQueue.retry_count < WorkflowSyncQueue.max_retries,
            )
            .order_by(WorkflowSyncQueue.updated_at)
            .limit(10)
            .all()
        )

        for record in records:
            # 指数退避：2^retry_count 分钟
            backoff_minutes = 2 ** record.retry_count
            if record.updated_at and (datetime.now() - record.updated_at) < timedelta(minutes=backoff_minutes):
                continue

            record.status = "processing"
            db.commit()

            handler = _ACTION_HANDLERS.get(record.action)
            if not handler:
                record.status = "failed"
                record.retry_count = record.max_retries  # 防止无限循环
                record.error_message = f"Unknown action: {record.action}"
                db.commit()
                continue

            try:
                await handler(db, record)
                record.status = "success"
                record.completed_at = datetime.now()
                record.error_message = None
                db.commit()
                logger.info("Workflow sync %s %s succeeded", record.action, record.workflow_id)
            except Exception as e:
                db.rollback()
                record.retry_count += 1
                exhausted = record.retry_count >= record.max_retries
                record.status = "failed" if exhausted else "pending"
                record.error_message = str(e)[:500]
                # publish 乐观更新了 online，失败时回写 tested
                if exhausted and record.action == "publish":
                    wf = db.query(Workflow).filter(Workflow.id == record.workflow_id).first()
                    if wf and wf.status == "online":
                        wf.status = "tested"
                        wf.schedule_status = "OFFLINE"
                db.commit()
                if exhausted:
                    logger.error(
                        "Workflow sync %s %s FAILED PERMANENTLY after %d retries: %s",
                        record.action, record.workflow_id, record.max_retries, e
                    )
                else:
                    logger.warning(
                        "Workflow sync %s %s failed (retry %d/%d): %s",
                        record.action, record.workflow_id, record.retry_count, record.max_retries, e
                    )
    except Exception:
        db.rollback()
        logger.exception("Workflow sync queue consumer error")
    finally:
        db.close()


def start_sync_scheduler():
    global scheduler
    if scheduler is not None:
        return
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _consume_queue,
        trigger=IntervalTrigger(seconds=10),
        id="workflow_sync_consumer",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Workflow sync scheduler started")


def shutdown_sync_scheduler():
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("Workflow sync scheduler shutdown")
