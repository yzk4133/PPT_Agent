# 框架设计 Agent 详解

> **核心个性**：设计逻辑合理的 PPT 页面结构，自动验证和修复框架

---

## 目录

1. [职责与能力](#职责与能力)
2. [核心个性特征](#核心个性特征)
3. [设计原则](#设计原则)
4. [关键实现细节](#关键实现细节)
5. [验证与修复](#验证与修复)
6. [使用示例](#使用示例)
7. [常见问题](#常见问题)

---

## 职责与能力

### 核心职责

框架设计 Agent 是 PPT 生成流程的**建筑师**，负责根据结构化需求设计 PPT 的**框架结构**。

**为什么重要？**
- ❌ 没有它：不知道有多少页、每页什么内容、如何组织
- ✅ 有它：为内容生成 Agent 提供清晰的蓝图

### 关键能力

| 能力 | 说明 | 重要性 |
|------|------|--------|
| **框架设计** | 根据需求设计页面结构 | ⭐⭐⭐⭐⭐ |
| **自动验证** | 检查框架逻辑是否正确 | ⭐⭐⭐⭐⭐ |
| **自动修复** | 修复页码、页数等问题 | ⭐⭐⭐⭐⭐ |
| **模块分配** | 将核心模块分配到具体页面 | ⭐⭐⭐⭐ |
| **研究标记** | 标记需要研究的页面 | ⭐⭐⭐⭐ |
| **降级设计** | LLM 失败时使用模板框架 | ⭐⭐⭐ |

---

## 核心个性特征

### 1. 设计逻辑合理的页面结构

**什么是"逻辑合理"？**

```
✅ 合理的结构：
[封面] → [目录] → [第1章] → [第2章] → ... → [总结]
 ↑      ↑        ↑        ↑
第1页  第2页    第3页    第4页

❌ 不合理的结构：
[目录] → [封面] → [总结] → [第2章]
↑ 封面不在第1页，目录在封面前面
```

**设计规则**：

```python
# 规则1：第1页必须是封面
if pages[0].page_type != PageType.COVER:
    errors.append("第一页必须是封面页")

# 规则2：第2页通常是目录
if len(pages) >= 2:
    if pages[1].page_type != PageType.DIRECTORY:
        warnings.append("第二页建议是目录页")

# 规则3：最后一页通常是总结或致谢
last_page = pages[-1]
if last_page.page_type not in [PageType.SUMMARY, PageType.THANKS]:
    warnings.append("最后一页建议是总结或致谢")

# 规则4：页码必须从1开始连续
for i, page in enumerate(pages, 1):
    if page.page_no != i:
        errors.append(f"第{i}页的page_no是{page.page_no}")
```

---

### 2. 自动验证和修复框架

**验证检查项**：

```python
def validate(framework, expected_page_num):
    """验证框架"""
    errors = []

    # 检查1：页数是否正确
    if framework.total_page != expected_page_num:
        errors.append(f"页数不匹配：期望{expected_page_num}，实际{framework.total_page}")

    # 检查2：是否有封面
    has_cover = any(p.page_type == PageType.COVER for p in framework.pages)
    if not has_cover:
        errors.append("缺少封面页")

    # 检查3：页码是否连续
    for i, page in enumerate(framework.pages):
        if page.page_no != i + 1:
            errors.append(f"页码不连续：第{i+1}个页面的page_no是{page.page_no}")

    # 检查4：需要研究的页面有关键词
    for page in framework.pages:
        if page.is_need_research and not page.keywords:
            errors.append(f"第{page.page_no}页需要研究资料但没有提供关键词")

    return len(errors) == 0, errors
```

**自动修复**：

```python
def fix_framework(framework, expected_page_num):
    """修复框架"""

    # 修复1：调整页数
    if len(framework.pages) < expected_page_num:
        # 添加缺失的页面
        for i in range(len(framework.pages), expected_page_num):
            framework.add_page(PageDefinition(
                page_no=i + 1,
                title=f"第{i+1}部分",
                page_type=PageType.CONTENT
            ))
    elif len(framework.pages) > expected_page_num:
        # 删除多余的页面
        framework.pages = framework.pages[:expected_page_num]

    # 修复2：重新编号所有页面
    framework._renumber_pages()

    # 修复3：更新特殊页面引用
    framework._update_special_pages()

    # 修复4：更新索引列表
    framework._update_indices()

    return framework
```

---

### 3. 核心模块到页面的智能分配

**挑战**：用户需求是"5个核心模块"，但 PPT 只有10页，如何分配？

**分配策略**：

```python
def _distribute_modules_to_pages(
    self,
    modules: List[str],
    total_page_num: int
) -> List[Dict]:
    """将核心模块分配到页面"""

    # 可用页数（除去封面、目录、总结）
    available_pages = total_page_num - 3  # 假设需要封面、目录、总结

    # 平均分配
    pages_per_module = max(1, available_pages // len(modules))

    pages = []
    current_page = 2  # 从第2页开始（第1页是封面）

    for module_name in modules:
        # 决定这个模块占用几页
        pages_for_module = min(pages_per_module, available_pages)

        # 创建页面定义
        for i in range(pages_for_module):
            pages.append({
                "page_no": current_page,
                "title": f"{module_name}（{i+1}）" if pages_for_module > 1 else module_name,
                "page_type": PageType.CONTENT,
                "core_content": f"{module_name}的详细内容",
                # ...
            })

            current_page += 1
            available_pages -= 1

    return pages
```

**示例**：

```python
# 输入
modules = ["AI介绍", "技术原理", "应用场景", "未来展望"]
page_num = 10

# 输出
pages = [
    {"page_no": 1, "title": "封面", ...},
    {"page_no": 2, "title": "目录", ...},
    {"page_no": 3, "title": "AI介绍", ...},        # 模块1
    {"page_no": 4, "title": "技术原理", ...},      # 模块2
    {"page_no": 5, "title": "应用场景（1）", ...}, # 模块3
    {"page_no": 6, "title": "应用场景（2）", ...}, # 模块3
    {"page_no": 7, "title": "未来展望", ...},      # 模块4
    {"page_no": 8, "title": "总结", ...},
    # ... 等等，这样分配
]
```

---

### 4. 研究页面的智能标记

**什么时候需要研究？**

```python
def _mark_research_pages(
    self,
    framework: PPTFramework,
    requirement: Dict[str, Any]
):
    """标记需要研究的页面"""

    # 选项1：用户明确指定
    if requirement.get("need_research"):
        # 默认第3、6、9页需要研究（均匀分布）
        research_indices = [i for i in range(3, framework.total_page + 1, 3)]

    # 选项2：根据关键词判断
    else:
        research_indices = []
        for page in framework.pages:
            # 如果页面标题包含"前沿"、"最新"、"技术"等关键词
            research_keywords = ["前沿", "最新", "技术", "研究", "发展"]
            if any(keyword in page.title for keyword in research_keywords):
                research_indices.append(page.page_no)

    # 标记页面
    for idx in research_indices:
        framework.pages[idx - 1].is_need_research = True

    # 更新框架
    framework.research_page_indices = research_indices
    framework.has_research_pages = len(research_indices) > 0
```

---

## 设计原则

### 1. 固定页面规则

```
┌──────────────────────────────────────────┐
│  页码   页面类型      是否必需               │
├──────────────────────────────────────────┤
│   1     封面(COVER)      ✅ 必需              │
│   2     目录(DIRECTORY)   ⭐ 强烈建议         │
│   3     内容(CONTENT)     -                  │
│   ...    ...            -                  │
│  n-1    内容(CONTENT)     -                  │
│   n     总结(SUMMARY)    ⭐ 强烈建议         │
│   n+1   致谢(THANKS)    - 可选              │
└──────────────────────────────────────────┘
```

### 2. 页面类型定义

```python
class PageType(str, Enum):
    """页面类型"""
    COVER = "cover"                   # 封面
    DIRECTORY = "directory"            # 目录
    CONTENT = "content"                # 内容页
    CHART = "chart"                    # 图表页
    IMAGE = "image"                    # 配图页
    SUMMARY = "summary"                # 总结
    THANKS = "thanks"                  # 致谢
```

### 3. 内容类型定义

```python
class ContentType(str, Enum):
    """内容类型"""
    TEXT_ONLY = "text_only"            # 纯文本
    TEXT_WITH_IMAGE = "text_with_image"  # 文字+配图
    TEXT_WITH_CHART = "text_with_chart"  # 文字+图表
    TEXT_WITH_BOTH = "text_with_both"    # 文字+图表+配图
    IMAGE_ONLY = "image_only"          # 纯配图
    CHART_ONLY = "chart_only"          # 纯图表
```

### 4. 设计约束

```python
# 约束1：总页数必须匹配
expected_page_num = requirement["page_num"]
assert framework.total_page == expected_page_num

# 约束2：页码必须连续
for i, page in enumerate(framework.pages):
    assert page.page_no == i + 1

# 约束3：核心模块必须全部分配
framework_modules = [p.title for p in framework.pages if p.page_type == PageType.CONTENT]
for module in requirement["core_modules"]:
    assert any(module in title for title in framework_modules)

# 约束4：需要研究的页面必须有关键词
for page in framework.pages:
    if page.is_need_research:
        assert page.keywords, f"第{page.page_no}页需要研究但没有关键词"
```

---

## 输入输出格式

### 输入

```python
{
    "ppt_topic": str,                # PPT 主题
    "page_num": int,                 # 页数
    "scene": str,                    # 场景
    "core_modules": List[str],        # 核心模块列表
    "need_research": bool,           # 是否需要研究
    "template_type": str,            # 模板类型
    "language": str,                 # 语言
    # ... 其他字段
}
```

### 输出

```python
{
    "total_page": int,                      # 总页数

    "ppt_framework": [                      # 页面定义列表
        {
            "page_no": int,                  # 页码
            "title": str,                    # 页面标题
            "page_type": str,                # 页面类型
            "core_content": str,             # 核心内容描述
            "is_need_chart": bool,            # 是否需要图表
            "is_need_research": bool,         # 是否需要研究
            "is_need_image": bool,            # 是否需要配图
            "content_type": str,              # 内容类型
            "keywords": List[str],             # 关键词
            "estimated_word_count": int,      # 预估字数
            "layout_suggestion": str          # 布局建议
        },
        # ... 更多页面
    ],

    "has_research_pages": bool,             # 是否有需要研究的页面
    "research_page_indices": List[int],      # 需要研究的页码列表
    "chart_page_indices": List[int],         # 需要图表的页码列表
    "image_page_indices": List[int],         # 需要配图的页码列表
    "framework_type": str                   # 框架类型（linear/branching）
}
```

---

## 关键实现细节

### 1. 主设计流程

```python
async def design(self, requirement: Dict[str, Any]) -> Dict[str, Any]:
    """
    设计 PPT 框架的主流程

    流程：
    1. 创建基础框架（封面、目录、总结）
    2. 分配核心模块到内容页
    3. 标记需要特殊功能的页面（研究、图表、配图）
    4. 验证框架逻辑
    5. 修复发现的问题
    6. 返回最终框架
    """

    # 1. 创建基础框架
    framework = PPTFramework.create_default(
        page_num=requirement["page_num"],
        topic=requirement["ppt_topic"]
    )

    # 2. 替换内容页（如果有核心模块）
    if requirement["core_modules"]:
        # 删除默认的内容页
        framework.pages = [
            p for p in framework.pages
            if p.page_type in [PageType.COVER, PageType.DIRECTORY, PageType.SUMMARY]
        ]

        # 添加基于核心模块的内容页
        module_pages = self._distribute_modules_to_pages(
            modules=requirement["core_modules"],
            total_page_num=requirement["page_num"]
        )
        for page_dict in module_pages:
            framework.add_page(PageDefinition.from_dict(page_dict))

    # 3. 标记特殊页面
    self._mark_special_pages(framework, requirement)

    # 4. 验证和修复
    is_valid, errors = framework.validate(requirement["page_num"])
    if not is_valid:
        self.logger.warning(f"Framework validation failed: {errors}")
        framework = self._fix_framework(framework, requirement["page_num"])

    # 5. 返回
    return framework.to_dict()
```

---

### 2. 核心模块分配算法

```python
def _distribute_modules_to_pages(
    self,
    modules: List[str],
    total_page_num: int,
    available_page_func: Optional[callable] = None
) -> List[PageDefinition]:
    """
    将核心模块智能分配到页面

    策略：
    - 重要模块分配更多页面
    - 相关模块合并到一个页面
    - 确保所有模块都有空间展示
    """

    # 1. 分析模块重要性
    module_weights = {
        "背景": 1, "介绍": 1, "概述": 1,
        "原理": 2, "方法": 2, "技术": 2, "实现": 2,
        "应用": 3, "案例": 3, "实践": 3, "场景": 3,
        "优势": 2, "创新": 2, "亮点": 2,
        "挑战": 1, "风险": 1, "不足": 1,
        "总结": 2, "展望": 2, "未来": 2,
    }

    # 2. 计算每个模块的权重分数
    module_scores = []
    for module in modules:
        score = 0
        for keyword, weight in module_weights.items():
            if keyword in module:
                score += weight
        module_scores.append((module, score))

    # 3. 按重要性排序
    module_scores.sort(key=lambda x: x[1], reverse=True)

    # 4. 可用页数（除去固定页面）
    available_pages = total_page_num - 3  # 减去封面、目录、总结

    # 5. 智能分配
    pages = []
    current_page_no = 2  # 从第2页开始（第1页是封面）
    remaining_pages = available_pages

    for i, (module, score) in enumerate(module_scores):
        # 根据重要性决定页数
        if i < len(module_scores) - 1:
            # 不是最后一个模块
            if score >= 3:
                pages_for_this = min(3, remaining_pages // (len(module_scores) - i))
            else:
                pages_for_this = min(2, remaining_pages // (len(module_scores) - i))
        else:
            # 最后一个模块，占用所有剩余页面
            pages_for_this = remaining_pages

        # 创建页面
        for j in range(pages_for_this):
            subtitle = f"（{j+1}）" if pages_for_this > 1 else ""
            pages.append(PageDefinition(
                page_no=current_page_no + j,
                title=f"{module}{subtitle}",
                page_type=PageType.CONTENT,
                core_content=f"{module}的详细内容",
                # ...
            ))

        current_page_no += pages_for_this
        remaining_pages -= pages_for_this

    return pages
```

---

### 3. 特殊页面标记逻辑

```python
def _mark_special_pages(
    self,
    framework: PPTFramework,
    requirement: Dict[str, Any]
):
    """标记特殊页面"""

    # 1. 标记需要研究的页面
    if requirement.get("need_research"):
        research_indices = []
        for i, page in enumerate(framework.pages):
            # 默认每3页中有1页需要研究
            if (i + 1) % 3 == 0 and page.page_type == PageType.CONTENT:
                research_indices.append(page.page_no)
                page.is_need_research = True
                # 添加关键词（从页面标题提取）
                page.keywords = [page.title]

        framework.research_page_indices = research_indices
        framework.has_research_pages = len(research_indices) > 0

    # 2. 标记需要图表的页面
    chart_keywords = ["数据", "统计", "对比", "趋势", "分析"]
    for page in framework.pages:
        if page.page_type == PageType.CONTENT:
            if any(keyword in page.title for keyword in chart_keywords):
                page.is_need_chart = True
                break  # 每个内容页最多一个图表

    # 3. 标记需要配图的页面
    image_keywords = ["展示", "演示", "效果", "产品", "界面"]
    for page in framework.pages:
        if page.page_type == PageType.CONTENT:
            if any(keyword in page.title for keyword in image_keywords):
                page.is_need_image = True
```

---

## 验证与修复

### 验证函数

```python
def validate(self, expected_page_num: int) -> tuple[bool, List[str]]:
    """
    验证框架

    检查项：
    1. 总页数是否匹配
    2. 是否有封面
    3. 页码是否连续
    4. 需要研究的页面是否有关键词
    """

    errors = []

    # 检查1：页数
    if self.total_page != expected_page_num:
        errors.append(f"页数不匹配：期望{expected_page_num}，实际{self.total_page}")

    # 检查2：封面
    if not self.pages or self.pages[0].page_type != PageType.COVER:
        errors.append("缺少封面页")

    # 检查3：页码连续性
    for i, page in enumerate(self.pages):
        if page.page_no != i + 1:
            errors.append(f"页码不连续：第{i+1}个页面的page_no是{page.page_no}")

    # 检查4：研究页面关键词
    for page in self.pages:
        if page.is_need_research and not page.keywords:
            errors.append(f"第{page.page_no}页需要研究资料但没有提供关键词")

    return len(errors) == 0, errors
```

### 修复函数

```python
def fix(self, expected_page_num: int) -> None:
    """
    修复框架

    修复项：
    1. 调整页数
    2. 重新编号页面
    3. 更新特殊页面引用
    4. 更新索引列表
    """

    # 修复1：调整页数
    if len(self.pages) < expected_page_num:
        # 添加缺失的页面
        for i in range(len(self.pages), expected_page_num):
            self.add_page(PageDefinition(
                page_no=i + 1,
                title=f"第{i+1}部分",
                page_type=PageType.CONTENT,
                core_content=f"第{i+1}部分的内容",
            ))
    elif len(self.pages) > expected_page_num:
        # 删除多余的页面
        self.pages = self.pages[:expected_page_num]

    # 修复2：重新编号
    self._renumber_pages()

    # 修复3：更新特殊页面引用
    self._update_special_pages()

    # 修复4：更新索引
    self._update_indices()
```

---

## 使用示例

### 基本使用

```python
from backend.agents_langchain.core.planning.framework_agent import (
    FrameworkDesignerAgent,
    create_framework_designer
)

# 创建 Agent
agent = create_framework_designer()

# 准备需求
requirement = {
    "ppt_topic": "人工智能概述",
    "page_num": 10,
    "core_modules": ["背景介绍", "技术原理", "应用场景", "未来展望"],
    "need_research": True,
    "language": "ZH-CN"
}

# 设计框架
framework = await agent.design(requirement)

# 查看结果
print(f"总页数: {framework['total_page']}")
print(f"页面列表: {[p['title'] for p in framework['ppt_framework']]}")
print(f"研究页面: {framework['research_page_indices']}")
print(f"图表页面: {framework['chart_page_indices']}")
```

---

## 常见问题

### Q1: 如何确保页码连续？

A: 自动重新编号

```python
def _renumber_pages(self):
    """重新编号所有页面"""
    for i, page in enumerate(self.pages, 1):
        page.page_no = i
```

### Q2: 如何处理页数不匹配？

A: 自动添加或删除

```python
def _fix_page_count(self, target_count: int):
    """修复页数"""
    current_count = len(self.pages)

    if current_count < target_count:
        # 添加页面
        for i in range(current_count, target_count):
            self.add_page(PageDefinition(
                page_no=i + 1,
                title=f"第{i+1}部分",
                page_type=PageType.CONTENT
            ))
    elif current_count > target_count:
        # 删除页面
        self.pages = self.pages[:target_count]
```

### Q3: 如何标记需要研究的页面？

A: 根据需求或关键词

```python
# 方式1：根据需求标记
if requirement.get("need_research"):
    for page in pages:
        if (page.page_no - 2) % 3 == 0:  # 每3页中有1页需要研究
            page.is_need_research = True
            page.keywords = [page.title]

# 方式2：根据关键词标记
research_keywords = ["前沿", "最新", "技术"]
for page in pages:
    if any(kw in page.title for kw in research_keywords):
        page.is_need_research = True
```

---

## 相关文档

- [Core Agents 设计指南](./README.md) - 通用架构和共性
- [需求解析 Agent](./requirement_agent.py.md) - 上一站：需求解析
- [研究 Agent](./research_agent.py.md) - 下一站：研究功能
