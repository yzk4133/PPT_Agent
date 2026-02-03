#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
渐进式加载Agent集成示例

展示如何在Agent中使用渐进式加载来优化token消耗：
1. 初始system prompt：最小化工具列表
2. Agent决定使用工具后：动态注入完整内容
"""

import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.dirname(__file__))

from skill_framework.core.skill_metadata_progressive import (
    ProgressiveSkillMetadata,
    ProgressiveSkillRegistry
)


class ProgressiveAgent:
    """
    使用渐进式加载的Agent示例

    工作流程：
    1. 初始化：加载最小化工具描述
    2. 用户请求：Agent分析并决定需要哪些技能
    3. 动态注入：按需加载完整技能内容
    4. 执行任务：使用完整内容完成任务
    """

    def __init__(self, skill_registry: ProgressiveSkillRegistry):
        self.registry = skill_registry
        self.conversation_history = []
        self.loaded_skills = set()  # 已加载完整内容的技能

    def get_system_prompt(self, mode: str = "minimal") -> str:
        """
        获取system prompt

        Args:
            mode: "minimal" | "standard" | "full"
        """
        base_instruction = """你是一个专业的AI助手，可以使用多个知识库和技能来帮助用户。

## 工作流程

1. 理解用户需求
2. 确定需要使用哪些技能
3. 如果需要某个技能的详细内容，系统会自动提供
4. 使用提供的技能内容完成任务

"""

        if mode == "minimal":
            tool_desc = self.registry.get_minimal_prompt()
        elif mode == "standard":
            tool_desc = self.registry.get_standard_prompt()
        else:  # full
            tool_desc = self.registry.get_standard_prompt()  # 暂时使用standard

        return base_instruction + "\n\n" + tool_desc

    def enrich_with_skill(self, skill_id: str) -> str:
        """
        用特定技能的完整内容丰富prompt

        当Agent决定使用某个技能时调用
        """
        if skill_id not in self.registry._skills:
            return f"\n\n# 注意：技能 {skill_id} 不存在\n"

        # 懒加载完整内容
        full_content = self.registry.get_full_content_for_skill(skill_id)

        # 记录已加载
        self.loaded_skills.add(skill_id)

        return f"""

# 技能详细内容：{skill_id}

系统已为你加载以下技能的完整内容，请仔细阅读并使用：

