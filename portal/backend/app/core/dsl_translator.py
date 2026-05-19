"""DSL Translator — 把 Portal Component / Workflow 翻译成 DolphinScheduler 原生 JSON

设计要点:
- Component (sql/python/shell/datax) → DS Task Definition
- Workflow (线性步骤) → DS Process Definition (taskDefinitionJson + taskRelationJson + locations)
- DataX 走 SHELL 节点 + heredoc 临时 JSON,不用 DS 原生 DataX 节点 (spec 冻结要求)
"""
import json
from typing import List, Dict, Any, Tuple, Optional


# DS 默认任务参数模板
DEFAULT_TASK_DEFAULTS = {
    "version": 0,
    "delayTime": "0",
    "flag": "YES",
    "isCache": "NO",
    "taskPriority": "MEDIUM",
    "workerGroup": "default",
    "environmentCode": -1,
    "failRetryTimes": "0",
    "failRetryInterval": "1",
    "timeoutFlag": "CLOSE",
    "timeoutNotifyStrategy": "",
    "timeout": 0,
    "cpuQuota": -1,
    "memoryMax": -1,
    "taskExecuteType": "BATCH",
}


def _datasource_type_for_ds(portal_type: str) -> str:
    """Portal 数据源 type → DS SQL 节点的 type 字段"""
    return (portal_type or "").upper() or "MYSQL"


def _build_datax_shell_script(config: Dict[str, Any]) -> str:
    """把 datax 组件 config 翻译成 SHELL 脚本 (heredoc 生成 JSON 后调 datax.py)

    config 期望字段:
      - rawJson: 完整 DataX job JSON 字符串 (优先)
      - 或 reader/writer/source_id/target_id: 高阶字段 (Phase 后期实现自动构造)
    """
    raw = config.get("rawJson")
    if not raw:
        # 兜底:把整个 config 序列化作为 job
        raw = json.dumps({"job": config}, ensure_ascii=False, indent=2)
    # 安全: 防止 heredoc 分隔符被 rawJson 内容突破
    HEREDOC_DELIM = "PORTAL_DATAX_EOF"
    if HEREDOC_DELIM in raw:
        raise ValueError("DataX JSON 内容包含非法字符序列")
    # 用 heredoc 写入临时文件,然后调用 datax.py
    # 注意: heredoc 用引号包裹 'EOF' 防止变量展开
    script = (
        "set -e\n"
        "export JAVA_HOME=${JAVA_HOME:-/opt/java/openjdk}\n"
        "export PATH=$JAVA_HOME/bin:$PATH\n"
        "JOB_FILE=/tmp/datax_job_$$_$(date +%s).json\n"
        "cat > \"$JOB_FILE\" <<'PORTAL_DATAX_EOF'\n"
        f"{raw}\n"
        "PORTAL_DATAX_EOF\n"
        "echo \"[Portal] datax job file: $JOB_FILE\"\n"
        "python3 /opt/datax/bin/datax.py \"$JOB_FILE\"\n"
        "rm -f \"$JOB_FILE\"\n"
    )
    return script


