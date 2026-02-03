# 使用指南

## 一、快速开始

### 1.1 初始化记忆系统

```python
# 伪代码
from cognition.memory.core import (
    HierarchicalMemoryManager,
    get_global_memory_manager,
    MemoryScope,
    MemoryLayer
)

# 方式1: 使用全局实例（推荐）
manager = get_global_memory_manager()

# 方式2: 创建自定义实例
from cognition.memory.core.database import DatabaseManager

db_manager = DatabaseManager()
manager = HierarchicalMemoryManager(
    l1_capacity=1000,                    # L1容量
    l2_redis_url="redis://localhost",    # Redis地址
    l3_db_manager=db_manager,            # 数据库管理器
    enable_auto_promotion=True,          # 启用自动提升
)

# 启动后台任务
await manager.start_background_tasks()
```

### 1.2 基础读写操作

```python
# 伪代码
# 写入数据
await manager.set(
    key="user_preferences",              # 数据键
    value={
        "theme": "dark",
        "language": "zh-CN"
    },                                  # 数据值
    scope=MemoryScope.USER,             # 作用域：用户级
    scope_id="user123",                 # 用户ID
    importance=0.8,                     # 重要性：0-1
    tags=["preferences", "ui"]          # 标签
)

# 读取数据
result = await manager.get(
    key="user_preferences",
    scope=MemoryScope.USER,
    scope_id="user123"
)

if result:
    value, metadata = result
    print(f"用户偏好: {value}")
    print(f"访问次数: {metadata.access_count}")
```

---

## 二、与Agent集成

### 2.1 Agent记忆Mixin

为Agent提供记忆能力的便捷方式：

```python
# 伪代码
class AgentMemoryMixin:
    """Agent记忆混入类"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.memory = get_global_memory_manager()
        self.session_id = generate_session_id()

    async def remember_decision(
        self,
        decision_type: str,
        action: str,
        context: dict,
        outcome: str = "pending"
    ):
        """记录决策"""
        await self.memory.set(
            key=f"decision:{decision_type}:{self.session_id}",
            value={
                "agent_name": self.agent_name,
                "action": action,
                "context": context,
                "outcome": outcome,
                "timestamp": now().isoformat()
            },
            scope=MemoryScope.AGENT,
            scope_id=self.agent_name,
            importance=0.6,
            tags=["decision", decision_type]
        )

    async def check_shared_workspace(self, data_key: str) -> Optional[dict]:
        """检查共享工作空间"""
        from cognition.memory.core.services import SharedWorkspaceService

        workspace = SharedWorkspaceService()
        return await workspace.get_shared_data(
            session_id=self.session_id,
            data_key=data_key,
            accessing_agent=self.agent_name
        )

    async def share_research_result(
        self,
        topic: str,
        findings: dict
    ):
        """共享研究结果"""
        from cognition.memory.core.services import SharedWorkspaceService

        workspace = SharedWorkspaceService()

        # 先检查是否已存在
        existing = await workspace.check_data_exists(
            session_id=self.session_id,
            data_key=topic
        )

        if existing:
            print(f"研究结果 {topic} 已存在，跳过")
            return

        # 共享结果
        await workspace.share_data(
            session_id=self.session_id,
            data_type="research_result",
            source_agent=self.agent_name,
            data_key=topic,
            data_content=findings,
            data_summary=findings.get("summary", ""),
            ttl_minutes=60
        )

# 使用示例
class ResearchAgent(AgentMemoryMixin):
    async def search(self, query: str):
        # 检查是否已有研究结果
        cached = await self.check_shared_workspace(query)
        if cached:
            return cached

        # 记录决策
        await self.remember_decision(
            decision_type="tool_selection",
            action="search",
            context={"query": query}
        )

        # 执行搜索
        results = await search_engine.search(query)

        # 共享结果
        await self.share_research_result(query, results)

        return results
```

