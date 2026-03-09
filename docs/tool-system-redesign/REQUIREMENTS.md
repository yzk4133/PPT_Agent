# 工具系统需求文档

> 统一Tool（本地+远程）和Skill（工作流参考），让Agent智能选择和使用能力

---

## 🎯 核心目标

构建一个统一的工具系统，让Agent能够智能地选择和使用**Tool**和**Skill**来完成各种任务。

**核心要求**：
- **Tool统一**：本地工具和远程MCP工具使用统一接口
- **Skill参考**：MD技能作为工作流参考，注入上下文
- **Agent自主**：LLM自主决策选择Skill和Tool的组合

---

## 📐 核心概念

### Tool（工具）
- **定义**：细粒度的可调用工具，统一为`invoke()`接口
- **分类**：
  - **本地Tool**：使用LangChain的`@tool`装饰器，直接执行本地函数
  - **远程MCP Tool**：通过MCP协议访问的远程工具服务
- **执行方式**：通过统一的`invoke(**kwargs)`方法调用
- **示例**：`web_search`（本地）、`database_query`（MCP远程）

### Skill（技能）
- **定义**：可复用的工作流参考文档
- **执行方式**：注入到上下文，提供工作流指导（不直接调用）
- **示例**：`frontend_development`、`backend_development`、`data_analysis`

### Agent（智能体）
- **定义**：接收任务，自主选择Skill和Tool
- **决策方式**：LLM根据任务需求自主决策
- **执行流程**：Skill注入上下文 + Tool调用操作

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Agent系统                            │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │          能力注册中心                            │    │
│  │     ┌────────────────────────────────────┐       │    │
│  │     │       Tool Registry                │       │    │
│  │     │  ┌──────────┐    ┌──────────┐     │       │    │
│  │     │  │Local Tool│    │MCP Tool  │     │       │    │
│  │     │  └──────────┘    └──────────┘     │       │    │
│  │     └────────────────────────────────────┘       │    │
│  │     ┌────────────┐      ┌────────────┐          │    │
│  │     │Skill Registry│                         │    │
│  │     └────────────┘                          │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                                │
│                          ▼                                │
│  ┌─────────────────────────────────────────────────┐    │
│  │          Agent接收任务                          │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                                │
│                          ▼                                │
│  ┌─────────────────────────────────────────────────┐    │
│  │          获取能力描述                            │    │
│  │     - 所有Tool的描述（本地+MCP统一展示）         │    │
│  │     - 所有Skill的描述                           │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                                │
│                          ▼                                │
│  ┌─────────────────────────────────────────────────┐    │
│  │          LLM自主决策                            │    │
│  │     - 分析任务需求                             │    │
│  │     - 选择需要的Skill和Tool（不区分本地/远程） │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                                │
│                          ▼                                │
│  ┌─────────────────────────────────────────────────┐    │
│  │          执行选择                               │    │
│  │     ┌────────────┐      ┌────────────┐         │    │
│  │     │Skill注入   │      │  Tool调用  │         │    │
│  │     │上下文      │      │  invoke()  │         │    │
│  │     └────────────┘      │    - 本地Tool        │    │
│  │                          │    - MCP Tool        │    │
│  │                          └────────────┘         │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                                │
│                          ▼                                │
│  ┌─────────────────────────────────────────────────┐    │
│  │          输出结果                                │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Tool设计

### 核心原则

**统一接口，不同实现**：本地Tool和远程MCP Tool对外呈现统一的`invoke()`接口，Agent无需区分调用。

### Tool接口

```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class Tool(ABC):
    """工具统一接口

    本地Tool和远程MCP Tool都实现此接口，
    Agent调用时无需关心工具的具体实现方式。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """工具唯一标识"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述（给LLM看的说明）"""
        pass

    @property
    def parameters(self) -> Dict[str, Any]:
        """参数schema（可选，用于LLM理解参数格式）"""
        return {}

    @abstractmethod
    async def invoke(self, **kwargs) -> Any:
        """统一调用接口

        本地Tool：直接执行本地函数
        MCP Tool：通过MCP协议调用远程服务

        Returns:
            工具执行结果
        """
        pass
```

### Tool类型与实现

#### 1. 本地Tool（LocalTool）

**特点**：
- 使用LangChain的`@tool`装饰器封装Python函数
- 直接在本地进程执行
- 无网络开销，响应快速

**实现**：

