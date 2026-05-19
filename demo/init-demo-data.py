#!/usr/bin/env python3
"""
Demo 数据初始化脚本

在 docker-compose 启动后运行，自动创建：
- 演示数据源（demo-mysql, demo-postgres）
- 演示组件（DataX/SQL/Python/Shell/Workflow）
- 演示文件夹和工作流

用法：
  python3 demo/init-demo-data.py

环境变量（从 .env 读取）：
  MYSQL_ROOT_PASSWORD - 用于 demo 数据库连接
  PORTAL_SECRET_KEY   - 用于加密数据源密码
"""

import json
import os
import sys
import time
from pathlib import Path

import requests

# 配置
BASE_URL = os.environ.get("PORTAL_BASE_URL", "http://localhost:8888")
API_URL = f"{BASE_URL}/api"
ENV_FILE = Path(__file__).parent.parent / ".env"

# Demo 数据库连接信息
DEMO_MYSQL = {
    "name": "Demo-电商业务库(MySQL)",
    "type": "mysql",
    "host": "demo-mysql",
    "port": 3306,
    "database_name": "demo_ecommerce",
    "username": "root",
    "description": "演示用电商业务库，包含 users/products/orders/order_items 等表",
}

DEMO_POSTGRES = {
    "name": "Demo-数仓(PostgreSQL)",
    "type": "postgresql",
    "host": "demo-postgres",
    "port": 5432,
    "database_name": "demo_dw",
    "username": "root",
    "description": "演示用数仓，包含 ods/dwd/dws/ads 各层表",
}


def load_env():
    """从 .env 文件加载环境变量"""
    if not ENV_FILE.exists():
        print(f"[ERROR] 找不到 .env 文件: {ENV_FILE}")
        sys.exit(1)
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v)