### 2.2 用户偏好学习

```python
# 伪代码
from cognition.memory.core.services import UserPreferenceService

class PPTGenerationAgent:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.pref_service = UserPreferenceService()
        self.memory = get_global_memory_manager()

    async def generate(self, requirements: dict):
        # 获取用户偏好
        preferences = await self.pref_service.get_user_preferences(self.user_id)

        # 应用偏好
        config = {
            "template": preferences.get("template", "default"),
            "color_scheme": preferences.get("color_scheme", "blue"),
            "font_size": preferences.get("font_size", "medium"),
        }

        # 生成PPT
        ppt = await ppt_generator.generate(requirements, config)

        # 记录生成结果
        await self.memory.set(
            key=f"generation:{self.user_id}:{now()}",
            value={
                "requirements": requirements,
                "config": config,
                "result": ppt
            },
            scope=MemoryScope.USER,
            scope_id=self.user_id,
            importance=0.7
        )

        return ppt

    async def handle_modification(self, ppt_id: str, modifications: dict):
        """处理用户修改"""

        # 更新满意度评分
        modification_count = len(modifications.get("changes", []))

        satisfaction = self._infer_satisfaction(modification_count)

        await self.pref_service.update_satisfaction(
            user_id=self.user_id,
            session_id=self.session_id,
            satisfaction_score=satisfaction
        )

        # 学习新偏好
        if "color_scheme" in modifications:
            await self.pref_service.update_preferences(
                user_id=self.user_id,
                updates={"color_scheme": modifications["color_scheme"]}
            )
```

---

## 三、分布式锁使用

### 3.1 保护关键操作

```python
# 伪代码
from cognition.memory.core.services import get_lock_service

async def update_user_profile(user_id: str, updates: dict):
    """安全更新用户配置"""

    lock_service = get_lock_service()
    lock_key = f"user_profile:update:{user_id}"

    # 方式1: 使用上下文管理器（推荐）
    async with lock_service.acquire(lock_key, ttl=5000) as lock:
        # 获取当前配置
        current = await db.get_user_profile(user_id)

        # 检查版本号（乐观锁）
        if current.version != expected_version:
            raise ConflictError("Concurrent modification")

        # 应用更新
        current.update(updates)
        current.version += 1

        # 保存
        await db.save(current)

        # 锁会在退出时自动释放
```

### 3.2 长时间任务自动续期

```python
# 伪代码
async def long_running_task(user_id: str):
    lock_service = get_lock_service()

    # 启用自动续期
    lock = await lock_service.acquire(
        f"long_task:{user_id}",
        ttl=10000,              # 10秒TTL
        auto_renewal=True       # 自动续期
    )

    try:
        # 执行长时间任务，无需担心锁过期
        await process_step_1()
        await asyncio.sleep(15)  # 超过原始TTL
        await process_step_2()
    finally:
        await lock.release()
```

### 3.3 装饰器方式

```python
# 伪代码
from cognition.memory.core.services import distributed_lock

@distributed_lock("update_user:{user_id}", ttl=5000)
async def update_user(user_id: str, data: dict):
    # 函数执行期间自动持有锁
    await db.update_user(user_id, data)
```

---

## 四、向量检索使用

### 4.1 基础语义检索

```python
# 伪代码
from cognition.memory.core.services import get_vector_cache

async def semantic_search(query: str, user_id: str):
    """语义检索用户记忆"""

    # 1. 获取查询向量
    cache_service = get_vector_cache()
    query_vector = await cache_service.get_embedding(query)

    # 2. 执行检索
    manager = get_global_memory_manager()
    results = await manager.semantic_search(
        query_embedding=query_vector,
        scope=MemoryScope.USER,
        scope_id=user_id,
        limit=10,
        min_importance=0.3
    )

    # 3. 处理结果
    for key, content, similarity in results:
        if similarity > 0.85:
            print(f"高度相关: {key} ({similarity:.2f})")
        elif similarity > 0.75:
            print(f"相关: {key} ({similarity:.2f})")
        else:
            print(f"可能相关: {key} ({similarity:.2f})")

    return results
```

