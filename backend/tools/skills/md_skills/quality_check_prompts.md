---
name: quality_check_guide
description: 内容质量检查的分层指南，包括质量标准、评分方法和优化策略
category: quality
version: 1.0.0
---

# 质量检查指南

## Level 1: 基本检查

### 检查项

1. **标题长度**: 5-20字
2. **要点数量**: 3-5个
3. **结构完整**: 有标题、有要点

### 快速验证

```python
def quick_check(content):
    return {
        "title_ok": 5 <= len(content["title"]) <= 20,
        "has_points": len(content["key_points"]) >= 3,
        "complete": bool(content.get("title")) and bool(content.get("key_points"))
    }
```

---

## Level 2: 质量指标

### 详细检查项

| 项目 | 标准 | 权重 |
|------|------|------|
| 标题长度 | 5-20 字 | 15% |
| 标题吸引力 | 不使用套话 | 10% |
| 要点数量 | 3-5 个 | 20% |
| 要点长度 | < 50 字 | 15% |
| 平行结构 | 保持一致 | 15% |
| 支撑证据 | 有细节说明 | 15% |

### 质量分数

```python
score = sum(checks.values()) / len(checks)

if score >= 0.9:
    return "优秀"
elif score >= 0.8:
    return "良好"
elif score >= 0.7:
    return "一般"
else:
    return "需改进"
```

---

## Level 3: 优化策略

### 迭代优化流程

```
初始内容（分数 0.7）
    ↓
第一轮优化：修复结构（分数 0.8）
    ↓
第二轮优化：改进表达（分数 0.85）
    ↓
第三轮优化：润色细节（分数 0.92）
```

### 优化优先级

| 优先级 | 问题类型 | 优化方法 |
|--------|----------|----------|
| P0 | 结构性问题 | 标题长度、要点数量 |
| P1 | 表达问题 | 清晰度、吸引力 |
| P2 | 润色问题 | 选词、语气 |

### 风格适配

根据受众调整内容风格：
- **专家**: 专业术语、逻辑严密
- **大众**: 类比生动、语言通俗
- **学生**: 循序渐进、增加示例

---

**最后更新**: 2026-02-16
**维护者**: MultiAgentPPT Team
**版本**: 1.0.0
