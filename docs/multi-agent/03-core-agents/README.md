# Core Agents 设计指南

> 本文档说明如何设计和实现单个 LangChain Agent，包括共性和个性的区分

---

## 目录

1. [Agent 架构概览](#agent-架构概览)
2. [构建 Agent 的考虑因素](#构建-agent-的考虑因素)
3. [通用参数配置](#通用参数配置)
4. [共性能力](#共性能力)
5. [五个 Agent 的个性](#五个-agent-的个性)
6. [实现检查清单](#实现检查清单)

---

## Agent 架构概览

### 什么是 Agent？

在 LangChain 中，Agent 是一个具有特定职责的智能体，能够：

- 🔤 接收输入（用户请求或前一个 Agent 的输出）
- 🧠 使用 LLM 进行推理和决策
- 📤 产生输出（结构化结果或自然语言）
- 🔄 与工作流集成（通过 `run_node` 方法）

### PPT 生成系统的 Agent 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    PPT 生成工作流                            │
│                                                              │
│  用户输入 ──► [需求解析 Agent] ──► [框架设计 Agent]        │
│                  │                   │                        │
│                  ▼                   ▼                        │
│             结构化需求           PPT 框架                      │
│                  │                   │                        │
│                  ▼                   ▼                        │
│             [研究 Agent?] ◄───────┘                        │
│                  │                                           │
│                  ▼                                           │
│          [内容生成 Agent] ◄───────────────────────────────┘   │
│                  │                                           │
│                  ▼                                           │
│          [渲染 Agent] ──► PPT 文件                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 构建 Agent 的考虑因素

### 1. 职责定义（单一职责原则）

**问题**：这个 Agent 负责什么？

| 考虑因素 | 说明 | 示例 |
|----------|------|------|
| **输入** | 接收什么样的数据？ | 用户输入 / 结构化需求 / PPT 框架 |
| **输出** | 产生什么样的结果？ | 结构化字典 / 页面列表 / 文本内容 |
| **转换** | 如何将输入转换为输出？ | 使用 LLM / 规则引擎 / 模板 |
| **验证** | 如何确保输出正确？ | schema 验证 / 逻辑检查 / 降级策略 |

### 2. LLM 配置

**问题**：使用什么样的 LLM？

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| **模型** | 使用哪个模型？ | gpt-4o-mini（性价比高） |
| **Temperature** | 创造性程度？ | 0.0（结构化输出） ~ 0.7（内容生成） |
| **Max Tokens** | 输出长度限制？ | 根据任务需求 |
| **Top P** | 采样参数？ | 1.0（默认） |

### 3. 提示词工程

**问题**：如何让 LLM 理解任务？

```
提示词结构：
┌─────────────────────────────────────┐
│  System Message（系统角色设定）       │
│  - 定义 Agent 的角色                 │
│  - 说明任务目标                      │
│  - 设定行为准则                      │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  Few-Shot Examples（示例）            │
│  - 提供输入输出示例                  │
│  - 展示期望的格式                     │
│  - 说明边界情况                      │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  Task Description（任务描述）         │
│  - 具体的输入数据                    │
│  - 约束条件和要求                    │
│  - 输出格式规范                      │
└─────────────────────────────────────┘
```

### 4. 输出结构

**问题**：如何确保 LLM 输出符合预期？

```python
# 使用 Pydantic 或 TypedDict 定义输出结构
from pydantic import BaseModel

class RequirementOutput(BaseModel):
    ppt_topic: str
    page_num: int
    scene: str
    # ...

# 在 LLM 调用时使用
response = await llm.with_structured_output(RequirementOutput).ainvoke(prompt)
```

### 5. 错误处理

**问题**：如果 LLM 失败了怎么办？

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| **重试** | 自动重试 N 次 | 临时性错误（网络问题） |
| **降级** | 使用规则引擎 | LLM 持续失败 |
| **默认值** | 返回预定义的默认值 | 无法获取有效输出 |
| **异常抛出** | 让调用者处理 | 无法恢复的错误 |

---

## 通用参数配置

### 所有 Agent 的共同参数

```python
class BaseAgent:
    def __init__(
        self,
        # LLM 配置
        model: Optional[ChatOpenAI] = None,         # LLM 模型
        temperature: float = 0.0,                    # 创造性程度

        # 行为配置
        retry_on_failure: bool = True,                # 失败时重试
        max_retries: int = 3,                         # 最大重试次数
        retry_delay: float = 1.0,                      # 重试延迟

        # 日志配置
        log_level: str = "INFO",                       # 日志级别
        log_prompt: bool = False,                     # 是否记录提示词
        log_response: bool = False,                   # 是否记录响应
    ):
        ...
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model` | `ChatOpenAI` | 从环境变量创建 | LLM 模型实例 |
| `temperature` | `float` | `0.0` | 控制输出的随机性（0.0=确定性，1.0=高度随机） |
| `retry_on_failure` | `bool` | `True` | 是否在失败时自动重试 |
| `max_retries` | `int` | `3` | 最大重试次数 |
| `retry_delay` | `float` | `1.0` | 重试之间的等待时间（秒） |
| `log_level` | `str` | `"INFO"` | 日志级别（DEBUG/INFO/WARNING/ERROR） |
| `log_prompt` | `bool` | `False` | 是否将提示词记录到日志（调试用） |
| `log_response` | `bool` | `False` | 是否将 LLM 响应记录到日志（调试用） |

---

## 共性能力

### 1. 基础结构（所有 Agent 都有）

```python
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
import logging

class BaseAgent:
    """Agent 基类"""

    def __init__(self, model: Optional[ChatOpenAI] = None, **kwargs):
        self.model = model or self._create_default_model()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_default_model(self) -> ChatOpenAI:
        """创建默认 LLM 模型"""
        # 实现细节...
        pass

    async def run_node(self, state: PPTGenerationState) -> PPTGenerationState:
        """LangGraph 节点函数（必须实现）"""
        # 实现细节...
        pass
```

### 2. 日志记录

```python
class BaseAgent:
    def _log_start(self, method: str, **kwargs):
        """记录方法开始"""
        self.logger.info(f"[{method}] Starting: {kwargs}")

    def _log_success(self, method: str, **kwargs):
        """记录方法成功"""
        self.logger.info(f"[{method}] Success: {kwargs}")

    def _log_error(self, method: str, error: Exception, **kwargs):
        """记录方法错误"""
        self.logger.error(f"[{method}] Error: {kwargs}", exc_info=error)

    def _log_llm_start(self, prompt: str):
        """记录 LLM 调用开始"""
        if self.log_prompt:
            self.logger.debug(f"[LLM] Prompt:\n{prompt}")

    def _log_llm_end(self, response: str):
        """记录 LLM 调用结束"""
        if self.log_response:
            self.logger.debug(f"[LLM] Response:\n{response}")
```

### 3. 重试机制

```python
class BaseAgent:
    async def _invoke_with_retry(
        self,
        prompt: str,
        **kwargs
    ) -> Any:
        """带重试的 LLM 调用"""
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                self._log_llm_start(prompt)
                response = await self.model.ainvoke(prompt, **kwargs)
                self._log_llm_end(response)
                return response

            except Exception as e:
                last_error = e
                self._log_error("invoke", e, attempt=attempt)

                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise

        # 不应该到达这里
        raise last_error
```

### 4. 降级策略

```python
class BaseAgent:
    async def execute_with_fallback(
        self,
        primary_method: callable,
        fallback_method: callable,
        *args,
        **kwargs
    ) -> Any:
        """执行主方法，失败时使用降级方法"""
        try:
            return await primary_method(*args, **kwargs)
        except Exception as e:
            self.logger.warning(f"Primary method failed: {e}, using fallback")
            return await fallback_method(*args, **kwargs)
```

### 5. 验证和修复

```python
class BaseAgent:
    def validate_output(self, output: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证输出是否符合预期"""
        errors = []

        # 检查必需字段
        required_fields = self._get_required_fields()
        for field in required_fields:
            if field not in output:
                errors.append(f"Missing required field: {field}")

        # 检查字段类型
        field_types = self._get_field_types()
        for field, expected_type in field_types.items():
            if field in output and not isinstance(output[field], expected_type):
                errors.append(f"Field {field} should be {expected_type}")

        return len(errors) == 0, errors

    def fix_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """修复输出中的问题"""
        # 填充缺失字段
        required_fields = self._get_required_fields()
        for field in required_fields:
            if field not in output:
                output[field] = self._get_default_value(field)

        return output
```

### 6. LangGraph 集成

```python
class BaseAgent:
    async def run_node(self, state: PPTGenerationState) -> PPTGenerationState:
        """
        LangGraph 节点函数（必须实现）

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        method_name = self._get_processing_method()

        try:
            # 1. 记录开始
            self._log_start(method_name, stage=self._get_stage_name())

            # 2. 执行处理
            input_data = self._extract_input(state)
            output_data = await self._process(input_data)

            # 3. 验证输出
            is_valid, errors = self.validate_output(output_data)
            if not is_valid:
                self.logger.warning(f"Output validation failed: {errors}")
                output_data = self.fix_output(output_data)

            # 4. 更新状态
            updated_state = self._update_state(state, output_data)

            # 5. 更新进度
            from ..models.state import update_state_progress
            updated_state = update_state_progress(
                updated_state,
                self._get_stage_name(),
                self._get_progress_weight()
            )

            # 6. 记录成功
            self._log_success(method_name)

            return updated_state

        except Exception as e:
            # 错误处理
            self._log_error(method_name, e)
            state["error"] = str(e)
            return state
```

---

## 五个 Agent 的个性

### 对比表

| Agent | 输入 | 输出 | 核心任务 | Temperature | 特殊能力 |
|-------|------|------|----------|-------------|----------|
| **需求解析** | 用户自然语言 | 结构化需求 | 理解用户意图 | 0.0 | 降级解析 |
| **框架设计** | 结构化需求 | PPT 框架 | 设计页面结构 | 0.0 | 自动修复框架 |
| **研究** | 单个页面定义 | 研究结果 | 查找资料 | 0.3 | 并行处理 |
| **内容生成** | 页面定义 + 研究结果 | 页面内容 | 生成文本 | 0.7 | 结合研究结果 |
| **渲染** | 所有页面内容 | PPT 文件 | 生成文件 | 0.0 | 模板应用 |

### 各 Agent 的个性特征

#### 1. 需求解析 Agent

**个性**：理解模糊输入，提取结构化信息

```python
# 特殊能力
class RequirementParserAgent(BaseAgent):
    def _get_default_modules(self, scene: str) -> List[str]:
        """根据场景提供默认模块"""
        # 不同场景有不同的默认模块
        pass

    def _detect_language(self, text: str) -> str:
        """检测语言（中文/英文）"""
        # 自动检测用户输入的语言
        pass

    def _fallback_parse(self, user_input: str) -> Dict[str, Any]:
        """降级解析：不使用 LLM，使用规则"""
        # LLM 失败时的降级策略
        pass
```

#### 2. 框架设计 Agent

**个性**：设计逻辑合理的页面结构

```python
# 特殊能力
class FrameworkDesignerAgent(BaseAgent):
    def _validate_and_fix(self, framework: Dict[str, Any]) -> Dict[str, Any]:
        """验证并修复框架"""
        # - 确保页数正确
        # - 确保页码连续
        # - 确保有封面和目录
        pass

    def _distribute_modules(self, modules: List[str], page_num: int) -> List[Dict]:
        """将核心模块分配到页面"""
        # 合理安排每个模块占用的页数
        pass

    def _mark_research_pages(self, framework: Dict[str, Any], requirement: Dict):
        """标记需要研究的页面"""
        # 根据需求标记哪些页面需要研究
        pass
```

#### 3. 研究 Agent

**个性**：并行研究多个页面

```python
# 特殊能力
class ResearchAgent(BaseAgent):
    async def research_page(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """研究单个页面"""
        # 针对单个页面进行资料查找
        pass

    # 注意：这个 Agent 不直接使用 run_node
    # 而是由 PagePipeline 并发调用 research_page
```

#### 4. 内容生成 Agent

**个性**：结合研究结果，生成高质量内容

```python
# 特殊能力
class ContentMaterialAgent(BaseAgent):
    async def generate_content_for_page(
        self,
        page: Dict[str, Any],
        research_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """为单个页面生成内容（结合研究结果）"""
        # - 查找相关的研究结果
        # - 根据研究结果生成内容
        # - 控制字数在合理范围
        pass

    def _find_relevant_research(
        self,
        page: Dict[str, Any],
        research_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """查找与页面相关的研究结果"""
        # 根据页面标题和关键词匹配相关研究
        pass
```

#### 5. 渲染 Agent

**个性**：应用模板，生成最终文件

```python
# 特殊能力
class TemplateRendererAgent(BaseAgent):
    async def render(self, state: PPTGenerationState) -> Dict[str, Any]:
        """渲染 PPT"""
        # - 选择合适的模板
        # - 填充内容到模板
        # - 生成 .pptx 文件
        # - 返回文件路径
        pass

    def _select_template(self, requirement: Dict) -> str:
        """根据需求选择模板"""
        # 根据场景、风格等选择合适的模板文件
        pass

    def _apply_template(self, template_path: str, content_materials: List[Dict]) -> str:
        """应用模板生成 PPT"""
        # 使用 python-pptx 库生成文件
        pass
```

---

## 实现检查清单

### 新建 Agent 时需要实现的内容

#### 必须实现

- [ ] `__init__()` - 初始化方法
- [ ] `_create_default_model()` - 创建默认 LLM
- [ ] `run_node()` - LangGraph 节点函数
- [ ] `_process()` - 核心处理逻辑
- [ ] `_extract_input()` - 从状态提取输入
- [ ] `_update_state()` - 更新状态

#### 建议实现

- [ ] `validate_output()` - 验证输出
- [ ] `fix_output()` - 修复输出
- [ ] `execute_with_fallback()` - 降级策略
- [ ] 日志记录方法

#### 文档必须包含

- [ ] 职责说明
- [ ] 输入输出格式
- [ ] 参数说明
- [ ] 使用示例
- [ ] 错误处理
- [ ] 相关文件链接

---

## 总结

### 共性与个性

```python
# 共性：所有 Agent 都有
class BaseAgent:
    model: ChatOpenAI           # LLM
    logger: logging.Logger       # 日志
    retry_on_failure: bool       # 重试
    run_node()                   # LangGraph 节点
    _process()                   # 处理逻辑
    validate_output()            # 验证
    fix_output()                 # 修复

# 个性：每个 Agent 独特的地方
RequirementParserAgent:
    _fallback_parse()            # 降级解析
    _detect_language()           # 语言检测

FrameworkDesignerAgent:
    _validate_and_fix()          # 框架修复
    _distribute_modules()        # 模块分配

ResearchAgent:
    research_page()              # 单页研究
    # 特殊：被 PagePipeline 并行调用

ContentMaterialAgent:
    generate_content_for_page()  # 单页生成
    _find_relevant_research()     # 匹配研究

TemplateRendererAgent:
    render()                     # 渲染文件
    _select_template()           # 模板选择
```

### 设计原则

1. **单一职责**：每个 Agent 只做一件事
2. **接口统一**：所有 Agent 都有 `run_node()` 方法
3. **可配置**：通过参数控制行为
4. **可测试**：可以独立测试每个 Agent
5. **可降级**：LLM 失败时有备用方案
6. **可观测**：详细的日志记录

---

## 相关文档

- [需求解析 Agent](./requirement_agent.py.md) - 详解需求解析
- [框架设计 Agent](./framework_agent.py.md) - 详解框架设计
- [研究 Agent](./research_agent.py.md) - 详解研究功能
- [内容生成 Agent](./content_agent.py.md) - 详解内容生成
- [渲染 Agent](./renderer_agent.py.md) - 详解文件渲染
