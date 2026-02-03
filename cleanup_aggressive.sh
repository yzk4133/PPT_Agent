#!/bin/bash
# 激进清理方案 - 需要先重构代码依赖
# ⚠️ 警告：执行前请先备份整个项目！

set -e

echo "🔧 激进清理方案"
echo "===================="
echo ""

# 第一步：提取共享的子Agent到common
echo "📦 Step 1: 提取共享子Agent..."
mkdir -p backend/common/agents

# 复制子Agent
cp -r backend/slide_agent/slide_agent/sub_agents/* backend/common/agents/
echo "✅ 已复制 sub_agents 到 common/agents"

# 第二步：更新flat_slide_agent的导入
echo ""
echo "📝 Step 2: 更新 flat_slide_agent 的导入路径..."
echo "⚠️ 需要手动修改 flat_root_agent.py 的导入语句："
echo "   from slide_agent.sub_agents.* → from common.agents.*"

# 第三步：删除原slide_agent
echo ""
echo "🗑️  Step 3: 删除原 slide_agent..."
rm -rf backend/slide_agent
echo "✅ 已删除 slide_agent"

# 第四步：删除其他冗余模块
echo ""
echo "🗑️  Step 4: 删除其他冗余模块..."

# 删除未使用的ppt_api
rm -rf backend/ppt_api
echo "✅ 已删除 ppt_api"

# 删除实验性super_agent及其依赖
rm -rf backend/super_agent
rm -rf backend/simplePPT
rm -rf backend/simpleOutline
echo "✅ 已删除 super_agent, simplePPT, simpleOutline"

# 删除前端（可选）
read -p "是否删除 multiagent_front 前端? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf backend/multiagent_front
    echo "✅ 已删除 multiagent_front"
fi

# 迁移文档
echo ""
echo "📚 Step 5: 迁移文档..."
mkdir -p docs
mv backend/doc/* docs/ 2>/dev/null || true
mv backend/docs/* docs/ 2>/dev/null || true
rm -rf backend/doc backend/docs
echo "✅ 已迁移文档"

echo ""
echo "✅ 激进清理完成！"
echo ""
echo "⚠️ 接下来需要手动操作："
echo "1. 更新 backend/flat_slide_agent/agents/flat_root_agent.py"
echo "2. 将所有 from slide_agent.sub_agents 改为 from common.agents"
echo "3. 运行测试确保功能正常"
