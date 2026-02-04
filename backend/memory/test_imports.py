"""
测试新的扁平化 memory 包导入

用于验证重构后的导入路径是否正确
"""

def test_imports():
    """测试所有主要导入路径"""

    print("🔍 测试扁平化记忆系统导入...")

    # 测试1: 核心管理器
    try:
        from memory import (
            HierarchicalMemoryManager,
            MemoryScope,
            get_global_memory_manager,
        )

        print("✅ 核心管理器导入成功")
    except ImportError as e:
        print(f"❌ 核心管理器导入失败: {e}")
        return False

    # 测试2: 模型
    try:
        from memory import MemoryLayer, MemoryMetadata, PromotionReason

        print("✅ 模型导入成功")
    except ImportError as e:
        print(f"❌ 模型导入失败: {e}")
        return False

    # 测试3: 服务层
    try:
        from memory.services import (
            UserPreferenceService,
            SharedWorkspaceService,
            VectorMemoryService,
            AgentDecisionService,
        )

        print("✅ 服务层导入成功")
    except ImportError as e:
        print(f"❌ 服务层导入失败: {e}")
        return False

    # 测试4: 存储层
    try:
        from memory.storage import DatabaseManager, RedisCache, get_db

        print("✅ 存储层导入成功")
    except ImportError as e:
        print(f"❌ 存储层导入失败: {e}")
        return False

    # 测试5: 三层架构
    try:
        from memory.layers import L1TransientLayer, L2ShortTermLayer, L3LongtermLayer

        print("✅ 三层架构导入成功")
    except ImportError as e:
        print(f"❌ 三层架构导入失败: {e}")
        return False

    # 测试6: Agent集成
    try:
        from memory.integration import AgentMemoryMixin

        print("✅ Agent集成导入成功")
    except ImportError as e:
        print(f"❌ Agent集成导入失败: {e}")
        return False

    print("\n✨ 所有导入测试通过！")
    print("\n📦 新的导入方式:")
    print("   from memory import HierarchicalMemoryManager, MemoryScope")
    print("   from memory.services import UserPreferenceService")
    print("   from memory.integration import AgentMemoryMixin")

    return True

if __name__ == "__main__":
    import sys

    success = test_imports()
    sys.exit(0 if success else 1)
