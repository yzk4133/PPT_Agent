"""
统一配置管理系统

使用 Pydantic Settings 实现类型安全的配置管理，支持：
- 环境变量覆盖
- 多环境配置（dev/staging/prod）
- 配置验证
- 向后兼容的 Feature Flag
"""

import os
from enum import Enum
from typing import Dict, List, Optional, Any

# Pydantic v2 compatibility
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, field_validator as validator
except ImportError:
    from pydantic import BaseSettings, Field, validator



class Environment(str, Enum):
    """环境类型"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ModelProvider(str, Enum):
    """支持的模型提供商"""

    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    CLAUDE = "claude"
    GOOGLE = "google"
    QWEN = "qwen"


class AgentConfig(BaseSettings):
    """单个 Agent 的配置"""

    # 模型配置
    provider: ModelProvider = Field(ModelProvider.DEEPSEEK, description="模型提供商")
    model: str = Field("deepseek-chat", description="模型名称")
    fallback_model: Optional[str] = Field(None, description="降级备用模型")

    # 调用配置
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(4096, ge=1, le=128000, description="最大token数")
    timeout: int = Field(60, ge=10, le=600, description="超时时间（秒）")
    max_retries: int = Field(3, ge=0, le=10, description="最大重试次数")

    # 并发配置
    max_concurrency: int = Field(3, ge=1, le=20, description="最大并发数")

    # 降级配置
    enable_fallback: bool = Field(True, description="是否启用降级策略")
    fallback_threshold: float = Field(
        0.5, ge=0.0, le=1.0, description="降级阈值（失败率）"
    )

    class Config:
        env_prefix = ""  # 不使用前缀，由父类处理
        case_sensitive = False


class DatabaseConfig(BaseSettings):
    """数据库配置"""

    # PostgreSQL
    postgres_host: str = Field("localhost", description="PostgreSQL 主机")
    postgres_port: int = Field(5432, description="PostgreSQL 端口")
    postgres_db: str = Field("multiagent_ppt", description="数据库名")
    postgres_user: str = Field("postgres", description="用户名")
    postgres_password: str = Field("password", description="密码")

    # Redis
    redis_host: str = Field("localhost", description="Redis 主机")
    redis_port: int = Field(6379, description="Redis 端口")
    redis_db: int = Field(0, description="Redis 数据库")
    redis_password: Optional[str] = Field(None, description="Redis 密码")

    # 连接池配置
    pool_size: int = Field(50, ge=5, le=200, description="连接池大小")
    max_overflow: int = Field(20, ge=0, le=100, description="连接池溢出")

    @property
    def database_url(self) -> str:
        """生成 PostgreSQL 连接 URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def redis_url(self) -> str:
        """生成 Redis 连接 URL"""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_prefix = "DB_"
        case_sensitive = False


class FeatureFlags(BaseSettings):
    """Feature Flag 配置，用于灰度发布和向后兼容"""

    # 架构相关
    use_flat_architecture: bool = Field(True, description="使用扁平化架构（新架构）")
    use_persistent_memory: bool = Field(True, description="使用持久化记忆系统")

    # 功能相关
    enable_vector_cache: bool = Field(True, description="启用向量缓存")
    enable_user_preferences: bool = Field(True, description="启用用户偏好学习")
    enable_quality_check: bool = Field(True, description="启用 PPT 质量检查")

    # 工具相关
    enable_tool_hot_reload: bool = Field(False, description="启用工具热加载（实验性）")
    enable_mcp_tools: bool = Field(True, description="启用 MCP 工具")

    # 降级相关
    enable_auto_fallback: bool = Field(True, description="启用自动降级")

    class Config:
        env_prefix = "FEATURE_"
        case_sensitive = False


