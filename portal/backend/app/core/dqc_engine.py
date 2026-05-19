"""数据质量检查执行引擎

根据规则类型生成校验 SQL，在目标数据源上执行，比较结果返回 passed/failed。
Phase 1 支持 MySQL / PostgreSQL / ClickHouse。
"""
import logging
from typing import Optional, Dict, Any, Tuple

from app.core.db_adapter import _connect
from app.models.datasource import DataSource

logger = logging.getLogger(__name__)


def _validate_custom_sql(sql: str) -> str:
    """校验 custom_sql：仅允许单条 SELECT，禁止 DML/DDL/注释绕过。
    返回清理后的 SQL（已移除注释）。"""
    import re

    # 1. 移除块注释 /* ... */
    cleaned = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    # 2. 移除行注释 -- ...
    lines = [line.split("--")[0] for line in cleaned.split("\n")]
    cleaned = " ".join(lines)
    # 3. 规范化空白
    cleaned = " ".join(cleaned.split())

    # 4. 仅允许单条语句（无分号）
    stripped = cleaned.rstrip(";").strip()
    if ";" in stripped:
        raise ValueError("custom_sql 只允许单条 SELECT 语句")

    # 5. 必须以 SELECT 开头
    upper = stripped.upper()
    if not upper.startswith("SELECT"):
        raise ValueError("custom_sql 只允许 SELECT 语句")

    # 6. 禁止关键字（整词匹配，防止子串误报）
    forbidden = (
        "DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE",
        "ALTER", "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE",
        "UNION", "INTO", "LOAD", "COPY",
    )
    for kw in forbidden:
        if re.search(rf"\b{kw}\b", upper):
            raise ValueError(f"custom_sql 包含非法关键字: {kw}")

    return stripped


# 规则类型 → 是否需要字段名
RULE_REQUIRES_COLUMN = {
    "row_count": False,
    "null_count": True,
    "null_percent": True,
    "distinct_count": True,
    "distinct_percent": True,
    "duplicate_count": True,
    "duplicate_percent": True,
    "min": True,
    "max": True,
    "avg": True,
    "sum": True,
    "custom_sql": False,
    "regex_match_percent": True,
    "length_check": True,
    "value_range": True,
}


def _quote_identifier(name: str, ds_type: str) -> str:
    """根据数据源类型引用标识符"""
    t = ds_type.lower()
    if t in ("mysql", "clickhouse", "hive"):
        return f"`{name}`"
    return f'"{name}"'


def _table_ref(table: str, ds_type: str) -> str:
    """处理 schema.table 格式"""
    parts = table.split(".")
    return ".".join(_quote_identifier(p, ds_type) for p in parts)


def generate_check_sql(
    rule_type: str,
    table: str,
    column: Optional[str],
    ds_type: str,
    extra_config: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Optional[Tuple]]:
    """生成校验 SQL，返回 (sql, params)。

    params 用于 regex_match_percent / value_range 等需要额外参数的场景。
    """
    t = ds_type.lower()
    tbl = _table_ref(table, ds_type)
    col = _quote_identifier(column, ds_type) if column else None
    extra = extra_config or {}

    if rule_type == "row_count":
        return f"SELECT COUNT(*) FROM {tbl}", None

    if rule_type == "null_count":
        return f"SELECT COUNT(*) FROM {tbl} WHERE {col} IS NULL", None

    if rule_type == "null_percent":
        if t == "clickhouse":
            sql = (
                f"SELECT if(COUNT(*) = 0, 0, 100.0 * countIf({col} IS NULL) / COUNT(*)) "
                f"FROM {tbl}"
            )
        else:
            sql = (
                f"SELECT COALESCE(100.0 * SUM(CASE WHEN {col} IS NULL THEN 1 ELSE 0 END) / COUNT(*), 0) "
                f"FROM {tbl}"
            )
        return sql, None

    if rule_type == "distinct_count":
        return f"SELECT COUNT(DISTINCT {col}) FROM {tbl}", None

    if rule_type == "distinct_percent":
        if t == "clickhouse":
            sql = (
                f"SELECT if(COUNT(*) = 0, 0, 100.0 * uniqExact({col}) / COUNT(*)) "
                f"FROM {tbl}"
            )
        else:
            sql = (
                f"SELECT COALESCE(100.0 * COUNT(DISTINCT {col}) / COUNT(*), 0) "
                f"FROM {tbl}"
            )
        return sql, None

    if rule_type == "duplicate_count":
        return f"SELECT COUNT(*) - COUNT(DISTINCT {col}) FROM {tbl}", None

    if rule_type == "duplicate_percent":
        if t == "clickhouse":
            sql = (
                f"SELECT if(COUNT(*) = 0, 0, 100.0 * (COUNT(*) - uniqExact({col})) / COUNT(*)) "
                f"FROM {tbl}"
            )
        else:
            sql = (
                f"SELECT COALESCE(100.0 * (COUNT(*) - COUNT(DISTINCT {col})) / COUNT(*), 0) "
                f"FROM {tbl}"
            )
        return sql, None

    if rule_type in ("min", "max", "avg", "sum"):
        return f"SELECT {rule_type.upper()}({col}) FROM {tbl}", None

    if rule_type == "custom_sql":
        raw = extra.get("custom_sql", "").strip()
        if not raw:
            raise ValueError("custom_sql 规则需要提供 extra_config.custom_sql")
        sql = _validate_custom_sql(raw)
        return sql, None

    if rule_type == "regex_match_percent":
        pattern = extra.get("pattern", "")
        if not pattern:
            raise ValueError("regex_match_percent 规则需要提供 extra_config.pattern")
        if t == "postgresql":
            sql = (
                f"SELECT COALESCE(100.0 * SUM(CASE WHEN {col} ~ %s THEN 1 ELSE 0 END) / COUNT(*), 0) "
                f"FROM {tbl}"
            )
        elif t == "clickhouse":
            sql = (
                f"SELECT if(COUNT(*) = 0, 0, 100.0 * countIf(match({col}, %s)) / COUNT(*)) "
                f"FROM {tbl}"
            )
        else:
            # MySQL
            sql = (
                f"SELECT COALESCE(100.0 * SUM(CASE WHEN {col} REGEXP %s THEN 1 ELSE 0 END) / COUNT(*), 0) "
                f"FROM {tbl}"
            )
        return sql, (pattern,)

    if rule_type == "length_check":
        op = extra.get("length_op", "eq")
        length_val = extra.get("length_value", 0)
        sql_op = {"eq": "=", "gt": ">", "lt": "<", "gte": ">=", "lte": "<=", "neq": "!="}.get(op, "=")
        if t == "clickhouse":
            sql = f"SELECT COUNT(*) FROM {tbl} WHERE lengthUTF8({col}) {sql_op} %s"
        elif t == "postgresql":
            sql = f"SELECT COUNT(*) FROM {tbl} WHERE LENGTH({col}::text) {sql_op} %s"
        else:
            sql = f"SELECT COUNT(*) FROM {tbl} WHERE CHAR_LENGTH({col}) {sql_op} %s"
        return sql, (length_val,)

    if rule_type == "value_range":
        min_val = extra.get("min_value")
        max_val = extra.get("max_value")
        if min_val is None and max_val is None:
            raise ValueError("value_range 规则需要提供 min_value 或 max_value")
        conditions = []
        params = []
        if min_val is not None:
            conditions.append(f"{col} < %s")
            params.append(min_val)
        if max_val is not None:
            conditions.append(f"{col} > %s")
            params.append(max_val)
        sql = f"SELECT COUNT(*) FROM {tbl} WHERE ({' OR '.join(conditions)})"
        return sql, tuple(params)

    raise ValueError(f"不支持的规则类型: {rule_type}")


