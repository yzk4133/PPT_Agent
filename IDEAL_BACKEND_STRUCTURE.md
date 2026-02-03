# 理想的后端目录结构设计

## 🎯 核心原则

### 清晰的职责分离
每个目录/模块都有明确的单一职责

### 避免代码重复
通过共享组件和抽象避免重复代码

### 易于扩展
新功能可以快速添加，不影响现有代码

### 便于测试
每个模块都可以独立测试

### 微服务就绪
模块间低耦合，可以轻松拆分为独立服务

---

## 📁 理想目录结构

```
backend/
├── core/                          # 🔵 核心层：领域模型和业务逻辑
│   ├── __init__.py
│   ├── models/                    # 数据模型
│   │   ├── __init__.py
│   │   ├── presentation.py        # PPT领域模型
│   │   ├── slide.py               # 幻灯片模型
│   │   ├── outline.py             # 大纲模型
│   │   └── research.py            # 研究数据模型
│   │
│   ├── interfaces/                # 接口定义（抽象基类）
│   │   ├── __init__.py
│   │   ├── agent.py               # Agent接口
│   │   ├── memory.py              # 记忆系统接口
│   │   ├── tool.py                # 工具接口
│   │   └── llm.py                 # LLM客户端接口
│   │
│   └── services/                  # 核心业务服务
│       ├── __init__.py
│       ├── planning_service.py    # 规划服务
│       ├── research_service.py    # 研究服务
│       ├── generation_service.py  # 生成服务
│       └── quality_service.py     # 质量检查服务
│
├── agents/                        # 🤖 Agent层：具体的Agent实现
│   ├── __init__.py
│   ├── base/                      # Agent基类
│   │   ├── __init__.py
│   │   ├── base_agent.py          # 所有Agent的基类
│   │   ├── sequential_agent.py    # 顺序执行Agent
│   │   ├── parallel_agent.py      # 并行执行Agent
│   │   └── loop_agent.py          # 循环Agent
│   │
│   ├── planning/                  # 规划Agent
│   │   ├── __init__.py
│   │   ├── outline_agent.py       # 大纲生成Agent
│   │   ├── topic_splitter_agent.py # 主题拆分Agent
│   │   └── prompt.py              # Prompt模板
│   │
│   ├── research/                  # 研究Agent
│   │   ├── __init__.py
│   │   ├── researcher_agent.py    # 单个研究Agent
│   │   ├── parallel_researcher.py # 并行研究协调器
│   │   └── prompt.py
│   │
│   └── generation/                # 生成Agent
│       ├── __init__.py
│       ├── slide_writer_agent.py  # 幻灯片写入Agent
│       ├── slide_checker_agent.py # 幻灯片检查Agent
│       ├── ppt_assembler.py       # PPT组装器
│       └── prompt.py
│
├── memory/                        # 🧠 记忆系统：持久化和缓存
│   ├── __init__.py
│   ├── interfaces/                # 记忆接口
│   │   ├── __init__.py
│   │   ├── imemory.py             # 记忆抽象接口
│   │   └── isession.py            # 会话抽象接口
│   │
│   ├── implementations/           # 具体实现
│   │   ├── __init__.py
│   │   ├── persistent_memory.py   # PostgreSQL持久化
│   │   ├── cache_memory.py        # Redis缓存
│   │   ├── vector_memory.py       # 向量存储（pgvector）
│   │   └── in_memory_memory.py    # 内存实现（开发/测试）
│   │
│   ├── services/                  # 记忆服务
│   │   ├── __init__.py
│   │   ├── session_service.py     # 会话管理
│   │   ├── preference_service.py  # 用户偏好
│   │   └── semantic_search.py     # 语义检索
│   │
│   └── utils/                     # 记忆工具
│       ├── __init__.py
│       ├── compressor.py          # 上下文压缩
│       └── deduplicator.py        # 去重工具
│
├── tools/                         # 🔧 工具层：可复用的工具函数
│   ├── __init__.py
│   ├── search/                    # 搜索工具
│   │   ├── __init__.py
│   │   ├── web_search.py          # 网页搜索
│   │   ├── document_search.py     # 文档搜索
│   │   └── semantic_search.py     # 向量搜索
│   │
│   ├── media/                     # 媒体工具
│   │   ├── __init__.py
│   │   ├── image_search.py        # 图片搜索
│   │   ├── image_processor.py     # 图片处理
│   │   └── video_processor.py     # 视频处理（可选）
│   │
│   ├── file/                      # 文件工具
│   │   ├── __init__.py
│   │   ├── ppt_exporter.py        # PPT导出
│   │   ├── pdf_exporter.py        # PDF导出
│   │   └── file_manager.py        # 文件管理
│   │
│   └── mcp/                       # MCP工具集成
│       ├── __init__.py
│       ├── mcp_client.py          # MCP客户端
│       └── tools/                 # MCP工具集合
│           ├── __init__.py
│           └── ...
│
├── infrastructure/                # 🏗️ 基础设施层：技术实现细节
│   ├── __init__.py
│   ├── llm/                       # LLM客户端
│   │   ├── __init__.py
│   │   ├── base.py                # LLM抽象基类
│   │   ├── openai_client.py       # OpenAI实现
│   │   ├── anthropic_client.py    # Anthropic实现
│   │   ├── together_client.py     # Together AI实现
│   │   ├── factory.py             # LLM工厂
│   │   └── fallback.py            # 降级策略
│   │
│   ├── database/                  # 数据库
│   │   ├── __init__.py
│   │   ├── postgres.py            # PostgreSQL连接
│   │   ├── redis.py               # Redis连接
│   │   ├── repositories.py        # 数据仓储
│   │   └── migrations/            # 数据库迁移
│   │
│   ├── config/                    # 配置管理
│   │   ├── __init__.py
│   │   ├── settings.py            # 配置定义
│   │   ├── loader.py              # 配置加载器
│   │   └── validators.py          # 配置验证
│   │
│   ├── logging/                   # 日志系统
│   │   ├── __init__.py
│   │   ├── logger.py              # 日志配置
│   │   └── formatters.py          # 日志格式化
│   │
│   └── monitoring/                # 监控和指标
│       ├── __init__.py
│       ├── metrics.py             # 性能指标
│       ├── tracing.py             # 链路追踪
│       └── health.py              # 健康检查
│
├── api/                           # 🌐 API层：对外接口
│   ├── __init__.py
│   ├── routes/                    # 路由定义
│   │   ├── __init__.py
│   │   ├── presentation.py        # PPT生成API
│   │   ├── outline.py             # 大纲生成API
│   │   ├── health.py              # 健康检查API
│   │   └── admin.py               # 管理API（可选）
│   │
│   ├── schemas/                   # API数据模型
│   │   ├── __init__.py
│   │   ├── requests.py            # 请求模型
│   │   ├── responses.py           # 响应模型
│   │   └── errors.py              # 错误模型
│   │
│   ├── middleware/                # 中间件
│   │   ├── __init__.py
│   │   ├── auth.py                # 认证中间件（可选）
│   │   ├── cors.py                # CORS处理
│   │   ├── rate_limit.py          # 速率限制（可选）
│   │   └── logging.py             # 请求日志
│   │
│   └── server.py                  # API服务器启动
│
├── services/                      # 📦 服务层：组合各层完成业务流程
│   ├── __init__.py
│   ├── presentation_service.py    # PPT生成服务（主服务）
│   ├── outline_service.py         # 大纲生成服务
│   ├── export_service.py          # 导出服务
│   └── coordination_service.py    # 多Agent协调服务
│
├── tests/                         # 🧪 测试层
│   ├── __init__.py
│   ├── unit/                      # 单元测试
│   │   ├── test_agents.py
│   │   ├── test_memory.py
│   │   ├── test_tools.py
│   │   └── test_services.py
│   │
│   ├── integration/               # 集成测试
│   │   ├── test_ppt_generation.py
│   │   ├── test_outline_generation.py
│   │   └── test_end_to_end.py
│   │
│   ├── fixtures/                  # 测试数据
│   │   ├── mock_slides.py
│   │   ├── mock_research.py
│   │   └── sample_data.py
│   │
│   └── utils/                     # 测试工具
│       ├── __init__.py
│       ├── assertions.py
│       └── helpers.py
│
├── scripts/                       # 📜 脚本：工具和维护脚本
│   ├── init_db.py                 # 初始化数据库
│   ├── migrate.py                 # 数据库迁移
│   ├── benchmark.py               # 性能测试
│   ├── cleanup.py                 # 清理脚本
│   └── export_demo.py             # 导出示例
│
├── config/                        # ⚙️ 配置文件
│   ├── settings.yaml              # 主配置文件
│   ├── settings.dev.yaml          # 开发环境配置
│   ├── settings.prod.yaml         # 生产环境配置
│   ├── agents.yaml                # Agent配置
│   └── tools.yaml                 # 工具配置
│
├── docs/                          # 📚 文档
│   ├── architecture.md            # 架构文档
│   ├── api.md                     # API文档
│   ├── agents.md                  # Agent文档
│   └── deployment.md              # 部署文档
│
├── docker/                        # 🐳 Docker配置
│   ├── Dockerfile                 # 主Dockerfile
│   ├── Dockerfile.dev             # 开发环境Dockerfile
│   └── entrypoint.sh              # 容器启动脚本
│
├── deployments/                   # 🚀 部署配置
│   ├── docker-compose.yml         # Docker Compose配置
│   ├── docker-compose.dev.yml     # 开发环境
│   ├── docker-compose.prod.yml    # 生产环境
│   └── kubernetes/                # K8s配置（可选）
│       └── ...
│
├── .env.example                   # 环境变量示例
├── .gitignore
├── requirements.txt               # Python依赖
├── requirements-dev.txt           # 开发依赖
├── setup.py                       # 包安装脚本
├── pytest.ini                     # Pytest配置
├── README.md
└── CHANGELOG.md                   # 变更日志
```

