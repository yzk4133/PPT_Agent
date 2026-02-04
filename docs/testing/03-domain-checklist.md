# Domain 层测试执行清单

> **测试阶段**: 阶段3 - Domain层
> **预计时间**: 2-3天
> **使用方法**: 按顺序完成每个任务，打勾表示完成

---

## 📋 准备阶段 (第1天上午)

### 环境准备

- [ ] 确认pytest已安装: `pip install pytest pytest-asyncio pytest-cov pytest-mock`
- [ ] 确认测试配置: 检查 `backend/pytest.ini` 或创建该文件
- [ ] 确认项目结构: `backend/domain/` 目录存在
- [ ] 创建测试目录: `backend/domain/tests/`

### 创建测试基础结构

- [ ] 创建 `backend/domain/tests/__init__.py`
- [ ] 创建 `backend/domain/tests/conftest.py` (pytest fixtures)
- [ ] 创建 `backend/domain/tests/fixtures/` 目录
- [ ] 创建测试子目录:
  - [ ] `test_value_objects/`
  - [ ] `test_entities/`
  - [ ] `test_services/`
  - [ ] `test_events/`
  - [ ] `test_exceptions/`

---

## 📝 第1步: 测试fixtures (第1天上午)

### 创建 conftest.py

在 `backend/domain/tests/conftest.py` 中添加:

```python
import pytest
from datetime import datetime

@pytest.fixture
def sample_task():
    """创建示例任务"""
    from domain.entities.task import Task
    return Task(id="test_task_001", raw_input="生成PPT")

@pytest.fixture
def sample_requirement():
    """创建示例需求"""
    from domain.value_objects.requirement import Requirement, SceneType
    return Requirement(
        ppt_topic="AI介绍",
        page_num=10,
        scene=SceneType.BUSINESS_REPORT
    )
```

- [ ] conftest.py 创建完成
- [ ] 运行 `pytest --collect-only backend/domain/tests/` 确认可收集到fixtures

---

## 📝 第2步: 值对象测试 (第1天下午)

### 2.1 Requirement 测试

文件: `backend/domain/tests/test_value_objects/test_requirement.py`

#### 创建测试 (优先级P0)

- [ ] TEST-REQ-001: 有效数据创建需求
- [ ] TEST-REQ-002: 空主题抛出异常
- [ ] TEST-REQ-003: 页数 < 1 抛出异常
- [ ] TEST-REQ-004: 页数 > 100 抛出异常
- [ ] TEST-REQ-005: 无效场景类型抛出异常
- [ ] TEST-REQ-006: 无效模板类型抛出异常
- [ ] TEST-REQ-007: with_defaults() 工厂方法
- [ ] TEST-REQ-008: to_dict() 序列化
- [ ] TEST-REQ-009: from_dict() 反序列化
- [ ] TEST-REQ-010: 往返转换数据一致性

#### 边界测试 (优先级P1)

- [ ] TEST-REQ-011: 页数为1 (最小边界)
- [ ] TEST-REQ-012: 页数为100 (最大边界)
- [ ] TEST-REQ-013: 核心模块数 = 页数
- [ ] TEST-REQ-014: 核心模块数 > 页数 (应失败)

#### 验证

```bash
pytest backend/domain/tests/test_value_objects/test_requirement.py -v
pytest backend/domain/tests/test_value_objects/test_requirement.py --cov=domain.value_objects.requirement
```

- [ ] 所有测试通过
- [ ] 覆盖率 ≥ 85%

### 2.2 Framework 测试

文件: `backend/domain/tests/test_value_objects/test_framework.py`

- [ ] TEST-FRW-001: 有效数据创建框架
- [ ] TEST-FRW-002: 空大纲抛出异常
- [ ] TEST-FRW-003: 幻灯片数 < 1 抛出异常
- [ ] TEST-FRW-004: 序列化/反序列化

- [ ] 所有测试通过
- [ ] 覆盖率 ≥ 85%

### 2.3 其他值对象测试

- [ ] Topic 测试: `test_topic.py`
- [ ] Slide 测试: `test_slide.py`
- [ ] PageState 测试: `test_page_state.py`

---

## 📝 第3步: 实体测试 (第2天)

### 3.1 Task 实体测试 (核心!)

文件: `backend/domain/tests/test_entities/test_task.py`

#### 生命周期测试 (P0)