### 4.2 批量向量操作

```python
# 伪代码
async def batch_vector_operations(texts: list):
    cache_service = get_vector_cache()

    # 批量获取向量
    embeddings = await cache_service.get_embeddings(texts)

    # 存储到L3
    manager = get_global_memory_manager()

    for text, embedding in zip(texts, embeddings):
        await manager.set(
            key=f"vector:{hash(text)}",
            value={"text": text, "embedding": embedding},
            scope=MemoryScope.USER,
            scope_id="shared",
            importance=0.5
        )
```

---

## 五、监控和调试

### 5.1 查看系统统计

```python
# 伪代码
async def print_system_stats():
    manager = get_global_memory_manager()

    stats = await manager.get_stats()

    print("=== 记忆系统统计 ===")
    print(f"L1 数据量: {stats['l1_transient']['data_count']}/{stats['l1_transient']['capacity']}")
    print(f"L1 命中率: {stats['l1_transient']['hit_rate']:.2%}")

    print(f"L2 可用: {stats['l2_short_term']['redis_available']}")
    print(f"L2 命中率: {stats['l2_short_term']['hit_rate']:.2%}")

    print(f"L3 记录数: {stats['l3_long_term']['total_records']}")
    print(f"L3 平均重要性: {stats['l3_long_term']['avg_importance']:.2f}")

    print(f"\n总数据量: {stats['total_data_count']}")

    # 提升统计
    promotion = stats['promotion']
    print(f"\n=== 提升统计 ===")
    print(f"总提升次数: {promotion['total_promotions']}")
    print(f"唯一数据提升: {promotion['unique_keys_promoted']}")

    print("按原因分布:")
    for reason, count in promotion['by_reason'].items():
        print(f"  - {reason}: {count}")

    print("按层级转换:")
    for transition, count in promotion['by_layer_transition'].items():
        print(f"  - {transition}: {count}")
```

### 5.2 查询提升历史

```python
# 伪代码
async def analyze_promotion_history():
    manager = get_global_memory_manager()

    # 获取最近的提升事件
    events = await manager.get_promotion_history(limit=100)

    print("=== 提升历史 ===")

    for event in events[:10]:  # 显示前10条
        print(f"""
时间: {event['timestamp']}
键: {event['key']}
流转: {event['from_layer']} → {event['to_layer']}
原因: {event['reason']}
访问次数: {event['access_count']}
重要性: {event['importance']}
        """)

    # 分析提升模式
    l1_to_l2 = sum(1 for e in events if e['from_layer'] == 'L1_TRANSIENT')
    l2_to_l3 = sum(1 for e in events if e['from_layer'] == 'L2_SHORT_TERM')

    print(f"\n提升分布: L1→L2={l1_to_l2}, L2→L3={l2_to_l3}")
```

### 5.3 调试单个数据

```python
# 伪代码
async def debug_memory_key(key: str, scope: MemoryScope, scope_id: str):
    """调试指定键的数据状态"""

    manager = get_global_memory_manager()

    print(f"=== 调试: {key} ===")

    # 检查L1
    l1_result = await manager.l1.get(key, scope, scope_id)
    if l1_result:
        value, metadata = l1_result
        print(f"✓ 存在于 L1")
        print(f"  访问次数: {metadata.access_count}")
        print(f"  重要性: {metadata.importance}")
        print(f"  标签: {metadata.tags}")
    else:
        print("✗ 不存在于 L1")

    # 检查L2
    l2_result = await manager.l2.get(key, scope, scope_id)
    if l2_result:
        value, metadata = l2_result
        print(f"✓ 存在于 L2")
        print(f"  访问次数: {metadata.access_count}")
        print(f"  会话数: {len(metadata.session_ids)}")

        # 获取跨会话使用次数
        cross_session = await manager.l2.get_cross_session_count(key)
        print(f"  跨会话使用: {cross_session}")
    else:
        print("✗ 不存在于 L2")

    # 检查L3
    l3_result = await manager.l3.get(key, scope, scope_id)
    if l3_result:
        value, metadata = l3_result
        print(f"✓ 存在于 L3")
        print(f"  重要性: {metadata.importance}")
        print(f"  创建时间: {metadata.created_at}")
    else:
        print("✗ 不存在于 L3")

    # 检查是否会被提升
    if l1_result:
        value, metadata = l1_result
        if metadata.should_promote_to_l2():
            print("⚠ 满足L1→L2提升条件")
        else:
            print("→ 不满足L1→L2提升条件")
```

