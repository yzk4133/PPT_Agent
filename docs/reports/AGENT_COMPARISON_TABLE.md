# Agent Tools & Skills 配置对比表

## 📊 当前配置

| Agent | Tools | MD Skills | Python Skills | 主要能力 |
|-------|-------|-----------|--------------|----------|
| **RequirementParserAgent** | ❌ 无 | ❌ 无 | ❌ 无 | 自然语言 → 结构化需求 |
| **FrameworkDesignerAgent** | ❌ 无 | ✅ brand-guidelines<br>✅ domain-name-brainstormer | ❌ 无 | 设计 PPT 框架 |
| **ResearchAgent** | ⚠️ web_search<br>⚠️ fetch_url<br>（未启用） | ✅ lead-research-assistant | ❌ 无 | 收集研究资料 |
| **ContentMaterialAgent** | ❌ 无 | ✅ content-research-writer<br>✅ changelog-generator | ❌ 无 | 生成页面内容 |
| **TemplateRendererAgent** | ❌ 无 | ✅ canvas-design<br>✅ pptx | ❌ 无 | 渲染 XML 输出 |

---

## 🎯 建议配置

| Agent | Tools | MD Skills | Python Skills | 改进点 |
|-------|-------|-----------|--------------|--------|
| **RequirementParserAgent** | ❌ 无 | ➕ intent-recognition | ➕ intent_analysis_skill | 识别用户意图，补充隐含需求 |
| **FrameworkDesignerAgent** | ❌ 无 | ✅ brand-guidelines<br>✅ domain-name-brainstormer | ➕ **framework_design**<br>➕ topic_decomposition<br>➕ section_planning | 使用可执行工作流程 |
| **ResearchAgent** | ✅ web_search<br>✅ fetch_url<br>（启用 MCP） | ✅ lead-research-assistant | ➕ **research_workflow** | 使用可执行工作流程 + 实时搜索 |
| **ContentMaterialAgent** | ❌ 无 | ✅ content-research-writer<br>✅ changelog-generator | ➕ **content_generation**<br>➕ content_optimization<br>➕ content_quality_check | 使用可执行工作流程 + 质量保证 |
| **TemplateRendererAgent** | ❌ 无 | ✅ canvas-design<br>✅ pptx | ➕ layout_selection | 智能布局选择 |

---

## 📈 改进前后对比

### ResearchAgent

**改进前**：
```
用户输入 → LLM 生成研究资料 → 返回结果
         ↑
      仅使用内部知识，无法获取实时信息
```

**改进后**：
```
用户输入 → Python Skill 工作流程 → MCP 搜索工具 → 实时信息
          ├─ 关键词提取            ├─ web_search
          ├─ 并行搜索              └─ fetch_url
          ├─ 信息过滤
          ├─ 内容提取
          └─ 综合分析
```

**收益**：
- ✅ 可执行的工作流程（不依赖 LLM）
- ✅ 实时信息获取
- ✅ 可测试、可调试
- ✅ 结构化输出

---

### ContentMaterialAgent

**改进前**：
```
研究资料 → LLM 生成内容 → 返回结果
          ↑
      无质量检查，可能返回低质量内容
```

**改进后**：
```
研究资料 → Python Skill 工作流程 → 质量检查 → 优化 → 最终内容
          ├─ 需求分析                ├─ 评分    ├─ 迭代优化
          ├─ 要点提取                └─ 通过/失败
          ├─ 结构化
          ├─ 优化表达
          └─ 质量检查
```

**收益**：
- ✅ 5 步工作流程（结构化）
- ✅ 质量检查（自动评分）
- ✅ 迭代优化（自动提升）
- ✅ 用户偏好适配

---

### FrameworkDesignerAgent

**改进前**：
```
需求 → LLM 生成完整框架 → 返回结果
       ↑
    一次性生成，缺乏模块化
```

**改进后**：
```
需求 → Python Skill 工作流程 → 框架设计
      ├─ 主题分解               ├─ 主标题
      ├─ 章节规划               ├─ 章节划分
      ├─ 结构设计               ├─ 页面分配
      └─ 流程优化               └─ 逻辑流程
```

