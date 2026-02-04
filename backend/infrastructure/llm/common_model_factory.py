"""
模型工厂 - 带降级功能的模型创建

提供统一的模型创建接口，支持：
- 多模型提供商（DeepSeek/OpenAI/Claude/Google/Qwen）
- 自动降级（主模型失败 → 备用模型）
- 模型健康检查
- 缓存结果复用
"""

import os
import logging
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from google.genai.types import (
    GenerateContentConfig,
    GoogleSearch,
    SafetySetting,
    HarmCategory,
)

from ..config.common_config import get_config, ModelProvider, AgentConfig

logger = logging.getLogger(__name__)

class ModelType(str, Enum):
    """模型类型"""

    CHAT = "chat"  # 对话模型
    EMBEDDING = "embedding"  # 嵌入模型
    IMAGE = "image"  # 图像模型

@dataclass
class ModelFallbackResult:
    """模型创建结果（包含降级信息）"""

    model: Any  # 创建的模型对象
    provider: ModelProvider  # 实际使用的提供商
    model_name: str  # 实际使用的模型名称
    is_fallback: bool  # 是否使用了降级
    fallback_reason: Optional[str] = None  # 降级原因

class ModelFactory:
    """模型工厂类"""

    def __init__(self):
        self.config = get_config()
        self._model_cache: Dict[str, Any] = {}  # 模型缓存
        self._failed_models: set = set()  # 失败的模型（熔断）

    def _get_litellm_model_name(self, provider: ModelProvider, model: str) -> str:
        """
        转换为 LiteLLM 格式的模型名称

        Args:
            provider: 模型提供商
            model: 模型名称

        Returns:
            LiteLLM 格式的模型名称
        """
        provider_prefixes = {
            ModelProvider.DEEPSEEK: "deepseek/",
            ModelProvider.OPENAI: "openai/",
            ModelProvider.CLAUDE: "claude/",
            ModelProvider.GOOGLE: "gemini/",
            ModelProvider.QWEN: "qwen/",
        }

        prefix = provider_prefixes.get(provider, "")

        # 如果模型名已包含前缀，不重复添加
        if model.startswith(tuple(provider_prefixes.values())):
            return model

        return f"{prefix}{model}"

    def _create_google_model(self, model_name: str, agent_config: AgentConfig) -> Any:
        """
        创建 Google Gemini 模型

        Args:
            model_name: 模型名称
            agent_config: Agent 配置

        Returns:
            Google 模型实例
        """
        from google import genai
        from google.genai.types import GenerateContentConfig, GoogleSearch

        # 创建 Google AI 客户端
        client = genai.Client(api_key=self.config.get_api_key(ModelProvider.GOOGLE))

        # 配置参数
        config = GenerateContentConfig(
            temperature=agent_config.temperature,
            max_output_tokens=agent_config.max_tokens,
            response_modalities=["TEXT"],
        )

        # 移除 gemini/ 前缀（如果有）
        clean_model_name = model_name.replace("gemini/", "")

        return {
            "client": client,
            "model": clean_model_name,
            "config": config,
            "type": "google",
        }

    def _create_litellm_model(
        self, full_model_name: str, provider: ModelProvider, agent_config: AgentConfig
    ) -> Any:
        """
        创建 LiteLLM 模型（用于其他提供商）

        Args:
            full_model_name: 完整模型名称（包含前缀）
            provider: 提供商
            agent_config: Agent 配置

        Returns:
            模型配置字典
        """
        # 设置 API Key 环境变量
        api_key = self.config.get_api_key(provider)
        if api_key:
            env_key_map = {
                ModelProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
                ModelProvider.OPENAI: "OPENAI_API_KEY",
                ModelProvider.CLAUDE: "ANTHROPIC_API_KEY",
                ModelProvider.QWEN: "QWEN_API_KEY",
            }
            env_key = env_key_map.get(provider)
            if env_key:
                os.environ[env_key] = api_key

        return {
            "model": full_model_name,
            "temperature": agent_config.temperature,
            "max_tokens": agent_config.max_tokens,
            "timeout": agent_config.timeout,
            "type": "litellm",
            "provider": provider.value,
        }

    def create_model(
        self,
        agent_config: AgentConfig,
        model_type: ModelType = ModelType.CHAT,
        enable_cache: bool = True,
    ) -> Any:
        """
        创建模型（不带降级）

        Args:
            agent_config: Agent 配置
            model_type: 模型类型
            enable_cache: 是否启用缓存

        Returns:
            模型实例

        Raises:
            ValueError: 模型创建失败
        """
        cache_key = f"{agent_config.provider}:{agent_config.model}:{model_type}"

        # 检查缓存
        if enable_cache and cache_key in self._model_cache:
            logger.debug(f"Using cached model: {cache_key}")
            return self._model_cache[cache_key]

        # 检查熔断
        if cache_key in self._failed_models:
            raise ValueError(f"Model {cache_key} is in circuit breaker state")

        try:
            full_model_name = self._get_litellm_model_name(
                agent_config.provider, agent_config.model
            )

            # Google 模型特殊处理
            if agent_config.provider == ModelProvider.GOOGLE:
                model = self._create_google_model(full_model_name, agent_config)
            else:
                model = self._create_litellm_model(
                    full_model_name, agent_config.provider, agent_config
                )

            # 缓存模型
            if enable_cache:
                self._model_cache[cache_key] = model

            logger.info(f"Created model: {cache_key}")
            return model

        except Exception as e:
            logger.error(f"Failed to create model {cache_key}: {e}")
            self._failed_models.add(cache_key)
            raise ValueError(f"Model creation failed: {e}")

    def create_model_with_fallback(
        self,
        agent_config: AgentConfig,
        model_type: ModelType = ModelType.CHAT,
        enable_cache: bool = True,
    ) -> ModelFallbackResult:
        """
        创建模型（带自动降级）

        Args:
            agent_config: Agent 配置
            model_type: 模型类型
            enable_cache: 是否启用缓存

        Returns:
            ModelFallbackResult 包含模型和降级信息

        Raises:
            ValueError: 所有模型（包括降级）都失败
        """
        # 尝试主模型
        try:
            model = self.create_model(agent_config, model_type, enable_cache)
            return ModelFallbackResult(
                model=model,
                provider=agent_config.provider,
                model_name=agent_config.model,
                is_fallback=False,
            )
        except Exception as primary_error:
            logger.warning(f"Primary model failed: {primary_error}")

            # 如果未启用降级或无备用模型，直接失败
            if not agent_config.enable_fallback or not agent_config.fallback_model:
                raise ValueError(
                    f"Primary model failed and no fallback available: {primary_error}"
                )

            # 尝试备用模型
            try:
                logger.info(f"Attempting fallback model: {agent_config.fallback_model}")

                # 创建备用配置
                fallback_config = AgentConfig(
                    provider=agent_config.provider,  # 保持相同提供商
                    model=agent_config.fallback_model,
                    temperature=agent_config.temperature,
                    max_tokens=agent_config.max_tokens,
                    timeout=agent_config.timeout,
                    enable_fallback=False,  # 防止递归降级
                )

                fallback_model = self.create_model(
                    fallback_config, model_type, enable_cache
                )

                return ModelFallbackResult(
                    model=fallback_model,
                    provider=agent_config.provider,
                    model_name=agent_config.fallback_model,
                    is_fallback=True,
                    fallback_reason=str(primary_error),
                )

            except Exception as fallback_error:
                logger.error(f"Fallback model also failed: {fallback_error}")
                raise ValueError(
                    f"Both primary and fallback models failed. Primary: {primary_error}, Fallback: {fallback_error}"
                )

    def clear_cache(self, model_key: Optional[str] = None):
        """
        清除模型缓存

        Args:
            model_key: 特定模型的缓存键，None 表示清除所有
        """
        if model_key:
            self._model_cache.pop(model_key, None)
            logger.info(f"Cleared cache for model: {model_key}")
        else:
            self._model_cache.clear()
            logger.info("Cleared all model cache")

    def reset_circuit_breaker(self, model_key: Optional[str] = None):
        """
        重置熔断器

        Args:
            model_key: 特定模型的键，None 表示重置所有
        """
        if model_key:
            self._failed_models.discard(model_key)
            logger.info(f"Reset circuit breaker for model: {model_key}")
        else:
            self._failed_models.clear()
            logger.info("Reset all circuit breakers")

