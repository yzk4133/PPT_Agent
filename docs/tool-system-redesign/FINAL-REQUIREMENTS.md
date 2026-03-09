# MultiAgentPPT 工具系统需求文档

> 基于宁缺毋滥原则的最终工具配置方案

---

## 📋 文档信息

| 项目 | 内容 |
|------|------|
| **项目名称** | MultiAgentPPT |
| **文档版本** | v1.0 Final |
| **创建日期** | 2026-03-07 |
| **文档类型** | 工具系统需求文档 |
| **文档状态** | ✅ 已确认 |

---

## 🎯 设计原则

### 核心原则

1. **宁缺毋滥** - 只保留真正必要的工具
2. **职责清晰** - Tool vs MCP Tool vs MD Skill
3. **高度垂直** - 每个 Skill 专注一个领域
4. **易于扩展** - 统一接口，便于后续添加

### 三种工具对比

| 维度 | LangChain Tool | MCP Tool | MD Skill |
|------|---------------|----------|----------|
| **本质** | 本地Python函数 | 远程服务协议 | Markdown文档 |
| **实现方式** | `@tool`装饰器 | HTTP/stdio | YAML+MD |
| **调用方式** | `invoke()` | `invoke()` | 注入上下文 |
| **执行主体** | 本地代码 | 外部服务 | LLM参考 |
| **适用场景** | 核心业务逻辑 | 外部能力扩展 | 领域知识指导 |

---

## 📦 工具清单总览

### 数量统计

| 类型 | 数量 | 说明 |
|------|------|------|
| **MCP Tools** | 2个 | 远程能力（搜索、视觉） |
| **LangChain Tools** | 8个 | 本地核心能力 |
| **MD Skills** | 8-10个 | 领域知识库 |
| **总计** | 18-20个 | 精简配置 |

---

## 🔧 MCP Tools（2个）

### 1. zhipu_web_search

| 属性 | 值 |
|------|-----|
| **名称** | `zhipu_web_search` |
| **类型** | HTTP |
| **功能** | 高质量中文网络搜索 |
| **用途** | 搜索参考资料、数据、案例 |
| **优先级** | ⭐⭐⭐ 必须 |
| **API** | https://open.bigmodel.cn/api/mcp/web_search_prime/mcp |

**配置**
```yaml
zhipu-search:
  type: "http"
  url: "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp"
  headers:
    Authorization: "Bearer ${ZHIPU_API_KEY}"
```

**使用场景**
- 搜索PPT主题相关资料
- 查找案例和数据
- 获取行业报告
- 中文搜索优化

---

### 2. zai_vision

| 属性 | 值 |
|------|-----|
| **名称** | `zai_vision` |
| **类型** | stdio（本地子进程） |
| **功能** | 图片视觉理解 |
| **用途** | 图片内容分析、质量评估、图片选择 |
| **优先级** | ⭐⭐⭐ 必须 |
| **能力** | vision_understand, vision_ocr, vision_qa, vision_compare |

**配置**
```yaml
zai-vision:
  type: "stdio"
  command: "npx"
  args: ["-y", "@z_ai/mcp-server"]
  env:
    Z_AI_API_KEY: "${ZAI_API_KEY}"
    Z_AI_MODE: "ZHIPU"
```

**使用场景**
- 分析图片内容
- 选择合适的配图
- 提取图片中的文字
- 生成图片描述
- 评估图片质量

---

## 🛠️ LangChain 本地 Tools（8个）

### 搜索类

#### 1. search_images

| 属性 | 值 |
|------|-----|
| **名称** | `search_images` |
| **功能** | 搜索图片URL |
| **用途** | 获取候选图片 |
| **优先级** | ⭐⭐⭐ 必须 |

---

### 图片类

#### 2. download_image

| 属性 | 值 |
|------|-----|
| **名称** | `download_image` |
| **功能** | 下载图片到本地 |
| **用途** | 将图片URL保存为本地文件 |
| **优先级** | ⭐⭐⭐ 必须 |

#### 3. process_image

| 属性 | 值 |
|------|-----|
| **名称** | `process_image` |
| **功能** | 图片处理（调整大小、裁剪、格式转换） |
| **用途** | 适配PPT尺寸和格式 |
| **优先级** | ⭐⭐⭐ 必须 |

