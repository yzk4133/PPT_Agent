"""
Requirement State Domain Model

Domain model for the requirement parsing stage state.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple

@dataclass
class RequirementState:
    """
    需求解析后的状态

    表示需求解析阶段完成后的结构化状态。

    Attributes:
        ppt_topic: PPT主题
        scene: 使用场景
        industry: 行业
        audience: 受众
        page_num: 页数
        template_type: 模板类型
        core_modules: 核心模块列表
        need_research: 是否需要研究资料
        keywords: 关键词列表
        language: 语言
        special_require: 特殊要求列表
    """

    ppt_topic: str
    scene: str = "business_report"
    industry: str = ""
    audience: str = ""
    page_num: int = 10
    template_type: str = "business_template"
    core_modules: List[str] = field(default_factory=list)
    need_research: bool = False
    keywords: List[str] = field(default_factory=list)
    language: str = "ZH-CN"
    special_require: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（兼容性）"""
        return {
            "ppt_topic": self.ppt_topic,
            "scene": self.scene,
            "industry": self.industry,
            "audience": self.audience,
            "page_num": self.page_num,
            "template_type": self.template_type,
            "core_modules": self.core_modules,
            "need_research": self.need_research,
            "keywords": self.keywords,
            "language": self.language,
            "special_require": self.special_require
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RequirementState":
        """从字典创建"""
        return cls(
            ppt_topic=data.get("ppt_topic", ""),
            scene=data.get("scene", "business_report"),
            industry=data.get("industry", ""),
            audience=data.get("audience", ""),
            page_num=data.get("page_num", 10),
            template_type=data.get("template_type", "business_template"),
            core_modules=data.get("core_modules", []),
            need_research=data.get("need_research", False),
            keywords=data.get("keywords", []),
            language=data.get("language", "ZH-CN"),
            special_require=data.get("special_require", [])
        )

    def validate(self) -> Tuple[bool, List[str]]:
        """
        自校验

        Returns:
            (是否有效, 错误列表)
        """
        errors = []

        if not self.ppt_topic or len(self.ppt_topic.strip()) == 0:
            errors.append("ppt_topic不能为空")

        if self.page_num < 1 or self.page_num > 100:
            errors.append("page_num必须在1-100之间")

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
            self.core_modules = self._get_default_modules()

        if not self.keywords:
            self.keywords = self._extract_keywords()

    def _get_default_modules(self) -> List[str]:
        """根据场景获取默认核心模块"""
        default_modules = {
            "business_report": ["封面", "目录", "背景介绍", "核心内容", "数据展示", "总结展望"],
            "campus_defense": ["封面", "研究背景", "研究方法", "研究结果", "结论与展望"],
            "product_presentation": ["封面", "产品概述", "核心功能", "使用场景", "价格方案", "联系方式"],
            "training": ["封面", "培训目标", "内容概览", "详细内容", "练习环节", "总结回顾"],
            "conference": ["封面", "会议背景", "议程安排", "核心议题", "讨论环节", "总结"],
        }
        return default_modules.get(self.scene, ["封面", "主要内容", "总结"])

    def _extract_keywords(self) -> List[str]:
        """从主题中提取关键词（简单实现）"""
        import re
        words = re.findall(r'[\w]+', self.ppt_topic)
        return [w for w in words if len(w) > 1][:3]

    @property
    def summary(self) -> str:
        """获取需求摘要"""
        return f"{self.ppt_topic} ({self.page_num}页, {self.scene})"

if __name__ == "__main__":
    # 测试代码
    state = RequirementState(
        ppt_topic="AI技术介绍",
        page_num=15,
        scene="business_report",
        need_research=True
    )

    print("RequirementState Test:")
    print(f"Summary: {state.summary}")

    is_valid, errors = state.validate()
    print(f"Valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")

    state.fill_defaults()
    print(f"Default modules: {state.core_modules}")

    dict_data = state.to_dict()
    restored = RequirementState.from_dict(dict_data)
    print(f"Restored: {restored.summary}")
