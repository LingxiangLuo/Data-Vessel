"""Tests for app/core/dsl_translator.py — Component/Workflow → DS JSON"""
import json
import pytest
from unittest.mock import MagicMock

from app.core.dsl_translator import (
    _datasource_type_for_ds,
    _build_datax_shell_script,
    translate_component_to_task,
    build_task_relations,
    build_locations,
    translate_workflow,
    _topological_sort,
    build_task_relations_from_dag,
    translate_workflow_dag,
)


# ---- 辅助工厂 ----

def _comp(type_: str, cfg: dict, name: str = "test", desc: str = ""):
    c = MagicMock()
    c.type = type_
    c.name = name
    c.description = desc
    c.config_json = cfg
    return c


def _workflow(steps: list, name: str = "wf", desc: str = ""):
    w = MagicMock()
    w.name = name
    w.description = desc
    w.steps_json = steps
    return w


# ---- _datasource_type_for_ds ----

def test_datasource_type_uppercase():
    assert _datasource_type_for_ds("mysql") == "MYSQL"
    assert _datasource_type_for_ds("postgresql") == "POSTGRESQL"


def test_datasource_type_empty_defaults_mysql():
    assert _datasource_type_for_ds("") == "MYSQL"
    assert _datasource_type_for_ds(None) == "MYSQL"


# ---- _build_datax_shell_script ----

def test_datax_script_uses_raw_json():
    raw = '{"job": {"content": []}}'
    script = _build_datax_shell_script({"rawJson": raw})
    assert raw in script
    assert "datax.py" in script
    assert "set -e" in script


def test_datax_script_fallback_when_no_raw():
    script = _build_datax_shell_script({"key": "val"})
    assert "datax.py" in script
    assert "job" in script


def test_datax_heredoc_uses_quoted_delimiter():
    # 'PORTAL_DATAX_EOF' 防止变量展开
    script = _build_datax_shell_script({"rawJson": "{}"})
    assert "<<'PORTAL_DATAX_EOF'" in script


# ---- translate_component_to_task ----

def test_sql_component_basic():
    comp = _comp("sql", {"datasource_id": 1, "sql": "SELECT 1"})
    task = translate_component_to_task(comp, task_code=100)
    assert task["taskType"] == "SQL"
    assert task["code"] == 100
    assert task["taskParams"]["sqlType"] == "0"  # SELECT → query


def test_sql_non_select_is_non_query():
    comp = _comp("sql", {"sql": "INSERT INTO t VALUES (1)"})
    task = translate_component_to_task(comp, task_code=101)
    assert task["taskParams"]["sqlType"] == "1"


def test_sql_datasource_lookup():
    ds = MagicMock()
    ds.type = "postgresql"
    comp = _comp("sql", {"datasource_id": 5, "sql": "SELECT 1"})
    task = translate_component_to_task(comp, task_code=102, datasource_lookup={5: ds})
    assert task["taskParams"]["type"] == "POSTGRESQL"


def test_python_component():
    comp = _comp("python", {"script": "print('hello')"})
    task = translate_component_to_task(comp, task_code=200)
    assert task["taskType"] == "PYTHON"
    assert task["taskParams"]["rawScript"] == "print('hello')"


def test_shell_component():
    comp = _comp("shell", {"script": "echo hi"})
    task = translate_component_to_task(comp, task_code=300)
    assert task["taskType"] == "SHELL"
    assert "echo hi" in task["taskParams"]["rawScript"]


def test_datax_component_becomes_shell():
    comp = _comp("datax", {"rawJson": '{"job":{}}'})
    task = translate_component_to_task(comp, task_code=400)
    assert task["taskType"] == "SHELL"
    assert task["timeoutFlag"] == "OPEN"
    assert task["timeout"] >= 5


def test_timeout_opens_flag():
    comp = _comp("python", {"script": "x=1", "timeout": 120})
    task = translate_component_to_task(comp, task_code=201)
    assert task["timeoutFlag"] == "OPEN"
    assert task["timeout"] == 2  # 120秒 → 2分钟


def test_unsupported_type_raises():
    comp = _comp("r", {})
    with pytest.raises(ValueError, match="不支持的组件类型"):
        translate_component_to_task(comp, task_code=999)


def test_task_name_override():
    comp = _comp("shell", {"script": ""}, name="original")
    task = translate_component_to_task(comp, task_code=301, task_name="override")
    assert task["name"] == "override"


# ---- build_task_relations ----

def test_empty_task_codes_returns_empty():
    assert build_task_relations([]) == []


