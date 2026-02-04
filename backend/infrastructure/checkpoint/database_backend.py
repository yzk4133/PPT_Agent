"""
Checkpoint Database Backend

Implements checkpoint persistence using database storage.
"""

import json
import logging
import sys
import os
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

# Add parent directory to path

from domain.models.checkpoint import Checkpoint
from domain.models.execution_mode import ExecutionMode
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import text, select, update, delete, insert, Table, Column, String, Integer, DateTime, MetaData
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class ICheckpointBackend(ABC):
    """
    Checkpoint存储后端接口

    定义checkpoint持久化的抽象接口。
    """

    @abstractmethod
    async def save(self, checkpoint: Checkpoint) -> bool:
        """保存checkpoint"""
        pass

    @abstractmethod
    async def load(self, task_id: str) -> Optional[Checkpoint]:
        """加载checkpoint"""
        pass

    @abstractmethod
    async def update(self, task_id: str, framework: Dict[str, Any]) -> bool:
        """更新checkpoint（用户修改大纲后）"""
        pass

    @abstractmethod
    async def delete(self, task_id: str) -> bool:
        """删除checkpoint"""
        pass

    @abstractmethod
    async def list_by_user(self, user_id: str, limit: int = 10) -> List[Checkpoint]:
        """列出用户的checkpoints"""
        pass

    @abstractmethod
    async def list_all(self) -> List[Checkpoint]:
        """列出所有checkpoint"""
        pass

@dataclass
class DatabaseConfig:
    """数据库配置"""
    db_path: str = "data/checkpoints.db"

class InMemoryCheckpointBackend(ICheckpointBackend):
    """
    内存checkpoint存储后端

    适用于开发和测试。
    """

    def __init__(self):
        """初始化内存存储"""
        self._checkpoints: Dict[str, Checkpoint] = {}
        logger.info("InMemoryCheckpointBackend initialized")

    async def save(self, checkpoint: Checkpoint) -> bool:
        """保存checkpoint到内存"""
        self._checkpoints[checkpoint.task_id] = checkpoint
        logger.debug(f"Checkpoint saved to memory: {checkpoint.task_id}")
        return True

    async def load(self, task_id: str) -> Optional[Checkpoint]:
        """从内存加载checkpoint"""
        return self._checkpoints.get(task_id)

    async def update(self, task_id: str, framework: Dict[str, Any]) -> bool:
        """更新checkpoint的框架"""
        checkpoint = self._checkpoints.get(task_id)
        if not checkpoint:
            return False

        checkpoint.update_framework(framework)
        logger.debug(f"Checkpoint framework updated: {task_id}")
        return True

    async def delete(self, task_id: str) -> bool:
        """从内存删除checkpoint"""
        if task_id in self._checkpoints:
            checkpoint = self._checkpoints[task_id]
            checkpoint.status = "deleted"
            del self._checkpoints[task_id]
            logger.debug(f"Checkpoint deleted from memory: {task_id}")
            return True
        return False

    async def list_by_user(self, user_id: str, limit: int = 10) -> List[Checkpoint]:
        """列出用户的checkpoints"""
        checkpoints = [
            cp for cp in self._checkpoints.values()
            if cp.user_id == user_id and cp.status != "deleted"
        ]
        # 按更新时间倒序排列
        checkpoints.sort(key=lambda x: x.updated_at, reverse=True)
        return checkpoints[:limit]

    async def list_all(self) -> List[Checkpoint]:
        """列出所有checkpoint"""
        return [
            cp for cp in self._checkpoints.values()
            if cp.status != "deleted"
        ]

    def clear(self) -> None:
        """清空所有checkpoint"""
        self._checkpoints.clear()

