-- MySQL数据库初始化脚本
-- 用于创建MultiAgentPPT记忆系统的数据库

-- 创建数据库
CREATE DATABASE IF NOT EXISTS multiagent_ppt
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE multiagent_ppt;

-- 显示创建结果
SELECT 'Database multiagent_ppt created successfully!' AS Result;

-- 显示数据库信息
SHOW CREATE DATABASE multiagent_ppt;

-- ===========================================
-- 注意：表结构由SQLAlchemy自动创建
-- 运行: python -m backend.agents.memory.storage.database --init
-- ===========================================

-- 授权示例（如果需要创建专用用户）
-- CREATE USER IF NOT EXISTS 'multiagent'@'localhost' IDENTIFIED BY 'your_password';
-- GRANT ALL PRIVILEGES ON multiagent_ppt.* TO 'multiagent'@'localhost';
-- FLUSH PRIVILEGES;