- [ ] TEST-TASK-001: 创建任务，状态为PENDING
- [ ] TEST-TASK-002: 开始阶段，状态更新
- [ ] TEST-TASK-003: 更新阶段进度
- [ ] TEST-TASK-004: 完成阶段
- [ ] TEST-TASK-005: 失败阶段
- [ ] TEST-TASK-006: 完成任务

#### 进度计算测试 (P0)

- [ ] TEST-TASK-007: 初始进度为0
- [ ] TEST-TASK-008: 需求解析完成 (15%)
- [ ] TEST-TASK-009: 框架设计完成 (30%)
- [ ] TEST-TASK-010: 多阶段累加
- [ ] TEST-TASK-011: 不需要研究时跳过

#### 事件测试 (P0)

- [ ] TEST-TASK-012: 开始阶段触发事件
- [ ] TEST-TASK-013: 完成阶段触发事件
- [ ] TEST-TASK-014: 失败阶段触发两个事件
- [ ] TEST-TASK-015: 获取事件后清空列表

#### 元数据测试 (P1)

- [ ] TEST-TASK-016: 创建时间自动设置
- [ ] TEST-TASK-017: 更新时间自动更新
- [ ] TEST-TASK-018: 总耗时计算

#### 序列化测试 (P0)

- [ ] TEST-TASK-019: to_dict() 包含所有数据
- [ ] TEST-TASK-020: from_dict() 正确还原

#### 验证

```bash
pytest backend/domain/tests/test_entities/test_task.py -v
pytest backend/domain/tests/test_entities/test_task.py --cov=domain.entities.task
```

- [ ] 所有测试通过
- [ ] 覆盖率 ≥ 90% (核心实体要求更高)

### 3.2 Presentation 实体测试

- [ ] TEST-PRES-001 到 TEST-PRES-012

### 3.3 Checkpoint 实体测试

- [ ] TEST-CHK-001 到 TEST-CHK-010

---

## 📝 第4步: 领域服务测试 (第2天下午)

### 4.1 TaskValidationService 测试

文件: `backend/domain/tests/test_services/test_task_validation_service.py`

- [ ] TEST-VAL-001: 验证有效需求
- [ ] TEST-VAL-002: 空主题验证失败
- [ ] TEST-VAL-003: 无效页数验证失败
- [ ] TEST-VAL-004: 无效场景验证失败
- [ ] TEST-VAL-005: 无效状态转换
- [ ] TEST-VAL-006: 验证框架
- [ ] TEST-VAL-007: 验证研究结果

- [ ] 所有测试通过
- [ ] 覆盖率 ≥ 85%

### 4.2 TaskProgressService 测试

- [ ] TEST-PROG-001 到 TEST-PROG-008

### 4.3 StageTransitionService 测试

- [ ] TEST-TRANS-001 到 TEST-TRANS-012

---

## 📝 第5步: 事件测试 (第3天上午)

文件: `backend/domain/tests/test_events/test_task_events.py`

- [ ] TEST-EVT-001: 创建TASK_CREATED事件
- [ ] TEST-EVT-002: 创建REQUIREMENT_PARSED事件
- [ ] TEST-EVT-003: 创建FRAMEWORK_DESIGNED事件
- [ ] TEST-EVT-004: 创建STAGE_STARTED事件
- [ ] TEST-EVT-005: 创建STAGE_COMPLETED事件
- [ ] TEST-EVT-006: 创建STAGE_FAILED事件
- [ ] TEST-EVT-007: 创建TASK_COMPLETED事件
- [ ] TEST-EVT-008: 创建TASK_FAILED事件
- [ ] TEST-EVT-009: 事件序列化
- [ ] TEST-EVT-010: 事件反序列化
- [ ] TEST-EVT-011: 时间戳正确
- [ ] TEST-EVT-012: 关联ID一致

- [ ] 所有测试通过
- [ ] 覆盖率 ≥ 85%

---

## 📝 第6步: 异常测试 (第3天上午)

文件: `backend/domain/tests/test_exceptions/test_domain_exceptions.py`

- [ ] TEST-EXC-001: TaskNotFoundException
- [ ] TEST-EXC-002: TaskValidationError with errors
- [ ] TEST-EXC-003: TaskValidationError with field
- [ ] TEST-EXC-004: InvalidTaskStateError
- [ ] TEST-EXC-005: TaskTransitionError
- [ ] TEST-EXC-006: 异常详情完整
- [ ] TEST-EXC-007: 向后兼容别名

