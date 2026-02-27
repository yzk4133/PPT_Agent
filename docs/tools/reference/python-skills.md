# Python Skills 参考文档

> **8 个可执行工作流的完整列表和详细说明**

Python Skills 是实现为 Python 类的工作流，转换为 LangChain Tools 后可以被 LLM 调用执行。

---

## 📋 Skills 列表

### 1️⃣ 研究类 Skills (1个)

#### research_workflow

**基本信息**
- **Skill 名称**: `research_workflow`
- **实现文件**: `backend/tools/skills/python_skills/research_workflow.py`
- **使用 Agent**: ResearchAgent
- **Skill 类型**: Python Skill（可执行工作流）
- **版本**: 1.0.0

**功能说明**
执行系统化的 4 步研究工作流程：
1. **关键词提取**：从主题中提取关键搜索词
2. **并行搜索**：使用多个搜索词并行搜索
3. **信息过滤**：根据相关性过滤结果
4. **综合分析**：整合信息生成结构化报告

**使用场景**
- 为 PPT 页面收集背景资料
- 获取特定主题的最新信息
- 研究竞争对手和案例

**输入参数**
```python
topic: str              # 研究主题
keywords: List[str]     # 搜索关键词列表
depth: int = 3          # 研究深度（1-5）
```

**输出格式**
```python
{
    "success": True,
    "data": {
        "topic": "人工智能",
        "key_points": ["要点1", "要点2", ...],
        "background": "背景知识...",
        "statistics": [{"data": "...", "source": "..."}],
        "examples": ["案例1", "案例2"],
        "sources": ["来源1", "来源2"]
    },
    "error": None
}
```

**调用示例**
```python
# LLM 调用
result = await research_workflow.ainvoke({
    "topic": "人工智能在医疗领域的应用",
    "keywords": ["AI 医疗", "人工智能诊断", "医疗 AI 案例"],
    "depth": 3
})
```

---

### 2️⃣ 内容类 Skills (3个)

#### content_generation

**基本信息**
- **Skill 名称**: `content_generation`
- **实现文件**: `backend/tools/skills/python_skills/content_generation.py`
- **使用 Agent**: ContentMaterialAgent
- **Skill 类型**: Python Skill（可执行工作流）
- **版本**: 1.0.0

**功能说明**
执行 5 步结构化内容生成：
1. **需求分析**：理解页面的目标和受众
2. **要点提取**：从研究资料中提取关键信息
3. **结构化**：组织内容的逻辑结构
4. **优化表达**：改进语言的清晰度和吸引力
5. **质量检查**：验证内容的完整性和质量

**使用场景**
- 为 PPT 页面生成正文内容
- 创建标题和要点列表
- 生成图表描述和配图建议

**输入参数**
```python
topic: str              # 内容主题
page_type: str          # 页面类型 (content/chart/image)
word_count: int = 300   # 目标字数
tone: str = "professional"  # 语调风格
research_data: Dict = None  # 研究资料
```

**输出格式**
```python
{
    "success": True,
    "data": {
        "title": "人工智能技术概览",
        "key_points": [
            "机器学习是 AI 的核心",
            "深度学习推动 AI 发展",
            "AI 应用遍布各行各业"
        ],
        "content_text": "详细内容...",
        "has_chart": True,
        "chart_data": {...},
        "has_image": True,
        "image_suggestion": {...}
    },
    "error": None
}
```

---

#### content_optimization

**基本信息**
- **Skill 名称**: `content_optimization`
- **实现文件**: `backend/tools/skills/python_skills/content_optimization.py`
- **使用 Agent**: ContentMaterialAgent
- **Skill 类型**: Python Skill（可执行工作流）
- **版本**: 1.0.0

**功能说明**
优化已生成的内容质量：
- **结构优化**：改进逻辑和层次
- **语言优化**：提升表达清晰度
- **吸引力优化**：增强标题和要点
- **简洁性优化**：去除冗余信息

**使用场景**
- 改进初稿内容
- 提升内容吸引力
- 调整内容风格

**输入参数**
```python
content: Dict          # 原始内容
optimization_goal: str = "clarity"  # 优化目标 (clarity/engagement/conciseness)
max_iterations: int = 3  # 最大优化轮次
```

**输出格式**
```python
{
    "success": True,
    "data": {
        "original": {...},
        "optimized": {...},
        "improvements": ["改进了标题", "精简了要点", ...],
        "quality_score": {"before": 0.7, "after": 0.9}
    },
    "error": None
}
```

---

#### content_quality_check

