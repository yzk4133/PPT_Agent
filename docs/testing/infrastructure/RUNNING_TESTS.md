# 运行测试指南

> **如何运行和分析 Infrastructure 层测试**

---

## 🚀 快速开始

### 前置要求

```bash
# 确保已安装测试依赖
pip install pytest pytest-asyncio pytest-cov
```

### 基本命令

```bash
# 进入项目根目录
cd backend

# 运行所有测试
pytest infrastructure/tests/

# 查看帮助
pytest --help
```

---

## 📋 运行不同类型的测试

### 1. 运行所有测试

```bash
# 基本运行
pytest infrastructure/tests/

# 详细输出
pytest -v infrastructure/tests/

# 超详细输出（显示每个测试的打印内容）
pytest -vv infrastructure/tests/
```

### 2. 运行特定模块

```bash
# Database 模块
pytest infrastructure/tests/database/

# LLM 模块
pytest infrastructure/tests/llm/

# Config 模块
pytest infrastructure/tests/config/

# Cache 模块
pytest infrastructure/tests/cache/

# Security 模块
pytest infrastructure/tests/security/

# Middleware 模块
pytest infrastructure/tests/middleware/
```

### 3. 运行特定文件

```bash
# 单个测试文件
pytest infrastructure/tests/database/test_connection_manager.py

# 多个测试文件
pytest infrastructure/tests/llm/test_model_factory.py infrastructure/tests/llm/test_retry_decorator.py
```

### 4. 运行特定测试函数

```bash
# 运行单个测试函数
pytest infrastructure/tests/cache/test_agent_cache.py::test_cache_hit_and_miss

# 运行类中的所有测试
pytest infrastructure/tests/cache/test_agent_cache.py::TestAgentCache
```

---

## 🏷️ 使用测试标记

### 按类型运行

```bash
# 只运行单元测试
pytest -m "unit" infrastructure/tests/

# 只运行集成测试
pytest -m "integration" infrastructure/tests/

# 只运行异步测试
pytest -m "async" infrastructure/tests/

# 运行所有慢速测试
pytest -m "slow" infrastructure/tests/

# 排除慢速测试
pytest -m "not slow" infrastructure/tests/
```

### 按模块运行

```bash
# 只运行数据库相关测试
pytest -m "database" infrastructure/tests/

# 只运行 LLM 相关测试
pytest -m "llm" infrastructure/tests/

# 只运行 Redis 相关测试
pytest -m "redis" infrastructure/tests/
```

### 组合标记

```bash
# 运行数据库单元测试
pytest -m "database and unit" infrastructure/tests/

# 运行异步集成测试
pytest -m "async and integration" infrastructure/tests/
```

---

## 📊 覆盖率报告

### 生成覆盖率报告

```bash
# 生成终端覆盖率报告
pytest --cov=backend/infrastructure --cov-report=term-missing infrastructure/tests/

# 生成 HTML 覆盖率报告
pytest --cov=backend/infrastructure --cov-report=html infrastructure/tests/

# 生成 XML 覆盖率报告（用于 CI）
pytest --cov=backend/infrastructure --cov-report=xml infrastructure/tests/
```

### 查看覆盖率报告

```bash
# HTML 报告生成在 htmlcov/ 目录
# 在浏览器中打开
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### 覆盖率目标

测试配置要求最低 **70%** 的覆盖率：

```bash
# 如果覆盖率低于 70%，测试将失败
pytest infrastructure/tests/

# 临时降低覆盖率要求
pytest --cov-fail-under=60 infrastructure/tests/
```

---

## 🐛 调试失败的测试

### 显示详细错误信息

```bash
# 显示简短错误信息（默认）
pytest infrastructure/tests/

# 显示详细错误信息
pytest -v infrastructure/tests/

# 显示超详细错误信息（包括完整堆栈）
pytest -vv infrastructure/tests/

# 在第一个失败时停止
pytest -x infrastructure/tests/

# 在第 N 个失败后停止
pytest --maxfail=3 infrastructure/tests/
```

### 只运行失败的测试

```bash
# 运行上次失败的测试
pytest --lf infrastructure/tests/

# 运行上次失败的测试（先显示详细信息）
pytest -v --lf infrastructure/tests/

# 运行所有测试，但优先显示失败的
pytest -ff infrastructure/tests/
```

### 进入调试模式

```bash
# 在测试失败时进入 PDB 调试器
pytest --pdb infrastructure/tests/

# 在测试开始时进入 PDB 调试器
pytest --trace infrastructure/tests/
```

### 打印调试

```bash
# 显示测试中所有的 print 输出
pytest -s infrastructure/tests/

# 捕获打印输出并显示在失败报告中
pytest --capture=no infrastructure/tests/
```

---

## ⚡ 性能相关

### 并行运行测试

```bash
# 使用 pytest-xdist 并行运行（需要安装）
pip install pytest-xdist

# 自动检测 CPU 数量并行运行
pytest -n auto infrastructure/tests/

