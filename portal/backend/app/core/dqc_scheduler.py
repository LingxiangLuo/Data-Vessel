"""DQC 报告定时任务调度器

使用 APScheduler 在后台运行，每日/每周自动生成并发送质量报告。
"""
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import sessionmaker

from app.core.database import engine
from app.core.dqc_report_generator import generate_report
from app.models.dqc_report import DqcReport, DqcReportHistory

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None

SessionLocal = sessionmaker(bind=engine)


def _send_report(report_id: int, data: dict):
    """发送报告给订阅者（预留接口，当前仅记录日志）。"""
    logger.info(f"[DQC Report #{report_id}] 报告生成完成: {data['summary']}")
    # TODO: 集成飞书/钉钉/邮件通知


def _run_report_job(report_id: int):
    """执行单个报告的生成和发送。"""
    db = SessionLocal()
    try:
        report = db.query(DqcReport).filter(DqcReport.id == report_id, DqcReport.enabled == True).first()
        if not report:
            return

        now = datetime.now()
        data = generate_report(db, rule_ids=report.rule_ids, period_type=report.period_type, period_end=now)

        # 保存历史记录
        from datetime import timedelta
        period_start = now - timedelta(days=7 if report.period_type == "weekly" else 1)
        history = DqcReportHistory(
            report_id=report.id,
            period_start=period_start,
            period_end=now,
            content_json=data,
            status="success",
        )
        db.add(history)

        # 更新最后发送时间
        report.last_sent_at = now
        db.commit()

        _send_report(report.id, data)
    except Exception as e:
        logger.exception(f"[DQC Report #{report_id}] 报告生成失败")
        try:
            history = DqcReportHistory(
                report_id=report_id,
                period_start=now,
                period_end=now,
                status="failed",
                error_msg=str(e),
            )
            db.add(history)
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


def start_scheduler():
    """启动 DQC 报告定时调度器。"""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return

    _scheduler = BackgroundScheduler()

    # 每日 09:00 执行 daily 报告
    _scheduler.add_job(
        _run_all_reports,
        trigger=CronTrigger(hour=9, minute=0),
        id="dqc_daily_reports",
        replace_existing=True,
    )

    # 每周一 09:00 执行 weekly 报告
    _scheduler.add_job(
        _run_all_reports,
        trigger=CronTrigger(day_of_week="mon", hour=9, minute=30),
        id="dqc_weekly_reports",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("[DQC Scheduler] 报告定时调度器已启动")


def _run_all_reports():
    """执行所有启用的报告。"""
    db = SessionLocal()
    try:
        reports = db.query(DqcReport).filter(DqcReport.enabled == True).all()
        for report in reports:
            _run_report_job(report.id)
    finally:
        db.close()


def shutdown_scheduler():
    """关闭调度器。"""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()
        logger.info("[DQC Scheduler] 报告定时调度器已关闭")
