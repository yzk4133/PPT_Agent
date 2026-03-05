"""
PPT 需求数据集验证脚本

用于检查 ppt_requirement.jsonl 的数据质量和分布
"""

import json
from collections import Counter
from typing import Dict, Any

# 验证规则
VALID_TYPES = ["education", "business", "academic", "creative", "marketing"]
VALID_STYLES = ["minimalist", "modern", "creative", "professional"]
VALID_AUDIENCES = ["students", "investors", "colleagues", "public", "experts"]


def validate_json_format(json_str: str) -> tuple[bool, str, Any]:
    """验证 JSON 格式和内容"""
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return False, f"JSON 格式错误: {e}", None

    # 检查必填字段
    required_fields = ["topic", "type", "style"]
    for field in required_fields:
        if field not in data:
            return False, f"缺少必填字段: {field}", data

    # 检查 topic
    if not data.get("topic") or len(str(data["topic"])) < 2:
        return False, "topic 不能为空或太短", data

    # 检查 type
    if data["type"] not in VALID_TYPES:
        return False, f"type 无效: {data['type']}", data

    # 检查 style
    if data["style"] not in VALID_STYLES:
        return False, f"style 无效: {data['style']}", data

    # 检查 page_num
    if "page_num" in data:
        if not isinstance(data["page_num"], int):
            return False, "page_num 必须是整数", data
        if data["page_num"] < 1 or data["page_num"] > 50:
            return False, f"page_num 超出范围: {data['page_num']}", data

    # 检查 target_audience
    if "target_audience" in data:
        if data["target_audience"] not in VALID_AUDIENCES:
            return False, f"target_audience 无效: {data['target_audience']}", data

    return True, "", data


def validate_dataset(file_path: str) -> Dict[str, Any]:
    """验证整个数据集"""
    total = 0
    valid = 0
    invalid = 0

    # 统计字段分布
    type_dist = Counter()
    style_dist = Counter()
    audience_dist = Counter()
    topic_length = []

    # 错误样本
    errors = []

    print(f"正在验证数据集: {file_path}")
    print("=" * 60)

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            total += 1

            try:
                sample = json.loads(line.strip())

                # 检查 conversations 字段
                if "conversations" not in sample:
                    errors.append(f"Line {line_num}: 缺少 conversations 字段")
                    invalid += 1
                    continue

                conversations = sample["conversations"]
                if len(conversations) != 2:
                    errors.append(f"Line {line_num}: conversations 必须是 2 轮")
                    invalid += 1
                    continue

                # 验证输出格式
                human_input = conversations[0]["value"]
                gpt_output = conversations[1]["value"]

                is_valid, error_msg, data = validate_json_format(gpt_output)

                if is_valid:
                    valid += 1

                    # 统计分布
                    type_dist[data["type"]] += 1
                    style_dist[data["style"]] += 1
                    if "target_audience" in data:
                        audience_dist[data["target_audience"]] += 1
                    topic_length.append(len(data["topic"]))
                else:
                    errors.append(f"Line {line_num}: {error_msg}")
                    invalid += 1

            except Exception as e:
                errors.append(f"Line {line_num}: {str(e)}")
                invalid += 1

    # 打印结果
    print(f"\n[OK] 验证完成")
    print(f"=" * 60)
    print(f"总样本数: {total}")
    print(f"有效样本: {valid} ({valid/total*100:.1f}%)")
    print(f"无效样本: {invalid} ({invalid/total*100:.1f}%)")

    print(f"\n[STATS] 字段分布:")
    print(f"=" * 60)
    print(f"\n[type 分布]")
    for t, count in type_dist.most_common():
        print(f"  {t:15s}: {count:3d} ({count/valid*100:.1f}%)")

    print(f"\n[style 分布]")
    for s, count in style_dist.most_common():
        print(f"  {s:15s}: {count:3d} ({count/valid*100:.1f}%)")

    print(f"\n[target_audience 分布]")
    for a, count in audience_dist.most_common():
        print(f"  {a:15s}: {count:3d} ({count/valid*100:.1f}%)")

    if topic_length:
        avg_length = sum(topic_length) / len(topic_length)
        print(f"\n[topic 长度统计]")
        print(f"  平均长度: {avg_length:.1f} 字符")
        print(f"  最短: {min(topic_length)} 字符")
        print(f"  最长: {max(topic_length)} 字符")

    if errors:
        print(f"\n[ERROR] 错误列表 (前10条):")
        print(f"=" * 60)
        for error in errors[:10]:
            print(f"  {error}")
        if len(errors) > 10:
            print(f"  ... 还有 {len(errors) - 10} 条错误")

    print(f"\n" + "=" * 60)
    quality = '优秀' if valid/total > 0.95 else '良好' if valid/total > 0.9 else '需要改进'
    print(f"[RATING] 数据集质量: {quality}")
    print(f"=" * 60)


if __name__ == "__main__":
    import sys

    file_path = sys.argv[1] if len(sys.argv) > 1 else "../dataset/ppt_requirement.jsonl"

    validate_dataset(file_path)
