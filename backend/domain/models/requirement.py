"""
Requirement Domain Model

需求领域模型，用于表示结构化的PPT生成需求。
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

class SceneType(str, Enum):
    """使用场景类型"""
    BUSINESS_REPORT = "business_report"  # 商务汇报
    CAMPUS_DEFENSE = "campus_defense"    # 校园答辩
    PRODUCT_PRESENTATION = "product_presentation"  # 产品宣讲
    TRAINING = "training"                # 培训
    CONFERENCE = "conference"            # 会议
    OTHER = "other"                      # 其他

class TemplateType(str, Enum):
    """模板类型"""
    BUSINESS = "business_template"       # 商务模板
    ACADEMIC = "academic_template"       # 学术模板
    CREATIVE = "creative_template"       # 创意模板
    SIMPLE = "simple_template"           # 简约模板
    TECH = "tech_template"               # 科技模板

@dataclass
class Requirement:
    """
    结构化需求模型

    从自然语言中提取的结构化需求。

    Attributes:
        ppt_topic: PPT主题
        scene: 使用场景
        industry: 行业
        audience: 受众
        page_num: 页数
        template_type: 模板类型
        core_modules: 核心模块列表
        need_research: 是否需要研究资料
        special_require: 特殊要求列表
        language: 语言
        keywords: 关键词列表
        style_preference: 风格偏好
        color_scheme: 配色方案
    """

    ppt_topic: str
    scene: SceneType = SceneType.BUSINESS_REPORT
    industry: str = ""
    audience: str = ""
    page_num: int = 10
    template_type: TemplateType = TemplateType.BUSINESS
    core_modules: List[str] = field(default_factory=list)
    need_research: bool = False
    special_require: List[str] = field(default_factory=list)
    language: str = "EN-US"
    keywords: List[str] = field(default_factory=list)
    style_preference: str = ""
    color_scheme: str = ""

    def validate(self) -> tuple[bool, List[str]]:
        """
        校验需求完整性

        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []

        if not self.ppt_topic or len(self.ppt_topic.strip()) == 0:
            errors.append("PPT主题不能为空")

        if self.page_num < 1:
            errors.append("页数必须大于0")
        elif self.page_num > 100:
            errors.append("页数不能超过100")

        if self.scene not in SceneType:
            errors.append(f"无效的场景类型: {self.scene}")

        if self.template_type not in TemplateType:
            errors.append(f"无效的模板类型: {self.template_type}")

        # 检查核心模块数量
        if self.core_modules and len(self.core_modules) > self.page_num:
            errors.append("核心模块数量不能超过页数")

        return len(errors) == 0, errors

    def fill_defaults(self) -> None:
        """填充默认值"""
        if not self.industry:
            self.industry = "通用"

        if not self.audience:
            self.audience = "普通观众"

        if not self.core_modules:
            # 根据场景生成默认核心模块
            self.core_modules = self._get_default_modules()

        if not self.keywords:
            # 从主题中提取关键词
            self.keywords = self._extract_keywords()

    def _get_default_modules(self) -> List[str]:
        """根据场景获取默认核心模块"""
        default_modules = {
            SceneType.BUSINESS_REPORT: ["封面", "目录", "背景介绍", "核心内容", "数据展示", "总结展望"],
            SceneType.CAMPUS_DEFENSE: ["封面", "研究背景", "研究方法", "研究结果", "结论与展望"],
            SceneType.PRODUCT_PRESENTATION: ["封面", "产品概述", "核心功能", "使用场景", "价格方案", "联系方式"],
            SceneType.TRAINING: ["封面", "培训目标", "内容概览", "详细内容", "练习环节", "总结回顾"],
            SceneType.CONFERENCE: ["封面", "会议背景", "议程安排", "核心议题", "讨论环节", "总结"],
            SceneType.OTHER: ["封面", "目录", "主要内容", "总结"]
        }
        return default_modules.get(self.scene, ["封面", "主要内容", "总结"])

    def _extract_keywords(self) -> List[str]:
        """从主题中提取关键词（简单实现）"""
        # 简单实现：按空格和标点分割
        import re
        words = re.findall(r'[\w]+', self.ppt_topic)
        # 返回前3个有意义的词
        return [w for w in words if len(w) > 1][:3]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "ppt_topic": self.ppt_topic,
            "scene": self.scene.value if isinstance(self.scene, SceneType) else self.scene,
            "industry": self.industry,
            "audience": self.audience,
            "page_num": self.page_num,
            "template_type": self.template_type.value if isinstance(self.template_type, TemplateType) else self.template_type,
            "core_modules": self.core_modules,
            "need_research": self.need_research,
            "special_require": self.special_require,
            "language": self.language,
            "keywords": self.keywords,
            "style_preference": self.style_preference,
            "color_scheme": self.color_scheme
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Requirement":
        """从字典创建实例"""
        scene_str = data.get("scene", "business_report")
        scene = SceneType(scene_str) if isinstance(scene_str, str) else scene_str

        template_str = data.get("template_type", "business_template")
        template_type = TemplateType(template_str) if isinstance(template_str, str) else template_str

        return cls(
            ppt_topic=data.get("ppt_topic", ""),
            scene=scene,
            industry=data.get("industry", ""),
            audience=data.get("audience", ""),
            page_num=data.get("page_num", 10),
            template_type=template_type,
            core_modules=data.get("core_modules", []),
            need_research=data.get("need_research", False),
            special_require=data.get("special_require", []),
            language=data.get("language", "EN-US"),
            keywords=data.get("keywords", []),
            style_preference=data.get("style_preference", ""),
            color_scheme=data.get("color_scheme", "")
        )

    @classmethod
    def from_natural_language(cls, natural_input: str) -> "Requirement":
        """
        从自然语言输入创建需求（简单解析）

        Args:
            natural_input: 自然语言输入

        Returns:
            Requirement实例
        """
        # 简单解析实现
        # 实际使用中应该由RequirementParserAgent来处理
        return cls(
            ppt_topic=natural_input.strip(),
            page_num=10,
            language="EN-US"
        )

    def __str__(self) -> str:
        return f"Requirement(topic='{self.ppt_topic}', pages={self.page_num}, template={self.template_type.value})"

@dataclass
class RequirementAnalysis:
    """
    需求分析结果

    Attributes:
        requirement: 结构化需求
        confidence: 置信度 (0-1)
        missing_fields: 缺失字段列表
        ambiguous_fields: 模糊字段列表
        suggestions: 建议列表
    """

    requirement: Requirement
    confidence: float = 1.0
    missing_fields: List[str] = field(default_factory=list)
    ambiguous_fields: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement": self.requirement.to_dict(),
            "confidence": self.confidence,
            "missing_fields": self.missing_fields,
            "ambiguous_fields": self.ambiguous_fields,
            "suggestions": self.suggestions
        }

if __name__ == "__main__":
    # 测试代码
    req = Requirement(
        ppt_topic="2025电商618销售复盘",
        page_num=15,
        template_type=TemplateType.BUSINESS,
        need_research=True
    )

    is_valid, errors = req.validate()
    print(f"Valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")

    req.fill_defaults()
    print(f"Default modules: {req.core_modules}")
    print(f"Keywords: {req.keywords}")
    print(req.to_dict())
