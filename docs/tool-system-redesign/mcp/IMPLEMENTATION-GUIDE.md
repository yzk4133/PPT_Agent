# MCP集成实现指南

> 从零开始集成两个智谱MCP服务的完整实现步骤

---

## 📋 文档信息

| 项目 | 内容 |
|------|------|
| **项目名称** | MultiAgentPPT |
| **文档版本** | v1.0 |
| **创建日期** | 2026-03-07 |
| **文档类型** | 实现指南 |

---

## 🎯 实现目标

将两个智谱MCP服务集成到项目中，使Agent能够调用：
- **智谱搜索** (HTTP方式) - 高质量网络搜索
- **Zai视觉** (stdio方式) - 图片视觉理解

---

## 📅 实施阶段概览

```
Phase 1: 环境准备 (1天)
   ↓
Phase 2: 配置管理 (0.5天)
   ↓
Phase 3: MCP客户端层 (1.5天)
   ↓
Phase 4: 工具包装层 (1天)
   ↓
Phase 5: 工具注册集成 (0.5天)
   ↓
Phase 6: 测试验证 (1.5天)

总计: 约6天
```

---

## Phase 1: 环境准备

### 目标
准备好运行MCP服务所需的所有前提条件

### 步骤

#### 1.1 安装Node.js和npx

**为什么需要**：Zai MCP Server是Node.js包，需要Node.js环境运行

**操作步骤**：
- 下载并安装Node.js (版本 >= 18.0.0)
- 验证安装：`node --version` 和 `npx --version`
- Windows用户：确保环境变量PATH包含Node.js路径

**验收标准**：
```bash
$ node --version
v18.x.x 或更高

$ npx --version
10.x.x 或更高
```

#### 1.2 申请智谱AI API Key

**为什么需要**：调用智谱搜索和Zai视觉需要认证

**操作步骤**：
1. 访问 https://open.bigmodel.cn/
2. 注册/登录账号
3. 进入控制台 → API Key管理
4. 创建新的API Key
5. 复制保存（格式：`id.secret`，只显示一次）

**注意事项**：
- 保存好API Key，泄露后需要重新生成
- 新用户有免费额度

#### 1.3 安装Python依赖

**为什么需要**：MCP协议的Python SDK和异步HTTP库

**操作步骤**：
```bash
pip install mcp aiohttp pyyaml python-dotenv
```

**依赖说明**：
- `mcp` - MCP协议的Python SDK
- `aiohttp` - 异步HTTP客户端
- `pyyaml` - YAML配置文件解析
- `python-dotenv` - 环境变量加载

---

## Phase 2: 配置管理

### 目标
创建配置文件，存储敏感信息和连接参数

### 步骤

#### 2.1 创建目录结构

```bash
mkdir -p config
```

#### 2.2 创建 .env 文件

**位置**：项目根目录

**内容**：
```bash
# 智谱AI API Key
ZHIPU_API_KEY=your_actual_api_key_here

# Zai API Key (通常与智谱相同)
ZAI_API_KEY=your_actual_api_key_here
```

**安全措施**：
- 永远不要提交.env到Git仓库
- 在.gitignore中添加.env

#### 2.3 创建 mcp_config.yaml

**位置**：`config/mcp_config.yaml`

**内容**：
```yaml
servers:
  # 智谱搜索 (HTTP方式)
  zhipu-search:
    type: http
    url: https://open.bigmodel.cn/api/mcp/web_search_prime/mcp
    headers:
      Authorization: Bearer ${ZHIPU_API_KEY}
    timeout: 30

  # Zai视觉 (stdio方式)
  zai-vision:
    type: stdio
    command: npx
    args: ["-y", "@z_ai/mcp-server"]
    env:
      Z_AI_API_KEY: ${ZAI_API_KEY}
      Z_AI_MODE: ZHIPU
```

**配置说明**：
- `${VAR_NAME}` 会被替换为环境变量的值
- `timeout` 是HTTP请求超时时间（秒）
- `-y` 参数让npx自动确认安装

#### 2.4 更新 .gitignore

**添加内容**：
```gitignore
# 环境变量
.env
.env.local

# MCP配置(包含敏感信息)
config/mcp_config.yaml
```

---

## Phase 3: MCP客户端层

### 目标
实现与MCP服务器通信的底层客户端

### 文件组织
```
backend/agents/core/mcp/
├── __init__.py
├── base_client.py       # 基础客户端接口
├── http_client.py       # HTTP客户端实现
├── stdio_client.py      # stdio客户端实现
└── servers.py           # 服务器管理器
```

### 步骤

#### 3.1 创建目录

```bash
mkdir -p backend/agents/core/mcp
```

#### 3.2 实现 base_client.py

