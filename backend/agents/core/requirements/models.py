"""
需求解析智能体 - 数据模型

定义PPTRequirement和枚举类，用于结构化PPT生成需求

枚举类：
- Language: ZH_CN, EN_US
- TemplateType: BUSINESS, ACADEMIC, CREATIVE
- Scene: BUSINESS_REPORT, ACADEMIC_PRESENTATION, PRODUCT_LAUNCH, TRAINING
- Tone: PROFESSIONAL, CASUAL, CREATIVE

主模型：
- PPTRequirement: 包含所有字段和验证逻辑
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional
from enum import Enum


class Language(str, Enum):
    """语言代码枚举"""
    ZH_CN = "ZH-CN"  # 中文
    EN_US = "EN-US"  # 英文


class TemplateType(str, Enum):
    """PPT模板类型枚举"""
    BUSINESS = "business_template"     # 商务模板
    ACADEMIC = "academic_template"     # 学术模板
    CREATIVE = "creative_template"    # 创意模板


class Scene(str, Enum):
    """PPT使用场景枚举"""
    BUSINESS_REPORT = "business_report"              # 商务报告
    ACADEMIC_PRESENTATION = "academic_presentation"  # 学术演示
    PRODUCT_LAUNCH = "product_launch"                # 产品发布
    TRAINING = "training"                            # 培训教学


class Tone(str, Enum):
    """PPT语调风格枚举"""
    PROFESSIONAL = "professional"  # 专业正式
    CASUAL = "casual"            # 轻松随意
    CREATIVE = "creative"        # 创意活泼


class PPTRequirement(BaseModel):
    """
    PPT生成需求模型

    字段分类：
    - 必须字段：ppt_topic, page_num, language
    - 推荐字段：template_type, scene, tone, core_modules（有默认值）
    - 可选字段：need_research, color_scheme, target_audience

    验证规则：
    - ppt_topic: 2-100字符，不能为空或只有空格
    - page_num: 5-50之间
    - language: 必须是有效枚举值
    - 拒绝额外字段（捕获LLM幻觉）
    """

    # ========== 必须字段 ==========
    ppt_topic: str = Field(
        ...,
        description="PPT主题",
        min_length=2,
        max_length=100
    )

    page_num: int = Field(
        ...,
        description="PPT页数",
        ge=5,
        le=50
    )

    language: Language = Field(
        ...,
        description="语言代码"
    )

    # ========== 推荐字段（有默认值） ==========
    template_type: TemplateType = Field(
        default=TemplateType.BUSINESS,
        description="模板类型"
    )

    scene: Scene = Field(
        default=Scene.BUSINESS_REPORT,
        description="使用场景"
    )

    tone: Tone = Field(
        default=Tone.PROFESSIONAL,
        description="语调风格"
    )

    core_modules: List[str] = Field(
        default_factory=list,
        description="核心模块列表",
        max_length=10
    )

    # ========== 可选字段 ==========
    need_research: bool = Field(
        default=False,
        description="是否需要研究"
    )

    color_scheme: Optional[str] = Field(
        default=None,
        description="色彩方案"
    )

    target_audience: Optional[str] = Field(
        default=None,
        description="目标受众"
    )

    # ========== 验证器 ==========
    @field_validator('ppt_topic')
    @classmethod
    def topic_not_empty(cls, v: str) -> str:
        """验证主题不能为空或只有空格"""
        if not v or not v.strip():
            raise ValueError('主题不能为空')
        return v.strip()

    # ========== 配置 ==========
    model_config = ConfigDict(
        use_enum_values=True,  # 返回枚举值而非枚举对象
        extra="forbid"         # 拒绝额外字段（捕获LLM幻觉）
    )
