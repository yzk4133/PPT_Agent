# 测试编写指南

> **版本**: 1.0
> **更新日期**: 2025-02-04

---

## 目录

- [多智能体系统测试注意事项](#多智能体系统测试注意事项)
- [异步代码测试最佳实践](#异步代码测试最佳实践)
- [外部依赖Mock策略](#外部依赖mock策略)
- [记忆系统测试方法](#记忆系统测试方法)
- [Checkpoint与恢复测试](#checkpoint与恢复测试)
- [测试Fixture管理](#测试fixture管理)
- [集成测试环境设置](#集成测试环境设置)
- [常用Mock工具介绍](#常用mock工具介绍)

---

## 多智能体系统测试注意事项

### 1. 并发测试

#### 测试Agent并行执行

```python
@pytest.mark.asyncio
async def test_parallel_agents_execution():
    """测试多个Agent并行执行"""
    from agents.core.research.parallel_research_agent import ParallelResearchAgent

    # 创建并行Agent
    agent = ParallelResearchAgent(name="TestParallelAgent")

    # 创建模拟上下文
    class MockContext:
        class MockSession:
            state = {
                "split_topics": json.dumps({
                    "topics": [
                        {"id": 1, "title": "主题1", "description": "描述1"},
                        {"id": 2, "title": "主题2", "description": "描述2"},
                    ]
                })
            }

        session = MockSession()

    ctx = MockContext()

    # Mock工具调用
    with patch('agents.tools.search.document_search.DocumentSearch') as mock_search:
        mock_search.return_value = ["结果1", "结果2"]

        # 执行并行任务
        result = await agent._run_async_impl(ctx)

        # 验证并发执行
        assert result is not None
        # 验证所有任务都被执行
```

#### 测试并发安全性

```python
@pytest.mark.asyncio
async def test_shared_workspace_concurrent_access():
    """测试共享工作空间的并发访问"""
    from cognition.memory.core.services.shared_workspace_service import (
        SharedWorkspaceService
    )

    service = SharedWorkspaceService()

    # 模拟多个Agent同时写入
    tasks = []
    for i in range(10):
        task = service.share_data(
            data_type="test",
            data_key=f"key_{i}",
            data_content={"value": i},
            ttl_minutes=60
        )
        tasks.append(task)

    # 并发执行
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 验证没有异常
    assert not any(isinstance(r, Exception) for r in results)

    # 验证数据一致性
    for i in range(10):
        data = await service.get_shared_data("test", f"key_{i}")
        assert data is not None
```

### 2. Agent间通信测试

#### 测试Agent间数据传递

```python
@pytest.mark.asyncio
async def test_agent_communication():
    """测试Agent间通信"""
    from agents.core.research.research_agent_with_memory import ResearchAgentWithMemory
    from agents.core.generation.content_material_agent_with_memory import ContentMaterialAgentWithMemory

    # 创建两个Agent
    research_agent = ResearchAgentWithMemory(name="ResearchAgent")
    content_agent = ContentMaterialAgentWithMemory(name="ContentAgent")

    # 设置相同上下文（模拟同一任务）
    user_id = "test_user"
    task_id = "test_task"

    research_agent.set_context(user_id=user_id, task_id=task_id)
    content_agent.set_context(user_id=user_id, task_id=task_id)

    # ResearchAgent共享数据
    research_data = {
        "page_title": "AI技术",
        "content": "研究内容",
        "source": "行业报告"
    }

    await research_agent.share_data(
        data_type="research_result",
        data_key="AI技术",
        data_content=research_data,
        target_agents=["ContentMaterialAgent"],
        ttl_minutes=180
    )

    # ContentMaterialAgent获取数据
    shared_data = await content_agent.get_shared_data(
        data_type="research_result",
        data_key="AI技术"
    )

    # 验证数据传递成功
    assert shared_data is not None
    assert shared_data["page_title"] == "AI技术"
    assert shared_data["content"] == "研究内容"
```

#### 测试Agent状态同步

```python
@pytest.mark.asyncio
async def test_agent_state_sync():
    """测试Agent状态同步"""
    from domain.entities import Task, TaskStage, TaskStatus

    # 创建任务
    task = Task(id="test_task", raw_input="Generate PPT")

    # Agent1更新状态
    task.start_stage(TaskStage.REQUIREMENT_PARSING)
    assert task.stages[TaskStage.REQUIREMENT_PARSING].status == TaskStatus.IN_PROGRESS

    # Agent2完成该阶段
    task.complete_stage(TaskStage.REQUIREMENT_PARSING)
    assert task.stages[TaskStage.REQUIREMENT_PARSING].status == TaskStatus.COMPLETED

    # 验证事件被触发
    events = task.get_pending_events()
    assert len(events) >= 2
```

### 3. Agent状态转换测试

```python
@pytest.mark.asyncio
async def test_agent_lifecycle():
    """测试Agent生命周期状态转换"""
    from agents.core.base_agent_with_memory import AgentMemoryMixin

    class TestAgent(AgentMemoryMixin):
        pass

    agent = TestAgent(name="TestAgent")

    # 测试初始状态
    assert agent.is_memory_enabled() in [True, False]

    # 测试上下文设置
    agent.set_context(user_id="test_user", task_id="test_task")
    assert agent.user_id == "test_user"
    assert agent.task_id == "test_task"

    # 测试记忆操作
    if agent.is_memory_enabled():
        await agent.remember(
            key="test_key",
            value="test_value",
            scope="TASK"
        )

        recalled = await agent.recall(key="test_key", scope="TASK")
        assert recalled == "test_value"
```

---

## 异步代码测试最佳实践

### 1. 使用 pytest-asyncio

#### 安装和配置

```bash
pip install pytest-asyncio
```

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
```

#### 基本异步测试

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """基本的异步测试"""
    result = await async_function()
    assert result == expected

@pytest.mark.asyncio
async def test_async_with_fixture(async_fixture):
    """使用fixture的异步测试"""
    result = await async_function(async_fixture)
    assert result is not None
```

### 2. 异步Fixture

```python
@pytest.fixture
async def async_database():
    """异步数据库fixture"""
    db = await create_database()
    yield db
    await db.close()

@pytest.fixture
async def async_agent():
    """异步Agent fixture"""
    from agents.core.planning.topic_splitter_agent import TopicSplitterAgent

    agent = TopicSplitterAgent(name="TestAgent")
    await agent.initialize()
    yield agent
    await agent.cleanup()

# 使用
@pytest.mark.asyncio
async def test_with_async_agent(async_agent):
    result = await agent.run(context, input_data)
    assert result.is_success
```

### 3. 测试异步上下文管理器

```python
@pytest.mark.asyncio
async def test_async_context_manager():
    """测试异步上下文管理器"""
    async with AsyncDatabase() as db:
        result = await db.query("SELECT * FROM tasks")
        assert len(result) > 0
    # 自动清理

@pytest.mark.asyncio
async def test_async_context_manager_error():
    """测试异常时的清理"""
    with pytest.raises(DatabaseError):
        async with AsyncDatabase() as db:
            await db.query("INVALID SQL")
    # 验证资源已释放
```

### 4. 测试超时和取消

```python
@pytest.mark.asyncio
async def test_timeout():
    """测试超时处理"""
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(0.1):
            await slow_operation()

@pytest.mark.asyncio
async def test_cancellation():
    """测试任务取消"""
    task = asyncio.create_task(slow_operation())

    # 取消任务
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
```

### 5. 并发测试模式

```python
@pytest.mark.asyncio
async def test_concurrent_operations():
    """测试并发操作"""
    # 创建多个并发任务
    tasks = [
        async_operation(i) for i in range(10)
    ]

    # 并发执行
    results = await asyncio.gather(*tasks)

    # 验证结果
    assert len(results) == 10

@pytest.mark.asyncio
async def test_concurrent_with_semaphore():
    """测试信号量限制并发"""
    semaphore = asyncio.Semaphore(3)

    async def limited_operation(i):
        async with semaphore:
            return await async_operation(i)

    tasks = [limited_operation(i) for i in range(10)]
    results = await asyncio.gather(*tasks)
    assert len(results) == 10
```

---

## 外部依赖Mock策略

### 1. LLM调用Mock

#### 使用unittest.mock

```python
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_agent_with_mocked_llm():
    """测试Agent使用Mock的LLM"""
    from agents.core.planning.topic_splitter_agent import TopicSplitterAgent

    # Mock LLM响应
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "topics": [
            {"id": 1, "title": "主题1", "description": "描述1"}
        ]
    })

    # Patch LLM调用
    with patch('agents.core.planning.topic_splitter_agent.call_llm') as mock_llm:
        mock_llm.return_value = mock_response

        # 创建并运行Agent
        agent = TopicSplitterAgent(name="TestAgent")
        result = await agent.run(context, input_data)

        # 验证LLM被调用
        mock_llm.assert_called_once()

        # 验证结果
        assert result.is_success
```

#### 使用自定义Mock类

```python
class MockLLMModel:
    """Mock LLM模型"""

    def __init__(self, response_text):
        self.response_text = response_text
        self.call_count = 0
        self.call_history = []

    async def generate_async(self, prompt):
        """模拟LLM生成"""
        self.call_count += 1
        self.call_history.append(prompt)

        mock_response = MagicMock()
        mock_response.text = self.response_text
        return mock_response

# 使用
@pytest.mark.asyncio
async def test_with_custom_mock():
    mock_llm = MockLLMModel(
        response_text='{"topics": [{"id": 1, "title": "主题1"}]}'
    )

    with patch('create_llm_model', return_value=mock_llm):
        agent = TopicSplitterAgent(name="TestAgent")
        result = await agent.run(context, input_data)

        assert mock_llm.call_count > 0
        assert result.is_success
```

### 2. 数据库Mock

#### 使用SQLite内存数据库

```python
@pytest.fixture
async def test_db():
    """创建测试数据库"""
    from infrastructure.database.connection_manager import ConnectionManager

    # 使用SQLite内存数据库
    db = ConnectionManager(database_url="sqlite:///:memory:")
    await db.initialize()
    await db.create_tables()

    yield db

    await db.close()

# 使用
@pytest.mark.asyncio
async def test_database_operations(test_db):
    # 插入测试数据
    await test_db.execute(
        "INSERT INTO tasks (id, raw_input) VALUES (?, ?)",
        ("task_1", "test input")
    )

    # 查询验证
    result = await test_db.fetch_one(
        "SELECT * FROM tasks WHERE id = ?",
        ("task_1",)
    )

    assert result is not None
    assert result["raw_input"] == "test input"
```

#### 使用fakeredis

```bash
pip install fakeredis
```

```python
import fakeredis.asyncio as fakeredis

@pytest.fixture
async def mock_redis():
    """Mock Redis"""
    redis = fakeredis.FakeRedis(decode_responses=True)
    yield redis
    await redis.close()

# 使用
@pytest.mark.asyncio
async def test_redis_cache(mock_redis):
    from infrastructure.cache.redis_cache import RedisCache

    cache = RedisCache(redis_client=mock_redis)

    # 测试缓存
    await cache.set("key", "value", ttl=60)
    result = await cache.get("key")

    assert result == "value"
```

### 3. MCP工具Mock

```python
@pytest.mark.asyncio
async def test_mcp_tool_mock():
    """测试MCP工具Mock"""
    from agents.tools.mcp.mcp_integration import MCPIntegration

    # Mock MCP工具响应
    mock_tool_result = {
        "success": True,
        "data": {"result": "tool output"}
    }

    with patch('agents.tools.mcp.mcp_integration.call_mcp_tool') as mock_tool:
        mock_tool.return_value = mock_tool_result

        # 测试
        mcp = MCPIntegration()
        result = await mcp.execute_tool("test_tool", {"param": "value"})

        assert result["success"] is True
        mock_tool.assert_called_once_with("test_tool", {"param": "value"})
```

### 4. HTTP请求Mock

#### 使用aioresponses

```bash
pip install aioresponses
```

```python
import aioresponses

@pytest.mark.asyncio
async def test_http_request_mock():
    """测试HTTP请求Mock"""
    import aiohttp

    with aioresponses.aioresponses() as m:
        # Mock HTTP响应
        m.get(
            "http://api.example.com/search",
            payload={"results": ["result1", "result2"]},
            status=200
        )

        # 测试代码
        async with aiohttp.ClientSession() as session:
            async with session.get("http://api.example.com/search") as resp:
                data = await resp.json()

        # 验证
        assert data == {"results": ["result1", "result2"]}

        # 验证请求被发送
        assert len(m.requests) == 1
```

---

## 记忆系统测试方法

### 1. 分层记忆测试

```python
@pytest.mark.asyncio
async def test_hierarchical_memory():
    """测试分层记忆"""
    from cognition.memory.core.hierarchical_memory_manager import (
        HierarchicalMemoryManager,
        MemoryLevel
    )

    manager = HierarchicalMemoryManager()

    # 测试L1: 瞬时记忆
    manager.store("key1", "value1", level=MemoryLevel.TRANSIENT)
    value = manager.retrieve("key1")
    assert value == "value1"

    # 测试L2: 短期记忆
    await manager.store("key2", "value2", level=MemoryLevel.SHORT_TERM)
    value = await manager.retrieve("key2")
    assert value == "value2"

    # 测试L3: 长期记忆
    await manager.store("key3", "value3", level=MemoryLevel.LONG_TERM)
    value = await manager.retrieve("key3")
    assert value == "value3"
```

### 2. Agent记忆Mixin测试

```python
@pytest.mark.asyncio
async def test_agent_memory_operations():
    """测试Agent记忆操作"""
    from agents.core.base_agent_with_memory import AgentMemoryMixin

    class TestAgent(AgentMemoryMixin):
        pass

    agent = TestAgent(name="TestAgent")
    agent.set_context(user_id="user_1", task_id="task_1")

    # 测试记住和回忆
    if agent.is_memory_enabled():
        # 保存记忆
        success = await agent.remember(
            key="research_result",
            value={"topic": "AI", "content": "内容"},
            importance=0.8,
            scope="TASK"
        )

        # 召回记忆
        recalled = await agent.recall(
            key="research_result",
            scope="TASK"
        )

        assert recalled is not None
        assert recalled["topic"] == "AI"
```

### 3. 记忆共享测试

```python
@pytest.mark.asyncio
async def test_shared_workspace():
    """测试共享工作空间"""
    from agents.core.base_agent_with_memory import AgentMemoryMixin

    class AgentA(AgentMemoryMixin):
        pass

    class AgentB(AgentMemoryMixin):
        pass

    agent_a = AgentA(name="AgentA")
    agent_b = AgentB(name="AgentB")

    # 设置相同上下文
    agent_a.set_context(user_id="user_1", task_id="task_1")
    agent_b.set_context(user_id="user_1", task_id="task_1")

    # AgentA共享数据
    await agent_a.share_data(
        data_type="research",
        data_key="topic_1",
        data_content={"title": "AI", "content": "..."},
        target_agents=["AgentB"],
        ttl_minutes=60
    )

    # AgentB获取数据
    shared_data = await agent_b.get_shared_data(
        data_type="research",
        data_key="topic_1"
    )

    assert shared_data is not None
    assert shared_data["title"] == "AI"
```

---

## Checkpoint与恢复测试

### 1. Checkpoint保存测试

```python
@pytest.mark.asyncio
async def test_checkpoint_save():
    """测试Checkpoint保存"""
    from infrastructure.checkpoint.checkpoint_manager import CheckpointManager
    from domain.entities import Task, TaskStage

    manager = CheckpointManager()

    # 创建任务
    task = Task(id="task_1", raw_input="Generate PPT")
    task.start_stage(TaskStage.REQUIREMENT_PARSING)
    task.update_stage_progress(TaskStage.REQUIREMENT_PARSING, 50)

    # 保存检查点
    checkpoint_id = await manager.save_checkpoint(
        task_id=task.id,
        phase=1,
        data=task.to_dict()
    )

    assert checkpoint_id is not None
```

### 2. Checkpoint恢复测试

```python
@pytest.mark.asyncio
async def test_checkpoint_load():
    """测试Checkpoint恢复"""
    from infrastructure.checkpoint.checkpoint_manager import CheckpointManager
    from domain.entities import Task

    manager = CheckpointManager()

    # 保存检查点
    task = Task(id="task_1", raw_input="Generate PPT")
    checkpoint_id = await manager.save_checkpoint(
        task_id=task.id,
        phase=1,
        data=task.to_dict()
    )

    # 加载检查点
    loaded_data = await manager.load_checkpoint(checkpoint_id)

    # 验证数据恢复
    assert loaded_data is not None
    assert loaded_data["id"] == "task_1"

    # 重建任务
    restored_task = Task.from_dict(loaded_data)
    assert restored_task.id == task.id
    assert restored_task.raw_input == task.raw_input
```

### 3. Checkpoint版本管理测试

```python
@pytest.mark.asyncio
async def test_checkpoint_versioning():
    """测试Checkpoint版本管理"""
    from infrastructure.checkpoint.checkpoint_manager import CheckpointManager

    manager = CheckpointManager()

    # 保存多个版本
    checkpoint_ids = []
    for i in range(3):
        checkpoint_id = await manager.save_checkpoint(
            task_id="task_1",
            phase=1,
            data={"version": i, "data": f"state_{i}"}
        )
        checkpoint_ids.append(checkpoint_id)

    # 列出所有版本
    versions = await manager.list_checkpoints("task_1")
    assert len(versions) == 3

    # 加载最新版本
    latest = await manager.load_latest_checkpoint("task_1")
    assert latest["version"] == 2

    # 删除旧版本
    await manager.delete_checkpoint(checkpoint_ids[0])
    versions = await manager.list_checkpoints("task_1")
    assert len(versions) == 2
```

---

## 测试Fixture管理

### 1. Fixture作用域

```python
# function级别（默认）- 每个测试函数都会重新创建
@pytest.fixture
def function_fixture():
    return Object()

# class级别 - 每个测试类创建一次
@pytest.fixture(scope="class")
def class_fixture():
    return Object()

# module级别 - 每个模块创建一次
@pytest.fixture(scope="module")
def module_fixture():
    return Object()

# session级别 - 整个测试会话创建一次
@pytest.fixture(scope="session")
def session_fixture():
    return Object()
```

### 2. Fixture依赖

```python
@pytest.fixture
def database():
    """创建数据库"""
    db = create_database()
    return db

@pytest.fixture
def session(database):
    """依赖于database fixture"""
    return database.create_session()

@pytest.fixture
def repository(session):
    """依赖于session fixture"""
    return TaskRepository(session)

# 使用
def test_repository(repository):
    # repository使用了session，session使用了database
    result = repository.get_task("task_1")
    assert result is not None
```

### 3. 常用Fixture示例

```python
# conftest.py - 放在项目根目录

@pytest.fixture
async def mock_llm():
    """Mock LLM"""
    mock = AsyncMock()
    mock.generate_async.return_value = MagicMock(
        text='{"result": "success"}'
    )
    return mock

@pytest.fixture
async def test_task():
    """创建测试任务"""
    from domain.entities import Task
    return Task(
        id="test_task_1",
        raw_input="Generate a PPT about AI"
    )

@pytest.fixture
async def test_agent():
    """创建测试Agent"""
    from agents.core.planning.topic_splitter_agent import TopicSplitterAgent
    agent = TopicSplitterAgent(name="TestAgent")
    yield agent
    # 清理
    await agent.cleanup()

@pytest.fixture
async def agent_context():
    """创建Agent上下文"""
    from domain.communication import AgentContext, ExecutionMode
    return AgentContext(
        request_id="test_request_1",
        execution_mode=ExecutionMode.FULL
    )
```

---

## 集成测试环境设置

### 1. 测试配置文件

```python
# tests/conftest.py
import os
import pytest

# 设置测试环境变量
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"  # 使用测试DB
os.environ["LLM_API_KEY"] = "test_key"

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_database():
    """初始化测试数据库"""
    from infrastructure.database.connection_manager import ConnectionManager

    db = ConnectionManager(database_url=os.getenv("DATABASE_URL"))
    await db.initialize()
    await db.create_tables()

    yield db

    await db.drop_tables()
    await db.close()

@pytest.fixture(scope="session")
async def test_redis():
    """初始化测试Redis"""
    import redis.asyncio as redis

    redis_client = await redis.from_url(
        os.getenv("REDIS_URL"),
        decode_responses=True
    )

    yield redis_client

    await redis_client.flushall()
    await redis_client.close()
```

### 2. 测试数据工厂

```python
# tests/factories.py
from domain.entities import Task, TaskStatus
from domain.value_objects import Requirement

class TaskFactory:
    """测试任务工厂"""

    @staticmethod
    def create_task(
        task_id: str = "test_task_1",
        raw_input: str = "Generate PPT",
        **kwargs
    ) -> Task:
        """创建测试任务"""
        return Task(
            id=task_id,
            raw_input=raw_input,
            **kwargs
        )

class RequirementFactory:
    """测试需求工厂"""

    @staticmethod
    def create_requirement(
        ppt_topic: str = "AI",
        page_num: int = 10,
        **kwargs
    ) -> Requirement:
        """创建测试需求"""
        return Requirement(
            ppt_topic=ppt_topic,
            page_num=page_num,
            **kwargs
        )

# 使用
def test_with_factory():
    task = TaskFactory.create_task()
    req = RequirementFactory.create_requirement()

    assert task.id == "test_task_1"
    assert req.ppt_topic == "AI"
```

### 3. 测试数据清理

```python
@pytest.fixture(autouse=True)
async def cleanup_test_data(test_database):
    """自动清理测试数据"""
    yield

    # 测试结束后清理
    await test_database.execute("DELETE FROM tasks WHERE id LIKE 'test_%'")
    await test_database.execute("DELETE FROM checkpoints WHERE task_id LIKE 'test_%'")
```

---

## 常用Mock工具介绍

### 1. unittest.mock

#### MagicMock

```python
from unittest.mock import MagicMock

# 创建Mock对象
mock = MagicMock()

# 配置返回值
mock.method.return_value = "result"

# 配置副作用
mock.method.side_effect = [1, 2, 3]  # 返回序列
mock.method.side_effect = ValueError("Error")  # 抛出异常

# 验证调用
mock.method.assert_called_once()
mock.method.assert_called_with(arg1, arg2)
mock.method.assert_any_call(arg1)  # 是否被调用过
```

#### AsyncMock

```python
from unittest.mock import AsyncMock

# 创建异步Mock
async_mock = AsyncMock()
async_mock.return_value = "async result"

# 使用
result = await async_mock()
assert result == "async result"
```

#### patch

```python
from unittest.mock import patch

# 上下文管理器
with patch('module.ClassName') as mock_class:
    instance = mock_class.return_value
    instance.method.return_value = "result"

    # 测试代码
    result = ClassName().method()
    assert result == "result"

# 装饰器
@patch('module.function1')
@patch('module.function2')
def test_with_patches(mock_func2, mock_func1):
    # 注意顺序：从下到上
    mock_func1.return_value = "result1"
    mock_func2.return_value = "result2"
```

### 2. pytest-mock

```bash
pip install pytest-mock
```

```python
import pytest

def test_with_pytest_mock(mocker):
    """使用pytest-mock"""

    # mocker.patch 是 unittest.mock.patch 的别名
    mock_func = mocker.patch('module.function')
    mock_func.return_value = "result"

    # mocker.spy 监视真实对象
    spy = mocker.spy(module, 'ClassName')

    # mocker.stub 创建存根
    stub = mocker.stub()

    # 自动恢复：测试结束后自动撤销patch
```

### 3. freezegun (时间Mock)

```bash
pip install freezegun
```

```python
from freezegun import freeze_time
import datetime

@freeze_time("2025-02-04 12:00:00")
def test_with_fixed_time():
    """测试固定时间"""
    assert datetime.datetime.now() == datetime.datetime(2025, 2, 4, 12, 0, 0)

@freeze_time("2025-02-04 12:00:00", tick=True)
def test_time_passage():
    """时间流动"""
    time1 = datetime.datetime.now()
    time.sleep(1)
    time2 = datetime.datetime.now()
    assert time2 > time1
```

---

## 测试最佳实践总结

### DO ✅

1. **使用有意义的测试名称**
   ```python
   def test_task_creation_with_valid_input():  # 清楚
   def test_task_1():  # 不清楚
   ```

2. **一个测试一个断言（或相关断言）**
   ```python
   def test_task_status():
       task = Task(id="1", raw_input="test")
       assert task.status == TaskStatus.PENDING
   ```

3. **使用Given-When-Then模式**
   ```python
   def test_task_completion():
       # Given
       task = Task(id="1", raw_input="test")

       # When
       task.mark_completed()

       # Then
       assert task.status == TaskStatus.COMPLETED
   ```

4. **测试边界条件**
   ```python
   @pytest.mark.parametrize("input,expected", [
       (0, False),
       (1, True),
       (100, True),
       (101, False),
   ])
   def test_page_validation(input, expected):
       result = validate_page_num(input)
       assert result == expected
   ```

### DON'T ❌

1. **不要在测试中写逻辑**
   ```python
   # 错误：测试中有if-else
   def test_with_logic():
       if condition:
           assert result == expected1
       else:
           assert result == expected2

   # 正确：分开写两个测试
   def test_condition_true():
       assert result == expected1

   def test_condition_false():
       assert result == expected2
   ```

2. **不要测试私有方法**
   ```python
   # 错误
   def test_private_method():
       obj._private_method()  # 不要测试

   # 正确：通过公共接口测试
   def test_public_behavior():
       result = obj.public_method()
       assert result == expected
   ```

3. **不要依赖测试执行顺序**
   ```python
   # 错误：test2依赖test1的执行
   def test_1():
       global.state = "modified"

   def test_2():
       assert global.state == "modified"

   # 正确：每个测试独立
   def test_1():
       state = "modified"
       assert process(state) == result

   def test_2():
       state = "other"
       assert process(state) == result
   ```

---

## 总结

### 关键要点

1. **异步测试**: 使用 `@pytest.mark.asyncio`
2. **Mock外部依赖**: LLM、数据库、Redis、HTTP
3. **记忆系统测试**: 分层测试、共享测试
4. **Checkpoint测试**: 保存、恢复、版本管理
5. **Fixture管理**: 合理使用作用域
6. **并发测试**: 注意线程安全

### 下一步

1. 设置 `conftest.py` 全局fixture
2. 编写各层测试用例
3. 运行测试并检查覆盖率
4. 持续维护测试代码

---

**维护者**: MultiAgentPPT Team
**版本**: 1.0
**最后更新**: 2025-02-04