**目的**：定义所有MCP客户端必须实现的统一接口

**核心方法**：
- `connect()` - 建立连接
- `disconnect()` - 断开连接
- `call_tool(tool_name, **kwargs)` - 调用工具
- `list_tools()` - 列出可用工具

**要点**：
- 使用抽象基类(ABC)强制子类实现方法
- 初始化接收name和config参数

#### 3.3 实现 http_client.py

**目的**：通过HTTP调用智谱搜索MCP服务

**核心功能**：
- 使用aiohttp创建HTTP会话
- 构建符合MCP规范的JSON-RPC请求
- 发送POST请求到配置的URL
- 处理认证头和超时
- 解析JSON响应

**关键点**：
- 请求格式：
  ```json
  {
    "method": "tools/call",
    "params": {
      "name": "tool_name",
      "arguments": {...}
    }
  }
  ```
- 错误处理：检查HTTP状态码，处理非200响应
- 资源管理：正确关闭HTTP会话

#### 3.4 实现 stdio_client.py

**目的**：通过stdin/stdout与Zai视觉MCP进程通信

**核心功能**：
- 使用asyncio.create_subprocess_exec启动子进程
- 设置环境变量（API Key等）
- 通过stdin写入JSON-RPC请求
- 通过stdout读取JSON-RPC响应
- 管理进程生命周期

**关键点**：
- 请求格式：JSON字符串 + 换行符
- 响应读取：按行读取，解析JSON
- 错误处理：检查响应中的error字段
- 进程管理：正确启动和终止子进程

#### 3.5 实现 servers.py

**目的**：统一管理所有MCP服务器

**核心功能**：
- 加载YAML配置文件
- 替换环境变量占位符（如 `${ZHIPU_API_KEY}`）
- 根据type创建对应的客户端实例
- 提供启动所有/停止所有/获取客户端的方法

**关键点**：
- 使用python-dotenv加载.env文件
- 递归替换配置中的环境变量
- 维护客户端字典 {name: client}

---

## Phase 4: 工具包装层

### 目标
将MCP客户端包装成LangChain工具，供Agent使用

### 文件组织
```
backend/tools/domain/resource/
├── zhipu_search_tool.py   # 搜索工具
└── zai_vision_tool.py     # 视觉工具
```

### 步骤

#### 4.1 实现 zhipu_search_tool.py

**目的**：包装智谱搜索为LangChain工具

**核心组件**：

1. **输入模型 (Pydantic)**
   - 定义输入参数：query (搜索词)、count (结果数量)
   - 提供字段描述和默认值

2. **工具类**
   - 持有MCP管理器引用
   - 实现invoke方法：调用HTTP客户端的web_search_prime
   - 实现格式化方法：提取搜索结果的标题、URL、摘要

3. **工厂函数**
   - 创建工具实例
   - 转换为LangChain的StructuredTool
   - 提供工具描述（会被LLM看到）

**工具描述示例**：
```
使用智谱AI进行高质量网络搜索，特别适合中文内容。
参数：query (搜索关键词), count (返回结果数量，默认5)
```

#### 4.2 实现 zai_vision_tool.py

**目的**：包装Zai视觉为LangChain工具

**核心组件**：

1. **输入模型**
   - 定义输入参数：tool_name (工具类型)、image_source (图片URL)
   - 支持四种工具：vision_understand, vision_ocr, vision_qa, vision_compare

2. **工具类**
   - 持有MCP管理器引用
   - 实现invoke方法：调用stdio客户端
   - 支持额外的kwargs参数（如question、language等）

3. **工厂函数**
   - 创建工具实例
   - 提供清晰的工具描述

**四种视觉能力**：
- `vision_understand` - 图片内容理解
- `vision_ocr` - 文字识别
- `vision_qa` - 视觉问答
- `vision_compare` - 图片对比

---

## Phase 5: 工具注册集成

### 目标
将MCP工具集成到现有的工具注册系统

### 步骤

#### 5.1 修改 tool_registry.py

**需要添加的功能**：

1. **初始化MCP管理器**
   - 在__init__中创建MCPServerManager实例

2. **异步初始化方法**
   - 启动所有MCP服务器
   - 调用工厂函数创建MCP工具
   - 注册到工具字典

3. **异步清理方法**
   - 停止所有MCP服务器
   - 释放资源

4. **保持接口一致性**
   - MCP工具和本地工具使用相同的获取方式
   - 统一的get_tool(name)方法

**使用示例**：
```python
registry = ToolRegistry()
await registry.initialize()  # 启动MCP服务器

tool = registry.get_tool("zhipu_search")
result = await tool.invoke(query="AI")

await registry.cleanup()  # 清理资源
```

---

## Phase 6: 测试验证

