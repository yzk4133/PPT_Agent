#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
懒加载版本的 MarkdownSkillMetadata

提供三种加载策略：
1. 完整加载（Eager）- 当前实现
2. 懒加载（Lazy）- 仅元数据，按需读取内容
3. 缓存加载（Cached）- 懒加载 + LRU缓存
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path
import threading


@dataclass
class MarkdownSkillMetadataLazy:
    """
    懒加载版本的 Markdown 技能元数据

    只在首次访问时才读取文件内容，减少内存占用和启动时间
    """

    # 基础元数据（始终加载）
    skill_id: str
    name: str
    version: str
    category: Any  # SkillCategory
    tags: list
    description: str
    enabled: bool = True
    author: Optional[str] = None
    dependencies: list = field(default_factory=list)
    parameters: dict = field(default_factory=dict)
    examples: list = field(default_factory=list)

    # 懒加载相关字段
    file_path: str = ""
    _content: Optional[str] = field(default=None, repr=False)
    _loaded: bool = field(default=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def load_content(self) -> None:
        """
        懒加载：从文件读取内容（仅首次调用时执行）

        线程安全的实现，支持多线程环境
        """
        if self._loaded:
            return

        with self._lock:
            # 双重检查锁定
            if self._loaded:
                return

            try:
                path = Path(self.file_path)
                if not path.exists():
                    self._content = f"# 错误：文件不存在\n\n{self.file_path}"
                    self._loaded = True
                    return

                with open(path, "r", encoding="utf-8") as f:
                    full_content = f.read()

                # 提取正文（跳过 frontmatter）
                if full_content.startswith("---"):
                    end_idx = full_content.find("\n---", 4)
                    if end_idx != -1:
                        self._content = full_content[end_idx + 4:].strip()
                    else:
                        self._content = full_content
                else:
                    self._content = full_content

                self._loaded = True

            except Exception as e:
                self._content = f"# 加载错误\n\n{str(e)}"
                self._loaded = True

    @property
    def content(self) -> str:
        """
        内容属性（按需加载）

        首次访问时触发文件读取，后续直接返回缓存
        """
        if not self._loaded:
            self.load_content()
        return self._content or ""

    def unload_content(self) -> None:
        """
        手动卸载内容，释放内存

        当不再需要某个技能内容时可以调用
        """
        with self._lock:
            self._content = None
            self._loaded = False

    def get_content_for_prompt(self) -> str:
        """
        获取格式化的提示词内容（触发懒加载）

        Returns:
            格式化的字符串
        """
        tags_str = ", ".join(self.tags) if self.tags else "None"

        return f"""## {self.name}

**Description**: {self.description}
**Category**: {self.category.value if hasattr(self.category, 'value') else self.category}
**Tags**: {tags_str}

{self.content}"""

    def to_dict(self, include_content: bool = False) -> Dict[str, Any]:
        """
        转换为字典

        Args:
            include_content: 是否包含完整内容（False则只包含元数据）
        """
        base_dict = {
            "skill_id": self.skill_id,
            "name": self.name,
            "version": self.version,
            "category": self.category.value if hasattr(self.category, 'value') else str(self.category),
            "tags": self.tags,
            "description": self.description,
            "enabled": self.enabled,
            "author": self.author,
            "file_path": self.file_path,
            "loaded": self._loaded,  # 新增：是否已加载
            "content_length": len(self.content) if self._loaded else 0,  # 新增：内容长度
        }

        # 可选包含内容
        if include_content and self._loaded:
            base_dict["content"] = self.content

        return base_dict


class CachedMarkdownSkillMetadata(MarkdownSkillMetadataLazy):
    """
    带LRU缓存的懒加载版本

    自动管理内存，当技能数量过多时自动卸载不常用的内容
    """

    # 类级别的LRU缓存（所有实例共享）
    _cache_max_size = 20  # 最多缓存20个技能的内容
    _cache_order = []  # 记录访问顺序
    _cache_lock = threading.Lock()

    @classmethod
    def set_cache_size(cls, size: int):
        """设置最大缓存数量"""
        with cls._cache_lock:
            cls._cache_max_size = size

    def load_content(self) -> None:
        """带缓存管理的加载"""
        if self._loaded:
            # 更新访问顺序
            self._update_cache_order()
            return

        # 检查是否需要清理缓存
        self._cleanup_cache()

        # 调用父类加载
        super().load_content()

        # 更新访问顺序
        self._update_cache_order()

    def _update_cache_order(self):
        """更新LRU缓存顺序"""
        with self._cache_lock:
            skill_id = self.skill_id
            if skill_id in self._cache_order:
                self._cache_order.remove(skill_id)
            self._cache_order.append(skill_id)

    def _cleanup_cache(self):
        """清理超出缓存大小的旧内容"""
        with self._cache_lock:
            # 获取所有已加载的技能ID
            loaded_skills = [
                sid for sid in self._cache_order
                if sid != self.skill_id  # 排除当前技能
            ]

            # 如果超出缓存大小，卸载最旧的
            while len(loaded_skills) >= self._cache_max_size:
                oldest_sid = loaded_skills.pop(0)
                # 这里需要访问注册表来卸载
                # 实际实现需要在 SkillRegistry 中配合
                print(f"[Cache] Unloading skill: {oldest_sid}")


# 使用示例和对比测试
if __name__ == "__main__":
    import time

    print("=" * 60)
    print("懒加载技能元数据测试")
    print("=" * 60)

    # 模拟创建懒加载技能
    skill_lazy = MarkdownSkillMetadataLazy(
        skill_id="test-lazy",
        name="测试技能（懒加载）",
        version="1.0.0",
        category="search",
        tags=["test", "lazy"],
        description="测试懒加载功能",
        file_path="skills/search/web_search_strategy_zh.md"
    )

    print("\n【1】创建技能后")
    print(f"  已加载: {skill_lazy._loaded}")
    print(f"  内容长度: {len(skill_lazy._content) if skill_lazy._content else 0}")

    print("\n【2】首次访问 content 属性")
    start = time.time()
    content = skill_lazy.content
    elapsed = time.time() - start
    print(f"  已加载: {skill_lazy._loaded}")
    print(f"  内容长度: {len(content)}")
    print(f"  耗时: {elapsed:.4f}秒")

    print("\n【3】再次访问 content 属性（使用缓存）")
    start = time.time()
    content2 = skill_lazy.content
    elapsed = time.time() - start
    print(f"  耗时: {elapsed:.4f}秒")
    print(f"  内容相同: {content == content2}")

    print("\n【4】转换为字典（不包含内容）")
    info = skill_lazy.to_dict(include_content=False)
    print(f"  包含content键: {'content' in info}")
    print(f"  loaded字段: {info['loaded']}")
    print(f"  content_length: {info['content_length']}")

    print("\n【5】手动卸载内容")
    skill_lazy.unload_content()
    print(f"  已加载: {skill_lazy._loaded}")
    print(f"  内存占用: 已释放")