---

### 文件类

#### 4. read_template

| 属性 | 值 |
|------|-----|
| **名称** | `read_template` |
| **功能** | 读取PPT模板文件 |
| **用途** | 基于模板生成PPT |
| **优先级** | ⭐⭐⭐ 必须 |

#### 5. save_pptx

| 属性 | 值 |
|------|-----|
| **名称** | `save_pptx` |
| **功能** | 保存PPT到指定目录 |
| **用途** | 文件持久化 |
| **优先级** | ⭐⭐⭐ 必须 |

---

### 生成类

#### 6. create_pptx

| 属性 | 值 |
|------|-----|
| **名称** | `create_pptx` |
| **功能** | 生成PPT对象 |
| **用途** | 创建PPT文件结构 |
| **优先级** | ⭐⭐⭐ 必须 |

---

### 记忆类

#### 7. vector_search

| 属性 | 值 |
|------|-----|
| **名称** | `vector_search` |
| **功能** | 向量检索历史内容 |
| **用途** | 复用研究结果 |
| **优先级** | ⭐⭐ 推荐 |

---

### 质量类

#### 8. quality_check

| 属性 | 值 |
|------|-----|
| **名称** | `quality_check` |
| **功能** | 检查内容质量 |
| **用途** | 内容质量控制 |
| **优先级** | ⭐⭐⭐ 必须 |

---

## 📚 MD Skills（8-10个）

### 定位

**领域知识库** - 非"工作流"，而是"专业知识"

不是"怎么做"，而是"知道什么"——提供 PPT 生成相关的专业知识、规范、经验。

---

### 必备 Skills（8个）

#### 1. ppt_structure.md

| 属性 | 值 |
|------|-----|
| **名称** | `ppt_structure` |
| **领域** | PPT结构规范 |
| **内容** | 封面/内容/总结页标准、章节划分原则、页数与时长关系 |
| **推荐工具** | create_pptx, read_template |

**核心内容**
- 封面页设计规范
- 内容页设计规范
- 总结页设计规范
- 章节划分原则
- 页面数量与时长对应

---

#### 2. content_writing.md

| 属性 | 值 |
|------|-----|
| **名称** | `content_writing` |
| **领域** | 内容写作规范 |
| **内容** | 标题/要点/语言风格指南 |
| **推荐工具** | - |

**核心内容**
- 标题写作规范（5-15字）
- 要点提炼原则（平行结构、动词开头）
- 语言风格指南（专业/轻松/严谨）

---

#### 3. data_processing.md

| 属性 | 值 |
|------|-----|
| **名称** | `data_processing` |
| **领域** | 数据处理完整流程 |
| **内容** | 数据获取→清洗→分析→图表选择→可视化 |
| **推荐工具** | zhipu_web_search, vector_search |

**核心内容**
- **数据获取**：来源识别、搜索关键词
- **数据清洗**：格式统一、缺失值处理、异常值剔除
- **数据分析**：趋势/对比/占比分析
- **图表选择**：5种基础图表选择指南
  - 柱状图（数值比较）
  - 折线图（趋势变化）
  - 饼图（占比分布）
  - 条形图（排名展示）
  - 表格（精确数据）

---

#### 4. image_selection.md

| 属性 | 值 |
|------|-----|
| **名称** | `image_selection` |
| **领域** | 配图选择知识 |
| **内容** | 图片类型/质量标准/来源建议 |
| **推荐工具** | search_images, zai_vision |

**核心内容**
- 图片类型与场景匹配
- 图片质量标准
- 图片来源建议
- 版权注意事项

---

### 视觉风格 Skills（4个）

#### 5. business_style.md

| 属性 | 值 |
|------|-----|
| **名称** | `business_style` |
| **领域** | 商务风格设计 |
| **适用场景** | 商务汇报、项目提案、工作总结 |
| **配色** | 主色#1F4788（深蓝）、辅助#6B7280（灰）、强调#2563EB（亮蓝） |
| **字体** | 思源黑体 / 微软雅黑 |
| **推荐工具** | read_template, create_pptx |

**核心内容**
- 配色方案
- 字体规范
- 布局规范（左图右文/左文右图/上下布局）
- 图表设计
- 典型页面示例

---

#### 6. tech_style.md

