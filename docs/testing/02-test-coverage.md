# 覆盖率目标和验证方法

> **版本**: 1.0
> **更新日期**: 2025-02-04

---

## 目录

- [覆盖率目标](#覆盖率目标)
- [覆盖率工具配置](#覆盖率工具配置)
- [覆盖率报告生成](#覆盖率报告生成)
- [覆盖率检查重点](#覆盖率检查重点)
- [覆盖率提升策略](#覆盖率提升策略)

---

## 覆盖率目标

### 分层覆盖率目标

| 层 | 目标覆盖率 | 说明 |
|----|-----------|------|
| **Utils** | 85% | 工具函数应全面测试 |
| **Infrastructure** | 70% | Mock外部依赖后可达 |
| **Domain** | 85% | 核心业务逻辑 |
| **Cognition** | 75% | Mock LLM后可达 |
| **Tools** | 70% | Mock API后可达 |
| **Agents** | 70% | Mock LLM和工具后可达 |
| **Services/API** | 60% | 端到端测试为主 |
| **整体目标** | 75% | 全局覆盖率 |

### 覆盖率类型说明

#### 1. 行覆盖率 (Line Coverage)

**定义**: 代码中执行的行数占总行数的比例

**目标**: ≥ 75%

**示例**:
```python
def calculate_discount(price, customer_type):
    if customer_type == "VIP":           # 行1
        return price * 0.8               # 行2
    elif customer_type == "NEW":         # 行3
        return price * 0.9               # 行4
    else:                                # 行5
        return price                     # 行6
```

要达到100%行覆盖率，需要测试所有分支。

#### 2. 分支覆盖率 (Branch Coverage)

**定义**: 执行的分支数占总分支数的比例

**目标**: ≥ 65%

**示例**:
```python
def is_valid_user(user):
    if user and user.is_active and user.has_permission:  # 3个条件
        return True
    return False
```

需要测试：
- `user=None`
- `user.is_active=False`
- `user.has_permission=False`
- 所有条件为True

#### 3. 函数覆盖率 (Function Coverage)

**定义**: 被调用的函数数占总函数数的比例

**目标**: ≥ 90%

**说明**: 确保所有公共函数都有测试调用。

---

## 覆盖率工具配置

### pytest-cov 配置

#### 安装

```bash
pip install pytest pytest-cov
```

#### 配置文件

创建 `pytest.ini` 或 `pyproject.toml`:

**pytest.ini**:
```ini
[pytest]
testpaths = backend
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=backend
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=70
```

**pyproject.toml**:
```toml
[tool.pytest.ini_options]
testpaths = ["backend"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--cov=backend",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=70"
]

[tool.coverage.run]
source = ["backend"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__init__.py",
    "*/migrations/*",
    "*/archive/*"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod"
]
```

### 覆盖率配置说明

#### include/exclude 配置

```python
# .coveragerc
[run]
source = backend
omit =
    */tests/*
    */test_*.py
    */__init__.py
    */migrations/*
    */archive/*
    */venv/*

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov
```

#### 排除合理的不测试代码

```python
# 这些代码可以排除覆盖率：
# 1. 抽象方法
@abstractmethod
def my_method(self): pass

# 2. 协议定义
class MyProtocol(Protocol): pass

# 3. 类型检查块
if TYPE_CHECKING:
    from typing import Something

# 4. 主程序入口
if __name__ == "__main__":
    main()

# 5. 显式标记
# pragma: no cover
def internal_helper(): pass
```

---

## 覆盖率报告生成

### 命令行报告

#### 基本报告

```bash
# 生成终端报告
pytest --cov=backend --cov-report=term

# 生成带缺失行的报告
pytest --cov=backend --cov-report=term-missing
```

**输出示例**:
```
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
backend/utils/config.py                    45      5    89%   23-27
backend/utils/compressor.py                32      2    94%   45-46
backend/domain/entities/task.py            78      8    90%   89-95
backend/agents/core/base.py               120     35    71%   156-190
---------------------------------------------------------------------
TOTAL                                     450    120    73%
```

#### HTML报告

```bash
# 生成HTML报告
pytest --cov=backend --cov-report=html

# 打开报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

#### XML报告 (CI集成)

```bash
# 生成XML报告
pytest --cov=backend --cov-report=xml
```

### 报告解读

#### 终端报告字段

| 字段 | 说明 |
|------|------|
| **Stmts** | 语句总数 |
| **Miss** | 未执行的语句数 |
| **Cover** | 覆盖率百分比 |
| **Missing** | 未覆盖的行号 |

#### HTML报告特性

- **文件浏览**: 按目录查看覆盖率
- **代码高亮**: 绿色=已覆盖，红色=未覆盖
- **分支标记**: 显示哪些分支未测试
- **趋势图表**: 覆盖率历史变化

---

## 覆盖率检查重点

### 1. 分支覆盖

#### 复杂条件测试

```python
# 待测试代码
def validate_user(user):
    if user is None:
        return False, "User is None"
    if not user.is_active:
        return False, "User not active"
    if not user.email_verified:
        return False, "Email not verified"
    if user.balance < 0:
        return False, "Negative balance"
    return True, "Valid"
```

**测试要点**:
```python
def test_validate_user_branches():
    # 分支1: user is None
    result = validate_user(None)
    assert result == (False, "User is None")

    # 分支2: not active
    inactive_user = User(is_active=False)
    result = validate_user(inactive_user)
    assert result == (False, "User not active")

    # 分支3: email not verified
    unverified_user = User(is_active=True, email_verified=False)
    result = validate_user(unverified_user)
    assert result == (False, "Email not verified")

    # 分支4: negative balance
    user = User(is_active=True, email_verified=True, balance=-10)
    result = validate_user(user)
    assert result == (False, "Negative balance")

    # 分支5: valid
    valid_user = User(is_active=True, email_verified=True, balance=100)
    result = validate_user(valid_user)
    assert result == (True, "Valid")
```

### 2. 异常处理

```python
# 待测试代码
def process_payment(amount, user):
    try:
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if user.balance < amount:
            raise InsufficientFundsError()
        user.balance -= amount
        return True
    except ValueError as e:
        logger.error(f"Invalid amount: {e}")
        return False
    except InsufficientFundsError:
        logger.warning("Insufficient funds")
        return False
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        raise
```

**测试要点**:
```python
def test_process_payment_exceptions():
    # 正常流程
    user = User(balance=100)
    assert process_payment(50, user) == True
    assert user.balance == 50

    # ValueError
    assert process_payment(0, user) == False
    assert process_payment(-10, user) == False

    # InsufficientFundsError
    assert process_payment(200, user) == False

    # 意外异常 (使用mock)
    with patch('module.User.balance', new_callable=PropertyMock) as mock_balance:
        mock_balance.side_effect = Exception("Unexpected")
        with pytest.raises(Exception):
            process_payment(10, user)
```

### 3. 边界条件

```python
# 待测试代码
def paginate(items, page=1, per_page=10):
    if per_page <= 0:
        raise ValueError("per_page must be positive")
    if page < 1:
        raise ValueError("page must be >= 1")

    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end]
```

**测试要点**:
```python
def test_paginate_boundaries():
    items = list(range(100))

    # 边界1: 第一页
    assert paginate(items, 1, 10) == list(range(10))

    # 边界2: 最后一页
    assert paginate(items, 10, 10) == list(range(90, 100))

    # 边界3: 空页
    assert paginate(items, 11, 10) == []

    # 边界4: per_page=1
    assert paginate(items, 1, 1) == [0]

    # 边界5: per_page超过总数
    assert paginate(items, 1, 200) == items

    # 边界6: page=0 (应该抛异常)
    with pytest.raises(ValueError):
        paginate(items, 0, 10)

    # 边界7: per_page=0 (应该抛异常)
    with pytest.raises(ValueError):
        paginate(items, 1, 0)
```

### 4. 异步代码

```python
# 待测试代码
async def fetch_data(url, timeout=5):
    try:
        async with asyncio.timeout(timeout):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
    except asyncio.TimeoutError:
        return {"error": "timeout"}
    except aiohttp.ClientError as e:
        return {"error": str(e)}
```

**测试要点**:
```python
@pytest.mark.asyncio
async def test_fetch_data_scenarios():
    # 成功场景
    with aioresponses() as m:
        m.get("http://example.com", payload={"data": "test"})
        result = await fetch_data("http://example.com")
        assert result == {"data": "test"}

    # 超时场景
    with aioresponses() as m:
        m.get("http://example.com", timeout=True)
        result = await fetch_data("http://example.com", timeout=0.1)
        assert result == {"error": "timeout"}

    # 错误场景
    with aioresponses() as m:
        m.get("http://example.com", status=500)
        result = await fetch_data("http://example.com")
        assert "error" in result
```

### 5. 并发代码

```python
# 待测试代码
async def parallel_fetch(urls, max_concurrent=5):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_with_limit(url):
        async with semaphore:
            return await fetch_data(url)

    tasks = [fetch_with_limit(url) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

**测试要点**:
```python
@pytest.mark.asyncio
async def test_parallel_fetch_concurrency():
    urls = [f"http://example.com/{i}" for i in range(10)]

    with aioresponses() as m:
        # 模拟延迟响应
        for url in urls:
            m.get(url, payload={"url": url})

        results = await parallel_fetch(urls, max_concurrent=3)

        # 验证结果
        assert len(results) == 10
        assert all(isinstance(r, dict) for r in results)
```

---

## 覆盖率提升策略

### 策略1: 从最简单的路径开始

```python
# 1. 先写"快乐路径"测试
def test_create_task_success():
    task = Task(id="1", raw_input="test")
    assert task.status == TaskStatus.PENDING

# 2. 然后添加边界条件
def test_create_task_with_empty_input():
    with pytest.raises(ValidationError):
        Task(id="1", raw_input="")

# 3. 最后添加异常路径
def test_create_task_with_invalid_status():
    with pytest.raises(ValueError):
        Task(id="1", raw_input="test", status="INVALID")
```

### 策略2: 使用参数化测试

```python
# 覆盖多个输入场景
@pytest.mark.parametrize("input,expected", [
    ("valid topic", True),           # 正常输入
    ("  spaces  ", True),            # 带空格
    ("", False),                     # 空字符串
    ("a", True),                     # 最小长度
    ("a" * 1000, True),              # 最大长度
    ("a" * 1001, False),             # 超过最大长度
])
def test_topic_validation(input, expected):
    result = validate_topic(input)
    assert result.is_valid == expected
```

### 策略3: 使用Fixture复用设置

```python
@pytest.fixture
def sample_task():
    return Task(id="test-1", raw_input="Create PPT about AI")

@pytest.fixture
def sample_user():
    return User(id="user-1", name="Test User")

# 复用fixture提高测试效率
def test_task_with_user(sample_task, sample_user):
    result = assign_task_to_user(sample_task, sample_user)
    assert result.assigned_to == sample_user.id
```

### 策略4: 集成测试补充单元测试

```python
# 单元测试: 测试单个函数
def test_validate_requirement():
    req = Requirement(ppt_topic="AI", page_num=10)
    assert req.is_valid()

# 集成测试: 测试完整流程
@pytest.mark.asyncio
async def test_requirement_to_framework():
    # 这个测试同时覆盖多个函数
    req = Requirement(ppt_topic="AI", page_num=10)
    service = FrameworkDesignService()
    framework = await service.design_framework(req)

    assert framework.total_pages == 10
    assert framework.pages[0].page_type == PageType.COVER
```

### 策略5: 使用覆盖率报告找盲点

1. 运行覆盖率测试
2. 打开HTML报告
3. 找到红色标记的行
4. 分析为什么未覆盖
5. 添加测试用例

```bash
# 1. 生成报告
pytest --cov=backend --cov-report=html

# 2. 打开报告
open htmlcov/index.html

# 3. 查找未覆盖的代码
# 例如发现 backend/domain/models/task.py:150 未覆盖

# 4. 添加测试
def test_task_retry_counter():
    task = Task(id="1", raw_input="test")
    # 触发第150行的逻辑
    task.increment_retry()
    assert task.retry_count == 1
```

### 策略6: 突变测试 (Mutation Testing)

使用工具检测测试质量:

```bash
# 安装mutmut
pip install mutmut

# 运行突变测试
mutmut run --paths-to-mutate backend/

# 查看结果
mutmut results
```

如果测试不够好，突变会存活（未被杀死）。

### 策略7: 覆盖率增量检查

在CI中检查覆盖率是否下降:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=backend --cov-report=xml
      - name: Check coverage
        run: |
          coverage=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
          if (( $(echo "$coverage < 70" | bc -l) )); then
            echo "Coverage $coverage% is below 70%"
            exit 1
          fi
```

---

## 覆盖率与质量的关系

### 高覆盖率的误区

❌ **误区1: 覆盖率=质量**
- 覆盖率只衡量代码执行量，不测试正确性
- 需要结合代码审查和功能测试

❌ **误区2: 追求100%覆盖率**
- 某些代码难以测试（如异常处理）
- 边际收益递减
- 70-80%通常是合理的平衡点

❌ **误区3: 只看整体覆盖率**
- 关键模块需要更高覆盖率
- 核心业务逻辑应该达到85%+

### 覆盖率最佳实践

✅ **分层设定目标**
- Utils层: 85%+
- Domain层: 85%+
- Infrastructure层: 70%+
- Agents层: 70%+
- API层: 60%+

✅ **持续监控**
- 每次PR检查覆盖率
- 防止覆盖率下降
- 报告覆盖率趋势

✅ **关注质量**
- 测试用例要有意义
- 避免为了覆盖率写无用测试
- 结合代码审查

---

## 常见问题

### Q1: 如何处理难以测试的代码?

**A**: 使用以下策略:
1. 重构代码，提高可测试性
2. 使用依赖注入
3. Mock外部依赖
4. 集成测试覆盖

### Q2: 覆盖率下降怎么办?

**A**:
1. 检查新增代码是否有测试
2. 检查是否删除了测试
3. 使用 `git diff` 找变化
4. 运行 `pytest --cov-report=term-missing` 查缺失

### Q3: 多高的覆盖率合适?

**A**:
- **关键业务逻辑**: 85%+
- **一般业务逻辑**: 70%+
- **工具函数**: 80%+
- **整体**: 70-75%

### Q4: 如何提高分支覆盖率?

**A**:
1. 识别所有条件分支
2. 为每个分支写测试
3. 使用参数化测试
4. 使用Mock模拟不同场景

---

## 总结

### 关键要点

1. **设定合理目标**: 不是100%，而是70-85%
2. **分层设定**: 关键模块要求更高
3. **持续监控**: CI集成覆盖率检查
4. **质量优先**: 测试质量 > 覆盖率数字

### 工具推荐

- **pytest-cov**: 覆盖率统计
- **coverage.py**: 底层覆盖率工具
- **mutmut**: 突变测试
- **pytest-html**: HTML测试报告

### 下一步

1. 配置 `pytest.ini` 或 `pyproject.toml`
2. 设定各层覆盖率目标
3. 集成到CI流程
4. 定期检查覆盖率报告

---

**维护者**: MultiAgentPPT Team
**版本**: 1.0
**最后更新**: 2025-02-04
