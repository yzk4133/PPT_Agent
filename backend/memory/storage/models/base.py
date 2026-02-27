"""
Base Models for Memory System
兼容 MySQL 和 PostgreSQL
"""
from datetime import datetime
from typing import Any, Dict
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BaseModel(Base):
    """
    模型基类

    提供通用的时间戳字段和转换方法
    """

    __abstract__ = True

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        子类应该实现此方法以提供具体的转换逻辑
        """
        raise NotImplementedError(f"{self.__class__.__name__}.to_dict() must be implemented")
