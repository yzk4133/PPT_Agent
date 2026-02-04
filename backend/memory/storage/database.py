#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库连接管理
"""
import os
import logging
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
from contextlib import contextmanager

from .models import Base, CREATE_VECTOR_INDEX_SQL

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器 - 单例模式"""

    _instance: Optional["DatabaseManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/multiagent_ppt",
        )

        # 创建引擎
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # 连接前先ping检查可用性
            pool_recycle=3600,  # 1小时回收连接
            echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # 是否打印SQL
        )

        # 创建会话工厂
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        self._initialized = True
        logger.info(
            f"DatabaseManager initialized with URL: {self._mask_password(self.database_url)}"
        )

    @staticmethod
    def _mask_password(url: str) -> str:
        """隐藏密码显示"""
        if "@" in url:
            parts = url.split("@")
            if ":" in parts[0]:
                user_pass = parts[0].rsplit(":", 1)
                return f"{user_pass[0]}:****@{parts[1]}"
        return url

    def init_db(self, drop_existing: bool = False):
        """初始化数据库表"""
        try:
            if drop_existing:
                logger.warning("Dropping all existing tables...")
                Base.metadata.drop_all(bind=self.engine)

            # 创建所有表
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")

            # 创建pgvector扩展和索引
            self._create_vector_extension()

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _create_vector_extension(self):
        """创建pgvector扩展和向量索引"""
        try:
            with self.engine.connect() as conn:
                # 执行创建扩展和索引的SQL
                for statement in CREATE_VECTOR_INDEX_SQL.strip().split(";"):
                    statement = statement.strip()
                    if statement:
                        conn.execute(text(statement))
                        conn.commit()
            logger.info("pgvector extension and indexes created successfully")
        except Exception as e:
            logger.warning(
                f"Failed to create pgvector extension (may already exist): {e}"
            )

    @contextmanager
    def get_session(self):
        """获取数据库会话（上下文管理器）"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def health_check(self) -> bool:
        """健康检查"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None

def get_db() -> DatabaseManager:
    """获取数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

def get_db_session() -> Session:
    """获取数据库会话（用于依赖注入）"""
    db = get_db()
    return db.SessionLocal()

# 初始化脚本（仅在直接运行时执行）
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    db = get_db()

    if "--init" in sys.argv:
        drop = "--drop" in sys.argv
        db.init_db(drop_existing=drop)
        print("✅ Database initialized successfully!")

    elif "--health" in sys.argv:
        if db.health_check():
            print("✅ Database is healthy!")
            sys.exit(0)
        else:
            print("❌ Database health check failed!")
            sys.exit(1)

    else:
        print("Usage:")
        print("  python database.py --init        # Initialize database")
        print("  python database.py --init --drop # Drop and recreate tables")
        print("  python database.py --health      # Health check")
