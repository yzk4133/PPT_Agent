# 需求解析 Agent 详解

> **核心个性**：理解模糊的用户输入，提取结构化的 PPT 需求

---

## 目录

1. [职责与能力](#职责与能力)
2. [核心个性特征](#核心个性特征)
3. [输入输出格式](#输入输出格式)
4. [关键实现细节](#关键实现细节)
5. [降级策略](#降级策略)
6. [使用示例](#使用示例)
7. [常见问题](#常见问题)

---

## 职责与能力

### 核心职责

需求解析 Agent 是整个 PPT 生成流程的**第一步**，负责将用户的**自然语言输入**转换为**结构化需求**。

**为什么重要？**
- ❌ 没有它：后续 Agent 不知道要生成什么样的 PPT
- ✅ 有它：为后续所有 Agent 提供明确的指导

### 关键能力

| 能力 | 说明 | 重要性 |
|------|------|--------|
| **理解模糊输入** | 处理不完整、不清晰的用户描述 | ⭐⭐⭐⭐⭐ |
| **信息提取** | 从文本中提取主题、页数、风格等 | ⭐⭐⭐⭐⭐ |
| **场景识别** | 自动判断使用场景（商业/学术/产品演示等） | ⭐⭐⭐⭐ |
| **语言检测** | 自动识别中文/英文 | ⭐⭐⭐ |
| **需求补全** | 为缺失的信息提供合理的默认值 | ⭐⭐⭐⭐ |
| **降级解析** | LLM 失败时使用规则引擎 | ⭐⭐⭐⭐ |

---

## 核心个性特征

### 1. 理解模糊输入

用户输入可能是这样的：

```
❌ 不清晰的输入：
"做一个PPT"
"关于AI的"
"要好看一点"

✅ Agent 需要理解：
隐含的主题 → 需要推断
隐含的页数 → 使用默认值
隐含的风格 → 根据场景推断
```

**实现方式**：

```python
# 提示词设计
SYSTEM_PROMPT = """
你是一个专业的 PPT 需求分析专家。

你的任务是：
1. 理解用户的自然语言输入（可能不完整、不清晰）
2. 提取或推断出 PPT 的关键信息
3. 为缺失的信息提供合理的默认值

推断原则：
- 如果用户没有指定页数，默认使用 10 页
- 如果用户没有指定风格，根据场景推断（商业=商务风，学术=学术风）
- 如果用户没有指定主题，从输入文本中提取关键短语
"""
```

---

### 2. 场景自动识别

**支持的场景类型**：

```python
SCENARIOS = {
    "business_report": "商业报告",
    "campus_defense": "校园答辩",
    "product_presentation": "产品演示",
    "training": "培训",
    "conference": "会议",
    "other": "其他"
}
```

**识别逻辑**：

```python
def _detect_scene(self, user_input: str) -> str:
    """自动识别使用场景"""

    # 关键词映射
    scene_keywords = {
        "business_report": ["财报", "业绩", "商业", "报告", "季度", "年度"],
        "campus_defense": ["答辩", "论文", "毕业", "学术", "研究", "开题"],
        "product_presentation": ["产品", "发布", "演示", "功能", "介绍"],
        "training": ["培训", "教学", "课程", "学习"],
        "conference": ["会议", "峰会", "论坛", "演讲"],
    }

    # 匹配关键词
    for scene, keywords in scene_keywords.items():
        if any(keyword in user_input for keyword in keywords):
            return scene

    # 默认为商业报告
    return "business_report"
```

---

### 3. 语言自动检测

**支持的类型**：

```python
LANGUAGES = {
    "ZH-CN": "中文（简体）",
    "EN-US": "英文（美国）"
}
```

**检测逻辑**：

```python
def _detect_language(self, user_input: str) -> str:
    """自动检测语言"""

    # 检查是否包含中文字符
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in user_input)

    if has_chinese:
        return "ZH-CN"
    else:
        return "EN-US"
```

**为什么重要？**
- 影响 LLM 的提示词语言
- 影响默认模块的名称
- 影响模板选择

---

### 4. 智能默认值

| 字段 | 默认值规则 | 例子 |
|------|-----------|------|
| `page_num` | 10 页 | 固定默认值 |
| `template_type` | 根据场景推断 | 商业报告 → business_template |
| `scene` | 根据关键词识别 | 提到"答辩" → campus_defense |
| `core_modules` | 根据场景生成 | 答辩场景 → [封面, 研究背景, 研究方法, ...] |
| `language` | 根据输入检测 | 有中文字符 → ZH-CN |
| `keywords` | 提取前3个关键词 | "人工智能深度学习" → [人工智能, 深度, 学习] |
| `need_research` | 默认 False | 可以通过参数或场景调整 |

**示例**：

```python
# 输入
user_input = "生成一份关于人工智能的PPT"

# 输出（自动填充）
{
    "ppt_topic": "人工智能",
    "page_num": 10,          # ← 默认值
    "scene": "business_report", # ← 默认值
    "template_type": "business_template", # ← 根据场景推断
    "language": "ZH-CN",      # ← 检测到中文
    "core_modules": [...],    # ← 根据场景生成
    "keywords": ["人工智能"],  # ← 提取关键词
    "need_research": False    # ← 默认值
}
```

---

## 输入输出格式

### 输入

```python
user_input: str  # 用户的自然语言输入
```

**示例**：
```python
# 简单输入
"做一个关于AI的PPT"

# 详细输入
"生成一份15页的PPT，主题是人工智能在医疗领域的应用，学术风格，需要引用最新研究"

# 不完整输入
"关于量子计算的演示文稿"
```

### 输出

```python
{
    # 基本信息
    "ppt_topic": str,              # PPT 主题
    "page_num": int,               # 页数

    # 场景与风格
    "scene": str,                  # 使用场景
    "template_type": str,          # 模板类型
    "language": str,               # 语言

    # 受众与目的
    "audience": str,               # 目标受众
    "industry": str,               # 所属行业

    # 结构指导
    "core_modules": List[str],     # 核心模块列表

    # 特殊需求
    "need_research": bool,         # 是否需要研究
    "special_require": List[str],   # 特殊要求

    # 样式偏好
    "style_preference": str,       # 风格偏好
    "color_scheme": str,           # 配色方案
    "keywords": List[str]           # 关键词
}
```

---

## 关键实现细节

### 1. 主流程

```python
async def parse(self, user_input: str) -> Dict[str, Any]:
    """
    解析用户输入的主流程

    流程：
    1. 预处理：检测语言、识别场景
    2. LLM 解析：调用 LLM 提取结构化信息
    3. 验证：检查输出是否完整
    4. 降级：如果 LLM 失败，使用规则引擎
    5. 返回：结构化需求字典
    """

    # 1. 预处理
    language = self._detect_language(user_input)
    scene = self._detect_scene(user_input)

    # 2. LLM 解析
    requirement = await self._parse_with_llm(
        user_input=user_input,
        language=language,
        scene=scene
    )

    # 3. 验证和修复
    requirement = self._validate_and_fill_defaults(
        requirement=requirement,
        user_input=user_input
    )

    return requirement
```

---

### 2. LLM 提示词设计

```python
def _build_prompt(
    self,
    user_input: str,
    language: str,
    scene: str
) -> str:
    """构建 LLM 提示词"""

    return f"""
请分析以下 PPT 生成需求，提取关键信息：

用户输入：
{user_input}

已识别信息：
- 语言：{language}
- 场景：{scene}

请提取以下信息（如果用户没有明确说明，请根据上下文合理推断）：

1. ppt_topic: PPT 的主题
2. page_num: 页数（10-20页为宜）
3. audience: 目标受众
4. industry: 所属行业（如有）
5. core_modules: 核心模块列表（3-6个）
6. need_research: 是否需要研究资料（true/false）
7. keywords: 关键词列表（3-5个）
8. special_require: 特殊要求（如有）

请以 JSON 格式输出。
"""
```

---

### 3. 验证和默认值填充

```python
def _validate_and_fill_defaults(
    self,
    requirement: Dict[str, Any],
    user_input: str
) -> Dict[str, Any]:
    """验证并填充默认值"""

    # 1. 确保必需字段存在
    if "ppt_topic" not in requirement:
        requirement["ppt_topic"] = user_input[:100]  # 取前100个字符

    # 2. 填充默认页数
    if "page_num" not in requirement:
        requirement["page_num"] = 10
    elif requirement["page_num"] < 1:
        requirement["page_num"] = 10

    # 3. 填充语言
    if "language" not in requirement:
        requirement["language"] = self._detect_language(user_input)

    # 4. 填充场景
    if "scene" not in requirement:
        requirement["scene"] = self._detect_scene(user_input)

    # 5. 填充模板类型
    if "template_type" not in requirement:
        requirement["template_type"] = self._get_default_template(requirement["scene"])

    # 6. 填充核心模块
    if "core_modules" not in requirement or not requirement["core_modules"]:
        requirement["core_modules"] = self._get_default_modules(requirement["scene"])

    # 7. 填充关键词
    if "keywords" not in requirement or not requirement["keywords"]:
        requirement["keywords"] = self._extract_keywords(user_input)

    # 8. 填充研究标记
    if "need_research" not in requirement:
        requirement["need_research"] = False

    return requirement
```

---

### 4. 关键词提取

```python
def _extract_keywords(self, text: str) -> List[str]:
    """从文本中提取关键词"""

    # 简单实现：提取所有2-4个字的词组
    import re

    # 移除标点符号
    text = re.sub(r'[^\w\s]', ' ', text)

    # 分词
    words = text.split()

    # 过滤停用词
    stopwords = {"的", "是", "一个", "生成", "制作", "PPT", "ppt"}
    keywords = [w for w in words if w not in stopwords and len(w) >= 2]

    # 取前3个
    return keywords[:3]
```

---

## 降级策略

### 什么时候触发降级？

```
LLM 解析失败 ↓
│
├─ 网络错误
├─ API 限流
├─ 超时
└─ 返回格式错误

触发降级策略 → 使用规则引擎解析
```

### 降级实现

```python
def _fallback_parse(self, user_input: str) -> Dict[str, Any]:
    """
    降级解析：使用规则引擎

    不依赖 LLM，使用规则提取信息
    """

    # 1. 提取主题（取前100个字符）
    ppt_topic = user_input[:100]

    # 2. 检测语言
    language = self._detect_language(user_input)

    # 3. 检测场景
    scene = self._detect_scene(user_input)

    # 4. 使用默认值
    requirement = {
        "ppt_topic": ppt_topic,
        "page_num": 10,
        "scene": scene,
        "template_type": self._get_default_template(scene),
        "language": language,
        "audience": "大众",
        "industry": "",
        "core_modules": self._get_default_modules(scene),
        "need_research": False,
        "special_require": [],
        "keywords": self._extract_keywords(user_input),
        "style_preference": "",
        "color_scheme": ""
    }

    return requirement
```

**降级的优缺点**：

| 优点 | 缺点 |
|------|------|
| ✅ 可靠：不依赖 LLM | ❌ 信息提取不完整 |
| ✅ 快速：无需网络请求 | ❌ 理解能力有限 |
| ✅ 稳定：不会因 API 问题失败 | ❌ 需要维护大量规则 |

---

## 使用示例

### 基本使用

```python
from backend.agents_langchain.core.requirements.requirement_agent import (
    RequirementParserAgent,
    create_requirement_parser
)

# 创建 Agent
agent = create_requirement_parser()

# 解析输入
result = await agent.parse("生成一份关于人工智能的PPT，15页，学术风格")

# 查看结果
print(f"主题: {result['ppt_topic']}")
print(f"页数: {result['page_num']}")
print(f"场景: {result['scene']}")
print(f"语言: {result['language']}")
print(f"核心模块: {result['core_modules']}")
```

### 处理不同场景

```python
# 场景1：商业报告
result1 = await agent.parse("生成Q3财报PPT，10页，面向投资者")
# → scene: business_report
# → audience: 投资者
# → core_modules: [封面, 目录, 财务亮点, 业务回顾, 未来展望]

# 场景2：校园答辩
result2 = await agent.parse("硕士论文答辩PPT，需要展示研究成果")
# → scene: campus_defense
# → core_modules: [封面, 研究背景, 研究方法, 研究结果, 结论]
# → need_research: True

# 场景3：产品演示
result3 = await agent.parse("新功能发布PPT，要吸引客户")
# → scene: product_presentation
# → audience: 客户
# → core_modules: [封面, 产品概述, 核心功能, 使用案例, 价格方案, 联系方式]
```

---

## 常见问题

### Q1: 如何处理完全无法理解的输入？

A: 使用最保守的默认值

```python
# 输入："asdfg"（完全无意义）
# 输出：
{
    "ppt_topic": "asdfg",
    "page_num": 10,           # 默认
    "scene": "business_report", # 默认
    "language": "ZH-CN",       # 假设中文
    "core_modules": [...]     # 默认模块
}
```

### Q2: 如何提高提取的准确率？

A: 优化提示词 + Few-Shot 学习

```python
# 在提示词中添加示例
prompt = f"""
请分析以下需求：

示例1：
输入："生成财报PPT"
输出：{{"scene": "business_report", "audience": "投资者", ...}}

示例2：
输入："毕业答辩PPT"
输出：{{"scene": "campus_defense", "audience": "答辩委员会", ...}}

现在请分析：
输入：{user_input}
输出：
"""
```

### Q3: 如何支持更多场景？

A: 扩展场景关键词映射

```python
scene_keywords = {
    "business_report": [...],
    "campus_defense": [...],
    # 添加新场景
    "marketing": ["营销", "推广", "宣传", "品牌"],
    "annual_meeting": ["年会", "年度大会", "全员大会"],
    ...
}
```

---

## 相关文档

- [Core Agents 设计指南](./README.md) - 通用架构和共性
- [框架设计 Agent](./framework_agent.py.md) - 下一站：框架设计
- [状态模型](../01-models/state.py.md) - 状态定义
