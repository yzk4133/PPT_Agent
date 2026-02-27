# 高级用法

## 📋 概述

本文档提供 LangChain 多Agent PPT 生成系统的高级使用示例和技巧。

## 🔧 自定义 Agent

### 创建自定义 Agent

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class CustomAgent:
    def __init__(self, model: ChatOpenAI = None):
        self.model = model or ChatOpenAI()
        self.chain = self._create_chain()

    def _create_chain(self):
        prompt = ChatPromptTemplate.from_template(
            "自定义 Prompt 模板\n{input}"
        )
        parser = JsonOutputParser()
        return prompt | self.model | parser

    async def process(self, input_data: dict):
        return await self.chain.ainvoke(input_data)
```

### 集成自定义 Agent

```python
from agents_langchain.coordinator import MasterGraph

# 创建自定义 Agent
custom_agent = CustomAgent()

# 集成到工作流
graph = MasterGraph(
    requirement_agent=custom_agent,  # 使用自定义 Agent
    # 其他 Agent 使用默认
)
```

## 🔄 工作流扩展

### 添加新节点

```python
from langgraph.graph import StateGraph

class ExtendedMasterGraph(MasterGraph):
    def _build_graph(self) -> StateGraph:
        # 调用父类方法
        graph = super()._build_graph()

        # 添加新节点
        builder = StateGraph(PPTGenerationState)
        builder.add_node("custom_node", self.custom_node.run_node)

        # 添加边
        builder.add_edge("content_generation", "custom_node")
        builder.add_edge("custom_node", "template_renderer")

        return builder.compile()
```

### 添加条件分支

```python
def _should_use_template(self, state: PPTGenerationState) -> str:
    """自定义条件判断"""
    requirement = state.get("structured_requirements", {})
    template_type = requirement.get("template_type", "")

    if template_type == "academic_template":
        return "academic_renderer"
    else:
        return "standard_renderer"

# 在图中添加条件边
builder.add_conditional_edges(
    "framework_designer",
    self._should_use_template,
    {
        "academic_renderer": "academic_renderer",
        "standard_renderer": "template_renderer"
    }
)
```

## 📊 状态管理

### 自定义状态字段

```python
from typing import TypedDict
from agents_langchain.models.state import PPTGenerationState

class CustomState(PPTGenerationState):
    """扩展的状态类"""
    custom_field: str
    metadata: dict

# 使用自定义状态
def create_custom_graph() -> StateGraph:
    builder = StateGraph(CustomState)
    ...
```

### 状态中间件

```python
class StateMiddleware:
    """状态处理中间件"""

    async def before_node(
        self,
        state: PPTGenerationState,
        node_name: str
    ) -> PPTGenerationState:
        """节点执行前处理"""
        print(f"即将执行节点: {node_name}")
        print(f"当前进度: {state['progress']}%")
        return state

    async def after_node(
        self,
        state: PPTGenerationState,
        node_name: str
    ) -> PPTGenerationState:
        """节点执行后处理"""
        print(f"节点完成: {node_name}")
        return state
```

## 🎯 Prompt 工程

### 自定义 Prompt

```python
from agents_langchain.core.requirements import RequirementParserAgent

# 自定义 Prompt
CUSTOM_PROMPT = """你是专业的PPT分析师...

用户输入：{user_input}

请分析并返回JSON格式：
{{...}}
"""

class CustomRequirementParser(RequirementParserAgent):
    def _create_chain(self):
        prompt = ChatPromptTemplate.from_template(CUSTOM_PROMPT)
        parser = JsonOutputParser()
        return prompt | self.model | parser
```

### Prompt 模板变量

```python
# 使用多个变量
prompt = ChatPromptTemplate.from_template("""
主题：{ppt_topic}
页数：{page_num}
场景：{scene}

根据以上信息生成...
""")

result = await chain.ainvoke({
    "ppt_topic": "AI介绍",
    "page_num": 10,
    "scene": "business_report"
})
```

## 🚀 性能优化

### 批量处理

```python
async def generate_multiple_ppts(tasks: List[str]):
    """批量生成多个 PPT"""
    graph = create_master_graph()

    # 并行生成
    results = await asyncio.gather(*[
        graph.generate(task) for task in tasks
    ])

    return results

# 使用
tasks = [
    "生成AI介绍PPT",
    "生成机器学习PPT",
    "生成深度学习PPT"
]

results = await generate_multiple_ppts(tasks)
```

### 缓存优化

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_template_by_type(template_type: str) -> dict:
    """缓存模板查询"""
    # 查询逻辑
    return template_data
```

## 🔐 错误处理

### 自定义错误处理

```python
class CustomErrorHandler:
    """自定义错误处理器"""

    async def handle_error(
        self,
        error: Exception,
        state: PPTGenerationState
    ) -> PPTGenerationState:
        """处理错误"""
        # 记录错误
        logger.error(f"Error in {state['current_stage']}: {error}")

        # 根据错误类型采取不同措施
        if isinstance(error, ValueError):
            # 数据验证错误
            return await self._handle_validation_error(state)
        elif isinstance(error, APIError):
            # API 调用错误
            return await self._handle_api_error(state)
        else:
            # 其他错误
            state["error"] = str(error)
            state["current_stage"] = "failed"
            return state

    async def _handle_validation_error(self, state):
        """处理验证错误"""
        # 尝试修复数据
        state["structured_requirements"] = self._fix_requirements(
            state.get("structured_requirements", {})
        )
        return state

    async def _handle_api_error(self, state):
        """处理 API 错误"""
        # 等待后重试
        await asyncio.sleep(5)
        return state
```

### 重试策略

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def robust_llm_call(chain, input_data):
    """带重试的 LLM 调用"""
    return await chain.ainvoke(input_data)
```

## 📊 监控和日志

### 自定义日志

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ppt_generation.log'),
        logging.StreamHandler()
    ]
)

# 在 Agent 中使用
logger = logging.getLogger(__name__)
logger.info("Starting PPT generation")
logger.debug(f"Input: {user_input}")
```

### 进度回调

```python
async def progress_callback(progress: int, stage: str, state: dict):
    """进度回调函数"""
    print(f"进度: {progress}% - 阶段: {stage}")
    # 可以在这里发送 WebSocket 通知
    # 或者更新数据库中的进度

# 使用回调
result = await graph.generate_with_callbacks(
    user_input="创建PPT",
    on_progress=progress_callback
)
```

## 🔌 API 集成

### FastAPI 集成

```python
from fastapi import FastAPI, BackgroundTasks
from agents_langchain import create_master_graph

app = FastAPI()
graph = create_master_graph()

@app.post("/generate-ppt")
async def generate_ppt(
    user_input: str,
    background_tasks: BackgroundTasks
):
    """异步生成 PPT"""
    # 在后台运行
    result = await graph.generate(user_input)

    return {
        "task_id": result["task_id"],
        "status": result["current_stage"],
        "file_path": result.get("ppt_output", {}).get("file_path")
    }

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """查询任务状态"""
    # 从数据库或缓存获取状态
    return {"task_id": task_id, "status": "..."}
```

## 🔗 相关文档

- [basic-usage.md](basic-usage.md): 基础用法
- [../03-core-agents/](../03-core-agents/): 各 Agent 详细文档
- [../04-workflow/](../04-workflow/): 工作流文档
