"""
MCP Integration Test Script

测试 MCP Server 和 Client 的完整集成流程。

使用步骤：
1. 设置环境变量：export BING_SEARCH_API_KEY="your_key"
2. 启动 MCP Server（在另一个终端）：python -m backend.tools.mcp.server
3. 运行测试脚本：python backend/tools/mcp/test_mcp_integration.py
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mcp_client():
    """测试 MCP Client 连接和工具调用"""

    print("\n" + "="*80)
    print("测试 1: MCP Client 基础连接")
    print("="*80)

    try:
        from backend.tools.domain.search.web_search_mcp import get_mcp_client

        # 获取 MCP Client（会触发连接）
        client = await get_mcp_client()

        print("✅ MCP Client 连接成功")
        print(f"   Client 类型: {type(client)}")

    except Exception as e:
        print(f"❌ MCP Client 连接失败: {e}")
        logger.error("Connection failed", exc_info=True)
        return False

    return True


async def test_web_search_mcp():
    """测试 web_search_mcp_tool 调用"""

    print("\n" + "="*80)
    print("测试 2: Web Search MCP Tool 调用")
    print("="*80)

    try:
        from backend.tools.domain.search.web_search_mcp import web_search_mcp_tool

        # 测试调用
        query = "artificial intelligence"
        num_results = 3

        print(f"查询: {query}")
        print(f"结果数量: {num_results}")

        result = await web_search_mcp_tool.ainvoke({
            "query": query,
            "num_results": num_results
        })

        print("\n✅ Web Search 调用成功")
        print(f"\n结果预览（前500字符）:")
        print("-" * 80)
        print(result[:500] + "..." if len(result) > 500 else result)
        print("-" * 80)

        # 验证结果格式
        if "Found" in result and "results" in result:
            print("\n✅ 结果格式验证通过")
        else:
            print("\n⚠️ 结果格式可能不符合预期")

        return True

    except Exception as e:
        print(f"\n❌ Web Search 调用失败: {e}")
        logger.error("Web search failed", exc_info=True)
        return False


async def test_tool_registry():
    """测试在 Tool Registry 中注册 MCP Tool"""

    print("\n" + "="*80)
    print("测试 3: Tool Registry 集成")
    print("="*80)

    try:
        # 重置注册表
        from backend.tools.application.tool_registry import reset_global_registry, get_native_registry

        reset_global_registry()

        # 测试不使用 MCP
        print("\n[Case 1] 不使用 MCP (USE_MCP_WEB_SEARCH=false)")
        registry = get_native_registry()

        web_search = registry.get_tool("web_search")
        if web_search:
            print(f"✅ 注册成功: {web_search.name}")
            print(f"   描述: {web_search.description[:100]}...")
        else:
            print("❌ 未找到 web_search tool")

        # 测试使用 MCP
        print("\n[Case 2] 使用 MCP (USE_MCP_WEB_SEARCH=true)")
        os.environ["USE_MCP_WEB_SEARCH"] = "true"
        reset_global_registry()

        registry = get_native_registry()

        web_search_mcp = registry.get_tool("web_search_mcp")
        if web_search_mcp:
            print(f"✅ 注册成功: {web_search_mcp.name}")
            print(f"   描述: {web_search_mcp.description}")
        else:
            print("❌ 未找到 web_search_mcp tool")

        # 清理环境变量
        os.environ["USE_MCP_WEB_SEARCH"] = "false"

        return True

    except Exception as e:
        print(f"\n❌ Tool Registry 测试失败: {e}")
        logger.error("Registry test failed", exc_info=True)
        return False


async def test_agent_integration():
    """测试 Agent 使用 MCP Tool"""

    print("\n" + "="*80)
    print("测试 4: Agent 集成（ResearchAgent）")
    print("="*80)

    try:
        from backend.agents.core.research.research_agent import ResearchAgent
        from backend.tools.application.tool_registry import reset_global_registry

        # 重置注册表并启用 MCP
        reset_global_registry()
        os.environ["USE_MCP_WEB_SEARCH"] = "true"

        # 创建 ResearchAgent
        print("\n创建 ResearchAgent...")
        agent = ResearchAgent(
            temperature=0.3,
            enable_memory=False
        )

        print("✅ ResearchAgent 创建成功")

        # 检查 tools
        tools = agent.tools
        mcp_tools = [t for t in tools if "mcp" in t.name.lower()]

        if mcp_tools:
            print(f"\n✅ Agent 包含 MCP Tools: {[t.name for t in mcp_tools]}")
        else:
            print("\n⚠️ Agent 未包含 MCP Tools（可能回退到 LangChain 版本）")

        # 测试简单查询
        print("\n执行测试查询...")
        result = await agent.execute_with_tools(
            "搜索 'machine learning basics' 并返回3个结果"
        )

        print("✅ Agent 执行成功")
        print(f"\n结果预览（前300字符）:")
        print("-" * 80)
        print(result[:300] + "..." if len(result) > 300 else result)
        print("-" * 80)

        # 清理
        os.environ["USE_MCP_WEB_SEARCH"] = "false"

        return True

    except Exception as e:
        print(f"\n❌ Agent 集成测试失败: {e}")
        logger.error("Agent test failed", exc_info=True)
        os.environ["USE_MCP_WEB_SEARCH"] = "false"
        return False


async def main():
    """运行所有测试"""

    print("\n" + "="*80)
    print("MCP Integration Test Suite")
    print("="*80)

    # 检查环境变量
    if not os.getenv("BING_SEARCH_API_KEY"):
        print("\n⚠️ 警告: BING_SEARCH_API_KEY 未设置")
        print("   请设置环境变量: export BING_SEARCH_API_KEY='your_key'")
        print("\n跳过需要 API Key 的测试...")
    else:
        print("\n✅ BING_SEARCH_API_KEY 已配置")

    # 运行测试
    results = {}

    # 测试 1: MCP Client 连接
    if os.getenv("BING_SEARCH_API_KEY"):
        results["client"] = await test_mcp_client()
    else:
        print("\n⏭️ 跳过测试 1: 需要启动 MCP Server")
        results["client"] = None

    # 测试 2: Web Search Tool
    if os.getenv("BING_SEARCH_API_KEY"):
        results["web_search"] = await test_web_search_mcp()
    else:
        print("\n⏭️ 跳过测试 2: 需要启动 MCP Server")
        results["web_search"] = None

    # 测试 3: Tool Registry
    results["registry"] = await test_tool_registry()

    # 测试 4: Agent 集成
    if os.getenv("BING_SEARCH_API_KEY"):
        results["agent"] = await test_agent_integration()
    else:
        print("\n⏭️ 跳过测试 4: 需要启动 MCP Server")
        results["agent"] = None

    # 打印总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)

    for test_name, result in results.items():
        if result is None:
            status = "⏭️ 跳过"
        elif result:
            status = "✅ 通过"
        else:
            status = "❌ 失败"

        print(f"{test_name:20s}: {status}")

    # 统计
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)

    print(f"\n总计: {passed} 通过, {failed} 失败, {skipped} 跳过")

    if failed > 0:
        print("\n❌ 部分测试失败，请检查日志")
        return 1
    else:
        print("\n✅ 所有执行的测试通过！")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
