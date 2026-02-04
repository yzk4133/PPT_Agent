"""
直接测试数据模型功能
"""
import sys
import os
os.chdir(r"C:\Users\yanzikun\Desktop\CS\5. Project\MultiAgentPPT-main\backend")

# 添加路径
sys.path.insert(0, ".")

print("测试 Memory 数据模型...")
print("=" * 60)

# 测试 1: MemoryMetadata
print("\n[1] 测试 MemoryMetadata...")
try:
    from memory.models import MemoryMetadata, MemoryLayer, MemoryScope

    # 创建元数据
    m = MemoryMetadata(
        key="test_key",
        layer=MemoryLayer.L1_TRANSIENT,
        scope=MemoryScope.SESSION,
        importance=0.5
    )

    # 测试重要性限制
    assert m.importance == 0.5, f"Expected 0.5, got {m.importance}"

    m2 = MemoryMetadata(
        key="test2",
        layer=MemoryLayer.L1_TRANSIENT,
        scope=MemoryScope.SESSION,
        importance=1.5  # 应该被限制到 1.0
    )
    assert m2.importance == 1.0, f"Expected 1.0, got {m2.importance}"

    print("  PASS - 重要性限制正常")
    print("  PASS - 元数据创建正常")

    # 测试访问计数
    original = m.access_count
    m.increment_access()
    assert m.access_count == original + 1
    print("  PASS - 访问计数正常")

    # 测试会话 ID
    m.add_session_id("session_1")
    m.add_session_id("session_2")
    assert len(m.session_ids) == 2
    m.add_session_id("session_1")  # 不应该重复添加
    assert len(m.session_ids) == 2
    print("  PASS - 会话 ID 管理正常")

    # 测试提升规则
    assert not m.should_promote_to_l2(), "不应提升（访问次数不足）"

    m.access_count = 3
    assert m.should_promote_to_l2(), "应该提升（访问次数>=3）"
    print("  PASS - L2 提升规则正常")

    m.session_ids = ["s1", "s2"]
    assert m.should_promote_to_l3(), "应该提升（跨会话>=2）"
    print("  PASS - L3 提升规则正常")

except Exception as e:
    print(f"  FAIL - MemoryMetadata 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("所有数据模型测试通过！")
print("=" * 60)

# 测试 2: 枚举类
print("\n[2] 测试枚举类...")
try:
    from memory.models import PromotionReason  # 添加导入
    assert MemoryLayer.L1_TRANSIENT.value == "transient"
    assert MemoryScope.TASK.value == "task"
    assert PromotionReason.HIGH_ACCESS_FREQUENCY.value == "high_access_frequency"
    print("  PASS - 所有枚举值正确")
except Exception as e:
    print(f"  FAIL - 枚举测试失败: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("基础测试全部通过！")
print("=" * 60)
