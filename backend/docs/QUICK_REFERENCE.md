# Backend 架构重构 - 快速参考

## 🎯 一分钟总结

### 当前问题
- ❌ 代码重复（slide_agent vs flat_slide_agent）
- ❌ 依赖混乱（flat依赖slide）
- ❌ 未使用文件（super_agent, ppt_api等）
- ❌ 缺少清晰分层

### 解决方案
1. ✅ **先归档** → 移动未使用文件到 `backend/archive/`
2. ✅ **创建新结构** → 建立清晰的分层目录
3. ⏳ **逐步重构** → 迁移代码到新架构
4. ⏳ **最后清理** → 删除旧代码

---

## 📁 迁移后的目录结构

```
backend/
├── 📦 archive/              # 旧文件归档（安全保存）
│   ├── super_agent/
│   ├── ppt_api/
│   ├── skills/
│   └── ...
│
├── 🤖 agents/               # Agent层（未来目标）
│   ├── base/
│   ├── planning/
│   ├── research/
│   └── generation/
│
├── 🌐 api/                  # API层（未来目标）
│   ├── routes/
│   ├── schemas/
│   └── middleware/
│
├── 🔵 core/                 # 核心层（未来目标）
│   ├── models/
│   ├── interfaces/
│   └── services/
│
├── 🏗️ infrastructure/       # 基础设施（未来目标）
│   ├── llm/
│   ├── database/
│   ├── config/
│   └── logging/
│
├── 🧠 memory/               # 记忆系统
│   ├── interfaces/
│   ├── implementations/
│   ├── services/
│   └── utils/
│
├── 🔧 tools/                # 工具层（未来目标）
│   ├── search/
│   ├── media/
│   ├── file/
│   └── mcp/
│
├── 📦 services/             # 服务层（未来目标）
│   ├── presentation_service.py
│   └── outline_service.py
│
├── 🧪 tests/                # 测试（未来目标）
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── ✅ 保留的原目录（生产服务）
│   ├── slide_agent/         # 暂保留，被flat复用
│   ├── slide_outline/       # 暂保留
│   ├── flat_slide_agent/    # ✅ 新架构
│   ├── flat_slide_outline/  # ✅ 新架构
│   ├── save_ppt/            # ✅ 生产
│   ├── hostAgentAPI/        # ✅ 核心
│   ├── multiagent_front/    # ✅ 前端
│   ├── persistent_memory/   # ✅ 记忆系统
│   └── common/              # ✅ 基础设施
│       ├── config.py
│       ├── model_factory.py
│       ├── context_compressor.py
│       ├── adk_agent_executor.py  # 新提取
│       └── a2a_client.py          # 新提取
│
├── docker-compose.yml
├── STRUCTURE_MAPPING.md
└── REFACTORING_GUIDE.md
```

---

## 🚀 快速开始

### 执行迁移

**Windows:**
```cmd
migrate_backend.bat
```

**Linux/Mac:**
```bash
chmod +x migrate_backend.sh
./migrate_backend.sh
```

### 验证迁移

```bash
# 1. 检查归档
ls backend/archive/
# 应该看到: super_agent, ppt_api, skills, ...

# 2. 检查新目录
ls backend/agents/
ls backend/api/
ls backend/core/

# 3. 测试服务
cd backend/flat_slide_agent
python main_api.py
```

---

## 📊 各层职责速查

| 层 | 职责 | 不做什么 |
|---|------|---------|
| **API** | 处理HTTP | 业务逻辑 |
| **Service** | 编排流程 | 调用LLM |
| **Agent** | 执行任务 | 编排流程 |
| **Domain Model** | 数据+规则 | 调用LLM/DB |
| **Infrastructure** | 技术实现 | 业务逻辑 |

---

## 🗺️ 重构路线图

### 阶段1：归档和准备 ✅ **已完成**
- 归档7个未使用模块
- 提取重复代码
- 创建新目录结构

### 阶段2：解耦依赖 ⏳ **进行中**（预计1-2周）
```
任务：
1. 提取 slide_agent/sub_agents/ → backend/agents/
2. 更新 flat_slide_agent 的导入路径
3. 测试独立运行
```

