-- ============================================
-- Demo 电商数仓 (PostgreSQL) — 目标库
-- ============================================

-- ODS 层 — 原始数据同步
CREATE SCHEMA IF NOT EXISTS ods;

CREATE TABLE IF NOT EXISTS ods.users (
  id BIGINT PRIMARY KEY,
  username VARCHAR(64) NOT NULL,
  email VARCHAR(128),
  phone VARCHAR(20),
  gender SMALLINT DEFAULT 0,
  birthday DATE,
  city VARCHAR(64),
  register_time TIMESTAMP,
  vip_level SMALLINT DEFAULT 0,
  status SMALLINT DEFAULT 1,
  create_time TIMESTAMP,
  update_time TIMESTAMP,
  etl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.products (
  id BIGINT PRIMARY KEY,
  sku_code VARCHAR(32) NOT NULL,
  name VARCHAR(255) NOT NULL,
  category_id INT NOT NULL,
  category_name VARCHAR(64),
  brand VARCHAR(64),
  price NUMERIC(18,2) NOT NULL,
  cost NUMERIC(18,2),
  stock INT DEFAULT 0,
  weight_g INT,
  description TEXT,
  status SMALLINT DEFAULT 1,
  create_time TIMESTAMP,
  update_time TIMESTAMP,
  etl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.orders (
  id BIGINT PRIMARY KEY,
  order_no VARCHAR(32) NOT NULL,
  user_id BIGINT NOT NULL,
  total_amount NUMERIC(18,2) NOT NULL,
  discount_amount NUMERIC(18,2) DEFAULT 0,
  pay_amount NUMERIC(18,2) NOT NULL,
  status SMALLINT DEFAULT 0,
  pay_type SMALLINT DEFAULT 0,
  address TEXT,
  city VARCHAR(64),
  province VARCHAR(64),
  create_time TIMESTAMP,
  pay_time TIMESTAMP,
  ship_time TIMESTAMP,
  complete_time TIMESTAMP,
  dt DATE,
  etl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.order_items (
  id BIGINT PRIMARY KEY,
  order_id BIGINT NOT NULL,
  order_no VARCHAR(32) NOT NULL,
  product_id BIGINT NOT NULL,
  sku_code VARCHAR(32),
  product_name VARCHAR(255),
  quantity INT NOT NULL DEFAULT 1,
  unit_price NUMERIC(18,2) NOT NULL,
  total_price NUMERIC(18,2) NOT NULL,
  discount_price NUMERIC(18,2) DEFAULT 0,
  create_time TIMESTAMP,
  dt DATE,
  etl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DWD 层 — 明细事实表
CREATE SCHEMA IF NOT EXISTS dwd;

CREATE TABLE IF NOT EXISTS dwd.order_detail (
  id BIGINT PRIMARY KEY,
  order_no VARCHAR(32) NOT NULL,
  user_id BIGINT NOT NULL,
  username VARCHAR(64),
  vip_level SMALLINT,
  city VARCHAR(64),
  product_id BIGINT NOT NULL,
  sku_code VARCHAR(32),
  product_name VARCHAR(255),
  category_name VARCHAR(64),
  brand VARCHAR(64),
  quantity INT NOT NULL,
  unit_price NUMERIC(18,2),
  total_price NUMERIC(18,2),
  discount_amount NUMERIC(18,2),
  pay_amount NUMERIC(18,2),
  order_status SMALLINT,
  pay_type SMALLINT,
  order_create_time TIMESTAMP,
  dt DATE,
  etl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DWS 层 — 轻度汇总
CREATE SCHEMA IF NOT EXISTS dws;

CREATE TABLE IF NOT EXISTS dws.user_order_stats (
  user_id BIGINT PRIMARY KEY,
  username VARCHAR(64),
  vip_level SMALLINT,
  city VARCHAR(64),
  total_orders INT DEFAULT 0,
  total_amount NUMERIC(18,2) DEFAULT 0,
  total_discount NUMERIC(18,2) DEFAULT 0,
  avg_order_amount NUMERIC(18,2) DEFAULT 0,
  last_order_time TIMESTAMP,
  etl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dws.product_sales_daily (
  dt DATE NOT NULL,
  product_id BIGINT NOT NULL,
  product_name VARCHAR(255),
  category_name VARCHAR(64),
  brand VARCHAR(64),
  sales_quantity INT DEFAULT 0,
  sales_amount NUMERIC(18,2) DEFAULT 0,
  order_count INT DEFAULT 0,
  PRIMARY KEY (dt, product_id)
);

-- ADS 层 — 应用层报表
CREATE SCHEMA IF NOT EXISTS ads;

CREATE TABLE IF NOT EXISTS ads.daily_sales_report (
  dt DATE PRIMARY KEY,
  total_orders INT DEFAULT 0,
  total_amount NUMERIC(18,2) DEFAULT 0,
  total_users INT DEFAULT 0,
  new_users INT DEFAULT 0,
  avg_order_amount NUMERIC(18,2) DEFAULT 0,
  top_city VARCHAR(64),
  top_category VARCHAR(64),
  etl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
