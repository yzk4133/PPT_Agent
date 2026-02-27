# 5 个 Agent 的 Tools 和 Skills 配置现状分析

> 分析当前每个 Agent 配备的工具和技能，以及改进空间

---

## 📊 当前配置概览

### Agent 映射

| Agent | 职责 | 文件位置 |
|-------|------|----------|
| **RequirementParserAgent** | 需求解析 | `requirements/requirement_agent.py` |
| **FrameworkDesignerAgent** | 框架设计 | `planning/framework_agent.py` |
| **ResearchAgent** | 研究资料收集 | `research/research_agent.py` |
| **ContentMaterialAgent** | 内容生成 | `generation/content_agent.py` |
| **TemplateRendererAgent** | 渲染输出 | `rendering/renderer_agent.py` |

---

## 🔍 详细分析

### 1. RequirementParserAgent（需求解析）

**Tools 配置**：❌ 无

**Skills 配置**：❌ 无

**当前能力**：
- 使用 LLM 解析自然语言输入
- 提取结构化的 PPT 生成需求
- JSON 格式输出
- 支持用户偏好个性化（需启用记忆）

**提示词模板**：
```python
REQUIREMENT_PARSER_PROMPT = """
你是一名专业的PPT需求分析专家。
任务：分析用户的自然语言输入，提取结构化的PPT生成需求。

用户输入：{user_input}

输出格式：{
    "ppt_topic": "主题",
    "page_num": 10-30,
    "language": "ZH-CN|EN-US",
    "template_type": "business/academic/creative",
    ...
}
"""
```

---

### 2. FrameworkDesignerAgent（框架设计）

**Tools 配置**：❌ 无

**Skills 配置**：✅ 有（2 个 MD Skills）

| Skill | 类型 | 用途 |
|-------|------|------|
| `brand-guidelines` | MD | 品牌色彩和排版规范 |
| `domain-name-brainstormer` | MD | 创意标题和章节命名 |

**当前能力**：
- 使用 LLM 设计 PPT 框架
- 生成每页的标题、类型、内容描述
- 应用品牌规范（颜色、字体）
- 应用创意方法（标题生成、章节命名）
- 支持用户偏好（图表/图片偏好）
- 缓存框架设计结果

**提示词模板**：
```python
FRAMEWORK_DESIGNER_PROMPT = """
{SKILL_INSTRUCTIONS}  # ← Skills 被注入这里

你是一名专业的PPT结构设计专家。

需求信息：
- 主题：{ppt_topic}
- 页数：{page_num}
- 模板类型：{template_type}
...

请设计包含{page_num}页的PPT框架...
"""
```

**Skills 应用方式**：
- `_extract_design_guidance()` 提取设计指导
- `_apply_skills_to_prompt()` 将 Skills 注入提示词
- 品牌规范用于视觉一致性
- 创意方法用于标题和章节设计

---

### 3. ResearchAgent（研究资料收集）

**Tools 配置**：⚠️ 有但未启用（默认关闭）

| Tool | 类型 | 用途 | 状态 |
|------|------|------|------|
| `web_search` | MCP Tool | 网络搜索 | 需手动启用 |
| `fetch_url` | MCP Tool | 网页内容获取 | 需手动启用 |

**Skills 配置**：✅ 有（1 个 MD Skill）

| Skill | 类型 | 用途 |
|-------|------|------|
| `lead-research-assistant` | MD | 系统化研究方法 |

**当前能力**：
- 为需要研究的页面收集资料
- 生成背景信息和相关数据
- 支持搜索工具（需启用 `use_search_tools=True`）
- 工具失败时自动降级到 LLM 模式
- 并行研究多个页面
- 缓存研究结果

**提示词模板**：
```python
RESEARCH_PROMPT = """
{SKILL_INSTRUCTIONS}  # ← lead-research-assistant 被注入

你是一名专业的研究助理。

页面信息：
- 页码：{page_no}
- 标题：{page_title}
- 关键词：{keywords}

请为这个页面生成相关的研究资料：
1. 背景知识
2. 关键数据或事实
3. 相关案例或例子
4. 参考来源
"""
```

**工具使用方式**（如果启用）：
```python
if use_search_tools:
    self._setup_tools()  # 加载 web_search, fetch_url
    # 使用 LangChain AgentExecutor
    # LLM 可以调用工具进行实时搜索
```

---

### 4. ContentMaterialAgent（内容生成）

**Tools 配置**：❌ 无

**Skills 配置**：✅ 有（2 个 MD Skills）

| Skill | 类型 | 用途 |
|-------|------|------|
| `content-research-writer` | MD | 高质量内容创作 |
| `changelog-generator` | MD | 内容优化和转换 |