{full_content}
"""

    def simulate_conversation(self, user_query: str):
        """
        模拟对话流程（演示用）
        """
        print("\n" + "=" * 60)
        print("对话流程模拟")
        print("=" * 60)

        # 阶段1：初始prompt
        print("\n【阶段1】初始System Prompt（最小化）")
        print("-" * 60)
        initial_prompt = self.get_system_prompt(mode="minimal")
        print(initial_prompt)
        initial_tokens = len(initial_prompt) // 3
        print(f"\nToken估算: ~{initial_tokens} tokens")

        # 阶段2：用户查询
        print(f"\n【阶段2】用户查询")
        print("-" * 60)
        print(f"用户: {user_query}")

        # 阶段3：Agent分析并决定需要的技能
        print(f"\n【阶段3】Agent分析（模拟）")
        print("-" * 60)
        print("Agent思考: 用户需要研究方法指导，我应该使用 'research-guide-zh' 技能")

        # 阶段4：动态加载完整内容
        print(f"\n【阶段4】动态注入完整内容")
        print("-" * 60)
        enrichment = self.enrich_with_skill("research-guide-zh")
        print(enrichment[:500] + "..." if len(enrichment) > 500 else enrichment)

        # 阶段5：完整prompt
        print(f"\n【阶段5】最终完整Prompt")
        print("-" * 60)
        final_prompt = initial_prompt + enrichment
        final_tokens = len(final_prompt) // 3
        print(f"总长度: {len(final_prompt)} 字符")
        print(f"Token估算: ~{final_tokens} tokens")

        # 对比
        print(f"\n【Token对比】")
        print("-" * 60)
        print(f"如果不使用渐进式加载: ~{final_tokens * 3} tokens（假设加载所有技能）")
        print(f"使用渐进式加载:        ~{final_tokens} tokens（只加载需要的）")
        print(f"节省:                  {((final_tokens * 3 - final_tokens) / (final_tokens * 3) * 100):.1f}%")


def create_progressive_skills():
    """创建渐进式加载的技能"""
    skills = [
        ProgressiveSkillMetadata(
            skill_id="web-search-strategy-zh",
            name="网络搜索策略指南",
            version="1.0.0",
            category="search",
            tags=["web", "search", "strategy"],
            description="高效信息检索的网络搜索最佳实践和方法论",
            file_path="skills/search/web_search_strategy_zh.md",
        ),
        ProgressiveSkillMetadata(
            skill_id="research-guide-zh",
            name="研究方法指南",
            version="1.0.0",
            category="document",
            tags=["research", "methodology", "academic"],
            description="系统性研究的综合方法论指南",
            file_path="skills/document/research_guide_zh.md",
        ),
        ProgressiveSkillMetadata(
            skill_id="writing-style-guide-zh",
            name="写作风格指南",
            version="1.0.0",
            category="generation",
            tags=["writing", "style", "communication"],
            description="清晰、高效、专业写作的指导原则",
            file_path="skills/generation/writing_style_guide_zh.md",
        ),
    ]
    return skills


def main():
    """主演示函数"""
    print("=" * 60)
    print("渐进式加载Agent集成演示")
    print("目标：优化token消耗，实现高效上下文工程")
    print("=" * 60)

    # 创建技能注册表
    registry = ProgressiveSkillRegistry()
    skills = create_progressive_skills()

    for skill in skills:
        registry.register(skill)

    print(f"\n✓ 已注册 {len(skills)} 个技能")

    # 创建Agent
    agent = ProgressiveAgent(registry)

    # 场景1：研究任务
    agent.simulate_conversation(
        user_query="请帮我制定一个研究2024年AI发展趋势的计划"
    )

    # Token统计
    print("\n" + "=" * 60)
    print("Token消耗统计")
    print("=" * 60)

    estimate = registry.get_token_estimate()

    print(f"\n【所有技能完整加载】")
    print(f"  总Token数: ~{estimate['full']} tokens")
    print(f"  假设成本: ${estimate['full'] * 0.00001 / 1000:.4f} (按$0.01/1M tokens计算)")

    print(f"\n【渐进式加载（初始）】")
    print(f"  最小模式: ~{estimate['minimal']} tokens")
    print(f"  节省: {((estimate['full'] - estimate['minimal']) / estimate['full'] * 100):.1f}%")

    print(f"\n【渐进式加载（按需）】")
    print(f"  假设只使用1个技能: ~{estimate['minimal'] + estimate['by_skill']['research-guide-zh']['full']} tokens")
    print(f"  节省: {((estimate['full'] - (estimate['minimal'] + estimate['by_skill']['research-guide-zh']['full'])) / estimate['full'] * 100):.1f}%")

    # 实际使用场景建议
    print("\n" + "=" * 60)
    print("实施建议")
    print("=" * 60)

    print("""
推荐策略：

1. 【初始化阶段】（最小化）
   - system_prompt = get_minimal_prompt()
   - Token消耗: ~10-20 tokens/技能
   - 用途：让Agent知道有哪些可用工具

2. 【工具选择阶段】（标准）
   - 当Agent需要更多信息时：system_prompt += get_standard_prompt()
   - Token消耗: ~30-50 tokens/技能
   - 用途：帮助Agent选择合适的工具

3. 【执行阶段】（完整）
   - Agent选定工具后：system_prompt += get_full_content_for_skill(skill_id)
   - Token消耗: ~500-2000 tokens/技能
   - 用途：提供完整的执行指导

4. 【动态卸载】（可选）
   - 完成任务后：skill.unload_content()
   - 释放内存，为下一个任务准备

预期收益：
- 初始prompt减少60-80%
- 只加载真正需要的技能内容
- 内存占用降低40%+
- 支持更多技能而不影响性能
""")


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
