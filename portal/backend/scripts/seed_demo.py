"""一次性测试数据注入脚本 (Phase 13 观星台)

跑法 (从本机):
    python3 portal/backend/scripts/seed_demo.py

会做:
  1. 清理历史脏数据 (workflow / component / datasource 中名字带 e2e_/demo 的)
  2. 创建 2 个真实数据源
  3. 创建 5 个 Component (sql/python/shell/datax 覆盖)
  4. 全部发布
  5. 创建 3 个 Workflow
  6. 发布 + 触发若干次运行 (生成 DS 历史)
"""
import json
import sys
import time
import urllib.request
import urllib.error

import os

BASE = os.environ.get("PORTAL_BASE_URL", "http://localhost")


def call(method: str, path: str, token: str | None = None, body: dict | None = None) -> dict:
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body_text = e.read().decode() if e.fp else ""
        print(f"  ✗ {method} {path} → {e.code} {body_text[:200]}")
        return {"_error": e.code, "_body": body_text}


def login() -> str:
    r = call("POST", "/api/auth/login", body={"username": "admin", "password": "admin123"})
    return r["access_token"]


def cleanup(token: str):
    print("\n=== 1) 清理旧测试数据 ===")
    # Workflows
    wfs = call("GET", "/api/workflows?page=1&page_size=100", token).get("items", [])
    for w in wfs:
        wid = w["id"]
        status = w["status"]
        if status == "online":
            call("POST", f"/api/workflows/{wid}/offline", token)
        call("DELETE", f"/api/workflows/{wid}", token)
        print(f"  ✓ 删除工作流 {wid} {w['name']}")

    # Components
    comps = call("GET", "/api/components?page=1&page_size=100", token).get("items", [])
    for c in comps:
        cid = c["id"]
        if c["status"] == "online":
            call("POST", f"/api/components/{cid}/offline", token)
        call("DELETE", f"/api/components/{cid}", token)
        print(f"  ✓ 删除组件 {cid} {c['name']}")

    # Datasources (保留 id=2 那个空的)
    dss = call("GET", "/api/datasources?page=1&page_size=100", token).get("items", [])
    for d in dss:
        did = d["id"]
        # 只删除我们种过的(name 非空且 != id=2 那个)
        if d.get("name") and d.get("name") in ("PortalMySQL", "AppRedis-Demo"):
            call("DELETE", f"/api/datasources/{did}", token)
            print(f"  ✓ 删除数据源 {did} {d['name']}")


def create_datasources(token: str) -> dict:
    print("\n=== 2) 创建数据源 ===")
    out = {}

    ds1 = call("POST", "/api/datasources", token, body={
        "name": "PortalMySQL",
        "type": "mysql",
        "host": "mysql",
        "port": 3306,
        "database_name": "portal_db",
        "username": "root",
        "password": os.environ.get("MYSQL_ROOT_PASSWORD", "changeme"),
        "description": "Portal 元数据库 (内网)",
    })
    if "id" in ds1:
        out["mysql"] = ds1["id"]
        print(f"  ✓ MySQL 数据源 id={ds1['id']}")

    return out


