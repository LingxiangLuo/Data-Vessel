-- ============================================
-- 数据中台 MVP - 数据库初始化
-- ============================================

-- 创建 DolphinScheduler 数据库
CREATE DATABASE IF NOT EXISTS dolphinscheduler DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建 OpenMetadata 数据库
CREATE DATABASE IF NOT EXISTS openmetadata DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用 portal_db
USE portal_db;

-- ============================================
-- 用户表
-- ============================================
CREATE TABLE IF NOT EXISTS sys_user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    real_name VARCHAR(64),
    email VARCHAR(128),
    phone VARCHAR(20),
    role VARCHAR(32) DEFAULT 'user' COMMENT 'admin/user',
    status TINYINT DEFAULT 1 COMMENT '1=启用 0=禁用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 数据源管理表
-- ============================================
CREATE TABLE IF NOT EXISTS data_source (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128) NOT NULL COMMENT '数据源名称',
    type VARCHAR(32) NOT NULL COMMENT 'mysql/sqlserver/postgresql',
    host VARCHAR(255) NOT NULL,
    port INT NOT NULL,
    database_name VARCHAR(128) NOT NULL,
    username VARCHAR(128),
    password VARCHAR(255),
    description TEXT,
    status TINYINT DEFAULT 1 COMMENT '1=可用 0=不可用',
    last_check_time DATETIME,
    created_by BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 组件文件夹表
-- ============================================
CREATE TABLE IF NOT EXISTS component_folder (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128) NOT NULL COMMENT '文件夹名称',
    type VARCHAR(50) NOT NULL COMMENT 'sql / python / shell / datax',
    parent_id BIGINT COMMENT '父文件夹 id',
    depth INT DEFAULT 0 COMMENT '层级: 0=一级, 1=二级, 2=三级',
    created_by BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_type (type),
    INDEX idx_parent (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 同步任务表
-- ============================================
CREATE TABLE IF NOT EXISTS sync_task (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128) NOT NULL COMMENT '任务名称',
    source_id BIGINT NOT NULL COMMENT '源数据源ID',
    target_id BIGINT NOT NULL COMMENT '目标数据源ID',
    source_table VARCHAR(128) NOT NULL,
    target_table VARCHAR(128) NOT NULL,
    sync_type VARCHAR(32) DEFAULT 'full' COMMENT 'full/incremental',
    increment_column VARCHAR(128) COMMENT '增量字段',
    schedule_cron VARCHAR(64) COMMENT '调度 cron 表达式',
    ds_workflow_id BIGINT COMMENT 'DS 工作流ID',
    status VARCHAR(32) DEFAULT 'draft' COMMENT 'draft/active/paused/error',
    last_run_time DATETIME,
    last_run_status VARCHAR(32),
    created_by BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 操作日志表
-- ============================================
CREATE TABLE IF NOT EXISTS operation_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT,
    username VARCHAR(64),
    module VARCHAR(64) COMMENT '操作模块',
    action VARCHAR(64) COMMENT '操作类型',
    detail TEXT COMMENT '操作详情',
    ip VARCHAR(64),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 初始化管理员账号 (密码: admin123)
-- ============================================
INSERT INTO sys_user (username, password, real_name, role, status)
VALUES ('admin', '$2b$12$LJ3m4ys3Lg2mYGF0YEz6YOhYK7dN4r4VHYYFK4F4VHYYFK4F4VHYY', '系统管理员', 'admin', 1);
