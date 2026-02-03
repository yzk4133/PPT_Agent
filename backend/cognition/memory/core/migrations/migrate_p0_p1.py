#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - P0-P1新表
添加agent_decisions、tool_execution_feedback、shared_workspace_memory表
"""
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))

from models import Base, AgentDecision, ToolExecutionFeedback, SharedWorkspaceMemory
from database import DatabaseManager


def run_migration():
    """运行数据库迁移"""
    print("=" * 70)
    print(" 数据库迁移脚本 - P0-P1新功能 ")
    print("=" * 70)
    print("\n本脚本将添加以下新表:")
    print("  - agent_decisions (Agent决策追踪)")
    print("  - tool_execution_feedback (工具执行反馈)")
    print("  - shared_workspace_memory (Multi-Agent协作记忆)")
    print()

    # 获取数据库URL
    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/multiagent_ppt"
    )

    print(f"📊 数据库: {db_url.split('@')[1] if '@' in db_url else db_url}")

    # 确认
    response = input("\n是否继续? (y/n): ")
    if response.lower() != "y":
        print("❌ 已取消")
        return

    try:
        # 创建引擎
        engine = create_engine(db_url)

        print("\n📝 开始迁移...")

        # 检查表是否已存在
        with engine.connect() as conn:
            # 检查agent_decisions
            try:
                conn.execute(text("SELECT 1 FROM agent_decisions LIMIT 1"))
                print("⚠️  agent_decisions 表已存在，跳过")
                has_decisions = True
            except ProgrammingError:
                has_decisions = False

            # 检查tool_execution_feedback
            try:
                conn.execute(text("SELECT 1 FROM tool_execution_feedback LIMIT 1"))
                print("⚠️  tool_execution_feedback 表已存在，跳过")
                has_feedback = True
            except ProgrammingError:
                has_feedback = False

            # 检查shared_workspace_memory
            try:
                conn.execute(text("SELECT 1 FROM shared_workspace_memory LIMIT 1"))
                print("⚠️  shared_workspace_memory 表已存在，跳过")
                has_workspace = True
            except ProgrammingError:
                has_workspace = False

        # 创建新表
        if not (has_decisions and has_feedback and has_workspace):
            print("\n🔨 创建新表...")

            # 只创建不存在的表
            tables_to_create = []
            if not has_decisions:
                tables_to_create.append(AgentDecision.__table__)
                print("  ✓ agent_decisions")
            if not has_feedback:
                tables_to_create.append(ToolExecutionFeedback.__table__)
                print("  ✓ tool_execution_feedback")
            if not has_workspace:
                tables_to_create.append(SharedWorkspaceMemory.__table__)
                print("  ✓ shared_workspace_memory")

            # 创建表
            Base.metadata.create_all(engine, tables=tables_to_create)
            print("\n✅ 新表创建成功！")
        else:
            print("\n✅ 所有表已存在，无需迁移")

        # 创建索引
        print("\n📑 创建索引...")
        with engine.connect() as conn:
            # agent_decisions 索引
            try:
                conn.execute(
                    text(
                        """
                    CREATE INDEX IF NOT EXISTS idx_agent_session 
                    ON agent_decisions (agent_name, session_id)
                """
                    )
                )
                conn.execute(
                    text(
                        """
                    CREATE INDEX IF NOT EXISTS idx_decision_outcome 
                    ON agent_decisions (decision_type, outcome)
                """
                    )
                )
                print("  ✓ agent_decisions 索引")
            except Exception as e:
                print(f"  ⚠️  agent_decisions 索引创建失败: {e}")

            # tool_execution_feedback 索引
            try:
                conn.execute(
                    text(
                        """
                    CREATE INDEX IF NOT EXISTS idx_tool_session 
                    ON tool_execution_feedback (tool_name, session_id)
                """
                    )
                )
                conn.execute(
                    text(
                        """
                    CREATE INDEX IF NOT EXISTS idx_tool_success 
                    ON tool_execution_feedback (tool_name, success)
                """
                    )
                )
                print("  ✓ tool_execution_feedback 索引")
            except Exception as e:
                print(f"  ⚠️  tool_execution_feedback 索引创建失败: {e}")

            # shared_workspace_memory 索引
            try:
                conn.execute(
                    text(
                        """
                    CREATE INDEX IF NOT EXISTS idx_session_datatype 
                    ON shared_workspace_memory (session_id, data_type)
                """
                    )
                )
                conn.execute(
                    text(
                        """
                    CREATE INDEX IF NOT EXISTS idx_datakey_unique 
                    ON shared_workspace_memory (session_id, data_key)
                """
                    )
                )
                conn.execute(
                    text(
                        """
                    CREATE INDEX IF NOT EXISTS idx_expires_at 
                    ON shared_workspace_memory (expires_at)
                """
                    )
                )
                print("  ✓ shared_workspace_memory 索引")
            except Exception as e:
                print(f"  ⚠️  shared_workspace_memory 索引创建失败: {e}")

            conn.commit()

        print("\n✅ 索引创建成功！")

        # 验证
        print("\n🔍 验证表结构...")
        with engine.connect() as conn:
            # 验证agent_decisions
            result = conn.execute(
                text(
                    """
                SELECT COUNT(*) as count 
                FROM information_schema.columns 
                WHERE table_name = 'agent_decisions'
            """
                )
            )
            col_count = result.fetchone()[0]
            print(f"  ✓ agent_decisions: {col_count} 列")

            # 验证tool_execution_feedback
            result = conn.execute(
                text(
                    """
                SELECT COUNT(*) as count 
                FROM information_schema.columns 
                WHERE table_name = 'tool_execution_feedback'
            """
                )
            )
            col_count = result.fetchone()[0]
            print(f"  ✓ tool_execution_feedback: {col_count} 列")

            # 验证shared_workspace_memory
            result = conn.execute(
                text(
                    """
                SELECT COUNT(*) as count 
                FROM information_schema.columns 
                WHERE table_name = 'shared_workspace_memory'
            """
                )
            )
            col_count = result.fetchone()[0]
            print(f"  ✓ shared_workspace_memory: {col_count} 列")

        print("\n" + "=" * 70)
        print("✅ 迁移完成！")
        print("=" * 70)
        print("\n📋 接下来的步骤:")
        print("1. 在Agent中导入并使用新服务:")
        print("   from persistent_memory import AgentDecisionService")
        print("   from persistent_memory import ToolFeedbackService")
        print("   from persistent_memory import SharedWorkspaceService")
        print("   from persistent_memory import ContextWindowOptimizer")
        print()
        print("2. 运行集成演示:")
        print("   python demo_p0_p1_integration.py")
        print()
        print("3. 查看README.md了解详细使用方法")

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_migration()
