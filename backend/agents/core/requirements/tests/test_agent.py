"""
需求解析智能体 - Agent测试

测试目标：验证RequirementParserAgent类的初始化和方法骨架

测试分组：
- 组1: 初始化测试 (TA-INIT-001)
- 组2: 方法骨架测试 (TA-SKELETON-001)
- 组3: 参数验证测试 (TA-VALIDATE-001)

测试策略：
- 使用Mock模拟BaseAgent和ChatOpenAI，避免真实API调用
- 使用unittest.mock.patch来替换依赖
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from pydantic import ValidationError

# 导入被测试的模块
try:
    from backend.agents.core.requirements.requirement_agent import RequirementParserAgent
    from backend.agents.core.requirements.models import PPTRequirement, Language
except ImportError:
    pytest.skip("requirement_agent.py还未创建", allow_module_level=True)


class TestRequirementParserAgentInit:
    """测试RequirementParserAgent初始化 - TA-INIT-001"""

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_init_with_default_parameters(self, mock_chat_openai):
        """TA-INIT-001: 使用默认参数初始化"""
        # 设置mock实例
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()

        # 验证基本属性
        assert agent is not None
        assert hasattr(agent, 'agent_name')
        assert hasattr(agent, 'model')
        assert hasattr(agent, 'temperature')
        assert hasattr(agent, 'enable_memory')
        # 验证新增的参数
        assert hasattr(agent, 'timeout')
        assert hasattr(agent, 'max_retries')

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_init_with_custom_parameters(self, mock_chat_openai):
        """TA-INIT-002: 使用自定义参数初始化"""
        # 设置mock实例
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent(
            temperature=0.3,
            agent_name="custom_parser",
            enable_memory=True,
            timeout=15,
            max_retries=2
        )

        # 验证自定义参数被正确设置
        assert agent.agent_name == "custom_parser"
        assert agent.temperature == 0.3
        assert agent.enable_memory is True
        assert agent.timeout == 15
        assert agent.max_retries == 2

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_init_inherits_from_base_agent(self, mock_chat_openai):
        """TA-INIT-003: 验证继承自BaseAgent"""
        # 设置mock实例
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()

        # 验证有父类的基础属性
        assert hasattr(agent, 'agent_name')
        assert hasattr(agent, 'model')
        assert hasattr(agent, 'temperature')
        assert hasattr(agent, 'has_memory')

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_enable_memory_default_value(self, mock_chat_openai):
        """TA-INIT-004: 验证enable_memory默认值为False"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        assert agent.enable_memory is False

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_agent_name_default_value(self, mock_chat_openai):
        """TA-INIT-005: 验证agent_name默认值为RequirementParserAgent"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        assert agent.agent_name == "RequirementParserAgent"

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_temperature_default_value(self, mock_chat_openai):
        """TA-INIT-006: 验证temperature默认值为0.0"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        assert agent.temperature == 0.0

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_timeout_default_value(self, mock_chat_openai):
        """TA-INIT-007: 验证timeout默认值为10"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        assert agent.timeout == 10

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_max_retries_default_value(self, mock_chat_openai):
        """TA-INIT-008: 验证max_retries默认值为1"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        assert agent.max_retries == 1


class TestRequirementParserAgentMethods:
    """测试RequirementParserAgent方法 - TA-SKELETON-001"""

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_parse_method_exists(self, mock_chat_openai):
        """TA-SKELETON-001: parse方法存在"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        assert hasattr(agent, 'parse')
        assert callable(agent.parse)

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_parse_method_signature(self, mock_chat_openai):
        """TA-SKELETON-002: parse方法签名正确"""
        import inspect
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()

        # 验证是async方法
        assert inspect.iscoroutinefunction(agent.parse)

        # 验证参数
        sig = inspect.signature(agent.parse)
        params = list(sig.parameters.keys())
        assert 'user_input' in params

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_run_method_exists(self, mock_chat_openai):
        """TA-SKELETON-003: run方法存在"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        assert hasattr(agent, 'run')
        assert callable(agent.run)

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_run_method_is_async(self, mock_chat_openai):
        """TA-SKELETON-004: run是async方法"""
        import inspect
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        assert inspect.iscoroutinefunction(agent.run)

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_run_node_method_exists(self, mock_chat_openai):
        """TA-SKELETON-005: run_node方法存在"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        assert hasattr(agent, 'run_node')
        assert callable(agent.run_node)

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_fallback_parse_method_exists(self, mock_chat_openai):
        """TA-SKELETON-006: _fallback_parse方法存在"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        assert hasattr(agent, '_fallback_parse')
        assert callable(agent._fallback_parse)

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_validate_and_infer_method_exists(self, mock_chat_openai):
        """TA-SKELETON-007: _validate_and_infer方法存在"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        assert hasattr(agent, '_validate_and_infer')
        assert callable(agent._validate_and_infer)


class TestRequirementParserAgentValidation:
    """测试参数验证 - TA-VALIDATE-001"""

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_temperature_default_is_zero(self, mock_chat_openai):
        """TA-VALIDATE-001: temperature默认值为0（确定性行为）"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        assert agent.temperature == 0.0

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_temperature_can_be_customized(self, mock_chat_openai):
        """TA-VALIDATE-002: temperature可以被自定义"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent(temperature=0.7)
        assert agent.temperature == 0.7

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_enable_memory_default_is_false(self, mock_chat_openai):
        """TA-VALIDATE-003: enable_memory默认为False"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        assert agent.enable_memory is False

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_enable_memory_can_be_enabled(self, mock_chat_openai):
        """TA-VALIDATE-004: enable_memory可以被启用"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent(enable_memory=True)
        assert agent.enable_memory is True


class TestRequirementParserAgentAttributes:
    """测试Agent属性 - TA-ATTR-001"""

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_agent_has_description(self, mock_chat_openai):
        """TA-ATTR-001: Agent有描述信息"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        # 验证有docstring
        assert agent.__class__.__doc__ is not None
        assert len(agent.__class__.__doc__) > 0

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_agent_is_not_abstract(self, mock_chat_openai):
        """TA-ATTR-002: Agent可以被实例化"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        assert isinstance(agent, RequirementParserAgent)

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_agent_has_parser_chain(self, mock_chat_openai):
        """TA-ATTR-003: Agent有parser_chain属性"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        assert hasattr(agent, 'parser_chain')

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_has_memory_property(self, mock_chat_openai):
        """TA-ATTR-004: has_memory属性存在"""
        mock_model_instance = Mock()
        mock_model_instance.model_name = "gpt-4o-mini"
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        # 验证has_memory属性存在且可访问
        assert hasattr(agent, 'has_memory')
        # 默认情况下没有记忆
        assert agent.has_memory is False