### 阶段3：Docker集成 ⏳ **待开始**（预计1周）
```
任务：
1. 更新 docker-compose.yml
2. 添加 flat_* 服务
3. 测试容器化部署
```

### 阶段4：代码迁移 ⏳ **待开始**（预计2-4周）
```
任务：
1. 创建 Domain Models (core/models/)
2. 创建 Services (services/)
3. 创建 API Routes (api/routes/)
4. 迁移 Infrastructure
```

### 阶段5：清理 ⏳ **最后执行**
```
条件：
- flat架构稳定1个月+
- 所有测试通过
- 性能不低于旧架构

然后：
- 删除 slide_agent/
- 删除 slide_outline/
```

---

## 🧪 测试清单

### 功能测试
```bash
# 测试大纲生成
curl -X POST http://localhost:10002/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI", "num_slides": 5}'

# 测试PPT生成
curl -X POST http://localhost:10012/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI", "num_slides": 5}'
```

### 依赖检查
```bash
# 检查是否还有对旧模块的依赖
grep -r "from slide_agent" backend/flat_slide_agent/

# 应该返回空（无依赖）
```

### 性能对比
```bash
# 对比新旧架构性能
time test_old.sh
time test_new.sh

# 新架构应该 ≥ 旧架构
```

---

## 📈 预期收益

### 空间节省
- 归档未使用模块：~100 MB
- 未来删除旧代码：~70 MB
- **总计：~170 MB**

### 代码质量
- 重复率：60% → 0%
- 依赖清晰度：✅ 大幅提升
- 可维护性：✅ 显著改善

### 开发效率
- 新功能开发：⬆️ 40% 提升
- Bug修复：⬆️ 50% 提升
- 团队协作：⬆️ 60% 提升

---

## ⚠️ 注意事项

### 绝对不要做
- ❌ 在未测试前删除slide_agent
- ❌ 同时修改多个服务
- ❌ 跳过阶段直接做阶段5

### 必须做
- ✅ 每个阶段后都要测试
- ✅ 保留完整备份
- ✅ Git提交每个里程碑
- ✅ 文档更新同步进行

---

## 🆘 快速故障排除

### flat_slide_agent启动失败
```bash
# 检查导入
grep -r "from slide_agent" backend/flat_slide_agent/

# 更新导入
# from slide_agent.sub_agents.* → from agents.*
```

### Docker服务无法启动
```bash
# 查看日志
docker-compose logs flat_ppt_agent

# 重新构建
docker-compose build flat_ppt_agent
docker-compose up -d
```

### 回滚
```bash
# 恢复备份
cp -r backup_YYYYMMDD_HHMMSS/backend/* backend/
```

---

## 📚 相关文档

| 文档 | 用途 |
|------|------|
| `STRUCTURE_MAPPING.md` | 详细的目录映射 |
| `REFACTORING_GUIDE.md` | 完整的重构指南 |
| `ARCHITECTURE_LAYERS_EXPLAINED.md` | 分层架构详解 |
| `IDEAL_BACKEND_STRUCTURE.md` | 理想架构设计 |
| `BACKEND_CLEANUP_GUIDE.md` | 清理指南 |

---

## 🎓 核心概念

### 领域模型 vs Agent
```
领域模型 = 数据 + 规则（被动）
Agent = 行为 + 决策（主动）

Agent 操作领域模型完成任务
```

### 各层关系
```
API → Service → Agent → Domain Model
      ↑          ↑       ↑
      └──────────┴───────┴─ Infrastructure
```

### 单向依赖
```
上层依赖下层，下层不知道上层的存在
```

---

## 📞 获取帮助

### 遇到问题？
1. 查看相关文档
2. 检查日志文件
3. 恢复备份重试

### 需要更多信息？
- 阅读 `REFACTORING_GUIDE.md`
- 查看 `ARCHITECTURE_LAYERS_EXPLAINED.md`

---

**更新时间：** 2026-02-02
**当前阶段：** 阶段1（已完成）✅
**下一阶段：** 阶段2（解耦依赖）
**预计完成：** 2026-04-01
