"""
Repository Interfaces

定义数据访问层的接口，用于抽象和标准化数据持久化操作。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TypeVar, Generic

from ..models.topic import Topic, TopicList
from ..models.research import ResearchResult, ResearchResults
from ..models.slide import Slide, SlideList
from ..models.presentation import Presentation, PresentationRequest


# 泛型类型变量
T = TypeVar('T')
ID = TypeVar('ID')


class IRepository(ABC, Generic[T, ID]):
    """
    通用仓储接口

    定义基本的数据访问操作。
    """

    @abstractmethod
    async def save(self, entity: T) -> T:
        """
        保存实体

        Args:
            entity: 要保存的实体

        Returns:
            保存后的实体
        """
        pass

    @abstractmethod
    async def find_by_id(self, id: ID) -> Optional[T]:
        """
        根据ID查找实体

        Args:
            id: 实体ID

        Returns:
            找到的实体，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def find_all(self) -> List[T]:
        """
        查找所有实体

        Returns:
            实体列表
        """
        pass

    @abstractmethod
    async def delete(self, id: ID) -> bool:
        """
        删除实体

        Args:
            id: 实体ID

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        更新实体

        Args:
            entity: 要更新的实体

        Returns:
            更新后的实体
        """
        pass


class IPresentationRepository(IRepository[Presentation, str]):
    """
    演示文稿仓储接口

    专门用于管理演示文稿的持久化。
    """

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[Presentation]:
        """
        根据用户ID查找演示文稿

        Args:
            user_id: 用户ID

        Returns:
            演示文稿列表
        """
        pass

    @abstractmethod
    async def find_by_status(
        self,
        status: str,
        user_id: Optional[str] = None
    ) -> List[Presentation]:
        """
        根据状态查找演示文稿

        Args:
            status: 状态
            user_id: 用户ID（可选）

        Returns:
            演示文稿列表
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        id: str,
        status: str
    ) -> bool:
        """
        更新演示文稿状态

        Args:
            id: 演示文稿ID
            status: 新状态

        Returns:
            是否更新成功
        """
        pass

    @abstractmethod
    async def update_progress(
        self,
        id: str,
        progress_data: Dict[str, Any]
    ) -> bool:
        """
        更新演示文稿进度

        Args:
            id: 演示文稿ID
            progress_data: 进度数据

        Returns:
            是否更新成功
        """
        pass


class IUserPreferenceRepository(ABC):
    """
    用户偏好仓储接口

    用于管理用户偏好设置。
    """

    @abstractmethod
    async def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户偏好

        Args:
            user_id: 用户ID

        Returns:
            用户偏好字典
        """
        pass

    @abstractmethod
    async def save_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """
        保存用户偏好

        Args:
            user_id: 用户ID
            preferences: 偏好设置

        Returns:
            是否保存成功
        """
        pass

    @abstractmethod
    async def update_preference(
        self,
        user_id: str,
        key: str,
        value: Any
    ) -> bool:
        """
        更新单个偏好设置

        Args:
            user_id: 用户ID
            key: 偏好键
            value: 偏好值

        Returns:
            是否更新成功
        """
        pass


class ICacheRepository(ABC):
    """
    缓存仓储接口

    用于管理缓存数据。
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），可选

        Returns:
            是否设置成功
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        pass


class IVectorRepository(ABC):
    """
    向量仓储接口

    用于向量相似度搜索和存储。
    """

    @abstractmethod
    async def store(
        self,
        content: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        存储向量

        Args:
            content: 文本内容
            namespace: 命名空间
            metadata: 元数据

        Returns:
            向量ID
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        namespace: str,
        k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        向量相似度搜索

        Args:
            query: 查询文本
            namespace: 命名空间
            k: 返回结果数量
            similarity_threshold: 相似度阈值

        Returns:
            搜索结果列表，每个结果包含 content, similarity, metadata
        """
        pass

    @abstractmethod
    async def delete(
        self,
        vector_id: str,
        namespace: str
    ) -> bool:
        """
        删除向量

        Args:
            vector_id: 向量ID
            namespace: 命名空间

        Returns:
            是否删除成功
        """
        pass


class ISessionRepository(ABC):
    """
    会话仓储接口

    用于管理会话状态。
    """

    @abstractmethod
    async def create_session(self, user_id: str) -> str:
        """
        创建新会话

        Args:
            user_id: 用户ID

        Returns:
            会话ID
        """
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话

        Args:
            session_id: 会话ID

        Returns:
            会话数据，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def update_session(
        self,
        session_id: str,
        state: Dict[str, Any]
    ) -> bool:
        """
        更新会话状态

        Args:
            session_id: 会话ID
            state: 会话状态

        Returns:
            是否更新成功
        """
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话ID

        Returns:
            是否删除成功
        """
        pass


if __name__ == "__main__":
    # 测试代码
    print("Repository interfaces defined successfully")