```python
from langchain_core.tools import tool
from typing import Any, Dict

class LocalTool(Tool):
    """本地工具实现

    基于LangChain的@tool装饰器，封装Python函数为统一Tool接口。
    """

    def __init__(self, langchain_tool):
        """初始化

        Args:
            langchain_tool: LangChain工具对象（通过@tool装饰器创建）
        """
        self._tool = langchain_tool

    @property
    def name(self) -> str:
        return self._tool.name

    @property
    def description(self) -> str:
        return self._tool.description

    @property
    def parameters(self) -> Dict[str, Any]:
        return self._tool.args_schema.schema() if self._tool.args_schema else {}

    async def invoke(self, **kwargs) -> Any:
        """直接调用本地函数"""
        return await self._tool.ainvoke(kwargs)


# 使用示例
@tool
def calculator(expression: str) -> float:
    """计算数学表达式

    Args:
        expression: 数学表达式，如 "2 + 3 * 4"

    Returns:
        计算结果
    """
    return eval(expression)

# 创建本地Tool
calc_tool = LocalTool(calculator)
```

#### 2. 远程MCP Tool（MCPTool）

**特点**：
- 通过MCP（Model Context Protocol）协议访问远程服务
- 可访问外部系统的能力（数据库、API等）
- 需要处理网络通信和错误

**实现**：

```python
from typing import Any, Dict

class MCPTool(Tool):
    """MCP远程工具实现

    通过MCP协议调用远程工具服务。
    """

    def __init__(
        self,
        name: str,
        description: str,
        mcp_client,
        parameters: Dict[str, Any] = None
    ):
        """初始化

        Args:
            name: 工具名称
            description: 工具描述
            mcp_client: MCP客户端（已连接到远程服务器）
            parameters: 参数schema
        """
        self._name = name
        self._description = description
        self._client = mcp_client
        self._parameters = parameters or {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> Dict[str, Any]:
        return self._parameters

    async def invoke(self, **kwargs) -> Any:
        """通过MCP协议调用远程服务"""
        try:
            # 调用MCP客户端执行远程工具
            result = await self._client.call_tool(
                tool_name=self._name,
                arguments=kwargs
            )
            return result
        except Exception as e:
            # 处理MCP通信错误
            raise ToolInvocationError(
                f"MCP tool '{self._name}' failed: {str(e)}"
            )


# 使用示例
# 假设已有一个连接到远程MCP服务器的客户端
mcp_client = MCPClient(server_url="http://remote-server:8080")

# 创建MCP Tool
db_query_tool = MCPTool(
    name="database_query",
    description="查询数据库，支持SQL语句执行",
    mcp_client=mcp_client,
    parameters={
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "SQL查询语句"
            }
        },
        "required": ["sql"]
    }
)
```

### Tool统一注册

```python
from typing import List, Dict, Optional

class ToolRegistry:
    """工具注册中心

    统一管理本地Tool和远程MCP Tool，
    对Agent屏蔽工具类型的差异。
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """注册工具

        Args:
            tool: Tool实例（LocalTool或MCPTool）
        """
        self._tools[tool.name] = tool

    def find(self, name: str) -> Optional[Tool]:
        """查找工具

        Args:
            name: 工具名称

        Returns:
            Tool实例，不存在则返回None
        """
        return self._tools.get(name)

    def list(self) -> List[Tool]:
        """列出所有工具"""
        return list(self._tools.values())

    def get_descriptions(self) -> List[Dict[str, Any]]:
        """获取所有工具的描述（给LLM看）

        Returns:
            工具描述列表，包含name、description、parameters
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self._tools.values()
        ]
```

### Tool使用示例

```python
# 初始化Tool Registry
tool_registry = ToolRegistry()

# 注册本地Tool
tool_registry.register(LocalTool(calculator))
tool_registry.register(LocalTool(web_search))

# 注册MCP Tool
tool_registry.register(MCPTool(
    name="weather_service",
    description="查询天气信息",
    mcp_client=mcp_client
))
tool_registry.register(MCPTool(
    name="database_query",
    description="查询数据库",
    mcp_client=mcp_client
))

# Agent使用时无需区分本地/远程
tool = tool_registry.find("calculator")
result = await tool.invoke(expression="2 + 3")

tool = tool_registry.find("weather_service")
result = await tool.invoke(city="Beijing"))
```

---

## 📚 Skill设计

