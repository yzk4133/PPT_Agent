# 记忆系统与多智能体架构集成方案

## 一、集成概述

### 1.1 现有多智能体架构

MultiAgentPPT采用「1主5子」架构：

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| **MasterCoordinatorAgent** | 主协调智能体 | 用户需求 | 调度子Agent，整合结果 |
| **RequirementParserAgent** | 需求解析 | 自然语言需求 | 结构化需求清单 |
| **FrameworkDesignerAgent** | 框架设计 | 需求清单 | PPT框架（页序+每页定义） |
| **ResearchAgent** | 资料研究 | PPT框架 | 研究结果包 |
| **ContentMaterialAgent** | 内容素材 | 框架+研究结果 | 内容+素材（文字+图表） |
| **TemplateRendererAgent** | 模板渲染 | 内容素材 | PPT文件 |

### 1.2 记忆系统定位

记忆系统作为多智能体架构的「智能数据层」，提供三大核心能力：

```
┌─────────────────────────────────────────────────────────────┐
│                    多智能体协作层                          │
│  MasterCoordinator ↔ 各子Agent（信息通过主Agent中转）     │
├─────────────────────────────────────────────────────────────┤
│              记忆系统（智能数据层）                         │
│  ┌───────────────┬─────────────────┬───────────────────┐    │
│  │ Agent决策记忆  │  共享工作空间   │  用户偏好记忆    │    │
│  │ 记录决策过程   │  Agent间数据共享  │  学习用户行为    │    │
│  └───────────────┴─────────────────┴───────────────────┘    │
│  ┌───────────────┬─────────────────┬───────────────────┐    │
│  │ 研究结果缓存   │  向量语义检索    │  生命周期管理    │    │
│  │ 避免重复研究   │  智能查找相关内容  │  自动归档清理    │    │
│  └───────────────┴─────────────────┴───────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                    存储层                                 │
│  L1(瞬时) + L2(短期) + L3(长期) + PostgreSQL + pgvector    │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、按Agent的记忆需求分析

### 2.1 MasterCoordinatorAgent（主协调智能体）

**记忆需求**：

| 记忆类型 | 具体内容 | 生命周期 | 存储层级 |
|---------|---------|----------|---------|
| **任务状态记忆** | 任务ID、当前阶段、各子Agent状态、进度信息 | 会话级（数小时） | L2 |
| **用户交互历史** | 用户需求、修订记录、反馈 | 长期（用户级） | L3 |
| **决策追踪** | 调度决策、容错触发、重试记录 | 长期（分析用） | L3 |
| **中间结果缓存** | 各阶段输出（需求、框架、研究结果等） | 会话级（任务结束清理） | L2 |

**记忆集成方案**：

```python
# 伪代码
class MasterCoordinatorAgent:
    def __init__(self):
        self.memory = get_global_memory_manager()
        self.decision_service = AgentDecisionService()
        self.shared_workspace = SharedWorkspaceService()

    async def start_task(self, user_input: str):
        # 1. 生成任务ID并记录
        task_id = self._generate_task_id()

        await self.memory.set(
            key=f"task:{task_id}:state",
            value={
                "task_id": task_id,
                "user_input": user_input,
                "status": "started",
                "current_stage": "requirement_parsing",
                "start_time": now().isoformat()
            },
            scope=MemoryScope.SESSION,
            scope_id=task_id,
            importance=0.9,  # 任务状态高优先级
            tags=["task_state", "coordination"]
        )

        # 2. 记录决策（为什么要调用需求解析Agent）
        await self.decision_service.record_decision(
            session_id=task_id,
            agent_name="MasterCoordinator",
            decision_type="task_dispatch",
            selected_action="dispatch_requirement_parser",
            context={"user_input": user_input},
            confidence_score=1.0
        )

    async def complete_stage(self, task_id: str, stage: str, result: dict):
        # 3. 更新任务进度
        task_state = await self.memory.get(
            key=f"task:{task_id}:state",
            scope=MemoryScope.SESSION,
            scope_id=task_id
        )
        state, metadata = task_state
        state["current_stage"] = f"{stage}_completed"
        state["last_update"] = now().isoformat()

        await self.memory.set(
            key=f"task:{task_id}:stage_{stage}",
            value=result,
            scope=MemoryScope.SESSION,
            scope_id=task_id,
            importance=0.8,
            tags=["stage_result", stage]
        )

        # 4. 共享到工作空间，供后续Agent使用
        await self.shared_workspace.share_data(
            session_id=task_id,
            data_type="stage_result",
            source_agent="MasterCoordinator",
            data_key=stage,
            data_content=result,
            ttl_minutes=120  # 2小时有效期
        )
