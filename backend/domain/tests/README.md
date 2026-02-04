# Domain 层测试运行指南

本指南说明如何运行 Domain 层的所有测试。

## 📋 前置要求

```bash
# 确保已安装必要的依赖
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

## 🚀 快速开始

### 运行所有Domain测试

```bash
# 从项目根目录运行
pytest backend/domain/tests/ -v

# 或者进入tests目录运行
cd backend/domain/tests
pytest . -v
```

### 运行特定测试文件

```bash
# Task实体测试
pytest backend/domain/tests/test_task_simple.py -v

# Requirement值对象测试
pytest backend/domain/tests/test_value_objects/test_requirement.py -v

# 事件测试
pytest backend/domain/tests/test_events/test_task_events.py -v

# 异常测试
pytest backend/domain/tests/test_exceptions/test_domain_exceptions.py -v

# 集成测试
pytest backend/domain/tests/test_integration/test_task_lifecycle.py -v
```

### 运行特定测试类或方法

```bash
# 运行特定测试类
pytest backend/domain/tests/test_task_simple.py::TestTaskBasic -v

# 运行特定测试方法
pytest backend/domain/tests/test_task_simple.py::TestTaskBasic::test_task_creation -v
```

## 📊 生成覆盖率报告

### 终端输出

```bash
# 显示覆盖率摘要
pytest backend/domain/tests/ --cov=backend.domain --cov-report=term-missing

# 显示分支覆盖率
pytest backend/domain/tests/ --cov=backend.domain --cov-report=term-missing --cov-branch
```

### HTML报告

```bash
# 生成HTML覆盖率报告
pytest backend/domain/tests/ --cov=backend.domain --cov-report=html

# 打开报告
# Windows: start htmlcov/index.html
# Mac: open htmlcov/index.html
# Linux: xdg-open htmlcov/index.html
```

### XML报告（CI/CD）

```bash
# 生成Cobertura XML报告
pytest backend/domain/tests/ --cov=backend.domain --cov-report=xml
```

## 🔍 按标记运行测试

```bash
# 只运行P0优先级测试
pytest backend/domain/tests/ -m p0 -v

# 只运行单元测试
pytest backend/domain/tests/ -m unit -v

# 只运行集成测试
pytest backend/domain/tests/ -m integration -v

# 运行所有domain层测试
pytest backend/domain/tests/ -m domain -v
```

## 📈 测试统计

### 统计信息

```bash
# 显示简短统计
pytest backend/domain/tests/ -q

# 显示详细统计
pytest backend/domain/tests/ -v --tb=no

# 显示最慢的10个测试
pytest backend/domain/tests/ --durations=10
```

## 🐛 调试测试

### 失败时进入pdb

```bash
# 测试失败时进入调试器
pytest backend/domain/tests/ --pdb

# 只在错误时进入pdb（不是失败）
pytest backend/domain/tests/ --pdb-errors
```

### 显示详细输出

```bash
# 显示print输出
pytest backend/domain/tests/ -v -s

# 显示完整回溯
pytest backend/domain/tests/ -v --tb=long

# 显示局部变量
pytest backend/domain/tests/ -v --tb=long --showlocals
```

## 🎯 常用命令组合

### 快速验证

```bash
# 快速运行所有测试（最小输出）
pytest backend/domain/tests/ -q
```

### 完整测试报告

```bash
# 运行所有测试并生成完整报告
pytest backend/domain/tests/ -v --cov=backend.domain --cov-report=html --cov-report=term
```

### 只运行失败的测试

```bash
# 运行上次失败的测试
pytest backend/domain/tests/ --lf

# 先运行失败的，然后运行其他的
pytest backend/domain/tests/ --ff
```

### 并行运行（需要pytest-xdist）

```bash
# 使用所有CPU核心
pytest backend/domain/tests/ -n auto

# 使用指定数量的进程
pytest backend/domain/tests/ -n 4
```

## 📝 当前测试状态

```
总测试数: 130
通过: 125
失败: 5
覆盖率: 86%
执行时间: ~0.6秒
```

## 🔧 故障排查

### ImportError: No module named 'domain'

**解决方案**: 确保在项目根目录运行，或者设置PYTHONPATH

```bash
# 方案1: 在根目录运行
cd /path/to/MultiAgentPPT-main
pytest backend/domain/tests/

# 方案2: 设置PYTHONPATH
export PYTHONPATH=/path/to/MultiAgentPPT-main/backend:$PYTHONPATH
pytest backend/domain/tests/
```

### 测试发现不到

**解决方案**: 确保测试文件以`test_`开头

```bash
# 检查测试文件命名
ls backend/domain/tests/test_*.py

# 使用完整路径
pytest /full/path/to/backend/domain/tests/test_task_simple.py
```

### 覆盖率不显示

**解决方案**: 确保安装了pytest-cov

```bash
pip install pytest-cov
```

## 📚 相关文档

- [测试设计文档](../../../docs/testing/03-domain-test-plan.md)
- [执行清单](../../../docs/testing/03-domain-checklist.md)
- [快速开始](../../../docs/testing/03-domain-quickstart.md)
- [测试报告](../../../docs/testing/03-domain-test-report.md)

## ✅ 验收标准

运行以下命令确认测试环境正常：

```bash
# 运行快速测试
pytest backend/domain/tests/test_task_simple.py -v

# 预期输出: 25 passed in ~0.1s
```

如果看到25个测试通过，说明测试环境配置正确！

---

**最后更新**: 2025-02-04
**维护者**: MultiAgentPPT Team
