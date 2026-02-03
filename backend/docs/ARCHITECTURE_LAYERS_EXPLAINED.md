# 后端分层架构详解：API、Service、Agent、Domain Model

## 🎯 核心问题：为什么需要这么多层？

### 一个真实的场景

用户通过前端发送请求：
```javascript
// 前端代码
fetch('/api/presentations', {
  method: 'POST',
  body: JSON.stringify({
    topic: "人工智能发展史",
    num_slides: 10,
    language: "zh-CN"
  })
})
```

这个请求需要经历哪些步骤？

---

## 📊 完整的请求流程

```
用户请求
   ↓
【API层】处理HTTP协议
   ↓
【Service层】编排业务流程
   ↓
【Agent层】执行具体任务
   ↓
【Domain Model】数据和规则
   ↓
【Infrastructure】技术实现（LLM、DB等）
```

---

## 🔍 逐层解析

### 第1层：API层（门面）

**职责：** 处理HTTP相关的事情

**关注点：**
- ✅ 接收HTTP请求
- ✅ 解析请求参数（JSON、Query、Path）
- ✅ 验证参数格式
- ✅ 调用Service
- ✅ 返回HTTP响应（JSON、状态码）
- ✅ 处理HTTP错误（404、500等）

**不关注：**
- ❌ 业务逻辑
- ❌ 如何生成PPT
- ❌ LLM调用
- ❌ 数据库操作

**代码示例：**

```python
# api/routes/presentation.py

from fastapi import APIRouter, HTTPException
from api.schemas.requests import GeneratePresentationRequest
from api.schemas.responses import PresentationResponse
from services.presentation_service import PresentationService

router = APIRouter(prefix="/api/presentations", tags=["presentations"])

@router.post("/", response_model=PresentationResponse, status_code=201)
async def generate_presentation(
    request: GeneratePresentationRequest  # 👈 API层的职责：解析HTTP请求
) -> PresentationResponse:  # 👈 API层的职责：返回HTTP响应
    """
    生成PPT

    API层的职责：
    1. 接收HTTP请求
    2. 验证参数格式（topic不能为空，num_slides在1-50之间）
    3. 调用Service层
    4. 返回HTTP响应
    """

    try:
        # 🔄 调用Service层（委托业务逻辑）
        service = PresentationService()
        presentation = await service.generate(
            topic=request.topic,           # 👈 传递参数
            num_slides=request.num_slides,
            user_id=request.user_id
        )

        # 🔄 将领域模型转换为API响应模型
        return PresentationResponse.from_domain(presentation)

    except ValueError as e:
        # 🔄 处理业务错误
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # 🔄 处理系统错误
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{presentation_id}", response_model=PresentationResponse)
async def get_presentation(presentation_id: str):
    """获取已生成的PPT"""

    # API层的职责：从HTTP路径提取参数
    service = PresentationService()
    presentation = await service.get(presentation_id)

    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    return PresentationResponse.from_domain(presentation)
```

**为什么需要API层？**

1. **解耦**：HTTP框架变化不影响业务逻辑
2. **复用**：同一个Service可以被HTTP、CLI、gRPC调用
3. **测试**：可以单独测试HTTP接口
4. **文档**：自动生成API文档（OpenAPI/Swagger）

---

### 第2层：Service层（指挥官）

**职责：** 编排业务流程

**关注点：**
- ✅ 协调多个Agent
- ✅ 管理事务（开始→提交/回滚）
- ✅ 流程控制（顺序、并行、循环）
- ✅ 错误处理和重试
- ✅ 业务规则编排

**不关注：**
- ❌ HTTP请求/响应
- ❌ 如何调用LLM（Agent的事）
- ❌ 数据格式转换

**代码示例：**

