# 数据库设计

> **版本：** 2.0.0
> **数据库：** MySQL 5.7+
> **更新日期：** 2025-02-09

---

## 目录

- [概述](#概述)
- [数据表清单](#数据表清单)
- [表结构详解](#表结构详解)
- [索引设计](#索引设计)
- [关系图](#关系图)
- [初始化脚本](#初始化脚本)

---

## 概述

记忆系统使用 MySQL 存储持久化数据，使用 Redis 作为缓存层。

### 为什么选择 MySQL

| 特性 | 说明 |
|------|------|
| **JSON 支持** | MySQL 5.7+ 原生支持 JSON 类型，满足灵活数据存储需求 |
| **成熟稳定** | 广泛使用，社区支持完善 |
| **事务支持** | 完整的 ACID 支持，保证数据一致性 |
| **性能优异** | 读写性能良好，适合高并发场景 |
| **运维简单** | 部署和维护相对简单 |

### 命名约定

- **表名：** 小写 + 下划线（snake_case）
- **字段名：** 小写 + 下划线
- **主键：** `id`（自增整数）或 表名特定的主键
- **时间戳：** `created_at`, `updated_at`
- **外键：** `{related_table}_id`

---

## 数据表清单

| 表名 | 用途 | 主要功能 |
|------|------|----------|
| `sessions` | 会话状态 | 存储 Agent 会话状态和版本控制 |
| `user_profiles` | 用户配置 | 用户偏好、使用统计、满意度评分 |
| `conversation_history` | 对话历史 | Agent 与用户对话记录 |
| `agent_decisions` | 决策追踪 | Agent 决策记录和分析 |
| `tool_execution_feedback` | 工具反馈 | 工具执行结果和反馈 |
| `shared_workspace_memory` | 工作空间 | Agent 间数据共享 |

---

## 表结构详解

### 1. sessions 表

会话状态管理表，用于存储 Agent 会话的状态数据，支持版本控制。

#### 表结构

```sql
CREATE TABLE sessions (
    id VARCHAR(255) PRIMARY KEY COMMENT '会话ID',
    task_id VARCHAR(255) NOT NULL COMMENT '任务ID',
    user_id VARCHAR(255) COMMENT '用户ID',
    state_data JSON COMMENT '状态数据',
    version INTEGER DEFAULT 1 COMMENT '版本号',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_task_id (task_id),
    INDEX idx_user_id (user_id),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent会话状态';
```

#### 字段说明

| 字段 | 类型 | 允许 NULL | 说明 |
|------|------|-----------|------|
| `id` | VARCHAR(255) | 否 | 会话唯一标识符 |
| `task_id` | VARCHAR(255) | 否 | 关联的任务 ID |
| `user_id` | VARCHAR(255) | 是 | 关联的用户 ID |
| `state_data` | JSON | 是 | 会话状态数据 |
| `version` | INTEGER | 否 | 状态版本号，用于乐观锁 |
| `created_at` | TIMESTAMP | 否 | 创建时间 |
| `updated_at` | TIMESTAMP | 否 | 最后更新时间 |

#### 使用场景

- 存储 Agent 在执行过程中的状态快照
- 支持状态回滚和恢复
- 跟踪状态变更历史

---

### 2. user_profiles 表

用户配置表，存储用户偏好设置、使用统计和满意度评分。

#### 表结构

```sql
CREATE TABLE user_profiles (
    user_id VARCHAR(255) PRIMARY KEY COMMENT '用户ID',
    preferences JSON COMMENT '用户偏好设置',
    session_count INTEGER DEFAULT 0 COMMENT '会话计数',
    generation_count INTEGER DEFAULT 0 COMMENT '生成计数',
    satisfaction_score FLOAT COMMENT '满意度评分(0-1)',
    last_interaction_at TIMESTAMP COMMENT '最后交互时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_satisfaction (satisfaction_score),
    INDEX idx_last_interaction (last_interaction_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户配置';
```

#### 字段说明

| 字段 | 类型 | 允许 NULL | 说明 |
|------|------|-----------|------|
| `user_id` | VARCHAR(255) | 否 | 用户唯一标识符 |
| `preferences` | JSON | 是 | 用户偏好设置（语言、主题、默认选项等） |
| `session_count` | INTEGER | 否 | 用户会话总数 |
| `generation_count` | INTEGER | 否 | PPT 生成总数 |
| `satisfaction_score` | FLOAT | 是 | 平均满意度评分（0.0-1.0） |
| `last_interaction_at` | TIMESTAMP | 是 | 最后交互时间 |
| `created_at` | TIMESTAMP | 否 | 账户创建时间 |
| `updated_at` | TIMESTAMP | 否 | 最后更新时间 |

#### preferences 结构示例

```json
{
    "language": "zh-CN",
    "theme": "dark",
    "default_slides": 15,
    "style": "professional",
    "auto_save": true,
    "notifications": true
}
```

---

### 3. conversation_history 表

对话历史表，存储 Agent 与用户的对话记录。

#### 表结构

```sql
CREATE TABLE conversation_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '对话ID',
    session_id VARCHAR(255) NOT NULL COMMENT '会话ID',
    user_id VARCHAR(255) COMMENT '用户ID',
    agent_name VARCHAR(100) COMMENT 'Agent名称',
    role VARCHAR(20) NOT NULL COMMENT '角色(user/agent/system)',
    content TEXT NOT NULL COMMENT '消息内容',
    metadata JSON COMMENT '元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_session (session_id),
    INDEX idx_user (user_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话历史';
```

#### 字段说明

| 字段 | 类型 | 允许 NULL | 说明 |
|------|------|-----------|------|
| `id` | BIGINT | 否 | 对话 ID |
| `session_id` | VARCHAR(255) | 否 | 关联会话 ID |
| `user_id` | VARCHAR(255) | 是 | 关联用户 ID |
| `agent_name` | VARCHAR(100) | 是 | 响应的 Agent 名称 |
| `role` | VARCHAR(20) | 否 | 角色：user/agent/system |
| `content` | TEXT | 否 | 消息内容 |
| `metadata` | JSON | 是 | 元数据（token 数、模型等） |
| `created_at` | TIMESTAMP | 否 | 消息时间 |

---

### 4. agent_decisions 表

Agent 决策表，记录 Agent 的决策过程和结果。

#### 表结构

```sql
CREATE TABLE agent_decisions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '决策ID',
    session_id VARCHAR(255) COMMENT '会话ID',
    user_id VARCHAR(255) COMMENT '用户ID',
    agent_name VARCHAR(100) NOT NULL COMMENT 'Agent名称',
    decision_type VARCHAR(50) NOT NULL COMMENT '决策类型',
    context JSON COMMENT '决策上下文',
    selected_action VARCHAR(255) NOT NULL COMMENT '选择的动作',
    alternatives JSON COMMENT '备选方案',
    reasoning TEXT COMMENT '推理过程',
    confidence_score FLOAT COMMENT '置信度(0-1)',
    outcome VARCHAR(50) COMMENT '结果',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_session (session_id),
    INDEX idx_agent (agent_name),
    INDEX idx_decision_type (decision_type),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent决策记录';
```

#### 字段说明

| 字段 | 类型 | 允许 NULL | 说明 |
|------|------|-----------|------|
| `id` | BIGINT | 否 | 决策 ID |
| `session_id` | VARCHAR(255) | 是 | 关联会话 ID |
| `user_id` | VARCHAR(255) | 是 | 关联用户 ID |
| `agent_name` | VARCHAR(100) | 否 | Agent 名称 |
| `decision_type` | VARCHAR(50) | 否 | 决策类型 |
| `context` | JSON | 是 | 决策上下文 |
| `selected_action` | VARCHAR(255) | 否 | 选择的动作 |
| `alternatives` | JSON | 是 | 备选方案列表 |
| `reasoning` | TEXT | 是 | 推理过程说明 |
| `confidence_score` | FLOAT | 是 | 置信度（0-1） |
| `outcome` | VARCHAR(50) | 是 | 结果（success/failure/timeout） |
| `created_at` | TIMESTAMP | 否 | 决策时间 |

#### decision_type 常见值

- `tool_selection` - 工具选择
- `rerouting` - 路由决策
- `parameter_tuning` - 参数调整
- `resource_allocation` - 资源分配
- `error_handling` - 错误处理

---

### 5. tool_execution_feedback 表

工具执行反馈表，记录工具执行的结果和反馈。

#### 表结构

```sql
CREATE TABLE tool_execution_feedback (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '反馈ID',
    session_id VARCHAR(255) COMMENT '会话ID',
    agent_name VARCHAR(100) COMMENT 'Agent名称',
    tool_name VARCHAR(100) NOT NULL COMMENT '工具名称',
    input_params JSON COMMENT '输入参数',
    execution_time_ms INTEGER COMMENT '执行时间(毫秒)',
    success BOOLEAN COMMENT '是否成功',
    error_message TEXT COMMENT '错误信息',
    user_feedback INTEGER COMMENT '用户反馈(1-5)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_session (session_id),
    INDEX idx_tool (tool_name),
    INDEX idx_success (success),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工具执行反馈';
```

#### 字段说明

| 字段 | 类型 | 允许 NULL | 说明 |
|------|------|-----------|------|
| `id` | BIGINT | 否 | 反馈 ID |
| `session_id` | VARCHAR(255) | 是 | 关联会话 ID |
| `agent_name` | VARCHAR(100) | 是 | 调用的 Agent 名称 |
| `tool_name` | VARCHAR(100) | 否 | 工具名称 |
| `input_params` | JSON | 是 | 输入参数 |
| `execution_time_ms` | INTEGER | 是 | 执行时间（毫秒） |
| `success` | BOOLEAN | 是 | 是否成功 |
| `error_message` | TEXT | 是 | 错误信息 |
| `user_feedback` | INTEGER | 是 | 用户反馈评分（1-5） |
| `created_at` | TIMESTAMP | 否 | 执行时间 |

---

### 6. shared_workspace_memory 表

工作空间共享表，用于 Agent 间数据共享。

#### 表结构

```sql
CREATE TABLE shared_workspace_memory (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '共享ID',
    session_id VARCHAR(255) NOT NULL COMMENT '会话ID',
    data_type VARCHAR(100) NOT NULL COMMENT '数据类型',
    source_agent VARCHAR(100) NOT NULL COMMENT '源Agent',
    data_key VARCHAR(255) NOT NULL COMMENT '数据键',
    data_content JSON NOT NULL COMMENT '数据内容',
    target_agents JSON COMMENT '目标Agent列表',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    expires_at TIMESTAMP NOT NULL COMMENT '过期时间',
    accessed_count INTEGER DEFAULT 0 COMMENT '访问次数',
    last_accessed_at TIMESTAMP COMMENT '最后访问时间',

    INDEX idx_session_data (session_id, data_type),
    INDEX idx_expires (expires_at),
    INDEX idx_data_key (data_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作空间共享';
```

#### 字段说明

| 字段 | 类型 | 允许 NULL | 说明 |
|------|------|-----------|------|
| `id` | BIGINT | 否 | 共享 ID |
| `session_id` | VARCHAR(255) | 否 | 关联会话 ID |
| `data_type` | VARCHAR(100) | 否 | 数据类型 |
| `source_agent` | VARCHAR(100) | 否 | 源 Agent 名称 |
| `data_key` | VARCHAR(255) | 否 | 数据键 |
| `data_content` | JSON | 否 | 数据内容 |
| `target_agents` | JSON | 是 | 目标 Agent 列表（null = 所有 Agent） |
| `created_at` | TIMESTAMP | 否 | 创建时间 |
| `expires_at` | TIMESTAMP | 否 | 过期时间 |
| `accessed_count` | INTEGER | 否 | 访问次数 |
| `last_accessed_at` | TIMESTAMP | 是 | 最后访问时间 |

#### data_type 常见值

- `research_result` - 研究结果
- `framework` - 框架设计
- `content` - 内容素材
- `outline` - 大纲
- `slides` - 幻灯片数据

---

## 索引设计

### 索引策略

#### 1. 主键索引

所有表都有主键索引：
- 自增整数：`id BIGINT AUTO_INCREMENT`
- 或业务主键：`user_id VARCHAR(255)`

#### 2. 外键索引

关联查询字段添加索引：
- `session_id`
- `user_id`
- `task_id`

#### 3. 复合索引

常用的查询组合：
```sql
-- 工作空间查询
INDEX idx_session_data (session_id, data_type)

-- 时间范围查询
INDEX idx_created (created_at)
```

### 索引维护

```sql
-- 查看索引
SHOW INDEX FROM sessions;
SHOW INDEX FROM user_profiles;
SHOW INDEX FROM agent_decisions;

-- 分析表
ANALYZE TABLE sessions;
ANALYZE TABLE user_profiles;
ANALYZE TABLE agent_decisions;

-- 优化表
OPTIMIZE TABLE sessions;
OPTIMIZE TABLE agent_decisions;
```

---

## 关系图

```
┌─────────────────┐
│   user_profiles │
│   (user_id PK)  │
└────────┬────────┘
         │ 1:N
         ├─────────────────────────────┐
         │                             │
    ┌────┴────┐                  ┌─────┴─────┐
    │ sessions │                  │conversation│
    │(task_id) │                  │  _history │
    └────┬────┘                  └───────────┘
         │ 1:N
         ├──────────────┬────────────────┐
         │              │                │
    ┌────┴────┐   ┌─────┴─────┐   ┌────┴────┐
    │  agent   │   │   shared  │   │   tool  │
    │_decisions│   │_workspace │   │_feedback │
    └──────────┘   └───────────┘   └─────────┘
```

---

## 初始化脚本

### 创建数据库

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS multiagent_ppt
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE multiagent_ppt;
```

### 创建用户（可选）

```sql
-- 创建用户
CREATE USER IF NOT EXISTS 'multiagent'@'localhost'
IDENTIFIED BY 'your_password';

-- 授予权限
GRANT ALL PRIVILEGES ON multiagent_ppt.*
TO 'multiagent'@'localhost';

FLUSH PRIVILEGES;
```

### 创建表

```sql
-- 1. sessions 表
CREATE TABLE sessions (
    id VARCHAR(255) PRIMARY KEY COMMENT '会话ID',
    task_id VARCHAR(255) NOT NULL COMMENT '任务ID',
    user_id VARCHAR(255) COMMENT '用户ID',
    state_data JSON COMMENT '状态数据',
    version INTEGER DEFAULT 1 COMMENT '版本号',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_task_id (task_id),
    INDEX idx_user_id (user_id),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent会话状态';

-- 2. user_profiles 表
CREATE TABLE user_profiles (
    user_id VARCHAR(255) PRIMARY KEY COMMENT '用户ID',
    preferences JSON COMMENT '用户偏好设置',
    session_count INTEGER DEFAULT 0 COMMENT '会话计数',
    generation_count INTEGER DEFAULT 0 COMMENT '生成计数',
    satisfaction_score FLOAT COMMENT '满意度评分(0-1)',
    last_interaction_at TIMESTAMP COMMENT '最后交互时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_satisfaction (satisfaction_score),
    INDEX idx_last_interaction (last_interaction_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户配置';

-- 3. conversation_history 表
CREATE TABLE conversation_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '对话ID',
    session_id VARCHAR(255) NOT NULL COMMENT '会话ID',
    user_id VARCHAR(255) COMMENT '用户ID',
    agent_name VARCHAR(100) COMMENT 'Agent名称',
    role VARCHAR(20) NOT NULL COMMENT '角色(user/agent/system)',
    content TEXT NOT NULL COMMENT '消息内容',
    metadata JSON COMMENT '元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_session (session_id),
    INDEX idx_user (user_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话历史';

-- 4. agent_decisions 表
CREATE TABLE agent_decisions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '决策ID',
    session_id VARCHAR(255) COMMENT '会话ID',
    user_id VARCHAR(255) COMMENT '用户ID',
    agent_name VARCHAR(100) NOT NULL COMMENT 'Agent名称',
    decision_type VARCHAR(50) NOT NULL COMMENT '决策类型',
    context JSON COMMENT '决策上下文',
    selected_action VARCHAR(255) NOT NULL COMMENT '选择的动作',
    alternatives JSON COMMENT '备选方案',
    reasoning TEXT COMMENT '推理过程',
    confidence_score FLOAT COMMENT '置信度(0-1)',
    outcome VARCHAR(50) COMMENT '结果',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_session (session_id),
    INDEX idx_agent (agent_name),
    INDEX idx_decision_type (decision_type),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent决策记录';

-- 5. tool_execution_feedback 表
CREATE TABLE tool_execution_feedback (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '反馈ID',
    session_id VARCHAR(255) COMMENT '会话ID',
    agent_name VARCHAR(100) COMMENT 'Agent名称',
    tool_name VARCHAR(100) NOT NULL COMMENT '工具名称',
    input_params JSON COMMENT '输入参数',
    execution_time_ms INTEGER COMMENT '执行时间(毫秒)',
    success BOOLEAN COMMENT '是否成功',
    error_message TEXT COMMENT '错误信息',
    user_feedback INTEGER COMMENT '用户反馈(1-5)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_session (session_id),
    INDEX idx_tool (tool_name),
    INDEX idx_success (success),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工具执行反馈';

-- 6. shared_workspace_memory 表
CREATE TABLE shared_workspace_memory (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '共享ID',
    session_id VARCHAR(255) NOT NULL COMMENT '会话ID',
    data_type VARCHAR(100) NOT NULL COMMENT '数据类型',
    source_agent VARCHAR(100) NOT NULL COMMENT '源Agent',
    data_key VARCHAR(255) NOT NULL COMMENT '数据键',
    data_content JSON NOT NULL COMMENT '数据内容',
    target_agents JSON COMMENT '目标Agent列表',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    expires_at TIMESTAMP NOT NULL COMMENT '过期时间',
    accessed_count INTEGER DEFAULT 0 COMMENT '访问次数',
    last_accessed_at TIMESTAMP COMMENT '最后访问时间',

    INDEX idx_session_data (session_id, data_type),
    INDEX idx_expires (expires_at),
    INDEX idx_data_key (data_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作空间共享';
```

### 验证表创建

```sql
-- 查看所有表
SHOW TABLES;

-- 查看表结构
DESC sessions;
DESC user_profiles;
DESC agent_decisions;
```

---

**文档版本：** 2.0.0
**最后更新：** 2025-02-09