```

---

### 2.2 RequirementParserAgent（需求解析智能体）

**记忆需求**：

| 记忆类型 | 具体内容 | 生命周期 | 存储层级 |
|---------|---------|----------|---------|
| **用户偏好学习** | 用户常用场景、模板类型、页数偏好、语言 | 长期（用户级） | L3 |
| **解析历史** | 历次解析结果、用户修正模式 | 长期（优化用） | L3 |
| **默认值模式** | 不同场景的默认值（商务/校园/产品） | 长期 | L3 |
| **解析失败案例** | 解析失败的用户输入、兜底方案 | 长期（改进用） | L3 |

**记忆集成方案**：

```python
# 伪代码
class RequirementParserAgent:
    def __init__(self):
        self.memory = get_global_memory_manager()
        self.user_pref_service = UserPreferenceService()

    async def parse_requirement(self, user_input: str, task_id: str):
        # 1. 检查用户历史偏好
        user_id = self._extract_user_id(task_id)
        user_preferences = await self.user_pref_service.get_user_preferences(user_id)

        # 2. 获取用户历史解析记录
        history_key = f"user:{user_id}:parse_history"
        parse_history = await self.memory.get(
            key=history_key,
            scope=MemoryScope.USER,
            scope_id=user_id
        )

        # 3. 基于历史优化解析
        if parse_history:
            # 知道用户过去常用"商务风模板"，优先解析
            pass

        # 4. 执行解析
        parsed_requirement = await self._parse_with_llm(user_input)

        # 5. 学习用户行为
        await self.user_pref_service.update_preferences(
            user_id=user_id,
            session_id=task_id,
            updates={
                "preferred_template": parsed_requirement.template_type,
                "preferred_page_num": parsed_requirement.page_num,
                "preferred_scene": parsed_requirement.scene
            }
        )

        # 6. 记录解析历史
        if parse_history:
            history[1], metadata = parse_history
            history.append({
                "timestamp": now().isoformat(),
                "user_input": user_input,
                "parsed_result": parsed_requirement.to_dict()
            })
            await self.memory.set(
                key=history_key,
                value=history,
                scope=MemoryScope.USER,
                scope_id=user_id,
                importance=0.5,
                tags=["parse_history"]
            )

        return parsed_requirement
```

**用户偏好学习具体场景**：

```python
# 用户多次使用"商务风"模板
第1次: "做一份商务汇报PPT" → 记录偏好商务模板
第2次: "做一个年度总结PPT" → 默认使用商务模板
第3次: "准备产品宣讲PPT" → 询问是否商务模板？
...

