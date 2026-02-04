# 关键文件清单和测试重点

> **版本**: 1.0
> **更新日期**: 2025-02-04

---

## 目录

- [Utils层关键文件](#utils层关键文件)
- [Infrastructure层关键文件](#infrastructure层关键文件)
- [Domain层关键文件](#domain层关键文件)
- [Cognition层关键文件](#cognition层关键文件)
- [Tools层关键文件](#tools层关键文件)
- [Agents层关键文件](#agents层关键文件)
- [Services/API层关键文件](#servicesapi层关键文件)
- [测试命令参考](#测试命令参考)

---

## Utils层关键文件

### 1. 配置管理

**文件**: `backend/utils/common/config.py` / `backend/infrastructure/config/common_config.py`

**测试要点**:
- ✅ 从环境变量加载配置
- ✅ 默认值设置
- ✅ 配置验证
- ✅ 类型转换

**测试文件位置**: `backend/utils/tests/test_config.py`

**示例**:
```python
def test_load_config_from_env():
    os.environ["API_KEY"] = "test_key"
    config = load_config()
    assert config.api_key == "test_key"

def test_config_defaults():
    config = load_config()
    assert config.debug is False
    assert config.max_retries == 3
```

### 2. 上下文压缩器

**文件**: `backend/utils/context_compressor.py`

**测试要点**:
- ✅ 幻灯片内容压缩
- ✅ Token节省计算
- ✅ 压缩质量验证
- ✅ 关键信息保留

**测试文件位置**: `backend/utils/tests/test_compressor.py`

### 3. 重试装饰器

**文件**: `backend/utils/common/retry_decorator.py` / `backend/infrastructure/llm/retry_decorator.py`

**测试要点**:
- ✅ 指数退避
- ✅ 最大重试次数
- ✅ 特定异常重试
- ✅ 重试间隔计算

**测试文件位置**: `backend/utils/tests/test_retry.py`

### 4. PPT生成工具

**文件**: `backend/utils/save_ppt/*.py`

**测试要点**:
- ✅ XML转PPT
- ✅ 幻灯片布局
- ✅ 图片插入
- ✅ 样式应用

**测试文件位置**: `backend/utils/save_ppt/tests/`

---

## Infrastructure层关键文件

### 1. LLM工厂

**文件**: `backend/infrastructure/llm/common_model_factory.py`

**测试要点**:
- ✅ 模型创建
- ✅ 降级机制
- ✅ 模型选择
- ✅ 配置验证

**测试文件位置**: `backend/infrastructure/llm/tests/test_factory.py`

**示例**:
```python
@pytest.mark.asyncio
async def test_create_model_with_fallback():
    model = create_model_with_fallback_simple(
        model="deepseek-chat",
        provider="deepseek",
        fallback_model="gpt-3.5-turbo"
    )

    # Mock主模型失败，使用降级
    with patch.object(model, 'generate_async') as mock_gen:
        mock_gen.side_effect = [Exception("API Error"), MagicMock(text="fallback result")]

        result = await model.generate_async("test prompt")
        assert result.text == "fallback result"
        assert mock_gen.call_count == 2
```

### 2. 缓存系统

**文件**: `backend/infrastructure/cache/agent_cache.py`

**测试要点**:
- ✅ 缓存存取
- ✅ TTL过期
- ✅ 缓存命中率
- ✅ 缓存清理

**测试文件位置**: `backend/infrastructure/cache/tests/test_cache.py`

### 3. Checkpoint管理

**文件**: `backend/infrastructure/checkpoint/checkpoint_manager.py`

**测试要点**:
- ✅ 保存检查点
- ✅ 加载检查点
- ✅ 版本管理
- ✅ 数据序列化/反序列化

**测试文件位置**: `backend/infrastructure/checkpoint/tests/test_manager.py`

### 4. 数据库连接

**文件**: `backend/infrastructure/database/connection_manager.py`

**测试要点**:
- ✅ 连接池管理
- ✅ 事务处理
- ✅ 连接重试
- ✅ 连接清理

**测试文件位置**: `backend/infrastructure/database/tests/test_connection.py`

### 5. MCP加载器

**文件**: `backend/infrastructure/mcp/mcp_loader.py`

**测试要点**:
- ✅ 工具加载
- ✅ 工具注册
- ✅ 错误处理
- ✅ 配置解析

**测试文件位置**: `backend/infrastructure/mcp/tests/test_loader.py`

---

## Domain层关键文件

### 1. 值对象 (Value Objects)

**文件**: `backend/domain/value_objects/requirement.py`, `framework.py`, `research.py`

**测试要点**:
- ✅ 创建验证
- ✅ 序列化/反序列化
- ✅ 不变性验证
- ✅ 相等性判断

**测试文件位置**: `backend/domain/tests/value_objects/`

**示例**:
```python
def test_requirement_validation():
    # 有效输入
    req = Requirement(
        ppt_topic="AI",
        page_num=10,
        scene=SceneType.BUSINESS_REPORT
    )
    assert req.ppt_topic == "AI"

    # 无效输入
    with pytest.raises(ValidationError):
        Requirement(ppt_topic="", page_num=10)

    with pytest.raises(ValidationError):
        Requirement(ppt_topic="AI", page_num=0)

def test_requirement_serialization():
    req = Requirement.with_defaults("AI", 10)
    data = req.to_dict()

    req2 = Requirement.from_dict(data)
    assert req == req2
```

### 2. 实体 (Entities)

**文件**: `backend/domain/entities/task.py`, `presentation.py`, `checkpoint.py`

**测试要点**:
- ✅ 实体创建
- ✅ 状态转换
- ✅ 进度更新
- ✅ 事件发射

**测试文件位置**: `backend/domain/tests/entities/`

**示例**:
```python
def test_task_stage_transition():
    task = Task(id="task_1", raw_input="Generate PPT")

    # 开始阶段
    task.start_stage(TaskStage.REQUIREMENT_PARSING)
    assert task.stages[TaskStage.REQUIREMENT_PARSING].status == TaskStatus.IN_PROGRESS

    # 更新进度
    task.update_stage_progress(TaskStage.REQUIREMENT_PARSING, 50)
    assert task.stages[TaskStage.REQUIREMENT_PARSING].progress == 50

    # 完成阶段
    task.complete_stage(TaskStage.REQUIREMENT_PARSING)
    assert task.stages[TaskStage.REQUIREMENT_PARSING].status == TaskStatus.COMPLETED

    # 验证事件
    events = task.get_pending_events()
    assert len(events) >= 2
```

### 3. 领域服务

**文件**: `backend/domain/services/task_progress_service.py`, `task_validation_service.py`

**测试要点**:
- ✅ 进度计算
- ✅ 验证逻辑
- ✅ 状态转换服务

**测试文件位置**: `backend/domain/tests/services/`

### 4. 领域事件

**文件**: `backend/domain/events/task_events.py`

**测试要点**:
- ✅ 事件创建
- ✅ 事件序列化
- ✅ 事件工厂

**测试文件位置**: `backend/domain/tests/events/`

---

## Cognition层关键文件

### 1. 提示词管理

**文件**: `backend/cognition/prompts/prompt_manager.py`

**测试要点**:
- ✅ 提示词获取
- ✅ 版本管理
- ✅ 模板变量
- ✅ 提示词缓存

**测试文件位置**: `backend/cognition/prompts/tests/test_manager.py`

**示例**:
```python
def test_prompt_manager():
    # 获取提示词
    prompt = PromptManager.get_prompt("planning", "v1")
    assert "主题拆分" in prompt

    # 使用模板变量
    prompt = PromptManager.get_prompt(
        "generation",
        page_num="3/10",
        research_doc="文档内容",
        language="EN-US"
    )
    assert "3/10" in prompt
    assert "EN-US" in prompt

    # 列出版本
    versions = PromptManager.list_versions("planning")
    assert "v1" in versions
```

### 2. 分层记忆管理器

**文件**: `backend/cognition/memory/core/hierarchical_memory_manager.py`

**测试要点**:
- ✅ L1/L2/L3存储
- ✅ 跨层检索
- ✅ 记忆提升
- ✅ 记忆淘汰

**测试文件位置**: `backend/cognition/memory/tests/test_manager.py`

### 3. 记忆服务

**文件**: `backend/cognition/memory/core/services/*.py`

**测试要点**:
- ✅ 决策记录服务
- ✅ 共享工作空间服务
- ✅ 上下文优化服务
- ✅ 用户偏好服务
- ✅ 工具反馈服务

**测试文件位置**: `backend/cognition/memory/tests/services/`

**示例** (参考已有测试):
```python
# backend/agents/tests/test_agent_memory_integration.py
# 已有的测试示例，可以作为参考编写类似测试
```

---

## Tools层关键文件

### 1. 工具注册表

**文件**: `backend/agents/tools/registry/unified_registry.py`

**测试要点**:
- ✅ 工具注册
- ✅ 工具获取
- ✅ 按类别列出
- ✅ 重复注册处理

**测试文件位置**: `backend/agents/tools/tests/test_registry.py`

### 2. 搜索工具

**文件**: `backend/agents/tools/search/document_search.py`

**测试要点**:
- ✅ 关键词搜索
- ✅ 结果限制
- ✅ 错误处理

**测试文件位置**: `backend/agents/tools/tests/search/test_document_search.py`

### 3. 媒体工具

**文件**: `backend/agents/tools/media/image_search.py`

**测试要点**:
- ✅ 图片搜索
- ✅ 图片下载
- ✅ URL验证

**测试文件位置**: `backend/agents/tools/tests/media/test_image_search.py`

### 4. 技能框架

**文件**: `backend/agents/tools/skills/*.py`

**测试要点**:
- ✅ @Skill装饰器
- ✅ 技能注册
- ✅ 技能加载
- ✅ 元数据管理

**测试文件位置**: `backend/agents/tools/tests/skills/`

---

## Agents层关键文件

### 1. 基础Agent类

**文件**: `backend/agents/core/base_agent_with_memory.py`

**测试要点**:
- ✅ 记忆操作
- ✅ 上下文管理
- ✅ 用户偏好
- ✅ 共享工作空间

**测试文件位置**: `backend/agents/core/tests/test_base_agent.py`

**已有参考**: `backend/agents/tests/test_agent_memory_integration.py`

### 2. 规划Agent

**文件**: `backend/agents/core/planning/topic_splitter_agent.py`

**测试要点**:
- ✅ 主题拆分
- ✅ LLM集成 (Mock)
- ✅ 输出验证

**测试文件位置**: `backend/agents/core/tests/planning/test_topic_splitter.py`

### 3. 研究Agent

**文件**: `backend/agents/core/research/parallel_research_agent.py`, `research_agent_with_memory.py`

**测试要点**:
- ✅ 并行执行
- ✅ 缓存机制
- ✅ 工具使用
- ✅ 错误恢复

**测试文件位置**: `backend/agents/core/tests/research/`

### 4. 生成Agent

**文件**: `backend/agents/core/generation/slide_writer_agent.py`, `content_material_agent_with_memory.py`

**测试要点**:
- ✅ 幻灯片生成
- ✅ 质量检查
- ✅ 重试机制
- ✅ 循环执行

**测试文件位置**: `backend/agents/core/tests/generation/`

### 5. 工作流编排

**文件**: `backend/agents/orchestrator/workflow_executor.py`

**测试要点**:
- ✅ 串行执行
- ✅ 并行执行
- ✅ DAG执行
- ✅ 进度跟踪

**测试文件位置**: `backend/agents/orchestrator/tests/test_executor.py`

---

## Services/API层关键文件

### 1. 服务层

**文件**: `backend/services/presentation_service.py`, `outline_service.py`

**测试要点**:
- ✅ 创建任务
- ✅ 生成流程
- ✅ 阶段编排
- ✅ 错误处理

**测试文件位置**: `backend/services/tests/test_presentation_service.py`

### 2. API路由

**文件**: `backend/api/routes/presentation.py`

**测试要点**:
- ✅ 端点响应
- ✅ 请求验证
- ✅ 错误响应
- ✅ 状态码

**测试文件位置**: `backend/api/tests/test_routes.py`

**示例**:
```python
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_create_presentation_endpoint():
    response = client.post(
        "/presentation/create",
        json={
            "outline": "AI技术介绍",
            "num_slides": 10,
            "language": "ZH-CN"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "presentation_id" in data

def test_get_progress_endpoint():
    # 先创建任务
    create_response = client.post("/presentation/create", json={...})
    task_id = create_response.json()["presentation_id"]

    # 查询进度
    response = client.get(f"/presentation/progress/{task_id}")
    assert response.status_code == 200

    data = response.json()
    assert "progress" in data
    assert "status" in data
```

### 3. 端到端测试

**文件**: `backend/tests/e2e/test_full_workflow.py`

**测试要点**:
- ✅ 完整PPT生成流程
- ✅ Checkpoint恢复
- ✅ 错误恢复

**测试文件位置**: `backend/tests/e2e/`

---

## 测试命令参考

### 运行所有测试

```bash
# 运行所有测试
pytest

# 详细输出
pytest -v

# 显示打印输出
pytest -s
```

### 运行特定层测试

```bash
# Utils层
pytest backend/utils/tests/

# Infrastructure层
pytest backend/infrastructure/tests/

# Domain层
pytest backend/domain/tests/

# Cognition层
pytest backend/cognition/tests/

# Tools层
pytest backend/agents/tools/tests/

# Agents层
pytest backend/agents/core/tests/

# Services/API层
pytest backend/services/tests/ backend/api/tests/
```

### 运行特定文件

```bash
# 测试单个文件
pytest backend/domain/tests/entities/test_task.py

# 测试单个类
pytest backend/domain/tests/entities/test_task.py::TestTask

# 测试单个方法
pytest backend/domain/tests/entities/test_task.py::TestTask::test_task_creation
```

### 使用标记

```bash
# 运行带特定标记的测试
pytest -m unit
pytest -m integration
pytest -m slow
pytest -m "not slow"
```

### 覆盖率报告

```bash
# 生成覆盖率报告
pytest --cov=backend --cov-report=html

# 生成终端报告
pytest --cov=backend --cov-report=term-missing

# 设置覆盖率阈值
pytest --cov=backend --cov-fail-under=70
```

### 并行运行

```bash
# 安装pytest-xdist
pip install pytest-xdist

# 使用多进程运行
pytest -n auto

# 指定进程数
pytest -n 4
```

### 只运行失败的测试

```bash
# 只运行上次失败的测试
pytest --lf

# 先运行失败的，然后运行其他
pytest --ff
```

### 停止在第一个失败

```bash
# 第一个失败后停止
pytest -x

# N个失败后停止
pytest --maxfail=3
```

---

## 测试文件结构建议

```
backend/
├── utils/
│   └── tests/
│       ├── __init__.py
│       ├── test_config.py
│       ├── test_compressor.py
│       └── test_retry.py
├── infrastructure/
│   └── tests/
│       ├── llm/
│       │   └── test_factory.py
│       ├── cache/
│       │   └── test_cache.py
│       ├── checkpoint/
│       │   └── test_manager.py
│       └── database/
│           └── test_connection.py
├── domain/
│   └── tests/
│       ├── value_objects/
│       │   ├── test_requirement.py
│       │   └── test_framework.py
│       ├── entities/
│       │   ├── test_task.py
│       │   └── test_presentation.py
│       ├── services/
│       │   └── test_task_validation.py
│       └── events/
│           └── test_events.py
├── cognition/
│   └── tests/
│       ├── prompts/
│       │   └── test_manager.py
│       └── memory/
│           ├── test_manager.py
│           └── services/
│               └── test_services.py
├── agents/
│   ├── tools/
│   │   └── tests/
│   │       ├── test_registry.py
│   │       ├── search/
│   │       └── media/
│   ├── core/
│   │   └── tests/
│   │       ├── test_base_agent.py
│   │       ├── planning/
│   │       ├── research/
│   │       └── generation/
│   └── orchestrator/
│       └── tests/
│           └── test_executor.py
├── services/
│   └── tests/
│       └── test_presentation_service.py
├── api/
│   └── tests/
│       └── test_routes.py
└── tests/
    ├── conftest.py
    ├── fixtures/
    │   └── factories.py
    └── e2e/
        └── test_full_workflow.py
```

---

## 已有测试参考

### 参考文件

**位置**: `backend/agents/tests/test_agent_memory_integration.py`

**内容概要**:
- AgentMemoryMixin基础功能测试
- ResearchAgent缓存测试
- 共享工作空间测试
- 用户偏好测试
- 端到端集成测试
- 性能测试

**可复用的测试模式**:

1. **Mock Agent模式**
   ```python
   class MockLlmAgent:
       def __init__(self, name="MockAgent"):
           self.name = name
   ```

2. **异步测试模式**
   ```python
   @pytest.mark.asyncio
   async def test_async_operation():
       result = await async_function()
       assert result is not None
   ```

3. **Skip条件模式**
   ```python
   if not agent.is_memory_enabled():
       pytest.skip("Memory system not available")
   ```

---

## 总结

### 关键文件优先级

| 优先级 | 文件类型 | 数量 | 测试重点 |
|--------|---------|------|---------|
| 🔴 高 | Domain实体和值对象 | ~15 | 业务逻辑验证 |
| 🔴 高 | 记忆系统核心 | ~10 | 异步存储检索 |
| 🟠 中 | Agent基类 | ~5 | 记忆集成 |
| 🟠 中 | 工作流编排 | ~3 | 并发执行 |
| 🟡 中 | LLM工厂 | ~3 | 降级机制 |
| 🟡 中 | 工具注册表 | ~4 | 注册和调用 |
| 🟢 低 | Utils工具函数 | ~8 | 边界条件 |
| 🟢 低 | API路由 | ~5 | 端到端 |

### 测试文件创建顺序

```
Week 1-2:
1. backend/utils/tests/
2. backend/infrastructure/tests/

Week 3:
3. backend/domain/tests/
4. backend/cognition/tests/

Week 4:
5. backend/agents/tools/tests/
6. backend/agents/core/tests/

Week 5:
7. backend/services/tests/
8. backend/api/tests/
9. backend/tests/e2e/
```

---

**维护者**: MultiAgentPPT Team
**版本**: 1.0
**最后更新**: 2025-02-04
