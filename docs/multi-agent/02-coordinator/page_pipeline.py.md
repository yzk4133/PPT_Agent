# page_pipeline.py 详解

> 页面流水线 - 并行执行页面级任务，实现 30%-60% 性能提升

---

## 目录

1. [概述](#概述)
2. [核心概念](#核心概念)
3. [架构设计：5层封装结构](#架构设计5层封装结构)
4. [PagePipeline 类详解](#pagepipeline-类详解)
5. [并发控制机制](#并发控制机制)
6. [重试机制](#重试机制)
7. [使用示例](#使用示例)
8. [性能优化](#性能优化)
9. [最佳实践](#最佳实践)
10. [调试技巧](#调试技巧)
11. [常见问题](#常见问题)

---

## 概述

### 作用

`page_pipeline.py` 实现页面级别的并行执行流水线，通过并发处理多个页面来显著提升性能。

### 为什么需要

- ❌ **串行执行**：100页 PPT 需要 200秒（2秒/页）
- ✅ **并行执行**：100页 PPT 只需 68秒（并发度=3）
- 📈 **性能提升**：30%-60%

### 核心特性

| 特性 | 说明 |
|------|------|
| **并发控制** | 使用 `asyncio.Semaphore` 限制并发数 |
| **自动重试** | 失败的页面自动重试（可配置次数） |
| **进度跟踪** | 实时回调报告进度 |
| **部分成功** | 部分页面失败不影响其他页面 |
| **错误隔离** | 单个页面的异常不会中断整个流程 |

---

## 核心概念

### 1. 并发执行（Concurrency）

```python
# 串行执行（慢）
[页面1] → [页面2] → [页面3] → [页面4] → [页面5]
耗时：5 × 2秒 = 10秒

# 并行执行（快）
批次1: [页面1, 页面2, 页面3] → 2秒
批次2: [页面4, 页面5]           → 2秒
总耗时：4秒（提升 60%）
```

### 2. 信号量（Semaphore）

控制同时运行的任务数量：

```python
semaphore = asyncio.Semaphore(3)  # 最多3个任务

async with semaphore:
    # 在这个代码块内，最多只有3个任务在运行
    result = await process_page(page)
```

### 3. 重试机制

自动重试失败的任务：

```python
for attempt in range(max_retries + 1):
    try:
        return await executor_func(page)
    except Exception:
        if attempt < max_retries:
            await asyncio.sleep(retry_delay)
        else:
            raise  # 最后一次也失败了
```

---

## 架构设计：5层封装结构

PagePipeline 采用了**洋葱式封装**设计，从内到外共有5层，每一层都给内层添加了新的能力。

### 层次结构图

```
┌─────────────────────────────────────────────────────────────┐
│                    第5层：具体应用                          │
│  execute_research_pipeline() / execute_content_pipeline()   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              第4层：通用并行框架                       │  │
│  │              execute_pages()                          │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │         第3层：并发控制门                        │  │
│  │  │         _process_page_with_semaphore()           │  │
│  │  │  ┌───────────────────────────────────────────┐  │  │  │
│  │  │  │      第2层：重试机制                      │  │  │  │
│  │  │  │      _process_page_with_retry()           │  │  │  │
│  │  │  │  ┌─────────────────────────────────────┐  │  │  │  │
│  │  │  │  │   第1层：真正干活的地方               │  │  │  │  │
│  │  │  │  │   executor_func(page)                 │  │  │  │  │
│  │  │  │  │   - research_agent.research_page()    │  │  │  │  │
│  │  │  │  │   - content_agent.generate_content()  │  │  │  │  │
│  │  │  │  └─────────────────────────────────────┘  │  │  │  │
│  │  │  └───────────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

### 逐层解析

#### 第1层：真正干活的地方（原始函数）

```python
# 这一层是 Agent 的方法，不做任何封装
async def research_page(page):
    """研究单个页面（原始函数）"""
    # 调用 LLM，查找资料
    result = await llm.ainvoke(f"Research: {page}")
    return result

async def generate_content(page):
    """生成单个页面的内容（原始函数）"""
    # 调用 LLM，生成内容
    result = await llm.ainvoke(f"Generate: {page}")
    return result
```

**职责**：纯粹的逻辑处理，不知道重试、并发这些东西

---

#### 第2层：重试机制

```python
async def _process_page_with_retry(self, page, executor_func, ...):
    """在第1层外面加一层：自动重试"""

    for attempt in range(self.max_retries + 1):
        try:
            # 调用第1层
            return await executor_func(page)
        except Exception as e:
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay)  # 等待后重试
            else:
                raise  # 最后一次也失败了，抛出异常
```

**职责**：失败后自动重试

**封装关系**：
```
重试层 包装 原始函数
retry(executor_func(page))
```

**执行流程**：
```
尝试1 → 失败 → 等待1秒
尝试2 → 失败 → 等待1秒
尝试3 → 成功 → 返回结果
```

---

#### 第3层：并发控制门

```python
async def _process_page_with_semaphore(self, page, executor_func, ...):
    """在第2层外面加一层：控制并发"""

    # 关键！这里限制了同时运行的任务数
    async with self.semaphore:
        # 只有拿到 semaphore 的任务才能进入
        return await self._process_page_with_retry(page, executor_func, ...)
    # 离开时自动释放 semaphore
```

**职责**：限制同时运行的任务数量

**封装关系**：
```
并发层 包装 重试层 包装 原始函数
semaphore_control(retry(executor_func(page)))
```

**工作原理**：
```
想象一个门，门上有3个闸机（max_concurrency=3）

任务队列: [任务1, 任务2, 任务3, 任务4, 任务5, ...]

时间0s:
  [任务1] [任务2] [任务3] 通过闸机，正在执行
  任务4、任务5... 在门口等待 ⏳

时间1s:
  任务1 完成，离开闸机 ✓
  任务4 通过闸机，开始执行
  任务5 继续等待 ⏳
```

**Semaphore 是什么？**

```python
# Semaphore 就像停车场的车位
semaphore = asyncio.Semaphore(3)  # 只有3个车位

async with semaphore:  # 获取车位
    # 停车（执行任务）
    await do_work()
# 离开时自动释放车位
```

---

#### 第4层：通用并行框架

```python
async def execute_pages(self, pages, executor_func, progress_callback):
    """在第3层外面加一层：批量并行执行"""

    # 1. 为每个页面创建一个任务
    tasks = []
    for page in pages:
        # 每个任务都会经过第3层的 semaphore 控制
        task = self._process_page_with_semaphore(
            page,
            executor_func,
            progress_callback,
            total_pages
        )
        tasks.append(task)

    # 2. 并发执行所有任务
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 3. 分离成功和失败的结果
    successful_results = [r for r in results if not isinstance(r, Exception)]

    return successful_results
```

**职责**：
- 创建所有任务
- 并发执行
- 处理异常

**封装关系**：
```
并行层 包装 并发层 包装 重试层 包装 原始函数
parallel_execute(semaphore_control(retry(executor_func(page))))
```

**关键点**：
- 虽然创建了 10 个任务
- 但同时运行的最多 `max_concurrency` 个
- 为什么？因为每个任务都会经过第3层的 semaphore 控制

---

#### 第5层：具体应用

```python
async def execute_research_pipeline(self, state, research_agent):
    """在第4层外面加一层：研究业务逻辑"""

    # 1. 获取需要研究的页面
    pages_to_research = self._get_pages_need_research(state)

    # 2. 定义进度回调
    async def progress_callback(page_no, total):
        progress = 30 + (page_no / total) * 20  # 30% → 50%
        update_state_progress(state, "research", int(progress))

    # 3. 调用通用并行函数
    results = await self.execute_pages(
        pages_to_research,
        research_agent.research_page,  # ← 传入具体的执行函数
        progress_callback
    )

    # 4. 更新状态
    state["research_results"] = results
    return state
```

**职责**：
- 业务逻辑（筛选哪些页面需要研究）
- 进度映射（30% → 50%）
- 状态更新

**封装关系**：
```
业务层 包装 并行层 包装 并发层 包装 重试层 包装 原始函数
research_pipeline(parallel_execute(semaphore_control(retry(research_page(page)))))
```

---

### 为什么要这样封装？

#### 1. 代码复用

```python
# ❌ 不分层：重复代码
async def execute_research():
    tasks = []
    for page in pages:
        tasks.append(self._process_with_semaphore_and_retry(page, research_func))
    results = await asyncio.gather(*tasks)
    return results

async def execute_content():
    tasks = []
    for page in pages:
        tasks.append(self._process_with_semaphore_and_retry(page, content_func))
    results = await asyncio.gather(*tasks)
    return results

# ✅ 分层：代码复用
async def execute_pages(self, pages, executor_func, ...):
    # 通用逻辑（只写一次）
    tasks = [self._process_page_with_semaphore(...) for page in pages]
    return await asyncio.gather(*tasks)

# 具体应用
async def execute_research_pipeline(self, ...):
    return await self.execute_pages(pages, research_agent.research_page, ...)

async def execute_content_pipeline(self, ...):
    return await self.execute_pages(pages, content_agent.generate_content, ...)
```

---

#### 2. 关注点分离

每一层只做一件事：

| 层次 | 职责 | 修改影响 |
|------|------|----------|
| **第1层：原始函数** | 业务逻辑（研究/生成） | 只影响具体业务 |
| **第2层：重试机制** | 失败重试 | 只影响重试策略 |
| **第3层：并发控制** | 限制并发数 | 只影响并发数 |
| **第4层：并行框架** | 批量执行、异常处理 | 只影响执行方式 |
| **第5层：业务应用** | 具体业务逻辑 | 只影响业务 |

**好处**：修改某一层时，不需要修改其他层

```python
# 修改重试策略：只需修改第2层
# 修改并发数：只需修改第3层的 Semaphore 初始化
# 修改业务逻辑：只需修改第5层或第1层
```

---

#### 3. 易于测试

每一层都可以独立测试：

```python
# 测试第1层（原始函数）
async def test_research_page():
    result = await research_agent.research_page(mock_page)
    assert result is not None

# 测试第2层（重试）
async def test_retry():
    call_count = [0]
    async def flaky_func(page):
        call_count[0] += 1
        if call_count[0] < 3:
            raise Exception("Fail")
        return "Success"

    result = await pipeline._process_page_with_retry(mock_page, flaky_func, ...)
    assert call_count[0] == 3  # 重试了2次，总共调用3次

# 测试第3层（并发）
async def test_concurrency():
    start_time = time.time()
    results = await pipeline.execute_pages(
        [mock_page] * 10,
        slow_executor,  # 每个需要1秒
        max_concurrency=3
    )
    elapsed = time.time() - start_time
    assert 3 < elapsed < 5  # 10个任务，并发3，应该约4秒
```

---

### 形象比喻：工厂流水线

想象一个**工厂**：

```
┌──────────────────────────────────────────┐
│  第5层：车间主任（安排今天生产什么）       │
│  execute_research_pipeline()              │
│  - 决定生产哪些产品                        │
│  - 调度生产流程                            │
└──────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│  第4层：流水线（批量处理）                 │
│  execute_pages()                         │
│  - 启动所有工人                            │
│  - 收集所有产品                            │
└──────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│  第3层：门禁（限制人数）                   │
│  semaphore                                │
│  - 只允许N个工人同时工作                   │
│  - 其他人等待                              │
└──────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│  第2层：质检员（重试）                     │
│  retry logic                              │
│  - 产品不合格？重新做                      │
│  - 最多重试N次                             │
└──────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│  第1层：工人（真正干活）                   │
│  executor_func()                         │
│  - 生产单个产品                            │
└──────────────────────────────────────────┘
```

---

### 完整执行流程示例

```python
# 场景：研究 10 个页面，max_concurrency=3

async def main():
    pipeline = PagePipeline(max_concurrency=3)

    # 页面列表
    pages = [f"page{i}" for i in range(1, 11)]

    # 执行器函数（第1层）
    async def research_agent_func(page):
        await asyncio.sleep(2)  # 模拟耗时操作
        return f"researched: {page}"

    # 调用具体应用（第5层）
    results = await pipeline.execute_research_pipeline(
        state=state,
        research_agent=research_agent
    )
```

**执行时间线**：

```
时间0s:  创建 10 个任务
         └─ 但只有 3 个能拿到 semaphore 许可

         运行中: [page1, page2, page3]
         等待中: [page4, page5, page6, page7, page8, page9, page10]

时间2s:  page1 完成 → 释放 semaphore ✓
         └─ page4 拿到 semaphore，开始运行

         运行中: [page2, page3, page4]
         等待中: [page5, page6, page7, page8, page9, page10]

时间4s:  page2 完成 → page5 开始
         运行中: [page3, page4, page5]

时间6s:  page3 完成 → page6 开始
         运行中: [page4, page5, page6]

...

总耗时: 约8秒（分4批，每批2秒）
串行耗时: 20秒
提升: 2.5倍
```

---

### 核心思想

```
每一层只做一件事，做好一件事

内层不需要知道外层的存在
外层通过包装内层来添加功能
```

**代码组织原则**：

```python
# 内层（简单）
def worker():
    return "product"

# 逐层包装
worker_with_retry = retry(worker)
worker_with_concurrency = semaphore(worker_with_retry)
worker_with_parallel = parallel(worker_with_concurrency)
worker_with_business = business(worker_with_parallel)
```

---

## PagePipeline 类详解

### 初始化

```python
def __init__(
    self,
    max_concurrency: int = 3,      # 最大并发数
    max_retries: int = 2,          # 最大重试次数
    retry_delay: float = 1.0       # 重试延迟（秒）
):
    """
    初始化页面流水线

    Args:
        max_concurrency: 同时运行的最大任务数
        max_retries: 失败后的重试次数（不包括首次尝试）
        retry_delay: 每次重试之间的等待时间（秒）
    """
    self.max_concurrency = max_concurrency
    self.max_retries = max_retries
    self.retry_delay = retry_delay

    # 创建信号量
    self.semaphore = asyncio.Semaphore(max_concurrency)
```

**参数说明**：

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `max_concurrency` | 3-5 | 太低影响性能，太高可能导致资源耗尽 |
| `max_retries` | 2-3 | 太少可能错过临时性错误，太多浪费时间 |
| `retry_delay` | 1.0-2.0 | 给错误恢复一些时间 |

---

### 核心方法

#### 1. execute_pages()

**并行执行页面任务的主方法**

```python
async def execute_pages(
    self,
    pages: List[Dict[str, Any]],
    executor_func: Callable,
    progress_callback: Optional[Callable] = None,
) -> List[Dict[str, Any]]:
    """
    并行执行页面任务

    Args:
        pages: 页面定义列表
        executor_func: 执行函数，签名为 async def func(page: Dict) -> Dict
        progress_callback: 进度回调，签名为 async def func(page_no: int, total: int)

    Returns:
        成功执行的结果列表（失败的结果会被过滤掉）

    Raises:
        不会抛出异常（内部处理所有异常）
    """
```

**执行流程**：

```python
# 1. 边界检查
if not pages:
    logger.warning("[PagePipeline] No pages to execute")
    return []

# 2. 创建所有任务
tasks = []
for page in pages:
    task = self._process_page_with_semaphore(
        page, executor_func, progress_callback, total_pages
    )
    tasks.append(task)

# 3. 并行执行（关键！）
results = await asyncio.gather(*tasks, return_exceptions=True)

# 4. 分离成功和失败的结果
successful_results = []
failed_pages = []

for i, result in enumerate(results):
    if isinstance(result, Exception):
        logger.error(f"[PagePipeline] Page {i+1} failed: {result}")
        failed_pages.append((pages[i], result))
    else:
        successful_results.append(result)

# 5. 返回结果
logger.info(f"Completed: {len(successful_results)}/{total_pages} successful")
return successful_results
```

**关键点**：

- ✅ `return_exceptions=True`：异常会被返回而不是抛出
- ✅ 部分失败不影响整体：只返回成功的结果
- ✅ 详细的日志记录

---

#### 2. execute_research_pipeline()

**执行研究流水线**

```python
async def execute_research_pipeline(
    self,
    state: PPTGenerationState,
    research_agent,
) -> PPTGenerationState:
    """
    执行研究流水线

    Args:
        state: 当前状态
        research_agent: 研究智能体

    Returns:
        更新后的状态（包含研究结果）

    Progress: 30% → 50%
    """
```

**实现细节**：

```python
async def execute_research_pipeline(self, state, research_agent):
    # 1. 获取需要研究的页面
    framework = state.get("ppt_framework", {})
    pages = framework.get("ppt_framework", [])
    research_indices = framework.get("research_page_indices", [])

    if not research_indices:
        logger.info("[PagePipeline] No pages need research")
        state["research_results"] = []
        return state

    # 2. 筛选需要研究的页面
    pages_to_research = [p for p in pages if p.get("page_no") in research_indices]

    # 3. 创建进度回调
    async def progress_callback(page_no: int, total: int):
        progress = 30 + (page_no / total) * 20  # 30% → 50%
        update_state_progress(state, "research", int(progress))

    # 4. 并行执行研究
    results = await self.execute_pages(
        pages_to_research,
        research_agent.research_page,  # 调用 agent 的方法
        progress_callback
    )

    # 5. 更新状态
    state["research_results"] = results
    return state
```

---

#### 3. execute_content_pipeline()

**执行内容生成流水线**

```python
async def execute_content_pipeline(
    self,
    state: PPTGenerationState,
    content_agent,
) -> PPTGenerationState:
    """
    执行内容生成流水线

    Args:
        state: 当前状态
        content_agent: 内容生成智能体

    Returns:
        更新后的状态（包含生成的内容）

    Progress: 50% → 80%
    """
```

**实现细节**：

```python
async def execute_content_pipeline(self, state, content_agent):
    # 1. 获取页面和研究结果
    framework = state.get("ppt_framework", {})
    pages = framework.get("ppt_framework", [])
    research_results = state.get("research_results", [])

    # 2. 创建进度回调
    async def progress_callback(page_no: int, total: int):
        progress = 50 + (page_no / total) * 30  # 50% → 80%
        update_state_progress(state, "content_generation", int(progress))

    # 3. 创建执行函数（绑定研究结果）
    async def generate_content(page: Dict[str, Any]) -> Dict[str, Any]:
        # 每个页面可以使用相关的研究结果
        return await content_agent.generate_content_for_page(page, research_results)

    # 4. 并行生成内容
    results = await self.execute_pages(pages, generate_content, progress_callback)

    # 5. 更新状态
    state["content_materials"] = results
    return state
```

---

### 私有方法

#### _process_page_with_semaphore()

**使用信号量控制并发**

```python
async def _process_page_with_semaphore(
    self,
    page: Dict[str, Any],
    executor_func: Callable,
    progress_callback: Optional[Callable],
    total_pages: int,
) -> Dict[str, Any]:
    """
    使用信号量控制并发的页面处理

    这是并发控制的关键：async with self.semaphore 会等待，
    直到有可用的并发槽位。
    """
    async with self.semaphore:
        return await self._process_page_with_retry(
            page, executor_func, progress_callback, total_pages
        )
```

**工作原理**：

```
假设 max_concurrency = 3：

时间线：
0s:  任务1, 任务2, 任务3 开始（3个槽位满了）
1s:  任务1 完成，任务4 开始（获得空闲槽位）
1.5s: 任务2 完成，任务5 开始
2s:  任务3 完成，任务6 开始
...

同时最多只有3个任务在运行！
```

---

#### _process_page_with_retry()

**带重试的页面处理**

```python
async def _process_page_with_retry(
    self,
    page: Dict[str, Any],
    executor_func: Callable,
    progress_callback: Optional[Callable],
    total_pages: int,
) -> Dict[str, Any]:
    """
    带重试的页面处理

    实现：尝试执行 → 失败则等待 → 重试 → ... → 超过次数则抛出异常
    """
    page_no = page.get("page_no", 1)
    last_error = None

    # 尝试 max_retries + 1 次（首次 + 重试）
    for attempt in range(self.max_retries + 1):
        try:
            logger.debug(f"[PagePipeline] Processing page {page_no}, attempt {attempt + 1}")

            # 执行任务
            result = await executor_func(page)

            # 成功！调用进度回调
            if progress_callback:
                await progress_callback(page_no, total_pages)

            return result

        except Exception as e:
            last_error = e
            logger.warning(f"[PagePipeline] Page {page_no} failed on attempt {attempt + 1}: {e}")

            if attempt < self.max_retries:
                # 等待后重试
                await asyncio.sleep(self.retry_delay)
            else:
                # 最后一次尝试也失败了
                logger.error(f"[PagePipeline] Page {page_no} failed after {self.max_retries + 1} attempts")
                raise
```

---

## 并发控制机制

### Semaphore 工作原理

```python
import asyncio

class PagePipeline:
    def __init__(self, max_concurrency: int = 3):
        # 创建信号量，最多允许3个并发
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def process_with_limit(self, page):
        # 获取信号量（如果已满则等待）
        async with self.semaphore:
            # 在这里执行任务，最多只有 max_concurrency 个在运行
            result = await self.do_work(page)
            return result
```

**实际运行示例**：

```python
# 假设有10个页面，max_concurrency=3

async def main():
    pipeline = PagePipeline(max_concurrency=3)
    pages = [f"page{i}" for i in range(10)]

    # 创建10个任务
    tasks = [pipeline.process_with_limit(page) for page in pages]

    # 并发执行
    results = await asyncio.gather(*tasks)

# 执行时序：
# 时间0s:  page0, page1, page2 开始（3个）
# 时间1s:  page0 完成，page3 开始
# 时间1.2s: page1 完成，page4 开始
# 时间1.5s: page2 完成，page5 开始
# ...以此类推
```

---

### 并发数选择

| 场景 | 推荐并发数 | 理由 |
|------|-----------|------|
| **CPU密集型** | 2-4 | 避免过度上下文切换 |
| **I/O密集型** | 5-10 | I/O等待时可以处理其他任务 |
| **调用外部API** | 3-5 | 避免API限流 |
| **本地LLM推理** | 1-2 | 避免内存/显存不足 |

**公式**（经验法则）：

```python
# I/O密集型
max_concurrency = min(10, cpu_count() * 2)

# CPU密集型
max_concurrency = cpu_count()

# 混合型（LLM调用）
max_concurrency = 3  # 保守估计
```

---

## 重试机制

### 重试策略

```python
class PagePipeline:
    def __init__(
        self,
        max_retries: int = 2,      # 最多重试2次
        retry_delay: float = 1.0,  # 每次重试等待1秒
    ):
        ...
```

### 重试时序

```
max_retries = 2 的场景：

尝试1 (0s) ──✗ 失败 ──→ 等待1秒
    ↓
尝试2 (1s) ──✗ 失败 ──→ 等待1秒
    ↓
尝试3 (2s) ──✗ 失败 ──→ 抛出异常

总耗时：约3秒（包括重试延迟）
```

### 指数退避（进阶）

可以改进为指数退避策略：

```python
async def _process_page_with_retry_exponential_backoff(self, ...):
    """使用指数退避的重试策略"""
    for attempt in range(self.max_retries + 1):
        try:
            return await executor_func(page)
        except Exception as e:
            if attempt < self.max_retries:
                # 指数退避：1s, 2s, 4s, 8s, ...
                delay = self.retry_delay * (2 ** attempt)
                await asyncio.sleep(delay)
            else:
                raise
```

---

## 使用示例

### 1. 基本使用

```python
from backend.agents_langchain.coordinator.page_pipeline import (
    create_page_pipeline,
)

# 创建流水线
pipeline = create_page_pipeline(
    max_concurrency=3,
    max_retries=2,
    retry_delay=1.0,
)

# 定义执行函数
async def my_executor(page: Dict[str, Any]) -> Dict[str, Any]:
    """处理单个页面"""
    page_no = page["page_no"]
    # 模拟耗时操作
    await asyncio.sleep(1)
    return {
        "page_no": page_no,
        "result": f"Content for page {page_no}",
        "timestamp": datetime.now().isoformat(),
    }

# 定义进度回调
async def my_progress_callback(page_no: int, total: int):
    """页面完成时的回调"""
    progress = (page_no / total) * 100
    print(f"进度: {page_no}/{total} ({progress:.1f}%)")

# 执行
pages = [{"page_no": i, "title": f"Page {i}"} for i in range(1, 11)]
results = await pipeline.execute_pages(
    pages=pages,
    executor_func=my_executor,
    progress_callback=my_progress_callback,
)

print(f"完成: {len(results)} 个页面")
```

### 2. 在工作流中使用

```python
async def research_workflow(state: PPTGenerationState):
    """研究工作流"""
    pipeline = create_page_pipeline(max_concurrency=3)

    # 获取研究 agent
    research_agent = create_research_agent(model)

    # 执行研究流水线
    state = await pipeline.execute_research_pipeline(state, research_agent)

    # 检查结果
    research_results = state.get("research_results", [])
    print(f"研究完成: {len(research_results)} 个页面")

    return state
```

### 3. 自定义错误处理

```python
async def safe_executor(page: Dict) -> Dict:
    """带自定义错误处理的执行器"""
    try:
        result = await do_something(page)
        return {"success": True, "data": result}
    except Exception as e:
        # 返回错误信息而不是抛出异常
        return {
            "success": False,
            "error": str(e),
            "page_no": page["page_no"],
        }

# 执行
results = await pipeline.execute_pages(pages, safe_executor)

# 过滤成功的结果
successful = [r for r in results if r.get("success")]
failed = [r for r in results if not r.get("success")]

print(f"成功: {len(successful)}, 失败: {len(failed)}")
```

---

## 性能优化

### 1. 并发数调优

```python
import time

async def benchmark_concurrency():
    """测试不同并发数的性能"""
    pages = [{"page_no": i} for i in range(100)]

    for concurrency in [1, 2, 3, 5, 10]:
        pipeline = create_page_pipeline(max_concurrency=concurrency)

        start = time.time()
        results = await pipeline.execute_pages(pages, mock_executor)
        elapsed = time.time() - start

        print(f"并发度={concurrency}: {elapsed:.2f}s ({len(results)} 页)")

# 结果示例：
# 并发度=1: 100.00s (100 页)  ← 串行
# 并发度=2: 50.50s (100 页)
# 并发度=3: 34.20s (100 页)   ← 最优
# 并发度=5: 25.10s (100 页)   ← 边际收益递减
# 并发度=10: 22.80s (100 页)  ← 资源竞争
```

### 2. 超时控制

```python
async def execute_with_timeout(page):
    """带超时的执行"""
    try:
        # 最多等待5秒
        result = await asyncio.wait_for(
            process_page(page),
            timeout=5.0
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(f"Page {page['page_no']} timed out")
        raise
```

### 3. 批量处理

```python
async def execute_in_batches(pages, executor, batch_size=10):
    """分批处理大量页面"""
    results = []

    for i in range(0, len(pages), batch_size):
        batch = pages[i:i+batch_size]
        batch_results = await pipeline.execute_pages(batch, executor)
        results.extend(batch_results)

        # 批次间休息，避免资源耗尽
        await asyncio.sleep(0.5)

    return results
```

---

## 最佳实践

### 1. 选择合适的并发数

```python
# ✅ 好的做法：根据场景选择
if calling_external_api:
    max_concurrency = 3  # 避免API限流
elif cpu_intensive:
    max_concurrency = 2  # 避免CPU过载
else:
    max_concurrency = 5  # 通用场景

# ❌ 不好的做法：固定值
max_concurrency = 10  # 可能导致资源耗尽
```

### 2. 处理部分失败

```python
# 执行流水线
results = await pipeline.execute_pages(pages, executor)

# 检查完整性
if len(results) < len(pages):
    failed_count = len(pages) - len(results)
    logger.warning(f"有 {failed_count} 个页面失败")

    # 决策：是否继续？
    if failed_count > len(pages) * 0.1:  # 失败率>10%
        raise Exception("失败率过高，中止流程")
```

### 3. 进度回调优化

```python
class ProgressThrottle:
    """限制进度回调频率"""
    def __init__(self, callback, min_interval=0.5):
        self.callback = callback
        self.min_interval = min_interval
        self.last_call = 0

    async def call(self, *args):
        now = time.time()
        if now - self.last_call >= self.min_interval:
            await self.callback(*args)
            self.last_call = now

# 使用
throttled_callback = ProgressThrottle(my_callback, min_interval=0.5)
results = await pipeline.execute_pages(pages, executor, throttled_callback.call)
```

### 4. 资源清理

```python
async def execute_with_cleanup(pages, executor):
    """确保资源被正确清理"""
    try:
        results = await pipeline.execute_pages(pages, executor)
        return results
    finally:
        # 清理资源
        await cleanup_resources()
        logger.info("Resources cleaned up")
```

---

## 调试技巧

### 1. 详细日志

```python
import logging

# 启用详细日志
logging.getLogger("backend.agents_langchain.coordinator.page_pipeline").setLevel(logging.DEBUG)

# 现在可以看到每个页面的执行详情
# [DEBUG] Processing page 1, attempt 1
# [DEBUG] Processing page 2, attempt 1
# ...
```

### 2. 模拟慢操作

```python
async def slow_executor(page):
    """模拟慢操作（测试用）"""
    delay = random.uniform(0.5, 2.0)  # 随机延迟
    await asyncio.sleep(delay)
    return {"page_no": page["page_no"], "delay": delay}
```

### 3. 模拟失败

```python
class FlakyExecutor:
    """模拟不稳定的执行器（测试用）"""
    def __init__(self, failure_rate=0.3):
        self.failure_rate = failure_rate

    async def execute(self, page):
        if random.random() < self.failure_rate:
            raise Exception(f"Random failure on page {page['page_no']}")

        await asyncio.sleep(1)
        return {"page_no": page["page_no"], "success": True}

# 使用
flaky_executor = FlakyExecutor(failure_rate=0.3)
results = await pipeline.execute_pages(pages, flaky_executor.execute)
```

### 4. 监控并发

```python
class MonitoredPagePipeline(PagePipeline):
    """带监控的页面流水线"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_tasks = 0
        self.max_active_tasks = 0

    async def _process_page_with_semaphore(self, *args, **kwargs):
        self.active_tasks += 1
        self.max_active_tasks = max(self.max_active_tasks, self.active_tasks)

        try:
            result = await super()._process_page_with_semaphore(*args, **kwargs)
            return result
        finally:
            self.active_tasks -= 1

    def get_stats(self):
        return {
            "active_tasks": self.active_tasks,
            "max_active_tasks": self.max_active_tasks,
            "max_concurrency": self.max_concurrency,
        }

# 使用
pipeline = MonitoredPagePipeline(max_concurrency=3)
results = await pipeline.execute_pages(pages, executor)
print(pipeline.get_stats())
# {'active_tasks': 0, 'max_active_tasks': 3, 'max_concurrency': 3}
```

---

## 常见问题

### Q1: 如何处理某些页面特别慢的情况？

A: 使用超时机制：

```python
async def executor_with_timeout(page):
    try:
        return await asyncio.wait_for(
            process_page(page),
            timeout=10.0  # 最多等10秒
        )
    except asyncio.TimeoutError:
        logger.warning(f"Page {page['page_no']} timed out")
        raise
```

### Q2: 如何保证结果的顺序？

A: 使用原始页面的顺序：

```python
# execute_pages 已经保证了这一点
results = await pipeline.execute_pages(pages, executor)
# results 的顺序与 pages 一致

# 如果需要按页号排序：
results_sorted = sorted(results, key=lambda r: r["page_no"])
```

### Q3: 如何处理内存不足的问题？

A: 降低并发数或分批处理：

```python
# 方案1：降低并发数
pipeline = create_page_pipeline(max_concurrency=2)

# 方案2：分批处理
batch_size = 20
for i in range(0, len(pages), batch_size):
    batch = pages[i:i+batch_size]
    results = await pipeline.execute_pages(batch, executor)
```

### Q4: 能否取消正在执行的任务？

A: 使用 `asyncio.Task` 和取消：

```python
async def execute_with_cancellation(pages, executor):
    """支持取消的执行"""
    tasks = [
        asyncio.create_task(executor(page))
        for page in pages
    ]

    try:
        # 等待所有任务（可被取消）
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    except asyncio.CancelledError:
        # 取消所有任务
        for task in tasks:
            task.cancel()
        raise
```

---

## 相关文档

- [设计指南](./design-guide.md) - Coordinator 层设计
- [实施指南](./implementation-guide.md) - 如何实现 page_pipeline
- [MasterGraph 文档](./master_graph.py.md) - 主工作流详解