### Skill接口

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class Skill(ABC):
    """技能接口"""

    @property
    @abstractmethod
    def name(self) -> str:
        """技能名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """技能描述（给LLM看）"""
        pass

    @property
    def scenarios(self) -> List[str]:
        """适用场景列表"""
        pass

    @property
    def workflow_steps(self) -> List[str]:
        """工作流步骤"""
        pass

    @property
    def recommended_tools(self) -> List[str]:
        """推荐使用的工具名称列表"""
        pass

    @property
    def examples(self) -> List[Dict[str, Any]]:
        """使用示例"""
        pass

    @abstractmethod
    async def get_content(self) -> str:
        """获取技能完整内容（注入到上下文）

        Returns:
            Markdown格式的技能文档内容
        """
        pass
```

### Skill格式（Markdown + YAML Frontmatter）

```markdown
---
name: "frontend_development"
description: "前端开发工作流，包含React、TailwindCSS等规范"
scenarios:
  - "创建Web页面"
  - "开发React组件"
  - "实现响应式布局"
recommended_tools:
  - "web_search"
  - "code_generator"
version: "1.0.0"
author: "System"
---

# Frontend Development Workflow

## 工作流步骤

1. **需求分析** - 理解用户需求和功能要求
2. **设计规划** - 确定页面结构和组件划分
3. **搜索参考** - 查找类似设计和最佳实践
4. **代码生成** - 按照规范生成代码
5. **样式调整** - 应用统一的美术风格

## 代码规范

### 文件结构
```
src/
├── components/    # React组件
├── assets/        # 静态资源
├── styles/        # 样式文件
└── utils/         # 工具函数
```

### 命名规范
- 组件: PascalCase (UserProfile.tsx)
- 文件: kebab-case (user-profile.tsx)

### 美术风格
- 主色: #3B82F6
- 字体: Inter
- 圆角: 8px

## 示例

### 示例1：创建按钮组件
```tsx
interface ButtonProps {
  label: string;
  onClick: () => void;
}

export const Button: React.FC<ButtonProps> = ({ label, onClick }) => {
  return (
    <button
      onClick={onClick}
      className="bg-blue-500 text-white px-4 py-2 rounded"
    >
      {label}
    </button>
  );
};
```
```

---

## 🤖 Agent实现

### Agent核心流程

```python
from typing import List, Dict, Any

class Agent:
    """Agent主类

    统一调度Tool和Skill，自主决策完成任务。
    """

    def __init__(
        self,
        llm,
        tool_registry: ToolRegistry,
        skill_registry: SkillRegistry
    ):
        """初始化

        Args:
            llm: 大语言模型
            tool_registry: 工具注册中心（包含本地和MCP工具）
            skill_registry: 技能注册中心
        """
        self.llm = llm
        self.tool_registry = tool_registry
        self.skill_registry = skill_registry

    async def run(self, task: str) -> str:
        """执行任务

        Args:
            task: 任务描述

        Returns:
            执行结果
        """

        # 1. 获取能力描述（本地Tool和MCP Tool统一展示）
        tool_descriptions = self.tool_registry.get_descriptions()
        skill_summaries = self.skill_registry.get_summaries()

        # 2. LLM自主决策
        decision = await self._make_decision(
            task,
            tool_descriptions,
            skill_summaries
        )

        # 3. 执行Skill（注入上下文）
        context = await self._execute_skills(decision.selected_skills)

        # 4. 执行Tool（本地和MCP统一调用）
        results = await self._execute_tools(
            decision.selected_tools,
            task,
            context
        )

        # 5. 生成最终结果
        return await self._generate_result(task, results, context)

    async def _make_decision(
        self,
        task: str,
        tool_descriptions: List[Dict],
        skill_summaries: List[Dict]
    ) -> Dict[str, Any]:
        """LLM决策

        让LLM根据任务选择合适的Skill和Tool组合。
        """
        prompt = f"""
任务：{task}

可用工具：
{self._format_tools(tool_descriptions)}

可用技能：
{self._format_skills(skill_summaries)}

