# 工具系统快速参考

> 新工具系统的快速上手指南

## 🚀 5分钟快速开始

### 1. 安装依赖

```bash
pip install -r backend/requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入 API 密钥（可选）
```

### 3. 使用 MCP 工具

```python
# 导入工具
from backend.agents.tools.mcp import web_search, search_images
import json

# 网络搜索
result = await web_search(query="人工智能", num_results=5)
data = json.loads(result)

# 图片搜索
images = await search_images(query="business", num_results=3)
```

---

## 📚 工具速查表

### MCP 工具

| 工具 | 功能 | 必需配置 |
|------|------|----------|
| `web_search` | 网络搜索 | `BING_SEARCH_API_KEY` |
| `fetch_url` | 网页抓取 | 无 |
| `search_images` | 图片搜索 | `UNSPLASH_ACCESS_KEY` |
| `create_pptx` | 生成PPT | 无 |
| `state_store` | 状态存储 | 无（或Redis） |
| `vector_search` | 向量搜索 | 无 |

### Skills

| 类型 | 位置 | 示例 |
|------|------|------|
| 提示词型 | `skills/prompts/*.md` | `research_topic.md` |
| 函数型 | `skills/functions/*.py` | `research_skill.py` |

---

## 💡 常用代码片段

### 网络研究流程

```python
from backend.agents.tools.mcp import web_search, fetch_url
import json

# 搜索
search_result = await web_search(query="AI", num_results=5)
search_data = json.loads(search_result)

# 获取第一个结果
if search_data["success"]:
    first_url = search_data["result"]["results"][0]["url"]

    # 抓取内容
    content = await fetch_url(url=first_url)
    content_data = json.loads(content)

    print(content_data["result"]["text_content"])
```

### 生成演示文稿

```python
from backend.agents.tools.mcp import create_pptx

slides = [
    {"layout": "Title", "title": "演示标题"},
    {"layout": "Title and Content", "title": "第一页", "content": ["要点1", "要点2"]}
]

result = await create_pptx(
    slides=slides,
    output_path="./presentation.pptx"
)
```

### 使用研究 Skill

```python
from backend.agents.tools.skills.functions import ResearchTopicSkill
import json

skill = ResearchTopicSkill()
result = await skill.execute(topic="量子计算", depth=3)

data = json.loads(result)
print(data["result"]["summary"])
```

### 使用统一注册表

```python
from backend.agents.tools.registry.unified_registry import get_unified_registry

registry = get_unified_registry()

# 查看所有工具
tools = registry.list_tools()
print(tools)

# 获取 ADK 工具
adk_tools = registry.get_adk_tools()
```

---

## ⚠️ 迁移对照表

### DocumentSearch → web_search

| 旧代码 | 新代码 |
|--------|--------|
| `DocumentSearch(keyword="AI", number=5)` | `web_search(query="AI", num_results=5)` |
| 返回字符串 | 返回 JSON（需要 `json.loads()`） |

### SearchImage → search_images

| 旧代码 | 新代码 |
|--------|--------|
| `SearchImage(query="flowers")` | `search_images(query="flowers", num_results=5)` |
| 返回 URL 字符串 | 返回 JSON（包含多个图片） |

---

## 🎯 工具选择指南

### 需要搜索信息？

| 需求 | 使用工具 |
|------|----------|
| 网络搜索 | `web_search` |
| 抓取网页内容 | `fetch_url` |
| 语义搜索知识库 | `vector_search` |
| 深度研究流程 | `ResearchTopicSkill` |

### 需要处理图片？

| 需求 | 使用工具 |
|------|----------|
| 搜索图片 | `search_images` |
| 选择幻灯片布局 | `SelectSlideLayoutSkill` |

### 需要生成内容？

| 需求 | 使用工具 |
|------|----------|
| 生成PPT | `create_pptx` |
| 优化内容 | `OptimizeContentSkill` (提示词) |
| 质量检查 | `QualityCheckSkill` (提示词) |

### 需要管理状态？

| 需求 | 使用工具 |
|------|----------|
| 存储临时数据 | `state_store` |
| 任务调度 | `TaskSchedulerSkill` |
| 重试逻辑 | `RetryWithBackoffSkill` |

---

## 🔧 配置速查

### 环境变量

```bash
# 搜索（必需用于 web_search）
BING_SEARCH_API_KEY=your_key

# 图片搜索（必需用于 search_images）
UNSPLASH_ACCESS_KEY=your_key

# Redis（可选，用于 state_store）
REDIS_URL=redis://localhost:6379/0

# 缓存（可选）
MCP_CACHE_ENABLED=true
MCP_CACHE_TTL=3600
```

### 目录结构

```
./data/
├── mcp_cache/    # fetch_url 缓存
└── state/        # state_store 文件存储
```

---

## 📖 更多文档

- [完整变更日志](./REFACTORING_CHANGELOG.md)
- [工具系统总览](./tools_overview.md)
- [工具开发指南](./tools_development.md)
- [主 README](../../backend/agents/tools/README.md)

---

## ❓ 常见问题

### Q: 工具返回什么格式？

A: 所有 MCP 工具返回 JSON 字符串：
```json
{
  "success": true/false,
  "result": {...},
  "error": {...}
}
```

### Q: 如何获取 API 密钥？

A: 参考 [REFACTORING_CHANGELOG.md](./REFACTORING_CHANGELOG.md) 的常见问题部分

### Q: 旧工具还能用吗？

A: 可以，但会显示警告。建议迁移到新工具。

---

**快速链接**:
- [变更日志](./REFACTORING_CHANGELOG.md) | [工具总览](./tools_overview.md) | [开发指南](./tools_development.md)