- [ ] 所有测试通过

---

## 📝 第7步: 集成测试 (第3天下午)

文件: `backend/domain/tests/test_integration/test_task_lifecycle.py`

- [ ] TEST-INT-001: 完整任务生命周期
- [ ] TEST-INT-002: 事件传播
- [ ] TEST-INT-003: 服务协作
- [ ] TEST-INT-004: 错误恢复流程

- [ ] 所有测试通过

---

## ✅ 验收阶段 (第3天下午)

### 运行所有测试

```bash
# 运行domain层所有测试
pytest backend/domain/tests/ -v

# 生成覆盖率报告
pytest backend/domain/tests/ --cov=backend/domain --cov-report=html

# 查看覆盖率
pytest backend/domain/tests/ --cov=backend/domain --cov-report=term-missing
```

### 验收检查

- [ ] **覆盖率达标**:
  - [ ] 代码覆盖率 ≥ 85%
  - [ ] 分支覆盖率 ≥ 80%
  - [ ] 行覆盖率 ≥ 90%

- [ ] **P0用例全部通过**:
  - [ ] Task实体: ✓
  - [ ] Requirement值对象: ✓
  - [ ] TaskValidationService: ✓

- [ ] **无阻塞性缺陷**:
  - [ ] P0缺陷: 0个
  - [ ] P1缺陷: ≤ 3个

- [ ] **文档完整**:
  - [ ] 每个测试有docstring
  - [ ] 测试ID正确标注
  - [ ] 覆盖率报告生成

### 生成报告

- [ ] 生成HTML覆盖率报告: `pytest backend/domain/tests/ --cov=backend/domain --cov-report=html`
- [ ] 打开报告: `htmlcov/index.html`
- [ ] 截图保存到文档

- [ ] 记录测试统计:
  - 总测试数: _____
  - 通过数: _____
  - 失败数: _____
  - 跳过数: _____
  - 覆盖率: _____%

---

## 📊 测试统计模板

```
┌─────────────────────────────────────┐
│     Domain 层测试统计报告            │
├─────────────────────────────────────┤
│ 测试日期: _____________              │
│ 测试人员: _____________              │
├─────────────────────────────────────┤
│ 测试用例统计                         │
│ ├─ 值对象:      ______ / ______     │
│ ├─ 实体:        ______ / ______     │
│ ├─ 服务:        ______ / ______     │
│ ├─ 事件:        ______ / ______     │
│ ├─ 异常:        ______ / ______     │
│ └─ 集成:        ______ / ______     │
├─────────────────────────────────────┤
│ 总计:          ______ / ______     │
│ 通过率:        ______%              │
├─────────────────────────────────────┤
│ 覆盖率统计                            │
│ ├─ 代码覆盖率:  ______%             │
│ ├─ 分支覆盖率:  ______%             │
│ └─ 行覆盖率:    ______%             │
├─────────────────────────────────────┤
│ 缺陷统计                             │
│ ├─ P0缺陷:     ______ 个            │
│ ├─ P1缺陷:     ______ 个            │
│ └─ P2缺陷:     ______ 个            │
└─────────────────────────────────────┘
```

---

## 🔧 常见问题解决

### 问题1: ImportError

```
解决方案:
1. 确认在项目根目录运行pytest
2. 检查PYTHONPATH包含项目路径
3. 检查__init__.py文件是否存在
```

### 问题2: 覆盖率不达标

```
解决方案:
1. 查看未覆盖的代码行
2. 添加对应测试用例
3. 检查是否有死代码
```

### 问题3: 测试运行缓慢

```
解决方案:
1. 使用pytest-xdist并行运行: pytest -n auto
2. 检查是否有慢fixture
3. 优化测试数据准备
```

---

## 📚 参考文档

- [Domain层测试详细设计](./03-domain-test-plan.md)
- [测试编写指南](./03-test-guide.md)
- [pytest官方文档](https://docs.pytest.org/)

---

**完成标准**:

- [ ] 所有P0测试通过
- [ ] 覆盖率 ≥ 85%
- [ ] 测试报告完成
- [ ] 可以进入下一阶段 (Cognition层)

**签字**: _____________  **日期**: _____________