def _execute_sql(ds: DataSource, sql: str, params: Optional[Tuple]) -> Any:
    """在数据源上执行 SQL，返回单值结果"""
    t = ds.type.lower()
    conn = None
    try:
        conn = _connect(ds)
        if t == "clickhouse":
            result = conn.execute(sql, params or ())
            if result:
                return result[0][0]
            return None
        else:
            cur = conn.cursor()
            cur.execute(sql, params or ())
            row = cur.fetchone()
            cur.close()
            if row:
                return row[0]
            return None
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def _to_float(val) -> Optional[float]:
    """将查询结果转为浮点数"""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def compare(actual: Optional[float], operator: str, threshold: float, threshold_max: Optional[float] = None) -> bool:
    """比较实际值与阈值"""
    if actual is None:
        # 空值时：除了 neq 都算失败（保守策略）
        return operator == "neq"

    if operator == "gt":
        return actual > threshold
    if operator == "lt":
        return actual < threshold
    if operator == "gte":
        return actual >= threshold
    if operator == "lte":
        return actual <= threshold
    if operator == "eq":
        return actual == threshold
    if operator == "neq":
        return actual != threshold
    if operator == "between":
        if threshold_max is None:
            raise ValueError("between 操作需要 threshold_max")
        return threshold <= actual <= threshold_max

    raise ValueError(f"不支持的比较操作: {operator}")


def execute_rule(rule, ds: DataSource) -> Dict[str, Any]:
    """执行单个质量规则检查。

    Args:
        rule: DqcRule ORM 实例（需有 rule_type, table_name, column_name, operator, threshold, threshold_max）
        ds: DataSource ORM 实例

    Returns:
        {"actual_value": str|None, "passed": bool, "error_msg": str|None}
    """
    try:
        # 解析 threshold 为浮点数
        threshold_val = float(rule.threshold) if rule.threshold else 0.0
        threshold_max_val = float(rule.threshold_max) if rule.threshold_max else None

        # 加载 extra_config（JSON 字段，如 custom_sql / pattern / min_value / max_value）
        extra = getattr(rule, "extra_config", None) or {}

        sql, params = generate_check_sql(
            rule.rule_type,
            rule.table_name,
            rule.column_name,
            ds.type,
            extra,
        )

        raw_value = _execute_sql(ds, sql, params)
        actual_val = _to_float(raw_value)

        passed = compare(actual_val, rule.operator, threshold_val, threshold_max_val)

        return {
            "actual_value": str(raw_value) if raw_value is not None else None,
            "passed": passed,
            "error_msg": None,
        }

    except Exception as e:
        logger.error(f"DQC 规则执行失败: {e}", exc_info=True)
        # 对外返回通用错误，避免泄露数据库内部信息
        safe_msg = "规则执行异常，请检查规则配置或数据源连接"
        if "custom_sql" in str(e).lower():
            safe_msg = "自定义 SQL 执行异常，请检查 SQL 语法"
        elif "不支持的规则类型" in str(e) or "不支持的比较操作" in str(e):
            safe_msg = str(e)
        return {
            "actual_value": None,
            "passed": False,
            "error_msg": safe_msg,
        }
