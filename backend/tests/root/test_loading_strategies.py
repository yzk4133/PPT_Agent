#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
技能加载策略对比测试

对比三种加载策略的性能和内存占用：
1. 完整加载（Eager）- 当前实现
2. 懒加载（Lazy）- 仅元数据，按需读取
3. 混合策略 - 小文件完整加载，大文件懒加载
"""

import sys
import os
import time
import tracemalloc
from pathlib import Path
from typing import Dict, List, Any

# 添加backend到路径
sys.path.insert(0, os.path.dirname(__file__))

from skill_framework.core.skill_metadata import MarkdownSkillMetadata, SkillCategory
from skill_framework.core.skill_metadata_lazy import MarkdownSkillMetadataLazy
from skill_framework.core.skill_loaders import MarkdownSkillLoader


class EagerMarkdownSkillLoader(MarkdownSkillLoader):
    """完整加载器（当前实现）"""

    def load_from_file(self, file_path: Path) -> Any:
        """完整加载：读取所有内容到内存"""
        parsed = self._parse_frontmatter(file_path)
        if not parsed:
            return None

        frontmatter = parsed["frontmatter"]
        content = parsed["content"]

        # 转换category为枚举
        category_str = frontmatter.get("category", "utility")
        try:
            category = SkillCategory(category_str)
        except ValueError:
            category = SkillCategory.UTILITY

        return MarkdownSkillMetadata(
            skill_id=frontmatter["skill_id"],
            name=frontmatter["name"],
            version=frontmatter.get("version", "1.0.0"),
            category=category,
            tags=frontmatter.get("tags", []),
            description=frontmatter.get("description", ""),
            enabled=frontmatter.get("enabled", True),
            author=frontmatter.get("author"),
            dependencies=frontmatter.get("dependencies", []),
            parameters=frontmatter.get("parameters", {}),
            examples=frontmatter.get("examples", []),
            content=content,  # 完整内容立即加载
            file_path=str(file_path),
        )


class LazyMarkdownSkillLoader(MarkdownSkillLoader):
    """懒加载器：仅元数据，内容按需加载"""

    def load_from_file(self, file_path: Path) -> Any:
        """懒加载：只存储路径，不读取内容"""
        parsed = self._parse_frontmatter(file_path)
        if not parsed:
            return None

        frontmatter = parsed["frontmatter"]

        # 转换category为枚举
        category_str = frontmatter.get("category", "utility")
        try:
            category = SkillCategory(category_str)
        except ValueError:
            category = SkillCategory.UTILITY

        # 不读取content，只存储file_path
        return MarkdownSkillMetadataLazy(
            skill_id=frontmatter["skill_id"],
            name=frontmatter["name"],
            version=frontmatter.get("version", "1.0.0"),
            category=category,
            tags=frontmatter.get("tags", []),
            description=frontmatter.get("description", ""),
            enabled=frontmatter.get("enabled", True),
            author=frontmatter.get("author"),
            dependencies=frontmatter.get("dependencies", []),
            parameters=frontmatter.get("parameters", {}),
            examples=frontmatter.get("examples", []),
            file_path=str(file_path),  # 只存储路径
            _content=None,  # 不加载内容
            _loaded=False,
        )


class HybridMarkdownSkillLoader(MarkdownSkillLoader):
    """混合加载器：小文件完整加载，大文件懒加载"""

    # 小文件阈值（字符数）
    SMALL_FILE_THRESHOLD = 3000

    def load_from_file(self, file_path: Path) -> Any:
        """混合加载：根据文件大小决定策略"""
        parsed = self._parse_frontmatter(file_path)
        if not parsed:
            return None

        frontmatter = parsed["frontmatter"]
        content = parsed["content"]
        content_size = len(content)

        # 转换category为枚举
        category_str = frontmatter.get("category", "utility")
        try:
            category = SkillCategory(category_str)
        except ValueError:
            category = SkillCategory.UTILITY

        frontmatter_common = {
            "skill_id": frontmatter["skill_id"],
            "name": frontmatter["name"],
            "version": frontmatter.get("version", "1.0.0"),
            "category": category,
            "tags": frontmatter.get("tags", []),
            "description": frontmatter.get("description", ""),
            "enabled": frontmatter.get("enabled", True),
            "author": frontmatter.get("author"),
            "dependencies": frontmatter.get("dependencies", []),
            "parameters": frontmatter.get("parameters", {}),
            "examples": frontmatter.get("examples", []),
            "file_path": str(file_path),
        }

        # 小文件：完整加载
        if content_size <= self.SMALL_FILE_THRESHOLD:
            return MarkdownSkillMetadata(
                **frontmatter_common,
                content=content,  # 立即加载
            )
        # 大文件：懒加载
        else:
            return MarkdownSkillMetadataLazy(
                **frontmatter_common,
                _content=None,
                _loaded=False,
            )


def measure_performance(
    loader_class,
    loader_name: str,
    skill_directories: List[str],
    access_content: bool = True
) -> Dict[str, Any]:
    """
    测量加载性能

    Args:
        loader_class: 加载器类
        loader_name: 加载器名称
        skill_directories: 技能目录列表
        access_content: 是否访问content（模拟实际使用）

    Returns:
        性能指标字典
    """
    print(f"\n{'=' * 60}")
    print(f"测试策略: {loader_name}")
    print(f"{'=' * 60}")

    # 开始内存跟踪
    tracemalloc.start()
    start_time = time.time()

    # 加载所有技能
    loader = loader_class(skill_directories)
    files = loader.discover_files()
    skills = []

    for file_path in files:
        skill = loader.load_from_file(file_path)
        if skill:
            skills.append(skill)

    load_time = time.time() - start_time
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"✓ 加载技能数: {len(skills)}")
    print(f"✓ 加载时间: {load_time:.4f}秒")
    print(f"✓ 当前内存: {current_mem / 1024:.2f} KB")
    print(f"✓ 峰值内存: {peak_mem / 1024:.2f} KB")

    # 模拟使用：访问内容
    if access_content:
        print(f"\n→ 模拟使用：访问所有技能内容...")

        tracemalloc.start()
        start_time = time.time()

        total_content_length = 0
        for skill in skills:
            content = skill.get_content_for_prompt()
            total_content_length += len(content)

        access_time = time.time() - start_time
        current_mem2, peak_mem2 = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"✓ 访问时间: {access_time:.4f}秒")
        print(f"✓ 内容总长度: {total_content_length:,} 字符")
        print(f"✓ 访问后内存: {current_mem2 / 1024:.2f} KB")
        print(f"✓ 访问后峰值: {peak_mem2 / 1024:.2f} KB")

        return {
            "strategy": loader_name,
            "skills_count": len(skills),
            "load_time": load_time,
            "load_memory_kb": peak_mem / 1024,
            "access_time": access_time,
            "access_memory_kb": peak_mem2 / 1024,
            "total_content_length": total_content_length,
        }
    else:
        return {
            "strategy": loader_name,
            "skills_count": len(skills),
            "load_time": load_time,
            "load_memory_kb": peak_mem / 1024,
        }


def main():
    """主测试函数"""
    print("=" * 60)
    print("技能加载策略性能对比测试")
    print("=" * 60)

    # 技能目录
    skill_dirs = [
        "skills/search",
        "skills/document",
        "skills/generation"
    ]

    results = []

    # 测试1：完整加载（当前实现）
    result_eager = measure_performance(
        EagerMarkdownSkillLoader,
        "完整加载（Eager Loading）",
        skill_dirs,
        access_content=True
    )
    results.append(result_eager)

    # 测试2：懒加载
    result_lazy = measure_performance(
        LazyMarkdownSkillLoader,
        "懒加载（Lazy Loading）",
        skill_dirs,
        access_content=True
    )
    results.append(result_lazy)

    # 测试3：混合加载
    result_hybrid = measure_performance(
        HybridMarkdownSkillLoader,
        "混合加载（Hybrid，阈值3KB）",
        skill_dirs,
        access_content=True
    )
    results.append(result_hybrid)

    # 对比总结
    print("\n" + "=" * 60)
    print("性能对比总结")
    print("=" * 60)

    print(f"\n{'策略':<25} {'加载时间':<12} {'加载内存':<12} {'访问时间':<12} {'访问后内存':<12}")
    print("-" * 73)

    for r in results:
        print(f"{r['strategy']:<25} "
              f"{r['load_time']:.4f}s      "
              f"{r['load_memory_kb']:>7.1f} KB   "
              f"{r['access_time']:.4f}s      "
              f"{r['access_memory_kb']:>7.1f} KB")

    # 计算提升百分比
    eager = results[0]
    lazy = results[1]

    load_time_improvement = ((eager['load_time'] - lazy['load_time']) / eager['load_time']) * 100
    load_mem_improvement = ((eager['load_memory_kb'] - lazy['load_memory_kb']) / eager['load_memory_kb']) * 100

    print("\n" + "=" * 60)
    print("懒加载 vs 完整加载")
    print("=" * 60)
    print(f"启动时间节省: {load_time_improvement:.1f}%")
    print(f"启动内存节省: {load_mem_improvement:.1f}%")
    print(f"首次访问延迟: +{lazy['access_time'] - eager['access_time']:.4f}秒")

    # 建议
    print("\n" + "=" * 60)
    print("实施建议")
    print("=" * 60)

    skill_count = eager['skills_count']
    avg_size = eager['total_content_length'] / skill_count

    print(f"\n当前项目情况：")
    print(f"  • 技能数量: {skill_count}")
    print(f"  • 平均大小: {avg_size:.0f} 字符")
    print(f"  • 总内容量: {eager['total_content_length']:,} 字符 ({eager['total_content_length']/1024:.1f} KB)")

    print(f"\n推荐策略：")

    if skill_count < 10 and avg_size < 5000:
        print(f"  ✓ 使用【完整加载】")
        print(f"    理由：技能数量少，内容小，完整加载响应最快")
    elif skill_count < 30 and avg_size < 10000:
        print(f"  ✓ 使用【混合加载】（阈值建议：5KB）")
        print(f"    理由：平衡内存和速度，小技能快速访问，大技能按需加载")
    else:
        print(f"  ✓ 使用【懒加载 + 缓存】")
        print(f"    理由：技能数量多或内容大，懒加载可显著减少内存占用")

    print(f"\n迁移步骤：")
    print(f"  1. 在 skill_metadata.py 中添加 content 属性的懒加载逻辑")
    print(f"  2. 修改 MarkdownSkillLoader.load_from_file() 不立即读取content")
    print(f"  3. 保持 API 不变，向后兼容现有代码")


if __name__ == "__main__":
    # 设置输出编码
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')

    try:
        main()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
