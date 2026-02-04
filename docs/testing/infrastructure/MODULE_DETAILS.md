# 模块测试详细说明

> **Infrastructure 层各模块测试内容详解**

---

## 📦 Database 模块测试

**文件**: `database/test_connection_manager.py`
**测试用例**: 14 个
**目标覆盖率**: 80%+

### 测试场景

#### 1. 初始化测试 (2 个)
- `test_initialization` - 测试数据库管理器初始化
- `test_double_initialization_protection` - 测试重复初始化防护

#### 2. 会话管理测试 (4 个)
- `test_postgres_session_creation` - 测试 PostgreSQL 会话创建
- `test_redis_client_creation` - 测试 Redis 客户端创建
- `test_postgres_context_manager` - 测试 PostgreSQL 上下文管理器
- `test_redis_context_manager` - 测试 Redis 上下文管理器

#### 3. 事务管理测试 (2 个)
- `test_session_commit_on_success` - 测试成功时提交
- `test_session_rollback_on_error` - 测试异常时回滚

#### 4. 健康检查测试 (3 个)
- `test_postgres_health_check_success` - 测试 PostgreSQL 健康检查成功
- `test_postgres_health_check_failure` - 测试 PostgreSQL 健康检查失败
- `test_redis_health_check` - 测试 Redis 健康检查

#### 5. 其他功能测试 (3 个)
- `test_pool_stats` - 测试连接池统计
- `test_close_all_connections` - 测试关闭所有连接
- `test_uninitialized_access` - 测试未初始化时访问的异常

### Mock 策略
- PostgreSQL: 使用 `async_mock` 模拟引擎和会话
- Redis: 使用 `AsyncMock` 模拟客户端
- 连接池: 使用 `MagicMock` 模拟连接池对象

---

## 🤖 LLM 模块测试

### 1. Model Factory 测试

**文件**: `llm/test_model_factory.py`
**测试用例**: 18 个
**目标覆盖率**: 80%+

#### 测试场景

##### 模型创建 (6 个)
- `test_create_deepseek_model` - 测试创建 DeepSeek 模型
- `test_create_openai_model` - 测试创建 OpenAI 模型
- `test_create_claude_model` - 测试创建 Claude 模型
- `test_create_google_model` - 测试创建 Google Gemini 模型
- `test_create_qwen_model` - 测试创建 Qwen 模型
- `test_model_caching` - 测试模型缓存

##### 降级机制 (4 个)
- `test_create_model_with_fallback_success` - 测试降级成功
- `test_fallback_on_primary_failure` - 测试主模型失败时降级
- `test_fallback_disabled` - 测试禁用降级时直接失败
- `test_both_primary_and_fallback_fail` - 测试主备模型都失败

##### 熔断器 (2 个)
- `test_create_model_circuit_breaker` - 测试熔断器功能
- `test_reset_circuit_breaker` - 测试熔断器重置

##### 其他功能 (6 个)
- `test_get_litellm_model_name` - 测试模型名称转换
- `test_create_litellm_model` - 测试创建 LiteLLM 模型
- `test_clear_model_cache` - 测试清除模型缓存
- `test_clear_all_model_cache` - 测试清除所有缓存
- `test_custom_config` - 测试自定义配置
- `test_global_factory_singleton` - 测试全局工厂单例

---

### 2. Retry Decorator 测试

**文件**: `llm/test_retry_decorator.py`
**测试用例**: 22 个
**目标覆盖率**: 80%+

#### 测试场景

##### 异常分类 (3 个)
- `test_retryable_error` - 测试 RetryableError
- `test_fallback_error` - 测试 FallbackError
- `test_fatal_error` - 测试 FatalError

##### 熔断器测试 (7 个)
- `test_circuit_breaker_call_success` - 测试熔断器调用成功
- `test_circuit_breaker_call_failure` - 测试熔断器调用失败
- `test_circuit_breaker_open_state` - 测试熔断器 OPEN 状态
- `test_circuit_breaker_half_open_state` - 测试熔断器 HALF_OPEN 状态
- `test_circuit_breaker_half_open_failure` - 测试 HALF_OPEN 状态下失败
- `test_circuit_breaker_reset` - 测试熔断器重置
- `test_get_circuit_breaker` - 测试获取熔断器

