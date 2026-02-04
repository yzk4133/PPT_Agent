"""
Requirement 值对象测试

测试需求值对象的创建、验证、序列化等功能
"""

import pytest
from domain.value_objects.requirement import (
    Requirement,
    RequirementAnalysis,
    SceneType,
    TemplateType
)
from domain.exceptions import ValidationError

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestRequirementCreation:
    """Requirement 创建测试"""

    def test_create_requirement_with_valid_data(self):
        """
        [TEST-REQ-001] 测试使用有效数据创建需求

        Given: 有效的需求数据
        When: 创建Requirement对象
        Then: 对象应该被成功创建，属性值正确
        """
        # Given
        topic = "AI技术介绍"
        page_num = 10
        scene = SceneType.BUSINESS_REPORT
        template = TemplateType.BUSINESS

        # When
        req = Requirement(
            ppt_topic=topic,
            page_num=page_num,
            scene=scene,
            template_type=template
        )

        # Then
        assert req.ppt_topic == topic
        assert req.page_num == page_num
        assert req.scene == scene
        assert req.template_type == template

    def test_create_requirement_with_minimal_data(self):
        """
        [TEST-REQ-002] 测试使用最小有效数据创建需求

        Given: 仅提供必填字段
        When: 创建Requirement对象
        Then: 对象应该被成功创建，默认值正确
        """
        # Given & When
        req = Requirement(
            ppt_topic="测试主题",
            page_num=5
        )

        # Then
        assert req.ppt_topic == "测试主题"
        assert req.page_num == 5
        assert req.scene == SceneType.BUSINESS_REPORT  # 默认值
        assert req.template_type == TemplateType.BUSINESS  # 默认值
        assert req.language == "EN-US"  # 默认值
        assert req.need_research is False  # 默认值

    def test_requirement_is_immutable(self):
        """
        [TEST-REQ-003] 测试Requirement不可变性

        Given: 一个Requirement对象
        When: 尝试修改属性
        Then: 应该抛出异常
        """
        # Given
        req = Requirement(ppt_topic="测试", page_num=10)

        # When & Then - 尝试修改应该抛出异常
        with pytest.raises(Exception):  # FrozenInstanceError
            req.ppt_topic = "新主题"

        with pytest.raises(Exception):
            req.page_num = 20

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestRequirementValidation:
    """Requirement 验证测试"""

    def test_empty_topic_raises_error(self):
        """
        [TEST-REQ-004] 测试空主题抛出异常

        Given: 空字符串主题
        When: 创建Requirement
        Then: 应该抛出ValidationError
        """
        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            Requirement(ppt_topic="", page_num=10)

        assert "PPT主题不能为空" in str(exc_info.value.errors)

    def test_whitespace_only_topic_raises_error(self):
        """
        [TEST-REQ-005] 测试仅包含空格的主题抛出异常

        Given: 仅包含空格的主题
        When: 创建Requirement
        Then: 应该抛出ValidationError
        """
        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            Requirement(ppt_topic="   ", page_num=10)

        assert "PPT主题不能为空" in str(exc_info.value.errors)

    @pytest.mark.parametrize("page_num", [0, -1, -10, -100])
    def test_page_num_less_than_1_raises_error(self, page_num):
        """
        [TEST-REQ-006] 测试页数小于1抛出异常

        Given: 页数小于1
        When: 创建Requirement
        Then: 应该抛出ValidationError
        """
        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            Requirement(ppt_topic="测试", page_num=page_num)

        assert "页数必须大于0" in str(exc_info.value.errors)

    def test_page_num_exceeds_100_raises_error(self):
        """
        [TEST-REQ-007] 测试页数超过100抛出异常

        Given: 页数为101
        When: 创建Requirement
        Then: 应该抛出ValidationError
        """
        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            Requirement(ppt_topic="测试", page_num=101)

        assert "页数不能超过100" in str(exc_info.value.errors)

    @pytest.mark.parametrize("page_num", [1, 2, 10, 50, 99, 100])
    def test_valid_page_numbers(self, page_num):
        """
        [TEST-REQ-008] 测试有效页数边界值

        Given: 边界页数（1和100）
        When: 创建Requirement
        Then: 应该成功创建
        """
        # When & Then
        req = Requirement(ppt_topic="测试", page_num=page_num)
        assert req.page_num == page_num

    def test_invalid_scene_type_raises_error(self):
        """
        [TEST-REQ-009] 测试无效场景类型抛出异常

        Given: 无效的场景类型
        When: 创建Requirement
        Then: 应该抛出ValidationError
        """
        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            Requirement(ppt_topic="测试", page_num=10, scene="invalid_scene")

        assert "无效的场景类型" in str(exc_info.value.errors)

    def test_invalid_template_type_raises_error(self):
        """
        [TEST-REQ-010] 测试无效模板类型抛出异常

        Given: 无效的模板类型
        When: 创建Requirement
        Then: 应该抛出ValidationError
        """
        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            Requirement(ppt_topic="测试", page_num=10, template_type="invalid_template")

        assert "无效的模板类型" in str(exc_info.value.errors)

    def test_core_modules_exceeds_page_num_raises_error(self):
        """
        [TEST-REQ-011] 测试核心模块数超过页数抛出异常

        Given: 核心模块数大于页数
        When: 创建Requirement
        Then: 应该抛出ValidationError
        """
        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            Requirement(
                ppt_topic="测试",
                page_num=5,
                core_modules=["模块1", "模块2", "模块3", "模块4", "模块5", "模块6"]
            )

        assert "核心模块数量不能超过页数" in str(exc_info.value.errors)

    def test_core_modules_equals_page_num(self):
        """
        [TEST-REQ-012] 测试核心模块数等于页数

        Given: 核心模块数等于页数
        When: 创建Requirement
        Then: 应该成功创建
        """
        # When & Then - 不应该抛出异常
        req = Requirement(
            ppt_topic="测试",
            page_num=5,
            core_modules=["模块1", "模块2", "模块3", "模块4", "模块5"]
        )
        assert len(req.core_modules) == 5

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestRequirementFactoryMethods:
    """Requirement 工厂方法测试"""

    def test_with_defaults_sets_all_defaults(self):
        """
        [TEST-REQ-013] 测试with_defaults设置所有默认值

        Given: 仅提供主题
        When: 使用with_defaults创建
        Then: 应该设置所有默认值
        """
        # When
        req = Requirement.with_defaults(ppt_topic="AI介绍")

        # Then
        assert req.ppt_topic == "AI介绍"
        assert req.industry == "通用"
        assert req.audience == "普通观众"
        assert len(req.core_modules) > 0
        assert len(req.keywords) > 0

    def test_with_defaults_respects_scene_type(self):
        """
        [TEST-REQ-014] 测试with_defaults根据场景设置模块

        Given: 不同的场景类型
        When: 使用with_defaults创建
        Then: 核心模块应该符合场景
        """
        # When - 商务汇报
        business_req = Requirement.with_defaults(
            ppt_topic="销售报告",
            scene=SceneType.BUSINESS_REPORT
        )

        # Then
        assert "封面" in business_req.core_modules
        assert "目录" in business_req.core_modules

        # When - 校园答辩
        campus_req = Requirement.with_defaults(
            ppt_topic="毕业论文",
            scene=SceneType.CAMPUS_DEFENSE
        )

        # Then
        assert "封面" in campus_req.core_modules
        assert "研究背景" in campus_req.core_modules

    def test_with_defaults_can_override(self):
        """
        [TEST-REQ-015] 测试with_defaults可以覆盖默认值

        Given: 提供自定义值
        When: 使用with_defaults创建
        Then: 自定义值应该覆盖默认值
        """
        # When
        req = Requirement.with_defaults(
            ppt_topic="AI介绍",
            industry="科技",
            audience="开发者"
        )

        # Then
        assert req.industry == "科技"
        assert req.audience == "开发者"

    def test_extract_keywords_from_topic(self):
        """
        [TEST-REQ-016] 测试从主题提取关键词

        Given: 一个主题
        When: 使用with_defaults创建
        Then: 关键词应该从主题中提取
        """
        # When
        req = Requirement.with_defaults(ppt_topic="人工智能在医疗领域的应用")

        # Then
        assert len(req.keywords) > 0
        assert any("人工智能" in k or "AI" in k for k in req.keywords)

    def test_from_natural_language(self):
        """
        [TEST-REQ-017] 测试从自然语言创建需求

        Given: 自然语言输入
        When: 使用from_natural_language创建
        Then: 应该创建一个基本需求
        """
        # When
        req = Requirement.from_natural_language("帮我做一个关于AI的PPT")

        # Then
        assert req.ppt_topic == "帮我做一个关于AI的PPT"
        assert req.page_num == 10  # 默认值

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestRequirementSerialization:
    """Requirement 序列化测试"""

    def test_to_dict_returns_correct_data(self):
        """
        [TEST-REQ-018] 测试to_dict返回正确数据

        Given: 一个Requirement对象
        When: 转换为字典
        Then: 字典应该包含所有字段
        """
        # Given
        req = Requirement(
            ppt_topic="AI介绍",
            page_num=10,
            scene=SceneType.BUSINESS_REPORT,
            template_type=TemplateType.BUSINESS,
            industry="科技",
            audience="开发者"
        )

        # When
        data = req.to_dict()

        # Then
        assert data["ppt_topic"] == "AI介绍"
        assert data["page_num"] == 10
        assert data["scene"] == "business_report"
        assert data["template_type"] == "business_template"
        assert data["industry"] == "科技"
        assert data["audience"] == "开发者"

    def test_from_dict_creates_requirement(self):
        """
        [TEST-REQ-019] 测试from_dict创建Requirement

        Given: 一个需求字典
        When: 从字典创建Requirement
        Then: 对象应该被正确创建
        """
        # Given
        data = {
            "ppt_topic": "AI介绍",
            "page_num": 10,
            "scene": "business_report",
            "template_type": "business_template",
            "industry": "科技",
            "audience": "开发者"
        }

        # When
        req = Requirement.from_dict(data)

        # Then
        assert req.ppt_topic == "AI介绍"
        assert req.page_num == 10
        assert req.scene == SceneType.BUSINESS_REPORT
        assert req.template_type == TemplateType.BUSINESS

    def test_round_trip_preserves_data(self):
        """
        [TEST-REQ-020] 测试往返转换保持数据一致性

        Given: 一个Requirement对象
        When: 转换为字典再还原
        Then: 数据应该完全一致
        """
        # Given
        original = Requirement(
            ppt_topic="AI介绍",
            page_num=10,
            scene=SceneType.BUSINESS_REPORT,
            industry="科技"
        )

        # When
        data = original.to_dict()
        restored = Requirement.from_dict(data)

        # Then
        assert restored.ppt_topic == original.ppt_topic
        assert restored.page_num == original.page_num
        assert restored.scene == original.scene
        assert restored.industry == original.industry

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p1
class TestRequirementStringRepresentation:
    """Requirement 字符串表示测试"""

    def test_str_representation(self):
        """
        [TEST-REQ-021] 测试字符串表示

        Given: 一个Requirement对象
        When: 转换为字符串
        Then: 应该包含关键信息
        """
        # Given
        req = Requirement(
            ppt_topic="AI介绍",
            page_num=10,
            template_type=TemplateType.BUSINESS
        )

        # When
        req_str = str(req)

        # Then
        assert "AI介绍" in req_str
        assert "10" in req_str
        assert "business_template" in req_str

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p2
class TestRequirementAnalysis:
    """RequirementAnalysis 测试"""

    def test_create_analysis(self):
        """
        [TEST-REQ-022] 测试创建需求分析

        Given: 需求和分析结果
        When: 创建RequirementAnalysis
        Then: 分析结果应该被正确存储
        """
        # Given
        req = Requirement(ppt_topic="AI介绍", page_num=10)

        # When
        analysis = RequirementAnalysis(
            requirement=req,
            confidence=0.95,
            missing_fields=["语言", "风格"],
            ambiguous_fields=["目标受众"],
            suggestions=["建议添加案例分析"]
        )

        # Then
        assert analysis.requirement == req
        assert analysis.confidence == 0.95
        assert "语言" in analysis.missing_fields
        assert "目标受众" in analysis.ambiguous_fields
        assert len(analysis.suggestions) > 0

    def test_analysis_to_dict(self):
        """
        [TEST-REQ-023] 测试分析结果序列化

        Given: 一个RequirementAnalysis对象
        When: 转换为字典
        Then: 应该包含所有分析数据
        """
        # Given
        req = Requirement(ppt_topic="AI介绍", page_num=10)
        analysis = RequirementAnalysis(
            requirement=req,
            confidence=0.9,
            missing_fields=["语言"],
            suggestions=["建议1"]
        )

        # When
        data = analysis.to_dict()

        # Then
        assert "requirement" in data
        assert "confidence" in data
        assert data["confidence"] == 0.9
        assert "语言" in data["missing_fields"]

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p1
class TestRequirementSceneTypes:
    """Requirement 场景类型测试"""

    def test_all_scene_types_valid(self):
        """
        [TEST-REQ-024] 测试所有场景类型都有效

        Given: 所有定义的场景类型
        When: 创建Requirement
        Then: 所有类型都应该有效
        """
        for scene in SceneType:
            # When & Then - 不应该抛出异常
            req = Requirement(
                ppt_topic="测试",
                page_num=10,
                scene=scene
            )
            assert req.scene == scene

    def test_all_template_types_valid(self):
        """
        [TEST-REQ-025] 测试所有模板类型都有效

        Given: 所有定义的模板类型
        When: 创建Requirement
        Then: 所有类型都应该有效
        """
        for template in TemplateType:
            # When & Then - 不应该抛出异常
            req = Requirement(
                ppt_topic="测试",
                page_num=10,
                template_type=template
            )
            assert req.template_type == template

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
