"""数据质量报告生成器

汇总指定周期内的规则执行情况，生成结构化报告数据。
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.dqc_rule import DqcRule
from app.models.dqc_check import DqcCheck
from app.models.datasource import DataSource


def generate_report(
    db: Session,
    rule_ids: Optional[List[int]] = None,
    period_type: str = "daily",
    period_end: Optional[datetime] = None,
) -> Dict[str, Any]:
    """生成质量报告数据。

    Args:
        db: 数据库会话
        rule_ids: 指定规则 ID 列表，None 表示全部规则
        period_type: daily / weekly
        period_end: 周期结束时间，默认当前时间

    Returns:
        {
            "period": {"type": str, "start": str, "end": str},
            "summary": {"total_checks": int, "passed": int, "failed": int, "pass_rate": float},
            "rule_stats": [{"rule_id": int, "name": str, "checks": int, "failed": int, "fail_rate": float}],
            "top_failed_rules": [{"rule_id": int, "name": str, "datasource_name": str, "fail_count": int}],
            "coverage": {"total_rules": int, "checked_rules": int, "coverage_rate": float},
        }
    """
    now = period_end or datetime.now()
    if period_type == "weekly":
        start = now - timedelta(days=7)
    else:
        start = now - timedelta(days=1)

    # 查询范围内的检查记录
    q = db.query(DqcCheck).filter(DqcCheck.checked_at >= start, DqcCheck.checked_at <= now)
    if rule_ids:
        q = q.filter(DqcCheck.rule_id.in_(rule_ids))
    checks = q.all()

    total = len(checks)
    passed = sum(1 for c in checks if c.passed)
    failed = total - passed
    pass_rate = round(passed / total * 100, 2) if total > 0 else 0.0

    # 按规则聚合
    rule_stats_map: Dict[int, Dict[str, Any]] = {}
    for c in checks:
        rid = c.rule_id
        if rid not in rule_stats_map:
            rule_stats_map[rid] = {"rule_id": rid, "checks": 0, "failed": 0}
        rule_stats_map[rid]["checks"] += 1
        if not c.passed:
            rule_stats_map[rid]["failed"] += 1

    # 补充规则名称和数据源
    all_rule_ids = list(rule_stats_map.keys())
    rules = db.query(DqcRule).filter(DqcRule.id.in_(all_rule_ids)).all() if all_rule_ids else []
    rule_map = {r.id: r for r in rules}
    ds_ids = list({r.datasource_id for r in rules if r.datasource_id})
    ds_map = {}
    if ds_ids:
        ds_map = {d.id: d for d in db.query(DataSource).filter(DataSource.id.in_(ds_ids)).all()}

    rule_stats = []
    for rid, stat in rule_stats_map.items():
        r = rule_map.get(rid)
        name = r.name if r else f"规则 #{rid}"
        stat["name"] = name
        stat["fail_rate"] = round(stat["failed"] / stat["checks"] * 100, 2) if stat["checks"] > 0 else 0.0
        rule_stats.append(stat)

    # TOP 失败规则（按失败次数降序）
    top_failed = sorted(
        [s for s in rule_stats if s["failed"] > 0],
        key=lambda x: x["failed"],
        reverse=True,
    )[:5]
    top_failed_enriched = []
    for s in top_failed:
        r = rule_map.get(s["rule_id"])
        ds_name = ds_map.get(r.datasource_id).name if r and r.datasource_id in ds_map else "-"
        top_failed_enriched.append({
            "rule_id": s["rule_id"],
            "name": s["name"],
            "datasource_name": ds_name,
            "fail_count": s["failed"],
        })

    # 覆盖率：已检查规则 / 总规则
    total_rules_q = db.query(DqcRule).filter(DqcRule.enabled == True)
    if rule_ids:
        total_rules_q = total_rules_q.filter(DqcRule.id.in_(rule_ids))
    total_rules = total_rules_q.count()
    checked_rules = len(rule_stats_map)
    coverage_rate = round(checked_rules / total_rules * 100, 2) if total_rules > 0 else 0.0

    return {
        "period": {
            "type": period_type,
            "start": start.strftime("%Y-%m-%d %H:%M:%S"),
            "end": now.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "summary": {
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
        },
        "rule_stats": rule_stats,
        "top_failed_rules": top_failed_enriched,
        "coverage": {
            "total_rules": total_rules,
            "checked_rules": checked_rules,
            "coverage_rate": coverage_rate,
        },
    }
