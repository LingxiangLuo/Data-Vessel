-- ============================================
-- Demo 电商业务库 (MySQL) — 源库
-- ============================================
CREATE DATABASE IF NOT EXISTS demo_ecommerce
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE demo_ecommerce;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(64) NOT NULL,
  email VARCHAR(128),
  phone VARCHAR(20),
  gender TINYINT DEFAULT 0 COMMENT '0=未知 1=男 2=女',
  birthday DATE,
  city VARCHAR(64),
  register_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  vip_level TINYINT DEFAULT 0 COMMENT '0=普通 1=银卡 2=金卡 3=钻石',
  status TINYINT DEFAULT 1 COMMENT '0=禁用 1=启用',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_register_time (register_time),
  INDEX idx_city (city),
  INDEX idx_vip_level (vip_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 商品表
CREATE TABLE IF NOT EXISTS products (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  sku_code VARCHAR(32) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  category_id INT NOT NULL,
  category_name VARCHAR(64),
  brand VARCHAR(64),
  price DECIMAL(18,2) NOT NULL,
  cost DECIMAL(18,2),
  stock INT DEFAULT 0,
  weight_g INT,
  description TEXT,
  status TINYINT DEFAULT 1 COMMENT '0=下架 1=上架',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_category (category_id),
  INDEX idx_brand (brand),
  INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  order_no VARCHAR(32) NOT NULL UNIQUE,
  user_id BIGINT NOT NULL,
  total_amount DECIMAL(18,2) NOT NULL,
  discount_amount DECIMAL(18,2) DEFAULT 0,
  pay_amount DECIMAL(18,2) NOT NULL,
  status TINYINT DEFAULT 0 COMMENT '0=待支付 1=已支付 2=已发货 3=已完成 4=已取消',
  pay_type TINYINT DEFAULT 0 COMMENT '1=支付宝 2=微信 3=银行卡',
  address TEXT,
  city VARCHAR(64),
  province VARCHAR(64),
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  pay_time DATETIME,
  ship_time DATETIME,
  complete_time DATETIME,
  dt DATE GENERATED ALWAYS AS (DATE(create_time)) STORED,
  INDEX idx_user_id (user_id),
  INDEX idx_order_no (order_no),
  INDEX idx_status (status),
  INDEX idx_create_time (create_time),
  INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 订单明细表
CREATE TABLE IF NOT EXISTS order_items (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  order_id BIGINT NOT NULL,
  order_no VARCHAR(32) NOT NULL,
  product_id BIGINT NOT NULL,
  sku_code VARCHAR(32),
  product_name VARCHAR(255),
  quantity INT NOT NULL DEFAULT 1,
  unit_price DECIMAL(18,2) NOT NULL,
  total_price DECIMAL(18,2) NOT NULL,
  discount_price DECIMAL(18,2) DEFAULT 0,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  dt DATE GENERATED ALWAYS AS (DATE(create_time)) STORED,
  INDEX idx_order_id (order_id),
  INDEX idx_product_id (product_id),
  INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 商品类目表（维度表）
CREATE TABLE IF NOT EXISTS categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(64) NOT NULL,
  parent_id INT DEFAULT 0,
  level TINYINT DEFAULT 1,
  sort_order INT DEFAULT 0,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 插入类目数据
-- ============================================
INSERT INTO categories (id, name, parent_id, level, sort_order) VALUES
(1, '数码家电', 0, 1, 1),
(2, '手机通讯', 1, 2, 1),
(3, '电脑办公', 1, 2, 2),
(4, '摄影摄像', 1, 2, 3),
(5, '家用电器', 1, 2, 4),
(6, '服装鞋包', 0, 1, 2),
(7, '女装', 6, 2, 1),
(8, '男装', 6, 2, 2),
(9, '鞋靴', 6, 2, 3),
(10, '食品饮料', 0, 1, 3),
(11, '休闲食品', 10, 2, 1),
(12, '饮料冲调', 10, 2, 2),
(13, '生鲜水果', 10, 2, 3),
(14, '美妆个护', 0, 1, 4),
(15, '面部护肤', 14, 2, 1),
(16, '彩妆香水', 14, 2, 2),
(17, '家居日用', 0, 1, 5),
(18, '家纺', 17, 2, 1),
(19, '厨具', 17, 2, 2),
(20, '家具', 17, 2, 3);

-- ============================================
-- 插入用户数据 (10,000 条)
-- ============================================
INSERT INTO users (username, email, phone, gender, birthday, city, register_time, vip_level, status)
SELECT
  CONCAT('user', LPAD(seq, 6, '0')) AS username,
  CONCAT('user', LPAD(seq, 6, '0'), '@demo.com') AS email,
  CONCAT('1', FLOOR(3 + RAND() * 7), LPAD(FLOOR(RAND() * 1000000000), 9, '0')) AS phone,
  ELT(FLOOR(1 + RAND() * 3), 0, 1, 2) AS gender,
  DATE_SUB(CURDATE(), INTERVAL FLOOR(18 + RAND() * 50) YEAR) AS birthday,
  ELT(FLOOR(1 + RAND() * 10), '北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '重庆') AS city,
  DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 730) DAY) AS register_time,
  ELT(FLOOR(1 + RAND() * 4), 0, 0, 1, 2) AS vip_level,
  IF(RAND() > 0.05, 1, 0) AS status
FROM (
  SELECT @row := @row + 1 AS seq
  FROM (SELECT 0 UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3) t1,
       (SELECT 0 UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3) t2,
       (SELECT 0 UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3) t3,
       (SELECT 0 UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3) t4,
       (SELECT 0 UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3) t5,
       (SELECT 0 UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5) t6,
       (SELECT @row := 0) t0
) nums
WHERE seq <= 10000;

-- ============================================
-- 插入商品数据 (1,000 条)
-- ============================================
INSERT INTO products (sku_code, name, category_id, category_name, brand, price, cost, stock, weight_g, description, status)
SELECT
  CONCAT('SKU', LPAD(seq, 6, '0')) AS sku_code,
  CONCAT(
    ELT(FLOOR(1 + RAND() * 5), '优质', '精品', '热销', '新品', '限量'),
    ELT(FLOOR(1 + RAND() * 20),
      '智能手机', '笔记本电脑', '无线耳机', '机械键盘', '4K显示器',
      '连衣裙', '休闲T恤', '运动鞋', '牛仔裤', '羽绒服',
      '巧克力', '咖啡豆', '坚果礼盒', '果汁饮料', '进口牛奶',
      '面膜', '口红', '护肤套装', '香水', '眼影盘',
      '四件套', '不粘锅', '收纳箱', '台灯', '抱枕'
    )
  ) AS name,
  ELT(FLOOR(1 + RAND() * 20), 2,2,3,3,4,5,7,7,8,9,11,11,12,13,15,15,16,17,18,19) AS category_id,
  ELT(FLOOR(1 + RAND() * 5), '手机通讯', '电脑办公', '服装鞋包', '食品饮料', '美妆个护') AS category_name,
  ELT(FLOOR(1 + RAND() * 10), 'Apple', 'Samsung', 'Huawei', 'Nike', 'Adidas', 'Loreal', 'Dyson', 'Sony', 'Uniqlo', 'Nestle') AS brand,
  ROUND(50 + RAND() * 9950, 2) AS price,
  ROUND(30 + RAND() * 7000, 2) AS cost,
  FLOOR(RAND() * 5000) AS stock,
  FLOOR(100 + RAND() * 9000) AS weight_g,
  CONCAT('这是一款', ELT(FLOOR(1 + RAND() * 5), '高品质', '性价比极高', '口碑爆棚', '销量领先', '用户好评'), '的商品') AS description,
  IF(RAND() > 0.1, 1, 0) AS status
FROM (
  SELECT @row := @row + 1 AS seq
  FROM (SELECT 0 UNION ALL SELECT 1) t1,
       (SELECT 0 UNION ALL SELECT 1) t2,
       (SELECT 0 UNION ALL SELECT 1) t3,
       (SELECT 0 UNION ALL SELECT 1) t4,
       (SELECT 0 UNION ALL SELECT 1) t5,
       (SELECT 0 UNION ALL SELECT 1) t6,
       (SELECT 0 UNION ALL SELECT 1) t7,
       (SELECT 0 UNION ALL SELECT 1) t8,
       (SELECT 0 UNION ALL SELECT 1) t9,
       (SELECT @row := 0) t0
) nums
WHERE seq <= 1000;

-- ============================================
-- 插入订单数据 (50,000 条)
-- ============================================
INSERT INTO orders (order_no, user_id, total_amount, discount_amount, pay_amount, status, pay_type, address, city, province, create_time, pay_time, ship_time, complete_time)
SELECT
  CONCAT('O', DATE_FORMAT(DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 365) DAY), '%Y%m%d'), LPAD(seq, 6, '0')) AS order_no,
  FLOOR(1 + RAND() * 10000) AS user_id,
  ROUND(50 + RAND() * 4950, 2) AS total_amount,
  ROUND(RAND() * 200, 2) AS discount_amount,
  ROUND(50 + RAND() * 4750, 2) AS pay_amount,
  ELT(FLOOR(1 + RAND() * 5), 0, 1, 2, 3, 4) AS status,
  ELT(FLOOR(1 + RAND() * 4), 1, 1, 2, 3) AS pay_type,
  CONCAT(FLOOR(1 + RAND() * 100), '号', ELT(FLOOR(1 + RAND() * 5), '街道', '路', '巷', '大道', '弄')) AS address,
  ELT(FLOOR(1 + RAND() * 10), '北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '重庆') AS city,
  ELT(FLOOR(1 + RAND() * 5), '华北', '华东', '华南', '西南', '华中') AS province,
  DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 365) DAY) AS create_time,
  DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 300) DAY) AS pay_time,
  DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 200) DAY) AS ship_time,
  DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 100) DAY) AS complete_time
