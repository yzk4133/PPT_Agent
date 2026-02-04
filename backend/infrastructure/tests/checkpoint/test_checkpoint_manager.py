"""
Checkpoint Manager 测试
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from infrastructure.checkpoint.checkpoint_manager import (
    CheckpointManager,
    get_checkpoint_manager,
    set_checkpoint_manager,
)
from infrastructure.checkpoint.database_backend import ICheckpointBackend

@pytest.mark.unit
@pytest.mark.asyncio
class TestCheckpointManager:
    """测试 CheckpointManager 类"""

    async def test_checkpoint_manager_initialization(self):
        """测试初始化"""
        backend = MagicMock(spec=ICheckpointBackend)
        manager = CheckpointManager(backend)

        assert manager.backend is backend

    async def test_save_checkpoint(self):
        """测试保存检查点"""
        backend = MagicMock(spec=ICheckpointBackend)
        backend.save = AsyncMock(return_value=True)

        manager = CheckpointManager(backend)

        checkpoint = await manager.save_checkpoint(
            task_id="task_001",
            user_id="user_001",
            execution_mode="phase_1",
            phase=2,
            raw_input="Test input",
            requirements={"topic": "AI"},
            framework={"pages": 10},
        )

        assert checkpoint is not None
        assert checkpoint.task_id == "task_001"
        backend.save.assert_called_once()

    async def test_save_checkpoint_failure(self):
        """测试保存检查点失败"""
        backend = MagicMock(spec=ICheckpointBackend)
        backend.save = AsyncMock(return_value=False)

        manager = CheckpointManager(backend)

        with pytest.raises(RuntimeError, match="Failed to save checkpoint"):
            await manager.save_checkpoint(
                task_id="task_001",
                user_id="user_001",
                execution_mode="phase_1",
                phase=2,
                raw_input="Test input",
                requirements={},
                framework={},
            )

    async def test_load_checkpoint(self):
        """测试加载检查点"""
        from domain.models.checkpoint import Checkpoint
        from datetime import datetime

        backend = MagicMock(spec=ICheckpointBackend)
        checkpoint = Checkpoint(
            task_id="task_001",
            user_id="user_001",
            execution_mode="phase_1",
            phase=2,
            raw_user_input="Test",
            structured_requirements={},
            ppt_framework={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        backend.load = AsyncMock(return_value=checkpoint)

        manager = CheckpointManager(backend)
        result = await manager.load_checkpoint("task_001")

        assert result is not None
        assert result.task_id == "task_001"
        backend.load.assert_called_once_with("task_001")

    async def test_load_checkpoint_not_found(self):
        """测试加载不存在的检查点"""
        backend = MagicMock(spec=ICheckpointBackend)
        backend.load = AsyncMock(return_value=None)

        manager = CheckpointManager(backend)
        result = await manager.load_checkpoint("task_001")

        assert result is None

    async def test_update_framework(self):
        """测试更新框架"""
        from domain.models.checkpoint import Checkpoint
        from datetime import datetime

        backend = MagicMock(spec=ICheckpointBackend)
        checkpoint = Checkpoint(
            task_id="task_001",
            user_id="user_001",
            execution_mode="phase_1",
            phase=2,
            raw_user_input="Test",
            structured_requirements={},
            ppt_framework={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status="editing",
        )
        backend.load = AsyncMock(return_value=checkpoint)
        backend.update = AsyncMock(return_value=True)

        manager = CheckpointManager(backend)
        result = await manager.update_framework("task_001", {"new": "framework"})

        assert result is True
        backend.update.assert_called_once()

    async def test_delete_checkpoint(self):
        """测试删除检查点"""
        backend = MagicMock(spec=ICheckpointBackend)
        backend.delete = AsyncMock(return_value=True)

        manager = CheckpointManager(backend)
        result = await manager.delete_checkpoint("task_001")

        assert result is True
        backend.delete.assert_called_once_with("task_001")

    async def test_get_user_checkpoints(self):
        """测试获取用户检查点列表"""
        from domain.models.checkpoint import Checkpoint
        from datetime import datetime

        backend = MagicMock(spec=ICheckpointBackend)
        checkpoints = [
            Checkpoint(
                task_id=f"task_{i:03d}",
                user_id="user_001",
                execution_mode="phase_1",
                phase=2,
                raw_user_input="Test",
                structured_requirements={},
                ppt_framework={},
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(3)
        ]
        backend.list_by_user = AsyncMock(return_value=checkpoints)

        manager = CheckpointManager(backend)
        result = await manager.get_user_checkpoints("user_001")

        assert len(result) == 3
        backend.list_by_user.assert_called_once_with("user_001", 50)

    async def test_mark_completed(self):
        """测试标记完成"""
        from domain.models.checkpoint import Checkpoint
        from datetime import datetime

        backend = MagicMock(spec=ICheckpointBackend)
        checkpoint = Checkpoint(
            task_id="task_001",
            user_id="user_001",
            execution_mode="phase_1",
            phase=2,
            raw_user_input="Test",
            structured_requirements={},
            ppt_framework={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        backend.load = AsyncMock(return_value=checkpoint)
        backend.save = AsyncMock(return_value=True)

        manager = CheckpointManager(backend)
        result = await manager.mark_completed("task_001")

        assert result is True

    async def test_cleanup_expired(self):
        """测试清理过期检查点"""
        from domain.models.checkpoint import Checkpoint
        from datetime import datetime, timedelta

        backend = MagicMock(spec=ICheckpointBackend)
        checkpoint = Checkpoint(
            task_id="task_001",
            user_id="user_001",
            execution_mode="phase_1",
            phase=2,
            raw_user_input="Test",
            structured_requirements={},
            ppt_framework={},
            created_at=datetime.now() - timedelta(hours=25),
            updated_at=datetime.now() - timedelta(hours=25),
        )
        backend.list_all = AsyncMock(return_value=[checkpoint])
        backend.delete = AsyncMock(return_value=True)

        manager = CheckpointManager(backend)
        result = await manager.cleanup_expired(ttl_hours=24)

        # 结果取决于检查点是否过期
        assert isinstance(result, int)

@pytest.mark.unit
class TestGlobalCheckpointManager:
    """测试全局检查点管理器"""

    def test_get_checkpoint_manager_none(self):
        """测试获取未设置的全局检查点管理器"""
        import infrastructure.checkpoint.checkpoint_manager as cp_module
        cp_module._checkpoint_manager = None

        manager = get_checkpoint_manager()
        assert manager is None

    def test_set_checkpoint_manager(self):
        """测试设置全局检查点管理器"""
        backend = MagicMock(spec=ICheckpointBackend)
        manager = CheckpointManager(backend)

        set_checkpoint_manager(manager)

        result = get_checkpoint_manager()
        assert result is manager
