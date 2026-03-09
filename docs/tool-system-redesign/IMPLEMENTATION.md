# 工具系统实施方案

> 基于REQUIREMENTS.md的详细实施计划

---

## 📋 开发原则

根据需求讨论，确定以下开发原则：

1. **自底向上开发**：先构建基础框架，再做上层集成
2. **第一期支持MCP**：本地Tool和MCP Tool同步实现
3. **单文件改动**：每个阶段只修改/创建1个文件
4. **TDD驱动**：每个功能先写测试，再实现代码
5. **阶段集成测试**：每完成一个阶段就进行集成测试

---

## 🗺️ 实施路线图

```
Phase 1: 基础框架
├── Step 1: 异常定义
├── Step 2: Tool接口
├── Step 3: Tool Registry
├── Step 4: Skill接口
└── Step 5: Skill Registry

Phase 2: Tool实现
├── Step 6: MCP客户端封装
├── Step 7: LocalTool实现
├── Step 8: MCPTool实现
└── Step 9: Tool集成测试

Phase 3: Skill实现
├── Step 10: MDSkill实现
├── Step 11: Skill示例文档
└── Step 12: Skill集成测试

Phase 4: Agent实现
├── Step 13: Agent基础框架
├── Step 14: LLM决策机制
├── Step 15: 完整工作流
└── Step 16: 端到端测试
```

---

## Phase 1: 基础框架（预计1周）

### Step 1: 异常定义
**文件**: `backend/agents/core/tools/exceptions.py`

**TDD流程**:
1. 先写测试 `tests/tools/test_exceptions.py`
2. 定义异常类
3. 验证测试通过

**实现内容**:
```python
class ToolError(Exception):
    """工具基础异常"""
    pass

class ToolNotFoundError(ToolError):
    """工具不存在"""
    pass

class ToolInvocationError(ToolError):
    """工具调用失败"""
    pass
```

**验收标准**:
- [ ] 异常类可正常抛出和捕获
- [ ] 异常信息包含足够的上下文

---

### Step 2: Tool接口
**文件**: `backend/agents/core/tools/interface.py`

**TDD流程**:
1. 先写测试 `tests/tools/test_interface.py`
2. 定义Tool接口
3. 验证测试通过

**实现内容**:
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class Tool(ABC):
    """工具统一接口"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具唯一标识"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述（给LLM看）"""
        pass

    @property
    def parameters(self) -> Dict[str, Any]:
        """参数schema"""
        return {}

    @abstractmethod
    async def invoke(self, **kwargs) -> Any:
        """调用工具"""
        pass
```

**验收标准**:
- [ ] 接口定义清晰
- [ ] 子类必须实现抽象方法
- [ ] 测试覆盖所有抽象方法

---

### Step 3: Tool Registry
**文件**: `backend/agents/core/tools/registry.py`

**TDD流程**:
1. 先写测试 `tests/tools/test_registry.py`
2. 实现ToolRegistry
3. 验证测试通过

**实现内容**:
```python
from typing import List, Dict, Optional
from .interface import Tool
from .exceptions import ToolNotFoundError

