"""
Skills 基类

定义所有 Skills 的通用接口和基础功能
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging


logger = logging.getLogger(__name__)


class BaseSkill(ABC):
    """Skill 基类"""

    # Skill 元数据（子类必须定义）
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    category: str = "general"

    def __init__(self, llm=None):
        """
        初始化 Skill

        Args:
            llm: LLM 实例（可选）
        """
        self.llm = llm
        self._validate_metadata()

    def _validate_metadata(self):
        """验证元数据是否完整"""
        if not self.name:
            raise ValueError(f"{self.__class__.__name__} 必须定义 name 属性")
        if not self.description:
            raise ValueError(f"{self.__class__.__name__} 必须定义 description 属性")

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """
        执行 Skill 的主要逻辑

        Args:
            **kwargs: Skill 参数

        Returns:
            str: LLM 可直接理解和使用的字符串
        """
        pass

    def get_metadata(self) -> Dict[str, str]:
        """获取 Skill 元数据"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": self.category,
            "class": self.__class__.__name__
        }

    def __repr__(self) -> str:
        return f"<Skill {self.name} v{self.version}>"


class CompositeSkill(BaseSkill):
    """
    组合 Skill

    将多个 Skills 组合成一个工作流程
    """

    def __init__(self, skills: list, llm=None):
        """
        初始化组合 Skill

        Args:
            skills: 子 Skill 列表
            llm: LLM 实例
        """
        super().__init__(llm)
        self.skills = skills

        # 组合描述
        skill_names = [s.name for s in skills]
        self.name = f"composite_{'_'.join(skill_names)}"
        self.description = f"组合 Skill: {' → '.join(skill_names)}"
        self.category = "composite"

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        依次执行所有子 Skills

        Args:
            **kwargs: 传递给第一个 Skill 的参数

        Returns:
            所有 Skills 的执行结果列表
        """
        results = []
        current_input = kwargs

        for i, skill in enumerate(self.skills):
            logger.info(f"[CompositeSkill] 执行第 {i+1}/{len(self.skills)} 个 Skill: {skill.name}")

            result = await skill.execute(**current_input)

            if not result.get("success"):
                return {
                    "success": False,
                    "error": f"Skill {skill.name} 执行失败: {result.get('error')}",
                    "failed_at": i,
                    "partial_results": results
                }

            results.append(result)
            # 将当前 Skill 的输出传递给下一个
            current_input = result.get("data", {})

        return {
            "success": True,
            "data": {
                "final_output": current_input,
                "all_results": results
            }
        }


class SkillExecutionError(Exception):
    """Skill 执行异常"""
    pass
