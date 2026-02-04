# Utils 目录结构说明

## 📁 目录结构

```
utils/
│
├── 📦 save_ppt/                    # PPT生成模块
│   ├── __init__.py                 # 统一导出
│   ├── config.py                   # 配置类
│   ├── text_processor.py           # 文本处理工具
│   ├── generator.py                # 主生成器
│   ├── main.py                     # 入口函数
│   ├── main_api.py                 # FastAPI接口
│   ├── look_master.py              # 辅助工具
│   ├── strategies/                 # 策略实现
│   │   ├── base.py                 # 抽象基类
│   │   ├── title_slide.py          # 标题页
│   │   ├── content_slide.py        # 内容页
│   │   ├── toc_slide.py            # 目录页
│   │   ├── image_slide.py          # 图片页
│   │   ├── subsection_slide.py     # 子章节
│   │   ├── references_slide.py     # 参考文献
│   │   └── end_slide.py            # 结束页
│   └── output_ppts/                # 输出目录
│
├── 🧪 tests/                       # 测试目录
│   ├── conftest.py                 # 共享fixture
│   ├── fixtures/                   # 测试数据
│   ├── integration/                # 集成测试
│   ├── test_context_compressor.py  # 上下文压缩测试
│   ├── test_text_processor.py      # 文本处理测试
│   ├── test_slide_strategies.py    # 策略测试
│   ├── test_ppt_generator.py       # 生成器测试
│   └── test_main_api.py            # API测试
│
├── 📦 context_compressor.py         # 上下文压缩工具
├── 📦 common/                       # 通用模块(DEPRECATED)
│
├── 📄 README.md                     # 模块说明
├── 📄 TESTING_GUIDE.md              # 测试指南
├── 📄 CLEANUP_SUMMARY.md            # 清理总结
├── 📄 pytest.ini                    # pytest配置
│
└── 🗄️ .archive/                     # 归档目录
    ├── ppt_generator.py_*          # 原始文件(已拆分)
    ├── split_ppt_generator.py_*    # 拆分脚本
    └── *.md_*                      # 临时文档
```

## 🚀 快速开始

### 使用PPT生成器

```python
from utils.save_ppt import start_generate_presentation

json_data = {
    "title": "演示文稿标题",
    "sections": [...],
    "references": [...]
}

output_path = start_generate_presentation(json_data)
```

### 运行测试

```bash
cd backend/utils

# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_text_processor.py -v
pytest tests/test_slide_strategies.py -v

# 查看覆盖率
pytest tests/ --cov=save_ppt --cov-report=html
```

## 📊 模块说明

| 模块 | 说明 | 大小 |
|------|------|------|
| save_ppt/ | PPT生成核心模块 | ~50KB |
| strategies/ | 策略模式实现 | ~30KB |
| tests/ | 测试代码 | ~2KB |

## ✅ 测试状态

- test_text_processor.py: ✅ 27/27 通过
- test_slide_strategies.py: ✅ 24/24 通过
- 总计: ✅ 51/51 通过 (100%)

## 📝 更多文档

- `CLEANUP_SUMMARY.md` - 详细清理总结
- `save_ppt/README.md` - PPT模块说明
- `save_ppt/SPLIT_COMPLETE.md` - 拆分完成文档
- `tests/README.md` - 测试说明

---

**最后更新**: 2025-02-04