---

## 六、场景示例

### 6.1 多Agent协作场景

```python
# 伪代码
async def collaborative_research():
    """多Agent协作研究示例"""

    # Agent A: 研究者
    researcher = ResearchAgent("ResearchAgent")
    research_result = await researcher.search("AI最新进展")

    # Agent B: 内容组织者
    organizer = ContentOrganizerAgent("OrganizerAgent")

    # 检查是否已有研究结果
    cached = await organizer.check_shared_workspace("AI最新进展")
    if cached:
        print("使用缓存的研究结果")
        research_result = cached

    # 组织内容
    outline = await organizer.organize(research_result)

    # Agent C: PPT生成器
    generator = PPTGeneratorAgent("GeneratorAgent")
    ppt = await generator.generate(outline)

    return ppt
```

### 6.2 用户会话管理

```python
# 伪代码
class UserSession:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.session_id = generate_session_id()
        self.memory = get_global_memory_manager()
        self.pref_service = UserPreferenceService()

    async def initialize(self):
        """初始化会话"""
        # 获取用户偏好
        preferences = await self.pref_service.get_user_preferences(self.user_id)

        # 记录会话开始
        await self.memory.set(
            key=f"session:{self.session_id}:start",
            value={
                "user_id": self.user_id,
                "start_time": now().isoformat(),
                "preferences": preferences
            },
            scope=MemoryScope.SESSION,
            scope_id=self.session_id,
            importance=0.6
        )

    async def save_state(self, key: str, value: any):
        """保存会话状态"""
        await self.memory.set(
            key=f"session:{self.session_id}:{key}",
            value=value,
            scope=MemoryScope.SESSION,
            scope_id=self.session_id,
            importance=0.5
        )

    async def get_state(self, key: str):
        """获取会话状态"""
        result = await self.memory.get(
            key=f"session:{self.session_id}:{key}",
            scope=MemoryScope.SESSION,
            scope_id=self.session_id
        )
        return result[0] if result else None

    async def cleanup(self):
        """清理会话"""
        # 重要的数据提升到L3
        important_keys = ["final_result", "user_feedback"]

        for key in important_keys:
            await self.memory.promote_to_l3(
                key=f"session:{self.session_id}:{key}",
                scope=MemoryScope.SESSION,
                scope_id=self.session_id
            )

        # 清空会话
        await self.memory.clear_scope(
            scope=MemoryScope.SESSION,
            scope_id=self.session_id
        )

        # 更新用户统计
        await self.pref_service.increment_session_count(self.user_id)
```

### 6.3 批量导入数据

```python
# 伪代码
async def import_user_data(user_id: str, data_list: list):
    """批量导入用户数据"""

    manager = get_global_memory_manager()

    # 分批处理
    batch_size = 100

    for i in range(0, len(data_list), batch_size):
        batch = data_list[i:i+batch_size]

        # 并发写入
        tasks = []
        for item in batch:
            task = manager.set(
                key=f"import:{item['id']}",
                value=item,
                scope=MemoryScope.USER,
                scope_id=user_id,
                importance=0.5
            )
            tasks.append(task)

        await asyncio.gather(*tasks)

        print(f"已导入 {i + len(batch)}/{len(data_list)} 条")

    # 刷新L1高价值数据到L2
    count = await manager.batch_flush_l1_to_l2(
        scope=MemoryScope.USER,
        scope_id=user_id
    )

    print(f"已刷新 {count} 条数据到L2")
```