def translate_component_to_task(
    component: Any,
    task_code: int,
    task_name: Optional[str] = None,
    datasource_lookup: Optional[Dict[int, Any]] = None,
) -> Dict[str, Any]:
    """单个 Component → DS Task Definition JSON

    参数:
        component: SQLAlchemy Component 实例,需含 .type / .name / .config_json / .description
        task_code: DS 分配的任务编码
        task_name: 步骤名 (默认取 component.name)
        datasource_lookup: {id: DataSource} 用于 SQL 节点查 datasource 类型
    """
    from app.core.param_engine import build_param_context, substitute_config

    cfg = component.config_json or {}
    ctype = component.type

    # Portal 层参数替换：调度执行时使用默认值（无 runtime_overrides）
    ctx = build_param_context(getattr(component, 'params', None) or [])
    cfg = substitute_config(cfg, ctx, ctype)
    name = task_name or component.name
    base = {
        "code": task_code,
        "name": name,
        "description": component.description or "",
        **DEFAULT_TASK_DEFAULTS,
    }

    if ctype == "sql":
        ds_id = cfg.get("datasource_id")
        ds_type = "MYSQL"
        ds_datasource_id = None
        if datasource_lookup and ds_id and ds_id in datasource_lookup:
            ds_obj = datasource_lookup[ds_id]
            ds_type = _datasource_type_for_ds(ds_obj.type)
            ds_datasource_id = getattr(ds_obj, "ds_datasource_id", None)
        sql_text = cfg.get("sql", "")
        # 判断 SQL 类型: SELECT 为 query(0),其他为 non-query(1)
        sql_type = "0" if sql_text.strip().lower().startswith("select") else "1"
        base["taskType"] = "SQL"
        base["taskParams"] = {
            "type": ds_type,
            "datasource": ds_datasource_id or ds_id,
            "sql": sql_text,
            "sqlType": sql_type,
            "preStatements": cfg.get("preStatements", []),
            "postStatements": cfg.get("postStatements", []),
            "displayRows": 10,
            "localParams": cfg.get("localParams", []),
            "resourceList": [],
        }
        if cfg.get("timeout"):
            base["timeoutFlag"] = "OPEN"
            base["timeout"] = int(cfg["timeout"]) // 60 or 1  # DS timeout 单位是分钟

    elif ctype == "python":
        base["taskType"] = "PYTHON"
        base["taskParams"] = {
            "rawScript": cfg.get("script", ""),
            "resourceList": [],
            "localParams": cfg.get("localParams", []),
        }
        if cfg.get("timeout"):
            base["timeoutFlag"] = "OPEN"
            base["timeout"] = int(cfg["timeout"]) // 60 or 1

    elif ctype == "shell":
        base["taskType"] = "SHELL"
        base["taskParams"] = {
            "rawScript": cfg.get("script", ""),
            "resourceList": [],
            "localParams": cfg.get("localParams", []),
        }
        if cfg.get("timeout"):
            base["timeoutFlag"] = "OPEN"
            base["timeout"] = int(cfg["timeout"]) // 60 or 1

    elif ctype == "datax":
        # DataX 翻译成 SHELL + heredoc
        # 若 rawJson 缺失,尝试用 build_datax_job 现场生成标准 DataX JSON
        datax_cfg = dict(cfg)
        if not datax_cfg.get("rawJson"):
            source_id = datax_cfg.get("source_id")
            target_id = datax_cfg.get("target_id")
            if (
                datasource_lookup
                and source_id in datasource_lookup
                and target_id in datasource_lookup
            ):
                from app.core.datax_builder import build_datax_job
                source_ds = datasource_lookup[source_id]
                target_ds = datasource_lookup[target_id]
                job = build_datax_job(
                    source_ds=source_ds,
                    source_table=datax_cfg.get("source_table", ""),
                    target_ds=target_ds,
                    target_table=datax_cfg.get("target_table", ""),
                    field_mapping=datax_cfg.get("field_mapping", []),
                    sync_type=datax_cfg.get("sync_type", "full"),
                    increment_column=datax_cfg.get("increment_column"),
                    where_clause=datax_cfg.get("where_clause"),
                    split_pk=datax_cfg.get("split_pk"),
                    write_mode=datax_cfg.get("write_mode", "insert"),
                    channel=datax_cfg.get("channel", 3),
                    pre_sql=datax_cfg.get("pre_sql"),
                    post_sql=datax_cfg.get("post_sql"),
                    mask_password=False,
                )
                datax_cfg["rawJson"] = json.dumps(job, ensure_ascii=False, indent=2)
        base["taskType"] = "SHELL"
        base["taskParams"] = {
            "rawScript": _build_datax_shell_script(datax_cfg),
            "resourceList": [],
            "localParams": [],
        }
        # DataX 默认给更宽松的超时
        base["timeoutFlag"] = "OPEN"
        base["timeout"] = max(int(cfg.get("timeout", 1800)) // 60, 5)

    else:
        raise ValueError(f"不支持的组件类型: {ctype}")

    return base


def build_task_relations(task_codes: List[int]) -> List[Dict[str, Any]]:
    """线性流水线的 task relation (preTaskCode → postTaskCode)

    DS 约定:
      - 第一个任务用 preTaskCode=0 表示入口
      - 后续每个任务用前一个的 code 作为 preTaskCode
    """
    relations = []
    if not task_codes:
        return relations
    # 入口边
    relations.append({
        "preTaskCode": 0,
        "preTaskVersion": 0,
        "postTaskCode": task_codes[0],
        "postTaskVersion": 0,
        "name": "",
        "conditionType": "NONE",
        "conditionParams": {},
    })
    # 后续连接
    for i in range(1, len(task_codes)):
        relations.append({
            "preTaskCode": task_codes[i - 1],
            "preTaskVersion": 0,
            "postTaskCode": task_codes[i],
            "postTaskVersion": 0,
            "name": "",
            "conditionType": "NONE",
            "conditionParams": {},
        })
    return relations


def build_locations(task_codes: List[int]) -> List[Dict[str, Any]]:
    """线性流水线的节点坐标(DS DAG 图渲染用,横向排列)"""
    return [
        {"taskCode": code, "x": 200 + i * 220, "y": 200}
        for i, code in enumerate(task_codes)
    ]


def translate_workflow(
    workflow: Any,
    components_by_id: Dict[int, Any],
    task_codes: List[int],
    datasource_lookup: Optional[Dict[int, Any]] = None,
    dqc_rules_lookup: Optional[Dict[int, List[Any]]] = None,
    portal_base_url: str = "http://portal:8000",
    service_token: str = "",
) -> Dict[str, Any]:
    """Workflow → DS Process Definition save 所需的 4 个字段

    DQC 任务插入逻辑（线性工作流）：
      组件任务 → [DQC 任务链] → 下一个组件任务

    task_codes 需包含所有组件任务 code + DQC 任务 code。

    返回:
        {
            "name": ...,
            "description": ...,
            "taskDefinitionJson": "[...]",
            "taskRelationJson": "[...]",
            "locations": "[...]",
        }
    """
    steps = workflow.steps_json or []
    # 先统计需要多少 DQC 任务
    dqc_count = 0
    for step in steps:
        cid = step.get("component_id")
        comp = components_by_id.get(cid)
        if comp and dqc_rules_lookup:
            rules = dqc_rules_lookup.get(cid, [])
            dqc_count += len([r for r in rules if getattr(r, "enabled", True)])

    comp_count = len(steps)
    total_needed = comp_count + dqc_count
    if len(task_codes) != total_needed:
        raise ValueError(f"task_codes 数量与步骤数不一致: 需要 {total_needed} 个，实际 {len(task_codes)}")

    comp_codes = task_codes[:comp_count]
    dqc_codes = task_codes[comp_count:total_needed]
    dqc_code_iter = iter(dqc_codes)

    # 构建 execution_order: 每个 step 后面紧跟它的 DQC 任务
    execution_codes = []  # List[int] 按执行顺序排列的所有 task code
    task_defs = []

    for step, tcode in zip(steps, comp_codes):
        cid = step.get("component_id")
        comp = components_by_id.get(cid)
        if not comp:
            raise ValueError(f"组件 {cid} 不存在")
        step_name = step.get("name") or comp.name
        td = translate_component_to_task(comp, tcode, task_name=step_name, datasource_lookup=datasource_lookup)
        task_defs.append(td)
        execution_codes.append(tcode)

        # 追加该组件的 DQC 任务
        dqc_tasks = _collect_dqc_tasks_for_component(
            comp, dqc_rules_lookup, dqc_code_iter, portal_base_url, service_token
        )
        task_defs.extend(dqc_tasks)
        execution_codes.extend(t["code"] for t in dqc_tasks)

    relations = build_task_relations(execution_codes)
    locations = build_locations(execution_codes)

    return {
        "name": workflow.name,
        "description": workflow.description or "",
        "taskDefinitionJson": json.dumps(task_defs, ensure_ascii=False),
        "taskRelationJson": json.dumps(relations, ensure_ascii=False),
        "locations": json.dumps(locations, ensure_ascii=False),
    }


# ============================================================
# DQC 任务翻译
# ============================================================

def translate_dqc_task(
    rule: Any,
    task_code: int,
    portal_base_url: str = "http://portal:8000",
    service_token: str = "",
) -> Dict[str, Any]:
    """将 DQC 规则翻译为 DS SHELL 任务定义

    SHELL 脚本调用 Portal API 执行质量检查，根据 is_strong 控制 exit code：
    - 强规则失败：exit 1（DS 阻断下游）
    - 弱规则失败：exit 0（仅告警，下游继续）
    """
    is_strong = getattr(rule, "is_strong", False)
    suffix = "[强]" if is_strong else "[弱]"
    name = f"DQC:{rule.name}{suffix}"
    # 截断到 DS 允许的 100 字符以内
    if len(name) > 100:
        name = name[:97] + "..."

    check_url = f"{portal_base_url}/api/dqc-rules/{rule.id}/check"
    exit_cmd = "exit 1" if is_strong else 'echo "[DQC] Weak rule, continuing..."'

    script = f'''set -e
CHECK_URL="{check_url}"
SVC_TOKEN="{service_token}"
echo "[DQC] Running check for rule #{rule.id}..."
RESULT=$(curl -s -X POST "$CHECK_URL" \\
  -H "X-Service-Token: $SVC_TOKEN" \\
  -H "Content-Type: application/json" || echo '{{"passed":false,"error_msg":"curl failed"}}')
echo "[DQC] Raw result: $RESULT"
# 优先用 jq，回退 grep
if command -v jq > /dev/null 2>&1; then
  PASSED=$(echo "$RESULT" | jq -r ".passed // false")
else
  PASSED=$(echo "$RESULT" | grep -o '"passed":true' > /dev/null 2>&1 && echo "true" || echo "false")
fi
if [ "$PASSED" != "true" ]; then
  echo "[DQC] Check FAILED"
  {exit_cmd}
fi
echo "[DQC] Check PASSED"
'''

    return {
        "code": task_code,
        "name": name,
        "taskType": "SHELL",
        "taskParams": {
            "rawScript": script,
            "resourceList": [],
            "localParams": [],
        },
        **DEFAULT_TASK_DEFAULTS,
        "timeoutFlag": "OPEN",
        "timeout": 10,  # DQC 检查通常很快，最多 10 分钟
    }


def _collect_dqc_tasks_for_component(
    comp: Any,
    dqc_rules_lookup: Optional[Dict[int, List[Any]]],
    task_code_iter,
    portal_base_url: str,
    service_token: str,
) -> List[Dict[str, Any]]:
    """收集单个组件关联的所有 DQC 任务定义"""
    if not dqc_rules_lookup:
        return []
    rules = dqc_rules_lookup.get(getattr(comp, "id", None), [])
    return [
        translate_dqc_task(r, next(task_code_iter), portal_base_url, service_token)
        for r in rules if getattr(r, "enabled", True)
    ]


# ============================================================
# DAG 模式翻译（支持并行分支和汇聚）
# ============================================================

def _topological_sort(nodes: List[Dict], edges: List[Dict]) -> List[str]:
    """Kahn 算法拓扑排序，同时检测环"""
    from collections import deque
    node_ids = {n["id"] for n in nodes}
    in_degree = {nid: 0 for nid in node_ids}
    adj = {nid: [] for nid in node_ids}
    for e in edges:
        if e["source"] in node_ids and e["target"] in node_ids:
            adj[e["source"]].append(e["target"])
            in_degree[e["target"]] += 1
    queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
    result = []
    while queue:
        nid = queue.popleft()
        result.append(nid)
        for child in adj[nid]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)
    if len(result) != len(node_ids):
        raise ValueError("DAG 中存在环，无法发布")
    return result


