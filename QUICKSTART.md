# MultiAgentPPT 启动指南

## 项目简介

MultiAgentPPT 是一个基于 A2A + MCP + ADK 的多智能体系统，支持流式并发生成高质量 PPT 内容。

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   MySQL         │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 3306    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲
                                │
                       ┌────────┴────────┐
                       │  Agent Services │
                       │  - Outline      │
                       │  - Slides       │
                       │  - Download     │
                       └─────────────────┘
```

---

## 前置要求

### 软件依赖

| 软件    | 版本要求     | 用途         |
| ------- | ------------ | ------------ |
| Python  | 3.11+ / 3.12 | 后端运行环境 |
| Node.js | 18+          | 前端运行环境 |
| pnpm    | 最新版       | 前端包管理器 |
| Docker  | 最新版       | 数据库服务   |

### API 密钥

需要准备以下 API 密钥之一：

- **Google AI** (推荐): `GOOGLE_API_KEY`
- **OpenAI**: `OPENAI_API_KEY`
- **DeepSeek**: `DEEPSEEK_API_KEY`
- **Claude**: `CLAUDE_API_KEY`

---

## 快速启动

### 方式一：手动启动（推荐开发环境）

打开 **3 个终端窗口**，分别执行以下命令：

#### 终端 1 - 启动数据库

```bash
# 启动 MySQL
docker run --name mysqldb -p 3306:3306 -e MYSQL_ROOT_PASSWORD=password -e MYSQL_DATABASE=multiagent_ppt -d mysql:8.0

# 启动 Redis
docker run -d -p 6379:6379 --name multiagent_redis redis:alpine
```

> 如果提示容器名冲突（如 `/multiagent_redis` 已存在），先执行：
>
> ```bash
> docker rm -f multiagent_redis mysqldb
> ```
>
> 然后再重新 `docker run`。

> **国内用户** (如遇网络问题):
>
> ```bash
> docker run --name mysqldb -p 3306:3306 -e MYSQL_ROOT_PASSWORD=password -e MYSQL_DATABASE=multiagent_ppt -d registry.cn-hangzhou.aliyuncs.com/library/mysql:8.0
> ```

#### 终端 2 - 启动后端

```bash
# 创建并激活虚拟环境
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 安装依赖
cd backend
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 配置环境变量（项目当前没有 backend/.env.example，请手动创建 backend/.env）
# 可参考下方“后端环境变量”示例，至少需要配置 DATABASE_URL、REDIS_URL 和一个 API KEY

# 启动后端服务
cd api
python main.py
```

> 如果你之前创建过 `multiagent` 环境并出现 `Permission denied ...\\Scripts\\python.exe`，请先关闭所有占用该环境的终端/进程，或改用新的环境目录（推荐 `.venv`）。
>
> 如果启动时报 `ModuleNotFoundError: No module named 'langchain_openai'`，通常是“当前 Python 解释器不是刚刚安装依赖的那个环境”。可用下面命令核对：
>
> ```bash
> where python
> python -m pip show langchain-openai
> ```
>
> 如果 `show` 查不到，重新执行：
>
> ```bash
> python -m pip install -r backend/requirements.txt
> ```

后端启动成功后可访问:

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/health

#### 终端 3 - 启动前端

```bash
cd frontend

# 安装依赖
pnpm install

# 配置环境变量
cp env_template .env      # macOS/Linux
copy env_template .env    # Windows

# 初始化数据库
pnpm db:push

# 启动前端服务
pnpm dev
```

前端启动后访问: **http://localhost:3000/presentation**（若 3000 被占用，会自动切换到 3001）

---

### 方式二：Docker Compose 启动（推荐生产环境）

```bash
# 在项目根目录执行
docker-compose up -d
```

> 注意：使用前请检查 `docker-compose.yml` 和各目录下的 `Dockerfile` 文件配置是否正确。

---

## 环境变量配置

### 后端环境变量 (`backend/.env`)

```bash
# ===========================================
# 持久化记忆系统配置
# ===========================================
USE_PERSISTENT_MEMORY=true

# MySQL 数据库配置
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/multiagent_ppt

# Redis 缓存配置
REDIS_URL=redis://127.0.0.1:6379/0

