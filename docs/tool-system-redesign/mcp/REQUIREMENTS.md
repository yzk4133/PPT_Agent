# MCP集成需求文档

> MultiAgentPPT项目的MCP（Model Context Protocol）集成方案

---

## 📋 文档信息

| 项目 | 内容 |
|------|------|
| **项目名称** | MultiAgentPPT |
| **文档版本** | v2.0 |
| **创建日期** | 2026-03-07 |
| **更新日期** | 2026-03-07 |
| **文档类型** | MCP集成需求文档 |
| **文档状态** | ✅ 已确认 |

---

## 🎯 项目背景

### 项目定位

**MultiAgentPPT** 是一个基于多Agent协作的**PPT自动生成工具**。

### 核心功能

接收用户的PPT主题需求，自动完成：
1. **需求分析** - 理解用户想要什么样的PPT
2. **内容规划** - 设计PPT的结构和大纲
3. **内容生成** - 为每页生成具体内容和配图
4. **格式化输出** - 生成最终的PPT文件

---

## 💡 为什么需要MCP

### 1. 复用生态工具

MCP生态中已有成熟的服务器实现，无需重复造轮子：

| 需求 | MCP解决方案 |
|------|-------------|
| 高质量搜索 | `zhipu web-search-prime` |
| 图片理解 | `zai-mcp-server` |

### 2. 统一协议，易于扩展

- 所有外部能力都用统一的 `invoke()` 接口
- Agent无需关心工具是本地还是远程
- 新增能力只需注册新的MCP服务器

### 3. 解耦系统架构

- PPT生成核心逻辑与外部服务解耦
- 可灵活替换或升级MCP服务器
- 支持分布式部署

---

## 🏗️ 系统架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                    PPT生成Agent                          │
│                  (本地Python代码)                        │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │              LLM决策层（本地调用）                 │   │
│  │         使用LangChain直接调用OpenAI等API          │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                                │
│                          ▼                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Tool Registry                        │   │
│  │     ┌────────────────────────────────────┐       │   │
│  │     │         本地Tool                    │       │   │
│  │     │  • create_pptx (PPT生成)           │       │   │
│  │     │  • template_manager (模板管理)      │       │   │
│  │     │  • image_processor (图片处理)       │       │   │
│  │     │  • search_images (图片搜索)         │       │   │
│  │     │  • file_reader (文件读取)           │       │   │
│  │     └────────────────────────────────────┘       │   │
│  │     ┌────────────────────────────────────┐       │   │
│  │     │         MCP Tool                   │       │   │
│  │     │  • zhipu_web_search (网络搜索)     │       │   │
│  │     │  • zai_vision (图片理解)           │       │   │
│  │     └────────────────────────────────────┘       │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                                │
└──────────────────────────┼────────────────────────────────
                           │
                           ▼
         ┌───────────────────────────────────┐
         │       MCP Servers                 │
         ├───────────────────────────────────┤
         │                                   │
         │  ┌─────────────────────────────┐  │
         │  │  智谱 AI (HTTP)              │  │
         │  │  • web-search-prime         │  │
         │  │  端口: HTTPS API            │  │
         │  └─────────────────────────────┘  │
         │                                   │
         │  ┌─────────────────────────────┐  │
         │  │  Zai MCP Server (本地子进程) │  │
         │  │  • 图片理解                  │  │
         │  │  端口: stdin/stdout          │  │
         │  └─────────────────────────────┘  │
         │                                   │
         └───────────────────────────────────┘