# 用户多次修改默认页数
第1次: 生成15页 → 用户未修改
第2次: 生成20页 → 用户改为15页 → 学习到偏好15页左右
第3次: 自动生成15页
```

---

### 2.3 FrameworkDesignerAgent（框架设计智能体）

**记忆需求**：

| 记忆类型 | 具体内容 | 生命周期 | 存储层级 |
|---------|---------|----------|---------|
| **行业框架模板** | 不同行业、场景的标准框架（电商/金融/教育） | 长期 | L3 |
| **页序设计模式** | 成功的页序设计案例 | 长期（学习用） | L3 |
| **模板适配经验** | 框架与模板的匹配效果 | 长期（优化用） | L3 |
| **设计历史** | 历次框架设计结果 | 长期（分析用） | L3 |

**记忆集成方案**：

```python
# 伪代码
class FrameworkDesignerAgent:
    def __init__(self):
        self.memory = get_global_memory_manager()
        self.vector_cache = get_vector_cache()

    async def design_framework(self, requirement: dict, task_id: str):
        industry = requirement.get("industry", "通用")
        scene = requirement.get("scene", "商务汇报")

        # 1. 检查是否有相似的历史框架（语义检索）
        framework_query = f"{industry} {scene} PPT框架"
        query_vector = await self.vector_cache.get_embedding(framework_query)

        similar_frameworks = await self.memory.semantic_search(
            query_embedding=query_vector,
            scope=MemoryScope.WORKSPACE,
            scope_id="framework_templates",
            limit=5,
            min_importance=0.6
        )

        # 2. 如果找到高相似度框架，复用
        if similar_frameworks and similar_frameworks[0][2] > 0.85:
            similar_framework_key = similar_frameworks[0][0]
            cached_framework = await self.memory.get(
                key=similar_framework_key,
                scope=MemoryScope.WORKSPACE,
                scope_id="framework_templates"
            )
            if cached_framework:
                # 复用并调整
                return await self._adapt_framework(cached_framework[0], requirement)

        # 3. 设计新框架
        new_framework = await self._design_with_llm(requirement)

        # 4. 存储为新模板（向量嵌入）
        await self.memory.set(
            key=f"framework:{task_id}",
            value=new_framework,
            scope=MemoryScope.WORKSPACE,
            scope_id="framework_templates",
            importance=0.7,
            tags=[industry, scene, "framework_template"]
        )

        # 5. 记录设计决策
        await self.decision_service.record_decision(
            session_id=task_id,
            agent_name="FrameworkDesigner",
            decision_type="framework_design",
            selected_action="create_new_framework",  # 或 "reuse_framework"
            context={
                "industry": industry,
                "scene": scene,
                "similar_frameworks_found": len(similar_frameworks)
            }
        )

        return new_framework
```

**行业框架模板示例**：

```python
# 存储在L3的框架模板
framework_templates = {
    "电商复盘": {
        "standard_pages": ["封面", "目录", "前言", "核心数据", "行业对比", "竞品分析", "问题总结", "优化策略", "总结"],
        "page_order": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "research_pages": [5, 6],  # 行业对比、竞品分析
        "data_pages": [4, 5, 6],   # 需要图表的页面
    },
    "校园答辩": {
        "standard_pages": ["封面", "研究背景", "文献综述", "研究方法", "实验结果", "分析讨论", "结论", "参考文献"],
        "page_order": [1, 2, 3, 4, 5, 6, 7, 8],
        "research_pages": [2, 3],
        "data_pages": [5],
    }
}
```

---

### 2.4 ResearchAgent（资料研究智能体） - 最重要

**记忆需求**：

| 记忆类型 | 具体内容 | 生命周期 | 存储层级 |
|---------|---------|----------|---------|
| **研究结果缓存** | 已研究过的主题、研究结果（关键！避免重复研究） | 长期（用户级） | L3 |
| **研究来源库** | 可信来源列表（艾瑞咨询、36氪等） | 长期 | L3 |
| **关键词索引** | 主题→研究结果的映射 | 长期 | L3 |
| **研究失败记录** | 未找到资料的主题 | 长期（避免重复尝试） | L3 |
| **跨任务共享** | 相似研究结果的复用 | 长期 | L3 |

**记忆集成方案**：

```python
# 伪代码
class ResearchAgent:
    def __init__(self):
        self.memory = get_global_memory_manager()
        self.shared_workspace = SharedWorkspaceService()
        self.vector_cache = get_vector_cache()

    async def research_page(self, page_info: dict, task_id: str):
        page_title = page_info.get("title", "")
        keywords = page_info.get("keywords", [])
        core_content = page_info.get("core_content", "")

        # 1. 检查是否已研究过（关键词+语义检索）
        research_key = f"research:{hash_keywords(keywords)}"

        cached_research = await self.memory.get(
            key=research_key,
            scope=MemoryScope.USER,
            scope_id="research_cache"  # 跨用户的缓存
        )

        if cached_research:
            result, metadata = cached_research
            # 检查是否过期（研究数据可能有时间限制）
            if self._is_research_still_valid(result):
                logger.info(f"Found cached research for: {page_title}")
                await self.decision_service.record_decision(
                    session_id=task_id,
                    agent_name="ResearchAgent",
                    decision_type="research_reuse",
                    selected_action="use_cached_research",
                    context={"cached_at": result["timestamp"]}
                )
                return result

        # 2. 检查共享工作空间（其他Agent可能已研究过）
        shared_key = f"research:{page_title}"
        shared_result = await self.shared_workspace.get_shared_data(
            session_id=task_id,
            data_key=shared_key,
            accessing_agent="ResearchAgent"
        )

        if shared_result:
            logger.info(f"Found shared research from other agent: {page_title}")
            return shared_result

        # 3. 执行新研究
        research_result = await self._perform_research(page_info)

        # 4. 缓存研究结果（重要！）
        await self.memory.set(
            key=research_key,
            value=research_result,
            scope=MemoryScope.USER,
            scope_id="research_cache",
            importance=0.8,  # 研究结果高价值
            tags=["research_result"] + keywords
        )

        # 5. 同时存储向量嵌入（语义检索）
        content_text = research_result["content"]
        content_embedding = await self.vector_cache.get_embedding(
            f"{page_title} {content_text[:200]}..."  # 标题+摘要
        )

        await self.memory.set(
            key=f"vector:{research_key}",
            value={
                "page_title": page_title,
                "content": research_result,
                "embedding": content_embedding
            },
            scope=MemoryScope.USER,
            scope_id="research_vectors",
            importance=0.6
        )

        # 6. 共享到工作空间（供ContentMaterialAgent使用）
        await self.shared_workspace.share_data(
            session_id=task_id,
            data_type="research_result",
            source_agent="ResearchAgent",
            data_key=page_title,
            data_content=research_result,
            ttl_minutes=120
        )

        return research_result

    async def _perform_research(self, page_info: dict) -> dict:
        """执行研究（调用工具）"""
        # ... 研究逻辑 ...

        # 记录研究决策
        await self.decision_service.record_decision(
            session_id=task_id,
            agent_name="ResearchAgent",
            decision_type="tool_selection",
            selected_action="use_document_search",  # 或其他工具
            context={"page_info": page_info},
            outcome="pending"
        )

        # 调用搜索工具
        search_result = await self.search_tool.search(query)

        # 更新决策结果
        await self.decision_service.update_decision_outcome(
            decision_id=...,
            outcome="success" if search_result else "failure",
            execution_time_ms=...,
            relevance_score=...
        )

        return search_result
