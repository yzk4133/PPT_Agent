# Common Infrastructure (backend/common)

统一的基础设施模块，为 MultiAgentPPT 的所有 Agent 提供共享功能。

## 📦 模块组成

### 1. 配置管理 (`config.py`)

基于 Pydantic Settings 的类型安全配置系统。

**特性:**

- ✅ 环境变量自动覆盖
- ✅ 多环境支持 (dev/staging/prod)
- ✅ 配置验证和类型检查
- ✅ Feature Flags 支持灰度发布

**使用示例:**

```python
from backend.common import get_config

config = get_config()
print(config.environment)  # development
print(config.database.database_url)  # postgresql://...
print(config.features.use_flat_architecture)  # True

# 获取特定 Agent 配置
research_config = config.get_agent_config("research")
print(research_config.max_concurrency)  # 3
```

### 2. 模型工厂 (`model_factory.py`)

统一的模型创建接口，支持多提供商和自动降级。

**特性:**

- ✅ 支持 DeepSeek/OpenAI/Claude/Google/Qwen
- ✅ 主模型 → 备用模型自动降级
- ✅ 模型缓存和熔断器
- ✅ Google Gemini 特殊处理

**使用示例:**

```python
from backend.common import create_model_with_fallback, get_config

config = get_config()
agent_config = config.research_agent
agent_config.fallback_model = "deepseek-chat"  # 设置备用模型

result = create_model_with_fallback(agent_config)
if result.is_fallback:
    print(f"⚠️  Using fallback: {result.fallback_reason}")
print(f"Model: {result.model_name}")
```

### 3. 工具管理器 (`tool_manager.py`)

统一管理原生 ADK 工具和 MCP 工具。

**特性:**

- ✅ 支持原生 AgentTool 和 MCP 工具
- ✅ 线程安全的工具注册和访问
- ✅ 健康检查和自动摘除
- ✅ 工具热加载（可选，实验性）

**使用示例:**

```python
from backend.common import get_tool_manager
from google.adk.tools import AgentTool

manager = get_tool_manager()

# 注册原生工具
class MyTool(AgentTool):
    name = "MyTool"
    description = "A custom tool"

manager.register_native_tool(MyTool())

# 注册 MCP 工具
manager.register_mcp_tool(
    name="SearchDocument",
    mcp_client=mcp_client_instance,
    tool_type=ToolType.MCP_SSE,
    health_check_url="http://localhost:8000/health"
)

# 获取工具
tool = manager.get_tool("MyTool")

# 健康检查
health = await manager.health_check()
print(health)  # {"MyTool": True, "SearchDocument": True}
```

### 4. 重试装饰器 (`retry_decorator.py`)

基于 tenacity 的统一重试和熔断机制。

**特性:**

- ✅ 指数退避重试
- ✅ 错误分类（RetryableError/FallbackError/FatalError）
- ✅ 熔断器模式
- ✅ 支持同步和异步

**使用示例:**

```python
from backend.common.retry_decorator import (
    retry_with_exponential_backoff,
    retry_with_fallback,
    RetryableError
)

# 方式 1：简单重试
@retry_with_exponential_backoff(max_attempts=3)
def call_api():
    # 如果失败，自动重试 3 次
    return requests.get("https://api.example.com")

# 方式 2：带降级重试
def fallback_handler():
    return "Fallback result"

@retry_with_fallback(max_attempts=3, fallback_func=fallback_handler)
def risky_operation():
    # 失败后自动降级
    raise RetryableError("Temporary failure")

result = risky_operation()  # 返回 "Fallback result"
```

### 5. 降级策略框架 (`fallback/`)

多级降级链，支持各种场景的优雅降级。

**特性:**

- ✅ JSON 解析降级（完整解析 → 正则提取 → 默认结构）
- ✅ 并行任务部分成功处理
- ✅ LLM 调用降级（主模型 → 备用 → 缓存）
- ✅ 自定义降级链

**使用示例:**

```python
from backend.common.fallback import JSONFallbackParser, PartialSuccessHandler

# JSON 解析降级
result = JSONFallbackParser.parse_with_fallback(
    '{"topics": [invalid json...',
    default_structure={"topics": []}
)
if result.success:
    print(f"Parsed at level: {result.level}")
    print(f"Data: {result.data}")

# 部分成功处理
parallel_results = [
    (True, "Result 1"),
    (False, None),
    (True, "Result 2"),
]
result = PartialSuccessHandler.handle_parallel_results(
    parallel_results,
    min_success_rate=0.5
)
print(f"Success rate: {result.metadata['success_rate']}")
print(f"Valid data: {result.data}")
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend/common
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制模板
cp env_template .env

# 编辑 .env 文件
nano .env
```

### 3. 在 Agent 中使用