请分析任务需求，选择合适的技能和工具组合。
返回JSON格式：
{{
    "selected_skills": ["skill_name1", "skill_name2"],
    "selected_tools": ["tool_name1", "tool_name2"],
    "reasoning": "选择原因"
}}
"""
        response = await self.llm.ainvoke(prompt)
        return self._parse_decision(response)

    async def _execute_tools(
        self,
        tool_names: List[str],
        task: str,
        context: str
    ) -> List[Any]:
        """执行工具

        统一调用本地Tool和MCP Tool，无需区分。
        """
        results = []
        for name in tool_names:
            tool = self.tool_registry.find(name)
            if tool:
                # 统一调用接口，本地和MCP无差别
                result = await tool.invoke(task=task, context=context)
                results.append(result)
        return results

    async def _execute_skills(self, skill_names: List[str]) -> str:
        """执行技能

        将Skill内容注入到上下文中。
        """
        contents = []
        for name in skill_names:
            skill = self.skill_registry.find(name)
            if skill:
                content = await skill.get_content()
                contents.append(content)
        return "\n\n".join(contents)
```

---

## 💡 完整示例

```python
import asyncio
from langchain_openai import ChatOpenAI

# 初始化
llm = ChatOpenAI(model="gpt-4")
tool_registry = ToolRegistry()
skill_registry = SkillRegistry("skills/")

# 注册本地Tool
tool_registry.register(LocalTool(web_search))
tool_registry.register(LocalTool(code_generator))

# 注册MCP Tool
mcp_client = MCPClient(server_url="http://mcp-server:8080")
tool_registry.register(MCPTool(
    name="database_query",
    description="查询数据库",
    mcp_client=mcp_client
))

# 创建Agent
agent = Agent(llm, tool_registry, skill_registry)

# 执行任务
task = "创建一个用户登录页面，支持从数据库查询用户信息"
result = await agent.run(task)

# Agent内部流程：
# 1. LLM决策 → 选择Skill: frontend_development
#                    选择Tool: web_search, code_generator, database_query
# 2. 注入frontend_development的Skill内容到上下文
# 3. 调用Tool完成任务：
#    - web_search (本地Tool) → 搜索登录页面设计参考
#    - code_generator (本地Tool) → 生成登录页面代码
#    - database_query (MCP Tool) → 查询用户信息
# 4. 输出最终结果
```

---

## 📁 项目结构

```
backend/agents/core/
├── tools/                    # 工具系统
│   ├── __init__.py
│   ├── interface.py          # Tool统一接口
│   ├── registry.py           # Tool Registry
│   ├── local_tool.py         # 本地Tool实现（基于LangChain）
│   ├── mcp_tool.py           # MCP Tool实现
│   └── exceptions.py         # 工具相关异常
│
├── skills/                   # 技能系统
│   ├── __init__.py
│   ├── interface.py          # Skill接口
│   ├── registry.py           # Skill Registry
│   └── md_skill.py           # MD Skill实现
│
└── agent/                    # Agent
    ├── __init__.py
    └── agent.py              # Agent主类

skills/                        # MD技能包文件
├── frontend_development.md
├── backend_development.md
└── data_analysis.md
```

---

## 🎯 核心优势

### 1. 统一性
- **Tool统一接口**：本地和MCP Tool统一为`invoke()`接口
- **Agent无感知**：Agent调用时无需区分工具类型
- **简化决策**：LLM只需关注工具功能，不关心实现方式

### 2. 灵活性
- **Skill作为参考**：提供工作流指导，不强制执行路径
- **Tool可扩展**：轻松添加新的本地或远程工具
- **Agent自适应**：根据实际情况调整执行策略

### 3. 智能化
- **LLM自主决策**：根据任务选择最佳Skill和Tool组合
- **上下文感知**：Skill注入相关领域知识
- **动态组合**：不同任务可复用相同的能力

### 4. 可维护性
- **清晰分层**：Tool、Skill、Agent职责明确
- **易于测试**：每个组件可独立测试
- **便于扩展**：新能力只需实现接口并注册

---

## 📋 开发计划

### Phase 1: 基础框架（1周）
- [ ] Tool统一接口定义（`interface.py`）
- [ ] Tool Registry实现（`registry.py`）
- [ ] Skill接口定义（`skills/interface.py`）
- [ ] Skill Registry实现（`skills/registry.py`）
- [ ] 基础Agent类（`agent/agent.py`）

### Phase 2: Tool实现（1周）
- [ ] LocalTool实现（基于LangChain，`local_tool.py`）
- [ ] MCPTool实现（`mcp_tool.py`）
- [ ] MCP客户端集成
- [ ] Tool异常处理（`exceptions.py`）

### Phase 3: Skill实现（1周）
- [ ] MDSkill实现（`md_skill.py`）
- [ ] YAML frontmatter解析
- [ ] Skill元数据提取
- [ ] 示例Skill文档编写

### Phase 4: Agent集成与测试（1周）
- [ ] LLM决策机制实现
- [ ] 完整工作流测试
- [ ] 集成测试（本地Tool + MCP Tool）
- [ ] 文档完善

---

## 🧪 测试策略

### 单元测试
```python
# 测试本地Tool
async def test_local_tool():
    calc = LocalTool(calculator)
    result = await calc.invoke(expression="2 + 3")
    assert result == 5.0

# 测试MCP Tool
async def test_mcp_tool():
    mcp_tool = MCPTool("test_tool", "Test", mcp_client)
    result = await mcp.invoke(param="value")
    assert result is not None

# 测试Tool Registry
def test_tool_registry():
    registry = ToolRegistry()
    registry.register(calc_tool)
    assert registry.find("calculator") is not None
```

### 集成测试
```python
# 测试完整Agent流程
async def test_agent_with_mixed_tools():
    agent = Agent(llm, tool_registry, skill_registry)
    result = await agent.run("创建登录页面")
    assert "login" in result.lower()
```

---

**文档版本**：v2.0
**创建时间**：2026-03-07
**更新内容**：明确区分本地Tool和远程MCP Tool，统一Tool接口
