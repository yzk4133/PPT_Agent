# Domain 层测试快速开始指南

> **目标**: 在30分钟内运行第一个Domain层测试
> **适用**: 刚开始测试Domain层的开发者

---

## 🚀 5步快速开始

### 步骤1: 创建测试目录 (2分钟)

```bash
# 在项目根目录执行
cd backend/domain
mkdir -p tests
cd tests
touch __init__.py
```

### 步骤2: 创建第一个测试文件 (5分钟)

创建文件: `backend/domain/tests/test_task_simple.py`

```python
"""
简单的Task实体测试

这是第一个测试，用于验证测试环境是否正确设置
"""

import pytest
from domain.entities.task import Task, TaskStatus, TaskStage


class TestTaskBasic:
    """Task实体基础测试"""

    def test_task_creation(self):
        """测试: 能够创建一个任务"""
        # Given - 准备数据
        task_id = "test_001"
        raw_input = "生成一份AI介绍PPT"

        # When - 执行操作
        task = Task(id=task_id, raw_input=raw_input)

        # Then - 验证结果
        assert task.id == task_id
        assert task.raw_input == raw_input
        assert task.status == TaskStatus.PENDING
        print(f"✓ 任务创建成功: {task}")

    def test_task_initialization(self):
        """测试: 任务初始化时应该创建所有阶段"""
        # Given & When
        task = Task(id="test_002", raw_input="测试")

        # Then
        assert len(task.stages) == len(TaskStage)
        assert TaskStage.REQUIREMENT_PARSING in task.stages
        assert TaskStage.FRAMEWORK_DESIGN in task.stages
        print(f"✓ 任务包含 {len(task.stages)} 个阶段")

    def test_task_initial_progress(self):
        """测试: 新任务的进度应该为0"""
        # Given & When
        task = Task(id="test_003", raw_input="测试")

        # Then
        progress = task.get_overall_progress()
        assert progress == 0
        print(f"✓ 初始进度: {progress}%")


if __name__ == "__main__":
    # 直接运行这个文件进行测试
    pytest.main([__file__, "-v", "-s"])
```

### 步骤3: 运行测试 (1分钟)

```bash
# 方式1: 使用pytest
cd backend
pytest domain/tests/test_task_simple.py -v

# 方式2: 使用pytest并查看输出
pytest domain/tests/test_task_simple.py -v -s

# 方式3: 直接运行Python文件
python domain/tests/test_task_simple.py
```

**预期输出**:

```
test_task_simple.py::TestTaskBasic::test_task_creation PASSED [33%]
✓ 任务创建成功: Task(id='test_001', status=pending, progress=0%)

test_task_simple.py::TestTaskBasic::test_task_initialization PASSED [67%]
✓ 任务包含 5 个阶段

test_task_simple.py::TestTaskBasic::test_task_initial_progress PASSED [100%]
✓ 初始进度: 0%

============================== 3 passed in 0.05s ===============================
```

### 步骤4: 添加更多测试 (10分钟)

在同一个文件中继续添加:

```python
    def test_stage_lifecycle(self):
        """测试: 任务阶段生命周期"""
        # Given
        task = Task(id="test_004", raw_input="测试")

        # When - 开始阶段
        task.start_stage(TaskStage.REQUIREMENT_PARSING)

        # Then - 验证状态
        assert task.stages[TaskStage.REQUIREMENT_PARSING].status == TaskStatus.PARSING_REQUIREMENTS
        assert task.stages[TaskStage.REQUIREMENT_PARSING].started_at is not None
        print(f"✓ 阶段已开始: {TaskStage.REQUIREMENT_PARSING}")

        # When - 更新进度
        task.update_stage_progress(TaskStage.REQUIREMENT_PARSING, 50)

        # Then - 验证进度
        assert task.stages[TaskStage.REQUIREMENT_PARSING].progress == 50
        print(f"✓ 进度已更新: 50%")

        # When - 完成阶段
        task.complete_stage(TaskStage.REQUIREMENT_PARSING)

        # Then - 验证完成状态
        assert task.stages[TaskStage.REQUIREMENT_PARSING].status == TaskStatus.COMPLETED
        assert task.stages[TaskStage.REQUIREMENT_PARSING].progress == 100
        print(f"✓ 阶段已完成")

    def test_progress_calculation(self):
        """测试: 进度计算"""
        # Given
        task = Task(id="test_005", raw_input="测试")

        # When - 完成需求解析阶段 (15%)
        task.start_stage(TaskStage.REQUIREMENT_PARSING)
        task.complete_stage(TaskStage.REQUIREMENT_PARSING)

        # Then - 验证进度
        progress = task.get_overall_progress()
        assert 14 <= progress <= 16  # 约15%
        print(f"✓ 完成需求解析后进度: {progress}%")

        # When - 完成框架设计阶段 (30%)
        task.start_stage(TaskStage.FRAMEWORK_DESIGN)
        task.complete_stage(TaskStage.FRAMEWORK_DESIGN)

        # Then - 验证总进度
        progress = task.get_overall_progress()
        assert 44 <= progress <= 46  # 约45%
        print(f"✓ 完成两个阶段后进度: {progress}%")

    def test_task_serialization(self):
        """测试: 任务序列化"""
        # Given
        task = Task(id="test_006", raw_input="测试", status=TaskStatus.COMPLETED)

        # When - 转换为字典
        data = task.to_dict()

        # Then - 验证字典内容
        assert data["id"] == "test_006"
        assert data["status"] == "completed"
        assert data["raw_input"] == "测试"
        print(f"✓ to_dict() 成功")

        # When - 从字典还原
        restored_task = Task.from_dict(data)

        # Then - 验证还原结果
        assert restored_task.id == task.id
        assert restored_task.status == task.status
        assert restored_task.raw_input == task.raw_input
        print(f"✓ from_dict() 成功，数据一致")
```

### 步骤5: 检查覆盖率 (2分钟)

```bash
# 生成覆盖率报告
pytest backend/domain/tests/test_task_simple.py --cov=backend.domain.entities.task --cov-report=term-missing

# 生成HTML报告
pytest backend/domain/tests/test_task_simple.py --cov=backend.domain.entities.task --cov-report=html

# 打开报告
# Windows: start htmlcov/index.html
# Mac: open htmlcov/index.html
# Linux: xdg-open htmlcov/index.html
```

**预期结果**: 覆盖率应该达到 20-30%

---

## 📝 测试模板

### 模板1: 基础测试

```python
def test_<功能>_<场景>():
    """
    [测试ID] TEST-XXX

    测试名称: <功能> - <场景>

    Given: 准备条件
    When: 执行操作
    Then: 验证结果
    """
    # Given
    <准备测试数据>

    # When
    <执行被测试的操作>

    # Then
    assert <期望结果>
```

### 模板2: 参数化测试

```python
@pytest.mark.parametrize("input,expected", [
    (1, True),      # 最小边界
    (10, True),     # 正常值
    (100, True),    # 最大边界
    (0, False),     # 太小
    (101, False),   # 太大
])
def test_validation(input, expected):
    """测试不同输入的验证"""
    if expected:
        # 应该成功
        result = create_object(value=input)
        assert result.value == input
    else:
        # 应该失败
        with pytest.raises(ValidationError):
            create_object(value=input)
```

### 模板3: 异常测试

```python
def test_exception_handling():
    """测试异常处理"""
    # Given
    task = Task(id="test", raw_input="测试")

    # When & Then
    with pytest.raises(ValidationError) as exc_info:
        task.start_stage(TaskStage.REQUIREMENT_PARSING)
        task.fail_stage(TaskStage.REQUIREMENT_PARSING, "测试错误")

    assert "测试错误" in str(exc_info.value)
```

---

## 🎯 下一步

### 完成基础测试后，继续:

