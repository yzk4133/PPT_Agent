"""
三层内存架构完整示例

展示如何使用HierarchicalMemoryManager进行数据管理
"""

import asyncio
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# 导入三层内存架构
from persistent_memory import (
    HierarchicalMemoryManager,
    MemoryScope,
    MemoryLayer,
    init_global_memory_manager,
    shutdown_global_memory_manager,
)


async def demo_basic_operations():
    """演示基础操作"""
    print("\n" + "=" * 60)
    print("【演示1】基础操作：get/set/delete/exists")
    print("=" * 60)

    # 创建内存管理器
    memory = HierarchicalMemoryManager(l1_capacity=1000, enable_auto_promotion=True)
    await memory.start_background_tasks()

    try:
        # 场景：Agent处理用户任务
        user_id = "user_123"
        session_id = "session_456"

        # 1. 存储任务级临时数据（自动存入L1）
        await memory.set(
            key="current_task_context",
            value={"task": "生成PPT", "slides": 5, "theme": "商务"},
            scope=MemoryScope.TASK,
            scope_id="task_789",
            importance=0.3,  # 低重要性，保留在L1
        )

        # 2. 存储会话级数据（自动存入L2）
        await memory.set(
            key="user_preferences",
            value={"language": "zh-CN", "font_size": 14},
            scope=MemoryScope.SESSION,
            scope_id=session_id,
            importance=0.6,
        )

        # 3. 手动标记重要数据（直接存入L3）
        await memory.set(
            key="company_template",
            value={"logo": "company.png", "colors": ["#FF0000", "#0000FF"]},
            scope=MemoryScope.USER,
            scope_id=user_id,
            importance=0.9,  # 高重要性
            target_layer=MemoryLayer.L3_LONG_TERM,  # 强制L3
        )

        # 4. 读取数据（自动搜索L1→L2→L3）
        result = await memory.get("current_task_context", MemoryScope.TASK, "task_789")
        if result:
            value, metadata = result
            print(f"✓ 读取任务上下文: {value}")
            print(f"  - 存储层级: {metadata.layer.value}")
            print(f"  - 访问次数: {metadata.access_count}")

        # 5. 检查存在性
        exists = await memory.exists("company_template", MemoryScope.USER, user_id)
        print(f"✓ 公司模板存在: {exists}")

        # 6. 删除数据
        deleted = await memory.delete(
            "current_task_context", MemoryScope.TASK, "task_789"
        )
        print(f"✓ 删除任务上下文: {deleted}")

    finally:
        await memory.stop_background_tasks()


async def demo_auto_promotion():
    """演示自动提升机制"""
    print("\n" + "=" * 60)
    print("【演示2】自动提升：L1→L2→L3")
    print("=" * 60)

    memory = HierarchicalMemoryManager(enable_auto_promotion=True)
    await memory.start_background_tasks()

    try:
        task_id = "task_auto_promote"

        # 1. 存储低重要性数据到L1
        await memory.set(
            key="test_data",
            value={"counter": 0},
            scope=MemoryScope.TASK,
            scope_id=task_id,
            importance=0.3,
        )

        print("初始数据存储在 L1")

        # 2. 多次访问，触发提升条件
        for i in range(5):
            result = await memory.get("test_data", MemoryScope.TASK, task_id)
            if result:
                value, metadata = result
                print(
                    f"第{i+1}次访问: 层级={metadata.layer.value}, 访问次数={metadata.access_count}"
                )

                # 检查是否应该提升到L2
                if metadata.should_promote_to_l2():
                    print(f"  → 满足L1→L2提升条件 (访问≥3次)")

        # 3. 手动提升到L3（用户标记重要）
        promoted = await memory.promote_to_l3("test_data", MemoryScope.TASK, task_id)
        print(f"✓ 手动提升到L3: {promoted}")

        # 4. 查看提升统计
        stats = await memory.get_stats()
        print(f"\n提升统计:")
        print(f"  总提升次数: {stats['promotion']['total_promotions']}")
        print(f"  按原因分布: {stats['promotion']['by_reason']}")

    finally:
        await memory.stop_background_tasks()