class AppConfig(BaseSettings):
    """应用全局配置"""

    # 环境配置
    environment: Environment = Field(Environment.DEVELOPMENT, description="运行环境")
    debug: bool = Field(False, description="调试模式")
    log_level: str = Field("INFO", description="日志级别")

    # 认证配置
    jwt_secret_key: str = Field("your-secret-key-change-in-production", description="JWT 密钥")
    jwt_algorithm: str = Field("HS256", description="JWT 算法")
    access_token_expire_minutes: int = Field(30, description="访问令牌过期时间（分钟）")
    refresh_token_expire_days: int = Field(30, description="刷新令牌过期时间（天）")

    # CORS 配置
    cors_allowed_origins: list = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="允许的 CORS 来源"
    )

    # 限流配置
    rate_limit_enabled: bool = Field(True, description="是否启用限流")
    rate_limit_per_minute: int = Field(100, description="每分钟请求限制")

    # API 密钥
    openai_api_key: Optional[str] = Field(None, description="OpenAI API Key")
    deepseek_api_key: Optional[str] = Field(None, description="DeepSeek API Key")
    claude_api_key: Optional[str] = Field(None, description="Claude API Key")
    google_api_key: Optional[str] = Field(None, description="Google API Key")
    qwen_api_key: Optional[str] = Field(None, description="Qwen API Key")

    # 数据库配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    # Feature Flags
    features: FeatureFlags = Field(default_factory=FeatureFlags)

    # Agent 配置（各个 Agent 可单独配置）
    split_topic_agent: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            provider=ModelProvider.DEEPSEEK,
            model="deepseek-chat",
            temperature=0.3,  # 拆分主题需要低温度，保持一致性
            max_tokens=2048,
        )
    )

    research_agent: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            provider=ModelProvider.DEEPSEEK,
            model="deepseek-chat",
            temperature=0.7,
            max_tokens=8192,
            max_concurrency=3,
        )
    )

    ppt_writer_agent: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            provider=ModelProvider.DEEPSEEK,
            model="deepseek-chat",
            temperature=0.5,
            max_tokens=4096,
        )
    )

    ppt_checker_agent: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            provider=ModelProvider.DEEPSEEK,
            model="deepseek-chat",
            temperature=0.2,  # 检查需要低温度，保持严格
            max_tokens=2048,
        )
    )

    outline_agent: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            provider=ModelProvider.DEEPSEEK,
            model="deepseek-chat",
            temperature=0.7,
            max_tokens=8192,
        )
    )

    @validator("log_level")
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    # Disable API key validation for Pydantic v2 compatibility
    # @validator(
    #     "openai_api_key",
    #     "deepseek_api_key",
    #     "claude_api_key",
    #     "google_api_key",
    #     "qwen_api_key",
    # )
    # def validate_api_keys(cls, v, values):
    #     """在生产环境验证 API Key"""
    #     env = values.get("environment", Environment.DEVELOPMENT)
    #     if env == Environment.PRODUCTION and not v:
    #         # 生产环境可以允许部分 Key 为空，只要有至少一个可用
    #         pass
    #     return v

    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """根据 Agent 名称获取配置"""
        agent_config_map = {
            "split_topic": self.split_topic_agent,
            "research": self.research_agent,
            "ppt_writer": self.ppt_writer_agent,
            "ppt_checker": self.ppt_checker_agent,
            "outline": self.outline_agent,
        }
        return agent_config_map.get(agent_name, AgentConfig())

    def get_api_key(self, provider: ModelProvider) -> Optional[str]:
        """根据提供商获取 API Key"""
        key_map = {
            ModelProvider.OPENAI: self.openai_api_key,
            ModelProvider.DEEPSEEK: self.deepseek_api_key,
            ModelProvider.CLAUDE: self.claude_api_key,
            ModelProvider.GOOGLE: self.google_api_key,
            ModelProvider.QWEN: self.qwen_api_key,
        }
        return key_map.get(provider)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Note: fields config is not supported in Pydantic v2, use env_prefix per field instead


# 全局配置实例（单例模式）
_config_instance: Optional[AppConfig] = None


def get_config(reload: bool = False) -> AppConfig:
    """
    获取全局配置实例（单例）

    Args:
        reload: 是否重新加载配置（用于热更新）

    Returns:
        AppConfig 实例
    """
    global _config_instance
    if _config_instance is None or reload:
        _config_instance = AppConfig()
    return _config_instance


def update_config(**kwargs) -> AppConfig:
    """
    更新配置（运行时修改）

    Args:
        **kwargs: 要更新的配置项

    Returns:
        更新后的配置实例
    """
    config = get_config()
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config


if __name__ == "__main__":
    # 测试配置加载
    config = get_config()
    print(f"Environment: {config.environment}")
    print(f"Database URL: {config.database.database_url}")
    print(f"Redis URL: {config.database.redis_url}")
    print(f"Use Flat Architecture: {config.features.use_flat_architecture}")
    print(f"Split Topic Agent Model: {config.split_topic_agent.model}")
    print(f"Research Agent Concurrency: {config.research_agent.max_concurrency}")
