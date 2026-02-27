# Memory System - Restructured Architecture

## Overview

This memory system provides comprehensive memory capabilities for LangChain agents, including user preferences, decision tracking, workspace sharing, and vector-based semantic search.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│              (LangGraph Agents - 业务层)                     │
│  RequirementAgent | ResearchAgent | FrameworkAgent | ...    │
└────────────────────────────┬────────────────────────────────┘
                              │ 继承
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 MemoryAwareAgent                             │
│              (记忆感知Agent基类)                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  MemoryAwareAgent (基类)                              │   │
│  │  - 直接聚合记忆服务                                    │   │
│  │  - 从 LangGraph 状态提取上下文                         │   │
│  │  - 作用域自动推断                                      │   │
│  │  - 提供便捷的记忆操作API                               │   │
│  │    remember(), recall(), forget(), share_data()       │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                              │ 调用
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                              │
│                  (业务逻辑层)                                │
│  ┌──────────────────┐ ┌─────────────────┐ ┌─────────────┐  │
│  │ UserPreference   │ │  Decision       │ │  Workspace  │  │
│  │ Service          │ │  Service        │ │  Service    │  │
│  └──────────────────┘ └─────────────────┘ └─────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                              │ 调用
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Storage Layer                              │
│                  (数据持久化层)                              │
│  ┌──────────────────┐     ┌──────────────────┐             │
│  │  MySQL           │     │     Redis        │             │
│  │  - 会话状态       │     │  - L2 缓存        │             │
│  │  - 用户偏好       │     │  - 会话缓存       │             │
│  │  - 向量记忆       │     │  - 热点数据       │             │
│  │  - 决策追踪       │     │                   │             │
│  └──────────────────┘     └──────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
backend/memory/
├── __init__.py                      # 公开 API 导出
│
├── memory_aware_agent.py            # Agent 基类（核心）
│
├── core/                            # 核心模块
│   ├── __init__.py
│   ├── config.py                    # 配置管理
│   └── memory_system.py             # 记忆系统入口
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
│       ├── vector_memory.py         # 向量记忆模型
│       ├── conversation.py          # 对话历史模型
│       ├── agent_decision.py        # Agent决策模型
│       ├── tool_feedback.py         # 工具反馈模型
│       └── workspace.py             # 工作空间模型
│
└── tests/                           # 测试模块
    ├── __init__.py
    ├── conftest.py                  # 测试配置
    ├── test_memory_integration.py   # 集成测试
    └── test_services/               # 服务测试
```

## Key Components

### Core Layer

#### MemoryAwareAgent
Base class that provides memory capabilities to LangChain agents.

**优化后的架构：** MemoryAwareAgent 直接聚合记忆服务，无需中间层。

```python
from backend.memory import MemoryAwareAgent

class MyAgent(MemoryAwareAgent):
    async def run_node(self, state):
        self._get_memory(state)
        await self.remember("key", "value")
        result = await self.recall("key")
        return state
```

**核心特性：**
- 直接聚合服务（UserPreferenceService, DecisionService, WorkspaceService）
- 从 LangGraph 状态自动提取上下文（task_id, user_id, session_id）
- 自动推断记忆作用域（TASK/USER/WORKSPACE/SESSION）
- 优雅降级：记忆不可用时仍可正常运行

#### MemorySystem
Unified entry point for the memory system, managing all services and resources.

```python
from backend.memory import initialize_memory_system

# Initialize system
await initialize_memory_system()
```

### Service Layer

#### UserPreferenceService
Manages user preferences, usage statistics, and satisfaction scores.

```python
from backend.memory import UserPreferenceService

service = UserPreferenceService(db_session, cache_client)
preferences = await service.get_user_preferences(user_id="user123")
await service.update_preferences(user_id="user123", preferences={"style": "professional"})
```

#### DecisionService
Records and analyzes agent decisions for optimization.

```python
from backend.memory import DecisionService

service = DecisionService(db_session, cache_client)
await service.record_decision(
    session_id="session123",
    user_id="user123",
    agent_name="ResearchAgent",
    decision_type="tool_selection",
    context={"query": "..."},
    selected_action="web_search"
)
```

#### WorkspaceService
Manages data sharing between multi-agents.

```python
from backend.memory import WorkspaceService

service = WorkspaceService(db_session, cache_client)
await service.share_data(
    session_id="session123",
    data_type="research_result",
    source_agent="ResearchAgent",
    data_key="findings",
    data_content={"results": [...]}
)
```

### Storage Layer

#### Database Models
- **Session**: Stores agent session state with version control
- **UserProfile**: Stores user preferences and usage statistics
- **VectorMemory**: Stores semantic vectors with pgvector
- **ConversationHistory**: Stores dialogue history
- **AgentDecision**: Tracks agent decisions and outcomes
- **ToolExecutionFeedback**: Tracks tool usage and feedback
- **SharedWorkspaceMemory**: Manages multi-agent data sharing

### Utility Layer

#### Scope Helper
Infers memory scope from keys and provides scope validation.

```python
from backend.agents.memory.utils import infer_scope_from_key

