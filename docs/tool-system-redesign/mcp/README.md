# MCP集成文档

> MultiAgentPPT项目的MCP（Model Context Protocol）集成完整文档

---

## 📚 文档导航

| 文档 | 说明 | 适用场景 |
|------|------|----------|
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | 架构设计 | 理解MCP集成的整体架构和设计思路 |
| **[REQUIREMENTS.md](./REQUIREMENTS.md)** | 需求文档 | 了解MCP集成的完整需求和功能规格 |
| **[IMPLEMENTATION-GUIDE.md](./IMPLEMENTATION-GUIDE.md)** | 实现指南 | 从零开始的完整实现步骤 |
| **[API-GUIDE.md](./API-GUIDE.md)** | 配置指南 | 学习如何配置MCP服务器和环境 |
| **[EXAMPLES.md](./EXAMPLES.md)** | 使用示例 | 查看代码示例和最佳实践 |

---

## 🎯 快速开始

### 1️⃣ 理解架构

```bash
# 查看架构设计
cat docs/tool-system-redesign/mcp/ARCHITECTURE.md
```

**你将了解到**:
- ✅ MCP协议的核心概念
- ✅ 系统分层架构
- ✅ 数据流向和组件职责
- ✅ 为什么需要两种传输方式

### 2️⃣ 阅读需求

```bash
# 查看需求文档
cat docs/tool-system-redesign/mcp/REQUIREMENTS.md
```

**你将了解到**:
- ✅ 为什么需要MCP
- ✅ 2个MCP服务器选型
- ✅ 能力分配方案
- ✅ 验收标准

### 3️⃣ 开始实现

```bash
# 查看实现指南
cat docs/tool-system-redesign/mcp/IMPLEMENTATION-GUIDE.md
```

**你将完成**:
- ✅ 环境准备和配置
- ✅ MCP客户端层实现
- ✅ 工具包装层实现
- ✅ 工具注册和测试

### 4️⃣ 配置环境

```bash
# 查看配置指南
cat docs/tool-system-redesign/mcp/API-GUIDE.md
```

**你将完成**:
- ✅ 安装Node.js和npx
- ✅ 申请智谱AI API Key
- ✅ 创建MCP配置文件
- ✅ 测试MCP服务器

### 5️⃣ 查看示例代码

```bash
# 查看使用示例
cat docs/tool-system-redesign/mcp/EXAMPLES.md
```

**你将学到**:
- ✅ 基础用法
- ✅ 完整流程示例
- ✅ 最佳实践
- ✅ 常见场景处理

---

## 📦 MCP服务器清单

本项目集成的MCP服务器：

| 服务器 | 类型 | 功能 | 状态 |
|--------|------|------|------|
| **zhipu web-search-prime** | HTTP | 高质量网络搜索 | ✅ 已确定 |
| **zai-mcp-server** | stdio | 图片视觉理解 | ✅ 已确定 |

---

## 🏗️ 系统架构

```
PPT生成Agent (本地)
    │
    ├─ LLM本地调用 (LangChain)
    │   └─ OpenAI/Claude API
    │
    └─ Tool Registry
        │
        ├─ 本地Tool (python-pptx, image_processor等)
        │
        └─ MCP Tool
            ├─ zhipu_web_search (HTTP)
            └─ zai_vision (stdio)
```

---

## 🚀 快速启动

### 前置要求

- [ ] Node.js >= 18.0.0
- [ ] Python >= 3.10
- [ ] 智谱AI API Key

### 环境配置

```bash
# 1. 安装Zai MCP Server
npm install -g @z_ai/mcp-server

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 ZHIPU_API_KEY 和 ZAI_API_KEY

# 3. 测试MCP服务器
# 测试智谱搜索（HTTP）
curl -X POST "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp" \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"query": "AI", "count": 5}'

# 测试Zai视觉（stdio）
npx -y @z_ai/mcp-server
```

---

## 📊 MCP工具能力

### 智谱 web-search-prime

- **功能**: 高质量网络搜索
- **优势**: 中文搜索优化，结果质量高
- **部署**: HTTP远程服务
- **成本**: 已包含在Coding Plan中

**适用场景**:
- 搜索PPT主题相关资料
- 查找案例和数据
- 获取行业报告

### Zai MCP Server

- **功能**: 图片视觉理解
- **能力**:
  - 图片内容分析
  - OCR文字识别
  - 视觉问答
  - 图片对比
- **部署**: 本地子进程
- **模型**: 智谱AI视觉模型

**适用场景**:
- 分析图片内容
- 选择合适的配图
- 提取图片中的文字
- 生成图片描述

---

## 📝 开发计划

| 阶段 | 内容 | 预计时间 | 状态 |
|------|------|----------|------|
| Phase 1 | 环境准备 | 1天 | ⏳ 待开始 |
| Phase 2 | 配置管理 | 0.5天 | ⏳ 待开始 |
| Phase 3 | MCP客户端层 | 1.5天 | ⏳ 待开始 |
| Phase 4 | 工具包装层 | 1天 | ⏳ 待开始 |
| Phase 5 | 工具注册集成 | 0.5天 | ⏳ 待开始 |
| Phase 6 | 测试验证 | 1.5天 | ⏳ 待开始 |

**总计**: 约6天

详见 [实现指南](./IMPLEMENTATION-GUIDE.md)

---

## 🔗 相关链接

### 官方文档

- [MCP协议规范](https://modelcontextprotocol.io/)
- [智谱AI开放平台](https://open.bigmodel.cn/)
- [Zai MCP Server](https://www.npmjs.com/package/@z_ai/mcp-server)

### 项目文档

- [工具系统需求](../REQUIREMENTS.md)
- [工具系统实施](../IMPLEMENTATION.md)

---

## 🐛 问题反馈

遇到问题？

1. 查看 [API-GUIDE.md](./API-GUIDE.md) 的常见问题排查
2. 检查日志文件: `logs/mcp_*.log`
3. 提交Issue到项目仓库

---

## 📝 更新日志

### v2.1 (2026-03-07)

- ✅ 新增架构设计文档 (ARCHITECTURE.md)
- ✅ 新增实现指南文档 (IMPLEMENTATION-GUIDE.md)
- ✅ 完善文档导航结构
- ✅ 统一开发计划描述

### v2.0 (2026-03-07)

- ✅ 精简为2个MCP服务器
- ✅ 添加Zai视觉理解工具
- ✅ 更新配置和使用示例
- ✅ 移除Filesystem和Puppeteer

### v1.0 (2026-03-07)

- ✅ 初始版本
- ✅ 3个MCP服务器设计

---

**文档版本**: v2.0
**最后更新**: 2026-03-07
**维护状态**: ✅ 活跃维护
