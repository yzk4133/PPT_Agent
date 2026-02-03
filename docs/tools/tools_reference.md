# 工具参考手册

## 目录

- [搜索类工具](#搜索类工具)
  - [DocumentSearch](#documentsearch)
- [媒体类工具](#媒体类工具)
  - [SearchImage](#searchimage)
- [技能框架工具](#技能框架工具)
  - [技能装饰器](#技能装饰器)
- [MCP工具](#mcp工具)

## 搜索类工具

### DocumentSearch

**工具名称**: `DocumentSearch`

**类别**: `ToolCategory.SEARCH`

**文件路径**: `backend/agents/tools/search/document_search.py`

**版本**: `1.0.0`

**作者**: `MultiAgentPPT`

#### 功能描述

根据关键词搜索文档资料。该工具集成了向量记忆服务，支持语义搜索，并提供降级策略确保可用性。

#### 参数说明

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| keyword | str | 是 | 搜索关键词 |
| number | int | 是 | 返回文档数量 |
| tool_context | ToolContext | 是 | ADK工具上下文 |

#### 返回值

**类型**: `str`

**格式**: 每篇文档以 `# 文档id:{id}\n{content}\n\n` 格式拼接

#### 使用示例

```python
from google.adk import Agent
from google.adk.tools import ToolContext
from agents.tools.search.document_search import DocumentSearch

# 示例1: 直接调用
result = await DocumentSearch(
    keyword="电动汽车",
    number=2,
    tool_context=tool_context
)
print(result)

# 示例2: 在Agent中使用
research_agent = Agent(
    name="research_agent",
    model="gemini-2.5-flash",
    instruction="使用DocumentSearch工具搜索文档信息",
    tools=[DocumentSearch]
)
```

#### 搜索流程

1. 检查向量记忆服务是否可用
2. 如果可用，执行向量搜索（相似度阈值0.75）
3. 如果未命中或服务不可用，使用默认文档数据库
4. 将结果缓存到向量数据库

#### 适用场景

- 文档检索和资料查询
- 学术研究辅助
- 知识库问答
- 背景资料收集

#### 注意事项

- 向量搜索相似度阈值默认为0.75，可根据需求调整
- 默认文档数据库包含电动汽车相关资料
- 搜索结果会自动缓存到向量数据库供后续使用

---

## 媒体类工具

### SearchImage

**工具名称**: `SearchImage`

**类别**: `ToolCategory.MEDIA`

**文件路径**: `backend/agents/tools/media/image_search.py`

**版本**: `1.0.0`

**作者**: `MultiAgentPPT`

#### 功能描述

根据关键词搜索对应的图片。当前为模拟实现，返回预设的图片URL列表。

#### 参数说明

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| query | str | 是 | 搜索关键词 |
| tool_context | ToolContext | 是 | ADK工具上下文 |

#### 返回值

**类型**: `str`

**格式**: 图片URL字符串

#### 使用示例

```python
from agents.tools.media.image_search import SearchImage

# 示例1: 直接调用
image_url = await SearchImage(
    query="flowers",
    tool_context=tool_context
)
print(image_url)
# 输出示例: https://cdn.pixabay.com/photo/2024/12/18/07/57/aura-9274671_640.jpg

# 示例2: 在Agent中使用
content_agent = Agent(
    name="content_agent",
    model="gemini-2.5-flash",
    instruction="使用SearchImage为PPT查找相关图片",
    tools=[SearchImage]
)
```

#### 预设图片列表

当前版本从以下预设列表中随机返回图片URL：

1. `https://cdn.pixabay.com/photo/2024/12/18/07/57/aura-9274671_640.jpg`
2. `https://cdn.pixabay.com/photo/2024/12/18/15:02/old-9275581_640.jpg`
3. `https://cdn.pixabay.com/photo/2022/11/08/11/16/alien-7578281_640.jpg`
4. `https://cdn.pixabay.com/photo/2023/01/27/02:28/figure-7747589_640.jpg`
5. `https://cdn.pixabay.com/photo/2022/10/29/12:34/fantasy-7555144_640.jpg`

#### 适用场景

- PPT图片素材搜索
- 内容配图查找
- 视觉资源获取
- 演示文稿制作

#### 注意事项

- 当前为模拟实现，生产环境需要接入真实的图片搜索API（如Unsplash、Pexels等）
- 返回结果是随机选择的，与搜索关键词无实际关联
- 建议后续实现真实的图片搜索服务

---

## 技能框架工具

### 技能装饰器

#### @Skill 装饰器

**文件路径**: `backend/agents/tools/skills/skill_decorator.py`

**功能描述**: 将Python类标记为技能，附加元数据并使其可被技能框架识别和管理。

**参数说明**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| name | str | 是 | - | 技能显示名称 |
| version | str | 否 | "1.0.0" | 语义版本字符串 |
| category | str | 否 | "utility" | 技能类别（来自SkillCategory枚举） |
| tags | List[str] | 否 | [] | 标签列表，用于过滤 |
| description | str | 否 | "" | 技能描述 |
| enabled | bool | 否 | True | 是否默认启用 |
| author | str | 否 | None | 作者名称 |
| dependencies | List[str] | 否 | [] | 依赖的技能ID列表 |

**使用示例**

```python
from agents.tools.skills.skill_decorator import Skill
from google.adk.tools import ToolContext

@Skill(
    name="TextAnalysis",
    version="1.0.0",
    category="analysis",
    tags=["text", "analysis", "nlp"],
    description="文本分析技能，支持情感分析和关键词提取",
    enabled=True,
    author="Your Name"
)
class TextAnalysisSkill:
    async def analyze_sentiment(self, text: str, tool_context: ToolContext) -> str:
        """分析文本情感"""
        # 实现情感分析逻辑
        return f"情感分析结果: {text}"

    async def extract_keywords(self, text: str, tool_context: ToolContext) -> str:
        """提取关键词"""
        # 实现关键词提取逻辑
        return f"关键词: 关键词1, 关键词2"

# 注册技能
from agents.tools.skills.managers.skill_manager import SkillManager
skill_manager = SkillManager()
skill_manager.register_custom_skill(TextAnalysisSkill)

# 获取工具
tools = skill_manager.get_tools_for_agent(skill_ids=["text_analysis"])
```

#### @SkillMethod 装饰器

**功能描述**: 为技能中的特定方法添加额外的元数据。

**参数说明**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| description | str | 否 | "" | 方法功能描述 |
| parameters | Dict[str, Any] | 否 | {} | 参数模式定义 |
| examples | List[Dict[str, Any]] | 否 | [] | 使用示例列表 |

**使用示例**

```python
from agents.tools.skills.skill_decorator import Skill, SkillMethod

@Skill(
    name="Calculator",
    category="utility",
    description="计算器技能"
)
class CalculatorSkill:
    @SkillMethod(
        description="执行加法运算",
        parameters={
            "a": {"type": "number", "description": "第一个数"},
            "b": {"type": "number", "description": "第二个数"}
        },
        examples=[
            {"input": {"a": 5, "b": 3}, "output": 8}
        ]
    )
    async def add(self, a: float, b: float, tool_context: ToolContext) -> str:
        """加法运算"""
        return str(a + b)

    @SkillMethod(
        description="执行乘法运算",
        parameters={
            "a": {"type": "number", "description": "被乘数"},
            "b": {"type": "number", "description": "乘数"}
        }
    )
    async def multiply(self, a: float, b: float, tool_context: ToolContext) -> str:
        """乘法运算"""
        return str(a * b)
```

---

## MCP工具

### MCP Integration

**文件路径**: `backend/agents/tools/mcp/mcp_integration.py`

**功能描述**: 加载和管理MCP（Model Context Protocol）工具，支持SSE和Stdio两种连接方式。

### load_mcp_tools()

**功能**: 从配置文件加载MCP工具

**参数说明**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| mcp_config_path | str | 是 | - | MCP配置文件路径 |
| skill_manager | SkillManager | 否 | None | 可选的SkillManager实例 |
| auto_register | bool | 否 | True | 是否自动注册到SkillManager |

**返回值**: `List[MCPToolset]` - MCP工具集列表

**使用示例**

```python
from agents.tools.mcp.mcp_integration import load_mcp_tools
from agents.tools.skills.managers.skill_manager import SkillManager

# 创建SkillManager
skill_manager = SkillManager()

# 加载MCP工具
mcp_tools = load_mcp_tools(
    mcp_config_path="mcp_config.json",
    skill_manager=skill_manager,
    auto_register=True
)

print(f"已加载 {len(mcp_tools)} 个MCP工具")
```

**MCP配置文件格式** (mcp_config.json):

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    },
    "sse-server": {
      "url": "https://example.com/mcp",
      "timeout": 60
    }
  }
}
```

### load_all_tools()

**功能**: 为代理加载所有工具（技能 + MCP工具）

**参数说明**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| mcp_config_path | str | 否 | "mcp_config.json" | MCP配置文件路径 |
| skill_config_path | str | 否 | "backend/skill_config.json" | 技能配置文件路径 |
| agent_name | str | 否 | None | 代理名称 |
| categories | List[SkillCategory] | 否 | None | 类别过滤器 |
| tags | List[str] | 否 | None | 标签过滤器 |
| include_mcp | bool | 否 | True | 是否包含MCP工具 |

**返回值**: `List[Any]` - 工具列表

**使用示例**

```python
from agents.tools.mcp.mcp_integration import load_all_tools
from agents.tools.skills.skill_metadata import SkillCategory
from google.adk import Agent

# 加载所有工具
tools = load_all_tools(
    agent_name="research_agent",
    categories=[SkillCategory.SEARCH, SkillCategory.DOCUMENT],
    include_mcp=True
)

# 创建Agent
agent = Agent(
    name="research_agent",
    model="gemini-2.5-flash",
    instruction="研究助手",
    tools=tools
)
```

---

## 按类别索引

### SEARCH (搜索)
- [DocumentSearch](#documentsearch)

### MEDIA (媒体)
- [SearchImage](#searchimage)

### UTILITY (通用)
- [@Skill 装饰器](#skill-装饰器)
- [@SkillMethod 装饰器](#skillmethod-装饰器)

### EXTERNAL (外部)
- [MCP Integration](#mcp-integration)

---

## 按字母顺序索引

- **D**
  - [DocumentSearch](#documentsearch)

- **M**
  - [MCP Integration](#mcp-integration)

- **S**
  - [SearchImage](#searchimage)
  - [@Skill 装饰器](#skill-装饰器)
  - [@SkillMethod 装饰器](#skillmethod-装饰器)

---

## 相关文档

- [工具系统总览](tools_overview.md) - 系统概述和快速开始
- [工具系统架构详解](tools_architecture.md) - 架构设计和实现说明
- [技能框架指南](skills_framework.md) - 技能框架使用详解
- [工具开发指南](tools_development.md) - 创建新工具的开发指南
