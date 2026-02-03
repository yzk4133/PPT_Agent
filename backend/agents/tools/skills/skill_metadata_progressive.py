#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
渐进式加载元数据 - 用于上下文工程优化

核心思想：
1. 初始system prompt：只注入简洁的工具描述（元数据）
2. Agent决定使用某个skill时：动态加载完整skill内容

这样可以：
- 大幅减少初始system prompt的token消耗
- 只在真正需要时才加载详细内容
- 保持Agent的工具发现能力
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
import threading


@dataclass
class ProgressiveSkillMetadata:
    """
    渐进式加载的技能元数据

    支持三种级别的描述：
    1. 简洁描述（Minimal）- 用于初始system prompt
    2. 标准描述（Standard）- 用于工具选择
    3. 完整内容（Full）- 用于实际执行时注入
    """

    # ===== 基础元数据（始终加载） =====
    skill_id: str
    name: str
    version: str
    category: Any
    tags: List[str]
    description: str  # 简洁的一行描述
    enabled: bool = True
    author: Optional[str] = None
    file_path: str = ""

    # ===== 工具定义（用于function calling） =====
    parameters: Optional[Dict[str, Any]] = None  # 参数schema（如果有）
    examples: List[Dict[str, Any]] = field(default_factory=list)

    # ===== 懒加载的完整内容 =====
    _full_content: Optional[str] = field(default=None, repr=False)
    _content_loaded: bool = field(default=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    # ===== 缓存的描述文本 =====
    _minimal_description: Optional[str] = field(default=None, repr=False)
    _standard_description: Optional[str] = field(default=None, repr=False)

    def get_minimal_description(self) -> str:
        """
        获取最小化描述（用于初始system prompt）

        格式：
        - 工具ID: web-search-strategy
        - 名称: WebSearchStrategy
        - 描述: 网络搜索最佳实践

        Token消耗: ~10-15 tokens
        """
        if self._minimal_description is None:
            self._minimal_description = (
                f"- {self.name} ({self.skill_id}): {self.description}"
            )
        return self._minimal_description

    def get_standard_description(self) -> str:
        """
        获取标准描述（用于工具选择阶段）

        格式：
        ## WebSearchStrategy (web-search-strategy)
        **Category**: search
        **Tags**: web, search, strategy
        **Description**: 网络搜索最佳实践和方法论

        Token消耗: ~30-50 tokens
        """
        if self._standard_description is None:
            tags_str = ", ".join(self.tags) if self.tags else "None"
            category_str = self.category.value if hasattr(self.category, 'value') else str(self.category)

            self._standard_description = f"""## {self.name} ({self.skill_id})
**Category**: {category_str}
**Tags**: {tags_str}
**Description**: {self.description}"""
        return self._standard_description

    def get_full_content(self) -> str:
        """
        获取完整内容（用于实际执行时注入）

        包含完整的文档正文

        Token消耗: ~500-2000 tokens（取决于文档大小）
        """
        if not self._content_loaded:
            self._load_full_content()

        if self._full_content is None:
            return ""

        tags_str = ", ".join(self.tags) if self.tags else "None"
        category_str = self.category.value if hasattr(self.category, 'value') else str(self.category)

        return f"""## {self.name}

**Description**: {self.description}
**Category**: {category_str}
**Tags**: {tags_str}

{self._full_content}"""

    def _load_full_content(self) -> None:
        """懒加载：从文件读取完整内容"""
        if self._content_loaded:
            return

        with self._lock:
            # 双重检查锁定
            if self._content_loaded:
                return

            try:
                path = Path(self.file_path)
                if not path.exists():
                    self._full_content = f"# 错误：文件不存在\n\n{self.file_path}"
                    self._content_loaded = True
                    return

                with open(path, "r", encoding="utf-8") as f:
                    full_content = f.read()

                # 提取正文（跳过frontmatter）
                if full_content.startswith("---"):
                    end_idx = full_content.find("\n---", 4)
                    if end_idx != -1:
                        self._full_content = full_content[end_idx + 4:].strip()
                    else:
                        self._full_content = full_content
                else:
                    self._full_content = full_content

                self._content_loaded = True

            except Exception as e:
                self._full_content = f"# 加载错误\n\n{str(e)}"
                self._content_loaded = True

    def unload_content(self) -> None:
        """卸载完整内容，释放内存"""
        with self._lock:
            self._full_content = None
            self._content_loaded = False

    def to_tool_definition(self) -> Dict[str, Any]:
        """
        转换为工具定义（用于function calling）

        返回类似ADK工具定义的格式
        """
        return {
            "name": self.skill_id,
            "description": self.description,
            "parameters": self.parameters or {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }

    def get_token_estimate(self) -> Dict[str, int]:
        """
        估算各阶段的token消耗

        Returns:
            {
                "minimal": 10-15 tokens,
                "standard": 30-50 tokens,
                "full": 500-2000 tokens
            }
        """
        minimal_len = len(self.get_minimal_description())
        standard_len = len(self.get_standard_description())

        # 粗略估算：1 token ≈ 4 characters (英文) 或 2 characters (中文)
        full_len = len(self._full_content) if self._content_loaded else 0

        return {
            "minimal": minimal_len // 3,  # 粗略估计
            "standard": standard_len // 3,
            "full": full_len // 3,
            "minimal_chars": minimal_len,
            "standard_chars": standard_len,
            "full_chars": full_len,
        }


class ProgressiveSkillRegistry:
    """
    渐进式技能注册表

    管理技能的分阶段加载和注入
    """

    def __init__(self):
        self._skills: Dict[str, ProgressiveSkillMetadata] = {}

    def register(self, metadata: ProgressiveSkillMetadata) -> None:
        """注册技能"""
        skill_id = metadata.skill_id
        self._skills[skill_id] = metadata

    def get_minimal_prompt(self, skill_ids: Optional[List[str]] = None) -> str:
        """
        获取最小化system prompt

        用于Agent初始化，只包含工具列表
        """
        skills = self._filter_skills(skill_ids)

        sections = []
        for skill in skills:
            sections.append(skill.get_minimal_description())

        if not sections:
            return ""

        return """# 可用工具列表

你可以使用以下知识库和技能：
""" + "\n".join(sections)

    def get_standard_prompt(self, skill_ids: Optional[List[str]] = None) -> str:
        """
        获取标准描述prompt

        用于工具选择阶段，包含更多细节
        """
        skills = self._filter_skills(skill_ids)

        sections = []
        for skill in skills:
            sections.append(skill.get_standard_description())

        if not sections:
            return ""

        return """# 可用工具详细描述

以下是你可以使用的知识库和技能的详细描述：
""" + "\n\n---\n\n".join(sections)

    def get_full_content_for_skill(self, skill_id: str) -> str:
        """
        获取单个技能的完整内容

        当Agent决定使用某个技能时调用
        """
        if skill_id not in self._skills:
            return f"# 错误：技能 {skill_id} 不存在"

        skill = self._skills[skill_id]
        return skill.get_full_content()

    def get_token_estimate(self, skill_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        估算token消耗

        Args:
            skill_ids: 要计算的技能ID列表（None表示全部）

        Returns:
            {
                "minimal": int,  # 最小模式token数
                "standard": int,  # 标准模式token数
                "full": int,  # 完整模式token数
                "by_skill": {...}  # 各技能的token估算
            }
        """
        skills = self._filter_skills(skill_ids)

        minimal_total = 0
        standard_total = 0
        full_total = 0
        by_skill = {}

        for skill in skills:
            estimate = skill.get_token_estimate()
            by_skill[skill.skill_id] = estimate
            minimal_total += estimate["minimal"]
            standard_total += estimate["standard"]
            full_total += estimate["full"]

        return {
            "minimal": minimal_total,
            "standard": standard_total,
            "full": full_total,
            "by_skill": by_skill,
        }

    def _filter_skills(self, skill_ids: Optional[List[str]]) -> List[ProgressiveSkillMetadata]:
        """过滤技能列表"""
        if skill_ids is None:
            return list(self._skills.values())

        return [self._skills[sid] for sid in skill_ids if sid in self._skills]


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("渐进式加载示例 - 上下文工程优化")
    print("=" * 60)

    # 创建示例技能
    skill1 = ProgressiveSkillMetadata(
        skill_id="web-search-strategy-zh",
        name="网络搜索策略指南",
        version="1.0.0",
        category="search",
        tags=["web", "search", "strategy"],
        description="高效信息检索的网络搜索最佳实践和方法论",
        file_path="skills/search/web_search_strategy_zh.md",
    )

    skill2 = ProgressiveSkillMetadata(
        skill_id="research-guide-zh",
        name="研究方法指南",
        version="1.0.0",
        category="document",
        tags=["research", "methodology"],
        description="系统性研究的综合方法论指南",
        file_path="skills/document/research_guide_zh.md",
    )

    # 注册到注册表
    registry = ProgressiveSkillRegistry()
    registry.register(skill1)
    registry.register(skill2)

    print("\n【1】最小化prompt（用于初始system prompt）")
    print("-" * 60)
    minimal = registry.get_minimal_prompt()
    print(minimal)
    print(f"\nToken估算: ~{len(minimal)//3} tokens")

    print("\n【2】标准描述prompt（用于工具选择）")
    print("-" * 60)
    standard = registry.get_standard_prompt()
    print(standard[:400] + "..." if len(standard) > 400 else standard)
    print(f"\nToken估算: ~{len(standard)//3} tokens")

    print("\n【3】完整内容（按需加载）")
    print("-" * 60)
    full = registry.get_full_content_for_skill("web-search-strategy-zh")
    print(full[:300] + "..." if len(full) > 300 else full)
    print(f"\nToken估算: ~{len(full)//3} tokens")

    print("\n【4】Token消耗对比")
    print("-" * 60)
    estimate = registry.get_token_estimate()
    print(f"最小模式（初始加载）:  ~{estimate['minimal']} tokens")
    print(f"标准模式（工具选择）:  ~{estimate['standard']} tokens")
    print(f"完整模式（执行时）:    ~{estimate['full']} tokens")
    print(f"\n节省比例: {((estimate['full'] - estimate['minimal']) / estimate['full'] * 100):.1f}%")

    print("\n【5】按技能详细估算")
    print("-" * 60)
    for skill_id, est in estimate['by_skill'].items():
        print(f"\n{skill_id}:")
        print(f"  最小: ~{est['minimal']} tokens")
        print(f"  标准: ~{est['standard']} tokens")
        print(f"  完整: ~{est['full']} tokens")
