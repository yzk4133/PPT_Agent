# 层级详解

> **版本：** 2.0.0
> **更新日期：** 2025-02-09

---

## 目录

- [第1层：应用层详解](#第1层应用层详解)
- [第2层：适配层详解](#第2层适配层详解)
- [第3层：服务层详解](#第3层服务层详解)
- [第4层：存储层详解](#第4层存储层详解)
- [层级调用流程](#层级调用流程)

---

## 第1层：应用层详解

### 层的职责

**应用层** = 业务逻辑层，实现具体的业务功能（研究、框架设计、内容生成等）

### 内部分解

```
应用层
├── RequirementAgent    # 需求解析 Agent
├── ResearchAgent       # 研究 Agent
├── FrameworkAgent      # 框架设计 Agent
├── ContentAgent        # 内容生成 Agent
└── ...                 # 其他业务 Agent
```

### Agent 的标准结构

每个业务 Agent 都遵循相同的模式：

```python
class MyAgent(MemoryAwareAgent):  # 1. 继承记忆基类
    """业务 Agent 的标准结构"""

    # 2. 初始化（可选）
    def __init__(self, agent_name=None, enable_memory=True):
        super().__init__(agent_name, enable_memory)
        # 初始化业务相关的配置

    # 3. 核心业务方法
    async def run_node(self, state):
        """LangGraph 节点入口"""

        # Step 1: 初始化记忆（必须）
        self._get_memory(state)

        # Step 2: 执行业务逻辑
        result = await self._do_business_logic(state)

        # Step 3: 使用记忆（可选）
        await self.remember("result", result)

        # Step 4: 返回状态
        return state

    # 4. 业务逻辑方法（私有）
    async def _do_business_logic(self, state):
        """实际的业务实现"""
        # ... 业务代码
        pass
```

### 示例：ResearchAgent 的完整实现

```python
from backend.agents.memory import MemoryAwareAgent

class ResearchAgent(MemoryAwareAgent):
    """研究 Agent - 负责信息收集"""

    def __init__(self, agent_name="ResearchAgent", enable_memory=True):
        super().__init__(agent_name, enable_memory)

        # 业务相关的配置
        self.max_results = 10
        self.search_timeout = 30

    async def run_node(self, state):
        """
        LangGraph 节点入口

        输入：state (LangChain 状态)
        输出：state (更新后的状态)
        """
        # === 1. 初始化记忆 ===
        self._get_memory(state)

        # 提取业务参数
        query = state.get("user_query", "")
        user_id = state.get("user_id", "anonymous")

        # === 2. 检查缓存（使用记忆） ===
        cached = await self.recall(f"research:{query}")
        if cached:
            print(f"[{self.agent_name}] 使用缓存的研究结果")
            state["research_results"] = cached
            return state

        # === 3. 执行业务逻辑 ===
        print(f"[{self.agent_name}] 开始研究: {query}")
        results = await self._do_search(query)

        # === 4. 保存结果（使用记忆） ===
        await self.remember(f"research:{query}", results, importance=0.8)

        # === 5. 共享数据（使用工作空间） ===
        await self.share_data(
            data_type="research_result",
            data_key="findings",
            data_content=results,
            target_agents=["FrameworkAgent", "ContentAgent"]
        )

        # === 6. 记录决策（使用决策追踪） ===
        await self.record_decision(
            decision_type="search_method",
            selected_action="web_search",
            context={"query": query, "results_count": len(results)},
            reasoning="使用网络搜索获取实时信息",
            confidence_score=0.9
        )

        # === 7. 更新状态 ===
        state["research_results"] = results
        return state

    # === 业务逻辑方法 ===

    async def _do_search(self, query):
        """执行搜索（业务逻辑）"""
        # 模拟搜索操作
        await asyncio.sleep(1)  # 模拟网络请求

        results = {
            "query": query,
            "title": f"关于 {query} 的研究",
            "points": [
                f"{query} 的第一个要点",
                f"{query} 的第二个要点",
                f"{query} 的第三个要点"
            ],
            "sources": [
                f"https://example.com/{query}/1",
                f"https://example.com/{query}/2"
            ],
            "timestamp": datetime.now().isoformat()
        }

        return results
```

### 应用层的关键点

| 要点 | 说明 | 示例 |
|------|------|------|
| **继承基类** | 继承 `MemoryAwareAgent` 获得记忆能力 | `class MyAgent(MemoryAwareAgent)` |
| **初始化记忆** | 在 `run_node` 开始时调用 | `self._get_memory(state)` |
| **使用记忆** | 调用简化接口 | `await self.remember(key, value)` |
| **专注业务** | 核心逻辑在私有方法中 | `await self._do_business_logic()` |

### 应用层的文件组织

```
backend/agents/core/
├── planning/
│   ├── requirement_agent.py      # 需求解析 Agent
│   └── framework_agent.py        # 框架设计 Agent
├── generation/
│   ├── content_agent.py          # 内容生成 Agent
│   └── renderer_agent.py         # 渲染 Agent
└── research/
    └── research_agent.py         # 研究 Agent
```

---

## 第2层：适配层详解

### 层的职责

**适配层** = 桥接层，协调 LangChain 状态和记忆系统

### 内部分解

```
适配层
├── MemoryAwareAgent          # Agent 基类（提供接口）
│   ├── _get_memory()        # 初始化记忆管理器
│   ├── remember()           # 存储记忆
│   ├── recall()             # 检索记忆
│   ├── forget()             # 删除记忆
│   └── ...                  # 其他便捷方法
│
└── StateBoundMemoryManager  # 状态绑定管理器（核心协调）
    ├── 上下文提取           # 从 LangChain 状态提取 ID
    ├── 作用域推断           # 推断记忆作用域
    ├── 服务路由             # 调用正确的服务
    └── 优雅降级             # 处理记忆不可用
```

### MemoryAwareAgent 的实现

```python
class MemoryAwareAgent(ABC):
    """
    记忆感知 Agent 基类

    职责：
    1. 提供 Agent 使用的记忆接口
    2. 管理 StateBoundMemoryManager 的生命周期
    3. 将调用委托给 StateBoundMemoryManager
    """

    def __init__(self, agent_name=None, enable_memory=True):
        self._agent_name = agent_name or self.__class__.__name__
        self._enable_memory = enable_memory
        self._memory = None  # 延迟初始化

    def _get_memory(self, state) -> StateBoundMemoryManager:
        """
        初始化记忆管理器

        工作：
        1. 创建 StateBoundMemoryManager
        2. 传入 LangChain 状态
        3. 返回管理器实例
        """
        if self._memory is None:
            self._memory = get_memory_manager_for_state(
                state=state,
                agent_name=self._agent_name,
                enable_memory=self._enable_memory
            )
        return self._memory

    # === 便捷接口（委托给 StateBoundMemoryManager） ===

    async def remember(self, key, value, **kwargs):
        """存储记忆 - 委托给管理器"""
        if not self.has_memory:
            return False
        return await self.memory.remember(key, value, **kwargs)

    async def recall(self, key, **kwargs):
        """检索记忆 - 委托给管理器"""
        if not self.has_memory:
            return None
        return await self.memory.recall(key, **kwargs)

    # ... 其他方法类似
```

### StateBoundMemoryManager 的实现

```python
class StateBoundMemoryManager:
    """
    状态绑定记忆管理器

    职责：
    1. 从 LangChain 状态提取上下文
    2. 推断记忆作用域
    3. 路由到正确的服务
    4. 处理优雅降级
    """

    def __init__(self, state=None, agent_name="UnknownAgent", enable_memory=True):
        self.agent_name = agent_name
        self.enable_memory = enable_memory

        # === 1. 上下文提取 ===
        self._task_id = None
        self._user_id = None
        self._session_id = None

        if state:
            self._update_context(state)

        # === 2. 初始化服务 ===
        if self.enable_memory:
            self._initialize_services()

    # === 上下文提取 ===

    def _update_context(self, state):
        """从 LangChain 状态提取上下文"""
        self._task_id = state.get("task_id")
        self._user_id = state.get("user_id", "anonymous")
        self._session_id = state.get("session_id", self._task_id)

    # === 作用域推断 ===

    def _infer_scope_from_key(self, key: str) -> str:
        """根据键推断作用域"""
        key_lower = key.lower()

        # 状态相关 → TASK
        if any(kw in key_lower for kw in ["state", "status", "progress"]):
            return "TASK"

        # 用户数据 → USER
        elif any(kw in key_lower for kw in ["research", "cache", "preference"]):
            return "USER"

        # 默认 → TASK
        else:
            return "TASK"

    # === 服务路由 ===

    async def remember(self, key, value, importance=0.5, scope=None, tags=None):
        """
        存储记忆

        工作流程：
        1. 推断作用域
        2. 获取作用域 ID
        3. 调用底层记忆服务
        """
        if not self.enable_memory:
            return False

        # 1. 推断作用域
        if scope is None:
            scope = self._infer_scope_from_key(key)

        # 2. 获取作用域 ID
        scope_id = self._get_scope_id(scope)

        # 3. 添加标签
        all_tags = tags or []
        all_tags.extend([self.agent_name, key])

        # 4. 调用底层服务
        success = await self._memory_manager.set(
            key=f"{self.agent_name}:{key}",
            value=value,
            scope=self._MemoryScope[scope.upper()],
            scope_id=scope_id,
            importance=importance,
            tags=all_tags,
        )

        return success

    # === 作用域 ID 映射 ===

    def _get_scope_id(self, scope: str) -> str:
        """根据作用域返回对应的 ID"""
        if scope == "USER":
            return self._user_id or "anonymous"
        elif scope == "WORKSPACE":
            return self._session_id or self._task_id or "default"
        else:  # TASK, SESSION
            return self._task_id or self._session_id or "default"
```

### 适配层的工作流程

```
Agent 调用: await self.remember("research", data)
    │
    ▼
MemoryAwareAgent.remember()
    │ 接收调用
    ▼
StateBoundMemoryManager.remember()
    │
    ├─→ 1. 上下文提取
    │      task_id = state.get("task_id")
    │      user_id = state.get("user_id")
    │
    ├─→ 2. 作用域推断
    │      scope = infer_scope("research") → "USER"
    │
    ├─→ 3. 获取作用域 ID
    │      scope_id = user_id
    │
    └─→ 4. 调用服务层
           await _memory_manager.set(key, value, scope, scope_id)
```

### 适配层的关键点

| 功能 | 实现位置 | 说明 |
|------|----------|------|
| **上下文提取** | `_update_context()` | 从 LangChain 状态提取 ID |
| **作用域推断** | `_infer_scope_from_key()` | 根据键自动推断作用域 |
| **服务路由** | `remember/recall` | 调用底层服务 |
| **优雅降级** | `enable_memory` | 记忆不可用时自动禁用 |

---

## 第3层：服务层详解

### 层的职责

**服务层** = 业务逻辑层，实现记忆相关的业务规则

### 内部分解

```
服务层
├── BaseService               # 服务基类
│   ├── 数据库会话管理
│   ├── 缓存操作
│   └── 通用 CRUD
│
├── UserPreferenceService      # 用户偏好服务
│   ├── 偏好管理
│   ├── 使用统计
│   └── 满意度评分
│
├── DecisionService            # 决策追踪服务
│   ├── 决策记录
│   ├── 决策分析
│   └── 历史查询
│
└── WorkspaceService           # 工作空间服务
    ├── 数据共享
    ├── TTL 管理
    └── 访问控制
```

### BaseService 的实现

```python
class BaseService:
    """
    服务基类

    职责：
    1. 管理数据库会话
    2. 提供 Redis 缓存操作
    3. 实现通用 CRUD 方法
    """

    def __init__(self, db_session=None, cache_client=None):
        # 数据库会话
        self.db_session = db_session
        # Redis 缓存
        self.cache = cache_client

    # === 通用 CRUD ===

    async def get(self, model, id):
        """查询单条记录（带缓存）"""
        # 1. 检查缓存
        cache_key = f"{model.__name__}:{id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # 2. 查询数据库
        result = self.db_session.query(model).filter_by(id=id).first()

        # 3. 写入缓存
        if result:
            await self.cache.set(cache_key, result, ttl=3600)

        return result

    async def create(self, model, **kwargs):
        """创建记录"""
        instance = model(**kwargs)
        self.db_session.add(instance)
        self.db_session.commit()
        self.db_session.refresh(instance)
        return instance

    async def update(self, model, id, **kwargs):
        """更新记录"""
        instance = await self.get(model, id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            self.db_session.commit()

            # 清理缓存
            await self.cache.delete(f"{model.__name__}:{id}")

        return instance
```

### UserPreferenceService 的实现

```python
class UserPreferenceService(BaseService):
    """
    用户偏好服务

    业务逻辑：
    1. 用户偏好管理（增删改查）
    2. 使用统计（会话数、生成数）
    3. 满意度评分（加权平均）
    """

    # === 偏好管理 ===

    async def get_user_preferences(self, user_id, create_if_not_exists=False):
        """获取用户偏好（带缓存）"""
        # 1. 检查缓存
        cached = await self.cache.get_user_preferences(user_id)
        if cached:
            return cached

        # 2. 查询数据库
        profile = await self.get(UserProfile, user_id)

        # 3. 不存在则创建
        if not profile and create_if_not_exists:
            profile = UserProfile(user_id=user_id)
            self.db_session.add(profile)
            self.db_session.commit()
            self.db_session.refresh(profile)

        # 4. 返回数据
        if profile:
            preferences = profile.to_dict()

            # 5. 写入缓存
            await self.cache.set_user_preferences(user_id, preferences)

            return preferences

        return {}

    async def update_preferences(self, user_id, preferences):
        """更新用户偏好"""
        # 1. 获取或创建用户
        profile = await self.get(UserProfile, user_id)
        if not profile:
            profile = UserProfile(user_id=user_id, preferences=preferences)
            self.db_session.add(profile)
        else:
            # 2. 更新偏好
            for key, value in preferences.items():
                profile.set_preference(key, value)

        # 3. 提交事务
        self.db_session.commit()

        # 4. 清理缓存
        await self.cache.delete_user_preferences(user_id)

        return True

    # === 统计管理 ===

    async def increment_session_count(self, user_id):
        """增加会话计数"""
        profile = await self.get(UserProfile, user_id)
        if profile:
            profile.session_count += 1
            self.db_session.commit()
            await self.cache.delete_user_preferences(user_id)
        return True

    # === 满意度评分 ===

    async def update_satisfaction_score(self, user_id, score):
        """
        更新满意度评分（加权平均）

        业务规则：
        - 新分数 = (旧分数 * 旧计数 + 新分数) / (旧计数 + 1)
        """
        profile = await self.get(UserProfile, user_id)
        if profile:
            old_score = profile.satisfaction_score or 0
            count = profile.session_count or 1

            # 加权平均
            new_score = (old_score * count + score) / (count + 1)

            profile.satisfaction_score = new_score
            self.db_session.commit()

            await self.cache.delete_user_preferences(user_id)

        return True
```

### DecisionService 的实现

```python
class DecisionService(BaseService):
    """
    决策追踪服务

    业务逻辑：
    1. 记录 Agent 决策
    2. 查询决策历史
    3. 分析决策模式
    """

    async def record_decision(
        self,
        session_id,
        user_id,
        agent_name,
        decision_type,
        context,
        selected_action,
        alternatives,
        reasoning,
        confidence_score
    ):
        """记录决策"""
        decision = AgentDecision(
            session_id=session_id,
            user_id=user_id,
            agent_name=agent_name,
            decision_type=decision_type,
            context=context,
            selected_action=selected_action,
            alternatives=alternatives,
            reasoning=reasoning,
            confidence_score=confidence_score
        )

        self.db_session.add(decision)
        self.db_session.commit()

        return decision

    async def get_decision_history(self, agent_name, limit=100):
        """获取决策历史"""
        decisions = self.db_session.query(AgentDecision)\
            .filter_by(agent_name=agent_name)\
            .order_by(AgentDecision.created_at.desc())\
            .limit(limit)\
            .all()

        return decisions

    async def analyze_decisions(self, session_id):
        """分析决策模式"""
        decisions = self.db_session.query(AgentDecision)\
            .filter_by(session_id=session_id)\
            .all()

        # 业务逻辑：统计决策类型分布
        type_counts = {}
        for d in decisions:
            type_counts[d.decision_type] = type_counts.get(d.decision_type, 0) + 1

        # 业务逻辑：计算平均置信度
        avg_confidence = sum(d.confidence_score or 0 for d in decisions) / len(decisions)

        return {
            "total_decisions": len(decisions),
            "type_distribution": type_counts,
            "average_confidence": avg_confidence
        }
```

### 服务层的关键点

| 特性 | 说明 |
|------|------|
| **继承 BaseService** | 复用数据库和缓存操作 |
| **业务逻辑封装** | 在服务层实现复杂业务规则 |
| **缓存管理** | 自动处理缓存读写 |
| **事务管理** | 自动提交和回滚 |

---

## 第4层：存储层详解

### 层的职责

**存储层** = 数据持久化层，与 MySQL 和 Redis 交互

### 内部分解

```
存储层
├── DatabaseManager            # 数据库管理器
│   ├── 连接池管理
│   ├── 会话创建
│   └── 健康检查
│
├── RedisCache                 # Redis 缓存
│   ├── 连接管理
│   ├── 缓存操作
│   └── TTL 管理
│
└── Models/                    # 数据模型
    ├── Base                   # 基类
    ├── Session                # 会话模型
    ├── UserProfile            # 用户模型
    ├── AgentDecision          # 决策模型
    └── ...                    # 其他模型
```

### DatabaseManager 的实现

```python
class DatabaseManager:
    """
    数据库管理器

    职责：
    1. 管理 MySQL 连接池
    2. 创建数据库会话
    3. 健康检查
    """

    def __init__(self):
        # === 1. 创建引擎（连接池） ===
        self.engine = create_engine(
            DATABASE_URL,
            pool_size=10,           # 初始连接数
            max_overflow=20,        # 额外连接数
            pool_pre_ping=True,     # 连接前检查
            echo=False              # 不打印 SQL
        )

        # === 2. 创建会话工厂 ===
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def SessionLocal(self):
        """创建数据库会话"""
        return self.SessionLocal()

    def health_check(self):
        """健康检查"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
```

### RedisCache 的实现

```python
class RedisCache:
    """
    Redis 缓存

    职责：
    1. 管理 Redis 连接
    2. 提供缓存操作
    3. 处理 TTL
    """

    def __init__(self, redis_url=None):
        # === 1. 创建连接 ===
        self.client = redis.from_url(
            redis_url or REDIS_URL,
            decode_responses=True
        )

    def is_available(self):
        """检查 Redis 是否可用"""
        try:
            self.client.ping()
            return True
        except:
            return False

    # === 基本操作 ===

    async def get(self, key):
        """获取缓存"""
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except:
            return None

    async def set(self, key, value, ttl=3600):
        """设置缓存"""
        try:
            await self.client.setex(
                key,
                ttl,
                json.dumps(value, ensure_ascii=False)
            )
            return True
        except:
            return False

    async def delete(self, key):
        """删除缓存"""
        try:
            await self.client.delete(key)
            return True
        except:
            return False

    # === 用户偏好缓存 ===

    async def get_user_preferences(self, user_id):
        """获取用户偏好缓存"""
        key = f"user_pref:{user_id}"
        return await self.get(key)

    async def set_user_preferences(self, user_id, prefs):
        """设置用户偏好缓存"""
        key = f"user_pref:{user_id}"
        return await self.set(key, prefs, ttl=86400)  # 24小时

    async def delete_user_preferences(self, user_id):
        """删除用户偏好缓存"""
        key = f"user_pref:{user_id}"
        return await self.delete(key)
```

### 数据模型的实现

```python
class BaseModel(Base):
    """所有模型的基类"""

    def to_dict(self):
        """转换为字典"""
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
        }


class UserProfile(BaseModel):
    """用户配置模型"""

    __tablename__ = "user_profiles"

    # === 字段定义 ===
    user_id = Column(String(255), primary_key=True)
    preferences = Column(JSON, nullable=True)
    session_count = Column(Integer, default=0)
    generation_count = Column(Integer, default=0)
    satisfaction_score = Column(Float, nullable=True)
    last_interaction_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # === 业务方法 ===

    def set_preference(self, key, value):
        """设置单个偏好"""
        if self.preferences is None:
            self.preferences = {}
        self.preferences[key] = value

    def get_preference(self, key, default=None):
        """获取单个偏好"""
        if self.preferences is None:
            return default
        return self.preferences.get(key, default)

    def increment_session_count(self):
        """增加会话计数"""
        self.session_count += 1
        self.last_interaction_at = datetime.utcnow()

    def increment_generation_count(self):
        """增加生成计数"""
        self.generation_count += 1
        self.last_interaction_at = datetime.utcnow()

    def update_satisfaction_score(self, score):
        """更新满意度评分"""
        self.satisfaction_score = score
```

### 存储层的关键点

| 组件 | 职责 | 关键方法 |
|------|------|----------|
| **DatabaseManager** | MySQL 连接管理 | `SessionLocal()`, `health_check()` |
| **RedisCache** | Redis 缓存操作 | `get()`, `set()`, `delete()` |
| **BaseModel** | 模型基类 | `to_dict()` |
| **具体模型** | 数据表映射 | 字段定义 + 业务方法 |

---

## 层级调用流程

### 完整的调用链

以"保存用户偏好"为例：

```python
# === 应用层 ===
class MyAgent(MemoryAwareAgent):
    async def run_node(self, state):
        # 保存用户偏好
        await self.memory.update_user_preferences({
            "language": "zh-CN"
        })
        return state

# === 适配层 ===
class StateBoundMemoryManager:
    async def update_user_preferences(self, updates, user_id=None):
        # 调用服务层
        await self._user_pref_service.update_preferences(
            user_id or self._user_id,
            updates
        )

# === 服务层 ===
class UserPreferenceService:
    async def update_preferences(self, user_id, preferences):
        # 1. 获取或创建用户
        profile = await self.get(UserProfile, user_id)

        # 2. 更新数据
        for key, value in preferences.items():
            profile.set_preference(key, value)

        # 3. 提交到数据库（存储层）
        self.db_session.commit()

        # 4. 清理缓存（存储层）
        await self.cache.delete_user_preferences(user_id)

# === 存储层 ===
# DatabaseManager
db_session.commit()  # 提交到 MySQL

# RedisCache
await client.delete(f"user_pref:{user_id}")  # 删除 Redis 缓存
```

### 数据流图

```
┌─────────────────────────────────────────────────────────────┐
│  应用层：MyAgent                                             │
│  await self.memory.update_user_preferences({"lang": "zh"})  │
└────────────────────────────┬────────────────────────────────┘
                             │ 调用
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  适配层：StateBoundMemoryManager                            │
│  await self._user_pref_service.update_preferences(uid, prefs)│
└────────────────────────────┬────────────────────────────────┘
                             │ 调用
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  服务层：UserPreferenceService                              │
│  profile = await self.get(UserProfile, user_id)            │
│  profile.set_preference("lang", "zh")                      │
│  self.db_session.commit()  ─────────────────┐               │
│  await self.cache.delete_user_preferences() │               │
└────────────────────────────┬────────────────────┼───────────┘
                             │ 调用           │ 调用
                             ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│  存储层                         ┌────────────────────────────┐ │
│  ┌─────────────────────┐      │  RedisCache               │ │
│  │  DatabaseManager    │      │  await client.delete()    │ │
│  │  MySQL              │      └────────────────────────────┘ │
│  │  UPDATE user_profiles│                                   │
│  │  SET preferences =...│                                   │
│  └─────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘
```

### 层级职责总结

| 层 | 职责 | 输入 | 输出 |
|----|------|------|------|
| **应用层** | 业务逻辑 | `state` | `state` |
| **适配层** | 协调 LangChain | 接口调用 | 服务调用 |
| **服务层** | 业务规则 | 服务请求 | 数据操作 |
| **存储层** | 数据持久化 | 数据操作 | MySQL/Redis |

---

**文档版本：** 2.0.0
**最后更新：** 2025-02-09
