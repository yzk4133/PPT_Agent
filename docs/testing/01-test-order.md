# 测试顺序详细说明

> **版本**: 1.0
> **更新日期**: 2025-02-04

---

## 目录

- [概述](#概述)
- [依赖关系分析](#依赖关系分析)
- [阶段详细说明](#阶段详细说明)
- [测试里程碑](#测试里程碑)
- [模块依赖图](#模块依赖图)

---

## 概述

本文档详细说明 MultiAgentPPT 后端模块的7阶段测试顺序，以及为什么这样安排。

### 为什么需要测试顺序？

1. **依赖关系**: 上层依赖下层，下层测试通过后才能测试上层
2. **快速反馈**: 优先测试基础模块，可以更快发现问题
3. **逐步验证**: 从简单到复杂，逐步构建信心
4. **减少调试**: 基础模块问题会影响上层，先测试可以减少重复调试

### 测试顺序原则

```
依赖方向: 上层 → 下层
测试方向: 下层 → 上层

Utils → Infrastructure → Domain → Cognition → Tools → Agents → Services/API
```

---

## 依赖关系分析

### 层级依赖矩阵

| 层 | 依赖的层 | 无依赖模块 | 测试优先级 |
|----|---------|-----------|-----------|
| Utils | 无 | 所有工具函数 | **1** (最高) |
| Infrastructure | Utils | 配置、日志 | **2** |
| Domain | Utils, Infrastructure | 值对象、实体 | **3** |
| Cognition | Utils, Domain | 提示词模板 | **4** |
| Tools | Infrastructure, Domain | 工具注册表 | **5** |
| Agents | Cognition, Tools, Domain | Agent基类 | **6** |
| Services/API | Agents, Domain | - | **7** (最低) |

### 循环依赖检测

**当前架构无循环依赖** ✅

验证方法：
```
如果 A → B 且 B → A，则存在循环依赖
检查: 无此情况
```

---

## 阶段详细说明

### 阶段 1: Utils 层 (第1-2天)

**优先级**: 🔴 最高
**测试类型**: 单元测试
**无外部依赖**

#### 1.1 配置管理

**文件**: `backend/utils/common/config.py`

```python
# 测试要点
class TestConfig:
    def test_load_config_from_env(self):
        """测试从环境变量加载配置"""

    def test_config_defaults(self):
        """测试默认值"""

    def test_config_validation(self):
        """测试配置验证"""
```

#### 1.2 上下文压缩器

**文件**: `backend/utils/context_compressor.py`

```python
# 测试要点
class TestContextCompressor:
    def test_compress_slides(self):
        """测试幻灯片压缩"""

    def test_token_savings_calculation(self):
        """测试Token节省计算"""

    def test_compression_quality(self):
        """测试压缩质量"""
```

#### 1.3 重试装饰器

**文件**: `backend/utils/common/retry_decorator.py`

```python
# 测试要点
class TestRetryDecorator:
    def test_retry_on_exception(self):
        """测试异常重试"""

    def test_exponential_backoff(self):
        """测试指数退避"""

    def test_max_retries_limit(self):
        """测试最大重试次数"""
```

#### 1.4 PPT生成工具

**文件**: `backend/utils/save_ppt/*.py`

```python
# 测试要点
class TestPPTGenerator:
    def test_xml_to_ppt_conversion(self):
        """测试XML转PPT"""

    def test_slide_layout(self):
        """测试幻灯片布局"""

    def test_image_insertion(self):
        """测试图片插入"""
```

**完成标准**:
- ✅ 覆盖率 ≥ 80%
- ✅ 所有核心函数有测试
- ✅ 边界条件覆盖

---

### 阶段 2: Infrastructure 层 (第3-5天)

**优先级**: 🟠 高
**测试类型**: 单元测试 + 集成测试
**依赖**: Utils层

#### 2.1 LLM工厂和降级

**文件**: `backend/infrastructure/llm/*.py`

```python
# 测试要点
class TestLLMFactory:
    @pytest.mark.asyncio
    async def test_create_model(self):
        """测试模型创建"""

    async def test_fallback_mechanism(self):
        """测试降级机制"""

    async def test_model_selection(self):
        """测试模型选择"""
```

#### 2.2 缓存系统

**文件**: `backend/infrastructure/cache/agent_cache.py`

```python
# 测试要点
class TestAgentCache:
    def test_cache_set_get(self):
        """测试缓存存取"""

    def test_cache_expiration(self):
        """测试缓存过期"""

    def test_cache_hit_rate(self):
        """测试缓存命中率"""
```

#### 2.3 Checkpoint管理

**文件**: `backend/infrastructure/checkpoint/*.py`

```python
# 测试要点
class TestCheckpointManager:
    def test_save_checkpoint(self):
        """测试保存检查点"""

    def test_load_checkpoint(self):
        """测试加载检查点"""

    def test_checkpoint_versioning(self):
        """测试检查点版本管理"""
```

#### 2.4 数据库连接

**文件**: `backend/infrastructure/database/*.py`

```python
# 测试要点
class TestDatabaseConnection:
    @pytest.fixture
    async def db_session(self):
        """使用SQLite内存数据库"""

    async def test_connection_pool(self):
        """测试连接池"""

    async def test_transaction_rollback(self):
        """测试事务回滚"""
```

#### 2.5 日志配置

**文件**: `backend/infrastructure/logging/logger_config.py`

```python
# 测试要点
class TestLoggerConfig:
    def test_logger_creation(self):
        """测试日志创建"""

    def test_log_levels(self):
        """测试日志级别"""

    def test_log_rotation(self):
        """测试日志轮转"""
```

#### 2.6 MCP加载器

**文件**: `backend/infrastructure/mcp/mcp_loader.py`

```python
# 测试要点
class TestMCPLoader:
    def test_load_mcp_tools(self):
        """测试加载MCP工具"""

    def test_tool_registration(self):
        """测试工具注册"""

    def test_error_handling(self):
        """测试错误处理"""
```

**完成标准**:
- ✅ 覆盖率 ≥ 70%
- ✅ Mock所有外部服务
- ✅ 异常处理测试

---

### 阶段 3: Domain 层 (第6-8天)

**优先级**: 🟡 中高
**测试类型**: 单元测试
**依赖**: Utils, Infrastructure (部分)

#### 3.1 值对象 (Value Objects)

**文件**: `backend/domain/value_objects/*.py`

```python
# 测试要点
class TestRequirement:
    def test_requirement_creation(self):
        """测试需求创建"""

    def test_requirement_validation(self):
        """测试需求验证"""

    def test_requirement_serialization(self):
        """测试序列化"""

class TestPPTFramework:
    def test_framework_creation(self):
        """测试框架创建"""

    def test_page_definition(self):
        """测试页面定义"""

    def test_framework_validation(self):
        """测试框架验证"""
```

#### 3.2 实体 (Entities)

**文件**: `backend/domain/entities/*.py`

```python
# 测试要点
class TestTask:
    def test_task_creation(self):
        """测试任务创建"""

    def test_stage_transition(self):
        """测试阶段转换"""

    def test_progress_calculation(self):
        """测试进度计算"""

    def test_event_emission(self):
        """测试事件发射"""

class TestPresentation:
    def test_presentation_status(self):
        """测试演示文稿状态"""

    def test_presentation_progress(self):
        """测试进度更新"""
```

#### 3.3 领域服务

**文件**: `backend/domain/services/*.py`

```python
# 测试要点
class TestTaskProgressService:
    def test_calculate_overall_progress(self):
        """测试总体进度计算"""

    def test_calculate_stage_progress(self):
        """测试阶段进度计算"""

class TestTaskValidationService:
    def test_validate_requirement(self):
        """测试需求验证"""

    def test_validate_framework(self):
        """测试框架验证"""

    def test_validate_task_transition(self):
        """测试状态转换验证"""
```

#### 3.4 领域事件

**文件**: `backend/domain/events/*.py`

```python
# 测试要点
class TestTaskEvents:
    def test_event_creation(self):
        """测试事件创建"""

    def test_event_serialization(self):
        """测试事件序列化"""

    def test_event_factory(self):
        """测试事件工厂"""
```

#### 3.5 领域异常

**文件**: `backend/domain/exceptions/*.py`

```python
# 测试要点
class TestDomainExceptions:
    def test_validation_error(self):
        """测试验证异常"""

    def test_state_transition_error(self):
        """测试状态转换异常"""

    def test_error_message_format(self):
        """测试错误消息格式"""
```

**完成标准**:
- ✅ 覆盖率 ≥ 85%
- ✅ 所有业务规则验证
- ✅ 边界条件和异常路径

---

### 阶段 4: Cognition 层 (第9-12天)

**优先级**: 🟡 中
**测试类型**: 单元测试 + 集成测试
**依赖**: Utils, Domain

#### 4.1 提示词管理

**文件**: `backend/cognition/prompts/*.py`

```python
# 测试要点
class TestPromptManager:
    def test_get_prompt(self):
        """测试获取提示词"""

    def test_prompt_versioning(self):
        """测试提示词版本管理"""

    def test_prompt_template_variables(self):
        """测试模板变量"""

    def test_prompt_caching(self):
        """测试提示词缓存"""
```

#### 4.2 记忆系统核心

**文件**: `backend/cognition/memory/core/*.py`

```python
# 测试要点
class TestHierarchicalMemoryManager:
    @pytest.mark.asyncio
    async def test_store_to_transient(self):
        """测试存储到瞬时记忆"""

    async def test_store_to_short_term(self):
        """测试存储到短期记忆"""

    async def test_store_to_long_term(self):
        """测试存储到长期记忆"""

    async def test_retrieve_from_layers(self):
        """测试从各层检索"""

    async def test_memory_promotion(self):
        """测试记忆提升"""

class TestDatabaseBackend:
    @pytest.mark.asyncio
    async def test_save_memory(self):
        """测试保存记忆到数据库"""

    async def test_load_memory(self):
        """测试从数据库加载记忆"""

    async def test_delete_memory(self):
        """测试删除记忆"""
```

#### 4.3 记忆服务

**文件**: `backend/cognition/memory/core/services/*.py`

```python
# 测试要点
class TestAgentDecisionService:
    @pytest.mark.asyncio
    async def test_record_decision(self):
        """测试记录决策"""

    async def test_get_decision_history(self):
        """测试获取决策历史"""

class TestSharedWorkspaceService:
    @pytest.mark.asyncio
    async def test_share_data(self):
        """测试共享数据"""

    async def test_get_shared_data(self):
        """测试获取共享数据"""

    async def test_data_expiration(self):
        """测试数据过期"""

class TestContextOptimizer:
    @pytest.mark.asyncio
    async def test_optimize_context(self):
        """测试上下文优化"""

    async def test_context_compression(self):
        """测试上下文压缩"""
```

**完成标准**:
- ✅ 覆盖率 ≥ 75%
- ✅ 使用Mock数据库
- ✅ 异步操作测试

---

### 阶段 5: Tools 层 (第13-15天)

**优先级**: 🟢 中低
**测试类型**: 单元测试
**依赖**: Infrastructure, Domain

#### 5.1 工具注册表

**文件**: `backend/agents/tools/registry/*.py`

```python
# 测试要点
class TestUnifiedToolRegistry:
    def test_register_tool(self):
        """测试工具注册"""

    def test_get_tool(self):
        """测试获取工具"""

    def test_list_tools_by_category(self):
        """测试按类别列出工具"""

    def test_tool_metadata(self):
        """测试工具元数据"""

    def test_duplicate_registration(self):
        """测试重复注册"""
```

#### 5.2 搜索工具

**文件**: `backend/agents/tools/search/document_search.py`

```python
# 测试要点
class TestDocumentSearch:
    @pytest.mark.asyncio
    async def test_search_by_keyword(self):
        """测试关键词搜索"""

    async def test_search_results_limit(self):
        """测试结果限制"""

    async def test_search_error_handling(self):
        """测试搜索错误处理"""
```

#### 5.3 媒体工具

**文件**: `backend/agents/tools/media/image_search.py`

```python
# 测试要点
class TestImageSearch:
    @pytest.mark.asyncio
    async def test_search_images(self):
        """测试图片搜索"""

    async def test_image_filtering(self):
        """测试图片过滤"""

    async def test_download_image(self):
        """测试图片下载"""
```

#### 5.4 技能框架

**文件**: `backend/agents/tools/skills/*.py`

```python
# 测试要点
class TestSkillFramework:
    def test_skill_decorator(self):
        """测试@Skill装饰器"""

    def test_skill_registration(self):
        """测试技能注册"""

    def test_skill_metadata(self):
        """测试技能元数据"""

    def test_skill_loading(self):
        """测试技能加载"""
```

**完成标准**:
- ✅ 覆盖率 ≥ 70%
- ✅ Mock外部API
- ✅ 错误处理测试

---

### 阶段 6: Agents 层 (第16-20天)

**优先级**: 🟢 中低
**测试类型**: 单元测试 + 集成测试
**依赖**: Cognition, Tools, Domain

#### 6.1 基础Agent类

**文件**: `backend/agents/core/base_agent_with_memory.py`

```python
# 测试要点
class TestAgentMemoryMixin:
    @pytest.mark.asyncio
    async def test_memory_operations(self):
        """测试记忆操作"""

    async def test_context_management(self):
        """测试上下文管理"""

    async def test_user_preferences(self):
        """测试用户偏好"""

    async def test_shared_workspace(self):
        """测试共享工作空间"""
```

#### 6.2 规划Agent

**文件**: `backend/agents/core/planning/*.py`

```python
# 测试要点
class TestTopicSplitterAgent:
    @pytest.mark.asyncio
    async def test_split_topics(self):
        """测试主题拆分"""

    async def test_topic_validation(self):
        """测试主题验证"""

    async def test_llm_integration(self):
        """测试LLM集成 (使用Mock)"""
```

#### 6.3 研究Agent

**文件**: `backend/agents/core/research/*.py`

```python
# 测试要点
class TestParallelResearchAgent:
    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """测试并行执行"""

    async def test_research_caching(self):
        """测试研究缓存"""

    async def test_tool_usage(self):
        """测试工具使用"""

    async def test_error_recovery(self):
        """测试错误恢复"""
```

#### 6.4 生成Agent

**文件**: `backend/agents/core/generation/*.py`

```python
# 测试要点
class TestSlideWriterAgent:
    @pytest.mark.asyncio
    async def test_generate_slide(self):
        """测试生成幻灯片"""

    async def test_quality_checking(self):
        """测试质量检查"""

    async def test_retry_mechanism(self):
        """测试重试机制"""

    async def test_loop_execution(self):
        """测试循环执行"""
```

**完成标准**:
- ✅ 覆盖率 ≥ 70%
- ✅ Mock LLM调用
- ✅ 并发测试
- ✅ 集成测试

---

### 阶段 7: Services & API 层 (第21-24天)

**优先级**: 🔵 低
**测试类型**: 集成测试 + 端到端测试
**依赖**: Agents, Domain

#### 7.1 服务层

**文件**: `backend/services/*.py`

```python
# 测试要点
class TestPresentationService:
    @pytest.mark.asyncio
    async def test_create_presentation(self):
        """测试创建演示文稿"""

    async def test_generate_presentation(self):
        """测试生成演示文稿"""

    async def test_stage_orchestration(self):
        """测试阶段编排"""

    async def test_error_handling(self):
        """测试错误处理"""

class TestOutlineService:
    @pytest.mark.asyncio
    async def test_generate_outline(self):
        """测试生成大纲"""

    async def test_outline_validation(self):
        """测试大纲验证"""
```

#### 7.2 工作流编排

**文件**: `backend/agents/orchestrator/*.py`

```python
# 测试要点
class TestWorkflowExecutor:
    @pytest.mark.asyncio
    async def test_sequential_execution(self):
        """测试串行执行"""

    async def test_parallel_execution(self):
        """测试并行执行"""

    async def test_workflow_dag(self):
        """测试工作流DAG"""

    async def test_checkpoint_recovery(self):
        """测试检查点恢复"""

    async def test_progress_tracking(self):
        """测试进度跟踪"""
```

#### 7.3 API路由

**文件**: `backend/api/routes/*.py`

```python
# 测试要点
class TestPresentationAPI:
    @pytest.mark.asyncio
    async def test_create_presentation_endpoint(self):
        """测试创建演示文稿端点"""

    async def test_get_progress_endpoint(self):
        """测试获取进度端点"""

    async def test_get_detail_endpoint(self):
        """测试获取详情端点"""

    async def test_error_responses(self):
        """测试错误响应"""

    async def test_request_validation(self):
        """测试请求验证"""
```

#### 7.4 端到端测试

**文件**: `backend/tests/e2e/*.py`

```python
# 测试要点
class TestE2E:
    @pytest.mark.asyncio
    async def test_full_ppt_generation(self):
        """测试完整PPT生成流程"""

        # 1. 创建任务
        # 2. 需求解析
        # 3. 框架设计
        # 4. 并行研究
        # 5. 内容生成
        # 6. PPT渲染
        # 7. 验证输出

    async def test_checkpoint_recovery_flow(self):
        """测试检查点恢复流程"""

    async def test_error_recovery_flow(self):
        """测试错误恢复流程"""
```

**完成标准**:
- ✅ 覆盖率 ≥ 60%
- ✅ 完整流程测试
- ✅ 错误场景测试
- ✅ 性能测试

---

## 测试里程碑

| 里程碑 | 完成阶段 | 交付物 | 验收标准 |
|--------|---------|--------|---------|
| M1: 基础设施 | 阶段1-2 | Utils, Infrastructure测试 | 覆盖率≥75%, CI通过 |
| M2: 领域核心 | 阶段3-4 | Domain, Cognition测试 | 覆盖率≥80%, 业务规则覆盖 |
| M3: 工具Agent | 阶段5-6 | Tools, Agents测试 | 覆盖率≥70%, 并发测试通过 |
| M4: 系统集成 | 阶段7 | Services, API, E2E测试 | 覆盖率≥60%, 端到端流程通过 |

---

## 模块依赖图

### 高层依赖图

```
┌─────────────────────────────────────────────────────────┐
│                    Services / API Layer                 │
│                   (阶段7: 最后测试)                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                      Agents Layer                        │
│                   (阶段6: 倒数第2)                        │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Tools   │ Planning │ Research  │Generation│  Orchestr.  │
│  (阶段5) │  (阶段6) │  (阶段6)  │  (阶段6)  │   (阶段7)    │
└──────────┴──────────┴──────────┴──────────┴─────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                    Cognition Layer                      │
│                   (阶段4: 中期测试)                       │
├───────────────────────────┬─────────────────────────────┤
│      Prompts              │        Memory              │
└───────────────────────────┴─────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                     Domain Layer                        │
│                   (阶段3: 早期测试)                       │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│ Entities │  Value   │ Services │  Events  │ Exceptions  │
│          │ Objects  │          │          │             │
└──────────┴──────────┴──────────┴──────────┴─────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                 Infrastructure Layer                     │
│                   (阶段2: 早期测试)                       │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│   LLM    │  Cache   │   DB     │ Checkpt  │     MCP     │
└──────────┴──────────┴──────────┴──────────┴─────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                      Utils Layer                         │
│                   (阶段1: 首先测试)                       │
└──────────────────────────────────────────────────────────┘
```

### 详细依赖关系

```
Utils (无依赖)
  ↓
Infrastructure → Utils
  ↓
Domain → Utils, Infrastructure(部分)
  ↓
Cognition → Utils, Domain
  ↓
Tools → Infrastructure, Domain
  ↓
Agents → Cognition, Tools, Domain
  ↓
Services/API → Agents, Domain, Orchestrator
```

---

## 测试优先级说明

### 为什么这样排序？

1. **Utils 层最先测试**
   - 无外部依赖
   - 纯函数逻辑
   - 快速反馈
   - 所有上层都依赖它

2. **Infrastructure 第二**
   - 技术基础设施
   - 提供Mock能力
   - Domain层需要它

3. **Domain 第三**
   - 核心业务逻辑
   - 相对独立
   - Agents依赖它

4. **Cognition 第四**
   - 依赖Domain
   - Agents需要它
   - 需要Mock外部服务

5. **Tools 第五**
   - 支持Agent功能
   - 依赖Infrastructure
   - 相对独立

6. **Agents 第六**
   - 依赖最多
   - 最复杂
   - 需要所有下层准备就绪

7. **Services/API 最后**
   - 集成所有模块
   - 端到端测试
   - 依赖所有上层

---

## 测试时间线

```
Week 1-2:  Utils + Infrastructure          ████████░░ 80%
Week 3:    Domain Layer                    █████░░░░░ 50%
Week 4:    Cognition Layer                 ████░░░░░░░ 40%
Week 5:    Tools Layer                     ████░░░░░░░ 40%
Week 6-7:  Agents Layer                    ██████░░░░ 60%
Week 8:    Services/API + E2E              █████░░░░░ 50%
```

---

## 总结

### 关键要点

1. **自底向上**: 从无依赖模块开始
2. **依赖驱动**: 按依赖关系排序
3. **快速反馈**: 基础模块优先
4. **逐步集成**: 最后测试集成

### 常见问题

**Q: 可以跳过某个阶段吗？**
A: 不建议。每个阶段都有依赖，跳过会导致后续测试困难。

**Q: 可以并行测试多个阶段吗？**
A: 可以，但需要确保依赖的层已经测试通过。

**Q: 如果下层测试失败怎么办？**
A: 应该先修复下层问题，再继续上层测试。

---

**维护者**: MultiAgentPPT Team
**版本**: 1.0
**最后更新**: 2025-02-04
