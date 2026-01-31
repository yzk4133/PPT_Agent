#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库模型定义
使用SQLAlchemy ORM + pgvector扩展
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, Float, Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # 如果pgvector未安装，使用占位符
    Vector = None

Base = declarative_base()


class Session(Base):
    """会话表 - 存储Agent会话状态"""

    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    app_name = Column(String(255), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, index=True)

    # 使用JSONB存储会话状态（支持索引和查询）
    state = Column(JSONB, nullable=False, default=dict)

    # 乐观锁版本号
    version = Column(Integer, nullable=False, default=1)

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 会话元数据
    metadata = Column(JSONB, default=dict)

    __table_args__ = (
        # 复合唯一索引：同一个app下user的session唯一
        Index("idx_user_app_session", "user_id", "app_name", "session_id", unique=True),
        Index("idx_updated_at", "updated_at"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "app_name": self.app_name,
            "session_id": self.session_id,
            "state": self.state,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


class UserProfile(Base):
    """用户配置表 - 存储用户偏好"""

    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, unique=True, index=True)

    # 用户偏好配置（JSONB格式，灵活存储）
    preferences = Column(JSONB, nullable=False, default=dict)
    # 示例结构：
    # {
    #   "language": "EN-US",
    #   "default_slides": 10,
    #   "style": "professional",
    #   "color_scheme": "blue",
    #   "font_size": "medium"
    # }

    # 使用统计
    total_sessions = Column(Integer, default=0)
    successful_generations = Column(Integer, default=0)

    # 满意度评分（基于修改次数反推）
    avg_satisfaction_score = Column(Float, default=0.0)

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 乐观锁版本号
    version = Column(Integer, nullable=False, default=1)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "preferences": self.preferences,
            "total_sessions": self.total_sessions,
            "successful_generations": self.successful_generations,
            "avg_satisfaction_score": self.avg_satisfaction_score,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }


class VectorMemory(Base):
    """向量记忆表 - 使用pgvector存储语义向量"""

    __tablename__ = "vector_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 命名空间隔离（research_findings / outlines / slide_templates）
    namespace = Column(String(100), nullable=False, index=True)

    # 内容和元数据
    content = Column(Text, nullable=False)
    metadata = Column(JSONB, default=dict)

    # 向量字段（1536维 - OpenAI text-embedding-3-small）
    embedding = Column(Vector(1536)) if Vector else Column(Text)

    # 使用统计
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime)

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 用户ID（可选，用于用户特定的记忆）
    user_id = Column(String(255), index=True)

    __table_args__ = (
        Index("idx_namespace_created", "namespace", "created_at"),
        Index("idx_user_namespace", "user_id", "namespace"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "namespace": self.namespace,
            "content": self.content,
            "metadata": self.metadata,
            "access_count": self.access_count,
            "last_accessed_at": (
                self.last_accessed_at.isoformat() if self.last_accessed_at else None
            ),
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id,
        }


class ConversationHistory(Base):
    """会话历史表 - 存储对话记录"""

    __tablename__ = "conversation_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 关联会话
    session_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)

    # 消息内容
    role = Column(String(50), nullable=False)  # user / assistant / system
    content = Column(Text, nullable=False)

    # 元数据（附加信息）
    metadata = Column(JSONB, default=dict)

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (Index("idx_session_created", "session_id", "created_at"),)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


# 创建向量索引的SQL（需要手动执行或通过迁移脚本）
CREATE_VECTOR_INDEX_SQL = """
-- 创建pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建向量索引（HNSW算法，适合高维向量）
CREATE INDEX IF NOT EXISTS idx_vector_memories_embedding 
ON vector_memories USING hnsw (embedding vector_cosine_ops);

-- 创建GIN索引加速JSONB查询
CREATE INDEX IF NOT EXISTS idx_sessions_state_gin ON sessions USING gin (state);
CREATE INDEX IF NOT EXISTS idx_user_profiles_preferences_gin ON user_profiles USING gin (preferences);
CREATE INDEX IF NOT EXISTS idx_vector_memories_metadata_gin ON vector_memories USING gin (metadata);
"""
