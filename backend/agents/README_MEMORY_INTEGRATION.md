# Agent Memory Integration Guide

MultiAgentPPT 智能体记忆系统集成使用指南

## 概述

记忆系统为MultiAgentPPT的智能体提供了三层记忆能力：

1. **L1 - 瞬时层** (Transient Layer): 内存缓存，快速访问，自动清理
2. **L2 - 短期层** (Short-term Layer): Redis缓存，跨实例共享
3. **L3 - 长期层** (Long-term Layer): 数据库存储，持久化保存

## 核心功能

### 1. 研究缓存 (ResearchAgent)

- **功能**: 缓存研究结果，避免重复研究
- **缓存时长**: 默认7天（可通过 `RESEARCH_CACHE_TTL_DAYS` 配置）
- **预期效果**: 减少搜索API调用30%+

```python
# 自动使用缓存
from agents.core.research import research_agent

# 第一次请求：执行实际研究
result1 = await research_agent.run_async(ctx)

# 第二次请求：使用缓存（相同主题）
result2 = await research_agent.run_async(ctx)
```

### 2. 用户偏好学习 (RequirementParserAgent)

- **功能**: 学习用户常用配置（页数、语言、风格等）
- **学习方式**: 统计用户历史选择，自动更新偏好
- **应用场景**: 自动应用用户偏好到新任务

```python
# 用户偏好自动应用
from agents.core.requirements import requirement_parser_agent

# 第一次用户请求: "15页商务PPT"
# -> 系统学习偏好: default_slides=15, template_type=BUSINESS

# 第二次用户请求: "生成AI技术PPT"
# -> 系统自动应用: 15页、商务模板
```

### 3. 共享工作空间 (跨Agent协作)

- **功能**: ResearchAgent → ContentMaterialAgent 数据流转
- **共享类型**: 研究结果、框架、内容等
- **TTL**: 默认3小时（可配置）

```python
# ResearchAgent发布数据
await research_agent.share_data(
    data_type="research_result",
    data_key="页面标题",
    data_content=research_data,
    target_agents=["ContentMaterialAgent"],
    ttl_minutes=180
)

# ContentMaterialAgent获取数据
shared_data = await content_agent.get_shared_data(
    data_type="research_result",
    data_key="页面标题"
)
```

### 4. 任务状态追踪 (MasterCoordinator)

- **功能**: 记录任务执行状态和进度
- **追踪内容**: 阶段完成情况、耗时、错误等
- **应用场景**: 任务恢复、性能分析

## 快速开始

### 环境配置

创建 `.env` 文件：

```bash
# 启用记忆系统（默认: true）
USE_AGENT_MEMORY=true

# 研究缓存配置
RESEARCH_CACHE_TTL_DAYS=7

# 内容缓存配置
ENABLE_CONTENT_CACHE=true
CONTENT_CACHE_TTL_HOURS=24

# 性能追踪
ENABLE_PERFORMANCE_TRACKING=true
ENABLE_TASK_MEMORY=true

# 偏好学习
ENABLE_PREFERENCE_LEARNING=true
MIN_SAMPLES_FOR_LEARNING=3

# 语义搜索
ENABLE_SEMANTIC_SEARCH=true
```

### 代码集成

```python
from agents.orchestrator import master_coordinator_agent

# 使用带记忆的版本（通过环境变量自动选择）
# 如果 USE_AGENT_MEMORY=true，使用记忆增强版
# 如果 USE_AGENT_MEMORY=false，使用原始版本
agent = master_coordinator_agent

# 执行任务
result = await agent.run_async(ctx)
```

## API参考

### AgentMemoryMixin

所有带记忆的Agent都继承此混入类：

#### 基础记忆方法

```python
# 保存记忆
await agent.remember(
    key="my_key",              # 记忆键
    value={"data": "value"},   # 记忆值
    importance=0.7,            # 重要性 (0-1)
    scope="TASK",              # 作用域: TASK/USER/WORKSPACE/SESSION
    tags=["tag1", "tag2"]      # 标签
)

# 召回记忆
value = await agent.recall(
    key="my_key",
    scope="TASK",
    search_all_layers=True     # 是否搜索所有层
)

# 删除记忆
await agent.forget(
    key="my_key",
    scope="TASK"
)
```

