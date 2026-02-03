"""
分层架构可视化

展示API、Service、Agent、Domain Model之间的关系
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

import sys
import io

# 设置 stdout 编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(14, 16))
ax.set_xlim(0, 10)
ax.set_ylim(0, 20)
ax.axis('off')

# 标题
ax.text(5, 19.5, '后端分层架构：API → Service → Agent → Domain Model',
        ha='center', fontsize=16, fontweight='bold')

# === 定义各层 ===

layers = [
    {
        'name': 'API Layer',
        'y': 17,
        'color': '#FF6B6B',
        'description': '处理HTTP请求/响应',
        'responsibilities': [
            '接收HTTP请求',
            '解析参数 (JSON/Query)',
            '验证格式',
            '调用Service',
            '返回响应'
        ],
        'not_responsibilities': [
            '业务逻辑',
            'LLM调用',
            '数据库操作'
        ]
    },
    {
        'name': 'Service Layer',
        'y': 13,
        'color': '#4ECDC4',
        'description': '编排业务流程',
        'responsibilities': [
            '协调多个Agent',
            '事务管理',
            '流程控制',
            '错误处理',
            '业务规则'
        ],
        'not_responsibilities': [
            'HTTP处理',
            '如何调用LLM'
        ]
    },
    {
        'name': 'Agent Layer',
        'y': 9,
        'color': '#95E1D3',
        'description': '执行具体任务',
        'responsibilities': [
            '调用LLM',
            '使用工具',
            '决策和推理',
            '处理具体任务',
            '质量检查'
        ],
        'not_responsibilities': [
            'HTTP处理',
            '整体流程编排',
            '事务管理'
        ]
    },
    {
        'name': 'Domain Model',
        'y': 5,
        'color': '#FFEAA7',
        'description': '数据和业务规则',
        'responsibilities': [
            '数据结构',
            '业务规则',
            '验证逻辑',
            '计算方法'
        ],
        'not_responsibilities': [
            '如何被创建',
            '如何被保存',
            'HTTP/JSON格式'
        ]
    },
    {
        'name': 'Infrastructure',
        'y': 1,
        'color': '#DFE6E9',
        'description': '技术实现',
        'responsibilities': [
            'LLM客户端',
            '数据库',
            '文件系统',
            '外部API'
        ],
        'not_responsibilities': [
            '业务逻辑',
            '流程编排'
        ]
    }
]

# === 绘制各层 ===

for i, layer in enumerate(layers):
    y = layer['y']

    # 层标题
    box = FancyBboxPatch((1, y - 0.8), 8, 1.6,
                         boxstyle="round,pad=0.1",
                         edgecolor='black', facecolor=layer['color'],
                         linewidth=2, alpha=0.8)
    ax.add_patch(box)

    ax.text(5, y + 0.3, layer['name'],
            ha='center', fontsize=14, fontweight='bold')
    ax.text(5, y - 0.3, layer['description'],
            ha='center', fontsize=10, style='italic')

    # 职责列表
    resp_y = y + 0.6
    ax.text(0.3, resp_y, '✓ 职责:', fontsize=9, fontweight='bold', color='green')
    for j, resp in enumerate(layer['responsibilities']):
        ax.text(0.5, resp_y - 0.25 - j*0.3, f'• {resp}',
                fontsize=8, va='top')

    # 非职责列表
    not_resp_y = y - 1.2
    if layer['not_responsibilities']:
        ax.text(0.3, not_resp_y, '✗ 不负责:', fontsize=9, fontweight='bold', color='red')
        for j, not_resp in enumerate(layer['not_responsibilities']):
            ax.text(0.5, not_resp_y - 0.25 - j*0.3, f'• {not_resp}',
                    fontsize=8, va='top', color='darkred')

# === 绘制依赖箭头 ===

arrows = [
    (17, 13, '调用'),
    (13, 9, '协调'),
    (9, 5, '操作'),
    (9, 1, '使用')
]

for start_y, end_y, label in arrows:
    arrow = FancyArrowPatch((5, start_y - 0.9), (5, end_y + 0.9),
                            arrowstyle='->', mutation_scale=20,
                            linewidth=2, color='#3498DB')
    ax.add_patch(arrow)

    mid_y = (start_y + end_y) / 2
    ax.text(5.3, mid_y, label,
            fontsize=9, color='#3498DB', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#3498DB'))

# === 添加请求流程示例 ===

flow_x = 7.5
flow_y_start = 17
flow_texts = [
    (17, '1. POST /api/presentations'),
    (16.2, '2. 验证参数'),
    (13.8, '3. 生成PPT()'),
    (12.2, '4. 创建会话'),
    (10.2, '5. create_outline()'),
    (9.8, '6. 调用LLM'),
    (7.8, '7. 创建Outline对象'),
    (5.8, '8. 保存到数据库'),
    (2.8, '9. OpenAI API'),
    (2.5, '10. 返回结果'),
    (16.5, '11. 返回JSON响应')
]

for y, text in flow_texts:
    ax.text(flow_x, y, text, fontsize=7, ha='left',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='lightblue', alpha=0.7))

# === 添加图例和说明 ===

# 图例
legend_y = -1
ax.text(5, legend_y, '依赖关系：上层依赖下层，单向流动',
        ha='center', fontsize=10, style='italic',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow'))

# 关键原则
principles = [
    '关键原则：',
    '• 单一职责：每层只做一件事',
    '• 单向依赖：上层依赖下层',
    '• 低耦合：可以替换任何层',
    '• 高内聚：相关代码放一起'
]

for i, principle in enumerate(principles):
    ax.text(0.5, legend_y - 0.5 - i*0.35, principle,
            fontsize=8, va='top',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='lightgray', alpha=0.5))

plt.tight_layout()
plt.savefig('architecture_layers_diagram.png', dpi=300, bbox_inches='tight', pad_inches=0.5)
print("✅ 架构图已保存: architecture_layers_diagram.png")

# 打印详细说明
print("\n" + "="*80)
print("📊 分层架构详细说明")
print("="*80)

print("\n🔴 为什么要分层？")
print("-" * 40)
print("1. 职责清晰：每层只做一件事")
print("2. 易于测试：可以mock任何层")
print("3. 便于复用：Service可以被HTTP、CLI、gRPC调用")
print("4. 易于维护：修改LLM不影响API")
print("5. 团队协作：不同人负责不同层")

print("\n📋 各层的职责对比")
print("-" * 40)
print(f"{'层':<20} {'主要职责':<30} {'不负责'}")
print("-" * 80)
for layer in layers:
    print(f"{layer['name']:<20} {layer['description']:<30} {layer['not_responsibilities'][0]}")

print("\n🔄 请求流程示例")
print("-" * 40)
print("用户请求: POST /api/presentations")
print("  { 'topic': 'AI发展史', 'num_slides': 10 }")
print()
print("1. API层接收 → 验证参数 → 调用Service")
print("2. Service层 → 创建会话 → 协调Agent")
print("3. Agent层 → 调用LLM → 创建Domain Model")
print("4. Infrastructure → OpenAI API")
print("5. 返回结果 → Agent → Service → API → 用户")

print("\n⚠️ 常见错误")
print("-" * 40)
print("❌ 在API层直接调用Agent")
print("   问题：API层太重，无法复用")
print()
print("❌ 在Agent里编排流程")
print("   问题：Agent太复杂，难以测试")
print()
print("❌ 在Domain Model里调用LLM")
print("   问题：领域模型应该纯粹，不依赖外部")

print("\n✅ 正确的做法")
print("-" * 40)
print("✓ API层：只处理HTTP")
print("✓ Service层：编排流程")
print("✓ Agent层：执行任务")
print("✓ Domain Model：数据和规则")
print("✓ Infrastructure：技术实现")

print("\n💡 类比理解")
print("-" * 40)
print("API层      = 服务员（接单、端菜）")
print("Service层  = 厨师长（安排做菜顺序）")
print("Agent层    = 厨师（炒菜、切菜）")
print("Domain Model = 菜谱（菜品定义）")
print("Infrastructure = 厨具（锅、铲、刀）")

print("\n" + "="*80)
print("📚 相关文档")
print("="*80)
print("- ARCHITECTURE_LAYERS_EXPLAINED.md（详细说明）")
print("- IDEAL_BACKEND_STRUCTURE.md（理想结构）")
print("- BACKEND_CLEANUP_GUIDE.md（清理指南）")

print("\n" + "="*80)
