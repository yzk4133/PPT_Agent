# 基础用法

## 📋 概述

本文档提供 LangChain 多Agent PPT 生成系统的基础使用示例。

## 🚀 快速开始

### 1. 基本用法

```python
from agents_langchain import create_master_graph

# 创建工作流图
graph = create_master_graph()

# 生成 PPT
result = await graph.generate(
    user_input="创建一份关于人工智能的PPT，10页"
)

# 查看结果
print(f"任务 ID: {result['task_id']}")
print(f"输出文件: {result['ppt_output']['file_path']}")
print(f"总页数: {result['ppt_framework']['total_page']}")
```

### 2. 查看生成进度

```python
result = await graph.generate("创建一份PPT")

# 检查进度
print(f"当前阶段: {result['current_stage']}")
print(f"进度: {result['progress']}%")
```

### 3. 处理错误

```python
result = await graph.generate("创建一份PPT")

if result.get("error"):
    print(f"生成失败: {result['error']}")
    print(f"失败阶段: {result['current_stage']}")
else:
    print(f"生成成功: {result['ppt_output']['file_path']}")
```

## 🔧 单独使用各个 Agent

### 需求解析

```python
from agents_langchain.core.requirements import create_requirement_parser

agent = create_requirement_parser()
result = await agent.parse("生成一份关于AI的PPT，10页，学术风格")

print(f"主题: {result['ppt_topic']}")
print(f"页数: {result['page_num']}")
print(f"风格: {result['style_preference']}")
```

### 框架设计

```python
from agents_langchain.core.planning import create_framework_designer

agent = create_framework_designer()

requirement = {
    "ppt_topic": "人工智能概述",
    "page_num": 10,
    "need_research": True,
    "language": "ZH-CN"
}

framework = await agent.design(requirement)
print(f"总页数: {framework['total_page']}")
print(f"研究页面: {framework['research_page_indices']}")
```

### 页面研究

```python
from agents_langchain.core.research import create_research_agent

agent = create_research_agent()

page = {
    "page_no": 3,
    "title": "AI发展历史",
    "core_content": "介绍AI的发展历程",
    "keywords": ["AI", "历史", "发展"]
}

result = await agent.research_page(page)
print(f"研究内容: {result['research_content']}")
```

### 内容生成

```python
from agents_langchain.core.generation import create_content_agent

agent = create_content_agent()

page = {
    "page_no": 1,
    "title": "封面",
    "page_type": "cover",
    "is_need_image": True
}

result = await agent.generate_content_for_page(page, [])
print(f"内容: {result['content_text']}")
print(f"有配图: {result['has_image']}")
```

### PPT 渲染

```python
from agents_langchain.core.rendering import create_renderer_agent

agent = create_renderer_agent(output_dir="output")

result = await agent.render(
    framework=framework_dict,
    content_materials=content_list,
    requirement=requirement_dict,
    task_id="my_ppt"
)

print(f"文件路径: {result['file_path']}")
print(f"预览数据: {result['preview_data']}")
```

## 🔗 链式使用

### 完整流程

```python
from agents_langchain.core.requirements import create_requirement_parser
from agents_langchain.core.planning import create_framework_designer
from agents_langchain.core.research import create_research_agent
from agents_langchain.core.generation import create_content_agent
from agents_langchain.core.rendering import create_renderer_agent

# 1. 解析需求
requirement_agent = create_requirement_parser()
requirement = await requirement_agent.parse("创建AI介绍PPT，10页")

# 2. 设计框架
framework_agent = create_framework_designer()
framework = await framework_agent.design(requirement)

# 3. 研究页面（如果需要）
if framework['has_research_pages']:
    research_agent = create_research_agent()
    pages = framework['ppt_framework']
    research_results = await research_agent.research_all_pages(
        pages,
        framework['research_page_indices']
    )
else:
    research_results = []

# 4. 生成内容
content_agent = create_content_agent()
content_materials = await content_agent.generate_content_for_all_pages(
    framework['ppt_framework'],
    research_results
)

# 5. 渲染 PPT
renderer_agent = create_renderer_agent()
output = await renderer_agent.render(
    framework,
    content_materials,
    requirement,
    "my_ppt"
)

print(f"完成: {output['file_path']}")
```

## 📝 不同场景的输入

### 学术场景

```python
result = await graph.generate(
    user_input="生成一份关于深度学习的论文答辩PPT，15页，学术风格，需要参考资料"
)
```

### 商业场景

```python
result = await graph.generate(
    user_input="创建Q3销售报告商务演示，8页，包含图表和数据"
)
```

### 培训场景

```python
result = await graph.generate(
    user_input="制作Python编程培训课件，20页，包含代码示例和练习"
)
```

### 产品演示

```python
result = await graph.generate(
    user_input="新产品发布演示文稿，12页，突出核心功能和使用场景"
)
```

## 🔧 配置选项

### 使用自定义 LLM

```python
from langchain_openai import ChatOpenAI

# 创建自定义模型
model = ChatOpenAI(
    model="gpt-4o",
    temperature=0.0,
    api_key="your-api-key"
)

# 使用自定义模型
graph = create_master_graph(model=model)
```

### 配置并发数

```python
import os

# 设置环境变量
os.environ["PAGE_PIPELINE_CONCURRENCY"] = "5"

# 或直接配置
from agents_langchain.coordinator import create_page_pipeline

pipeline = create_page_pipeline(max_concurrency=5)
graph = create_master_graph(page_pipeline=pipeline)
```

### 配置输出目录

```python
from agents_langchain.core.rendering import create_renderer_agent

agent = create_renderer_agent(output_dir="./my_output")
```

## 🧪 测试运行

### 单元测试

```bash
cd backend/agents_langchain
python -m pytest tests/ -v
```

### 集成测试

```bash
cd backend/agents_langchain/tests
python test_integration.py
```

### 单独测试模块

```bash
# 测试需求解析
python -m agents_langchain.core.requirements.requirement_agent

# 测试框架设计
python -m agents_langchain.core.planning.framework_agent

# 测试研究
python -m agents_langchain.core.research.research_agent

# 测试内容生成
python -m agents_langchain.core.generation.content_agent

# 测试渲染
python -m agents_langchain.core.rendering.renderer_agent

# 测试主工作流
python -m agents_langchain.coordinator.master_graph
```

## 🔗 相关文档

- [advanced-usage.md](advanced-usage.md): 高级用法
- [../03-core-agents/](../03-core-agents/): 各 Agent 详细文档
- [../../README.md](../../README.md): 主文档
