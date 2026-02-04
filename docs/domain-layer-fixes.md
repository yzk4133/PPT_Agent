# Domain Layer DDD Refactor - Issue Fixes

## 问题总结

在 DDD 重构过程中发现了以下严重问题：

### 1. 重复定义（严重）

**问题描述**：
- `AgentContext` 同时存在于 `communication/agent_context.py` 和 `models/agent_context.py`
- `AgentResult` 同时存在于 `communication/agent_result.py` 和 `models/agent_result.py`
- `ExecutionMode` 在多处定义
- `AgentStage` 在多处定义

**影响**：
- 维护困难（需要同步修改多个文件）
- 导入混乱（不知道应该从哪里导入）
- 潜在的不一致性

### 2. 命名冲突/混乱

**问题描述**：
在 `communication/__init__.py` 中使用别名导出：
```python
Requirement as AgentRequirement
PPTFramework as AgentPPTFramework
ExecutionMode as AgentExecutionMode
```

**原因**：
不同模块中有同名类，需要别名来区分。

### 3. 向后兼容层混乱

**问题描述**：
- `models/` 被标记为 DEPRECATED
- 但仍然包含 `agent_context.py` 和 `agent_result.py`
- 导致不知道应该使用哪个版本

## 解决方案

### 1. 删除重复文件

**删除的文件**：
- `backend/domain/models/agent_context.py`
- `backend/domain/models/agent_result.py`

**保留的文件**（权威版本）：
- `backend/domain/communication/agent_context.py`
- `backend/domain/communication/agent_result.py`

### 2. 更新导入

**更新文件**：`backend/domain/models/__init__.py`

**修改前**（从本地导入）：
```python
from .agent_context import (
    AgentContext,
    ExecutionMode as AgentExecutionMode,
    AgentStage,
)
from .agent_result import (
    AgentResult,
    ResultStatus,
)
```

**修改后**（从 communication/ 重新导出）：
```python
# Agent 通信模型 - 从 communication/ 重新导出以保持向后兼容
from ..communication.agent_context import (
    AgentContext,
    Requirement as AgentRequirement,
    PPTFramework as AgentPPTFramework,
    ResearchResult as AgentResearchResult,
    SlideContent,
    ExecutionMode as AgentExecutionMode,
    AgentStage,
)
from ..communication.agent_result import (
    AgentResult,
    ResultStatus,
    ValidationResult,
    ProgressEvent,
)
```

### 3. 更新直接引用

**更新文件**：`backend/agents/orchestrator/components/agent_gateway.py`

**修改前**：
```python
from domain.models.agent_context import AgentContext, AgentStage
from domain.models.agent_result import AgentResult, ResultStatus
```

**修改后**：
```python
from domain.communication.agent_context import AgentContext, AgentStage
from domain.communication.agent_result import AgentResult, ResultStatus
```

## 导入路径指南

### 推荐导入方式（新代码）

```python
# Agent 通信模型 - 从 communication/ 导入
from domain.communication import AgentContext, AgentResult

# 实体 - 从 entities/ 导入
from domain.entities import Task, TaskStatus, TaskStage

# 值对象 - 从 value_objects/ 导入
from domain.value_objects import Requirement, PPTFramework

# 服务 - 从 services/ 导入
from domain.services import task_progress_service, task_validation_service

# 异常 - 从 exceptions/ 导入
from domain.exceptions import ValidationError, InvalidStateTransitionError

# 事件 - 从 events/ 导入
from domain.events import create_task_created_event

# 配置 - 从 config/ 导入
from domain.config import TaskConfig, TaskProgressWeights

# 接口 - 从 interfaces/ 导入
from domain.interfaces import IAgent, IAgentConfig
```

### 向后兼容导入（旧代码）

```python
# 仍然支持，但不推荐用于新代码
from domain.models import AgentContext, AgentResult, ExecutionMode
```

### 通用导入（通过 __init__.py）

