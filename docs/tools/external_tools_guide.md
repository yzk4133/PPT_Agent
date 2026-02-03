# 外部工具设计指南：MCP + Skills

本文档详细说明 MultiAgentPPT 项目所需的外部工具，包括 MCP 协议工具和 Skills 封装工具。

---

## 目录

- [工具架构概览](#工具架构概览)
- [MCP 工具清单](#mcp-工具清单)
- [Skills 工具清单](#skills-工具清单)
- [工具实现规范](#工具实现规范)
- [工具集成指南](#工具集成指南)

---

## 工具架构概览

### 三层工具体系

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Layer                          │
│  (RequirementParser, ResearchAgent, ContentAgent, ...) │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   Tool Layer                            │
├───────────────────┬─────────────────────────────────────┤
│   MCP Tools       │         Skills                      │
│  (外部资源访问)    │      (流程封装)                     │
├───────────────────┼─────────────────────────────────────┤
│ • web_search      │ • ResearchTopicSkill                │
│ • fetch_url       │ • SelectSlideLayoutSkill            │
│ • search_images   │ • TaskSchedulerSkill                │
│ • create_pptx     │ • QualityCheckSkill                 │
│ • state_store     │ • RetryWithBackoffSkill             │
│ • vector_search   │ • GenerateChartSkill                │
└───────────────────┴─────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│               External Services                         │
│  (Search APIs, Image APIs, Database, File System, ...)  │
└─────────────────────────────────────────────────────────┘
```

### 设计原则

| 原则 | 说明 |
|-----|------|
| **最小化外部依赖** | 只在真正需要外部数据时才使用 MCP |
| **统一协议** | 所有外部工具通过 MCP 协议访问 |
| **可测试性** | 工具可独立测试，不依赖 Agent |
| **可复用性** | 工具设计为通用，可被多个 Agent 使用 |
| **错误处理** | 统一的错误处理和重试机制 |
| **性能优化** | 支持缓存、批量操作、并行执行 |

---

## MCP 工具清单

### MCP 工具分类

| 类别 | 工具 | 用途 | 优先级 |
|-----|------|------|--------|
| **搜索类** | `web_search` | 网络搜索 | ⭐⭐⭐ 必需 |
| **搜索类** | `vector_search` | 向量检索 | ✅ 已有 |
| **数据获取类** | `fetch_url` | 网页抓取 | ⭐⭐ 推荐 |
| **数据获取类** | `search_images` | 图片搜索 | ⭐⭐⭐ 必需 |
| **文件操作类** | `read_file` | 读取文件 | ⭐⭐⭐ 必需 |
| **文件操作类** | `write_file` | 写入文件 | ⭐⭐⭐ 必需 |
| **生成类** | `create_pptx` | 生成PPT | ⭐⭐⭐ 必需 |
| **生成类** | `generate_chart` | 生成图表 | ⭐⭐ 推荐 |
| **转换类** | `convert_format` | 格式转换 | ⭐⭐ 推荐 |
| **状态管理类** | `state_store` | 状态存储 | ⭐⭐⭐ 必需 |
| **状态管理类** | `checkpoint_save` | 检查点保存 | ⭐⭐⭐ 必需 |

---

### 1️⃣ web_search (网络搜索)

#### 功能描述
执行网络搜索，返回搜索结果列表。

#### 参数定义

```python
{
  "name": "web_search",
  "description": "执行网络搜索并返回结果",
  "parameters": {
    "query": {
      "type": "string",
      "description": "搜索关键词",
      "required": true
    },
    "num_results": {
      "type": "integer",
      "description": "返回结果数量(默认5, 最大10)",
      "default": 5,
      "range": [1, 10]
    },
    "search_engine": {
      "type": "string",
      "description": "搜索引擎",
      "enum": ["bing", "google", "duckduckgo"],
      "default": "bing"
    },
    "language": {
      "type": "string",
      "description": "搜索语言",
      "default": "zh-CN"
    },
    "time_range": {
      "type": "string",
      "description": "时间范围",
      "enum": ["any", "day", "week", "month", "year"],
      "default": "any"
    }
  }
}
```

#### 返回格式

```json
{
  "query": "搜索关键词",
  "total_results": 5,
  "results": [
    {
      "title": "结果标题",
      "url": "https://example.com",
      "snippet": "摘要描述...",
      "published_date": "2024-01-15",
      "source": "网站名称",
      "relevance_score": 0.95
    }
  ],
  "search_time_ms": 450,
  "search_engine": "bing"
}
```

#### 实现示例

```python
# backend/agents/tools/mcp/web_search.py

import httpx
from typing import Optional, List, Dict
from google.adk.tools import ToolContext

# 配置
BING_SEARCH_API_KEY = os.getenv("BING_SEARCH_API_KEY")
BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"

async def web_search(
    query: str,
    num_results: int = 5,
    search_engine: str = "bing",
    language: str = "zh-CN",
    time_range: str = "any",
    tool_context: ToolContext = None
) -> str:
    """
    执行网络搜索

    Args:
        query: 搜索关键词
        num_results: 返回结果数量
        search_engine: 搜索引擎
        language: 搜索语言
        tool_context: 工具上下文

    Returns:
        JSON 格式的搜索结果
    """
    agent_name = tool_context.agent_name if tool_context else "unknown"
    print(f"[{agent_name}] 执行网络搜索: {query}")

    try:
        if search_engine == "bing":
            results = await _search_bing(query, num_results, language)
        elif search_engine == "google":
            results = await _search_google(query, num_results, language)
        else:
            raise ValueError(f"不支持的搜索引擎: {search_engine}")

        # 格式化返回
        formatted_results = {
            "query": query,
            "total_results": len(results),
            "results": results,
            "search_engine": search_engine
        }

        return json.dumps(formatted_results, ensure_ascii=False)

    except Exception as e:
        error_result = {
            "query": query,
            "error": str(e),
            "results": []
        }
        return json.dumps(error_result, ensure_ascii=False)


async def _search_bing(
    query: str,
    num_results: int,
    language: str
) -> List[Dict]:
    """使用 Bing Search API"""
    headers = {"Ocp-Apim-Subscription-Key": BING_SEARCH_API_KEY}

    params = {
        "q": query,
        "count": num_results,
        "mkt": language,
        "safeSearch": "Moderate"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            BING_ENDPOINT,
            headers=headers,
            params=params,
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()

    # 解析结果
    results = []
    for item in data.get("webPages", {}).get("value", []):
        results.append({
            "title": item.get("name"),
            "url": item.get("url"),
            "snippet": item.get("snippet"),
            "display_url": item.get("displayUrl"),
            "date": item.get("date"),
            "relevance_score": 0.8  # Bing 不提供分数，给默认值
        })

    return results


async def _search_google(
    query: str,
    num_results: int,
    language: str
) -> List[Dict]:
    """使用 Google Custom Search API"""
    # TODO: 实现 Google 搜索
    pass
```

#### API 选型

| 服务 | 免费配额 | 价格 | 推荐 |
|-----|---------|------|------|
| **Bing Search API** | 1000次/月 | 免费 | ✅ 推荐 |
| **Google Custom Search** | 100次/天 | $5/1000次 | 可选 |
| **SerpAPI** | 100次/月 | $50/月 | 生产环境 |

---

### 2️⃣ fetch_url (网页抓取)

#### 功能描述
获取指定 URL 的完整网页内容。

#### 参数定义

```python
{
  "name": "fetch_url",
  "description": "获取URL的完整内容",
  "parameters": {
    "url": {
      "type": "string",
      "description": "目标URL",
      "required": true
    },
    "timeout": {
      "type": "integer",
      "description": "超时时间(秒)",
      "default": 10,
      "range": [5, 30]
    },
    "extract_type": {
      "type": "string",
      "description": "提取内容类型",
      "enum": ["full", "main_content", "article", "text_only"],
      "default": "main_content"
    },
    "use_cache": {
      "type": "boolean",
      "description": "是否使用缓存",
      "default": true
    }
  }
}
```

#### 返回格式

```json
{
  "url": "https://example.com/article",
  "title": "文章标题",
  "content": "主要内容...",
  "text_content": "纯文本内容...",
  "author": "作者",
  "published_date": "2024-01-15",
  "word_count": 1500,
  "fetched_at": "2024-02-03T10:30:00Z",
  "from_cache": false
}
```

#### 实现示例

```python
# backend/agents/tools/mcp/fetch_url.py

import httpx
from bs4 import BeautifulSoup
from readability import Document
import html2text
from typing import Dict
from datetime import datetime

async def fetch_url(
    url: str,
    timeout: int = 10,
    extract_type: str = "main_content",
    use_cache: bool = True,
    tool_context: ToolContext = None
) -> str:
    """
    获取 URL 内容

    Args:
        url: 目标 URL
        timeout: 超时时间
        extract_type: 提取类型
        use_cache: 是否使用缓存
        tool_context: 工具上下文

    Returns:
        JSON 格式的页面内容
    """
    print(f"[fetch_url] 获取: {url}")

    # 检查缓存
    if use_cache:
        cached = await _get_from_cache(url)
        if cached:
            return cached

    try:
        # 获取页面
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            html = response.text

        # 提取内容
        result = await _extract_content(html, extract_type, url)

        # 存储缓存
        if use_cache:
            await _save_to_cache(url, result)

        return json.dumps(result, ensure_ascii=False, default=str)

    except Exception as e:
        return json.dumps({
            "url": url,
            "error": str(e),
            "content": None
        })


async def _extract_content(
    html: str,
    extract_type: str,
    url: str
) -> Dict:
    """提取页面内容"""
    soup = BeautifulSoup(html, 'html.parser')

    result = {
        "url": url,
        "title": soup.title.string if soup.title else "",
        "fetched_at": datetime.now().isoformat()
    }

    if extract_type == "full":
        result["content"] = html
        result["text_content"] = soup.get_text()

    elif extract_type == "main_content":
        # 使用 readability 提取主要内容
        doc = Document(html)
        result["content"] = doc.summary()
        result["text_content"] = html2text.html2text(doc.summary())

    elif extract_type == "text_only":
        h = html2text.HTML2Text()
        h.ignore_links = True
        result["text_content"] = h.handle(html)
        result["word_count"] = len(result["text_content"].split())

    return result
```

---

### 3️⃣ search_images (图片搜索)

#### 功能描述
根据关键词搜索图片。

#### 参数定义

```python
{
  "name": "search_images",
  "description": "搜索图片",
  "parameters": {
    "query": {
      "type": "string",
      "description": "搜索关键词",
      "required": true
    },
    "num_results": {
      "type": "integer",
      "description": "返回数量",
      "default": 5,
      "range": [1, 10]
    },
    "orientation": {
      "type": "string",
      "description": "图片方向",
      "enum": ["landscape", "portrait", "square"],
      "default": "landscape"
    },
    "size": {
      "type": "string",
      "description": "图片尺寸",
      "enum": ["small", "medium", "large", "original"],
      "default": "large"
    },
    "color": {
      "type": "string",
      "description": "主色调",
      "enum": ["any", "black_white", "black", "white", "yellow", "orange", "red", "purple", "green", "blue"],
      "default": "any"
    }
  }
}
```

#### 返回格式

```json
{
  "query": "business meeting",
  "total_results": 5,
  "images": [
    {
      "url": "https://images.unsplash.com/photo-xxx",
      "thumbnail": "https://images.unsplash.com/photo-xxx?w=200",
      "description": "Business professionals in a meeting",
      "photographer": "John Doe",
      "width": 1920,
      "height": 1080,
      "source": "unsplash"
    }
  ]
}
```

#### 实现示例

```python
# backend/agents/tools/mcp/search_images.py

import httpx
import os

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
UNSPLASH_API = "https://api.unsplash.com/search/photos"

async def search_images(
    query: str,
    num_results: int = 5,
    orientation: str = "landscape",
    size: str = "large",
    color: str = "any",
    tool_context: ToolContext = None
) -> str:
    """
    搜索图片

    Args:
        query: 搜索关键词
        num_results: 返回数量
        orientation: 图片方向
        size: 图片尺寸
        tool_context: 工具上下文

    Returns:
        JSON 格式的图片列表
    """
    print(f"[search_images] 搜索: {query}")

    try:
        params = {
            "query": query,
            "per_page": num_results,
            "orientation": orientation,
            "color": color if color != "any" else None
        }

        headers = {
            "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                UNSPLASH_API,
                headers=headers,
                params={k: v for k, v in params.items() if v}
            )
            response.raise_for_status()
            data = response.json()

        # 解析结果
        images = []
        for photo in data.get("results", []):
            images.append({
                "url": photo["urls"][size],
                "thumbnail": photo["urls"]["thumb"],
                "description": photo.get("description") or photo.get("alt_description"),
                "photographer": photo["user"]["name"],
                "width": photo["width"],
                "height": photo["height"],
                "source": "unsplash"
            })

        result = {
            "query": query,
            "total_results": len(images),
            "images": images
        }

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "query": query,
            "error": str(e),
            "images": []
        })
```

---

### 4️⃣ create_pptx (生成 PPT)

#### 功能描述
根据结构化数据生成 PPT 文件。

#### 参数定义

```python
{
  "name": "create_pptx",
  "description": "生成PPT文件",
  "parameters": {
    "slides": {
      "type": "array",
      "description": "幻灯片数据",
      "required": true,
      "items": {
        "type": "object",
        "properties": {
          "layout": {"type": "string"},
          "title": {"type": "string"},
          "subtitle": {"type": "string"},
          "content": {"type": "array"},
          "images": {"type": "array"},
          "notes": {"type": "string"}
        }
      }
    },
    "template_path": {
      "type": "string",
      "description": "模板文件路径"
    },
    "output_path": {
      "type": "string",
      "description": "输出文件路径",
      "required": true
    },
    "theme": {
      "type": "object",
      "description": "主题配置"
    }
  }
}
```

#### 返回格式

```json
{
  "success": true,
  "output_path": "/path/to/output.pptx",
  "total_slides": 10,
  "file_size_mb": 2.5,
  "created_at": "2024-02-03T10:30:00Z"
}
```

#### 实现示例

```python
# backend/agents/tools/mcp/create_pptx.py

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from typing import List, Dict
import os

async def create_pptx(
    slides: List[Dict],
    output_path: str,
    template_path: str = None,
    theme: Dict = None,
    tool_context: ToolContext = None
) -> str:
    """
    生成 PPT 文件

    Args:
        slides: 幻灯片数据
        output_path: 输出路径
        template_path: 模板路径
        theme: 主题配置
        tool_context: 工具上下文

    Returns:
        JSON 格式的结果
    """
    print(f"[create_pptx] 生成PPT: {len(slides)}页")

    try:
        # 加载模板或创建新演示
        if template_path and os.path.exists(template_path):
            prs = Presentation(template_path)
        else:
            prs = Presentation()
            # 应用主题
            if theme:
                _apply_theme(prs, theme)

        # 添加幻灯片
        for slide_data in slides:
            _add_slide(prs, slide_data)

        # 保存
        prs.save(output_path)

        # 返回结果
        file_size = os.path.getsize(output_path) / (1024 * 1024)

        result = {
            "success": True,
            "output_path": output_path,
            "total_slides": len(slides),
            "file_size_mb": round(file_size, 2),
            "created_at": datetime.now().isoformat()
        }

        return json.dumps(result, ensure_ascii=False, default=str)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "output_path": output_path
        })


def _add_slide(prs: Presentation, slide_data: Dict):
    """添加单个幻灯片"""
    layout = _get_layout(prs, slide_data.get("layout", "Title and Content"))
    slide = prs.slides.add_slide(layout)

    # 设置标题
    if slide.shapes.title:
        slide.shapes.title.text = slide_data.get("title", "")

    # 设置内容
    if "content" in slide_data and slide_data["content"]:
        for idx, point in enumerate(slide_data["content"]):
            text_box = slide.placeholders[1].text_frame
            if idx == 0:
                text_box.text = point
            else:
                text_box.add_paragraph().text = point

    # 插入图片
    if "images" in slide_data:
        for img_url in slide_data["images"]:
            _insert_image(slide, img_url)

    # 添加备注
    if "notes" in slide_data:
        slide.notes_slide.notes_text_frame.text = slide_data["notes"]


def _get_layout(prs: Presentation, layout_name: str):
    """获取布局"""
    layout_map = {
        "Title": 0,
        "Title and Content": 1,
        "Section Header": 2,
        "Two Content": 3,
        "Comparison": 4,
        "Title Only": 5,
        "Blank": 6
    }
    idx = layout_map.get(layout_name, 1)
    return prs.slide_layouts[idx]


def _insert_image(slide, image_url: str):
    """插入图片（从URL）"""
    # TODO: 下载图片并插入
    pass
```

---

### 5️⃣ state_store (状态存储)

#### 功能描述
存储和检索 Agent 执行状态。

#### 参数定义

```python
{
  "name": "state_store",
  "description": "存储/获取状态",
  "parameters": {
    "operation": {
      "type": "string",
      "enum": ["get", "set", "delete", "list"],
      "required": true
    },
    "key": {
      "type": "string",
      "description": "状态键"
    },
    "value": {
      "type": "any",
      "description": "状态值(set操作时需要)"
    },
    "namespace": {
      "type": "string",
      "description": "命名空间",
      "default": "default"
    }
  }
}
```

#### 实现示例

```python
# backend/agents/tools/mcp/state_store.py

import redis
import json
import os

# 使用 Redis 或文件系统
REDIS_URL = os.getenv("REDIS_URL")

class StateStore:
    def __init__(self):
        if REDIS_URL:
            self.client = redis.from_url(REDIS_URL)
            self.backend = "redis"
        else:
            self.backend = "file"
            self.base_path = "./data/state"

    async def execute(
        self,
        operation: str,
        key: str = None,
        value = None,
        namespace: str = "default"
    ) -> str:
        """执行状态操作"""
        if operation == "get":
            return await self._get(key, namespace)
        elif operation == "set":
            return await self._set(key, value, namespace)
        elif operation == "delete":
            return await self._delete(key, namespace)
        elif operation == "list":
            return await self._list(namespace)

    async def _get(self, key: str, namespace: str):
        if self.backend == "redis":
            data = self.client.get(f"{namespace}:{key}")
            return data.decode() if data else None
        else:
            path = f"{self.base_path}/{namespace}/{key}.json"
            if os.path.exists(path):
                with open(path) as f:
                    return f.read()
            return None

    async def _set(self, key: str, value, namespace: str):
        if self.backend == "redis":
            self.client.set(f"{namespace}:{key}", json.dumps(value))
        else:
            path = f"{self.base_path}/{namespace}"
            os.makedirs(path, exist_ok=True)
            with open(f"{path}/{key}.json", "w") as f:
                json.dump(value, f)
```

---

## Skills 工具清单

### Skills 分类

| 类别 | Skill | 功能 | 优先级 |
|-----|-------|------|--------|
| **研究类** | `ResearchTopicSkill` | 深度研究流程 | ⭐⭐⭐ 必需 |
| **研究类** | `SynthesizeInfoSkill` | 信息综合 | ⭐⭐ 推荐 |
| **布局类** | `SelectSlideLayoutSkill` | 布局选择 | ⭐⭐⭐ 必需 |
| **布局类** | `AnalyzeLayoutSkill` | 布局分析 | ⭐⭐ 推荐 |
| **内容类** | `OptimizeContentSkill` | 内容优化 | ⭐⭐ 推荐 |
| **质量类** | `QualityCheckSkill` | 质量检查 | ⭐⭐⭐ 必需 |
| **任务类** | `TaskSchedulerSkill` | 任务调度 | ⭐⭐⭐ 必需 |
| **任务类** | `RetryWithBackoffSkill` | 重试逻辑 | ⭐⭐⭐ 必需 |

---

### 1️⃣ ResearchTopicSkill (深度研究)

#### 功能描述
封装完整的研究流程：分解→搜索→抓取→综合。

#### 参数定义

```python
@skill(
    name="research_topic",
    description="对主题进行深度研究",
    parameters={
        "topic": {
            "type": "string",
            "description": "研究主题",
            "required": True
        },
        "depth": {
            "type": "integer",
            "description": "研究深度(1-5)",
            "default": 3
        },
        "max_sources": {
            "type": "integer",
            "description": "最大来源数",
            "default": 10
        }
    }
)
```

#### 实现示例

```python
# backend/agents/tools/skills/research_skill.py

from backend.agents.tools.skills.skill_decorator import skill
import asyncio

@skill(
    name="research_topic",
    description="对主题进行深度研究"
)
async def research_topic(
    topic: str,
    depth: int = 3,
    max_sources: int = 10,
    tool_context: ToolContext = None
) -> str:
    """
    深度研究流程

    Args:
        topic: 研究主题
        depth: 研究深度(1=快速, 3=标准, 5=深度)
        max_sources: 最大来源数
        tool_context: 工具上下文

    Returns:
        研究报告(JSON)
    """
    print(f"[ResearchTopicSkill] 开始研究: {topic}")

    # 步骤1: 分解主题（使用 LLM）
    subtopics = await _decompose_topic(topic, depth)
    print(f"  → 分解为 {len(subtopics)} 个子主题")

    # 步骤2: 并行搜索（调用 MCP web_search）
    search_tasks = [
        _call_mcp_tool("web_search", {
            "query": subtopic,
            "num_results": max_sources // len(subtopics)
        })
        for subtopic in subtopics
    ]
    search_results = await asyncio.gather(*search_tasks)
    print(f"  → 获得 {len(search_results)} 组搜索结果")

    # 步骤3: 抓取关键网页（调用 MCP fetch_url）
    detailed_content = await _fetch_key_pages(search_results, max_sources)
    print(f"  → 抓取了 {len(detailed_content)} 个详细页面")

    # 步骤4: 提取和整合信息（使用 LLM）
    synthesized = await _synthesize_information(topic, detailed_content)
    print(f"  → 综合完成")

    # 步骤5: 生成研究报告（使用 LLM）
    report = await _generate_research_report(topic, synthesized)
    print(f"  → 研究完成")

    return report


async def _decompose_topic(topic: str, depth: int) -> List[str]:
    """分解主题为子主题"""
    prompt = f"""
    将以下主题分解为 {3 + depth} 个可研究的子主题：
    主题：{topic}

    返回JSON数组：["子主题1", "子主题2", ...]
    """
    # 调用 LLM
    result = await call_llm(prompt)
    return json.loads(result)


async def _fetch_key_pages(
    search_results: List[str],
    max_pages: int
) -> List[str]:
    """抓取关键网页"""
    all_urls = []
    for result_json in search_results:
        result = json.loads(result_json)
        all_urls.extend([item["url"] for item in result["results"]])

    # 选择最相关的 URL
    selected_urls = all_urls[:max_pages]

    # 并行抓取
    fetch_tasks = [
        _call_mcp_tool("fetch_url", {"url": url})
        for url in selected_urls
    ]
    fetched = await asyncio.gather(*fetch_tasks)

    return [f for f in fetched if f]


async def _synthesize_information(
    topic: str,
    contents: List[str]
) -> str:
    """综合信息"""
    # 使用 LLM 综合多个来源的信息
    prompt = f"""
    请综合以下信息，提取关于"{topic}"的关键发现：

    {chr(10).join(contents[:5])}

    返回结构化的综合信息。
    """
    return await call_llm(prompt)
```

---

### 2️⃣ SelectSlideLayoutSkill (布局选择)

#### 功能描述
根据内容类型选择合适的幻灯片布局。

#### 实现示例

```python
# backend/agents/tools/skills/layout_skill.py

@skill(
    name="select_slide_layout",
    description="根据内容选择合适的幻灯片布局"
)
async def select_slide_layout(
    content_type: str,
    has_image: bool = False,
    has_chart: bool = False,
    bullet_count: int = 3,
    tool_context: ToolContext = None
) -> str:
    """
    选择幻灯片布局

    Args:
        content_type: 内容类型
        has_image: 是否有图片
        has_chart: 是否有图表
        bullet_count: 要点数量
        tool_context: 工具上下文

    Returns:
        布局类型名称
    """
    # 布局映射
    LAYOUT_DECISION_TREE = {
        "title_page": "Title",
        "toc": "Title and Content",
        "section": "Section Header",
    }

    # 决策逻辑
    if content_type == "title_page":
        return "Title"

    elif content_type == "section":
        return "Section Header"

    elif content_type == "toc":
        return "Title and Content"

    elif has_chart and has_image:
        return "Two Content"  # 图表在左，图片在右

    elif has_chart:
        return "Title and Content"

    elif has_image:
        if bullet_count > 3:
            return "Two Content"  # 文字在左，图片在右
        else:
            return "Title and Content"

    elif content_type == "comparison":
        return "Comparison"

    else:  # 纯文字
        if bullet_count > 5:
            return "Two Content"  # 分两列
        else:
            return "Title and Content"
```

---

### 3️⃣ TaskSchedulerSkill (任务调度)

#### 功能描述
DAG 任务调度和执行。

#### 实现示例

```python
# backend/agents/tools/skills/scheduler_skill.py

@skill(
    name="schedule_tasks",
    description="调度和执行DAG任务"
)
async def schedule_tasks(
    tasks: List[Dict],
    max_parallel: int = 3,
    tool_context: ToolContext = None
) -> str:
    """
    调度任务

    Args:
        tasks: 任务列表，包含依赖关系
        max_parallel: 最大并行数
        tool_context: 工具上下文

    Returns:
        执行结果
    """
    # 构建 DAG
    dag = _build_dag(tasks)

    # 拓扑排序
    execution_order = _topological_sort(dag)

    # 执行
    results = {}
    for level in execution_order:
        # 并行执行当前层的任务
        level_tasks = [
            _execute_task(task_id, dag[task_id])
            for task_id in level
        ]
        level_results = await asyncio.gather(*level_tasks, return_exceptions=True)

        # 更新结果
        for task_id, result in zip(level, level_results):
            results[task_id] = {
                "success": not isinstance(result, Exception),
                "result": result if not isinstance(result, Exception) else str(result)
            }

    return json.dumps(results)


def _build_dag(tasks: List[Dict]) -> Dict:
    """构建 DAG"""
    dag = {}
    for task in tasks:
        dag[task["id"]] = {
            "func": task["function"],
            "params": task.get("params", {}),
            "dependencies": task.get("depends_on", [])
        }
    return dag


def _topological_sort(dag: Dict) -> List[List[str]]:
    """拓扑排序，返回分层执行顺序"""
    # Kahn's algorithm
    in_degree = {task_id: len(deps) for task_id, deps in dag.items()}
    queue = [task_id for task_id, degree in in_degree.items() if degree == 0]

    levels = []
    while queue:
        current_level = queue
        queue = []
        for task_id in current_level:
            for other_task_id, task_data in dag.items():
                if task_id in task_data["dependencies"]:
                    in_degree[other_task_id] -= 1
                    if in_degree[other_task_id] == 0:
                        queue.append(other_task_id)
        levels.append(current_level)

    return levels
```

---

### 4️⃣ QualityCheckSkill (质量检查)

#### 实现示例

```python
# backend/agents/tools/skills/quality_skill.py

@skill(
    name="quality_check",
    description="检查PPT内容质量"
)
async def quality_check(
    ppt_content: str,
    requirements: Dict = None,
    check_dimensions: List[str] = None,
    tool_context: ToolContext = None
) -> str:
    """
    质量检查

    Args:
        ppt_content: PPT内容
        requirements: 原始需求
        check_dimensions: 检查维度
        tool_context: 工具上下文

    Returns:
        质量报告
    """
    # 使用 LLM 进行质量检查
    check_prompt = f"""
    请检查以下PPT内容的质量：

    {ppt_content}

    检查维度：{check_dimensions or ["completeness", "logic", "expression"]}

    返回JSON格式的质量报告。
    """

    report = await call_llm(check_prompt)

    # 保存检查结果
    await _call_mcp_tool("state_store", {
        "operation": "set",
        "key": f"quality_check_{datetime.now().isoformat()}",
        "value": report
    })

    return report
```

---

### 5️⃣ RetryWithBackoffSkill (重试逻辑)

#### 实现示例

```python
# backend/agents/tools/skills/retry_skill.py

@skill(
    name="retry_with_backoff",
    description="带指数退避的重试逻辑"
)
async def retry_with_backoff(
    func: callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    tool_context: ToolContext = None
):
    """
    执行并重试

    Args:
        func: 要执行的函数
        max_retries: 最大重试次数
        base_delay: 基础延迟(秒)
        tool_context: 工具上下文
    """
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # 最后一次重试失败，抛出异常

            # 计算延迟
            delay = min(base_delay * (2 ** attempt), max_delay)
            print(f"  ⚠️ 失败，{delay}秒后重试... (尝试 {attempt + 1}/{max_retries})")

            await asyncio.sleep(delay)
```

---

## 工具实现规范

### 命名规范

```python
# MCP 工具命名：动词_名词
web_search
fetch_url
search_images
create_pptx

# Skill 命名：名词 + Skill
ResearchTopicSkill
SelectSlideLayoutSkill
QualityCheckSkill
```

### 错误处理规范

```python
# 统一的错误返回格式
{
  "success": False,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {...}
  },
  "result": None
}
```

### 日志规范

```python
# 使用统一的日志格式
import logging

logger = logging.getLogger(__name__)

logger.info(f"[{tool_name}] 开始执行: {params}")
logger.debug(f"[{tool_name}] 执行详情: {...}")
logger.warning(f"[{tool_name}] 警告: {...}")
logger.error(f"[{tool_name}] 错误: {...}", exc_info=True)
```

---

## 工具集成指南

### 1. 在 Agent 中使用 MCP 工具

```python
class MyAgent:
    async def execute(self, context):
        # 调用 MCP 工具
        search_results = await self.call_mcp_tool(
            "web_search",
            {"query": "人工智能", "num_results": 5}
        )

        # 解析结果
        results = json.loads(search_results)

        # 使用结果
        for item in results["results"]:
            print(item["title"])
```

### 2. 在 Agent 中使用 Skill

```python
from backend.agents.tools.skills.skill_manager import SkillManager

class MyAgent:
    def __init__(self):
        self.skill_manager = SkillManager()

    async def execute(self, context):
        # 调用 Skill
        report = await self.skill_manager.execute_skill(
            "research_topic",
            topic="人工智能",
            depth=3
        )

        return report
```

### 3. 工具链组合

```python
# 研究流程：MCP + Skill + Prompt
async def research_flow(topic: str):
    # 1. 使用 Skill 封装的研究流程
    research_result = await skill_manager.execute(
        "ResearchTopicSkill",
        topic=topic,
        depth=3
    )

    # 2. 使用 Prompt 提取关键信息
    key_info = await extract_key_info(research_result)

    # 3. 返回结果
    return key_info
```

---

## 实现优先级

### 第一阶段：核心 MCP 工具 (Week 1-2)

```
✅ vector_search       - 已有
🔨 web_search         - 网络搜索
🔨 fetch_url          - 网页抓取
🔨 search_images      - 图片搜索
🔨 create_pptx        - PPT生成
🔨 state_store        - 状态存储
```

### 第二阶段：核心 Skills (Week 3)

```
🔲 ResearchTopicSkill      - 研究流程
🔲 SelectSlideLayoutSkill  - 布局选择
🔲 TaskSchedulerSkill      - 任务调度
🔲 QualityCheckSkill       - 质量检查
```

### 第三阶段：增强功能 (Week 4)

```
🔲 generate_chart          - 图表生成
🔲 convert_format          - 格式转换
🔲 RetryWithBackoffSkill   - 重试逻辑
🔲 OptimizeContentSkill    - 内容优化
```

---

**文档版本：** v1.0
**最后更新：** 2025-02-03
**维护者：** MultiAgentPPT Team
