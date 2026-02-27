"""
Markdown Skill - 解析 MD 文件并封装为 LangChain Tool

用于将 MD Skills (content_prompts.md 等) 解析为可用的 LangChain Tools
"""

from pathlib import Path
from typing import Dict, Optional
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
import logging
import yaml
import re

logger = logging.getLogger(__name__)


class MarkdownSkill:
    """
    Markdown Skill 解析器

    职责：
    - 解析 MD 文件的 frontmatter (YAML)
    - 提取 Level 1/2/3 内容
    - 提供内容访问接口
    """

    def __init__(self, file_path: Path):
        """
        初始化 Markdown Skill

        Args:
            file_path: MD 文件路径
        """
        self.file_path = file_path
        self.metadata: Dict = {}
        self.levels: Dict[int, str] = {}
        self._load()

    def _load(self):
        """解析 MD 文件"""
        try:
            content = self.file_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"[MarkdownSkill] Failed to read {self.file_path}: {e}")
            raise

        # 提取 frontmatter
        if content.startswith('---'):
            end_idx = content.find('---', 3)
            if end_idx != -1:
                frontmatter_text = content[3:end_idx].strip()
                try:
                    self.metadata = yaml.safe_load(frontmatter_text) or {}
                except yaml.YAMLError as e:
                    logger.warning(f"[MarkdownSkill] Failed to parse frontmatter: {e}")
                    self.metadata = {}
                body_content = content[end_idx+3:].strip()
            else:
                body_content = content
        else:
            body_content = content

        # 解析层级
        self._parse_levels(body_content)

    def _parse_levels(self, content: str):
        """
        提取 Level 1/2/3 内容

        支持格式:
        ## Level 1: 快速指南
        或
        ## Level 1：快速指南
        """
        pattern = r'##+\s*Level\s+(\d+)[:：]\s*(.+)'

        current_level = None
        current_content = []

        for line in content.split('\n'):
            match = re.match(pattern, line)
            if match:
                # 保存上一级内容
                if current_level is not None:
                    self.levels[current_level] = '\n'.join(current_content).strip()

                # 开始新级别
                current_level = int(match.group(1))
                current_content = [line]
            else:
                if current_level is not None:
                    current_content.append(line)

        # 保存最后一级
        if current_level is not None:
            self.levels[current_level] = '\n'.join(current_content).strip()

    def get_content(self, level: int = 1) -> str:
        """
        获取指定 level 的内容

        Args:
            level: 层级 (1, 2, 3)

        Returns:
            该层级的内容字符串
        """
        return self.levels.get(level, self.levels.get(1, ""))

    def get_progressive_content(self, max_level: int = 1) -> str:
        """
        获取渐进式内容（包含所有较低级别）

        Args:
            max_level: 最高层级

        Returns:
            所有级别的内容，用 --- 分隔
        """
        sections = []
        for lvl in sorted(self.levels.keys()):
            if lvl > max_level:
                break
            sections.append(self.levels[lvl])
        return '\n\n---\n\n'.join(sections)

    @property
    def name(self) -> str:
        """Skill 名称（从 frontmatter 或文件名）"""
        return self.metadata.get('name', self.file_path.stem)

    @property
    def description(self) -> str:
        """Skill 描述（从 frontmatter）"""
        return self.metadata.get('description', '')

    @property
    def category(self) -> str:
        """Skill 分类（从 frontmatter）"""
        return self.metadata.get('category', 'general')

    @property
    def version(self) -> str:
        """Skill 版本（从 frontmatter）"""
        return self.metadata.get('version', '1.0.0')


def create_md_skill_tool(md_skill: MarkdownSkill) -> StructuredTool:
    """
    将 MD Skill 封装为 LangChain Tool

    核心逻辑：创建一个函数，调用 md_skill.get_progressive_content()

    Args:
        md_skill: MarkdownSkill 实例

    Returns:
        LangChain StructuredTool
    """
    def md_skill_function(
        level: int = 1,
        progressive: bool = True
    ) -> str:
        """
        获取分层指南内容

        Args:
            level: 详细程度（1=快速, 2=详细, 3=高级）
            progressive: 是否包含所有较低级别

        Returns:
            str: 纯文本格式的指南
        """
        try:
            if progressive:
                return md_skill.get_progressive_content(max_level=level)
            else:
                return md_skill.get_content(level=level)
        except Exception as e:
            logger.error(f"[MDSkillTool] Failed to get content: {e}")
            return f"Error: {str(e)}"

    # 创建 Tool 描述
    tool_description = f"""{md_skill.description}

这是一个分层指南工具，提供不同详细程度的指导。

**使用场景**：当你需要参考最佳实践、工作流程或详细指导时

**级别说明**：
- level=1: 快速指南（简洁的步骤清单）
- level=2: 详细指南（完整的参数说明和示例）
- level=3: 高级技巧（深入的优化策略）

**建议**：
- 首次使用：level=1
- 遇到问题：level=2
- 仍需帮助：level=3
"""

    # 创建参数 Schema
    class MdSkillInput(BaseModel):
        level: int = Field(
            default=1,
            ge=1,
            le=3,
            description="详细程度（1=快速, 2=详细, 3=高级）"
        )
        progressive: bool = Field(
            default=True,
            description="是否包含所有较低级别的内容（推荐True）"
        )

    # 封装为 Tool
    return StructuredTool.from_function(
        func=md_skill_function,
        name=md_skill.name,
        description=tool_description,
        args_schema=MdSkillInput
    )
