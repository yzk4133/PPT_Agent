"""
Execution Mode Domain Model

Defines the execution modes for MasterCoordinator to support
two-phase PPT generation workflow.
"""

from enum import Enum

class ExecutionMode(str, Enum):
    """
    MasterCoordinator执行模式

    支持三种执行模式：
    - FULL: 完整执行所有阶段（一次性生成完整PPT）
    - PHASE_1: 仅执行阶段1-2（需求解析+框架设计，生成大纲）
    - PHASE_2: 从checkpoint继续执行阶段3-5（研究→内容→渲染）
    """

    FULL = "full"           # 完整执行所有阶段
    PHASE_1 = "phase_1"     # 仅执行阶段1-2（生成大纲）
    PHASE_2 = "phase_2"     # 从checkpoint继续执行阶段3-5

    def __str__(self) -> str:
        return self.value

    @property
    def is_full(self) -> bool:
        """是否为完整执行模式"""
        return self == ExecutionMode.FULL

    @property
    def is_phase_1(self) -> bool:
        """是否为阶段1执行模式"""
        return self == ExecutionMode.PHASE_1

    @property
    def is_phase_2(self) -> bool:
        """是否为阶段2执行模式"""
        return self == ExecutionMode.PHASE_2

    @property
    def needs_checkpoint(self) -> bool:
        """是否需要保存checkpoint"""
        return self in (ExecutionMode.PHASE_1, ExecutionMode.PHASE_2)

    @property
    def description(self) -> str:
        """获取执行模式描述"""
        descriptions = {
            ExecutionMode.FULL: "完整执行：一次性生成完整PPT",
            ExecutionMode.PHASE_1: "阶段1执行：生成大纲供用户编辑",
            ExecutionMode.PHASE_2: "阶段2执行：从确认的大纲生成PPT"
        }
        return descriptions.get(self, "未知模式")

    @classmethod
    def from_string(cls, value: str) -> "ExecutionMode":
        """从字符串创建ExecutionMode"""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(
                f"Invalid execution mode: {value}. "
                f"Valid values are: {', '.join([m.value for m in cls])}"
            )

if __name__ == "__main__":
    # 测试代码
    print("Testing ExecutionMode")
    print("=" * 60)

    for mode in ExecutionMode:
        print(f"\n{mode.value}:")
        print(f"  - is_full: {mode.is_full}")
        print(f"  - is_phase_1: {mode.is_phase_1}")
        print(f"  - is_phase_2: {mode.is_phase_2}")
        print(f"  - needs_checkpoint: {mode.needs_checkpoint}")
        print(f"  - description: {mode.description}")

    # 测试from_string
    print("\n" + "=" * 60)
    print("Testing from_string:")
    print(f"from_string('full') = {ExecutionMode.from_string('full')}")
    print(f"from_string('PHASE_1') = {ExecutionMode.from_string('PHASE_1')}")
    print(f"from_string('phase_2') = {ExecutionMode.from_string('phase_2')}")
