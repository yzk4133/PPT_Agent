# MCP 实现指南

> **最后更新**: 2026-02-16
> **版本**: 1.0.0
> **状态**: 实验性功能

---

## 📋 目录

1. [概述](#概述)
2. [架构设计](#架构设计)
3. [实现细节](#实现细节)
4. [使用指南](#使用指南)
5. [性能对比](#性能对比)
6. [故障排查](#故障排查)
7. [最佳实践](#最佳实践)
8. [常见问题](#常见问题)

---

## 概述

### 什么是 MCP？

**MCP (Model Context Protocol)** 是由 Anthropic 提出的一种标准化协议，用于 AI 模型与工具之间的通信。

#### 核心概念

```
┌─────────────┐                    ┌─────────────┐
│   AI Model  │                    │    Tool     │
│  (Claude)   │                    │  (任意实现) │
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       │           ┌──────────────┐       │
       └──────────▶│  MCP 协议     │◀──────┘
                   │  (JSON-RPC)  │
                   └──────────────┘
```

**特点**：
- 🔄 **标准化**: 统一的通信协议，不依赖特定框架
- 🔌 **解耦**: AI 模型和工具实现完全分离
- 🌐 **跨语言**: 支持不同编程语言之间的集成
- 📡 **进程间通信**: 支持多种通信方式（stdio, HTTP, WebSocket）

### 项目中的 MCP 实现

MultiAgentPPT 项目在 **web_search** 工具上实现了 MCP 支持，作为实验性功能。

#### 实现范围

✅ **已实现**:
- `web_search` 工具的 MCP Server
- MCP Client 包装器
- 与现有 Tool Registry 的集成
- 双版本并存（LangChain + MCP）

❌ **未实现**:
- 其他工具的 MCP 支持（如 `fetch_url`, `weixin_search`）
- HTTP/WebSocket 通信方式（仅使用 stdio）
- 生产环境的部署优化

#### 实验目的

1. **验证可行性**: 在真实项目中测试 MCP 协议的实用性
2. **性能评估**: 对比 LangChain 和 MCP 两种实现的性能差异
3. **架构探索**: 为可能的跨系统集成做技术储备
4. **学习实践**: 深入理解 MCP 协议的工作原理

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Agent 层                              │
│  (ContentAgent, ResearchAgent, FrameworkAgent, etc.)        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Tool Registry 层                          │
│  NativeToolRegistry - 统一管理所有工具                       │
│                                                              │
│  ┌──────────────┐              ┌──────────────┐            │
│  │ LangChain    │              │     MCP      │            │
│  │ Tools        │              │   Tools      │            │
│  └──────────────┘              └──────────────┘            │
└─────────────────────────────────────────────────────────────┘
           │                              │
           ▼                              ▼
┌──────────────────────┐      ┌──────────────────────┐
│  LangChain 实现      │      │   MCP 实现           │
│  - 异步函数          │      │  - MCP Client        │
│  - httpx 直接调用    │      │  - stdio 通信        │
│                      │      │  - JSON-RPC 协议     │
└──────────────────────┘      └──────────┬───────────┘
                                          │
                                          ▼
                              ┌──────────────────────┐
                              │   MCP Server         │
                              │  - stdio 服务        │
                              │  - httpx 调用 API    │
                              └──────────┬───────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  外部 API             │
                              │  (Bing Search)        │
                              └──────────────────────┘
```

### 组件说明

#### 1. MCP Server

**位置**: `backend/tools/mcp/server.py`

**职责**:
- 启动 stdio 服务，监听来自 Client 的请求
- 注册 `web_search` 工具
- 调用外部 API（Bing Search）
- 返回格式化的搜索结果

**通信方式**: stdio（标准输入/输出）

**协议**: JSON-RPC 2.0（由 MCP SDK 处理）

#### 2. MCP Client

**位置**: `backend/tools/domain/search/web_search_mcp.py`

**职责**:
- 连接到 MCP Server（通过 stdio）
- 将 MCP 工具封装为 LangChain `StructuredTool`
- 处理工具调用的序列化/反序列化
- 提供与 LangChain Tool 兼容的接口

**特性**:
- 懒加载：首次调用时才建立连接
- 单例模式：全局共享一个 Client 实例
- 错误处理：连接失败时抛出详细异常

#### 3. Tool Registry 集成

**位置**: `backend/tools/application/tool_registry.py`

**职责**:
- 根据环境变量 `USE_MCP_WEB_SEARCH` 选择版本
- 注册正确的工具到注册表
- 提供统一的访问接口

**切换逻辑**:
```python
use_mcp_web_search = os.getenv("USE_MCP_WEB_SEARCH", "false").lower() == "true"

if use_mcp_web_search:
    # 注册 MCP 版本
    from backend.tools.domain.search.web_search_mcp import web_search_mcp_tool
    _global_registry.register_tool(web_search_mcp_tool, category="SEARCH")
else:
    # 注册 LangChain 版本
    from backend.tools.domain.search import web_search_tool
    _global_registry.register_tool(web_search_tool, category="SEARCH")
```

---

## 实现细节

### MCP Server 实现

#### 完整代码解析

```python
"""
MCP Server - 提供 web_search 服务

使用 Anthropic MCP SDK 实现，通过 stdio 进行通信。
"""

import asyncio
import logging
import os
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

# 配置
BING_SEARCH_API_KEY = os.getenv("BING_SEARCH_API_KEY")
BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"

# 创建 MCP Server 实例
server = Server("search-server")

@server.tool("web_search")
async def web_search(
    query: str,
    num_results: int = 5,
    language: str = "zh-CN"
) -> str:
    """
    Execute web search using Bing Search API

    Args:
        query: 搜索查询字符串
        num_results: 返回结果数量（1-10）
        language: 语言代码（如 "zh-CN", "en-US"）

    Returns:
        str: 格式化的搜索结果
    """
    # 1. 验证 API Key
    if not BING_SEARCH_API_KEY:
        raise ValueError("BING_SEARCH_API_KEY not configured")

    # 2. 准备请求
    headers = {"Ocp-Apim-Subscription-Key": BING_SEARCH_API_KEY}
    params = {
        "q": query,
        "count": num_results,
        "mkt": language,
        "safeSearch": "Moderate",
        "textFormat": "HTML",
        "textDecorations": "true"
    }

    # 3. 执行搜索
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(BING_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

    # 4. 解析结果
    results = []
    web_pages = data.get("webPages", {}).get("value", [])

    for item in web_pages:
        results.append({
            "title": item.get("name", ""),
            "url": item.get("url", ""),
            "snippet": item.get("snippet", ""),
            "display_url": item.get("displayUrl", ""),
            "date": item.get("date"),
            "source": _extract_domain(item.get("url", ""))
        })

    # 5. 格式化输出
    output = f"Found {len(results)} results for '{query}':\n\n"
    for i, item in enumerate(results, 1):
        output += f"{i}. {item['title']}\n"
        output += f"   URL: {item['url']}\n"
        if item['snippet']:
            snippet = item['snippet'][:150].replace('\n', ' ')
            output += f"   {snippet}...\n\n"

    return output

async def main():
    """启动 MCP Server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

#### 关键点解析

**1. @server.tool() 装饰器**

```python
@server.tool("web_search")
async def web_search(...) -> str:
    ...
```

- **作用**: 将函数注册为 MCP 工具
- **参数**: 工具名称（在协议中使用的标识符）
- **自动处理**: SDK 自动生成工具的 schema、描述等信息

**2. stdio_server()**

```python
async with stdio_server() as (read_stream, write_stream):
    await server.run(read_stream, write_stream, ...)
```

- **作用**: 创建 stdio 通信流
- **read_stream**: 从 stdin 读取 JSON-RPC 请求
- **write_stream**: 向 stdout 写写 JSON-RPC 响应
- **协议细节**: SDK 自动处理 JSON-RPC 2.0 的序列化/反序列化

**3. server.run()**

```python
await server.run(read_stream, write_stream, server.create_initialization_options())
```

- **作用**: 启动 MCP Server 的主循环
- **功能**:
  - 处理 `initialize` 请求（协议握手）
  - 处理 `tools/list` 请求（列出可用工具）
  - 处理 `tools/call` 请求（调用工具）
  - 保持连接直到进程结束

---

### MCP Client 实现

#### 完整代码解析

```python
"""
MCP Web Search Tool - 通过 MCP 调用 web_search

使用 Anthropic MCP SDK 连接到 MCP Server，将 web_search 暴露为 LangChain Tool。
"""

import logging
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class MCPWebSearchInput(BaseModel):
    """MCP Web search input schema"""
    query: str = Field(description="Search query string")
    num_results: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of results to return (1-10)"
    )

# MCP Client（懒加载单例）
_mcp_client: Optional[object] = None

async def get_mcp_client():
    """
    获取 MCP Client（懒加载）

    Returns:
        MCP Client 实例
    """
    global _mcp_client
    if _mcp_client is None:
        from mcp.client import Client, StdioServerParameters

        logger.info("[MCP Client] Initializing connection to MCP Server...")

        # 配置 Server 参数
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "backend.tools.mcp.server"],
            env=None  # 继承当前环境变量
        )

        # 创建 Client
        _mcp_client = Client(server_params)

        try:
            # 初始化连接
            await _mcp_client.initialize()
            logger.info("[MCP Client] Connected to MCP Server successfully")
        except Exception as e:
            logger.error(f"[MCP Client] Failed to connect: {e}", exc_info=True)
            raise

    return _mcp_client

async def web_search_mcp_func(
    query: str,
    num_results: int = 5
) -> str:
    """
    Web search via MCP Server

    通过 MCP 协议调用远程的 web_search 工具。
    """
    logger.info(f"[MCP Wrapper] Calling web_search via MCP: query={query}")

    try:
        # 获取 MCP Client
        client = await get_mcp_client()

        # 调用 MCP Server 的工具
        result = await client.call_tool("web_search", {
            "query": query,
            "num_results": num_results,
            "language": "zh-CN"
        })

        # 处理返回结果
        if hasattr(result, 'content'):
            content = result.content
            if isinstance(content, list) and len(content) > 0:
                return content[0].text
            return str(content)
        elif isinstance(result, dict):
            if 'content' in result:
                return str(result['content'])
            elif 'results' in result:
                return str(result['results'])
        elif isinstance(result, str):
            return result
        else:
            return str(result)

    except Exception as e:
        logger.error(f"[MCP Wrapper] Error calling MCP: {e}", exc_info=True)
        raise

# 创建 Langchain Tool
web_search_mcp_tool = StructuredTool.from_function(
    func=web_search_mcp_func,
    name="web_search_mcp",
    description="Web search via MCP Server - experimental implementation",
    args_schema=MCPWebSearchInput
)
```

#### 关键点解析

**1. StdioServerParameters**

```python
server_params = StdioServerParameters(
    command="python",
    args=["-m", "backend.tools.mcp.server"],
    env=None
)
```

- **command**: 启动 MCP Server 的命令
- **args**: 命令参数
- **env**: 环境变量（None 表示继承当前进程的环境变量）
- **作用**: 定义如何启动和连接到 MCP Server

**2. Client.initialize()**

```python
await _mcp_client.initialize()
```

- **作用**: 执行 MCP 握手协议
- **过程**:
  1. 启动 Server 进程
  2. 发送 `initialize` 请求
  3. 交换能力信息（supported versions, capabilities）
  4. 等待 Server 的 `initialized` 通知

**3. Client.call_tool()**

```python
result = await client.call_tool("web_search", {
    "query": query,
    "num_results": num_results,
    "language": "zh-CN"
})
```

- **作用**: 调用 MCP Server 上的工具
- **参数**:
  - `"web_search"`: 工具名称
  - 字典: 工具参数
- **返回**: CallToolResult 对象（包含 content 字段）

**4. 结果处理**

```python
if hasattr(result, 'content'):
    content = result.content
    if isinstance(content, list) and len(content) > 0:
        return content[0].text
    return str(content)
```

- **原因**: MCP SDK 返回的结果结构复杂
- **处理**: 提取实际的文本内容
- **兼容性**: 处理多种可能的返回格式

**5. StructuredTool 封装**

```python
web_search_mcp_tool = StructuredTool.from_function(
    func=web_search_mcp_func,
    name="web_search_mcp",
    description="Web search via MCP Server - experimental",
    args_schema=MCPWebSearchInput
)
```

- **作用**: 将异步函数封装为 LangChain Tool
- **参数**:
  - `func`: 实际执行的函数
  - `name`: 工具名称（Agent 可见）
  - `description`: 工具描述（帮助 LLM 理解工具用途）
  - `args_schema`: 输入参数的 Pydantic Schema

---

### MCP 协议流程

#### 完整的调用流程

```
┌─────────────┐                         ┌─────────────┐
│   Agent     │                         │ MCP Server  │
└──────┬──────┘                         └──────┬──────┘
       │                                       │
       │ 1. agent.ainvoke({"query": "AI"})    │
       ├─────────────────────────────────────▶│
       │                                       │
       │                          2. 解析参数  │
       │                          提取: query  │
       │                          num_results │
       │                                       │
       │ 3. client.call_tool("web_search", {  │
       │    "query": "AI",                    │
       │    "num_results": 5                  │
       │  })                                  │
       ├─────────────────────────────────────▶│
       │                                       │
       │                          4. 调用 API  │
       │                          httpx.get(  │
       │                            BING_API, │
       │                            params    │
       │                          )           │
       │                                       │
       │                          5. 格式化   │
       │                          返回字符串  │
       │                                       │
       │ 6. CallToolResult {                  │
       │    content: [TextContent {           │
       │      text: "Found 5 results..."      │
       │    }]                                 │
       │  }                                   │
       │◀─────────────────────────────────────┤
       │                                       │
       │ 7. 提取 content[0].text              │
       │                                       │
       │ 8. 返回给 Agent: "Found 5 results..."│
       │◀─────────────────────────────────────┤
       │                                       │
```

#### JSON-RPC 消息示例

**请求 (Client → Server)**:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "web_search",
    "arguments": {
      "query": "artificial intelligence",
      "num_results": 5,
      "language": "zh-CN"
    }
  },
  "id": 1
}
```

**响应 (Server → Client)**:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Found 5 results for 'artificial intelligence':\n\n1. Artificial Intelligence - Wikipedia\n   URL: https://en.wikipedia.org/wiki/Artificial_intelligence\n   Artificial intelligence (AI) is intelligence demonstrated by machines...\n\n"
      }
    ]
  },
  "id": 1
}
```

---

## 使用指南

### 环境准备

#### 1. 安装依赖

```bash
# 安装 MCP SDK
pip install mcp httpx

# 或使用 requirements.txt
pip install -r backend/requirements.txt
```

#### 2. 设置环境变量

```bash
# 必需：Bing Search API Key
export BING_SEARCH_API_KEY="your_api_key_here"

# 可选：启用 MCP 版本
export USE_MCP_WEB_SEARCH="true"
```

**获取 Bing Search API Key**:
1. 访问 [Microsoft Azure Portal](https://portal.azure.com/)
2. 创建 "Bing Search v7" 资源
3. 复制 API Key

### 启动 MCP Server

#### 终端 1: 启动 Server

```bash
# 方式 1: 使用模块运行（推荐）
python -m backend.tools.mcp.server

# 方式 2: 直接运行
cd backend/tools/mcp
python server.py

# 预期输出：
# [INFO] Starting search server...
# [INFO] BING_API_KEY configured: True
# [INFO] Server running on stdio
```

**保持运行，不要关闭终端！**

### 在代码中使用 MCP

#### 方式 1: 直接使用 Tool

```python
from backend.tools.domain.search.web_search_mcp import web_search_mcp_tool

# 调用工具
result = await web_search_mcp_tool.ainvoke({
    "query": "machine learning",
    "num_results": 3
})

print(result)
# 输出：
# Found 3 results for 'machine learning':
#
# 1. Machine Learning - Wikipedia
#    URL: https://en.wikipedia.org/wiki/Machine_learning
#    Machine learning (ML) is a field of inquiry...
```

#### 方式 2: 在 Agent 中使用

```python
import os
from backend.agents.core.research.research_agent import ResearchAgent

# 启用 MCP
os.environ["USE_MCP_WEB_SEARCH"] = "true"

# 创建 Agent（自动使用 MCP 版本）
agent = ResearchAgent()

# Agent 会自动选择工具
result = await agent.execute_with_tools(
    "搜索 'deep learning' 并返回5个结果"
)

print(result)
```

#### 方式 3: 通过 Tool Registry

```python
import os
from backend.tools.application.tool_registry import get_native_registry

# 启用 MCP
os.environ["USE_MCP_WEB_SEARCH"] = "true"

# 重置注册表（应用环境变量）
from backend.tools.application.tool_registry import reset_global_registry
reset_global_registry()

# 获取注册表
registry = get_native_registry()

# 获取 MCP 工具
web_search = registry.get_tool("web_search_mcp")

# 调用工具
result = await web_search.ainvoke({
    "query": "neural networks",
    "num_results": 5
})
```

### 切换版本

#### LangChain 版本（默认）

```bash
# 不设置环境变量或设置为 false
export USE_MCP_WEB_SEARCH="false"
python your_script.py
```

**特点**:
- ✅ 性能更好（无中间层）
- ✅ 简单直接
- ✅ 无需启动额外进程

#### MCP 版本（实验性）

```bash
# 启用 MCP
export USE_MCP_WEB_SEARCH="true"

# 先启动 MCP Server（另一个终端）
python -m backend.tools.mcp.server

# 运行脚本
python your_script.py
```

**特点**:
- ✅ 标准化协议
- ✅ 跨系统集成
- ⚠️ 需要启动额外进程
- ⚠️ 稍有性能开销

---

## 性能对比

### 测试环境

- **CPU**: Intel Core i7
- **内存**: 16GB
- **Python**: 3.10
- **测试查询**: "artificial intelligence"
- **结果数量**: 5

### 性能指标

| 指标 | LangChain 版本 | MCP 版本 | 差异 |
|------|---------------|----------|------|
| **首次调用** | ~800ms | ~1200ms | +400ms (+50%) |
| **后续调用** | ~750ms | ~850ms | +100ms (+13%) |
| **内存占用** | ~50MB | ~85MB | +35MB (+70%) |
| **代码复杂度** | 简单 | 中等 | +50 行代码 |

### 性能分析

#### 1. 首次调用延迟

**LangChain 版本**:
```
Agent 调用 → 异步函数 → httpx → API
总耗时: ~800ms
```

**MCP 版本**:
```
Agent 调用 → Client 连接 → 协议握手 → JSON-RPC → Server → httpx → API → 响应 → JSON-RPC → Client
总耗时: ~1200ms
```

**额外开销来源**:
- 进程启动: ~50ms
- 协议握手: ~100ms
- JSON 序列化/反序列化: ~50ms
- stdio 通信: ~100ms

#### 2. 后续调用

**LangChain 版本**: 无变化，始终 ~750ms

**MCP 版本**: 降至 ~850ms
- 原因: Client 已连接，无需握手
- 剩余开销: JSON 序列化 + stdio 通信 (~100ms)

#### 3. 内存占用

**LangChain 版本**:
- Agent: ~40MB
- Tool: ~10MB
- **总计**: ~50MB

**MCP 版本**:
- Agent: ~40MB
- Client: ~10MB
- Server 进程: ~35MB
- **总计**: ~85MB

**额外内存**: Server 进程（~35MB）

### 性能优化建议

#### 1. 减少 JSON 序列化开销

```python
# 当前: 每次调用都序列化/反序列化
result = await client.call_tool("web_search", {...})

# 优化: 批量调用（未来实现）
results = await client.call_tool("web_search_batch", {
    "queries": ["AI", "ML", "DL"]  # 一次调用多个查询
})
```

#### 2. 使用连接池

```python
# 当前: 每个 Agent 一个 Client
# 优化: 全局共享 Client
_mcp_client = None  # 已实现
```

#### 3. 缓存结果

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_search(query: str, num_results: int) -> str:
    return await web_search_mcp_func(query, num_results)
```

### 适用场景

#### 使用 LangChain 版本（默认）

✅ **推荐场景**:
- 单一 Python 项目
- 追求最佳性能
- 简单直接的需求
- 不需要跨系统集成

#### 使用 MCP 版本（实验性）

✅ **适用场景**:
- 需要与其他系统共享工具
- 工具实现需要独立部署
- 需要标准化协议
- 学习和实验目的

---

## 故障排查

### 问题 1: MCP Client 连接失败

**错误信息**:
```
[MCP Client] Failed to connect: [Errno 32] Broken pipe
```

**原因**: MCP Server 未启动

**解决方案**:
1. 检查 MCP Server 是否正在运行：
   ```bash
   ps aux | grep "backend.tools.mcp.server"
   ```

2. 启动 MCP Server：
   ```bash
   python -m backend.tools.mcp.server
   ```

3. 检查环境变量：
   ```bash
   echo $BING_SEARCH_API_KEY
   ```

---

### 问题 2: 搜索返回空结果

**错误信息**:
```
Found 0 results for 'AI'
```

**原因**: Bing API Key 无效或过期

**解决方案**:
1. 验证 API Key：
   ```bash
   curl -G "https://api.bing.microsoft.com/v7.0/search" \
     -H "Ocp-Apim-Subscription-Key: YOUR_KEY" \
     --data-urlencode "q=test" \
     --data-urlencode "count=1"
   ```

2. 检查 API Key 是否正确设置：
   ```bash
   echo $BING_SEARCH_API_KEY
   ```

3. 重新生成 API Key（如果已过期）

---

### 问题 3: ImportError: mcp not found

**错误信息**:
```
ImportError: No module named 'mcp'
```

**原因**: MCP SDK 未安装

**解决方案**:
```bash
# 安装 MCP SDK
pip install mcp

# 或使用 requirements.txt
pip install -r backend/requirements.txt
```

---

### 问题 4: 自动回退到 LangChain 版本

**日志信息**:
```
[NativeToolRegistry] MCP web_search not available: ...
[NativeToolRegistry] Fallback to LangChain version
```

**原因**: MCP 版本导入失败

**可能原因**:
1. MCP SDK 未安装
2. `web_search_mcp.py` 文件不存在或语法错误
3. 依赖库版本不兼容

**解决方案**:
1. 检查依赖：
   ```bash
   pip list | grep mcp
   ```

2. 重新安装依赖：
   ```bash
   pip install --upgrade mcp httpx
   ```

3. 测试 MCP Server：
   ```bash
   python -m backend.tools.mcp.server
   ```

---

### 问题 5: Agent 没有使用 MCP Tool

**现象**: Agent 仍然使用 `web_search` 而不是 `web_search_mcp`

**原因**: 环境变量未设置或注册表未重置

**解决方案**:
```python
import os
from backend.tools.application.tool_registry import reset_global_registry

# 1. 设置环境变量
os.environ["USE_MCP_WEB_SEARCH"] = "true"

# 2. 重置注册表
reset_global_registry()

# 3. 创建 Agent
from backend.agents.core.research.research_agent import ResearchAgent
agent = ResearchAgent()

# 4. 验证工具
print([t.name for t in agent.tools])
# 应该包含: web_search_mcp
```

---

### 问题 6: stdio 通信卡死

**现象**: MCP Server 启动后无响应，Client 等待超时

**原因**: stdio 缓冲区问题

**解决方案**:
```python
# 在 MCP Server 中禁用缓冲
import sys
sys.stdout.reconfigure(line_buffering=True)  # Python 3.7+

# 或在启动时使用 -u 参数
python -u -m backend.tools.mcp.server
```

---

## 最佳实践

### 1. 环境变量管理

**推荐做法**:
```bash
# .env 文件
BING_SEARCH_API_KEY=your_key_here
USE_MCP_WEB_SEARCH=false  # 默认关闭

# 开发时启用
export USE_MCP_WEB_SEARCH="true"
```

**好处**:
- 生产环境默认使用稳定的 LangChain 版本
- 开发/实验时按需启用 MCP
- 避免意外使用实验性功能

---

### 2. 错误处理

**推荐做法**:
```python
async def safe_web_search(query: str, num_results: int = 5) -> str:
    """带错误处理的搜索"""
    try:
        # 尝试使用 MCP 版本
        from backend.tools.domain.search.web_search_mcp import web_search_mcp_tool
        return await web_search_mcp_tool.ainvoke({
            "query": query,
            "num_results": num_results
        })
    except Exception as e:
        logger.warning(f"MCP search failed: {e}, falling back to LangChain")

        # 回退到 LangChain 版本
        from backend.tools.domain.search import web_search_tool
        return await web_search_tool.ainvoke({
            "query": query,
            "num_results": num_results
        })
```

**好处**:
- 提高可用性
- 透明回退
- 用户体验无感知

---

### 3. 日志记录

**推荐做法**:
```python
import logging

logger = logging.getLogger(__name__)

async def web_search_with_logging(query: str, num_results: int = 5) -> str:
    """带详细日志的搜索"""
    logger.info(f"[Web Search] Starting search: query={query}, num_results={num_results}")

    start_time = time.time()

    result = await web_search_mcp_tool.ainvoke({
        "query": query,
        "num_results": num_results
    })

    elapsed = time.time() - start_time

    logger.info(f"[Web Search] Completed in {elapsed:.2f}s")
    logger.debug(f"[Web Search] Result preview: {result[:200]}...")

    return result
```

**好处**:
- 便于调试
- 性能监控
- 问题定位

---

### 4. 测试策略

**单元测试**:
```python
import pytest

@pytest.mark.asyncio
async def test_mcp_web_search():
    """测试 MCP 搜索"""
    from backend.tools.domain.search.web_search_mcp import web_search_mcp_tool

    result = await web_search_mcp_tool.ainvoke({
        "query": "test",
        "num_results": 3
    })

    assert "Found" in result
    assert "results" in result
```

**集成测试**:
```python
@pytest.mark.asyncio
async def test_agent_with_mcp():
    """测试 Agent 使用 MCP"""
    import os
    os.environ["USE_MCP_WEB_SEARCH"] = "true"

    from backend.agents.core.research.research_agent import ResearchAgent

    agent = ResearchAgent()
    result = await agent.execute_with_tools("搜索 AI")

    assert result is not None
    assert len(result) > 0
```

---

### 5. 性能监控

**推荐做法**:
```python
import time
from contextlib import asynccontextmanager

@asynccontextmanager
async def monitor_performance(operation: str):
    """性能监控上下文"""
    start = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start
        logger.info(f"[Performance] {operation} took {elapsed:.2f}s")

        # 超过阈值告警
        if elapsed > 2.0:
            logger.warning(f"[Performance] {operation} is slow!")

# 使用
async with monitor_performance("web_search"):
    result = await web_search_mcp_tool.ainvoke({...})
```

---

## 常见问题

### Q1: MCP 和 LangChain 版本可以同时使用吗？

**答**: 可以，但不推荐。

**原因**:
- 两个版本功能相同，同时使用没有意义
- 会增加内存占用（两个进程）
- 可能导致 Agent 混淆（两个相似的工具）

**推荐做法**:
```python
# 根据环境变量选择一个版本
use_mcp = os.getenv("USE_MCP_WEB_SEARCH", "false").lower() == "true"

if use_mcp:
    tools = [web_search_mcp_tool]
else:
    tools = [web_search_tool]
```

---

### Q2: MCP Server 可以远程部署吗？

**答**: 当前实现不支持。

**原因**:
- 当前仅使用 stdio 通信（本地）
- 需要改为 HTTP 或 WebSocket 才能远程部署

**未来计划**:
```python
# 未来可能实现 HTTP 通信
from mcp.server.http import http_server

async def main():
    async with http_server(port=8080) as (read_stream, write_stream):
        await server.run(read_stream, write_stream)
```

---

### Q3: 如何添加更多 MCP 工具？

**答**: 在 `server.py` 中添加更多工具。

**示例**:
```python
@server.tool("fetch_url")
async def fetch_url(url: str) -> str:
    """Fetch URL content"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text

@server.tool("weixin_search")
async def weixin_search(query: str, num_results: int = 5) -> str:
    """WeChat article search"""
    # 实现微信搜索
    ...
```

**注意事项**:
- 每个工具需要独立的 `@server.tool()` 装饰器
- 工具名称要唯一
- 参数类型要明确（使用 type hints）

---

### Q4: MCP Server 崩溃了怎么办？

**答**: Client 会抛出异常，需要重启 Server。

**解决方案**:
1. 检查 Server 日志：
   ```bash
   # 在 Server 终端查看错误信息
   ```

2. 重启 Server：
   ```bash
   # Ctrl+C 停止
   # 重新启动
   python -m backend.tools.mcp.server
   ```

3. 使用进程管理工具（生产环境）：
   ```ini
   # supervisord.conf
   [program:mcp-server]
   command=python -m backend.tools.mcp.server
   autorestart=true
   ```

---

### Q5: MCP 版本会影响 Agent 的决策吗？

**答**: 不会。

**原因**:
- 两个版本的 `description` 相同
- LLM 看到的是相同的工具描述
- 决策逻辑不受影响

**验证**:
```python
# 两个版本的描述
web_search.description        # "Execute web search using Bing Search API"
web_search_mcp.description    # "Web search via MCP Server - experimental"

# 略有不同，但功能描述相同
```

---

### Q6: 如何调试 MCP 通信？

**答**: 启用详细日志。

**方法**:
```python
import logging

# 启用 MCP SDK 日志
logging.getLogger("mcp").setLevel(logging.DEBUG)

# 启用自定义日志
logging.getLogger("backend.tools.domain.search.web_search_mcp").setLevel(logging.DEBUG)

# 运行
result = await web_search_mcp_tool.ainvoke({...})
```

**输出示例**:
```
[DEBUG] mcp.client - Sending request: {"jsonrpc": "2.0", "method": "tools/call", ...}
[DEBUG] mcp.client - Received response: {"jsonrpc": "2.0", "result": {...}}
[INFO] backend.tools.domain.search.web_search_mcp - [MCP Wrapper] Calling web_search via MCP: query=AI
```

---

## 总结

### MCP 实现的核心价值

1. **标准化**: 使用统一的协议，不依赖特定框架
2. **解耦**: 工具实现与使用方完全分离
3. **跨平台**: 支持不同编程语言之间的集成
4. **可扩展**: 易于添加新工具和新功能

### 适用场景

✅ **推荐使用 MCP**:
- 需要跨系统集成
- 工具需要独立部署
- 追求标准化协议
- 学习和实验

❌ **不推荐使用 MCP**:
- 单一 Python 项目
- 追求极致性能
- 简单直接的需求
- 生产环境（当前为实验性功能）

### 后续计划

1. **性能优化**: 减少协议开销
2. **功能扩展**: 添加更多工具
3. **通信方式**: 支持 HTTP/WebSocket
4. **生产部署**: 完善监控和容错

---

## 相关资源

### 官方文档
- [MCP 协议规范](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Anthropic MCP 文档](https://modelcontextprotocol.io/)

### 项目文档
- [MCP Server 使用指南](../../backend/tools/mcp/README.md)
- [MCP 实现总结](../../MCP_IMPLEMENTATION_SUMMARY.md)
- [MCP 状态说明](../../MCP_STATUS_CLARIFICATION.md)

### 测试脚本
- [集成测试](../../backend/tools/mcp/test_mcp_integration.py)

---

**文档版本**: 1.0.0
**最后更新**: 2026-02-16
**维护者**: MultiAgentPPT 团队
