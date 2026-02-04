"""
Model Factory 测试
"""

import pytest
from unittest.mock import patch, MagicMock
from infrastructure.llm.common_model_factory import (
    ModelFactory,
    ModelFallbackResult,
    ModelType,
    ModelProvider,
    get_model_factory,
    create_model_with_fallback,
    create_model_with_fallback_simple,
    _factory_instance,
)
from infrastructure.config.common_config import AgentConfig

@pytest.mark.unit
def test_model_factory_initialization():
    """测试模型工厂初始化"""
    factory = ModelFactory()

    assert factory.config is not None
    assert factory._model_cache == {}
    assert factory._failed_models == set()

@pytest.mark.unit
def test_get_litellm_model_name():
    """测试 LiteLLM 模型名称转换"""
    factory = ModelFactory()

    # 测试各提供商前缀
    assert factory._get_litellm_model_name(ModelProvider.DEEPSEEK, "chat") == "deepseek/chat"
    assert factory._get_litellm_model_name(ModelProvider.OPENAI, "gpt-4") == "openai/gpt-4"
    assert factory._get_litellm_model_name(ModelProvider.CLAUDE, "claude-3") == "claude/claude-3"
    assert factory._get_litellm_model_name(ModelProvider.GOOGLE, "gemini-pro") == "gemini/gemini-pro"
    assert factory._get_litellm_model_name(ModelProvider.QWEN, "qwen-turbo") == "qwen/qwen-turbo"

    # 测试已包含前缀的情况
    assert factory._get_litellm_model_name(ModelProvider.DEEPSEEK, "deepseek/chat") == "deepseek/chat"

@pytest.mark.unit
def test_create_litellm_model():
    """测试创建 LiteLLM 模型"""
    factory = ModelFactory()

    config = AgentConfig(
        provider=ModelProvider.DEEPSEEK,
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=4096,
        timeout=60,
    )

    model = factory._create_litellm_model("deepseek/deepseek-chat", ModelProvider.DEEPSEEK, config)

    assert model["model"] == "deepseek/deepseek-chat"
    assert model["temperature"] == 0.7
    assert model["max_tokens"] == 4096
    assert model["type"] == "litellm"
    assert model["provider"] == "deepseek"

@pytest.mark.unit
@patch("infrastructure.llm.common_model_factory.genai.Client")
def test_create_google_model(mock_google_client):
    """测试创建 Google 模型"""
    mock_client_instance = MagicMock()
    mock_google_client.return_value = mock_client_instance

    factory = ModelFactory()

    config = AgentConfig(
        provider=ModelProvider.GOOGLE,
        model="gemini-pro",
        temperature=0.7,
        max_tokens=4096,
    )

    model = factory._create_google_model("gemini/gemini-pro", config)

    assert model["type"] == "google"
    assert model["model"] == "gemini-pro"
    assert model["client"] == mock_client_instance
    assert model["config"].temperature == 0.7
    assert model["config"].max_output_tokens == 4096

@pytest.mark.unit
def test_create_model_with_caching():
    """测试模型创建和缓存"""
    factory = ModelFactory()

    config = AgentConfig(
        provider=ModelProvider.DEEPSEEK,
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=4096,
    )

    # Mock 创建模型方法
    with patch.object(factory, "_create_litellm_model") as mock_create:
        mock_create.return_value = {"model": "deepseek/chat", "type": "litellm"}

        # 第一次创建
        model1 = factory.create_model(config)
        assert model1 is not None
        mock_create.assert_called_once()

        # 第二次创建（应该使用缓存）
        model2 = factory.create_model(config)
        assert model2 is not None
        # mock_create 仍然只被调用一次（第二次使用缓存）

    # 验证缓存
    cache_key = f"{ModelProvider.DEEPSEEK}:{config.model}:{ModelType.CHAT}"
    assert cache_key in factory._model_cache

@pytest.mark.unit
def test_create_model_without_caching():
    """测试禁用缓存的模型创建"""
    factory = ModelFactory()

    config = AgentConfig(
        provider=ModelProvider.OPENAI,
        model="gpt-4",
        temperature=0.5,
        max_tokens=2048,
    )

    with patch.object(factory, "_create_litellm_model") as mock_create:
        mock_create.return_value = {"model": "openai/gpt-4", "type": "litellm"}

        # 创建模型，禁用缓存
        model1 = factory.create_model(config, enable_cache=False)
        model2 = factory.create_model(config, enable_cache=False)

        # 两次都应该调用创建方法
        assert mock_create.call_count == 2

