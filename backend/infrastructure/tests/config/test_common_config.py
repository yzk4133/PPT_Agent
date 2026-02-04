"""
Common Config 测试
"""

import pytest
import os
from pydantic import ValidationError
from infrastructure.config.common_config import (
    Environment,
    ModelProvider,
    AgentConfig,
    DatabaseConfig,
    FeatureFlags,
    AppConfig,
    get_config,
    update_config,
    _config_instance,
)

@pytest.mark.unit
class TestEnvironment:
    """测试 Environment 枚举"""

    def test_environment_values(self):
        """测试环境枚举值"""
        assert Environment.DEVELOPMENT == "development"
        assert Environment.STAGING == "staging"
        assert Environment.PRODUCTION == "production"

@pytest.mark.unit
class TestModelProvider:
    """测试 ModelProvider 枚举"""

    def test_provider_values(self):
        """测试提供商枚举值"""
        assert ModelProvider.DEEPSEEK == "deepseek"
        assert ModelProvider.OPENAI == "openai"
        assert ModelProvider.CLAUDE == "claude"
        assert ModelProvider.GOOGLE == "google"
        assert ModelProvider.QWEN == "qwen"

@pytest.mark.unit
class TestAgentConfig:
    """测试 AgentConfig 配置"""

    def test_agent_config_defaults(self):
        """测试 AgentConfig 默认值"""
        config = AgentConfig()

        assert config.provider == ModelProvider.DEEPSEEK
        assert config.model == "deepseek-chat"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.timeout == 60
        assert config.max_retries == 3
        assert config.max_concurrency == 3
        assert config.enable_fallback is True
        assert config.fallback_model is None

    def test_agent_config_custom_values(self):
        """测试 AgentConfig 自定义值"""
        config = AgentConfig(
            provider=ModelProvider.OPENAI,
            model="gpt-4",
            temperature=0.5,
            max_tokens=2048,
            timeout=120,
            max_retries=5,
            max_concurrency=5,
            enable_fallback=False,
            fallback_model="gpt-3.5-turbo",
        )

        assert config.provider == ModelProvider.OPENAI
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048
        assert config.timeout == 120
        assert config.max_retries == 5
        assert config.max_concurrency == 5
        assert config.enable_fallback is False
        assert config.fallback_model == "gpt-3.5-turbo"

    def test_agent_config_validation_temperature(self):
        """测试温度参数验证"""
        # 温度超出范围（太高）
        with pytest.raises(ValidationError):
            AgentConfig(temperature=3.0)

        # 温度超出范围（太低）
        with pytest.raises(ValidationError):
            AgentConfig(temperature=-0.1)

    def test_agent_config_validation_max_tokens(self):
        """测试 max_tokens 验证"""
        # max_tokens 太小
        with pytest.raises(ValidationError):
            AgentConfig(max_tokens=0)

        # max_tokens 太大
        with pytest.raises(ValidationError):
            AgentConfig(max_tokens=200000)

    def test_agent_config_validation_timeout(self):
        """测试超时参数验证"""
        # timeout 太小
        with pytest.raises(ValidationError):
            AgentConfig(timeout=5)

        # timeout 太大
        with pytest.raises(ValidationError):
            AgentConfig(timeout=1000)

@pytest.mark.unit
class TestDatabaseConfig:
    """测试 DatabaseConfig 配置"""

    def test_database_config_defaults(self):
        """测试 DatabaseConfig 默认值"""
        config = DatabaseConfig()

        assert config.postgres_host == "localhost"
        assert config.postgres_port == 5432
        assert config.postgres_db == "multiagent_ppt"
        assert config.postgres_user == "postgres"
        assert config.postgres_password == "password"

        assert config.redis_host == "localhost"
        assert config.redis_port == 6379
        assert config.redis_db == 0
        assert config.redis_password is None

        assert config.pool_size == 50
        assert config.max_overflow == 20

    def test_database_url_property(self):
        """测试 database_url 属性"""
        config = DatabaseConfig(
            postgres_user="testuser",
            postgres_password="testpass",
            postgres_host="testhost",
            postgres_port=5433,
            postgres_db="testdb",
        )

        expected_url = "postgresql://testuser:testpass@testhost:5433/testdb"
        assert config.database_url == expected_url

    def test_redis_url_property(self):
        """测试 redis_url 属性"""
        # 无密码
        config = DatabaseConfig(
            redis_host="localhost",
            redis_port=6379,
            redis_db=1,
            redis_password=None,
        )

        expected_url = "redis://localhost:6379/1"
        assert config.redis_url == expected_url

        # 有密码
        config = DatabaseConfig(
            redis_host="localhost",
            redis_port=6379,
            redis_db=1,
            redis_password="mypass",
        )

        expected_url = "redis://:mypass@localhost:6379/1"
        assert config.redis_url == expected_url

