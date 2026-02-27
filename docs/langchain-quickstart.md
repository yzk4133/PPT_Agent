# LangChain 迁移快速启动指南

## 🚀 30分钟快速验证

### Step 1: 安装依赖（5分钟）

```bash
cd backend
pip install langchain langchain-core langchain-openai langgraph
pip install openai
```

### Step 2: 创建最小 Demo（15分钟）

创建文件 `backend/quick_demo.py`:

```python
"""
LangChain 最小可运行 Demo
30分钟验证技术栈可行性
"""
import os
import asyncio
from typing import TypedDict, Sequence, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END


class SimpleState(TypedDict):
    """简单状态"""
    messages: Annotated[Sequence[BaseMessage], "消息历史"]
    current_stage: str


# LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",  # 或 "deepseek-chat"
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")  # 或 DEEPSEEK_API_KEY
)


# 节点1: 需求分析
async def analyze_requirement(state: SimpleState) -> SimpleState:
    print(">>> 阶段1: 需求分析")

    response = await llm.ainvoke([
        ("system", "你是PPT需求分析专家"),
        ("human", state["messages"][-1].content)
    ])

    return {
        **state,
        "messages": state["messages"] + [
            AIMessage(content=f"需求已分析: {response.content[:100]}...")
        ],
        "current_stage": "ANALYZED"
    }


# 节点2: 框架设计
async def design_framework(state: SimpleState) -> SimpleState:
    print(">>> 阶段2: 框架设计")

    response = await llm.ainvoke([
        ("system", "你是PPT框架设计专家"),
        ("human", "根据前面的需求设计PPT框架")
    ])

    return {
        **state,
        "messages": state["messages"] + [
            AIMessage(content=f"框架已设计: {response.content[:100]}...")
        ],
        "current_stage": "DESIGNED"
    }


# 节点3: 内容生成
async def generate_content(state: SimpleState) -> SimpleState:
    print(">>> 阶段3: 内容生成")

    response = await llm.ainvoke([
        ("system", "你是PPT内容生成专家"),
        ("human", "根据框架生成PPT内容")
    ])

    return {
        **state,
        "messages": state["messages"] + [
            AIMessage(content=f"内容已生成: {response.content[:100]}...")
        ],
        "current_stage": "COMPLETED"
    }


# 构建图
def create_graph():
    """创建工作流图"""
    graph = StateGraph(SimpleState)

    # 添加节点
    graph.add_node("analyze", analyze_requirement)
    graph.add_node("design", design_framework)
    graph.add_node("generate", generate_content)

    # 定义流程
    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "design")
    graph.add_edge("design", "generate")
    graph.add_edge("generate", END)

    return graph.compile()


# 主函数
async def main():
    print("=" * 50)
    print("LangChain PPT 生成 Demo")
    print("=" * 50)

    # 创建图
    graph = create_graph()

    # 初始状态
    initial_state = {
        "messages": [HumanMessage(content="生成一份关于AI技术的PPT介绍，10页")],
        "current_stage": "START"
    }

    # 执行
    result = await graph.ainvoke(initial_state)

    print("\n" + "=" * 50)
    print("完成！")
    print("=" * 50)
    print(f"执行阶段: {result['current_stage']}")
    print(f"消息数量: {len(result['messages'])}")


if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3: 运行验证（5分钟）

```bash
# 设置 API Key
export OPENAI_API_KEY="your-key-here"

# 或使用 DeepSeek
export OPENAI_API_KEY="your-deepseek-key"
export OPENAI_BASE_URL="https://api.deepseek.com/v1"

# 运行
python backend/quick_demo.py
```

### Step 4: 观察输出

应该看到：
```
==================================================
LangChain PPT 生成 Demo
==================================================
>>> 阶段1: 需求分析
>>> 阶段2: 框架设计
>>> 阶段3: 内容生成

==================================================
完成！
==================================================
执行阶段: COMPLETED
消息数量: 4
```

---

## 🎯 验证成功后做什么？

如果 Demo 能跑通，说明 LangChain 可行，可以开始完整迁移。

如果 Demo 跑不通，检查：
1. API Key 是否正确
2. 网络是否通畅
3. 依赖是否安装完整

---

## 💡 与 Google ADK 的核心差异

| 特性 | Google ADK | LangChain + LangGraph |
|------|-----------|---------------------|
| **Agent定义** | `class XAgent(BaseAgent)` | `async def node(state: State)` |
| **状态管理** | `ctx.session.state` | `State(TypedDict)` |
| **流程编排** | 手动调用 `agent.run_async()` | `StateGraph.add_edge()` |
| **条件分支** | `if/else` 判断 | `add_conditional_edges()` |
| **并发执行** | `asyncio.gather()` | `RunnableParallel` |
| **记忆系统** | 自定义 `AgentMemoryMixin` | `MemorySaver` + `checkpointer` |

---

## 📋 下一步行动

- [ ] 运行 quick_demo.py，验证基础功能
- [ ] 对比 Google ADK 和 LangChain 的代码差异
- [ ] 开始 Phase 1: 环境准备
- [ ] 阅读 LangGraph 官方教程

---

## 🔗 学习资源

- LangChain 快速开始: https://python.langchain.com/docs/get_started/introduction
- LangGraph 教程: https://langchain-ai.github.io/langgraph/tutorials/introduction/
- 状态图示例: https://langchain-ai.github.io/langgraph/tutorials/introduction/#next-steps

---

**预计时间**: 30分钟完成验证
