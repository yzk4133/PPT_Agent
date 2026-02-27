"""
Models Module

包含数据模型：
- ExecutionMode: 执行模式
- Checkpoint: 检查点
- CheckpointSummary: 检查点摘要
"""

# PPT generation models
from .execution_mode import ExecutionMode
from .checkpoint import Checkpoint, CheckpointSummary

__all__ = [
    # PPT generation models
    "ExecutionMode",
    "Checkpoint",
    "CheckpointSummary",
]