def build_task_relations_from_dag(
    edges: List[Dict],
    node_to_task_code: Dict[str, int],
    nodes: List[Dict],
) -> List[Dict[str, Any]]:
    """DAG 结构 → DS taskRelationJson"""
    node_ids = {n["id"] for n in nodes}
    targets_with_incoming = {e["target"] for e in edges if e["source"] in node_ids and e["target"] in node_ids}
    relations = []
    # Root nodes（入度为 0）
    for n in nodes:
        if n["id"] not in targets_with_incoming:
            relations.append({
                "preTaskCode": 0,
                "preTaskVersion": 0,
                "postTaskCode": node_to_task_code[n["id"]],
                "postTaskVersion": 0,
                "name": "",
                "conditionType": "NONE",
                "conditionParams": {},
            })
    # 普通边
    for e in edges:
        if e["source"] in node_ids and e["target"] in node_ids:
            relations.append({
                "preTaskCode": node_to_task_code[e["source"]],
                "preTaskVersion": 0,
                "postTaskCode": node_to_task_code[e["target"]],
                "postTaskVersion": 0,
                "name": "",
                "conditionType": "NONE",
                "conditionParams": {},
            })
    return relations


def build_locations_from_dag(
    nodes: List[Dict],
    node_to_task_code: Dict[str, int],
) -> List[Dict[str, Any]]:
    """直接使用前端保存的 position"""
    return [
        {"taskCode": node_to_task_code[n["id"]], "x": int(n["position"]["x"]), "y": int(n["position"]["y"])}
        for n in nodes
    ]