@pytest.mark.unit
def test_create_model_circuit_breaker():
    """测试熔断器功能"""
    factory = ModelFactory()

    config = AgentConfig(
        provider=ModelProvider.DEEPSEEK,
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=4096,
    )

    # 第一次失败
    with pytest.raises(ValueError, match="Model creation failed"):
        factory.create_model(config)

    # 验证熔断器状态
    cache_key = f"{ModelProvider.DEEPSEEK}:{config.model}:{ModelType.CHAT}"
    assert cache_key in factory._failed_models

    # 第二次应该被熔断
    with pytest.raises(ValueError, match="Circuit breaker state"):
        factory.create_model(config)

@pytest.mark.unit
def test_create_model_with_fallback_success():
    """测试带降级的模型创建 - 成功场景"""
    factory = ModelFactory()

    config = AgentConfig(
        provider=ModelProvider.DEEPSEEK,
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=4096,
        enable_fallback=True,
        fallback_model="deepseek-lite",
    )

    with patch.object(factory, "create_model") as mock_create:
        mock_create.return_value = {"model": "deepseek/chat"}

        result = factory.create_model_with_fallback(config)

        assert result.is_fallback is False
        assert result.model_name == "deepseek-chat"
        assert result.provider == ModelProvider.DEEPSEEK
        mock_create.assert_called_once()

@pytest.mark.unit
def test_fallback_on_primary_failure():
    """测试主模型失败时降级"""
    factory = ModelFactory()

    config = AgentConfig(
        provider=ModelProvider.DEEPSEEK,
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=4096,
        enable_fallback=True,
        fallback_model="deepseek-lite",
    )

    with patch.object(factory, "create_model") as mock_create:
        # 主模型失败，备用模型成功
        mock_create.side_effect = [
            ValueError("Primary failed"),  # 第一次调用失败
            {"model": "deepseek-lite"}     # 第二次调用成功
        ]

        result = factory.create_model_with_fallback(config)

        assert result.is_fallback is True
        assert result.model_name == "deepseek-lite"
        assert result.fallback_reason == "Primary failed"
        assert mock_create.call_count == 2

@pytest.mark.unit
def test_fallback_disabled():
    """测试禁用降级时直接失败"""
    factory = ModelFactory()

    config = AgentConfig(
        provider=ModelProvider.DEEPSEEK,
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=4096,
        enable_fallback=False,  # 禁用降级
        fallback_model="deepseek-lite",
    )

    with patch.object(factory, "create_model") as mock_create:
        mock_create.side_effect = ValueError("Primary failed")

        # 应该直接抛出异常，不尝试降级
        with pytest.raises(ValueError, match="Primary model failed and no fallback available"):
            factory.create_model_with_fallback(config)

        # 只调用一次
        assert mock_create.call_count == 1

@pytest.mark.unit
def test_both_primary_and_fallback_fail():
    """测试主模型和备用模型都失败"""
    factory = ModelFactory()

    config = AgentConfig(
        provider=ModelProvider.DEEPSEEK,
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=4096,
        enable_fallback=True,
        fallback_model="deepseek-lite",
    )

    with patch.object(factory, "create_model") as mock_create:
        # 两次调用都失败
        mock_create.side_effect = [
            ValueError("Primary failed"),
            ValueError("Fallback failed"),
        ]

        # 应该抛出包含两个错误的异常
        with pytest.raises(ValueError, match="Both primary and fallback models failed"):
            factory.create_model_with_fallback(config)

        assert mock_create.call_count == 2

@pytest.mark.unit
def test_clear_model_cache():
    """测试清除模型缓存"""
    factory = ModelFactory()

    config = AgentConfig(
        provider=ModelProvider.DEEPSEEK,
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=4096,
    )

    with patch.object(factory, "_create_litellm_model") as mock_create:
        mock_create.return_value = {"model": "deepseek/chat"}

        # 创建两个模型并缓存
        factory.create_model(config)

        cache_key = f"{ModelProvider.DEEPSEEK}:{config.model}:{ModelType.CHAT}"
        assert cache_key in factory._model_cache

        # 清除特定模型缓存
        factory.clear_cache(cache_key)
        assert cache_key not in factory._model_cache