```

### 核心设计原则

**1. LLM本地调用**
- LLM是核心决策能力，应该紧密集成
- 使用LangChain等框架直接调用OpenAI/Claude等API
- 性能最优，延迟最低

**2. MCP处理外部能力**
- MCP负责调用外部服务API
- 统一协议，易于管理和扩展
- 支持HTTP和本地子进程两种方式

**3. Tool统一接口**
- 本地Tool和MCP Tool都实现 `invoke(**kwargs)` 接口
- Agent调用时无需区分工具类型

---

## 📦 MCP服务器选型

### 选型依据

基于PPT生成流程的功能需求分析，确定以下MCP服务器：

### 1. 智谱 web-search-prime

**部署方式**: HTTP远程服务

**功能**: 使用智谱AI的高质量搜索API进行网络搜索

**应用场景**:
- 搜索PPT主题相关的最新资料
- 查找案例、数据和统计信息
- 获取行业报告和参考内容
- 中文搜索优化

**为什么选择智谱搜索**:
- 提供官方MCP HTTP接口
- 搜索质量高，中文支持好
- 已订阅Coding Plan，无需额外付费
- HTTP调用，无需本地Node.js环境

**配置示例**:
```json
{
  "mcpServers": {
    "web-search-prime": {
      "type": "streamable-http",
      "url": "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp",
      "headers": {
        "Authorization": "Bearer your_api_key"
      }
    }
  }
}
```

**官方文档**: https://open.bigmodel.cn/

---

### 2. zai-mcp-server

**部署方式**: 本地子进程

**功能**: 提供多种视觉理解能力

**应用场景**:
- **图片内容分析**: 理解图片中的内容、文字、场景
- **图片描述生成**: 为PPT配图生成描述文字
- **图片选择建议**: 根据内容推荐合适的配图
- **OCR文字识别**: 提取图片中的文字信息
- **图片质量评估**: 判断图片是否适合用于PPT

**能力列表**:
- `vision_understand` - 图片理解
- `vision_ocr` - 文字识别
- `vision_qa` - 视觉问答
- `vision_compare` - 图片对比

**为什么选择zai-mcp-server**:
- 提供完整的视觉理解能力
- 支持智谱AI视觉模型
- 本地子进程，性能好
- 付费服务，质量有保障

**配置示例**:
```json
{
  "mcpServers": {
    "zai-mcp-server": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@z_ai/mcp-server"],
      "env": {
        "Z_AI_API_KEY": "your_api_key",
        "Z_AI_MODE": "ZHIPU"
      }
    }
  }
}
```

**官方仓库**: `@z_ai/mcp-server`

---

## 🔄 PPT生成流程与能力分配

### 完整流程图

```
用户输入: "制作一份关于AI发展趋势的PPT"
         │
         ▼
┌──────────────────────────────────────────┐
│  Step 1: 需求分析                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  能力: LLM本地调用                        │
│  输出: 理解用户需求，提取关键信息         │
└──────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  Step 2: 内容规划                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  能力: LLM本地调用                        │
│  输出: PPT大纲、每页标题和要点            │
└──────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  Step 3: 内容生成                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  子步骤3.1: 生成文本内容                 │
│    能力: LLM本地调用 + Python Skills     │
│    输出: 每页的详细文本内容              │
│                                          │
│  子步骤3.2: 搜索相关资料                 │
│    能力: MCP zhipu_web_search           │
│    输出: 相关资料、数据、案例             │
│                                          │
│  子步骤3.3: 获取和筛选配图               │
│    能力: search_images + MCP zai_vision │
│    输出: 筛选后的合适配图                │
└──────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  Step 4: 格式化输出                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  子步骤4.1: 生成PPT文件                  │
│    能力: 本地 create_pptx               │
│    输出: PPT文件对象                     │
│                                          │
│  子步骤4.2: 处理图片                     │
│    能力: 本地 image_processor            │
│    输出: 调整大小和格式的图片            │
└──────────────────────────────────────────┘
         │
         ▼
    输出: final.pptx
```

### 能力分配矩阵

| 步骤 | 子步骤 | 所需能力 | 实现方式 |
|------|--------|----------|----------|
| **需求分析** | 理解用户意图 | 自然语言理解 | LLM本地调用 |
| **内容规划** | 生成PPT大纲 | 结构化内容生成 | LLM本地调用 |
| **内容生成** | 生成文本内容 | 文本创作 | LLM + Python Skills |
| **内容生成** | 搜索相关资料 | 网络搜索 | **MCP: zhipu_web_search** |
| **内容生成** | 获取配图 | 图片搜索 | 本地: search_images |
| **内容生成** | 筛选配图 | 图片理解 | **MCP: zai_vision** |
| **格式化输出** | 生成PPT文件 | PPT格式化 | 本地: create_pptx |
| **格式化输出** | 处理图片 | 图片处理 | 本地: image_processor |

---

## ⚙️ MCP配置方案

### 部署方式总结

| MCP服务器 | 部署方式 | 理由 |
|-----------|----------|------|
| **zhipu web-search-prime** | HTTP远程 | 智谱云服务，无需本地环境 |
| **zai-mcp-server** | 本地子进程 | 需要调用视觉模型，本地性能好 |

### 配置文件结构

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

### 环境变量

```bash
# .env 文件

# 智谱AI API Key
# 申请地址: https://open.bigmodel.cn/
ZHIPU_API_KEY=your_zhipu_api_key_here