#### 共享工作空间方法

```python
# 共享数据
data_id = await agent.share_data(
    data_type="research_result",
    data_key="unique_key",
    data_content={"data": "content"},
    target_agents=["OtherAgent"],
    ttl_minutes=60
)

# 获取共享数据
data = await agent.get_shared_data(
    data_type="research_result",
    data_key="unique_key"
)

# 列出共享数据
data_list = await agent.list_shared_data(
    data_type="research_result"  # None表示所有类型
)
```

#### 用户偏好方法

```python
# 获取用户偏好
preferences = await agent.get_user_preferences(
    user_id="user_123"
)
# 返回: {"default_slides": 15, "language": "ZH-CN", ...}

# 更新用户偏好
await agent.update_user_preferences(
    user_id="user_123",
    updates={"default_slides": 20, "style": "专业"}
)

# 增加偏好计数（用于统计）
await agent.increment_preference_counter(
    user_id="user_123",
    preference_key="page_num_15"
)
```

#### 决策记录方法

```python
# 记录决策
await agent.record_decision(
    decision_type="tool_selection",
    selected_action="use_cached_research",
    context={"page_title": "AI技术", "age_days": 3},
    reasoning="使用3天前的缓存研究，节省API调用",
    confidence_score=0.9,
    alternatives=["perform_new_research", "use_shared_research"]
)

# 获取相似决策（用于参考）
similar_decisions = await agent.get_similar_decisions(
    context={"page_title": "AI技术"},
    limit=5
)
```

## 架构设计

### 集成模式

采用 **Mixin 模式** 实现记忆能力：

```python
class ResearchAgentWithMemory(AgentMemoryMixin, OptimizedResearchAgent):
    """
    继承顺序：
    1. AgentMemoryMixin - 提供记忆方法
    2. OptimizedResearchAgent - 原始Agent功能
    """
    pass
```

### 作用域设计

| 作用域 | 说明 | 生命周期 | 示例 |
|--------|------|----------|------|
| TASK | 任务级 | 单个任务 | 阶段状态、进度 |
| USER | 用户级 | 跨任务 | 用户偏好、研究缓存 |
| WORKSPACE | 工作空间 | 会话内 | 共享数据 |
| SESSION | 会话级 | 单次会话 | 临时状态 |

### 数据流转

```
用户请求 → RequirementParserAgent (学习偏好)
         ↓
    FrameworkDesignerAgent
         ↓
    ResearchAgent (缓存研究) → 共享工作空间
         ↓                        ↓
    ContentMaterialAgent ←──────┘ (使用共享研究)
         ↓
    TemplateRendererAgent
         ↓
    MasterCoordinator (记录任务状态)
```

## 性能优化

### 缓存策略

1. **研究缓存**: 7天TTL，避免重复搜索
2. **内容缓存**: 24小时TTL，加速重复内容生成
3. **L1自动清理**: 基于LRU策略
4. **L2→L3提升**: 高价值数据自动持久化

### 性能指标

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 研究API调用 | 100% | 70% | -30% |
| 重复请求响应 | 100% | 10-50% | +50-90% |
| 跨Agent数据传递 | 通过ctx.state | 共享工作空间 | 更快 |

## 监控与调试

### 查看记忆统计

```python
# 获取记忆系统统计
from cognition.memory.core.core.hierarchical_memory_manager import (
    get_global_memory_manager,
)

manager = get_global_memory_manager()
stats = await manager.get_stats()

print(f"L1数据量: {stats['l1_transient']['data_count']}")
print(f"L2命中数: {stats['l2_short_term']['hits']}")
print(f"L3记录数: {stats['l3_long_term']['total_records']}")
```

### 查看Agent统计