##### 重试装饰器 (5 个)
- `test_retry_with_exponential_backoff` - 测试指数退避重试
- `test_max_retries_exceeded` - 测试超过最大重试次数
- `test_no_retry_on_success` - 测试成功时不重试
- `test_retry_with_custom_exceptions` - 测试自定义异常重试

##### 降级重试 (3 个)
- `test_retry_with_fallback_success` - 测试降级成功
- `test_retry_with_fallback_function` - 测试降级函数
- `test_retry_with_fatal_error_no_retry` - 测试致命错误不重试

##### 异步测试 (4 个)
- `test_async_retry_on_failure` - 测试异步重试
- `test_async_retry_success` - 测试异步成功
- `test_async_retry_with_fallback` - 测试异步降级
- `test_async_fatal_error_no_retry` - 测试异步致命错误

---

### 3. LLM Cache 测试

**文件**: `llm/test_llm_cache.py`
**测试用例**: 14 个
**目标覆盖率**: 80%+

#### 测试场景

##### 基础功能 (6 个)
- `test_cache_initialization` - 测试缓存初始化
- `test_generate_cache_key` - 测试缓存键生成
- `test_cache_set_and_get` - 测试缓存设置和获取
- `test_cache_hit` - 测试缓存命中
- `test_cache_miss` - 测试缓存未命中
- `test_cache_expiration` - 测试缓存过期

##### 高级功能 (8 个)
- `test_cache_set_and_get` - 测试缓存操作
- `test_cleanup_expired` - 测试清理过期缓存
- `test_get_stats` - 测试获取统计信息
- `test_reset_stats` - 测试重置统计
- `test_hit_updates_last_accessed` - 测试更新最后访问时间
- `test_cached_llm_call_decorator_async` - 测试异步装饰器
- `test_cached_llm_call_decorator_sync` - 测试同步装饰器
- `test_cached_llm_call_different_params` - 测试不同参数不使用缓存

---

## ⚙️ Config 模块测试

**文件**: `config/test_common_config.py`
**测试用例**: 17 个
**目标覆盖率**: 90%+

### 测试场景

#### 枚举测试 (2 个)
- `test_environment_values` - 测试环境枚举值
- `test_provider_values` - 测试提供商枚举值

#### AgentConfig 测试 (5 个)
- `test_agent_config_defaults` - 测试默认值
- `test_agent_config_custom_values` - 测试自定义值
- `test_agent_config_validation_temperature` - 测试温度参数验证
- `test_agent_config_validation_max_tokens` - 测试 max_tokens 验证
- `test_agent_config_validation_timeout` - 测试超时参数验证

#### DatabaseConfig 测试 (2 个)
- `test_database_config_defaults` - 测试数据库配置默认值
- `test_database_url_property` - 测试 database_url 属性
- `test_redis_url_property` - 测试 redis_url 属性

#### AppConfig 测试 (6 个)
- `test_app_config_defaults` - 测试应用配置默认值
- `test_cors_origins_list_property` - 测试 CORS origins 属性
- `test_get_agent_config` - 测试获取 Agent 配置
- `test_get_api_key` - 测试获取 API Key
- `test_log_level_validation_valid` - 测试有效日志级别
- `test_log_level_validation_invalid` - 测试无效日志级别

#### 验证测试 (2 个)
- `test_jwt_secret_validation_development` - 测试开发环境 JWT 密钥
- `test_jwt_secret_validation_production_no_key` - 测试生产环境无密钥

---

## 💾 Cache 模块测试

**文件**: `cache/test_agent_cache.py`
**测试用例**: 18 个
**目标覆盖率**: 85%+

### 测试场景

#### CacheEntry 测试 (6 个)
- `test_cache_entry_creation` - 测试缓存条目创建
- `test_is_expired_with_ttl` - 测试带 TTL 的过期检查
- `test_is_expired_without_ttl` - 测试不带 TTL 的过期检查
- `test_touch` - 测试更新访问信息
- `test_to_dict` - 测试转换为字典

