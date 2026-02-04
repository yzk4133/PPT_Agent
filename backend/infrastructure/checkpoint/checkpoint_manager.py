"""
Checkpoint Manager

Manages checkpoint persistence for two-phase PPT generation workflow.
"""

import logging
import sys
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add parent directory to path

from domain.models.checkpoint import Checkpoint, CheckpointSummary
from .database_backend import ICheckpointBackend, DatabaseCheckpointBackend

logger = logging.getLogger(__name__)

class CheckpointManager:
    """
    Checkpoint管理器

    负责checkpoint的保存、加载、更新和查询。

    使用示例:
        manager = CheckpointManager(DatabaseCheckpointBackend(db_session))

        # 保存checkpoint
        checkpoint = await manager.save_checkpoint(
            task_id="task_001",
            user_id="user_001",
            execution_mode=ExecutionMode.PHASE_1,
            phase=2,
            raw_input="做一份AI介绍PPT",
            requirements=requirement_dict,
            framework=framework_dict
        )

        # 加载checkpoint
        checkpoint = await manager.load_checkpoint("task_001")

        # 更新框架
        await manager.update_framework("task_001", new_framework)

        # 获取用户所有checkpoint
        checkpoints = await manager.get_user_checkpoints("user_001")
    """

    def __init__(self, backend: ICheckpointBackend):
        """
        初始化CheckpointManager

        Args:
            backend: Checkpoint存储后端
        """
        self.backend = backend
        logger.info("CheckpointManager initialized")

    async def save_checkpoint(
        self,
        task_id: str,
        user_id: str,
        execution_mode,
        phase: int,
        raw_input: str,
        requirements: Dict[str, Any],
        framework: Dict[str, Any],
        parent_task_id: Optional[str] = None
    ) -> Checkpoint:
        """
        创建并保存checkpoint

        Args:
            task_id: 任务ID
            user_id: 用户ID
            execution_mode: 执行模式
            phase: 当前阶段
            raw_input: 原始用户输入
            requirements: 结构化需求
            framework: PPT框架
            parent_task_id: 父任务ID

        Returns:
            保存的Checkpoint对象
        """
        checkpoint = Checkpoint(
            task_id=task_id,
            user_id=user_id,
            execution_mode=execution_mode,
            phase=phase,
            raw_user_input=raw_input,
            structured_requirements=requirements,
            ppt_framework=framework,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status="editing",
            version=1,
            parent_task_id=parent_task_id
        )

        success = await self.backend.save(checkpoint)
        if not success:
            raise RuntimeError(f"Failed to save checkpoint: {task_id}")

        logger.info(f"Checkpoint saved: {task_id} (phase {phase}, user {user_id})")
        return checkpoint

    async def load_checkpoint(self, task_id: str) -> Optional[Checkpoint]:
        """
        加载checkpoint

        Args:
            task_id: 任务ID

        Returns:
            Checkpoint对象，如果不存在则返回None
        """
        checkpoint = await self.backend.load(task_id)

        if checkpoint:
            # 检查是否过期
            if checkpoint.is_expired():
                logger.warning(f"Checkpoint {task_id} is expired")
                await self.backend.delete(task_id)
                return None

            logger.info(f"Checkpoint loaded: {task_id} (phase {checkpoint.phase})")
        else:
            logger.warning(f"Checkpoint not found: {task_id}")

        return checkpoint

    async def update_framework(
        self,
        task_id: str,
        new_framework: Dict[str, Any]
    ) -> bool:
        """
        用户修改大纲后更新框架

        Args:
            task_id: 任务ID
            new_framework: 新的PPT框架

        Returns:
            是否更新成功
        """
        # 先加载checkpoint确保存在
        checkpoint = await self.load_checkpoint(task_id)
        if not checkpoint:
            logger.error(f"Cannot update framework: checkpoint not found: {task_id}")
            return False

        # 检查是否可编辑
        if not checkpoint.is_editable():
            logger.error(f"Cannot update framework: checkpoint is not editable: {task_id}")
            return False

        success = await self.backend.update(task_id, new_framework)
        if success:
            logger.info(f"Framework updated: {task_id}")
        else:
            logger.error(f"Failed to update framework: {task_id}")

        return success

    async def delete_checkpoint(self, task_id: str) -> bool:
        """
        删除checkpoint（软删除）

        Args:
            task_id: 任务ID

        Returns:
            是否删除成功
        """
        success = await self.backend.delete(task_id)
        if success:
            logger.info(f"Checkpoint deleted: {task_id}")
        else:
            logger.error(f"Failed to delete checkpoint: {task_id}")

        return success

    async def get_user_checkpoints(
        self,
        user_id: str,
        status_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[Checkpoint]:
        """
        获取用户的所有checkpoint

        Args:
            user_id: 用户ID
            status_filter: 状态过滤 (editing, completed, expired)
            limit: 最大返回数量

        Returns:
            Checkpoint列表
        """
        checkpoints = await self.backend.list_by_user(user_id, limit)

        # 状态过滤
        if status_filter:
            checkpoints = [cp for cp in checkpoints if cp.status == status_filter]

        logger.info(f"Retrieved {len(checkpoints)} checkpoints for user {user_id}")
        return checkpoints

    async def get_checkpoint_summaries(
        self,
        user_id: str,
        status_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[CheckpointSummary]:
        """
        获取用户的checkpoint摘要列表

        Args:
            user_id: 用户ID
            status_filter: 状态过滤
            limit: 最大返回数量

        Returns:
            CheckpointSummary列表
        """
        checkpoints = await self.get_user_checkpoints(user_id, status_filter, limit)
        return [CheckpointSummary.from_checkpoint(cp) for cp in checkpoints]

    async def mark_completed(self, task_id: str) -> bool:
        """
        标记checkpoint为已完成

        Args:
            task_id: 任务ID

        Returns:
            是否标记成功
        """
        checkpoint = await self.load_checkpoint(task_id)
        if not checkpoint:
            return False

        checkpoint.mark_completed()
        success = await self.backend.save(checkpoint)

        if success:
            logger.info(f"Checkpoint marked as completed: {task_id}")

        return success

    async def cleanup_expired(self, ttl_hours: int = 24) -> int:
        """
        清理过期的checkpoint

        Args:
            ttl_hours: 生存时间（小时）

        Returns:
            清理的checkpoint数量
        """
        # 获取所有editing状态的checkpoint
        all_checkpoints = await self.backend.list_all()

        expired_count = 0
        for checkpoint in all_checkpoints:
            if checkpoint.is_expired(ttl_hours):
                await self.backend.delete(checkpoint.task_id)
                expired_count += 1

        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired checkpoints")

        return expired_count

    async def get_checkpoint_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取checkpoint的摘要信息

        Args:
            task_id: 任务ID

        Returns:
            摘要信息字典，如果checkpoint不存在则返回None
        """
        checkpoint = await self.load_checkpoint(task_id)
        if not checkpoint:
            return None

        return checkpoint.get_summary()

# 全局checkpoint manager实例
_checkpoint_manager: Optional[CheckpointManager] = None

def get_checkpoint_manager() -> Optional[CheckpointManager]:
    """获取全局checkpoint manager实例"""
    return _checkpoint_manager

def set_checkpoint_manager(manager: CheckpointManager) -> None:
    """设置全局checkpoint manager实例"""
    global _checkpoint_manager
    _checkpoint_manager = manager

if __name__ == "__main__":
    # 测试代码
    import asyncio
    from domain.models.execution_mode import ExecutionMode

    async def test_checkpoint_manager():
        print("Testing CheckpointManager")
        print("=" * 60)

        # 创建内存后端（用于测试）
        from .database_backend import InMemoryCheckpointBackend

        backend = InMemoryCheckpointBackend()
        manager = CheckpointManager(backend)

        # 创建测试数据
        task_id = "task_test_001"
        user_id = "user_test_001"
        execution_mode = ExecutionMode.PHASE_1

        requirements = {
            "ppt_topic": "测试主题",
            "page_num": 10,
            "need_research": True
        }

        framework = {
            "total_page": 10,
            "ppt_framework": [
                {"page_no": 1, "title": "封面"}
            ]
        }

        # 保存checkpoint
        print("\n1. Saving checkpoint...")
        checkpoint = await manager.save_checkpoint(
            task_id=task_id,
            user_id=user_id,
            execution_mode=execution_mode,
            phase=2,
            raw_input="测试输入",
            requirements=requirements,
            framework=framework
        )
        print(f"   Checkpoint saved: {checkpoint.task_id}")

        # 加载checkpoint
        print("\n2. Loading checkpoint...")
        loaded = await manager.load_checkpoint(task_id)
        if loaded:
            print(f"   Checkpoint loaded: phase={loaded.phase}, status={loaded.status}")

        # 更新框架
        print("\n3. Updating framework...")
        new_framework = framework.copy()
        new_framework["ppt_framework"].append({"page_no": 2, "title": "新增页面"})
        success = await manager.update_framework(task_id, new_framework)
        print(f"   Update success: {success}")

        # 获取用户checkpoint列表
        print("\n4. Getting user checkpoints...")
        checkpoints = await manager.get_user_checkpoints(user_id)
        print(f"   Found {len(checkpoints)} checkpoints")

        # 获取摘要
        print("\n5. Getting checkpoint summaries...")
        summaries = await manager.get_checkpoint_summaries(user_id)
        for summary in summaries:
            print(f"   - {summary.task_id}: {summary.ppt_topic} ({summary.total_pages}页)")

        # 获取checkpoint信息
        print("\n6. Getting checkpoint info...")
        info = await manager.get_checkpoint_info(task_id)
        if info:
            print(f"   Info: {info}")

        # 标记完成
        print("\n7. Marking as completed...")
        await manager.mark_completed(task_id)

        # 清理
        print("\n8. Cleanup...")
        await manager.delete_checkpoint(task_id)
        print("   Checkpoint deleted")

    asyncio.run(test_checkpoint_manager())
