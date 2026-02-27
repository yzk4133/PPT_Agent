# Domain Tools 参考文档

> **10 个外部工具的完整列表和详细说明**

Domain Tools 是直接实现为 LangChain Tools 的外部工具，提供搜索、媒体、实用和数据库功能。

---

## 📋 工具列表

### 1️⃣ 搜索类工具 (3个)

#### web_search

**基本信息**
- **工具名称**: `web_search`
- **实现文件**: `backend/tools/domain/search/web_search.py`
- **工具类别**: SEARCH
- **版本**: 1.0.0

**功能说明**
- 使用 Bing 搜索 API v7 进行网络搜索
- 支持中文和英文搜索
- 返回搜索结果的标题、摘要和 URL

**使用场景**
- 研究主题的背景信息
- 获取最新数据和新闻
- 查找相关案例和实例

**参数**
```python
query: str        # 搜索关键词
num_results: int = 5  # 返回结果数量（1-10）
```

**返回示例**
```python
{
    "results": [
        {
            "title": "人工智能在医疗领域的应用",
            "url": "https://example.com/ai-healthcare",
            "snippet": "人工智能技术正在 revolutionizing 医疗行业..."
        }
    ]
}
```

---

#### fetch_url

**基本信息**
- **工具名称**: `fetch_url`
- **实现文件**: `backend/tools/domain/search/fetch_url.py`
- **工具类别**: SEARCH
- **版本**: 1.0.0

**功能说明**
- 获取指定 URL 的网页内容
- 提取正文文本（去除 HTML 标签）
- 支持中英文网页

**使用场景**
- 获取详细的文章内容
- 补充搜索结果的摘要信息
- 提取特定网页的数据

**参数**
```python
url: str          # 网页 URL
max_length: int = 5000  # 返回的最大字符数
```

**返回示例**
```python
{
    "url": "https://example.com/article",
    "title": "文章标题",
    "content": "网页正文内容...",
    "length": 1234
}
```

---

#### weixin_search

**基本信息**
- **工具名称**: `weixin_search`
- **实现文件**: `backend/tools/domain/search/weixin_search.py`
- **工具类别**: SEARCH
- **版本**: 1.0.0

**功能说明**
- 搜索微信公众号文章
- 获取高质量中文内容
- 适用于获取专业分析和案例

**使用场景**
- 搜索行业分析文章
- 获取案例研究
- 查找专业解读

**参数**
```python
query: str        # 搜索关键词
num_results: int = 5  # 返回结果数量
```

---

### 2️⃣ 媒体类工具 (1个)

#### search_images

**基本信息**
- **工具名称**: `search_images`
- **实现文件**: `backend/tools/domain/media/search_images.py`
- **工具类别**: MEDIA
- **版本**: 1.0.0

**功能说明**
- 搜索高质量图片
- 支持关键词搜索
- 返回图片 URL 和描述

**使用场景**
- 为 PPT 页面查找配图
- 获取示意图和图表
- 搜索图标和素材

**参数**
```python
query: str        # 搜索关键词
num_results: int = 5  # 返回结果数量
```

**返回示例**
```python
{
    "images": [
        {
            "url": "https://example.com/image.jpg",
            "thumbnail": "https://example.com/thumb.jpg",
            "description": "AI 技术架构图"
        }
    ]
}
```

---

### 3️⃣ 实用类工具 (3个)

#### create_pptx

**基本信息**
- **工具名称**: `create_pptx`
- **实现文件**: `backend/tools/domain/utility/create_pptx.py`
- **工具类别**: UTILITY
- **版本**: 1.0.0

**功能说明**
- 创建 PowerPoint (.pptx) 文件
- 支持添加标题、内容、图片
- 自动应用模板样式

**使用场景**
- 从框架生成最终 PPT
- 批量创建演示文稿
- 导出 Agent 生成的内容

**参数**
```python
output_path: str           # 输出文件路径
slides: List[Dict]         # 幻灯片列表
template: str = "default"  # 模板名称
```

**返回示例**
```python
{
    "success": True,
    "file_path": "/path/to/output.pptx",
    "slides_count": 10
}
```

---

#### xml_converter

**基本信息**
- **工具名称**: `xml_converter`
- **实现文件**: `backend/tools/domain/utility/xml_converter.py`
- **工具类别**: UTILITY
- **版本**: 1.0.0

**功能说明**
- XML 与 JSON 之间的格式转换
- 支持复杂的嵌套结构
- 保持数据完整性