#### CacheStats 测试 (5 个)
- `test_cache_stats_defaults` - 测试缓存统计默认值
- `test_total_requests_property` - 测试总请求数属性
- `test_hit_rate_property` - 测试命中率属性
- `test_to_dict` - 测试转换为字典

#### AgentCache 测试 (18 个)
- `test_cache_initialization` - 测试缓存初始化
- `test_cache_set_and_get` - 测试缓存设置和获取
- `test_cache_hit_and_miss` - 测试缓存命中和未命中
- `test_cache_key_generation_dict` - 测试字典键生成
- `test_cache_key_generation_string` - 测试字符串键生成
- `test_cache_expiration` - 测试缓存过期
- `test_cache_invalidate_specific` - 测试失效特定条目
- `test_cache_invalidate_all_for_agent` - 测试失效所有条目
- `test_cache_clear` - 测试清空缓存
- `test_cleanup_expired` - 测试清理过期缓存
- `test_get_stats_global` - 测试全局统计
- `test_get_stats_per_agent` - 测试按 agent 统计
- `test_lru_eviction_by_count` - 测试基于数量的 LRU 淘汰
- `test_default_ttl_by_agent_type` - 测试默认 TTL
- `test_estimate_size` - 测试大小估算
- `test_thread_safety` - 测试线程安全

#### 全局缓存测试 (3 个)
- `test_get_global_cache_singleton` - 测试全局缓存单例
- `test_reset_global_cache` - 测试重置全局缓存

#### 装饰器测试 (2 个)
- `test_cached_decorator` - 测试缓存装饰器

---

## 🔒 Security 模块测试

### 1. JWT Handler 测试

**文件**: `security/test_jwt_handler.py`
**测试用例**: 13 个
**目标覆盖率**: 90%+

#### 测试场景

##### 基础功能 (6 个)
- `test_jwt_handler_initialization` - 测试 JWT 处理器初始化
- `test_create_access_token` - 测试创建访问令牌
- `test_create_access_token_with_claims` - 测试创建带额外声明的令牌
- `test_create_refresh_token` - 测试创建刷新令牌
- `test_decode_token_valid` - 测试解码有效令牌
- `test_decode_token_invalid` - 测试解码无效令牌

##### 验证测试 (3 个)
- `test_verify_token_valid` - 测试验证有效令牌
- `test_verify_token_invalid_type` - 测试验证错误类型令牌
- `test_verify_refresh_token_valid` - 测试验证刷新令牌

##### 其他功能 (4 个)
- `test_token_expiration` - 测试令牌过期
- `test_multiple_tokens_same_user` - 测试为同一用户创建多个令牌
- `test_custom_secret_from_env` - 测试从环境变量获取密钥
- `test_fallback_secret` - 测试回退到默认密钥

---

### 2. Password Handler 测试

**文件**: `security/test_password_handler.py`
**测试用例**: 15 个
**目标覆盖率**: 90%+

#### 测试场景

##### 密码哈希 (5 个)
- `test_password_handler_initialization` - 测试初始化
- `test_hash_password` - 测试密码哈希
- `test_hash_password_different_each_time` - 测试每次哈希不同
- `test_verify_password_correct` - 测试验证正确密码
- `test_verify_password_incorrect` - 测试验证错误密码
- `test_verify_password_empty` - 测试验证空密码

##### 密码强度验证 (9 个)
- `test_validate_password_strength_valid` - 测试有效密码
- `test_validate_password_strength_too_short` - 测试过短密码
- `test_validate_password_strength_no_uppercase` - 测试无大写字母
- `test_validate_password_strength_no_lowercase` - 测试无小写字母
- `test_validate_password_strength_no_digit` - 测试无数字
- `test_validate_and_hash_valid` - 测试验证并加密
- `test_validate_and_hash_invalid` - 测试验证失败
- `test_unicode_password` - 测试 Unicode 密码
- `test_very_long_password` - 测试超长密码

##### 安全测试 (1 个)
- `test_hash_timing_attack_resistance` - 测试时序攻击抵抗

---

## 🌉 Middleware 模块测试