```

**避免重复研究的关键机制**：

```
场景1: 用户研究"2025电商618数据"
├─ 第1次PPT生成: ResearchAgent研究并缓存
├─ 第2次PPT生成（同主题）: 直接从缓存读取，跳过研究
└─ 跨用户共享: 用户A研究后，用户B生成类似PPT时直接使用

场景2: 语义相似主题匹配
├─ 用户需求: "电商双11数据" → 语义匹配到 "电商618数据"
└─ 自动适配复用，提示用户: "找到相似研究资料，是否使用？"
```

---

### 2.5 ContentMaterialAgent（内容素材智能体）

**记忆需求**：

| 记忆类型 | 具体内容 | 生命周期 | 存储层级 |
|---------|---------|----------|---------|
| **内容模板** | 常用文案模板（开场白、总结语等） | 长期 | L3 |
| **图表类型偏好** | 不同场景的图表类型选择 | 长期（用户级） | L3 |
| **文字风格模式** | 不同用户/场景的文字风格 | 长期（用户级） | L3 |
| **素材复用** | 可复用的图表、配图 | 长期 | L3 |
| **生成历史** | 历次生成的内容（用于改进） | 长期 | L3 |

**记忆集成方案**：

```python
# 伪代码
class ContentMaterialAgent:
    def __init__(self):
        self.memory = get_global_memory_manager()
        self.shared_workspace = SharedWorkspaceService()

    async def generate_content(self, page_info: dict, task_id: str):
        page_no = page_info.get("page_no")

        # 1. 从共享工作空间获取研究结果
        research_key = page_info.get("title")
        research_result = await self.shared_workspace.get_shared_data(
            session_id=task_id,
            data_key=research_key,
            accessing_agent="ContentMaterialAgent"
        )

        # 2. 检查是否有可复用内容
        reusable_content = await self._find_reusable_content(page_info)
        if reusable_content:
            return await self._adapt_reusable_content(reusable_content, page_info)

        # 3. 生成新内容
        content = await self._generate_with_llm(page_info, research_result)

        # 4. 记录生成决策
        await self.decision_service.record_decision(
            session_id=task_id,
            agent_name="ContentMaterialAgent",
            decision_type="content_generation",
            selected_action="generate_with_llm",
            context={
                "page_no": page_no,
                "has_research": research_result is not None,
                "content_length": len(content)
            }
        )

        return content

    async def _find_reusable_content(self, page_info: dict):
        """查找可复用内容"""
        # 语义检索历史内容
        page_title = page_info.get("title")
        title_embedding = await self.vector_cache.get_embedding(page_title)

        similar_contents = await self.memory.semantic_search(
            query_embedding=title_embedding,
            scope=MemoryScope.WORKSPACE,
            scope_id="content_templates",
            limit=3,
            min_importance=0.7
        )

        return similar_contents
