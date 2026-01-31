# 🚀 MultiAgentPPT

**News**: 当前的版本不再维护，因为PPT内容和模版无法很好的维护，所以采用新的方案重构。 推荐采用PPT的模版的方式，更企业化的版本： https://github.com/johnson7788/TrainPPTAgent

作者微信答疑解惑：
![weichat.png](docs%2Fweichat.png)

一个基于 A2A + MCP + ADK 的多智能体系统，支持流式并发生成高质量 (可在线编辑）PPT 内容。

## 🧠 一、项目简介

MultiAgentPPT 利用多智能体架构实现从主题输入到完整演示文稿生成的自动化流程，主要步骤包括：

1. **大纲生成 Agent**：根据用户需求生成初步内容大纲。
2. **Topic 拆分 Agent**：将大纲内容细分为多个主题。
3. **Research Agent 并行工作**：多个智能体分别对每个主题进行深入调研。
4. **Summary Agent 汇总输出**：将调研结果汇总生成 PPT 内容，实时流式返回前端。

## 优点

- **多Agent协作**：通过多智能体并行工作，提高内容生成的效率和准确性。
- **实时流式返回**：支持流式返回生成的 PPT 内容，提升用户体验。
- **高质量内容**：结合外部检索和智能体协作，生成高质量的内容大纲和演示文稿。
- **可扩展性**：系统设计灵活，易于扩展新的智能体和功能模块。

## 二、近期升级

### ✅ 已完成（Done）

- ✅ **持久化记忆系统**（2026-01-30 NEW!）：
  - PostgreSQL + Redis + pgvector 三层记忆架构
  - 会话持久化（乐观锁并发控制）
  - 用户偏好智能学习（自动记忆语言、幻灯片数量等）
  - 向量语义检索（OpenAI embeddings + HNSW索引）
  - 研究结果缓存（减少API调用，降低30%成本）
  - 详见：[backend/persistent_memory/README.md](backend/persistent_memory/README.md)
- ✅ 除 Gemini 以外流的输出 Bug 修复，ADK 和 A2A 的包问题：[查看详情](https://github.com/johnson7788/MultiAgentPPT/blob/stream/backend/birthday_planner/README.md)
- ✅ 图片渲染方面：根据是否为背景图动态切换样式（`object-cover` 或 `object-contain`），并在非背景图下展示说明文字。为保证 PPT 页面唯一性，使用大模型输出中的 `page_number` 作为唯一标识，替代原先基于标题的方式，以支持内容更新与校对。
- ✅ 使用循环 Agent 生成每一页 PPT，代替一次性生成全部内容，方便生成更多页数，避免 LLM 的 token 输出限制。
- ✅ 引入 PPTChecker Agent 检查每一页生成的 PPT 质量。实际测试效果良好，请自行替换为真实图片数据和内容 RAG 数据。
- ✅ 前端显示每个 Agent 的生成过程状态。
- ✅ pptx下载，使用python-pptx下载前端json数据，后端渲染。
- ✅ metadata 数据传输：支持前端向 Agent 传输配置，Agent 返回结果时附带 metadata 信息。
- ✅ [本地模型适配.md](docs/%E6%9C%AC%E5%9C%B0%E6%A8%A1%E5%9E%8B%E9%80%82%E9%85%8D.md)

### 📝 待完成（Todo）

- 🔄 整合编辑可见可下载的pptx前端

## 三、使用界面截图展示

以下是 MultiAgentPPT 项目的核心功能演示：

### 1. 输入主题界面

用户在界面中输入希望生成的 PPT 主题内容：

![输入主题界面](docs/1测试界面输入主题.png)

### 2. 流式生成大纲过程

系统根据输入内容，实时流式返回生成的大纲结构：

![流式生成大纲](docs/2流式生成大纲.png)

### 3. 生成完整大纲

最终系统将展示完整的大纲，供用户进一步确认：

![完整大纲](docs/3完整大纲.png)

### 4. 流式生成PPT内容

确认大纲后，系统开始流式生成每页幻灯片内容，并返回给前端：

![流式生成PPT](docs/4流式生成PPT.png)

### 5. 对于多Agent生成PPT，slide_agent中，添加进度细节展示

![process_detail1.png](docs/process_detail1.png)
![process_detail2.png](docs/process_detail2.png)
![process_detail3.png](docs/process_detail3.png)
![process_detail4.png](docs/process_detail4.png)
![image_update.png](docs/image_update.png)

## 📊 并发的多Agent的协作流程（slide_agent + slide_outline)

```mermaid
flowchart TD
    A[用户输入研究内容] --> B[调用 Outline Agent]
    B --> C[MCP 检索资料]
    C --> D[生成大纲]
    D --> E{用户确认大纲}
    E --> F[发送大纲给 PPT 生成 Agent]

    F --> G[Split Outline Agent 拆分大纲]
    G --> H[Parallel Agent 并行处理]

    %% 并发 Research Agent
    H --> I1[Research Agent 1]
    H --> I2[Research Agent 2]
    H --> I3[Research Agent 3]

    I1 --> RAG1[自动知识库检索 RAG]
    I2 --> RAG2[自动知识库检索 RAG]
    I3 --> RAG3[自动知识库检索 RAG]

    RAG1 --> J[SummaryAgent合并结果]
    RAG2 --> J
    RAG3 --> J

    J --> L[Loop PPT Agent 生成幻灯片页]

    subgraph Loop PPT Agent
        L1[Write PPT Agent<br>生成每页幻灯片]
        L2[Check PPT Agent<br>检查每页内容质量，最多重试 3 次]
        L1 --> L2
        L2 --> L1
    end

    L --> L1
```

## 🗂️ 项目结构

```bash
MultiAgentPPT/
├── backend/              # 后端多Agent服务目录
│   ├── simpleOutline/    # 简化版大纲生成服务（无外部依赖）
│   ├── simplePPT/        # 简化版PPT生成服务（不使用检索或并发）
│   ├── slide_outline/    # 带外部检索的大纲生成大纲服务（大纲根据MCP工具检索后更精准）
│   ├── slide_agent/      # 并发式多Agent PPT生成主要xml格式的PPT内容
├── frontend/             # Next.js 前端界面
```

---

## ⚙️ 四、快速开始

### 🐍 4.1 后端环境配置（Python）

**1. 创建虚拟环境**

创建名为 `multiagent` 的虚拟环境（推荐 Python 3.11+/3.12 版本，避免 bug）：

```bash
python -m venv multiagent
```

**2. 激活虚拟环境**

根据你的系统选择对应命令：

**Windows 系统**（CMD 命令行 或 VSCode 终端）：

```bash
multiagent\Scripts\activate
```

**macOS / Linux 系统**（终端）：

```bash
source multiagent/bin/activate
```

**3. 安装依赖**

```bash
cd backend
pip install -r requirements.txt
```

**4. 设置后端环境变量**

为所有模块复制模板配置文件：

**Windows 系统：**

```bash
# 复制 simpleOutline 的环境文件
cd backend/simpleOutline
copy env_template .env

# 复制 simplePPT 的环境文件
cd ../simplePPT
copy env_template .env

# 复制 slide_outline 的环境文件
cd ../slide_outline
copy env_template .env

# 复制 slide_agent 的环境文件
cd ../slide_agent
copy env_template .env
```

**macOS / Linux 系统：**

```bash
# 复制 simpleOutline 的环境文件
cd backend/simpleOutline
cp env_template .env

# 复制 simplePPT 的环境文件
cd ../simplePPT
cp env_template .env

# 复制 slide_outline 的环境文件
cd ../slide_outline
cp env_template .env

# 复制 slide_agent 的环境文件
cd ../slide_agent
cp env_template .env
```

---

### 🧪 4.2 启动后端服务

| 模块            | 功能                     | 默认端口                        | 启动命令             |
| --------------- | ------------------------ | ------------------------------- | -------------------- |
| `simpleOutline` | 简单大纲生成             | 10001                           | `python main_api.py` |
| `simplePPT`     | 简单PPT生成              | 10011                           | `python main_api.py` |
| `slide_outline` | 高质量大纲生成（带检索） | 10001（需关闭 `simpleOutline`） | `python main_api.py` |
| `slide_agent`   | 多Agent并发生成完整PPT   | 10011（需关闭 `simplePPT`）     | `python main_api.py` |

---

## 🧱 五、前端数据库设置和安装与运行（Next.js）

数据库用于存储用户生成的 PPT：

**1. 使用 Docker 启动 PostgreSQL**

**使用 VPN 时：**

```bash
docker run --name postgresdb -p 5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=welcome -d postgres
```

**国内使用（镜像加速）：**

```bash
docker run --name postgresdb -p 5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=welcome -d swr.cn-north-4.myhuaweicloud.com/ddn-k8s/ghcr.io/cloudnative-pg/postgresql:15
```

**2. 修改 `.env` 配置文件**

```env
DATABASE_URL="postgresql://postgres:welcome@localhost:5432/presentation_ai"
A2A_AGENT_OUTLINE_URL="http://localhost:10001"
A2A_AGENT_SLIDES_URL="http://localhost:10011"
DOWNLOAD_SLIDES_URL="http://localhost:10021"
```

**3. 安装依赖并初始化数据库**

```bash
# 复制环境变量模板
cp env_template .env

# 安装前端依赖
pnpm install

# 推送数据库模型和插入用户数据
pnpm db:push

# 启动前端服务
npm run dev
```

**4. 访问应用**

打开浏览器访问：[http://localhost:3000/presentation](http://localhost:3000/presentation)

---

## 🐳 Docker 部署

**注意事项：** 使用前请自行检查 `docker-compose.yml` 和每个目录下的 `Dockerfile` 文件。

**启动前端：**

```bash
cd frontend
docker compose up
```

**启动后端：**

```bash
cd backend
docker compose up
```

---

## 🧪 示例数据说明

> 当前系统内置调研示例为：**“电动汽车发展概述”**。如需其他主题调研，请配置对应 Agent 并对接真实数据源。
> 配置真实数据，只需更改prompt和对应的MCP工具即可。

---

## 📎 六、参考来源

前端项目部分基于开源仓库：[allweonedev/presentation-ai](https://github.com/allweonedev/presentation-ai)

# Star History

[![Star History Chart](https://api.star-history.com/svg?repos=johnson7788/MultiAgentPPT&type=Date)](https://www.star-history.com/#johnson7788/MultiAgentPPT&Date)