---

## 七、错误处理

### 7.1 常见错误处理

```python
# 伪代码
async def safe_memory_operation():
    manager = get_global_memory_manager()

    try:
        result = await manager.get(
            key="some_key",
            scope=MemoryScope.USER,
            scope_id="user123"
        )

        if result is None:
            # 数据不存在
            print("数据不存在，使用默认值")
            return get_default_value()

        value, metadata = result
        return value

    except RedisUnavailableError:
        # Redis不可用，降级到L3
        print("Redis不可用，直接查询L3")
        l3_result = await manager.l3.get(
            key="some_key",
            scope=MemoryScope.USER,
            scope_id="user123"
        )
        return l3_result[0] if l3_result else None

    except DatabaseError as e:
        # 数据库错误
        print(f"数据库错误: {e}")
        return None

    except Exception as e:
        # 未知错误
        print(f"未知错误: {e}")
        return None
```

### 7.2 重试机制

```python
# 伪代码
async def retry_memory_operation(
    max_retries: int = 3,
    retry_delay: float = 1.0
):
    """带重试的记忆操作"""

    manager = get_global_memory_manager()

    for attempt in range(max_retries):
        try:
            result = await manager.get(...)
            return result

        except RedisUnavailableError:
            if attempt < max_retries - 1:
                print(f"Redis不可用，{retry_delay}秒后重试...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
            else:
                raise

    return None
```

---

## 八、性能优化建议

### 8.1 批量操作优先

```python
# 伪代码
# ❌ 不推荐：逐个写入
for item in items:
    await manager.set(
        key=item['key'],
        value=item['value'],
        scope=MemoryScope.USER,
        scope_id=user_id
    )

# ✅ 推荐：批量并发
tasks = [
    manager.set(
        key=item['key'],
        value=item['value'],
        scope=MemoryScope.USER,
        scope_id=user_id
    )
    for item in items
]
await asyncio.gather(*tasks)
```

### 8.2 合理设置重要性

```python
# 伪代码
# 根据数据类型设置重要性
importance_map = {
    "user_preferences": 0.9,      # 用户偏好 - 高重要性
    "research_result": 0.7,       # 研究结果 - 较高
    "temporary_data": 0.3,        # 临时数据 - 低
    "cache": 0.2,                 # 缓存 - 很低
}

await manager.set(
    key=key,
    value=value,
    scope=MemoryScope.USER,
    scope_id=user_id,
    importance=importance_map.get(data_type, 0.5)
)
```

### 8.3 使用向量缓存

```python
# 伪代码
# 总是使用缓存获取向量
cache_service = get_vector_cache()

embedding = await cache_service.get_embedding(
    text="查询文本",
    use_cache=True  # 默认开启
)

# 预热高频查询
high_freq_queries = ["常见问题1", "常见问题2"]
await cache_service.warm_cache(high_freq_queries)
```

### 8.4 定期清理

```python
# 伪代码
# 定期清理过期数据
async def periodic_cleanup():
    manager = get_global_memory_manager()

    # 清理L1
    l1_count = await manager.l1.clear_scope(
        scope=MemoryScope.TASK,
        scope_id="completed_task"
    )

    # 清理L2
    l2_count = await manager.l2.clear_scope(
        scope=MemoryScope.SESSION,
        scope_id="expired_session"
    )

    print(f"清理完成: L1={l1_count}, L2={l2_count}")

# 使用定时任务
asyncio.create_task(periodic_cleanup())
```
