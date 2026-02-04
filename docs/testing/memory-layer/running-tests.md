# Memory 层测试运行指南

> **目标读者**: 开发者、测试工程师、CI/CD 工程师
> **用途**: 快速上手 Memory 层测试

---

## 📋 目录

- [环境准备](#环境准备)
- [快速开始](#快速开始)
- [测试运行模式](#测试运行模式)
- [覆盖率报告](#覆盖率报告)
- [常见问题](#常见问题)
- [CI/CD 集成](#cicd-集成)

---

## 环境准备

### 系统要求

- **Python**: 3.8+
- **操作系统**: Windows / Linux / macOS
- **内存**: 至少 2GB 可用内存
- **磁盘**: 至少 100MB 可用空间

### 依赖安装

#### 1. 核心依赖

```bash
# 测试框架
pip install pytest==7.4.0
pip install pytest-asyncio==0.21.0
pip install pytest-cov==4.1.0
pip install pytest-mock==3.11.1

# Mock Redis
pip install fakeredis==2.20.0
```

#### 2. 可选依赖

```bash
# 并行测试
pip install pytest-xdist==3.3.1

# 性能分析
pip install pytest-benchmark==4.0.0

# 代码覆盖率 HTML 报告
pip install coverage[toml]==7.3.2
```

#### 3. 开发依赖（从项目根目录）

```bash
cd backend
pip install -r requirements.txt
```

### 验证安装

```bash
# 检查 pytest 版本
pytest --version

# 验证异步支持
python -c "import pytest_asyncio; print('pytest-asyncio OK')"

# 验证 fakeredis
python -c "import fakeredis; print('fakeredis OK')"

# 验证 Memory 层可导入
cd memory/tests
python -c "from memory.models import MemoryMetadata; print('Memory layer OK')"
```

---

## 快速开始

### 第一次运行测试

```bash
# 1. 进入测试目录
cd backend/memory/tests

# 2. 运行所有测试
pytest -v

# 3. 查看结果
# 应该看到类似输出：
# ======== 200 passed in 5.23s ========
```

### 运行特定测试

```bash
# 运行单元测试
pytest unit/ -v

# 运行集成测试
pytest integration/ -v

# 运行特定文件
pytest unit/test_l1_layer.py -v

# 运行特定测试类
pytest unit/test_l1_layer.py::TestL1TransientLayer -v

# 运行特定测试方法
pytest unit/test_l1_layer.py::TestL1TransientLayer::test_set_and_get -v
```

---

## 测试运行模式

### 1. 开发模式

**用途**: 日常开发，快速反馈

```bash
# 快速测试（仅单元测试）
pytest unit/ -v

# 显示详细输出
pytest unit/ -v -s

# 遇到失败时停止
pytest unit/ -x

# 只运行失败的测试
pytest unit/ --lf
```

### 2. 全面模式

**用途**: 提交代码前，全面验证

```bash
# 所有测试
pytest -v

# 带覆盖率
pytest --cov=backend.memory --cov-report=html

# 生成详细报告
pytest -v --html=report.html --self-contained-html
```

### 3. 性能模式

**用途**: 性能基准测试

```bash
# 运行标记为 slow 的测试
pytest -m slow -v

# 性能基准测试
pytest -v --benchmark-only

# 最慢的 10 个测试
pytest -v --durations=10
```

### 4. CI/CD 模式

**用途**: 持续集成，自动化测试

```bash
# 并行运行（4 个进程）
pytest -n 4 -v

# 生成 XML 报告（用于 CI）
pytest -v --junitxml=results.xml

# 带覆盖率的 CI 模式
pytest --cov=backend.memory --cov-report=xml --cov-report=term --junitxml=results.xml
```

---

## 覆盖率报告

### 生成覆盖率报告

#### HTML 报告（推荐）

```bash
pytest --cov=backend.memory --cov-report=html

# 打开报告
# Windows: start htmlcov/index.html
# Linux/Mac: open htmlcov/index.html
```

#### 终端报告

```bash
# 简要报告
pytest --cov=backend.memory --cov-report=term-missing

# 详细报告
pytest --cov=backend.memory --cov-report=term
```

#### XML 报告

```bash
pytest --cov=backend.memory --cov-report=xml
```

### 覆盖率目标

| 组件 | 当前覆盖率 | 目标覆盖率 |
|------|-----------|-----------|
| 数据模型 | ~95% | ≥ 90% |
| L1 层 | ~90% | ≥ 85% |
| L2 层 | ~85% | ≥ 80% |
| L3 层 | ~80% | ≥ 75% |
| 提升引擎 | ~85% | ≥ 80% |
| 管理器 | ~80% | ≥ 75% |
| **总体** | **~80%** | **≥ 75%** |

### 查看未覆盖的代码

```bash
# 生成 HTML 报告
pytest --cov=backend.memory --cov-report=html

# 在浏览器中打开 htmlcov/index.html
# 红色标记表示未覆盖的代码
```

### 提高覆盖率

```bash
# 运行特定模块的覆盖率
pytest unit/test_models.py --cov=backend.memory.models --cov-report=html

# 查看哪些行未被覆盖
pytest --cov=backend.memory --cov-report=annotate
```

---

## 测试标记

### 可用标记

| 标记 | 说明 | 数量 |
|------|------|------|
| `unit` | 单元测试 | 150+ |
| `integration` | 集成测试 | 50+ |
| `slow` | 慢速测试（>1秒） | ~20 |
| `redis` | 需要 Redis | ~30 |
| `postgres` | 需要 PostgreSQL | ~20 |
| `vector` | 需要 pgvector | ~5 |

### 按标记运行

```bash
# 只运行单元测试
pytest -m unit -v

# 只运行集成测试
pytest -m integration -v

# 排除慢速测试
pytest -m "not slow" -v

# 只运行需要 Redis 的测试
pytest -m redis -v
```

---

## 调试测试

### 调试失败的测试

```bash
# 1. 运行特定测试并显示详细输出
pytest unit/test_l1_layer.py::TestL1TransientLayer::test_set_and_get -v -s

# 2. 进入 pdb 调试器
pytest unit/test_l1_layer.py::TestL1TransientLayer::test_set_and_get --pdb

# 3. 失败时进入 pdb
pytest unit/test_l1_layer.py::TestL1TransientLayer::test_set_and_get --pdb

# 4. 显示详细 traceback
pytest unit/test_l1_layer.py::TestL1TransientLayer::test_set_and_get --tb=long
```

### 查看测试输出

```bash
# 显示 print 输出
pytest -v -s

# 只显示失败的输出
pytest -v -s --tb=short

# 捕获日志
pytest -v --log-cli-level=DEBUG
```

---

## 常见问题

### 问题 1: 导入错误

**错误信息**:
```
ModuleNotFoundError: No module named 'memory'
```

**解决方案**:
```bash
# 确保在正确的目录
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest memory/tests/
```

### 问题 2: 异步测试错误

**错误信息**:
```
asyncio_only: async functions are not supported
```

**解决方案**:
```bash
# 确保安装了 pytest-asyncio
pip install pytest-asyncio

# 检查 pytest.ini 配置
cat pytest.ini
# 应该包含：asyncio_mode = auto
```

### 问题 3: fakeredis 错误

**错误信息**:
```
ImportError: cannot import name 'FakeStrictRedis'
```

**解决方案**:
```bash
pip install fakeredis==2.20.0
```

### 问题 4: 测试超时

**错误信息**:
```
TimeoutError: Condition not met within 5 seconds
```

**解决方案**:
```bash
# 排除慢速测试
pytest -m "not slow" -v

# 或增加超时时间
# 在测试中修改 wait_for_condition 调用
```

### 问题 5: 并发测试失败

**错误信息**:
```
AssertionError: Expected X but got Y
```

**解决方案**:
```bash
# 串行运行测试
pytest -v -n 0

# 或减少并发数
pytest -v -n 2
```

---

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Memory Layer Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-asyncio pytest-cov fakeredis
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

    - name: Run tests
      run: |
        cd backend/memory/tests
        pytest -v --cov=backend.memory --cov-report=xml --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        flags: memory-layer
        name: codecov-umbrella

    - name: Archive test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-results-${{ matrix.python-version }}
        path: backend/memory/tests/htmlcov/
```

### Jenkins 示例

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                sh 'pip install pytest pytest-asyncio pytest-cov fakeredis'
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Test') {
            steps {
                dir('backend/memory/tests') {
                    sh 'pytest -v --cov=backend.memory --cov-report=xml --cov-report=html --junitxml=results.xml'
                }
            }
        }

        stage('Report') {
            steps {
                junit 'backend/memory/tests/results.xml'
                publishHTML(target: [
                    reportDir: 'backend/memory/tests/htmlcov',
                    reportFiles: 'index.html',
                    reportName: 'Coverage Report'
                ])
            }
        }
    }
}
```

### GitLab CI 示例

```yaml
stages:
  - test

test:
  stage: test
  image: python:3.10

  before_script:
    - pip install pytest pytest-asyncio pytest-cov fakeredis
    - pip install -r requirements.txt

  script:
    - cd backend/memory/tests
    - pytest -v --cov=backend.memory --cov-report=xml --cov-report=html --junitxml=results.xml

  coverage: '/TOTAL.*\s+(\d+%)$/'

  artifacts:
    when: always
    paths:
      - backend/memory/tests/htmlcov/
      - backend/memory/tests/results.xml
    reports:
      coverage_report:
        coverage_format: cobertura
        path: backend/memory/tests/coverage.xml
      junit: backend/memory/tests/results.xml
```

---

## 测试脚本

### 快速测试脚本

创建 `backend/memory/tests/run_tests.sh`:

```bash
#!/bin/bash
# Memory 层快速测试脚本

set -e

echo "🧪 Memory Layer 测试"
echo "===================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 进入测试目录
cd "$(dirname "$0")"

# 快速测试（不包括慢速测试）
echo -e "${YELLOW}运行快速测试...${NC}"
pytest -m "not slow" -v

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 快速测试通过！${NC}"
    exit 0
else
    echo -e "${YELLOW}✗ 测试失败${NC}"
    exit 1
fi
```

使用：
```bash
chmod +x backend/memory/tests/run_tests.sh
./backend/memory/tests/run_tests.sh
```

### 完整测试脚本

创建 `backend/memory/tests/run_all_tests.sh`:

```bash
#!/bin/bash
# Memory 层完整测试脚本

set -e

echo "🧪 Memory Layer 完整测试"
echo "========================"

# 进入测试目录
cd "$(dirname "$0")"

# 运行所有测试
echo "运行所有测试..."
pytest -v

# 生成覆盖率报告
echo "生成覆盖率报告..."
pytest --cov=backend.memory --cov-report=html --cov-report=term

echo "✓ 测试完成！"
echo "覆盖报告：htmlcov/index.html"
```

---

## 相关文档

- [测试总览](../memory-layer/README.md)
- [单元测试详情](../memory-layer/unit-tests.md)
- [集成测试详情](../memory-layer/integration-tests.md)
- [测试覆盖率报告](../memory-layer/coverage-report.md)
