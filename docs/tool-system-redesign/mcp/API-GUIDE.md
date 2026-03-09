# MCP环境配置指南

> MultiAgentPPT项目的MCP服务器配置详细步骤

---

## 📋 前置要求

### 必需软件

| 软件 | 版本要求 | 用途 | 检查命令 |
|------|----------|------|----------|
| **Node.js** | >= 18.0.0 | 运行Zai MCP Server | `node --version` |
| **npx** | 随Node.js安装 | 执行npm包 | `npx --version` |
| **Python** | >= 3.10 | 运行项目 | `python --version` |
| **pip** | 随Python安装 | 安装Python包 | `pip --version` |

### 安装Node.js

**Windows**:
```bash
# 使用winget安装
winget install OpenJS.NodeJS.LTS

# 或访问官网下载安装包
# https://nodejs.org/
```

**macOS**:
```bash
# 使用Homebrew安装
brew install node
```

**Linux**:
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 验证安装

```bash
# 检查Node.js版本
node --version
# 应输出: v18.x.x 或更高

# 检查npx
npx --version
# 应输出版本号
```

---

## 🔑 API密钥申请

### 智谱 AI API Key

#### Step 1: 注册账号

1. 访问智谱AI开放平台: https://open.bigmodel.cn/
2. 点击右上角 **"注册"**
3. 支持以下登录方式:
   - 手机号注册
   - 邮箱注册

#### Step 2: 获取API Key

1. 登录后进入控制台
2. 点击 **"API Key"**
3. 点击 **"新增API Key"**
4. 复制保存API Key（格式: `xxxxxxxxxxxxxxxx.xxxxxx`）

**注意**:
- ⚠️ API Key只显示一次，请立即复制保存
- 🔑 一个账号可以创建多个API Key
- 💰 新用户有免费额度

#### Step 3: 查看使用配额

免费套餐包含:
- ✅ 新用户赠送Token额度
- 💳 按需付费，用完充值

---

## ⚙️ MCP配置文件

### 创建配置文件

在项目根目录创建 `config/mcp_config.yaml`:

```bash
mkdir -p config
touch config/mcp_config.yaml
```

### 完整配置示例

```yaml
# config/mcp_config.yaml

# MCP服务器配置
servers:
  # ============================================
  # 智谱搜索服务器 (HTTP)
  # ============================================
  zhipu-search:
    type: "http"
    url: "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp"
    headers:
      Authorization: "Bearer ${ZHIPU_API_KEY}"

  # ============================================
  # Zai视觉服务器 (本地子进程)
  # ============================================
  zai-vision:
    type: "stdio"
    command: "npx"
    args: ["-y", "@z_ai/mcp-server"]
    env:
      Z_AI_API_KEY: "${ZAI_API_KEY}"
      Z_AI_MODE: "ZHIPU"
```

### 配置说明

**zhipu-search**:
- `type: "http"` - HTTP远程服务
- `url`: 智谱MCP服务地址
- `headers`: 认证信息

**zai-vision**:
- `type: "stdio"` - 本地子进程
- `command`: 使用npx执行
- `args`: 启动参数
  - `-y`: 自动确认安装
  - `@z_ai/mcp-server`: Zai MCP Server包名
- `env`: 环境变量
  - `Z_AI_API_KEY`: API密钥
  - `Z_AI_MODE`: 使用智谱模型

---

## 🌍 环境变量配置

### 创建.env文件

在项目根目录创建 `.env` 文件:

```bash
# .env

# 智谱AI API Key
# 申请地址: https://open.bigmodel.cn/
ZHIPU_API_KEY=your_zhipu_api_key_here

# Zai API Key (通常与智谱相同)
ZAI_API_KEY=your_zai_api_key_here
```

### 加载环境变量

**使用python-dotenv**:

```python
# backend/config.py
from dotenv import load_dotenv
import os

# 加载.env文件
load_dotenv()

# 获取API Key
ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY')
ZAI_API_KEY = os.getenv('ZAI_API_KEY')
```

**安装依赖**:

```bash
pip install python-dotenv
```

### .env安全

**重要**: `.env` 文件包含敏感信息，不要提交到Git！

确保 `.gitignore` 包含:

```gitignore
# .gitignore

# 环境变量
.env
.env.local

# MCP配置
config/mcp_config.yaml
```

---

## 🧪 测试MCP服务器

### 测试智谱搜索

```bash
# 使用curl测试
curl -X POST "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp" \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "人工智能发展趋势",
    "count": 5
  }'
```

