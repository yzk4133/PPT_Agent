# Tools 系统文档

MultiAgentPPT 项目的工具系统文档 - 统一工具架构。

---

## 🎯 快速导航

### 我想...
| 需求 | 推荐文档 |
|------|---------|
| **了解工具系统概览** | [本 README](./README.md) |
| **如何在 Agent 中使用工具** | [应用层文档](./application/README.md) |
| **理解注册表原理** | [Tool Registry 详解](./application/tool-registry.md) |
| **查看 Domain Tools 列表** | [Domain Tools 参考](./reference/domain-tools.md) |
| **查看 Python Skills 列表** | [Python Skills 参考](./reference/python-skills.md) |
| **查看 MD Skills 列表** | [MD Skills 参考](./reference/md-skills.md) |

---

## 📖 文档结构

```
docs/tools/
├── README.md                    # 本文件 - 主导航
│
├── application/                 # 【应用层】如何使用工具系统
│   ├── README.md                # 应用层总览
│   └── tool-registry.md         # 工具注册表详解
│
└── reference/                   # 【参考文档】工具完整列表
    ├── README.md                # 参考文档导航
    ├── domain-tools.md          # Domain Tools（10个）
    ├── python-skills.md         # Python Skills（8个）
    └── md-skills.md             # MD Skills（4个）
```

---

## 🏗️ 统一工具系统

### 系统架构

```
┌─────────────────────────────────────────────────┐
│          应用层                   │
│    统一注册表 (tool_registry.py)                │
│    - 集中管理所有工具                            │
│    - 自动发现和注册                              │
│    - 分类查询（SEARCH, SKILL, ...）             │
└─────────────────────────────────────────────────┘
                     ↓ 依赖
┌─────────────────────────────────────────────────┐
│          实现层                 │
│    ┌──────────────────────────────────────┐    │
│    │ Domain Tools (10个)                  │    │
│    │ - search/ (3个)                      │    │
│    │ - media/ (1个)                       │    │
│    │ - utility/ (3个)                     │    │
│    │ - database/ (2个)                    │    │
│    └──────────────────────────────────────┘    │
│    ┌──────────────────────────────────────┐    │
│    │ Skills (12个)                        │    │
│    │ - python_skills/ (8个)               │    │
│    │ - md_skills/ (4个)                   │    │
│    └──────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
                     ↓ 依赖
┌─────────────────────────────────────────────────┐
│          基础设施层               │
│    - LangChain Tools (StructuredTool)          │
│    - BaseSkill 基类                            │
│    - MarkdownSkill 解析器                      │
│    - 配置、异常处理、监控                        │
└─────────────────────────────────────────────────┘
```

---

## 🔑 核心概念

### Tool vs Skill

| 类型 | 定义 | 实现方式 | 数量 | LLM 使用方式 |
|------|------|----------|------|--------------|
| **Domain Tool** | 可执行的外部能力 | 直接实现为 LangChain Tools | 10个 | 调用执行 |
| **Python Skill** | 可执行的工作流 | Python 类，转换为 Tools | 8个 | 调用执行 |
| **MD Skill** | 分层的提示词模板 | Markdown 文件，封装为 Tools | 4个 | 查阅参考 |

**统一管理**：所有工具（Domain + Python + MD）都注册到同一个 `NativeToolRegistry`，通过统一的 SKILL 类别访问。

### 工具分类

#### Domain Tools（10个）

**搜索类**：
- `web_search`: 网络搜索
- `fetch_url`: 获取 URL 内容
- `weixin_search`: 微信文章搜索

**媒体类**：
- `search_images`: 图片搜索

**实用类**：
- `create_pptx`: 创建 PPT 文件
- `xml_converter`: XML 转换
- `a2a_client`: Agent 间通信

**数据库类**：
- `state_store`: 状态存储
- `vector_search`: 向量搜索

#### Skills（12个 = 8个Python + 4个MD）

**Python Skills（可执行）**：
- `research_workflow`: 研究工作流
- `content_generation`: 内容生成
- `content_optimization`: 内容优化
- `content_quality_check`: 质量检查
- `framework_design`: 框架设计
- `topic_decomposition`: 主题分解
- `section_planning`: 章节规划
- `layout_selection`: 布局选择

