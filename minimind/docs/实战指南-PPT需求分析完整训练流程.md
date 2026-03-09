# 实战指南：PPT 需求分析完整训练流程

> **创建日期**: 2026-03-07
> **项目目标**: 基于 MiniMind 训练小模型，实现 PPT 需求的结构化分析
> **训练流程**: 环境搭建 → 数据准备 → 预训练 → SFT → LoRA 微调 → 模型评估

---

## 📋 目录

1. [环境搭建](#1-环境搭建)
2. [数据准备](#2-数据准备)
3. [预训练 (Pretraining)](#3-预训练-pretraining)
4. [监督微调 (SFT)](#4-监督微调-sft)
5. [LoRA 微调](#5-lora-微调)
6. [模型评估](#6-模型评估)
7. [部署使用](#7-部署使用)
8. [常见问题](#8-常见问题)

---

## 1. 环境搭建

### 1.1 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| **GPU** | GTX 1660 (6GB) | RTX 3060/4060 (12GB) |
| **内存** | 16GB | 32GB |
| **存储** | 20GB SSD | 50GB SSD |
| **CUDA** | 11.8+ | 12.1+ |

### 1.2 软件安装

```bash
# 1. 克隆项目
git clone https://github.com/jingyaogong/minimind.git
cd minimind

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 验证安装
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
```

### 1.3 目录结构

```
minimind/
├── data/                          # 训练数据
│   ├── pretrain_hq.jsonl         # 预训练数据
│   ├── sft_ppt.jsonl             # SFT 数据
│   └── lora_ppt.jsonl            # LoRA 数据
├── out/                          # 输出目录
│   ├── pretrain_512.pth          # 预训练权重
│   ├── full_sft_512.pth          # SFT 权重
│   └── lora_ppt.pth              # LoRA 权重
├── model/                        # Tokenizer
│   ├── vocab.json
│   ├── merges.txt
│   └── tokenizer_config.json
├── scripts/                      # 辅助脚本
│   └── generate_ppt_data.py      # 数据生成脚本
└── trainer/                      # 训练脚本
    ├── train_pretrain.py
    ├── train_full_sft.py
    └── train_lora.py
```

---

## 2. 数据准备

### 2.1 数据生成脚本

创建 `scripts/generate_ppt_data.py`：

```python
import json
import random
from pathlib import Path

# PPT 主题列表
TOPICS = [
    "人工智能", "机器学习", "深度学习", "数据分析", "云计算",
    "区块链", "物联网", "5G技术", "网络安全", "虚拟现实",
    "季度汇报", "年度总结", "项目进展", "产品发布", "市场分析",
    "技术分享", "培训教程", "企业介绍", "商业计划", "投资路演"
]

# PPT 风格列表
STYLES = [
    "科技感", "简约", "商务", "卡通", "清新",
    "复古", "未来感", "工业风", "自然风", "艺术风"
]

# 表达模板
TEMPLATES = [
    "做一个关于{topic}的PPT，{style}风格",
    "我要做一个{topic}的PPT，要{style}一点的",
    "帮我做一个PPT，主题是{topic}，风格{style}",
    "制作一个关于{topic}的演示文稿，{style}风格",
    "需要一个{topic}主题的PPT，风格要{style}",
    "{topic}的PPT，{style}风格，快帮我做",
    "PPT主题{topic}，风格{style}，帮我生成",
    "来个{topic}的PPT，要{style}风格",
]

def generate_single_sample():
    """生成单条训练数据"""
    topic = random.choice(TOPICS)
    style = random.choice(STYLES)
    template = random.choice(TEMPLATES)

    # 生成用户输入
    user_input = template.format(topic=topic, style=style)

    # 生成结构化输出
    output = {
        "topic": topic,
        "style": style
    }

    return {
        "conversations": [
            {"from": "human", "value": user_input},
            {"from": "gpt", "value": json.dumps(output, ensure_ascii=False)}
        ]
    }

def generate_dataset(num_samples=1000, output_path="data/lora_ppt.jsonl"):
    """生成完整数据集"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for _ in range(num_samples):
            sample = generate_single_sample()
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')

    print(f"✅ 生成 {num_samples} 条数据到 {output_path}")

    # 数据统计
    with open(output_path, 'r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f]

    print(f"\n数据统计:")
    print(f"  总数: {len(data)}")
    print(f"  主题数: {len(TOPICS)}")
    print(f"  风格数: {len(STYLES)}")

    return output_path

if __name__ == "__main__":
    generate_dataset(num_samples=1000)
```

### 2.2 生成数据

```bash
# 生成 LoRA 微调数据
python scripts/generate_ppt_data.py
```

输出示例：
```
✅ 生成 1000 条数据到 data/lora_ppt.jsonl

数据统计:
  总数: 1000
  主题数: 20
  风格数: 10
```

### 2.3 数据验证

创建 `scripts/validate_data.py`：

```python
import json
from collections import Counter

def validate_data(data_path):
    """验证数据质量"""
    errors = []
    stats = {"topics": Counter(), "styles": Counter(), "total": 0}

    with open(data_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line)

                # 检查 conversations
                if 'conversations' not in data:
                    errors.append(f"行{line_num}: 缺少 conversations")
                    continue

                convs = data['conversations']
                if len(convs) < 2:
                    errors.append(f"行{line_num}: 对话不足2条")
                    continue

                # 提取输出
                output = convs[-1]['value']
                try:
                    output_json = json.loads(output)
                    topic = output_json.get('topic', '')
                    style = output_json.get('style', '')

                    if topic and style:
                        stats['topics'][topic] += 1
                        stats['styles'][style] += 1
                        stats['total'] += 1
                    else:
                        errors.append(f"行{line_num}: 缺少 topic 或 style")

                except json.JSONDecodeError:
                    errors.append(f"行{line_num}: 输出不是合法 JSON")

            except Exception as e:
                errors.append(f"行{line_num}: {e}")

    # 输出结果
    print("数据验证结果:")
    print(f"  总数据量: {stats['total']}")
    print(f"  主题分布 (Top 10):")
    for topic, count in stats['topics'].most_common(10):
        print(f"    {topic}: {count} ({count/stats['total']*100:.1f}%)")
    print(f"  风格分布 (Top 10):")
    for style, count in stats['styles'].most_common(10):
        print(f"    {style}: {count} ({count/stats['total']*100:.1f}%)")

    if errors:
        print(f"\n❌ 发现 {len(errors)} 个错误:")
        for err in errors[:10]:
            print(f"  {err}")
        if len(errors) > 10:
            print(f"  ... 还有 {len(errors)-10} 个错误")
    else:
        print("\n✅ 数据验证通过！")

if __name__ == "__main__":
    validate_data("data/lora_ppt.jsonl")
```

运行验证：
```bash
python scripts/validate_data.py
```

---

## 3. 预训练 (Pretraining)

### 3.1 准备预训练数据

预训练数据需要是无标注的大规模文本。可以：
1. 下载项目提供的预训练数据
2. 使用自己的文本数据

```bash
# 创建数据目录
mkdir -p data

# 方式1: 使用项目数据（如果提供）
# 下载后放到 data/pretrain_hq.jsonl

# 方式2: 创建简单的预训练数据
python -c "
import json
texts = [
    '人工智能是计算机科学的一个分支。',
    '机器学习是人工智能的一个子集。',
    '深度学习使用神经网络模拟人脑。',
    # ... 更多文本
]
with open('data/pretrain_hq.jsonl', 'w', encoding='utf-8') as f:
    for text in texts:
        f.write(json.dumps({'text': text}, ensure_ascii=False) + '\n')
"
```

### 3.2 预训练命令

```bash
python trainer/train_pretrain.py \
    --data_path data/pretrain_hq.jsonl \
    --out_dir out \
    --hidden_size 512 \
    --num_hidden_layers 8 \
    --num_attention_heads 8 \
    --num_key_value_heads 2 \
    --max_seq_len 512 \
    --epochs 1 \
    --batch_size 32 \
    --learning_rate 5e-4 \
    --warmup_ratio 0.1 \
    --weight_decay 0.01 \
    --grad_clip 1.0 \
    --device cuda:0 \
    --dtype bfloat16 \
    --flash_attn
```

### 3.3 预训练输出

成功后会生成：
```
out/
└── pretrain_512.pth  # 预训练权重
```

训练日志示例：
```
Epoch: [1/1][100/500] loss: 3.523 lr: 0.000500
Epoch: [1/1][200/500] loss: 2.845 lr: 0.000500
Epoch: [1/1][300/500] loss: 2.312 lr: 0.000500
Epoch: [1/1][400/500] loss: 1.987 lr: 0.000500
Epoch: [1/1][500/500] loss: 1.765 lr: 0.000500

✅ 预训练完成，权重已保存到 out/pretrain_512.pth
```

### 3.4 预训练参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| `--data_path` | data/pretrain_hq.jsonl | 预训练数据路径 |
| `--out_dir` | out | 输出目录 |
| `--hidden_size` | 512 | 隐藏层维度 |
| `--num_hidden_layers` | 8 | Transformer 层数 |
| `--max_seq_len` | 512 | 最大序列长度 |
| `--epochs` | 1 | 训练轮数 |
| `--batch_size` | 32 | 批次大小 |
| `--learning_rate` | 5e-4 | 学习率 |
| `--dtype` | bfloat16 | 数据类型 |

---

## 4. 监督微调 (SFT)

### 4.1 准备 SFT 数据

SFT 数据需要是对话格式。创建 `data/sft_ppt.jsonl`：

```jsonl
{"conversations": [{"from": "human", "value": "你好"}, {"from": "gpt", "value": "你好！有什么可以帮助你的？"}]}
{"conversations": [{"from": "human", "value": "做一个关于人工智能的PPT"}, {"from": "gpt", "value": "好的，我来帮你做一个关于人工智能的PPT。你希望是什么风格的？"}]}
{"conversations": [{"from": "human", "value": "科技感风格"}, {"from": "gpt", "value": "没问题，我会为你制作一个科技感风格的人工智能主题PPT。"}]}
```

或者用脚本生成：

```python
import json

sft_data = [
    {"conversations": [
        {"from": "human", "value": "你好"},
        {"from": "gpt", "value": "你好！有什么可以帮助你的？"}
    ]},
    {"conversations": [
        {"from": "human", "value": "帮我做一个PPT"},
        {"from": "gpt", "value": "好的，我来帮你制作PPT。请告诉我主题和风格。"}
    ]},
    # ... 更多对话数据
]

with open('data/sft_ppt.jsonl', 'w', encoding='utf-8') as f:
    for item in sft_data:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')
```

### 4.2 SFT 训练命令

```bash
python trainer/train_full_sft.py \
    --data_path data/sft_ppt.jsonl \
    --load_from out/pretrain_512.pth \
    --out_dir out \
    --hidden_size 512 \
    --num_hidden_layers 8 \
    --num_attention_heads 8 \
    --num_key_value_heads 2 \
    --max_seq_len 512 \
    --epochs 2 \
    --batch_size 16 \
    --learning_rate 5e-7 \
    --warmup_ratio 0.1 \
    --weight_decay 0.01 \
    --grad_clip 1.0 \
    --device cuda:0 \
    --dtype bfloat16 \
    --flash_attn
```

### 4.3 SFT 输出

成功后会生成：
```
out/
├── pretrain_512.pth
└── full_sft_512.pth  # SFT 权重
```

训练日志示例：
```
Epoch: [1/2][50/200] loss: 2.125 lr: 0.0000005
Epoch: [1/2][100/200] loss: 1.876 lr: 0.0000005
Epoch: [1/2][150/200] loss: 1.654 lr: 0.0000005
Epoch: [1/2][200/200] loss: 1.543 lr: 0.0000005
Epoch: [1/2] 完成, 平均 Loss: 1.650

Epoch: [2/2][50/200] loss: 1.234 lr: 0.0000003
Epoch: [2/2][100/200] loss: 1.123 lr: 0.0000003
Epoch: [2/2][150/200] loss: 1.056 lr: 0.0000003
Epoch: [2/2][200/200] loss: 0.987 lr: 0.0000003
Epoch: [2/2] 完成, 平均 Loss: 1.100

✅ SFT 训练完成，权重已保存到 out/full_sft_512.pth
```

### 4.4 SFT 参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| `--load_from` | out/pretrain_512.pth | 加载预训练权重 |
| `--epochs` | 2 | 训练轮数（比预训练少） |
| `--batch_size` | 16 | 批次大小（比预训练小） |
| `--learning_rate` | 5e-7 | 学习率（比预训练小很多） |

---

## 5. LoRA 微调

### 5.1 LoRA 训练命令

```bash
python trainer/train_lora.py \
    --pretrained_model_path out/full_sft_512.pth \
    --data_path data/lora_ppt.jsonl \
    --out_dir out \
    --lora_rank 8 \
    --lora_alpha 32 \
    --lora_dropout 0.1 \
    --max_seq_len 512 \
    --epochs 10 \
    --batch_size 32 \
    --learning_rate 1e-4 \
    --warmup_ratio 0.1 \
    --weight_decay 0.01 \
    --grad_clip 1.0 \
    --device cuda:0 \
    --dtype bfloat16 \
    --flash_attn
```

### 5.2 LoRA 输出

成功后会生成：
```
out/
├── pretrain_512.pth
├── full_sft_512.pth
└── lora_ppt.pth  # LoRA 权重
```

训练日志示例：
```
Epoch: [1/10][10/32] loss: 2.543 lr: 0.000100
Epoch: [1/10][20/32] loss: 1.987 lr: 0.000100
Epoch: [1/10][32/32] loss: 1.765 lr: 0.000100
Epoch: [1/10] 完成, 平均 Loss: 2.098, 验证 Loss: 2.234

Epoch: [2/10][10/32] loss: 1.543 lr: 0.000085
Epoch: [2/10][20/32] loss: 1.234 lr: 0.000085
Epoch: [2/10][32/32] loss: 1.123 lr: 0.000085
Epoch: [2/10] 完成, 平均 Loss: 1.300, 验证 Loss: 1.456

...

Epoch: [9/10][32/32] loss: 0.321 lr: 0.000020
Epoch: [9/10] 完成, 平均 Loss: 0.350, 验证 Loss: 0.380

Epoch: [10/10][32/32] loss: 0.298 lr: 0.000010
Epoch: [10/10] 完成, 平均 Loss: 0.320, 验证 Loss: 0.350

✅ LoRA 训练完成，权重已保存到 out/lora_ppt.pth
```

### 5.3 LoRA 参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| `--pretrained_model_path` | out/full_sft_512.pth | 加载 SFT 权重 |
| `--lora_rank` | 8 | LoRA 秩数 |
| `--lora_alpha` | 32 | LoRA 缩放因子 |
| `--lora_dropout` | 0.1 | LoRA Dropout |
| `--epochs` | 10 | 训练轮数 |
| `--learning_rate` | 1e-4 | 学习率（LoRA 可以用较大的学习率） |

---

## 6. 模型评估

### 6.1 创建评估脚本

创建 `scripts/eval_ppt.py`：

```python
import json
import torch
from transformers import AutoTokenizer
from model.model_minimind import MiniMindForCausalLM, MiniMindConfig
from model.model_lora import apply_lora, load_lora

def load_model(model_path, lora_path=None):
    """加载模型"""
    # 加载配置
    config = MiniMindConfig(
        hidden_size=512,
        num_hidden_layers=8,
        num_attention_heads=8,
        num_key_value_heads=2,
    )

    # 创建模型
    model = MiniMindForCausalLM(config)

    # 加载权重
    state_dict = torch.load(model_path, map_location='cpu')
    model.load_state_dict(state_dict, strict=False)

    # 加载 LoRA
    if lora_path:
        apply_lora(model, r=8, lora_alpha=32, dropout=0.1)
        load_lora(model, lora_path)

    model.eval()
    return model

def recognize_ppt_requirement(model, tokenizer, query, device='cuda'):
    """识别 PPT 需求"""
    prompt = f"{query}"
    messages = [{"role": "user", "content": prompt}]

    # 格式化为 ChatML
    prompt_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(prompt_text, return_tensors="pt").to(device)

    # 生成
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            temperature=0.1,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    # 解码
    response = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[1]:],
        skip_special_tokens=True
    )

    return response

def main():
    # 加载模型
    print("加载模型...")
    tokenizer = AutoTokenizer.from_pretrained("./model/")
    model = load_model(
        "out/full_sft_512.pth",
        "out/lora_ppt.pth"
    )
    model = model.to('cuda')

    # 测试案例
    test_cases = [
        "做一个关于人工智能的PPT，科技感风格",
        "我要做一个季度汇报的PPT，简约风格",
        "帮我做一个区块链的演示文稿，商务风格",
        "来个数据分析的PPT，要清新一点",
        "制作一个深度学习的PPT，未来感风格",
    ]

    print("\n" + "="*60)
    print("PPT 需求识别测试")
    print("="*60)

    for query in test_cases:
        print(f"\n输入: {query}")

        try:
            response = recognize_ppt_requirement(model, tokenizer, query)

            # 尝试解析 JSON
            try:
                result = json.loads(response)
                print(f"主题: {result.get('topic', 'N/A')}")
                print(f"风格: {result.get('style', 'N/A')}")
            except json.JSONDecodeError:
                print(f"原始输出: {response}")
                print("⚠️ JSON 解析失败")

        except Exception as e:
            print(f"❌ 错误: {e}")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
```

### 6.2 运行评估

```bash
python scripts/eval_ppt.py
```

输出示例：
```
加载模型...

============================================================
PPT 需求识别测试
============================================================

输入: 做一个关于人工智能的PPT，科技感风格
主题: 人工智能
风格: 科技感

输入: 我要做一个季度汇报的PPT，简约风格
主题: 季度汇报
风格: 简约

输入: 帮我做一个区块链的演示文稿，商务风格
主题: 区块链
风格: 商务

...
```

### 6.3 计算准确率

创建 `scripts/accuracy_eval.py`：

```python
import json
import torch
from transformers import AutoTokenizer
from model.model_minimind import MiniMindForCausalLM, MiniMindConfig
from model.model_lora import apply_lora, load_lora
from tqdm import tqdm

def evaluate_accuracy(data_path, model_path, lora_path):
    """计算准确率"""
    # 加载模型
    tokenizer = AutoTokenizer.from_pretrained("./model/")
    config = MiniMindConfig(hidden_size=512, num_hidden_layers=8)
    model = MiniMindForCausalLM(config)

    state_dict = torch.load(model_path, map_location='cpu')
    model.load_state_dict(state_dict, strict=False)

    apply_lora(model, r=8, lora_alpha=32, dropout=0.1)
    load_lora(model, lora_path)
    model.eval()
    model = model.to('cuda')

    # 加载数据
    with open(data_path, 'r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f]

    # 评估
    topic_correct = 0
    style_correct = 0
    both_correct = 0
    total = 0

    for sample in tqdm(data, desc="Evaluating"):
        convs = sample['conversations']
        query = convs[0]['value']
        expected_output = json.loads(convs[-1]['value'])

        # 推理
        messages = [{"role": "user", "content": query}]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to('cuda')

        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=100, temperature=0.1)

        response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

        # 比较
        try:
            predicted = json.loads(response)
            pred_topic = predicted.get('topic', '')
            pred_style = predicted.get('style', '')

            exp_topic = expected_output.get('topic', '')
            exp_style = expected_output.get('style', '')

            if pred_topic == exp_topic:
                topic_correct += 1
            if pred_style == exp_style:
                style_correct += 1
            if pred_topic == exp_topic and pred_style == exp_style:
                both_correct += 1

        except json.JSONDecodeError:
            pass

        total += 1

    # 输出结果
    print(f"\n评估结果:")
    print(f"  总样本数: {total}")
    print(f"  主题准确率: {topic_correct/total*100:.2f}%")
    print(f"  风格准确率: {style_correct/total*100:.2f}%")
    print(f"  整体准确率: {both_correct/total*100:.2f}%")

if __name__ == "__main__":
    evaluate_accuracy(
        "data/lora_ppt.jsonl",
        "out/full_sft_512.pth",
        "out/lora_ppt.pth"
    )
```

运行准确率评估：
```bash
python scripts/accuracy_eval.py
```

---

## 7. 部署使用

### 7.1 创建 API 服务

创建 `scripts/serve_ppt_api.py`：

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
import json
from transformers import AutoTokenizer
from model.model_minimind import MiniMindForCausalLM, MiniMindConfig
from model.model_lora import apply_lora, load_lora
import uvicorn

app = FastAPI(title="PPT 需求分析 API")

# 全局模型
model = None
tokenizer = None

class PPTRequest(BaseModel):
    query: str
    temperature: float = 0.1

class PPTResponse(BaseModel):
    query: str
    topic: str
    style: str
    confidence: float

@app.on_event("startup")
def load_model():
    """启动时加载模型"""
    global model, tokenizer

    print("加载模型...")
    tokenizer = AutoTokenizer.from_pretrained("./model/")

    config = MiniMindConfig(hidden_size=512, num_hidden_layers=8)
    model = MiniMindForCausalLM(config)

    state_dict = torch.load("out/full_sft_512.pth", map_location='cpu')
    model.load_state_dict(state_dict, strict=False)

    apply_lora(model, r=8, lora_alpha=32, dropout=0.1)
    load_lora(model, "out/lora_ppt.pth")

    model.eval()
    model = model.to('cuda')

    print("✅ 模型加载完成")

@app.post("/analyze", response_model=PPTResponse)
def analyze_ppt_requirement(request: PPTRequest):
    """分析 PPT 需求"""
    try:
        # 构造 prompt
        messages = [{"role": "user", "content": request.query}]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to('cuda')

        # 生成
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                temperature=request.temperature,
                top_p=0.9,
                do_sample=True,
            )

        response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

        # 解析 JSON
        try:
            result = json.loads(response)
            return PPTResponse(
                query=request.query,
                topic=result.get('topic', ''),
                style=result.get('style', ''),
                confidence=0.95  # TODO: 计算真实置信度
            )
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail=f"JSON 解析失败: {response}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 7.2 启动 API 服务

```bash
python scripts/serve_ppt_api.py
```

### 7.3 调用 API

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query": "做一个关于人工智能的PPT，科技感风格"}'
```

返回示例：
```json
{
  "query": "做一个关于人工智能的PPT，科技感风格",
  "topic": "人工智能",
  "style": "科技感",
  "confidence": 0.95
}
```

---

## 8. 常见问题

### Q1: 显存不足怎么办？

**A**: 有几种优化方案：
1. 减小 `batch_size`
2. 开启梯度累积：`--accumulation_steps 8`
3. 使用更小的模型：`--hidden_size 512`
4. 启用混合精度：`--dtype bfloat16`

### Q2: 训练速度慢？

**A**: 检查以下几点：
1. 确保 Flash Attention 可用：`--flash_attn`
2. 使用单卡训练（小模型不需要分布式）
3. 增加 `num_workers`（数据加载）
4. 使用 SSD 存储数据

### Q3: Loss 不收敛？

**A**: 常见原因：
1. 学习率过大：降低 `learning_rate`
2. 数据质量差：检查数据格式
3. 模型配置错误：确认 `vocab_size` 和 tokenizer 匹配

### Q4: JSON 解析失败率高？

**A**: 优化方案：
1. 降低生成温度：`temperature=0.1`
2. 使用约束解码（outlines 库）
3. 增加 JSON 格式样本
4. 后处理重试机制

### Q5: 如何监控训练进度？

**A**: 可以：
1. 使用 WandB：添加 `--use_wandb` 参数
2. 查看日志文件：`out/training.log`
3. 定期保存检查点：`--save_steps 100`

---

## 9. 下一步

完成训练后，你可以：

1. **优化模型**：调整超参数，提升准确率
2. **扩展字段**：增加页数、目标受众等字段
3. **性能优化**：实现 KV Cache、查询缓存
4. **部署上线**：部署到生产环境，添加监控
5. **持续迭代**：收集用户反馈，持续优化

---

**文档版本**: v1.0
**最后更新**: 2026-03-07
**预计训练时间**: 2-3 小时（完整流程）
**预计成本**: $2-5（GPU 租赁）
