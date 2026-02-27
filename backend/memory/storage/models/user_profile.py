"""
User Profile Model
兼容 MySQL 和 PostgreSQL
"""
from typing import Any, Dict, Optional
from sqlalchemy import Column, String, Integer, Float, Index, Text
from datetime import datetime
import uuid

from .base import Base, BaseModel


class UserProfile(BaseModel):
    """
    用户配置表 - 存储用户偏好

    存储用户的使用偏好、使用统计和满意度评分
    """

    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, unique=True, index=True)

    # 用户偏好配置（使用Text存储JSON，兼容MySQL和PostgreSQL）
    preferences = Column(Text, nullable=False, default="{}")

    # 使用统计
    total_sessions = Column(Integer, default=0)
    successful_generations = Column(Integer, default=0)

    # 满意度评分（基于修改次数反推）
    avg_satisfaction_score = Column(Float, default=0.0)

    # 乐观锁版本号
    version = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        Index("idx_user_satisfaction", "avg_satisfaction_score"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        import json
        preferences = json.loads(self.preferences) if self.preferences else {}

        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "preferences": preferences,
            "total_sessions": self.total_sessions,
            "successful_generations": self.successful_generations,
            "avg_satisfaction_score": self.avg_satisfaction_score,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }

    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        获取单个偏好设置

        Args:
            key: 偏好键
            default: 默认值

        Returns:
            偏好值或默认值
        """
        import json
        prefs = json.loads(self.preferences) if self.preferences else {}
        return prefs.get(key, default)

    def set_preference(self, key: str, value: Any) -> None:
        """
        设置单个偏好

        Args:
            key: 偏好键
            value: 偏好值
        """
        import json
        prefs = json.loads(self.preferences) if self.preferences else {}
        prefs[key] = value
        self.preferences = json.dumps(prefs, ensure_ascii=False)

    def increment_session_count(self) -> int:
        """增加会话计数"""
        self.total_sessions += 1
        return self.total_sessions

    def increment_generation_count(self) -> int:
        """增加生成计数"""
        self.successful_generations += 1
        return self.successful_generations

    def update_satisfaction_score(self, score: float) -> None:
        """
        更新满意度评分（使用移动平均）

        Args:
            score: 新的满意度评分 (0.0-1.0)
        """
        if self.avg_satisfaction_score == 0.0:
            self.avg_satisfaction_score = score
        else:
            # 简单的移动平均
            alpha = 0.3  # 平滑因子
            self.avg_satisfaction_score = (
                alpha * score + (1 - alpha) * self.avg_satisfaction_score
            )

    @property
    def preferences_dict(self) -> Dict[str, Any]:
        """获取preferences为字典"""
        import json
        return json.loads(self.preferences) if self.preferences else {}

    @preferences_dict.setter
    def preferences_dict(self, value: Dict[str, Any]):
        """设置preferences为字典"""
        import json
        self.preferences = json.dumps(value, ensure_ascii=False)
