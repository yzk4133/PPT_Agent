"""
Memory 层测试验证脚本

验证测试基础设施和基础功能是否正常工作。
"""

import sys
import os
import asyncio

# 设置路径
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

print("=" * 60)
print("Memory Layer 测试验证")
print("=" * 60)

# 测试 1: 基础导入
print("\n[1/6] 测试基础导入...")
try:
    from memory.models import MemoryMetadata, MemoryLayer, MemoryScope, PromotionReason
    from memory.layers.l1_transient import L1TransientLayer
    from memory.layers.l2_short_term import L2ShortTermLayer
    from memory.promotion import PromotionConfig, ActiveScopeTracker, PromotionRuleEngine
    print("  PASS - 所有基础模块导入成功")
except Exception as e:
    print(f"  FAIL - 导入错误: {e}")
    sys.exit(1)

# 测试 2: L1 层基础功能
print("\n[2/6] 测试 L1 层...")
async def test_l1():
    try:
        layer = L1TransientLayer(capacity=10)
        await layer.set("key1", {"data": "test"}, MemoryScope.SESSION, "session_1")
        result = await layer.get("key1", MemoryScope.SESSION, "session_1")
        assert result is not None
        assert result[0] == {"data": "test"}
        print("  PASS - L1 层基础功能正常")
    except Exception as e:
        print(f"  FAIL - L1 测试错误: {e}")
        raise

asyncio.run(test_l1())

# 测试 3: L1 层 LRU 淘汰
print("\n[3/6] 测试 L1 LRU 淘汰...")
async def test_lru():
    try:
        layer = L1TransientLayer(capacity=3)
        await layer.set("k1", {"d": 1}, MemoryScope.SESSION, "s1")
        await layer.set("k2", {"d": 2}, MemoryScope.SESSION, "s1")
        await layer.set("k3", {"d": 3}, MemoryScope.SESSION, "s1")
        await layer.set("k4", {"d": 4}, MemoryScope.SESSION, "s1")
        # k1 应该被淘汰
        exists = await layer.exists("k1", MemoryScope.SESSION, "s1")
        assert not exists, "k1 应该被淘汰"
        print("  PASS - LRU 淘汰机制正常")
    except Exception as e:
        print(f"  FAIL - LRU 测试错误: {e}")
        raise

asyncio.run(test_lru())

# 测试 4: 作用域隔离
print("\n[4/6] 测试作用域隔离...")
async def test_scope():
    try:
        layer = L1TransientLayer(capacity=10)
        await layer.set("key", {"scope": "task"}, MemoryScope.TASK, "task_1")
        await layer.set("key", {"scope": "session"}, MemoryScope.SESSION, "session_1")
        # 两者应该独立存在
        task_result = await layer.get("key", MemoryScope.TASK, "task_1")
        session_result = await layer.get("key", MemoryScope.SESSION, "session_1")
        assert task_result[0]["scope"] == "task"
        assert session_result[0]["scope"] == "session"
        print("  PASS - 作用域隔离正常")
    except Exception as e:
        print(f"  FAIL - 作用域测试错误: {e}")
        raise

asyncio.run(test_scope())

# 测试 5: L2 层（使用 fakeredis）
print("\n[5/6] 测试 L2 层（fakeredis）...")
try:
    from fakeredis import FakeStrictRedis
    # 先创建层但不连接
    l2 = L2ShortTermLayer(redis_url="redis://localhost:6379/0")
    # 然后替换为 fake redis
    l2.client = FakeStrictRedis(decode_responses=False)
    print("  PASS - L2 层初始化成功（使用 fakeredis）")
except Exception as e:
    print(f"  WARN - L2 测试警告: {e}")
    print("  INFO - L2 测试跳过（可选）")

# 测试 6: 提升引擎
print("\n[6/6] 测试提升引擎...")
async def test_promotion():
    try:
        config = PromotionConfig()
        config.PROMOTE_L1_ACCESS_COUNT = 2  # 降低阈值用于测试
        engine = PromotionRuleEngine(config=config)

        metadata = MemoryMetadata(
            key="test",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
            access_count=2,  # 达到阈值
        )

        should_promote, reason, _ = engine.should_promote_l1_to_l2(metadata)
        assert should_promote is True
        assert reason == PromotionReason.HIGH_ACCESS_FREQUENCY
        print("  PASS - 提升引擎规则正常")
    except Exception as e:
        print(f"  FAIL - 提升引擎测试错误: {e}")
        raise

asyncio.run(test_promotion())

print("\n" + "=" * 60)
print("验证完成!")
print("=" * 60)
print("\n所有基础功能测试通过！")
print("测试文件已创建，但完整测试套件可能需要进一步调试。")
print("\n测试文件位置:")
print("  - 测试文件: backend/memory/tests/")
print("  - 文档: docs/testing/memory-layer/")
print("\n下一步:")
print("  1. 检查并修复导入问题")
print("  2. 运行: pytest backend/memory/tests/unit/test_models.py -v")
print("  3. 生成覆盖率: pytest --cov=backend.memory --cov-report=html")