```python
# ResearchAgent
print(f"缓存命中: {research_agent.stats['cache_hits']}")
print(f"新研究: {research_agent.stats['new_research']}")

# ContentMaterialAgent
print(f"共享研究使用: {content_agent.stats['shared_research_used']}")

# MasterCoordinator
print(f"总任务数: {coordinator.stats['total_tasks']}")
print(f"完成任务数: {coordinator.stats['completed_tasks']}")
```

### 日志级别

```python
import logging

# 设置日志级别
logging.getLogger("agents").setLevel(logging.DEBUG)
logging.getLogger("cognition.memory").setLevel(logging.DEBUG)
```

## 故障排查

### 记忆系统不可用

**症状**: Agent记忆功能不生效

**解决方案**:
1. 检查环境变量: `USE_AGENT_MEMORY=true`
2. 检查记忆系统安装: `pip install -e backend/cognition/memory/`
3. 查看日志: `grep "记忆" logs/agent.log`

### 缓存未命中

**症状**: 相同请求每次都执行完整流程

**解决方案**:
1. 检查缓存键是否一致
2. 检查缓存是否过期 (RESEARCH_CACHE_TTL_DAYS)
3. 查看记忆统计验证缓存写入

### 共享数据获取失败

**症状**: ContentMaterialAgent无法获取ResearchAgent共享的数据

**解决方案**:
1. 检查是否使用相同的task_id/session_id
2. 检查数据TTL是否过期
3. 查看共享工作空间日志

## 最佳实践

### 1. 选择合适的作用域

```python
# ✅ 正确: 用户偏好使用USER作用域
await agent.remember(key="user_pref", value=pref, scope="USER")

# ❌ 错误: 用户偏好使用TASK作用域（任务结束后丢失）
await agent.remember(key="user_pref", value=pref, scope="TASK")
```

### 2. 设置合适的TTL

```python
# 研究数据: 7天（研究有一定时效性）
await agent.share_data(..., ttl_minutes=7 * 24 * 60)

# 共享框架: 3小时（单次任务内使用）
await agent.share_data(..., ttl_minutes=3 * 60)
```

### 3. 使用决策记录

```python
# 记录重要决策以便分析
await agent.record_decision(
    decision_type="research_reuse",
    selected_action="use_cached_research",
    context={...},
    reasoning="详细说明决策原因",
    confidence_score=0.9
)
```

### 4. 定期清理过期数据

```python
# 清理指定作用域
await agent.memory_manager.clear_scope(
    scope=MemoryScope.TASK,
    scope_id=task_id,
    layers=[MemoryLayer.L1_TRANSIENT, MemoryLayer.L2_SHORT_TERM]
)
```

## 测试

运行测试：

```bash
cd backend
pytest agents/tests/test_agent_memory_integration.py -v
```

测试覆盖率：

```bash
pytest agents/tests/test_agent_memory_integration.py --cov=agents --cov-report=html
```

## 回滚方案

如需禁用记忆系统：

```bash
# 方法1: 环境变量
export USE_AGENT_MEMORY=false

# 方法2: 代码中
from agents.core.research import optimized_research_agent
agent = optimized_research_agent  # 直接使用原始版本
```

## 进阶话题

### 自定义记忆策略

```python
class CustomAgentWithMemory(AgentMemoryMixin, YourAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 自定义缓存时长
        self.custom_ttl_days = 30

        # 自定义统计
        self.custom_stats = {"metric1": 0, "metric2": 0}
```

### 向量语义搜索

```python
# 使用向量检索相似研究
similar_research = await agent.memory_manager.semantic_search(
    query_embedding=embedding,
    scope=MemoryScope.USER,
    scope_id=user_id,
    limit=5,
    min_importance=0.5
)
```

## 贡献指南

如需扩展记忆功能：

1. 继承 `AgentMemoryMixin`
2. 实现新的记忆方法
3. 添加单元测试
4. 更新文档

## 相关链接

- [记忆系统架构文档](../../cognition/memory/core/README.md)
- [Agent开发指南](./README.md)
- [API文档](../../docs/api.md)