# ===========================================
# LLM 模型配置
# ===========================================
MODEL_PROVIDER=google
LLM_MODEL=gemini-2.0-flash-exp

# Google AI (推荐)
GOOGLE_API_KEY=your_google_api_key_here

# 或者使用 OpenAI
# OPENAI_API_KEY=your_openai_api_key_here

# 或者使用 DeepSeek
# DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 或者使用 Claude
# CLAUDE_API_KEY=your_claude_api_key_here
```

### 前端环境变量 (`frontend/.env`)

```bash
DATABASE_URL="mysql://root:password@localhost:3306/multiagent_ppt"
A2A_AGENT_OUTLINE_URL="http://localhost:10001"
A2A_AGENT_SLIDES_URL="http://localhost:10011"
DOWNLOAD_SLIDES_URL="http://localhost:10021"
```

---

## 常见问题

### 1. Docker 数据库启动失败

**问题**: 端口被占用

**解决**:

```bash
# 检查端口占用
netstat -ano | findstr :3306

# 停止并删除旧容器
docker stop mysqldb multiagent_redis
docker rm mysqldb multiagent_redis

# 重新启动
docker run --name mysqldb -p 3306:3306 -e MYSQL_ROOT_PASSWORD=password -e MYSQL_DATABASE=multiagent_ppt -d mysql:8.0
```

### 2. 后端依赖安装失败

**问题**: pip 安装依赖时报错

**解决**:

```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

如果遇到 `hashes` 校验失败或下载到空包，改用官方源：

```bash
pip install -r requirements.txt --index-url https://pypi.org/simple --no-cache-dir
```

如果在 Windows 上遇到路径过长（例如安装 `litellm` 时报错 `No such file or directory`），建议使用短路径虚拟环境：

```bash
# Windows 示例
python -m venv C:\venvs\mapp
C:\venvs\mapp\Scripts\activate
```

### 3. 前端数据库初始化失败

**问题**: `pnpm db:push` 执行失败

**解决**:

```bash
# 确保 MySQL 正在运行
docker ps | grep mysql

# 检查数据库连接
docker exec -it mysqldb mysql -uroot -ppassword
```

如果报错 `the URL must start with the protocol mysql://`，检查 `frontend/.env` 的 `DATABASE_URL` 是否为 MySQL 连接串。

如果报错 `P2002 Unique constraint failed on PRIMARY`（常见于重复执行 `pnpm db:push`）：

- 这是种子数据重复插入导致的冲突；当前项目已改为幂等 seed。
- 直接重新执行 `pnpm db:push` 即可。

### 4. API 调用失败

**问题**: 前端无法连接后端 API

**解决**:

1. 检查后端是否启动: http://localhost:8000/api/health
2. 检查前端 `.env` 文件中的 API 地址是否正确
3. 检查后端 CORS 配置是否允许前端地址

---

## 开发命令速查

### 后端

```bash
# 启动后端
cd backend/api && python main.py

# 运行测试
pytest

# 代码格式检查
black .
```

### 前端

```bash
# 开发模式
pnpm dev

# 构建生产版本
npm run build

# 启动生产服务
npm start

# 数据库管理
pnpm db:push      # 推送 schema
pnpm db:studio    # 打开 Prisma Studio
```

---

## 项目结构

```
MultiAgentPPT/
├── backend/              # 后端服务
│   ├── api/             # FastAPI 统一网关
│   ├── agents/          # Agent 服务
│   ├── infrastructure/  # 基础设施
│   ├── memory/          # 记忆系统
│   └── requirements.txt # Python 依赖
├── frontend/            # 前端服务
│   ├── src/            # Next.js 源代码
│   ├── prisma/         # 数据库 schema
│   └── package.json    # Node.js 依赖
├── docs/               # 文档
└── docker-compose.yml  # Docker 编排配置
```

---

## 相关文档

- [完整 README](README.md)
- [记忆系统文档](docs/memory-system/README.md)
- [架构优化报告](docs/memory-system/adapter-layer/ARCHITECTURE_OPTIMIZATION_REPORT.md)

---

## 许可证

[Apache License 2.0](LICENSE)
