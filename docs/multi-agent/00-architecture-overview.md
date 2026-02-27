# 架构总览

## 🏗️ 整体架构

LangChain 多Agent PPT 生成系统是一个基于 LangGraph 的声明式工作流系统，采用状态图 (StateGraph) 模式构建。

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           LangChain Multi-Agent System                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │  Models     │    │ Coordinator │    │ Core Agents │                 │
│  │             │    │             │    │             │                 │
│  │ • State     │◄───┤ MasterGraph ├───►│ • Requirement│                │
│  │ • Framework │    │             │    │ • Framework  │                │
│  └─────────────┘    │ PagePipeline│    │ • Research   │                │
│                     └─────────────┘    │ • Content    │                │
│                                         │ • Renderer   │                │
│                                         └─────────────┘                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## 📊 工作流图

```
                    用户输入 (user_input)
                            │
                            ▼
              ┌─────────────────────────────┐
              │   Requirement Parser Agent   │ (15%)
              │   解析用户自然语言输入         │
              └──────────────┬──────────────┘
                             │
                             ▼
              ┌─────────────────────────────┐
              │   Framework Designer Agent   │ (30%)
              │   设计 PPT 框架结构           │
              └──────────────┬──────────────┘
                             │
                    ┌────────┴────────┐
                    │   need_research? │
                    └────────┬────────┘
                     ┌───────┴────────┐
                     │ YES            │ NO
                     ▼                │
        ┌──────────────────┐          │
        │  Research Agent  │ (50%)    │
        │  研究相关资料      │          │
        └─────────┬────────┘          │
                  │                    │
                  └──────┬─────────────┘
                         ▼
              ┌─────────────────────────────┐
              │   Content Material Agent     │ (80%)
              │   为每页生成详细内容          │
              └──────────────┬──────────────┘
                             │
                             ▼
              ┌─────────────────────────────┐
              │   Template Renderer Agent    │ (100%)
              │   生成最终 PPT 输出          │
              └──────────────┬──────────────┘
                             │
                             ▼
                      PPT 输出 (ppt_output)
```

## 🔧 核心组件

### 1. 模型层 (Models)

#### 状态模型 (`state.py`)

- **`PPTGenerationState`**: 主状态类，继承自所有子状态
  - `InputState`: 用户输入
  - `RequirementState`: 需求解析结果
  - `FrameworkState`: 框架设计结果
  - `ResearchState`: 研究结果
  - `ContentState`: 内容素材
  - `OutputState`: 最终输出

#### 框架模型 (`framework.py`)

- **`PageType`**: 页面类型枚举 (封面、目录、内容、图表等)
- **`ContentType`**: 内容类型枚举 (纯文本、图文、图表等)
- **`PageDefinition`**: 页面定义数据类
- **`PPTFramework`**: PPT 框架数据类

### 2. 协调器层 (Coordinator)

#### 主工作流图 (`master_graph.py`)

**`MasterGraph`** 类负责构建和执行整个工作流。

**核心方法**:
- `_build_graph()`: 构建状态图
- `_should_research()`: 条件判断函数
- `generate()`: 主入口函数

**节点定义**:
- `requirement_parser`: 需求解析节点
- `framework_designer`: 框架设计节点
- `research`: 研究节点（条件）
- `content_generation`: 内容生成节点
- `template_renderer`: 模板渲染节点

#### 页面流水线 (`page_pipeline.py`)

**`PagePipeline`** 类负责页面级别的并行执行。

**核心功能**:
- 使用 `asyncio.Semaphore` 控制并发数
- 重试失败的页面
- 进度跟踪
- 部分成功支持

### 3. 核心智能体层 (Core Agents)

#### 需求解析智能体 (`requirement_agent.py`)

**`RequirementParserAgent`** 负责解析用户输入。

**输入**:
- 自然语言用户输入

**输出**:
- 结构化需求字典:
  - `ppt_topic`: PPT 主题
  - `page_num`: 页数
  - `scene`: 使用场景
  - `template_type`: 模板类型
  - `core_modules`: 核心模块
  - `need_research`: 是否需要研究

**降级策略**:
- 如果 LLM 解析失败，使用规则基础解析

#### 框架设计智能体 (`framework_agent.py`)

**`FrameworkDesignerAgent`** 负责设计 PPT 框架。

**输入**:
- 结构化需求

**输出**:
- PPT 框架字典:
  - `total_page`: 总页数
  - `ppt_framework`: 页面定义列表
  - `research_page_indices`: 需要研究的页面索引
  - `chart_page_indices`: 需要图表的页面索引

**降级策略**:
- 使用 `PPTFramework.create_default()` 生成默认框架

#### 研究智能体 (`research_agent.py`)

**`ResearchAgent`** 负责为需要研究的页面收集资料。

**输入**:
- 页面定义

**输出**:
- 研究结果字典:
  - `research_content`: 研究内容
  - `keywords`: 关键词
  - `status`: 状态

**降级策略**:
- 返回占位内容

#### 内容生成智能体 (`content_agent.py`)

**`ContentMaterialAgent`** 负责为每页生成详细内容。

**输入**:
- 页面定义
- 研究结果（可选）

**输出**:
- 内容素材字典:
  - `content_text`: 正文内容
  - `has_chart`: 是否有图表
  - `chart_data`: 图表数据
  - `has_image`: 是否有配图
  - `image_suggestion`: 配图建议

**降级策略**:
- 根据页面类型生成简单内容

#### 渲染智能体 (`renderer_agent.py`)

**`TemplateRendererAgent`** 负责生成最终 PPT 输出。

**输入**:
- 框架字典
- 内容素材列表
- 需求字典

**输出**:
- 输出字典:
  - `file_path`: 文件路径
  - `preview_data`: 预览数据
  - `total_pages`: 总页数

## 🔄 状态流转

状态在 LangGraph 工作流中自动传递和累积：

```python
# 初始状态
{
    "user_input": "...",
    "task_id": "...",
    "structured_requirements": {},   # 由 requirement_agent 填充
    "ppt_framework": {},             # 由 framework_agent 填充
    "research_results": [],          # 由 research_agent 填充
    "content_materials": [],         # 由 content_agent 填充
    "ppt_output": {},                # 由 renderer_agent 填充
    "current_stage": "init",
    "progress": 0,
    ...
}
```

## ⚡ 性能优化

1. **并行执行**: 页面级流水线支持并发处理
2. **异步 I/O**: 所有 LLM 调用都是异步的
3. **重试机制**: 失败的任务会自动重试
4. **降级策略**: 确保即使部分失败也能产生结果

## 🔐 边界情况处理

每个 Agent 都实现了边界情况处理：

1. **输入验证**: 验证必需的输入字段
2. **错误捕获**: 捕获并记录异常
3. **降级机制**: 使用 fallback 策略
4. **状态验证**: 使用 `validate_state_for_stage()` 验证状态

## 📝 使用示例

参见 [05-examples](05-examples/) 目录获取详细的使用示例。
