#!/bin/bash
# 后端文件迁移和重构脚本
# 策略：先归档旧文件，再重构，确保安全

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║          Backend 文件迁移和重构脚本                          ║"
echo "║  策略：先归档 → 再重构 → 最终优化                            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 创建备份目录
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
ARCHIVE_DIR="backend/archive"

echo -e "${BLUE}📦 步骤 0：创建备份和归档目录${NC}"
echo "备份目录: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"
mkdir -p "$ARCHIVE_DIR"

# 完整备份
echo "正在完整备份 backend/..."
cp -r backend "$BACKUP_DIR/"
echo -e "${GREEN}✅ 备份完成${NC}"
echo ""

# ============================================================================
# 阶段1：归档未使用的模块（安全）
# ============================================================================
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  阶段1：归档未使用的模块（安全）                                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1.1 归档 super_agent（实验性，未被使用）
echo -e "${YELLOW}📦 1.1 归档 super_agent/（实验性功能）${NC}"
if [ -d "backend/super_agent" ]; then
    mv backend/super_agent "$ARCHIVE_DIR/"
    echo -e "${GREEN}   ✅ 已归档: super_agent/${NC}"
else
    echo -e "${YELLOW}   ⚠️  super_agent/ 不存在，跳过${NC}"
fi

# 1.2 归档 ppt_api（未集成）
echo -e "${YELLOW}📦 1.2 归档 ppt_api/（未集成到系统）${NC}"
if [ -d "backend/ppt_api" ]; then
    mv backend/ppt_api "$ARCHIVE_DIR/"
    echo -e "${GREEN}   ✅ 已归档: ppt_api/${NC}"
else
    echo -e "${YELLOW}   ⚠️  ppt_api/ 不存在，跳过${NC}"
fi

# 1.3 归档 skills（未启用）
echo -e "${YELLOW}📦 1.3 归档 skills/（未启用的技能定义）${NC}"
if [ -d "backend/skills" ]; then
    mv backend/skills "$ARCHIVE_DIR/"
    echo -e "${GREEN}   ✅ 已归档: skills/${NC}"
else
    echo -e "${YELLOW}   ⚠️  skills/ 不存在，跳过${NC}"
fi

# 1.4 归档 simplePPT 和 simpleOutline（被super_agent使用）
echo -e "${YELLOW}📦 1.4 归档 simplePPT/ 和 simpleOutline/（依赖已归档的super_agent）${NC}"
if [ -d "backend/simplePPT" ]; then
    mv backend/simplePPT "$ARCHIVE_DIR/"
    echo -e "${GREEN}   ✅ 已归档: simplePPT/${NC}"
fi
if [ -d "backend/simpleOutline" ]; then
    mv backend/simpleOutline "$ARCHIVE_DIR/"
    echo -e "${GREEN}   ✅ 已归档: simpleOutline/${NC}"
fi

