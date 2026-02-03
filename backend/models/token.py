"""
Token 模型
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from memory.storage.models import Base
import uuid


class RefreshToken(Base):
    """刷新令牌表"""

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_revoked = Column(Boolean, default=False, index=True)
    revoked_at = Column(DateTime)

    # 关系
    user = relationship("User", back_populates="refresh_tokens")

    @classmethod
    def create(cls, user_id: uuid.UUID, token: str, expires_days: int = 30):
        """创建刷新令牌"""
        return cls(
            user_id=user_id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(days=expires_days)
        )

    def is_valid(self) -> bool:
        """检查令牌是否有效"""
        return not self.is_revoked and self.expires_at > datetime.utcnow()

    def revoke(self):
        """撤销令牌"""
        self.is_revoked = True
        self.revoked_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_revoked": self.is_revoked,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
        }

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, is_revoked={self.is_revoked})>"
