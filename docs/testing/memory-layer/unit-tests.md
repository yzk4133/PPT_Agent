# Memory 层单元测试详情

> **测试类型**: 单元测试
> **测试文件**: 6 个文件
> **测试用例数**: 150+
> **覆盖目标**: ≥ 80%

---

## 📋 目录

- [测试概述](#测试概述)
- [数据模型测试](#数据模型测试)
- [L1 瞬时层测试](#l1-瞬时层测试)
- [L2 短期层测试](#l2-短期层测试)
- [L3 长期层测试](#l3-长期层测试)
- [提升引擎测试](#提升引擎测试)
- [管理器测试](#管理器测试)

---

## 测试概述

### 什么是单元测试？

单元测试是对软件中最小可测试单元（通常是函数、类或模块）进行验证的测试。对于 Memory 层：

- **测试对象**: 独立的类和函数
- **依赖方式**: 使用 Mock 对象隔离外部依赖
- **执行速度**: 快速（毫秒级）
- **测试范围**: 单一功能点

### 单元测试的价值

1. **快速反馈** - 几秒钟内发现问题
2. **精确定位** - 直接定位到具体的函数或方法
3. **重构保护** - 修改代码时快速验证
4. **文档作用** - 展示组件的正确使用方式

### 测试文件清单

```
unit/
├── test_models.py         # 30+ 测试用例
├── test_l1_layer.py       # 40+ 测试用例
├── test_l2_layer.py       # 35+ 测试用例
├── test_l3_layer.py       # 25+ 测试用例
├── test_promotion.py      # 30+ 测试用例
└── test_manager.py        # 25+ 测试用例
```

---

## 数据模型测试

**文件**: `unit/test_models.py`
**测试用例数**: 30+
**覆盖目标**: ≥ 90%

### 测试范围

#### 1. MemoryMetadata 类

测试核心数据结构的所有功能：

##### 基础功能测试
```python
class TestMemoryMetadata:
    def test_metadata_creation(self)
    def test_metadata_creation_with_custom_values(self)
```

**验证内容**:
- ✅ 默认值正确初始化
- ✅ 自定义值正确设置
- ✅ created_at 和 last_accessed 自动生成

##### 重要性限制测试
```python
def test_importance_clamping_high(self)
def test_importance_clamping_low(self)
def test_importance_boundary_values(self)
```

**验证内容**:
- ✅ 重要性 > 1.0 被限制为 1.0
- ✅ 重要性 < 0.0 被限制为 0.0
- ✅ 边界值 0.0 和 1.0 保持不变

##### 访问计数测试
```python
def test_increment_access(self)
def test_increment_access_multiple_times(self)
```

**验证内容**:
- ✅ 每次调用增加 1
- ✅ last_accessed 时间自动更新
- ✅ 支持多次递增

##### 会话 ID 管理测试
```python
def test_add_session_id_new(self)
def test_add_session_id_duplicate(self)
def test_add_multiple_session_ids(self)
```

**验证内容**:
- ✅ 新会话 ID 被添加
- ✅ 重复会话 ID 被忽略
- ✅ 支持多个会话 ID

##### 提升判断测试
```python
def test_should_promote_to_l2_by_access_count(self)
def test_should_promote_to_l2_by_importance(self)
def test_should_promote_to_l2_combined_conditions(self)
def test_should_promote_to_l3_by_session_count(self)
```

**验证内容**:
- ✅ 访问次数 ≥ 3 触发 L2 提升
- ✅ 重要性 ≥ 0.7 触发 L2 提升
- ✅ 会话数 ≥ 2 触发 L3 提升
- ✅ 组合条件正确判断

##### 序列化测试
```python
def test_to_dict(self)
def test_to_dict_empty_collections(self)
```

**验证内容**:
- ✅ 正确转换为字典格式
- ✅ 时间戳正确格式化
- ✅ 空集合正确处理

#### 2. 枚举类测试

```python
class TestMemoryEnums:
    def test_memory_layer_values(self)
    def test_memory_scope_values(self)
    def test_promotion_reason_values(self)
```

**验证内容**:
- ✅ 所有枚举值正确定义
- ✅ 枚举值符合预期

#### 3. PromotionTracker 类

##### 追踪功能测试
```python
class TestPromotionTracker:
    def test_tracker_initialization(self)
    def test_record_promotion(self)
    def test_record_multiple_promotions_same_key(self)
```

**验证内容**:
- ✅ 追踪器正确初始化
- ✅ 提升事件正确记录
- ✅ 同一键多次提升都被记录

##### 查询功能测试
```python
def test_get_promotion_history_existing(self)
def test_get_promotion_history_nonexistent(self)
```

**验证内容**:
- ✅ 返回现有键的历史
- ✅ 不存在的键返回空列表

##### 统计功能测试
```python
def test_get_stats_empty_tracker(self)
def test_get_stats_with_data(self)
```

**验证内容**:
- ✅ 空追踪器返回零统计
- ✅ 有数据时正确聚合

---

## L1 瞬时层测试

**文件**: `unit/test_l1_layer.py`
**测试用例数**: 40+
**覆盖目标**: ≥ 85%

### 测试范围

#### 1. LRUCache 类

##### 基础操作测试
```python
class TestLRUCache:
    async def test_cache_set_and_get(self)
    async def test_cache_get_nonexistent(self)
```

**验证内容**:
- ✅ 数据正确写入和读取
- ✅ 不存在的键返回 None

##### LRU 淘汰测试
```python
async def test_lru_eviction(self)
async def test_lru_updates_on_access(self)
```

**验证内容**:
- ✅ 超容量时最旧数据被淘汰
- ✅ 访问数据更新其位置
- ✅ 淘汰顺序正确

##### 缓存管理测试
```python
async def test_cache_delete(self)
async def test_cache_exists(self)
async def test_cache_keys_no_pattern(self)
async def test_cache_keys_with_pattern(self)
async def test_cache_clear(self)
async def test_cache_size(self)
```

**验证内容**:
- ✅ 删除操作正确
- ✅ 存在性检查准确
- ✅ 键列表支持模式匹配
- ✅ 清空操作正确
- ✅ 大小查询准确

#### 2. L1TransientLayer 类

##### 初始化和基础操作
```python
class TestL1TransientLayer:
    async def test_layer_initialization(self)
    async def test_set_and_get(self)
    async def test_get_nonexistent_key(self)
```

**验证内容**:
- ✅ 层级正确初始化
- ✅ 数据正确存储和检索
- ✅ 未命中时返回 None

##### 访问计数测试
```python
async def test_get_increments_access_count(self)
```

**验证内容**:
- ✅ 每次获取增加访问计数
- ✅ 访问计数正确累加

##### TTL 功能测试
```python
async def test_set_with_custom_ttl(self)
```

**验证内容**:
- ✅ 自定义 TTL 生效
- ✅ 过期数据被清理

##### 元数据测试
```python
async def test_get_metadata(self)
async def test_update_metadata(self)
async def test_update_metadata_nonexistent_key(self)
```

**验证内容**:
- ✅ 元数据正确获取
- ✅ 元数据正确更新
- ✅ 不存在的键返回 False

##### 作用域管理测试
```python
async def test_list_keys_no_pattern(self)
async def test_list_keys_with_pattern(self)
async def test_list_keys_scope_isolation(self)
async def test_clear_scope(self)
```

**验证内容**:
- ✅ 键列表支持模式过滤
- ✅ 不同作用域数据隔离
- ✅ 作用域清理正确

##### 提升相关测试
```python
async def test_get_promotion_candidates_by_access(self)
async def test_get_promotion_candidates_by_importance(self)
async def test_batch_flush_to_l2(self)
```

**验证内容**:
- ✅ 按访问次数识别候选
- ✅ 按重要性识别候选
- ✅ 批量刷新功能正确

##### 并发和性能测试
```python
async def test_concurrent_access(self)
async def test_lru_eviction_behavior(self)
```

**验证内容**:
- ✅ 并发读写无冲突
- ✅ LRU 在高负载下正确淘汰

---

## L2 短期层测试

**文件**: `unit/test_l2_layer.py`
**测试用例数**: 35+
**覆盖目标**: ≥ 80%

### 测试范围

#### 1. 连接管理

```python
class TestL2ShortTermLayer:
    def test_layer_initialization(self)
    async def test_redis_connection_available(self)
```

**验证内容**:
- ✅ 层级正确初始化
- ✅ Redis 连接可用性检查

#### 2. 基础数据操作

```python
async def test_set_and_get(self)
async def test_get_nonexistent_key(self)
async def test_get_increments_access_count(self)
```

**验证内容**:
- ✅ 数据正确存储和检索
- ✅ 访问计数自动递增

#### 3. TTL 功能

```python
async def test_set_with_custom_ttl(self)
```

**验证内容**:
- ✅ 自定义 TTL 正确应用
- ✅ 过期后数据不可访问

#### 4. 序列化测试

```python
async def test_serialization_complex_data(self)
async def test_serialization_metadata(self)
```

**验证内容**:
- ✅ 复杂数据结构正确序列化
- ✅ Unicode 字符正确处理
- ✅ 元数据序列化/反序列化

#### 5. 批量操作

```python
async def test_batch_set(self)
async def test_batch_set_with_metadata(self)
```

**验证内容**:
- ✅ 批量设置功能正确
- ✅ 批量操作性能良好
- ✅ 元数据正确传递

#### 6. 作用域和隔离

```python
async def test_list_keys(self)
async def test_list_keys_with_pattern(self)
async def test_list_keys_scope_isolation(self)
```

**验证内容**:
- ✅ 键列表功能正确
- ✅ 作用域隔离有效

#### 7. 跨会话追踪

```python
async def test_cross_session_tracking(self)
async def test_session_scope_adds_session_id(self)
```

**验证内容**:
- ✅ 跨会话使用正确追踪
- ✅ 会话 ID 正确添加到元数据

#### 8. 故障处理

```python
async def test_redis_failure_handling_get(self)
async def test_redis_failure_handling_set(self)
async def test_redis_failure_handling_delete(self)
```

**验证内容**:
- ✅ Redis 故障时优雅降级
- ✅ 错误被正确处理

---

## L3 长期层测试

**文件**: `unit/test_l3_layer.py`
**测试用例数**: 25+
**覆盖目标**: ≥ 75%

### 测试范围

#### 1. 基础 CRUD 操作

```python
class TestL3LongtermLayer:
    async def test_set_success(self)
    async def test_set_failure(self)
    async def test_get_success(self)
    async def test_get_not_found(self)
```

**验证内容**:
- ✅ 数据正确设置
- ✅ 数据正确检索
- ✅ 错误正确返回

#### 2. 删除操作

```python
async def test_delete_success(self)
async def test_delete_not_found(self)
```

**验证内容**:
- ✅ 存在的数据正确删除
- ✅ 不存在的数据返回 False

#### 3. 存在性检查

```python
async def test_exists_true(self)
async def test_exists_false(self)
```

**验证内容**:
- ✅ 存在的数据返回 True
- ✅ 不存在的数据返回 False

#### 4. 键管理

```python
async def test_list_keys(self)
async def test_list_keys_with_pattern(self)
```

**验证内容**:
- ✅ 键列表正确返回
- ✅ 模式匹配正确工作

#### 5. 元数据操作

```python
async def test_get_metadata(self)
async def test_update_metadata(self)
async def test_update_metadata_not_found(self)
```

**验证内容**:
- ✅ 元数据正确获取
- ✅ 元数据正确更新
- ✅ 不存在的键返回 False

#### 6. 向量搜索

```python
async def test_semantic_search(self)
async def test_semantic_search_empty_results(self)
async def test_semantic_search_unavailable(self)
```

**验证内容**:
- ✅ 向量搜索功能可用
- ✅ 无结果时返回空列表
- ✅ pgvector 不可用时降级

#### 7. 数据处理

```python
async def test_jsonb_storage(self)
async def test_upsert_behavior(self)
async def test_full_text_search(self)
async def test_importance_filtering(self)
```

**验证内容**:
- ✅ JSONB 数据正确存储
- ✅ Upsert 行为正确（存在则更新，不存在则插入）
- ✅ 全文检索功能
- ✅ 重要性过滤功能

#### 8. 文本提取

```python
async def test_extract_text_content_string(self)
async def test_extract_text_content_dict(self)
async def test_extract_text_content_list(self)
async def test_extract_text_content_complex(self)
```

**验证内容**:
- ✅ 从字符串提取文本
- ✅ 从字典提取文本
- ✅ 从列表提取文本
- ✅ 从复杂结构提取文本

---

## 提升引擎测试

**文件**: `unit/test_promotion.py`
**测试用例数**: 30+
**覆盖目标**: ≥ 80%

### 测试范围

#### 1. 配置测试

```python
class TestPromotionConfig:
    def test_default_config(self)
    def test_custom_config(self)
```

**验证内容**:
- ✅ 默认配置值正确
- ✅ 自定义配置生效

#### 2. 作用域追踪器

```python
class TestActiveScopeTracker:
    async def test_initialization(self)
    async def test_mark_active(self)
    async def test_mark_multiple_active(self)
    async def test_is_active_nonexistent(self)
    async def test_is_active_expired(self)
    async def test_get_active_scopes(self)
    async def test_get_active_scopes_filters_expired(self)
    async def test_cleanup_inactive(self)
    async def test_mark_active_updates_timestamp(self)
```

**验证内容**:
- ✅ 作用域正确标记为活跃
- ✅ 过期作用域被清理
- ✅ 活跃作用域列表正确
- ✅ 时间戳更新功能

#### 3. 规则引擎

```python
class TestPromotionRuleEngine:
    def test_should_promote_l1_to_l2_by_access(self)
    def test_should_promote_l1_to_l2_by_importance(self)
    def test_should_not_promote_l1_to_l2(self)
    def test_should_promote_l1_with_long_lifetime(self)
    def test_should_promote_l2_to_l3_by_cross_session(self)
    def test_should_promote_l2_to_l3_by_high_access_and_importance(self)
    def test_should_not_promote_l2_to_l3(self)
```

**验证内容**:
- ✅ L1→L2 规则：访问频率
- ✅ L1→L2 规则：重要性
- ✅ L1→L2 规则：长期存在
- ✅ L2→L3 规则：跨会话
- ✅ L2→L3 规则：高访问+高重要性

#### 4. 数据迁移器

```python
class TestDataMigrator:
    async def test_migrate_l1_to_l2_empty_candidates(self)
    async def test_migrate_l1_to_l2_success(self)
    async def test_migrate_l1_to_l2_with_failure(self)
    async def test_migrate_l1_to_l2_batches(self)
    async def test_migrate_l2_to_l3_success(self)
    async def test_migrate_l2_to_l3_with_failure(self)
    async def test_migrate_l2_to_l3_increments_importance(self)
```

**验证内容**:
- ✅ 空候选列表处理
- ✅ 成功迁移
- ✅ 失败处理
- ✅ 批量处理
- ✅ 重要性自动提升

#### 5. 事件记录器

```python
class TestPromotionEventLogger:
    async def test_log_event(self)
    async def test_log_event_with_error(self)
    async def test_get_events(self)
    async def test_get_events_filtered_by_key(self)
    async def test_get_events_filtered_by_layer(self)
    async def test_get_stats(self)
    async def test_clear_old_events(self)
    async def test_max_history_limit(self)
```

**验证内容**:
- ✅ 事件正确记录
- ✅ 失败事件正确记录
- ✅ 事件查询和筛选
- ✅ 统计信息正确
- ✅ 旧事件清理
- ✅ 历史记录限制

#### 6. 提升引擎

```python
class TestPromotionEngine:
    def test_initialization(self)
    async def test_mark_scope_active(self)
    async def test_promote_l1_to_l2_empty(self)
    async def test_promote_l2_to_l3_empty(self)
    async def test_get_stats(self)
    async def test_get_promotion_history(self)
```

**验证内容**:
- ✅ 引擎正确初始化
- ✅ 作用域激活标记
- ✅ L1→L2 提升流程
- ✅ L2→L3 提升流程
- ✅ 统计信息聚合

---

## 管理器测试

**文件**: `unit/test_manager.py`
**测试用例数**: 25+
**覆盖目标**: ≥ 75%

### 测试范围

#### 1. 初始化

```python
class TestHierarchicalMemoryManager:
    def test_initialization(self)
    def test_initialization_with_promotion(self)
```

**验证内容**:
- ✅ 管理器正确初始化
- ✅ 自动提升可配置
- ✅ 三层正确创建

#### 2. 数据获取

```python
async def test_get_from_l1(self)
async def test_get_from_l2_with_l1_fallback(self)
async def test_get_from_l3_with_cascade(self)
async def test_get_not_found(self)
async def test_get_without_search_all_layers(self)
```

**验证内容**:
- ✅ 从 L1 获取
- ✅ 从 L2 获取并回写 L1
- ✅ 从 L3 获取并级联回写
- ✅ 未命中处理
- ✅ 搜索范围控制

#### 3. 数据设置

```python
async def test_set_to_l1(self)
async def test_set_to_l2_by_importance(self)
async def test_set_to_l2_by_scope(self)
async def test_set_to_l3_direct(self)
async def test_set_with_tags(self)
```

**验证内容**:
- ✅ 设置到 L1
- ✅ 按重要性设置到 L2
- ✅ 按作用域设置到 L2
- ✅ 直接设置到 L3
- ✅ 标签正确传递

#### 4. 数据删除

```python
async def test_delete_from_l1_only(self)
async def test_delete_from_all_layers(self)
```

**验证内容**:
- ✅ 仅删除 L1
- ✅ 删除所有层
- ✅ 删除结果正确

#### 5. 作用域管理

```python
async def test_exists(self)
async def test_exists_not_found(self)
async def test_clear_scope_all_layers(self)
async def test_clear_scope_specific_layers(self)
```

**验证内容**:
- ✅ 存在性检查
- ✅ 清理所有层
- ✅ 清理特定层

#### 6. 统计和监控

```python
async def test_get_stats(self)
```

**验证内容**:
- ✅ 统计信息正确聚合
- ✅ 各层统计正确

#### 7. 高级功能

```python
async def test_manual_promote_to_l3(self)
async def test_manual_promote_to_l3_not_found(self)
async def test_batch_flush_l1_to_l2(self)
async def test_batch_flush_l1_to_l2_empty(self)
async def test_semantic_search(self)
```

**验证内容**:
- ✅ 手动提升到 L3
- ✅ 批量刷新 L1 到 L2
- ✅ 语义搜索功能

#### 8. 辅助功能

```python
def test_determine_target_layer_by_importance(self)
def test_determine_target_layer_by_scope(self)
```

**验证内容**:
- ✅ 按重要性确定目标层
- ✅ 按作用域确定目标层

#### 9. 后台任务

```python
async def test_start_background_tasks(self)
async def test_stop_background_tasks(self)
```

**验证内容**:
- ✅ 后台任务正确启动
- ✅ 后台任务正确停止

#### 10. 全局管理器

```python
class TestGlobalMemoryManager:
    def test_get_global_memory_manager(self)
    async def test_init_global_memory_manager(self)
    async def test_shutdown_global_memory_manager(self)
```

**验证内容**:
- ✅ 全局实例获取
- ✅ 全局实例初始化
- ✅ 全局实例关闭

---

## 运行单元测试

### 运行所有单元测试

```bash
cd backend/memory/tests
pytest unit/ -v
```

### 运行特定文件

```bash
# 测试数据模型
pytest unit/test_models.py -v

# 测试 L1 层
pytest unit/test_l1_layer.py -v

# 测试 L2 层
pytest unit/test_l2_layer.py -v

# 测试 L3 层
pytest unit/test_l3_layer.py -v

# 测试提升引擎
pytest unit/test_promotion.py -v

# 测试管理器
pytest unit/test_manager.py -v
```

### 带覆盖率运行

```bash
pytest unit/ --cov=backend.memory --cov-report=html
```

---

## 单元测试最佳实践

### 1. 测试命名

```python
# 好的命名
async def test_lru_eviction_when_capacity_exceeded(self)
async def test_promotion_by_access_count(self)

# 避免的命名
async def test_lru(self)
async def test_promotion(self)
```

### 2. AAA 模式

```python
async def test_set_and_get(self):
    # Arrange（准备）
    layer = L1TransientLayer(capacity=100)
    test_value = {"data": "test"}

    # Act（执行）
    await layer.set("key", test_value, MemoryScope.SESSION, "session_1")
    result = await layer.get("key", MemoryScope.SESSION, "session_1")

    # Assert（断言）
    assert result is not None
    assert result[0] == test_value
```

### 3. 独立性

```python
# 每个测试独立运行
async def test_feature_x(self):
    layer = create_fresh_layer()  # 不依赖其他测试的状态
    # ...

async def test_feature_y(self):
    layer = create_fresh_layer()  # 创建新实例
    # ...
```

### 4. 清晰的断言

```python
# 好的断言
assert result.success_count == 5
assert error_message in result.errors[0]

# 避免模糊的断言
assert result  # 不清楚测试了什么
```

---

## 相关文档

- [集成测试详情](./integration-tests.md)
- [测试覆盖率报告](./coverage-report.md)
- [运行指南](./running-tests.md)