FROM (
  SELECT @row := @row + 1 AS seq
  FROM (SELECT 0 UNION ALL SELECT 1) t1,
       (SELECT 0 UNION ALL SELECT 1) t2,
       (SELECT 0 UNION ALL SELECT 1) t3,
       (SELECT 0 UNION ALL SELECT 1) t4,
       (SELECT 0 UNION ALL SELECT 1) t5,
       (SELECT 0 UNION ALL SELECT 1) t6,
       (SELECT 0 UNION ALL SELECT 1) t7,
       (SELECT 0 UNION ALL SELECT 1) t8,
       (SELECT 0 UNION ALL SELECT 1) t9,
       (SELECT 0 UNION ALL SELECT 1) t10,
       (SELECT 0 UNION ALL SELECT 1) t11,
       (SELECT 0 UNION ALL SELECT 1) t12,
       (SELECT 0 UNION ALL SELECT 1) t13,
       (SELECT 0 UNION ALL SELECT 1) t14,
       (SELECT 0 UNION ALL SELECT 1) t15,
       (SELECT 0 UNION ALL SELECT 1) t16,
       (SELECT @row := 0) t0
) nums
WHERE seq <= 50000;

-- ============================================
-- 插入订单明细数据 (200,000 条)
-- ============================================
INSERT INTO order_items (order_id, order_no, product_id, sku_code, product_name, quantity, unit_price, total_price, discount_price, create_time)
SELECT
  o.id AS order_id,
  o.order_no AS order_no,
  FLOOR(1 + RAND() * 1000) AS product_id,
  CONCAT('SKU', LPAD(FLOOR(1 + RAND() * 1000), 6, '0')) AS sku_code,
  ELT(FLOOR(1 + RAND() * 10), '智能手机', '笔记本电脑', '连衣裙', '运动鞋', '巧克力', '面膜', '咖啡豆', '机械键盘', '羽绒服', '口红') AS product_name,
  FLOOR(1 + RAND() * 5) AS quantity,
  ROUND(50 + RAND() * 950, 2) AS unit_price,
  ROUND((50 + RAND() * 950) * FLOOR(1 + RAND() * 5), 2) AS total_price,
  ROUND(RAND() * 50, 2) AS discount_price,
  o.create_time AS create_time
FROM orders o
JOIN (
  SELECT @row := @row + 1 AS seq
  FROM (SELECT 0 UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3) t1,
       (SELECT 0 UNION ALL SELECT 1) t2,
       (SELECT 0 UNION ALL SELECT 1) t3,
       (SELECT 0 UNION ALL SELECT 1) t4,
       (SELECT @row := 0) t0
) nums ON nums.seq <= FLOOR(1 + RAND() * 4)
WHERE o.id IS NOT NULL;