**基本信息**
- **Skill 名称**: `content_quality_check`
- **实现文件**: `backend/tools/skills/python_skills/content_quality_check.py`
- **使用 Agent**: ContentMaterialAgent
- **Skill 类型**: Python Skill（可执行工作流）
- **版本**: 1.0.0

**功能说明**
检查内容质量并给出评分：
- **完整性检查**：标题、要点、数据是否齐全
- **准确性检查**：事实是否准确
- **规范性检查**：格式、长度是否符合规范
- **吸引力检查**：标题是否有吸引力

**使用场景**
- 验证生成内容的质量
- 发现需要改进的地方
- 决定是否需要重新生成

**输入参数**
```python
content: Dict          # 待检查的内容
check_level: str = "standard"  # 检查级别 (basic/standard/strict)
```

**输出格式**
```python
{
    "success": True,
    "data": {
        "overall_score": 0.85,
        "checks": {
            "completeness": 0.9,
            "accuracy": 0.8,
            "standard": 0.85,
            "appeal": 0.8
        },
        "issues": ["标题过长", "缺少数据支撑"],
        "recommendations": ["精简标题", "添加具体数据"]
    },
    "error": None
}
```

---

### 3️⃣ 框架类 Skills (3个)

#### framework_design

**基本信息**
- **Skill 名称**: `framework_design`
- **实现文件**: `backend/tools/skills/python_skills/framework_design.py`
- **使用 Agent**: FrameworkDesignerAgent
- **Skill 类型**: Python Skill（可执行工作流）
- **版本**: 1.0.0

**功能说明**
设计 PPT 的整体框架：
- **封面设计**：标题和副标题
- **目录结构**：章节划分
- **页面分配**：为每个主题分配页数
- **特殊标记**：标记需要研究、图表、图片的页面

**使用场景**
- 从主题生成 PPT 框架
- 规划演示文稿结构
- 确定内容重点

**输入参数**
```python
topic: str              # 演示主题
total_pages: int = 10   # 总页数
audience: str = "general"  # 目标受众 (expert/general/student)
focus_areas: List[str] = None  # 重点领域
```

**输出格式**
```python
{
    "success": True,
    "data": {
        "title": "人工智能技术概览",
        "subtitle": "从原理到应用",
        "pages": [
            {"page_no": 1, "type": "cover", "title": "封面"},
            {"page_no": 2, "type": "directory", "title": "目录"},
            {"page_no": 3, "type": "content", "title": "AI 简介", "is_need_research": True},
            ...
        ]
    },
    "error": None
}
```

---

#### topic_decomposition

**基本信息**
- **Skill 名称**: `topic_decomposition`
- **实现文件**: `backend/tools/skills/python_skills/topic_decomposition.py`
- **使用 Agent**: FrameworkDesignerAgent
- **Skill 类型**: Python Skill（可执行工作流）
- **版本**: 1.0.0

**功能说明**
将复杂主题分解为子主题：
- **层次分解**：逐层细分
- **逻辑关联**：保持主题间的逻辑关系
- **页数估算**：为每个子主题估算所需页数

**使用场景**
- 将大主题分解为可管理的部分
- 规划章节结构
- 确定内容深度

**输入参数**
```python
topic: str              # 待分解的主题
max_depth: int = 3      # 分解深度
max_pages_per_section: int = 5  # 每个部分的最大页数
```

**输出格式**
```python
{
    "success": True,
    "data": {
        "main_topic": "人工智能",
        "subtopics": [
            {
                "name": "机器学习",
                "depth": 2,
                "estimated_pages": 3,
                "children": ["监督学习", "无监督学习", "强化学习"]
            },
            ...
        ]
    },
    "error": None
}
```

---

#### section_planning

**基本信息**
- **Skill 名称**: `section_planning`
- **实现文件**: `backend/tools/skills/python_skills/section_planning.py`
- **使用 Agent**: FrameworkDesignerAgent
- **Skill 类型**: Python Skill（可执行工作流）
- **版本**: 1.0.0

**功能说明**
规划章节的详细内容：
- **页面类型**：确定每页的类型（内容页/图表页/图片页）
- **核心内容**：定义每页的核心要点
- **研究需求**：标记需要外部研究的页面

**使用场景**
- 详细规划每个章节
- 确定页面的布局和内容
- 标记研究需求

**输入参数**
```python
section: Dict           # 章节信息
total_pages: int        # 可用页数
include_visuals: bool = True  # 是否包含视觉元素
```