# Zai API Key (如果与智谱不同)
ZAI_API_KEY=your_zai_api_key_here
```

---

## 📁 项目结构

```
backend/
├── agents/
│   └── core/
│       └── mcp/                           # MCP模块
│           ├── __init__.py
│           ├── http_client.py             # HTTP MCP客户端
│           ├── stdio_client.py            # stdio MCP客户端
│           └── servers.py                 # 服务器配置
│
├── tools/
│   ├── domain/
│   │   ├── resource/
│   │   │   ├── zhipu_search_tool.py       # 智谱搜索工具
│   │   │   └── zai_vision_tool.py         # Zai视觉工具
│   │   └── ...
│   │
│   └── application/
│       └── tool_registry.py               # 工具注册表
│
├── config/
│   └── mcp_config.yaml                    # MCP配置文件
│
└── main.py                                # 主入口

resources/                                  # 资源目录
├── templates/                             # PPT模板
├── images/                                # 图片资源
└── output/                                # 输出目录
```

---

## 🔑 API密钥申请

### 智谱 AI API Key

**申请地址**: https://open.bigmodel.cn/

**申请步骤**:
1. 访问智谱AI开放平台
2. 注册/登录账号
3. 进入API Key管理
4. 创建新的API Key
5. 复制保存（只显示一次）

**定价**:
- 免费额度: 新用户有免费额度
- 付费版: 按Token计费

**用途**:
- web-search-prime 搜索
- zai-mcp-server 视觉理解

---

## 📊 数据流示例

### 智谱搜索调用

```python
# 伪代码示例

async def search_references(topic: str):
    """搜索参考资料"""

    # 调用智谱MCP搜索
    results = await zhipu_search_tool.invoke(
        query=topic,
        count=5
    )

    # 处理搜索结果
    for result in results:
        print(f"标题: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"摘要: {result['snippet']}")

    return results
```

### Zai视觉理解调用

```python
# 伪代码示例

async def select_best_image(images: list, slide_content: str):
    """选择最合适的配图"""

    best_image = None
    best_score = 0

    for image_url in images:
        # 使用Zai视觉理解分析图片
        analysis = await zai_vision_tool.invoke(
            tool_name="vision_understand",
            image_url=image_url
        )

        # 根据内容匹配度打分
        score = calculate_relevance(analysis, slide_content)

        if score > best_score:
            best_score = score
            best_image = image_url

    return best_image
```

---

## ✅ 验收标准

### 功能验收

- [ ] 智谱搜索可以正常返回中文搜索结果
- [ ] Zai视觉可以正确分析图片内容
- [ ] 两个MCP服务器可以同时运行
- [ ] Agent可以通过统一的Tool接口调用MCP
- [ ] 完整的PPT生成流程可以端到端执行

### 性能验收

| 指标 | 目标值 |
|------|--------|
| 智谱搜索响应时间 | < 3s |
| Zai视觉分析时间 | < 5s |
| MCP服务器启动时间 | < 10s |
| 端到端PPT生成时间 | < 60s |

### 稳定性验收

- [ ] MCP服务器异常可以自动重试
- [ ] 网络错误可以降级处理
- [ ] API限流可以正确处理
- [ ] 资源正确释放（进程关闭）

---

## 📅 实施计划

### Phase 1: 环境准备（1天）

- [ ] 申请智谱AI API Key
- [ ] 安装Node.js和npx
- [ ] 安装Zai MCP Server
- [ ] 创建配置文件

### Phase 2: MCP客户端开发（2天）

- [ ] 实现HTTP MCP客户端
- [ ] 实现stdio MCP客户端
- [ ] 实现MCP Tool包装器
- [ ] 单元测试

### Phase 3: 工具集成（2天）

- [ ] 实现智谱搜索工具
- [ ] 实现Zai视觉工具
- [ ] 集成到Tool Registry
- [ ] 集成测试

### Phase 4: 优化完善（1天）

- [ ] 错误处理和重试机制
- [ ] 性能优化
- [ ] 日志和监控
- [ ] 文档完善

**总预计时间**: 6天

---

## 📚 参考资料

### MCP官方文档

- MCP协议规范: https://modelcontextprotocol.io/
- Python SDK文档: https://github.com/modelcontextprotocol/python-sdk

### 服务商文档

- 智谱AI开放平台: https://open.bigmodel.cn/
- Zai MCP Server: `@z_ai/mcp-server`

### 相关技术

- LangChain: https://python.langchain.com/
- python-pptx: https://python-pptx.readthedocs.io/

---

## 📝 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2026-03-07 | 初始版本（3个MCP） | System |
| v2.0 | 2026-03-07 | 精简为2个MCP，添加Zai视觉 | System |

---

**文档状态**: ✅ 需求已确认，可以开始实施
