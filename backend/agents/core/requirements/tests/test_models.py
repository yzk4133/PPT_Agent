"""
需求解析智能体 - 数据模型测试

测试目标：验证PPTRequirement模型和枚举类的正确性

测试分组：
- 组1: 枚举类测试 (TM-ENUM-001)
- 组2: 模型创建测试 (TM-CREATE-001)
- 组3: 字段验证测试 (TM-VALIDATE-001)
- 组4: 默认值测试 (TM-DEFAULT-001)
- 组5: 额外字段拒绝测试 (TM-EXTRA-001)
- 组6: 模型转换测试 (TM-CONVERT-001)
"""

import pytest
from pydantic import ValidationError

# 导入被测试的模块（先创建测试，models.py还不存在）
try:
    from backend.agents.core.requirements.models import (
        PPTRequirement,
        Language,
        TemplateType,
        Scene,
        Tone
    )
except ImportError:
    pytest.skip("models.py还未创建", allow_module_level=True)


class TestEnum:
    """测试枚举类 - TM-ENUM-001"""

    def test_language_values(self):
        """TM-ENUM-001: Language枚举值"""
        assert Language.ZH_CN.value == "ZH-CN"
        assert Language.EN_US.value == "EN-US"

    def test_language_from_string(self):
        """TM-ENUM-003: 从字符串创建枚举"""
        lang = Language("ZH-CN")
        assert lang == Language.ZH_CN
        assert lang.value == "ZH-CN"

    def test_template_type_values(self):
        """TM-ENUM-004: TemplateType枚举"""
        assert TemplateType.BUSINESS.value == "business_template"
        assert TemplateType.ACADEMIC.value == "academic_template"
        assert TemplateType.CREATIVE.value == "creative_template"

    def test_scene_values(self):
        """TM-ENUM-005: Scene枚举"""
        assert Scene.BUSINESS_REPORT.value == "business_report"
        assert Scene.ACADEMIC_PRESENTATION.value == "academic_presentation"
        assert Scene.PRODUCT_LAUNCH.value == "product_launch"
        assert Scene.TRAINING.value == "training"

    def test_tone_values(self):
        """TM-ENUM-006: Tone枚举"""
        assert Tone.PROFESSIONAL.value == "professional"
        assert Tone.CASUAL.value == "casual"
        assert Tone.CREATIVE.value == "creative"