# 指定并行数
pytest -n 4 infrastructure/tests/
```

### 运行最慢的测试

```bash
# 显示最慢的 10 个测试
pytest --durations=10 infrastructure/tests/

# 将最慢的测试保存到文件
pytest --durations=10 --durations-min=1.0 infrastructure/tests/ > slow_tests.txt
```

---

## 🔄 持续监控模式

```bash
# 监控文件变化并自动重新运行
# 需要安装 pytest-watch
pip install pytest-watch

# 监控所有测试
ptw infrastructure/tests/

# 监控特定目录
ptw infrastructure/tests/llm/

# 监控并清除之前的缓存
ptw --runner "pytest infrastructure/tests/"
```

---

## 🧩 清理和准备

### 清理缓存和临时文件

```bash
# 清理 pytest 缓存
pytest --cache-clear

# 清理覆盖率数据
rm -rf htmlcov/
rm -rf .coverage
rm -rf .pytest_cache/
```

### 重新安装依赖

```bash
# 确保测试依赖是最新的
pip install --upgrade pytest pytest-asyncio pytest-cov
```

---

## 📋 生成测试报告

### HTML 报告（推荐）

```bash
# 生成包含所有信息的 HTML 报告
pytest --html=report.html --self-contained-html infrastructure/tests/
```

### JUnit XML 报告（CI/CD）

```bash
# 生成 JUnit XML 格式报告
pytest --junitxml=test-results.xml infrastructure/tests/
```

### JSON 报告

```bash
# 生成 JSON 格式报告
pytest --json-report --json-report-file=test-report.json infrastructure/tests/
```

---

## 🎯 常用测试场景

### 场景 1: 开发时快速验证

```bash
# 只运行单元测试，跳过慢速测试
pytest -m "unit and not slow" infrastructure/tests/ -v
```

### 场景 2: 提交前完整验证

```bash
# 运行所有测试并生成覆盖率报告
pytest infrastructure/tests/ --cov=backend/infrastructure --cov-report=html
```

### 场景 3: 调试特定模块

```bash
# 运行特定模块并显示详细输出
pytest -vv infrastructure/tests/llm/test_model_factory.py -k test_create_model
```

### 场景 4: CI/CD 环境

```bash
# CI 环境中运行（快速、并行）
pytest -n auto --dist=loadscope -q infrastructure/tests/

# 生成覆盖率报告供 CI 使用
pytest --cov=backend/infrastructure --cov-report=xml --cov-report=term infrastructure/tests/
```

---

## 📈 测试结果解读

### 终端输出示例

```
================================ test session starts ========================================
platform linux -- Python 3.8.10
pytest 7.0.0, pytest-asyncio 0.21.0
rootdir: /app
configfile: backend/infrastructure/tests/pytest.ini
testpaths: backend/infrastructure/tests

collected 245 items

tests/database/test_connection_manager.py::TestDatabaseManager::test_initialization PASSED [ 5%]
tests/database/test_connection_manager.py::TestDatabaseManager::test_postgres_session_creation PASSED [ 10%]
...

============================== 245 passed in 12.34s ==============================

----------- coverage: platform linux, python 3.8.10 ---------------------------
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
backend/infrastructure/cache.py      150     20    87%    7%
backend/infrastructure/database.py    200     40    80%    12%
...
-----------------------------------------------------------
TOTAL                           1500    450    70%


====================== 245 passed, 70% coverage in 12.34s =======================
```

### 关键指标解读

| 指标 | 说明 | 示例值 |
|------|------|--------|
| `245 passed` | 通过的测试数量 | ✅ 全部通过 |
| `70% coverage` | 代码覆盖率 | ✅ 达标 |
| `12.34s` | 总运行时间 | ⏱️ 合理 |
| `Missing` | 未覆盖的代码行 | 450 行未覆盖 |

---

## 🚨 常见问题和解决方案

### 问题 1: 导入错误

```
ModuleNotFoundError: No module named 'infrastructure'
```

**解决方案**:
```bash
# 确保在正确的目录运行
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 问题 2: 异步测试失败

```
asyncio_mode must be set to 'auto'
```

**解决方案**:
- 确保 `pytest.ini` 中配置了 `asyncio_mode = auto`
- 安装最新版本的 `pytest-asyncio`

### 问题 3: 数据库连接失败

```
ConnectionRefusedError: [Errno 61] Connection refused
```

**解决方案**:
- 测试使用了 mock，不需要实际的数据库
- 确保没有修改 `conftest.py` 中的 mock 配置

### 问题 4: 覆盖率文件冲突

```
Coverage数据冲突，已存在 .coverage 文件
```

**解决方案**:
```bash
# 删除旧的覆盖率文件
rm -f .coverage .coverage.* htmlcov/ .pytest_cache/
```

---

## 📚 更多资源

- [pytest 官方文档](https://docs.pytest.org/)
- [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov 文档](https://pytest-cov.readthedocs.io/)

---

**文档版本**: 1.0
**最后更新**: 2025-02-04
