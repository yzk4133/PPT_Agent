# MD Skills 参考文档

> **4 个分层指南文档的完整列表和详细说明**

MD Skills 是静态的 Markdown 文档，封装为 LangChain Tools 后可以被 LLM 查阅参考。每个 MD Skill 提供 Level 1-3 的分层指导。

---

## 📋 Skills 列表

### 1. content_generation_prompts

**基本信息**
- **Skill 名称**: `content_generation_prompts`
- **文件名**: `content_generation_prompts.md`
- **实现文件**: `backend/tools/skills/md_skills/content_generation_prompts.md`
- **工具类别**: SKILL
- **版本**: 1.0.0

**功能说明**
提供内容生成的最佳实践和分层指南。

**层级结构**
- **Level 1: 快速指南** - 3 步快速生成
  - 理解需求
  - 提取要点
  - 生成内容

- **Level 2: 详细指南** - 完整参数说明
  - 页面类型适配
  - 语调风格调整
  - 结构化方法

- **Level 3: 高级技巧** - 深入优化策略
  - 迭代优化流程
  - 质量提升技巧
  - 风格适配方法

**使用场景**
- LLM 不确定如何生成高质量内容时
- 需要参考内容生成的最佳实践
- 遇到质量问题时查看详细指导

**调用示例**
```python
# LLM 调用 MD Tool
result = await content_generation_prompts.ainvoke({
    "level": 2,           # 详细程度（1-3）
    "progressive": True   # 包含所有较低级别
})
```

**返回内容**
```markdown
# 内容生成指南

## Level 1: 快速指南

### 核心步骤（3 步）

1. **理解需求** → 分析页面类型、目标受众、核心信息
2. **提取要点** → 从研究资料中提取 3-5 个关键要点
3. **生成内容** → 使用简洁、专业、有逻辑性的语言

### 快速模板

**内容页模板**：
- 标题：5-20 字，简洁有力
- 要点：3-5 个，每个 < 50 字
- 结构：平行结构，保持一致

---

## Level 2: 详细指南

### 页面类型适配

**内容页**：
- 重点：逻辑清晰，层次分明
- 结构：引言 → 3-5个要点 → 总结

**图表页**：
- 重点：数据准确，解读清晰
- 结构：图表标题 → 数据说明 → 关键洞察

...

## Level 3: 高级技巧

### 迭代优化流程

```
初稿（分数 0.7）
    ↓
第1轮：修复结构问题（分数 0.8）
    ↓
第2轮：改进表达（分数 0.85）
    ↓
第3轮：润色细节（分数 0.92）
```
```

---

### 2. research_prompts

**基本信息**
- **Skill 名称**: `research_prompts`
- **文件名**: `research_prompts.md`
- **实现文件**: `backend/tools/skills/md_skills/research_prompts.md`
- **工具类别**: SKILL
- **版本**: 1.0.0

**功能说明**
提供研究工作流程的分层指南。

**层级结构**
- **Level 1: 快速指南** - 3 步研究流程
  - 理解需求
  - 搜索收集
  - 整理归纳

- **Level 2: 详细指南** - 搜索策略和技巧
  - 信息类型识别
  - 关键词构建
  - 工具选择

- **Level 3: 高级技巧** - 深度挖掘策略
  - 并行搜索
  - 深度挖掘
  - 数据验证

**使用场景**
- 需要研究方法指导
- 搜索结果不理想时
- 需要提升研究质量

**调用示例**
```python
result = await research_prompts.ainvoke({
    "level": 2,
    "progressive": True
})
```

---

### 3. framework_prompts

**基本信息**
- **Skill 名称**: `framework_prompts`
- **文件名**: `framework_prompts.md`
- **实现文件**: `backend/tools/skills/md_skills/framework_prompts.md`
- **工具类别**: SKILL
- **版本**: 1.0.0

**功能说明**
提供 PPT 框架设计的分层指南。

**层级结构**
- **Level 1: 快速指南** - 标准框架结构
  - 封面、目录、内容、总结
  - 页数分配建议

- **Level 2: 详细指南** - 页面类型说明
  - 各类页面的特点和用途
  - 框架设计流程
  - 研究需求标记

- **Level 3: 高级技巧** - 模块化设计
  - 模块化框架设计
  - 研究需求标记策略
  - 图表分布策略

**使用场景**
- 设计 PPT 框架时参考
- 规划页面类型和布局
- 优化框架结构

**调用示例**
```python
result = await framework_prompts.ainvoke({
    "level": 1,
    "progressive": False  # 只返回 Level 1
})
```

---

### 4. quality_check_prompts

**基本信息**
- **Skill 名称**: `quality_check_prompts`
- **文件名**: `quality_check_prompts.md`
- **实现文件**: `backend/tools/skills/md_skills/quality_check_prompts.md`
- **工具类别**: SKILL
- **版本**: 1.0.0

**功能说明**
提供内容质量检查的分层指南。

**层级结构**
- **Level 1: 基本检查** - 快速验证
  - 标题长度
  - 要点数量
  - 结构完整性

- **Level 2: 质量指标** - 详细评分
  - 各项质量标准
  - 权重分配
  - 质量分数计算

- **Level 3: 优化策略** - 迭代改进
  - 迭代优化流程
  - 优化优先级
  - 风格适配

**使用场景**
- 检查内容质量
- 发现质量问题
- 制定优化方案

**调用示例**
```python
result = await quality_check_prompts.ainvoke({
    "level": 3,
    "progressive": True
})
```

---

## 🔧 使用示例

