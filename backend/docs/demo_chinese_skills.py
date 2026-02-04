#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
中文技能演示脚本

演示如何使用混合技能系统中的中文技能
"""

import sys
import os

# 添加backend到路径

from skill_framework import SkillManager, SkillCategory

def demo_chinese_skills():
    """演示中文技能的使用"""

    print("=" * 60)
    print("中文技能系统演示")
    print("=" * 60)

    # 初始化技能管理器
    manager = SkillManager(config_path="skill_config_local.json", auto_load=True)

    # 1. 查看所有中文技能
    print("\n【1】所有中文技能列表")
    print("-" * 60)

    chinese_skills = [
        "web-search-strategy-zh",
        "research-guide-zh",
        "writing-style-guide-zh"
    ]

    for skill_id in chinese_skills:
        info = manager.get_descriptive_skill_info(skill_id)
        if info:
            print(f"\n技能名称: {info['name']}")
            print(f"技能ID: {skill_id}")
            print(f"类别: {info['category']}")
            print(f"描述: {info['description']}")

    # 2. 获取特定类别的中文技能
    print("\n\n【2】搜索类中文技能内容（用于注入Prompt）")
    print("-" * 60)

    search_content = manager.get_descriptive_content_for_prompt(
        skill_ids=["web-search-strategy-zh"]
    )

    print(search_content[:500] + "..." if len(search_content) > 500 else search_content)

    # 3. 为Agent配置混合技能（中文）
    print("\n\n【3】为研究Agent配置中文技能")
    print("-" * 60)

    research_skills = manager.get_skills_for_agent(
        skill_ids=[
            "web-search-strategy-zh",      # 中文搜索策略
            "research-guide-zh",            # 中文研究指南
        ]
    )

    print(f"可执行技能数量: {len(research_skills['executable'])}")
    print(f"描述性技能数量: {len(research_skills['descriptive'])}")

    print("\n描述性技能:")
    for skill in research_skills['descriptive']:
        print(f"  - {skill['name']} ({skill['skill_id']})")

    # 4. 构建增强的中文系统提示词
    print("\n\n【4】构建增强的中文系统提示词")
    print("-" * 60)

    base_instruction = """你是一个专业的研究助手，擅长使用网络搜索和系统化的研究方法来帮助用户获取信息。

请根据以下策略和指南进行工作：
"""

    # 获取中文技能内容
    chinese_knowledge = manager.get_descriptive_content_for_prompt(
        skill_ids=["web-search-strategy-zh", "research-guide-zh"]
    )

    # 组合完整指令
    full_instruction = base_instruction + chinese_knowledge + """

## 工作流程

1. 理解用户需求
2. 应用上述搜索策略
3. 使用系统化的研究方法
4. 提供结构化的研究结果
"""

    print("完整指令长度:", len(full_instruction), "字符")
    print("\n指令预览:")
    print(full_instruction[:400] + "...\n")

    # 5. 统计信息
    print("\n【5】技能系统统计")
    print("-" * 60)

    stats = manager.get_stats()
    print(f"总技能数: {stats['total_skills']}")
    print(f"可执行技能: {stats['executable_skills']}")
    print(f"描述性技能: {stats['descriptive_skills']}")
    print(f"类别分布: {stats['categories']}")

    # 统计中文技能
    all_descriptive = manager.get_all_descriptive_skills()
    zh_skills = [s for s in all_descriptive if 'chinese' in s.get('tags', [])]
    print(f"\n中文描述性技能: {len(zh_skills)}")
    for skill in zh_skills:
        print(f"  - {skill['name']} ({skill['skill_id']})")

def demo_create_chinese_agent():
    """演示如何创建使用中文技能的Agent（伪代码）"""

    print("\n\n" + "=" * 60)
    print("【附录】创建中文Agent的示例代码")
    print("=" * 60)

    example_code = '''
from skill_framework import SkillManager
from google.adk import Agent

# 1. 初始化技能管理器
skill_manager = SkillManager(config_path="skill_config_local.json")

# 2. 获取可执行工具（如文档搜索）
tools = skill_manager.get_tools_for_agent(
    categories=[SkillCategory.DOCUMENT]
)

# 3. 获取中文描述性技能（用于注入Prompt）
chinese_knowledge = skill_manager.get_descriptive_content_for_prompt(
    skill_ids=[
        "web-search-strategy-zh",
        "research-guide-zh",
        "writing-style-guide-zh"
    ]
)

# 4. 构建中文系统指令
instruction = f"""# 你是一个专业的中文内容创作助手

## 可用的知识和策略

{chinese_knowledge}

## 工作要求

1. 使用上述策略进行研究
2. 应用写作指南进行内容创作
3. 用中文回复用户
4. 提供结构化、专业的输出
"""

# 5. 创建Agent
agent = Agent(
    name="chinese_content_agent",
    tools=tools,
    instruction=instruction,
    model="gemini-2.5-flash-exp"  # 或其他支持中文的模型
)

# 6. 使用Agent
response = agent.run("请帮我研究2024年人工智能在教育领域的应用")
'''

    print(example_code)

if __name__ == "__main__":
    # 设置输出编码为UTF-8（Windows控制台）
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')

    try:
        demo_chinese_skills()
        demo_create_chinese_agent()

        print("\n" + "=" * 60)
        print("演示完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
