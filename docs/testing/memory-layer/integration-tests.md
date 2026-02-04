# Memory 层集成测试详情

> **测试类型**: 集成测试
> **测试文件**: 4 个文件
> **测试用例数**: 50+
> **覆盖目标**: 验证组件交互

---

## 📋 目录

- [集成测试概述](#集成测试概述)
- [层级提升测试](#层级提升测试)
- [作用域隔离测试](#作用域隔离测试)
- [并发访问测试](#并发访问测试)
- [端到端测试](#端到端测试)

---

## 集成测试概述

### 什么是集成测试？

集成测试验证多个组件协同工作时的行为。对于 Memory 层：

- **测试对象**: 组件之间的交互
- **依赖方式**: 使用部分真实实现
- **执行速度**: 中等（秒级）
- **测试范围**: 完整工作流

### 集成测试的价值

1. **验证交互** - 确保组件间正确协作
2. **发现集成问题** - 找出接口不匹配
3. **测试工作流** - 验证端到端场景
4. **性能验证** - 测试真实负载下的表现

### 测试文件清单

```
integration/
├── test_layer_promotion.py      # 15+ 测试用例
├── test_scope_isolation.py      # 20+ 测试用例
├── test_concurrent_access.py    # 15+ 测试用例
└── test_end_to_end.py           # 10+ 测试用例
```

---

## 层级提升测试

**文件**: `integration/test_layer_promotion.py`
**测试用例数**: 15+

### 测试目标

验证数据在 L1 → L2 → L3 三层之间的自动流转。

### 测试场景

#### 1. L1 → L2 自动提升

##### 按访问次数提升

```python
class TestL1ToL2Promotion:
    async def test_l1_to_l2_by_access_count(self)
```

**测试流程**:
1. 在 L1 层写入数据
2. 访问数据 3 次（达到提升阈值）
3. 标记作用域为活跃
4. 触发提升引擎
5. 验证数据在 L2 层存在

**验证点**:
- ✅ 访问次数达到 3 次触发提升
- ✅ 数据成功写入 L2
- ✅ L1 层数据保留或删除（根据配置）

##### 按重要性提升

```python
async def test_l1_to_l2_by_importance(self)
```

**测试流程**:
1. 写入高重要性数据（importance ≥ 0.7）
2. 触发提升引擎
3. 验证数据在 L2 层

**验证点**:
- ✅ 重要性 ≥ 0.7 触发提升
- ✅ 无需多次访问即可提升

##### 批量提升

```python
async def test_l1_to_l2_batch_promotion(self)
```

**测试流程**:
1. 写入多个符合提升条件的数据
2. 触发批量提升
3. 验证多个数据都被提升

**验证点**:
- ✅ 批量提升功能正常
- ✅ 提升数量正确

#### 2. L2 → L3 自动提升

##### 按跨会话使用提升

```python
class TestL2ToL3Promotion:
    async def test_l2_to_l3_by_cross_session(self)
```

**测试流程**:
1. 在 L2 层写入数据
2. 从多个会话访问该数据
3. 触发提升引擎
4. 验证数据在 L3 层

**验证点**:
- ✅ 跨会话使用 ≥ 2 次触发提升
- ✅ 数据成功写入 L3

#### 3. 完整提升链

```python
class TestFullPromotionChain:
    async def test_full_chain_l1_to_l3(self)
```

**测试流程**:
1. 数据写入 L1
2. 多次访问触发 L1→L2 提升
3. 跨会话使用触发 L2→L3 提升
4. 验证数据最终在 L3 层

**验证点**:
- ✅ 完整提升链路畅通
- ✅ 每层提升规则正确
- ✅ 数据在各层正确传递

#### 4. 提升失败处理

```python
class TestPromotionWithFailures:
    async def test_promotion_with_l2_failure(self)
    async def test_partial_batch_failure(self)
```

**测试场景**:
- L2 写入失败
- 部分批次失败

**验证点**:
- ✅ 失败不影响其他数据
- ✅ 错误被正确记录
- ✅ 系统继续运行

#### 5. 提升优先级

```python
class TestPromotionPriority:
    async def test_high_importance_promoted_first(self)
```

**测试场景**:
- 高重要性数据优先提升

**验证点**:
- ✅ 提升优先级正确
- ✅ 限制数量时优先高价值

#### 6. 事件追踪

```python
class TestPromotionEventTracking:
    async def test_promotion_events_logged(self)
    async def test_promotion_stats(self)
```

**验证点**:
- ✅ 每次提升都被记录
- ✅ 统计信息准确

---

## 作用域隔离测试

**文件**: `integration/test_scope_isolation.py`
**测试用例数**: 20+

### 测试目标

验证不同作用域的数据严格隔离，无数据泄漏。

### 作用域类型

| 作用域 | 隔离范围 | 共享范围 |
|--------|---------|---------|
| **TASK** | 单个任务 | 不共享 |
| **SESSION** | 单个会话 | 不共享 |
| **AGENT** | 单个 Agent | 不共享 |
| **WORKSPACE** | 工作区内 | 工作区内所有 Agent |
| **USER** | 单个用户 | 不共享 |

### 测试场景

#### 1. 任务级隔离

```python
class TestTaskScopeIsolation:
    async def test_different_tasks_isolated(self)
    async def test_task_not_visible_to_other_tasks(self)
```

**验证点**:
- ✅ 不同任务的数据互不可见
- ✅ 相同键在不同任务中独立
- ✅ 任务作用域严格隔离

#### 2. 会话级隔离

```python
class TestSessionScopeIsolation:
    async def test_different_sessions_isolated(self)
    async def test_session_isolation_in_l2(self)
```

**验证点**:
- ✅ 不同会话的数据隔离
- ✅ L2 层也保持隔离
- ✅ 会话 ID 正确追踪

#### 3. Agent 级隔离

```python
class TestAgentScopeIsolation:
    async def test_different_agents_isolated(self)
    async def test_agent_private_data(self)
```

**验证点**:
- ✅ 不同 Agent 的数据隔离
- ✅ Agent 私有数据受保护
- ✅ 同一 Agent 可跨会话访问

#### 4. 工作区共享

```python
class TestWorkspaceScopeSharing:
    async def test_workspace_shared_by_agents(self)
    async def test_different_workspaces_isolated(self)
```

**验证点**:
- ✅ 工作区内数据可共享
- ✅ 不同工作区数据隔离
- ✅ 多 Agent 协作支持

#### 5. 用户级全局

```python
class TestUserScopeGlobal:
    async def test_user_scope_globally_visible(self)
    async def test_different_users_isolated(self)
```

**验证点**:
- ✅ 用户级数据全局可见
- ✅ 不同用户数据隔离
- ✅ 用户偏好跨会话可用

#### 6. 跨作用域泄漏检测

```python
class TestCrossScopeDataLeak:
    async def test_no_cross_scope_leak_task_to_session(self)
    async def test_no_cross_scope_leak_agent_to_workspace(self)
    async def test_clear_scope_only_affects_target(self)
    async def test_list_keys_only_in_scope(self)
```

**验证点**:
- ✅ 任务数据不泄漏到会话
- ✅ Agent 数据不泄漏到工作区
- ✅ 清理作用域不影响其他
- ✅ 键列表仅返回目标作用域

#### 7. 作用域层次

```python
class TestScopeHierarchy:
    async def test_multiple_scopes_coexist(self)
    async def test_scope_delete_doesnt_affect_others(self)
```

**验证点**:
- ✅ 多个作用域可共存
- ✅ 删除一个不影响其他
- ✅ 同一键在不同作用域独立

#### 8. 提升时保留作用域

```python
class TestScopeIsolationWithPromotion:
    async def test_promotion_preserves_scope(self)
```

**验证点**:
- ✅ 提升后作用域信息保留
- ✅ L2 中的数据保持作用域隔离

---

## 并发访问测试

**文件**: `integration/test_concurrent_access.py`
**测试用例数**: 15+

### 测试目标

验证系统在高并发场景下的线程安全性和数据一致性。

### 测试场景

#### 1. L1 并发访问

```python
class TestConcurrentL1Access:
    async def test_concurrent_reads(self)
    async def test_concurrent_writes(self)
    async def test_concurrent_writes_same_key(self)
    async def test_concurrent_mixed_operations(self)
```

**验证点**:
- ✅ 并发读取数据一致
- ✅ 并发写入不同键无冲突
- ✅ 并发写入同一键（最后写入胜）
- ✅ 混合读写操作正常

#### 2. L2 并发操作

```python
class TestConcurrentL2Access:
    async def test_concurrent_redis_operations(self)
    async def test_concurrent_batch_operations(self)
```

**验证点**:
- ✅ 并发 Redis 操作正确
- ✅ 并发批量操作无冲突
- ✅ 管道操作线程安全

#### 3. 并发提升

```python
class TestConcurrentPromotion:
    async def test_concurrent_l1_to_l2_promotion(self)
```

**验证点**:
- ✅ 并发提升无冲突
- ✅ 提升任务正确执行

#### 4. LRU 竞态条件

```python
class TestLRURaceConditions:
    async def test_lru_concurrent_access(self)
    async def test_lru_eviction_under_load(self)
```

**验证点**:
- ✅ LRU 缓存并发安全
- ✅ 锁机制防止竞态
- ✅ 高负载下淘汰正确

#### 5. 作用域并发操作

```python
class TestConcurrentScopeOperations:
    async def test_concurrent_different_scopes(self)
    async def test_concurrent_scope_isolation(self)
```

**验证点**:
- ✅ 不同作用域并发独立
- ✅ 作用域隔离在并发下保持

#### 6. 并发删除

```python
class TestConcurrentDeleteOperations:
    async def test_concurrent_deletes(self)
    async def test_concurrent_delete_and_read(self)
```

**验证点**:
- ✅ 并发删除无冲突
- ✅ 删除和读取并发正常

#### 7. 并发清理作用域

```python
class TestConcurrentClearScope:
    async def test_concurrent_clear_different_scopes(self)
```

**验证点**:
- ✅ 并发清理不同作用域
- ✅ 清理计数准确

#### 8. 并发统计

```python
class TestConcurrentStats:
    async def test_concurrent_stats_collection(self)
```

**验证点**:
- ✅ 并发统计收集一致
- ✅ 统计数据准确

---

## 端到端测试

**文件**: `integration/test_end_to_end.py`
**测试用例数**: 10+

### 测试目标

验证完整的用户场景和工作流。

### 测试场景

#### 1. 完整数据生命周期

```python
class TestFullLifecycle:
    async def test_lifecycle_l1_to_l3(self)
    async def test_lifecycle_with_deletion(self)
```

**测试流程**:
1. 写入到 L1
2. 访问触发 L1→L2 提升
3. 跨会话触发 L2→L3 提升
4. 从 L3 检索验证
5. 删除数据

**验证点**:
- ✅ 完整生命周期畅通
- ✅ 每层功能正确
- ✅ 删除从所有层生效

#### 2. 多 Agent 协作

```python
class TestMultiAgentScenarios:
    async def test_agent_workspace_sharing(self)
    async def test_agent_private_workspace(self)
```

**测试场景**:
- Agent A 写入工作区数据
- Agent B 读取工作区数据
- Agent 私有数据隔离

**验证点**:
- ✅ 工作区共享正常
- ✅ 私有数据受保护
- ✅ 多 Agent 协作支持

#### 3. 高负载场景

```python
class TestHighLoadScenarios:
    async def test_high_write_volume(self)
    async def test_concurrent_high_load(self)
```

**测试场景**:
- 写入 500+ 条数据
- 并发高负载写入

**验证点**:
- ✅ 系统稳定运行
- ✅ 容量限制正确
- ✅ 无数据损坏

#### 4. 故障恢复

```python
class TestFailureRecovery:
    async def test_l2_failure_graceful_degradation(self)
    async def test_recovery_after_failure(self)
```

**测试场景**:
- L2 层失败
- L2 层恢复

**验证点**:
- ✅ 优雅降级到 L1
- ✅ 恢复后继续工作
- ✅ 无数据丢失

#### 5. 混合作用域场景

```python
class TestMixedScopeScenarios:
    async def test_multi_scope_data_flow(self)
    async def test_scope_hierarchy(self)
```

**测试场景**:
- 数据在不同作用域间流动
- 多层作用域层次

**验证点**:
- ✅ 不同作用域共存
- ✅ 作用域层次正确
- ✅ 数据流正确

#### 6. 管理器集成

```python
class TestManagerIntegration:
    async def test_manager_set_and_get(self)
    async def test_manager_auto_layer_selection(self)
    async def test_manager_cascade_get(self)
```

**验证点**:
- ✅ 管理器协调正确
- ✅ 自动层级选择
- ✅ 级联回写

#### 7. 统计聚合

```python
class TestStatsAggregation:
    async def test_global_stats(self)
```

**验证点**:
- ✅ 全局统计正确聚合
- ✅ 各层统计准确

#### 8. 后台任务

```python
class TestBackgroundTasks:
    async def test_background_task_lifecycle(self)
```

**验证点**:
- ✅ 后台任务正确启动
- ✅ 后台任务正确停止
- ✅ 任务清理完整

---

## 运行集成测试

### 运行所有集成测试

```bash
cd backend/memory/tests
pytest integration/ -v
```

### 运行特定文件

```bash
# 层级提升测试
pytest integration/test_layer_promotion.py -v

# 作用域隔离测试
pytest integration/test_scope_isolation.py -v

# 并发访问测试
pytest integration/test_concurrent_access.py -v

# 端到端测试
pytest integration/test_end_to_end.py -v
```

### 带详细输出

```bash
# 显示 print 输出
pytest integration/ -v -s

# 显示更详细的 traceback
pytest integration/ -v --tb=long
```

---

## 集成测试模式

### 1. 烟雾测试（Smoke Tests）

快速验证基本功能：

```bash
pytest integration/ -k "test_l1_to_l2_by_access_count or test_different_tasks_isolated" -v
```

### 2. 边界测试

测试极限情况：

```bash
pytest integration/ -k "high_load or failure or concurrent" -v
```

### 3. 回归测试

验证修复后未引入新问题：

```bash
pytest integration/ -v
```

---

## 集成测试最佳实践

### 1. 真实场景

```python
# 好的集成测试 - 模拟真实场景
async def test_multi_agent_collaboration(self):
    # Agent A 写入工作区
    await manager.set("shared", {"from": "A"}, scope=WORKSPACE, scope_id="ws1")

    # Agent B 读取工作区
    result = await manager.get("shared", scope=WORKSPACE, scope_id="ws1")
    assert result[0]["from"] == "A"
```

### 2. 完整工作流

```python
async def test_full_workflow(self):
    # 1. 写入
    await manager.set("key", {"value": 1}, scope=TASK, scope_id="task1")

    # 2. 多次访问
    for _ in range(3):
        await manager.get("key", scope=TASK, scope_id="task1")

    # 3. 提升到 L2
    await manager.batch_flush_l1_to_l2(scope=TASK, scope_id="task1")

    # 4. 验证在 L2
    exists = await manager.l2.exists("key", scope=TASK, scope_id="task1")
    assert exists is True
```

### 3. 验证副作用

```python
async def test_promotion_side_effects(self):
    # 提升前：数据在 L1
    in_l1_before = await manager.l1.exists("key", scope, scope_id)

    # 触发提升
    await engine.promote_l1_to_l2(l1, l2)

    # 提升后：数据在 L2
    in_l2_after = await manager.l2.exists("key", scope, scope_id)

    assert in_l1_before is True
    assert in_l2_after is True
```

---

## 相关文档

- [单元测试详情](./unit-tests.md)
- [测试覆盖率报告](./coverage-report.md)
- [运行指南](./running-tests.md)
