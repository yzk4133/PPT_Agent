# 📚 Infrastructure 测试文档索引

> **快速导航到所有测试文档**

---

## 📖 文档列表

| 文档 | 描述 | 适用人群 |
|------|------|---------|
| [README.md](README.md) | 总体概述和快速开始 | 所有人 |
| [TEST_SUMMARY.md](TEST_SUMMARY.md) | 测试统计和数量分析 | 开发者、项目经理 |
| [MODULE_DETAILS.md](MODULE_DETAILS.md) | 各模块测试内容详解 | 开发者、测试人员 |
| [RUNNING_TESTS.md](RUNNING_TESTS.md) | 运行测试的完整指南 | 开发者、DevOps |

---

## 🎯 按需查看

### 我想了解...

**"测试包含什么内容？"**
→ 阅读 [README.md](README.md)

**"有多少测试用例？覆盖了哪些功能？"**
→ 阅读 [TEST_SUMMARY.md](TEST_SUMMARY.md)

**"某个具体模块怎么测试的？"**
→ 阅读 [MODULE_DETAILS.md](MODULE_DETAILS.md)

**"如何运行测试？如何查看覆盖率？"**
→ 阅读 [RUNNING_TESTS.md](RUNNING_TESTS.md)

---

## 📊 快速统计

```
测试文件总数:    19 个
测试用例总数:    245+ 个
覆盖模块数:      12 个
目标覆盖率:      70%+
优先级分布:      P0: 85 | P1: 73 | P2: 66 | P3: 13
```

---

## 🚀 快速开始

```bash
# 运行所有测试
cd backend
pytest infrastructure/tests/

# 查看覆盖率
pytest infrastructure/tests/ --cov=backend/infrastructure --cov-report=html
open htmlcov/index.html
```

---

**文档版本**: 1.0
**最后更新**: 2025-02-04
