# revision_handler.py 详解

> 修订处理器 - 处理用户对已生成 PPT 的修改请求

---

## 目录

1. [概述](#概述)
2. [核心概念](#核心概念)
3. [数据结构](#数据结构)
4. [RevisionHandler 类](#revisionhandler-类)
5. [修订类型详解](#修订类型详解)
6. [使用示例](#使用示例)
7. [最佳实践](#最佳实践)

---

## 概述

### 作用

`revision_handler.py` 处理用户对已生成 PPT 的修改请求，支持局部修改而不是重新生成整个 PPT。

### 为什么需要

- ❌ **没有它**：用户不满意只能从头生成，浪费时间
- ✅ **有它**：可以修改特定页面或内容，快速迭代

### 形象比喻

就像文档编辑模式：
- ❌ 没有修订：改一个错别字要重写整篇文章
- ✅ 有修订：直接定位到那一行修改

### 应用场景

| 场景 | 修改类型 | 示例 |
|------|----------|------|
| 内容不准确 | content | "把第3页的数据改得更准确" |
| 风格不合适 | style | "把整体风格改得更正式" |
| 结构不合理 | structure | "在第5页后增加一页总结" |
| 资料不足 | research | "为第7页补充更多研究资料" |

---

## 核心概念

### 1. 修订请求（RevisionRequest）

定义用户想要修改的类型、范围和指令：

```python
@dataclass
class RevisionRequest:
    type: Literal["content", "style", "structure", "research"]
    target: Literal["page_index", "all", "section"]
    instructions: str
    page_indices: Optional[List[int]] = None
    section_name: Optional[str] = None
```

### 2. 修订处理器（RevisionHandler）

解析请求并应用修改：

- 路由到对应的处理方法
- 使用 LLM 执行修订
- 更新状态中的内容
- 记录修订历史

### 3. 修订历史

跟踪所有修改操作，用于审计和回滚：

```python
state["revision_history"] = [
    {
        "timestamp": "2024-01-01T10:00:00",
        "type": "content",
        "instructions": "Make the content more concise",
        "target": "page_index",
    },
    # ...
]
```

---

## 数据结构

### RevisionRequest

```python
@dataclass
class RevisionRequest:
    """
    Revision request data structure

    Attributes:
        type: Revision type (content/style/structure/research)
        target: Target scope (page_index/all/section)
        instructions: User instructions
        page_indices: Specific page indices to revise (for targeted revisions)
        section_name: Section name (for section-based revisions)
    """
    type: Literal["content", "style", "structure", "research"]
    target: Literal["page_index", "all", "section"]
    instructions: str
    page_indices: Optional[List[int]] = None
    section_name: Optional[str] = None
```

---

## RevisionHandler 类

### 初始化

```python
def __init__(self, model: Optional[ChatOpenAI] = None):
    """
    Initialize revision handler

    Args:
        model: LLM model for content revision
    """
    # 如果没有提供模型，使用默认配置创建
    if self.model is None:
        self.model = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7,  # 较高的温度以获得更多样化的修订
        )
```

### 核心方法

#### handle_revision_request()

```python
async def handle_revision_request(
    self,
    state: PPTGenerationState,
    revision_request: Dict[str, Any],
) -> PPTGenerationState:
    """
    Handle a revision request（主入口）

    Args:
        state: Current state
        revision_request: Revision request dictionary

    Returns:
        Updated state with revisions applied
    """
    # 1. 解析请求
    request = self._parse_revision_request(revision_request)

    # 2. 记录修订历史
    if "revision_history" not in state:
        state["revision_history"] = []

    state["revision_history"].append({
        "timestamp": datetime.now().isoformat(),
        "type": request.type,
        "instructions": request.instructions,
        "target": request.target,
    })

    # 3. 路由到具体的处理方法
    if request.type == "content":
        return await self._revise_content(state, request)
    elif request.type == "style":
        return await self._revise_style(state, request)
    elif request.type == "structure":
        return await self._revise_structure(state, request)
    elif request.type == "research":
        return await self._revise_research(state, request)
```

---

## 修订类型详解

### 1. 内容修订（content）

修改特定页面的文本内容。

```python
async def _revise_content(
    self,
    state: PPTGenerationState,
    request: RevisionRequest,
) -> PPTGenerationState:
    """Revise content based on user feedback"""
    logger.info("[RevisionHandler] Revising content")

    content_materials = state.get("content_materials", [])

    if not content_materials:
        logger.warning("[RevisionHandler] No content materials to revise")
        return state

    # 确定要修订哪些页面
    if request.target == "all":
        indices = range(len(content_materials))
    elif request.page_indices:
        indices = request.page_indices
    else:
        indices = []

    # 逐页修订
    for idx in indices:
        if idx >= len(content_materials):
            continue

        material = content_materials[idx]
        original_content = material.get("content", "")

        # 构建 LLM 提示
        system_prompt = """You are a content revision expert. Revise content based on user feedback."""

        user_prompt = f"""Original Content:
{original_content}

User Revision Instructions:
{request.instructions}

Please provide revised content that addresses the user's feedback. Return only the revised content."""

        try:
            # 调用 LLM
            response = await self.model.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ])

            # 更新材料
            content_materials[idx] = {
                **material,
                "content": response.content,
                "revised": True,
                "revision_note": request.instructions,
            }

            logger.debug(f"[RevisionHandler] Revised content for page {idx}")

        except Exception as e:
            logger.error(f"[RevisionHandler] Error revising page {idx}: {e}")

    state["content_materials"] = content_materials
    return state
```

**示例**：

```python
revision_request = {
    "type": "content",
    "target": "page_index",
    "page_indices": [2, 3],
    "instructions": "把这两页的内容改得更简洁一些"
}

state = await revision_handler.handle_revision_request(state, revision_request)
```

### 2. 风格修订（style）

修改内容的风格、语气、格式等。

```python
async def _revise_style(
    self,
    state: PPTGenerationState,
    request: RevisionRequest,
) -> PPTGenerationState:
    """Revise style/tone of content"""
    logger.info("[RevisionHandler] Revising style")

    # 与内容修订类似，但提示词不同
    # 重点在于风格、语气、用词的调整

    # 简化实现：委托给内容修订
    return await self._revise_content(state, request)
```

**示例**：

```python
revision_request = {
    "type": "style",
    "target": "all",
    "instructions": "把整体风格改得更正式、更学术化"
}
```

### 3. 结构修订（structure）

修改 PPT 的组织结构（增加、删除、重排页面）。

```python
async def _revise_structure(
    self,
    state: PPTGenerationState,
    request: RevisionRequest,
) -> PPTGenerationState:
    """Revise PPT structure"""
    logger.info("[RevisionHandler] Revising structure")

    framework = state.get("ppt_framework", {})
    pages = framework.get("ppt_framework", [])

    # 解析修订指令中的结构变化
    # 这可能涉及：
    # 1. 重新生成框架
    # 2. 增删页面
    # 3. 调整页面顺序

    # 标记需要重新设计框架
    state["needs_framework_revision"] = True
    state["framework_revision_instructions"] = request.instructions

    return state
```

**示例**：

```python
revision_request = {
    "type": "structure",
    "target": "all",
    "instructions": "在第5页后增加一页总结，删除第8页"
}
```

### 4. 研究修订（research）

为特定页面补充研究资料。

```python
async def _revise_research(
    self,
    state: PPTGenerationState,
    request: RevisionRequest,
) -> PPTGenerationState:
    """Revise research results"""
    logger.info("[RevisionHandler] Revising research")

    # 标记需要额外研究
    state["needs_additional_research"] = True
    state["research_revision_instructions"] = request.instructions

    return state
```

**示例**：

```python
revision_request = {
    "type": "research",
    "target": "page_index",
    "page_indices": [7],
    "instructions": "为第7页补充更多关于人工智能伦理的研究资料"
}
```

---

## 使用示例

### 1. 基本使用

```python
from backend.agents_langchain.coordinator.revision_handler import (
    RevisionHandler,
    create_revision_handler,
)

# 创建修订处理器
handler = create_revision_handler()

# 定义修订请求
revision_request = {
    "type": "content",
    "target": "page_index",
    "page_indices": [2],
    "instructions": "把第3页的内容改得更简洁一些"
}

# 应用修订
state = await handler.handle_revision_request(state, revision_request)
```

### 2. 批量修订

```python
# 修订多个页面
revision_request = {
    "type": "content",
    "target": "page_index",
    "page_indices": [0, 1, 2, 3],  # 修订前4页
    "instructions": "把这些页面的内容都改得更正式一些"
}

state = await handler.handle_revision_request(state, revision_request)
```

### 3. 全局修订

```python
# 修订所有页面
revision_request = {
    "type": "style",
    "target": "all",
    "instructions": "把整体风格改得更学术化"
}

state = await handler.handle_revision_request(state, revision_request)
```

### 4. 增量修订

```python
# 直接提供新内容（不使用 LLM）
new_content = """
这是修改后的内容：
1. 第一点
2. 第二点
3. 第三点
"""

state = await handler.apply_incremental_revision(
    state=state,
    page_index=2,
    new_content=new_content
)
```

### 5. 查看修订历史

```python
# 获取修订摘要
summary = handler.get_revision_summary(state)

print(f"总修订次数: {summary['total_revisions']}")
print(f"最新修订: {summary['latest_revision']}")
print(f"修订类型: {summary['revision_types']}")

# 输出:
# 总修订次数: 3
# 最新修订: {'timestamp': '2024-01-01T10:00:00', 'type': 'content', ...}
# 修订类型: ['content', 'style', 'content']
```

---

## 最佳实践

### 1. 验证修订请求

✅ **建议**：在处理前验证请求的合法性

```python
def _parse_revision_request(self, request: Dict[str, Any]) -> RevisionRequest:
    """Parse and validate revision request"""
    revision_type = request.get("type", "content")
    target = request.get("target", "all")

    # 标准化类型
    if revision_type not in ["content", "style", "structure", "research"]:
        logger.warning(f"Unknown revision type: {revision_type}, defaulting to content")
        revision_type = "content"

    # 标准化目标
    if target not in ["page_index", "all", "section"]:
        logger.warning(f"Unknown target: {target}, defaulting to all")
        target = "all"

    return RevisionRequest(
        type=revision_type,
        target=target,
        instructions=request.get("instructions", ""),
        page_indices=request.get("page_indices"),
        section_name=request.get("section_name"),
    )
```

### 2. 处理边界情况

✅ **建议**：处理 page_index 超出范围的情况

```python
for idx in indices:
    if idx >= len(content_materials):
        logger.warning(f"[RevisionHandler] Page index {idx} out of range, skipping")
        continue

    # 正常处理...
```

### 3. 保留原始内容

✅ **建议**：修订时保留原始内容，方便回滚

```python
content_materials[idx] = {
    **material,
    "content": response.content,           # 新内容
    "original_content": material.get("content"),  # 保留原内容
    "revised": True,
    "revision_note": request.instructions,
}
```

### 4. 记录修订历史

✅ **建议**：详细记录每次修订，便于审计

```python
state["revision_history"].append({
    "timestamp": datetime.now().isoformat(),
    "type": request.type,
    "instructions": request.instructions,
    "target": request.target,
    "page_indices": request.page_indices,
    "success": True,
})
```

### 5. 错误恢复

✅ **建议**：修订失败时保留原内容

```python
try:
    response = await self.model.ainvoke([...])
    content_materials[idx] = {...}  # 更新
except Exception as e:
    logger.error(f"[RevisionHandler] Error revising page {idx}: {e}")
    # 不更新内容，保留原样
    # 可以标记为失败
    content_materials[idx] = {
        **material,
        "revision_failed": True,
        "revision_error": str(e),
    }
```

---

## 高级用法

### 1. 自定义修订策略

```python
class CustomRevisionHandler(RevisionHandler):
    """自定义修订处理器"""

    async def _revise_content(self, state, request):
        # 自定义修订逻辑
        # 例如：使用不同的提示词模板
        # 例如：应用多次修订
        pass
```

### 2. 批量处理修订请求

```python
async def apply_multiple_revisions(state, requests):
    """应用多个修订请求"""
    handler = create_revision_handler()

    for revision_request in requests:
        state = await handler.handle_revision_request(state, revision_request)

    return state

# 使用
requests = [
    {"type": "content", "target": "page_index", "page_indices": [0], "instructions": "..."},
    {"type": "style", "target": "all", "instructions": "..."},
]

state = await apply_multiple_revisions(state, requests)
```

### 3. 条件修订

```python
# 根据内容质量决定是否修订
def should_revise(content):
    # 简单的启发式规则
    return len(content) < 50 or "TODO" in content

for idx, material in enumerate(content_materials):
    if should_revise(material.get("content", "")):
        # 自动触发修订
        state = await handler.handle_revision_request(state, {
            "type": "content",
            "target": "page_index",
            "page_indices": [idx],
            "instructions": "扩展此内容"
        })
```

---

## 常见问题

### Q1: 如何处理修订失败？

A: 修订处理器会捕获异常并记录日志，但不会中断整个流程：

```python
try:
    response = await self.model.ainvoke([...])
except Exception as e:
    logger.error(f"Error revising page {idx}: {e}")
    # 保留原内容，继续处理其他页面
```

### Q2: 如何回滚修订？

A: 使用保留的原始内容：

```python
# 回滚特定页面
def rollback_page(state, page_index):
    content_materials = state.get("content_materials", [])
    if page_index < len(content_materials):
        material = content_materials[page_index]
        if "original_content" in material:
            material["content"] = material["original_content"]
            material["revised"] = False
    return state
```

### Q3: 如何提高修订质量？

A: 优化 LLM 提示词：

```python
system_prompt = """You are an expert content reviser.

Guidelines:
- Maintain the original structure
- Improve clarity and conciseness
- Preserve key information
- Use professional language

User feedback will be provided below."""

user_prompt = f"""Original Content:
{original_content}

User Revision Instructions:
{request.instructions}

Revised Content:"""
```

### Q4: 支持撤销修订吗？

A: 通过修订历史实现撤销：

```python
def undo_last_revision(state):
    """撤销最后一次修订"""
    revision_history = state.get("revision_history", [])

    if not revision_history:
        return state

    last_revision = revision_history.pop()

    # 根据修订类型执行相应的撤销逻辑
    # 注意：完全撤销可能需要保存完整的状态快照
    return state
```

---

## 相关文档

- [设计指南](./design-guide.md) - Coordinator 层设计
- [实施指南](./implementation-guide.md) - 如何实现 revision_handler
- [ProgressTracker 文档](./progress_tracker.py.md) - 进度追踪详解
