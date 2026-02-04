# 导入优化指南

## 概述

项目已优化导入系统，通过以下方式简化导入语句：

1. ✅ **统一的 `__init__.py` 导出** - 每个层级提供简洁的重新导出
2. ✅ **PYTHONPATH 配置** - 通过 `pyproject.toml` 和 `.vscode/settings.json` 配置
3. ✅ **移除手动路径操作** - 清除所有 `sys.path.insert()` 调用
4. ✅ **延迟导入** - 避免循环依赖

## 配置说明

### PYTHONPATH 配置

项目根目录已自动添加到 Python 路径：

- **VS Code**: 在 `.vscode/settings.json` 中已配置
- **命令行**: 使用 `PYTHONPATH=.` 或 `pip install -e .`

### 安装项目（推荐）

```bash
# 在项目根目录执行
pip install -e .

# 现在可以直接从 backend 导入
# 而无需关心文件位置
```

## 简化的导入方式

### ❌ 旧方式（长路径导入）

```python
# 不再需要这样
from agents.core.planning.requirements.requirement_parser_agent import requirement_parser_agent
from agents.orchestrator.components.progress_tracker import get_progress_tracker
from infrastructure.config.common_config import get_config
from infrastructure.llm.fallback import JSONFallbackParser
```

### ✅ 新方式（简洁导入）

```python
# 方式1: 从 backend 顶层导入（最简洁）
from backend import (
    requirement_parser_agent,
    get_progress_tracker,
    get_config,
    JSONFallbackParser,
)

# 方式2: 从各层导入
from agents import requirement_parser_agent
from infrastructure import get_config, JSONFallbackParser
from services import TaskService, PresentationService

# 方式3: 从具体模块导入（仍然有效）
from agents.core.planning import requirement_parser_agent
from infrastructure.config import get_config
```

## 各层导入参考

### 1. 领域层 (Domain)

```python
# 推荐方式
from domain import (
    Task, TaskStatus, TaskStage,
    Requirement, PPTFramework,
    task_progress_service,
    task_validation_service,
)

# 或者从 backend 导入
from backend import Task, TaskStatus, task_progress_service
```

### 2. Agent 层

```python
# 推荐: 从 agents 导入
from agents import (
    requirement_parser_agent,
    framework_designer_agent,
    master_coordinator_agent,
    get_progress_tracker,
)

# 或者从 backend 导入
from backend import master_coordinator_agent
```

### 3. 基础设施层 (Infrastructure)

```python
# 推荐: 从 infrastructure 导入
from infrastructure import (
    get_config,
    JSONFallbackParser,
    setup_exception_handlers,
    PasswordHandler,
    JWTHandler,
)

# 或者从 backend 导入
from backend import get_config, JSONFallbackParser
```

### 4. 服务层 (Services)

```python
# 推荐: 从 services 导入
from services import (
    TaskService,
    PresentationService,
    OutlineService,
)

# 或者从 backend 导入
from backend import TaskService, PresentationService
```

### 5. Google ADK / GenAI

```python
# 推荐: 从 backend 导入
from backend import (
    BaseAgent, LlmAgent,
    InvocationContext, CallbackContext,
    Event, genai_types,
)

# 或者直接导入
from google.adk.agents import BaseAgent, LlmAgent
```

## 迁移指南

### 步骤1: 运行清理脚本

```bash
# 清理所有 sys.path.insert 调用
python scripts/clean_imports.py
```

### 步骤2: 更新导入语句

使用以下规则更新你的导入：

| 旧导入 | 新导入 |
|--------|--------|
| `from agents.core.planning.requirements.requirement_parser_agent import requirement_parser_agent` | `from agents import requirement_parser_agent` |
| `from infrastructure.config.common_config import get_config` | `from infrastructure import get_config` |
| `from agents.orchestrator.components.progress_tracker import get_progress_tracker` | `from agents import get_progress_tracker` |
| `from services.task_service import TaskService` | `from services import TaskService` |

### 步骤3: 验证导入

```bash
# 运行测试验证
pytest backend/ -v

# 或者运行应用
python -m backend.api.main
```

## 常见问题

### Q: 为什么会出现 `ImportError`?

**A**: 请确保已配置 PYTHONPATH：

```bash
# 方式1: 设置环境变量
export PYTHONPATH=.

# 方式2: 安装项目
pip install -e .

# 方式3: 使用 -m 参数运行
python -m backend.api.main
```

### Q: 如何处理循环导入?

**A**: 使用以下策略：

1. **延迟导入**: 在函数内部导入而非模块顶部
2. **使用 `TYPE_CHECKING`**: 类型提示时导入
3. **重新设计**: 考虑模块职责划分

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from some_module import SomeClass

def my_function():
    from some_module import SomeClass  # 延迟导入
    ...
```

### Q: infrastructure 模块如何避免循环导入?

**A**: infrastructure 使用 `__getattr__` 实现延迟导入：

```python
# infrastructure/__init__.py
def __getattr__(name: str):
    """延迟导入，避免循环依赖"""
    if name == "get_config":
        from infrastructure.config.common_config import get_config
        return get_config
    raise AttributeError(f"module 'infrastructure' has no attribute '{name}'")
```

## 最佳实践

### ✅ DO

- ✅ 从 `backend` 或各层 `__init__.py` 导入
- ✅ 使用有意义的别名避免冲突
- ✅ 按标准库、第三方库、本地模块分组导入
- ✅ 使用 `isort` 自动排序导入

```python
# 标准库
import asyncio
from typing import Optional

# 第三方库
from fastapi import FastAPI
from pydantic import Field

# 本地模块（使用简化导入）
from backend import Task, TaskStatus
from agents import master_coordinator_agent
from infrastructure import get_config
```

### ❌ DON'T

- ❌ 不要使用深层路径导入（除非必要）
- ❌ 不要在代码中使用 `sys.path.insert()`
- ❌ 不要使用相对导入（`from .. import`）
- ❌ 不要在函数外延迟导入

```python
# ❌ 避免这样
from agents.core.planning.requirements.requirement_parser_agent import requirement_parser_agent
sys.path.insert(0, os.path.join(...))
```

## 工具推荐

### 自动排序导入

```bash
# 安装 isort
pip install isort

# 自动排序导入
isort backend/

# 检查导入
isort backend/ --check-only
```

### VS Code 设置

已在 `.vscode/settings.json` 中配置：

```json
{
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

## 相关文件

- 📄 `backend/__init__.py` - 顶层导入导出
- 📄 `pyproject.toml` - 项目配置
- 📄 `.vscode/settings.json` - VS Code 配置
- 🔧 `scripts/clean_imports.py` - 清理脚本

## 更新日志

- **2026-02-04**: 初始版本
  - 创建统一的 `__init__.py` 导出
  - 配置 PYTHONPATH
  - 添加清理脚本