class TestRequirementParserAgentFallbackParse:
    """测试规则降级解析 - TA-FALLBACK-001"""

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_fallback_parse_chinese_input(self, mock_chat_openai):
        """TA-FALLBACK-001: 中文输入识别"""
        mock_model_instance = Mock()
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        result = agent._fallback_parse("生成一份关于人工智能的PPT")

        assert result["language"] == "ZH-CN"
        assert result["ppt_topic"] == "生成一份关于人工智能的PPT"

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_fallback_parse_english_input(self, mock_chat_openai):
        """TA-FALLBACK-002: 英文输入识别"""
        mock_model_instance = Mock()
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        result = agent._fallback_parse("Create a presentation about AI")

        assert result["language"] == "EN-US"
        assert result["ppt_topic"] == "Create a presentation about AI"

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_fallback_parse_with_page_number(self, mock_chat_openai):
        """TA-FALLBACK-003: 提取页数"""
        mock_model_instance = Mock()
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        result = agent._fallback_parse("生成一份15页的PPT")

        assert result["page_num"] == 15

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_fallback_parse_without_page_number(self, mock_chat_openai):
        """TA-FALLBACK-004: 无页数时使用默认值"""
        mock_model_instance = Mock()
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        result = agent._fallback_parse("生成一份PPT")

        assert result["page_num"] == 10

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_fallback_parse_page_out_of_range_low(self, mock_chat_openai):
        """TA-FALLBACK-005: 页数过小时自动修正"""
        mock_model_instance = Mock()
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        result = agent._fallback_parse("生成一份3页的PPT")

        # 页数应该被修正到最小值5
        assert result["page_num"] == 5

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_fallback_parse_page_out_of_range_high(self, mock_chat_openai):
        """TA-FALLBACK-006: 页数过大时自动修正"""
        mock_model_instance = Mock()
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        result = agent._fallback_parse("生成一份100页的PPT")

        # 页数应该被修正到最大值50
        assert result["page_num"] == 50

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_fallback_parse_academic_keywords(self, mock_chat_openai):
        """TA-FALLBACK-007: 学术关键词识别"""
        mock_model_instance = Mock()
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        result = agent._fallback_parse("生成一份学术研究PPT")

        assert result["template_type"] == "academic_template" or result["scene"] == "academic_presentation"

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_fallback_parse_creative_keywords(self, mock_chat_openai):
        """TA-FALLBACK-008: 创意关键词识别"""
        mock_model_instance = Mock()
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        result = agent._fallback_parse("生成一份创意设计PPT")

        # 创意场景应该被识别
        assert "creative" in result.get("template_type", "") or "creative" in result.get("style_preference", "")

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_fallback_parse_returns_valid_dict(self, mock_chat_openai):
        """TA-FALLBACK-009: 返回字典能通过PPTRequirement验证"""
        mock_model_instance = Mock()
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        result = agent._fallback_parse("生成一份关于人工智能的15页PPT")

        # 验证返回字典包含所有必需字段
        assert "ppt_topic" in result
        assert "page_num" in result
        assert "language" in result
        assert "template_type" in result
        assert "scene" in result

        # 验证可以用PPTRequirement验证（如果实现了tone字段）
        try:
            req = PPTRequirement(
                ppt_topic=result["ppt_topic"],
                page_num=result["page_num"],
                language=Language(result["language"])
            )
            assert req.page_num == result["page_num"]
        except (ValidationError, ValueError) as e:
            pytest.fail(f"返回字典无法通过PPTRequirement验证: {e}")

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_fallback_parse_long_input_truncated(self, mock_chat_openai):
        """TA-FALLBACK-010: 长输入自动截断到100字符"""
        mock_model_instance = Mock()
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        long_input = "生成一份关于" + "A" * 200 + "的PPT"
        result = agent._fallback_parse(long_input)

        # 主题应该被截断到100字符
        assert len(result["ppt_topic"]) <= 100

    @patch('backend.agents.core.base_agent.ChatOpenAI')
    def test_fallback_parse_mixed_chinese_english(self, mock_chat_openai):
        """TA-FALLBACK-011: 混合中英文优先识别为中文"""
        mock_model_instance = Mock()
        mock_chat_openai.return_value = mock_model_instance

        agent = RequirementParserAgent()
        result = agent._fallback_parse("生成一份AI人工智能的PPT presentation")

        # 包含中文应该识别为ZH-CN
        assert result["language"] == "ZH-CN"
