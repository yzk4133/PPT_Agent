#!/bin/bash
# 保守清理方案 - 只删除确定不需要的部分
# ✅ 安全：不影响任何现有功能

set -e

echo "🧹 保守清理方案"
echo "===================="
echo ""

# 创建备份
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "📦 创建备份: $BACKUP_DIR"
cp -r backend "$BACKUP_DIR/"

# 删除未使用的ppt_api
echo ""
echo "🗑️  1/4: 删除 ppt_api (完全未使用)..."
if [ -d "backend/ppt_api" ]; then
    rm -rf backend/ppt_api
    echo "✅ 已删除 ppt_api/"
else
    echo "⚠️  ppt_api 不存在，跳过"
fi

# 删除空壳目录
echo ""
echo "🗑️  2/4: 删除 super_agent 的空子模块..."
if [ -d "backend/super_agent/simpleArtical" ]; then
    rm -rf backend/super_agent/simpleArtical
    echo "✅ 已删除 super_agent/simpleArtical/"
fi

if [ -d "backend/super_agent/simpleOutline" ]; then
    rm -rf backend/super_agent/simpleOutline
    echo "✅ 已删除 super_agent/simpleOutline/"
fi

# 迁移文档
echo ""
echo "🗑️  3/4: 迁移文档到根目录..."
if [ -d "backend/doc" ]; then
    mkdir -p docs
    cp -r backend/doc/* docs/ 2>/dev/null || true
    rm -rf backend/doc
    echo "✅ 已迁移 backend/doc/"
fi

if [ -d "backend/docs" ]; then
    mkdir -p docs
    cp -r backend/docs/* docs/ 2>/dev/null || true
    rm -rf backend/docs
    echo "✅ 已迁移 backend/docs/"
fi

# 清理测试文件（可选）
echo ""
read -p "🗑️  4/4: 是否删除测试文件? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f backend/test_*.py
    rm -f backend/demo_*.py
    echo "✅ 已删除测试文件"
fi

echo ""
echo "✅ 保守清理完成！"
echo ""
echo "📊 清理结果:"
echo "   - 删除: ppt_api/ (未使用)"
echo "   - 删除: super_agent/simpleArtical/ (空壳)"
echo "   - 删除: super_agent/simpleOutline/ (空壳)"
echo "   - 迁移: doc/ 和 docs/ → 项目根目录"
echo ""
echo "💾 备份位置: $BACKUP_DIR"
echo ""
echo "⚠️ 注意：以下模块仍然保留（需要手动评估）"
echo "   - super_agent/ (实验性功能)"
echo "   - multiagent_front/ (Web前端)"
echo "   - simplePPT/ 和 simpleOutline/ (被super_agent使用)"
echo "   - slide_agent/ (被flat_slide_agent依赖，需重构)"
echo ""
echo "💡 提示：如果确认不需要，可以手动删除这些模块"
