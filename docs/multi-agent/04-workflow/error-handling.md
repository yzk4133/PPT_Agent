# 错误处理详解

## 📋 概述

本文档详细说明系统中的错误处理机制和降级策略。

## 🛡️ 错误处理层次

### 1. Agent 级别错误处理

每个 Agent 都实现了错误捕获和降级机制：

```python
try:
    # 使用 LLM 处理
    result = await self.chain.ainvoke(input_data)
except Exception as e:
    logger.warning(f"LLM failed: {e}, using fallback")
    return self._fallback_method(input_data)
```

### 2. 节点级别错误处理

LangGraph 节点中的错误处理：

```python
async def run_node(self, state: PPTGenerationState) -> PPTGenerationState:
    try:
        # 节点逻辑
        result = await self.process(state)
        state.update(result)
        return state
    except Exception as e:
        state["error"] = str(e)
        state["current_stage"] = "failed"
        return state
```

### 3. 工作流级别错误处理

主工作流的错误处理：

```python
try:
    final_state = await self.graph.ainvoke(initial_state)
except Exception as e:
    final_state = initial_state
    final_state["error"] = str(e)
    final_state["current_stage"] = "failed"
    return final_state
```

## 🔄 降级策略

### RequirementParserAgent

| 场景 | 主要方法 | 降级方法 |
|------|---------|---------|
| LLM 解析失败 | LLM 解析 | 规则基础解析 |

**降级逻辑**:
```python
def _fallback_parse(self, user_input: str) -> Dict[str, Any]:
    # 简单规则解析
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in user_input)
    return {
        "ppt_topic": user_input[:100],
        "page_num": 10,
        "language": "ZH-CN" if has_chinese else "EN-US",
        ...
    }
```

### FrameworkDesignerAgent

| 场景 | 主要方法 | 降级方法 |
|------|---------|---------|
| LLM 设计失败 | LLM 设计 | 默认框架模板 |

**降级逻辑**:
```python
def _fallback_design(self, requirement: Dict[str, Any]) -> Dict[str, Any]:
    framework_obj = PPTFramework.create_default(
        page_num=requirement.get("page_num", 10),
        topic=requirement.get("ppt_topic", "")
    )
    return framework_obj.to_dict()
```

### ResearchAgent

| 场景 | 主要方法 | 降级方法 |
|------|---------|---------|
| LLM 研究失败 | LLM 生成研究内容 | 返回占位内容 |

**降级逻辑**:
```python
def _fallback_research(self, page: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "page_no": page.get("page_no"),
        "research_content": f"关于「{title}」的研究资料\n\n- 背景知识：[待补充]",
        "status": "fallback"
    }
```

### ContentMaterialAgent

| 场景 | 主要方法 | 降级方法 |
|------|---------|---------|
| LLM 生成失败 | LLM 生成内容 | 根据页面类型生成简单内容 |

**降级逻辑**:
```python
def _fallback_content(self, page: Dict[str, Any], ...) -> Dict[str, Any]:
    if page_type == "cover":
        content_text = f"{title}\n\n汇报人\n日期"
    elif page_type == "directory":
        content_text = "目录：\n- 第一章\n- 第二章"
    ...
    return {"content_text": content_text, ...}
```

### TemplateRendererAgent

| 场景 | 主要方法 | 降级方法 |
|------|---------|---------|
| 缺少数据 | 正常渲染 | 抛出 ValueError |

**不提供降级**: 渲染阶段必须要有完整的框架和内容数据。

## 🔐 输入验证

### 状态验证

```python
def validate_state_for_stage(state, stage) -> tuple[bool, List[str]]:
    errors = []

    if stage == "framework_design":
        if not state.get("structured_requirements"):
            errors.append("缺少 structured_requirements")
    ...
```

### 字段验证

```python
# 验证必需字段
if not requirement.get("ppt_topic"):
    raise ValueError("缺少 ppt_topic")

# 验证数值范围
page_num = requirement.get("page_num", 0)
if page_num < 1 or page_num > 100:
    page_num = 10  # 使用默认值
```

## 📊 错误传播

### 错误信息流向

```
Agent 异常
    │
    ├─► 捕获并记录日志
    ├─► 设置降级状态
    └─► 返回降级结果
            │
            ▼
    节点接收降级结果
            │
            ├─► 更新状态
            └─► 传递到下一节点
```

### 错误状态结构

```python
{
    "error": str,           # 错误消息
    "current_stage": str,   # 失败的阶段
    "progress": int,        # 失败时的进度
    ...
}
```

## 🔄 重试机制

### PagePipeline 重试

```python
class PagePipeline:
    def __init__(self, max_retries: int = 2, retry_delay: float = 1.0):
        ...

    async def _process_page_with_retry(self, page, executor_func, ...):
        for attempt in range(self.max_retries + 1):
            try:
                return await executor_func(page)
            except Exception as e:
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise  # 最后一次尝试失败，抛出异常
```

### 重试配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_retries` | 2 | 最大重试次数 |
| `retry_delay` | 1.0秒 | 重试延迟 |

## 🛠️ 错误恢复

### 部分成功处理

页面流水线支持部分成功：

```python
results = await asyncio.gather(*tasks, return_exceptions=True)

successful_results = []
failed_pages = []

for i, result in enumerate(results):
    if isinstance(result, Exception):
        failed_pages.append((pages[i], result))
    else:
        successful_results.append(result)

# 返回成功的结果，失败的不会阻止整体流程
return successful_results
```

### 状态一致性

即使部分失败，状态也保持一致：

```python
# 即使某些页面研究失败，仍保存成功的页面
state["research_results"] = successful_results  # 不包含失败的
```

## 📝 错误日志

### 日志级别

| 级别 | 用途 | 示例 |
|------|------|------|
| `DEBUG` | 详细调试信息 | "Processing page 3, attempt 2" |
| `INFO` | 正常流程信息 | "Research completed: 5 pages" |
| `WARNING` | 降级触发 | "LLM parsing failed, using fallback" |
| `ERROR` | 错误发生 | "Page 3 research failed: ..." |

### 日志格式

```python
logger.info(f"[{AgentName}] Message: {details}")
logger.warning(f"[{AgentName}] Warning: {warning}")
logger.error(f"[{AgentName}] Error: {error}", exc_info=True)
```

## 🔗 相关文档

- [state-flow.md](state-flow.md): 状态流转
- [performance.md](performance.md): 性能优化
- [../03-core-agents/](../03-core-agents/): 各 Agent 的错误处理
