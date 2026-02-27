# LangChain 多 Agent 系统模型设计指南

> 本文档说明 `backend/agents_langchain/models/` 目录中两个核心文件的设计思路和最佳实践。

---

## 目录

1. [两个文件的核心区别](#两个文件的核心区别)
2. [设计顺序：自顶向下](#设计顺序自顶向下)
3. [framework.py 设计指南](#frameworkpy-设计指南)
4. [state.py 设计指南](#statepy-设计指南)
5. [边界情况处理](#边界情况处理)
6. [书写顺序与时间分配](#书写顺序与时间分配)
7. [快速自检清单](#快速自检清单)

---

## 两个文件的核心区别

### 形象理解

| 维度 | state.py | framework.py |
|------|----------|--------------|
| **含义** | "我已经写到第3页了" | "这个 PPT 有10页，第1页是封面" |
| **关注点** | 任务执行过程 | 产品数据结构 |
| **生命周期** | 临时，任务完成就丢弃 | 持久，PPT 文件的一部分 |
| **变化频率** | 每个节点执行后都在变 | 只在"框架设计阶段"确定一次 |
| **存储位置** | 内存中，Agent 之间传递 | 最终会写入 PPT 文件 |
| **谁关心** | Orchestrator（协调者） | Template Renderer（渲染器） |

### 类比说明

| 类比 | state.py | framework.py |
|------|----------|--------------|
| **外卖** | 订单状态（已下单→配送中→已完成） | 订单内容（汉堡+薯条+可乐） |
| **做饭** | 做饭的步骤 | 食谱的配方 |
| **进度** | 进度条 | 设计图 |

简单说：**state 是工作流的"进度条"，framework 是 PPT 的"设计图"**。

---

## 设计顺序：自顶向下

```
1. 理解业务 → 2. 设计领域模型 → 3. 设计状态模型 → 4. 实现辅助函数
         ↓              ↓                ↓              ↓
     framework.py    framework.py     state.py      state.py
```

### 第一步：理解业务（动笔之前先想清楚）

**问自己这几个问题：**

| 问题 | 示例答案 |
|------|----------|
| **整个流程有几步？** | 需求解析 → 框架设计 → 研究 → 内容生成 → 渲染 |
| **每步输入是什么？** | 需求解析输入：用户自然语言 |
| **每步输出是什么？** | 框架设计输出：PPT 结构定义 |
| **最终产品是什么？** | 一个 .pptx 文件，包含 N 页幻灯片 |
| **哪些数据需要持久化？** | PPT 框架、每页的内容 |
| **哪些数据只是临时用的？** | 进度、错误信息、执行日志 |

---

## framework.py 设计指南

**为什么先设计这个？** → 因为状态是为业务服务的，不知道长什么样怎么设计状态？

### 必须包含的内容

```python
# 1. 枚举：业务中固定的分类
class PageType(str, Enum):
    COVER = "cover"
    DIRECTORY = "directory"
    CONTENT = "content"
    CHART = "chart"
    IMAGE = "image"
    SUMMARY = "summary"
    THANKS = "thanks"

class ContentType(str, Enum):
    TEXT_ONLY = "text_only"
    TEXT_WITH_IMAGE = "text_with_image"
    TEXT_WITH_CHART = "text_with_chart"
    TEXT_WITH_BOTH = "text_with_both"
    IMAGE_ONLY = "image_only"
    CHART_ONLY = "chart_only"

# 2. 核心实体：最小的业务单元
@dataclass
class PageDefinition:
    page_no: int          # 必须：唯一标识
    title: str            # 必须：业务核心字段
    page_type: PageType   # 必须：分类
    core_content: str     # 必须：核心内容
    is_need_chart: bool   # 业务字段
    is_need_research: bool
    is_need_image: bool
    content_type: ContentType
    keywords: List[str]
    estimated_word_count: int
    layout_suggestion: str

    # 必须：字典转换（用于序列化）
    def to_dict(self) -> Dict[str, Any]: ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PageDefinition": ...

# 3. 聚合根：管理实体的容器
@dataclass
class PPTFramework:
    total_page: int
    pages: List[PageDefinition]

    # 必须：增删改查
    def add_page(self, page: PageDefinition) -> None: ...
    def insert_page(self, index: int, page: PageDefinition) -> None: ...
    def remove_page(self, page_no: int) -> Optional[PageDefinition]: ...
    def get_page(self, page_no: int) -> Optional[PageDefinition]: ...
    def get_pages_by_type(self, page_type: PageType) -> List[PageDefinition]: ...

    # 必须：验证规则
    def validate(self, expected_page_num: int) -> tuple[bool, List[str]]: ...

    # 必须：字典转换
    def to_dict(self) -> Dict[str, Any]: ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PPTFramework": ...

    # 便捷方法
    @classmethod
    def create_default(cls, page_num: int, topic: str = "") -> "PPTFramework": ...
```

### 设计检查清单

- [ ] 所有业务实体都列出来了吗？
- [ ] 实体之间的关系清楚吗？（如：PPT 包含多个 Page）
- [ ] 每个字段有类型约束吗？
- [ ] 有验证逻辑吗？（如：总页数必须等于 pages 数量）
- [ ] 有字典转换方法吗？（`to_dict` / `from_dict`，用于序列化）
- [ ] 有便捷的工厂方法吗？（如 `create_default`）

---

## state.py 设计指南

### 必须包含的内容

```python
# 1. 输入状态：工作流的起点
class InputState(TypedDict):
    user_input: str      # 用户说了什么
    task_id: str         # 任务唯一标识

# 2. 各阶段输出状态：每个节点产生什么
class RequirementState(TypedDict):
    structured_requirements: Dict[str, Any]  # 需求解析的结果

class FrameworkState(TypedDict):
    ppt_framework: Dict[str, Any]            # 框架设计的结果

class ResearchState(TypedDict):
    research_results: List[Dict[str, Any]]   # 研究的结果

class ContentState(TypedDict):
    content_materials: List[Dict[str, Any]]  # 内容生成的结果

class OutputState(TypedDict):
    ppt_output: Dict[str, Any]               # 最终 PPT 输出

# 3. 主状态：累积所有信息
class PPTGenerationState(InputState, RequirementState, FrameworkState,
                          ResearchState, ContentState, OutputState):
    # 必须：元数据
    current_stage: str
    progress: int
    messages: List[BaseMessage]
    error: Optional[str]

    # 必须：审计信息
    start_time: str
    user_id: str
    session_id: str

# 4. 工厂函数：创建初始状态
def create_initial_state(
    user_input: str,
    task_id: str,
    user_id: str = "anonymous"
) -> PPTGenerationState: ...

# 5. 更新函数：修改状态
def update_state_progress(
    state: PPTGenerationState,
    stage: str,
    progress: int
) -> PPTGenerationState: ...

def add_message_to_state(
    state: PPTGenerationState,
    message: BaseMessage
) -> PPTGenerationState: ...

def set_state_error(
    state: PPTGenerationState,
    error: str
) -> PPTGenerationState: ...

# 6. 验证函数：检查状态完整性
def validate_state_for_stage(
    state: PPTGenerationState,
    stage: str
) -> tuple[bool, List[str]]: ...

# 7. 辅助查询函数：简化状态访问
def get_requirement_field(
    state: PPTGenerationState,
    field: str,
    default=None
) -> Any: ...

def get_framework_pages(
    state: PPTGenerationState
) -> List[Dict[str, Any]]: ...

def needs_research(state: PPTGenerationState) -> bool: ...
```

### 设计检查清单

- [ ] 每个节点的输入输出都定义了吗？
- [ ] 状态字段有初始值吗？（避免 KeyError）
- [ ] 有类型注解吗？（TypedDict 很重要）
- [ ] 有验证函数吗？（确保数据完整）
- [ ] 有辅助查询函数吗？（如 `needs_research(state)`）
- [ ] 有错误处理机制吗？（`set_state_error`）

---

## 边界情况处理

### framework.py 要考虑

```python
# 边界情况
- 没有页的 PPT 怎么办？ → validate() 检查
- 删除封面页后，谁来当新封面？ → _update_special_pages() 重新分配
- 页码不连续怎么办？ → _renumber_pages() 自动重排
- 需要研究但没有关键词？ → validate() 报错
```

### state.py 要考虑

```python
# 边界情况
- 某个节点失败了，状态怎么记录？ → error 字段
- 用户中途取消任务，状态怎么更新？ → update_state_progress()
- 并发任务会不会互相干扰？ → task_id / session_id 隔离
- 状态字段访问失败怎么办？ → get_xxx() 函数提供默认值
```

---

## 书写顺序与时间分配

```bash
# 1. 先写框架模型（30% 时间）
framework.py:
  ├─ 枚举定义 (PageType, ContentType)
  ├─ PageDefinition
  ├─ PPTFramework
  └─ 单元测试

# 2. 再写状态模型（40% 时间）
state.py:
  ├─ 各阶段 State 定义
  ├─ 主 State 定义
  ├─ 工厂函数 (create_initial_state)
  ├─ 更新函数 (update_state_progress)
  ├─ 验证函数 (validate_state_for_stage)
  └─ 辅助查询函数

# 3. 最后写 __init__.py（5% 时间）
__init__.py:
  └─ 导出所有公共接口

# 4. 补充文档和测试（25% 时间）
docstrings + unit tests
```

---

## 快速自检清单

写完后问自己：

| 问题 | 检查方式 |
|------|----------|
| **能独立运行吗？** | `python framework.py` 不报错 |
| **能序列化吗？** | `to_dict()` 后能 JSON 序列化 |
| **能反序列化吗？** | `from_dict()` 后恢复原样 |
| **类型安全吗？** | mypy 检查无错误 |
| **有测试吗？** | pytest 通过所有用例 |
| **有文档吗？** | 每个函数都有 docstring |
| **易于使用吗？** | 提供了便捷的查询函数 |

---

## 核心原则

```
framework.py：面向业务，变化少 → 用 dataclass，强类型
state.py：    面向流程，变化多 → 用 TypedDict，弱类型
```

### 这样设计的好处

1. **业务改了不用动状态** → 修改 PPT 结构只需改 framework.py
2. **流程改了不用动业务** → 增加处理节点只需改 state.py
3. **各自独立测试** → 可以单独验证领域逻辑和状态转换
4. **团队协作友好** → 不同的人可以并行开发

---

## 实际代码示例

### framework.py 关键代码片段

```python
@dataclass
class PPTFramework:
    """PPT 框架的聚合根"""
    total_page: int
    pages: List[PageDefinition] = field(default_factory=list)

    def add_page(self, page: PageDefinition) -> None:
        """添加页面并自动维护一致性"""
        page.page_no = len(self.pages) + 1
        self.pages.append(page)
        self.total_page = len(self.pages)
        self._update_special_pages()  # 自动更新特殊页面引用
        self._update_indices()         # 自动更新索引列表
```

### state.py 关键代码片段

```python
def create_initial_state(
    user_input: str,
    task_id: str,
    user_id: str = "anonymous"
) -> PPTGenerationState:
    """创建所有字段已初始化的初始状态，避免 KeyError"""
    return PPTGenerationState(
        user_input=user_input,
        task_id=task_id,
        structured_requirements={},  # 空字典而非 None
        ppt_framework={},
        research_results=[],
        content_materials=[],
        ppt_output={},
        current_stage="init",
        progress=0,
        messages=[],
        error=None,
        start_time=datetime.now().isoformat(),
        user_id=user_id,
        session_id=task_id,
    )
```

---

## 总结

1. **先理解业务，再写代码** → 不然后面会反复重构
2. **先设计领域模型，再设计状态** → 状态是为业务服务的
3. **dataclass 强类型，TypedDict 弱类型** → 各有适用场景
4. **提供便捷函数** → 让调用者更轻松
5. **必须有序列化方法** → 数据要在不同服务间传递
6. **必须有验证逻辑** → 尽早发现数据问题
7. **必须有测试** → 保证代码质量