1. **测试Requirement值对象** (15分钟)
   ```bash
   # 创建文件
   touch backend/domain/tests/test_requirement_simple.py
   ```

2. **测试TaskValidationService** (10分钟)
   ```bash
   # 创建文件
   touch backend/domain/tests/test_validation_service_simple.py
   ```

3. **查看完整测试计划**
   - 详细设计: [03-domain-test-plan.md](./03-domain-test-plan.md)
   - 执行清单: [03-domain-checklist.md](./03-domain-checklist.md)

---

## 💡 测试编写技巧

### 技巧1: 使用描述性测试名称

```python
# ❌ 不好
def test_1():
    pass

# ✅ 好
def test_task_creation_with_valid_input():
    pass
```

### 技巧2: 每个测试只验证一件事

```python
# ❌ 不好 - 测试太多东西
def test_task_everything():
    task = Task(id="test", raw_input="测试")
    task.start_stage(stage1)
    task.complete_stage(stage1)
    task.start_stage(stage2)
    task.fail_stage(stage2)
    assert ...  # 太多断言

# ✅ 好 - 每个测试一个焦点
def test_task_stage_start():
    task = Task(id="test", raw_input="测试")
    task.start_stage(TaskStage.REQUIREMENT_PARSING)
    assert task.stages[...].status == ...

def test_task_stage_completion():
    task = Task(id="test", raw_input="测试")
    task.start_stage(TaskStage.REQUIREMENT_PARSING)
    task.complete_stage(TaskStage.REQUIREMENT_PARSING)
    assert task.stages[...].status == TaskStatus.COMPLETED
```

### 技巧3: 使用Given-When-Then注释

```python
def test_progress_calculation():
    # Given - 一个已完成的任务
    task = Task(id="test", raw_input="测试")
    task.start_stage(TaskStage.REQUIREMENT_PARSING)
    task.complete_stage(TaskStage.REQUIREMENT_PARSING)

    # When - 计算进度
    progress = task.get_overall_progress()

    # Then - 验证进度
    assert progress == 15
```

---

## 🐛 常见错误

### 错误1: ImportError

```
ModuleNotFoundError: No module named 'domain'
```

**解决方案**:
```bash
# 确保在项目根目录运行
cd /path/to/MultiAgentPPT-main
pytest backend/domain/tests/test_task_simple.py
```

### 错误2: 测试发现不到

```
collected 0 items
```

**解决方案**:
```bash
# 检查文件名是否以 test_ 开头
# 检查是否在tests目录下
# 使用完整路径
pytest backend/domain/tests/test_task_simple.py
```

### 错误3: AttributeError

```
AttributeError: module 'domain.entities.task' has no attribute 'Task'
```

**解决方案**:
```python
# 检查导入路径
# 确保Task类在task.py中已导出
# 查看domain/entities/task.py中是否有: class Task:
```

---

## ✅ 验证检查点

在进入下一阶段前，确保:

- [ ] 至少完成 `test_task_simple.py` (5个测试)
- [ ] 所有测试通过
- [ ] 理解Given-When-Then模式
- [ ] 能够独立编写新测试
- [ ] 覆盖率 ≥ 20% (初步)

---

## 📞 获取帮助

- **查看文档**: [03-domain-test-plan.md](./03-domain-test-plan.md)
- **查看清单**: [03-domain-checklist.md](./03-domain-checklist.md)
- **查看指南**: [03-test-guide.md](./03-test-guide.md)
- **pytest文档**: https://docs.pytest.org/

---

**开始时间**: _________  **完成时间**: _________

**当前进度**:
- [ ] 步骤1: 创建目录
- [ ] 步骤2: 创建测试文件
- [ ] 步骤3: 运行测试
- [ ] 步骤4: 添加更多测试
- [ ] 步骤5: 检查覆盖率

**下一步**: 开始完整的Domain层测试 ➡️ [03-domain-checklist.md](./03-domain-checklist.md)
