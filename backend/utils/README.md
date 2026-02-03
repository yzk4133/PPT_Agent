# Utils Layer

## 定位

通用工具函数层，提供纯函数、无状态的业务无关工具。

## 设计原则

1. **纯函数**: 无副作用，输出仅依赖于输入
2. **无状态**: 不依赖配置、不涉及外部服务
3. **高度复用**: 可在任何项目中独立使用
4. **业务无关**: 不包含特定业务逻辑

## 目录结构

```
utils/
├── save_ppt/                   # PPT文件操作工具
│   ├── main_api.py             # PPT生成API
│   ├── ppt_generator.py        # PPT生成器
│   └── look_master.py          # 样式管理
├── common/                     # ⚠️ 已弃用（已迁移到 infrastructure）
│   └── __init__.py             # 仅保留向后兼容
└── README.md                   # 本文档
```

## 与 Infrastructure 的区别

| 方面 | Utils Layer | Infrastructure Layer |
|------|-------------|---------------------|
| 职责 | 纯函数工具 | 技术基础设施和服务 |
| 状态 | 无状态 | 可有状态（数据库连接、缓存等） |
| 配置依赖 | 不依赖配置 | 依赖配置（环境变量、Feature Flags） |
| 外部服务 | 不涉及 | 涉及（LLM、数据库、MCP等） |
| 示例 | 文本处理、文件操作 | 配置管理、模型工厂 |

## 迁移说明

`utils/common` 模块已迁移到 `infrastructure` 层。

### 导入路径迁移对照表

| 旧路径 | 新路径 |
|--------|--------|
| `from utils.common import get_config` | `from infrastructure.config import get_config` |
| `from utils.common.model_factory import create_model_with_fallback` | `from infrastructure.llm import create_model_with_fallback` |
| `from utils.common.tool_manager import UnifiedToolManager` | `from infrastructure.tools import UnifiedToolManager` |
| `from utils.common.context_compressor import ContextCompressor` | `from infrastructure.utils import ContextCompressor` |
| `from utils.common.retry_decorator import retry_with_exponential_backoff` | `from infrastructure.llm import retry_with_exponential_backoff` |
| `from utils.common.fallback import JSONFallbackParser` | `from infrastructure.llm.fallback import JSONFallbackParser` |

详细迁移路径请参考 `utils/common/__init__.py` 中的文档。

## 添加新工具

当添加新的通用工具时，请遵循以下原则：

1. **纯函数**: 工具函数应该是纯函数，无副作用
2. **类型注解**: 使用类型注解提高可读性
3. **文档字符串**: 添加清晰的文档字符串
4. **测试**: 为工具函数编写单元测试

### 示例

```python
# utils/text_processing/text_utils.py
from typing import str

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本到指定长度。

    Args:
        text: 要截断的文本
        max_length: 最大长度
        suffix: 截断后添加的后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
```
