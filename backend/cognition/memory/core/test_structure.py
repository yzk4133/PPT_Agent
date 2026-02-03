"""
验证新的目录结构是否正常工作
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    """测试所有导入是否正常"""

    print("测试基础模块导入...")
    try:
        from persistent_memory import DatabaseManager, RedisCache

        print("✓ 基础模块导入成功")
    except Exception as e:
        print(f"✗ 基础模块导入失败: {e}")
        return False

    print("\n测试三层架构核心导入...")
    try:
        from persistent_memory import (
            HierarchicalMemoryManager,
            MemoryScope,
            MemoryLayer,
            get_global_memory_manager,
        )

        print("✓ 三层架构核心导入成功")
    except Exception as e:
        print(f"✗ 三层架构核心导入失败: {e}")
        return False

    print("\n测试业务服务导入...")
    try:
        from persistent_memory import (
            PostgresSessionService,
            UserPreferenceService,
            AgentDecisionService,
            ContextWindowOptimizer,
        )

        print("✓ 业务服务导入成功")
    except Exception as e:
        print(f"✗ 业务服务导入失败: {e}")
        return False

    print("\n" + "=" * 50)
    print("所有导入测试通过！✓")
    print("=" * 50)

    print("\n目录结构:")
    print("persistent_memory/")
    print("├── core/              # 三层内存架构核心")
    print("├── services/          # 业务服务层")
    print("├── demos/             # 演示和测试")
    print("├── migrations/        # 数据库迁移")
    print("├── database.py        # 数据库管理")
    print("├── models.py          # 数据模型")
    print("├── redis_cache.py     # Redis缓存")
    print("└── README.md          # 使用文档")

    return True


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
