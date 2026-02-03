"""
三层内存架构数据库迁移脚本

创建longterm_memory表并设置必要的索引和扩展
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """执行数据库迁移"""

    # 获取数据库连接
    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/multiagent_ppt"
    )

    logger.info(f"Connecting to database...")
    engine = create_engine(db_url)

    try:
        with engine.connect() as conn:
            # 1. 检查并启用pgvector扩展
            logger.info("Checking pgvector extension...")
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                logger.info("✓ pgvector extension enabled")
            except SQLAlchemyError as e:
                logger.warning(f"Failed to enable pgvector: {e}")
                logger.warning("Continuing without vector support...")

            # 2. 检查表是否已存在
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()

            if "longterm_memory" in existing_tables:
                logger.info("⚠ longterm_memory table already exists")
                response = input("Drop and recreate? (yes/no): ")
                if response.lower() == "yes":
                    conn.execute(text("DROP TABLE IF EXISTS longterm_memory CASCADE"))
                    conn.commit()
                    logger.info("✓ Dropped existing table")
                else:
                    logger.info("Skipping table creation")
                    return

            # 3. 创建longterm_memory表
            logger.info("Creating longterm_memory table...")

            create_table_sql = """
            CREATE TABLE longterm_memory (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                
                -- 内存键和作用域
                memory_key VARCHAR(500) NOT NULL,
                scope VARCHAR(50) NOT NULL,
                scope_id VARCHAR(255) NOT NULL,
                
                -- 数据内容
                content JSONB NOT NULL,
                content_text TEXT,
                
                -- 向量嵌入（1536维，OpenAI text-embedding-3-small）
                embedding vector(1536),
                
                -- 元数据
                importance FLOAT DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                session_count INTEGER DEFAULT 0,
                tags JSONB DEFAULT '[]'::jsonb,
                
                -- 提升信息
                promoted_from_layer VARCHAR(20),
                promotion_reason VARCHAR(50),
                promotion_timestamp TIMESTAMP,
                
                -- 时间戳
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """

            conn.execute(text(create_table_sql))
            conn.commit()
            logger.info("✓ Table created")

            # 4. 创建索引
            logger.info("Creating indexes...")

            indexes = [
                # 作用域索引
                (
                    "idx_longterm_scope",
                    "CREATE INDEX idx_longterm_scope ON longterm_memory(scope, scope_id)",
                ),
                # 唯一键索引
                (
                    "idx_longterm_key_scope",
                    "CREATE UNIQUE INDEX idx_longterm_key_scope ON longterm_memory(memory_key, scope, scope_id)",
                ),
                # 重要性索引（用于筛选高价值数据）
                (
                    "idx_longterm_importance",
                    "CREATE INDEX idx_longterm_importance ON longterm_memory(importance)",
                ),
                # 最后访问时间索引（用于清理过期数据）
                (
                    "idx_longterm_last_accessed",
                    "CREATE INDEX idx_longterm_last_accessed ON longterm_memory(last_accessed)",
                ),
                # JSONB GIN索引（用于标签搜索）
                (
                    "idx_longterm_tags",
                    "CREATE INDEX idx_longterm_tags ON longterm_memory USING GIN(tags)",
                ),
                # 向量相似度索引（IVFFlat算法，100个聚类）
                (
                    "idx_longterm_embedding",
                    "CREATE INDEX idx_longterm_embedding ON longterm_memory USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)",
                ),
            ]

            for idx_name, idx_sql in indexes:
                try:
                    conn.execute(text(idx_sql))
                    logger.info(f"  ✓ {idx_name}")
                except SQLAlchemyError as e:
                    if "vector" in idx_name.lower():
                        logger.warning(
                            f"  ⚠ {idx_name} skipped (pgvector not available)"
                        )
                    else:
                        logger.error(f"  ✗ {idx_name}: {e}")
                        raise

            conn.commit()
            logger.info("✓ All indexes created")

            # 5. 创建更新时间戳的触发器
            logger.info("Creating update timestamp trigger...")

            trigger_sql = """
            CREATE OR REPLACE FUNCTION update_longterm_memory_timestamp()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            CREATE TRIGGER trg_longterm_memory_update
            BEFORE UPDATE ON longterm_memory
            FOR EACH ROW
            EXECUTE FUNCTION update_longterm_memory_timestamp();
            """

            conn.execute(text(trigger_sql))
            conn.commit()
            logger.info("✓ Trigger created")

            # 6. 验证表结构
            logger.info("Verifying table structure...")

            result = conn.execute(
                text(
                    """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'longterm_memory'
                ORDER BY ordinal_position
            """
                )
            )

            columns = result.fetchall()
            logger.info(f"✓ Table has {len(columns)} columns:")
            for col_name, col_type, nullable in columns:
                logger.info(f"  - {col_name}: {col_type} (nullable={nullable})")

            # 7. 插入测试数据
            logger.info("Inserting test data...")

            test_data_sql = """
            INSERT INTO longterm_memory 
            (memory_key, scope, scope_id, content, content_text, importance, tags)
            VALUES
            ('test:system_config', 'user', 'system', 
             '{"version": "1.0", "env": "production"}'::jsonb,
             'version 1.0 production',
             0.9,
             '["system", "config"]'::jsonb),
            
            ('test:user_preference', 'user', 'user_test_123',
             '{"language": "zh-CN", "theme": "dark"}'::jsonb,
             'language zh-CN theme dark',
             0.7,
             '["user", "preference"]'::jsonb)
            """

            conn.execute(text(test_data_sql))
            conn.commit()
            logger.info("✓ Test data inserted")

            # 8. 验证数据
            result = conn.execute(text("SELECT COUNT(*) FROM longterm_memory"))
            count = result.scalar()
            logger.info(f"✓ Table contains {count} test records")

            logger.info("\n" + "=" * 60)
            logger.info("✓ Migration completed successfully!")
            logger.info("=" * 60)

            logger.info("\n下一步：")
            logger.info("1. 运行 demo_hierarchical_memory.py 测试三层架构")
            logger.info("2. 集成到现有Agent服务中")
            logger.info("3. 使用 HierarchicalMemoryManager 替换直接数据库访问")

    except SQLAlchemyError as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        engine.dispose()


def rollback_migration():
    """回滚迁移"""
    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/multiagent_ppt"
    )

    logger.info("Rolling back migration...")
    engine = create_engine(db_url)

    try:
        with engine.connect() as conn:
            # 删除触发器和函数
            conn.execute(
                text(
                    "DROP TRIGGER IF EXISTS trg_longterm_memory_update ON longterm_memory"
                )
            )
            conn.execute(
                text("DROP FUNCTION IF EXISTS update_longterm_memory_timestamp()")
            )

            # 删除表
            conn.execute(text("DROP TABLE IF EXISTS longterm_memory CASCADE"))
            conn.commit()

            logger.info("✓ Rollback completed")

    except SQLAlchemyError as e:
        logger.error(f"❌ Rollback failed: {e}")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate database for hierarchical memory"
    )
    parser.add_argument(
        "--rollback", action="store_true", help="Rollback migration (drop table)"
    )

    args = parser.parse_args()

    if args.rollback:
        rollback_migration()
    else:
        run_migration()