| 属性 | 值 |
|------|-----|
| **名称** | `tech_style` |
| **领域** | 科技风格设计 |
| **适用场景** | 技术分享、产品发布、架构设计 |
| **配色** | 深色背景渐变、科技蓝#3B82F6、紫色#8B5CF6、青色#06B6D4 |
| **字体** | 思源黑体 / Inter / JetBrains Mono（代码） |
| **推荐工具** | read_template, create_pptx |

**核心内容**
- 深色模式配色
- 渐变使用
- 网格系统布局
- 发光效果
- 代码展示
- 架构图标

---

#### 7. academic_style.md

| 属性 | 值 |
|------|-----|
| **名称** | `academic_style` |
| **领域** | 学术风格设计 |
| **适用场景** | 学术报告、论文答辩、研究成果展示 |
| **配色** | 三原色、学术蓝#2C5282、灰色系 |
| **字体** | 宋体/思源宋体（中文）+ Times New Roman（英文） |
| **推荐工具** | read_template, create_pptx |

**核心内容**
- 配色方案
- 衬线字体使用
- 纵向排版
- 引用标注
- 数据严谨性

---

#### 8. creative_style.md

| 属性 | 值 |
|------|-----|
| **名称** | `creative_style` |
| **领域** | 创意风格设计 |
| **适用场景** | 创意分享、作品集、灵感展示 |
| **配色** | 鲜艳色彩、多色搭配、渐变色 |
| **字体** | 混合字体、手写字体点缀 |
| **推荐工具** | read_template, create_pptx |

**核心内容**
- 鲜艳配色方案
- 不规则布局
- 混合字体使用
- 装饰元素
- 动画效果

---

### 可选 Skills（0-2个）

#### 9. audience_adaptation.md（可选）

| 属性 | 值 |
|------|-----|
| **名称** | `audience_adaptation` |
| **领域** | 受众适配知识 |
| **内容** | 不同受众的特点和内容调整策略 |

**核心内容**
- 专家受众：深度专业、术语
- 普通受众：通俗易懂、举例
- 学生受众：循序渐进、详细

---

#### 10. quality_standards.md（可选）

| 属性 | 值 |
|------|-----|
| **名称** | `quality_standards` |
| **领域** | 质量评估标准 |
| **内容** | 内容/形式层面的评价维度 |

**核心内容**
- 内容质量：准确性、完整性、逻辑性
- 形式质量：美观性、一致性、可读性
- 常见缺陷和改进建议

---

## 📁 项目结构

```
backend/tools/
├── domain/
│   ├── search/
│   │   └── search_images_tool.py          # 图片搜索
│   ├── media/
│   │   ├── download_image_tool.py         # 图片下载
│   │   └── process_image_tool.py          # 图片处理
│   ├── utility/
│   │   ├── create_pptx_tool.py            # 生成PPT对象
│   │   ├── read_template_tool.py          # 读取模板
│   │   └── save_pptx_tool.py              # 保存PPT
│   ├── database/
│   │   └── vector_search_tool.py          # 向量检索
│   └── quality/
│       └── quality_check_tool.py          # 质量检查
├── mcp/
│   ├── zhipu_search_tool.py               # 智谱搜索（MCP）
│   └── zai_vision_tool.py                 # Zai视觉（MCP）
├── skills/
│   ├── ppt_structure.md                   # PPT结构规范
│   ├── content_writing.md                 # 内容写作规范
│   ├── data_processing.md                 # 数据处理流程
│   ├── image_selection.md                 # 配图选择知识
│   ├── business_style.md                  # 商务风格
│   ├── tech_style.md                      # 科技风格
│   ├── academic_style.md                  # 学术风格
│   ├── creative_style.md                  # 创意风格
│   ├── audience_adaptation.md             # 受众适配（可选）
│   └── quality_standards.md               # 质量标准（可选）
└── application/
    └── tool_registry.py                   # 工具注册中心

# 删除
python_skills/                              # 删除整个目录
```

---

## 🔄 完整工作流示例