**当前能力**：
- 为每页生成详细内容
- 生成图表数据（如果需要）
- 提供配图建议（如果需要）
- 使用研究结果丰富内容
- 支持并行内容生成
- 应用用户偏好（语言、语调、风格）
- 缓存生成的内容

**提示词模板**：
```python
CONTENT_GENERATION_PROMPT = """
{SKILL_INSTRUCTIONS}  # ← Skills 被注入

你是一名专业的PPT内容创作专家。

页面信息：
- 页码：{page_no}
- 标题：{page_title}
- 类型：{page_type}

{research_section}  # ← ResearchAgent 的结果

用户偏好：
- 语言：{language}
- 语调：{tone}
- 模板：{template_type}

请生成PPT内容素材...
"""
```

**用户偏好支持**：
- `language`: ZH-CN / EN-US
- `tone`: professional / casual / creative
- `template_type`: business / academic / creative

---

### 5. TemplateRendererAgent（渲染输出）

**Tools 配置**：❌ 无

**Skills 配置**：✅ 有（2 个 MD Skills）

| Skill | 类型 | 用途 |
|-------|------|------|
| `canvas-design` | MD | 画布设计原则 |
| `pptx` | MD | PPT 设计规范 |

**当前能力**：
- 汇总所有阶段数据
- 生成 XML 格式的 PPT 内容
- 生成前端预览数据
- 支持文件保存
- 应用设计原则
- 缓存渲染结果

**设计原则应用**：
```python
def _extract_design_principles(self):
    principles = {}

    # canvas-design 原则
    principles["canvas"] = {
        "minimal_text": True,        # 极简文本
        "spatial_expression": True,  # 空间表达
        "expert_craftsmanship": True,# 专业技艺
        "negative_space": True,      # 负空间利用
    }

    # pptx 原则
    principles["pptx"] = {
        "web_safe_fonts": True,      # 网络安全字体
        "visual_hierarchy": True,    # 视觉层次
        "readability": True,         # 可读性
        "consistency": True,         # 一致性
    }

    return principles
```

---

## 📈 配置统计

### Skills 使用统计

| Agent | MD Skills 数 | Python Skills 数 |
|-------|--------------|------------------|
| RequirementParserAgent | 0 | 0 |
| FrameworkDesignerAgent | 2 | 0 |
| ResearchAgent | 1 | 0 |
| ContentMaterialAgent | 2 | 0 |
| TemplateRendererAgent | 2 | 0 |
| **总计** | **7** | **0** |

### Tools 使用统计

| Agent | Tools 数 | Tools 类型 |
|-------|----------|-----------|
| RequirementParserAgent | 0 | - |
| FrameworkDesignerAgent | 0 | - |
| ResearchAgent | 2（未启用）| MCP Tools |
| ContentMaterialAgent | 0 | - |
| TemplateRendererAgent | 0 | - |

---

## 🎯 改进空间

### 高优先级改进（P0）

#### 1. 使用新的 Python Skills

**现状**：所有 Agent 都只使用 MD Skills（提示词模板）

**改进**：使用刚刚创建的 Python Skills（可执行工作流程）

| Agent | 当前 Skills | 建议新增 Python Skills | 收益 |
|-------|-----------|---------------------|------|
| **ResearchAgent** | `lead-research-assistant` (MD) | `research_workflow` (Python) | ✅ 可执行的工作流程<br>✅ 可测试<br>✅ 支持工具集成 |
| **ContentAgent** | `content-research-writer`, `changelog-generator` (MD) | `content_generation` (Python) | ✅ 5步工作流程<br>✅ 质量检查<br>✅ 迭代优化 |
| **FrameworkAgent** | `brand-guidelines`, `domain-name-brainstormer` (MD) | `framework_design` (Python) | ✅ 结构化流程<br>✅ 主题分解<br>✅ 流程优化 |

**实施方式**：

```python
# 在 ResearchAgent 中使用 Python Skill
from backend.tools.skills import load_skill

class ResearchAgent(BaseAgent):
    def __init__(self, llm=None, use_search_tools=False):
        super().__init__(llm=llm)

        # 加载 Python Skill
        if use_python_skill:
            self.research_workflow = load_skill("research_workflow", llm=llm)
            self.research_workflow.search_tool = self._get_search_tool()

    async def execute_task(self, state):
        # 使用 Python Skill 执行工作流程
        result = await self.research_workflow.execute(
            topic=state["topic"],
            num_sources=5,
            depth="medium"
        )

        state["research_results"] = result["data"]
        return state
```

---

#### 2. 启用 ResearchAgent 的搜索工具

**现状**：ResearchAgent 有搜索工具配置但默认关闭