---

## 🎯 各层职责说明

### 1. core/ - 核心层

**职责：** 定义领域模型和核心业务逻辑

**包含：**
- **models/** - 领域模型（Presentation, Slide, Outline等）
- **interfaces/** - 抽象接口（Agent, Memory, Tool等）
- **services/** - 核心业务服务（Planning, Research, Generation等）

**特点：**
- 不依赖任何外部技术（框架、数据库等）
- 可以独立测试和复用
- 定义清晰的业务边界

**示例：**
```python
# core/models/presentation.py
@dataclass
class Presentation:
    """PPT领域模型"""
    id: str
    topic: str
    slides: List[Slide]
    metadata: PresentationMetadata
    created_at: datetime

    def add_slide(self, slide: Slide) -> None:
        """添加幻灯片"""
        self.slides.append(slide)

    def validate(self) -> bool:
        """验证PPT完整性"""
        return len(self.slides) > 0
```

---

### 2. agents/ - Agent层

**职责：** 实现具体的Agent

**包含：**
- **base/** - Agent基类和抽象
- **planning/** - 规划相关Agent
- **research/** - 研究相关Agent
- **generation/** - 生成相关Agent

**特点：**
- 继承自 `base/` 的基类
- 实现 `core/interfaces/agent.py` 定义的标准接口
- 每个Agent独立，可以单独测试
- Agent之间通过接口通信，不直接依赖

**示例：**
```python
# agents/planning/outline_agent.py
from core.interfaces.agent import IAgent
from agents.base.base_agent import BaseAgent

class OutlineAgent(BaseAgent):
    """大纲生成Agent"""

    def __init__(self, llm_client, memory_service):
        super().__init__(
            name="OutlineAgent",
            llm_client=llm_client,
            memory_service=memory_service
        )

    async def plan(self, topic: str, num_slides: int) -> Outline:
        """生成PPT大纲"""
        prompt = self._build_prompt(topic, num_slides)
        response = await self.llm_client.generate(prompt)
        outline = self._parse_response(response)
        return outline
```

---

### 3. memory/ - 记忆系统

**职责：** 管理会话、偏好、缓存和向量存储

**包含：**
- **interfaces/** - 记忆抽象接口
- **implementations/** - 具体实现（PostgreSQL, Redis, Vector）
- **services/** - 高级记忆服务
- **utils/** - 压缩、去重等工具

**特点：**
- 支持多种存储后端
- 统一的记忆接口
- 自动压缩和去重
- 语义检索能力

**示例：**
```python
# memory/services/session_service.py
class SessionService:
    """会话管理服务"""

    def __init__(self, persistent_db, cache_db):
        self.persistent = persistent_db
        self.cache = cache_db

    async def create_session(self, user_id: str) -> Session:
        """创建新会话"""
        session = Session(user_id=user_id)
        await self.persistent.save(session)
        await self.cache.set(session.id, session, ttl=3600)
        return session

    async def get_session(self, session_id: str) -> Session:
        """获取会话（先查缓存）"""
        # 先查缓存
        session = await self.cache.get(session_id)
        if session:
            return session

        # 缓存未命中，查持久化
        session = await self.persistent.get(session_id)
        if session:
            await self.cache.set(session_id, session, ttl=3600)
        return session
```

---

### 4. tools/ - 工具层

**职责：** 可复用的工具函数

**包含：**
- **search/** - 搜索工具（web、文档、向量）
- **media/** - 媒体处理（图片、视频）
- **file/** - 文件操作（PPT、PDF导出）
- **mcp/** - MCP工具集成

**特点：**
- 每个工具都是独立的
- 可以被任何Agent调用
- 有清晰的输入输出
- 易于测试和mock

**示例：**
```python
# tools/search/document_search.py
class DocumentSearchTool:
    """文档搜索工具"""

    name = "document_search"
    description = "在知识库中搜索相关文档"

    def __init__(self, vector_store):
        self.vector_store = vector_store

    async def search(self, query: str, top_k: int = 5) -> List[Document]:
        """搜索相关文档"""
        query_vector = await self.embed(query)
        results = await self.vector_store.similarity_search(
            query_vector,
            top_k=top_k
        )
        return results
```

---

### 5. infrastructure/ - 基础设施层

**职责：** 技术实现细节（数据库、LLM、配置等）

**包含：**
- **llm/** - LLM客户端（OpenAI, Anthropic等）
- **database/** - 数据库连接和仓储
- **config/** - 配置管理
- **logging/** - 日志系统
- **monitoring/** - 监控和指标

**特点：**
- 封装技术细节
- 提供统一的抽象
- 支持降级和重试
- 便于替换实现

**示例：**
```python
# infrastructure/llm/factory.py
class LLMFactory:
    """LLM客户端工厂"""

    @staticmethod
    def create(provider: str, model: str, **kwargs) -> BaseLLM:
        """创建LLM客户端"""
        if provider == "openai":
            return OpenAIClient(model=model, **kwargs)
        elif provider == "anthropic":
            return AnthropicClient(model=model, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    @staticmethod
    def create_with_fallback(configs: List[LLMConfig]) -> BaseLLM:
        """创建带降级的LLM客户端"""
        clients = [LLMFactory.create(c.provider, c.model)
                   for c in configs]
        return FallbackLLM(clients)
```

---

### 6. api/ - API层

**职责：** 对外HTTP接口

**包含：**
- **routes/** - 路由定义
- **schemas/** - API数据模型
- **middleware/** - 中间件
- **server.py** - 服务器启动

**特点：**
- 薄层：只处理HTTP相关逻辑
- 业务逻辑委托给 services/
- 统一的错误处理
- 请求/响应验证

**示例：**
```python
# api/routes/presentation.py
from fastapi import APIRouter, HTTPException
from api.schemas.requests import GeneratePresentationRequest
from api.schemas.responses import PresentationResponse
from services.presentation_service import PresentationService

router = APIRouter(prefix="/api/presentations", tags=["presentations"])

@router.post("/", response_model=PresentationResponse)
async def generate_presentation(
    request: GeneratePresentationRequest
) -> PresentationResponse:
    """生成PPT"""
    try:
        service = PresentationService()
        presentation = await service.generate(
            topic=request.topic,
            num_slides=request.num_slides,
            language=request.language
        )
        return PresentationResponse.from_domain(presentation)
    except Exception as e:
        raise HTTPException(status_code=500, str(e))
```

---

### 7. services/ - 服务层

**职责：** 组合各层完成业务流程

**包含：**
- **presentation_service.py** - PPT生成主服务
- **outline_service.py** - 大纲生成服务
- **export_service.py** - 导出服务
- **coordination_service.py** - 多Agent协调

**特点：**
- 协调多个Agent
- 编排业务流程
- 事务管理
- 错误处理

**示例：**
```python
# services/presentation_service.py
class PresentationService:
    """PPT生成服务"""

    def __init__(self):
        self.planner = PlanningService()
        self.researcher = ResearchService()
        self.generator = GenerationService()
        self.memory = SessionService()

    async def generate(
        self,
        topic: str,
        num_slides: int,
        user_id: str
    ) -> Presentation:
        """生成PPT的完整流程"""
        # 1. 创建会话
        session = await self.memory.create_session(user_id)

        # 2. 规划阶段
        outline = await self.planner.create_outline(topic, num_slides)

        # 3. 研究阶段
        research_data = await self.researcher.research(outline)

        # 4. 生成阶段
        presentation = await self.generator.generate(
            outline,
            research_data
        )

        # 5. 保存结果
        await self.memory.save_result(session.id, presentation)

        return presentation
```

---

## 📊 与当前结构对比

### 当前结构的问题

```
backend/
├── slide_agent/           # ❌ 与flat_slide_agent重复
├── flat_slide_agent/      # ⚠️ 依赖slide_agent
├── simplePPT/             # ❌ 完全未使用
├── super_agent/           # ❌ 实验性，端口冲突
├── ppt_api/               # ❌ 完全未使用
├── common/                # ✅ 好的实践
└── ...
```

**问题：**
1. 代码重复（slide_agent vs flat_slide_agent）
2. 职责不清（common既是基础设施又是业务逻辑）
3. 依赖混乱（flat_slide_agent依赖slide_agent）
4. 缺少抽象（没有明确的接口定义）
5. 难以测试（紧耦合）

### 理想结构的好处

```
backend/
├── core/                  # ✅ 清晰的领域模型
├── agents/                # ✅ 独立的Agent实现
├── memory/                # ✅ 统一的记忆系统
├── tools/                 # ✅ 可复用的工具
├── infrastructure/        # ✅ 技术细节隔离
├── api/                   # ✅ 对外接口
├── services/              # ✅ 业务流程编排
└── tests/                 # ✅ 完整的测试
```

**优势：**
1. ✅ 单一职责（每个模块只做一件事）
2. ✅ 低耦合（通过接口通信）
3. ✅ 易测试（可以mock任何层）
4. ✅ 可扩展（添加新功能不影响现有代码）
5. ✅ 易维护（结构清晰，定位问题快）

---

## 🔄 迁移路径

### 阶段1：提取核心（1-2周）

```
1. 创建 core/ 目录
2. 定义领域模型（models/）
3. 定义接口（interfaces/）
4. 提取共享逻辑到 services/
```

### 阶段2：重组Agent（2-3周）

```
1. 创建 agents/ 目录
2. 提取 Agent基类到 agents/base/
3. 移动所有Agent到 agents/ 下对应的目录
4. 解除 flat_slide_agent 对 slide_agent 的依赖
```

### 阶段3：统一基础设施（2-3周）

```
1. 创建 infrastructure/ 目录
2. 移动数据库相关代码
3. 移动LLM客户端代码
4. 移动配置和日志代码
```

### 阶段4：完善API和服务（1-2周）

```
1. 创建 api/ 目录
2. 创建 services/ 目录
3. 提取业务流程到 services/
4. 重构路由到 api/
```

### 阶段5：完善测试（持续）

```
1. 创建 tests/ 目录
2. 为每个模块添加单元测试
3. 添加集成测试
4. 设置CI/CD
```

---

## 💡 设计原则总结

### 1. 依赖倒置

高层模块不依赖低层模块，都依赖抽象：

```python
# ✅ 好的设计
class Agent:
    def __init__(self, llm: ILLM, memory: IMemory):  # 依赖接口
        pass

# ❌ 不好的设计
class Agent:
    def __init__(self, llm: OpenAIClient, memory: PostgresMemory):  # 依赖具体实现
        pass
```

### 2. 单一职责

每个类/模块只有一个变化的理由：

```python
# ✅ 好的设计
class PresentationGenerator:  # 只负责生成
    def generate(self, outline): pass

class PresentationExporter:   # 只负责导出
    def export(self, presentation): pass

# ❌ 不好的设计
class PresentationManager:    # 职责太多
    def generate(self, outline): pass
    def export(self, presentation): pass
    def save(self, presentation): pass
    def validate(self, presentation): pass
```

### 3. 开闭原则

对扩展开放，对修改关闭：

```python
# ✅ 好的设计
class ToolRegistry:
    def register_tool(self, tool: ITool):  # 可以扩展新工具
        self.tools[tool.name] = tool

# ❌ 不好的设计
class ToolRegistry:
    def __init__(self):
        self.web_search = WebSearch()   # 添加新工具需要修改代码
        self.doc_search = DocSearch()
```

### 4. 接口隔离

客户端不应该依赖它不需要的接口：

```python
# ✅ 好的设计
class IReadable(ABC):
    @abstractmethod
    def read(self): pass

class IWritable(ABC):
    @abstractmethod
    def write(self, data): pass

# ❌ 不好的设计
class IStorage(ABC):
    @abstractmethod
    def read(self): pass
    @abstractmethod
    def write(self, data): pass
    @abstractmethod
    def delete(self): pass
    @abstractmethod
    def search(self): pass
    # 如果只需要读，却依赖了所有方法
```

---

## 📚 参考资源

### 架构模式
- [DDD (领域驱动设计)](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [洋葱架构](https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/)
- [六边形架构](https://alistair.cockburn.us/hexagonal-architecture/)

### Python项目结构
- [Python项目最佳实践](https://docs.python-guide.org/writing/structure/)
- [FastAPI项目结构](https://fastapi.tiangolo.com/tutorial/)
- [Google Python风格指南](https://google.github.io/styleguide/pyguide.html)

### 微服务架构
- [Building Microservices](https://www.oreilly.com/library/view/building-microservices/9781491950340/)
- [Microservices Patterns](https://www.manning.com/books/microservices-patterns)

---

**文档版本**：v1.0
**最后更新**：2026-02-02
**维护者**：Claude Code