@pytest.mark.unit
class TestFeatureFlags:
    """测试 FeatureFlags 配置"""

    def test_feature_flags_defaults(self):
        """测试 FeatureFlags 默认值"""
        flags = FeatureFlags()

        assert flags.use_flat_architecture is True
        assert flags.use_persistent_memory is True
        assert flags.enable_vector_cache is True
        assert flags.enable_user_preferences is True
        assert flags.enable_quality_check is True
        assert flags.enable_tool_hot_reload is False
        assert flags.enable_mcp_tools is True
        assert flags.enable_auto_fallback is True

@pytest.mark.unit
class TestAppConfig:
    """测试 AppConfig 配置"""

    def test_app_config_defaults(self):
        """测试 AppConfig 默认值"""
        config = AppConfig()

        assert config.environment == Environment.DEVELOPMENT
        assert config.debug is False
        assert config.log_level == "INFO"

        assert config.jwt_algorithm == "HS256"
        assert config.access_token_expire_minutes == 30
        assert config.refresh_token_expire_days == 30

        assert config.rate_limit_enabled is True
        assert config.rate_limit_per_minute == 100

        assert config.database is not None
        assert config.features is not None

        # Agent configs
        assert config.split_topic_agent is not None
        assert config.research_agent is not None
        assert config.ppt_writer_agent is not None
        assert config.ppt_checker_agent is not None
        assert config.outline_agent is not None

    def test_cors_origins_list_property(self):
        """测试 CORS origins 列表属性"""
        config = AppConfig(
            cors_allowed_origins="http://localhost:3000, http://localhost:5173, https://example.com"
        )

        origins = config.cors_origins_list

        assert len(origins) == 3
        assert "http://localhost:3000" in origins
        assert "http://localhost:5173" in origins
        assert "https://example.com" in origins

    def test_get_agent_config(self):
        """测试获取 Agent 配置"""
        config = AppConfig()

        split_config = config.get_agent_config("split_topic")
        assert split_config.provider == ModelProvider.DEEPSEEK
        assert split_config.model == "deepseek-chat"

        research_config = config.get_agent_config("research")
        assert research_config.max_concurrency == 3

        # 未知的 agent 应该返回默认配置
        unknown_config = config.get_agent_config("unknown_agent")
        assert unknown_config.provider == ModelProvider.DEEPSEEK

    def test_get_api_key(self):
        """测试获取 API Key"""
        config = AppConfig(
            openai_api_key="sk-test-openai",
            deepseek_api_key="sk-test-deepseek",
        )

        assert config.get_api_key(ModelProvider.OPENAI) == "sk-test-openai"
        assert config.get_api_key(ModelProvider.DEEPSEEK) == "sk-test-deepseek"
        assert config.get_api_key(ModelProvider.CLAUDE) is None

    def test_log_level_validation_valid(self):
        """测试有效日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            config = AppConfig(log_level=level)
            assert config.log_level == level

    def test_log_level_validation_invalid(self):
        """测试无效日志级别"""
        with pytest.raises(ValidationError, match="Invalid log level"):
            AppConfig(log_level="INVALID")

    def test_jwt_secret_validation_development(self):
        """测试开发环境 JWT 密钥验证"""
        # 开发环境没有密钥应该自动生成（警告）
        config = AppConfig(
            environment=Environment.DEVELOPMENT,
            jwt_secret_key="",
        )

        # 应该自动生成密钥
        assert len(config.jwt_secret_key) > 0

    def test_jwt_secret_validation_production_no_key(self):
        """测试生产环境没有 JWT 密钥"""
        with pytest.raises(ValidationError, match="JWT_SECRET_KEY must be set in production"):
            AppConfig(
                environment=Environment.PRODUCTION,
                jwt_secret_key="",
            )

    def test_jwt_secret_validation_production_too_short(self):
        """测试生产环境 JWT 密钥太短"""
        with pytest.raises(ValidationError, match="JWT_SECRET_KEY too short"):
            AppConfig(
                environment=Environment.PRODUCTION,
                jwt_secret_key="short",
            )

    def test_jwt_secret_validation_production_insecure(self):
        """测试生产环境使用不安全的 JWT 密钥"""
        with pytest.raises(ValidationError, match="using a default/insecure value"):
            AppConfig(
                environment=Environment.PRODUCTION,
                jwt_secret_key="your-secret-key-change-in-production",
            )

    def test_api_key_validation_placeholder(self):
        """测试 API Key 占位符验证"""
        # 占位符应该被设置为 None（带警告）
        config = AppConfig(
            deepseek_api_key="your_api_key_here"
        )

        # 占位符应该被清空
        assert config.deepseek_api_key is None

    def test_api_key_validation_empty_string(self):
        """测试空字符串 API Key"""
        config = AppConfig(
            deepseek_api_key="   "
        )

        # 空字符串应该被设置为 None
        assert config.deepseek_api_key is None

@pytest.mark.unit
class TestConfigSingleton:
    """测试配置单例"""

    def test_get_config_singleton(self):
        """测试配置单例模式"""
        import infrastructure.config.common_config as config_module

        # 重置全局变量
        config_module._config_instance = None

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_get_config_reload(self):
        """测试重新加载配置"""
        import infrastructure.config.common_config as config_module

        # 重置全局变量
        config_module._config_instance = None

        config1 = get_config()
        config2 = get_config(reload=True)

        # 重新加载应该创建新实例
        assert config1 is not config2

@pytest.mark.unit
class TestUpdateConfig:
    """测试更新配置"""

    def test_update_config_valid(self):
        """测试更新有效配置"""
        import infrastructure.config.common_config as config_module

        # 重置全局变量
        config_module._config_instance = None

        config = get_config()
        original_debug = config.debug

        # 更新配置
        updated_config = update_config(debug=True)

        assert updated_config.debug is True
        assert updated_config is config  # 应该返回同一个实例

        # 恢复原始值
        config.debug = original_debug

    def test_update_config_invalid_field(self):
        """测试更新无效字段"""
        import infrastructure.config.common_config as config_module

        # 重置全局变量
        config_module._config_instance = None

        config = get_config()

        # 更新不存在的字段应该静默失败
        updated_config = update_config(nonexistent_field="value")

        # 不应该抛出异常
        assert updated_config is config

@pytest.mark.unit
class TestConfigEnvLoading:
    """测试环境变量加载"""

    def test_load_from_env(self):
        """测试从环境变量加载配置"""
        # 设置环境变量
        os.environ["ENVIRONMENT"] = "production"
        os.environ["DEBUG"] = "true"
        os.environ["LOG_LEVEL"] = "ERROR"

        try:
            config = AppConfig()

            assert config.environment == Environment.PRODUCTION
            assert config.debug is True
            assert config.log_level == "ERROR"
        finally:
            # 清理环境变量
            os.environ.pop("ENVIRONMENT", None)
            os.environ.pop("DEBUG", None)
            os.environ.pop("LOG_LEVEL", None)

    def test_database_config_from_env(self):
        """测试数据库配置从环境变量加载"""
        os.environ["DB_POSTGRES_HOST"] = "remotehost"
        os.environ["DB_POSTGRES_PORT"] = "5433"
        os.environ["DB_REDIS_HOST"] = "redishost"

        try:
            config = DatabaseConfig()

            assert config.postgres_host == "remotehost"
            assert config.postgres_port == 5433
            assert config.redis_host == "redishost"
        finally:
            # 清理环境变量
            os.environ.pop("DB_POSTGRES_HOST", None)
            os.environ.pop("DB_POSTGRES_PORT", None)
            os.environ.pop("DB_REDIS_HOST", None)
