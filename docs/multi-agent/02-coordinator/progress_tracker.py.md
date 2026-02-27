# progress_tracker.py 详解

> 进度跟踪器 - 实时追踪和报告 PPT 生成工作流的进度

---

## 目录

1. [概述](#概述)
2. [核心概念](#核心概念)
3. [数据结构](#数据结构)
4. [ProgressTracker 类](#progresstracker-类)
5. [StageProgressMapper 类](#stageprogressmapper-类)
6. [使用示例](#使用示例)
7. [最佳实践](#最佳实践)

---

## 概述

### 作用

`progress_tracker.py` 提供实时进度跟踪功能，让用户知道 PPT 生成任务进行到哪一步了。

### 为什么需要

- ❌ **没有它**：用户不知道任务进度，只能干等
- ✅ **有它**：实时反馈进度百分比，提升用户体验

### 形象比喻

就像外卖订单的状态显示：
- "已下单" → "制作中" → "配送中" → "已送达"

---

## 核心概念

### 1. 进度更新（ProgressUpdate）

每次进度变化时产生的数据快照：

```python
@dataclass
class ProgressUpdate:
    stage: str           # 当前阶段：如 "research"
    progress: int        # 进度百分比：0-100
    message: str         # 进度消息："Researching page 3/10"
    timestamp: datetime  # 时间戳
    metadata: Dict       # 额外信息
```

### 2. 进度跟踪器（ProgressTracker）

管理整个工作流的进度：

- 记录当前阶段和进度
- 触发回调函数（通知前端）
- 记录历史进度（用于调试）
- 计算阶段耗时

### 3. 阶段映射（StageProgressMapper）

将 LangGraph 的阶段名称映射到进度百分比：

```python
# 阶段权重
DEFAULT_STAGE_WEIGHTS = {
    "requirement_parser": 10,   # 0% → 10%
    "framework_designer": 20,   # 10% → 30%
    "research": 30,             # 30% → 60%
    "content_generation": 25,   # 60% → 85%
    "template_renderer": 15,    # 85% → 100%
}
```

---

## 数据结构

### ProgressUpdate

```python
@dataclass
class ProgressUpdate:
    """
    进度更新数据结构

    Attributes:
        stage: 当前阶段名称
        progress: 进度百分比 (0-100)
        message: 进度消息
        timestamp: 更新时间戳
        metadata: 额外元数据
    """
    stage: str
    progress: int
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于 JSON 序列化）"""
        return {
            "stage": self.stage,
            "progress": self.progress,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
```

---

## ProgressTracker 类

### 初始化

```python
def __init__(
    self,
    task_id: str,
    on_progress: Optional[Callable[[ProgressUpdate], None]] = None,
    on_stage_complete: Optional[Callable[[str, PPTGenerationState], None]] = None,
    on_error: Optional[Callable[[str, Exception], None]] = None,
):
    """
    初始化进度跟踪器

    Args:
        task_id: 任务标识符
        on_progress: 进度回调函数 (progress_update)
        on_stage_complete: 阶段完成回调 (stage_name, state)
        on_error: 错误回调 (stage_name, error)
    """
```

### 阶段常量

```python
class ProgressTracker:
    # Stage definitions
    STAGE_INIT = "init"
    STAGE_REQUIREMENT_PARSING = "requirement_parsing"
    STAGE_FRAMEWORK_DESIGN = "framework_design"
    STAGE_RESEARCH = "research"
    STAGE_CONTENT_GENERATION = "content_generation"
    STAGE_QUALITY_CHECK = "quality_check"
    STAGE_REFINEMENT = "refinement"
    STAGE_TEMPLATE_RENDERING = "template_rendering"
    STAGE_COMPLETE = "complete"
```

### 核心方法

#### update_stage()

```python
def update_stage(
    self,
    stage: str,
    progress: int,
    message: str = "",
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    更新进度并触发回调

    Args:
        stage: 当前阶段名称
        progress: 进度百分比 (0-100)
        message: 进度消息
        metadata: 可选元数据
    """
    # 1. 限制进度范围
    progress = max(0, min(100, progress))

    # 2. 跟踪阶段时间
    if stage != self._current_stage:
        self._stage_start_times[stage] = datetime.now()
        self._current_stage = stage

    # 3. 创建更新
    update = ProgressUpdate(
        stage=stage,
        progress=progress,
        message=message or f"Processing {stage}",
        timestamp=datetime.now(),
        metadata=metadata or {},
    )

    # 4. 保存到历史
    self._progress_history.append(update)

    # 5. 触发回调
    if self.on_progress:
        try:
            self.on_progress(update)
        except Exception as e:
            logger.error(f"[ProgressTracker] Progress callback error: {e}")
```

#### stage_complete()

```python
def stage_complete(
    self,
    stage: str,
    state: PPTGenerationState,
):
    """
    标记阶段为完成并触发回调

    Args:
        stage: 阶段名称
        state: 当前状态
    """
    update = ProgressUpdate(
        stage=stage,
        progress=100,
        message=f"{stage} completed",
        timestamp=datetime.now(),
        metadata={"stage_complete": True},
    )

    self._progress_history.append(update)

    # 触发回调
    if self.on_stage_complete:
        try:
            self.on_stage_complete(stage, state)
        except Exception as e:
            logger.error(f"[ProgressTracker] Stage complete callback error: {e}")
```

#### error()

```python
def error(
    self,
    stage: str,
    error: Exception,
):
    """
    处理错误并触发回调

    Args:
        stage: 发生错误的阶段
        error: 异常
    """
    update = ProgressUpdate(
        stage=stage,
        progress=self._current_progress,
        message=f"Error in {stage}: {str(error)}",
        timestamp=datetime.now(),
        metadata={"error": True, "error_type": type(error).__name__},
    )

    self._progress_history.append(update)

    # 触发回调
    if self.on_error:
        try:
            self.on_error(stage, error)
        except Exception as e:
            logger.error(f"[ProgressTracker] Error callback error: {e}")
```

#### 查询方法

```python
def get_elapsed_time(self) -> float:
    """获取总经过时间（秒）"""

def get_stage_elapsed_time(self, stage: str) -> Optional[float]:
    """获取特定阶段的经过时间"""

def get_history(self) -> List[Dict[str, Any]]:
    """获取进度历史"""

def get_summary(self) -> Dict[str, Any]:
    """获取进度摘要"""
    return {
        "task_id": self.task_id,
        "current_stage": self._current_stage,
        "current_progress": self._current_progress,
        "elapsed_time_seconds": self.get_elapsed_time(),
        "total_updates": len(self._progress_history),
    }
```

---

## StageProgressMapper 类

### 作用

将 LangGraph 的节点名称映射到进度百分比。

### 阶段权重

```python
class StageProgressMapper:
    """将 LangGraph 阶段映射到进度百分比"""

    # Default stage weights (sums to 100)
    DEFAULT_STAGE_WEIGHTS = {
        "requirement_parser": 10,
        "framework_designer": 20,
        "research": 30,
        "content_generation": 25,
        "quality_check": 10,
        "template_renderer": 5,
    }
```

### 核心方法

#### get_progress_for_stage()

```python
@classmethod
def get_progress_for_stage(
    cls,
    stage: str,
    stage_weights: Optional[Dict[str, int]] = None,
) -> int:
    """
    获取阶段的进度百分比（阶段开始时的进度）

    Args:
        stage: 阶段名称
        stage_weights: 可选的自定义阶段权重

    Returns:
        进度百分比

    Example:
        >>> StageProgressMapper.get_progress_for_stage("research")
        30  # research 阶段开始时，进度是 30%
    """
    weights = stage_weights or cls.DEFAULT_STAGE_WEIGHTS

    # 计算此阶段之前的累积进度
    progress = 0
    for s, w in weights.items():
        if s == stage:
            return progress
        progress += w

    return progress
```

#### get_stage_progress_range()

```python
@classmethod
def get_stage_progress_range(
    cls,
    stage: str,
    stage_weights: Optional[Dict[str, int]] = None,
) -> tuple[int, int]:
    """
    获取阶段的进度范围 (开始, 结束)

    Args:
        stage: 阶段名称
        stage_weights: 可选的自定义阶段权重

    Returns:
        (start_progress, end_progress) 元组

    Example:
        >>> StageProgressMapper.get_stage_progress_range("research")
        (30, 60)  # research 阶段从 30% 进行到 60%
    """
    weights = stage_weights or cls.DEFAULT_STAGE_WEIGHTS

    start = 0
    found = False

    for s, w in weights.items():
        if found:
            return (start, start + w)
        if s == stage:
            found = True
            start += w

    if found:
        return (start, 100)

    return (0, 0)
```

---

## 使用示例

### 1. 基本使用

```python
from backend.agents_langchain.coordinator.progress_tracker import (
    create_progress_tracker,
    ProgressUpdate
)

# 创建进度跟踪器
tracker = create_progress_tracker(
    state=initial_state,
    on_progress=lambda update: print(f"Progress: {update.progress}% - {update.message}"),
    on_stage_complete=lambda stage, state: print(f"Stage {stage} completed!"),
    on_error=lambda stage, error: print(f"Error in {stage}: {error}"),
)

# 更新进度
tracker.update_stage("research", 35, "Researching page 3/10")
# 输出: Progress: 35% - Researching page 3/10

# 标记阶段完成
tracker.stage_complete("research", state)
# 输出: Stage research completed!

# 获取摘要
summary = tracker.get_summary()
print(summary)
# {
#     "task_id": "task_abc123",
#     "current_stage": "research",
#     "current_progress": 35,
#     "elapsed_time_seconds": 12.5,
#     "total_updates": 5
# }
```

### 2. 在工作流中使用

```python
async def generate_ppt_with_progress(user_input: str):
    # 创建状态
    state = create_initial_state(user_input, "task_001")

    # 创建进度跟踪器
    tracker = create_progress_tracker(
        state=state,
        on_progress=lambda update: send_to_frontend(update),
    )

    try:
        # 阶段1：需求解析
        tracker.update_stage("requirement_parser", 0, "Parsing requirements")
        state = await requirement_agent.run(state)
        tracker.stage_complete("requirement_parser", state)

        # 阶段2：框架设计
        tracker.update_stage("framework_designer", 10, "Designing framework")
        state = await framework_agent.run(state)
        tracker.stage_complete("framework_designer", state)

        # ... 其他阶段

    except Exception as e:
        tracker.error("generation", e)
        raise
```

### 3. 自定义阶段权重

```python
# 如果某些阶段耗时更长，可以调整权重
custom_weights = {
    "requirement_parser": 5,    # 快速，只占5%
    "framework_designer": 10,   # 较快，占10%
    "research": 50,             # 最慢，占50%
    "content_generation": 30,   # 慢，占30%
    "template_renderer": 5,     # 快速，占5%
}

# 获取自定义进度
progress = StageProgressMapper.get_progress_for_stage(
    "research",
    stage_weights=custom_weights
)
# 返回: 15 (5 + 10)
```

### 4. 获取历史记录

```python
# 执行完成后，查看所有进度更新
history = tracker.get_history()

for update in history:
    print(f"[{update['timestamp']}] {update['stage']}: {update['progress']}%")

# 输出:
# [2024-01-01 10:00:00] init: 0%
# [2024-01-01 10:00:05] requirement_parser: 5%
# [2024-01-01 10:00:10] requirement_parser: 10%
# [2024-01-01 10:00:15] framework_designer: 15%
# ...
```

---

## 最佳实践

### 1. 回调函数异常处理

⚠️ **问题**：回调函数可能抛出异常，中断主流程

✅ **解决**：在触发回调时捕获异常

```python
# ProgressTracker 已经做了异常处理
if self.on_progress:
    try:
        self.on_progress(update)
    except Exception as e:
        logger.error(f"Progress callback error: {e}")
        # 继续执行，不中断主流程
```

### 2. 进度值限制

⚠️ **问题**：进度值可能超出 0-100 范围

✅ **解决**：自动限制范围

```python
def update_stage(self, stage: str, progress: int, message: str = ""):
    # 限制进度范围
    progress = max(0, min(100, progress))
    # ...
```

### 3. 阶段时间跟踪

✅ **建议**：利用时间跟踪分析性能瓶颈

```python
# 获取各阶段耗时
for stage in ["requirement_parser", "research", "content_generation"]:
    elapsed = tracker.get_stage_elapsed_time(stage)
    print(f"{stage}: {elapsed:.2f}s")

# 输出:
# requirement_parser: 5.23s
# research: 45.67s  ← 瓶颈！
# content_generation: 32.10s
```

### 4. 元数据使用

✅ **建议**：利用元数据传递额外信息

```python
# 传递详细信息
tracker.update_stage(
    "research",
    35,
    "Researching page 3/10",
    metadata={
        "current_page": 3,
        "total_pages": 10,
        "estimated_time_remaining": 120,  # 秒
    }
)
```

### 5. JSON 序列化

✅ **建议**：使用 `to_dict()` 方法进行序列化

```python
update = ProgressUpdate(
    stage="research",
    progress=35,
    message="Researching..."
)

# 可以直接序列化为 JSON
import json
json_str = json.dumps(update.to_dict())
```

---

## 调试技巧

### 1. 查看完整历史

```python
# 打印所有进度更新
for update_dict in tracker.get_history():
    print(f"{update_dict['timestamp']} - {update_dict['stage']}: {update_dict['progress']}%")
```

### 2. 检查回调是否被调用

```python
# 添加日志
def my_callback(update: ProgressUpdate):
    print(f"[CALLBACK] Progress: {update.progress}%")

tracker = create_progress_tracker(
    state=state,
    on_progress=my_callback,
)
```

### 3. 模拟进度更新

```python
# 测试时模拟进度更新
for i in range(0, 101, 10):
    tracker.update_stage("test", i, f"Progress {i}%")
    time.sleep(0.1)  # 模拟耗时
```

---

## 常见问题

### Q1: 如何自定义进度显示？

A: 通过 `on_progress` 回调自定义显示方式：

```python
def my_progress_display(update: ProgressUpdate):
    # 自定义显示逻辑
    print(f"📊 {update.stage}: {update.progress}%")
    print(f"   {update.message}")
    # 发送到前端、写入文件等

tracker = create_progress_tracker(
    state=state,
    on_progress=my_progress_display,
)
```

### Q2: 如何在不同阶段使用不同的进度权重？

A: 使用 `stage_weights` 参数：

```python
custom_weights = {
    "requirement_parser": 5,
    "framework_designer": 15,
    "research": 40,
    "content_generation": 30,
    "template_renderer": 10,
}

progress = StageProgressMapper.get_progress_for_stage(
    "research",
    stage_weights=custom_weights
)
```

### Q3: 如何处理回调中的异常？

A: ProgressTracker 已经自动捕获回调异常，不会中断主流程。如需自定义处理：

```python
def safe_callback(update: ProgressUpdate):
    try:
        # 可能抛出异常的操作
        send_to_frontend(update)
    except Exception as e:
        logger.error(f"Callback failed: {e}")
        # 其他恢复逻辑

tracker = create_progress_tracker(
    state=state,
    on_progress=safe_callback,
)
```

---

## 相关文档

- [设计指南](./design-guide.md) - Coordinator 层设计
- [实施指南](./implementation-guide.md) - 如何实现 progress_tracker
- [RevisionHandler 文档](./revision_handler.py.md) - 修订处理详解
