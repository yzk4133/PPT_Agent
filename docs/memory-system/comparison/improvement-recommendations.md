# 改进建议与实施指南

> **版本：** 1.0.0 | **更新时间：** 2026-02-10

---

## 目录

- [第一部分：短期优化 (1-2周实现)](#第一部分短期优化-1-2周实现)
- [第二部分：长期重构 (1-2个月实现)](#第二部分长期重构-1-2个月实现)
- [第三部分：混合架构方案](#第三部分混合架构方案)
- [附录](#附录)

---

## 第一部分：短期优化 (1-2周实现)

### 优化 1：消息压缩机制 ⭐⭐⭐

**优先级：** 高 | **工作量：** 3-5 天 | **收益：** 减少 50-70% token 使用

---

#### 问题描述

MultiAgentPPT 当前无消息压缩机制，长对话可能导致：
1. Token 溢出超过模型上下文限制
2. API 调用成本增加
3. 响应速度下降

OpenCode 通过自动压缩机制有效解决了这个问题。

---

#### 实施方案

**Step 1: 添加 Token 计数**

```python
# backend/memory/utils/token_counter.py

import tiktoken
from typing import List, Dict, Any

class TokenCounter:
    """Token 计数器"""

    def __init__(self, model: str = "gpt-4"):
        self.encoding = tiktoken.encoding_for_model(model)

    def count_messages(self, messages: List[Dict[str, Any]]) -> int:
        """计算消息列表的 token 数量"""
        num_tokens = 0
        for message in messages:
            num_tokens += self.count_message(message)
        return num_tokens

    def count_message(self, message: Dict[str, Any]) -> int:
        """计算单条消息的 token 数量"""
        num_tokens = 0
        # 消息角色
        num_tokens += len(self.encoding.encode(message.get("role", "")))
        # 消息内容
        content = message.get("content", "")
        num_tokens += len(self.encoding.encode(content))
        return num_tokens

    def count_string(self, text: str) -> int:
        """计算文本的 token 数量"""
        return len(self.encoding.encode(text))

# 使用示例
counter = TokenCounter()
token_count = counter.count_messages(messages)
```

**Step 2: 检测消息溢出**

```python
# backend/memory/services/message_compression.py

import logging
from typing import List, Dict, Any
from .token_counter import TokenCounter

logger = logging.getLogger(__name__)

class MessageCompressionService:
    """消息压缩服务"""

    def __init__(self, model_limit: int = 128000):
        self.model_limit = model_limit
        self.counter = TokenCounter()

    async def is_overflow(self, messages: List[Dict[str, Any]]) -> bool:
        """检测消息是否溢出"""
        tokens = self.counter.count_messages(messages)
        return tokens > self.model_limit

    async def get_token_count(self, messages: List[Dict[str, Any]]) -> int:
        """获取当前 token 数量"""
        return self.counter.count_messages(messages)

    async def should_compact(self, messages: List[Dict[str, Any]]) -> bool:
        """判断是否需要压缩"""
        # 超过 80% 限制时开始压缩
        tokens = await self.get_token_count(messages)
        return tokens > self.model_limit * 0.8
```

**Step 3: 实现压缩策略**

```python
# backend/memory/services/message_compression.py (续)

import json
from datetime import datetime

class MessageCompressionService:
    # ...

    async def compact_messages(
        self,
        messages: List[Dict[str, Any]],
        strategy: str = "truncate"
    ) -> List[Dict[str, Any]]:
        """
        压缩消息列表

        Args:
            messages: 原始消息列表
            strategy: 压缩策略
                - "truncate": 截断旧消息
                - "summary": 生成摘要
                - "compact": 紧凑化工具结果

        Returns:
            压缩后的消息列表
        """
        if strategy == "truncate":
            return await self._compact_by_truncation(messages)
        elif strategy == "summary":
            return await self._compact_by_summary(messages)
        elif strategy == "compact":
            return await self._compact_by_compaction(messages)
        else:
            raise ValueError(f"Unknown compression strategy: {strategy}")

    async def _compact_by_truncation(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """通过截断旧消息压缩"""
        # 保留最新的 N 条消息
        keep_count = 20

        # 插入压缩标记
        compact_marker = {
            "role": "system",
            "content": f"[Previous messages were truncated to fit context. "
                      f"Showing the last {keep_count} messages only.]",
            "timestamp": datetime.now().isoformat(),
            "compact": True
        }

        return [compact_marker] + messages[-keep_count:]

    async def _compact_by_summary(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """通过生成摘要压缩"""
        # 1. 将旧消息分组
        old_messages = messages[:-10]
        recent_messages = messages[-10:]

        # 2. 生成摘要
        summary = await self._generate_summary(old_messages)

        # 3. 插入摘要消息
        summary_message = {
            "role": "system",
            "content": f"[Summary of previous conversation]\n{summary}",
            "timestamp": datetime.now().isoformat(),
            "summary": True
        }

        return [summary_message] + recent_messages

    async def _compact_by_compaction(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """通过紧凑化工具结果压缩"""
        compacted = []

        for msg in messages:
            # 紧凑化助手消息中的长内容
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                if len(content) > 1000:
                    msg = {
                        **msg,
                        "content": content[:500] + "\n\n[Content compacted to save tokens...]",
                        "compacted": True
                    }

            compacted.append(msg)

        return compacted

    async def _generate_summary(
        self,
        messages: List[Dict[str, Any]]
    ) -> str:
        """使用 LLM 生成对话摘要"""
        # 将消息转换为文本
        conversation = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in messages
        ])

        # 调用 LLM 生成摘要
        summary_prompt = f"""
        Please summarize the following conversation concisely:

        {conversation}

        Summary:
        """

        # 这里需要调用实际的 LLM
        # 示例代码：
        # from langchain.llms import OpenAI
        # llm = OpenAI(temperature=0)
        # summary = await llm.agenerate([summary_prompt])
        # return summary.generations[0][0].text

        # 临时返回占位符
        return "[Summary would be generated by LLM here]"
```

**Step 4: 集成到 Agent**

```python
# backend/agents/core/base_agent.py (修改)

from backend.memory.services.message_compression import MessageCompressionService

class MemoryAwareAgent:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.compression_service = MessageCompressionService()

    async def _get_memory(self, state: Dict[str, Any]):
        """初始化记忆服务"""
        # ... 原有代码 ...

        # 检查是否需要压缩
        if await self.compression_service.should_compact(
            state.get("messages", [])
        ):
            logger.info("Compacting messages...")
            state["messages"] = await self.compression_service.compact_messages(
                state["messages"],
                strategy="summary"  # 可配置
            )
```

**Step 5: 配置化**

```python
# backend/infrastructure/config/common_config.py

class MemoryConfig:
    """记忆系统配置"""

    # 消息压缩配置
    ENABLE_MESSAGE_COMPRESSION: bool = True
    COMPRESSION_STRATEGY: str = "summary"  # "truncate" | "summary" | "compact"
    MODEL_TOKEN_LIMIT: int = 128000
    COMPRESSION_THRESHOLD: float = 0.8  # 80% 时触发压缩

    # 消息保留配置
    MIN_RECENT_MESSAGES: int = 10  # 最少保留的消息数
```

---

#### 预期收益

| 指标 | 改进前 | 改进后 | 提升 |
|------|-------:|-------:|-----:|
| Token 使用 | 100% | 30-50% | 50-70% ↓ |
| API 成本 | $1.00 | $0.30-0.50 | 50-70% ↓ |
| 响应速度 | 基准 | +20-30% | 20-30% ↑ |

---

#### 风险与注意事项

1. **信息丢失风险**
   - 截断策略：可能丢失早期重要信息
   - 缓解：保留系统消息、关键决策点

2. **摘要质量问题**
   - LLM 摘要可能不准确
   - 缓解：使用温度=0 的模型、保留原始消息引用

3. **性能影响**
   - 压缩操作需要额外时间
   - 缓解：异步执行、缓存摘要结果

---

### 优化 2：异步写入优化 ⭐⭐

**优先级：** 中 | **工作量：** 2-3 天 | **收益：** 减少 30-50% 响应延迟

---

#### 问题描述

当前同步写入数据库会阻塞主流程，影响用户体验。

---

#### 实施方案

**创建异步写入队列：**

```python
# backend/infrastructure/async_writer.py

import asyncio
import logging
from typing import Any, Callable, Awaitable
from collections import deque

logger = logging.getLogger(__name__)

class AsyncWriter:
    """异步写入器 - 队列化写操作"""

    def __init__(self, max_queue_size: int = 1000, workers: int = 2):
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.workers = workers
        self.running = False
        self._worker_tasks: List[asyncio.Task] = []

    async def start(self):
        """启动异步写入器"""
        if self.running:
            return

        self.running = True
        self._worker_tasks = [
            asyncio.create_task(self._write_worker(i))
            for i in range(self.workers)
        ]
        logger.info(f"AsyncWriter started with {self.workers} workers")

    async def stop(self):
        """停止异步写入器"""
        if not self.running:
            return

        self.running = False

        # 等待队列清空
        await self.queue.join()

        # 取消 worker 任务
        for task in self._worker_tasks:
            task.cancel()

        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        logger.info("AsyncWriter stopped")

    async def _write_worker(self, worker_id: int):
        """写入工作协程"""
        logger.info(f"Write worker {worker_id} started")

        while self.running:
            try:
                # 获取写入任务
                write_task = await self.queue.get()

                # 执行写入
                try:
                    await write_task.func(*write_task.args, **write_task.kwargs)
                    write_task.future.set_result(None)
                except Exception as e:
                    logger.error(f"Write worker {worker_id} error: {e}")
                    write_task.future.set_exception(e)

                finally:
                    self.queue.task_done()

            except asyncio.CancelledError:
                break

        logger.info(f"Write worker {worker_id} stopped")

    async def write(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any
    ) -> asyncio.Future:
        """
        异步写入

        Args:
            func: 异步写入函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Future 对象，可 await 等待完成
        """
        if not self.running:
            raise RuntimeError("AsyncWriter is not running")

        # 创建任务
        task = WriteTask(func, args, kwargs)

        # 加入队列
        await self.queue.put(task)

        return task.future

    def write_nowait(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any
    ) -> asyncio.Future:
        """非阻塞写入"""
        if not self.running:
            raise RuntimeError("AsyncWriter is not running")

        task = WriteTask(func, args, kwargs)

        try:
            self.queue.put_nowait(task)
        except asyncio.QueueFull:
            logger.warning("AsyncWriter queue is full, writing synchronously")
            # 队列满时同步写入
            loop = asyncio.get_event_loop()
            return loop.create_task(func(*args, **kwargs))

        return task.future


@dataclass
class WriteTask:
    """写入任务"""
    func: Callable[..., Awaitable[Any]]
    args: tuple
    kwargs: dict
    future: asyncio.Future = field(default_factory=lambda: asyncio.Future())

# 全局异步写入器
_async_writer: Optional[AsyncWriter] = None

def get_async_writer() -> AsyncWriter:
    """获取全局异步写入器"""
    global _async_writer
    if _async_writer is None:
        _async_writer = AsyncWriter(max_queue_size=1000, workers=2)
    return _async_writer
```

**集成到服务层：**

```python
# backend/memory/services/user_preference_service.py (修改)

from backend.infrastructure.async_writer import get_async_writer

class UserPreferenceService:
    # ...

    async def update_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """更新用户偏好（异步写入）"""
        if not self.db_session:
            return False

        try:
            profile = self._get_profile(user_id)

            if not profile:
                profile = UserProfile(user_id=user_id)
                self.db_session.add(profile)

            # 更新偏好
            for key, value in preferences.items():
                profile.set_preference(key, value)

            # 使用异步写入
            writer = get_async_writer()
            await writer.write(
                self._commit_and_invalidate,
                self.db_session,
                user_id
            )

            self.logger.info(f"Queued preference update for user {user_id}")
            return True

        except Exception as e:
            self.logger.error(f"Update preferences error: {e}")
            return False

    async def _commit_and_invalidate(
        self,
        session: Session,
        user_id: str
    ):
        """提交并使缓存失效"""
        try:
            session.commit()

            # 使缓存失效
            if self.enable_cache:
                await self.cache_client.delete_user_preferences(user_id)

        except Exception as e:
            session.rollback()
            raise
```

**启动时初始化：**

```python
# backend/main.py (修改)

from backend.infrastructure.async_writer import get_async_writer

async def startup():
    """应用启动"""
    # 启动异步写入器
    writer = get_async_writer()
    await writer.start()

    logger.info("AsyncWriter started")

async def shutdown():
    """应用关闭"""
    # 停止异步写入器
    writer = get_async_writer()
    await writer.stop()

    logger.info("AsyncWriter stopped")
```

---

#### 预期收益

| 指标 | 改进前 | 改进后 | 提升 |
|------|-------:|-------:|-----:|
| 响应延迟 | 100-200ms | 50-100ms | 50% ↓ |
| 吞吐量 | ~100 req/s | ~300 req/s | 200% ↑ |

---

### 优化 3：文件锁机制 ⭐⭐

**优先级：** 中 | **工作量：** 1-2 天 | **收益：** 避免并发冲突

---

#### 问题描述

检查点更新可能发生并发冲突，导致数据不一致。

---

#### 实施方案

**创建文件锁工具：**

```python
# backend/infrastructure/file_lock.py

import asyncio
import fcntl
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def file_lock(filepath: str, mode: str = 'r') -> AsyncIterator:
    """
    文件锁上下文管理器

    Args:
        filepath: 文件路径
        mode: 锁模式 ('r' 读锁, 'w' 写锁)

    Yields:
        文件对象
    """
    f = None
    try:
        # 打开文件
        f = open(filepath, mode)

        # 获取文件锁
        if mode == 'w':
            # 写锁（排他锁）
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        else:
            # 读锁（共享锁）
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)

        logger.debug(f"Acquired file lock: {filepath} ({mode})")
        yield f

    finally:
        # 释放锁
        if f:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            f.close()
            logger.debug(f"Released file lock: {filepath}")
```

**应用到检查点更新：**

```python
# backend/infrastructure/checkpoint/database_backend.py (修改)

from backend.infrastructure.file_lock import file_lock

class DatabaseCheckpointBackend:
    # ...

    async def save(self, checkpoint: Checkpoint) -> bool:
        """保存检查点（带锁）"""
        lock_file = f"/tmp/checkpoint_{checkpoint.task_id}.lock"

        async with file_lock(lock_file, 'w') as f:
            # 执行数据库操作
            try:
                existing = self.session.query(CheckpointModel).filter(
                    CheckpointModel.task_id == checkpoint.task_id
                ).first()

                if existing:
                    # 更新
                    existing.user_id = checkpoint.user_id
                    existing.phase = checkpoint.phase
                    # ... 其他字段
                else:
                    # 插入
                    model = CheckpointModel(
                        task_id=checkpoint.task_id,
                        user_id=checkpoint.user_id,
                        # ...
                    )
                    self.session.add(model)

                self.session.commit()
                return True

            except Exception as e:
                self.session.rollback()
                logger.error(f"Save checkpoint error: {e}")
                return False
```

**注意：** Windows 系统需要使用不同的锁机制。

```python
# Windows 版本的文件锁
import msvcrt

@asynccontextmanager
async def file_lock_windows(filepath: str, mode: str = 'r') -> AsyncIterator:
    """Windows 文件锁"""
    f = None
    try:
        f = open(filepath, mode)

        if mode == 'w':
            # Windows 写锁
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
        else:
            # Windows 读锁
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)

        yield f

    finally:
        if f:
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            f.close()
```

---

#### 预期收益

| 指标 | 改进前 | 改进后 |
|------|-------:|-------:|
| 并发冲突 | 偶发 | 0 |
| 数据一致性 | 99% | 100% |

---

## 第二部分：长期重构 (1-2个月实现)

### 重构 1：父子会话机制 ⭐⭐⭐

**优先级：** 高 | **工作量：** 2-3 周 | **收益：** 支持多路径探索

---

#### 问题描述

当前系统无法保存多路径探索，用户无法在同一基础上尝试不同方向。

---

#### 实施方案

**Step 1: 数据库 Schema 调整**

```sql
-- 添加 parent_id 字段
ALTER TABLE checkpoints
ADD COLUMN parent_id VARCHAR(255) NULL,
ADD COLUMN forked_from_message_id VARCHAR(255) NULL,
ADD COLUMN is_fork BOOLEAN DEFAULT FALSE;

-- 创建索引
CREATE INDEX idx_parent_id ON checkpoints(parent_id);
CREATE INDEX idx_fork ON checkpoints(is_fork);

-- 添加 fork 计数字段
ALTER TABLE checkpoints
ADD COLUMN fork_count INT DEFAULT 0;
```

**Step 2: Fork 功能实现**

```python
# backend/infrastructure/checkpoint/fork_manager.py

import logging
from typing import Optional
from datetime import datetime
from models.checkpoint import Checkpoint

logger = logging.getLogger(__name__)

class ForkManager:
    """会话 Fork 管理器"""

    def __init__(self, checkpoint_manager):
        self.checkpoint_manager = checkpoint_manager

    async def fork_checkpoint(
        self,
        parent_task_id: str,
        message_id: Optional[str] = None,
        new_title: Optional[str] = None
    ) -> Checkpoint:
        """
        Fork 检查点

        Args:
            parent_task_id: 父任务 ID
            message_id: 从哪条消息开始 fork（可选）
            new_title: 新会话标题（可选）

        Returns:
            新的检查点
        """
        # 1. 加载父检查点
        parent = await self.checkpoint_manager.load_checkpoint(parent_task_id)
        if not parent:
            raise ValueError(f"Parent checkpoint not found: {parent_task_id}")

        # 2. 生成新任务 ID
        from utils.id_generator import generate_task_id
        new_task_id = generate_task_id()

        # 3. 生成标题
        if not new_title:
            new_title = self._get_forked_title(parent.raw_user_input, parent.fork_count)

        # 4. 复制检查点数据
        new_checkpoint = Checkpoint(
            task_id=new_task_id,
            user_id=parent.user_id,
            execution_mode=parent.execution_mode,
            phase=parent.phase,
            raw_user_input=parent.raw_user_input,
            structured_requirements=parent.structured_requirements.copy(),
            ppt_framework=parent.ppt_framework.copy(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status="editing",
            version=1,
            parent_task_id=parent_task_id,
            forked_from_message_id=message_id,
            is_fork=True
        )

        # 5. 保存新检查点
        await self.checkpoint_manager.backend.save(new_checkpoint)

        # 6. 更新父检查点的 fork 计数
        parent.fork_count += 1
        await self.checkpoint_manager.backend.save(parent)

        logger.info(f"Forked checkpoint: {parent_task_id} -> {new_task_id}")
        return new_checkpoint

    def _get_forked_title(self, original_title: str, fork_count: int) -> str:
        """生成 fork 标题"""
        # 检查是否已有 fork 标记
        import re
        match = re.match(r'^(.+) \(fork #(\d+)\)$', original_title)
        if match:
            base = match.group(1)
            num = int(match.group(2)) + 1
            return f"{base} (fork #{num})"
        else:
            return f"{original_title} (fork #1)"

    async def get_fork_tree(self, root_task_id: str) -> dict:
        """
        获取 fork 树

        Returns:
            树形结构:
            {
                "task_id": "...",
                "children": [
                    {
                        "task_id": "...",
                        "children": [...]
                    }
                ]
            }
        """
        async def build_tree(task_id: str) -> dict:
            # 查找子检查点
            children = await self.checkpoint_manager.backend.list_by_parent(task_id)

            return {
                "task_id": task_id,
                "children": [
                    await build_tree(child.task_id)
                    for child in children
                ]
            }

        return await build_tree(root_task_id)

    async def list_forks(self, parent_task_id: str) -> list:
        """列出所有 fork"""
        return await self.checkpoint_manager.backend.list_by_parent(parent_task_id)
```

**Step 3: API 端点**

```python
# backend/api/routes/checkpoint.py (修改)

from fastapi import APIRouter, Depends
from backend.infrastructure.checkpoint.fork_manager import ForkManager

router = APIRouter()

@router.post("/checkpoint/{task_id}/fork")
async def fork_checkpoint(
    task_id: str,
    message_id: Optional[str] = None,
    title: Optional[str] = None,
    fork_manager: ForkManager = Depends(get_fork_manager)
):
    """Fork 检查点"""
    try:
        new_checkpoint = await fork_manager.fork_checkpoint(
            parent_task_id=task_id,
            message_id=message_id,
            new_title=title
        )
        return {"success": True, "checkpoint": new_checkpoint}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/checkpoint/{task_id}/forks")
async def list_forks(
    task_id: str,
    fork_manager: ForkManager = Depends(get_fork_manager)
):
    """列出所有 fork"""
    forks = await fork_manager.list_forks(task_id)
    return {"forks": forks}

@router.get("/checkpoint/{task_id}/tree")
async def get_fork_tree(
    task_id: str,
    fork_manager: ForkManager = Depends(get_fork_manager)
):
    """获取 fork 树"""
    tree = await fork_manager.get_fork_tree(task_id)
    return tree
```

**Step 4: UI 调整**

```typescript
// frontend/src/components/CheckpointTree.tsx (新建)

import React, { useEffect, useState } from 'react';

interface CheckpointNode {
  task_id: string;
  children: CheckpointNode[];
}

export const CheckpointTree: React.FC<{ rootTaskId: string }> = ({ rootTaskId }) => {
  const [tree, setTree] = useState<CheckpointNode | null>(null);

  useEffect(() => {
    fetch(`/api/checkpoint/${rootTaskId}/tree`)
      .then(res => res.json())
      .then(data => setTree(data));
  }, [rootTaskId]);

  const renderNode = (node: CheckpointNode) => (
    <li key={node.task_id}>
      <button onClick={() => loadCheckpoint(node.task_id)}>
        {node.task_id}
      </button>
      {node.children.length > 0 && (
        <ul>
          {node.children.map(child => renderNode(child))}
        </ul>
      )}
    </li>
  );

  if (!tree) return <div>Loading...</div>;

  return (
    <div className="checkpoint-tree">
      <h3>Session Forks</h3>
      <ul>{renderNode(tree)}</ul>
    </div>
  );
};
```

---

#### 预期收益

| 功能 | 改进前 | 改进后 |
|------|-------:|-------:|
| 多路径探索 | ❌ | ✅ |
| 实验性 | 低 | 高 |
| 用户体验 | 单一路线 | 多分支选择 |

---

### 重构 2：Git 快照集成 ⭐⭐

**优先级：** 中 | **工作量：** 2-3 周 | **收益：** 减少 70-80% 存储空间

---

#### 问题描述

检查点占用大量存储空间，缺少版本控制能力。

---

#### 实施方案

**Step 1: 初始化快照仓库**

```python
# backend/infrastructure/snapshot/git_snapshot.py

import subprocess
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class GitSnapshotManager:
    """Git 快照管理器"""

    def __init__(self, base_dir: str = "/data/snapshots"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_repo_path(self, project_id: str) -> Path:
        """获取项目仓库路径"""
        return self.base_dir / project_id / ".git"

    async def init_repo(self, project_id: str) -> bool:
        """初始化 Git 仓库"""
        repo_path = self._get_repo_path(project_id).parent
        git_dir = self._get_repo_path(project_id)

        if git_dir.exists():
            logger.info(f"Git repo already exists: {project_id}")
            return True

        try:
            # 创建目录
            repo_path.mkdir(parents=True, exist_ok=True)

            # 初始化 git
            subprocess.run(
                ["git", "init"],
                cwd=repo_path,
                capture_output=True,
                check=True
            )

            # 配置 git
            subprocess.run(
                ["git", "config", "user.email", "multiagent@ppt.local"],
                cwd=repo_path,
                capture_output=True,
                check=True
            )
            subprocess.run(
                ["git", "config", "user.name", "MultiAgentPPT"],
                cwd=repo_path,
                capture_output=True,
                check=True
            )

            logger.info(f"Initialized git repo: {project_id}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to init git repo: {e}")
            return False

    async def create_snapshot(
        self,
        project_id: str,
        data: dict,
        message: Optional[str] = None
    ) -> str:
        """
        创建快照

        Returns:
            commit hash
        """
        repo_path = self._get_repo_path(project_id).parent

        # 确保 repo 已初始化
        await self.init_repo(project_id)

        try:
            # 1. 写入数据文件
            data_file = repo_path / "snapshot.json"
            import json
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)

            # 2. 添加到 git
            subprocess.run(
                ["git", "add", "snapshot.json"],
                cwd=repo_path,
                capture_output=True,
                check=True
            )

            # 3. 提交
            commit_msg = message or f"Snapshot {datetime.now().isoformat()}"
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=repo_path,
                capture_output=True,
                check=True,
                text=True
            )

            # 4. 获取 commit hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                check=True,
                text=True
            )

            commit_hash = hash_result.stdout.strip()
            logger.info(f"Created snapshot: {project_id} -> {commit_hash}")
            return commit_hash

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create snapshot: {e}")
            raise

    async def restore_snapshot(
        self,
        project_id: str,
        commit_hash: str
    ) -> Optional[dict]:
        """恢复快照"""
        repo_path = self._get_repo_path(project_id).parent

        try:
            # 1. Checkout 到指定 commit
            subprocess.run(
                ["git", "checkout", commit_hash],
                cwd=repo_path,
                capture_output=True,
                check=True
            )

            # 2. 读取数据
            import json
            data_file = repo_path / "snapshot.json"
            with open(data_file, 'r') as f:
                data = json.load(f)

            logger.info(f"Restored snapshot: {project_id} -> {commit_hash}")
            return data

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restore snapshot: {e}")
            return None

    async def list_snapshots(self, project_id: str) -> list:
        """列出所有快照"""
        repo_path = self._get_repo_path(project_id).parent

        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "--all"],
                cwd=repo_path,
                capture_output=True,
                check=True,
                text=True
            )

            snapshots = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                hash_msg = line.split(' ', 1)
                snapshots.append({
                    'hash': hash_msg[0],
                    'message': hash_msg[1] if len(hash_msg) > 1 else ''
                })

            return snapshots

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list snapshots: {e}")
            return []

    async def cleanup_old_snapshots(
        self,
        project_id: str,
        keep_days: int = 7
    ):
        """清理旧快照"""
        repo_path = self._get_repo_path(project_id).parent

        try:
            # 使用 git gc 清理
            subprocess.run(
                ["git", "gc", "--prune=now"],
                cwd=repo_path,
                capture_output=True,
                check=True
            )

            logger.info(f"Cleaned up old snapshots: {project_id}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to cleanup snapshots: {e}")
```

**Step 2: 集成到检查点管理器**

```python
# backend/infrastructure/checkpoint/checkpoint_manager.py (修改)

from backend.infrastructure.snapshot.git_snapshot import GitSnapshotManager

class CheckpointManager:
    def __init__(self, backend, enable_snapshots: bool = True):
        self.backend = backend
        self.snapshot_manager = GitSnapshotManager() if enable_snapshots else None

    async def save_checkpoint(self, ...) -> Checkpoint:
        # ... 原有代码 ...

        # 创建 Git 快照
        if self.snapshot_manager:
            snapshot_data = {
                "checkpoint": checkpoint.__dict__,
                "timestamp": datetime.now().isoformat()
            }
            commit_hash = await self.snapshot_manager.create_snapshot(
                project_id=user_id,  # 使用 user_id 作为 project_id
                data=snapshot_data,
                message=f"Checkpoint {task_id}"
            )
            # 存储快照 hash
            checkpoint.snapshot_hash = commit_hash

        return checkpoint

    async def restore_from_snapshot(
        self,
        project_id: str,
        snapshot_hash: str
    ) -> Optional[Checkpoint]:
        """从快照恢复"""
        if not self.snapshot_manager:
            logger.error("Snapshot manager not enabled")
            return None

        snapshot_data = await self.snapshot_manager.restore_snapshot(
            project_id,
            snapshot_hash
        )

        if snapshot_data:
            # 重建检查点对象
            checkpoint_data = snapshot_data.get("checkpoint")
            return Checkpoint(**checkpoint_data)

        return None
```

---

#### 预期收益

| 指标 | 改进前 | 改进后 | 提升 |
|------|-------:|-------:|-----:|
| 存储空间 | 100% | 20-30% | 70-80% ↓ |
| 版本回滚 | 不支持 | 支持 | ✅ |
| Diff 查看 | 不支持 | 支持 | ✅ |

---

### 重构 3：分层消息存储 ⭐⭐

**优先级：** 中 | **工作量：** 1-2 周 | **收益：** 查询性能提升

---

#### 问题描述

单一表结构导致消息表膨胀，查询性能下降。

---

#### 实施方案

**Step 1: 数据库 Schema**

```sql
-- 消息主表
CREATE TABLE messages (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'user' | 'assistant'
    parent_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_summary BOOLEAN DEFAULT FALSE,
    is_compacted BOOLEAN DEFAULT FALSE,

    INDEX idx_task_created (task_id, created_at),
    INDEX idx_parent (parent_id),
    FOREIGN KEY (task_id) REFERENCES checkpoints(task_id) ON DELETE CASCADE
);

-- 消息部分表
CREATE TABLE message_parts (
    id VARCHAR(36) PRIMARY KEY,
    message_id VARCHAR(36) NOT NULL,
    part_type VARCHAR(50) NOT NULL,  -- 'text', 'tool', 'file', etc.
    content TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_message (message_id),
    INDEX idx_type (part_type),
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
);
```

**Step 2: ORM 模型**

```python
# backend/memory/storage/models/message.py

from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.memory.storage.models.base import Base

class Message(Base):
    """消息模型"""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True)
    task_id = Column(String(36), ForeignKey("checkpoints.task_id"), nullable=False)
    role = Column(String(20), nullable=False)
    parent_id = Column(String(36), ForeignKey("messages.id"))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    is_summary = Column(Boolean, default=False)
    is_compacted = Column(Boolean, default=False)

    # 关系
    parts = relationship("MessagePart", back_populates="message", cascade="all, delete-orphan")
    parent = relationship("Message", remote_side=[id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "role": self.role,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_summary": self.is_summary,
            "is_compacted": self.is_compacted,
        }


class MessagePart(Base):
    """消息部分模型"""
    __tablename__ = "message_parts"

    id = Column(String(36), primary_key=True)
    message_id = Column(String(36), ForeignKey("messages.id"), nullable=False)
    part_type = Column(String(50), nullable=False)
    content = Column(Text)
    metadata = Column(JSON)
    created_at = Column(DateTime)

    # 关系
    message = relationship("Message", back_populates="parts")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "message_id": self.message_id,
            "part_type": self.part_type,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
```

**Step 3: 消息服务**

```python
# backend/memory/services/message_service.py

import logging
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageService:
    """消息服务"""

    def __init__(self, db_session):
        self.db_session = db_session

    async def create_message(
        self,
        task_id: str,
        role: str,
        parts: List[Dict[str, Any]],
        parent_id: Optional[str] = None
    ) -> str:
        """创建消息"""
        message_id = str(uuid4())

        # 创建消息
        message = Message(
            id=message_id,
            task_id=task_id,
            role=role,
            parent_id=parent_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.db_session.add(message)

        # 创建 parts
        for part_data in parts:
            part = MessagePart(
                id=str(uuid4()),
                message_id=message_id,
                part_type=part_data["type"],
                content=part_data.get("content"),
                metadata=part_data.get("metadata"),
                created_at=datetime.now()
            )
            self.db_session.add(part)

        self.db_session.commit()
        logger.info(f"Created message: {message_id}")
        return message_id

    async def get_messages(
        self,
        task_id: str,
        limit: Optional[int] = None,
        include_parts: bool = True
    ) -> List[Dict[str, Any]]:
        """获取消息列表"""
        query = self.db_session.query(Message).filter(
            Message.task_id == task_id
        ).order_by(Message.created_at)

        if limit:
            query = query.limit(limit)

        messages = query.all()

        result = []
        for msg in messages:
            msg_dict = msg.to_dict()

            if include_parts:
                msg_dict["parts"] = [part.to_dict() for part in msg.parts]

            result.append(msg_dict)

        return result

    async def get_message(
        self,
        message_id: str,
        include_parts: bool = True
    ) -> Optional[Dict[str, Any]]:
        """获取单条消息"""
        message = self.db_session.query(Message).filter(
            Message.id == message_id
        ).first()

        if not message:
            return None

        result = message.to_dict()

        if include_parts:
            result["parts"] = [part.to_dict() for part in message.parts]

        return result

    async def delete_message(self, message_id: str) -> bool:
        """删除消息（级联删除 parts）"""
        message = self.db_session.query(Message).filter(
            Message.id == message_id
        ).first()

        if not message:
            return False

        self.db_session.delete(message)
        self.db_session.commit()
        logger.info(f"Deleted message: {message_id}")
        return True

    async def compact_old_messages(
        self,
        task_id: str,
        keep_count: int = 20
    ) -> int:
        """压缩旧消息"""
        # 获取所有消息
        messages = self.db_session.query(Message).filter(
            Message.task_id == task_id
        ).order_by(Message.created_at.desc()).all()

        if len(messages) <= keep_count:
            return 0

        # 标记旧消息为已压缩
        old_messages = messages[keep_count:]
        for msg in old_messages:
            msg.is_compacted = True

        self.db_session.commit()
        logger.info(f"Compacted {len(old_messages)} messages for task {task_id}")
        return len(old_messages)
```

---

#### 预期收益

| 指标 | 改进前 | 改进后 | 提升 |
|------|-------:|-------:|-----:|
| 查询性能 | 基准 | +50% | 50% ↑ |
| 存储效率 | 基准 | +30% | 30% ↑ |
| 扩展性 | 低 | 高 | - |

---

## 第三部分：混合架构方案

### 推荐架构

结合 OpenCode 和 MultiAgentPPT 的优势：

```
┌─────────────────────────────────────────────────────────────┐
│                     应用层 (Agent)                          │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   适配层 (MemoryAwareAgent)                  │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌──────────────────────────┬──────────────────────────────────┐
│      服务层              │        缓存层                     │
│  UserPreferenceService   │    RedisCache                    │
│  MessageService          │    (热点数据)                    │
│  CheckpointManager       │                                  │
│  ForkManager             │                                  │
└──────────────────────────┴──────────────────────────────────┘
                           ↓
┌──────────────────────────┬──────────────────────────────────┐
│      文件存储            │        数据库索引                │
│  消息内容                │    MySQL                         │
│  快照数据                │    (元数据、索引、用户)          │
│  (JSON + Git压缩)        │                                  │
└──────────────────────────┴──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   版本控制 (Git)                             │
│            (快照、压缩、diff、回滚)                          │
└─────────────────────────────────────────────────────────────┘
```

### 数据分配策略

| 数据类型 | 存储位置 | 原因 |
|---------|---------|------|
| 用户偏好 | MySQL + Redis | 需要快速查询、多租户 |
| 检查点元数据 | MySQL | 需要复杂查询、关联 |
| 消息内容 | 文件系统 + Git | 大文件、版本控制 |
| 快照数据 | Git | 压缩存储、diff 查看 |
| 会话状态 | Redis | 临时数据、快速访问 |

---

## 附录

### A. 实施优先级矩阵

| 优化项 | 优先级 | 工作量 | 收益 | 推荐顺序 |
|--------|-------:|-------:|-----:|:--------:|
| 消息压缩 | 高 | 3-5天 | 高 | 1 |
| 异步写入 | 中 | 2-3天 | 中 | 2 |
| 文件锁 | 中 | 1-2天 | 低 | 3 |
| 父子会话 | 高 | 2-3周 | 高 | 4 |
| Git快照 | 中 | 2-3周 | 高 | 5 |
| 分层消息 | 中 | 1-2周 | 中 | 6 |

### B. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|-----:|-----:|----------|
| 数据迁移失败 | 中 | 高 | 充分测试、备份 |
| 性能下降 | 低 | 中 | 基准测试、灰度发布 |
| 用户习惯改变 | 中 | 低 | 文档、培训 |
| 兼容性问题 | 低 | 中 | 版本控制、回滚方案 |

### C. 成本估算

| 阶段 | 工作量 | 人力 | 成本（人天） |
|------|-------:|----:|------------:|
| 短期优化 | 6-10天 | 1人 | 8 |
| 长期重构 | 5-8周 | 1-2人 | 40-60 |
| 测试验证 | 1-2周 | 1人 | 5-10 |
| **总计** | - | - | **53-78人天** |

---

**文档版本：** 1.0.0
**最后更新：** 2026-02-10
**维护者：** MultiAgentPPT Team
