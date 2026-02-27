# framework.py - 框架模型详解

## 📋 文件概述

`backend/agents_langchain/models/framework.py` 定义了 PPT 框架结构的领域模型。

## 🎯 主要功能

1. 定义页面类型和内容类型枚举
2. 定义页面定义和框架数据类
3. 提供框架验证和辅助函数

## 📦 枚举类型

### PageType

**页面类型枚举**

```python
class PageType(str, Enum):
    COVER = "cover"           # 封面
    DIRECTORY = "directory"   # 目录
    CONTENT = "content"       # 内容页
    CHART = "chart"           # 图表页
    IMAGE = "image"           # 配图页
    SUMMARY = "summary"       # 总结
    THANKS = "thanks"         # 致谢
```

### ContentType

**内容类型枚举**

```python
class ContentType(str, Enum):
    TEXT_ONLY = "text_only"             # 纯文本
    TEXT_WITH_IMAGE = "text_with_image" # 文字+配图
    TEXT_WITH_CHART = "text_with_chart" # 文字+图表
    TEXT_WITH_BOTH = "text_with_both"   # 文字+图表+配图
    IMAGE_ONLY = "image_only"           # 纯配图
    CHART_ONLY = "chart_only"           # 纯图表
```

## 📦 数据类

### PageDefinition

**页面定义数据类**

```python
@dataclass
class PageDefinition:
    page_no: int                           # 页码
    title: str                             # 页面标题
    page_type: PageType = PageType.CONTENT # 页面类型
    core_content: str = ""                 # 核心内容描述
    is_need_chart: bool = False            # 是否需要图表
    is_need_research: bool = False         # 是否需要研究资料
    is_need_image: bool = False            # 是否需要配图
    content_type: ContentType = ContentType.TEXT_ONLY
    keywords: List[str] = field(default_factory=list)
    estimated_word_count: int = 100        # 预估字数
    layout_suggestion: str = ""            # 布局建议
```

**核心方法**:

| 方法 | 描述 | 边界情况 |
|------|------|---------|
| `to_dict()` | 转换为字典格式 | 枚举自动转换为字符串 |
| `from_dict()` | 从字典创建实例 | 自动解析枚举字符串 |

### PPTFramework

**PPT 框架数据类**

```python
@dataclass
class PPTFramework:
    total_page: int                              # 总页数
    pages: List[PageDefinition] = field(...)     # 页面定义列表
    cover_page: Optional[PageDefinition] = None  # 封面页引用
    directory_page: Optional[PageDefinition] = None  # 目录页引用
    summary_page: Optional[PageDefinition] = None   # 总结页引用
    has_research_pages: bool = False             # 是否包含需要研究的页面
    research_page_indices: List[int] = field(...)   # 需要研究的页面索引
    chart_page_indices: List[int] = field(...)      # 需要图表的页面索引
    image_page_indices: List[int] = field(...)      # 需要配图的页面索引
    framework_type: str = "linear"                # 框架类型
```

**核心方法**:

| 方法 | 描述 | 边界情况 |
|------|------|---------|
| `add_page()` | 添加页面 | 自动重新编号和更新索引 |
| `insert_page()` | 在指定位置插入页面 | 自动重新编号 |
| `remove_page()` | 删除页面 | 返回被删除的页面，未找到返回 None |
| `get_page()` | 获取指定页码的页面 | 未找到返回 None |
| `get_pages_by_type()` | 根据类型获取页面列表 | 返回空列表如果没有 |
| `validate()` | 校验框架 | 返回 (是否有效, 错误列表) |
| `to_dict()` | 转换为字典格式 | - |
| `from_dict()` | 从字典创建实例 | - |
| `create_default()` | 创建默认框架 | 类方法 |

**内部方法**:
- `_renumber_pages()`: 重新编号页面
- `_update_special_pages()`: 更新特殊页面引用
- `_update_indices()`: 更新索引列表

## 🔧 辅助函数

### create_framework_from_requirement()

**从结构化需求创建 PPT 框架**

```python
def create_framework_from_requirement(
    requirement: Dict[str, Any]
) -> PPTFramework
```

**参数**:
- `requirement`: 结构化需求字典

**返回**: PPTFramework 实例

**边界情况**:
- 如果未提供 `ppt_topic`，使用空字符串
- 如果未提供 `page_num`，使用 10

### filter_pages_need_research()

**筛选需要研究的页面**

```python
def filter_pages_need_research(
    framework: PPTFramework
) -> List[PageDefinition]
```

### filter_pages_need_chart()

**筛选需要图表的页面**

```python
def filter_pages_need_chart(
    framework: PPTFramework
) -> List[PageDefinition]
```

## 🔐 验证规则

`PPTFramework.validate()` 检查以下规则：

| 规则 | 错误消息 |
|------|---------|
| 页数匹配期望值 | `页数不匹配：期望{expected}，实际{actual}` |
| 框架中有页面 | `框架中没有页面` |
| 第一页是封面 | `缺少封面页` |
| 页码连续 | `页码不连续：第{i}个页面的page_no是{page_no}` |
| 研究页面有关键词 | `第{n}页需要研究资料但没有提供关键词` |

## 📝 使用示例

```python
# 创建默认框架
framework = PPTFramework.create_default(
    page_num=10,
    topic="人工智能介绍"
)

# 验证框架
is_valid, errors = framework.validate(10)
if not is_valid:
    print(f"验证失败: {errors}")

# 转换为字典
framework_dict = framework.to_dict()

# 从字典恢复
framework2 = PPTFramework.from_dict(framework_dict)

# 添加页面
new_page = PageDefinition(
    page_no=11,
    title="新页面",
    page_type=PageType.CONTENT
)
framework.add_page(new_page)

# 筛选页面
research_pages = filter_pages_need_research(framework)
chart_pages = filter_pages_need_chart(framework)
```

## 🔗 相关文件

- [`state.py`](state.py.md): 状态模型定义
- [`../core/planning/framework_agent.py`](../03-core-agents/framework_agent.py.md): 使用这些模型的框架设计智能体
