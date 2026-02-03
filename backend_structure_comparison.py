"""
后端目录结构对比可视化

生成当前结构 vs 理想结构的对比图
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

import sys
import io

# 设置 stdout 编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 12))
fig.suptitle('后端目录结构对比：当前 vs 理想', fontsize=18, fontweight='bold')

# ============ 当前结构 ============
current_modules = [
    ('slide_agent', 45, 'red', '核心'),
    ('flat_slide_agent', 30, 'orange', '依赖slide_agent'),
    ('slide_outline', 20, 'red', '核心'),
    ('flat_slide_outline', 15, 'orange', '优化版'),
    ('simplePPT', 10, 'gray', '未使用'),
    ('simpleOutline', 8, 'gray', '未使用'),
    ('super_agent', 12, 'gray', '实验性'),
    ('ppt_api', 10, 'gray', '未使用'),
    ('save_ppt', 15, 'green', '核心'),
    ('hostAgentAPI', 25, 'green', '核心'),
    ('multiagent_front', 20, 'blue', '前端'),
    ('persistent_memory', 18, 'green', '核心'),
    ('common', 22, 'green', '核心'),
    ('skill_framework', 15, 'purple', '未来'),
    ('skills', 12, 'purple', '未来'),
]

y_pos = 0
for name, size, color, label in current_modules:
    # 绘制模块
    box = FancyBboxPatch((0, y_pos), size, 0.8,
                         boxstyle="round,pad=0.05",
                         edgecolor='black', facecolor=color, alpha=0.7, linewidth=1.5)
    ax1.add_patch(box)

    # 添加名称和大小
    ax1.text(size/2, y_pos + 0.4, f'{name}\n{size}MB',
             ha='center', va='center', fontsize=9, fontweight='bold', color='white')

    # 添加标签
    ax1.text(size + 2, y_pos + 0.4, label,
             ha='left', va='center', fontsize=8, color='black')

    y_pos += 1.2

ax1.set_xlim(0, 60)
ax1.set_ylim(y_pos, -2)
ax1.set_title('🔴 当前结构（混乱）', fontsize=14, fontweight='bold', pad=20)
ax1.axis('off')

# 添加图例
legend_elements = [
    mpatches.Patch(color='red', label='重复代码'),
    mpatches.Patch(color='orange', label='依赖问题'),
    mpatches.Patch(color='gray', label='未使用'),
    mpatches.Patch(color='green', label='核心模块'),
    mpatches.Patch(color='blue', label='前端'),
    mpatches.Patch(color='purple', label='未来'),
]
ax1.legend(handles=legend_elements, loc='upper right', fontsize=9)

# 统计信息
current_total = sum(size for _, size, _, _ in current_modules)
current_dup = sum(size for _, size, color, _ in current_modules if color in ['red', 'orange'])
current_unused = sum(size for _, size, color, _ in current_modules if color == 'gray')

stats_text = f'''
📊 统计信息
总大小: {current_total} MB
重复代码: {current_dup} MB ({current_dup/current_total*100:.1f}%)
未使用: {current_unused} MB ({current_unused/current_total*100:.1f}%)
模块数: {len(current_modules)}
'''
ax1.text(55, 2, stats_text, fontsize=9, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# ============ 理想结构 ============
ideal_modules = [
    ('核心层 core/', 15, 'blue', '领域模型'),
    ('  models/', 5, 'lightblue', ''),
    ('  interfaces/', 4, 'lightblue', ''),
    ('  services/', 6, 'lightblue', ''),

    ('Agent层 agents/', 25, 'green', '所有Agent'),
    ('  base/', 5, 'lightgreen', ''),
    ('  planning/', 8, 'lightgreen', ''),
    ('  research/', 6, 'lightgreen', ''),
    ('  generation/', 6, 'lightgreen', ''),

    ('记忆系统 memory/', 18, 'purple', '持久化+缓存'),
    ('  interfaces/', 4, 'thistle', ''),
    ('  implementations/', 8, 'thistle', ''),
    ('  services/', 6, 'thistle', ''),

    ('工具层 tools/', 12, 'orange', '可复用工具'),
    ('  search/', 4, 'moccasin', ''),
    ('  media/', 3, 'moccasin', ''),
    ('  file/', 3, 'moccasin', ''),
    ('  mcp/', 2, 'moccasin', ''),

    ('基础设施 infrastructure/', 15, 'cyan', '技术实现'),
    ('  llm/', 5, 'lightcyan', ''),
    ('  database/', 4, 'lightcyan', ''),
    ('  config/', 3, 'lightcyan', ''),
    ('  logging/', 3, 'lightcyan', ''),

    ('API层 api/', 10, 'pink', 'HTTP接口'),
    ('  routes/', 4, 'lightpink', ''),
    ('  schemas/', 3, 'lightpink', ''),
    ('  middleware/', 3, 'lightpink', ''),

    ('服务层 services/', 12, 'yellow', '业务编排'),

    ('测试 tests/', 8, 'gray', ''),
]

y_pos = 0
for name, size, color, label in ideal_modules:
    # 缩进判断
    indent = 2 if name.startswith('  ') else 0

    # 绘制模块
    box = FancyBboxPatch((indent, y_pos), size, 0.8,
                         boxstyle="round,pad=0.05",
                         edgecolor='black', facecolor=color, alpha=0.7, linewidth=1.5)
    ax2.add_patch(box)

    # 添加名称和大小
    ax2.text(indent + size/2, y_pos + 0.4, f'{name}\n{size}MB',
             ha='center', va='center', fontsize=9, fontweight='bold', color='black')

    # 添加标签（仅顶层）
    if label and not name.startswith('  '):
        ax2.text(indent + size + 1, y_pos + 0.4, label,
                 ha='left', va='center', fontsize=8, color='black')

    y_pos += 1.0

ax2.set_xlim(0, 30)
ax2.set_ylim(y_pos, -2)
ax2.set_title('✅ 理想结构（清晰）', fontsize=14, fontweight='bold', pad=20)
ax2.axis('off')

# 添加图例
legend_elements = [
    mpatches.Patch(color='blue', label='核心层'),
    mpatches.Patch(color='green', label='Agent层'),
    mpatches.Patch(color='purple', label='记忆系统'),
    mpatches.Patch(color='orange', label='工具层'),
    mpatches.Patch(color='cyan', label='基础设施'),
    mpatches.Patch(color='pink', label='API层'),
    mpatches.Patch(color='yellow', label='服务层'),
    mpatches.Patch(color='gray', label='测试'),
]
ax2.legend(handles=legend_elements, loc='upper right', fontsize=9)

# 统计信息
ideal_total = sum(size for _, size, _, _ in ideal_modules)

stats_text = f'''
📊 统计信息
总大小: {ideal_total} MB
节省空间: {current_total - ideal_total} MB
({(1-ideal_total/current_total)*100:.1f}%)
模块数: {len(ideal_modules)}
代码重复: 0%
职责清晰: ✅
易于测试: ✅
可扩展: ✅
'''
ax2.text(30, 2, stats_text, fontsize=9, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

plt.tight_layout()
plt.savefig('backend_structure_comparison.png', dpi=300, bbox_inches='tight')
print("✅ 对比图已保存: backend_structure_comparison.png")

# 打印详细对比
print("\n" + "="*80)
print("📊 后端目录结构详细对比")
print("="*80)

print("\n🔴 当前结构的问题:")
print("1. 代码重复：slide_agent (45MB) vs flat_slide_agent (30MB)")
print("2. 依赖混乱：flat_slide_agent 强依赖 slide_agent")
print("3. 未使用模块：simplePPT, simpleOutline, ppt_api, super_agent (40MB)")
print("4. 职责不清：common 既是基础设施又是业务逻辑")
print("5. 难以测试：紧耦合，难以mock")
print("6. 缺少抽象：没有明确的接口定义")

print("\n✅ 理想结构的优势:")
print("1. 单一职责：每个模块只做一件事")
print("2. 低耦合：通过接口通信")
print("3. 易测试：可以mock任何层")
print("4. 可扩展：添加新功能不影响现有代码")
print("5. 易维护：结构清晰，定位问题快")
print("6. 符合DDD：领域模型与基础设施分离")

print("\n💾 空间节省:")
print(f"当前: {current_total} MB")
print(f"理想: {ideal_total} MB")
print(f"节省: {current_total - ideal_total} MB ({(1-ideal_total/current_total)*100:.1f}%)")

print("\n🔄 迁移优先级:")
print("阶段1（本周）: 创建 core/ 和 interfaces/")
print("阶段2（本月）: 重组 agents/，解除依赖")
print("阶段3（下月）: 统一 infrastructure/")
print("阶段4（持续）: 完善 tests/")

print("\n" + "="*80)
