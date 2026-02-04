"""
Database Migration: Create Checkpoints Table

This migration creates the agent_checkpoints table for storing
PPT generation checkpoints for two-phase workflow.
"""

import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def migrate(database_path: str = "data/checkpoints.db") -> bool:
    """
    Run migration to create checkpoints table

    Args:
        database_path: Path to the SQLite database file

    Returns:
        True if migration succeeded, False otherwise
    """
    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(database_path) or ".", exist_ok=True)

        # Connect to database
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Create checkpoints table
        cursor.execute("""
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

        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_checkpoints_user_id
            ON agent_checkpoints(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_checkpoints_status
            ON agent_checkpoints(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_checkpoints_updated_at
            ON agent_checkpoints(updated_at)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_checkpoints_task_id
            ON agent_checkpoints(task_id)
        """)

        conn.commit()
        conn.close()

        logger.info(f"Migration completed successfully: {database_path}")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

def rollback(database_path: str = "data/checkpoints.db") -> bool:
    """
    Rollback migration by dropping checkpoints table

    Args:
        database_path: Path to the SQLite database file

    Returns:
        True if rollback succeeded, False otherwise
    """
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Drop table
        cursor.execute("DROP TABLE IF EXISTS agent_checkpoints")

        # Drop indexes
        cursor.execute("DROP INDEX IF EXISTS idx_checkpoints_user_id")
        cursor.execute("DROP INDEX IF EXISTS idx_checkpoints_status")
        cursor.execute("DROP INDEX IF EXISTS idx_checkpoints_updated_at")
        cursor.execute("DROP INDEX IF EXISTS idx_checkpoints_task_id")

        conn.commit()
        conn.close()

        logger.info(f"Rollback completed: {database_path}")
        return True

    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        return False

def get_migration_status(database_path: str = "data/checkpoints.db") -> dict:
    """
    Get the status of checkpoints table migration

    Args:
        database_path: Path to the SQLite database file

    Returns:
        Dictionary with migration status information
    """
    status = {
        "database_exists": os.path.exists(database_path),
        "table_exists": False,
        "indexes": {},
        "row_count": 0
    }

    if not status["database_exists"]:
        return status

    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='agent_checkpoints'
        """)
        status["table_exists"] = cursor.fetchone() is not None

        if status["table_exists"]:
            # Check indexes
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND tbl_name='agent_checkpoints'
            """)
            for row in cursor.fetchall():
                status["indexes"][row[0]] = True

            # Get row count
            cursor.execute("SELECT COUNT(*) FROM agent_checkpoints")
            status["row_count"] = cursor.fetchone()[0]

        conn.close()

    except Exception as e:
        logger.error(f"Failed to get migration status: {e}")

    return status

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    import argparse

    parser = argparse.ArgumentParser(description="Checkpoints table migration")
    parser.add_argument("--database", default="data/checkpoints.db",
                       help="Path to SQLite database")
    parser.add_argument("--action", choices=["migrate", "rollback", "status"],
                       default="migrate", help="Migration action")

    args = parser.parse_args()

    if args.action == "migrate":
        success = migrate(args.database)
        if success:
            print("✓ Migration completed successfully")
        else:
            print("✗ Migration failed")
            exit(1)

    elif args.action == "rollback":
        success = rollback(args.database)
        if success:
            print("✓ Rollback completed successfully")
        else:
            print("✗ Rollback failed")
            exit(1)

    elif args.action == "status":
        status = get_migration_status(args.database)
        print("Migration Status:")
        print(f"  Database exists: {status['database_exists']}")
        print(f"  Table exists: {status['table_exists']}")
        print(f"  Indexes: {len(status['indexes'])}")
        print(f"  Row count: {status['row_count']}")