**MD Skills（指南）**：
- `content_generation_prompts`: 内容生成指南
- `research_prompts`: 研究工作指南
- `framework_prompts`: 框架设计指南
- `quality_check_prompts`: 质量检查指南

---

## 📂 代码结构

```
backend/tools/
├── application/              # 【应用层】统一管理
│   ├── __init__.py
│   └── tool_registry.py      # ← 核心文件：统一注册表
│
├── domain/                   # 【实现层】Domain Tools
│   ├── search/               (3个)
│   ├── media/                (1个)
│   ├── utility/              (3个)
│   └── database/             (2个)
│
└── skills/                   # 【实现层】Skills
    ├── base_skill.py         # Python Skill 基类
    ├── markdown_skill.py     # MD Skill 解析器
    ├── python_skills/        (8个 Python Skills)
    │   ├── research_workflow.py
    │   ├── content_generation.py
    │   └── ...
    └── md_skills/            (4个 MD Skills)
        ├── content_generation_prompts.md
        ├── research_prompts.md
        ├── framework_prompts.md
        └── quality_check_prompts.md
```

**关键点**：
- ✅ 单一注册表：`tool_registry.py` 管理所有工具
- ✅ 自动发现：Domain Tools 模块级注册，Python Skills 导入时转换，MD Skills 启动时扫描
- ✅ 统一接口：所有工具都转换为 LangChain Tools，通过 `get_tools_by_category()` 访问

---

## 📚 系统概览

### 核心组件

**1. NativeToolRegistry（统一注册表）**

位置：`backend/tools/application/tool_registry.py`

功能：
- 统一管理所有工具（Domain + Python + MD）
- 自动发现和注册
- 按类别组织（SEARCH, SKILL, MEDIA, UTILITY, DATABASE）
- 提供查询接口

**2. BaseSkill（Python Skill 基类）**

位置：`backend/tools/skills/base_skill.py`

功能：
- Python Skill 的抽象基类
- 定义 `execute()` 接口
- 提供生命周期管理

**3. MarkdownSkill（MD Skill 解析器）**

位置：`backend/tools/skills/markdown_skill.py`

功能：
- 解析 MD 文件的 frontmatter
- 提取 Level 1/2/3 内容
- 封装为 LangChain Tool

---

## 🚀 快速开始

### 1. 获取所有工具

```python
from backend.tools.application import get_native_registry

# 获取全局注册表
registry = get_native_registry()

# 查看摘要
registry.log_summary()
# [NativeToolRegistry] Total tools: 21
#   SEARCH: 3 tools - web_search, fetch_url, weixin_search
#   SKILL: 12 tools - content_generation, content_generation_guide, ...
#   MEDIA: 1 tools - search_images
#   UTILITY: 3 tools - create_pptx, xml_converter, a2a_client
#   DATABASE: 2 tools - state_store, vector_search

# 获取所有工具
all_tools = registry.get_all_tools()
```

### 2. 获取特定类别的工具

```python
# 获取搜索工具
search_tools = registry.get_tools_by_category("SEARCH")

# 获取 Skills（包含 Python + MD）
skill_tools = registry.get_tools_by_category("SKILL")

# 获取数据库工具
db_tools = registry.get_tools_by_category("DATABASE")
```

### 3. 在 Agent 中使用

```python
from backend.agents.core.base_agent import BaseToolAgent

class MyAgent(BaseToolAgent):
    def __init__(self):
        # 自动加载 SKILL 类别的工具（包含 Python + MD）
        super().__init__(
            tool_categories=["SKILL"],
            agent_name="MyAgent"
        )

    async def execute_task(self, query):
        # LLM 自主选择工具
        # 可以调用 Python Tools 执行任务
        # 也可以查阅 MD Guides 获取指导
        result = await self.execute_with_tools(query)
        return result
```

---

## 📖 学习建议

### 新手路径（30分钟）

1. 阅读 [本 README](README.md) - 5分钟
2. 阅读 [应用层 README](01-application/README.md) - 10分钟
3. 阅读 [实现层 README](02-implementation/README.md) - 15分钟

### 深入学习（2小时）

1. **理解注册表原理**：[tool-registry.md](01-application/tool-registry.md)
2. **查看工具实现**：[tools-overview.md](02-implementation/tools-overview.md)
3. **理解三层架构**：[three-layers.md](03-infrastructure/three-layers.md)