def encrypt_password(plain: str) -> str:
    """使用与后端相同的 Fernet 加密"""
    try:
        import base64
        import hashlib

        from cryptography.fernet import Fernet

        key = os.environ.get("PORTAL_SECRET_KEY", "")
        if not key:
            return plain
        digest = hashlib.sha256(key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(digest)
        f = Fernet(fernet_key)
        return f.encrypt(plain.encode()).decode()
    except Exception as e:
        print(f"[WARN] 密码加密失败，使用明文: {e}")
        return plain


def wait_for_api(timeout: int = 120):
    """等待后端 API 就绪"""
    print("[INFO] 等待后端 API 就绪...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{API_URL}/dashboard/stats", timeout=5)
            # 200 表示已登录，401/403 表示服务已就绪但需要登录
            if r.status_code in (200, 401, 403):
                print("[INFO] 后端 API 已就绪")
                return True
        except Exception:
            pass
        time.sleep(2)
    print("[ERROR] 后端 API 未就绪，请检查服务状态")
    return False


def login() -> str:
    """登录并获取 cookie/token"""
    password = os.environ.get("ADMIN_INIT_PASSWORD", "")
    if not password:
        password = "admin123"  # 默认密码

    r = requests.post(
        f"{API_URL}/auth/login",
        json={"username": "admin", "password": password},
        timeout=10,
    )
    if r.status_code != 200:
        print(f"[ERROR] 登录失败: {r.status_code} {r.text}")
        sys.exit(1)

    # 从响应 cookie 中获取 session
    cookies = r.cookies
    print("[INFO] 登录成功")
    return cookies


def create_datasource(cookies, ds_config: dict, password: str) -> int:
    """创建数据源，返回 id"""
    # 注意：后端会自动加密密码，这里发送明文即可
    payload = {
        **ds_config,
        "password": password,
    }
    r = requests.post(
        f"{API_URL}/datasources",
        json=payload,
        cookies=cookies,
        timeout=10,
    )
    if r.status_code == 200:
        ds_id = r.json().get("id")
        print(f"[OK] 数据源已创建: {ds_config['name']} (id={ds_id})")
        # 自动测试连接，更新状态
        r_test = requests.post(
            f"{API_URL}/datasources/{ds_id}/test",
            cookies=cookies,
            timeout=15,
        )
        if r_test.status_code == 200:
            test_res = r_test.json()
            status_label = "正常" if test_res.get("status") == 1 else "不可用"
            print(f"  [TEST] 连接测试: {test_res.get('message', '')} ({status_label})")
        else:
            print(f"  [WARN] 连接测试失败: {r_test.status_code}")
        return ds_id
    elif r.status_code == 409 or "已存在" in r.text:
        # 尝试查找已存在的数据源
        r2 = requests.get(f"{API_URL}/datasources", cookies=cookies, timeout=10)
        for item in r2.json().get("items", []):
            if item.get("name") == ds_config["name"]:
                ds_id = item["id"]
                print(f"[OK] 数据源已存在: {ds_config['name']} (id={ds_id})")
                # 更新密码（后端会自动重新加密）
                r_upd = requests.put(
                    f"{API_URL}/datasources/{ds_id}",
                    json={"password": password},
                    cookies=cookies,
                    timeout=10,
                )
                if r_upd.status_code == 200:
                    print(f"  [UPD] 密码已更新")
                # 重新测试连接
                r_test = requests.post(
                    f"{API_URL}/datasources/{ds_id}/test",
                    cookies=cookies,
                    timeout=15,
                )
                if r_test.status_code == 200:
                    test_res = r_test.json()
                    status_label = "正常" if test_res.get("status") == 1 else "不可用"
                    print(f"  [TEST] 连接测试: {test_res.get('message', '')} ({status_label})")
                return ds_id
    print(f"[ERROR] 创建数据源失败: {r.status_code} {r.text}")
    return 0


def create_folder(cookies, name: str, type_: str, parent_id: int = None) -> int:
    """创建组件文件夹"""
    payload = {"name": name, "type": type_}
    if parent_id:
        payload["parent_id"] = parent_id
    r = requests.post(
        f"{API_URL}/components/folders",
        json=payload,
        cookies=cookies,
        timeout=10,
    )
    if r.status_code == 200:
        fid = r.json().get("id")
        print(f"[OK] 文件夹已创建: {name} (id={fid})")
        return fid
    # 查找已存在
    r2 = requests.get(
        f"{API_URL}/components/folders",
        params={"type": type_},
        cookies=cookies,
        timeout=10,
    )
    for item in r2.json().get("items", []):
        if item.get("name") == name:
            return item["id"]
    return 0


def create_component(cookies, name: str, type_: str, description: str, config_json: dict, folder_id: int = None) -> int:
    """创建或更新组件（同名则更新配置）"""
    # 先查找是否已存在同名组件
    r2 = requests.get(
        f"{API_URL}/components",
        params={"type": type_, "keyword": name, "page_size": 50},
        cookies=cookies,
        timeout=10,
    )
    existing = None
    for item in r2.json().get("items", []):
        if item.get("name") == name:
            existing = item
            break

    if existing:
        cid = existing["id"]
        # 更新现有组件
        payload = {
            "name": name,
            "type": type_,
            "description": description,
            "config_json": config_json,
        }
        if folder_id:
            payload["folder_id"] = folder_id
        r = requests.put(
            f"{API_URL}/components/{cid}",
            json=payload,
            cookies=cookies,
            timeout=10,
        )
        if r.status_code == 200:
            print(f"[OK] 组件已更新: {name} (id={cid})")
            return cid
        print(f"[WARN] 更新组件失败 [{name}]: {r.status_code} {r.text}")
        return cid

    # 创建新组件
    payload = {
        "name": name,
        "type": type_,
        "description": description,
        "config_json": config_json,
    }
    if folder_id:
        payload["folder_id"] = folder_id

    r = requests.post(
        f"{API_URL}/components",
        json=payload,
        cookies=cookies,
        timeout=10,
    )
    if r.status_code == 200:
        cid = r.json().get("id")
        print(f"[OK] 组件已创建: {name} (id={cid})")
        return cid
    print(f"[ERROR] 创建组件失败 [{name}]: {r.status_code} {r.text}")
    return 0


def create_workflow(cookies, name: str, description: str, dag_json: dict, cron: str = None) -> int:
    """创建或更新工作流（同名则更新配置）"""
    # 先查找是否已存在同名工作流
    r2 = requests.get(
        f"{API_URL}/workflows",
        params={"keyword": name, "page_size": 50},
        cookies=cookies,
        timeout=10,
    )
    existing = None
    for item in r2.json().get("items", []):
        if item.get("name") == name:
            existing = item
            break

    payload = {
        "name": name,
        "description": description,
        "dag_json": dag_json,
    }
    if cron:
        payload["cron_expression"] = cron

    if existing:
        wid = existing["id"]
        r = requests.put(
            f"{API_URL}/workflows/{wid}",
            json=payload,
            cookies=cookies,
            timeout=10,
        )
        if r.status_code == 200:
            print(f"[OK] 工作流已更新: {name} (id={wid})")
            return wid
        print(f"[WARN] 更新工作流失败 [{name}]: {r.status_code} {r.text}")
        return wid

    r = requests.post(
        f"{API_URL}/workflows",
        json=payload,
        cookies=cookies,
        timeout=10,
    )
    if r.status_code == 200:
        wid = r.json().get("id")
        print(f"[OK] 工作流已创建: {name} (id={wid})")
        return wid
    print(f"[ERROR] 创建工作流失败 [{name}]: {r.status_code} {r.text}")
    return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Demo 数据初始化脚本")
    parser.add_argument("--password", "-p", default="", help="管理员密码 (默认读取 ADMIN_INIT_PASSWORD 环境变量或提示输入)")
    parser.add_argument("--base-url", "-u", default="", help="后端 API 基础 URL (默认 http://localhost:8888)")
    parser.add_argument("--skip-existing", action="store_true", help="跳过已存在的记录")
    args = parser.parse_args()

    global BASE_URL, API_URL
    if args.base_url:
        BASE_URL = args.base_url
        API_URL = f"{BASE_URL}/api"

    load_env()

    db_password = os.environ.get("MYSQL_ROOT_PASSWORD", "")
    if not db_password:
        print("[ERROR] MYSQL_ROOT_PASSWORD 未设置，请检查 .env 文件")
        sys.exit(1)

    admin_password = args.password or os.environ.get("ADMIN_INIT_PASSWORD", "")
    if not admin_password:
        import getpass
        admin_password = getpass.getpass("请输入管理员密码: ")

    os.environ["ADMIN_INIT_PASSWORD"] = admin_password

    if not wait_for_api():
        sys.exit(1)

    cookies = login()

    # ============================================================
    # 1. 创建数据源
    # ============================================================
    print("\n========== 创建数据源 ==========")
    mysql_id = create_datasource(cookies, DEMO_MYSQL, db_password)
    pg_id = create_datasource(cookies, DEMO_POSTGRES, db_password)

    if not mysql_id or not pg_id:
        print("[ERROR] 数据源创建失败，中止")
        sys.exit(1)

    # ============================================================
    # 2. 创建文件夹
    # ============================================================
    print("\n========== 创建文件夹 ==========")
    datax_folder = create_folder(cookies, "DataX-电商同步", "datax")
    sql_folder = create_folder(cookies, "SQL-数仓构建", "sql")
    py_folder = create_folder(cookies, "Python-数据清洗", "python")
    sh_folder = create_folder(cookies, "Shell-运维脚本", "shell")

    # ============================================================
    # 3. 创建 DataX 组件
    # ============================================================
    print("\n========== 创建 DataX 组件 ==========")

    # DataX 1: 用户表全量同步
    create_component(
        cookies,
        "ODS-用户表全量同步",
        "datax",
        "将 demo_ecommerce.users 全量同步到 ods.users",
        {
            "name": "ODS-用户表全量同步",
            "source_id": mysql_id,
            "target_id": pg_id,
            "source_table": "users",
            "target_table": "ods.users",
            "sync_type": "full",
            "field_mapping": [
                {"kind": "column", "src": "id", "dst": "id"},
                {"kind": "column", "src": "username", "dst": "username"},
                {"kind": "column", "src": "email", "dst": "email"},
                {"kind": "column", "src": "phone", "dst": "phone"},
                {"kind": "column", "src": "gender", "dst": "gender"},
                {"kind": "column", "src": "birthday", "dst": "birthday"},
                {"kind": "column", "src": "city", "dst": "city"},
                {"kind": "column", "src": "register_time", "dst": "register_time"},
                {"kind": "column", "src": "vip_level", "dst": "vip_level"},
                {"kind": "column", "src": "status", "dst": "status"},
                {"kind": "column", "src": "create_time", "dst": "create_time"},
                {"kind": "column", "src": "update_time", "dst": "update_time"},
            ],
            "write_mode": "insert",
            "channel": 3,
            "pre_sql": ["TRUNCATE TABLE ods.users"],
        },
        datax_folder,
    )

    # DataX 2: 商品表全量同步
    create_component(
        cookies,
        "ODS-商品表全量同步",
        "datax",
        "将 demo_ecommerce.products 全量同步到 ods.products",
        {
            "name": "ODS-商品表全量同步",
            "source_id": mysql_id,
            "target_id": pg_id,
            "source_table": "products",
            "target_table": "ods.products",
            "sync_type": "full",
            "field_mapping": [
                {"kind": "column", "src": "id", "dst": "id"},
                {"kind": "column", "src": "sku_code", "dst": "sku_code"},
                {"kind": "column", "src": "name", "dst": "name"},
                {"kind": "column", "src": "category_id", "dst": "category_id"},
                {"kind": "column", "src": "category_name", "dst": "category_name"},
                {"kind": "column", "src": "brand", "dst": "brand"},
                {"kind": "column", "src": "price", "dst": "price"},
                {"kind": "column", "src": "cost", "dst": "cost"},
                {"kind": "column", "src": "stock", "dst": "stock"},
                {"kind": "column", "src": "weight_g", "dst": "weight_g"},
                {"kind": "column", "src": "description", "dst": "description"},
                {"kind": "column", "src": "status", "dst": "status"},
                {"kind": "column", "src": "create_time", "dst": "create_time"},
                {"kind": "column", "src": "update_time", "dst": "update_time"},
            ],
            "write_mode": "insert",
            "channel": 3,
            "pre_sql": ["TRUNCATE TABLE ods.products"],
        },
        datax_folder,
    )

    # DataX 3: 订单表增量同步（按 dt）
    create_component(
        cookies,
        "ODS-订单表增量同步",
        "datax",
        "按 dt 增量同步 demo_ecommerce.orders 到 ods.orders",
        {
            "name": "ODS-订单表增量同步",
            "source_id": mysql_id,
            "target_id": pg_id,
            "source_table": "orders",
            "target_table": "ods.orders",
            "sync_type": "increment",
            "increment_column": "dt",
            "field_mapping": [
                {"kind": "column", "src": "id", "dst": "id"},
                {"kind": "column", "src": "order_no", "dst": "order_no"},
                {"kind": "column", "src": "user_id", "dst": "user_id"},
                {"kind": "column", "src": "total_amount", "dst": "total_amount"},
                {"kind": "column", "src": "discount_amount", "dst": "discount_amount"},
                {"kind": "column", "src": "pay_amount", "dst": "pay_amount"},
                {"kind": "column", "src": "status", "dst": "status"},
                {"kind": "column", "src": "pay_type", "dst": "pay_type"},
                {"kind": "column", "src": "address", "dst": "address"},
                {"kind": "column", "src": "city", "dst": "city"},
                {"kind": "column", "src": "province", "dst": "province"},
                {"kind": "column", "src": "create_time", "dst": "create_time"},
                {"kind": "column", "src": "pay_time", "dst": "pay_time"},
                {"kind": "column", "src": "ship_time", "dst": "ship_time"},
                {"kind": "column", "src": "complete_time", "dst": "complete_time"},
                {"kind": "column", "src": "dt", "dst": "dt"},
            ],
            "write_mode": "insert",
            "channel": 5,
            "where_clause": "dt = '${bizdate}'",
            "split_pk": "id",
        },
        datax_folder,
    )

    # DataX 4: 订单明细表增量同步
    create_component(
        cookies,
        "ODS-订单明细增量同步",
        "datax",
        "按 dt 增量同步 demo_ecommerce.order_items 到 ods.order_items",
        {
            "name": "ODS-订单明细增量同步",
            "source_id": mysql_id,
            "target_id": pg_id,
            "source_table": "order_items",
            "target_table": "ods.order_items",
            "sync_type": "increment",
            "increment_column": "dt",
            "field_mapping": [
                {"kind": "column", "src": "id", "dst": "id"},
                {"kind": "column", "src": "order_id", "dst": "order_id"},
                {"kind": "column", "src": "order_no", "dst": "order_no"},
                {"kind": "column", "src": "product_id", "dst": "product_id"},
                {"kind": "column", "src": "sku_code", "dst": "sku_code"},
                {"kind": "column", "src": "product_name", "dst": "product_name"},
                {"kind": "column", "src": "quantity", "dst": "quantity"},
                {"kind": "column", "src": "unit_price", "dst": "unit_price"},
                {"kind": "column", "src": "total_price", "dst": "total_price"},
                {"kind": "column", "src": "discount_price", "dst": "discount_price"},
                {"kind": "column", "src": "create_time", "dst": "create_time"},
                {"kind": "column", "src": "dt", "dst": "dt"},
            ],
            "write_mode": "insert",
            "channel": 5,
            "where_clause": "dt = '${bizdate}'",
            "split_pk": "id",
        },
        datax_folder,
    )

    # DataX 5: 带过滤条件和字段转换的同步
    create_component(
        cookies,
        "ODS-VIP用户订单同步",
        "datax",
        "仅同步 VIP 用户（vip_level > 0）的订单数据",
        {
            "name": "ODS-VIP用户订单同步",
            "source_id": mysql_id,
            "target_id": pg_id,
            "source_table": "orders",
            "target_table": "ods.orders",
            "sync_type": "full",
            "field_mapping": [
                {"kind": "column", "src": "id", "dst": "id"},
                {"kind": "column", "src": "order_no", "dst": "order_no"},
                {"kind": "column", "src": "user_id", "dst": "user_id"},
                {"kind": "column", "src": "total_amount", "dst": "total_amount"},
                {"kind": "column", "src": "pay_amount", "dst": "pay_amount"},
                {"kind": "column", "src": "status", "dst": "status"},
                {"kind": "column", "src": "city", "dst": "city"},
                {"kind": "column", "src": "create_time", "dst": "create_time"},
                {"kind": "column", "src": "dt", "dst": "dt"},
            ],
            "write_mode": "replace",
            "channel": 3,
            "where_clause": "user_id IN (SELECT id FROM users WHERE vip_level > 0)",
        },
        datax_folder,
    )

    # ============================================================
    # 4. 创建 SQL 组件
    # ============================================================
    print("\n========== 创建 SQL 组件 ==========")

    create_component(
        cookies,
        "DWD-订单明细宽表构建",
        "sql",
        "关联 ODS 层订单、用户、商品数据，构建 DWD 订单明细宽表",
        {
            "datasource_id": pg_id,
            "sql": """
INSERT INTO dwd.order_detail (
    id, order_no, user_id, username, vip_level, city,
    product_id, sku_code, product_name, category_name, brand,
    quantity, unit_price, total_price, discount_amount, pay_amount,
    order_status, pay_type, order_create_time, dt
)
SELECT
    oi.id,
    o.order_no,
    o.user_id,
    u.username,
    u.vip_level,
    u.city,
    oi.product_id,
    oi.sku_code,
    oi.product_name,
    p.category_name,
    p.brand,
    oi.quantity,
    oi.unit_price,
    oi.total_price,
    o.discount_amount,
    o.pay_amount,
    o.status AS order_status,
    o.pay_type,
    o.create_time AS order_create_time,
    o.dt
FROM ods.orders o
JOIN ods.order_items oi ON o.id = oi.order_id
LEFT JOIN ods.users u ON o.user_id = u.id
LEFT JOIN ods.products p ON oi.product_id = p.id
WHERE o.dt = '${bizdate}'
ON CONFLICT (id) DO UPDATE SET
    username = EXCLUDED.username,
    vip_level = EXCLUDED.vip_level,
    city = EXCLUDED.city,
    category_name = EXCLUDED.category_name,
    brand = EXCLUDED.brand,
    pay_amount = EXCLUDED.pay_amount,
    order_status = EXCLUDED.order_status,
    etl_time = CURRENT_TIMESTAMP;
            """.strip(),
            "timeout": 300,
        },
        sql_folder,
    )

    create_component(
        cookies,
        "DWS-用户订单统计",
        "sql",
        "按用户汇总订单统计指标",
        {
            "datasource_id": pg_id,
            "sql": """
INSERT INTO dws.user_order_stats (
    user_id, username, vip_level, city,
    total_orders, total_amount, total_discount, avg_order_amount, last_order_time
)
SELECT
    o.user_id,
    MAX(u.username) AS username,
    MAX(u.vip_level) AS vip_level,
    MAX(u.city) AS city,
    COUNT(DISTINCT o.id) AS total_orders,
    SUM(o.pay_amount) AS total_amount,
    SUM(o.discount_amount) AS total_discount,
    ROUND(AVG(o.pay_amount), 2) AS avg_order_amount,
    MAX(o.create_time) AS last_order_time
FROM ods.orders o
LEFT JOIN ods.users u ON o.user_id = u.id
WHERE o.dt = '${bizdate}'
GROUP BY o.user_id
ON CONFLICT (user_id) DO UPDATE SET
    total_orders = EXCLUDED.total_orders,
    total_amount = EXCLUDED.total_amount,
    total_discount = EXCLUDED.total_discount,
    avg_order_amount = EXCLUDED.avg_order_amount,
    last_order_time = EXCLUDED.last_order_time,
    etl_time = CURRENT_TIMESTAMP;
            """.strip(),
            "timeout": 300,
        },
        sql_folder,
    )

    create_component(
        cookies,
        "DWS-商品日销售统计",
        "sql",
        "按商品和日期汇总销售统计",
        {
            "datasource_id": pg_id,
            "sql": """
INSERT INTO dws.product_sales_daily (
    dt, product_id, product_name, category_name, brand,
    sales_quantity, sales_amount, order_count
)
SELECT
    o.dt,
    oi.product_id,
    MAX(oi.product_name) AS product_name,
    MAX(p.category_name) AS category_name,
    MAX(p.brand) AS brand,
    SUM(oi.quantity) AS sales_quantity,
    SUM(oi.total_price) AS sales_amount,
    COUNT(DISTINCT oi.order_id) AS order_count
FROM ods.orders o
JOIN ods.order_items oi ON o.id = oi.order_id
LEFT JOIN ods.products p ON oi.product_id = p.id
WHERE o.dt = '${bizdate}'
GROUP BY o.dt, oi.product_id
ON CONFLICT (dt, product_id) DO UPDATE SET
    sales_quantity = EXCLUDED.sales_quantity,
    sales_amount = EXCLUDED.sales_amount,
    order_count = EXCLUDED.order_count,
    etl_time = CURRENT_TIMESTAMP;
            """.strip(),
            "timeout": 300,
        },
        sql_folder,
    )

    create_component(
        cookies,
        "ADS-日报表生成",
        "sql",
        "生成每日销售汇总报表",
        {
            "datasource_id": pg_id,
            "sql": """
INSERT INTO ads.daily_sales_report (
    dt, total_orders, total_amount, total_users, new_users,
    avg_order_amount, top_city, top_category
)
WITH daily_stats AS (
    SELECT
        dt,
        COUNT(DISTINCT id) AS total_orders,
        SUM(pay_amount) AS total_amount,
        COUNT(DISTINCT user_id) AS total_users
    FROM ods.orders
    WHERE dt = '${bizdate}'
    GROUP BY dt
),
new_user_stats AS (
    SELECT COUNT(*) AS new_users
    FROM ods.users
    WHERE DATE(register_time) = '${bizdate}'
),
top_city AS (
    SELECT city
    FROM ods.orders
    WHERE dt = '${bizdate}'
    GROUP BY city
    ORDER BY COUNT(*) DESC
    LIMIT 1
),
top_category AS (
    SELECT p.category_name
    FROM ods.order_items oi
    JOIN ods.products p ON oi.product_id = p.id
    JOIN ods.orders o ON oi.order_id = o.id
    WHERE o.dt = '${bizdate}'
    GROUP BY p.category_name
    ORDER BY SUM(oi.total_price) DESC
    LIMIT 1
)
SELECT
    d.dt,
    d.total_orders,
    d.total_amount,
    d.total_users,
    n.new_users,
    ROUND(d.total_amount / NULLIF(d.total_orders, 0), 2) AS avg_order_amount,
    tc.city AS top_city,
    tcat.category_name AS top_category
FROM daily_stats d
CROSS JOIN new_user_stats n
CROSS JOIN top_city tc
CROSS JOIN top_category tcat
ON CONFLICT (dt) DO UPDATE SET
    total_orders = EXCLUDED.total_orders,
    total_amount = EXCLUDED.total_amount,
    total_users = EXCLUDED.total_users,
    new_users = EXCLUDED.new_users,
    avg_order_amount = EXCLUDED.avg_order_amount,
    top_city = EXCLUDED.top_city,
    top_category = EXCLUDED.top_category,
    etl_time = CURRENT_TIMESTAMP;
            """.strip(),
            "timeout": 300,
        },
        sql_folder,
    )

    # ============================================================
    # 5. 创建 Python 组件
    # ============================================================
    print("\n========== 创建 Python 组件 ==========")

    create_component(
        cookies,
        "PY-数据质量检查",
        "python",
        "检查 ODS 层数据质量：空值率、重复率、异常值",
        {
            "script": """
import json
import sys

# 模拟数据质量检查结果
quality_report = {
    "check_time": "${cyctime}",
    "tables_checked": ["ods.users", "ods.products", "ods.orders", "ods.order_items"],
    "issues": [],
    "score": 95
}

# 检查用户表空值
print("[CHECK] 检查 users 表邮箱空值率...")
# 实际场景下这里会连接数据库执行 SQL 查询
# SELECT COUNT(*) - COUNT(email) * 100.0 / COUNT(*) FROM ods.users

# 检查订单金额异常值
print("[CHECK] 检查 orders 表金额异常值...")
# SELECT COUNT(*) FROM ods.orders WHERE pay_amount <= 0 OR total_amount <= 0

# 检查订单明细重复
print("[CHECK] 检查 order_items 重复记录...")
# SELECT order_id, product_id, COUNT(*) FROM ods.order_items GROUP BY order_id, product_id HAVING COUNT(*) > 1

quality_report["issues"] = [
    {"table": "ods.users", "column": "email", "issue": "空值率 2.3%", "severity": "low"},
    {"table": "ods.orders", "column": "pay_amount", "issue": "异常值 5条", "severity": "medium"},
]

print(json.dumps(quality_report, indent=2, ensure_ascii=False))
print("[DONE] 数据质量检查完成，综合评分: 95")
            """.strip(),
            "timeout": 300,
        },
        py_folder,
    )

    create_component(
        cookies,
        "PY-用户画像标签生成",
        "python",
        "基于订单数据生成用户消费画像标签",
        {
            "script": """
import json

print("[START] 用户画像标签生成任务")
print("[INFO] 业务日期: ${bizdate}")

# 模拟标签生成逻辑
# 实际场景下会连接数仓执行复杂计算

tags = {
    "high_value_users": {
        "description": "高价值用户（累计消费 > 10000）",
        "count": 120,
        "criteria": "total_amount > 10000"
    },
    "loyal_users": {
        "description": "忠诚用户（订单数 > 10）",
        "count": 850,
        "criteria": "total_orders > 10"
    },
    "churn_risk": {
        "description": "流失风险用户（30天未下单）",
        "count": 3200,
        "criteria": "last_order_time < NOW() - INTERVAL '30 days'"
    },
    "new_users": {
        "description": "新注册用户（7天内）",
        "count": 180,
        "criteria": "register_time > NOW() - INTERVAL '7 days'"
    }
}

print(json.dumps(tags, indent=2, ensure_ascii=False))
print("[DONE] 用户画像标签生成完成")
            """.strip(),
            "timeout": 300,
        },
        py_folder,
    )

    # ============================================================
    # 6. 创建 Shell 组件
    # ============================================================
    print("\n========== 创建 Shell 组件 ==========")

    create_component(
        cookies,
        "SH-日志清理",
        "shell",
        "清理 7 天前的 DolphinScheduler 执行日志",
        {
            "script": """
#!/bin/bash
set -e

echo "[START] 日志清理任务"
echo "[INFO] 当前时间: $(date '+%Y-%m-%d %H:%M:%S')"

# 清理 DS 日志目录（保留 7 天）
LOG_DIR="/opt/dolphinscheduler/logs"
if [ -d "$LOG_DIR" ]; then
    echo "[INFO] 清理 $LOG_DIR 下 7 天前的日志..."
    find $LOG_DIR -type f -name "*.log" -mtime +7 | head -20 | while read f; do
        echo "  DELETE: $f"
        rm -f "$f"
    done
    echo "[OK] 日志清理完成"
else
    echo "[WARN] 日志目录不存在: $LOG_DIR"
fi

# 统计清理后磁盘使用
echo "[INFO] 磁盘使用情况:"
df -h | grep -E '(Filesystem|/opt|/var)'

echo "[DONE] 日志清理任务完成"
            """.strip(),
            "timeout": 300,
        },
        sh_folder,
    )

    # ============================================================
    # 7. 创建工作流
    # ============================================================
    print("\n========== 创建工作流 ==========")

    # 先获取刚才创建的组件 ID
    r = requests.get(
        f"{API_URL}/components",
        params={"page": 1, "page_size": 100},
        cookies=cookies,
        timeout=10,
    )
    comps = {c["name"]: c["id"] for c in r.json().get("items", [])}

    def cid(name):
        return comps.get(name, 0)

    # 工作流 1: ODS 层同步
    create_workflow(
        cookies,
        "WF-ODS层每日同步",
        "每日将业务库数据同步到 ODS 层",
        {
            "nodes": [
                {"id": "n1", "component_id": cid("ODS-用户表全量同步"), "name": "用户表同步", "position": {"x": 100, "y": 100}},
                {"id": "n2", "component_id": cid("ODS-商品表全量同步"), "name": "商品表同步", "position": {"x": 300, "y": 100}},
                {"id": "n3", "component_id": cid("ODS-订单表增量同步"), "name": "订单表同步", "position": {"x": 100, "y": 250}},
                {"id": "n4", "component_id": cid("ODS-订单明细增量同步"), "name": "订单明细同步", "position": {"x": 300, "y": 250}},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n3"},
                {"id": "e2", "source": "n2", "target": "n4"},
            ],
        },
        "0 2 * * *",  # 每天凌晨 2 点
    )

    # 工作流 2: DWD/DWS/ADS 层构建
    create_workflow(
        cookies,
        "WF-数仓分层构建",
        "基于 ODS 数据构建 DWD、DWS、ADS 层",
        {
            "nodes": [
                {"id": "n1", "component_id": cid("DWD-订单明细宽表构建"), "name": "DWD宽表", "position": {"x": 100, "y": 100}},
                {"id": "n2", "component_id": cid("DWS-用户订单统计"), "name": "用户统计", "position": {"x": 100, "y": 250}},
                {"id": "n3", "component_id": cid("DWS-商品日销售统计"), "name": "商品统计", "position": {"x": 300, "y": 250}},
                {"id": "n4", "component_id": cid("ADS-日报表生成"), "name": "日报表", "position": {"x": 200, "y": 400}},
                {"id": "n5", "component_id": cid("PY-数据质量检查"), "name": "质量检查", "position": {"x": 450, "y": 100}},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n1", "target": "n3"},
                {"id": "e3", "source": "n2", "target": "n4"},
                {"id": "e4", "source": "n3", "target": "n4"},
            ],
        },
        "30 2 * * *",  # 每天凌晨 2:30
    )

    print("\n========== Demo 数据初始化完成 ==========")
    print(f"数据源: Demo-电商业务库(MySQL) id={mysql_id}, Demo-数仓(PostgreSQL) id={pg_id}")
    print(f"组件: {len(comps)} 个已创建")
    print("工作流: 2 个已创建（ODS同步 + 数仓构建）")


if __name__ == "__main__":
    main()