### 目标
确保整个MCP集成正常工作

### 步骤

#### 6.1 单元测试

**测试范围**：
- HTTP客户端的请求构建和响应解析
- stdio客户端的进程管理和通信
- 工具的参数验证和结果格式化
- 配置加载和环境变量替换

**测试方法**：
- 使用Mock对象模拟MCP服务器响应
- 测试异常情况（网络错误、超时、错误响应）
- 验证参数校验逻辑

#### 6.2 集成测试

**测试范围**：
- 客户端与真实MCP服务器的通信
- 工具注册表的初始化和工具获取
- 配置文件的正确加载

**测试方法**：
- 连接真实的智谱搜索API
- 启动真实的Zai视觉进程
- 验证端到端调用流程

#### 6.3 端到端测试

**测试范围**：
- Agent调用MCP工具生成PPT的完整流程
- 多工具协作场景

**测试场景**：
```
1. 搜索PPT主题相关资料
   - 调用zhipu_search
   - 验证返回结果质量

2. 分析图片选择配图
   - 调用zai_vision分析候选图片
   - 验证分析结果准确性

3. 完整PPT生成
   - 搜索资料 → 生成大纲 → 选择配图 → 生成PPT
   - 验证整个流程无错误
```

#### 6.4 性能测试

**测试指标**：
| 指标 | 目标值 | 测试方法 |
|------|--------|----------|
| 智谱搜索响应时间 | < 3s | 多次调用取平均值 |
| Zai视觉分析时间 | < 5s | 多次调用取平均值 |
| MCP服务器启动时间 | < 10s | 测量启动到可用时间 |
| 端到端PPT生成时间 | < 60s | 完整流程测试 |

#### 6.5 稳定性测试

**测试场景**：
- 网络异常时的重试机制
- API限流时的降级处理
- 子进程异常退出时的恢复
- 并发调用多个工具

---

## 📋 验收清单

### 功能验收

- [ ] 智谱搜索可以正常返回中文搜索结果
- [ ] Zai视觉可以正确分析图片内容
- [ ] 两个MCP服务器可以同时运行
- [ ] Agent可以通过统一的Tool接口调用MCP
- [ ] 完整的PPT生成流程可以端到端执行

### 性能验收

- [ ] 智谱搜索响应时间 < 3s
- [ ] Zai视觉分析时间 < 5s
- [ ] MCP服务器启动时间 < 10s
- [ ] 端到端PPT生成时间 < 60s

### 稳定性验收

- [ ] MCP服务器异常可以自动重试
- [ ] 网络错误可以降级处理
- [ ] API限流可以正确处理
- [ ] 资源正确释放（进程关闭）

---

## 🐛 常见问题

### Q1: npx命令找不到

**解决**：
1. 确认Node.js已正确安装
2. 重新打开终端（刷新环境变量）
3. Windows可能需要重启电脑

### Q2: 智谱API Key无效

**解决**：
1. 确认API Key格式正确
2. 检查环境变量是否正确加载
3. 访问控制台查看使用情况

### Q3: Zai MCP Server启动失败

**解决**：
1. 检查网络连接
2. 确认ZAI_API_KEY正确
3. 更新npx: `npm update -g npx`

### Q4: 视觉分析超时

**解决**：
1. 检查网络连接
2. 减小图片尺寸
3. 降低detail_level
4. 添加重试机制

---

## 📚 参考资源

### 官方文档
- MCP协议规范: https://modelcontextprotocol.io/
- Python SDK文档: https://github.com/modelcontextprotocol/python-sdk
- 智谱AI开放平台: https://open.bigmodel.cn/

### 项目文档
- [架构设计](./ARCHITECTURE.md) - 详细架构说明
- [需求文档](./REQUIREMENTS.md) - 功能需求
- [配置指南](./API-GUIDE.md) - 环境配置
- [使用示例](./EXAMPLES.md) - 代码示例

---

## 📝 实施建议

### 开发顺序

1. **先实现HTTP客户端**（更简单，容易调试）
2. **再实现stdio客户端**（需要处理进程管理）
3. **然后实现工具包装**（可以直接使用客户端）
4. **最后集成到注册表**（需要所有组件就绪）

### 调试技巧

1. **使用日志**：记录所有MCP调用的请求和响应
2. **Mock测试**：先用Mock数据测试客户端逻辑
3. **分步验证**：先测试单独的客户端，再测试完整流程

### 代码规范

1. **异步编程**：所有MCP调用都是异步的，使用async/await
2. **错误处理**：每个层级都要有适当的错误处理
3. **资源管理**：确保连接和进程正确关闭

---

**文档版本**: v1.0
**最后更新**: 2026-03-07
**预计工期**: 6天
**维护状态**: ✅ 活跃维护
