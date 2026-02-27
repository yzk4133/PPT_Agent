"""
Execution Mode Model

Defines the execution modes for PPT generation workflow.
"""

from enum import Enum


class ExecutionMode(str, Enum):
    """
    PPT Generation Execution Modes

    Supports three execution modes:
    - FULL: Execute all phases at once (generate complete PPT in one go)
    - PHASE_1: Execute phase 1-2 only (requirement parsing + framework design, generate outline)
    - PHASE_2: Resume from checkpoint and execute phase 3-5 (research -> content -> rendering)
    """

    FULL = "full"           # Execute all phases
    PHASE_1 = "phase_1"     # Execute phase 1-2 only (generate outline)
    PHASE_2 = "phase_2"     # Resume from checkpoint for phase 3-5

    def __str__(self) -> str:
        return self.value

    @property
    def is_full(self) -> bool:
        """Check if this is full execution mode"""
        return self == ExecutionMode.FULL

    @property
    def is_phase_1(self) -> bool:
        """Check if this is phase 1 execution mode"""
        return self == ExecutionMode.PHASE_1

    @property
    def is_phase_2(self) -> bool:
        """Check if this is phase 2 execution mode"""
        return self == ExecutionMode.PHASE_2

    @property
    def needs_checkpoint(self) -> bool:
        """Check if this mode requires checkpoint"""
        return self in (ExecutionMode.PHASE_1, ExecutionMode.PHASE_2)

    @property
    def description(self) -> str:
        """Get description of this execution mode"""
        descriptions = {
            ExecutionMode.FULL: "完整执行：一次性生成完整PPT",
            ExecutionMode.PHASE_1: "阶段1执行：生成大纲供用户编辑",
            ExecutionMode.PHASE_2: "阶段2执行：从确认的大纲生成PPT"
        }
        return descriptions.get(self, "未知模式")

    @classmethod
    def from_string(cls, value: str) -> "ExecutionMode":
        """Create ExecutionMode from string"""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(
                f"Invalid execution mode: {value}. "
                f"Valid values are: {', '.join([m.value for m in cls])}"
            )


if __name__ == "__main__":
    # Test code
    print("Testing ExecutionMode")
    print("=" * 60)

    for mode in ExecutionMode:
        print(f"\n{mode.value}:")
        print(f"  - is_full: {mode.is_full}")
        print(f"  - is_phase_1: {mode.is_phase_1}")
        print(f"  - is_phase_2: {mode.is_phase_2}")
        print(f"  - needs_checkpoint: {mode.needs_checkpoint}")
        print(f"  - description: {mode.description}")
