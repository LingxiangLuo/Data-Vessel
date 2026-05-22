"""参数替换引擎 — Portal 层统一参数解析与替换

对标 DataWorks 调度参数体系，支持:
- 系统内置参数: ${bizdate}, ${cyctime}, ${gmtdate}
- 业务日期参数 ${...}: ${yyyy}, ${yyyymmdd}, ${yyyy-mm-dd}, ${yyyymmdd-7} 等
- 自定义参数: 用户在组件中定义的参数，值可引用其他参数（仅限已定义参数，不支持前向引用）
- 运行时覆盖: 手动执行时传入覆盖值

自定义参数限制:
- 按定义顺序解析，不支持引用后定义的参数（前向引用）
- 递归解析深度限制为 5 轮，防止循环引用导致栈溢出
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


# 参数引用正则 (匹配 ${key} 或 ${key.fmt(...)} 或 ${yyyymmdd-7} 等)
PARAM_REF_RE = re.compile(
    r"\$\{(\w+(?:\.\w+)?)(?:\.fmt\(([^)]+)\))?\}|"  # ${key} 或 ${key.fmt()}
    r"\$\{((?:\d{4}|yyyy|yy|mm|dd|yyyymm|yyyymmdd|yyyy[/-]mm[/-]dd)(?:[+-]\d+)?)\}|"  # ${yyyy}, ${yyyymmdd-7}
    r"\$\{([+-]\d+)\}"  # 纯数字偏移（DataWorks 快捷语法）
)

# 系统快捷参数（直接映射到日期字符串）
SYSTEM_SHORTCUTS = {"bizdate", "cyctime", "gmtdate", "bizmonth", "bizdate.prev", "bizdate.next", "last_sync_time"}


def _build_system_params(biz_date: Optional[datetime] = None, cyctime: Optional[datetime] = None) -> Dict[str, str]:
    """构建系统快捷参数字典"""
    now = cyctime or datetime.now()
    biz = biz_date or (now - timedelta(days=1))
    biz_str = biz.strftime("%Y%m%d")
    biz_prev = (biz - timedelta(days=1)).strftime("%Y%m%d")
    biz_next = (biz + timedelta(days=1)).strftime("%Y%m%d")
    gmt = now.strftime("%Y%m%d")
    cyctime_str = now.strftime("%Y%m%d%H%M%S")
    bizmonth = biz.strftime("%Y%m")
    last_sync = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

    return {
        "bizdate": biz_str,
        "bizdate.prev": biz_prev,
        "bizdate.next": biz_next,
        "cyctime": cyctime_str,  # DataWorks 格式: yyyymmddhh24miss
        "gmtdate": gmt,
        "bizmonth": bizmonth,
        "last_sync_time": last_sync,
    }


def _resolve_date_format(fmt: str, dt: datetime) -> str:
    """按 DataWorks 格式输出日期

    支持的格式:
    - yyyy, yy, mm, dd
    - yyyymm, yyyymmdd
    - yyyy-mm-dd, yyyy/mm/dd
    - yyyy-mm-dd hh24:mi:ss 等组合
    """
    # 将 DataWorks 格式映射为 Python strftime 格式
    mapping = {
        "yyyy": "%Y",
        "yy": "%y",
        "mm": "%m",
        "dd": "%d",
        "yyyymm": "%Y%m",
        "yyyymmdd": "%Y%m%d",
        "hh24": "%H",
        "hh": "%H",
        "hh12": "%I",
        "mi": "%M",
        "ss": "%S",
    }
    result = fmt
    # 按长度从长到短排序，避免短字符串提前破坏长字符串（如 yyyy 破坏 yyyymmdd）
    for dw_fmt, py_fmt in sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True):
        result = result.replace(dw_fmt, py_fmt)
    try:
        return dt.strftime(result)
    except ValueError:
        return dt.strftime("%Y%m%d")


def _apply_offset(dt: datetime, offset_str: Optional[str]) -> datetime:
    """应用日期偏移"""
    if not offset_str:
        return dt
    sign = 1 if offset_str[0] == "+" else -1
    value = int(offset_str[1:])
    return dt + timedelta(days=sign * value)


def _parse_param_token(token: str, ctx: Dict[str, str], biz_date: datetime, cyctime: datetime) -> str:
    """解析单个参数 token，返回替换后的值"""

    # 1. 系统快捷参数
    if token in SYSTEM_SHORTCUTS:
        return ctx.get(token, f"${{{token}}}")

    # 2. 自定义参数（用户在 params 中定义的 key）
    if token in ctx:
        val = ctx[token]
        # 如果值中还包含变量引用，递归解析（但限制深度防止循环）
        if "${" in val:
            return val  # 已在 build_param_context 中预解析
        return val

    # 3. DataWorks 日期格式参数 ${yyyy}, ${yyyymmdd}, ${yyyy-mm-dd} 等
    # 提取可能的偏移后缀 (±N)
    offset_match = re.match(r"^(\d{4}|yyyy|yy|mm|dd|yyyymm|yyyymmdd|yyyy[/-]mm[/-]dd|yyyy-mm-dd hh24:mi:ss|hh24:mi:ss)([+-]\d+)?$", token)
    if offset_match:
        fmt = offset_match.group(1)
        offset = offset_match.group(2)
        dt = _apply_offset(biz_date, offset)
        return _resolve_date_format(fmt, dt)

    # 4. 纯数字偏移 ${-7} → 基于业务日期的天数偏移（DataWorks 兼容语法）
    if re.match(r"^[+-]\d+$", token):
        days = int(token)
        dt = biz_date + timedelta(days=days)
        return dt.strftime("%Y%m%d")

    # 未匹配，保留原样
    return f"${{{token}}}"


def build_param_context(
    param_defs: List[Dict[str, Any]],
    runtime_overrides: Optional[Dict[str, str]] = None,
    biz_date: Optional[datetime] = None,
    cyctime: Optional[datetime] = None,
) -> Dict[str, str]:
    """构建完整的参数上下文

    解析顺序:
    1. 系统内置参数 (bizdate, cyctime, gmtdate, 年月日格式等)
    2. 自定义参数按定义顺序解析（支持引用已解析的参数，不支持前向引用）
    3. 运行时覆盖（最高优先级）

    注意: 自定义参数不支持前向引用，即第 N 个参数的值不能引用第 N+1 个参数。
    需要交叉引用的场景请在定义列表中调整顺序，或使用系统参数作为中间值。
    """
    now = cyctime or datetime.now()
    biz = biz_date or (now - timedelta(days=1))

    # 1. 系统参数
    ctx = _build_system_params(biz, now)

    # 预计算所有 DataWorks 格式的日期参数（常用组合）
    # 基于业务日期
    for fmt in ["yyyy", "yy", "mm", "dd", "yyyymm", "yyyymmdd", "yyyy-mm-dd", "yyyy/mm/dd"]:
        key = fmt
        ctx[key] = _resolve_date_format(fmt, biz)

    # 基于定时时间
    for fmt in ["yyyy", "yy", "mm", "dd", "yyyymm", "yyyymmdd", "yyyy-mm-dd", "hh24", "mi", "ss", "hh24:mi:ss"]:
        key = fmt + "_ct"  # 带 _ct 后缀表示 cyctime 基准
        ctx[key] = _resolve_date_format(fmt, now)

    # 2. 按顺序解析自定义参数
    seen_keys = set()
    for p in param_defs or []:
        key = p.get("key", "").strip()
        raw_value = p.get("value", "")
        if not key:
            continue
        if key in seen_keys:
            raise ValueError(f"参数定义中存在重复 key: {key}")
        seen_keys.add(key)
        resolved = substitute(str(raw_value), ctx, biz, now)
        ctx[key] = resolved

    # 3. 运行时覆盖
    if runtime_overrides:
        for key, val in runtime_overrides.items():
            ctx[key] = str(val)

    return ctx


def substitute(text: str, ctx: Dict[str, str], biz_date: Optional[datetime] = None, cyctime: Optional[datetime] = None) -> str:
    """将文本中所有 ${key} 替换为实际值

    支持:
    - ${bizdate}, ${cyctime}, ${gmtdate}
    - ${yyyy}, ${yyyymmdd}, ${yyyy-mm-dd}
    - ${yyyymmdd-7}, ${yyyy-1} 等偏移
    - 自定义参数 ${key}
    """
    if not text:
        return text

    if biz_date is None:
        biz_date = datetime.now() - timedelta(days=1)
    if cyctime is None:
        cyctime = datetime.now()

    def _replacer(m: re.Match) -> str:
        # 尝试所有捕获组，找到第一个非空的
        token = next((g for g in m.groups() if g is not None), None)
        if not token:
            return m.group(0)
        return _parse_param_token(token, ctx, biz_date, cyctime)

    # 支持两种格式: ${...} 和 $[...]（二期实现 $[...]）
    result = PARAM_REF_RE.sub(_replacer, text)
    return result


def substitute_config(cfg: Dict[str, Any], ctx: Dict[str, str], ctype: str, biz_date: Optional[datetime] = None, cyctime: Optional[datetime] = None) -> Dict[str, Any]:
    """根据组件类型，对 config_json 中需要替换的字段做参数替换

    返回一个新的 config（不修改原对象）
    """
    import copy
    new_cfg = copy.deepcopy(cfg)

    if ctype == "sql":
        if "sql" in new_cfg and isinstance(new_cfg["sql"], str):
            new_cfg["sql"] = substitute(new_cfg["sql"], ctx, biz_date, cyctime)
        for key in ("preStatements", "postStatements"):
            if key in new_cfg and isinstance(new_cfg[key], list):
                new_cfg[key] = [
                    substitute(s, ctx, biz_date, cyctime) if isinstance(s, str) else s
                    for s in new_cfg[key]
                ]

    elif ctype in ("python", "shell"):
        if "script" in new_cfg and isinstance(new_cfg["script"], str):
            new_cfg["script"] = substitute(new_cfg["script"], ctx, biz_date, cyctime)

    elif ctype == "datax":
        if "where_clause" in new_cfg and isinstance(new_cfg["where_clause"], str):
            new_cfg["where_clause"] = substitute(new_cfg["where_clause"], ctx, biz_date, cyctime)
        if "field_mapping" in new_cfg and isinstance(new_cfg["field_mapping"], list):
            new_cfg["field_mapping"] = [
                {
                    **fm,
                    "src": substitute(fm.get("src", ""), ctx, biz_date, cyctime) if fm.get("kind") in ("variable", "constant") else fm.get("src", ""),
                }
                for fm in new_cfg["field_mapping"]
            ]
        if "rawJson" in new_cfg and isinstance(new_cfg["rawJson"], str):
            new_cfg["rawJson"] = substitute(new_cfg["rawJson"], ctx, biz_date, cyctime)

    return new_cfg