@pytest.mark.unit
def test_clear_all_model_cache():
    """测试清除所有模型缓存"""
    factory = ModelFactory()

    config1 = AgentConfig(
        provider=ModelProvider.DEEPSEEK,
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=4096,
    )

    config2 = AgentConfig(
        provider=ModelProvider.OPENAI,
        model="gpt-4",
        temperature=0.5,
        max_tokens=2048,
    )

    with patch.object(factory, "_create_litellm_model") as mock_create:
        mock_create.return_value = {"model": "test"}

        factory.create_model(config1)
        factory.create_model(config2)

        assert len(factory._model_cache) == 2

        # 清除所有缓存
        factory.clear_cache()
        assert len(factory._model_cache) == 0

@pytest.mark.unit
def test_reset_circuit_breaker():
    """测试重置熔断器"""
    factory = ModelFactory()

    config = AgentConfig(
        provider=ModelProvider.DEEPSEEK,
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=4096,
    )

    # 第一次失败，触发熔断
    with pytest.raises(ValueError):
        factory.create_model(config)

    cache_key = f"{ModelProvider.DEEPSEEK}:{config.model}:{ModelType.CHAT}"
    assert cache_key in factory._failed_models

    # 重置熔断器
    factory.reset_circuit_breaker(cache_key)
    assert cache_key not in factory._failed_models

@pytest.mark.unit
def test_reset_all_circuit_breakers():
    """测试重置所有熔断器"""
    factory = ModelFactory()

    config1 = AgentConfig(
        provider=ModelProvider.DEEPSEEK,
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=4096,
    )

    config2 = AgentConfig(
        provider=ModelProvider.OPENAI,
        model="gpt-4",
        temperature=0.5,
        max_tokens=2048,
    )

    # 触发两个熔断器
    with pytest.raises(ValueError):
        factory.create_model(config1)
    with pytest.raises(ValueError):
        factory.create_model(config2)

    assert len(factory._failed_models) == 2

    # 重置所有
    factory.reset_circuit_breaker()
    assert len(factory._failed_models) == 0

@pytest.mark.unit
def test_global_factory_singleton():
    """测试全局工厂单例"""
    # 重置全局变量
    import infrastructure.llm.common_model_factory as factory_module
    factory_module._factory_instance = None

    factory1 = get_model_factory()
    factory2 = get_model_factory()

    assert factory1 is factory2

@pytest.mark.unit
def test_create_model_with_fallback_convenience_function():
    """测试便捷函数"""
    import infrastructure.llm.common_model_factory as factory_module
    factory_module._factory_instance = None

    config = AgentConfig(
        provider=ModelProvider.DEEPSEEK,
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=4096,
        enable_fallback=True,
        fallback_model="deepseek-lite",
    )

    with patch.object(get_model_factory(), "create_model_with_fallback") as mock_create:
        mock_create.return_value = ModelFallbackResult(
            model={"model": "deepseek/chat"},
            provider=ModelProvider.DEEPSEEK,
            model_name="deepseek-chat",
            is_fallback=False,
        )

        result = create_model_with_fallback(config)

        assert result.is_fallback is False
        mock_create.assert_called_once()

@pytest.mark.unit
def test_create_model_with_fallback_simple():
    """测试简化版便捷函数"""
    import infrastructure.llm.common_model_factory as factory_module
    factory_module._factory_instance = None

    with patch.object(get_model_factory(), "create_model_with_fallback") as mock_create:
        mock_create.return_value = ModelFallbackResult(
            model={"model": "deepseek/chat"},
            provider=ModelProvider.DEEPSEEK,
            model_name="deepseek-chat",
            is_fallback=False,
        )

        result = create_model_with_fallback_simple(
            model="deepseek-chat",
            provider="deepseek",
            fallback_model="deepseek-lite",
            temperature=0.7,
            max_tokens=4096,
        )

        assert result.is_fallback is False
        mock_create.assert_called_once()

        # 验证传递的参数
        call_args = mock_create.call_args[0][0]
        assert call_args.model == "deepseek-chat"
        assert call_args.provider == ModelProvider.DEEPSEEK
        assert call_args.fallback_model == "deepseek-lite"
