# MultiAgentPPT

基于多智能体架构的智能 PPT 生成系统，支持流式并发生成高质量、可在线编辑的演示文稿。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Stars](https://img.shields.io/github/stars/yzk4133/PPT_Agent?style=social)
![Issues](https://img.shields.io/github/issues/yzk4133/PPT_Agent)

## 特性

- **多Agent协作** - 大纲生成、主题拆分、并行研究、内容汇总的完整工作流
- **实时流式输出** - 支持流式返回生成的PPT内容，实时显示生成进度
- **智能记忆系统** - PostgreSQL + Redis + pgvector 三层记忆架构
- **外部知识检索** - 集成MCP工具进行自动知识库检索(RAG)
- **PPTX导出** - 支持下载可编辑的PowerPoint文件
- **在线编辑** - 前端支持内容实时预览和编辑
- **质量检查** - PPTChecker Agent自动检查内容质量
- **会话持久化** - 用户偏好智能学习，研究结果缓存

## 技术栈

### 后端
- **Python 3.11+** - 核心语言
- **FastAPI** - 高性能Web框架
- **LangChain + LangGraph** - AI应用框架
- **A2A SDK** - Agent间通信协议
- **MCP** - 模型上下文协议
- **ADK** - Agent开发工具包
- **SQLAlchemy** - ORM
- **PostgreSQL + Redis + pgvector** - 数据存储和向量检索

### 前端
- **Next.js 14** - React框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式框架
- **Prisma** - 数据库ORM
- **React Query** - 数据获取
- **Radix UI** - 组件库
- **Plate.js** - 富文本编辑器

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- Docker（用于PostgreSQL和Redis）

### 1. 克隆项目

```bash
git clone https://github.com/yzk4133/PPT_Agent.git
cd PPT_Agent
```

### 2. 后端环境配置

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
cd backend
pip install -r requirements.txt

# 配置环境变量
cd api
cp env_template .env
# 编辑 .env 文件，配置必要的API密钥
```

### 3. 启动数据库

```bash
# 启动 PostgreSQL
docker run --name postgresdb -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=welcome \
  -d postgres

# 启动 Redis
docker run -d -p 6379:6379 --name redis redis:alpine
```

**国内用户（使用镜像加速）：**

```bash
docker run --name postgresdb -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=welcome \
  -d swr.cn-north-4.myhuaweicloud.com/ddn-k8s/ghcr.io/cloudnative-pg/postgresql:15
```

### 4. 启动后端服务

```bash
cd backend/api
python main.py
```

访问 API 文档：http://localhost:8000/docs

### 5. 启动前端服务

```bash
cd frontend

# 安装依赖
pnpm install

# 配置环境变量
cp env_template .env
# 编辑 .env 文件

# 初始化数据库
pnpm db:push

# 启动开发服务器
npm run dev
```

访问应用：http://localhost:3000/presentation

### 完整启动流程（推荐）

打开三个终端窗口：

**终端 1 - 启动数据库：**

```bash
docker run --name postgresdb -p 5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=welcome -d postgres
```

**终端 2 - 启动后端：**

```bash
cd backend/api
python main.py
```

**终端 3 - 启动前端：**

```bash
cd frontend
npm run dev
```

访问：http://localhost:3000/presentation

## 系统架构

### Agent工作流

```mermaid
flowchart TD
    A[用户输入研究内容] --> B[大纲生成Agent]
    B --> C[MCP检索资料]
    C --> D[生成大纲]
    D --> E{用户确认}
    E --> F[发送给PPT生成Agent]

    F --> G[主题拆分Agent]
    G --> H[并行处理]

    H --> I1[Research Agent 1]
    H --> I2[Research Agent 2]
    H --> I3[Research Agent 3]

    I1 --> RAG1[RAG检索]
    I2 --> RAG2[RAG检索]
    I3 --> RAG3[RAG检索]

    RAG1 --> J[SummaryAgent汇总]
    RAG2 --> J
    RAG3 --> J

    J --> K[Loop PPT Agent]
    K --> L[Write PPT Agent]
    L --> M[Check PPT Agent]
    M --> N{质量检查通过?}
    N -->|否| L
    N -->|是| O[输出PPT内容]
```

### 项目结构

```
MultiAgentPPT/
├── backend/              # 后端服务
│   ├── api/             # FastAPI网关
│   ├── agents/          # Agent模块
│   │   ├── coordinator/ # 协调器
│   │   ├── core/        # 核心Agent
│   │   └── models/      # Agent模型
│   ├── memory/          # 记忆系统
│   ├── tools/           # MCP工具
│   └── utils/           # 工具函数
├── frontend/            # Next.js前端
├── minimind/           # MiniMind语言模型
├── docs/               # 项目文档
└── scripts/            # 脚本工具
```

## 配置说明

### 后端环境变量

在 `backend/api/.env` 中配置：

```bash
# API Keys (选择一个配置)
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# 数据库配置
DATABASE_URL=postgresql://postgres:welcome@localhost:5432/ppt_agent
REDIS_URL=redis://localhost:6379
```

### 前端环境变量

在 `frontend/.env` 中配置：

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 核心文档

- **[记忆系统文档](docs/memory-system/README.md)** - 记忆系统架构和使用指南
- **[快速开始指南](QUICK_START.md)** - 5分钟快速上手
- **[项目报告存档](docs/reports/README.md)** - 架构优化、重构记录、分析报告等
- **[架构优化报告](docs/memory-system/adapter-layer/ARCHITECTURE_OPTIMIZATION_REPORT.md)** - 记忆系统从三层简化为两层

## Docker部署

### 前端部署

```bash
cd frontend
docker compose up
```

### 后端部署

```bash
cd backend
docker compose up
```

**注意事项：** 使用前请自行检查 `docker-compose.yml` 和每个目录下的 `Dockerfile` 文件。

## API测试

```bash
# 健康检查
curl http://localhost:8000/api/health

# 生成大纲
curl -X POST http://localhost:8000/api/ppt/outline/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "人工智能发展概述",
    "language": "zh-CN",
    "numberOfCards": 10
  }'
```

更多API文档请访问：http://localhost:8000/docs

### 使用 Apifox/Postman

导入以下端点进行测试：

- `POST http://localhost:8000/api/ppt/outline/generate` - 生成大纲
- `POST http://localhost:8000/api/ppt/generate` - 生成幻灯片
- `GET http://localhost:8000/api/presentations` - 查询演示文稿列表

## 贡献

欢迎贡献代码、报告问题或提出改进建议！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情

## 致谢

- 前端部分基于 [allweonedev/presentation-ai](https://github.com/allweonedev/presentation-ai)
- 感谢所有贡献者的支持

---

**注意**: 本项目需要配置相应的API密钥才能正常使用。请确保在使用前正确配置环境变量。
