#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
技能框架 - 装饰器模块

此模块提供 @Skill 装饰器，用于将 Python 类标记为技能。
"""

from typing import Callable, Type, Any, List, Dict, Optional
from functools import wraps

from .skill_metadata import SkillMetadata, SkillCategory

def Skill(
    name: str,
    version: str = "1.0.0",
    category: str = "utility",
    tags: Optional[List[str]] = None,
    description: str = "",
    enabled: bool = True,
    author: Optional[str] = None,
    dependencies: Optional[List[str]] = None,
):
    """
    装饰器，用于将 Python 类标记为技能。

    被装饰的类将附加一个 __skill_metadata__ 属性，
    包含 SkillMetadata 实例。

    使用方法:
        @Skill(
            name="DocumentSearch",
            version="1.0.0",
            category="document",
            tags=["search", "document"],
            description="按关键词搜索文档"
        )
        class DocumentSearchSkill:
            async def search(self, keyword: str, tool_context) -> str:
                # 实现
                return results

    Args:
        name: 技能的显示名称
        version: 语义版本字符串
        category: 来自 SkillCategory 枚举值的类别
        tags: 用于过滤的标签列表
        description: 人类可读的描述
        enabled: 默认情况下是否启用技能
        author: 可选的作者名称
        dependencies: 此技能依赖的 skill_ids 列表
    """

    def decorator(cls: Type) -> Type:
        # 将类别字符串转换为枚举
        try:
            category_enum = SkillCategory(category)
        except ValueError:
            # 如果类别无效，默认使用 UTILITY
            category_enum = SkillCategory.UTILITY

        # 创建元数据
        metadata = SkillMetadata(
            skill_id=name.lower().replace(" ", "_"),
            name=name,
            version=version,
            category=category_enum,
            tags=tags or [],
            description=description,
            enabled=enabled,
            author=author,
            dependencies=dependencies or [],
        )

        # 将元数据附加到类
        cls.__skill_metadata__ = metadata

        # 也添加一个类方法来获取元数据
        if not hasattr(cls, "get_skill_metadata"):

            def get_skill_metadata(cls) -> SkillMetadata:
                return cls.__skill_metadata__

            cls.get_skill_metadata = classmethod(get_skill_metadata)

        return cls

    return decorator

def SkillMethod(
    description: str = "",
    parameters: Optional[Dict[str, Any]] = None,
    examples: Optional[List[Dict[str, Any]]] = None,
):
    """
    装饰器，为技能中的特定方法添加元数据。

    这是可选的，但为方法提供额外文档。

    使用方法:
        @Skill(name="MySkill", ...)
        class MySkill:
            @SkillMethod(
                description="搜索文档",
                parameters={
                    "keyword": {"type": "string", "description": "搜索关键词"},
                    "number": {"type": "integer", "description": "结果数量"}
                }
            )
            async def search(self, keyword: str, number: int, tool_context) -> str:
                # 实现
                pass

    Args:
        description: 此方法功能的描述
        parameters: 参数的模式字典
        examples: 使用示例列表
    """

    def decorator(func: Callable) -> Callable:
        # 将元数据存储为函数属性
        func.__skill_method_metadata__ = {
            "description": description,
            "parameters": parameters or {},
            "examples": examples or [],
        }

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # 将元数据复制到包装器
        wrapper.__skill_method_metadata__ = func.__skill_method_metadata__

        return wrapper

    return decorator
