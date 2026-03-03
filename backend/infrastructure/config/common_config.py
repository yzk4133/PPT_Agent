"""
统一配置管理系统

使用 Pydantic Settings 实现类型安全的配置管理，支持：
- 环境变量覆盖
- 多环境配置（dev/staging/prod）
- 配置验证
- 向后兼容的 Feature Flag
"""

import os
import secrets
import logging
from enum import Enum
from typing import Dict, List, Optional, Any

# Pydantic v2 compatibility
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, field_validator as validator
except ImportError:
    from pydantic import BaseSettings, Field, validator

logger = logging.getLogger(__name__)

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
        extra = "ignore"  # 忽略额外的环境变量

class DatabaseConfig(BaseSettings):
    """数据库配置"""

    # MySQL
    mysql_host: str = Field("localhost", description="MySQL 主机")
    mysql_port: int = Field(3306, description="MySQL 端口")
    mysql_db: str = Field("multiagent_ppt", description="数据库名")
    mysql_user: str = Field("root", description="用户名")
    mysql_password: str = Field("postgres", description="密码")

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
        """生成 MySQL 连接 URL"""
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"

    @property
    def redis_url(self) -> str:
        """生成 Redis 连接 URL"""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_prefix = "DB_"
        case_sensitive = False
        extra = "ignore"  # 忽略额外的环境变量

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
        extra = "ignore"  # 忽略额外的环境变量

class AppConfig(BaseSettings):
    """应用全局配置"""

    # 环境配置
    environment: Environment = Field(Environment.DEVELOPMENT, description="运行环境")
    debug: bool = Field(False, description="调试模式")
    log_level: str = Field("INFO", description="日志级别")

    # 认证配置
    jwt_secret_key: str = Field(
        default="",
        description="JWT 密钥（生产环境必须从环境变量设置）"
    )
    jwt_algorithm: str = Field("HS256", description="JWT 算法")
    access_token_expire_minutes: int = Field(30, description="访问令牌过期时间（分钟）")
    refresh_token_expire_days: int = Field(30, description="刷新令牌过期时间（天）")

    # CORS 配置
    cors_allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="允许的 CORS 来源（逗号分隔）"
    )

    @property
    def cors_origins_list(self) -> list:
        """将逗号分隔的 CORS 来源转换为列表"""
        if isinstance(self.cors_allowed_origins, str):
            return [origin.strip() for origin in self.cors_allowed_origins.split(",")]
        return self.cors_allowed_origins

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

    @validator("jwt_secret_key")
    def validate_jwt_secret(cls, v, info):
        """验证JWT密钥"""
        environment = info.data.get("environment", Environment.DEVELOPMENT)

        # 开发环境：如果未设置，生成一个临时密钥并警告
        if environment == Environment.DEVELOPMENT and not v:
            logger.warning(
                "JWT_SECRET_KEY not set in development mode. "
                "Using auto-generated temporary key. Set JWT_SECRET_KEY environment variable for persistence."
            )
            return secrets.token_urlsafe(32)

        # 生产环境：必须设置强密钥
        if environment == Environment.PRODUCTION:
            if not v:
                raise ValueError(
                    "JWT_SECRET_KEY must be set in production environment. "
                    "Set JWT_SECRET_KEY environment variable to a secure random string (at least 32 characters)."
                )
            if len(v) < 32:
                raise ValueError(
                    f"JWT_SECRET_KEY too short (got {len(v)} chars). "
                    "Must be at least 32 characters for security."
                )
            if v in ["your-secret-key-change-in-production", "secret", "password"]:
                raise ValueError(
                    "JWT_SECRET_KEY is using a default/insecure value. "
                    "Set JWT_SECRET_KEY environment variable to a secure random string."
                )

        return v

    @validator("openai_api_key", "deepseek_api_key", "claude_api_key", "google_api_key", "qwen_api_key")
    def validate_api_keys(cls, v, info):
        """验证 API Key 格式"""
        if v is None:
            return v

        # 检查是否为空字符串
        if isinstance(v, str) and not v.strip():
            return None

        # 基本格式验证（大多数API key都是字母数字和下划线）
        if not isinstance(v, str):
            raise ValueError("API key must be a string")

        # 检查是否使用了占位符值
        placeholder_values = [
            "your_api_key_here",
            "your-openai-api-key-here",
            "your_deepseek_api_key_here",
            "your_bing_search_api_key_here",
            "your_unsplash_access_key_here",
        ]
        if v.lower() in placeholder_values:
            logger.warning(f"API key is using placeholder value '{v}'. Please set a valid API key.")
            return None

        return v

    @validator("environment", mode="after")
    def validate_production_config(cls, v, info):
        """验证生产环境配置"""
        if v == Environment.PRODUCTION:
            # 检查是否有至少一个 API key
            api_keys = [
                info.data.get("openai_api_key"),
                info.data.get("deepseek_api_key"),
                info.data.get("claude_api_key"),
                info.data.get("google_api_key"),
                info.data.get("qwen_api_key"),
            ]
            if not any(api_keys):
                logger.warning(
                    "Production environment configured but no API keys are set. "
                    "At least one LLM provider API key is required."
                )
        return v

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
        extra = "ignore"  # 忽略额外的环境变量（如 USE_PERSISTENT_MEMORY, SQL_ECHO 等）
        # Note: fields config is not supported in Pydantic v2, use env_prefix per field instead

