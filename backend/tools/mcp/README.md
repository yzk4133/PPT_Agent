# MCP Server 使用指南

本文档说明如何启动和使用 MCP Server。

---

## 🚀 快速启动

### 步骤 1：配置环境变量

```bash
# .env 或环境变量
export BING_SEARCH_API_KEY="your_api_key_here"
```

### 步骤 2：安装依赖

```bash
# 安装 MCP SDK
pip install mcp httpx

# 或使用 requirements.txt
pip install -r requirements.txt
```

### 步骤 3：启动 MCP Server

```bash
# 方式 1：使用模块运行（推荐）
python -m backend.tools.mcp.server

# 方式 2：直接运行
cd backend/tools/mcp
python server.py

# 输出：
# [INFO] __main__ - Starting search server...
# [INFO] __main__ - BING_API_KEY configured: True
# [INFO] mcp.server.stdio - Server running on stdio
```

### 步骤 4：保持运行

MCP Server 需要保持运行，不要关闭终端。

---

## 🔍 验证 Server 是否正常

### 使用 MCP CLI 测试

```bash
# 安装 MCP CLI（如果需要）
npm install -g @modelcontextprotocol/cli

# 列出工具
mcp list-tools python -m backend.tools.mcp.server

# 调用工具
mcp call python -m backend.tools.mcp.server web_search --query "AI" --numResults 3
```

### 使用 Python 测试脚本

创建 `test_mcp_server.py`：

```python
import asyncio
from mcp.client import Client, StdioServerParameters

async def test():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "backend.tools.mcp.server"]
    )

    async with Client(server_params) as client:
        await client.initialize()

        # 列出工具
        tools = await client.list_tools()
        print(f"Available tools: {len(tools)}")

        # 调用工具
        result = await client.call_tool("web_search", {
            "query": "artificial intelligence",
            "num_results": 3
        })

        print("\nResult:")
        print(result)

asyncio.run(test())
```

运行测试：
```bash
python test_mcp_server.py
```

---

## 📊 日志输出

### 正常运行的日志

```
[INFO] __main__ - Starting search server...
[INFO] __main__ - BING_API_KEY configured: True
[INFO] mcp.server.stdio - Server running on stdio
[INFO] mcp.server.stdio - Received initialize request
[INFO] mcp.server.stdio - Sending initialize response
[INFO] mcp.server.stdio - Received tools/call request
[INFO] __main__ - [MCP Server] web_search called: query=AI, num_results=5
[INFO] __main__ - [MCP Server] Found 5 results
[INFO] __main__ - [MCP Server] Returning 5 results
```

---

## 🔧 配置选项

### 环境变量

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `BING_SEARCH_API_KEY` | ✅ | - | Bing Search API 密钥 |
| `LOG_LEVEL` | ❌ | INFO | 日志级别 |

### 启动参数

```bash
# 自定义日志级别
LOG_LEVEL=DEBUG python -m backend.tools.mcp.server

# 使用不同的工作目录
cd /path/to/project
python -m backend.tools.mcp.server
```

---

## ⚠️ 常见问题

### Q1: 启动后没有输出

**检查清单**：
```bash
# 1. 检查环境变量
echo $BING_SEARCH_API_KEY

# 2. 检查依赖安装
pip list | grep mcp

# 3. 检查端口冲突（如果有 HTTP 模式）
#（stdio 模式不需要端口）
```

### Q2: Agent 调用失败

**错误信息**：
```
[MCP Client] Failed to connect: [Errno 32] Broken pipe
```

**解决方案**：
1. 确保 MCP Server 正在运行
2. 检查是否在正确的目录
3. 查看两个终端的日志输出

### Q3: 搜索返回空结果

**检查**：
```bash
# 验证 API Key 是否有效
curl -G https://api.bing.microsoft.com/v7.0/search \
  -H "Ocp-Apim-Subscription-Key: YOUR_KEY" \
  "q=test&count=1"
```

### Q4: 如何停止 Server

**方式 1**：在终端按 `Ctrl+C`

**方式 2**：关闭终端窗口

**方式 3**（开发环境）：
```bash
# 查找进程
ps aux | grep "backend.tools.mcp.server"

# 杀死进程
kill <PID>
```

---

## 🚀 生产环境部署

### 使用 systemd（Linux）

创建 `/etc/systemd/systemd/mcp-search-server.service`：

```ini
[Unit]
Description=MCP Search Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/MultiAgentPPT
Environment="PATH=/path/to/venv/bin"
EnvironmentFile=/path/to/.env
ExecStart=/path/to/venv/bin/python -m backend.tools.mcp.server

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**启动服务**：
```bash
# 启用服务
sudo systemctl enable mcp-search-server

# 启动服务
sudo systemctl start mcp-search-server

# 查看状态
sudo systemctl status mcp-search-server

# 查看日志
sudo journalctl -u mcp-search-server -f
```

### 使用 supervisord（跨平台）

配置文件 `supervisord.conf`：

```ini
[program:mcp-search-server]
command=/path/to/venv/bin/python -m backend.tools.mcp.server
directory=/path/to/MultiAgentPPT
autostart=true
autorestart=true
stderr_logfile=/var/log/mcp-server.err.log
stdout_logfile=/var/log/mcp-server.out.log
user=your_user
environment=BING_SEARCH_API_KEY="%(env_BING_SEARCH_API_KEY)s"
```

**启动**：
```bash
supervisord -c supervisord.conf
```

---

## 🔗 相关文档

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Tools 规范](https://spec.modelcontextprotocol.io/)
- [MCP_STATUS_CLARIFICATION.md](../../../MCP_STATUS_CLARIFICATION.md) - MCP 在项目中的状态说明

---

**最后更新**: 2026-02-16
**维护者**: MultiAgentPPT 团队