class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool

    def find(self, name: str) -> Optional[Tool]:
        """查找工具"""
        return self._tools.get(name)

    def list(self) -> List[Tool]:
        """列出所有工具"""
        return list(self._tools.values())

    def get_descriptions(self) -> List[Dict[str, Any]]:
        """获取所有工具的描述（给LLM看）"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self._tools.values()
        ]
```

**验收标准**:
- [ ] 可以注册和查找工具
- [ ] 可以获取工具描述列表
- [ ] 测试覆盖注册、查找、列表功能

---

### Step 4: Skill接口
**文件**: `backend/agents/core/skills/interface.py`

**TDD流程**:
1. 先写测试 `tests/skills/test_interface.py`
2. 定义Skill接口
3. 验证测试通过

**实现内容**:
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
        """适用场景"""
        return []

    @property
    def workflow_steps(self) -> List[str]:
        """工作流步骤"""
        return []

    @property
    def recommended_tools(self) -> List[str]:
        """推荐使用的工具列表"""
        return []

    @property
    def examples(self) -> List[Dict[str, Any]]:
        """示例"""
        return []

    @abstractmethod
    async def get_content(self) -> str:
        """获取技能内容（注入到上下文）"""
        pass
```

**验收标准**:
- [ ] 接口定义清晰
- [ ] 子类必须实现抽象方法
- [ ] 测试覆盖核心方法

---

### Step 5: Skill Registry
**文件**: `backend/agents/core/skills/registry.py`

**TDD流程**:
1. 先写测试 `tests/skills/test_registry.py`
2. 实现SkillRegistry
3. 验证测试通过

**实现内容**:
```python
from typing import List, Dict, Optional
from .interface import Skill

class SkillRegistry:
    """技能注册中心"""

    def __init__(self):
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """注册技能"""
        self._skills[skill.name] = skill

    def find(self, name: str) -> Optional[Skill]:
        """查找技能"""
        return self._skills.get(name)

    def list(self) -> List[Skill]:
        """列出所有技能"""
        return list(self._skills.values())

    def get_summaries(self) -> List[Dict[str, str]]:
        """获取技能摘要（给LLM看）"""
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "scenarios": skill.scenarios,
                "recommended_tools": skill.recommended_tools
            }
            for skill in self._skills.values()
        ]
```

**验收标准**:
- [ ] 可以注册和查找技能
- [ ] 可以获取技能摘要列表
- [ ] 测试覆盖核心功能

**Phase 1 集成测试**:
```python
# tests/integration/test_phase1.py
async def test_tool_and_skill_registry():
    """测试Tool和Skill Registry可以正常工作"""
    tool_registry = ToolRegistry()
    skill_registry = SkillRegistry()

    # 验证基础功能
    assert len(tool_registry.list()) == 0
    assert len(skill_registry.list()) == 0
```

---

## Phase 2: Tool实现（预计1周）

### Step 6: MCP客户端封装
**文件**: `backend/agents/core/tools/mcp_client.py`

**TDD流程**:
1. 先写测试 `tests/tools/test_mcp_client.py`
2. 实现MCP客户端
3. 验证测试通过

**实现内容**:
```python
from typing import Any, Dict
import httpx

class MCPClient:
    """MCP协议客户端"""

    def __init__(self, server_url: str, timeout: int = 30):
        """初始化

        Args:
            server_url: MCP服务器地址
            timeout: 请求超时时间
        """
        self.server_url = server_url
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """调用远程工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        response = await self._client.post(
            f"{self.server_url}/tools/{tool_name}",
            json={"arguments": arguments}
        )
        response.raise_for_status()
        return response.json()

    async def close(self):
        """关闭客户端"""
        await self._client.aclose()
```

**验收标准**:
- [ ] 可以连接MCP服务器
- [ ] 可以调用远程工具
- [ ] 可以处理网络错误
- [ ] 测试覆盖成功和失败场景

**注意**:
- 需要准备一个测试用的MCP服务器
- 可以使用mock对象进行单元测试

---

### Step 7: LocalTool实现
**文件**: `backend/agents/core/tools/local_tool.py`

**TDD流程**:
1. 先写测试 `tests/tools/test_local_tool.py`
2. 实现LocalTool
3. 验证测试通过

**实现内容**:
```python
from typing import Any, Dict
from langchain_core.tools import BaseTool
from .interface import Tool