def test_single_task_has_entry_edge():
    rels = build_task_relations([42])
    assert len(rels) == 1
    assert rels[0]["preTaskCode"] == 0
    assert rels[0]["postTaskCode"] == 42


def test_three_tasks_linear_chain():
    rels = build_task_relations([1, 2, 3])
    assert len(rels) == 3
    assert rels[0] == {"preTaskCode": 0, "preTaskVersion": 0, "postTaskCode": 1,
                       "postTaskVersion": 0, "name": "", "conditionType": "NONE", "conditionParams": {}}
    assert rels[1]["preTaskCode"] == 1 and rels[1]["postTaskCode"] == 2
    assert rels[2]["preTaskCode"] == 2 and rels[2]["postTaskCode"] == 3


# ---- build_locations ----

def test_locations_horizontal_layout():
    locs = build_locations([10, 20, 30])
    assert len(locs) == 3
    assert locs[0] == {"taskCode": 10, "x": 200, "y": 200}
    assert locs[1]["x"] == 420   # 200 + 220
    assert locs[2]["x"] == 640   # 200 + 440


# ---- translate_workflow ----

def test_translate_workflow_basic():
    comp = _comp("sql", {"sql": "SELECT 1"}, name="step1")
    wf = _workflow([{"component_id": 1, "name": "Step 1"}])
    result = translate_workflow(wf, components_by_id={1: comp}, task_codes=[100])
    task_defs = json.loads(result["taskDefinitionJson"])
    assert len(task_defs) == 1
    assert task_defs[0]["name"] == "Step 1"
    assert json.loads(result["taskRelationJson"])[0]["postTaskCode"] == 100


def test_translate_workflow_steps_codes_mismatch_raises():
    wf = _workflow([{"component_id": 1}])
    with pytest.raises(ValueError, match="不一致"):
        translate_workflow(wf, components_by_id={}, task_codes=[1, 2])


def test_translate_workflow_missing_component_raises():
    wf = _workflow([{"component_id": 99}])
    with pytest.raises(ValueError, match="组件 99 不存在"):
        translate_workflow(wf, components_by_id={}, task_codes=[1])


# ---- _topological_sort ----

def test_topological_sort_linear():
    nodes = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    edges = [{"source": "a", "target": "b"}, {"source": "b", "target": "c"}]
    order = _topological_sort(nodes, edges)
    assert order.index("a") < order.index("b") < order.index("c")


def test_topological_sort_detects_cycle():
    nodes = [{"id": "a"}, {"id": "b"}]
    edges = [{"source": "a", "target": "b"}, {"source": "b", "target": "a"}]
    with pytest.raises(ValueError, match="环"):
        _topological_sort(nodes, edges)


def test_topological_sort_parallel_branches():
    nodes = [{"id": "start"}, {"id": "a"}, {"id": "b"}, {"id": "end"}]
    edges = [
        {"source": "start", "target": "a"},
        {"source": "start", "target": "b"},
        {"source": "a", "target": "end"},
        {"source": "b", "target": "end"},
    ]
    order = _topological_sort(nodes, edges)
    assert order[0] == "start"
    assert order[-1] == "end"


# ---- translate_workflow_dag ----

def test_translate_workflow_dag_skip_nodes():
    """skip=True 的节点应被过滤，不出现在 task_defs 里"""
    comp_a = _comp("shell", {"script": "echo a"}, name="A")
    comp_b = _comp("shell", {"script": "echo b"}, name="B")

    wf = MagicMock()
    wf.name = "dag_wf"
    wf.description = ""
    wf.dag_json = {
        "nodes": [
            {"id": "n1", "component_id": 1, "position": {"x": 100, "y": 100}},
            {"id": "n2", "component_id": 2, "position": {"x": 300, "y": 100}, "skip": True},
        ],
        "edges": [{"source": "n1", "target": "n2"}],
    }

    result = translate_workflow_dag(wf, components_by_id={1: comp_a, 2: comp_b}, task_codes=[10])
    task_defs = json.loads(result["taskDefinitionJson"])
    assert len(task_defs) == 1
    assert task_defs[0]["name"] == "A"


def test_translate_workflow_dag_missing_component_raises():
    wf = MagicMock()
    wf.name = "wf"
    wf.description = ""
    wf.dag_json = {
        "nodes": [{"id": "n1", "component_id": 99, "position": {"x": 0, "y": 0}}],
        "edges": [],
    }
    with pytest.raises(ValueError, match="组件 99 不存在"):
        translate_workflow_dag(wf, components_by_id={}, task_codes=[1])