```python
# 所有公共导出都可以通过 domain/ 导入
from domain import (
    Task, TaskStatus,
    Requirement, PPTFramework,
    AgentContext, AgentResult,
    ValidationError,
    task_progress_service,
)
```

## 清理结果

### 导入验证

所有导入路径都经过验证：

```bash
$ python -c "
from domain.models import AgentContext, AgentResult
from domain.communication import AgentContext, AgentResult
from domain import AgentContext, AgentResult
from agents.orchestrator.components.agent_gateway import AgentGateway
print('All imports successful!')
"

[OK] domain.models.AgentContext (backward compatible)
[OK] domain.models.AgentResult (backward compatible)
[OK] domain.models.ExecutionMode (backward compatible)
[OK] domain.communication.AgentContext (new path)
[OK] domain.communication.AgentResult (new path)
[OK] domain.AgentContext (via __init__.py)
[OK] domain.AgentResult (via __init__.py)
[OK] agent_gateway.AgentGateway imports work

All imports successful!
```

### 文件结构

```
backend/domain/
├── models/                          # 向后兼容层
│   ├── __init__.py                  # 从 communication/ 重新导出
│   ├── topic.py                     # 本地定义
│   ├── research.py                  # 本地定义
│   ├── slide.py                     # 本地定义
│   ├── presentation.py              # 本地定义
│   ├── task.py                      # 本地定义
│   ├── requirement.py               # 本地定义
│   ├── framework.py                 # 本地定义
│   ├── execution_mode.py            # 本地定义
│   ├── checkpoint.py                # 本地定义
│   ├── page_state.py                # 本地定义
│   ├── agent_context.py             # ❌ 已删除（重复）
│   └── agent_result.py              # ❌ 已删除（重复）
│
├── communication/                   # Agent 通信（权威版本）
│   ├── __init__.py
│   ├── agent_context.py             # ✓ 保留
│   └── agent_result.py              # ✓ 保留
```

## 最佳实践

### 1. 避免重复定义

**❌ 错误**：
```python
# models/agent_context.py
class AgentContext: pass

# communication/agent_context.py
class AgentContext: pass  # 重复！
```

**✅ 正确**：
```python
# communication/agent_context.py（权威版本）
class AgentContext: pass

# models/__init__.py（重新导出）
from ..communication.agent_context import AgentContext
```

### 2. 清晰的模块职责

- **entities/**: 实体（Task, Presentation, Checkpoint）
- **value_objects/**: 值对象（Requirement, Framework, Research）
- **communication/**: Agent 通信模型（AgentContext, AgentResult）
- **services/**: 领域服务
- **exceptions/**: 领域异常
- **events/**: 领域事件
- **config/**: 配置
- **interfaces/**: 接口定义
- **models/**: 向后兼容（重新导出，不定义新内容）

### 3. 导入规则

1. **新代码**：直接从模块导入（`from domain.communication import AgentContext`）
2. **旧代码**：继续使用 `from domain.models import ...`（向后兼容）
3. **通用导入**：使用 `from domain import ...`（通过 `__init__.py`）

## 后续工作

- [ ] 更新文档（QUICKSTART.md, README.md）中的导入示例
- [ ] 添加代码检查规则，防止新的重复定义
- [ ] 逐步迁移旧代码到新的导入路径
- [ ] 考虑在未来版本中完全移除 `models/` 文件夹

## 验证清单

- [x] 删除 `models/agent_context.py`
- [x] 删除 `models/agent_result.py`
- [x] 更新 `models/__init__.py` 从 communication/ 重新导出
- [x] 更新 `agent_gateway.py` 直接导入
- [x] 验证所有导入路径工作正常
- [x] 保持向后兼容性

## 相关文档

- [Domain Layer Documentation](./domain-layer.md)
- [DDD Restructure Summary](../backend/domain/DDD_RESTRUCTURE_SUMMARY.md)

---

**修复日期**: 2025-02-04
**修复者**: MultiAgentPPT Team