```python
# services/presentation_service.py

class PresentationService:
    """
    PPT生成服务

    Service层的职责：
    1. 编排整个生成流程
    2. 协调多个Agent
    3. 管理事务和错误
    """

    def __init__(self):
        # 🔄 注入依赖（不是直接new，而是依赖注入）
        self.llm = LLMFactory.create()
        self.memory = SessionService()
        self.db = DatabaseService()

    async def generate(
        self,
        topic: str,
        num_slides: int,
        user_id: str
    ) -> Presentation:
        """
        生成PPT的完整业务流程

        这是Service层的核心：编排！
        """

        # === 步骤1：创建会话 ===
        session = await self.memory.create_session(user_id)
        logger.info(f"Created session: {session.id}")

        try:
            # === 步骤2：规划阶段（调用Agent）===
            outline_agent = OutlineAgent(self.llm, self.memory)
            outline = await outline_agent.create_outline(
                topic=topic,
                num_slides=num_slides,
                session_id=session.id
            )

            # 🔄 Service层的决策：如果大纲质量不好，提前终止
            if not outline.is_valid():
                raise ValueError("Generated outline is not valid")

            # === 步骤3：研究阶段（并行调用多个Agent）===
            research_agent = ParallelResearchAgent(self.llm, self.tools)
            research_results = await research_agent.research_all_topics(
                outline.topics,
                session_id=session.id
            )

            # === 步骤4：生成阶段（循环调用Agent）===
            presentation = Presentation(id=generate_id(), topic=topic)
            writer_agent = SlideWriterAgent(self.llm, self.memory)
            checker_agent = QualityCheckerAgent(self.llm)

            for i, slide_topic in enumerate(outline.topics):
                # 🔄 Service层的编排：生成→检查→重试
                for attempt in range(3):
                    slide = await writer_agent.write_slide(
                        topic=slide_topic,
                        research_data=research_results[i],
                        previous_slides=presentation.slides
                    )

                    # 调用检查Agent
                    is_valid = await checker_agent.check(slide)
                    if is_valid:
                        break

                # 🔄 Service层的业务规则：添加到PPT
                presentation.add_slide(slide)

                # 🔄 Service层的用户体验：实时更新进度
                await self.memory.update_progress(
                    session.id,
                    progress=(i + 1) / num_slides * 100
                )

            # === 步骤5：保存结果 ===
            await self.db.save_presentation(presentation)
            await self.memory.complete_session(session.id)

            return presentation

        except Exception as e:
            # 🔄 Service层的事务：出错时回滚
            logger.error(f"Failed to generate presentation: {e}")
            await self.memory.fail_session(session.id, error=str(e))
            raise
```

**为什么需要Service层？**

1. **编排复杂流程**：生成PPT需要规划→研究→生成→检查，多个步骤
2. **事务管理**：所有步骤要么全成功，要么全回滚
3. **协调Agent**：多个Agent协同工作
4. **业务规则**：重试、降级、超时等
5. **可测试性**：可以mock Agent测试Service

**如果没有Service层会怎样？**

```python
# ❌ 不好的设计：在API层直接调用Agent
@router.post("/")
async def generate_presentation(request):
    # API层不应该包含这么多业务逻辑！

    # 创建Agent
    outline_agent = OutlineAgent(...)
    research_agent = ResearchAgent(...)
    writer_agent = SlideWriterAgent(...)
    checker_agent = QualityCheckerAgent(...)

    # 编排流程
    outline = await outline_agent.create_outline(...)
    research = await research_agent.research(...)

    presentation = Presentation(...)
    for topic in outline.topics:
        slide = await writer_agent.write_slide(...)
        is_valid = await checker_agent.check(slide)
        presentation.add_slide(slide)

    # 问题：
    # 1. API层太重
    # 2. 无法复用（CLI怎么用？）
    # 3. 难以测试
    # 4. 职责混乱
```

---

### 第3层：Agent层（工人）

**职责：** 执行具体任务

**关注点：**
- ✅ 调用LLM
- ✅ 使用工具（搜索、数据库）
- ✅ 决策和推理
- ✅ 处理具体任务

**不关注：**
- ❌ HTTP请求/响应
- ❌ 整体流程编排
- ❌ 事务管理

**代码示例：**

```python
# agents/planning/outline_agent.py

class OutlineAgent(BaseAgent):
    """
    大纲生成Agent

    Agent层的职责：
    1. 调用LLM
    2. 做决策（推理、重试）
    3. 返回结果
    """

    async def create_outline(
        self,
        topic: str,
        num_slides: int,
        session_id: str
    ) -> Outline:
        """
        生成PPT大纲

        Agent只负责这一件事！
        """

        # 🔄 Agent的决策：构建合适的Prompt
        system_prompt = "你是专业的PPT大纲规划师..."
        user_prompt = f"""
        请为以下主题生成PPT大纲：
        主题：{topic}
        页数：{num_slides}

        要求：
        1. 每页有明确的标题
        2. 逻辑连贯
        3. 结构清晰
        """

        # 🔄 Agent的工作：调用LLM
        for attempt in range(3):
            response = await self.llm.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            # 🔄 Agent的决策：验证和重试
            outline = self._parse_outline(response)

            if outline.is_valid():
                # 保存到记忆
                await self.memory.save_outline(session_id, outline)
                return outline
            else:
                # 质量不好，重试
                logger.warning(f"Outline quality low, retrying... ({attempt+1}/3)")
                user_prompt += f"\n\n上次结果不够好，请改进：{outline}"

        # 🔄 Agent的失败处理
        raise AgentExecutionError("Failed to generate valid outline after 3 attempts")

    def _parse_outline(self, response: str) -> Outline:
        """Agent的工具函数：解析LLM响应"""
        # 解析JSON/Markdown
        # 验证格式
        # 返回Outline对象
        pass
```

