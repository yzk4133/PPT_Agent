# 研究 Agent 详解

> **核心个性**：为单个页面收集研究资料，支持并发调用

---

## 目录

1. [职责与能力](#职责与能力)
2. [核心个性特征](#核心个性特征)
3. [输入输出格式](#输入输出格式)
4. [关键实现细节](#关键实现细节)
5. [降级策略](#降级策略)
6. [使用示例](#使用示例)
7. [常见问题](#常见问题)

---

## 职责与能力

### 核心职责

研究 Agent 是 PPT 生成流程中的**可选步骤**，负责为需要研究的页面收集背景资料、关键数据和相关案例。

**为什么需要研究？**
- ❌ 没有研究：内容生成完全依赖 LLM 的训练数据，可能过时或不准确
- ✅ 有研究：为内容生成提供准确、最新的背景信息

### 关键能力

| 能力 | 说明 | 重要性 |
|------|------|--------|
| **页面级研究** | 为单个页面收集相关资料 | ⭐⭐⭐⭐⭐ |
| **结构化输出** | 生成背景、数据、案例、引用等结构化信息 | ⭐⭐⭐⭐⭐ |
| **降级处理** | 失败时返回占位内容 | ⭐⭐⭐⭐ |
| **并发调用** | 支持被 PagePipeline 并发调用 | ⭐⭐⭐⭐ |

---

## 核心个性特征

### 1. 特殊的工作模式：被调用而非主动执行

**与其他 Agent 的区别**：

```python
# 典型的 Agent：使用 run_node()
class TypicalAgent(BaseAgent):
    async def run_node(self, state: PPTGenerationState) -> PPTGenerationState:
        """LangGraph 节点函数"""
        # 主动处理整个流程
        result = await self._process_all()
        state["output"] = result
        return state

# 研究 Agent：被 PagePipeline 调用
class ResearchAgent(BaseAgent):
    async def research_page(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """研究单个页面"""
        # 只处理一个页面
        pass
    # 注意：不直接使用 run_node()
```

**为什么这样设计？**

```
┌─────────────────────────────────────────────────────────┐
│  PagePipeline                                           │
│                                                         │
│  pages_to_research = [page1, page2, page3, ...]        │
│                                                         │
│  # 并发调用研究 Agent                                    │
│  tasks = [                                               │
│      research_agent.research_page(page1),               │
│      research_agent.research_page(page2),               │
│      research_agent.research_page(page3),               │
│  ]                                                      │
│                                                         │
│  results = await asyncio.gather(*tasks)                 │
└─────────────────────────────────────────────────────────┘
```

| 对比项 | run_node 模式 | research_page 模式 |
|--------|---------------|-------------------|
| **控制方式** | Agent 控制流程 | PagePipeline 控制 |
| **并发方式** | Agent 内部实现 | PagePipeline 实现 |
| **适用场景** | 串行处理、单次调用 | 并行处理、批量调用 |
| **灵活性** | 较低（节点结构固定） | 高（可自定义并发数） |

---

### 2. 页面级研究：每次只处理一页

**设计理念**：

```
❌ 错误方式：一次研究所有页面
async def research_all_pages(self, pages: List[Dict]) -> List[Dict]:
    prompt = f"请研究这些页面：{pages}"  # 太复杂！
    # LLM 难以一次性处理大量信息
    pass

✅ 正确方式：每次研究一个页面
async def research_page(self, page: Dict) -> Dict:
    prompt = f"请研究这个页面：{page}"  # 简单明确
    # LLM 可以专注处理单个页面
    pass
```

**为什么一次只研究一页？**

1. **专注度高**：LLM 的注意力集中在单个主题
2. **质量更好**：避免信息过载导致的输出质量下降
3. **易于控制**：可以针对不同页面调整研究策略
4. **容错性好**：单个页面失败不影响其他页面

---

### 3. 结构化研究内容

**输出格式**：

```python
{
    "page_no": int,                    # 页码
    "title": str,                      # 页面标题
    "research_content": str,           # 研究内容（主要输出）
    "keywords": List[str],             # 关键词
    "status": str                      # completed|fallback
}
```

**研究内容的结构**：

```markdown
# research_content 包含的内容

## 1. 背景知识
- 提供相关的背景信息
- 解释关键概念
- 说明发展趋势

## 2. 关键数据
- 具体的统计数据
- 重要的数字指标
- 调研结果

## 3. 相关案例
- 成功案例
- 失败教训
- 行业标杆

## 4. 参考来源
- 数据来源
- 参考链接
- 引用标注
```

**为什么结构化？**

```python
# 内容生成 Agent 可以直接使用结构化的研究结果

def _find_relevant_research(self, page, research_results):
    """查找相关研究"""
    for research in research_results:
        if research["page_no"] == page["page_no"]:
            # 直接使用研究内容
            return research["research_content"]
    return "研究资料：无"
```

---

### 4. Temperature = 0.3：准确性与创造性的平衡

**为什么使用 0.3？**

| Temperature | 特点 | 适用场景 | 研究 Agent |
|------------|------|---------|-----------|
| 0.0 | 完全确定性，每次输出相同 | 结构化数据提取 | ❌ 太刻板 |
| **0.3** | **准确性为主，少量创造性** | **研究资料收集** | ✅ **合适** |
| 0.7 | 平衡准确性和创造性 | 内容生成 | ❌ 太随意 |
| 1.0 | 高度创造性，随机性强 | 创意写作 | ❌ 不可靠 |

**实际效果对比**：

```python
# Temperature = 0.0 (太刻板)
research_content = """
人工智能：人工智能是计算机科学的一个分支。
背景：无数据。
案例：无案例。
"""

# Temperature = 0.3 (合适)
research_content = """
人工智能（Artificial Intelligence，AI）是计算机科学的一个重要分支，
致力于开发能够模拟人类智能的系统。

背景知识：
- 1956年，达特茅斯会议首次提出"人工智能"概念
- 经历了三次发展浪潮：符号主义、连接主义、深度学习

关键数据：
- 2023年全球AI市场规模达到1965亿美元
- 预计2030年将达到1.8万亿美元

相关案例：
- ChatGPT：OpenAI开发的对话式AI系统
- AlphaGo：DeepMind开发的围棋AI
"""

# Temperature = 0.7 (太随意)
research_content = """
人工智能就像一场革命！它正在改变我们的世界，就像魔法一样！
想象一下，未来我们可能都会有AI助手...
"""
```

---

## 输入输出格式

### 输入

```python
page: Dict[str, Any]  # 单个页面定义
```

**示例**：

```python
{
    "page_no": 3,
    "title": "AI发展历史",
    "core_content": "介绍人工智能的发展历程",
    "is_need_research": True,
    "keywords": ["AI", "历史", "发展"],
    "page_type": "content",
    "estimated_word_count": 200
}
```

### 输出

```python
{
    "page_no": int,                    # 页码
    "title": str,                      # 页面标题
    "research_content": str,           # 研究内容
    "keywords": List[str],             # 关键词
    "status": str                      # completed|fallback
}
```

---

## 关键实现细节

### 1. 主流程

```python
async def research_page(
    self,
    page: Dict[str, Any]
) -> Dict[str, Any]:
    """
    研究单个页面

    流程：
    1. 检查是否需要研究
    2. 构建 LLM 提示词
    3. 调用 LLM 生成研究内容
    4. 验证输出
    5. 失败时使用降级策略
    """
    # 1. 检查是否需要研究
    if not page.get("is_need_research", False):
        return self._skip_research(page)

    # 2. 构建提示词
    prompt = self._build_research_prompt(page)

    # 3. 调用 LLM
    try:
        research_content = await self._invoke_with_retry(prompt)

        # 4. 返回结果
        return {
            "page_no": page["page_no"],
            "title": page["title"],
            "research_content": research_content,
            "keywords": page.get("keywords", []),
            "status": "completed"
        }

    except Exception as e:
        # 5. 降级处理
        self.logger.warning(f"Research failed for page {page['page_no']}: {e}")
        return self._fallback_research(page)
```

---

### 2. LLM 提示词设计

```python
def _build_research_prompt(self, page: Dict[str, Any]) -> str:
    """构建研究提示词"""

    return f"""
你是一名专业的研究助理。

你的任务是为PPT页面收集相关的研究资料和背景信息。

页面信息：
- 页码：{page['page_no']}
- 标题：{page['title']}
- 内容描述：{page['core_content']}
- 关键词：{', '.join(page.get('keywords', []))}

请为这个页面生成相关的研究资料，包括：

1. 背景知识
   - 相关的概念定义
   - 发展历程
   - 当前趋势

2. 关键数据或事实
   - 具体的统计数据
   - 重要的数字指标
   - 调研结果

3. 相关案例或例子
   - 成功案例
   - 典型应用
   - 行业标杆

4. 参考来源
   - 数据来源
   - 参考链接（如有）

输出要求：
- 使用要点列表格式
- 保持简洁但信息丰富
- 确保信息的准确性和相关性
- 如果有具体数据，注明来源或说明是"示例数据"
"""
```

---

### 3. 跳过研究

```python
def _skip_research(self, page: Dict[str, Any]) -> Dict[str, Any]:
    """跳过研究（当页面不需要研究时）"""

    return {
        "page_no": page["page_no"],
        "title": page["title"],
        "research_content": "此页面不需要研究资料",
        "keywords": page.get("keywords", []),
        "status": "skipped"
    }
```

---

## 降级策略

### 什么时候触发降级？

```
LLM 研究失败 ↓
│
├─ 网络错误
├─ API 限流
├─ 超时
└─ 返回内容为空

触发降级策略 → 返回占位内容
```

### 降级实现

```python
def _fallback_research(self, page: Dict[str, Any]) -> Dict[str, Any]:
    """
    降级研究：返回占位内容
    """
    title = page.get("title", "未知标题")

    placeholder_content = f"""
关于「{title}」的研究资料

**背景知识**
[待补充 - 研究功能暂时不可用]

**关键数据**
[待补充 - 研究功能暂时不可用]

**相关案例**
[待补充 - 研究功能暂时不可用]

**参考来源**
[待补充 - 研究功能暂时不可用]
"""

    return {
        "page_no": page["page_no"],
        "title": page["title"],
        "research_content": placeholder_content.strip(),
        "keywords": page.get("keywords", []),
        "status": "fallback"
    }
```

**降级的影响**：

| 影响 | 说明 |
|------|------|
| ✅ 不会中断流程 | 内容生成 Agent 可以继续工作 |
| ✅ 提供占位符 | 明确告知用户研究失败 |
| ❌ 内容质量下降 | 没有研究资料，内容可能不够准确 |

---

## 使用示例

### 基本使用

```python
from backend.agents_langchain.core.research.research_agent import (
    ResearchAgent,
    create_research_agent
)

# 创建 Agent
agent = create_research_agent()

# 研究单个页面
page = {
    "page_no": 3,
    "title": "AI发展历史",
    "core_content": "介绍人工智能的发展历程",
    "is_need_research": True,
    "keywords": ["AI", "历史", "发展"],
    "page_type": "content"
}

result = await agent.research_page(page)

# 查看结果
print(f"第 {result['page_no']} 页研究完成")
print(f"状态: {result['status']}")
print(f"研究内容:\n{result['research_content']}")
```

### 与 PagePipeline 配合使用

```python
from backend.agents_langchain.coordinator.page_pipeline import PagePipeline

# 创建 PagePipeline
pipeline = PagePipeline(max_concurrent=5)

# 执行并行研究
state = {
    "ppt_framework": {
        "total_page": 10,
        "ppt_framework": [page1, page2, page3, ...]
    },
    "research_results": []
}

# PagePipeline 会自动并发调用 research_page
state = await pipeline.execute_research_pipeline(
    state=state,
    research_agent=agent
)

# 查看结果
print(f"研究了 {len(state['research_results'])} 个页面")
```

---

## 常见问题

### Q1: 为什么研究 Agent 不使用 run_node()？

A: 因为研究任务需要高度并发控制，由 PagePipeline 统一管理更合适。

```python
# ❌ 如果使用 run_node()
async def run_node(self, state):
    # 难以精细控制并发数
    # 难以处理部分失败的情况
    # 所有研究任务在一个节点中完成
    pass

# ✅ 使用 research_page()
async def research_page(self, page):
    # PagePipeline 可以控制并发数
    # 可以处理部分失败
    # 每个页面独立处理
    pass
```

### Q2: 如何判断哪些页面需要研究？

A: 在框架设计阶段，Framework Agent 会根据需求标记需要研究的页面。

```python
# 框架设计 Agent 标记需要研究的页面
if requirement.get("need_research"):
    # 每3页标记一页需要研究
    for i, page in enumerate(pages):
        if i % 3 == 0:  # 第3、6、9页...
            page["is_need_research"] = True
```

### Q3: 研究 Agent 如何与内容生成 Agent 配合？

A: 内容生成 Agent 会查找相关的研究结果。

```python
# 内容生成 Agent 的逻辑
def generate_content_for_page(self, page, research_results):
    # 1. 查找相关研究
    research = self._get_research_for_page(page["page_no"], research_results)

    # 2. 将研究资料加入提示词
    prompt = f"""
    请生成内容：
    页面标题：{page['title']}
    内容描述：{page['core_content']}

    研究资料：
    {research}

    请基于以上信息生成详细内容...
    """

    # 3. 生成内容
    content = await self._invoke_with_retry(prompt)
    return content
```

### Q4: Phase 2 会增加什么功能？

A: 会集成 MCP 搜索工具，实现实时信息检索。

```python
# Phase 2 的研究 Agent
class ResearchAgent(BaseAgent):
    def __init__(self, use_search_tools: bool = False):
        self.use_search_tools = use_search_tools
        if use_search_tools:
            self.search_tool = MCPSearchTool()

    async def research_page(self, page):
        if self.use_search_tools:
            # 使用真实的搜索工具
            search_results = await self.search_tool.search(page['keywords'])
            # 基于搜索结果生成研究内容
        else:
            # 使用 LLM 的知识库
            pass
```

---

## 相关文档

- [Core Agents 设计指南](./README.md) - 通用架构和共性
- [内容生成 Agent](./content_agent.py.md) - 如何使用研究结果
- [PagePipeline](../02-coordinator/page_pipeline.py.md) - 如何并发调用研究 Agent
- [框架设计 Agent](./framework_agent.py.md) - 如何标记需要研究的页面