class LocalTool(Tool):
    """本地工具实现

    基于LangChain的@tool装饰器，封装Python函数为统一Tool接口。
    """

    def __init__(self, langchain_tool: BaseTool):
        """初始化

        Args:
            langchain_tool: LangChain工具对象
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
        if self._tool.args_schema:
            return self._tool.args_schema.schema()
        return {}

    async def invoke(self, **kwargs) -> Any:
        """直接调用本地函数"""
        return await self._tool.ainvoke(kwargs)
```

**验收标准**:
- [ ] 可以封装LangChain工具
- [ ] 可以正确调用本地函数
- [ ] 参数schema正确提取
- [ ] 测试覆盖同步和异步调用

**使用示例**:
```python
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> float:
    """计算数学表达式"""
    return eval(expression)

calc_tool = LocalTool(calculator)
result = await calc_tool.invoke(expression="2 + 3")
```

---

### Step 8: MCPTool实现
**文件**: `backend/agents/core/tools/mcp_tool.py`

**TDD流程**:
1. 先写测试 `tests/tools/test_mcp_tool.py`
2. 实现MCPTool
3. 验证测试通过

**实现内容**:
```python
from typing import Any, Dict
from .interface import Tool
from .mcp_client import MCPClient
from .exceptions import ToolInvocationError

class MCPTool(Tool):
    """MCP远程工具实现

    通过MCP协议调用远程工具服务。
    """

    def __init__(
        self,
        name: str,
        description: str,
        mcp_client: MCPClient,
        parameters: Dict[str, Any] = None
    ):
        """初始化

        Args:
            name: 工具名称
            description: 工具描述
            mcp_client: MCP客户端
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
            result = await self._client.call_tool(
                tool_name=self._name,
                arguments=kwargs
            )
            return result
        except Exception as e:
            raise ToolInvocationError(
                f"MCP tool '{self._name}' failed: {str(e)}"
            ) from e
```

**验收标准**:
- [ ] 可以通过MCP客户端调用远程工具
- [ ] 可以正确处理调用失败
- [ ] 错误信息清晰有用
- [ ] 测试覆盖成功和失败场景

---

### Step 9: Tool集成测试
**文件**: `tests/integration/test_phase2.py`

**测试内容**:
```python
import pytest
from backend.agents.core.tools.registry import ToolRegistry
from backend.agents.core.tools.local_tool import LocalTool
from backend.agents.core.tools.mcp_tool import MCPTool

@pytest.mark.asyncio
async def test_mixed_tool_registry():
    """测试混合注册本地和MCP工具"""
    registry = ToolRegistry()

    # 注册本地工具
    @tool
    def local_calculator(expression: str) -> float:
        return eval(expression)
    registry.register(LocalTool(local_calculator))

    # 注册MCP工具（使用mock）
    mock_client = MockMCPClient()
    mcp_tool = MCPTool(
        name="remote_search",
        description="远程搜索",
        mcp_client=mock_client
    )
    registry.register(mcp_tool)

    # 验证
    assert len(registry.list()) == 2
    descriptions = registry.get_descriptions()
    assert len(descriptions) == 2

    # 测试调用
    calc = registry.find("local_calculator")
    result = await calc.invoke(expression="2+3")
    assert result == 5.0

    search = registry.find("remote_search")
    result = await search.invoke(query="test")
    assert result is not None

@pytest.mark.asyncio
async def test_tool_unified_interface():
    """测试本地和MCP工具使用统一接口"""
    registry = ToolRegistry()

    # 注册两种工具
    local_tool = LocalTool(local_calculator)
    mcp_tool = MCPTool("remote", "desc", mock_client)

    registry.register(local_tool)
    registry.register(mcp_tool)

    # 统一调用方式
    for tool_name in ["local_calculator", "remote"]:
        tool = registry.find(tool_name)
        assert tool is not None
        # 调用接口相同
        result = await tool.invoke()
```

**验收标准**:
- [ ] 本地和MCP工具可以同时注册
- [ ] 两种工具使用相同调用方式
- [ ] 工具描述统一格式
- [ ] 错误处理正确

---

## Phase 3: Skill实现（预计1周）

### Step 10: MDSkill实现
**文件**: `backend/agents/core/skills/md_skill.py`

**TDD流程**:
1. 先写测试 `tests/skills/test_md_skill.py`
2. 实现MDSkill
3. 验证测试通过

**实现内容**:
```python
import re
from typing import List, Dict, Any
from pathlib import Path
import yaml
from .interface import Skill

