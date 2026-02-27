# Tools 参考文档

> **完整工具列表和详细说明**

本文档提供所有工具的完整参考信息，包括 Domain Tools、Python Skills 和 MD Skills。

---

## 📖 文档导航

### Domain Tools（可执行工具）
- **[Domain Tools 完整列表](./domain-tools.md)** - 10 个外部工具的详细说明
  - 搜索类：web_search, fetch_url, weixin_search
  - 媒体类：search_images
  - 实用类：create_pptx, xml_converter, a2a_client
  - 数据库类：state_store, vector_search

### Python Skills（可执行工作流）
- **[Python Skills 完整列表](./python-skills.md)** - 8 个工作流的详细说明
  - 研究类：research_workflow
  - 内容类：content_generation, content_optimization, content_quality_check
  - 框架类：framework_design, topic_decomposition, section_planning
  - 布局类：layout_selection

### MD Skills（分层指南）
- **[MD Skills 完整列表](./md-skills.md)** - 4 个指南文档的详细说明
  - 内容生成指南：content_generation_prompts
  - 研究工作指南：research_prompts
  - 框架设计指南：framework_prompts
  - 质量检查指南：quality_check_prompts

---

## 📊 工具统计

### 按类型统计

| 类型 | 数量 | 说明 |
|------|------|------|
| **Domain Tools** | 10 | 直接实现为 LangChain Tools |
| **Python Skills** | 8 | Python 类，转换为 Tools |
| **MD Skills** | 4 | Markdown 文件，封装为 Tools |
| **总计** | **22** | 统一管理 |

### 按类别统计

| 类别 | 工具数 | 包含 |
|------|--------|------|
| **SEARCH** | 3 | web_search, fetch_url, weixin_search |
| **MEDIA** | 1 | search_images |
| **UTILITY** | 3 | create_pptx, xml_converter, a2a_client |
| **DATABASE** | 2 | state_store, vector_search |
| **SKILL** | 12 | 8个 Python Skills + 4个 MD Skills |

---

## 🔍 如何使用参考文档

### 查找工具

**方式 1：按类别查找**
1. 确定你需要的功能（搜索、内容生成、研究...）
2. 查看对应类别的文档
3. 找到合适的工具

**方式 2：按名称查找**
```bash
# 在文档中搜索工具名称
grep -r "web_search" docs/tools/reference/
```

**方式 3：使用注册表**
```python
from backend.tools.application.tool_registry import get_native_registry

registry = get_native_registry()
registry.log_summary()  # 查看所有工具
```

### 理解工具文档格式

每个工具的参考文档包含：

```markdown
# 工具名称

## 📋 基本信息
- 工具名称
- 实现文件
- 工具类别
- 版本

## 🎯 功能说明
- 核心功能
- 使用场景

## 📖 使用示例
- 代码示例
- 参数说明

## 🔧 技术细节
- 实现原理
- 依赖项
- 性能考虑
```

---

## 📚 相关文档

- **[应用层文档](../application/)** - 如何在 Agent 中使用工具
- **[系统主文档](../README.md)** - Tools 系统总览
- **[工具注册表详解](../application/tool-registry.md)** - 注册表原理

---

**最后更新**: 2026-02-16
**维护者**: MultiAgentPPT 团队
