# simplePPT 模块详解

## 📋 目录

- [模块概述](#模块概述)
- [目录结构](#目录结构)
- [核心功能](#核心功能)
- [文件详解](#文件详解)
- [工作流程](#工作流程)
- [配置说明](#配置说明)
- [使用示例](#使用示例)
- [与其他模块的关系](#与其他模块的关系)
- [技术栈](#技术栈)

---

## 模块概述

**simplePPT** 是 MultiAgentPPT 项目中的一个简化版 PPT 内容生成服务，它基于 **A2A 框架** 和 **Google ADK 架构** 构建，通过单个智能体根据提供的大纲生成结构化的 XML 格式 PPT 内容。

### 主要特点

- **单 Agent 架构**：使用单个智能体完成 PPT 生成，不涉及并发和外部检索
- **流式输出支持**：支持 SSE（Server-Sent Events）实时流式返回生成内容
- **XML 格式输出**：生成标准化的 XML 格式 PPT 内容，便于前端解析和渲染
- **灵活的模型支持**：支持多种 LLM 提供商（Google、Claude、OpenAI、DeepSeek 等）
- **可配置的元数据**：支持通过 metadata 传递 PPT 页数、语言等配置

### 适用场景

- 快速原型开发
- 功能测试和验证
- 不需要外部检索的简单 PPT 生成
- 学习和了解 A2A + ADK 框架集成

---

## 目录结构

```
backend/simplePPT/
├── __init__.py              # Python 包初始化文件
├── main_api.py              # FastAPI 主入口，暴露 SSE 接口
├── agent.py                 # 主控制 Agent，定义 PPT 生成逻辑
├── adk_agent_executor.py    # 实现 A2A 与 ADK 框架的集成逻辑
├── a2a_client.py            # A2A 客户端示例代码
├── create_model.py          # 模型创建工厂函数
├── env_template             # 环境变量配置模板
├── .env                     # 实际环境变量配置（不提交到版本控制）
└── README.md                # 模块说明文档
```

---

## 核心功能

### 1. PPT 内容生成

根据用户提供的大纲，生成包含多种布局和组件的 XML 格式 PPT 内容。

**支持的布局类型：**
- `vertical` - 图片显示在上方
- `left` - 图片显示在左侧
- `right` - 图片显示在右侧

**支持的内容组件：**
- `COLUMNS` - 列布局，用于比较展示
- `BULLETS` - 列表布局，用于列要点
- `ICONS` - 图标布局，结合图标展示概念
- `CYCLE` - 循环布局，用于展示流程或循环
- `ARROWS` - 箭头布局，用于展示因果或流程
- `TIMELINE` - 时间线布局，用于展示时间进程
- `PYRAMID` - 金字塔布局，用于展示层级结构
- `STAIRCASE` - 阶梯布局，用于展示阶段性进阶
- `CHART` - 图表布局，用于可视化数据

### 2. 流式响应

通过 SSE 协议实时推送 Agent 执行状态和生成内容，提升用户体验。

### 3. 元数据支持

支持从前端接收配置参数：
- `numSlides` - PPT 页数
- `language` - 语言设置（如 "中文"、"EN-US"）

---

## 文件详解

### 1. main_api.py

**作用**：FastAPI 主入口，启动 HTTP 服务

**核心功能**：
- 初始化 A2A 应用和 ADK Runner
- 配置 Agent 能力卡片（AgentCard）
- 设置流式/非流式输出模式
- 启动 Uvicorn 服务器

**关键代码解析**：

```python
# 配置 Agent 能力卡片
agent_card = AgentCard(
    name="ppt Agent",
    description="Generate the PPT content based on the provided outline",
    url=f"http://{host}:{port}/",
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=streaming),
    skills=[skill],
)

# 初始化 Runner
runner = Runner(
    app_name=agent_card.name,
    agent=root_agent,  # 来自 agent.py
    artifact_service=InMemoryArtifactService(),
    session_service=InMemorySessionService(),
    memory_service=InMemoryMemoryService(),
)

# 配置运行模式
run_config = RunConfig(
    streaming_mode=StreamingMode.SSE,  # 或 StreamingMode.NONE
    max_llm_calls=500
)
```

**默认端口**：10011

---

### 2. agent.py

**作用**：定义 PPT 生成 Agent 的核心逻辑

**核心功能**：
- 定义 Agent 的系统指令（instruction）
- 实现前置回调函数（before_agent_callback）
- 处理元数据（页数、语言等配置）
- 创建 Agent 实例

**关键组件**：

#### 系统指令（instruction）

详细定义了 PPT 生成的规则和要求：
- XML 格式规范
- 布局组件使用说明
- 内容扩展策略
- 示例图片资源

#### 前置回调函数

```python
def before_agent_callback(callback_context: CallbackContext) -> None:
    """
    在调用 LLM 之前，从会话状态中获取当前幻灯片计划，并格式化 LLM 输入。
    """
    metadata = callback_context.state.get("metadata", {})
    slides_plan_num = metadata.get("numSlides", 10)  # 默认 10 页
    language = metadata.get("language", "EN-US")      # 默认英文

    # 设置幻灯片数量和语言
    callback_context.state["slides_plan_num"] = slides_plan_num
    callback_context.state["language"] = language

    return None  # 返回 None，继续调用 LLM
```

#### Agent 创建

```python
root_agent = Agent(
    name="ppt_agent",
    model=model,  # 来自 create_model.py
    description="generate ppt content",
    instruction=instruction + SOME_EXAMPLE_IAMGES,
    before_agent_callback=before_agent_callback
)
```

---

### 3. adk_agent_executor.py

**作用**：实现 A2A 框架与 Google ADK 框架的集成

**核心功能**：
- 管理会话（session）的创建和获取
- 处理 Agent 执行事件流
- 转换 A2A 和 ADK 之间的数据格式
- 控制结果显示（通过 show_agent 配置）

**关键类和方法**：

#### ADKAgentExecutor 类

```python
class ADKAgentExecutor(AgentExecutor):
    def __init__(self, runner: Runner, card: AgentCard, run_config, show_agent):
        self.runner = runner
        self._card = card
        self._running_sessions = {}
        self.run_config = run_config
        self.show_agent = show_agent  # 控制哪些 Agent 的结果需要显示
```

#### 核心方法

- `_process_request()` - 处理请求，执行 Agent
- `_upsert_session()` - 创建或获取会话
- `execute()` - 执行 Agent 任务
- `convert_genai_parts_to_a2a()` - 将 ADK 格式转换为 A2A 格式
- `extract_function_info_to_datapart()` - 提取函数调用信息

**事件处理逻辑**：

```python
async for event in self._run_agent(session_id, new_message):
    agent_author = event.author

    # 如果是需要在前端显示的 Agent
    if agent_author in self.show_agent:
        await task_updater.update_status(
            TaskState.working,
            message=task_updater.new_agent_message(
                convert_genai_parts_to_a2a(event.content.parts),
                metadata={"author": agent_author, "show": True}
            ),
        )

    # 处理不同类型的事件
    elif event.is_final_response():
        # 最终响应
        await task_updater.add_artifact(...)
        await task_updater.complete()

    elif event.get_function_calls():
        # 函数调用
        await task_updater.update_status(...)

    # ... 其他事件类型处理
```

---

### 4. a2a_client.py

**作用**：A2A 客户端示例代码，用于测试和调试

**功能**：
- 演示如何调用 simplePPT 服务
- 展示流式请求的使用方法
- 展示元数据的传递方式

**示例代码**：

```python
async def httpx_client():
    client = await A2AClient.get_client_from_agent_card_url(
        httpx_client, 'http://localhost:10011'
    )

    request_id = uuid.uuid4().hex

    # 构造消息参数
    send_message_payload = {
        'message': {
            'role': 'user',
            'parts': [{'type': 'text', 'text': prompt}],
            'messageId': request_id,
            'metadata': {
                "numSlides": 10,      # PPT 页数
                "language": "中文"     # 语言
            }
        }
    }

    # 流式请求
    streaming_request = SendStreamingMessageRequest(
        id=request_id,
        params=MessageSendParams(**send_message_payload)
    )

    async for chunk in client.send_message_streaming(streaming_request):
        print(chunk.model_dump(mode='json', exclude_none=True))
```

---

### 5. create_model.py

**作用**：模型创建工厂函数，支持多种 LLM 提供商

**支持的提供商**：

| 提供商 | 标识符 | 说明 |
|--------|--------|------|
| Google | `google` | 使用 Gemini 模型 |
| Claude | `claude` | 使用 Anthropic Claude 模型 |
| OpenAI | `openai` | 使用 OpenAI GPT 模型 |
| DeepSeek | `deepseek` | 使用 DeepSeek 模型 |
| 阿里云 | `ali` | 使用阿里云通义千问模型 |
| 豆包 | `doubao` | 使用字节豆包模型 |
| 本地模型 | `local_*` | 本地部署的模型 |

**使用示例**：

```python
# 使用 Google Gemini
model = create_model(
    model="gemini-2.0-flash",
    provider="google"
)

# 使用 DeepSeek
model = create_model(
    model="deepseek-chat",
    provider="deepseek"
)

# 使用本地模型
model = create_model(
    model="deepseek-chat",
    provider="local_deepseek"
)
```

**核心逻辑**：

```python
def create_model(model: str, provider: str):
    if provider == "google":
        return model  # Google 直接返回模型名称
    elif provider == "claude":
        return LiteLlm(
            model="anthropic/" + model,
            api_key=os.environ.get("CLAUDE_API_KEY"),
        )
    elif provider == "openai":
        return LiteLlm(
            model="openai/" + model,
            api_key=os.environ.get("OPENAI_API_KEY"),
            api_base="https://api.openai.com/v1"
        )
    # ... 其他提供商
```

---

### 6. env_template

**作用**：环境变量配置模板

**配置项说明**：

```bash
# API 密钥配置
GOOGLE_API_KEY=xxx              # Google Gemini API 密钥
DEEPSEEK_API_KEY=xxx            # DeepSeek API 密钥
ALI_API_KEY=sk-xxx              # 阿里云 API 密钥
OPENAI_API_KEY=xxx              # OpenAI API 密钥
CLAUDE_API_KEY=xxx              # Claude API 密钥

# 流式输出配置
STREAMING=true                  # 是否启用流式响应

# 模型配置
MODEL_PROVIDER=google           # 模型提供商
LLM_MODEL=gemini-2.0-flash      # 模型名称

# 代理配置（可选）
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

---

## 工作流程

```
┌─────────────────┐
│  前端发送请求    │
│  (大纲+元数据)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  main_api.py    │
│  接收 HTTP 请求  │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ ADKAgentExecutor    │
│ 处理请求和会话管理    │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  agent.py           │
│  before_agent_      │
│  callback 处理元数据 │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  LLM 生成 PPT 内容  │
│  (XML 格式)         │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  ADKAgentExecutor   │
│  格式转换和事件处理  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  SSE 流式返回前端   │
│  实时推送生成内容    │
└─────────────────────┘
```

**详细步骤**：

1. **请求接收**：`main_api.py` 接收前端的 HTTP 请求
2. **会话管理**：`ADKAgentExecutor` 创建或获取会话
3. **元数据处理**：`agent.py` 的 `before_agent_callback` 从 metadata 中提取配置
4. **LLM 调用**：Agent 调用配置的 LLM 生成 PPT 内容
5. **事件处理**：`ADKAgentExecutor` 处理 LLM 返回的事件流
6. **格式转换**：将 ADK 格式转换为 A2A 格式
7. **流式返回**：通过 SSE 实时推送到前端

---

## 配置说明

### 1. 基础配置

复制环境变量模板：
```bash
cd backend/simplePPT
cp env_template .env
```

编辑 `.env` 文件，配置 API 密钥和模型：
```bash
# 选择模型提供商和模型
MODEL_PROVIDER=google
LLM_MODEL=gemini-2.0-flash

# 配置对应的 API 密钥
GOOGLE_API_KEY=your_api_key_here

# 启用流式输出
STREAMING=true
```

### 2. 模型选择建议

| 使用场景 | 推荐模型 | 说明 |
|----------|----------|------|
| 快速测试 | `gemini-2.0-flash` | 速度快，成本低 |
| 高质量生成 | `gemini-2.5-pro` | 质量高，速度适中 |
| 国内使用 | `deepseek-chat` | 无需代理，性价比高 |
| 本地部署 | `local_deepseek` | 数据隐私，无网络依赖 |

### 3. 代理配置

如果需要使用代理访问 API：
```bash
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

---

## 使用示例

### 1. 启动服务

```bash
cd backend/simplePPT
python main_api.py
```

默认监听：`http://localhost:10011`

### 2. 使用客户端调用

编辑 `a2a_client.py`，设置大纲内容：
```python
prompt = """
# 电动汽车发展概述
- 电动汽车的定义和类型
- 电动汽车发展简史
- 电动汽车在全球汽车市场的地位

# 电动汽车发展的驱动因素
- 环境保护
- 能源安全
- 技术进步
- 政策支持
...
"""
```

运行客户端：
```bash
python a2a_client.py
```

### 3. 前端集成

前端通过 HTTP API 调用：
```javascript
const response = await fetch('http://localhost:10011', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: {
      role: 'user',
      parts: [{ type: 'text', text: outline }],
      metadata: {
        numSlides: 10,
        language: '中文'
      }
    }
  })
});

// 处理流式响应
const reader = response.body.getReader();
// ...
```

### 4. 预期输出

生成的 XML 格式 PPT 内容：
```xml
<PRESENTATION>

<SECTION layout="vertical">
  <IMG src="https://example.com/image.jpg" alt="背景图" />
  <H1>特斯拉汽车调研</H1>
  <P>全球电动汽车市场深度分析</P>
</SECTION>

<SECTION layout="left">
  <IMG src="https://example.com/chart.png" alt="销量增长" />
  <BULLETS>
    <DIV><H3>全球电动汽车市场概况</H3><P>全球电动汽车销量持续增长...</P></DIV>
    <DIV><P>中国市场表现尤为突出...</P></DIV>
  </BULLETS>
</SECTION>

...

</PRESENTATION>
```

---

## 与其他模块的关系

### 项目结构对比

```
backend/
├── simpleOutline/    # 简化版大纲生成（无外部依赖）
├── simplePPT/        # 简化版PPT生成（当前模块）
├── slide_outline/    # 高质量大纲生成（带 MCP 检索）
└── slide_agent/      # 完整多Agent PPT生成（并发+检索）
```

### 功能对比

| 模块 | 功能 | 复杂度 | 外部依赖 | 并发 |
|------|------|--------|----------|------|
| `simpleOutline` | 生成大纲 | 低 | 无 | 否 |
| `simplePPT` | 生成 PPT 内容 | 低 | 无 | 否 |
| `slide_outline` | 生成大纲（高质量） | 中 | MCP 检索 | 否 |
| `slide_agent` | 完整 PPT 生成 | 高 | MCP + RAG | 是 |

### 调用关系

```
┌──────────────────┐
│  前端 (Next.js)  │
└────────┬─────────┘
         │
         ├─────────┬──────────────┬────────────────┐
         ▼         ▼              ▼                ▼
   ┌─────────┐ ┌─────────┐  ┌──────────────┐  ┌────────────┐
   │simple   │ │simple   │  │slide_        │  │slide_      │
   │Outline  │ │PPT      │  │outline       │  │agent       │
   └─────────┘ └─────────┘  └──────────────┘  └────────────┘
   大纲生成    PPT生成       高质量大纲         完整生成
   (端口10001) (端口10011)  (端口10001)       (端口10011)
```

### 协同工作

**方案 1：简化流程**
1. 前端 → `simpleOutline` → 生成大纲
2. 前端 → `simplePPT` → 生成 PPT 内容

**方案 2：完整流程**
1. 前端 → `slide_outline` → 生成高质量大纲（带检索）
2. 前端 → `slide_agent` → 多 Agent 并发生成完整 PPT

---

## 技术栈

### 核心框架
- **A2A (Agent-to-Agent)** - Agent 通信协议框架
- **Google ADK (Agent Development Kit)** - Google Agent 开发工具包
- **FastAPI** - 高性能 Web 框架
- **Uvicorn** - ASGI 服务器

### 依赖库
- **litellm** - 统一 LLM 接口
- **python-dotenv** - 环境变量管理
- **httpx** - 异步 HTTP 客户端
- **click** - 命令行工具

### 协议和格式
- **SSE (Server-Sent Events)** - 流式响应协议
- **XML** - PPT 内容输出格式

---

## 常见问题

### 1. 如何切换不同的 LLM 模型？

修改 `.env` 文件：
```bash
MODEL_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=your_key
```

### 2. 如何修改 PPT 的页数？

在前端请求的 metadata 中设置：
```json
{
  "metadata": {
    "numSlides": 15
  }
}
```

### 3. 如何使用本地模型？

配置 `.env`：
```bash
MODEL_PROVIDER=local_deepseek
LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=your_key
# 本地模型会自动连接到 http://localhost:6688
```

### 4. 流式输出和非流式输出有什么区别？

- **流式输出** (`STREAMING=true`)：实时推送生成内容，用户体验更好
- **非流式输出** (`STREAMING=false`)：等待全部生成完成后一次性返回

### 5. 如何调试 Agent？

在 `adk_agent_executor.py` 中已有详细的日志输出：
```python
logger.info(f"[adk executor] {agent_author}完成")
logger.debug(f"收到请求信息: {new_message}")
```

可以通过调整日志级别来控制输出量：
```python
logging.basicConfig(level=logging.DEBUG)  # 输出详细日志
logging.basicConfig(level=logging.INFO)   # 输出关键信息
```

---

## 总结

**simplePPT** 模块是一个简洁高效的 PPT 内容生成服务，适合：

✅ 快速原型开发和测试
✅ 学习 A2A + ADK 框架集成
✅ 不需要复杂检索和并发处理的场景

**核心优势**：
- 代码结构清晰，易于理解和修改
- 支持多种 LLM 提供商，灵活性强
- 流式输出，用户体验好
- XML 格式标准化，便于前端解析

**适用场景**：
- 教育、培训、演示文稿生成
- 内容创作辅助工具
- 自动化报告生成

如果需要更复杂的功能（如外部检索、多 Agent 并发），可以考虑使用 `slide_agent` 模块。