# 全局模型工厂实例
_factory_instance: Optional[ModelFactory] = None

def get_model_factory() -> ModelFactory:
    """获取全局模型工厂实例（单例）"""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = ModelFactory()
    return _factory_instance

def create_model_with_fallback(
    agent_config: AgentConfig,
    model_type: ModelType = ModelType.CHAT,
    enable_cache: bool = True,
) -> ModelFallbackResult:
    """
    便捷函数：创建带降级的模型

    Args:
        agent_config: Agent 配置
        model_type: 模型类型
        enable_cache: 是否启用缓存

    Returns:
        ModelFallbackResult
    """
    factory = get_model_factory()
    return factory.create_model_with_fallback(agent_config, model_type, enable_cache)

def create_model_with_fallback_simple(
    model: str,
    provider: str,
    model_type: ModelType = ModelType.CHAT,
    enable_cache: bool = True,
    fallback_model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    timeout: int = 60,
) -> ModelFallbackResult:
    """
    便捷函数：通过 model 和 provider 参数创建模型（向后兼容）

    Args:
        model: 模型名称（如 "deepseek-chat"）
        provider: 提供商名称（如 "deepseek"）
        model_type: 模型类型
        enable_cache: 是否启用缓存
        fallback_model: 备用模型（可选）
        temperature: 温度参数
        max_tokens: 最大 token 数
        timeout: 超时时间

    Returns:
        ModelFallbackResult
    """
    # 创建 AgentConfig
    agent_config = AgentConfig(
        model=model,
        provider=ModelProvider(provider),
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_fallback=bool(fallback_model),
        fallback_model=fallback_model,
    )

    return create_model_with_fallback(agent_config, model_type, enable_cache)

if __name__ == "__main__":
    # 测试模型创建
    import sys

    logging.basicConfig(level=logging.INFO)

    config = get_config()
    research_config = config.research_agent
    research_config.fallback_model = "deepseek-chat"  # 设置备用模型

    try:
        result = create_model_with_fallback(research_config)
        print(f"✅ Model created successfully")
        print(f"   Provider: {result.provider}")
        print(f"   Model: {result.model_name}")
        print(f"   Is Fallback: {result.is_fallback}")
        if result.is_fallback:
            print(f"   Fallback Reason: {result.fallback_reason}")
    except Exception as e:
        print(f"❌ Failed to create model: {e}")
        sys.exit(1)