### 测试文件 (3 个)

#### 1. Auth Middleware (`test_auth_middleware.py` - 8 个测试)
- `test_no_credentials` - 测试无认证凭证
- `test_valid_token` - 测试有效令牌
- `test_invalid_token` - 测试无效令牌
- `test_no_credentials_raises_exception` - 测试无凭证抛异常
- `test_require_auth_init` - 测试认证初始化
- `test_require_auth_init_optional` - 测试可选认证初始化

#### 2. Error Handler (`test_error_handler.py` - 9 个测试)
- `test_api_exception_handler` - 测试 API 异常处理
- `test_api_exception_handler_debug_mode` - 测试调试模式异常处理
- `test_http_exception_handler` - 测试 HTTP 异常处理
- `test_validation_exception_handler` - 测试验证异常处理
- `test_general_exception_handler` - 测试通用异常处理
- `test_setup_exception_handlers` - 测试设置异常处理器
- `test_exception_chaining` - 测试异常链

#### 3. Rate Limit (`test_rate_limit.py` - 10 个测试)
- `test_rate_limiter_initialization` - 测试限流器初始化
- `test_check_rate_limit_disabled` - 测试禁用限流
- `test_check_rate_limit_under_threshold` - 测试低于阈值
- `test_check_rate_limit_exceeds_threshold` - 测试超过阈值
- `test_check_rate_limit_redis_error` - 测试 Redis 错误处理
- `test_check_rate_limit_sliding_window` - 测试滑动窗口算法
- `test_rate_limit_check_with_user_id` - 测试用户 ID 限流
- `test_rate_limit_check_with_ip` - 测试 IP 限流
- `test_strict_rate_limit_check` - 测试严格限流
- `test_loose_rate_limit_check` - 测试宽松限流

---

## 📍 Checkpoint 模块测试

**文件**: `checkpoint/test_checkpoint_manager.py`
**测试用例**: 11 个
**目标覆盖率**: 75%+

### 测试场景

- `test_checkpoint_manager_initialization` - 测试初始化
- `test_save_checkpoint` - 测试保存检查点
- `test_save_checkpoint_failure` - 测试保存失败
- `test_load_checkpoint` - 测试加载检查点
- `test_load_checkpoint_not_found` - 测试加载不存在的检查点
- `test_update_framework` - 测试更新框架
- `test_delete_checkpoint` - 测试删除检查点
- `test_get_user_checkpoints` - 测试获取用户检查点列表
- `test_mark_completed` - 测试标记完成
- `test_cleanup_expired` - 测试清理过期检查点
- `test_get_checkpoint_manager_none` - 测试全局管理器

---

## 📨 Events 模块测试

**文件**: `events/test_event_store.py`
**测试用例**: 16 个
**目标覆盖率**: 75%+

### 测试场景

#### Event 测试 (3 个)
- `test_event_creation` - 测试事件创建
- `test_event_to_dict` - 测试转换为字典
- `test_event_from_dict` - 测试从字典创建

#### InMemoryEventStore 测试 (6 个)
- `test_append_event` - 测试添加事件
- `test_append_event_version_mismatch` - 测试版本不匹配
- `test_get_events` - 测试获取事件
- `test_get_events_with_version_range` - 测试按版本范围获取
- `test_get_event` - 测试获取单个事件
- `test_clear` - 测试清空事件存储

#### EventSourcedState 测试 (7 个)
- `test_initialization` - 测试初始化
- `test_raise_event` - 测试触发事件
- `test_commit` - 测试提交事件
- `test_rollback` - 测试回滚事件
- `test_replay` - 测试重放事件
- `test_register_handler` - 测试注册事件处理器
- `test_snapshot` - 测试快照

---

## 📦 其他模块测试

### DI Container (`di/test_container.py` - 6 个测试)
- `test_container_initialization` - 测试容器初始化
- `test_container_configuration` - 测试容器配置
- `test_container_providers` - 测试提供者
- `test_create_container` - 测试创建容器
- `test_get_global_container_singleton` - 测试全局容器单例
- `test_reset_global_container` - 测试重置全局容器