class MDSkill(Skill):
    """Markdown技能实现

    从MD文件加载技能定义，支持YAML frontmatter。
    """

    def __init__(self, file_path: str):
        """初始化

        Args:
            file_path: MD文件路径
        """
        self._file_path = Path(file_path)
        self._metadata = {}
        self._content = ""
        self._load()

    def _load(self):
        """加载MD文件"""
        content = self._file_path.read_text(encoding="utf-8")

        # 解析YAML frontmatter
        frontmatter_pattern = r"^---\n(.*?)\n---\n(.*)$"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if match:
            yaml_content, md_content = match.groups()
            self._metadata = yaml.safe_load(yaml_content)
            self._content = md_content
        else:
            raise ValueError(f"Invalid skill file: {self._file_path}")

    @property
    def name(self) -> str:
        return self._metadata.get("name", self._file_path.stem)

    @property
    def description(self) -> str:
        return self._metadata.get("description", "")

    @property
    def scenarios(self) -> List[str]:
        return self._metadata.get("scenarios", [])

    @property
    def workflow_steps(self) -> List[str]:
        return self._metadata.get("workflow_steps", [])

    @property
    def recommended_tools(self) -> List[str]:
        return self._metadata.get("recommended_tools", [])

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return self._metadata.get("examples", [])

    async def get_content(self) -> str:
        """获取技能完整内容"""
        return f"# {self.name}\n\n{self._content}"
```

**验收标准**:
- [ ] 可以解析YAML frontmatter
- [ ] 可以正确提取元数据
- [ ] 可以获取完整内容
- [ ] 测试覆盖各种MD格式

---

### Step 11: Skill示例文档
**文件**: `skills/frontend_development.md`

**内容**:
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

**其他示例文件**:
- `skills/backend_development.md`
- `skills/data_analysis.md`

---

### Step 12: Skill集成测试
**文件**: `tests/integration/test_phase3.py`

**测试内容**:
```python
import pytest
from backend.agents.core.skills.registry import SkillRegistry
from backend.agents.core.skills.md_skill import MDSkill

@pytest.mark.asyncio
async def test_skill_registry():
    """测试技能注册中心"""
    registry = SkillRegistry()

    # 加载MD技能
    frontend_skill = MDSkill("skills/frontend_development.md")
    backend_skill = MDSkill("skills/backend_development.md")

    registry.register(frontend_skill)
    registry.register(backend_skill)

    # 验证
    assert len(registry.list()) == 2

    summaries = registry.get_summaries()
    assert len(summaries) == 2
    assert summaries[0]["name"] in ["frontend_development", "backend_development"]

@pytest.mark.asyncio
async def test_skill_content_injection():
    """测试技能内容注入"""
    skill = MDSkill("skills/frontend_development.md")

    content = await skill.get_content()
    assert "Frontend Development Workflow" in content
    assert "工作流步骤" in content

    # 验证元数据
    assert skill.name == "frontend_development"
    assert "React" in skill.description
    assert "web_search" in skill.recommended_tools
```

**验收标准**:
- [ ] 可以加载MD技能文件
- [ ] 元数据正确提取
- [ ] 内容可以正确注入
- [ ] Skill Registry正常工作

---

## Phase 4: Agent实现（预计1周）

### Step 13: Agent基础框架
**文件**: `backend/agents/core/agent/agent.py`

**TDD流程**:
1. 先写测试 `tests/agent/test_agent.py`
2. 实现Agent基础类
3. 验证测试通过

**实现内容**:
```python
from typing import Any, Dict
from ..tools.registry import ToolRegistry
from ..skills.registry import SkillRegistry

class Agent:
    """Agent主类"""

    def __init__(
        self,
        llm,
        tool_registry: ToolRegistry,
        skill_registry: SkillRegistry
    ):
        """初始化

        Args:
            llm: 大语言模型
            tool_registry: 工具注册中心
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
        # 基础流程（后续步骤完善）
        tool_descriptions = self.tool_registry.get_descriptions()
        skill_summaries = self.skill_registry.get_summaries()

        # 暂时返回简单结果
        return f"Task: {task}\nTools: {len(tool_descriptions)}\nSkills: {len(skill_summaries)}"
```

**验收标准**:
- [ ] Agent可以初始化
- [ ] 可以获取Tool和Skill描述
- [ ] 测试覆盖基础流程

---

### Step 14: LLM决策机制
**文件**: `backend/agents/core/agent/decision.py`（辅助模块）

**TDD流程**:
1. 先写测试 `tests/agent/test_decision.py`
2. 实现决策逻辑
3. 验证测试通过

**实现内容**:
```python
from typing import List, Dict, Any

class DecisionMaker:
    """LLM决策模块"""

    def __init__(self, llm):
        self.llm = llm

    async def make_decision(
        self,
        task: str,
        tool_descriptions: List[Dict],
        skill_summaries: List[Dict]
    ) -> Dict[str, Any]:
        """让LLM决策选择Skill和Tool

        Args:
            task: 任务描述
            tool_descriptions: 工具描述列表
            skill_summaries: 技能摘要列表

        Returns:
            决策结果，包含selected_skills和selected_tools
        """
        prompt = self._build_prompt(task, tool_descriptions, skill_summaries)
        response = await self.llm.ainvoke(prompt)
        return self._parse_decision(response)

    def _build_prompt(
        self,
        task: str,
        tool_descriptions: List[Dict],
        skill_summaries: List[Dict]
    ) -> str:
        """构建决策提示词"""
        tools_str = "\n".join([
            f"- {t['name']}: {t['description']}"
            for t in tool_descriptions
        ])

        skills_str = "\n".join([
            f"- {s['name']}: {s['description']}"
            for s in skill_summaries
        ])

        return f"""
