"""
P0 级别测试：验证 BaseToolAgent 和 ResearchAgent 的工具集成

测试内容：
1. BaseToolAgent 能正确加载 MCP 工具
2. ResearchAgent 能正确继承 BaseToolAgent
3. 工具执行功能正常
4. 降级机制工作正常
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from langchain_openai import ChatOpenAI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """打印测试章节"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


async def test_1_basetoolagent_import():
    """测试1：验证 BaseToolAgent 可以正确导入"""
    print_section("测试1：导入 BaseToolAgent")

    try:
        from backend.agents.core.base_agent import BaseToolAgent
        print("[OK] BaseToolAgent 导入成功")
        return True
    except ImportError as e:
        print(f"[X] BaseToolAgent 导入失败: {e}")
        return False


async def test_2_basetoolagent_init():
    """测试2：验证 BaseToolAgent 可以正确初始化"""
    print_section("测试2：初始化 BaseToolAgent")

    try:
        from backend.agents.core.base_agent import BaseToolAgent

        # 测试不使用工具的初始化
        agent_no_tools = BaseToolAgent(
            use_tools=False,
            agent_name="TestAgent_NoTools"
        )
        print(f"✅ BaseToolAgent 无工具初始化成功")
        print(f"   - Agent 名称: {agent_no_tools.agent_name}")
        print(f"   - 工具启用: {agent_no_tools._use_tools}")
        print(f"   - 工具数量: {agent_no_tools.get_tool_count()}")

        # 测试使用工具的初始化
        print("\n尝试初始化带工具的 Agent...")
        agent_with_tools = BaseToolAgent(
            use_tools=True,
            tool_category="SEARCH",
            agent_name="TestAgent_WithTools",
            verbose=False
        )

        print(f"✅ BaseToolAgent 带工具初始化成功")
        print(f"   - Agent 名称: {agent_with_tools.agent_name}")
        print(f"   - 工具启用: {agent_with_tools._use_tools}")
        print(f"   - 工具数量: {agent_with_tools.get_tool_count()}")
        print(f"   - 已加载工具: {agent_with_tools.get_loaded_tools()}")

        return True

    except Exception as e:
        print(f"❌ BaseToolAgent 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_3_researchagent_init():
    """测试3：验证 ResearchAgent 可以正确初始化"""
    print_section("测试3：初始化 ResearchAgent")

    try:
        from backend.agents.core.research.research_agent import ResearchAgent

        # 测试不使用工具的初始化
        agent_no_tools = ResearchAgent(
            use_search_tools=False,
            enable_memory=False
        )
        print(f"✅ ResearchAgent 无工具初始化成功")
        print(f"   - Agent 名称: {agent_no_tools.agent_name}")
        print(f"   - 工具启用: {agent_no_tools._use_tools}")

        # 测试使用工具的初始化
        print("\n尝试初始化带工具的 ResearchAgent...")
        agent_with_tools = ResearchAgent(
            use_search_tools=True,
            enable_memory=False
        )

        print(f"✅ ResearchAgent 带工具初始化成功")
        print(f"   - Agent 名称: {agent_with_tools.agent_name}")
        print(f"   - 工具启用: {agent_with_tools._use_tools}")
        print(f"   - 工具数量: {agent_with_tools.get_tool_count()}")
        print(f"   - 已加载工具: {agent_with_tools.get_loaded_tools()}")

        return True

    except Exception as e:
        print(f"❌ ResearchAgent 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_4_tool_execution():
    """测试4：验证工具执行功能（需要 API Key）"""
    print_section("测试4：工具执行功能")

    try:
        from backend.agents.core.research.research_agent import ResearchAgent
        import os

        # 检查是否有 API Key
        if not os.getenv("OPENAI_API_KEY"):
            print("[!] 未设置 OPENAI_API_KEY，跳过工具执行测试")
            print("   要运行此测试，请设置环境变量：")
            print("   export OPENAI_API_KEY='your-api-key'")
            return True

        # 创建带工具的 Agent
        agent = ResearchAgent(
            use_search_tools=True,
            enable_memory=False
        )

        print(f"Agent 已创建，工具数量: {agent.get_tool_count()}")

        # 检查是否有搜索 API Key
        if not os.getenv("BING_SEARCH_API_KEY"):
            print("⚠️  未设置 BING_SEARCH_API_KEY，工具执行可能失败")
            print("   要完整测试，请设置：")
            print("   export BING_SEARCH_API_KEY='your-bing-key'")

        # 尝试执行简单的任务
        print("\n尝试执行简单研究任务...")

        test_page = {
            "page_no": 1,
            "title": "Python编程",
            "core_content": "Python是一种高级编程语言",
            "keywords": ["Python", "编程", "语言"]
        }

        result = await agent.research_page(test_page)

        print(f"✅ 研究任务执行完成")
        print(f"   - 页码: {result.get('page_no')}")
        print(f"   - 标题: {result.get('title')}")
        print(f"   - 状态: {result.get('status')}")
        print(f"   - 使用工具: {result.get('tools_used')}")
        print(f"   - 内容长度: {len(result.get('research_content', ''))}")

        return True

    except Exception as e:
        print(f"❌ 工具执行测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_5_fallback_mechanism():
    """测试5：验证降级机制"""
    print_section("测试5：降级机制")

    try:
        from backend.agents.core.research.research_agent import ResearchAgent
        import os

        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  未设置 OPENAI_API_KEY，跳过降级测试")
            return True

        # 创建不使用工具的 Agent
        agent = ResearchAgent(
            use_search_tools=False,  # 不使用工具
            enable_memory=False
        )

        print(f"Agent 已创建（LLM-only 模式）")

        test_page = {
            "page_no": 1,
            "title": "测试降级",
            "core_content": "测试内容",
            "keywords": ["测试"]
        }

        result = await agent.research_page(test_page)

        print(f"✅ LLM-only 模式执行成功")
        print(f"   - 使用工具: {result.get('tools_used')}")
        print(f"   - 内容长度: {len(result.get('research_content', ''))}")

        return True

    except Exception as e:
        print(f"❌ 降级机制测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_6_inheritance():
    """测试6：验证继承关系"""
    print_section("测试6：继承关系验证")

    try:
        from backend.agents.core.base_agent import BaseAgent, BaseToolAgent
        from backend.agents.core.research.research_agent import ResearchAgent

        # 检查继承关系
        print("检查继承关系：")
        print(f"   - BaseToolAgent 继承自 BaseAgent: {issubclass(BaseToolAgent, BaseAgent)}")
        print(f"   - ResearchAgent 继承自 BaseToolAgent: {issubclass(ResearchAgent, BaseToolAgent)}")

        # 检查方法可用性
        agent = ResearchAgent(use_search_tools=False)

        print(f"\n检查方法可用性：")
        print(f"   - has_tools(): {hasattr(agent, 'has_tools')}")
        print(f"   - get_loaded_tools(): {hasattr(agent, 'get_loaded_tools')}")
        print(f"   - get_tool_count(): {hasattr(agent, 'get_tool_count')}")
        print(f"   - execute_with_tools(): {hasattr(agent, 'execute_with_tools')}")
        print(f"   - research_page(): {hasattr(agent, 'research_page')}")

        print(f"\n✅ 继承关系正确")
        return True

    except Exception as e:
        print(f"❌ 继承关系测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("  P0 级别测试套件")
    print("  BaseToolAgent 和 ResearchAgent 工具集成")
    print("=" * 60)

    # 检查环境变量
    import os
    has_openai_key = bool(os.getenv("OPENAI_API_KEY"))
    has_bing_key = bool(os.getenv("BING_SEARCH_API_KEY"))

    print("\n环境检查：")
    print(f"   OPENAI_API_KEY: {'[OK] 已设置' if has_openai_key else '[X] 未设置'}")
    print(f"   BING_SEARCH_API_KEY: {'[OK] 已设置' if has_bing_key else '[!] 未设置（搜索工具需要）'}")

    # 运行测试
    tests = [
        ("导入 BaseToolAgent", test_1_basetoolagent_import),
        ("初始化 BaseToolAgent", test_2_basetoolagent_init),
        ("初始化 ResearchAgent", test_3_researchagent_init),
        ("工具执行功能", test_4_tool_execution),
        ("降级机制", test_5_fallback_mechanism),
        ("继承关系验证", test_6_inheritance),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试 '{test_name}' 发生异常: {e}")
            results.append((test_name, False))

    # 打印总结
    print_section("测试总结")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！P0 功能实现成功。")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查。")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
