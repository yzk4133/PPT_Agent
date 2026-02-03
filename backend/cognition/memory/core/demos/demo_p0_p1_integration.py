#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P0-P1功能集成示例
演示如何在Agent中使用新的记忆系统功能
"""
import asyncio
import time
from datetime import datetime

# 导入新服务
from persistent_memory import (
    AgentDecisionService,
    ToolFeedbackService,
    SharedWorkspaceService,
    ContextWindowOptimizer,
)


class EnhancedAgentExample:
    """增强版Agent示例 - 集成P0-P1功能"""

    def __init__(self):
        self.decision_service = AgentDecisionService(enable_cache=True)
        self.tool_feedback_service = ToolFeedbackService(enable_cache=True)
        self.workspace_service = SharedWorkspaceService(enable_cache=True)
        self.context_optimizer = ContextWindowOptimizer()

    async def execute_with_tracking(
        self,
        session_id: str,
        user_id: str,
        agent_name: str,
        task: str,
    ):
        """
        执行任务并完整追踪决策和工具调用
        """
        print(f"\n{'='*60}")
        print(f"Agent: {agent_name}")
        print(f"Task: {task}")
        print(f"{'='*60}\n")

        # === 步骤1: 记录决策 ===
        print("📝 Step 1: 记录Agent决策")
        decision_id = await self.decision_service.record_decision(
            session_id=session_id,
            user_id=user_id,
            agent_name=agent_name,
            decision_type=AgentDecisionService.TOOL_SELECTION,
            context={
                "task": task,
                "available_tools": ["DocumentSearch", "WebSearch", "VectorSearch"],
            },
            selected_action="DocumentSearch",
            alternatives=["WebSearch", "VectorSearch"],
            reasoning="任务需要搜索文档，DocumentSearch最适合",
            confidence_score=0.85,
        )
        print(f"✅ 决策已记录，ID: {decision_id}")

        # === 步骤2: 执行工具并追踪 ===
        print("\n🔧 Step 2: 执行工具调用")
        start_time = time.time()

        # 模拟工具执行
        tool_result = await self._simulate_tool_execution(task)

        latency_ms = int((time.time() - start_time) * 1000)

        # 记录工具执行
        feedback_id = await self.tool_feedback_service.record_tool_execution(
            session_id=session_id,
            user_id=user_id,
            tool_name="DocumentSearch",
            agent_name=agent_name,
            input_params={"keyword": task, "number": 5},
            latency_ms=latency_ms,
            success=True,
            output_summary={
                "result_count": len(tool_result),
                "data_size_kb": 15,
            },
            decision_id=decision_id,
        )
        print(f"✅ 工具执行已追踪，耗时: {latency_ms}ms, ID: {feedback_id}")

        # === 步骤3: 共享结果到工作空间 ===
        print("\n🤝 Step 3: 共享结果给其他Agent")
        shared_id = await self.workspace_service.share_data(
            session_id=session_id,
            data_type=SharedWorkspaceService.RESEARCH_RESULT,
            source_agent=agent_name,
            data_key=f"research_{task.replace(' ', '_')}",
            data_content={
                "query": task,
                "results": tool_result,
                "timestamp": datetime.utcnow().isoformat(),
            },
            data_summary=f"研究结果: {task} ({len(tool_result)}条)",
            target_agents=["PPTGeneratorAgent", "OutlineAgent"],  # 指定目标Agent
            ttl_minutes=30,
        )
        print(f"✅ 数据已共享，ID: {shared_id}")

        # === 步骤4: 更新决策结果 ===
        print("\n📊 Step 4: 更新决策执行结果")
        await self.decision_service.update_decision_outcome(
            decision_id=decision_id,
            outcome=AgentDecisionService.SUCCESS,
            execution_time_ms=latency_ms,
            token_usage={"prompt": 120, "completion": 80, "total": 200},
        )
        print(f"✅ 决策结果已更新")

        # === 步骤5: 更新工具使用反馈 ===
        print("\n💡 Step 5: 更新工具使用反馈")
        await self.tool_feedback_service.update_usage_feedback(
            feedback_id=feedback_id,
            used_in_final_output=True,  # 结果被使用
            relevance_score=0.92,  # 相关性评分
            user_feedback="positive",
        )
        print(f"✅ 工具反馈已更新")

        return tool_result

    async def _simulate_tool_execution(self, query: str):
        """模拟工具执行"""
        await asyncio.sleep(0.1)  # 模拟延迟
        return [
            {"title": f"Result 1 for {query}", "content": "..."},
            {"title": f"Result 2 for {query}", "content": "..."},
            {"title": f"Result 3 for {query}", "content": "..."},
        ]

    async def demonstrate_workspace_collaboration(self, session_id: str):
        """演示Multi-Agent协作"""
        print(f"\n{'='*60}")
        print("Multi-Agent 协作演示")
        print(f"{'='*60}\n")

        # Agent1 共享研究结果
        print("🤖 Agent1 (ResearchAgent) 共享研究结果...")
        await self.workspace_service.share_data(
            session_id=session_id,
            data_type=SharedWorkspaceService.RESEARCH_RESULT,
            source_agent="ResearchAgent",
            data_key="ai_trends_2024",
            data_content={
                "topic": "AI Trends 2024",
                "findings": ["Finding 1", "Finding 2", "Finding 3"],
            },
            data_summary="2024 AI趋势研究结果",
        )

        # Agent2 访问共享数据
        print("\n🤖 Agent2 (OutlineAgent) 访问共享数据...")
        research_data = await self.workspace_service.get_shared_data(
            session_id=session_id,
            data_key="ai_trends_2024",
            accessing_agent="OutlineAgent",
        )

        if research_data:
            print(f"✅ 成功获取: {research_data['topic']}")
            print(f"   发现数量: {len(research_data['findings'])}")
        else:
            print("❌ 未找到数据")

        # Agent3 也访问
        print("\n🤖 Agent3 (PPTGeneratorAgent) 访问共享数据...")
        ppt_data = await self.workspace_service.get_shared_data(
            session_id=session_id,
            data_key="ai_trends_2024",
            accessing_agent="PPTGeneratorAgent",
        )

        if ppt_data:
            print(f"✅ 成功获取: {ppt_data['topic']}")

        # 查看工作空间统计
        print("\n📊 工作空间统计:")
        stats = await self.workspace_service.get_workspace_stats(session_id)
        print(f"   总共享数据: {stats['total_shared_data']}")
        print(f"   总访问次数: {stats['total_accesses']}")
        print(f"   按Agent分布: {stats['by_source_agent']}")

    async def demonstrate_performance_analysis(self):
        """演示性能分析"""
        print(f"\n{'='*60}")
        print("性能分析演示")
        print(f"{'='*60}\n")

        # 分析Agent性能
        print("📈 Agent性能分析:")
        perf = await self.decision_service.analyze_agent_performance(
            agent_name="ResearchAgent",
            time_range_hours=24,
        )
        print(f"   总决策数: {perf['total_decisions']}")
        print(f"   成功率: {perf['success_rate']}%")
        print(f"   平均耗时: {perf['avg_execution_time_ms']}ms")
        print(f"   决策类型分布: {perf['decision_type_distribution']}")

        # 分析工具性能
        print("\n🔧 工具性能分析:")
        tool_perf = await self.tool_feedback_service.get_tool_performance(
            tool_name="DocumentSearch",
            time_range_hours=24,
        )
        print(f"   调用次数: {tool_perf['total_calls']}")
        print(f"   成功率: {tool_perf['success_rate']}%")
        print(f"   平均延迟: {tool_perf['avg_latency_ms']}ms")
        print(f"   使用率: {tool_perf['usage_rate']}%")
        if tool_perf.get("avg_relevance_score"):
            print(f"   相关性评分: {tool_perf['avg_relevance_score']}")


async def main():
    """主演示函数"""
    print("\n" + "=" * 70)
    print(" P0-P1 功能集成演示 - 增强版Agent记忆系统 ")
    print("=" * 70)

    agent = EnhancedAgentExample()
    session_id = "demo_session_001"
    user_id = "demo_user_001"

    try:
        # 演示1: 完整的追踪流程
        print("\n【演示1】完整的Agent执行追踪")
        await agent.execute_with_tracking(
            session_id=session_id,
            user_id=user_id,
            agent_name="ResearchAgent",
            task="AI trends in 2024",
        )

        # 演示2: Multi-Agent协作
        print("\n【演示2】Multi-Agent协作")
        await agent.demonstrate_workspace_collaboration(session_id)

        # 演示3: 性能分析
        print("\n【演示3】性能分析")
        await agent.demonstrate_performance_analysis()

        print("\n" + "=" * 70)
        print("✅ 所有演示完成！")
        print("=" * 70)

        # 总结
        print("\n📋 功能总结:")
        print("✓ P0: Agent决策追踪 - 记录决策过程、上下文、结果")
        print("✓ P0: 上下文窗口优化 - 智能管理Token预算")
        print("✓ P1: 工具执行反馈 - 追踪工具调用效果")
        print("✓ P1: Multi-Agent协作 - 跨Agent数据共享")
        print("\n💡 下一步:")
        print("1. 运行数据库迁移脚本创建新表")
        print("2. 在实际Agent中集成这些服务")
        print("3. 通过Dashboard查看分析结果")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