任务：{task}

可用工具：
{tools_str}

可用技能：
{skills_str}

请分析任务需求，选择合适的技能和工具组合。
返回JSON格式：
{{
    "selected_skills": ["skill_name1", "skill_name2"],
    "selected_tools": ["tool_name1", "tool_name2"],
    "reasoning": "选择原因"
}}
"""

    def _parse_decision(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        import json
        # 提取JSON部分
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # 降级处理：返回空选择
            return {
                "selected_skills": [],
                "selected_tools": [],
                "reasoning": "解析失败"
            }
```

**验收标准**:
- [ ] 可以构建正确的提示词
- [ ] 可以解析LLM响应
- [ ] 可以处理解析失败
- [ ] 测试覆盖决策流程

---

### Step 15: 完整工作流
**修改文件**: `backend/agents/core/agent/agent.py`

**TDD流程**:
1. 先更新测试 `tests/agent/test_agent.py`
2. 完善Agent实现
3. 验证测试通过

**实现内容**:
```python
from typing import List, Dict, Any
from .decision import DecisionMaker

class Agent:
    """Agent主类"""

    def __init__(
        self,
        llm,
        tool_registry: ToolRegistry,
        skill_registry: SkillRegistry
    ):
        self.llm = llm
        self.tool_registry = tool_registry
        self.skill_registry = skill_registry
        self.decision_maker = DecisionMaker(llm)

    async def run(self, task: str) -> str:
        """执行任务"""
        # 1. 获取能力描述
        tool_descriptions = self.tool_registry.get_descriptions()
        skill_summaries = self.skill_registry.get_summaries()

        # 2. LLM决策
        decision = await self.decision_maker.make_decision(
            task,
            tool_descriptions,
            skill_summaries
        )

        # 3. 执行Skill（注入上下文）
        context = await self._execute_skills(decision["selected_skills"])

        # 4. 执行Tool
        results = await self._execute_tools(
            decision["selected_tools"],
            task,
            context
        )

        # 5. 生成最终结果
        return await self._generate_result(task, results, context)

    async def _execute_skills(self, skill_names: List[str]) -> str:
        """执行技能"""
        contents = []
        for name in skill_names:
            skill = self.skill_registry.find(name)
            if skill:
                content = await skill.get_content()
                contents.append(content)
        return "\n\n".join(contents)

    async def _execute_tools(
        self,
        tool_names: List[str],
        task: str,
        context: str
    ) -> List[Any]:
        """执行工具"""
        results = []
        for name in tool_names:
            tool = self.tool_registry.find(name)
            if tool:
                result = await tool.invoke(task=task, context=context)
                results.append(result)
        return results

    async def _generate_result(
        self,
        task: str,
        results: List[Any],
        context: str
    ) -> str:
        """生成最终结果"""
        prompt = f"""
任务：{task}

参考信息：
{context}

工具执行结果：
{results}