```

---

### 2.6 TemplateRendererAgent（模板渲染智能体）

**记忆需求**：

| 记忆类型 | 具体内容 | 生命周期 | 存储层级 |
|---------|---------|----------|---------|
| **模板文件缓存** | 已加载的模板文件 | 长期 | L2 |
| **渲染历史** | 历次渲染参数、效果 | 长期（优化用） | L3 |
| **用户修订记录** | 用户修改过的页面、修改内容 | 长期（用户级） | L3 |
| **渲染性能数据** | 渲染耗时、文件大小 | 长期（优化用） | L3 |

**记忆集成方案**：

```python
# 伪代码
class TemplateRendererAgent:
    def __init__(self):
        self.memory = get_global_memory_manager()

    async def render_ppt(self, content_material: dict, task_id: str):
        # 1. 检查用户修订历史
        user_revisions = await self.memory.get(
            key=f"user_revisions:{task_id}",
            scope=MemoryScope.SESSION,
            scope_id=task_id
        )

        # 2. 加载模板（带缓存）
        template_key = content_material.get("template_type")
        template = await self._load_template_with_cache(template_key)

        # 3. 执行渲染
        ppt_file = await self._render_to_ppt(content_material, template)

        # 4. 记录渲染决策
        await self.decision_service.record_decision(
            session_id=task_id,
            agent_name="TemplateRendererAgent",
            decision_type="ppt_render",
            selected_action=f"render_with_{template_type}",
            context={
                "total_pages": content_material.get("total_page"),
                "file_size": os.path.getsize(ppt_file)
            },
            outcome="success"
        )

        return ppt_file

    async def _load_template_with_cache(self, template_type: str):
        """加载模板（带缓存）"""
        cache_key = f"template_file:{template_type}"

        # 先查L1
        template = await self.memory.l1.get(cache_key, ...)
        if template:
            return template

        # 再查L2
        template = await self.memory.l2.get(cache_key, ...)
        if template:
            # 回写L1
            await self.memory.l1.set(cache_key, template, ...)
            return template

        # 加载并缓存
        template = await self._load_template_from_disk(template_type)
        await self.memory.l1.set(cache_key, template, ...)
        await self.memory.l2.set(cache_key, template, ...)

        return template
```

---

## 三、跨Agent数据共享机制

### 3.1 共享工作空间使用场景

```
任务: task_20250203_001

