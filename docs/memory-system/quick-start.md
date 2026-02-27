# 记忆系统快速开始

> **5分钟上手指南** | 版本：5.1.0

---

## 🚀 快速开始

### 步骤1：环境配置（2分钟）

创建 `.env` 文件：

```bash
# 数据库（MySQL）
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/multiagent_ppt

# Redis
REDIS_URL=redis://localhost:6379/0

# 功能开关
MEMORY_ENABLE_USER_PREFERENCES=true
MEMORY_ENABLE_CACHE=true
```

### 步骤2：初始化数据库（1分钟）

```bash
# 方式1：使用命令行
cd backend
python -m memory.storage.database --init

# 方式2：使用代码
python -c "
from backend.memory.storage import get_db
from backend.memory.storage.models import Base

db = get_db()
Base.metadata.create_all(db.engine)
print('✅ Database initialized!')
"
```

### 步骤3：启动记忆系统（1分钟）

```python
# backend/main.py 或应用启动文件
from backend.memory import initialize_memory_system

async def startup():
    """应用启动时初始化"""
    system = await initialize_memory_system()

    if system:
        print("✅ Memory system initialized")
        status = await system.health_check()
        print(f"Database: {'✅' if status['database'] else '❌'}")
        print(f"Cache: {'✅' if status['cache'] else '❌'}")
    else:
        print("❌ Failed to initialize memory system")

# 运行
import asyncio
asyncio.run(startup())
```

### 步骤4：创建记忆感知Agent（1分钟）

```python
from backend.memory import MemoryAwareAgent

class MyAgent(MemoryAwareAgent):
    async def run_node(self, state):
        # 从状态初始化记忆
        self._get_memory(state)

        # 获取用户偏好
        preferences = await self.get_user_preferences()
        print(f"User preferences: {preferences}")

        # 应用偏好
        personalized = await self.apply_user_preferences_to_requirement(
            state["user_input"]
        )

        return {"**state": "personalized_requirement": personalized}
```

---

## ✅ 验证安装

运行测试脚本：

```python
# test_memory.py
import asyncio
from backend.memory import (
    initialize_memory_system,
    shutdown_memory_system,
    MemoryAwareAgent
)

async def main():
    # 1. 初始化
    print("1. Initializing memory system...")
    system = await initialize_memory_system()
    print(f"   Result: {'✅' if system else '❌'}")

    # 2. 健康检查
    print("2. Health check...")
    status = await system.health_check()
    print(f"   Database: {'✅' if status['database'] else '❌'}")
    print(f"   Cache: {'✅' if status['cache'] else '❌'}")

    # 3. 测试用户偏好
    print("3. Testing user preferences...")
    from backend.memory.services import UserPreferenceService

    service = system.user_preference_service
    prefs = await service.get_user_preferences(
        user_id="test_user",
        create_if_not_exists=True
    )
    print(f"   Preferences: {prefs}")

    # 4. 清理
    await shutdown_memory_system()
    print("4. Shutdown complete")

asyncio.run(main())
```

运行：
```bash
python test_memory.py
```

预期输出：
```
1. Initializing memory system...
   Result: ✅
2. Health check...
   Database: ✅
   Cache: ✅
3. Testing user preferences...
   Preferences: {'user_id': 'test_user', 'preferences': {...}}
4. Shutdown complete
```

---

## 💡 常见使用场景

### 场景1：用户偏好个性化

```python
class RequirementParserAgent(MemoryAwareAgent):
    async def run_node(self, state):
        self._get_memory(state)

        # 获取并应用用户偏好
        personalized = await self.apply_user_preferences_to_requirement(
            {"topic": "AI", "page_num": 10}
        )

        # personalized 可能会变成：
        # {"topic": "AI", "page_num": 15, "language": "ZH-CN"}

        return {**state, "requirements": personalized}
```

### 场景2：记录用户满意度

```python
class ContentAgent(MemoryAwareAgent):
    async def run_node(self, state):
        self._get_memory(state)

        # 生成内容
        content = await self.generate_content(state)

        # 假设用户修改了3次，满意度较低
        await self.record_user_satisfaction(
            score=0.6,
            feedback="内容可以，但图表太少"
        )

        return {**state, "content": content}
```

### 场景3：使用缓存（可选）

```python
class ResearchAgent(MemoryAwareAgent):
    async def run_node(self, state):
        self._get_memory(state)

        # 尝试从缓存获取
        cached = await self.recall("research_results")
        if cached:
            print("✅ Cache hit!")
            return {**state, "research": cached}

        # 缓存未命中，执行研究
        results = await self.do_research(state)

        # 存入缓存
        await self.remember("research_results", results, importance=0.8)

        return {**state, "research": results}
```

---

## 📚 下一步

### 深入学习

1. **应用层** → [04-application/README.md](./04-application/)
   - 5个Agent如何使用记忆系统
   - 完整的使用示例

2. **适配层** → [adapter-layer/README.md](./adapter-layer/)
   - MemoryAwareAgent详解
   - API参考

3. **服务层** → [service-layer/README.md](./service-layer/)
   - UserPreferenceService详解
   - 如何开发新Service

4. **存储层** → [storage-layer/README.md](./storage-layer/)
   - 数据库和缓存管理
   - 数据模型设计

### 故障排查

如果遇到问题：
- [配置指南](./reference/configuration.md) - 环境配置详解
- [故障排除](./reference/troubleshooting.md) - 常见问题解决

---

## 🎯 核心功能速查

| 功能 | 方法 | 说明 |
|------|------|------|
| **获取用户偏好** | `await self.get_user_preferences()` | 获取用户的配置 |
| **应用偏好** | `await self.apply_user_preferences_to_requirement(req)` | 个性化需求 |
| **记录满意度** | `await self.record_user_satisfaction(score)` | 记录用户反馈 |
| **缓存数据** | `await self.remember(key, value)` | 存储到缓存 |
| **读取缓存** | `await self.recall(key)` | 从缓存读取 |

---

**文档版本：** 5.1.0
**最后更新：** 2026-02-10