**问题**：
- 无法获取实时信息
- 研究质量依赖 LLM 内部知识
- 无法引用外部来源

**改进**：

```python
# 方式 1: 默认启用搜索工具
agent = ResearchAgent(
    use_search_tools=True,  # ← 改为 True
    use_research_skill=True
)

# 方式 2: 使用新的 MCP Server
# 在 ResearchAgent 中集成 MCP Client
from mcp import ClientSession, StdioServerParameters

class ResearchAgent(BaseAgent):
    def __init__(self):
        # 配置 MCP Server 参数
        self.mcp_server_params = StdioServerParameters(
            command="python",
            args=["backend/tools/mcp_server/server.py"],
            env={"BING_SEARCH_API_KEY": os.getenv("BING_SEARCH_API_KEY")}
        )

    async def search_with_mcp(self, query: str):
        """使用 MCP Server 搜索"""
        async with stdio_client(self.mcp_server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("web_search", {
                    "query": query,
                    "num_results": 5
                })
                return json.loads(result.content[0].text)
```

---

### 中优先级改进（P1）

#### 3. 为 ContentAgent 添加质量检查 Skill

**现状**：ContentAgent 生成内容后没有质量检查

**改进**：使用 `ContentQualityCheckSkill`

```python
from backend.tools.skills import load_skill, CompositeSkill

class ContentMaterialAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__(llm=llm)

        # 组合 Skills：生成 + 质检
        self.composite_skill = CompositeSkill([
            load_skill("content_generation", llm=llm),
            load_skill("content_quality_check", llm=llm)
        ])

    async def generate_content_for_page(self, page, research_results):
        # 生成内容
        result = await self.composite_skill.execute(
            topic=page["title"],
            research_data=research_results,
            audience="general"
        )

        # 检查质量
        quality_score = result["data"]["quality_score"]
        if quality_score < 0.8:
            logger.warning(f"Content quality low: {quality_score}, optimizing...")
            # 重新生成或优化

        return result["data"]
```

---

#### 4. 为 FrameworkAgent 添加主题分解 Skill

**现状**：FrameworkAgent 一次性生成完整框架，缺乏模块化

**改进**：使用 `TopicDecompositionSkill` 和 `SectionPlanningSkill`

```python
from backend.tools.skills import load_skill

class FrameworkDesignerAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__(llm=llm)

        # 加载子 Skills
        self.topic_decomposer = load_skill("topic_decomposition", llm=llm)
        self.section_planner = load_skill("section_planning", llm=llm)

    async def execute_task(self, state):
        requirement = state["structured_requirements"]
        topic = requirement["ppt_topic"]

        # 步骤 1: 分解主题
        decomposition = await self.topic_decomposer.execute(
            topic=topic,
            num_parts=5
        )
        subtopics = decomposition["data"]["parts"]

        # 步骤 2: 规划章节
        planning = await self.section_planner.execute(
            subtopics=subtopics,
            total_pages=requirement["page_num"]
        )

        # 步骤 3: 生成框架（使用 LLM）
        # ...

        return state
```

---

#### 5. 为 RendererAgent 添加布局选择 Skill

**现状**：RendererAgent 只生成 XML，没有布局建议

**改进**：创建 `LayoutSelectionSkill` 或使用现有的 MD Skills

```python
# backend/tools/skills/python_skills/layout_selection.py

class LayoutSelectionSkill(BaseSkill):
    """
    根据内容类型选择合适的布局
    """

    name = "layout_selection"
    description = "根据页面内容选择最佳布局"
    category = "rendering"

    async def execute(
        self,
        page_type: str,
        content_type: str,
        has_chart: bool,
        has_image: bool
    ) -> Dict[str, Any]:
        """选择布局"""

        # 布局规则
        layout_rules = {
            "cover": "title_center",
            "directory": "vertical_list",
            "content": {
                "text_only": "title_with_bullet_points",
                "text_with_chart": "title_with_left_chart",
                "text_with_image": "title_with_right_image",
                "text_with_both": "title_with_chart_and_image"
            },
            "summary": "title_with_bottom_summary"
        }

        # 选择布局
        if page_type == "content":
            layout = layout_rules["content"][content_type]
        else:
            layout = layout_rules[page_type]

        return {
            "success": True,
            "data": {
                "layout": layout,
                "alternatives": self._get_alternative_layouts(layout)
            }
        }
```

---

### 低优先级改进（P2）

#### 6. 为 RequirementParserAgent 添加意图识别 Skill

**现状**：RequirementParserAgent 只做简单解析

**改进**：添加意图识别和需求补充