**为什么需要Agent层？**

1. **封装AI能力**：LLM调用、推理、重试逻辑
2. **可复用**：同一个Agent可以在不同Service中使用
3. **可测试**：可以mock LLM测试Agent
4. **可替换**：可以从GPT-4换成Claude，不影响Service

---

### 第4层：Domain Model（蓝图）

**职责：** 定义数据和业务规则

**关注点：**
- ✅ 数据结构
- ✅ 业务规则（验证、计算）
- ✅ 不变性

**不关注：**
- ❌ 如何被创建（Agent或用户都可以）
- ❌ 如何被保存（数据库或文件）
- ❌ HTTP/JSON格式

**代码示例：**

```python
# core/models/presentation.py

@dataclass
class Presentation:
    """PPT领域模型"""

    # === 数据 ===
    id: str
    topic: str
    slides: List[Slide]
    created_at: datetime
    status: PresentationStatus

    # === 业务规则（常量）===
    MIN_SLIDES: int = 1
    MAX_SLIDES: int = 50
    MIN_TITLE_LENGTH: int = 5
    MAX_TITLE_LENGTH: int = 100

    # === 业务规则（方法）===
    def add_slide(self, slide: Slide) -> None:
        """添加幻灯片（包含业务规则）"""
        if len(self.slides) >= self.MAX_SLIDES:
            raise ValueError(f"Cannot exceed {self.MAX_SLIDES} slides")

        if slide.page_number != len(self.slides) + 1:
            raise ValueError("Slide page number mismatch")

        self.slides.append(slide)

    def validate(self) -> bool:
        """验证PPT完整性"""
        return (
            self.MIN_SLIDES <= len(self.slides) <= self.MAX_SLIDES and
            self.MIN_TITLE_LENGTH <= len(self.topic) <= self.MAX_TITLE_LENGTH and
            all(slide.is_valid() for slide in self.slides)
        )

    def get_duration(self) -> int:
        """计算总时长（派生属性）"""
        return sum(slide.duration_minutes for slide in self.slides)

    # === 没有以下内容 ===
    # ❌ save_to_database()      # 这是Infrastructure的事
    # ❌ call_llm_to_generate()   # 这是Agent的事
    # ❌ to_json()                # 这是API层的事
```

**为什么需要Domain Model？**

1. **业务规则集中**：验证、计算逻辑都在这里
2. **类型安全**：编译时检查，减少bug
3. **易于理解**：看到类就知道有哪些数据
4. **框架无关**：不依赖FastAPI、Pydantic等

---

### 第5层：Infrastructure（工具）

**职责：** 技术实现细节

**包含：**
- LLM客户端（OpenAI、Claude）
- 数据库（PostgreSQL、Redis）
- 文件系统
- 外部API

**代码示例：**

```python
# infrastructure/llm/openai_client.py

class OpenAIClient:
    """OpenAI LLM客户端"""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key)

    async def generate(self, prompt: str) -> str:
        """调用OpenAI API"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMException(f"OpenAI API error: {e}")
```

---

## 🔄 完整的请求流程示例

### 用户请求：生成一个关于"AI发展史"的PPT

```
┌─────────────────────────────────────────────────────────────┐
│ 1️⃣ 用户发送HTTP请求                                          │
│    POST /api/presentations                                    │
│    { "topic": "AI发展史", "num_slides": 10 }                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2️⃣ API层接收请求                                             │
│    - 解析JSON                                                 │
│    - 验证参数（topic不能为空）                                 │
│    - 调用Service                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3️⃣ Service层编排流程                                         │
│    ① 创建会话                                                 │
│    ② 调用OutlineAgent生成大纲                                 │
│    ③ 调用ResearchAgent研究资料                                │
│    ④ 循环调用WriterAgent生成幻灯片                            │
│    ⑤ 保存到数据库                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4️⃣ Agent层执行任务（以OutlineAgent为例）                       │
│    - 构建Prompt                                               │
│    - 调用LLM                                                  │
│    - 解析响应                                                 │
│    - 验证质量                                                 │
│    - 返回Outline对象                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5️⃣ Domain Model（Outline对象）                               │
│    - 包含数据：topics, title, structure                      │
│    - 包含方法：validate(), get_duration()                    │
│    - 被Agent创建，被Service使用                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6️⃣ Infrastructure（LLM客户端）                                │
│    - 调用OpenAI API                                           │
│    - 处理网络请求                                             │
│    - 返回文本                                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7️⃣ 返回响应                                                   │
│    - Agent → Service → API                                   │
│    - API转换为JSON                                           │
│    - 返回HTTP响应                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 各层的依赖关系

```
┌─────────────────────────────────────────┐
│           API Layer                      │
│  (处理HTTP，调用Service)                 │
└──────────────┬──────────────────────────┘
               │ 依赖
               ▼