### 在 Agent 中使用

```python
from backend.agents.core.base_agent import BaseToolAgent

class ContentAgent(BaseToolAgent):
    def __init__(self):
        super().__init__(
            tool_names=[
                "content_generation",         # Python Skill
                "content_generation_prompts", # MD Guide
                "quality_check_prompts",      # MD Guide
            ],
            agent_name="ContentAgent"
        )
```

### LLM 自主决策

```python
# LLM 推理过程
query = """
我需要生成一个高质量的内容，但不确定如何做。

请先使用 content_generation_prompts(level=1) 获取快速指南，
然后根据指南生成内容。

页面主题：AI在医疗领域的应用
"""

# LLM 可能的决策路径：
# 1. 调用 content_generation_prompts(level=1) 获取快速指南
# 2. 学习指南中的 3 步流程
# 3. 调用 content_generation 执行生成
# 4. 如果质量不佳，调用 content_generation_prompts(level=2) 获取详细指导
# 5. 重新生成或优化内容
```

### 渐进式查阅

```python
# 首次使用：Level 1（快速指南）
result1 = await content_generation_prompts.ainvoke({
    "level": 1,
    "progressive": False
})
# 返回：简洁的 3 步流程

# 遇到问题：Level 2（详细指南）
result2 = await content_generation_prompts.ainvoke({
    "level": 2,
    "progressive": False
})
# 返回：完整的参数说明和方法

# 仍需帮助：Level 3（高级技巧）
result3 = await content_generation_prompts.ainvoke({
    "level": 3,
    "progressive": True
})
# 返回：Level 1 + 2 + 3 的所有内容（渐进式）
```

---

## 📊 MD Skills 特性

### 分层结构

| Level | 名称 | 内容量 | 适用场景 |
|-------|------|--------|----------|
| **Level 1** | 快速指南 | ~500 字 | 首次使用、快速查看 |
| **Level 2** | 详细指南 | ~2000 字 | 遇到问题、需要详细说明 |
| **Level 3** | 高级技巧 | ~3000 字 | 深入优化、学习最佳实践 |

### Progressive 参数

| 参数值 | 返回内容 | 适用场景 |
|--------|----------|----------|
| **True** | Level 1 到 N 的所有内容 | 需要完整的渐进式指导 |
| **False** | 只返回 Level N 的内容 | 只需要特定级别的指导 |

### 调用示例

```python
# 示例 1：只看快速指南
await guide.ainvoke({"level": 1, "progressive": False})

# 示例 2：快速指南 + 详细指南
await guide.ainvoke({"level": 2, "progressive": True})

# 示例 3：所有层级（完整指南）
await guide.ainvoke({"level": 3, "progressive": True})
```

---

## 💡 最佳实践

### 1. 配对使用

```python
# ✅ 推荐：MD Guide + Python Skill
tool_names = [
    "research_workflow",        # 执行研究
    "research_prompts",         # 研究指南
]

# LLM 使用流程：
# 1. 查阅 research_prompts(level=1) 了解快速流程
# 2. 调用 research_workflow 执行研究
# 3. 如果遇到问题，查阅 research_prompts(level=2)
```

### 2. 渐进式学习

```python
# LLM 自主决策流程
query = """
生成高质量内容。

如果不确定如何做：
1. 先调用 content_generation_prompts(level=1) 获取快速指南
2. 根据指南调用 content_generation
3. 检查质量，如果 < 0.8，调用 content_generation_prompts(level=2)
4. 优化后再次检查
"""
```

### 3. 错误恢复

```python
# MD Guides 作为降级方案
try:
    # 尝试执行任务
    result = await python_skill.ainvoke(...)
except Exception as e:
    # 查阅 MD Guide 获取替代方案
    guide = await md_guide.ainvoke({"level": 2})
    # 根据 Guide 手动执行
```

---

## 📈 效果对比

### Before（不使用 MD Guides）

```python
# LLM 只有 Python Skills
tool_names = ["content_generation"]

# 可能的问题：
# - 不了解最佳实践
# - 生成质量不稳定
# - 遇到问题无法自查
```

### After（使用 MD Guides）

```python
# LLM 有 Python Skills + MD Guides
tool_names = [
    "content_generation",
    "content_generation_prompts",
    "quality_check_prompts",
]

# 优势：
# ✅ 可以查阅最佳实践
# ✅ 生成质量更稳定
# ✅ 遇到问题有指导
# ✅ 可以自我纠错
```

---

## 🔄 更新 MD Skills

MD Skills 是纯文本文件，更新非常简单：

### 1. 编辑文件

```bash
# 编辑 MD 文件
vim backend/tools/skills/md_skills/content_generation_prompts.md
```

### 2. 遵循格式

```markdown
---
name: content_generation_prompts
description: 内容生成的最佳实践和分层指南
category: content
version: 1.0.0
---

# 标题

## Level 1: 快速指南
...

## Level 2: 详细指南
...

## Level 3: 高级技巧
...
```

### 3. 重启服务

```bash
# 重启后自动重新加载
systemctl restart multiagent-ppt
```

**无需修改代码**！MD Skills 会自动被扫描和注册。

---

## 📚 相关文档

- **[应用层文档](../application/)** - 如何在 Agent 中使用这些 MD Skills
- **[Python Skills 参考](./python-skills.md)** - Python Skills 完整列表
- **[Domain Tools 参考](./domain-tools.md)** - Domain Tools 完整列表

---

**最后更新**: 2026-02-16
**维护者**: MultiAgentPPT 团队
