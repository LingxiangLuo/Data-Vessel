"""数据质量检查执行引擎

根据规则类型生成校验 SQL，在目标数据源上执行，比较结果返回 passed/failed。
Phase 1 支持 MySQL / PostgreSQL / ClickHouse。
"""
import logging
from typing import Optional, Dict, Any, Tuple

from app.core.db_adapter import _connect
from app.models.datasource import DataSource

logger = logging.getLogger(__name__)

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
    "table_size": False,
    "group_by_count": False,
    "value_enum": True,
    "format_check": True,
    "diff_percent": False,
    "diff_count": False,
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
        sql = extra.get("custom_sql", "").strip()
        if not sql:
            raise ValueError("custom_sql 规则需要提供 extra_config.custom_sql")
        upper = sql.upper()
        # 仅允许 SELECT 语句，禁止 DML/DDL
        if not upper.startswith("SELECT"):
            raise ValueError("custom_sql 只允许 SELECT 语句")
        forbidden = ("DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER", "CREATE", "GRANT", "REVOKE")
        for kw in forbidden:
            if kw in upper:
                raise ValueError(f"custom_sql 包含非法关键字: {kw}")
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

    # 新增 Phase 2 规则类型

    if rule_type == "table_size":
        if t == "mysql":
            parts = table.split(".")
            if len(parts) == 2:
                schema_name, table_name = parts
            else:
                schema_name = "DATABASE()"
                table_name = parts[0]
            schema_cond = f"table_schema = {schema_name}" if schema_name != "DATABASE()" else "table_schema = DATABASE()"
            sql = (
                f"SELECT COALESCE(data_length + index_length, 0) "
                f"FROM information_schema.tables "
                f"WHERE {schema_cond} AND table_name = %s"
            )
            return sql, (table_name,)
        elif t == "postgresql":
            sql = f"SELECT pg_total_relation_size(%s)"
            return sql, (table,)
        elif t == "clickhouse":
            sql = (
                f"SELECT COALESCE(sum(bytes), 0) FROM system.parts "
                f"WHERE table = %s AND active = 1"
            )
            return sql, (table.split(".")[-1],)
        else:
            raise ValueError(f"table_size 规则暂不支持数据源类型: {t}")

    if rule_type == "group_by_count":
        group_col = extra.get("group_by_column")
        target_val = extra.get("target_group_value")
        if not group_col or target_val is None:
            raise ValueError("group_by_count 规则需要提供 extra_config.group_by_column 和 target_group_value")
        gcol = _quote_identifier(group_col, ds_type)
        sql = f"SELECT COUNT(*) FROM {tbl} WHERE {gcol} = %s"
        return sql, (target_val,)

    if rule_type == "value_enum":
        allowed = extra.get("allowed_values")
        if not allowed or not isinstance(allowed, list):
            raise ValueError("value_enum 规则需要提供 extra_config.allowed_values (列表)")
        # 计算不在允许列表中的行数
        placeholders = ", ".join(["%s"] * len(allowed))
        sql = f"SELECT COUNT(*) FROM {tbl} WHERE {col} NOT IN ({placeholders})"
        return sql, tuple(allowed)

    if rule_type == "format_check":
        fmt = extra.get("format_type", "")
        patterns = {
            "date": r"^\d{4}-\d{2}-\d{2}",
            "datetime": r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}",
            "phone": r"^1[3-9]\d{9}$",
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "idcard": r"^\d{17}[\dXx]$",
        }
        pattern = patterns.get(fmt)
        if not pattern:
            raise ValueError(f"format_check 不支持格式类型: {fmt}，允许: {', '.join(patterns.keys())}")
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
            sql = (
                f"SELECT COALESCE(100.0 * SUM(CASE WHEN {col} REGEXP %s THEN 1 ELSE 0 END) / COUNT(*), 0) "
                f"FROM {tbl}"
            )
        return sql, (pattern,)

    if rule_type in ("diff_percent", "diff_count"):
        compare_with = extra.get("compare_with", "prev_day")
        time_col = extra.get("time_column")
        if not time_col:
            raise ValueError(f"{rule_type} 规则需要提供 extra_config.time_column")
        tcol = _quote_identifier(time_col, ds_type)

        # 当前值 SQL（不带时间过滤，假设表是分区表或全量表）
        current_sql = f"SELECT COUNT(*) FROM {tbl}"
        # 历史对比值 SQL
        if t == "clickhouse":
            if compare_with == "prev_day":
                hist_sql = f"SELECT COUNT(*) FROM {tbl} WHERE toDate({tcol}) = today() - 1"
            else:  # prev_week
                hist_sql = f"SELECT COUNT(*) FROM {tbl} WHERE toDate({tcol}) = today() - 7"
        elif t == "postgresql":
            if compare_with == "prev_day":
                hist_sql = f"SELECT COUNT(*) FROM {tbl} WHERE {tcol}::date = CURRENT_DATE - INTERVAL '1 day'"
            else:
                hist_sql = f"SELECT COUNT(*) FROM {tbl} WHERE {tcol}::date = CURRENT_DATE - INTERVAL '7 days'"
        else:  # mysql
            if compare_with == "prev_day":
                hist_sql = f"SELECT COUNT(*) FROM {tbl} WHERE DATE({tcol}) = DATE_SUB(CURDATE(), INTERVAL 1 DAY)"
            else:
                hist_sql = f"SELECT COUNT(*) FROM {tbl} WHERE DATE({tcol}) = DATE_SUB(CURDATE(), INTERVAL 7 DAY)"

        # 波动率规则需要特殊处理：在 execute_rule 中执行两条 SQL
        # 这里返回标记，让 execute_rule 识别并分别执行
        return f"__DIFF__|{current_sql}|{hist_sql}|{compare_with}", None

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

        # 波动率规则：执行两条 SQL
        if isinstance(sql, str) and sql.startswith("__DIFF__|"):
            parts = sql.split("|", 3)
            current_sql = parts[1]
            hist_sql = parts[2]
            compare_with = parts[3]
            current_val = _to_float(_execute_sql(ds, current_sql, None))
            hist_val = _to_float(_execute_sql(ds, hist_sql, None))

            if current_val is None or hist_val is None or hist_val == 0:
                actual_val = None
            elif rule.rule_type == "diff_percent":
                actual_val = abs(current_val - hist_val) / hist_val * 100
            else:  # diff_count
                actual_val = abs(current_val - hist_val)

            passed = compare(actual_val, rule.operator, threshold_val, threshold_max_val)
            display = f"{actual_val:.2f}" if actual_val is not None else "N/A"
            return {
                "actual_value": display,
                "passed": passed,
                "error_msg": None,
            }

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