### MCP Loader (`mcp/test_mcp_loader.py` - 10 个测试)
- `test_load_valid_config` - 测试加载有效配置
- `test_load_config_file_not_found` - 测试文件不存在
- `test_load_config_invalid_json` - 测试无效 JSON
- `test_load_mcp_tools_from_file` - 测试从文件加载
- `test_load_mcp_tools_file_not_exists` - 测试文件不存在
- `test_load_mcp_tools_from_config` - 测试从配置加载
- `test_load_mcp_tools_invalid_config` - 测试无效配置
- `test_mcp_manager_initialization` - 测试管理器初始化
- `test_mcp_manager_methods` - 测试管理器方法

### Logger Config (`logging/test_logger_config.py` - 11 个测试)
- `test_filter_api_key` - 测试过滤 API Key
- `test_filter_jwt` - 测试过滤 JWT
- `test_filter_password` - 测试过滤密码
- `test_json_formatter` - 测试 JSON 格式化
- `test_text_formatter` - 测试文本格式化
- `test_setup_logger_basic` - 测试基本日志器
- `test_setup_logger_json` - 测试 JSON 日志器
- `test_setup_logger_file_output` - 测试文件输出
- `test_logger_context` - 测试日志器上下文

### Health Checker (`health/test_health_checker.py` - 12 个测试)
- `test_register_checker` - 测试注册检查器
- `test_check_component` - 测试检查组件
- `test_check_component_unknown` - 测试检查未知组件
- `test_check_component_exception` - 测试检查异常
- `test_check_health` - 测试检查整体健康
- `test_check_health_unhealthy` - 测试不健康状态
- `test_get_last_result` - 测试获取上次结果

### Metrics Collector (`metrics/test_metrics_collector.py` - 13 个测试)
- `test_counter_initialization` - 测试计数器初始化
- `test_counter_inc` - 测试增加计数
- `test_counter_with_labels` - 测试带标签计数
- `test_gauge_set` - 测试设置仪表
- `test_gauge_inc` - 测试增加仪表值
- `test_histogram_observe` - 测试观察值
- `test_histogram_export` - 测试导出直方图
- `test_metrics_collector_initialization` - 测试收集器初始化
- `test_export_metrics` - 测试导出指标
- `test_measure_time_decorator` - 测试测量时间装饰器

---

## 🔗 集成测试

**文件**: `integration/test_infrastructure_integration.py`
**测试用例**: 8 个

### 测试场景

#### 跨模块集成 (4 个)
- `test_database_to_cache_integration` - 测试数据库-缓存集成
- `test_config_to_database_integration` - 测试配置-数据库集成
- `test_factory_to_config_integration` - 测试工厂-配置集成
- `test_full_stack_flow` - 测试完整流程

#### 错误处理集成 (2 个)
- `test_database_failure_handling` - 测试数据库失败处理
- `test_cache_failure_handling` - 测试缓存失败处理

#### 性能集成 (2 个)
- `test_cache_performance` - 测试缓存性能
- `test_concurrent_cache_access` - 测试并发访问

---

## 📊 测试覆盖的功能点

### 数据库功能
- ✅ 连接管理
- ✅ 会话管理
- ✅ 事务处理（提交/回滚）
- ✅ 健康检查
- ✅ 连接池统计
- ✅ 错误处理

### LLM 功能
- ✅ 多提供商支持
- ✅ 模型创建和缓存
- ✅ 自动降级机制
- ✅ 重试机制（指数退避）
- ✅ 熔断器模式
- ✅ 请求缓存

### 缓存功能
- ✅ TTL 过期
- ✅ LRU 淘汰
- ✅ 命中/未命中统计
- ✅ 线程安全
- ✅ 大小限制

### 安全功能
- ✅ JWT 生成/验证
- ✅ Token 过期处理
- ✅ 密码加密（bcrypt）
- ✅ 密码强度验证
- ✅ 敏感信息过滤

### 中间件功能
- ✅ 认证/授权
- ✅ 全局异常处理
- ✅ 请求验证
- ✅ 限流保护

---

**文档版本**: 1.0
**最后更新**: 2025-02-04
