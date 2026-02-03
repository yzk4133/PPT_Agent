#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
混合技能系统测试脚本

本脚本测试新的混合技能系统，支持：
- 可执行的 Python 技能
- 描述性 Markdown 技能
"""

import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from skill_framework import SkillManager, SkillCategory


def test_markdown_skill_loading():
    """测试 Markdown 技能是否正确加载"""
    print("=" * 60)
    print("测试 1: Markdown 技能加载")
    print("=" * 60)

    # 使用本地配置创建技能管理器（路径相对于 backend/ 目录）
    manager = SkillManager(config_path="skill_config_local.json", auto_load=True)

    # 获取所有描述性技能
    descriptive_skills = manager.get_all_descriptive_skills()

    print(f"\n找到 {len(descriptive_skills)} 个描述性技能：")

    for skill in descriptive_skills:
        print(f"\n- {skill['name']} (ID: {skill['skill_id']})")
        print(f"  Category: {skill['category']}")
        print(f"  Tags: {', '.join(skill['tags'])}")
        print(f"  Description: {skill['description']}")
        print(f"  Enabled: {skill['enabled']}")
        print(f"  Content length: {len(skill.get('content', ''))} characters")

    # 验证预期的技能已加载
    skill_ids = [s['skill_id'] for s in descriptive_skills]
    expected_ids = ['web-search-strategy', 'research-guide', 'writing-style-guide']

    print(f"\n预期技能: {expected_ids}")
    print(f"已加载技能: {skill_ids}")

    for expected_id in expected_ids:
        if expected_id in skill_ids:
            print(f"[通过] {expected_id} 加载成功")
        else:
            print(f"[失败] {expected_id} 未找到")

    return len(descriptive_skills) >= len(expected_ids)


def test_descriptive_content_for_prompt():
    """测试描述性技能是否可以格式化为 prompt"""
    print("\n" + "=" * 60)
    print("测试 2: 描述性内容格式化为 Prompt")
    print("=" * 60)

    manager = SkillManager(config_path="skill_config_local.json", auto_load=True)

    # 获取搜索类别的内容
    content = manager.get_descriptive_content_for_prompt(
        categories=[SkillCategory.SEARCH]
    )

    print("\n格式化的 SEARCH 类别内容：")
    print("-" * 60)
    print(content[:500] + "..." if len(content) > 500 else content)
    print("-" * 60)

    # 获取文档类别的内容
    content_doc = manager.get_descriptive_content_for_prompt(
        categories=[SkillCategory.DOCUMENT]
    )

    print(f"\nDOCUMENT 类别的内容长度: {len(content_doc)} 字符")

    return len(content) > 0


def test_get_skills_for_agent():
    """测试为 Agent 获取混合技能"""
    print("\n" + "=" * 60)
    print("测试 3: 获取 Agent 技能（混合）")
    print("=" * 60)

    manager = SkillManager(config_path="skill_config_local.json", auto_load=True)

    # 获取两种类型的技能
    skills = manager.get_skills_for_agent(
        categories=[SkillCategory.SEARCH, SkillCategory.DOCUMENT]
    )

    print(f"\n可执行技能: {len(skills['executable'])}")
    for skill in skills['executable']:
        print(f"  - {skill['name']} (ID: {skill['skill_id']})")

    print(f"\n描述性技能: {len(skills['descriptive'])}")
    for skill in skills['descriptive']:
        print(f"  - {skill['name']} (ID: {skill['skill_id']})")

    return len(skills['descriptive']) > 0


def test_get_descriptive_skill_info():
    """测试获取描述性技能的详细信息"""
    print("\n" + "=" * 60)
    print("测试 4: 获取描述性技能信息")
    print("=" * 60)

    manager = SkillManager(config_path="skill_config_local.json", auto_load=True)

    # 获取特定技能的信息
    skill_info = manager.get_descriptive_skill_info('web-search-strategy')

    if skill_info:
        print("\n'web-search-strategy' 的技能信息：")
        print(f"  名称: {skill_info['name']}")
        print(f"  版本: {skill_info['version']}")
        print(f"  类别: {skill_info['category']}")
        print(f"  作者: {skill_info.get('author', 'N/A')}")
        print(f"  文件: {skill_info.get('file_path', 'N/A')}")
        print(f"  内容预览: {skill_info.get('content', '')[:100]}...")
        return True
    else:
        print("获取技能信息失败")
        return False


def test_registry_stats():
    """测试注册表统计"""
    print("\n" + "=" * 60)
    print("测试 5: 注册表统计")
    print("=" * 60)

    manager = SkillManager(config_path="skill_config_local.json", auto_load=True)
    stats = manager.get_stats()

    print("\n注册表统计：")
    print(f"  可执行技能: {stats['executable_skills']}")
    print(f"  描述性技能: {stats['descriptive_skills']}")
    print(f"  总技能数: {stats['total_skills']}")
    print(f"  已启用可执行: {stats['enabled_executable']}")
    print(f"  已启用描述性: {stats['enabled_descriptive']}")
    print(f"  MCP 工具: {stats['mcp_tools']}")
    print(f"  类别: {stats['categories']}")
    print(f"  总标签数: {stats['total_tags']}")

    return stats['descriptive_skills'] > 0


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("混合技能系统测试套件")
    print("=" * 60)

    tests = [
        ("Markdown 技能加载", test_markdown_skill_loading),
        ("描述性内容格式化", test_descriptive_content_for_prompt),
        ("获取 Agent 技能", test_get_skills_for_agent),
        ("获取描述性技能信息", test_get_descriptive_skill_info),
        ("注册表统计", test_registry_stats),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[失败] 测试 '{name}' 出错: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 打印摘要
    print("\n" + "=" * 60)
    print("测试摘要")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[通过]" if result else "[失败]"
        print(f"{status}: {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n*** 所有测试通过！***")
        return 0
    else:
        print(f"\n*** {total - passed} 个测试失败 ***")
        return 1


if __name__ == "__main__":
    sys.exit(main())
