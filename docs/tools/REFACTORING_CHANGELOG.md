# 工具系统重构变更日志

本文档详细说明了 MultiAgentPPT 工具系统在 2025年2月 重构过程中的所有变化。

---

## 📋 目录

- [概述](#概述)
- [重构目标](#重构目标)
- [架构变化](#架构变化)
- [新增功能](#新增功能)
- [废弃功能](#废弃功能)
- [迁移指南](#迁移指南)
- [文件变更清单](#文件变更清单)
- [配置变化](#配置变化)
- [依赖变化](#依赖变化)

---

## 概述

本次重构是对 `backend/agents/tools/` 目录的全面升级，引入了 **MCP 工具**和 **Skills 体系**，实现了更加模块化、可扩展的工具框架。

### 重构范围

- ✅ **MCP 工具实现**：6个外部 API 集成工具
- ✅ **Skills 框架扩展**：5个提示词型 Skills + 4个函数型 Skills
- ✅ **统一注册表**：整合工具和 Skills 的注册机制
- ✅ **向后兼容**：保留旧工具并添加废弃警告
- ✅ **测试覆盖**：完整的测试套件
- ✅ **文档完善**：详细的使用文档

---

## 重构目标

### 之前的问题

1. **工具混乱**：工具分散在多个目录，缺乏统一管理
2. **功能单一**：只有基础的文档搜索和图片搜索
3. **缺少封装**：复杂流程没有可复用的能力封装
4. **缺少标准**：工具接口不一致，错误处理不统一

### 重构后的改进

1. **统一架构**：MCP 工具 + Skills 双层体系
2. **标准化接口**：所有工具返回统一的 JSON 格式
3. **可扩展性**：新增工具和技能变得简单
4. **向后兼容**：旧代码可以继续工作

---

## 架构变化

### 之前的目录结构

```
backend/agents/tools/
├── registry/
│   ├── tool_registry.py       # 旧注册表
│   └── unified_registry.py    # 统一注册表
├── search/
│   └── document_search.py     # 文档搜索
├── media/
│   └── image_search.py        # 图片搜索
└── skills/
    ├── skill_decorator.py
    ├── skill_loaders.py
    └── ...
```

### 重构后的目录结构

```
backend/agents/tools/
├── mcp/                          # [NEW] MCP 工具
│   ├── __init__.py
│   ├── base_mcp_tool.py          # [NEW] 基类
│   ├── web_search.py             # [NEW] 网络搜索
│   ├── fetch_url.py              # [NEW] 网页抓取
│   ├── search_images.py          # [NEW] 图片搜索
│   ├── create_pptx.py            # [NEW] PPT生成
│   ├── state_store.py            # [NEW] 状态存储
│   ├── vector_search.py          # [NEW] 向量搜索
│   └── mcp_integration.py        # [EXISTING] MCP集成
│
├── skills/                       # [ENHANCED] Skills框架
│   ├── prompts/                  # [NEW] 提示词型Skills
│   │   ├── README.md
│   │   ├── research_topic.md
│   │   ├── select_layout.md
│   │   ├── quality_check.md
│   │   ├── synthesize_info.md
│   │   └── optimize_content.md
│   ├── functions/                # [NEW] 函数型Skills
│   │   ├── __init__.py
│   │   ├── research_skill.py
│   │   ├── layout_skill.py
│   │   ├── scheduler_skill.py
│   │   └── retry_skill.py
│   ├── skill_decorator.py        # [EXISTING]
│   ├── skill_loaders.py          # [MODIFIED] 支持md和py
│   ├── skill_metadata.py         # [EXISTING]
│   └── ...
│
├── registry/
│   ├── tool_registry.py          # [DEPRECATED] 旧注册表
│   └── unified_registry.py       # [MODIFIED] 注册MCP工具
│
├── search/                       # [DEPRECATED] 保留但标记废弃
│   └── document_search.py        # [MODIFIED] 添加废弃警告
│
├── media/                        # [DEPRECATED] 保留但标记废弃
│   └── image_search.py           # [MODIFIED] 添加废弃警告
│
├── tests/                        # [NEW] 测试套件
│   ├── test_mcp_tools.py
│   └── test_skills.py
│
└── README.md                     # [NEW] 工具系统文档
```

---

## 新增功能

### 1. MCP 工具 (6个)

#### web_search

**功能**：使用 Bing Search API v7 执行网络搜索

**接口**：
```python
await web_search(
    query: str,              # 搜索关键词
    num_results: int = 5,    # 返回结果数量 (1-10)
    search_engine: str = "bing",
    language: str = "zh-CN",
    time_range: str = "any"  # any, day, week, month, year
)
```

**返回格式**：
```json
{
  "success": true,
  "result": {
    "results": [
      {
        "title": "结果标题",
        "url": "https://example.com",
        "snippet": "摘要描述",
        "source": "example.com",
        "relevance_score": 0.8
      }
    ]
  }
}
```

**配置**：
```bash
BING_SEARCH_API_KEY=your_key_here
```

#### fetch_url

**功能**：获取并提取网页内容（使用 readability）

**接口**：
```python
await fetch_url(
    url: str,                       # 目标URL
    timeout: int = 10,              # 超时时间（秒）
    extract_type: str = "main_content",  # full, main_content, text_only
    use_cache: bool = True          # 是否使用缓存
)
```

**返回格式**：
```json
{
  "success": true,
  "result": {
    "url": "https://example.com",
    "title": "页面标题",
    "text_content": "提取的纯文本内容",
    "word_count": 1500,
    "from_cache": false
  }
}
```

**特性**：
- 自动缓存（TTL: 1小时）
- 支持 readability 提取主要内容
- HTML 转文本

#### search_images

**功能**：使用 Unsplash/Pexels API 搜索图片

**接口**：
```python
await search_images(
    query: str,                   # 搜索关键词
    num_results: int = 5,         # 返回数量
    orientation: str = "landscape",  # landscape, portrait, squarish
    size: str = "large",          # small, medium, large, original
    color: str = "any",           # 颜色过滤
    source: str = "unsplash"      # unsplash, pexels
)
```

**返回格式**：
```json
{
  "success": true,
  "result": {
    "images": [
      {
        "url": "https://images.unsplash.com/photo-xxx",
        "thumbnail": "https://images.unsplash.com/photo-xxx?w=200",
        "description": "图片描述",
        "photographer": "摄影师名称",
        "width": 1920,
        "height": 1080,
        "source": "unsplash"
      }
    ]
  }
}
```

**配置**：
```bash
UNSPLASH_ACCESS_KEY=your_key_here
PEXELS_API_KEY=your_key_here
```

#### create_pptx

**功能**：使用 python-pptx 生成 PowerPoint 文件

**接口**：
```python
await create_pptx(
    slides: List[Dict],      # 幻灯片数据
    output_path: str,        # 输出文件路径
    template_path: str = None,  # 模板路径（可选）
    theme: Dict = None       # 主题配置（可选）
)
```

**幻灯片数据格式**：
```python
{
    "layout": "Title and Content",  # 布局类型
    "title": "幻灯片标题",
    "subtitle": "副标题",
    "content": ["要点1", "要点2", "要点3"],
    "images": ["url1", "url2"],
    "notes": "演讲者备注"
}
```

**支持的布局**：
- Title (标题页)
- Title and Content (标题+内容)
- Section Header (章节页)
- Two Content (双栏)
- Comparison (对比)
- Title Only (仅标题)
- Blank (空白)

#### state_store

**功能**：状态存储（支持 Redis 和文件系统）

**接口**：
```python
await state_store(
    operation: str,         # get, set, delete, list
    key: str,              # 状态键
    value: Any,            # 状态值（set时）
    namespace: str = "default"  # 命名空间
)
```

**使用示例**：
```python
# 存储状态
await state_store(
    operation="set",
    key="research_results",
    value={"data": "..."},
    namespace="research_agent"
)

# 获取状态
result = await state_store(
    operation="get",
    key="research_results",
    namespace="research_agent"
)

# 列出所有键
keys = await state_store(
    operation="list",
    namespace="research_agent"
)
```

**配置**：
```bash
# 可选：Redis（优先）
REDIS_URL=redis://localhost:6379/0

# 或使用文件存储
MCP_STATE_DIR=./data/state
```

#### vector_search

**功能**：向量数据库搜索（包装 VectorMemoryService）

**接口**：
```python
await vector_search(
    query: str,                 # 搜索查询
    collection: str = "default",  # 集合名称
    top_k: int = 5,             # 返回结果数
    filter_metadata: Dict = None  # 元数据过滤
)
```

**返回格式**：
```json
{
  "success": true,
  "result": {
    "results": [
      {
        "id": "doc_id",
        "content": "文档内容",
        "score": 0.95,
        "metadata": {}
      }
    ]
  }
}
```

### 2. Skills 框架扩展

#### 提示词型 Skills (Markdown)

新增 5 个提示词型 Skills，位于 `skills/prompts/`：

| Skill | 文件 | 功能 |
|-------|------|------|
| ResearchTopicSkill | `research_topic.md` | 深度研究方法论 |
| SelectSlideLayoutSkill | `select_layout.md` | 幻灯片布局选择决策树 |
| QualityCheckSkill | `quality_check.md` | 内容质量评估框架 |
| SynthesizeInfoSkill | `synthesize_info.md` | 信息综合技巧 |
| OptimizeContentSkill | `optimize_content.md` | 内容优化最佳实践 |

**使用方式**：
```python
from backend.agents.tools.skills.managers.skill_manager import SkillManager

skill_manager = SkillManager()

# 获取描述性 Skills 内容（用于系统提示）
content = skill_manager.get_descriptive_content_for_prompt(
    skill_ids=["research_topic", "quality_check"]
)

# 注入到 Agent 提示中
system_prompt = f"你是一个研究助手。\n\n{content}"
```

#### 函数型 Skills (Python)

新增 4 个函数型 Skills，位于 `skills/functions/`：

| Skill | 文件 | 功能 |
|-------|------|------|
| ResearchTopicSkill | `research_skill.py` | 执行深度研究流程 |
| SelectSlideLayoutSkill | `layout_skill.py` | 选择合适的幻灯片布局 |
| TaskSchedulerSkill | `scheduler_skill.py` | DAG 任务调度 |
| RetryWithBackoffSkill | `retry_skill.py` | 带指数退避的重试逻辑 |

**使用方式**：
```python
from backend.agents.tools.skills.functions import ResearchTopicSkill

skill = ResearchTopicSkill()
result = await skill.execute(
    topic="量子计算",
    depth=3,
    max_sources=10
)
```

### 3. 统一响应格式

所有 MCP 工具现在返回统一的 JSON 格式：

**成功响应**：
```json
{
  "success": true,
  "result": {
    // 工具特定的数据
  },
  "error": null,
  "tool": "tool_name",
  "timestamp": "2025-02-03T10:30:00Z"
}
```

**错误响应**：
```json
{
  "success": false,
  "result": null,
  "error": {
    "message": "错误描述",
    "details": {},
    "code": "ERROR_CODE"
  },
  "tool": "tool_name",
  "timestamp": "2025-02-03T10:30:00Z"
}
```

### 4. 统一注册表增强

**之前**：
```python
# 只能注册旧式工具
from backend.agents.tools.registry.unified_registry import register_tool

register_tool(
    name="MyTool",
    category=ToolCategory.UTILITY,
    description="My tool",
    tool_func=my_function
)
```

**现在**：
```python
# 自动注册所有 MCP 工具
from backend.agents.tools.registry.unified_registry import get_unified_registry

registry = get_unified_registry()

# 获取所有工具（包括 MCP）
all_tools = registry.get_all_tools()

# 获取特定类别的工具
search_tools = registry.get_tools_by_category(ToolCategory.SEARCH)

# 获取 ADK 工具（用于 Agent）
adk_tools = registry.get_adk_tools(categories=["SEARCH", "MEDIA"])
```

**自动注册的 MCP 工具**：
- `web_search` - 网络搜索
- `fetch_url` - 网页抓取
- `search_images` - 图片搜索
- `create_pptx` - PPT 生成
- `state_store` - 状态存储
- `vector_search` - 向量搜索

---

## 废弃功能

### 1. 旧式工具标记为 DEPRECATED

#### DocumentSearch (search/document_search.py)

**废弃警告**：
```python
⚠️ DEPRECATED: This tool is deprecated and will be removed in a future version.
Please use the new MCP tools instead:
  - Use 'web_search' for web search functionality
  - Use 'vector_search' for semantic search in knowledge base
```

**迁移方式**：
```python
# 旧方式 (已废弃)
from backend.agents.tools.search.document_search import DocumentSearch
result = await DocumentSearch(keyword="AI", number=5)

# 新方式 (推荐)
from backend.agents.tools.mcp import web_search, vector_search

# 用于网络搜索
result = await web_search(query="AI", num_results=5)

# 用于语义搜索
result = await vector_search(query="AI", top_k=5)
```

#### SearchImage (media/image_search.py)

**废弃警告**：
```python
⚠️ DEPRECATED: This tool is deprecated and will be removed in a future version.
Please use the new MCP 'search_images' tool instead.
```

**迁移方式**：
```python
# 旧方式 (已废弃)
from backend.agents.tools.media.image_search import SearchImage
result = await SearchImage(query="flowers")

# 新方式 (推荐)
from backend.agents.tools.mcp import search_images
result = await search_images(
    query="flowers",
    num_results=5,
    source="unsplash"
)
```

### 2. 变化总结

| 旧工具 | 状态 | 替代方案 |
|--------|------|----------|
| `DocumentSearch` | DEPRECATED | `web_search` 或 `vector_search` |
| `SearchImage` | DEPRECATED | `search_images` |

**注意**：
- 旧工具仍然可用，但默认被禁用
- 使用旧工具时会触发 `DeprecationWarning`
- 建议尽快迁移到新工具
- 旧工具将在未来版本中被移除

---

## 迁移指南

### Agent 开发者

#### 更新工具导入

**之前**：
```python
from backend.agents.tools.search.document_search import DocumentSearch
from backend.agents.tools.media.image_search import SearchImage

tools = [DocumentSearch, SearchImage]
```

**现在**：
```python
from backend.agents.tools.registry.unified_registry import get_unified_registry

registry = get_unified_registry()

# 方式1: 获取所有已启用的工具
tools = registry.get_adk_tools()

# 方式2: 获取特定类别的工具
tools = registry.get_adk_tools(categories=["SEARCH", "MEDIA"])

# 方式3: 直接导入 MCP 工具
from backend.agents.tools.mcp import web_search, fetch_url, search_images

tools = [web_search, fetch_url, search_images]
```

#### 更新工具调用

**之前**：
```python
result = await DocumentSearch(keyword="AI", number=5)
```

**现在**：
```python
from backend.agents.tools.mcp import web_search
import json

result_json = await web_search(query="AI", num_results=5)
result = json.loads(result_json)

if result["success"]:
    for item in result["result"]["results"]:
        print(item["title"], item["url"])
```

### 配置迁移

#### 新增环境变量

创建 `.env` 文件（如果不存在）：

```bash
# MCP 工具配置
BING_SEARCH_API_KEY=your_bing_search_api_key_here
UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here
PEXELS_API_KEY=your_pexels_api_key_here

# Redis (可选)
REDIS_URL=redis://localhost:6379/0

# 缓存配置
MCP_CACHE_DIR=./data/mcp_cache
MCP_CACHE_ENABLED=true
MCP_CACHE_TTL=3600

# 状态存储
MCP_STATE_DIR=./data/state
MCP_STATE_NAMESPACE=default
```

#### 复制环境变量模板

```bash
cp .env.example .env
# 编辑 .env 填入你的 API 密钥
```

---

## 文件变更清单

### 新增文件 (20个)

**MCP 工具 (7个)**：
- ✅ `backend/agents/tools/mcp/base_mcp_tool.py`
- ✅ `backend/agents/tools/mcp/web_search.py`
- ✅ `backend/agents/tools/mcp/fetch_url.py`
- ✅ `backend/agents/tools/mcp/search_images.py`
- ✅ `backend/agents/tools/mcp/create_pptx.py`
- ✅ `backend/agents/tools/mcp/state_store.py`
- ✅ `backend/agents/tools/mcp/vector_search.py`

**Skills - 提示词型 (6个)**：
- ✅ `backend/agents/tools/skills/prompts/README.md`
- ✅ `backend/agents/tools/skills/prompts/research_topic.md`
- ✅ `backend/agents/tools/skills/prompts/select_layout.md`
- ✅ `backend/agents/tools/skills/prompts/quality_check.md`
- ✅ `backend/agents/tools/skills/prompts/synthesize_info.md`
- ✅ `backend/agents/tools/skills/prompts/optimize_content.md`

**Skills - 函数型 (5个)**：
- ✅ `backend/agents/tools/skills/functions/__init__.py`
- ✅ `backend/agents/tools/skills/functions/research_skill.py`
- ✅ `backend/agents/tools/skills/functions/layout_skill.py`
- ✅ `backend/agents/tools/skills/functions/scheduler_skill.py`
- ✅ `backend/agents/tools/skills/functions/retry_skill.py`

**测试 (2个)**：
- ✅ `backend/agents/tools/tests/test_mcp_tools.py`
- ✅ `backend/agents/tools/tests/test_skills.py`
- ✅ `backend/agents/tools/tests/__init__.py`

### 修改文件 (8个)

| 文件 | 修改类型 | 修改内容 |
|------|----------|----------|
| `mcp/__init__.py` | MODIFIED | 导出所有 MCP 工具 |
| `skills/__init__.py` | MODIFIED | 导出函数型 Skills |
| `registry/unified_registry.py` | MODIFIED | 注册 MCP 工具，禁用旧工具 |
| `skills/skill_loaders.py` | EXISTING | 已支持 md 和 py 加载 |
| `search/document_search.py` | MODIFIED | 添加废弃警告 |
| `media/image_search.py` | MODIFIED | 添加废弃警告 |
| `requirements.txt` | MODIFIED | 添加新依赖 |
| `tools/README.md` | NEW | 工具系统文档 |

### 配置文件 (1个)

- ✅ `.env.example` - 环境变量模板

---

## 配置变化

### 1. 新增依赖

**requirements.txt** 新增：
```txt
# MCP Tools Dependencies
readability-lxml>=0.8.1      # Web content extraction
html2text>=2020.1.16          # HTML to text conversion
python-pptx>=0.6.21           # PowerPoint generation
lxml>=4.9.0                   # XML processing
```

### 2. 环境变量

**必需的环境变量**（用于核心功能）：
```bash
# 无 - 所有工具都有后备方案
```

**可选的环境变量**（增强功能）：
```bash
# 搜索功能
BING_SEARCH_API_KEY=...       # web_search 需要

# 图片搜索
UNSPLASH_ACCESS_KEY=...       # search_images (Unsplash)
PEXELS_API_KEY=...            # search_images (Pexels)

# 缓存
MCP_CACHE_ENABLED=true        # 启用缓存
MCP_CACHE_TTL=3600           # 缓存TTL（秒）

# 状态存储
REDIS_URL=redis://...         # Redis（可选，默认使用文件）
```

### 3. 目录创建

运行时自动创建的目录：
```bash
./data/mcp_cache/    # fetch_url 缓存
./data/state/        # state_store 文件存储
```

---

## 依赖变化

### 新增 Python 包

| 包名 | 版本 | 用途 |
|------|------|------|
| readability-lxml | >=0.8.1 | 网页主要内容提取 |
| html2text | >=2020.1.16 | HTML 转纯文本 |
| python-pptx | >=0.6.21 | PowerPoint 生成 |
| lxml | >=4.9.0 | XML/HTML 处理 |

### 已有包（无需安装）

- `httpx` - HTTP 客户端
- `BeautifulSoup4` - HTML 解析
- `redis` - Redis 客户端

### 安装命令

```bash
# 安装所有依赖
pip install -r backend/requirements.txt

# 或只安装新依赖
pip install readability-lxml html2text python-pptx lxml
```

---

## 使用示例

### 示例1: 网络研究

```python
import json
from backend.agents.tools.mcp import web_search, fetch_url

# 1. 搜索
search_result = await web_search(
    query="人工智能最新进展",
    num_results=5,
    time_range="month"
)
search_data = json.loads(search_result)

# 2. 提取关键页面内容
if search_data["success"]:
    urls = [item["url"] for item in search_data["result"]["results"][:3]]

    for url in urls:
        content = await fetch_url(url=url, extract_type="main_content")
        content_data = json.loads(content)

        if content_data["success"]:
            print(f"Title: {content_data['result']['title']}")
            print(f"Content: {content_data['result']['text_content'][:200]}...")
```

### 示例2: PPT 生成

```python
import json
from backend.agents.tools.mcp import create_pptx, search_images

# 1. 搜索图片
images = await search_images(
    query="business meeting",
    num_results=3,
    orientation="landscape"
)
images_data = json.loads(images)

# 2. 生成 PPT
slides = [
    {
        "layout": "Title",
        "title": "商业智能分析"
    },
    {
        "layout": "Title and Content",
        "title": "市场趋势",
        "content": [
            "2025年市场增长30%",
            "用户满意度提升",
            "新客户获取成本降低"
        ],
        "images": [item["url"] for item in images_data["result"]["images"][:1]]
    }
]

result = await create_pptx(
    slides=slides,
    output_path="./output.pptx"
)
```

### 示例3: 使用 Skills

```python
from backend.agents.tools.skills.functions import ResearchTopicSkill

# 创建研究 Skill
skill = ResearchTopicSkill()

# 执行深度研究
result = await skill.execute(
    topic="量子计算在金融领域的应用",
    depth=3,
    max_sources=10
)

result_data = json.loads(result)
if result_data["success"]:
    print(f"研究主题: {result_data['result']['topic']}")
    print(f"发现数量: {result_data['result']['total_sources']}")
```

### 示例4: 统一注册表使用

```python
from backend.agents.tools.registry.unified_registry import get_unified_registry

# 获取注册表
registry = get_unified_registry()

# 查看统计信息
stats = registry.get_stats()
print(f"总工具数: {stats['total_tools']}")
print(f"总Skills数: {stats['total_skills']}")

# 获取搜索类工具
search_tools = registry.get_tools_by_category(ToolCategory.SEARCH)
for tool in search_tools:
    print(f"  - {tool.metadata.name}: {tool.metadata.description}")

# 获取 ADK 工具（用于 Agent）
adk_tools = registry.get_adk_tools(categories=["SEARCH", "MEDIA"])
print(f"可用于Agent的工具数: {len(adk_tools)}")
```

---

## 测试

### 运行测试

```bash
# 测试 MCP 工具
pytest backend/agents/tools/tests/test_mcp_tools.py -v

# 测试 Skills
pytest backend/agents/tools/tests/test_skills.py -v

# 测试所有
pytest backend/agents/tools/tests/ -v
```

### 测试覆盖

**MCP 工具测试** (`test_mcp_tools.py`):
- ✅ web_search - API密钥缺失、无效搜索引擎
- ✅ fetch_url - 无效URL、超时
- ✅ search_images - API密钥缺失、无效来源
- ✅ create_pptx - 基本PPT生成、带图片
- ✅ state_store - set/get/delete/list操作
- ✅ vector_search - 服务不可用场景

**Skills 测试** (`test_skills.py`):
- ✅ 提示词 Skills - 文件存在性、frontmatter验证
- ✅ 函数 Skills - 执行、参数验证
- ✅ 装饰器 - @Skill 功能
- ✅ 加载器 - CompositeSkillLoader

---

## 向后兼容性

### 兼容性策略

1. **保留旧代码**：所有旧工具仍然存在
2. **添加警告**：使用旧工具时会显示 `DeprecationWarning`
3. **默认禁用**：旧工具在注册表中默认被禁用
4. **渐进迁移**：可以逐步迁移到新工具

### 启用旧工具

如果需要临时启用旧工具：

```python
from backend.agents.tools.registry.unified_registry import get_unified_registry

registry = get_unified_registry()

# 启用旧工具
registry.enable_tool("DocumentSearch")
registry.enable_tool("SearchImage")
```

---

## 常见问题

### Q1: 如何获取 API 密钥？

**Bing Search API**：
1. 访问 [Microsoft Cognitive Services](https://www.microsoft.com/cognitive-services/en-us/sign-up)
2. 注册 Bing Search v7
3. 获取 API 密钥

**Unsplash API**：
1. 访问 [Unsplash Developers](https://unsplash.com/developers)
2. 创建应用
3. 获取 Access Key

**Pexels API**：
1. 访问 [Pexels API](https://www.pexels.com/api/)
2. 申请 API 密钥

### Q2: MCP 工具与旧工具的区别？

| 特性 | 旧工具 | MCP 工具 |
|------|--------|----------|
| 标准化 | ❌ 接口不一致 | ✅ 统一 JSON 响应 |
| 错误处理 | ❌ 不完善 | ✅ 标准错误格式 |
| 缓存 | ❌ 无 | ✅ 内置缓存 |
| 文档 | ❌ 缺少 | ✅ 详细文档 |
| 测试 | ❌ 无 | ✅ 完整测试 |

### Q3: Skills 什么时候用提示词型vs函数型？

**提示词型 (Markdown)** - 适用于：
- 知识和方法论
- 决策框架
- 最佳实践指南
- 不需要执行的描述性内容

**函数型 (Python)** - 适用于：
- 需要实际执行的任务
- 需要调用其他工具
- 复杂的流程控制
- 需要返回结构化数据

### Q4: 如何添加新的 MCP 工具？

1. 继承 `BaseMCPTool`
2. 实现 `execute()` 方法
3. 使用 `_success()` 或 `_error()` 返回结果
4. 在 `mcp/__init__.py` 中导出
5. 在 `unified_registry.py` 中注册

详见 [tools/README.md](../../backend/agents/tools/README.md)

---

## 相关文档

- [工具系统总览](./tools_overview.md)
- [工具架构](./tools_architecture.md)
- [工具开发指南](./tools_development.md)
- [外部工具设计指南](./external_tools_guide.md)
- [Prompt 设计指南](./prompt_design_guide.md)
- [Skills 框架文档](./skills_framework.md)
- [主 README](../../backend/agents/tools/README.md)

---

## 版本信息

- **重构日期**: 2025-02-03
- **版本**: v2.0.0
- **维护者**: MultiAgentPPT Team

---

**更新日志**:
- 2025-02-03: 初始版本，完成 MCP 工具和 Skills 重构
