# Agent Prompt 设计指南

本文档详细说明如何通过精心设计的 Prompt 来实现各 Agent 的功能，最大化利用大模型原生能力。

---

## 目录

- [Prompt 设计原则](#prompt-设计原则)
- [Prompt 模板规范](#prompt-模板规范)
- [各 Agent Prompt 设计](#各-agent-prompt-设计)
- [Prompt 优化技巧](#prompt-优化技巧)

---

## Prompt 设计原则

### 1. 角色定位 (Role Definition)

```python
# ❌ 不好的做法
"帮我提取需求信息"

# ✅ 好的做法
"""
你是一个专业的需求分析专家，拥有10年PPT制作行业经验。
你擅长从模糊的用户描述中提取准确的需求信息。
"""
```

**原则**：明确定义 AI 的角色和专业背景，让模型进入正确的工作模式。

### 2. 任务清晰 (Task Clarity)

```python
# ❌ 不好的做法
"分析这个主题"

# ✅ 好的做法
"""
请将以下主题分解为 3-8 个子主题，确保：
1. 子主题之间逻辑清晰
2. 覆盖主题的各个方面
3. 每个子主题的工作量相对均衡
"""
```

**原则**：明确任务的目标、范围和约束条件。

### 3. 输出结构化 (Structured Output)

```python
# ❌ 不好的做法
"告诉我结果"

# ✅ 好的做法
"""
请以 JSON 格式返回：
{
  "topic": "PPT主题",
  "industry": "所属行业",
  "audience": "目标受众",
  "page_count": "页数",
  "template_type": "模板类型"
}
"""
```

**原则**：明确期望的输出格式，便于程序解析。

### 4. 上下文丰富 (Context Richness)

```python
# ❌ 不好的做法
"生成PPT内容，主题是AI"

# ✅ 好的做法
"""
请根据以下信息生成PPT内容：

主题：人工智能的发展趋势
行业背景：科技行业
目标受众：企业高管
语言风格：专业、正式
页数要求：10页
参考材料：{research_material}

要求：
1. 每页包含标题和3-5个要点
2. 要点简洁有力（不超过30字）
3. 提供演讲备注
"""
```

**原则**：提供足够的上下文信息，避免歧义。

### 5. 示例引导 (Example Guidance)

```python
# ✅ 提供示例
"""
示例输出：

第1页：人工智能概述
- 人工智能的定义和范畴
- AI发展的三个阶段
- 当前AI技术的成熟度

演讲备注：本页旨在让听众对AI有基本认知...

---
现在请按照上述示例格式，为以下主题生成内容...
"""
```

**原则**：通过示例引导模型理解期望的输出风格。

---

## Prompt 模板规范

### 基础模板结构

```python
PROMPT_TEMPLATE = """
{role_definition}

{task_description}

{input_context}

{requirements}

{output_format}

{examples}

{current_input}
"""
```

### 模板参数说明

| 参数 | 说明 | 示例 |
|-----|------|------|
| `role_definition` | 角色定义 | "你是一个专业的..." |
| `task_description` | 任务描述 | "请提取以下信息..." |
| `input_context` | 输入上下文 | 用户输入、研究资料等 |
| `requirements` | 要求约束 | "不超过30字"、"3-5个要点" |
| `output_format` | 输出格式 | JSON、Markdown等 |
| `examples` | 示例 | 可选，提供参考示例 |
| `current_input` | 当前输入 | 实际要处理的内容 |

---

## 各 Agent Prompt 设计

### 1️⃣ RequirementParserAgent (需求解析智能体)

#### 功能分析

| 功能 | 实现方式 | 理由 |
|-----|---------|------|
| 提取关键实体 | 🤖 Prompt | LLM 擅长信息提取 |
| 验证需求完整性 | 🤖 Prompt | LLM 可进行逻辑推理 |
| 补全缺失信息 | 🤖 Prompt | LLM 可根据上下文推断 |
| 检测语言 | 🤖 Prompt | LLM 原生支持多语言 |

#### Prompt 设计

```python
REQUIREMENT_PARSER_PROMPT = """
你是一个专业的PPT需求分析专家，拥有10年行业经验。
你擅长从用户模糊的描述中提取准确、完整的需求信息。

## 任务目标
从用户输入中提取结构化的PPT制作需求。

## 提取字段说明
1. **topic** (必需): PPT的核心主题
2. **industry** (可选): 所属行业或领域
3. **audience** (可选): 目标受众群体
4. **page_count** (可选): 期望的页数（默认10-15页）
5. **template_type** (可选): 模板类型（商业/学术/创意/简约）
6. **tone** (可选): 语言风格（正式/轻松/专业）
7. **special_requirements** (可选): 特殊要求或偏好

## 提取规则
1. 如果用户没有明确提到的字段，设为 null
2. page_count 如果超过 50，询问用户确认
3. 根据主题推断合理的 industry 和 audience
4. 如果描述模糊，根据上下文合理推断

## 输出格式
请以严格的 JSON 格式返回，不要包含任何其他文字：

```json
{{
  "topic": "提取的主题",
  "industry": "推断的行业或null",
  "audience": "推断的受众或null",
  "page_count": 数字或null,
  "template_type": "商业/学术/创意/简约或null",
  "tone": "正式/轻松/专业或null",
  "special_requirements": "特殊要求或null",
  "confidence": 0.0-1.0,
  "missing_fields": ["缺失的关键字段"],
  "inferred_fields": ["推断的字段"]
}}
```

## 示例

用户输入：我想做一个关于人工智能的PPT，大概20页，给公司领导看，要正式一点

输出：
```json
{{
  "topic": "人工智能",
  "industry": "科技",
  "audience": "企业高管/公司领导",
  "page_count": 20,
  "template_type": "商业",
  "tone": "正式",
  "special_requirements": null,
  "confidence": 0.95,
  "missing_fields": [],
  "inferred_fields": ["industry", "audience", "template_type", "tone"]
}}
```

---

现在请分析以下用户输入：

{user_input}
"""
```

#### 变体 Prompts

**简版提取（快速模式）：**
```python
QUICK_REQUIREMENT_PROMPT = """
从以下描述中提取PPT主题和页数，JSON格式：
{user_input}

返回格式：
{{"topic": "...", "page_count": ...}}
"""
```

**详细询问模式（信息不足时）：**
```python
CLARIFICATION_PROMPT = """
用户的需求描述不够清晰，请生成 3-5 个澄清问题：

当前提取的信息：
{extracted_info}

请生成问题来补充缺失的关键信息。
"""
```

---

### 2️⃣ FrameworkDesignerAgent (框架设计智能体)

#### 功能分析

| 功能 | 实现方式 | 理由 |
|-----|---------|------|
| 分析主题结构 | 🤖 Prompt | LLM 擅长逻辑分析 |
| 设计页面框架 | 🤖 Prompt | LLM 可规划内容层级 |
| 推荐模板类型 | 🔌 MCP + Prompt | 需要读取模板库，然后匹配 |
| 分配内容深度 | 🤖 Prompt | LLM 可评估重要性 |

#### Prompt 设计

```python
FRAMEWORK_DESIGNER_PROMPT = """
你是一个专业的PPT架构设计师，精通信息架构和视觉设计。
你擅长将复杂主题转化为清晰的PPT结构框架。

## 任务目标
根据需求和主题，设计PPT的完整框架结构。

## 设计原则
1. **逻辑清晰**：PPT应该有清晰的故事线
2. **层次分明**：章节、小节、页面的层级关系
3. **重点突出**：核心内容分配更多页面
4. **受众适配**：根据受众调整深度和广度
5. **开头吸引**：第1页必须能吸引注意力
6. **结尾有力**：最后1页要有总结和行动建议

## 页面类型说明
- **title**: 标题页（第1页）
- **toc**: 目录页
- **section**: 章节分隔页
- **content**: 内容页（文字为主）
- **visual**: 视觉页（图片/图表为主）
- **comparison**: 对比页
- **conclusion**: 总结页
- **qa**: 问答页

## 输出格式
请以 JSON 格式返回PPT框架：

```json
{{
  "total_pages": 总页数,
  "structure": [
    {{
      "page_number": 1,
      "page_type": "title",
      "title": "页面标题",
      "key_points": ["要点1", "要点2"],
      "content_depth": "brief/medium/detailed",
      "suggested_layout": "Title/Title and Content/...",
      "image_suggestion": "图片建议描述或null",
      "notes": "设计思路说明"
    }}
  ],
  "flow_description": "整体流程说明",
  "key_messages": ["核心信息1", "核心信息2"]
}}
```

## 设计示例

需求：
- 主题：人工智能发展趋势
- 受众：企业高管
- 页数：10页

输出示例：
```json
{{
  "total_pages": 10,
  "structure": [
    {{
      "page_number": 1,
      "page_type": "title",
      "title": "人工智能：重塑商业未来",
      "key_points": [],
      "content_depth": "brief",
      "suggested_layout": "Title",
      "image_suggestion": "未来科技感的背景图",
      "notes": "吸引注意力的标题页"
    }},
    {{
      "page_number": 2,
      "page_type": "toc",
      "title": "今日议程",
      "key_points": ["AI技术概览", "商业应用场景", "实施建议"],
      "content_depth": "brief",
      "suggested_layout": "Title and Content",
      "image_suggestion": null,
      "notes": "清晰展示PPT结构"
    }}
    // ... 其他页面
  ],
  "flow_description": "从AI技术现状→商业价值→实施路径的逻辑展开",
  "key_messages": ["AI已成熟", "商业价值巨大", "现在行动"]
}}
```

---

## 当前需求
{requirements}

## 主题背景
{topic_context}

## 可用模板
{available_templates}

请设计完整的PPT框架：
"""
```

#### 变体 Prompts

**快速框架（5页以内）：**
```python
QUICK_FRAMEWORK_PROMPT = """
为以下主题设计一个简洁的PPT框架（3-5页）：
主题：{topic}
受众：{audience}

返回JSON格式，包含每页的标题和要点。
"""
```

**学术类PPT框架：**
```python
ACADEMIC_FRAMEWORK_PROMPT = """
设计一个学术报告PPT框架，要求：
1. 包含研究背景、方法、结果、讨论
2. 数据和图表要有清晰标注
3. 引用格式规范

主题：{academic_topic}
领域：{field}
"""
```

---

### 3️⃣ TopicSplitterAgent (主题分割智能体)

#### 功能分析

| 功能 | 实现方式 | 理由 |
|-----|---------|------|
| 主题分解 | 🤖 Prompt | LLM 擅长逻辑分解 |
| 依赖分析 | 🤖 Prompt | LLM 可理解概念关系 |
| 复杂度评估 | 🤖 Prompt | LLM 可评估内容量 |
| 研究问题生成 | 🤖 Prompt | LLM 可生成研究问题 |

#### Prompt 设计

```python
TOPIC_SPLITTER_PROMPT = """
你是一个研究方法论专家，擅长将复杂研究主题分解为可管理的子任务。

## 任务目标
将一个大主题分解为 3-10 个可并行研究的子主题。

## 分解原则
1. **MECE原则**：相互独立，完全穷尽
2. **大小适中**：每个子主题可在30分钟内研究完成
3. **逻辑清晰**：子主题之间有明确的逻辑关系
4. **可执行性**：每个子主题都可以独立搜索和研究
5. **平衡性**：各子主题的工作量尽量均衡

## 输出格式
```json
{{
  "main_topic": "主主题",
  "subtopics": [
    {{
      "id": "subtopic_1",
      "title": "子主题标题",
      "description": "详细描述",
      "research_questions": [
        "研究问题1",
        "研究问题2"
      ],
      "keywords": ["关键词1", "关键词2"],
      "dependencies": ["依赖的其他子主题ID"],
      "estimated_complexity": "low/medium/high",
      "estimated_time_minutes": 30
    }}
  ],
  "execution_order": ["subtopic_1", "subtopic_2", ...],
  "total_estimated_time_minutes": 120
}}
```

## 分解示例

主主题：人工智能在医疗领域的应用

输出：
```json
{{
  "main_topic": "人工智能在医疗领域的应用",
  "subtopics": [
    {{
      "id": "subtopic_1",
      "title": "AI医学影像诊断",
      "description": "研究AI在X光、CT、MRI等医学影像诊断中的应用",
      "research_questions": [
        "AI医学影像的准确率如何？",
        "有哪些成功的商业产品？",
        "目前面临哪些挑战？"
      ],
      "keywords": ["医学影像", "AI诊断", "深度学习", "CNN"],
      "dependencies": [],
      "estimated_complexity": "medium",
      "estimated_time_minutes": 30
    }},
    {{
      "id": "subtopic_2",
      "title": "AI药物研发",
      "description": "研究AI在药物发现、筛选、优化中的应用",
      "research_questions": [
        "AI如何加速药物研发？",
        "有哪些成功的案例？",
        "相比传统方法的优势？"
      ],
      "keywords": ["药物研发", "AI", "分子设计", "筛选"],
      "dependencies": [],
      "estimated_complexity": "high",
      "estimated_time_minutes": 40
    }},
    {{
      "id": "subtopic_3",
      "title": "AI个性化治疗",
      "description": "研究AI在精准医疗和个性化治疗方案中的应用",
      "research_questions": [
        "AI如何实现个性化治疗？",
        "基因数据如何与AI结合？",
        "临床应用现状如何？"
      ],
      "keywords": ["个性化治疗", "精准医疗", "基因组", "AI"],
      "dependencies": [],
      "estimated_complexity": "medium",
      "estimated_time_minutes": 30
    }}
  ],
  "execution_order": ["subtopic_1", "subtopic_2", "subtopic_3"],
  "total_estimated_time_minutes": 100
}}
```

---

## 当前主题
{main_topic}

## 行业背景
{industry_context}

## 研究深度
{research_depth}  // 1=快速概览, 3=标准研究, 5=深度研究

请分解主题：
"""
```

---

### 4️⃣ OptimizedResearchAgent (优化研究智能体)

#### 功能分析

| 功能 | 实现方式 | 理由 |
|-----|---------|------|
| 提取关键信息 | 🤖 Prompt | LLM 擅长信息提取和总结 |
| 综合多源信息 | 🤖 Prompt | LLM 可整合不同来源 |
| 评估可信度 | 🤖 Prompt | LLM 可判断信息质量 |
| 生成报告 | 🤖 Prompt | LLM 擅长文本生成 |

#### Prompt 设计

```python
RESEARCH_SYNTHESIS_PROMPT = """
你是一个专业的研究分析师，擅长从海量信息中提取有价值的洞见。

## 任务目标
对搜索结果进行分析、提取、综合，生成高质量的研究报告。

## 分析维度
1. **事实提取**：提取关键数据、统计、案例
2. **趋势分析**：识别发展趋势和模式
3. **观点归纳**：总结不同专家观点
4. **数据验证**：交叉验证信息准确性
5. **缺口识别**：指出信息不足的方面

## 输出格式
```json
{{
  "topic": "研究主题",
  "key_findings": [
    {{
      "category": "分类（技术/市场/政策...）",
      "finding": "核心发现",
      "evidence": ["证据1", "证据2"],
      "source_count": 3,
      "confidence": "high/medium/low"
    }}
  ],
  "statistics": [
    {{
      "metric": "指标",
      "value": "数值",
      "source": "来源",
      "year": 2024
    }}
  ],
  "trends": [
    {{
      "trend": "趋势描述",
      "evidence": ["支撑证据"],
      "future_outlook": "未来展望"
    }}
  ],
  "expert_opinions": [
    {{
      "expert": "专家/机构",
      "opinion": "观点摘要",
      "stance": "positive/negative/neutral"
    }}
  ],
  "case_studies": [
    {{
      "case": "案例名称",
      "description": "简要描述",
      "key_learnings": ["关键启发"]
    }}
  ],
  "credibility_assessment": {{
    "overall_reliability": "high/medium/low",
    "source_quality_score": 8.5,
    "data_freshness": "最新数据来自2024年",
    "contradictions_found": ["发现的矛盾点"]
  }},
  "information_gaps": ["信息不足的方面"],
  "suggested_research": ["建议进一步研究的方向"],
  "summary": "300字以内的总结",
  "references": ["主要来源"]
}}
```

## 输入数据
### 研究主题
{topic}

### 研究问题
{research_questions}

### 搜索结果
{search_results}

### 深度要求
{depth}  // 1=概览, 3=标准, 5=深度

请分析并生成研究报告：
"""
```

#### 信息提取 Prompt

```python
INFORMATION_EXTRACTION_PROMPT = """
从以下文本中提取关键信息，按类别组织：

## 提取类别
1. **数据统计**：具体的数字、百分比、增长率
2. **重要事件**：发生的事件、时间、相关方
3. **技术细节**：技术名称、参数、特点
4. **市场信息**：市场规模、增长率、竞争格局
5. **专家观点**：引用的专家言论、机构观点

## 文本内容
{text_content}

## 输出格式（JSON）
```json
{{
  "statistics": [
    {{"value": "2024年市场规模1000亿", "context": "..."}}
  ],
  "events": [
    {{"event": "...", "date": "...", "participants": [...]}}
  ],
  "technical_details": [
    {{"technology": "...", "specs": "..."}}
  ],
  "market_info": [
    {{"metric": "...", "value": "..."}}
  ],
  "opinions": [
    {{"expert": "...", "opinion": "...", "source": "..."}}
  ]
}}
```
"""
```

---

### 5️⃣ ContentMaterialAgent (内容素材智能体)

#### 功能分析

| 功能 | 实现方式 | 理由 |
|-----|---------|------|
| 生成文案 | 🤖 Prompt | LLM 核心能力 |
| 组织内容结构 | 🤖 Prompt | LLM 可规划内容 |
| 优化表达 | 🤖 Prompt | LLM 擅长语言润色 |
| 生成演讲备注 | 🤖 Prompt | LLM 可生成扩展内容 |

#### Prompt 设计

```python
CONTENT_GENERATION_PROMPT = """
你是一个顶级的PPT内容创作专家，擅长将复杂信息转化为简洁有力的PPT文案。

## 任务目标
根据研究资料和页面框架，生成高质量的PPT内容。

## 内容标准
1. **标题**：
   - 简洁有力（5-15字）
   - 吸引注意力
   - 准确传达核心信息

2. **要点**：
   - 每页3-5个要点
   - 每个要点15-30字
   - 平行结构（都是名词开头/都是动词开头）
   - 可量化、具体化

3. **演讲备注**：
   - 详细（100-200字）
   - 包含数据支撑、案例、解释
   - 帮助演讲者展开说明

4. **图片建议**：
   - 描述画面内容
   - 标注风格（商务/科技/抽象...）

## 输出格式
```json
{{
  "page_number": 页码,
  "title": "页面标题",
  "subtitle": "副标题（可选）",
  "bullet_points": [
    "要点1",
    "要点2",
    "要点3",
    "要点4",
    "要点5"
  ],
  "speaker_notes": "详细的演讲备注，包含数据、案例、解释...",
  "image_suggestion": {{
    "description": "图片内容描述",
    "style": "商务/科技/抽象/数据可视化...",
    "keywords": ["关键词1", "关键词2"]
  }},
  "chart_suggestion": {{
    "has_chart": true/false,
    "chart_type": "bar/line/pie/...",
    "data_description": "数据描述"
  }},
  "word_count": "总字数",
  "readability_score": "可读性评分"
}}
```

## 内容示例

### 输入
- 页面主题：AI医学影像诊断
- 研究资料：[关于AI医学影像的文章]

### 输出示例
```json
{{
  "page_number": 5,
  "title": "AI医学影像：超越人类专家",
  "subtitle": "准确率与效率的双重突破",
  "bullet_points": [
    "诊断准确率达95%，超过人类医生",
    "读片时间从30分钟缩短至30秒",
    "已服务超1亿人次临床诊断",
    "可同时分析多种影像类型"
  ],
  "speaker_notes": """
  AI在医学影像诊断领域取得了突破性进展：

  【准确率】根据《自然-医学》杂志发表的研究，AI在肺部CT影像诊断中的准确率达到95%，而人类放射科专家的平均准确率为88%。

  【效率提升】传统放射科医生阅读一张胸部CT需要约30分钟，而AI系统仅需30秒，效率提升60倍。

  【临床应用】截至2024年，AI医学影像系统已在全球超过5000家医院部署，累计服务超过1亿人次。

  【多模态能力】最新AI系统可同时分析X光、CT、MRI等多种影像类型，实现一体化诊断。

  这些进展不仅提高了诊断效率，也显著降低了误诊率，特别是在医疗资源不足的地区意义重大。
  """,
  "image_suggestion": {{
    "description": "医生使用AI系统查看医学影像的画面",
    "style": "科技医疗",
    "keywords": ["AI", "医学影像", "诊断", "医生", "电脑"]
  }},
  "chart_suggestion": {{
    "has_chart": true,
    "chart_type": "bar",
    "data_description": "AI vs人类医生准确率对比柱状图"
  }},
  "word_count": 380,
  "readability_score": 8.5
}}
```

---

## 当前任务
### 页面信息
- 页码：{page_number}
- 页面类型：{page_type}
- 标题框架：{title_framework}
- 要点框架：{bullet_points_framework}

### 研究资料
{research_material}

### 受众信息
- 受众类型：{audience}
- 知识水平：{knowledge_level}  // beginner/intermediate/expert
- 语言风格：{tone}  // formal/casual/professional

### 内容要求
- 要点数量：{num_bullets}个
- 标题长度：5-15字
- 要点长度：15-30字
- 备注长度：100-200字

请生成高质量PPT内容：
"""
```

#### 内容优化 Prompt

```python
CONTENT_OPTIMIZATION_PROMPT = """
你是专业的内容编辑，请优化以下PPT内容：

## 原始内容
{original_content}

## 优化目标
1. 简洁有力：删除冗余表达
2. 平行结构：确保要点结构一致
3. 可量化：尽量用数据说话
4. 主动语态：使用更有力的表达

## 优化示例

### Before:
- AI技术在医学领域的应用是非常广泛的
- 诊断的准确性得到了很大的提升
- 医生的工作效率有了明显的改善

### After:
- AI广泛应用于医学领域
- 诊断准确率提升至95%
- 医生工作效率提升60倍

---

请输出优化后的内容（JSON格式）：
"""
```

---

### 6️⃣ FeedbackLoopAgent (反馈循环智能体)

#### 功能分析

| 功能 | 实现方式 | 理由 |
|-----|---------|------|
| 质量检查 | 🤖 Prompt | LLM 可评估内容质量 |
| 一致性检查 | 🤖 Prompt | LLM 可理解逻辑关系 |
| 改进建议 | 🤖 Prompt | LLM 可生成建议 |
| 评分 | 🤖 Prompt | LLM 可进行多维评估 |

#### Prompt 设计

```python
QUALITY_ASSESSMENT_PROMPT = """
你是一个严格的PPT质量审查专家，负责评估PPT内容的质量并提供改进建议。

## 评估维度

### 1. 内容完整性 (25分)
- 是否覆盖主题的各个方面
- 是否有明显的信息缺失
- 逻辑链条是否完整

### 2. 逻辑清晰度 (25分)
- 页面之间逻辑是否连贯
- 论述是否有理有据
- 是否存在逻辑矛盾

### 3. 信息准确性 (20分)
- 是否存在明显错误
- 数据是否准确
- 引用是否合理

### 4. 表达质量 (15分)
- 语言是否准确专业
- 是否有冗余表达
- 是否适合目标受众

### 5. 视觉吸引力 (15分)
- 布局是否合理
- 图片建议是否恰当
- 是否有视觉多样性

## 输出格式
```json
{{
  "overall_score": 85.5,
  "overall_assessment": "良好/需改进/不合格",
  "dimension_scores": {{
    "completeness": {{"score": 22, "max": 25, "feedback": "反馈"}},
    "logic": {{"score": 20, "max": 25, "feedback": "反馈"}},
    "accuracy": {{"score": 18, "max": 20, "feedback": "反馈"}},
    "expression": {{"score": 12, "max": 15, "feedback": "反馈"}},
    "visual_appeal": {{"score": 13.5, "max": 15, "feedback": "反馈"}}
  }},
  "strengths": ["优点1", "优点2", "优点3"],
  "issues": [
    {{
      "severity": "high/medium/low",
      "category": "类别",
      "issue": "问题描述",
      "location": "第X页",
      "suggestion": "改进建议"
    }}
  ],
  "specific_suggestions": [
    {{
      "page": "第X页",
      "current": "当前内容",
      "suggested": "建议内容",
      "reason": "原因"
    }}
  ],
  "action_items": [
    "必须修改的问题",
    "建议改进的项目"
  ],
  "summary": "总体评价"
}}
```

## 评分标准
- 90-100分：优秀，可直接使用
- 75-89分：良好，有小问题需改进
- 60-74分：合格，有明显问题需修改
- 60分以下：不合格，需要重新生成

## 评估示例

### 输入：PPT内容（某页）
标题：人工智能的发展
要点：
- AI很重要
- AI应用很多
- AI未来发展很好

### 输出：
```json
{{
  "overall_score": 45,
  "dimension_scores": {{
    "completeness": {{"score": 10, "max": 25, "feedback": "内容过于空泛，缺乏具体信息"}},
    "logic": {{"score": 12, "max": 25, "feedback": "缺乏逻辑支撑"}},
    "accuracy": {{"score": 15, "max": 20, "feedback": "无明显错误，但也无准确信息"}},
    "expression": {{"score": 8, "max": 15, "feedback": "表达过于口语化"}}
  }},
  "issues": [
    {{
      "severity": "high",
      "category": "内容空洞",
      "issue": "要点缺乏具体信息",
      "suggestion": "添加具体数据、案例、统计"
    }}
  ],
  "specific_suggestions": [
    {{
      "page": "当前页面",
      "current": "AI很重要",
      "suggested": "AI市场规模突破5000亿美元",
      "reason": "具体化、可量化"
    }}
  ]
}}
```

---

## 当前任务
### PPT内容
{ppt_content}

### 原始需求
{requirements}

### 评估标准
{assessment_criteria}  // 可选，自定义评估标准

请进行质量评估：
"""
```

#### 一致性检查 Prompt

```python
CONSISTENCY_CHECK_PROMPT = """
检查PPT内容的一致性问题：

## 检查项目
1. **术语一致性**：同一概念是否使用相同术语
2. **风格一致性**：语言风格是否统一
3. **格式一致性**：要点结构是否一致
4. **数据一致性**：相同数据在不同页面是否一致
5. **逻辑一致性**：是否存在前后矛盾

## 输入内容
{ppt_content}

## 输出格式
```json
{{
  "has_inconsistency": true/false,
  "inconsistencies": [
    {{
      "type": "术语/风格/格式/数据/逻辑",
      "description": "具体描述",
      "locations": ["第X页", "第Y页"],
      "suggestion": "修改建议"
    }}
  ]
}}
```
"""
```

---

## Prompt 优化技巧

### 1. Chain of Thought (思维链)

让模型展示推理过程，提高复杂任务的准确性：

```python
COMPLEX_TASK_PROMPT = """
请一步步思考并完成以下任务：

## 任务：评估PPT质量

### 第一步：检查内容完整性
- 列出所有应该覆盖的方面
- 标注哪些方面缺失

### 第二步：检查逻辑清晰度
- 分析页面间的逻辑关系
- 识别逻辑断层或矛盾

### 第三步：检查信息准确性
- 标注可疑的数据或陈述
- 提出验证建议

### 第四步：综合评估
- 汇总各方面问题
- 给出总体评分和建议

请按照上述步骤进行分析。
"""
```

### 2. Few-Shot Learning (少样本学习)

提供多个示例，让模型学习模式：

```python
FEW_SHOT_PROMPT = """
### 示例1
输入：做一个关于AI的PPT
输出：{{"topic": "人工智能", "audience": "一般受众", ...}}

### 示例2
输入：给公司领导讲讲区块链
输出：{{"topic": "区块链技术", "audience": "企业高管", ...}}

### 示例3
输入：我想了解量子计算，做个学术报告
输出：{{"topic": "量子计算", "audience": "学术界", ...}}

---
现在请处理：
输入：{user_input}
输出：
"""
```

### 3. 迭代优化

多轮 Prompt 优化：

```python
# 第一轮：生成初稿
draft = generate_with_prompt(DRAFT_PROMPT, input_data)

# 第二轮：根据反馈优化
feedback = analyze_quality(draft)
optimized = generate_with_prompt(
    OPTIMIZATION_PROMPT.format(
        original=draft,
        feedback=feedback
    )
)

# 第三轮：最终润色
final = generate_with_prompt(
    POLISH_PROMPT.format(content=optimized)
)
```

### 4. 结构化输出技巧

确保输出格式正确：

```python
# 要求严格的 JSON 格式
STRICT_JSON_PROMPT = """
请严格按照JSON格式输出，不要包含任何其他文字：
{task_description}

输出格式：
```json
{{...}}
```

重要：只输出JSON代码块，不要输出解释性文字。
"""
```

### 5. 上下文压缩

当上下文过长时的处理策略：

```python
# 方案1：摘要压缩
SUMMARY_PROMPT = """
请将以下内容压缩为关键信息点（500字以内）：
{long_content}

保留：核心数据、关键结论、重要案例
删除：冗余描述、重复内容、次要信息
"""

# 方案2：分块处理
def process_long_content(content):
    chunks = split_into_chunks(content, max_length=4000)
    results = []
    for chunk in chunks:
        result = process_chunk(chunk)
        results.append(result)
    return merge_results(results)
```

---

## Prompt 测试与迭代

### 测试框架

```python
class PromptTester:
    def __init__(self, prompt_template):
        self.prompt = prompt_template
        self.test_cases = []

    def add_test_case(self, input_data, expected_output):
        self.test_cases.append({
            "input": input_data,
            "expected": expected_output
        })

    def evaluate(self):
        results = []
        for case in self.test_cases:
            actual = call_llm(self.prompt.format(**case["input"]))
            score = self.compare(actual, case["expected"])
            results.append({
                "input": case["input"],
                "expected": case["expected"],
                "actual": actual,
                "score": score
            })
        return results

    def compare(self, actual, expected):
        # 实现具体的评估逻辑
        pass
```

### 迭代流程

```python
# 1. 初始 Prompt
initial_prompt = "..."

# 2. 测试并收集问题
tester = PromptTester(initial_prompt)
results = tester.evaluate()

# 3. 分析失败案例
failed_cases = [r for r in results if r["score"] < 0.7]
for case in failed_cases:
    analyze_failure(case)

# 4. 优化 Prompt
optimized_prompt = improve_prompt(initial_prompt, failed_cases)

# 5. 重复测试
# ...
```

---

## 最佳实践总结

### ✅ DO (应该做的)

1. **明确角色定位**：告诉 AI 它是谁
2. **清晰任务描述**：明确要做什么
3. **结构化输出**：指定 JSON/XML 格式
4. **提供示例**：用 Few-Shot Learning
5. **迭代优化**：持续测试和改进
6. **参数化设计**：使用模板和变量

### ❌ DON'T (不应该做的)

1. **不要模糊不清**：避免歧义表达
2. **不要过度复杂**：Prompt 不是越长越好
3. **不要假设理解**：明确说明所有要求
4. **不要忽视格式**：严格指定输出格式
5. **不要一次定型**：Prompt 需要持续优化

---

**文档版本：** v1.0
**最后更新：** 2025-02-03
**维护者：** MultiAgentPPT Team