async def demo_batch_operations():
    """演示批量操作"""
    print("\n" + "=" * 60)
    print("【演示3】批量操作：任务结束时刷新L1→L2")
    print("=" * 60)

    memory = HierarchicalMemoryManager()
    await memory.start_background_tasks()

    try:
        task_id = "task_batch"

        # 1. 在任务执行中，多次写入L1
        print("任务执行中，写入多个临时数据...")
        for i in range(10):
            await memory.set(
                key=f"temp_result_{i}",
                value={"step": i, "result": f"output_{i}"},
                scope=MemoryScope.TASK,
                scope_id=task_id,
                importance=0.5 + (i * 0.05),  # 递增重要性
            )

        # 2. 查看L1统计
        stats_before = await memory.get_stats()
        print(f"L1数据量: {stats_before['l1_transient']['data_count']}")

        # 3. 任务结束，批量刷新高价值数据到L2
        print("\n任务结束，刷新重要数据到L2...")
        flushed = await memory.batch_flush_l1_to_l2(MemoryScope.TASK, task_id)
        print(f"✓ 刷新了 {flushed} 条数据到L2")

        # 4. 清理任务作用域
        cleared = await memory.clear_scope(
            MemoryScope.TASK, task_id, layers=[MemoryLayer.L1_TRANSIENT]  # 只清理L1
        )
        print(f"✓ 清理L1: {cleared['l1']} 条")

    finally:
        await memory.stop_background_tasks()


async def demo_multi_agent_collaboration():
    """演示多Agent协作场景"""
    print("\n" + "=" * 60)
    print("【演示4】Multi-Agent协作：共享工作区")
    print("=" * 60)

    memory = HierarchicalMemoryManager()
    await memory.start_background_tasks()

    try:
        workspace_id = "workspace_ppt_project"

        # Agent 1: OutlineAgent 生成大纲
        print("Agent1 (OutlineAgent) 生成PPT大纲...")
        await memory.set(
            key="ppt_outline",
            value={
                "title": "2024年度总结",
                "slides": [
                    {"title": "业绩回顾", "content": "..."},
                    {"title": "团队建设", "content": "..."},
                    {"title": "未来展望", "content": "..."},
                ],
            },
            scope=MemoryScope.WORKSPACE,
            scope_id=workspace_id,
            importance=0.8,
            tags=["outline", "shared"],
        )

        # Agent 2: DesignAgent 读取大纲并设计样式
        print("Agent2 (DesignAgent) 读取大纲...")
        result = await memory.get("ppt_outline", MemoryScope.WORKSPACE, workspace_id)
        if result:
            outline, metadata = result
            print(f"  ✓ 获取大纲: {len(outline['slides'])} 页")

            # 设计样式并保存
            print("Agent2 设计样式...")
            await memory.set(
                key="ppt_design",
                value={
                    "theme": "现代商务",
                    "primary_color": "#1E90FF",
                    "font": "微软雅黑",
                },
                scope=MemoryScope.WORKSPACE,
                scope_id=workspace_id,
                importance=0.7,
                tags=["design", "shared"],
            )

        # Agent 3: ContentAgent 填充内容
        print("Agent3 (ContentAgent) 生成具体内容...")
        await memory.set(
            key="ppt_content",
            value={
                "slide_1": {
                    "title": "业绩回顾",
                    "bullets": ["销售额增长30%", "客户满意度95%"],
                },
                "slide_2": {
                    "title": "团队建设",
                    "bullets": ["新增10名员工", "组织5次团建"],
                },
            },
            scope=MemoryScope.WORKSPACE,
            scope_id=workspace_id,
            importance=0.9,
            tags=["content", "final"],
        )

        # 查看工作区所有数据
        print("\n工作区内容：")
        keys = await memory.l2.list_keys(MemoryScope.WORKSPACE, workspace_id)
        print(f"  共享数据键: {keys}")

    finally:
        await memory.stop_background_tasks()