def create_components(token: str, ds_map: dict) -> dict:
    print("\n=== 3) 创建 Component (覆盖 sql/python/shell/datax) ===")
    out = {}

    components = [
        {
            "name": "extract_users_from_portal",
            "type": "sql",
            "description": "从 Portal MySQL 抽取用户表",
            "config_json": {
                "sql": "SELECT id, username, created_at FROM sys_user LIMIT 100;",
                "timeout": 300,
                "datasource_id": ds_map.get("mysql"),
            },
        },
        {
            "name": "transform_user_data",
            "type": "python",
            "description": "Python 数据处理示例 (打印当前时间和环境)",
            "config_json": {
                "script": "import datetime\nprint('[transform] starting at', datetime.datetime.now())\nprint('[transform] done')",
                "timeout": 120,
            },
        },
        {
            "name": "cleanup_temp_files",
            "type": "shell",
            "description": "Shell 清理临时文件示例",
            "config_json": {
                "script": "echo '[cleanup] start' && date && echo '[cleanup] done'",
                "timeout": 60,
            },
        },
        {
            "name": "datax_user_sync_demo",
            "type": "datax",
            "description": "DataX 用户表同步示例(streamreader→streamwriter)",
            "config_json": {
                "timeout": 600,
                "rawJson": json.dumps({
                    "job": {
                        "content": [{
                            "reader": {
                                "name": "streamreader",
                                "parameter": {
                                    "sliceRecordCount": 5,
                                    "column": [
                                        {"type": "string", "value": "demo-user"},
                                        {"type": "long",   "value": 100},
                                    ],
                                },
                            },
                            "writer": {
                                "name": "streamwriter",
                                "parameter": {"print": True, "encoding": "UTF-8"},
                            },
                        }],
                        "setting": {"speed": {"channel": 1}},
                    },
                }, ensure_ascii=False, indent=2),
            },
        },
        {
            "name": "alert_summary_log",
            "type": "shell",
            "description": "工作流末尾汇总日志",
            "config_json": {
                "script": "echo '[summary] pipeline finished' && date && echo 'OK'",
                "timeout": 60,
            },
        },
    ]

    for cdef in components:
        r = call("POST", "/api/components", token, body=cdef)
        if "id" in r:
            cid = r["id"]
            out[cdef["name"]] = cid
            # test + publish
            call("POST", f"/api/components/{cid}/test", token)
            call("POST", f"/api/components/{cid}/publish", token)
            print(f"  ✓ {cdef['type']:<6} id={cid} {cdef['name']}  → online")

    return out


def create_workflows(token: str, comp_map: dict) -> dict:
    print("\n=== 4) 创建并发布 Workflow ===")
    out = {}

    workflows = [
        {
            "name": "daily_user_etl",
            "description": "每日用户全量同步 (DataX → Python → Shell)",
            "cron_expression": "0 0 2 * * ?",
            "steps": [
                {"component_id": comp_map["datax_user_sync_demo"],   "name": "datax_extract"},
                {"component_id": comp_map["transform_user_data"],     "name": "transform"},
                {"component_id": comp_map["alert_summary_log"],       "name": "alert"},
            ],
        },
        {
            "name": "nightly_cleanup",
            "description": "每晚清理临时文件",
            "cron_expression": "0 30 23 * * ?",
            "steps": [
                {"component_id": comp_map["cleanup_temp_files"], "name": "cleanup"},
                {"component_id": comp_map["alert_summary_log"],  "name": "alert"},
            ],
        },
        {
            "name": "user_data_export",
            "description": "用户数据导出 (SQL 抽取 + Python 加工)",
            "cron_expression": None,
            "steps": [
                {"component_id": comp_map["extract_users_from_portal"], "name": "sql_extract"},
                {"component_id": comp_map["transform_user_data"],        "name": "transform"},
            ],
        },
    ]

    for wdef in workflows:
        r = call("POST", "/api/workflows", token, body=wdef)
        if "id" in r:
            wid = r["id"]
            out[wdef["name"]] = wid
            call("POST", f"/api/workflows/{wid}/test", token)
            pub = call("POST", f"/api/workflows/{wid}/publish", token)
            pd = pub.get("ds_process_code")
            print(f"  ✓ id={wid:<3} {wdef['name']}  → online  ds_process_code={pd}")

    return out


def trigger_runs(token: str, wf_map: dict):
    print("\n=== 5) 触发若干次运行(填充 DS 历史)===")
    runs = [
        ("daily_user_etl", 2),
        ("nightly_cleanup", 2),
        ("user_data_export", 1),
    ]
    for name, n in runs:
        wid = wf_map.get(name)
        if not wid:
            continue
        for i in range(n):
            r = call("POST", f"/api/workflows/{wid}/run", token)
            inst = r.get("ds_response")
            print(f"  ▶ {name} run#{i+1} instance={inst}")
            time.sleep(1.0)


def main():
    token = login()
    print(f"Token len={len(token)}")
    cleanup(token)
    ds_map = create_datasources(token)
    comp_map = create_components(token, ds_map)
    wf_map = create_workflows(token, comp_map)
    trigger_runs(token, wf_map)
    print("\n=== Done ===")


if __name__ == "__main__":
    main()