**收益**：
- ✅ 模块化设计（可复用）
- ✅ 主题分解（系统化）
- ✅ 流程优化（逻辑性）
- ✅ 可组合子 Skills

---

## 🔧 实施步骤

### Step 1: 集成 Python Skills（立即）

```python
# backend/agents/core/research/research_agent.py

from backend.tools.skills import load_skill

class ResearchAgent(BaseToolAgent):
    def __init__(
        self,
        model=None,
        use_python_skill: bool = True,  # 新增参数
        **kwargs
    ):
        super().__init__(model=model, **kwargs)

        # 加载 Python Skill
        if use_python_skill:
            self.research_workflow = load_skill(
                "research_workflow",
                llm=model
            )
            # 注入搜索工具
            self.research_workflow.search_tool = self._get_search_tool()

    async def execute_task(self, state):
        # 使用 Python Skill
        topic = state["structured_requirements"]["ppt_topic"]
        result = await self.research_workflow.execute(
            topic=topic,
            num_sources=5,
            depth="medium"
        )

        state["research_results"] = result["data"]
        return state
```

### Step 2: 启用 MCP Tools（今天）

```python
# backend/agents/core/research/research_agent.py

class ResearchAgent(BaseToolAgent):
    def __init__(
        self,
        use_mcp_tools: bool = True,  # 改为 True
        **kwargs
    ):
        super().__init__(
            use_search_tools=use_mcp_tools,  # 启用工具
            **kwargs
        )
```

### Step 3: 添加质量检查（明天）

```python
# backend/agents/core/generation/content_agent.py

from backend.tools.skills import load_skill

class ContentMaterialAgent(BaseAgent):
    def __init__(self, model=None, enable_quality_check: bool = True, **kwargs):
        super().__init__(model=model, **kwargs)

        # 加载质量检查 Skill
        if enable_quality_check:
            self.quality_check = load_skill("content_quality_check", llm=model)

    async def generate_content_for_page(self, page, research_results):
        # 生成内容
        content = await self._generate_content(page, research_results)

        # 质量检查
        quality = await self.quality_check.execute(content=content)

        if not quality["data"]["passed"]:
            logger.warning(f"Quality score: {quality['data']['score']}, optimizing...")
            content = await self._optimize_content(content, quality["data"]["checks"])

        return content
```

---

## 📊 预期效果

### 改进前

| 指标 | 现状 |
|------|------|
| Tools 使用率 | 0%（未启用） |
| Python Skills 集成 | 0% |
| 工作流程可执行性 | 低（依赖 LLM） |
| 质量保证 | 无 |
| 实时信息获取 | 无 |

### 改进后

| 指标 | 目标 |
|------|------|
| Tools 使用率 | 100%（ResearchAgent + MCP） |
| Python Skills 集成 | 60%（3/5 Agents） |
| 工作流程可执行性 | 高（独立于 LLM） |
| 质量保证 | 有（自动评分 + 优化） |
| 实时信息获取 | 有（MCP 搜索工具） |

---

## 🎯 关键收益

### 1. 可执行性

**之前**：
```python
# 只能作为提示词
prompt = skill_content + user_input
result = llm.invoke(prompt)
```

**之后**：
```python
# 直接执行，返回结构化结果
result = await skill.execute(param1="value1")
data = result["data"]  # 字典格式
```

### 2. 可测试性

**之前**：
```python
# 无法独立测试
# 必须通过 LLM 调用
```

**之后**：
```python
# 单元测试
async def test_research_workflow():
    skill = load_skill("research_workflow", llm=mock_llm)
    result = await skill.execute(topic="AI", num_sources=3)
    assert result["success"] is True
    assert len(result["data"]["sources"]) == 3
```

### 3. 可组合性

**之前**：
```python
# Skills 独立使用
result1 = await skill1.execute()
result2 = await skill2.execute(result1)
```

**之后**：
```python
# 使用 CompositeSkill 组合
composite = CompositeSkill([skill1, skill2, skill3])
result = await composite.execute(topic="AI")
```

---

**最后更新**: 2026-02-10
