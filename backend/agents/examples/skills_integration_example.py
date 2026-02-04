"""
Skills框架集成示例

演示如何在Agent中使用Skills框架
"""

import asyncio
import logging
from backend.agents.orchestrator.agents.flat_outline_agent import create_flat_outline_agent
from backend.agents.tools.skills.skill_registry import SkillRegistry
from backend.agents.tools.monitoring.performance_monitor import PerformanceMonitor
from backend.agents.tools.registry.unified_registry import get_unified_registry, ToolCategory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def example_use_skills():
    """演示如何使用Skills"""

    print("\n" + "="*60)
    print("Skills框架集成示例")
    print("="*60 + "\n")

    # 方法1：通过SkillRegistry直接使用
    print("方法1：通过SkillRegistry直接使用")
    print("-" * 40)

    skill_registry = SkillRegistry.get_instance()
    skill_registry.discover_skills()

    # 获取所有可用的技能
    all_skills = skill_registry.list_skills()
    print(f"可用技能: {all_skills}")

    # 方法2：从UnifiedToolRegistry获取工具（包含Skills）
    print("\n方法2：从UnifiedToolRegistry获取工具")
    print("-" * 40)

    registry = get_unified_registry()

    # 获取统计信息
    stats = registry.get_stats()
    print(f"工具总数: {stats['total_tools']}")
    print(f"技能总数: {stats['total_skills']}")
    print(f"启用工具数: {stats['enabled_tools']}")

    # 按类别列出工具
    print("\n按类别列出的工具:")
    for category_name, count in stats['categories'].items():
        if count > 0:
            print(f"  - {category_name}: {count} 个")

    # 方法3：集成到Agent中
    print("\n方法3：集成到Agent中")
    print("-" * 40)

    # 创建agent并自动包含Skills
    agent = create_flat_outline_agent(
        model_name="deepseek-chat",
        provider="deepseek",
        include_skills=True  # 自动包含Skills
    )

    print(f"Agent创建成功: {agent.name}")
    print(f"Agent包含的MCP工具数量: {len(agent.mcp_tools)}")

    # 方法4：获取特定类别的工具
    print("\n方法4：获取特定类别的工具")
    print("-" * 40)

    search_tools = registry.get_adk_tools(
        categories=[ToolCategory.SEARCH],
        include_skills=True
    )
    print(f"搜索类工具数量: {len(search_tools)}")

    media_tools = registry.get_adk_tools(
        categories=[ToolCategory.MEDIA],
        include_skills=True
    )
    print(f"媒体类工具数量: {len(media_tools)}")

    # 方法5：性能监控
    print("\n方法5：性能监控")
    print("-" * 40)

    PerformanceMonitor.print_report()

    # 检查慢速工具
    slow_tools = PerformanceMonitor.get_slow_tools(threshold=5.0)
    if slow_tools:
        print(f"\n⚠️  慢速工具 (>5s): {', '.join(slow_tools)}")
    else:
        print("\n✅ 没有慢速工具")

    # 检查高错误率工具
    error_prone = PerformanceMonitor.get_error_prone_tools(error_threshold=0.1)
    if error_prone:
        print(f"⚠️  高错误率工具 (>10%): {', '.join(error_prone)}")
    else:
        print("✅ 没有高错误率工具")

    print("\n" + "="*60)
    print("示例执行完成")
    print("="*60 + "\n")

async def example_auto_discovery():
    """演示工具自动发现功能"""

    print("\n" + "="*60)
    print("工具自动发现示例")
    print("="*60 + "\n")

    from backend.agents.tools.mcp import auto_discovery

    # 发现所有MCP工具类
    tool_classes = auto_discovery.discover_mcp_tools()

    print(f"发现 {len(tool_classes)} 个MCP工具类:")
    for tool_class in tool_classes:
        print(f"  - {tool_class.__name__}")

    # 自动注册工具
    print("\n开始自动注册...")
    count = auto_discovery.auto_register_tools()
    print(f"成功注册 {count} 个工具")

    print("\n" + "="*60 + "\n")

async def example_mcp_to_adk_conversion():
    """演示MCP到ADK的转换"""

    print("\n" + "="*60)
    print("MCP到ADK转换示例")
    print("="*60 + "\n")

    from backend.agents.tools.adapters.mcp_to_adk_adapter import mcp_to_agent_tool
    from backend.agents.tools.registry.unified_registry import get_unified_registry

    registry = get_unified_registry()

    # 获取所有启用的工具
    enabled_tools = registry.get_enabled_tools()

    print(f"将 {len(enabled_tools)} 个工具转换为ADK格式:\n")

    for tool_name, registration in list(enabled_tools.items())[:3]:  # 只显示前3个
        if registration.tool_func:
            agent_tool = mcp_to_agent_tool(
                mcp_func=registration.tool_func,
                name=registration.metadata.name,
                description=registration.metadata.description
            )
            print(f"工具: {agent_tool.name}")
            print(f"  描述: {agent_tool.description}")
            print(f"  类型: {type(agent_tool).__name__}")
            print()

    print("\n" + "="*60 + "\n")

async def main():
    """主函数"""
    try:
        # 运行所有示例
        await example_use_skills()
        await example_auto_discovery()
        await example_mcp_to_adk_conversion()

    except Exception as e:
        logger.error(f"示例执行失败: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
