# 内容生成 Agent 详解

> **核心个性**：结合研究结果生成高质量内容，控制字数和多媒体元素

---

## 目录

1. [职责与能力](#职责与能力)
2. [核心个性特征](#核心个性特征)
3. [输入输出格式](#输入输出格式)
4. [关键实现细节](#关键实现细节)
5. [内容类型适配](#内容类型适配)
6. [使用示例](#使用示例)
7. [常见问题](#常见问题)

---

## 职责与能力

### 核心职责

内容生成 Agent 是 PPT 生成流程的**核心步骤**，负责为每一页生成详细的文本内容、图表建议和配图建议。

**为什么重要？**
- ❌ 没有它：只有框架结构，没有实际内容
- ✅ 有它：为每一页填充丰富、准确、有用的内容

### 关键能力

| 能力 | 说明 | 重要性 |
|------|------|--------|
| **结合研究** | 使用研究结果生成更准确的内容 | ⭐⭐⭐⭐⭐ |
| **字数控制** | 根据页面要求控制内容长度 | ⭐⭐⭐⭐⭐ |
| **多媒体建议** | 生成图表和配图建议 | ⭐⭐⭐⭐ |
| **类型适配** | 根据页面类型调整内容风格 | ⭐⭐⭐⭐⭐ |
| **并发生成** | 支持并行生成多页内容 | ⭐⭐⭐⭐ |

---

## 核心个性特征

### 1. 结合研究结果生成内容

**设计理念**：

```
┌─────────────────────────────────────────────────────────┐
│  内容生成的信息来源                                      │
│                                                         │
│  页面定义 + 研究结果 → 高质量内容                        │
│                                                         │
│  页面定义：提供方向和框架                                │
│  - 标题：生成什么主题的内容                              │
│  - 类型：用什么风格生成                                  │
│  - 字数：生成多长的内容                                  │
│                                                         │
│  研究结果：提供事实和素材                                │
│  - 背景知识：增强内容的准确性                            │
│  - 关键数据：增加内容的可信度                            │
│  - 相关案例：丰富内容的实用性                            │
└─────────────────────────────────────────────────────────┘
```

**实现方式**：

```python
async def generate_content_for_page(
    self,
    page: Dict[str, Any],
    research_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """生成单页内容"""

    # 1. 查找相关研究
    research_content = self._get_research_for_page(
        page_no=page["page_no"],
        research_results=research_results
    )

    # 2. 构建提示词（包含研究资料）
    prompt = f"""
请为以下页面生成PPT内容：

页面信息：
- 标题：{page['title']}
- 内容描述：{page['core_content']}
- 预估字数：{page.get('estimated_word_count', 200)}字

研究资料：
{research_content}

请基于以上信息生成详细内容...
"""

    # 3. 生成内容
    content = await self._invoke_with_retry(prompt)

    return content
```

**对比：有研究 vs 无研究**

```python
# ❌ 没有研究结果
content_text = """
人工智能在医疗领域的应用
人工智能可以用于医疗诊断和治疗，比如帮助医生看病。
它还可以分析病历数据，提高诊断准确性。
"""

# ✅ 有研究结果
content_text = """
人工智能在医疗领域的应用

**医学影像诊断**
- AI可以通过深度学习算法分析X光、CT、MRI等医学影像
- 准确率可达95%以上（数据来源：Nature Medicine, 2023）
- 案例：IBM Watson Health的肿瘤诊断系统

**药物研发**
- AI可以预测分子结构，加速新药发现
- 将药物研发周期从10年缩短至3-5年
- 案例：DeepMind的AlphaFold成功预测蛋白质结构

**个性化治疗**
- 基于患者基因组数据制定个性化治疗方案
- 提高治疗有效率，减少副作用
"""
```

---

### 2. 精确的字数控制

**为什么需要字数控制？**

```
❌ 没有字数控制：
- 第3页：50字（太少，PPT显得空荡）
- 第7页：2000字（太多，PPT放不下）
- 结果：内容不平衡，用户不满意

✅ 有字数控制：
- 第3页：200字（合适）
- 第7页：250字（合适）
- 结果：内容均匀，用户体验好
```

**实现方式**：

```python
def _build_prompt_with_word_count(
    self,
    page: Dict[str, Any],
    research_content: str
) -> str:
    """构建带字数要求的提示词"""

    word_count = page.get("estimated_word_count", 200)

    return f"""
请为以下页面生成PPT内容：

页面信息：
- 标题：{page['title']}
- 内容描述：{page['core_content']}

研究资料：
{research_content}

**重要要求**：
- 内容长度：严格控制在 {word_count} 字左右（±10%）
- 如果字数过少：增加细节和例子
- 如果字数过多：删减冗余内容，保留要点

请生成内容...
"""
```

**字数范围参考**：

| 页面类型 | 建议字数 | 说明 |
|---------|---------|------|
| 封面 | 20-30 | 只需要主题、副标题、汇报人 |
| 目录 | 50-80 | 列出章节即可 |
| 内容页 | 150-300 | 主要内容，需要详细但简洁 |
| 总结页 | 100-150 | 总结要点，不要重复 |

---

### 3. 多媒体元素生成：图表和配图

**为什么需要多媒体建议？**

```
纯文字内容 → 枯燥乏味
文字 + 图表 → 数据可视化
文字 + 配图 → 增强吸引力
文字 + 图表 + 配图 → 专业的PPT
```

**图表生成逻辑**：

```python
# 如果页面需要图表
if page.get("is_need_chart", False):

    # 提示词中要求生成图表信息
    prompt += """

**图表要求**：
请根据内容设计一个合适的图表，包括：
- chart_type: 图表类型（bar/line/pie/radar等）
- chart_title: 图表标题
- data_description: 图表数据描述

选择图表类型的原则：
- 比较数据 → bar（柱状图）
- 趋势变化 → line（折线图）
- 占比关系 → pie（饼图）
- 多维评估 → radar（雷达图）
"""

    # LLM 会返回
    chart_data = {
        "chart_type": "bar",
        "chart_title": "AI应用领域市场规模",
        "data_description": "医疗：500亿，金融：800亿，教育：300亿"
    }
```

**配图生成逻辑**：

```python
# 如果页面需要配图
if page.get("is_need_image", False):

    # 提示词中要求生成配图建议
    prompt += """

**配图要求**：
请为这个页面建议一张合适的配图，包括：
- search_query: 用于搜索图片的关键词
- description: 图片内容描述

配图选择原则：
- 与页面主题高度相关
- 视觉效果好，颜色和谐
- 避免过于抽象或复杂
"""

    # LLM 会返回
    image_suggestion = {
        "search_query": "artificial intelligence medical diagnosis",
        "description": "医生使用AI系统分析医学影像的场景"
    }
```

---

### 4. 根据页面类型调整内容风格

**不同页面类型的内容策略**：

```python
def _generate_content_by_type(
    self,
    page: Dict[str, Any],
    research_content: str
) -> str:
    """根据页面类型生成内容"""

    page_type = page.get("page_type", "content")

    # 封面页
    if page_type == "cover":
        return self._generate_cover_content(page)

    # 目录页
    elif page_type == "directory":
        return self._generate_directory_content(page)

    # 总结/致谢页
    elif page_type in ["summary", "thanks"]:
        return self._generate_simple_content(page)

    # 内容页
    else:
        return self._generate_detailed_content(page, research_content)
```

**各类型的内容生成策略**：

#### 1. 封面页

```python
def _generate_cover_content(self, page: Dict) -> str:
    """生成封面内容"""
    return {
        "content_text": f"""
{page.get('ppt_topic', 'PPT主题')}
{page.get('subtitle', '')}

汇报人：{page.get('author', '未知')}
日期：{datetime.now().strftime('%Y-%m-%d')}
        """.strip(),
        "has_chart": False,
        "has_image": False,
        "key_points": []
    }
```

#### 2. 目录页

```python
def _generate_directory_content(self, page: Dict) -> str:
    """生成目录内容"""
    modules = page.get("modules", [])
    items = "\n".join([f"{i+1}. {module}" for i, module in enumerate(modules)])

    return {
        "content_text": f"""
目录

{items}
        """.strip(),
        "has_chart": False,
        "has_image": False,
        "key_points": modules
    }
```

#### 3. 内容页

```python
def _generate_detailed_content(
    self,
    page: Dict,
    research_content: str
) -> str:
    """生成详细内容"""

    prompt = f"""
请为以下页面生成详细的PPT内容：

标题：{page['title']}
描述：{page['core_content']}
字数：{page.get('estimated_word_count', 200)}字

研究资料：
{research_content}

内容要求：
- 使用要点列表格式
- 每个要点简洁有力
- 结合研究资料增加可信度
- 保持逻辑清晰
"""

    content = await self._invoke_with_retry(prompt)
    return content
```

---

### 5. Temperature = 0.5：平衡准确性和创造性

**为什么使用 0.5？**

| Temperature | 特点 | 适用场景 | 内容生成 Agent |
|------------|------|---------|---------------|
| 0.0 | 完全确定性 | 结构化数据 | ❌ 太单调 |
| 0.3 | 准确性为主 | 研究资料 | ❌ 不够生动 |
| **0.5** | **平衡准确和创造** | **内容生成** | ✅ **合适** |
| 0.7 | 创造性为主 | 创意写作 | ❌ 可能不准确 |
| 1.0 | 高度创造性 | 头脑风暴 | ❌ 不可靠 |

**实际效果**：

```python
# Temperature = 0.3（太单调）
content_text = """
人工智能在医疗领域的应用。
第一，医学影像诊断。
第二，药物研发。
第三，个性化治疗。
"""

# Temperature = 0.5（合适）
content_text = """
人工智能正在医疗领域掀起一场变革：

🔍 **医学影像诊断**
AI通过深度学习分析医学影像，准确率达95%
IBM Watson Health已成为肿瘤诊断的重要助手

💊 **药物研发突破**
将新药研发周期从10年缩短至3-5年
DeepMind的AlphaFold成功预测2亿种蛋白质结构

🎯 **个性化治疗方案**
基于基因组数据制定精准治疗方案
显著提高疗效，减少副作用
"""

# Temperature = 0.7（太花哨）
content_text = """
想象一下，当你走进医院，AI医生已经为你准备好了一切！
这就像科幻电影变成了现实！✨
人工智能不仅在医学影像中大展身手，还在药物研发中创造奇迹！
每一次治疗都是独一无二的个性化体验！🚀
"""
```

---

## 输入输出格式

### 输入

```python
page: Dict[str, Any]              # 单个页面定义
research_results: List[Dict]      # 所有研究结果
```

**示例**：

```python
page = {
    "page_no": 3,
    "title": "AI在医疗领域的应用",
    "page_type": "content",
    "core_content": "介绍AI如何应用于医疗诊断和治疗",
    "estimated_word_count": 250,
    "is_need_chart": True,
    "is_need_image": False,
    "keywords": ["AI", "医疗", "诊断"]
}

research_results = [
    {
        "page_no": 3,
        "research_content": """
        AI在医疗领域的应用主要包括：
        1. 医学影像诊断：准确率95%
        2. 药物研发：缩短周期至3-5年
        3. 个性化治疗：基于基因组数据
        """
    }
]
```

### 输出

```python
{
    "page_no": int,
    "content_text": str,            # 正文内容
    "has_chart": bool,
    "chart_data": {                 # 图表数据（如果需要）
        "chart_type": str,
        "chart_title": str,
        "data_description": str
    },
    "has_image": bool,
    "image_suggestion": {           # 配图建议（如果需要）
        "search_query": str,
        "description": str
    },
    "key_points": List[str]         # 要点列表
}
```

---

## 关键实现细节

### 1. 主流程

```python
async def generate_content_for_page(
    self,
    page: Dict[str, Any],
    research_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    为单个页面生成内容

    流程：
    1. 获取页面的研究资料
    2. 根据页面类型选择生成策略
    3. 构建 LLM 提示词
    4. 调用 LLM 生成内容
    5. 解析图表和配图信息
    6. 验证输出
    7. 失败时使用降级策略
    """

    # 1. 获取研究资料
    research_content = self._get_research_for_page(
        page_no=page["page_no"],
        research_results=research_results
    )

    # 2. 根据页面类型选择策略
    page_type = page.get("page_type", "content")

    # 特殊类型使用固定模板
    if page_type == "cover":
        return self._generate_cover_content(page)
    elif page_type == "directory":
        return self._generate_directory_content(page)
    elif page_type in ["summary", "thanks"]:
        return self._generate_simple_content(page)

    # 内容页使用 LLM 生成
    try:
        # 3. 构建提示词
        prompt = self._build_content_prompt(page, research_content)

        # 4. 调用 LLM
        response = await self._invoke_with_retry(prompt)

        # 5. 解析输出
        content_data = self._parse_content_response(response, page)

        return content_data

    except Exception as e:
        # 7. 降级处理
        self.logger.warning(f"Content generation failed for page {page['page_no']}: {e}")
        return self._fallback_content(page, research_content)
```

---

### 2. 查找研究资料

```python
def _get_research_for_page(
    self,
    page_no: int,
    research_results: List[Dict[str, Any]]
) -> str:
    """获取页面的研究资料"""

    # 遍历研究结果，找到匹配的页面
    for research in research_results:
        if research["page_no"] == page_no:
            # 找到了
            if research.get("status") == "completed":
                return research["research_content"]
            else:
                # 研究失败或跳过
                return "研究资料：无"

    # 没有找到研究结果
    return "研究资料：无"
```

---

### 3. 构建内容生成提示词

```python
def _build_content_prompt(
    self,
    page: Dict[str, Any],
    research_content: str
) -> str:
    """构建内容生成提示词"""

    # 基础信息
    prompt = f"""
你是一名专业的PPT内容创作专家。

请为以下页面生成详细的PPT内容：

**页面信息**
- 页码：{page['page_no']}
- 标题：{page['title']}
- 内容描述：{page['core_content']}
- 预估字数：{page.get('estimated_word_count', 200)}字（±10%）

**研究资料**
{research_content}

**内容要求**
1. 结构清晰：使用要点列表或分段
2. 内容准确：基于研究资料，不编造数据
3. 简洁有力：避免冗长，突出要点
4. 专业严谨：使用规范的专业术语
"""

    # 图表要求
    if page.get("is_need_chart", False):
        prompt += """

**图表要求**
请根据内容设计一个合适的图表，包括：
- chart_type: 图表类型（bar/line/pie/radar等）
- chart_title: 图表标题（简洁明了）
- data_description: 图表数据描述（具体数字和说明）
"""

    # 配图要求
    if page.get("is_need_image", False):
        prompt += """

**配图要求**
请为这个页面建议一张合适的配图，包括：
- search_query: 用于搜索图片的关键词（英文）
- description: 图片内容描述（说明图片应该包含什么）
"""

    # 输出格式
    prompt += """

**输出格式（JSON）**
{
    "page_no": 页码,
    "content_text": "正文内容",
    "has_chart": true/false,
    "chart_data": {
        "chart_type": "图表类型",
        "chart_title": "图表标题",
        "data_description": "数据描述"
    },
    "has_image": true/false,
    "image_suggestion": {
        "search_query": "搜索关键词",
        "description": "图片描述"
    },
    "key_points": ["要点1", "要点2", "要点3"]
}
"""

    return prompt
```

---

## 降级策略

### 什么时候触发降级？

```
LLM 生成失败 ↓
│
├─ 网络错误
├─ API 限流
├─ 超时
└─ JSON 解析失败

触发降级策略 → 使用简单模板生成内容
```

### 降级实现

```python
def _fallback_content(
    self,
    page: Dict[str, Any],
    research_content: str
) -> Dict[str, Any]:
    """降级内容生成"""

    page_type = page.get("page_type", "content")

    # 根据页面类型返回不同的降级内容
    if page_type == "cover":
        content_text = f"{page.get('ppt_topic', 'PPT主题')}\n\n汇报人：{page.get('author', '未知')}"

    elif page_type == "directory":
        modules = page.get("modules", [])
        content_text = "目录\n" + "\n".join([f"{i+1}. {m}" for i, m in enumerate(modules)])

    elif page_type in ["summary", "thanks"]:
        content_text = "感谢聆听"

    else:
        # 内容页使用 core_content
        content_text = page.get("core_content", "内容生成失败")

    return {
        "page_no": page["page_no"],
        "content_text": content_text,
        "has_chart": False,
        "has_image": False,
        "key_points": []
    }
```

---

## 内容类型适配

### 封面页

**特点**：信息少，主要是展示

```python
# 输入
{
    "page_no": 1,
    "page_type": "cover",
    "ppt_topic": "人工智能在医疗领域的应用",
    "subtitle": "技术前沿与临床实践",
    "author": "张三",
    "date": "2024-01-15"
}

# 输出
{
    "content_text": """
    人工智能在医疗领域的应用
    技术前沿与临床实践

    汇报人：张三
    2024-01-15
    """,
    "has_chart": False,
    "has_image": False,
    "key_points": []
}
```

### 目录页

**特点**：列出章节，信息结构化

```python
# 输入
{
    "page_no": 2,
    "page_type": "directory",
    "modules": ["AI技术概述", "医疗应用场景", "案例分析", "未来展望"]
}

# 输出
{
    "content_text": """
    目录

    1. AI技术概述
    2. 医疗应用场景
    3. 案例分析
    4. 未来展望
    """,
    "has_chart": False,
    "has_image": False,
    "key_points": ["AI技术概述", "医疗应用场景", "案例分析", "未来展望"]
}
```

### 内容页

**特点**：详细内容，可能包含图表

```python
# 输入
{
    "page_no": 3,
    "page_type": "content",
    "title": "AI在医疗诊断中的应用",
    "core_content": "介绍AI如何辅助医学影像诊断",
    "estimated_word_count": 250,
    "is_need_chart": True
}

# 输出
{
    "content_text": """
    AI正在医学影像诊断领域发挥重要作用：

    🎯 **影像识别与分析**
    - X光片：准确识别肺炎、骨折等病变
    - CT扫描：快速定位肿瘤位置
    - MRI：分析软组织病变

    📊 **性能表现**
    - 准确率：95%以上
    - 速度：比人工快10倍
    - 成本：降低60%

    💡 **实际应用**
    - IBM Watson Health：肿瘤诊断
    - Google DeepMind：眼底疾病筛查
    """,
    "has_chart": True,
    "chart_data": {
        "chart_type": "bar",
        "chart_title": "AI诊断准确率对比",
        "data_description": "AI诊断：95%，人工诊断：85%，AI辅助：98%"
    },
    "has_image": False,
    "key_points": ["影像识别与分析", "性能表现", "实际应用"]
}
```

---

## 使用示例

### 基本使用

```python
from backend.agents_langchain.core.generation.content_agent import (
    ContentMaterialAgent,
    create_content_agent
)

# 创建 Agent
agent = create_content_agent()

# 准备数据
page = {
    "page_no": 3,
    "title": "AI在医疗诊断中的应用",
    "page_type": "content",
    "core_content": "介绍AI如何辅助医学影像诊断",
    "estimated_word_count": 250,
    "is_need_chart": True,
    "is_need_image": False
}

research_results = [
    {
        "page_no": 3,
        "research_content": """
        AI在医学影像诊断中的应用：
        1. X光片识别：准确率95%
        2. CT扫描分析：速度提升10倍
        3. MRI病灶检测：成本降低60%
        """
    }
]

# 生成内容
result = await agent.generate_content_for_page(page, research_results)

# 查看结果
print(f"内容: {result['content_text']}")
print(f"有图表: {result['has_chart']}")
if result['has_chart']:
    print(f"图表类型: {result['chart_data']['chart_type']}")
    print(f"图表标题: {result['chart_data']['chart_title']}")
```

---

## 常见问题

### Q1: 如何确保内容不超过字数限制？

A: 在提示词中明确要求，并在验证时检查。

```python
def validate_output(self, output: Dict) -> tuple[bool, List[str]]:
    """验证输出"""
    errors = []

    # 检查字数
    content_text = output.get("content_text", "")
    word_count = len(content_text)

    if word_count > self.max_word_count * 1.2:  # 允许超过20%
        errors.append(f"字数超出限制：{word_count} > {self.max_word_count}")

    return len(errors) == 0, errors
```

### Q2: 研究结果为空时如何生成内容？

A: 使用默认的研究内容提示。

```python
def _get_research_for_page(self, page_no, research_results):
    research = self._find_research(page_no, research_results)

    if not research or research.get("status") != "completed":
        # 返回默认提示
        return "研究资料：无\n\n请基于你的知识库生成内容。"

    return research["research_content"]
```

### Q3: 如何生成更生动的图表描述？

A: 在提示词中添加图表类型的选择逻辑。

```python
prompt += """
选择图表类型的原则：
- 比较不同类别的数据 → 使用 bar（柱状图）
- 展示时间趋势变化 → 使用 line（折线图）
- 显示占比关系 → 使用 pie（饼图）
- 多维度对比评估 → 使用 radar（雷达图）

请根据内容特点选择最合适的图表类型。
"""
```

### Q4: 如何处理特殊页面类型（如过渡页）？

A: 扩展页面类型判断。

```python
def _generate_content_by_type(self, page, research_content):
    page_type = page.get("page_type", "content")

    # 添加新类型
    if page_type == "transition":
        return self._generate_transition_content(page)
    elif page_type == "quote":
        return self._generate_quote_content(page)
    # ... 其他类型
```

---

## 相关文档

- [Core Agents 设计指南](./README.md) - 通用架构和共性
- [研究 Agent](./research_agent.py.md) - 如何生成研究结果
- [渲染 Agent](./renderer_agent.py.md) - 如何使用生成的内容
- [PagePipeline](../02-coordinator/page_pipeline.py.md) - 如何并发调用内容生成