```python
# backend/tools/skills/python_skills/intent_recognition.py

class IntentRecognitionSkill(BaseSkill):
    """
    识别用户意图并补充需求
    """

    name = "intent_recognition"
    description = "识别用户意图并补充隐含需求"
    category = "requirements"

    async def execute(
        self,
        user_input: str,
        parsed_requirement: Dict
    ) -> Dict[str, Any]:
        """识别意图并补充需求"""

        # 分析用户意图
        intent = await self._analyze_intent(user_input)

        # 补充隐含需求
        if intent.get("needs_research"):
            parsed_requirement["need_research"] = True

        if intent.get("needs_visuals"):
            parsed_requirement["prefer_more_images"] = True

        return {
            "success": True,
            "data": {
                "intent": intent,
                "enhanced_requirement": parsed_requirement
            }
        }
```

---

#### 7. 为所有 Agent 添加 Skills 组合能力

**现状**：Skills 独立使用，没有组合

**改进**：使用 `CompositeSkill` 组合多个 Skills

```python
from backend.tools.skills import CompositeSkill, load_skill

# ResearchAgent: 组合研究 + 质量检查
research_composite = CompositeSkill([
    load_skill("research_workflow", llm=llm),
    load_skill("content_quality_check", llm=llm)
])

# ContentAgent: 组合生成 + 优化 + 质检
content_composite = CompositeSkill([
    load_skill("content_generation", llm=llm),
    load_skill("content_optimization", llm=llm),
    load_skill("content_quality_check", llm=llm)
])

# FrameworkAgent: 组合分解 + 规划 + 设计
framework_composite = CompositeSkill([
    load_skill("topic_decomposition", llm=llm),
    load_skill("section_planning", llm=llm),
    load_skill("framework_design", llm=llm)
])
```

---

## 📊 改进优先级矩阵

| 改进项 | 优先级 | 复杂度 | 收益 | 实施时间 |
|-------|--------|--------|------|----------|
| 使用 Python Skills | P0 | 中 | 高 | 2-3 天 |
| 启用搜索工具 | P0 | 低 | 高 | 1 天 |
| 质量检查 Skill | P1 | 低 | 中 | 1 天 |
| 主题分解 Skill | P1 | 中 | 中 | 1-2 天 |
| 布局选择 Skill | P1 | 中 | 中 | 1-2 天 |
| 意图识别 Skill | P2 | 高 | 低 | 3-4 天 |
| Skills 组合 | P2 | 中 | 低 | 1-2 天 |

---

## 🎯 实施建议

### 阶段 1：立即可做（1-2 天）

1. **为 ResearchAgent 启用搜索工具**
   ```python
   # 在配置中启用
   agent = ResearchAgent(use_search_tools=True)
   ```

2. **为 ContentAgent 添加质量检查**
   ```python
   from backend.tools.skills import load_skill

   quality_skill = load_skill("content_quality_check", llm=llm)
   result = await quality_skill.execute(content=generated_content)
   ```

3. **使用 Python Skills 替代部分 MD Skills**
   ```python
   # 在 ResearchAgent 中
   from backend.tools.skills import load_skill

   research_skill = load_skill("research_workflow", llm=llm)
   result = await research_skill.execute(topic="AI", num_sources=5)
   ```

### 阶段 2：短期改进（3-5 天）

4. **为 FrameworkAgent 添加主题分解**

5. **为 RendererAgent 添加布局选择**

6. **创建 Skills 组合示例**

### 阶段 3：长期优化（1-2 周）

7. **为 RequirementParserAgent 添加意图识别**

8. **优化 Skills 组合和调度**

9. **添加 Skills 性能监控**

---

## 📝 总结

### 当前状态

| 维度 | 评分 | 说明 |
|------|------|------|
| **Tools 使用** | ⭐⭐ | 只有 ResearchAgent 配置了工具但未启用 |
| **MD Skills** | ⭐⭐⭐⭐ | 7 个 MD Skills 已集成，使用良好 |
| **Python Skills** | ⭐ | 刚创建，尚未集成 |
| **整体集成度** | ⭐⭐⭐ | 基础架构完成，但未充分利用新系统 |

### 核心问题

1. **Python Skills 未集成**：刚创建的可执行工作流程尚未被 Agent 使用
2. **搜索工具未启用**：ResearchAgent 的工具配置存在但默认关闭
3. **质量保证缺失**：内容生成后没有质量检查
4. **Skills 不可组合**：各 Skill 独立使用，没有组合能力

### 改进收益

- ✅ **可执行性**：Python Skills 可直接执行，不依赖 LLM
- ✅ **可测试性**：每个 Skill 可独立测试
- ✅ **可组合性**：CompositeSkill 支持工作流程组合
- ✅ **可扩展性**：新 Skill 易于添加和集成

---

**最后更新**: 2026-02-10