┌─────────────────────────────────────────────────────────┐
│  ResearchAgent 研究完成                                    │
│  → share_data(                                         │
│      data_key="2025电商618行业数据",                  │
│      data_content={...}                               │
│    )                                                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  ContentMaterialAgent 获取研究成果                      │
│  → get_shared_data(                                   │
│      data_key="2025电商618行业数据"                     │
│  )                                                      │
│  → 直接使用，无需重新研究                               │
└─────────────────────────────────────────────────────────┘
```

**数据共享的生命周期**：

```python
# 共享数据设置
await shared_workspace.share_data(
    session_id=task_id,
    data_type="research_result",
    source_agent="ResearchAgent",
    data_key="行业数据",
    data_content={...},
    ttl_minutes=60,              # 1小时后自动过期
    target_agents=["ContentMaterialAgent"]  # 仅对特定Agent可见
)
```

### 3.2 共享数据类型

| 数据类型 | 源Agent | 目标Agent | 示例 |
|---------|--------|----------|------|
| `research_result` | ResearchAgent | ContentMaterialAgent | 研究结果、数据、案例 |
| `framework` | FrameworkDesignerAgent | ContentMaterialAgent | PPT框架、页序 |
| `parsed_requirement` | RequirementParserAgent | 所有Agent | 结构化需求 |
| `content_draft` | ContentMaterialAgent | TemplateRendererAgent | 生成的内容素材 |
| `rendering_config` | TemplateRendererAgent | 所有Agent | 渲染配置 |

---

## 四、用户偏好学习机制

### 4.1 学习维度

| 学习维度 | 数据来源 | 记忆存储 | 应用场景 |
|---------|---------|---------|---------|
| **模板偏好** | 用户选择的模板类型 | L3用户偏好表 | 下次优先推荐 |
| **页数偏好** | 用户修改的页数 | L3用户偏好表 | 自动设置合理页数 |
| **语言偏好** | 用户语言选择 | L3用户偏好表 | 自动判断语言 |
| **风格偏好** | 用户选择的模板风格 | L3用户偏好表 | 匹配风格 |
| **修改行为** | 用户对内容的修改次数/类型 | L3满意度评分 | 优化生成质量 |

### 4.2 偏好学习流程

```
用户生成PPT
    ↓
[跟踪用户行为]
    ↓
┌─────────────────────────────────────────┐
│  记录:                                        │
│  - 初始选择: 商务风模板                    │
│  - 页数设置: 15页                          │
│  - 用户修改: 将第6页改为10页               │
│  - 用户反馈: "数据页太少"                  │
│  - 最终导出: 未修改直接导出                  │
└─────────────────────────────────────────┘
    ↓
[分析满意度]
    ↓
┌�─────────────────────────────────────────┐
│  满意度计算:                                  │
│  - 修改次数: 2次 → 中等满意度              │
│  - 导出未修改 → 高满意度                    │
│  - 数据页不足 → 低满意度                   │
└─────────────────────────────────────────┘
    ↓
[更新偏好]
    ↓
┌�─────────────────────────────────────────┐
│  更新偏好:                                    │
│  - 模板偏好: 商务风 +0.1                   │
│  - 页数偏好: 15页 +0.2                      │
│  - 数据页偏好: +0.3 (用户关注)               │
└─────────────────────────────────────────┘
```

### 4.3 偏好应用示例

```python
# 场景: 用户多次生成"电商复盘"PPT
# 第1次: 15页商务风
# 第2次: 12页商务风
# 第3次: 15页商务风

# 学习结果:
user_preference = {
    "preferred_template": "商务风",
    "preferred_page_num": 15,
    "preferred_scene": "电商复盘",
    "data_page_importance": 0.8,  # 用户关注数据页
    "chart_preference": "折线图"     # 用户偏好折线图展示趋势
}

# 下次生成时自动应用:
async def generate_with_learned_preferences(user_id: str, user_input: str):
    preference = await user_pref_service.get_user_preferences(user_id)

    # 生成时直接应用偏好
    requirement = {
        "template_type": preference.get("preferred_template", "商务风"),
        "page_num": preference.get("preferred_page_num", 15),
        ...
    }