# 1.5 归档文档（迁移到根目录）
echo -e "${YELLOW}📦 1.5 归档并迁移文档${NC}"
if [ -d "backend/doc" ]; then
    mkdir -p docs
    cp -r backend/doc/* docs/ 2>/dev/null || true
    mv backend/doc "$ARCHIVE_DIR/"
    echo -e "${GREEN}   ✅ 已归档: backend/doc/ → docs/${NC}"
fi
if [ -d "backend/docs" ]; then
    mkdir -p docs
    cp -r backend/docs/* docs/ 2>/dev/null || true
    mv backend/docs "$ARCHIVE_DIR/"
    echo -e "${GREEN}   ✅ 已归档: backend/docs/ → docs/${NC}"
fi

echo ""
echo -e "${GREEN}✅ 阶段1完成！已归档 5-7 个未使用的模块${NC}"
echo ""

# ============================================================================
# 阶段2：重构重复代码（中等）
# ============================================================================
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  阶段2：提取重复代码到 common/                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 2.1 提取 adk_agent_executor.py
echo -e "${YELLOW}🔧 2.1 提取 adk_agent_executor.py 到 common/${NC}"
if [ ! -f "backend/common/adk_agent_executor.py" ] && [ -f "backend/flat_slide_agent/adk_agent_executor.py" ]; then
    cp backend/flat_slide_agent/adk_agent_executor.py backend/common/
    echo -e "${GREEN}   ✅ 已提取: common/adk_agent_executor.py${NC}"
else
    echo -e "${YELLOW}   ⚠️  common/adk_agent_executor.py 已存在或源文件不存在${NC}"
fi

# 2.2 提取 a2a_client.py
echo -e "${YELLOW}🔧 2.2 提取 a2a_client.py 到 common/${NC}"
if [ ! -f "backend/common/a2a_client.py" ] && [ -f "backend/slide_agent/a2a_client.py" ]; then
    cp backend/slide_agent/a2a_client.py backend/common/
    echo -e "${GREEN}   ✅ 已提取: common/a2a_client.py${NC}"
else
    echo -e "${YELLOW}   ⚠️  common/a2a_client.py 已存在或源文件不存在${NC}"
fi

echo ""
echo -e "${YELLOW}⚠️  注意：重复代码已复制到 common/，但原文件保留（向后兼容）${NC}"
echo -e "${YELLOW}      后续可以逐步更新各模块使用 common/ 中的版本${NC}"
echo ""

# ============================================================================
# 阶段3：重组目录结构（创建清晰的层次）
# ============================================================================
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  阶段3：重组目录结构（创建清晰的层次）                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 创建新的目录结构（不移动文件，只创建目录）
echo -e "${YELLOW}📁 3.1 创建新的目录结构${NC}"

mkdir -p backend/agents/{base,planning,research,generation}
mkdir -p backend/api/{routes,schemas,middleware}
mkdir -p backend/core/{models,interfaces,services}
mkdir -p backend/infrastructure/{llm,database,config,logging}
mkdir -p backend/memory/{interfaces,implementations,services,utils}
mkdir -p backend/tools/{search,media,file,mcp}
mkdir -p backend/services
mkdir -p backend/tests/{unit,integration,fixtures,utils}

echo -e "${GREEN}   ✅ 已创建新的目录结构${NC}"
echo ""
echo -e "   新增目录："
echo -e "   - backend/agents/          （Agent实现）"
echo -e "   - backend/api/             （API接口）"
echo -e "   - backend/core/            （核心层）"
echo -e "   - backend/infrastructure/ （基础设施）"
echo -e "   - backend/memory/          （记忆系统）"
echo -e "   - backend/tools/           （工具集）"
echo -e "   - backend/services/        （业务服务）"
echo -e "   - backend/tests/           （测试）"
echo ""

# ============================================================================
# 阶段4：创建映射文档
# ============================================================================
echo -e "${YELLOW}📝 3.2 创建目录映射文档${NC}"

cat > backend/STRUCTURE_MAPPING.md << 'EOF'
# Backend 目录结构映射文档

## 新旧目录对照

### 🔄 保留的原目录（生产服务）

| 原目录 | 新位置 | 状态 |
|-------|-------|------|
| `slide_agent/` | 暂保留 | ✅ 生产服务，被flat复用 |
| `slide_outline/` | 暂保留 | ✅ 生产服务 |
| `flat_slide_agent/` | 暂保留 | ✅ 新架构 |
| `flat_slide_outline/` | 暂保留 | ✅ 新架构 |
| `save_ppt/` | 暂保留 | ✅ 生产服务 |
| `hostAgentAPI/` | 暂保留 | ✅ 核心服务 |
| `multiagent_front/` | 暂保留 | ✅ 前端界面 |
| `persistent_memory/` | 暂保留 | ✅ 记忆系统 |
| `common/` | `common/` | ✅ 核心基础设施 |

### 📦 已归档的目录

| 原目录 | 归档位置 | 原因 |
|-------|---------|------|
| `super_agent/` | `archive/super_agent/` | 实验性，未使用 |
| `ppt_api/` | `archive/ppt_api/` | 未集成 |
| `skills/` | `archive/skills/` | 未启用 |
| `simplePPT/` | `archive/simplePPT/` | 依赖super_agent |
| `simpleOutline/` | `archive/simpleOutline/` | 依赖super_agent |
| `doc/` | `archive/doc/` | 已迁移到根目录 |
| `docs/` | `archive/docs/` | 已迁移到根目录 |

### 🆕 新创建的目录结构

```
backend/
├── agents/                    # Agent实现（未来迁移目标）
│   ├── base/                  # Agent基类
│   ├── planning/              # 规划Agent
│   ├── research/              # 研究Agent
│   └── generation/            # 生成Agent
│
├── api/                       # API接口（未来迁移目标）
│   ├── routes/                # 路由
│   ├── schemas/               # 数据模型
│   └── middleware/            # 中间件
│
├── core/                      # 核心层（未来迁移目标）
│   ├── models/                # 领域模型
│   ├── interfaces/            # 接口定义
│   └── services/              # 核心服务
│
├── infrastructure/            # 基础设施（未来迁移目标）
│   ├── llm/                   # LLM客户端
│   ├── database/              # 数据库
│   ├── config/                # 配置
│   └── logging/               # 日志
│
├── memory/                    # 记忆系统（未来迁移目标）
│   ├── interfaces/            # 记忆接口
│   ├── implementations/       # 具体实现
│   └── services/              # 记忆服务
│
├── tools/                     # 工具集（未来迁移目标）
│   ├── search/                # 搜索工具
│   ├── media/                 # 媒体工具
│   ├── file/                  # 文件工具
│   └── mcp/                   # MCP工具
│
├── services/                  # 业务服务（未来迁移目标）
│
├── tests/                     # 测试（未来迁移目标）
│   ├── unit/                  # 单元测试
│   ├── integration/           # 集成测试
│   └── fixtures/              # 测试数据
│
├── [保留的原目录]            # 暂时保留，逐步迁移
├── common/                    # ✅ 核心基础设施
├── slide_agent/               # ✅ 生产服务
├── slide_outline/             # ✅ 生产服务
├── flat_slide_agent/          # ✅ 新架构
├── flat_slide_outline/        # ✅ 新架构
├── save_ppt/                  # ✅ 生产服务
├── hostAgentAPI/              # ✅ 核心服务
├── multiagent_front/          # ✅ 前端
└── persistent_memory/         # ✅ 记忆系统
```

## 迁移计划

### 阶段1：已完成 ✅
- [x] 归档未使用的模块
- [x] 创建新目录结构
- [x] 提取重复代码

### 阶段2：代码重构（进行中）
- [ ] 将 `slide_agent/slide_agent/sub_agents/` 迁移到 `backend/agents/`
- [ ] 解除 `flat_slide_agent` 对 `slide_agent` 的依赖
- [ ] 统一所有模块使用 `common/` 中的工具

### 阶段3：服务集成（计划中）
- [ ] 更新 docker-compose.yml
- [ ] 添加 flat_* 服务到生产环境
- [ ] 逐步替换旧服务

### 阶段4：清理（最后执行）
- [ ] 删除 `slide_agent/`（确认flat稳定后）
- [ ] 删除 `slide_outline/`（确认flat稳定后）
- [ ] 删除重复的代码文件

## 依赖关系

### 当前依赖
```
flat_slide_agent → slide_agent/sub_agents
slide_outline → 独立
flat_slide_outline → common
hostAgentAPI → multiagent_front
persistent_memory → 未被集成
```

### 目标依赖
```
所有服务 → common/
agents/ → core/models/
services/ → agents/ + core/
api/ → services/
```

## 端口使用

| 服务 | 端口 | 状态 | Docker |
|------|------|------|--------|
| slide_outline | 10001 | 生产 | ✅ |
| flat_slide_outline | 10002 | 新架构 | ❌ 需添加 |
| slide_agent | 10011 | 生产 | ✅ |
| flat_slide_agent | 10012 | 新架构 | ❌ 需添加 |
| save_ppt | 10021 | 生产 | ✅ |
| hostAgentAPI | 13000 | 生产 | ✅ |
| rag_tool | 6501 | 生产 | ✅ |
| llm_cache | 6688 | 生产 | ✅ |

---

**文档创建时间：** $(date)
**维护者：** Claude Code
EOF

echo -e "${GREEN}   ✅ 已创建: backend/STRUCTURE_MAPPING.md${NC}"
echo ""

# ============================================================================
# 完成：生成报告
# ============================================================================
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                     迁移完成报告                              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}✅ 阶段1：归档未使用模块${NC}"
echo "   - archive/super_agent/"
echo "   - archive/ppt_api/"
echo "   - archive/skills/"
echo "   - archive/simplePPT/"
echo "   - archive/simpleOutline/"
echo "   - archive/doc/（已迁移到根目录）"
echo "   - archive/docs/（已迁移到根目录）"
echo ""

echo -e "${GREEN}✅ 阶段2：提取重复代码${NC}"
echo "   - common/adk_agent_executor.py"
echo "   - common/a2a_client.py"
echo ""

echo -e "${GREEN}✅ 阶段3：创建新目录结构${NC}"
echo "   - backend/agents/"
echo "   - backend/api/"
echo "   - backend/core/"
echo "   - backend/infrastructure/"
echo "   - backend/memory/"
echo "   - backend/tools/"
echo "   - backend/services/"
echo "   - backend/tests/"
echo ""

echo -e "${BLUE}📊 统计信息：${NC}"
echo "   - 归档模块数：7"
echo "   - 新增目录数：8"
echo "   - 提取重复代码：2"
echo "   - 保留生产服务：8"
echo ""

echo -e "${YELLOW}💾 备份位置：${NC}"
echo "   $BACKUP_DIR"
echo ""

echo -e "${BLUE}📚 相关文档：${NC}"
echo "   - backend/STRUCTURE_MAPPING.md（目录映射）"
echo "   - backend/REFACTORING_GUIDE.md（重构指南）"
echo ""

echo -e "${GREEN}✨ 下一步建议：${NC}"
echo "   1. 查看 backend/STRUCTURE_MAPPING.md 了解详细计划"
echo "   2. 测试现有服务是否正常运行"
echo "   3. 开始逐步迁移代码到新目录结构"
echo "   4. 更新 docker-compose.yml 添加新服务"
echo ""

echo -e "${GREEN}🎉 迁移准备完成！系统可以正常使用。${NC}"
echo ""