def translate_workflow_dag(
    workflow: Any,
    components_by_id: Dict[int, Any],
    task_codes: List[int],
    datasource_lookup: Optional[Dict[int, Any]] = None,
    dqc_rules_lookup: Optional[Dict[int, List[Any]]] = None,
    portal_base_url: str = "http://portal:8000",
    service_token: str = "",
) -> Dict[str, Any]:
    """DAG 版本: Workflow → DS Process Definition payload

    DQC 任务插入逻辑（DAG 工作流）：
      组件任务 → [DQC 任务链] → 原下游任务
    """
    dag = workflow.dag_json
    nodes = dag["nodes"]
    edges = dag.get("edges", [])

    # 过滤 skip 节点及其关联边
    active_nodes = [n for n in nodes if not n.get("skip", False)]
    active_ids = {n["id"] for n in active_nodes}
    active_edges = [e for e in edges if e["source"] in active_ids and e["target"] in active_ids]

    # 环检测
    _topological_sort(active_nodes, active_edges)

    # 统计 DQC 任务数量
    dqc_count = 0
    for node in active_nodes:
        comp = components_by_id.get(node["component_id"])
        if comp and dqc_rules_lookup:
            rules = dqc_rules_lookup.get(node["component_id"], [])
            dqc_count += len([r for r in rules if getattr(r, "enabled", True)])

    comp_count = len(active_nodes)
    total_needed = comp_count + dqc_count
    if len(task_codes) < total_needed:
        raise ValueError(f"task_codes 不足: 需要 {total_needed} 个，实际 {len(task_codes)}")

    comp_codes = task_codes[:comp_count]
    dqc_codes = task_codes[comp_count:total_needed]
    dqc_code_iter = iter(dqc_codes)

    # 分配 task_code 给节点
    node_to_task_code = {}
    task_defs = []
    for i, node in enumerate(active_nodes):
        tcode = comp_codes[i]
        node_to_task_code[node["id"]] = tcode
        comp = components_by_id.get(node["component_id"])
        if not comp:
            raise ValueError(f"组件 {node['component_id']} 不存在")
        td = translate_component_to_task(
            comp, tcode,
            task_name=node.get("name") or comp.name,
            datasource_lookup=datasource_lookup,
        )
        task_defs.append(td)

    # 构建节点到 DQC task_codes 的映射
    node_to_dqc_codes: Dict[str, List[int]] = {}
    for node in active_nodes:
        comp = components_by_id.get(node["component_id"])
        if comp:
            dqc_tasks = _collect_dqc_tasks_for_component(
                comp, dqc_rules_lookup, dqc_code_iter, portal_base_url, service_token
            )
            if dqc_tasks:
                task_defs.extend(dqc_tasks)
                node_to_dqc_codes[node["id"]] = [t["code"] for t in dqc_tasks]

    # 构建 relations：有 DQC 的节点，其出边先经过 DQC 链
    node_ids = {n["id"] for n in active_nodes}
    targets_with_incoming = {e["target"] for e in active_edges if e["source"] in node_ids and e["target"] in node_ids}
    relations = []

    # Root nodes（入度为 0）
    for n in active_nodes:
        if n["id"] not in targets_with_incoming:
            relations.append({
                "preTaskCode": 0,
                "preTaskVersion": 0,
                "postTaskCode": node_to_task_code[n["id"]],
                "postTaskVersion": 0,
                "name": "",
                "conditionType": "NONE",
                "conditionParams": {},
            })

    # 普通边 + DQC 插入
    for e in active_edges:
        if e["source"] not in node_ids or e["target"] not in node_ids:
            continue
        source_code = node_to_task_code[e["source"]]
        target_code = node_to_task_code[e["target"]]

        dqc_chain = node_to_dqc_codes.get(e["source"], [])
        if dqc_chain:
            # 组件 → DQC1
            relations.append({
                "preTaskCode": source_code,
                "preTaskVersion": 0,
                "postTaskCode": dqc_chain[0],
                "postTaskVersion": 0,
                "name": "",
                "conditionType": "NONE",
                "conditionParams": {},
            })
            # DQC 链内部连接
            for j in range(1, len(dqc_chain)):
                relations.append({
                    "preTaskCode": dqc_chain[j - 1],
                    "preTaskVersion": 0,
                    "postTaskCode": dqc_chain[j],
                    "postTaskVersion": 0,
                    "name": "",
                    "conditionType": "NONE",
                    "conditionParams": {},
                })
            # 最后一个 DQC → 原下游
            relations.append({
                "preTaskCode": dqc_chain[-1],
                "preTaskVersion": 0,
                "postTaskCode": target_code,
                "postTaskVersion": 0,
                "name": "",
                "conditionType": "NONE",
                "conditionParams": {},
            })
        else:
            # 无 DQC，保持原边
            relations.append({
                "preTaskCode": source_code,
                "preTaskVersion": 0,
                "postTaskCode": target_code,
                "postTaskVersion": 0,
                "name": "",
                "conditionType": "NONE",
                "conditionParams": {},
            })

    # 为 DQC 任务生成位置（放在对应组件的右下方）
    locations = build_locations_from_dag(active_nodes, node_to_task_code)
    for node in active_nodes:
        dqc_chain = node_to_dqc_codes.get(node["id"], [])
        base_x = int(node["position"]["x"])
        base_y = int(node["position"]["y"])
        for idx, dcode in enumerate(dqc_chain):
            locations.append({
                "taskCode": dcode,
                "x": base_x + 120,
                "y": base_y + 100 + idx * 80,
            })

    return {
        "name": workflow.name,
        "description": workflow.description or "",
        "taskDefinitionJson": json.dumps(task_defs, ensure_ascii=False),
        "taskRelationJson": json.dumps(relations, ensure_ascii=False),
        "locations": json.dumps(locations, ensure_ascii=False),
    }
