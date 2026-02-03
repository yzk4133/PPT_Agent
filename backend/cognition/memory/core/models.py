#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库模型定义
使用SQLAlchemy ORM + pgvector扩展
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, Float, Index, text, Boolean, func
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


class AgentDecision(Base):
    """Agent决策表 - 追踪Agent的决策过程和结果"""

    __tablename__ = "agent_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 关联会话
    session_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)

    # 决策信息
    agent_name = Column(String(255), nullable=False, index=True)  # 做决策的Agent
    decision_type = Column(
        String(100), nullable=False
    )  # tool_selection / sub_agent_routing / parameter_choice

    # 决策上下文（决策时的状态）
    context = Column(JSONB, nullable=False, default=dict)
    # 示例: {"user_query": "...", "available_tools": [...], "current_state": {...}}

    # 决策结果
    selected_action = Column(String(255), nullable=False)  # 选择的工具/子Agent/参数
    alternatives = Column(JSONB, default=list)  # 考虑过的其他选项
    reasoning = Column(Text)  # Agent的推理过程（如有）
    confidence_score = Column(Float)  # 决策置信度 0.0-1.0

    # 执行结果
    outcome = Column(String(50))  # success / failure / partial / timeout
    execution_time_ms = Column(Integer)  # 执行耗时（毫秒）
    error_message = Column(Text)  # 错误信息（如有）

    # 资源消耗
    token_usage = Column(JSONB)  # {"prompt": 100, "completion": 50, "total": 150}

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_agent_session", "agent_name", "session_id"),
        Index("idx_decision_outcome", "decision_type", "outcome"),
        Index("idx_created_at", "created_at"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "user_id": self.user_id,
            "agent_name": self.agent_name,
            "decision_type": self.decision_type,
            "context": self.context,
            "selected_action": self.selected_action,
            "alternatives": self.alternatives,
            "reasoning": self.reasoning,
            "confidence_score": self.confidence_score,
            "outcome": self.outcome,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message,
            "token_usage": self.token_usage,
            "created_at": self.created_at.isoformat(),
        }


class ToolExecutionFeedback(Base):
    """工具执行反馈表 - 追踪工具调用效果"""

    __tablename__ = "tool_execution_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 关联会话和决策
    session_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    decision_id = Column(UUID(as_uuid=True), index=True)  # 关联到AgentDecision

    # 工具信息
    tool_name = Column(String(255), nullable=False, index=True)
    agent_name = Column(String(255), nullable=False)  # 调用工具的Agent

    # 输入输出
    input_params = Column(JSONB, nullable=False)  # 工具输入参数
    output_summary = Column(JSONB)  # 输出摘要（避免存储大文本）
    # 示例: {"result_count": 5, "keywords_found": [...], "data_size_kb": 12}

    # 使用情况
    used_in_final_output = Column(Boolean, default=None)  # 结果是否被最终使用
    relevance_score = Column(Float)  # 结果相关性评分 0.0-1.0
    user_feedback = Column(String(50))  # positive / negative / neutral （如有显式反馈）

    # 性能指标
    latency_ms = Column(Integer, nullable=False)  # 工具执行延迟
    success = Column(Boolean, nullable=False)
    error_type = Column(String(100))  # timeout / api_error / invalid_params

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_tool_session", "tool_name", "session_id"),
        Index("idx_tool_success", "tool_name", "success"),
        Index("idx_created_at", "created_at"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "user_id": self.user_id,
            "decision_id": str(self.decision_id) if self.decision_id else None,
            "tool_name": self.tool_name,
            "agent_name": self.agent_name,
            "input_params": self.input_params,
            "output_summary": self.output_summary,
            "used_in_final_output": self.used_in_final_output,
            "relevance_score": self.relevance_score,
            "user_feedback": self.user_feedback,
            "latency_ms": self.latency_ms,
            "success": self.success,
            "error_type": self.error_type,
            "created_at": self.created_at.isoformat(),
        }


class SharedWorkspaceMemory(Base):
    """共享工作空间记忆表 - Multi-Agent协作数据共享"""

    __tablename__ = "shared_workspace_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 关联会话
    session_id = Column(String(255), nullable=False, index=True)

    # 共享数据信息
    data_type = Column(
        String(100), nullable=False, index=True
    )  # research_result / outline / agent_output
    source_agent = Column(String(255), nullable=False)  # 产生数据的Agent
    data_key = Column(String(255), nullable=False)  # 数据唯一标识

    # 数据内容
    data_content = Column(JSONB, nullable=False)  # 实际共享的数据
    data_summary = Column(Text)  # 数据摘要（供快速检索）

    # 访问控制
    target_agents = Column(JSONB)  # 允许访问的Agent列表（null表示所有Agent可访问）
    access_count = Column(Integer, default=0)  # 被访问次数
    last_accessed_by = Column(String(255))  # 最后访问的Agent
    last_accessed_at = Column(DateTime)

    # 生命周期
    ttl_minutes = Column(Integer, default=60)  # 数据有效期（分钟）
    expires_at = Column(DateTime, index=True)  # 过期时间
    is_archived = Column(Boolean, default=False)  # 是否已归档

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_session_datatype", "session_id", "data_type"),
        Index("idx_datakey_unique", "session_id", "data_key", unique=True),
        Index("idx_source_agent", "source_agent"),
        Index("idx_expires_at", "expires_at"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "data_type": self.data_type,
            "source_agent": self.source_agent,
            "data_key": self.data_key,
            "data_content": self.data_content,
            "data_summary": self.data_summary,
            "target_agents": self.target_agents,
            "access_count": self.access_count,
            "last_accessed_by": self.last_accessed_by,
            "last_accessed_at": (
                self.last_accessed_at.isoformat() if self.last_accessed_at else None
            ),
            "ttl_minutes": self.ttl_minutes,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_archived": self.is_archived,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
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