def _execute_query_rows(ds: DataSource, sql: str, params: Optional[Tuple], limit: int = 10) -> list:
    """在数据源上执行 SQL，返回多行结果 (dict 列表)。"""
    t = ds.type.lower()
    conn = None
    try:
        conn = _connect(ds)
        if t == "clickhouse":
            # ClickHouse 驱动直接返回 list of tuples
            rows = conn.execute(sql, params or ())
            if not rows:
                return []
            # 尝试获取列名（clickhouse 驱动可能不直接提供）
            return [{"col_" + str(i): v for i, v in enumerate(row)} for row in rows[:limit]]
        else:
            cur = conn.cursor()
            cur.execute(sql, params or ())
            cols = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchmany(limit)
            cur.close()
            return [dict(zip(cols, row)) for row in rows]
    except Exception:
        logger.warning("采样查询执行失败", exc_info=True)
        return []
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def generate_sample_sql(rule_type: str, table: str, column: Optional[str], ds_type: str, extra: Optional[Dict[str, Any]] = None) -> Tuple[str, Optional[Tuple]]:
    """生成失败数据采样 SQL，返回 (sql, params)。"""
    t = ds_type.lower()
    tbl = _table_ref(table, ds_type)
    col = _quote_identifier(column, ds_type) if column else None
    extra = extra or {}

    if rule_type == "custom_sql" and col is None:
        # custom_sql 的采样就是执行原 SQL 限制条数
        base_sql = extra.get("custom_sql", "")
        if not base_sql:
            return "", None
        # 简单地在末尾加 LIMIT
        base_sql = base_sql.strip().rstrip(";")
        if t == "clickhouse":
            return f"{base_sql} LIMIT 10", None
        return f"{base_sql} LIMIT 10", None

    if rule_type == "null_count" and col:
        return f"SELECT * FROM {tbl} WHERE {col} IS NULL LIMIT 10", None

    if rule_type == "null_percent" and col:
        return f"SELECT * FROM {tbl} WHERE {col} IS NULL LIMIT 10", None

    if rule_type == "value_range" and col:
        min_val = extra.get("min_value")
        max_val = extra.get("max_value")
        conditions = []
        params = []
        if min_val is not None:
            conditions.append(f"{col} < %s")
            params.append(min_val)
        if max_val is not None:
            conditions.append(f"{col} > %s")
            params.append(max_val)
        if not conditions:
            return "", None
        sql = f"SELECT * FROM {tbl} WHERE ({' OR '.join(conditions)}) LIMIT 10"
        return sql, tuple(params)

    if rule_type == "regex_match_percent" and col:
        pattern = extra.get("pattern", "")
        if not pattern:
            return "", None
        if t == "postgresql":
            sql = f"SELECT * FROM {tbl} WHERE NOT ({col} ~ %s) LIMIT 10"
        elif t == "clickhouse":
            sql = f"SELECT * FROM {tbl} WHERE NOT match({col}, %s) LIMIT 10"
        else:
            sql = f"SELECT * FROM {tbl} WHERE NOT ({col} REGEXP %s) LIMIT 10"
        return sql, (pattern,)

    if rule_type == "length_check" and col:
        op = extra.get("length_op", "eq")
        length_val = extra.get("length_value", 0)
        sql_op = {"eq": "=", "gt": ">", "lt": "<", "gte": ">=", "lte": "<=", "neq": "!="}.get(op, "=")
        if t == "clickhouse":
            sql = f"SELECT * FROM {tbl} WHERE NOT lengthUTF8({col}) {sql_op} %s LIMIT 10"
        elif t == "postgresql":
            sql = f"SELECT * FROM {tbl} WHERE NOT LENGTH({col}::text) {sql_op} %s LIMIT 10"
        else:
            sql = f"SELECT * FROM {tbl} WHERE NOT CHAR_LENGTH({col}) {sql_op} %s LIMIT 10"
        return sql, (length_val,)

    if rule_type == "value_enum" and col:
        allowed = extra.get("allowed_values")
        if not allowed or not isinstance(allowed, list):
            return "", None
        placeholders = ", ".join(["%s"] * len(allowed))
        sql = f"SELECT * FROM {tbl} WHERE {col} NOT IN ({placeholders}) LIMIT 10"
        return sql, tuple(allowed)

    if rule_type == "format_check" and col:
        fmt = extra.get("format_type", "")
        patterns = {
            "date": r"^\\d{4}-\\d{2}-\\d{2}",
            "datetime": r"^\\d{4}-\\d{2}-\\d{2}[ T]\\d{2}:\\d{2}:\\d{2}",
            "phone": r"^1[3-9]\\d{9}$",
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
            "idcard": r"^\\d{17}[\\dXx]$",
        }
        pattern = patterns.get(fmt, "")
        if not pattern:
            return "", None
        if t == "postgresql":
            sql = f"SELECT * FROM {tbl} WHERE NOT ({col} ~ %s) LIMIT 10"
        elif t == "clickhouse":
            sql = f"SELECT * FROM {tbl} WHERE NOT match({col}, %s) LIMIT 10"
        else:
            sql = f"SELECT * FROM {tbl} WHERE NOT ({col} REGEXP %s) LIMIT 10"
        return sql, (pattern,)

    if rule_type == "duplicate_count" and col:
        # 找出重复值及对应行
        if t == "clickhouse":
            inner = f"SELECT {col} FROM {tbl} GROUP BY {col} HAVING COUNT(*) > 1 LIMIT 10"
            sql = f"SELECT * FROM {tbl} WHERE {col} IN ({inner}) LIMIT 10"
        else:
            inner = f"SELECT {col} FROM {tbl} GROUP BY {col} HAVING COUNT(*) > 1 LIMIT 10"
            sql = f"SELECT a.* FROM {tbl} AS a INNER JOIN ({inner}) AS b ON a.{col} = b.{col} LIMIT 10"
        return sql, None

    # 默认：无法生成采样 SQL
    return "", None


def sample_failures(rule, ds: DataSource) -> list:
    """对失败的规则执行采样查询，返回最多 10 条失败数据。

    Returns:
        [{col1: val1, col2: val2}, ...]
    """
    extra = getattr(rule, "extra_config", None) or {}
    sql, params = generate_sample_sql(
        rule.rule_type,
        rule.table_name,
        rule.column_name,
        ds.type,
        extra,
    )
    if not sql:
        return []
    return _execute_query_rows(ds, sql, params, limit=10)
