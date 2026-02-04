# MultiAgentPPT 测试策略

> **版本**: 1.0
> **更新日期**: 2025-02-04
> **架构类型**: 8层分层架构 + 多Agent系统测试策略

---

## 概述

本文档说明 MultiAgentPPT 后端模块的测试策略，包括测试顺序、覆盖率目标、测试编写指南和关键文件清单。

### 测试目标

- **确保代码质量**: 通过单元测试、集成测试和端到端测试验证系统行为
- **支持持续重构**: 为代码重构提供安全网
- **文档化代码行为**: 测试即文档，展示系统预期行为
- **提升开发效率**: 快速发现问题，减少调试时间

### 测试原则

1. **自底向上**: 从基础层开始测试，逐步向上层推进
2. **依赖驱动**: 优先测试无依赖或依赖少的模块
3. **隔离性**: 使用 Mock 隔离外部依赖
4. **可重复性**: 测试结果应稳定可重复
5. **快速反馈**: 单元测试应快速执行，集成测试可较慢

---

## 7个阶段概览

```
阶段 1: Utils 层 (无依赖)
   ├─ 配置管理
   ├─ 上下文压缩
   ├─ 重试装饰器
   └─ PPT生成工具

阶段 2: Infrastructure 层 (技术基础)
   ├─ LLM工厂和降级
   ├─ 缓存系统
   ├─ Checkpoint管理
   ├─ 数据库连接
   ├─ 日志配置
   └─ MCP加载器

阶段 3: Domain 层 (核心业务逻辑)
   ├─ 值对象 (Value Objects)
   ├─ 实体 (Entities)
   ├─ 领域服务
   ├─ 领域事件
   └─ 领域异常

阶段 4: Cognition 层 (AI认知能力)
   ├─ 提示词管理
   ├─ 记忆系统核心
   └─ 记忆服务

阶段 5: Tools 层 (Agent工具)
   ├─ 工具注册表
   ├─ 搜索工具
   ├─ 媒体工具
   └─ 技能框架

阶段 6: Agents 层 (Agent实现)
   ├─ 基础Agent类
   ├─ 规划Agent
   ├─ 研究Agent
   ├─ 生成Agent
   └─ 记忆Mixin

阶段 7: Services & API 层 (应用层)
   ├─ 服务层
   ├─ 工作流编排
   ├─ API路由
   └─ 端到端测试
```

---

## 各阶段快速参考

| 阶段 | 层 | 测试重点 | 估计时间 |
|------|-----|---------|---------|
| 1 | Utils | 工具函数正确性 | 1-2天 |
| 2 | Infrastructure | 外部服务集成 | 3-5天 |
| 3 | Domain | 业务逻辑验证 | 2-3天 |
| 4 | Cognition | 提示词和记忆 | 3-4天 |
| 5 | Tools | 工具注册和调用 | 2-3天 |
| 6 | Agents | Agent行为 | 4-5天 |
| 7 | Services/API | 端到端流程 | 3-4天 |

---

## 注意事项摘要

### 多Agent系统测试要点

1. **并发测试**: 并行Agent需要测试并发安全性
2. **通信测试**: 测试Agent间数据传递
3. **状态测试**: 测试Agent状态转换
4. **记忆测试**: 测试记忆存取和共享

### Mock策略

- **LLM调用**: 使用MockLLM模拟响应
- **数据库**: 使用SQLite内存数据库
- **Redis**: 使用fakeredis或Mock
- **MCP工具**: Mock工具响应

### 异步测试

- 所有异步函数使用 `pytest.mark.asyncio`
- 使用 `pytest-asyncio` 插件
- 注意异步上下文管理器

---

## 如何使用本文档

### 对于新开发者

1. 从 [01-test-order.md](./01-test-order.md) 了解测试顺序和原因
2. 阅读 [03-test-guide.md](./03-test-guide.md) 学习测试编写方法
3. 参考 [04-critical-files.md](./04-critical-files.md) 编写具体测试

### 对于测试负责人

1. 查看 [02-test-coverage.md](./02-test-coverage.md) 设定覆盖率目标
2. 根据 [01-test-order.md](./01-test-order.md) 制定测试计划
3. 监控各阶段覆盖率完成情况

### 对于代码审查者

1. 参考 [03-test-guide.md](./03-test-guide.md) 审查测试代码质量
2. 检查测试覆盖率是否达标
3. 验证Mock使用是否合理

---

## 文档导航

### 总体指南

| 文档 | 说明 |
|------|------|
| [01-test-order.md](./01-test-order.md) | 详细的7阶段测试顺序，包含依赖关系分析 |
| [02-test-coverage.md](./02-test-coverage.md) | 覆盖率目标、工具配置和提升策略 |
| [03-test-guide.md](./03-test-guide.md) | 测试编写指南、最佳实践和工具介绍 |
| [04-critical-files.md](./04-critical-files.md) | 关键文件清单和测试要点 |

### 各层详细文档

| 层 | 文档 | 状态 |
|-----|------|------|
| **Infrastructure** | [infrastructure/](./infrastructure/) | ✅ 已完成 |
| Domain | [03-domain-*.md](./03-domain-test-plan.md) | 🟡 进行中 |
| Utils | - | ⏳ 待开始 |
| Cognition | - | ⏳ 待开始 |
| Tools | - | ⏳ 待开始 |
| Agents | - | ⏳ 待开始 |
| Services/API | - | ⏳ 待开始 |

### Infrastructure 层文档 📚

> **阶段 2 完成** - Infrastructure 层测试已实施，85%+ 通过率

- **[infrastructure/README.md](./infrastructure/)** - Infrastructure 测试文档入口
- **[infrastructure/QUICK_START.md](./infrastructure/QUICK_START.md)** - 30秒快速开始 ⭐
- **[infrastructure/FINAL_REPORT.md](./infrastructure/FINAL_REPORT.md)** - 最终测试报告
- **[infrastructure/TEST_SUMMARY.md](./infrastructure/TEST_SUMMARY.md)** - 测试统计摘要
- **[infrastructure/RUNNING_TESTS.md](./infrastructure/RUNNING_TESTS.md)** - 运行测试完整指南

**快速链接**:
- 运行测试: `cd backend && pytest infrastructure/tests/ --no-cov`
- 查看状态: 6个模块已验证，通过率85%+
- 详细文档: [点击查看](./infrastructure/)

---

## 快速开始

### 安装测试依赖

```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
pip install fakeredis mock
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定阶段的测试
pytest backend/utils/tests/
pytest backend/domain/tests/

# 生成覆盖率报告
pytest --cov=backend --cov-report=html

# 运行异步测试
pytest -v
```

### 参考示例

查看现有测试文件：
```bash
backend/agents/tests/test_agent_memory_integration.py
```

---

## 相关文档

- [后端架构文档](../backend-architecture.md) - 了解系统架构
- [领域层文档](../domain-layer.md) - 了解领域模型
- [README.md](../README.md) - 项目说明

---

**维护者**: MultiAgentPPT Team
**版本**: 1.0
**最后更新**: 2025-02-04