**输出格式**
```python
{
    "success": True,
    "data": {
        "section_title": "机器学习基础",
        "pages": [
            {
                "page_no": 3,
                "type": "content",
                "title": "什么是机器学习",
                "core_content": "定义、特点、应用...",
                "is_need_research": False
            },
            {
                "page_no": 4,
                "type": "chart",
                "title": "机器学习分类",
                "core_content": "监督学习、无监督学习...",
                "is_need_research": True,
                "keywords": ["机器学习", "分类", "对比"]
            },
            ...
        ]
    },
    "error": None
}
```

---

### 4️⃣ 布局类 Skills (1个)

#### layout_selection

**基本信息**
- **Skill 名称**: `layout_selection`
- **实现文件**: `backend/tools/skills/python_skills/layout_selection.py`
- **使用 Agent**: RendererAgent（如果有）
- **Skill 类型**: Python Skill（可执行工作流）
- **版本**: 1.0.0

**功能说明**
为 PPT 页面选择合适的布局：
- **分析内容**：理解页面内容的类型和结构
- **推荐布局**：根据内容推荐最佳布局
- **提供选项**：提供多个备选布局

**使用场景**
- 为内容选择合适的 PPT 布局
- 优化页面视觉效果
- 提升内容可读性

**输入参数**
```python
page_info: Dict        # 页面信息（标题、要点数量、是否有图表）
template: str = "business"  # PPT 模板风格
```

**输出格式**
```python
{
    "success": True,
    "data": {
        "recommended_layout": "Title+Content",
        "layout_options": [
            {"name": "Title+Content", "suitability": 0.95},
            {"name": "Two Column", "suitability": 0.85},
            {"name": "Vertical List", "suitability": 0.75}
        ],
        "reasoning": "页面包含标题和 3 个要点，适合使用标题+内容布局..."
    },
    "error": None
}
```

---

## 🔧 使用示例

### 在 Agent 中使用

```python
from backend.agents.core.base_agent import BaseToolAgent

class ContentAgent(BaseToolAgent):
    def __init__(self):
        super().__init__(
            tool_names=[
                "content_generation",
                "content_optimization",
                "content_quality_check",
            ],
            agent_name="ContentAgent"
        )
```

### 直接调用

```python
from backend.tools.application.tool_registry import get_native_registry

registry = get_native_registry()

# 获取 Skill Tool
content_gen = registry.get_tool("content_generation")

# 调用 Skill
result = await content_gen.ainvoke({
    "topic": "人工智能技术",
    "page_type": "content",
    "word_count": 300,
    "tone": "professional"
})
```

---

## 📊 Skills 对比

| Skill | 输入 | 输出 | 复杂度 | 可靠性 |
|-------|------|------|--------|--------|
| **research_workflow** | 主题+关键词 | 结构化研究资料 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **content_generation** | 主题+类型 | PPT 内容 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **content_optimization** | 内容 | 优化后内容 | ⭐⭐ | ⭐⭐⭐⭐ |
| **content_quality_check** | 内容 | 质量评分 | ⭐ | ⭐⭐⭐⭐⭐ |
| **framework_design** | 主题+页数 | PPT 框架 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **topic_decomposition** | 主题 | 子主题列表 | ⭐⭐ | ⭐⭐⭐⭐ |
| **section_planning** | 章节 | 页面规划 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **layout_selection** | 页面信息 | 布局推荐 | ⭐ | ⭐⭐⭐⭐ |

---

## 💡 最佳实践

### 1. 配对使用 MD Guides

```python
# ✅ 推荐：配对使用
tool_names = [
    "content_generation",         # Python Skill
    "content_generation_prompts", # 对应的 MD Guide
]

# LLM 可以：
# 1. 先查阅 MD Guide 获取最佳实践
# 2. 再调用 Python Skill 执行任务
```

### 2. 渐进式优化

```python
# 1. 生成初稿
content = await content_generation.ainvoke({...})

# 2. 检查质量
quality = await content_quality_check.ainvoke({"content": content})

# 3. 如果质量不佳，优化
if quality["data"]["overall_score"] < 0.8:
    content = await content_optimization.ainvoke({"content": content})
```

### 3. 错误处理

```python
# Python Skills 返回统一格式
result = await skill.ainvoke(...)

if result["success"]:
    data = result["data"]
else:
    error = result["error"]
    # 处理错误
```

---

## 📚 相关文档

- **[应用层文档](../application/)** - 如何在 Agent 中使用这些 Skills
- **[Domain Tools 参考](./domain-tools.md)** - Domain Tools 完整列表
- **[MD Skills 参考](./md-skills.md)** - MD Skills 完整列表

---

**最后更新**: 2026-02-16
**维护者**: MultiAgentPPT 团队