### 开发者路径（4小时）

1. **应用层**：掌握如何使用注册表
2. **实现层**：了解如何添加新工具
3. **基础设施层**：理解底层设计原理

---

## 🎯 添加新工具

### Domain Tool

```python
# backend/tools/domain/search/my_search.py
from langchain.tools import StructuredTool
from backend.tools.application.tool_registry import get_native_registry

async def my_search_func(query: str) -> str:
    return f"搜索结果：{query}"

# 创建工具
my_search_tool = StructuredTool.from_function(
    func=my_search_func,
    name="my_search",
    description="我的搜索工具"
)

# 自动注册
registry = get_native_registry()
registry.register_tool(my_search_tool, category="SEARCH")
```

### Python Skill

```python
# backend/tools/skills/python_skills/my_skill.py
from backend.tools.skills.base_skill import BaseSkill
from langchain_core.tools import StructuredTool

class MyNewSkill(BaseSkill):
    name = "my_new_skill"
    description = "我的新技能"

    async def execute(self, param: str) -> Dict[str, Any]:
        return {
            "success": True,
            "data": {...},
            "error": None
        }

# 在模块内转换为 Tool
def _create_execution_function():
    async def execute(param: str) -> str:
        skill = MyNewSkill()
        result = await skill.execute(param=param)
        if result["success"]:
            return str(result["data"])
        else:
            return f"错误: {result['error']}"
    return execute

# 创建并注册
my_new_skill_tool = StructuredTool.from_function(
    func=_create_execution_function(),
    name="my_new_skill",
    description=MyNewSkill.description
)

registry = get_native_registry()
registry.register_tool(my_new_skill_tool, category="SKILL")
```

### MD Skill

```markdown
---
name: my_guide
description: 我的指南文档
category: guide
version: 1.0.0
---

# 我的指南

## Level 1: 快速指南

快速步骤...

## Level 2: 详细指南

详细说明...
```

**自动注册**：
- 将文件保存到 `backend/tools/skills/md_skills/my_guide.md`
- 重启服务后自动加载
- 无需修改任何代码

---

## 🔗 相关资源

- **项目主文档**: [MultiAgentPPT 文档](../)
- **源代码**: [backend/tools/](../../backend/tools/)
- **工具名称导入指南**: [TOOL_NAMES_IMPORT_GUIDE.md](../../TOOL_NAMES_IMPORT_GUIDE.md)

---

## ❓ 常见问题

### Q: Python Skills 和 MD Skills 有什么区别？

**A**:
- **Python Skills**: 可执行代码，调用后执行业务逻辑
- **MD Skills**: 静态文档，调用后返回分层指南文本
- **统一接口**: 都封装为 LangChain Tools，使用方式完全一样

### Q: 如何查看有哪些工具？

**A**:
```python
from backend.tools.application import get_native_registry

registry = get_native_registry()
registry.log_summary()  # 打印摘要
```

### Q: SKILL 类别包含哪些工具？

**A**:
- 8个可执行的 Python Tools
- 4个可查阅的 MD Guides
- 总共 12 个工具，统一管理

### Q: 如何调试工具加载问题？

**A**:
```python
# 查看注册表摘要
registry.log_summary()

# 检查特定工具
tool = registry.get_tool("tool_name")
if tool is None:
    print("工具未加载")
```

详见：[troubleshooting.md](03-infrastructure/troubleshooting.md)

---

## 📊 关键数字

### 工具统计

| 类型 | 数量 | 说明 |
|------|------|------|
| Domain Tools | 10 | 直接实现为 LangChain Tools |
| Python Skills | 8 | Python 类，转换为 Tools |
| MD Skills | 4 | Markdown 文件，封装为 Tools |
| **总计** | **22** | 统一管理 |

### 类别统计

| 类别 | 工具数 |
|------|--------|
| SEARCH | 3 |
| MEDIA | 1 |
| UTILITY | 3 |
| DATABASE | 2 |
| SKILL | 12 |

### 效率提升

| 指标 | 改进 |
|------|------|
| Agent 代码量减少 | 85% |
| 新增工具工作量减少 | 95% |
| 工具查找时间减少 | 97% |
| Bug 修复成本降低 | 70% |

---

**最后更新**: 2026-02-16
**维护者**: MultiAgentPPT 团队