```

---

## 五、Agent决策追踪与优化

### 5.1 决策记录内容

```python
# 决策记录示例
{
    "decision_id": "decision_20250203_001",
    "task_id": "task_20250203_001",
    "agent_name": "ResearchAgent",
    "decision_type": "tool_selection",  # 工具选择/子Agent路由/参数选择
    "context": {
        "page_info": {...},
        "available_tools": ["search", "database", "api"],
        "page_requirements": {...}
    },
    "selected_action": "use_document_search",  # 选择的结果
    "alternatives": ["database", "api"],
    "reasoning": "文档搜索最适合公开数据",
    "confidence_score": 0.9,  # 决策置信度
    "outcome": "success",  # success/failure/partial/timeout
    "execution_time_ms": 1500,
    "relevance_score": 0.85,  # 结果相关性
    "timestamp": "2025-02-03T10:30:00Z"
}
```

### 5.2 决策优化

**目标**: 通过分析历史决策，优化Agent行为

```python
# 决策分析
async def analyze_agent_performance(agent_name: str):
    decisions = await decision_service.get_agent_decisions(agent_name)

    # 工具使用统计
    tool_usage = {}
    for d in decisions:
        tool = d.get("selected_action")
        tool_usage[tool] = {
            "count": tool_usage.get(tool, {}).get("count", 0) + 1,
            "success_rate": calculate_success_rate(decisions, tool),
            "avg_time": calculate_avg_time(decisions, tool)
        }

    # 优化建议
    for tool, stats in tool_usage.items():
        if stats["success_rate"] < 0.5:
            print(f"工具 {tool} 成功率较低({stats['success_rate']:.0%})，考虑替换或优化")
        if stats["avg_time"] > 5000:
            print(f"工具 {tool} 响应慢({stats['avg_time']:.0f}ms)，考虑缓存或替换")
```

---

## 六、记忆存储策略总结

### 6.1 按Agent的存储需求汇总

| Agent | L1 (瞬时) | L2 (短期) | L3 (长期) |
|-------|----------|----------|----------|
| **MasterCoordinator** | 任务状态 | 中间结果 | 决策历史、用户交互 |
| **RequirementParser** | 解析过程 | 解析历史 | 用户偏好、失败案例 |
| **FrameworkDesigner** | 设计过程 | 设计历史 | 行业框架模板、页序模式 |
| **ResearchAgent** | 搜索过程 | 搜索结果 | **研究结果缓存**、来源库 |
| **ContentMaterial** | 生成过程 | 生成历史 | 内容模板、文字风格 |
| **TemplateRenderer** | 渲染过程 | 模板缓存 | 渲染历史、修订记录 |

### 6.2 按数据类型的存储策略

| 数据类型 | 示例 | 存储层级 | TTL | 提升条件 |
|---------|------|---------|-----|---------|
| **任务状态** | 当前任务进度、各Agent状态 | L2 | 任务结束 | 任务完成 |
| **中间结果** | 需求清单、框架、研究结果 | L2 | 任务结束 | 修订使用 |
| **研究结果** | 行业数据、案例、观点 | L3 | 永久 | 语义相似检索 |
| **用户偏好** | 模板、页数、语言 | L3 | 永久 | 跨会话使用 |
| **决策历史** | Agent决策、工具选择 | L3 | 永久 | 分析优化 |
| **内容模板** | 常用文案、开场白 | L3 | 永久 | 复用 |
| **框架模板** | 行业PPT框架 | L3 | 永久 | 语义检索 |

---

## 七、集成实施建议

### 7.1 阶段1: 基础集成（1周）

**目标**: 让所有Agent能够读写记忆系统

```python
# 为每个Agent添加记忆能力
class BaseAgentWithMemory:
    def __init__(self):
        self.memory = get_global_memory_manager()
        self.agent_name = self.__class__.__name__

    async def remember(self, key: str, value: any, importance: float = 0.5):
        """通用记忆方法"""
        await self.memory.set(
            key=f"{self.agent_name}:{key}",
            value=value,
            scope=MemoryScope.SESSION,
            scope_id=self.get_task_id(),
            importance=importance,
            tags=[self.agent_name]
        )

    async def recall(self, key: str) -> Optional[any]:
        """通用回忆方法"""
        result = await self.memory.get(
            key=f"{self.agent_name}:{key}",
            scope=MemoryScope.SESSION,
            scope_id=self.get_task_id()
        )
        return result[0] if result else None
```

### 7.2 阶段2: 研究Agent缓存（2周）

**目标**: 实现研究结果缓存，避免重复研究

1. 为ResearchAgent添加缓存检查
2. 实现研究结果向量化存储
3. 实现语义检索复用

### 7.3 阶段3: 用户偏好学习（2周）

**目标**: 学习用户行为，优化生成体验

1. 为RequirementParserAgent添加偏好学习
2. 实现修改行为追踪
3. 实现满意度评分

### 7.4 阶段4: 共享工作空间（1周）

**目标**: 实现跨Agent数据共享

1. 集成SharedWorkspaceService
2. 定义共享数据规范
3. 实现共享权限控制

---

## 八、数据流转示意图

```
用户输入
    ↓
