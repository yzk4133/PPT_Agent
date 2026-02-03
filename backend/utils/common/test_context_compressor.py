"""
上下文压缩器测试脚本

用于验证和演示上下文压缩的效果
"""

import sys
import os
import io

# 设置 stdout 编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))

from context_compressor import ContextCompressor, compress_slide_history


def create_mock_slide_xml(page_num: int, title: str, layout: str = "vertical") -> str:
    """创建模拟的幻灯片 XML"""
    return f"""
<SECTION layout="{layout}" page_number={page_num}>
  <H1>{title}</H1>

  <BULLETS>
    <DIV><H3>关键点1</H3><P>这是第{page_num}页的第一个重要要点，包含了详细说明和背景信息。</P></DIV>
    <DIV><H3>关键点2</H3><P>这是第{page_num}页的第二个要点，展示了关键数据和事实。</P></DIV>
    <DIV><P>第三个补充要点，用于支持前面的论点和观点。</P></DIV>
  </BULLETS>

  <IMG src="https://example.com/image{page_num}.jpg" alt="第{page_num}页的配图" background="false" />
</SECTION>
"""


def test_basic_compression():
    """测试基本的压缩功能"""
    print("=" * 80)
    print("测试1: 基本压缩功能")
    print("=" * 80)

    # 创建10页模拟数据
    slides = [
        create_mock_slide_xml(1, "人工智能的发展历程"),
        create_mock_slide_xml(2, "机器学习基础概念"),
        create_mock_slide_xml(3, "深度学习核心原理"),
        create_mock_slide_xml(4, "自然语言处理应用"),
        create_mock_slide_xml(5, "计算机视觉技术"),
        create_mock_slide_xml(6, "强化学习算法"),
        create_mock_slide_xml(7, "AI伦理与挑战"),
        create_mock_slide_xml(8, "未来发展趋势"),
        create_mock_slide_xml(9, "实际案例分析"),
        create_mock_slide_xml(10, "总结与展望"),
    ]

    # 计算原始大小
    original_text = "\n\n".join(slides)
    original_length = len(original_text)

    print(f"\n📊 原始数据:")
    print(f"  - 总页数: {len(slides)}")
    print(f"  - 总字符数: {original_length:,}")
    print(f"  - 估算tokens: ~{int(original_length * 0.7):,}")

    # 使用压缩器（保留最近3页）
    compressor = ContextCompressor(
        max_history_slides=3,
        include_all_titles=True,
        track_duplicates=True
    )

    # 测试生成第10页时的上下文
    compressed = compressor.compress_history(slides, current_index=9)
    compressed_length = len(compressed)

    print(f"\n✅ 压缩后数据（生成第10页时）:")
    print(f"  - 压缩后字符数: {compressed_length:,}")
    print(f"  - 估算tokens: ~{int(compressed_length * 0.7):,}")

    # 计算节省
    savings = compressor.get_token_savings(original_length, compressed_length)
    print(f"\n💰 节省效果:")
    print(f"  - 节省字符数: {savings['original_chars'] - savings['compressed_chars']:,}")
    print(f"  - 节省百分比: {savings['saved_percentage']}%")
    print(f"  - 节省tokens: ~{savings['estimated_saved_tokens']:,}")
    print(f"  - GPT-4o节省成本: ${savings['cost_savings_gpt4o']}")
    print(f"  - GPT-4o-mini节省成本: ${savings['cost_savings_gpt4o_mini']}")

    print(f"\n📝 压缩后的内容示例:")
    print("-" * 80)
    print(compressed)
    print("-" * 80)

    return savings