class DatabaseCheckpointBackend(ICheckpointBackend):
    """
    数据库checkpoint存储后端

    使用SQLite数据库持久化checkpoint数据。
    """

    def __init__(self, db_path: str = "data/checkpoints.db"):
        """
        初始化数据库后端

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._conn = None
        self._init_database()
        logger.info(f"DatabaseCheckpointBackend initialized: {db_path}")

    def _init_database(self) -> None:
        """初始化数据库表"""
        import sqlite3
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)

        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

        # 创建表
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                execution_mode TEXT NOT NULL,
                phase INTEGER NOT NULL,
                raw_user_input TEXT NOT NULL,
                structured_requirements TEXT NOT NULL,
                ppt_framework TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                status TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                parent_task_id TEXT,
                metadata TEXT DEFAULT '{}'
            )
        """)

        # 创建索引
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id
            ON agent_checkpoints(user_id)
        """)

        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status
            ON agent_checkpoints(status)
        """)

        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_updated_at
            ON agent_checkpoints(updated_at)
        """)

        self._conn.commit()
        logger.debug("Database table initialized")

    async def save(self, checkpoint: Checkpoint) -> bool:
        """保存checkpoint到数据库"""
        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO agent_checkpoints
                (task_id, user_id, execution_mode, phase, raw_user_input,
                 structured_requirements, ppt_framework, created_at, updated_at,
                 status, version, parent_task_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                checkpoint.task_id,
                checkpoint.user_id,
                checkpoint.execution_mode.value,
                checkpoint.phase,
                checkpoint.raw_user_input,
                json.dumps(checkpoint.structured_requirements, ensure_ascii=False),
                json.dumps(checkpoint.ppt_framework, ensure_ascii=False),
                checkpoint.created_at.isoformat(),
                checkpoint.updated_at.isoformat(),
                checkpoint.status,
                checkpoint.version,
                checkpoint.parent_task_id,
                json.dumps(checkpoint.metadata, ensure_ascii=False)
            ))
            self._conn.commit()
            logger.debug(f"Checkpoint saved to database: {checkpoint.task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False

    async def load(self, task_id: str) -> Optional[Checkpoint]:
        """从数据库加载checkpoint"""
        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT * FROM agent_checkpoints
                WHERE task_id = ? AND status != 'deleted'
                ORDER BY version DESC LIMIT 1
            """, (task_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_checkpoint(row)
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None

    async def update(self, task_id: str, framework: Dict[str, Any]) -> bool:
        """更新checkpoint的框架"""
        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                UPDATE agent_checkpoints
                SET ppt_framework = ?,
                    updated_at = ?,
                    version = version + 1
                WHERE task_id = ?
            """, (
                json.dumps(framework, ensure_ascii=False),
                datetime.now().isoformat(),
                task_id
            ))
            self._conn.commit()
            logger.debug(f"Checkpoint framework updated in database: {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update checkpoint framework: {e}")
            return False

    async def delete(self, task_id: str) -> bool:
        """软删除checkpoint"""
        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                UPDATE agent_checkpoints
                SET status = 'deleted'
                WHERE task_id = ?
            """, (task_id,))
            self._conn.commit()
            logger.debug(f"Checkpoint soft-deleted: {task_id}")
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete checkpoint: {e}")
            return False

    async def list_by_user(self, user_id: str, limit: int = 10) -> List[Checkpoint]:
        """列出用户的checkpoints"""
        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT * FROM agent_checkpoints
                WHERE user_id = ? AND status = 'editing'
                ORDER BY updated_at DESC
                LIMIT ?
            """, (user_id, limit))

            rows = cursor.fetchall()
            return [self._row_to_checkpoint(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []

    async def list_all(self) -> List[Checkpoint]:
        """列出所有checkpoint"""
        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT * FROM agent_checkpoints
                WHERE status != 'deleted'
                ORDER BY updated_at DESC
            """)

            rows = cursor.fetchall()
            return [self._row_to_checkpoint(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to list all checkpoints: {e}")
            return []

    def _row_to_checkpoint(self, row) -> Checkpoint:
        """将数据库行转换为Checkpoint对象"""
        return Checkpoint(
            task_id=row["task_id"],
            user_id=row["user_id"],
            execution_mode=ExecutionMode(row["execution_mode"]),
            phase=row["phase"],
            raw_user_input=row["raw_user_input"],
            structured_requirements=json.loads(row["structured_requirements"]),
            ppt_framework=json.loads(row["ppt_framework"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            status=row["status"],
            version=row["version"],
            parent_task_id=row["parent_task_id"],
            metadata=json.loads(row["metadata"])
        )

    def close(self) -> None:
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            logger.debug("Database connection closed")

class PostgresCheckpointBackend(ICheckpointBackend):
    """
    PostgreSQL checkpoint存储后端

    使用异步PostgreSQL数据库持久化checkpoint数据。
    """

    def __init__(self, session_factory: async_sessionmaker):
        """
        初始化PostgreSQL后端

        Args:
            session_factory: SQLAlchemy异步会话工厂
        """
        self.session_factory = session_factory
        logger.info("PostgresCheckpointBackend initialized")

    async def _init_table(self):
        """初始化数据库表（如果不存在）"""
        async with self.session_factory() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS agent_checkpoints (
                    id SERIAL PRIMARY KEY,
                    task_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    execution_mode TEXT NOT NULL,
                    phase INTEGER NOT NULL,
                    raw_user_input TEXT NOT NULL,
                    structured_requirements TEXT NOT NULL,
                    ppt_framework TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    parent_task_id TEXT,
                    metadata TEXT DEFAULT '{}'
                )
            """))

            # 创建索引
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_agent_checkpoints_user_id
                ON agent_checkpoints(user_id)
            """))

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_agent_checkpoints_status
                ON agent_checkpoints(status)
            """))

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_agent_checkpoints_updated_at
                ON agent_checkpoints(updated_at)
            """))

            await session.commit()
            logger.debug("PostgreSQL table and indexes initialized")

    async def save(self, checkpoint: Checkpoint) -> bool:
        """保存checkpoint到PostgreSQL"""
        try:
            async with self.session_factory() as session:
                await session.execute(text("""
                    INSERT INTO agent_checkpoints
                    (task_id, user_id, execution_mode, phase, raw_user_input,
                     structured_requirements, ppt_framework, created_at, updated_at,
                     status, version, parent_task_id, metadata)
                    VALUES (:task_id, :user_id, :execution_mode, :phase, :raw_user_input,
                     :structured_requirements, :ppt_framework, :created_at, :updated_at,
                     :status, :version, :parent_task_id, :metadata)
                    ON CONFLICT (task_id) DO UPDATE SET
                        user_id = EXCLUDED.user_id,
                        execution_mode = EXCLUDED.execution_mode,
                        phase = EXCLUDED.phase,
                        raw_user_input = EXCLUDED.raw_user_input,
                        structured_requirements = EXCLUDED.structured_requirements,
                        ppt_framework = EXCLUDED.ppt_framework,
                        updated_at = EXCLUDED.updated_at,
                        status = EXCLUDED.status,
                        version = EXCLUDED.version,
                        parent_task_id = EXCLUDED.parent_task_id,
                        metadata = EXCLUDED.metadata
                """), {
                    "task_id": checkpoint.task_id,
                    "user_id": checkpoint.user_id,
                    "execution_mode": checkpoint.execution_mode.value,
                    "phase": checkpoint.phase,
                    "raw_user_input": checkpoint.raw_user_input,
                    "structured_requirements": json.dumps(checkpoint.structured_requirements, ensure_ascii=False),
                    "ppt_framework": json.dumps(checkpoint.ppt_framework, ensure_ascii=False),
                    "created_at": checkpoint.created_at,
                    "updated_at": checkpoint.updated_at,
                    "status": checkpoint.status,
                    "version": checkpoint.version,
                    "parent_task_id": checkpoint.parent_task_id,
                    "metadata": json.dumps(checkpoint.metadata, ensure_ascii=False)
                })
                await session.commit()
                logger.debug(f"Checkpoint saved to PostgreSQL: {checkpoint.task_id}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to save checkpoint to PostgreSQL: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving checkpoint: {e}")
            return False

    async def load(self, task_id: str) -> Optional[Checkpoint]:
        """从PostgreSQL加载checkpoint"""
        try:
            async with self.session_factory() as session:
                result = await session.execute(text("""
                    SELECT * FROM agent_checkpoints
                    WHERE task_id = :task_id AND status != 'deleted'
                    ORDER BY version DESC LIMIT 1
                """), {"task_id": task_id})

                row = result.fetchone()
                if not row:
                    return None

                return self._row_to_checkpoint(row)
        except Exception as e:
            logger.error(f"Failed to load checkpoint from PostgreSQL: {e}")
            return None

    async def update(self, task_id: str, framework: Dict[str, Any]) -> bool:
        """更新checkpoint的框架"""
        try:
            async with self.session_factory() as session:
                await session.execute(text("""
                    UPDATE agent_checkpoints
                    SET ppt_framework = :ppt_framework,
                        updated_at = :updated_at,
                        version = version + 1
                    WHERE task_id = :task_id
                """), {
                    "ppt_framework": json.dumps(framework, ensure_ascii=False),
                    "updated_at": datetime.now(),
                    "task_id": task_id
                })
                await session.commit()
                logger.debug(f"Checkpoint framework updated in PostgreSQL: {task_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update checkpoint framework: {e}")
            return False

    async def delete(self, task_id: str) -> bool:
        """软删除checkpoint"""
        try:
            async with self.session_factory() as session:
                result = await session.execute(text("""
                    UPDATE agent_checkpoints
                    SET status = 'deleted'
                    WHERE task_id = :task_id
                """), {"task_id": task_id})
                await session.commit()
                logger.debug(f"Checkpoint soft-deleted in PostgreSQL: {task_id}")
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete checkpoint: {e}")
            return False

    async def list_by_user(self, user_id: str, limit: int = 10) -> List[Checkpoint]:
        """列出用户的checkpoints"""
        try:
            async with self.session_factory() as session:
                result = await session.execute(text("""
                    SELECT * FROM agent_checkpoints
                    WHERE user_id = :user_id AND status = 'editing'
                    ORDER BY updated_at DESC
                    LIMIT :limit
                """), {"user_id": user_id, "limit": limit})

                rows = result.fetchall()
                return [self._row_to_checkpoint(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []

    async def list_all(self) -> List[Checkpoint]:
        """列出所有checkpoint"""
        try:
            async with self.session_factory() as session:
                result = await session.execute(text("""
                    SELECT * FROM agent_checkpoints
                    WHERE status != 'deleted'
                    ORDER BY updated_at DESC
                """))

                rows = result.fetchall()
                return [self._row_to_checkpoint(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to list all checkpoints: {e}")
            return []

    def _row_to_checkpoint(self, row) -> Checkpoint:
        """将数据库行转换为Checkpoint对象"""
        return Checkpoint(
            task_id=row[1],  # task_id
            user_id=row[2],  # user_id
            execution_mode=ExecutionMode(row[3]),  # execution_mode
            phase=row[4],  # phase
            raw_user_input=row[5],  # raw_user_input
            structured_requirements=json.loads(row[6]),  # structured_requirements
            ppt_framework=json.loads(row[7]),  # ppt_framework
            created_at=row[8],  # created_at
            updated_at=row[9],  # updated_at
            status=row[10],  # status
            version=row[11],  # version
            parent_task_id=row[12],  # parent_task_id
            metadata=json.loads(row[13])  # metadata
        )

# 创建全局实例
_global_backend: Optional[ICheckpointBackend] = None

def get_checkpoint_backend() -> ICheckpointBackend:
    """获取全局checkpoint backend实例"""
    global _global_backend
    if _global_backend is None:
        _global_backend = InMemoryCheckpointBackend()
    return _global_backend

def set_checkpoint_backend(backend: ICheckpointBackend) -> None:
    """设置全局checkpoint backend实例"""
    global _global_backend
    _global_backend = backend

if __name__ == "__main__":
    # 测试代码
    import asyncio
    from domain.models.execution_mode import ExecutionMode

    async def test_backend():
        print("Testing InMemoryCheckpointBackend")
        print("=" * 60)

        backend = InMemoryCheckpointBackend()

        # 创建测试checkpoint
        checkpoint = Checkpoint(
            task_id="test_001",
            user_id="user_001",
            execution_mode=ExecutionMode.PHASE_1,
            phase=2,
            raw_user_input="测试输入",
            structured_requirements={"ppt_topic": "测试"},
            ppt_framework={"total_page": 10}
        )

        # 保存
        print("\n1. Saving checkpoint...")
        success = await backend.save(checkpoint)
        print(f"   Success: {success}")

        # 加载
        print("\n2. Loading checkpoint...")
        loaded = await backend.load("test_001")
        if loaded:
            print(f"   Loaded: {loaded.task_id}, phase={loaded.phase}")

        # 更新
        print("\n3. Updating framework...")
        new_framework = {"total_page": 15, "updated": True}
        success = await backend.update("test_001", new_framework)
        print(f"   Success: {success}")

        # 列出用户checkpoint
        print("\n4. Listing user checkpoints...")
        checkpoints = await backend.list_by_user("user_001")
        print(f"   Found {len(checkpoints)} checkpoints")

        # 删除
        print("\n5. Deleting checkpoint...")
        success = await backend.delete("test_001")
        print(f"   Success: {success}")

        print("\n" + "=" * 60)
        print("Testing DatabaseCheckpointBackend")
        print("=" * 60)

        db_backend = DatabaseCheckpointBackend("data/test_checkpoints.db")

        # 创建测试checkpoint
        checkpoint2 = Checkpoint(
            task_id="test_002",
            user_id="user_002",
            execution_mode=ExecutionMode.PHASE_1,
            phase=2,
            raw_user_input="数据库测试",
            structured_requirements={"ppt_topic": "数据库测试"},
            ppt_framework={"total_page": 20}
        )

        # 保存
        print("\n1. Saving to database...")
        success = await db_backend.save(checkpoint2)
        print(f"   Success: {success}")

        # 加载
        print("\n2. Loading from database...")
        loaded = await db_backend.load("test_002")
        if loaded:
            print(f"   Loaded: {loaded.task_id}, phase={loaded.phase}")

        db_backend.close()

    asyncio.run(test_backend())