**使用场景**
- 转换旧系统的 XML 数据
- 与外部系统交换数据
- 数据格式标准化

**参数**
```python
data: str           # 输入数据
from_format: str    # 输入格式 (xml/json)
to_format: str      # 输出格式 (xml/json)
```

---

#### a2a_client

**基本信息**
- **工具名称**: `a2a_client`
- **实现文件**: `backend/tools/domain/utility/a2a_client.py`
- **工具类别**: UTILITY
- **版本**: 1.0.0

**功能说明**
- Agent 间通信客户端
- 支持 RPC 调用
- 异步消息传递

**使用场景**
- Agent 协作
- 任务分发
- 数据共享

**参数**
```python
target_agent: str   # 目标 Agent 名称
message: Dict       # 消息内容
timeout: int = 30   # 超时时间（秒）
```

---

### 4️⃣ 数据库类工具 (2个)

#### state_store

**基本信息**
- **工具名称**: `state_store`
- **实现文件**: `backend/tools/domain/database/state_store.py`
- **工具类别**: DATABASE
- **版本**: 1.0.0

**功能说明**
- 存储和检索 PPT 生成状态
- 支持检查点机制
- 提供事务保证

**使用场景**
- 保存生成进度
- 恢复中断的任务
- 多 Agent 协作状态同步

**参数**
```python
task_id: str        # 任务 ID
state: Dict          # 状态数据
operation: str       # 操作类型 (save/load/delete)
```

---

#### vector_search

**基本信息**
- **工具名称**: `vector_search`
- **实现文件**: `backend/tools/domain/database/vector_search.py`
- **工具类别**: DATABASE
- **版本**: 1.0.0

**功能说明**
- 向量相似度搜索
- 语义匹配
- 支持批量查询

**使用场景**
- 查找相似内容
- 推荐相关资料
- 知识检索

**参数**
```python
query: str          # 查询文本
top_k: int = 5      # 返回结果数量
index: str = "default"  # 索引名称
```

**返回示例**
```python
{
    "results": [
        {
            "content": "相关内容...",
            "score": 0.95,
            "metadata": {...}
        }
    ]
}
```

---

## 🔧 使用示例

### 在 Agent 中使用

```python
from backend.agents.core.base_agent import BaseToolAgent

class MyAgent(BaseToolAgent):
    def __init__(self):
        super().__init__(
            tool_names=[
                "web_search",
                "fetch_url",
                "search_images",
            ],
            agent_name="MyAgent"
        )
```

### 直接调用

```python
from backend.tools.application.tool_registry import get_native_registry

registry = get_native_registry()

# 获取工具
web_search = registry.get_tool("web_search")

# 调用工具
result = await web_search.ainvoke({
    "query": "人工智能",
    "num_results": 5
})
```

---

## 📊 性能指标

| 工具 | 响应时间 | 并发支持 | 错误率 |
|------|----------|----------|--------|
| web_search | ~2s | ✅ | < 1% |
| fetch_url | ~1s | ✅ | < 2% |
| weixin_search | ~3s | ✅ | < 5% |
| search_images | ~2s | ✅ | < 3% |
| create_pptx | ~5s | ❌ | < 1% |
| xml_converter | < 1s | ✅ | < 1% |
| a2a_client | ~1s | ✅ | < 2% |
| state_store | < 1s | ✅ | < 0.1% |
| vector_search | ~1s | ✅ | < 1% |

---

## ⚠️ 注意事项

### 1. API 密钥配置

搜索工具（web_search, weixin_search）需要配置 API 密钥：

```python
# .env 文件
BING_SEARCH_API_KEY=your_api_key
WEIXIN_APP_ID=your_app_id
WEIXIN_APP_SECRET=your_app_secret
```

### 2. 速率限制

- `web_search`: 10 次/秒
- `fetch_url`: 20 次/秒
- `search_images`: 5 次/秒

### 3. 错误处理

所有工具都实现了错误处理：
- 网络错误：自动重试 3 次
- API 错误：返回详细错误信息
- 超时：默认 30 秒

---

## 📚 相关文档

- **[应用层文档](../application/)** - 如何在 Agent 中使用这些工具
- **[Python Skills 参考](./python-skills.md)** - Python Skills 完整列表
- **[MD Skills 参考](./md-skills.md)** - MD Skills 完整列表

---

**最后更新**: 2026-02-16
**维护者**: MultiAgentPPT 团队
