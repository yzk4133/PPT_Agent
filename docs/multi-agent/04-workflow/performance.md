# 性能优化详解

## 📋 概述

本文档详细说明系统中的性能优化策略和配置。

## ⚡ 性能指标

### 预期性能

| 场景 | 预期时间 | 说明 |
|------|---------|------|
| 5页 PPT（无研究） | < 60秒 | 简单场景 |
| 10页 PPT（有研究） | < 120秒 | 中等复杂度 |
| 20页 PPT（复杂） | < 200秒 | 高复杂度 |

### 并发效率

系统通过页面级并行执行实现 30%-60% 的性能提升：

```
串行执行时间: T
并行执行时间: T / efficiency
提升比例: efficiency = 1.3 - 1.6x
```

## 🚀 并行执行

### PagePipeline 并发控制

```python
class PagePipeline:
    def __init__(self, max_concurrency: int = 3):
        self.semaphore = asyncio.Semaphore(max_concurrency)
```

### 并发配置

| 参数 | 默认值 | 推荐范围 | 说明 |
|------|--------|---------|------|
| `max_concurrency` | 3 | 2-5 | 同时处理的页面数 |
| `max_retries` | 2 | 1-3 | 失败重试次数 |
| `retry_delay` | 1.0s | 0.5-2.0s | 重试延迟 |

### 并发示例

假设：
- `max_concurrency = 3`
- 页面数 = 10
- 每页处理时间 = 5秒

**串行执行**: 10 × 5 = 50秒
**并行执行**: 4 批 × 5 = 20秒（第一批3页，第二批3页，第三批3页，第四批1页）
**加速比**: 2.5x

## 🔄 异步 I/O

### 所有 LLM 调用都是异步的

```python
# ✅ 正确：异步调用
result = await self.chain.ainvoke(input_data)

# ❌ 错误：同步调用
result = self.chain.invoke(input_data)
```

### 并行 Agent 调用

```python
# 并行研究多个页面
tasks = [self.research_page(page) for page in pages]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

## 📊 进度映射

### 阶段进度分配

| 阶段 | 进度范围 | 权重 | 说明 |
|------|---------|------|------|
| 需求解析 | 0% → 15% | 15% | 单次 LLM 调用 |
| 框架设计 | 15% → 30% | 15% | 单次 LLM 调用 |
| 研究 | 30% → 50% | 20% | 并行页面处理 |
| 内容生成 | 50% → 80% | 30% | 并行页面处理 |
| 渲染 | 80% → 100% | 20% | 文件生成 |

### 进度计算公式

```python
# 研究阶段进度 = 30 + (已完成页面 / 总页面) * 20
progress = 30 + (completed / total) * 20

# 内容生成进度 = 50 + (已完成页面 / 总页面) * 30
progress = 50 + (completed / total) * 30
```

## 🎯 性能优化技巧

### 1. 调整并发数

```bash
# 环境变量配置
export PAGE_PIPELINE_CONCURRENCY=5
```

```python
# 代码配置
pipeline = create_page_pipeline(max_concurrency=5)
```

**权衡**:
- 并发数高 → 更快，但可能触发 API 限流
- 并发数低 → 更慢，但更稳定

### 2. 使用更快的模型

```bash
# 使用更快的模型
export LLM_MODEL=gpt-4o-mini
```

**模型性能对比**:

| 模型 | 速度 | 质量 | 推荐场景 |
|------|------|------|---------|
| gpt-4o-mini | 快 | 良好 | 通用场景 |
| gpt-4o | 中 | 优秀 | 高质量要求 |
| gpt-3.5-turbo | 很快 | 一般 | 测试/开发 |

### 3. 减少 LLM 调用

```python
# 使用缓存避免重复调用
from functools import lru_cache

@lru_cache(maxsize=128)
def get_default_modules(scene: str) -> List[str]:
    ...
```

### 4. 批量处理

```python
# 批量研究页面
await research_agent.research_all_pages(pages, indices)

# 而不是逐个研究
for page in pages:
    await research_agent.research_page(page)  # 慢
```

## 📈 性能监控

### 执行时间跟踪

```python
start_time = datetime.now()
result = await agent.process(input)
elapsed = (datetime.now() - start_time).total_seconds()
logger.info(f"Execution time: {elapsed:.2f}s")
```

### 性能日志

```python
logger.info(f"[PagePipeline] Completed: {len(successful)}/{total} pages in {elapsed:.2f}s")
logger.info(f"Parallel efficiency: {(total * time_per_page) / elapsed:.2f}x")
```

## 🔧 性能调优

### 常见性能问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 执行很慢 | 并发数太低 | 增加 `max_concurrency` |
| API 限流 | 并发数太高 | 降低 `max_concurrency` |
| 重试太多 | 不稳定的外部服务 | 调整 `max_retries` |
| 内存占用高 | 同时处理太多页面 | 降低并发或分批处理 |

### 性能调优示例

```python
# 针对不同场景优化配置

# 高吞吐量配置（多页，快速）
pipeline_fast = create_page_pipeline(
    max_concurrency=5,
    max_retries=1,
    retry_delay=0.5
)

# 高可靠性配置（少页，稳定）
pipeline_reliable = create_page_pipeline(
    max_concurrency=2,
    max_retries=3,
    retry_delay=2.0
)
```

## 📊 性能基准

### 测试场景

| 测试 | 页数 | 研究 | 并发数 | 预期时间 |
|------|------|------|--------|---------|
| 基础 | 5 | 否 | 3 | < 30s |
| 中等 | 10 | 是 | 3 | < 90s |
| 复杂 | 20 | 是 | 3 | < 180s |
| 高并发 | 20 | 是 | 5 | < 120s |

### 运行基准测试

```bash
cd backend/agents_langchain/tests
python test_integration.py
```

## 🔗 相关文档

- [state-flow.md](state-flow.md): 状态流转
- [error-handling.md](error-handling.md): 错误处理
- [../02-coordinator/page_pipeline.py.md](../02-coordinator/page_pipeline.py.md): 页面流水线