class TestPPTRequirement:
    """测试PPTRequirement模型"""

    # ========== 组2: 模型创建测试 ==========

    def test_create_with_required_fields_only(self):
        """TM-CREATE-001: 只提供必须字段，其他使用默认值"""
        req = PPTRequirement(
            ppt_topic="AI",
            page_num=10,
            language=Language.ZH_CN
        )

        # 验证必须字段
        assert req.ppt_topic == "AI"
        assert req.page_num == 10
        assert req.language == Language.ZH_CN

        # 验证默认值（TM-DEFAULT-001）
        assert req.template_type == TemplateType.BUSINESS
        assert req.scene == Scene.BUSINESS_REPORT
        assert req.tone == Tone.PROFESSIONAL
        assert req.core_modules == []
        assert req.need_research is False

    def test_create_with_all_fields(self):
        """TM-CREATE-002: 提供所有字段"""
        req = PPTRequirement(
            ppt_topic="深度学习",
            page_num=20,
            language=Language.ZH_CN,
            template_type=TemplateType.ACADEMIC,
            scene=Scene.ACADEMIC_PRESENTATION,
            tone=Tone.PROFESSIONAL,
            core_modules=["背景", "原理", "应用"],
            need_research=True,
            color_scheme="blue_theme",
            target_audience="技术人员"
        )

        assert req.ppt_topic == "深度学习"
        assert req.page_num == 20
        assert req.template_type == TemplateType.ACADEMIC
        assert req.scene == Scene.ACADEMIC_PRESENTATION
        assert req.core_modules == ["背景", "原理", "应用"]
        assert req.need_research is True
        assert req.color_scheme == "blue_theme"

    def test_create_with_enum_objects(self):
        """TM-CREATE-003: 使用枚举对象创建"""
        req = PPTRequirement(
            ppt_topic="AI",
            page_num=10,
            language=Language.ZH_CN,  # 使用枚举对象
            template_type=TemplateType.BUSINESS,
            scene=Scene.BUSINESS_REPORT
        )

        assert req.language == Language.ZH_CN
        assert req.template_type == TemplateType.BUSINESS

    # ========== 组3: 字段验证测试 ==========

    def test_topic_empty_raises_error(self):
        """TM-VALIDATE-001: 主题为空应抛出ValueError"""
        # Pydantic先检查min_length，所以会抛出ValidationError而不是ValueError
        with pytest.raises(ValidationError):
            PPTRequirement(
                ppt_topic="",
                page_num=10,
                language=Language.ZH_CN
            )

    def test_topic_only_spaces_raises_error(self):
        """TM-VALIDATE-002: 主题只有空格应抛出ValueError"""
        with pytest.raises(ValueError, match="主题不能为空"):
            PPTRequirement(
                ppt_topic="   ",
                page_num=10,
                language=Language.ZH_CN
            )

    def test_topic_too_short_raises_error(self):
        """TM-VALIDATE-003: 主题过短（<2字符）应抛出ValueError"""
        with pytest.raises(ValidationError):
            PPTRequirement(
                ppt_topic="A",  # 1字符，min_length=2
                page_num=10,
                language=Language.ZH_CN
            )

    def test_topic_too_long_raises_error(self):
        """TM-VALIDATE-004: 主题过长（>100字符）应抛出ValueError"""
        with pytest.raises(ValidationError):
            PPTRequirement(
                ppt_topic="A" * 101,  # 101字符，max_length=100
                page_num=10,
                language=Language.ZH_CN
            )

    def test_page_num_too_small_raises_error(self):
        """TM-VALIDATE-005: 页数过小（<5）应抛出ValidationError"""
        with pytest.raises(ValidationError):
            PPTRequirement(
                ppt_topic="AI",
                page_num=4,  # 小于5
                language=Language.ZH_CN
            )

    def test_page_num_too_large_raises_error(self):
        """TM-VALIDATE-006: 页数过大（>50）应抛出ValidationError"""
        with pytest.raises(ValidationError):
            PPTRequirement(
                ppt_topic="AI",
                page_num=51,  # 大于50
                language=Language.ZH_CN
            )

    def test_page_num_minimum_boundary(self):
        """TM-VALIDATE-007: 页数边界值（5）应通过"""
        req = PPTRequirement(
            ppt_topic="AI",
            page_num=5,  # 最小值
            language=Language.ZH_CN
        )
        assert req.page_num == 5

    def test_page_num_maximum_boundary(self):
        """TM-VALIDATE-008: 页数边界值（50）应通过"""
        req = PPTRequirement(
            ppt_topic="AI",
            page_num=50,  # 最大值
            language=Language.ZH_CN
        )
        assert req.page_num == 50

    def test_language_with_enum(self):
        """TM-VALIDATE-009: 使用语言枚举应通过"""
        req = PPTRequirement(
            ppt_topic="AI",
            page_num=10,
            language=Language.ZH_CN
        )
        assert req.language == Language.ZH_CN

    def test_language_with_invalid_enum_raises_error(self):
        """TM-VALIDATE-010: 使用无效语言值应抛出ValidationError"""
        with pytest.raises(ValidationError):
            PPTRequirement(
                ppt_topic="AI",
                page_num=10,
                language="INVALID"  # 无效枚举值
            )

    # ========== 组5: 额外字段拒绝测试 ==========

    def test_extra_fields_forbidden(self):
        """TM-EXTRA-001: 拒绝额外字段（捕获LLM幻觉）"""
        with pytest.raises(ValidationError):
            PPTRequirement(
                ppt_topic="AI",
                page_num=10,
                language=Language.ZH_CN,
                extra_field="不应该存在"  # 额外字段
            )

    # ========== 组6: 模型转换测试 ==========

    def test_model_dump_converts_enum_to_value(self):
        """TM-CONVERT-001: model_dump将枚举转为值"""
        req = PPTRequirement(
            ppt_topic="AI",
            page_num=10,
            language=Language.ZH_CN
        )

        data = req.model_dump()

        # 验证枚举被转为值
        assert data["ppt_topic"] == "AI"
        assert data["page_num"] == 10
        assert data["language"] == "ZH-CN"  # 枚举转为值
        assert data["template_type"] == "business_template"
        assert data["scene"] == "business_report"

    def test_model_dump_json_returns_json_string(self):
        """TM-CONVERT-002: model_dump_json返回JSON字符串"""
        req = PPTRequirement(
            ppt_topic="AI",
            page_num=10,
            language=Language.ZH_CN
        )

        json_str = req.model_dump_json()

        # 验证是JSON字符串（注意：Pydantic的JSON没有空格）
        assert isinstance(json_str, str)
        assert '"ppt_topic":"AI"' in json_str
        assert '"page_num":10' in json_str
        assert '"language":"ZH-CN"' in json_str

    def test_model_roundtrip(self):
        """TM-CONVERT-003: 模型转换往返测试"""
        # 创建原始模型
        req1 = PPTRequirement(
            ppt_topic="AI",
            page_num=10,
            language=Language.ZH_CN,
            template_type=TemplateType.ACADEMIC
        )

        # 转为字典
        data = req1.model_dump()

        # 从字典重建模型
        req2 = PPTRequirement(**data)

        # 验证一致
        assert req2.ppt_topic == req1.ppt_topic
        assert req2.page_num == req1.page_num
        assert req2.language == req1.language
        assert req2.template_type == req1.template_type

    # ========== 补充测试 ==========

    def test_core_modules_default_to_empty_list(self):
        """测试：core_modules默认为空列表"""
        req = PPTRequirement(
            ppt_topic="AI",
            page_num=10,
            language=Language.ZH_CN
        )
        assert req.core_modules == []

    def test_core_modules_can_be_set(self):
        """测试：可以设置core_modules"""
        req = PPTRequirement(
            ppt_topic="AI",
            page_num=10,
            language=Language.ZH_CN,
            core_modules=["模块1", "模块2", "模块3"]
        )
        assert len(req.core_modules) == 3
        assert "模块1" in req.core_modules

    def test_need_research_default_to_false(self):
        """测试：need_research默认为False"""
        req = PPTRequirement(
            ppt_topic="AI",
            page_num=10,
            language=Language.ZH_CN
        )
        assert req.need_research is False

    def test_optional_fields_can_be_none(self):
        """测试：可选字段可以为None"""
        req = PPTRequirement(
            ppt_topic="AI",
            page_num=10,
            language=Language.ZH_CN,
            color_scheme=None,
            target_audience=None
        )
        assert req.color_scheme is None
        assert req.target_audience is None

    def test_optional_fields_can_be_set(self):
        """测试：可选字段可以设置值"""
        req = PPTRequirement(
            ppt_topic="AI",
            page_num=10,
            language=Language.ZH_CN,
            color_scheme="blue",
            target_audience="开发者"
        )
        assert req.color_scheme == "blue"
        assert req.target_audience == "开发者"
