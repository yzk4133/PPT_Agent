# Backend 迁移和重构完整指南

## 📋 目录

1. [执行迁移](#执行迁移)
2. [当前架构分析](#当前架构分析)
3. [理想架构设计](#理想架构设计)
4. [重构路线图](#重构路线图)
5. [验证和测试](#验证和测试)

---

## 🚀 执行迁移

### 方式1：自动迁移（推荐）

#### Windows 用户
```cmd
migrate_backend.bat
```

#### Linux/Mac 用户
```bash
chmod +x migrate_backend.sh
./migrate_backend.sh
```

### 方式2：手动迁移

如果自动脚本失败，可以手动执行：

#### 步骤1：创建归档目录
```bash
mkdir -p backend/archive
mkdir backup_$(date +%Y%m%d_%H%M%S)
cp -r backend backup_$(date +%Y%m%d_%H%M%S)/
```

#### 步骤2：移动未使用的文件
```bash
# 移动实验性功能
mv backend/super_agent backend/archive/
mv backend/ppt_api backend/archive/
mv backend/skills backend/archive/
mv backend/simplePPT backend/archive/
mv backend/simpleOutline backend/archive/

# 迁移文档到根目录
mv backend/doc/* docs/ 2>/dev/null || true
mv backend/docs/* docs/ 2>/dev/null || true
rm -rf backend/doc backend/docs
```

#### 步骤3：创建新目录结构
```bash
# Agent层
mkdir -p backend/agents/{base,planning,research,generation}

# API层
mkdir -p backend/api/{routes,schemas,middleware}

# 核心层
mkdir -p backend/core/{models,interfaces,services}

# 基础设施层
mkdir -p backend/infrastructure/{llm,database,config,logging}

# 记忆系统
mkdir -p backend/memory/{interfaces,implementations,services,utils}

# 工具层
mkdir -p backend/tools/{search,media,file,mcp}

# 服务层
mkdir -p backend/services

# 测试
mkdir -p backend/tests/{unit,integration,fixtures,utils}
```

---

## 📊 当前架构分析

### 迁移前的结构

```
backend/
├── ❌ super_agent/          ← 实验性，未使用
├── ❌ ppt_api/              ← 未集成
├── ❌ skills/               ← 未启用
├── ❌ simplePPT/            ← 依赖super_agent
├── ❌ simpleOutline/        ← 依赖super_agent
├── ✅ slide_agent/          ← 生产服务，被flat复用
├── ✅ slide_outline/        ← 生产服务
├── ✅ flat_slide_agent/     ← 新架构，依赖旧模块
├── ✅ flat_slide_outline/   ← 新架构
├── ✅ save_ppt/             ← 生产服务
├── ✅ hostAgentAPI/         ← 核心服务
├── ✅ multiagent_front/     ← 前端界面
├── ✅ persistent_memory/    ← 记忆系统
├── ✅ common/               ← 核心基础设施
├── ❌ doc/                  ← 应该在根目录
└── ❌ docs/                 ← 应该在根目录
```

### 问题诊断

| 问题 | 影响 | 严重程度 |
|------|------|---------|
| `flat_slide_agent` 依赖 `slide_agent` | 无法删除旧代码 | 🔴 高 |
| 重复代码（adk_agent_executor, a2a_client） | 维护困难 | 🟡 中 |
| 未使用模块（super_agent, ppt_api） | 混淆视线 | 🟢 低 |
| 缺少清晰的分层 | 难以理解和扩展 | 🟡 中 |

---

## 🎯 理想架构设计

### 迁移后的目标结构

```
backend/
│
├── 📦 archive/                    # 已归档的旧文件
│   ├── super_agent/
│   ├── ppt_api/
│   ├── skills/
│   ├── simplePPT/
│   ├── simpleOutline/
│   ├── doc/
│   └── docs/
│
├── 🤖 agents/                     # Agent层（未来目标）
│   ├── base/                      # Agent基类
│   │   ├── base_agent.py
│   │   ├── sequential_agent.py
│   │   ├── parallel_agent.py
│   │   └── loop_agent.py
│   │
│   ├── planning/                  # 规划Agent
│   │   ├── outline_agent.py
│   │   ├── topic_splitter_agent.py
│   │   └── prompt.py
│   │
│   ├── research/                  # 研究Agent
│   │   ├── researcher_agent.py
│   │   ├── parallel_researcher.py
│   │   └── prompt.py
│   │
│   └── generation/                # 生成Agent
│       ├── slide_writer_agent.py
│       ├── slide_checker_agent.py
│       └── prompt.py
│
├── 🌐 api/                        # API层（未来目标）
│   ├── routes/                    # 路由定义
│   │   ├── presentation.py
│   │   ├── outline.py
│   │   └── health.py
│   │
│   ├── schemas/                   # 数据模型
│   │   ├── requests.py
│   │   ├── responses.py
│   │   └── errors.py
│   │
│   ├── middleware/                # 中间件
│   │   ├── auth.py
│   │   ├── cors.py
│   │   └── logging.py
│   │
│   └── server.py                  # 服务器启动
│
├── 🔵 core/                       # 核心层（未来目标）
│   ├── models/                    # 领域模型
│   │   ├── presentation.py
│   │   ├── slide.py
│   │   ├── outline.py
│   │   └── research.py
│   │
│   ├── interfaces/                # 接口定义
│   │   ├── agent.py
│   │   ├── memory.py
│   │   ├── tool.py
│   │   └── llm.py
│   │
│   └── services/                  # 核心服务
│       ├── planning_service.py
│       ├── research_service.py
│       └── generation_service.py
│
├── 🏗️ infrastructure/            # 基础设施层（未来目标）
│   ├── llm/                       # LLM客户端
│   │   ├── base.py
│   │   ├── openai_client.py
│   │   ├── anthropic_client.py
│   │   ├── factory.py
│   │   └── fallback.py
│   │
│   ├── database/                  # 数据库
│   │   ├── postgres.py
│   │   ├── redis.py
│   │   └── repositories.py
│   │
│   ├── config/                    # 配置
│   │   ├── settings.py
│   │   └── loader.py
│   │
│   └── logging/                   # 日志
│       └── logger.py
│
├── 🧠 memory/                     # 记忆系统
│   ├── interfaces/                # 记忆接口
│   │   └── imemory.py
│   │
│   ├── implementations/           # 具体实现
│   │   ├── persistent_memory.py
│   │   ├── cache_memory.py
│   │   └── vector_memory.py
│   │
│   ├── services/                  # 记忆服务
│   │   ├── session_service.py
│   │   └── preference_service.py
│   │
│   └── utils/                     # 记忆工具
│       ├── compressor.py          # 已有
│       └── deduplicator.py
│
├── 🔧 tools/                      # 工具层（未来目标）
│   ├── search/
│   │   ├── web_search.py
│   │   ├── document_search.py
│   │   └── semantic_search.py
│   │
│   ├── media/
│   │   ├── image_search.py
│   │   └── image_processor.py
│   │
│   ├── file/
│   │   ├── ppt_exporter.py
│   │   └── file_manager.py
│   │
│   └── mcp/
│       └── mcp_client.py
│
├── 📦 services/                   # 服务层（未来目标）
│   ├── presentation_service.py
│   ├── outline_service.py
│   └── coordination_service.py
│
├── 🧪 tests/                      # 测试（未来目标）
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── utils/
│
├── ✅ 保留的原目录（生产服务）
│   ├── slide_agent/               # 当前生产，逐步迁移后删除
│   ├── slide_outline/             # 当前生产，逐步迁移后删除
│   ├── flat_slide_agent/          # 新架构，已保留
│   ├── flat_slide_outline/        # 新架构，已保留
│   ├── save_ppt/                  # 生产服务，保留
│   ├── hostAgentAPI/              # 核心服务，保留
│   ├── multiagent_front/          # 前端，保留
│   ├── persistent_memory/         # 记忆系统，保留
│   │
│   └── common/                    # 核心基础设施，保留
│       ├── config.py
│       ├── model_factory.py
│       ├── tool_manager.py
│       ├── retry_decorator.py
│       ├── context_compressor.py
│       ├── fallback/
│       ├── adk_agent_executor.py  # 新提取
│       └── a2a_client.py          # 新提取
│
├── docker-compose.yml             # Docker配置
├── requirements.txt               # 依赖
├── STRUCTURE_MAPPING.md           # 本文档
└── REFACTORING_GUIDE.md           # 重构指南
```

---

## 🗺️ 重构路线图

### 阶段1：归档和准备（已完成）✅

**目标：** 清理未使用的文件，创建新目录结构

**任务：**
- [x] 归档 `super_agent/`
- [x] 归档 `ppt_api/`
- [x] 归档 `skills/`
- [x] 归档 `simplePPT/` 和 `simpleOutline/`
- [x] 迁移文档到根目录
- [x] 提取重复代码到 `common/`
- [x] 创建新的目录结构

**验证：**
```bash
# 检查归档
ls backend/archive/

# 检查新目录
ls backend/agents/
ls backend/api/
ls backend/core/

# 检查备份
ls backup_*/
```

---

### 阶段2：解耦依赖（1-2周）

**目标：** 解除 `flat_slide_agent` 对 `slide_agent` 的依赖

#### 步骤2.1：提取共享的子Agent

```bash
# 复制子模块到新位置
cp -r backend/slide_agent/slide_agent/sub_agents/* backend/agents/

# 目录结构变为：
backend/agents/
├── split_topic/
│   ├── agent.py
│   └── prompt.py
├── research_topic/
│   ├── agent.py
│   ├── tools/
│   └── prompt.py
└── ppt_writer/
    ├── agent.py
    ├── tools.py
    └── prompt.py
```

#### 步骤2.2：更新导入路径

**修改前：**
```python
# backend/flat_slide_agent/agents/flat_root_agent.py
from slide_agent.sub_agents.split_topic.agent import split_topic_agent
from slide_agent.sub_agents.research_topic.agent import parallel_search_agent
from slide_agent.sub_agents.ppt_writer.agent import ppt_generator_loop_agent
```

**修改后：**
```python
# backend/flat_slide_agent/agents/flat_root_agent.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents.split_topic.agent import split_topic_agent
from agents.research_topic.agent import parallel_search_agent
from agents.ppt_writer.agent import ppt_generator_loop_agent
```

#### 步骤2.3：测试

```bash
# 启动flat_slide_agent
cd backend/flat_slide_agent
python main_api.py

# 测试生成PPT
curl -X POST http://localhost:10012/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI发展史", "num_slides": 5}'
```

**完成标志：**
- ✅ `flat_slide_agent` 可以独立运行
- ✅ 不再依赖 `slide_agent/`

---

### 阶段3：更新Docker配置（1周）

**目标：** 将新架构添加到生产环境

#### 修改 docker-compose.yml

**添加新服务：**
```yaml
services:
  # 原有服务（保留）
  ppt_agent:
    build: ./backend/slide_agent
    ports:
      - "10011:10011"

  ppt_outline:
    build: ./backend/slide_outline
    ports:
      - "10001:10001"

  # 新增服务（flat架构）
  flat_ppt_agent:
    build: ./backend/flat_slide_agent
    ports:
      - "10012:10012"
    environment:
      - SERVICE_NAME=flat_ppt_agent
      - ARCHITECTURE=flat

  flat_ppt_outline:
    build: ./backend/flat_slide_outline
    ports:
      - "10002:10002"
    environment:
      - SERVICE_NAME=flat_ppt_outline
      - ARCHITECTURE=flat
```

#### 测试Docker服务

```bash
# 启动所有服务
docker-compose up -d

# 检查健康状态
curl http://localhost:10012/health
curl http://localhost:10002/health

# 测试生成
curl -X POST http://localhost:10012/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI发展史", "num_slides": 5}'
```

---

### 阶段4：代码迁移（2-4周）

**目标：** 逐步将代码迁移到新目录结构

#### 优先级1：Domain Models（1周）

```bash
# 创建领域模型
touch backend/core/models/presentation.py
touch backend/core/models/slide.py
touch backend/core/models/outline.py
touch backend/core/models/research.py

# 从现有代码中提取数据结构
# 参考：flat_slide_agent 中的数据结构定义
```

**示例：**
```python
# backend/core/models/presentation.py
from dataclasses import dataclass, field
from typing import List
from datetime import datetime

@dataclass
class Presentation:
    """PPT领域模型"""
    id: str
    topic: str
    slides: List['Slide'] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def add_slide(self, slide: 'Slide') -> None:
        if len(self.slides) >= 50:
            raise ValueError("Cannot exceed 50 slides")
        self.slides.append(slide)

    def validate(self) -> bool:
        return 1 <= len(self.slides) <= 50
```

#### 优先级2：Services（1周）

```bash
# 创建服务层
touch backend/services/presentation_service.py
touch backend/services/outline_service.py

# 从现有代码中提取业务逻辑
# 参考：flat_slide_agent/agents/flat_root_agent.py
```

**示例：**
```python
# backend/services/presentation_service.py
class PresentationService:
    """PPT生成服务"""

    def __init__(self):
        from agents.planning.outline_agent import OutlineAgent
        from agents.research.researcher_agent import ResearcherAgent
        from agents.generation.slide_writer_agent import SlideWriterAgent

        self.outline_agent = OutlineAgent(...)
        self.research_agent = ResearcherAgent(...)
        self.writer_agent = SlideWriterAgent(...)

    async def generate(self, topic: str, num_slides: int):
        # 编排流程
        outline = await self.outline_agent.create_outline(topic)
        research = await self.research_agent.research(outline)

        presentation = Presentation(id=generate_id(), topic=topic)
        for i in range(num_slides):
            slide = await self.writer_agent.write_slide(...)
            presentation.add_slide(slide)

        return presentation
```

#### 优先级3：API Routes（1周）

```bash
# 创建API路由
touch backend/api/routes/presentation.py
touch backend/api/routes/outline.py
touch backend/api/schemas/requests.py
touch backend/api/schemas/responses.py
```

**示例：**
```python
# backend/api/routes/presentation.py
from fastapi import APIRouter, HTTPException
from api.schemas.requests import GeneratePresentationRequest
from api.schemas.responses import PresentationResponse
from services.presentation_service import PresentationService

router = APIRouter(prefix="/api/presentations", tags=["presentations"])

@router.post("/", response_model=PresentationResponse)
async def generate_presentation(request: GeneratePresentationRequest):
    service = PresentationService()
    presentation = await service.generate(
        topic=request.topic,
        num_slides=request.num_slides
    )
    return PresentationResponse.from_domain(presentation)
```

#### 优先级4：Infrastructure（1周）

```bash
# 整合基础设施
mv backend/common/model_factory.py backend/infrastructure/llm/
mv backend/common/config.py backend/infrastructure/config/
```

---

### 阶段5：清理旧代码（最后执行）

**⚠️ 只有在以下条件满足后才执行：**

- [ ] `flat_slide_agent` 稳定运行1个月以上
- [ ] 所有测试通过
- [ ] 性能不低于旧架构
- [ ] 团队熟悉新架构

**然后才能删除：**

```bash
# 删除旧架构
rm -rf backend/slide_agent
rm -rf backend/slide_outline

# 保留flat架构
# backend/flat_slide_agent/
# backend/flat_slide_outline/
```

---

## 🧪 验证和测试

### 测试清单

#### 1. 功能测试

```bash
# 测试大纲生成
curl -X POST http://localhost:10002/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "人工智能", "num_slides": 10}'

# 测试PPT生成
curl -X POST http://localhost:10012/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "人工智能", "num_slides": 10}'

# 测试PPT导出
curl -X POST http://localhost:10021/export \
  -H "Content-Type: application/json" \
  -d '{"presentation_id": "..."}'
```

#### 2. 性能测试

```bash
# 对比旧架构 vs 新架构
time test_old_architecture.sh
time test_new_architecture.sh
```

**预期结果：**
- 新架构性能 ≥ 旧架构
- Token消耗 < 旧架构（因为有上下文压缩）

#### 3. 依赖检查

```bash
# 检查flat_slide_agent是否还依赖slide_agent
grep -r "from slide_agent" backend/flat_slide_agent/

# 应该返回空（无依赖）
```

---

## 📊 迁移进度跟踪

### 进度表

| 阶段 | 任务 | 状态 | 完成日期 |
|------|------|------|---------|
| 阶段1 | 归档未使用文件 | ✅ 已完成 | 2026-02-02 |
| 阶段1 | 创建新目录结构 | ✅ 已完成 | 2026-02-02 |
| 阶段1 | 提取重复代码 | ✅ 已完成 | 2026-02-02 |
| 阶段2 | 解耦flat依赖 | ⏳ 进行中 | - |
| 阶段2 | 更新导入路径 | ⏳ 待开始 | - |
| 阶段2 | 测试独立运行 | ⏳ 待开始 | - |
| 阶段3 | 更新Docker配置 | ⏳ 待开始 | - |
| 阶段3 | 添加新服务 | ⏳ 待开始 | - |
| 阶段4 | 迁移Domain Models | ⏳ 待开始 | - |
| 阶段4 | 迁移Services | ⏳ 待开始 | - |
| 阶段4 | 迁移API Routes | ⏳ 待开始 | - |
| 阶段5 | 删除旧代码 | ⏳ 待开始 | - |

### 里程碑

- 🏁 **M1**: 完成归档（2026-02-02）✅
- 🏁 **M2**: 完成解耦（预计2026-02-16）
- 🏁 **M3**: 完成Docker集成（预计2026-02-23）
- 🏁 **M4**: 完成代码迁移（预计2026-03-15）
- 🏁 **M5**: 完成清理（预计2026-04-01）

---

## 🆘 故障排除

### 问题1：flat_slide_agent启动失败

**症状：**
```
ImportError: No module named 'slide_agent.sub_agents'
```

**解决：**
```bash
# 检查导入路径
grep -r "from slide_agent" backend/flat_slide_agent/

# 更新为新的导入路径
# from slide_agent.sub_agents.* → from agents.*
```

### 问题2：Docker服务无法启动

**症状：**
```
ERROR: for flat_ppt_agent Cannot start service...
```

**解决：**
```bash
# 检查日志
docker-compose logs flat_ppt_agent

# 检查端口占用
netstat -an | grep 10012

# 重新构建
docker-compose build flat_ppt_agent
docker-compose up -d flat_ppt_agent
```

### 问题3：测试失败

**症状：**
```
AssertionError: Expected 10 slides, got 8
```

**解决：**
```bash
# 检查日志
tail -f backend/flat_slide_agent/logs/*.log

# 检查Agent配置
cat backend/flat_slide_agent/agents/flat_root_agent.py

# 重新测试
pytest backend/tests/integration/test_ppt_generation.py -v
```

---

## 📞 获取帮助

### 相关文档

- `STRUCTURE_MAPPING.md` - 目录结构映射
- `ARCHITECTURE_LAYERS_EXPLAINED.md` - 分层架构详解
- `IDEAL_BACKEND_STRUCTURE.md` - 理想架构设计
- `BACKEND_CLEANUP_GUIDE.md` - 清理指南

### 回滚方法

如果迁移出现问题，可以快速回滚：

```bash
# 恢复备份
cp -r backup_YYYYMMDD_HHMMSS/backend/* backend/

# 或者从archive恢复
mv backend/archive/slide_agent backend/
mv backend/archive/slide_outline backend/
```

---

**文档版本：** v1.0
**最后更新：** 2026-02-02
**维护者：** Claude Code
