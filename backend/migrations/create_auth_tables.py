"""
Database Migration: Create Authentication Tables

This migration creates the tables needed for user authentication and authorization:
- users: User accounts
- roles: User roles (ADMIN, USER, GUEST)
- permissions: Permissions (ppt:generate, ppt:read, etc.)
- user_roles: User-role many-to-many relationship
- role_permissions: Role-permission many-to-many relationship
- refresh_tokens: Refresh token storage
"""

import logging
import os
from sqlalchemy import create_engine, text
from infrastructure.config.common_config import get_config

logger = logging.getLogger(__name__)


def migrate(database_url: str = None) -> bool:
    """
    Run migration to create authentication tables

    Args:
        database_url: PostgreSQL database URL (optional, will use config if not provided)

    Returns:
        True if migration succeeded, False otherwise
    """
    try:
        if not database_url:
            config = get_config()
            database_url = config.database.database_url

        # Create engine
        engine = create_engine(database_url)

        # Create tables using SQLAlchemy models
        from models import User, Role, Permission, RefreshToken, user_roles, role_permissions
        from memory.storage.models import Base

        # Create all tables
        with engine.begin() as conn:
            # Create the new authentication tables
            User.__table__.create(conn, checkfirst=True)
            Role.__table__.create(conn, checkfirst=True)
            Permission.__table__.create(conn, checkfirst=True)
            RefreshToken.__table__.create(conn, checkfirst=True)

            # Create association tables
            user_roles.create(conn, checkfirst=True)
            role_permissions.create(conn, checkfirst=True)

        logger.info("Authentication tables created successfully")

        # Seed default roles and permissions
        _seed_default_data(engine)

        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return False


def _seed_default_data(engine):
    """Seed default roles and permissions"""
    from models import Role, Permission
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        # Check if data already exists
        existing_roles = session.query(Role).count()
        if existing_roles > 0:
            logger.info("Roles already exist, skipping seed")
            return

        # Create default permissions
        permissions = [
            # PPT permissions
            Permission(name="ppt:generate", resource="ppt", action="generate", description="生成PPT"),
            Permission(name="ppt:read", resource="ppt", action="read", description="查看PPT"),
            Permission(name="ppt:update", resource="ppt", action="update", description="更新PPT"),
            Permission(name="ppt:delete", resource="ppt", action="delete", description="删除PPT"),

            # User permissions
            Permission(name="user:read", resource="user", action="read", description="查看用户信息"),
            Permission(name="user:update", resource="user", action="update", description="更新用户信息"),

            # Admin permissions
            Permission(name="admin:users", resource="admin", action="users", description="管理用户"),
            Permission(name="admin:settings", resource="admin", action="settings", description="系统设置"),
        ]

        for perm in permissions:
            session.add(perm)

        # Create default roles
        # Admin role - all permissions
        admin_role = Role(name="ADMIN", description="管理员", is_active=True)
        admin_role.permissions = permissions

        # User role - basic PPT operations
        user_role = Role(name="USER", description="普通用户", is_active=True)
        user_permissions = [p for p in permissions if p.resource in ["ppt", "user"]]
        user_role.permissions = user_permissions

        # Guest role - read-only
        guest_role = Role(name="GUEST", description="访客", is_active=True)
        guest_permissions = [p for p in permissions if p.action == "read"]
        guest_role.permissions = guest_permissions

        session.add(admin_role)
        session.add(user_role)
        session.add(guest_role)

        session.commit()
        logger.info("Default roles and permissions seeded successfully")


def rollback(database_url: str = None) -> bool:
    """
    Rollback migration by dropping authentication tables

    Args:
        database_url: PostgreSQL database URL (optional, will use config if not provided)

    Returns:
        True if rollback succeeded, False otherwise
    """
    try:
        if not database_url:
            config = get_config()
            database_url = config.database.database_url

        engine = create_engine(database_url)

        with engine.begin() as conn:
            # Drop association tables first
            conn.execute(text("DROP TABLE IF EXISTS user_roles CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS role_permissions CASCADE"))

            # Drop main tables
            conn.execute(text("DROP TABLE IF EXISTS refresh_tokens CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS roles CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS permissions CASCADE"))

        logger.info("Authentication tables dropped successfully")
        return True

    except Exception as e:
        logger.error(f"Rollback failed: {e}", exc_info=True)
        return False


def get_migration_status(database_url: str = None) -> dict:
    """
    Get the status of authentication tables migration

    Args:
        database_url: PostgreSQL database URL (optional, will use config if not provided)

    Returns:
        Dictionary with migration status information
    """
    status = {
        "tables": {},
        "roles_count": 0,
        "permissions_count": 0,
        "users_count": 0
    }

    try:
        if not database_url:
            config = get_config()
            database_url = config.database.database_url

        engine = create_engine(database_url)

        with engine.connect() as conn:
            # Check if tables exist
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename IN ('users', 'roles', 'permissions', 'refresh_tokens', 'user_roles', 'role_permissions')
            """))
            for row in result:
                status["tables"][row[0]] = True

            if "users" in status["tables"]:
                # Get counts
                result = conn.execute(text("SELECT COUNT(*) FROM roles"))
                status["roles_count"] = result.scalar()

                result = conn.execute(text("SELECT COUNT(*) FROM permissions"))
                status["permissions_count"] = result.scalar()

                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                status["users_count"] = result.scalar()

    except Exception as e:
        logger.error(f"Failed to get migration status: {e}", exc_info=True)

    return status


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    import argparse

    parser = argparse.ArgumentParser(description="Authentication tables migration")
    parser.add_argument("--database", help="PostgreSQL database URL")
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
        print(f"  Tables: {', '.join(status['tables'].keys()) if status['tables'] else 'None'}")
        print(f"  Roles: {status['roles_count']}")
        print(f"  Permissions: {status['permissions_count']}")
        print(f"  Users: {status['users_count']}")