class LLMConfig(BaseSettings):
    """
    LLM配置（统一管理）

    消除项目中分散的 os.getenv() 调用，提供单一配置入口。
    """

    # API配置
    api_key: str = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or "",
        description="LLM API密钥"
    )
    base_url: str = Field(
        default_factory=lambda: os.getenv("OPENAI_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL") or "",
        description="LLM Base URL"
    )
    model: str = Field(
        default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"),
        description="LLM模型名称"
    )

    # 可选配置
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(4096, ge=1, le=128000, description="最大token数")
    timeout: int = Field(60, ge=10, le=600, description="超时时间（秒）")

    def to_langchain_config(self) -> Dict[str, Any]:
        """
        转换为LangChain ChatOpenAI所需的配置格式

        Returns:
            LangChain配置字典
        """
        return {
            "model": self.model,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
        }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# 全局配置实例（单例模式）
_config_instance: Optional[AppConfig] = None
_llm_config_instance: Optional[LLMConfig] = None

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


def get_llm_config(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
) -> LLMConfig:
    """
    获取LLM配置实例（单例）

    自动从环境变量读取配置，支持运行时覆盖。

    Args:
        temperature: 温度参数（可选，覆盖默认值）
        max_tokens: 最大token数（可选，覆盖默认值）
        model: 模型名称（可选，覆盖默认值）

    Returns:
        LLMConfig实例

    Examples:
        >>> # 使用默认配置
        >>> config = get_llm_config()
        >>> model = ChatOpenAI(**config.to_langchain_config())
        >>>
        >>> # 运行时覆盖
        >>> config = get_llm_config(temperature=0.5, model="gpt-4")
        >>> model = ChatOpenAI(**config.to_langchain_config())
    """
    global _llm_config_instance

    if _llm_config_instance is None or any([temperature is not None, max_tokens is not None, model is not None]):
        # 创建新的配置实例
        _llm_config_instance = LLMConfig()

        # 应用运行时覆盖
        if temperature is not None:
            _llm_config_instance.temperature = temperature
        if max_tokens is not None:
            _llm_config_instance.max_tokens = max_tokens
        if model is not None:
            _llm_config_instance.model = model

    return _llm_config_instance


def reset_llm_config():
    """重置LLM配置（主要用于测试）"""
    global _llm_config_instance
    _llm_config_instance = None


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 测试配置加载
    config = get_config()
    logger.info(f"Environment: {config.environment}")
    logger.info(f"Database URL: {config.database.database_url}")
    logger.info(f"Redis URL: {config.database.redis_url}")
    logger.info(f"Use Flat Architecture: {config.features.use_flat_architecture}")
    logger.info(f"Split Topic Agent Model: {config.split_topic_agent.model}")
    logger.info(f"Research Agent Concurrency: {config.research_agent.max_concurrency}")
    logger.info(f"CORS Origins: {config.cors_origins_list}")