┌──────────────────────────────────────────────┐
│  MasterCoordinatorAgent                        │
│  - 创建task_id                                │
│  - 记录任务状态到L2                           │
└──────────────────────────────────────────────┘
    ↓ 调度
┌──────────────────────────────────────────────┐
│  RequirementParserAgent                       │
│  - 检查用户历史偏好(L3)                       │
│  - 更新偏好记录                                │
│  - 记录解析历史(L3)                           │
└──────────────────────────────────────────────┘
    ↓ 输出
┌──────────────────────────────────────────────┐
│  FrameworkDesignerAgent                       │
│  - 语义检索相似框架(L3)                       │
│  - 复用或设计新框架                             │
│  - 存储为新模板(L3)                            │
└──────────────────────────────────────────────┘
    ↓ 输出
┌──────────────────────────────────────────────┐
│  ResearchAgent                                │
│  - 检查研究缓存(L3)                           │
│  - 执行研究                                    │
│  - 存储研究结果(L3) + 向量嵌入                 │
│  - 共享到工作空间(L2)                          │
└──────────────────────────────────────────────┘
    ↓ 输出
┌──────────────────────────────────────────────┐
│  ContentMaterialAgent                         │
│  - 从工作空间获取研究(L2)                      │
│  - 检查可复用内容(L3)                          │
│  - 生成内容+素材                               │
│  - 存储生成历史(L3)                             │
└──────────────────────────────────────────────┘
    ↓ 输出
┌──────────────────────────────────────────────┐
│  TemplateRendererAgent                       │
│  - 从工作空间获取素材(L2)                      │
│  - 渲染PPT                                     │
│  - 记录渲染历史(L3)                           │
└──────────────────────────────────────────────┘
```

---

## 九、记忆系统带来的核心价值

### 9.1 避免重复工作

```
场景: 用户连续两次生成"2025电商618复盘"PPT

无记忆系统:
├─ 第1次: ResearchAgent研究行业数据 → 30秒
├─ 第2次: ResearchAgent再次研究相同数据 → 30秒
└─ 总耗时: 60秒

有记忆系统:
├─ 第1次: ResearchAgent研究行业数据 → 30秒
│        → 存储到L3 + 向量嵌入
├─ 第2次: ResearchAgent检查缓存 → 命中 → 0.5秒
└─ 总耗时: 30.5秒，节省50%
```

### 9.2 智能适配

```
场景: 用户多次生成PPT后，系统自动学习偏好

第1次生成: 15页商务风
第2次生成: 12页商务风 → 用户改为15页
第3次生成: 自动生成15页商务风（已学习偏好）

满意度跟踪:
- 修改少 → 满意度高 → 提高该配置权重
- 修改多 → 满意度低 → 降低该配置权重
```

### 9.3 持续优化

```
通过分析Agent决策历史:
├─ 发现DocumentSearch成功率只有60%
├─ 优化搜索策略或替换工具
└─ 成功率提升到85%

通过分析用户反馈:
├─ 发现"数据页"是最关注的部分
├─ 自动增加数据页的详细程度
└─ 用户满意度提升
```

---

## 十、下一步行动

### 10.1 近期任务

1. **为所有Agent添加记忆Mixin基类** - 统一记忆接口
2. **实现ResearchAgent研究缓存** - 最高优先级，直接节省成本
3. **添加用户偏好追踪** - 提升用户体验
4. **集成共享工作空间** - 实现跨Agent数据共享

### 10.2 中期任务

1. **实现向量语义检索** - 智能复用框架和内容
2. **添加Agent决策分析** - 优化Agent行为
3. **实现满意度评分** - 学习用户反馈

### 10.3 长期任务

1. **自动优化Agent配置** - 基于决策历史自动调优
2. **跨用户知识共享** - 匿名共享有价值的研究结果
3. **预测性预加载** - 预测下一步需要的数据并预加载

---

这个集成方案将记忆系统作为多智能体架构的「智能数据层」，通过避免重复工作、学习用户偏好、优化决策过程，显著提升系统的效率和用户体验。
