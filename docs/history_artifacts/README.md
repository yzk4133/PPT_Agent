# MultiAgent PPT 系统

一个基于多Agent协作的智能PPT生成系统，利用AI技术让演示文稿创作更高效。

## 特性

- 🤖 **多Agent协作**: 专业的Agent分工合作
- 🎨 **智能设计**: 自动推荐配色、字体和布局
- ⚡ **高效生成**: 从需求到PPT，全程AI辅助
- 🔄 **灵活定制**: 支持多种风格和模板

## 快速开始

### 安装

```bash
git clone https://github.com/yourusername/MultiAgentPPT.git
cd MultiAgentPPT
pip install -r requirements.txt
```

### 配置

1. 复制配置文件：
```bash
cp config.example.yaml config.yaml
```

2. 设置API密钥（在config.yaml中）：
```yaml
anthropic:
  api_key: your-anthropic-api-key

openai:
  api_key: your-openai-api-key  # 可选
```

### 运行

```bash
python main.py
```

然后访问 http://localhost:8000

## 架构

```
┌─────────────┐
│  用户输入   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  协调器     │ ← 任务分解和调度
└──────┬──────┘
       │
   ┌───┴────┬────────┐
   ▼        ▼        ▼
┌──────┐ ┌──────┐ ┌──────────┐
│内容  │ │设计  │ │代码生成  │
│Agent │ │Agent │ │ Agent    │
└───┬──┘ └───┬──┘ └────┬─────┘
    │        │         │
    └───┬────┴─────────┘
        │
        ▼
   ┌─────────┐
   │PPT输出  │
   └─────────┘
```

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式

```bash
black backend/
isort backend/
```

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 许可证

MIT License