请基于以上信息生成最终结果。
"""
        response = await self.llm.ainvoke(prompt)
        return response
```

**验收标准**:
- [ ] 完整工作流可以执行
- [ ] Skill正确注入上下文
- [ ] Tool正确调用
- [ ] 生成合理结果

---

### Step 16: 端到端测试
**文件**: `tests/integration/test_e2e.py`

**测试内容**:
```python
import pytest
from langchain_openai import ChatOpenAI
from backend.agents.core.tools.registry import ToolRegistry
from backend.agents.core.tools.local_tool import LocalTool
from backend.agents.core.tools.mcp_tool import MCPTool
from backend.agents.core.skills.registry import SkillRegistry
from backend.agents.core.skills.md_skill import MDSkill
from backend.agents.core.agent.agent import Agent

@pytest.mark.asyncio
async def test_end_to_end_simple_task():
    """端到端测试：简单任务"""
    # 初始化
    llm = ChatOpenAI(model="gpt-4")
    tool_registry = ToolRegistry()
    skill_registry = SkillRegistry()

    # 注册工具
    @tool
    def calculator(expression: str) -> float:
        """计算数学表达式"""
        return eval(expression)

    tool_registry.register(LocalTool(calculator))

    # 注册技能
    skill = MDSkill("skills/frontend_development.md")
    skill_registry.register(skill)

    # 创建Agent
    agent = Agent(llm, tool_registry, skill_registry)

    # 执行任务
    result = await agent.run("计算2+3的结果")

    # 验证
    assert "5" in result or "five" in result.lower()

@pytest.mark.asyncio
async def test_end_to_end_complex_task():
    """端到端测试：复杂任务"""
    # 初始化（包含MCP工具）
    llm = ChatOpenAI(model="gpt-4")
    tool_registry = ToolRegistry()
    skill_registry = SkillRegistry()

    # 注册多种工具
    tool_registry.register(LocalTool(calculator))
    tool_registry.register(LocalTool(web_search))
    tool_registry.register(MCPTool("database", "数据库查询", mcp_client))

    # 注册多个技能
    skill_registry.register(MDSkill("skills/frontend_development.md"))
    skill_registry.register(MDSkill("skills/backend_development.md"))

    # 创建Agent
    agent = Agent(llm, tool_registry, skill_registry)

    # 执行复杂任务
    result = await agent.run("创建一个用户登录页面，支持从数据库查询用户信息")

    # 验证
    assert "login" in result.lower()
    assert "component" in result.lower() or "组件" in result
```

**验收标准**:
- [ ] 简单任务可以完成
- [ ] 复杂任务可以完成
- [ ] 本地和MCP工具都能正常调用
- [ ] Skill正确注入和使用
- [ ] 结果质量符合预期

---

## 📊 进度跟踪

### Phase 1 进度
- [ ] Step 1: 异常定义
- [ ] Step 2: Tool接口
- [ ] Step 3: Tool Registry
- [ ] Step 4: Skill接口
- [ ] Step 5: Skill Registry
- [ ] Phase 1 集成测试

### Phase 2 进度
- [ ] Step 6: MCP客户端封装
- [ ] Step 7: LocalTool实现
- [ ] Step 8: MCPTool实现
- [ ] Step 9: Tool集成测试

### Phase 3 进度
- [ ] Step 10: MDSkill实现
- [ ] Step 11: Skill示例文档
- [ ] Step 12: Skill集成测试

### Phase 4 进度
- [ ] Step 13: Agent基础框架
- [ ] Step 14: LLM决策机制
- [ ] Step 15: 完整工作流
- [ ] Step 16: 端到端测试

---

## 🎯 总体验收标准

### 功能完整性
- [ ] 支持本地Tool（基于LangChain）
- [ ] 支持远程MCP Tool
- [ ] 支持MD Skill工作流
- [ ] Agent可以自主决策
- [ ] 完整的端到端流程

### 代码质量
- [ ] 单元测试覆盖率 > 80%
- [ ] 所有集成测试通过
- [ ] 代码符合PEP8规范
- [ ] 类型注解完整
- [ ] 文档注释完善

### 性能要求
- [ ] 本地Tool调用延迟 < 100ms
- [ ] MCP Tool调用延迟 < 2s
- [ ] Agent决策时间 < 5s
- [ ] 端到端任务完成时间 < 30s

---

**文档版本**：v1.0
**创建时间**：2026-03-07
**总步骤数**：16步
**预计工期**：4周