scope = infer_scope_from_key("research_results")  # Returns "USER"
```

#### Context Extractor
Extracts context from LangChain state.

```python
from backend.agents.memory.utils import extract_context_from_state

context = extract_context_from_state(state)
```

#### Memory Optimizer
Provides memory optimization utilities.

```python
from backend.agents.memory.utils import calculate_memory_importance

importance = calculate_memory_importance(
    access_count=10,
    last_accessed=datetime.utcnow(),
    age_days=30
)
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Feature Flags
MEMORY_ENABLE_USER_PREFERENCES=true
MEMORY_ENABLE_DECISION_TRACKING=true
MEMORY_ENABLE_WORKSPACE=true
MEMORY_ENABLE_VECTOR_SEARCH=false
MEMORY_ENABLE_CACHE=true

# Performance
MEMORY_L1_CACHE_SIZE=1000
MEMORY_L2_TTL_SECONDS=3600
MEMORY_CONNECTION_POOL_SIZE=10

# Logging
MEMORY_LOG_LEVEL=INFO
MEMORY_LOG_OPERATIONS=true
MEMORY_LOG_SQL=false
```

### Programmatic Configuration

```python
from backend.memory import MemoryConfig, initialize_memory_system

config = MemoryConfig(
    enable_user_preferences=True,
    enable_decision_tracking=True,
    l1_cache_size=2000,
    log_level="DEBUG"
)

await initialize_memory_system(config)
```

## Usage Examples

### Basic Memory Operations

```python
from backend.memory import MemoryAwareAgent

class MyAgent(MemoryAwareAgent):
    async def run_node(self, state):
        # Initialize memory
        self._get_memory(state)

        # Store information
        await self.remember("research_results", results, importance=0.8)

        # Retrieve information
        cached = await self.recall("research_results")

        # Delete information
        await self.forget("research_results")

        return state
```

### User Preferences

```python
# Get preferences
preferences = await self.memory.get_user_preferences()
style = preferences.get("style", "professional")

# Update preferences
await self.memory.update_user_preferences({
    "language": "zh-CN",
    "default_slides": 15
})
```

### Workspace Sharing

```python
# Share data with other agents
await self.share_data(
    data_type="outline",
    data_key="main_outline",
    data_content=outline_data,
    target_agents=["ContentAgent", "FrameworkAgent"]
)

# Get shared data
shared_data = await self.get_shared_data(
    data_type="research_result",
    data_key="findings"
)
```

### Decision Tracking

```python
await self.record_decision(
    decision_type="tool_selection",
    selected_action="web_search",
    context={"query": user_query, "options": ["web_search", "wiki_search"]},
    alternatives=["wiki_search"],
    reasoning="User query requires real-time web data",
    confidence_score=0.9
)
```

## Testing

Run tests with pytest:

```bash
# Run all memory tests
pytest backend/memory/tests/ -v

# Run specific test file
pytest backend/memory/tests/test_memory_integration.py -v

# Run with coverage
pytest backend/memory/tests/ -v --cov=backend.memory
```

## Migration from Old System

If you're migrating from the old memory system:

1. **Architecture Simplification:** StateBoundMemoryManager has been removed
2. **Import paths remain the same:** `from backend.memory import MemoryAwareAgent`
3. **API remains fully backward compatible**
4. **New services are available** for more granular control
5. **Configuration is now centralized** in `MemoryConfig`

### What Changed

**Before (3-layer architecture):**
```
Agents → MemoryAwareAgent → StateBoundMemoryManager → Services
```

**After (2-layer architecture):**
```
Agents → MemoryAwareAgent (directly aggregates services)
```

The StateBoundMemoryManager layer has been removed. MemoryAwareAgent now directly aggregates the memory services.

## Performance Considerations

- **L1 Cache**: In-memory cache for frequently accessed data (~5-10x faster)
- **L2 Cache**: Redis cache for session data (~10-50x faster)
- **Connection Pooling**: Configurable pool size for database connections
- **Batch Operations**: Services support batch operations for efficiency

## Troubleshooting

### Memory Not Available

If memory operations fail silently:
1. Check if dependencies are installed: `pip install -r requirements.txt`
2. Verify database connection: `DATABASE_URL`
3. Verify Redis connection: `REDIS_URL`
4. Check logs for specific errors

### Performance Issues

1. Enable caching: `MEMORY_ENABLE_CACHE=true`
2. Increase cache sizes: `MEMORY_L1_CACHE_SIZE`, `MEMORY_L2_TTL_SECONDS`
3. Optimize database queries with indexes
4. Use batch operations where possible

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please follow the established code style and add tests for new features.