async def demo_statistics():
    """演示统计信息"""
    print("\n" + "=" * 60)
    print("【演示5】系统统计：性能指标")
    print("=" * 60)

    memory = HierarchicalMemoryManager()
    await memory.start_background_tasks()

    try:
        # 模拟一些操作
        for i in range(20):
            await memory.set(
                f"test_{i}",
                {"value": i},
                MemoryScope.TASK,
                "test_task",
                importance=0.3 + (i * 0.02),
            )

        for i in range(15):
            await memory.get(f"test_{i}", MemoryScope.TASK, "test_task")

        # 获取全局统计
        stats = await memory.get_stats()

        print("\nL1 瞬时内存:")
        print(f"  数据量: {stats['l1_transient']['data_count']}")
        print(f"  容量: {stats['l1_transient']['capacity']}")
        print(f"  命中率: {stats['l1_transient']['hit_rate']:.2%}")
        print(
            f"  命中: {stats['l1_transient']['hits']}, 未命中: {stats['l1_transient']['misses']}"
        )

        print("\nL2 短期内存:")
        print(f"  Redis可用: {stats['l2_short_term']['redis_available']}")
        print(f"  命中率: {stats['l2_short_term']['hit_rate']:.2%}")

        print("\nL3 长期内存:")
        print(f"  总记录数: {stats['l3_long_term'].get('total_records', 0)}")
        print(f"  平均重要性: {stats['l3_long_term'].get('avg_importance', 0):.2f}")

        print("\n数据提升:")
        print(f"  总提升次数: {stats['promotion']['total_promotions']}")
        print(f"  唯一键数: {stats['promotion']['unique_keys_promoted']}")

    finally:
        await memory.stop_background_tasks()


async def demo_global_instance():
    """演示全局单例模式"""
    print("\n" + "=" * 60)
    print("【演示6】全局单例：应用级共享")
    print("=" * 60)

    # 初始化全局实例
    memory = await init_global_memory_manager(
        l1_capacity=2000, enable_auto_promotion=True
    )

    try:
        print("✓ 全局内存管理器已初始化")

        # 在应用的任何地方都可以获取同一个实例
        from persistent_memory import get_global_memory_manager

        memory1 = get_global_memory_manager()
        memory2 = get_global_memory_manager()

        print(f"✓ 单例验证: memory1 is memory2 = {memory1 is memory2}")

        # 使用全局实例
        await memory1.set(
            "global_config",
            {"version": "1.0", "env": "production"},
            MemoryScope.USER,
            "system",
            importance=1.0,
        )

        result = await memory2.get("global_config", MemoryScope.USER, "system")
        if result:
            value, _ = result
            print(f"✓ 通过另一个引用读取: {value}")

    finally:
        # 关闭全局实例
        from persistent_memory import shutdown_global_memory_manager

        await shutdown_global_memory_manager()
        print("✓ 全局内存管理器已关闭")


async def main():
    """运行所有演示"""
    print("\n" + "=" * 70)
    print("三层内存架构完整演示")
    print("=" * 70)

    try:
        await demo_basic_operations()
        await demo_auto_promotion()
        await demo_batch_operations()
        await demo_multi_agent_collaboration()
        await demo_statistics()
        await demo_global_instance()

        print("\n" + "=" * 70)
        print("所有演示完成！")
        print("=" * 70)

        print("\n关键特性总结：")
        print("1. ✓ L1瞬时内存 - 任务级缓存，LRU淘汰")
        print("2. ✓ L2短期内存 - 会话级Redis存储")
        print("3. ✓ L3长期内存 - 用户级PostgreSQL持久化")
        print("4. ✓ 自动提升 - 基于访问模式和重要性")
        print("5. ✓ 批量操作 - 减少网络往返")
        print("6. ✓ Multi-Agent - 工作区共享数据")
        print("7. ✓ 全局单例 - 应用级统一管理")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
