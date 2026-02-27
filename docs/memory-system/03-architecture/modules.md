# 模块说明

> **版本：** 2.0.0
> **更新日期：** 2025-02-09

---

## 目录

- [目录结构](#目录结构)
- [核心层](#核心层-core)
- [服务层](#服务层-services)
- [存储层](#存储层-storage)
- [工具层](#工具层-utils)
- [文件清单](#文件清单)
- [依赖关系](#依赖关系)

---

## 目录结构

```
backend/agents/memory/
├── __init__.py                      # 公开 API 导出
│
├── memory_aware_agent.py            # Agent 基类
├── state_bound_manager.py           # 状态绑定管理器
│
├── core/                            # 核心模块
│   ├── __init__.py
│   ├── memory_system.py             # 系统入口
│   └── config.py                    # 配置管理
│
├── services/                        # 业务服务层
│   ├── __init__.py
│   ├── base_service.py              # 服务基类
│   ├── user_preference_service.py   # 用户偏好服务
│   ├── decision_service.py          # 决策追踪服务
│   └── workspace_service.py         # 工作空间服务
│
├── storage/                         # 数据持久化层
│   ├── __init__.py
│   ├── database.py                  # 数据库连接
│   ├── redis_cache.py               # Redis 缓存
│   └── models/                      # 模型定义
│       ├── __init__.py
│       ├── base.py                  # 基础模型
│       ├── session.py               # 会话模型
│       ├── user_profile.py          # 用户配置模型
│       ├── conversation.py          # 对话历史模型
│       ├── agent_decision.py        # Agent决策模型
│       ├── tool_feedback.py         # 工具反馈模型
│       └── workspace.py             # 工作空间模型
│
├── utils/                           # 工具函数
│   ├── __init__.py
│   ├── scope_helper.py              # 作用域推断
│   ├── context_extractor.py         # 上下文提取
│   └── memory_optimizer.py          # 记忆优化
│
├── tests/                           # 测试模块
│   ├── __init__.py
│   └── test_memory_integration.py   # 集成测试
│
└── init_mysql.sql                   # MySQL 初始化脚本
```

---

## 核心层 (core/)

核心层提供记忆系统的基础组件和入口点。

### MemoryAwareAgent

**文件：** `memory_aware_agent.py`

所有需要记忆功能的 Agent 的基类。通过组合模式提供记忆操作。

**职责：**
- 管理 StateBoundMemoryManager 的生命周期
- 提供便捷的记忆操作接口
- 自动从 LangChain 状态提取上下文

**主要方法：**
- `_get_memory(state)` - 从状态初始化记忆管理器
- `remember(key, value)` - 存储信息
- `recall(key)` - 检索信息
- `forget(key)` - 删除信息
- `share_data(...)` - 共享数据到工作空间

### StateBoundMemoryManager

**文件：** `state_bound_manager.py`

桥接 LangChain 状态和记忆系统的关键组件。

**职责：**
- 从状态提取上下文（task_id、user_id、session_id）
- 作用域推断和路由
- 调用底层服务（用户偏好、决策追踪、工作空间）

**主要方法：**
- `remember(key, value, scope)` - 存储记忆
- `recall(key, scope)` - 检索记忆
- `share_data(...)` - 共享数据
- `get_user_preferences()` - 获取用户偏好
- `record_decision(...)` - 记录决策

### MemorySystem

**文件：** `core/memory_system.py`

记忆系统的统一入口点。

**职责：**
- 管理所有服务实例
- 提供初始化和关闭方法
- 健康检查和统计信息

**主要方法：**
- `initialize()` - 初始化系统
- `shutdown()` - 关闭系统
- `health_check()` - 健康检查
- `get_statistics()` - 获取统计信息

### MemoryConfig

**文件：** `core/config.py`

配置管理类。

**职责：**
- 管理所有配置参数
- 从环境变量加载配置
- 验证配置有效性

**配置项：**
- 数据库 URL（MySQL）
- Redis URL
- 功能开关（用户偏好、决策追踪、工作空间）
- 性能参数（缓存大小、TTL、连接池）
- 日志配置

---

## 服务层 (services/)

服务层提供业务逻辑的实现。

### BaseService

**文件：** `services/base_service.py`

所有服务的基类，提供通用的数据库和缓存操作。

**职责：**
- 数据库会话管理
- Redis 缓存操作
- 通用 CRUD 操作

### UserPreferenceService

**文件：** `services/user_preference_service.py`

**职责：**
- 管理用户偏好设置
- 跟踪使用统计
- 记录满意度评分

**主要方法：**
- `get_user_preferences(user_id)` - 获取偏好
- `update_preferences(user_id, preferences)` - 更新偏好
- `increment_session_count(user_id)` - 增加会话计数
- `increment_generation_count(user_id)` - 增加生成计数
- `update_satisfaction_score(user_id, score)` - 更新满意度

### DecisionService

**文件：** `services/decision_service.py`

**职责：**
- 记录 Agent 决策
- 分析决策模式
- 提供决策优化建议

**主要方法：**
- `record_decision(...)` - 记录决策
- `get_decision_history(agent_name)` - 获取决策历史
- `analyze_decisions(session_id)` - 分析决策

### WorkspaceService

**文件：** `services/workspace_service.py`

**职责：**
- 管理 Agent 间的数据共享
- TTL 管理
- 访问控制

**主要方法：**
- `share_data(...)` - 共享数据
- `get_shared_data(...)` - 获取共享数据
- `list_shared_data(...)` - 列出共享数据
- `cleanup_expired()` - 清理过期数据

---

## 存储层 (storage/)

存储层负责数据持久化和缓存管理。

### DatabaseManager

**文件：** `storage/database.py`

**职责：**
- MySQL 连接管理
- 连接池管理
- 健康检查

**主要方法：**
- `health_check()` - 检查数据库连接
- `SessionLocal()` - 创建数据库会话

### RedisCache

**文件：** `storage/redis_cache.py`

**职责：**
- Redis 客户端封装
- L2 缓存操作
- 错误处理

**主要方法：**
- `is_available()` - 检查 Redis 是否可用
- `get/set/delete` - 缓存操作
- `get_user_preferences/set_user_preferences` - 用户偏好缓存

### 数据模型 (storage/models/)

| 模型文件 | 表名 | 用途 |
|----------|------|------|
| `base.py` | - | 所有模型的基类 |
| `session.py` | `sessions` | 会话状态管理，版本控制 |
| `user_profile.py` | `user_profiles` | 用户偏好、使用统计 |
| `conversation.py` | `conversation_history` | 对话历史记录 |
| `agent_decision.py` | `agent_decisions` | Agent 决策追踪 |
| `tool_feedback.py` | `tool_execution_feedback` | 工具执行反馈 |
| `workspace.py` | `shared_workspace_memory` | 工作空间共享 |

---

## 工具层 (utils/)

工具层提供辅助功能。

### scope_helper.py

**作用：**
- 从 key 推断记忆作用域
- 作用域验证
- 作用域 ID 获取

**主要函数：**
- `infer_scope_from_key(key)` - 推断作用域
- `get_scope_id(scope, task_id, user_id, session_id)` - 获取作用域 ID
- `validate_scope(scope)` - 验证作用域

### context_extractor.py

**作用：**
- 从 LangChain 状态提取上下文
- 上下文对象构建

**主要函数：**
- `extract_context_from_state(state)` - 提取上下文

### memory_optimizer.py

**作用：**
- 记忆重要性计算
- 记忆优化建议

**主要函数：**
- `calculate_memory_importance(access_count, last_accessed, age_days)` - 计算重要性
- `get_cleanup_recommendations()` - 获取清理建议

---

## 文件清单

| 文件 | 行数 | 职责 | 主要类/函数 |
|------|------|------|-------------|
| `__init__.py` | 131 | 公开 API 导出 | 所有公开接口 |
| `memory_aware_agent.py` | 309 | Agent 基类 | `MemoryAwareAgent`, `LangGraphAgentMixin` |
| `state_bound_manager.py` | 595 | 状态绑定管理器 | `StateBoundMemoryManager` |
| `core/memory_system.py` | 282 | 系统入口 | `MemorySystem`, `initialize_memory_system` |
| `core/config.py` | 237 | 配置管理 | `MemoryConfig`, `load_config_from_env` |
| `services/base_service.py` | ~150 | 服务基类 | `BaseService` |
| `services/user_preference_service.py` | 341 | 用户偏好服务 | `UserPreferenceService` |
| `services/decision_service.py` | ~300 | 决策服务 | `DecisionService` |
| `services/workspace_service.py` | ~300 | 工作空间服务 | `WorkspaceService` |
| `storage/database.py` | ~200 | 数据库管理 | `DatabaseManager` |
| `storage/redis_cache.py` | ~250 | Redis 缓存 | `RedisCache` |
| `storage/models/base.py` | ~100 | 基础模型 | `Base`, `BaseModel` |
| `storage/models/session.py` | ~100 | 会话模型 | `Session` |
| `storage/models/user_profile.py` | ~150 | 用户模型 | `UserProfile` |
| `storage/models/conversation.py` | ~80 | 对话模型 | `ConversationHistory` |
| `storage/models/agent_decision.py` | ~120 | 决策模型 | `AgentDecision` |
| `storage/models/tool_feedback.py` | ~90 | 工具反馈模型 | `ToolExecutionFeedback` |
| `storage/models/workspace.py` | ~130 | 工作空间模型 | `SharedWorkspaceMemory` |
| `utils/scope_helper.py` | ~100 | 作用域推断 | `infer_scope_from_key`, `get_scope_id` |
| `utils/context_extractor.py` | ~80 | 上下文提取 | `extract_context_from_state` |
| `utils/memory_optimizer.py` | ~100 | 记忆优化 | `calculate_memory_importance` |

---

## 依赖关系

### 模块依赖图

```
┌─────────────────────────────────────────────────────────────┐
│                     应用层                                   │
│                   LangGraph Agents                          │
└────────────────────────────┬────────────────────────────────┘
                     │ 依赖
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  memory_aware_agent.py                      │
│                  state_bound_manager.py                     │
└────────────────────────────┬────────────────────────────────┘
                     │ 依赖
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    core/                                     │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐  │
│  │memory_system │  │   config.py   │  │state_bound_... │  │
│  └──────────────┘  └───────────────┘  └─────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                     │ 依赖
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   services/                                  │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐  │
│  │user_pref_... │  │decision_...   │  │workspace_...    │  │
│  └──────────────┘  └───────────────┘  └─────────────────┘  │
│           │                │                   │            │
│           └────────────────┼───────────────────┘            │
                          ▼                                 │
│                   base_service.py                          │
└────────────────────────────┬────────────────────────────────┘
                     │ 依赖
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   storage/                                   │
│  ┌──────────────┐  ┌───────────────┐                       │
│  │ database.py  │  │ redis_cache   │                       │
│  └──────────────┘  └───────────────┘                       │
│           │                │                                │
│           └────────────────┼────────────────┘               │
                          ▼                                  │
│                     models/                                 │
│  session.py, user_profile.py, agent_decision.py, ...        │
└────────────────────────────┬────────────────────────────────┘
                     │ 依赖
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   utils/                                     │
│  scope_helper.py, context_extractor.py, memory_optimizer.py │
└─────────────────────────────────────────────────────────────┘
```

### 导入关系

```python
# 应用层导入
from backend.agents.memory import MemoryAwareAgent

# memory_aware_agent.py 导入
from .state_bound_manager import StateBoundMemoryManager

# state_bound_manager.py 导入
from .core import MemorySystem, get_global_config
from .services import UserPreferenceService, DecisionService, WorkspaceService

# core/memory_system.py 导入
from .config import MemoryConfig
from ..services import UserPreferenceService, DecisionService, WorkspaceService
from ..storage import DatabaseManager, RedisCache

# 服务层导入
from ..storage.models import Session, UserProfile, AgentDecision
from ..storage import DatabaseManager, RedisCache
from .base_service import BaseService

# 存储层导入
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import redis
```

---

**文档版本：** 2.0.0
**最后更新：** 2025-02-09
