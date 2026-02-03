"""
上下文压缩效果可视化

生成直观的图表对比改进前后的效果
"""

import sys
import io

# 设置 stdout 编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# 设置中文字体（支持中文显示）
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# 数据
pages = list(range(1, 11))
original_tokens = [241, 487, 730, 975, 1218, 1464, 1707, 1952, 2195, 2446]
compressed_tokens = [209, 335, 458, 489, 503, 521, 526, 543, 554, 574]

# 创建图表
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('上下文压缩效果分析', fontsize=16, fontweight='bold')

# 1. Token消耗对比（折线图）
ax1 = axes[0, 0]
ax1.plot(pages, original_tokens, 'o-', label='原始方案', linewidth=2, markersize=8)
ax1.plot(pages, compressed_tokens, 'o-', label='压缩方案', linewidth=2, markersize=8)
ax1.fill_between(pages, original_tokens, compressed_tokens, alpha=0.3, color='green', label='节省的Tokens')
ax1.set_xlabel('页码', fontsize=12)
ax1.set_ylabel('Token数量', fontsize=12)
ax1.set_title('Token消耗对比', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# 2. 节省比例（柱状图）
ax2 = axes[0, 1]
savings_percentage = [(1 - c/o) * 100 for o, c in zip(original_tokens, compressed_tokens)]
bars = ax2.bar(pages, savings_percentage, color='steelblue', alpha=0.7, edgecolor='black')
ax2.set_xlabel('页码', fontsize=12)
ax2.set_ylabel('节省比例 (%)', fontsize=12)
ax2.set_title('Token节省比例', fontsize=14, fontweight='bold')
ax2.set_ylim([0, 100])
ax2.grid(True, axis='y', alpha=0.3)

# 在柱状图上添加数值标签
for bar, pct in zip(bars, savings_percentage):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             f'{pct:.1f}%',
             ha='center', va='bottom', fontsize=9)

# 3. 累计Token消耗（堆叠面积图）
ax3 = axes[1, 0]
cumulative_original = np.cumsum(original_tokens)
cumulative_compressed = np.cumsum(compressed_tokens)
ax3.fill_between(pages, 0, cumulative_original, alpha=0.5, label='原始方案累计', color='red')
ax3.fill_between(pages, 0, cumulative_compressed, alpha=0.7, label='压缩方案累计', color='green')
ax3.set_xlabel('页码', fontsize=12)
ax3.set_ylabel('累计Token数量', fontsize=12)
ax3.set_title('累计Token消耗（生成10页）', fontsize=14, fontweight='bold')
ax3.legend(fontsize=10)
ax3.grid(True, alpha=0.3)

# 添加总节省标注
total_saved = cumulative_original[-1] - cumulative_compressed[-1]
ax3.text(0.5, 0.5, f'总节省\n{total_saved:,} tokens\n({(1-cumulative_compressed[-1]/cumulative_original[-1])*100:.1f}%)',
         transform=ax3.transAxes, fontsize=14, fontweight='bold',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
         ha='center', va='center')

# 4. 成本节省对比（柱状图）
ax4 = axes[1, 1]

# 假设 GPT-4o 价格: $0.01/1K tokens
cost_per_1k_tokens_gpt4o = 0.01
cost_per_1k_tokens_mini = 0.00015

original_cost_gpt4o = [t/1000 * cost_per_1k_tokens_gpt4o for t in original_tokens]
compressed_cost_gpt4o = [t/1000 * cost_per_1k_tokens_gpt4o for t in compressed_tokens]

x = np.arange(len(pages))
width = 0.35

bars1 = ax4.bar(x - width/2, original_cost_gpt4o, width, label='原始方案', color='red', alpha=0.7)
bars2 = ax4.bar(x + width/2, compressed_cost_gpt4o, width, label='压缩方案', color='green', alpha=0.7)

ax4.set_xlabel('页码', fontsize=12)
ax4.set_ylabel('单次调用成本 (美元)', fontsize=12)
ax4.set_title('GPT-4o 单次调用成本对比', fontsize=14, fontweight='bold')
ax4.legend(fontsize=10)
ax4.grid(True, axis='y', alpha=0.3)

# 添加累计成本标签
total_original_cost = sum(original_cost_gpt4o)
total_compressed_cost = sum(compressed_cost_gpt4o)
total_saved_cost = total_original_cost - total_compressed_cost

ax4.text(0.5, 0.5, f'10页累计成本\n原始: ${total_original_cost:.4f}\n压缩: ${total_compressed_cost:.4f}\n节省: ${total_saved_cost:.4f}',
         transform=ax4.transAxes, fontsize=11, fontweight='bold',
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7),
         ha='center', va='center')

plt.tight_layout()
plt.savefig('context_compression_comparison.png', dpi=300, bbox_inches='tight')
print("✅ 图表已保存: context_compression_comparison.png")

# 打印统计数据
print("\n" + "="*80)
print("📊 上下文压缩效果统计数据")
print("="*80)

print(f"\n1. 单页对比（第10页）:")
print(f"   原始: {original_tokens[-1]:,} tokens")
print(f"   压缩: {compressed_tokens[-1]:,} tokens")
print(f"   节省: {original_tokens[-1] - compressed_tokens[-1]:,} tokens ({savings_percentage[-1]:.1f}%)")

print(f"\n2. 累计对比（生成10页）:")
print(f"   原始累计: {cumulative_original[-1]:,} tokens")
print(f"   压缩累计: {cumulative_compressed[-1]:,} tokens")
print(f"   总节省: {cumulative_original[-1] - cumulative_compressed[-1]:,} tokens ({(1-cumulative_compressed[-1]/cumulative_original[-1])*100:.1f}%)")

print(f"\n3. 成本对比（GPT-4o，$0.01/1K tokens）:")
print(f"   原始方案: ${total_original_cost:.4f}")
print(f"   压缩方案: ${total_compressed_cost:.4f}")
print(f"   节省成本: ${total_saved_cost:.4f}")

print(f"\n4. 规模化效果（假设每天生成100个PPT）:")
daily_original = total_original_cost * 100
daily_compressed = total_compressed_cost * 100
daily_saved = daily_original - daily_compressed
print(f"   每天成本: ${daily_original:.2f} → ${daily_compressed:.2f}")
print(f"   每天节省: ${daily_saved:.2f}")
print(f"   每月节省: ${daily_saved * 30:.2f}")
print(f"   每年节省: ${daily_saved * 365:.2f}")

print("\n" + "="*80)
print("✅ 统计完成")
print("="*80)