def test_progressive_compression():
    """测试渐进式压缩（模拟生成过程中的压缩）"""
    print("\n" + "=" * 80)
    print("测试2: 渐进式压缩（模拟生成过程）")
    print("=" * 80)

    compressor = ContextCompressor(
        max_history_slides=3,
        include_all_titles=True,
        track_duplicates=True
    )

    # 模拟生成10页PPT
    slides = []
    total_original_tokens = 0
    total_compressed_tokens = 0

    for i in range(1, 11):
        slide = create_mock_slide_xml(
            i,
            f"第{i}章：人工智能主题{i}",
            "vertical" if i % 2 == 0 else "left"
        )
        slides.append(slide)

        # 计算原始大小
        original_text = "\n\n".join(slides)
        original_tokens = int(len(original_text) * 0.7)
        total_original_tokens += original_tokens

        # 压缩
        compressed = compressor.compress_history(slides, i)
        compressed_tokens = int(len(compressed) * 0.7)
        total_compressed_tokens += compressed_tokens

        savings = compressor.get_token_savings(len(original_text), len(compressed))

        print(f"\n第{i}页:")
        print(f"  原始tokens: ~{original_tokens:,} → 压缩后: ~{compressed_tokens:,} "
              f"(节省 {savings['saved_percentage']}%)")

    print(f"\n📊 累计效果（生成10页）:")
    print(f"  累计原始tokens: ~{total_original_tokens:,}")
    print(f"  累计压缩tokens: ~{total_compressed_tokens:,}")
    print(f"  总节省tokens: ~{total_original_tokens - total_compressed_tokens:,}")
    print(f"  平均节省比例: {(1 - total_compressed_tokens/total_original_tokens) * 100:.1f}%")


def test_duplication_detection():
    """测试重复检测功能"""
    print("\n" + "=" * 80)
    print("测试3: 重复内容检测")
    print("=" * 80)

    compressor = ContextCompressor(track_duplicates=True)

    # 添加第一页
    slide1 = create_mock_slide_xml(1, "人工智能发展", "vertical")
    info1 = compressor.extract_slide_info(slide1, 1)
    print(f"\n✅ 第1页已处理:")
    print(f"  标题: {info1.title}")
    print(f"  关键词: {', '.join(list(info1.keywords)[:10])}")

    # 添加第二页
    slide2 = create_mock_slide_xml(2, "机器学习基础", "left")
    info2 = compressor.extract_slide_info(slide2, 2)
    print(f"\n✅ 第2页已处理:")
    print(f"  标题: {info2.title}")
    print(f"  新增关键词: {', '.join(list(info2.keywords - info1.keywords)[:10])}")

    # 创建一个有重复的第三页
    slide3_duplicate = create_mock_slide_xml(3, "人工智能的未来", "vertical")  # 标题有"人工智能"
    dup_check = compressor.check_duplication(slide3_duplicate)

    print(f"\n🔍 检测第3页是否有重复:")
    print(f"  有重复: {dup_check['has_duplicate']}")
    print(f"  重复关键词: {dup_check['duplicate_keywords'][:10]}")
    if dup_check['suggestions']:
        print(f"  建议: {dup_check['suggestions']}")


def test_config_comparison():
    """测试不同配置的效果对比"""
    print("\n" + "=" * 80)
    print("测试4: 不同配置对比")
    print("=" * 80)

    # 创建10页数据
    slides = [create_mock_slide_xml(i, f"主题{i}") for i in range(1, 11)]

    configs = [
        {"name": "保守（仅1页详细）", "max_history": 1, "include_titles": True},
        {"name": "平衡（3页详细）", "max_history": 3, "include_titles": True},
        {"name": "详细（5页详细）", "max_history": 5, "include_titles": True},
        {"name": "精简（3页详细，无标题列表）", "max_history": 3, "include_titles": False},
    ]

    original_text = "\n\n".join(slides)
    print(f"\n原始数据: {len(original_text)} 字符\n")

    for config in configs:
        compressor = ContextCompressor(
            max_history_slides=config['max_history'],
            include_all_titles=config['include_titles']
        )
        compressed = compressor.compress_history(slides, 9)
        savings = compressor.get_token_savings(
            len('\n\n'.join(slides)),
            len(compressed)
        )

        print(f"{config['name']}:")
        print(f"  压缩后: {len(compressed):} 字符")
        print(f"  节省: {savings['saved_percentage']}% "
              f"(~{savings['estimated_saved_tokens']} tokens)")


if __name__ == "__main__":
    print("\n" + "🚀" * 40)
    print("上下文压缩器测试")
    print("🚀" * 40)

    # 运行所有测试
    test_basic_compression()
    test_progressive_compression()
    test_duplication_detection()
    test_config_comparison()

    print("\n" + "=" * 80)
    print("✅ 所有测试完成")
    print("=" * 80)