```python
# PPT生成完整流程

# 1. 搜索资料
zhipu_search_tool.invoke(query="AI发展趋势", count=5)

# 2. 搜索图片
search_images_tool.invoke(query="AI技术概念图")

# 3. 分析图片
zai_vision_tool.invoke(
    tool_name="vision_understand",
    image_url="https://example.com/image.jpg"
)

# 4. 下载图片
download_image_tool.invoke(
    url="https://example.com/image.jpg",
    path="./temp/img1.jpg"
)

# 5. 处理图片
process_image_tool.invoke(
    input_path="./temp/img1.jpg",
    output_path="./temp/img1_resized.jpg",
    max_width=1920
)

# 6. 检索历史
vector_search_tool.invoke(query="类似主题的历史内容")

# 7. 读取模板
read_template_tool.invoke(path="./templates/business.pptx")

# 8. 生成PPT（注入MD Skill上下文）
# context注入: business_style.md + ppt_structure.md
create_pptx_tool.invoke(
    template=template_obj,
    content=content_data,
    images=["./temp/img1_resized.jpg"]
)

# 9. 质量检查
quality_check_tool.invoke(content=ppt_content)

# 10. 保存PPT
save_pptx_tool.invoke(
    ppt_obj=ppt_obj,
    path="./output/final.pptx"
)
```

---

## 📊 风格对比表

| 特征 | 商务 | 科技 | 学术 | 创意 |
|------|------|------|------|------|
| **背景** | 白色 | 深色+渐变 | 白色 | 多样 |
| **主色** | 深蓝 | 蓝紫渐变 | 三原色 | 鲜艳多彩 |
| **字体** | 黑体 | 无衬线+等宽 | 衬线 | 混合 |
| **布局** | 居中对齐 | 网格化 | 纵向排版 | 不规则 |
| **动画** | 简单 | 动态 | 无 | 丰富 |
| **场景** | 商务汇报 | 技术分享 | 学术报告 | 创意展示 |

---

## ✅ 验收标准

### 功能验收

- [ ] MCP Tools 可正常调用
- [ ] 所有 LangChain Tools 可正常执行
- [ ] MD Skills 可正确加载和解析
- [ ] Tool Registry 统一管理所有工具
- [ ] 完整的 PPT 生成流程可端到端执行

### 质量验收

- [ ] 每个 Tool 有清晰的文档注释
- [ ] 每个 MD Skill 有完整的 YAML frontmatter
- [ ] 所有工具通过单元测试
- [ ] 集成测试覆盖完整流程
- [ ] 代码符合 PEP8 规范

### 性能验收

| 指标 | 目标值 |
|------|--------|
| MCP 搜索响应时间 | < 3s |
| MCP 视觉分析时间 | < 5s |
| 本地 Tool 调用延迟 | < 100ms |
| 端到端 PPT 生成时间 | < 60s |

---

## 📅 实施计划

### Phase 1: MCP Tools（1天）
- [ ] 配置 zhipu_search_tool
- [ ] 配置 zai_vision_tool
- [ ] 测试 MCP 连接

### Phase 2: LangChain Tools（2天）
- [ ] 实现 search_images_tool
- [ ] 实现 download_image_tool
- [ ] 实现 process_image_tool
- [ ] 实现 read_template_tool
- [ ] 实现 save_pptx_tool
- [ ] 实现 create_pptx_tool
- [ ] 实现 vector_search_tool
- [ ] 实现 quality_check_tool

### Phase 3: MD Skills（2天）
- [ ] 编写 ppt_structure.md
- [ ] 编写 content_writing.md
- [ ] 编写 data_processing.md
- [ ] 编写 image_selection.md
- [ ] 编写 business_style.md
- [ ] 编写 tech_style.md
- [ ] 编写 academic_style.md
- [ ] 编写 creative_style.md
- [ ] 编写 audience_adaptation.md（可选）
- [ ] 编写 quality_standards.md（可选）

### Phase 4: 集成测试（1天）
- [ ] Tool Registry 实现
- [ ] 完整流程测试
- [ ] 性能优化
- [ ] 文档完善

**总预计时间**: 6天

---

## 📝 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2026-03-07 | 初始版本，基于宁缺毋滥原则确定最终配置 | System |

---

## 🔗 相关文档

- [工具系统需求](./REQUIREMENTS.md)
- [工具系统实施](./IMPLEMENTATION.md)
- [MCP集成文档](./mcp/REQUIREMENTS.md)
- [MCP配置指南](./mcp/API-GUIDE.md)

---

**文档状态**: ✅ 需求已确认，可以开始实施