```python
# 在 slide_agent/main_api.py 或 slide_outline/main_api.py 中

from backend.common import (
    get_config,
    create_model_with_fallback,
    get_tool_manager,
)

# 1. 加载配置
config = get_config()

# 2. 创建模型（带降级）
agent_config = config.research_agent
model_result = create_model_with_fallback(agent_config)

# 3. 获取工具
tool_manager = get_tool_manager()
tools = tool_manager.get_all_tools()

# 4. 使用配置的 Feature Flags
if config.features.use_flat_architecture:
    # 使用新架构
    from slide_agent.flat_agent import FlatPPTGenerationAgent
else:
    # 使用旧架构（向后兼容）
    from slide_agent.agent import WritingSystemAgent
```

## 📋 Feature Flags

通过环境变量控制功能开关，实现灰度发布和向后兼容：

| Flag                              | 默认值  | 说明                     |
| --------------------------------- | ------- | ------------------------ |
| `FEATURE_USE_FLAT_ARCHITECTURE`   | `True`  | 使用扁平化架构（新）     |
| `FEATURE_USE_PERSISTENT_MEMORY`   | `True`  | 使用持久化记忆系统       |
| `FEATURE_ENABLE_VECTOR_CACHE`     | `True`  | 启用向量缓存             |
| `FEATURE_ENABLE_USER_PREFERENCES` | `True`  | 启用用户偏好学习         |
| `FEATURE_ENABLE_QUALITY_CHECK`    | `True`  | 启用 PPT 质量检查        |
| `FEATURE_ENABLE_TOOL_HOT_RELOAD`  | `False` | 启用工具热加载（实验性） |
| `FEATURE_ENABLE_MCP_TOOLS`        | `True`  | 启用 MCP 工具            |
| `FEATURE_ENABLE_AUTO_FALLBACK`    | `True`  | 启用自动降级             |

## 🔧 配置优先级

配置加载优先级（从高到低）：

1. **环境变量** - `AGENT_RESEARCH_MODEL=gpt-4`
2. **`.env` 文件** - 项目根目录的 `.env`
3. **代码默认值** - `config.py` 中的 `Field(default=...)`

示例：

```bash
# .env 文件
AGENT_RESEARCH_MODEL=deepseek-chat

# 环境变量覆盖
export AGENT_RESEARCH_MODEL=gpt-4

# 最终使用 gpt-4
```

## 📈 监控和调试

### 日志级别

```python
# 在 .env 中设置
LOG_LEVEL=DEBUG  # DEBUG/INFO/WARNING/ERROR/CRITICAL
```

### 检查配置

```bash
# 运行配置测试
python -m backend.common.config
```

### 测试模型创建

```bash
# 运行模型工厂测试
python -m backend.common.model_factory
```

### 测试工具管理器

```bash
# 运行工具管理器测试
python -m backend.common.tool_manager
```

### 测试重试机制

```bash
# 运行重试装饰器测试
python -m backend.common.retry_decorator
```

## 🛠️ 开发指南

### 添加新的 Agent 配置

1. 在 `config.py` 的 `AppConfig` 中添加：

```python
my_new_agent: AgentConfig = Field(default_factory=lambda: AgentConfig(
    provider=ModelProvider.DEEPSEEK,
    model="deepseek-chat",
    temperature=0.7,
    max_tokens=4096
))
```

2. 在 `env_template` 中添加环境变量：

```bash
AGENT_MY_NEW_PROVIDER=deepseek
AGENT_MY_NEW_MODEL=deepseek-chat
AGENT_MY_NEW_TEMPERATURE=0.7
```

3. 在 `get_agent_config` 方法中注册：

```python
def get_agent_config(self, agent_name: str) -> AgentConfig:
    agent_config_map = {
        "my_new": self.my_new_agent,
        # ...
    }
    return agent_config_map.get(agent_name, AgentConfig())
```

### 自定义降级策略

```python
from backend.common.fallback import FallbackChain, FallbackLevel

chain = FallbackChain("My Custom Fallback")

def strategy1():
    # 主策略
    return True, "primary_result"

def strategy2():
    # 备用策略
    return True, "fallback_result"

chain.add_strategy(FallbackLevel.PRIMARY, strategy1, "Primary strategy")
chain.add_strategy(FallbackLevel.SECONDARY, strategy2, "Fallback strategy")

result = chain.execute()
```

## 🔐 安全建议

1. **敏感信息**: 永远不要在代码中硬编码 API 密钥
2. **生产环境**: 使用环境变量或密钥管理服务（如 AWS Secrets Manager）
3. **`.env` 文件**: 添加到 `.gitignore`，不要提交到版本控制

## 📝 更新日志

- **v1.0.0** (2026-01-31): 初始版本
  - 统一配置管理
  - 模型工厂与降级
  - 工具管理器
  - 重试与熔断
  - 降级策略框架

## 🤝 贡献

欢迎贡献新的工具、降级策略或配置选项！

---

**文档最后更新**: 2026-01-31