┌─────────────────────────────────────────┐
│         Service Layer                    │
│  (编排流程，调用Agent)                    │
└──────────────┬──────────────────────────┘
               │ 依赖
               ▼
┌─────────────────────────────────────────┐
│          Agent Layer                     │
│  (执行任务，调用LLM/Tools)               │
└──────────────┬──────────────────────────┘
               │ 依赖
               ▼
┌─────────────────────────────────────────┐
│       Domain Model + Infrastructure       │
│  (数据和规则 + 技术实现)                  │
└─────────────────────────────────────────┘
```

**关键原则：**
- ✅ 单向依赖（上层依赖下层）
- ✅ 下层不知道上层的存在
- ✅ 可以替换任何层的实现

---

## 💡 为什么不能合并层？

### 问题：能不能把API和Service合并？

```python
# ❌ 不好的设计：合并API和Service
@router.post("/")
async def generate_presentation(request):
    # API逻辑
    topic = request.topic

    # Service逻辑（混在一起！）
    session = await create_session()
    outline = await outline_agent.create_outline(topic)
    research = await research_agent.research(outline)
    for i in range(10):
        slide = await writer_agent.write_slide(...)
        presentation.add_slide(slide)
    await db.save(presentation)

    # API逻辑
    return JSONResponse(presentation.to_dict())
```

**问题：**
1. ❌ 职责混乱：一个函数做太多事
2. ❌ 难以测试：怎么测试业务逻辑？
3. ❌ 无法复用：CLI、测试脚本怎么用？
4. ❌ 难以维护：修改业务逻辑要改API代码

### 问题：能不能把Service和Agent合并？

```python
# ❌ 不好的设计：在Agent里编排流程
class PresentationAgent(BaseAgent):
    async def generate_presentation(self, topic):
        # Agent不应该负责编排！
        outline = await self.create_outline(topic)
        research = await self.research(outline)

        presentation = Presentation()
        for slide_topic in outline.topics:
            slide = await self.write_slide(slide_topic)
            presentation.add_slide(slide)

        return presentation
```

**问题：**
1. ❌ Agent太重：包含太多逻辑
2. ❌ 难以复用：其他Service也想用这个Agent怎么办？
3. ❌ 难以测试：无法单独测试Agent
4. ❌ 违反单一职责：Agent应该只做一件事

---

## 📊 对比不同架构

### 单体架构（无分层）

```
┌─────────────────┐
│  所有代码在一起  │
│  - HTTP处理     │
│  - 业务逻辑     │
│  - LLM调用      │
│  - 数据验证     │
└─────────────────┘
```

**优点：** 简单，快速开始
**缺点：** 难以维护、测试、复用

### 分层架构（推荐）

```
┌─────────────┐
│  API层      │  ← HTTP接口
├─────────────┤
│  Service层  │  ← 业务编排
├─────────────┤
│  Agent层    │  ← AI能力
├─────────────┤
│  Domain层   │  ← 数据规则
├─────────────┤
│  Infra层    │  ← 技术实现
└─────────────┘
```

**优点：** 清晰、可维护、可测试、可复用
**缺点：** 需要更多文件、初期开发稍慢

---

## 🎓 总结

### 一句话概括每层

| 层 | 职责 | 一句话 |
|---|------|--------|
| **API** | 门面 | "接收HTTP请求，返回HTTP响应" |
| **Service** | 指挥官 | "编排流程，协调Agent" |
| **Agent** | 工人 | "调用LLM，执行具体任务" |
| **Domain Model** | 蓝图 | "定义数据和业务规则" |
| **Infrastructure** | 工具 | "提供技术能力（LLM、DB）" |

### 类比：餐厅

```
API层 = 服务员
  - 接收顾客订单
  - 端菜给顾客
  - 不关心怎么做的菜

Service层 = 厨师长
  - 安排做菜顺序
  - 协调多个厨师
  - 确保菜品质量

Agent层 = 厨师
  - 炒菜、切菜、煮汤
  - 使用厨具（Infrastructure）
  - 按照菜谱（Domain Model）

Domain Model = 菜谱
  - 定义菜品是什么
  - 包含用料和做法

Infrastructure = 厨具
  - 锅、铲、刀、灶
  - 提供技术能力
```

### 核心原则

1. **单一职责**：每层只做一件事
2. **单向依赖**：上层依赖下层
3. **低耦合**：可以替换任何层的实现
4. **高内聚**：相关的代码放在一起

你现在理解各层的关系了吗？如果还有疑问，我可以进一步解释！
