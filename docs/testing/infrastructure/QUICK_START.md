# 测试快速参考指南

> **Quick Start Guide - 如何运行和使用测试**
>
> 最后更新: 2025-02-04

---

## 🚀 30秒快速开始

```bash
# 1. 进入项目目录
cd backend

# 2. 运行所有测试
pytest infrastructure/tests/ --no-cov

# 3. 查看结果
# ✅ PASS = 测试通过
# ❌ FAIL = 测试失败
```

---

## 📊 当前测试状态

| 模块 | 状态 | 通过率 |
|------|------|--------|
| Config | ✅ 可用 | 100% |
| DI | ✅ 可用 | 100% |
| Health | ✅ 可用 | 100% |
| Cache | ✅ 可用 | 94% |
| Logging | 🟡 可用 | 82% |
| Security | ⚠️ 需修复 | - |
| 其他 | ⏳ 待测试 | - |

---

## 🔧 常用命令

### 运行测试

```bash
# 所有测试
pytest infrastructure/tests/ --no-cov

# 特定模块
pytest infrastructure/tests/config/ -v --no-cov
pytest infrastructure/tests/di/ -v --no-cov
pytest infrastructure/tests/health/ -v --no-cov

# 单个测试文件
pytest infrastructure/tests/config/test_common_config.py -v --no-cov

# 单个测试函数
pytest infrastructure/tests/config/test_common_config.py::TestEnvironment::test_environment_values -v --no-cov
```

### 带覆盖率

```bash
# 生成覆盖率报告
pytest infrastructure/tests/ --cov=infrastructure --cov-report=html

# 查看报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### 调试失败测试

```bash
# 显示详细输出
pytest infrastructure/tests/config/ -vv --no-cov

# 在第一个失败时停止
pytest infrastructure/tests/ -x --no-cov

# 只运行失败的测试
pytest infrastructure/tests/ --lf --no-cov

# 显示打印输出
pytest infrastructure/tests/config/ -s --no-cov
```

---

## ⚠️ 已知问题及解决方案

### 问题 1: bcrypt 库错误

**错误**:
```
ValueError: password cannot be longer than 72 bytes
AttributeError: module 'bcrypt' has no attribute '__about__'
```

**解决方案**:
```bash
pip install --upgrade bcrypt passlib
```

### 问题 2: 导入错误

**错误**:
```
ImportError: cannot import name 'AppConfig' from 'infrastructure'
```

**原因**: 使用了错误的导入方式

**解决方案**:
```python
# ❌ 错误
from infrastructure import AppConfig

# ✅ 正确
from infrastructure.config import AppConfig
```

### 问题 3: 数据库测试超时

**现象**: Database 测试挂起或超时

**原因**: Mock 不完善

**解决方案**: 当前跳过数据库测试
```bash
pytest infrastructure/tests/ --ignore=infrastructure/tests/database/ --no-cov
```

---

## 📋 测试文件结构

```
infrastructure/tests/
├── conftest.py                    # 全局 fixtures
├── fixtures/                      # 可重用的 fixtures
├── config/                        # ✅ 100% 通过
├── di/                            # ✅ 100% 通过
├── health/                        # ✅ 100% 通过
├── cache/                         # ✅ 94% 通过
├── test_logging/                  # 🟡 82% 通过
├── security/                      # ⚠️ 需修复
├── database/                      # ⏳ 待测试
├── llm/                           # ⏳ 待测试
├── middleware/                    # ⏳ 待测试
├── events/                        # ⏳ 待测试
├── checkpoint/                    # ⏳ 待测试
├── mcp/                           # ⏳ 待测试
├── metrics/                       # ⏳ 待测试
└── integration/                   # ⏳ 待测试
```

---

## 🎯 下一步行动

### 立即执行（P0）

1. **修复 bcrypt 问题**
   ```bash
   pip install --upgrade bcrypt passlib
   ```

2. **验证修复**
   ```bash
   pytest infrastructure/tests/security/test_password_handler.py -v --no-cov
   ```

### 短期执行（P1）

3. **运行所有可用测试**
   ```bash
   pytest infrastructure/tests/ --ignore=infrastructure/tests/database/ --ignore=infrastructure/tests/llm/ --no-cov
   ```

4. **修复小问题**
   - Logging 敏感数据过滤
   - Cache LRU 淘汰
   - JWT 时间计算

### 长期执行（P2）

5. **完成剩余模块测试**
6. **提高覆盖率到 70%+**

---

## 📖 详细文档

- [FINAL_REPORT.md](FINAL_REPORT.md) - 完整的最终报告
- [TESTING_ISSUES.md](TESTING_ISSUES.md) - 问题记录
- [RUNNING_TESTS.md](RUNNING_TESTS.md) - 详细运行指南
- [MODULE_DETAILS.md](MODULE_DETAILS.md) - 模块详情

---

## ✅ 检查清单

### 开始使用前

- [x] pytest 已安装
- [x] pytest-asyncio 已安装
- [x] pytest-cov 已安装
- [ ] bcrypt 已升级到最新版本
- [ ] 环境变量已正确设置

### 验证安装

```bash
# 检查 pytest
pytest --version

# 检查 pytest-asyncio
python -c "import pytest_asyncio; print(pytest_asyncio.__version__)"

# 检查 bcrypt
python -c "import bcrypt; print(bcrypt.__version__)"

# 运行简单测试
pytest infrastructure/tests/config/test_common_config.py::TestEnvironment::test_environment_values -v
```

---

## 💡 提示

1. **首次运行**: 先运行 config 模块测试，它们最稳定
2. **开发时**: 使用 `-x` 参数在第一个失败时停止
3. **调试时**: 使用 `-vv` 获取最详细的输出
4. **CI/CD**: 使用 `--no-cov` 加快测试速度
5. **覆盖率**: 只在本地生成，不要在每次运行时都生成

---

**快速指南版本**: 1.0
**最后更新**: 2025-02-04
**维护者**: MultiAgentPPT Team