### 测试Zai视觉

```bash
# 启动Zai MCP Server
npx -y @z_ai/mcp-server

# 在另一个终端测试（需要MCP客户端）
```

---

## 🔧 Zai MCP Server 详细说明

### 安装

```bash
# 全局安装（推荐）
npm install -g @z_ai/mcp-server

# 或使用npx直接运行
npx -y @z_ai/mcp-server
```

### 支持的工具

| 工具名称 | 功能 | 参数 |
|----------|------|------|
| `vision_understand` | 图片内容理解 | image_url, detail_level |
| `vision_ocr` | 文字识别 | image_url, language |
| `vision_qa` | 视觉问答 | image_url, question |
| `vision_compare` | 图片对比 | image_url1, image_url2 |

### 使用示例

```python
# 图片理解
await zai_vision_tool.invoke(
    tool_name="vision_understand",
    image_url="https://example.com/image.jpg",
    detail_level="high"
)

# 视觉问答
await zai_vision_tool.invoke(
    tool_name="vision_qa",
    image_url="https://example.com/image.jpg",
    question="图片中是什么场景？"
)

# 文字识别
await zai_vision_tool.invoke(
    tool_name="vision_ocr",
    image_url="https://example.com/text.jpg",
    language="zh"
)
```

---

## 🐛 常见问题排查

### 问题1: npx命令找不到

**错误信息**:
```
'npx' 不是内部或外部命令
```

**解决方案**:
1. 确认Node.js已正确安装
2. 重新打开终端（环境变量可能需要刷新）
3. Windows: 重启电脑
4. 检查PATH环境变量

---

### 问题2: 智谱API Key无效

**错误信息**:
```
Error: Invalid API key
```

**解决方案**:
1. 确认API Key格式正确
2. 检查环境变量是否正确加载
3. 确认API Key没有过期
4. 访问控制台查看使用情况

---

### 问题3: Zai MCP Server启动失败

**错误信息**:
```
Error: Failed to start Zai MCP Server
```

**解决方案**:
1. 检查网络连接
2. 确认ZAI_API_KEY正确
3. 更新npx: `npm update -g npx`
4. 清除缓存: `npx cache clean`

---

### 问题4: 视觉分析超时

**错误信息**:
```
Timeout during vision analysis
```

**解决方案**:
1. 检查网络连接
2. 减小图片尺寸
3. 降低detail_level
4. 添加重试机制

---

## 📊 监控和调试

### 查看MCP服务器日志

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 性能监控

```python
import time

async def monitored_mcp_call(tool, **kwargs):
    """监控MCP调用性能"""
    start = time.time()

    result = await tool.invoke(**kwargs)

    duration = time.time() - start
    logging.info(f"{tool.name} 调用耗时: {duration:.2f}s")

    return result
```

### 错误追踪

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def resilient_mcp_call(tool, **kwargs):
    """带重试的MCP调用"""
    return await tool.invoke(**kwargs)
```

---

## 🚀 快速启动脚本

### Windows (PowerShell)

```powershell
# scripts/start-mcp.ps1

# 加载环境变量
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}

Write-Host "✅ 环境变量已加载" -ForegroundColor Green
Write-Host "Zhipu API Key: $env:ZHIPU_API_KEY" -ForegroundColor Cyan
Write-Host "Zai API Key: $env:ZAI_API_KEY" -ForegroundColor Cyan
Write-Host ""
Write-Host "MCP服务器配置完成！" -ForegroundColor Green
```

### Linux/macOS (Bash)

```bash
#!/bin/bash
# scripts/start-mcp.sh

# 加载环境变量
export $(cat .env | grep -v '^#' | xargs)

# 创建日志目录
mkdir -p logs

echo "✅ 环境变量已加载"
echo "Zhipu API Key: ${ZHIPU_API_KEY:0:10}..."
echo "Zai API Key: ${ZAI_API_KEY:0:10}..."
echo ""
echo "🎉 MCP服务器配置完成！"
```

---

## 📝 配置检查清单

使用此清单确保配置正确：

- [ ] Node.js >= 18.0.0 已安装
- [ ] npx 可用
- [ ] 智谱AI API Key 已获取
- [ ] .env 文件已创建并配置
- [ ] mcp_config.yaml 已创建
- [ ] Zai MCP Server 可启动
- [ ] 智谱搜索API可调用
- [ ] .gitignore 已更新

---

**文档版本**: v2.0
**更新日期**: 2026-03-07
**适用项目**: MultiAgentPPT
