# 使用指南

> **版本：** 2.0.0
> **更新日期：** 2025-02-09

---

## 目录

- [快速开始](#快速开始)
- [基本操作](#基本操作)
- [用户偏好管理](#用户偏好管理)
- [决策追踪](#决策追踪)
- [工作空间共享](#工作空间共享)
- [最佳实践](#最佳实践)
- [完整示例](#完整示例)

---

## 快速开始

### 1. 初始化记忆系统

在应用启动时初始化记忆系统：

```python
from backend.agents.memory import initialize_memory_system

# 初始化（使用默认配置）
system = await initialize_memory_system()

# 检查系统状态
if system:
    status = await system.health_check()
    print(f"Database: {'OK' if status['database'] else 'FAIL'}")
    print(f"Cache: {'OK' if status['cache'] else 'FAIL'}")
```

### 2. 创建记忆感知 Agent

```python
from backend.agents.memory import MemoryAwareAgent

class MyAgent(MemoryAwareAgent):
    async def run_node(self, state):
        # 第一步：从状态初始化记忆
        self._get_memory(state)

        # 检查记忆是否可用
        if not self.has_memory:
            print("Memory not available, using default behavior")

        # 使用记忆
        await self.remember("key", "value")
        result = await self.recall("key")

        return state
```

### 3. 环境配置

创建 `.env` 文件：

```bash
# 数据库配置
DATABASE_URL=mysql://user:password@localhost:3306/multiagent_ppt

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# 功能开关
MEMORY_ENABLE_USER_PREFERENCES=true
MEMORY_ENABLE_DECISION_TRACKING=true
MEMORY_ENABLE_WORKSPACE=true
MEMORY_ENABLE_CACHE=true
```

---

## 基本操作

### remember() - 存储信息

```python
# 基本用法
await self.remember("research_results", results)

# 带重要性分数
await self.remember("important_data", data, importance=0.9)

# 指定作用域
await self.remember("user_setting", settings, scope="USER")

# 带标签
await self.remember("data", value, tags=["research", "web_search"])
```

### recall() - 检索信息

```python
# 基本用法
result = await self.recall("research_results")

# 指定作用域
result = await self.recall("user_setting", scope="USER")

# 仅搜索特定层
result = await self.recall("key", search_all_layers=False)
```

### forget() - 删除信息

```python
# 基本用法
await self.forget("old_data")

# 指定作用域
await self.forget("temp_data", scope="TASK")
```

---

## 用户偏好管理

### 获取用户偏好

```python
# 获取所有偏好
preferences = await self.memory.get_user_preferences()

# 使用偏好
language = preferences.get("language", "zh-CN")
theme = preferences.get("theme", "light")
default_slides = preferences.get("default_slides", 15)
```

### 更新用户偏好

```python
# 更新多个偏好
await self.memory.update_user_preferences({
    "language": "en-US",
    "theme": "dark",
    "default_slides": 20,
    "auto_save": True
})

# 使用服务直接操作
from backend.agents.memory import UserPreferenceService

service = UserPreferenceService(db_session, cache_client)
await service.set_preference(user_id, "language", "zh-CN")
```

### 使用统计

```python
# 增加会话计数
await self.memory.user_preference_service.increment_session_count(user_id)

# 增加生成计数
await self.memory.user_preference_service.increment_generation_count(user_id)

# 更新满意度评分（0.0-1.0）
await self.memory.user_preference_service.update_satisfaction_score(
    user_id, score=0.9
)
```

---

## 决策追踪

### 记录决策

```python
# 记录工具选择决策
await self.record_decision(
    decision_type="tool_selection",
    selected_action="web_search",
    context={
        "query": user_query,
        "options": ["web_search", "wiki_search", "local_search"]
    },
    alternatives=["wiki_search"],
    reasoning="用户查询需要实时网络数据",
    confidence_score=0.9
)

# 记录路由决策
await self.record_decision(
    decision_type="rerouting",
    selected_action="human_review",
    context={
        "current_stage": "content_generation",
        "error": "quality_threshold_not_met"
    },
    reasoning="内容质量不达标，需要人工审核",
    confidence_score=0.95
)

# 记录参数调整决策
await self.record_decision(
    decision_type="parameter_tuning",
    selected_action="increase_temperature",
    context={
        "current_temperature": 0.7,
        "output_quality": "too_conservative"
    },
    reasoning="输出过于保守，提高创造性",
    confidence_score=0.8
)
```

### 获取决策历史

```python
from backend.agents.memory import DecisionService

service = DecisionService(db_session, cache_client)

# 获取特定 Agent 的决策历史
history = await service.get_decision_history(
    agent_name="ResearchAgent",
    limit=10
)

for decision in history:
    print(f"{decision.decision_type}: {decision.selected_action}")
    print(f"  置信度: {decision.confidence_score}")
    print(f"  推理: {decision.reasoning}")
```

---

## 工作空间共享

### 共享数据

```python
# 共享研究结果给其他 Agent
await self.share_data(
    data_type="research_result",
    data_key="findings",
    data_content={
        "title": "AI 技术调研",
        "summary": "本文档总结了最新的 AI 技术...",
        "points": [
            "大语言模型的发展",
            "多模态 AI 的应用",
            "Agent 系统的架构"
        ],
        "sources": ["https://...", "https://..."]
    },
    target_agents=["FrameworkAgent", "ContentAgent"],
    ttl_minutes=60
)

# 共享框架设计
await self.share_data(
    data_type="framework",
    data_key="outline",
    data_content=outline_structure,
    target_agents=["ContentAgent"]
)

# 共享给所有 Agent
await self.share_data(
    data_type="session_config",
    data_key="settings",
    data_content=config,
    target_agents=None  # None = 所有 Agent
)
```

### 获取共享数据

```python
# 获取特定数据
findings = await self.get_shared_data(
    data_type="research_result",
    data_key="findings"
)

if findings:
    print(f"标题: {findings['title']}")
    print(f"要点: {findings['points']}")
```

### 列出共享数据

```python
# 列出所有研究类型的数据
all_research = await self.memory.list_shared_data(
    data_type="research_result"
)

for item in all_research:
    print(f"{item['data_key']} from {item['source_agent']}")
    print(f"  创建时间: {item['created_at']}")
    print(f"  访问次数: {item['accessed_count']}")

# 列出所有共享数据
all_shared = await self.memory.list_shared_data()
```

---

## 最佳实践

### 1. 记忆键命名规范

```python
# 好的命名
await self.remember("research_results", data)  # 清晰
await self.remember("user_language", lang)     # 明确作用域
await self.remember("task_progress", 0.5)      # 包含状态

# 避免的命名
await self.remember("data", data)              # 太泛化
await self.remember("temp", temp_data)         # 不明确
```

### 2. 重要性分数设置

```python
# 高重要性（用户偏好、重要配置）
await self.remember("user_preferences", prefs, importance=1.0)

# 中等重要性（研究结果、中间产物）
await self.remember("research_results", results, importance=0.7)

# 低重要性（临时状态、调试信息）
await self.remember("debug_info", info, importance=0.3)
```

### 3. 作用域选择

```python
# TASK 作用域：任务相关、临时数据
await self.remember("current_stage", "research", scope="TASK")
await self.remember("progress", 0.5, scope="TASK")

# USER 作用域：跨任务持久化
await self.remember("language", "zh-CN", scope="USER")
await self.remember("history", records, scope="USER")

# WORKSPACE 作用域：Agent 间共享
await self.remember("shared_data", data, scope="WORKSPACE")
```

### 4. 错误处理

```python
# 检查记忆是否可用
async def run_node(self, state):
    self._get_memory(state)

    if not self.has_memory:
        # 降级处理
        return await self._process_without_memory(state)

    # 正常处理
    return await self._process_with_memory(state)

# 安全的记忆操作
try:
    await self.remember("key", "value")
except Exception as e:
    logger.error(f"Memory error: {e}")
    # 继续执行，不影响主流程
```

### 5. 性能优化

```python
# 批量操作
# 不推荐
for item in items:
    await self.remember(f"item_{i}", item)

# 推荐
await self.remember("all_items", items)

# 缓存热点数据
# 频繁访问的数据应该有更高的重要性
await self.remember("hot_data", data, importance=0.9)

# 及时清理过期数据
await self.memory.workspace_service.cleanup_expired()
```

---

## 完整示例

### 研究 Agent 示例

```python
from backend.agents.memory import MemoryAwareAgent

class ResearchAgent(MemoryAwareAgent):
    """研究 Agent - 负责信息收集和研究"""

    async def run_node(self, state):
        # 1. 初始化记忆
        self._get_memory(state)

        # 2. 获取用户偏好
        preferences = await self.memory.get_user_preferences()
        language = preferences.get("language", "zh-CN")
        max_results = preferences.get("max_search_results", 10)

        # 3. 检查缓存
        cached = await self.recall("research_results")
        if cached:
            print("使用缓存的研究结果")
            state["research_results"] = cached
            return state

        # 4. 执行研究
        query = state.get("user_query", "")
        print(f"开始研究: {query}")

        results = await self._do_research(query, language, max_results)

        # 5. 存储结果
        await self.remember("research_results", results, importance=0.8)

        # 6. 记录决策
        await self.record_decision(
            decision_type="search_method",
            selected_action="web_search",
            context={"query": query, "results_count": len(results)},
            reasoning=f"使用网络搜索，语言: {language}",
            confidence_score=0.9
        )

        # 7. 共享结果给其他 Agent
        await self.share_data(
            data_type="research_result",
            data_key="findings",
            data_content=results,
            target_agents=["FrameworkAgent", "ContentAgent"],
            ttl_minutes=120
        )

        # 8. 更新统计
        await self.memory.user_preference_service.increment_generation_count(
            state.get("user_id", "anonymous")
        )

        state["research_results"] = results
        return state

    async def _do_research(self, query, language, max_results):
        """执行实际的研究工作"""
        # ... 实现研究逻辑
        return {"title": "...", "points": [], "sources": []}
```

### 框架设计 Agent 示例

```python
class FrameworkAgent(MemoryAwareAgent):
    """框架设计 Agent - 负责设计 PPT 框架"""

    async def run_node(self, state):
        # 1. 初始化记忆
        self._get_memory(state)

        # 2. 获取共享的研究结果
        research_data = await self.get_shared_data(
            data_type="research_result",
            data_key="findings"
        )

        if not research_data:
            # 没有研究结果，等待或跳过
            print("未找到研究结果，跳过框架设计")
            return state

        # 3. 获取用户偏好
        preferences = await self.memory.get_user_preferences()
        default_slides = preferences.get("default_slides", 15)

        # 4. 设计框架
        framework = await self._design_framework(
            research_data,
            default_slides
        )

        # 5. 存储框架
        await self.remember("framework", framework, importance=0.9)

        # 6. 记录决策
        await self.record_decision(
            decision_type="framework_design",
            selected_action="hierarchical_structure",
            context={
                "slides_count": len(framework["slides"]),
                "structure_type": "hierarchical"
            },
            reasoning=f"根据研究结果设计层次结构，共 {len(framework['slides'])} 页",
            confidence_score=0.85
        )

        # 7. 共享框架
        await self.share_data(
            data_type="framework",
            data_key="outline",
            data_content=framework,
            target_agents=["ContentAgent"],
            ttl_minutes=120
        )

        state["framework"] = framework
        return state

    async def _design_framework(self, research_data, slides_count):
        """设计框架结构"""
        # ... 实现框架设计逻辑
        return {"slides": [], "structure": "hierarchical"}
```

### 内容生成 Agent 示例

```python
class ContentAgent(MemoryAwareAgent):
    """内容生成 Agent - 负责生成幻灯片内容"""

    async def run_node(self, state):
        # 1. 初始化记忆
        self._get_memory(state)

        # 2. 获取框架和研究数据
        framework = await self.get_shared_data(
            data_type="framework",
            data_key="outline"
        )

        research = await self.get_shared_data(
            data_type="research_result",
            data_key="findings"
        )

        if not framework or not research:
            print("缺少必要数据，跳过内容生成")
            return state

        # 3. 生成内容
        content = await self._generate_content(
            framework,
            research
        )

        # 4. 存储内容
        await self.remember("generated_content", content, importance=0.9)

        # 5. 记录决策
        await self.record_decision(
            decision_type="content_generation",
            selected_action="ai_generation",
            context={
                "slides_generated": len(content["slides"]),
                "method": "langchain_llm"
            },
            reasoning=f"使用 AI 生成 {len(content['slides'])} 页幻灯片内容",
            confidence_score=0.8
        )

        # 6. 更新用户满意度（假设用户反馈）
        # await self.memory.user_preference_service.update_satisfaction_score(
        #     state.get("user_id"), score=0.9
        # )

        state["content"] = content
        return state

    async def _generate_content(self, framework, research):
        """生成幻灯片内容"""
        # ... 实现内容生成逻辑
        return {"slides": []}
```

---

**文档版本：** 2.0.0
**最后更新：** 2025-02-09
