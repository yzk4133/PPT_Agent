# 渲染 Agent 详解

> **核心个性**：将所有内容汇总为最终输出，生成预览数据和文件

---

## 目录

1. [职责与能力](#职责与能力)
2. [核心个性特征](#核心个性特征)
3. [输入输出格式](#输入输出格式)
4. [关键实现细节](#关键实现细节)
5. [XML 生成逻辑](#xml-生成逻辑)
6. [预览数据生成](#预览数据生成)
7. [使用示例](#使用示例)
8. [常见问题](#常见问题)

---

## 职责与能力

### 核心职责

渲染 Agent 是 PPT 生成流程的**最后一步**，负责将所有前面的工作（需求、框架、研究、内容）汇总为最终的可交付成果。

**为什么重要？**
- ❌ 没有它：前面的工作都是内存中的数据，用户无法使用
- ✅ 有它：生成用户可见、可用的最终输出

### 关键能力

| 能力 | 说明 | 重要性 |
|------|------|--------|
| **数据汇总** | 合并框架和内容数据 | ⭐⭐⭐⭐⭐ |
| **XML 生成** | 生成标准化的 XML 格式 | ⭐⭐⭐⭐⭐ |
| **预览数据** | 为前端提供预览信息 | ⭐⭐⭐⭐⭐ |
| **文件保存** | 保存输出到文件系统 | ⭐⭐⭐⭐ |
| **完整性验证** | 确保所有页面都有内容 | ⭐⭐⭐ |

---

## 核心个性特征

### 1. 数据汇总中心：连接所有前序阶段

**数据流转关系**：

```
┌───────────────────────────────────────────────────────────┐
│  PPT 生成流程的数据流                                      │
│                                                           │
│  用户输入                                                  │
│    ↓                                                       │
│  需求解析 ─────→ requirement                              │
│    ↓                                                       │
│  框架设计 ─────→ ppt_framework                            │
│    ↓                                                       │
│  研究 ─────→ research_results                             │
│    ↓                                                       │
│  内容生成 ─────→ content_materials                         │
│    ↓                                                       │
│  渲染 ─────→ 汇总所有数据 → 最终输出                      │
│                                                           │
│  渲染 Agent 是所有数据的汇聚点                             │
└───────────────────────────────────────────────────────────┘
```

**实现方式**：

```python
async def render(
    self,
    framework: Dict[str, Any],          # 来自框架设计 Agent
    content_materials: List[Dict],      # 来自内容生成 Agent
    requirement: Dict[str, Any],        # 来自需求解析 Agent
    task_id: str
) -> Dict[str, Any]:
    """渲染 PPT"""

    # 1. 验证输入数据完整性
    self._validate_inputs(framework, content_materials)

    # 2. 提取页面列表
    pages = framework["ppt_framework"]

    # 3. 为每个页面匹配内容
    for page in pages:
        page_no = page["page_no"]
        content = self._find_content_for_page(page_no, content_materials)
        page["content"] = content

    # 4. 生成 XML
    xml_content = self._generate_xml_content(framework, content_materials, requirement)

    # 5. 生成预览数据
    preview_data = self._generate_preview_data(framework, content_materials)

    # 6. 保存文件
    file_path = self._save_output(xml_content, task_id)

    return {
        "file_path": file_path,
        "xml_content": xml_content,
        "preview_data": preview_data,
        "total_pages": framework["total_page"]
    }
```

---

### 2. XML 生成：标准化的中间格式

**为什么使用 XML？**

```
┌─────────────────────────────────────────────────────────┐
│  输出格式的演进                                          │
│                                                         │
│  Phase 1（当前）：XML 格式                               │
│  ✅ 结构化、易于解析                                     │
│  ✅ 前端可以直接使用                                     │
│  ✅ 便于调试和验证                                       │
│  ❌ 不是真正的 PPT 文件                                  │
│                                                         │
│  Phase 2（未来）：.pptx 格式                             │
│  ✅ 真正的 PPT 文件                                      │
│  ✅ 可以用 PowerPoint 打开                              │
│  ✅ 支持复杂格式                                         │
│  ❌ 需要集成 python-pptx                                │
│                                                         │
│  Phase 3（未来）：多种格式                               │
│  - .pptx：真正的 PowerPoint 文件                        │
│  - .pdf：便于分享和打印                                  │
│  - HTML：在线预览                                       │
└─────────────────────────────────────────────────────────┘
```

**XML 结构**：

```xml
<PRESENTATION>
    <METADATA>
        <TOPIC>PPT 主题</TOPIC>
        <TOTAL_PAGES>10</TOTAL_PAGES>
        <CREATED_AT>2024-01-15T10:30:00</CREATED_AT>
        <LANGUAGE>ZH-CN</LANGUAGE>
    </METADATA>

    <SLIDES>
        <SLIDE page_no="1">
            <TYPE>cover</TYPE>
            <TITLE>人工智能在医疗领域的应用</TITLE>
            <SUBTITLE>技术前沿与临床实践</SUBTITLE>
            <AUTHOR>张三</AUTHOR>
            <DATE>2024-01-15</DATE>
        </SLIDE>

        <SLIDE page_no="2">
            <TYPE>directory</TYPE>
            <TITLE>目录</TITLE>
            <CONTENT>
                <ITEM>1. AI技术概述</ITEM>
                <ITEM>2. 医疗应用场景</ITEM>
                <ITEM>3. 案例分析</ITEM>
                <ITEM>4. 未来展望</ITEM>
            </CONTENT>
        </SLIDE>

        <SLIDE page_no="3">
            <TYPE>content</TYPE>
            <TITLE>AI在医疗诊断中的应用</TITLE>
            <CONTENT>
                <TEXT>AI正在医学影像诊断领域发挥重要作用...</TEXT>
                <CHART type="bar" title="诊断准确率对比">
                    <DATA>AI诊断：95%，人工诊断：85%</DATA>
                </CHART>
            </CONTENT>
            <KEY_POINTS>
                <POINT>影像识别与分析</POINT>
                <POINT>性能表现</POINT>
                <POINT>实际应用</POINT>
            </KEY_POINTS>
        </SLIDE>

        ... 更多页面 ...
    </SLIDES>
</PRESENTATION>
```

---

### 3. 预览数据生成：为前端提供摘要信息

**为什么需要预览数据？**

```python
# ❌ 如果没有预览数据
# 前端需要解析整个 XML 文件才能显示基本信息
# - 性能差：XML 文件可能很大
# - 复杂：前端需要解析 XML

# ✅ 有了预览数据
# 前端可以直接使用结构化的 JSON
# - 性能好：只包含必要信息
# - 简单：直接使用 JSON 数据
```

**预览数据结构**：

```python
{
    "total_pages": 10,
    "created_at": "2024-01-15T10:30:00",
    "pages": [
        {
            "page_no": 1,
            "title": "人工智能在医疗领域的应用",
            "type": "cover",
            "has_chart": False,
            "has_image": False,
            "preview_text": "人工智能在医疗领域的应用\n技术前沿与临床实践"
        },
        {
            "page_no": 2,
            "title": "目录",
            "type": "directory",
            "has_chart": False,
            "has_image": False,
            "preview_text": "目录\n1. AI技术概述\n2. 医疗应用场景..."
        },
        {
            "page_no": 3,
            "title": "AI在医疗诊断中的应用",
            "type": "content",
            "has_chart": True,
            "has_image": False,
            "preview_text": "AI正在医学影像诊断领域发挥重要作用：\n🎯 影像识别与分析..."
        }
        # ... 更多页面
    ]
}
```

**实现方式**：

```python
def _generate_preview_data(
    self,
    framework: Dict[str, Any],
    content_materials: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """生成预览数据"""

    pages = []

    # 遍历每一页
    for page_def in framework["ppt_framework"]:
        page_no = page_def["page_no"]

        # 找到对应的内容
        content = self._find_content_for_page(page_no, content_materials)

        # 生成预览文本（前100个字符）
        preview_text = content.get("content_text", "")[:100]

        pages.append({
            "page_no": page_no,
            "title": page_def.get("title", ""),
            "type": page_def.get("page_type", "content"),
            "has_chart": content.get("has_chart", False),
            "has_image": content.get("has_image", False),
            "preview_text": preview_text
        })

    return {
        "total_pages": framework["total_page"],
        "pages": pages,
        "created_at": datetime.now().isoformat()
    }
```

---

### 4. 页面与内容的匹配逻辑

**问题**：框架定义的页面和内容素材可能不一一对应

**解决方案**：

```python
def _find_content_for_page(
    self,
    page_no: int,
    content_materials: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """查找页面的内容素材"""

    # 1. 尝试精确匹配
    for content in content_materials:
        if content.get("page_no") == page_no:
            return content

    # 2. 没有找到，返回空内容
    self.logger.warning(f"No content found for page {page_no}")
    return self._empty_content()

def _empty_content(self) -> Dict[str, Any]:
    """返回空内容"""
    return {
        "content_text": "内容缺失",
        "has_chart": False,
        "has_image": False,
        "key_points": []
    }
```

**匹配流程**：

```
框架页面列表：[page1, page2, page3, ...]
内容素材列表：[content1, content2, content3, ...]

匹配逻辑：
┌─────────┬──────────────┬────────────────┐
│ 框架页面 │ 内容素材     │ 结果           │
├─────────┼──────────────┼────────────────┤
│ page1   │ content1     │ ✅ 匹配成功    │
│ page2   │ content2     │ ✅ 匹配成功    │
│ page3   │ (缺失)       │ ⚠️ 使用空内容  │
└─────────┴──────────────┴────────────────┘
```

---

## 输入输出格式

### 输入

```python
framework: Dict[str, Any]          # PPT 框架
content_materials: List[Dict]      # 内容素材列表
requirement: Dict[str, Any]        # 需求信息
task_id: str                       # 任务 ID
```

**示例**：

```python
framework = {
    "total_page": 3,
    "ppt_framework": [
        {
            "page_no": 1,
            "page_type": "cover",
            "title": "人工智能在医疗领域的应用"
        },
        {
            "page_no": 2,
            "page_type": "directory",
            "title": "目录"
        },
        {
            "page_no": 3,
            "page_type": "content",
            "title": "AI在医疗诊断中的应用"
        }
    ]
}

content_materials = [
    {
        "page_no": 1,
        "content_text": "人工智能在医疗领域的应用\n...",
        "has_chart": False,
        "has_image": False
    },
    {
        "page_no": 2,
        "content_text": "目录\n1. ...",
        "has_chart": False,
        "has_image": False
    },
    {
        "page_no": 3,
        "content_text": "AI正在医学影像诊断领域...",
        "has_chart": True,
        "has_image": False,
        "chart_data": {...}
    }
]

requirement = {
    "ppt_topic": "人工智能在医疗领域的应用",
    "language": "ZH-CN"
}

task_id = "task_20240115_103000"
```

### 输出

```python
{
    "file_path": str,             # 文件路径
    "xml_content": str,           # XML 内容
    "preview_data": {             # 预览数据
        "total_pages": int,
        "pages": [...],
        "created_at": str
    },
    "total_pages": int
}
```

---

## 关键实现细节

### 1. 主流程

```python
async def render(
    self,
    framework: Dict[str, Any],
    content_materials: List[Dict[str, Any]],
    requirement: Dict[str, Any],
    task_id: str
) -> Dict[str, Any]:
    """
    渲染 PPT

    流程：
    1. 验证输入数据
    2. 生成 XML 内容
    3. 生成预览数据
    4. 保存文件
    5. 返回结果
    """

    # 1. 验证输入
    self._validate_inputs(framework, content_materials)

    # 2. 生成 XML
    xml_content = self._generate_xml_content(
        framework=framework,
        content_materials=content_materials,
        requirement=requirement
    )

    # 3. 生成预览数据
    preview_data = self._generate_preview_data(
        framework=framework,
        content_materials=content_materials
    )

    # 4. 保存文件
    file_path = self._save_output(xml_content, task_id)

    # 5. 返回结果
    return {
        "file_path": file_path,
        "xml_content": xml_content,
        "preview_data": preview_data,
        "total_pages": framework["total_page"]
    }
```

---

### 2. 输入验证

```python
def _validate_inputs(
    self,
    framework: Dict[str, Any],
    content_materials: List[Dict[str, Any]]
):
    """验证输入数据"""

    # 检查框架
    if not framework:
        raise ValueError("框架不能为空")

    if "ppt_framework" not in framework:
        raise ValueError("框架缺少 ppt_framework 字段")

    if "total_page" not in framework:
        raise ValueError("框架缺少 total_page 字段")

    # 检查内容素材
    if not content_materials:
        self.logger.warning("内容素材为空，将使用空内容")

    # 检查页数匹配
    framework_pages = len(framework["ppt_framework"])
    content_pages = len(content_materials)

    if framework_pages != content_pages:
        self.logger.warning(
            f"框架页数({framework_pages})与内容页数({content_pages})不匹配"
        )
```

---

## XML 生成逻辑

### 1. 整体结构

```python
def _generate_xml_content(
    self,
    framework: Dict[str, Any],
    content_materials: List[Dict[str, Any]],
    requirement: Dict[str, Any]
) -> str:
    """生成 XML 内容"""

    lines = []

    # 1. 开始标签
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<PRESENTATION>')

    # 2. 元数据
    lines.append('  <METADATA>')
    lines.append(f'    <TOPIC>{self._escape_xml(requirement.get("ppt_topic", ""))}</TOPIC>')
    lines.append(f'    <TOTAL_PAGES>{framework["total_page"]}</TOTAL_PAGES>')
    lines.append(f'    <CREATED_AT>{datetime.now().isoformat()}</CREATED_AT>')
    lines.append(f'    <LANGUAGE>{requirement.get("language", "ZH-CN")}</LANGUAGE>')
    lines.append('  </METADATA>')

    # 3. 幻灯片列表
    lines.append('  <SLIDES>')
    for page_def in framework["ppt_framework"]:
        page_xml = self._generate_page_xml(
            page_no=page_def["page_no"],
            page_def=page_def,
            content_materials=content_materials,
            requirement=requirement
        )
        lines.append(page_xml)
    lines.append('  </SLIDES>')

    # 4. 结束标签
    lines.append('</PRESENTATION>')

    return '\n'.join(lines)
```

---

### 2. 单个页面生成

```python
def _generate_page_xml(
    self,
    page_no: int,
    page_def: Dict[str, Any],
    content_materials: List[Dict[str, Any]],
    requirement: Dict[str, Any]
) -> str:
    """生成单个页面的 XML"""

    lines = []
    indent = "    "

    # 找到内容素材
    content = self._find_content_for_page(page_no, content_materials)

    # 开始标签
    lines.append(f'{indent}<SLIDE page_no="{page_no}">')

    # 基本信息
    page_type = page_def.get("page_type", "content")
    lines.append(f'{indent}  <TYPE>{page_type}</TYPE>')
    lines.append(f'{indent}  <TITLE>{self._escape_xml(page_def.get("title", ""))}</TITLE>')

    # 根据类型生成不同的内容
    if page_type == "cover":
        lines.extend(self._generate_cover_xml(page_def, content, indent))
    elif page_type == "directory":
        lines.extend(self._generate_directory_xml(page_def, content, indent))
    elif page_type in ["summary", "thanks"]:
        lines.extend(self._generate_simple_xml(page_def, content, indent))
    else:
        lines.extend(self._generate_content_xml(page_def, content, indent))

    # 结束标签
    lines.append(f'{indent}</SLIDE>')

    return '\n'.join(lines)
```

---

### 3. 不同类型的 XML 生成

#### 封面页

```python
def _generate_cover_xml(
    self,
    page_def: Dict,
    content: Dict,
    indent: str
) -> List[str]:
    """生成封面页 XML"""
    lines = []

    lines.append(f'{indent}  <SUBTITLE>{self._escape_xml(page_def.get("subtitle", ""))}</SUBTITLE>')
    lines.append(f'{indent}  <AUTHOR>{self._escape_xml(page_def.get("author", ""))}</AUTHOR>')
    lines.append(f'{indent}  <DATE>{page_def.get("date", datetime.now().strftime("%Y-%m-%d"))}</DATE>')

    return lines
```

#### 目录页

```python
def _generate_directory_xml(
    self,
    page_def: Dict,
    content: Dict,
    indent: str
) -> List[str]:
    """生成目录页 XML"""
    lines = []

    modules = page_def.get("modules", [])
    if modules:
        lines.append(f'{indent}  <CONTENT>')
        for module in modules:
            lines.append(f'{indent}    <ITEM>{self._escape_xml(module)}</ITEM>')
        lines.append(f'{indent}  </CONTENT>')

    return lines
```

#### 内容页

```python
def _generate_content_xml(
    self,
    page_def: Dict,
    content: Dict,
    indent: str
) -> List[str]:
    """生成内容页 XML"""
    lines = []

    # 文本内容
    content_text = content.get("content_text", "")
    if content_text:
        lines.append(f'{indent}  <CONTENT>')
        lines.append(f'{indent}    <TEXT>{self._escape_xml(content_text)}</TEXT>')

        # 图表
        if content.get("has_chart") and content.get("chart_data"):
            chart = content["chart_data"]
            lines.append(f'{indent}    <CHART type="{chart.get("chart_type", "")}">')
            lines.append(f'{indent}      <TITLE>{self._escape_xml(chart.get("chart_title", ""))}</TITLE>')
            lines.append(f'{indent}      <DATA>{self._escape_xml(chart.get("data_description", ""))}</DATA>')
            lines.append(f'{indent}    </CHART>')

        # 配图
        if content.get("has_image") and content.get("image_suggestion"):
            image = content["image_suggestion"]
            lines.append(f'{indent}    <IMAGE>')
            lines.append(f'{indent}      <SEARCH_QUERY>{self._escape_xml(image.get("search_query", ""))}</SEARCH_QUERY>')
            lines.append(f'{indent}      <DESCRIPTION>{self._escape_xml(image.get("description", ""))}</DESCRIPTION>')
            lines.append(f'{indent}    </IMAGE>')

        lines.append(f'{indent}  </CONTENT>')

    # 要点
    key_points = content.get("key_points", [])
    if key_points:
        lines.append(f'{indent}  <KEY_POINTS>')
        for point in key_points:
            lines.append(f'{indent}    <POINT>{self._escape_xml(point)}</POINT>')
        lines.append(f'{indent}  </KEY_POINTS>')

    return lines
```

---

## 预览数据生成

```python
def _generate_preview_data(
    self,
    framework: Dict[str, Any],
    content_materials: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """生成预览数据"""

    pages = []

    for page_def in framework["ppt_framework"]:
        page_no = page_def["page_no"]

        # 找到内容
        content = self._find_content_for_page(page_no, content_materials)

        # 预览文本（前100个字符）
        preview_text = content.get("content_text", "")
        if len(preview_text) > 100:
            preview_text = preview_text[:100] + "..."

        pages.append({
            "page_no": page_no,
            "title": page_def.get("title", ""),
            "type": page_def.get("page_type", "content"),
            "has_chart": content.get("has_chart", False),
            "has_image": content.get("has_image", False),
            "preview_text": preview_text
        })

    return {
        "total_pages": framework["total_page"],
        "pages": pages,
        "created_at": datetime.now().isoformat()
    }
```

---

## 文件保存

```python
def _save_output(
    self,
    xml_content: str,
    task_id: str
) -> str:
    """保存输出文件"""

    # 1. 确保输出目录存在
    output_dir = Path(self.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"ppt_{task_id}_{timestamp}.xml"
    file_path = output_dir / file_name

    # 3. 写入文件
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    self.logger.info(f"Output saved to: {file_path}")

    return str(file_path)
```

---

## 使用示例

### 基本使用

```python
from backend.agents_langchain.core.rendering.renderer_agent import (
    TemplateRendererAgent,
    create_renderer_agent
)

# 创建 Agent
agent = create_renderer_agent(output_dir="output")

# 准备数据
framework = {
    "total_page": 3,
    "ppt_framework": [
        {
            "page_no": 1,
            "page_type": "cover",
            "title": "人工智能在医疗领域的应用",
            "subtitle": "技术前沿与临床实践",
            "author": "张三"
        },
        {
            "page_no": 2,
            "page_type": "directory",
            "title": "目录",
            "modules": ["AI技术概述", "医疗应用场景", "案例分析", "未来展望"]
        },
        {
            "page_no": 3,
            "page_type": "content",
            "title": "AI在医疗诊断中的应用"
        }
    ]
}

content_materials = [
    {
        "page_no": 1,
        "content_text": "人工智能在医疗领域的应用\n技术前沿与临床实践\n\n汇报人：张三",
        "has_chart": False,
        "has_image": False
    },
    {
        "page_no": 2,
        "content_text": "目录\n1. AI技术概述\n2. 医疗应用场景\n3. 案例分析\n4. 未来展望",
        "has_chart": False,
        "has_image": False
    },
    {
        "page_no": 3,
        "content_text": "AI正在医学影像诊断领域发挥重要作用...",
        "has_chart": True,
        "has_image": False,
        "chart_data": {
            "chart_type": "bar",
            "chart_title": "AI诊断准确率对比",
            "data_description": "AI诊断：95%，人工诊断：85%"
        },
        "key_points": ["影像识别", "性能表现", "实际应用"]
    }
]

requirement = {
    "ppt_topic": "人工智能在医疗领域的应用",
    "language": "ZH-CN"
}

# 渲染 PPT
result = await agent.render(
    framework=framework,
    content_materials=content_materials,
    requirement=requirement,
    task_id="task_001"
)

# 查看结果
print(f"文件已保存: {result['file_path']}")
print(f"总页数: {result['total_pages']}")
print(f"预览数据页数: {len(result['preview_data']['pages'])}")
```

---

## 常见问题

### Q1: 为什么当前只生成 XML 而不是 .pptx？

A: XML 是 Phase 1 的简化实现。

```python
# Phase 1（当前）
✅ XML 格式
- 优点：简单、快速、易于调试
- 缺点：不是真正的 PPT 文件

# Phase 2（未来）
✅ .pptx 格式（使用 python-pptx）
- 优点：真正的 PowerPoint 文件
- 缺点：需要集成复杂库
```

### Q2: 如果某页没有内容素材怎么办？

A: 使用空内容占位。

```python
def _find_content_for_page(self, page_no, content_materials):
    for content in content_materials:
        if content["page_no"] == page_no:
            return content

    # 没找到，返回空内容
    self.logger.warning(f"Page {page_no} has no content, using empty content")
    return self._empty_content()
```

### Q3: 如何处理 XML 中的特殊字符？

A: 使用转义函数。

```python
def _escape_xml(self, text: str) -> str:
    """转义 XML 特殊字符"""
    if not text:
        return ""

    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")

    return text
```

### Q4: Phase 2 如何生成 .pptx 文件？

A: 使用 python-pptx 库。

```python
from pptx import Presentation

def _generate_pptx(self, framework, content_materials, requirement):
    """生成 .pptx 文件"""
    prs = Presentation()

    for page_def in framework["ppt_framework"]:
        # 添加幻灯片
        slide = prs.slides.add_slide(self._select_layout(page_def["page_type"]))

        # 添加标题
        title_shape = slide.shapes.title
        title_shape.text = page_def["title"]

        # 添加内容
        # ... 更多代码

    # 保存文件
    file_path = f"output/ppt_{task_id}.pptx"
    prs.save(file_path)

    return file_path
```

---

## 相关文档

- [Core Agents 设计指南](./README.md) - 通用架构和共性
- [内容生成 Agent](./content_agent.py.md) - 生成内容素材
- [框架设计 Agent](./framework_agent.py.md) - 设计 PPT 框架
- [需求解析 Agent](./requirement_agent.py.md) - 解析用户需求
