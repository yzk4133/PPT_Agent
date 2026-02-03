# 上下文压缩器 (Context Compressor)

## 📊 效果总结

根据测试结果，上下文压缩器可以带来显著的性能提升：

### Token 节省
- **单页生成**：第10页时节省 **77.3%** 的 tokens
- **渐进式生成**：生成10页累计节省 **64.9%** 的 tokens
- **累计效果**：10页PPT总共节省约 **8,703 tokens**

### 成本节省（GPT-4o）
- 单次调用节省：$0.0188
- 生成10页累计节省：约 $0.13

### 成本节省（GPT-4o-mini）
- 单次调用节省：$0.0003
- 生成10页累计节省：约 $0.002

---

## 🚀 快速开始

### 1. 基本使用

```python
from common.context_compressor import ContextCompressor

# 创建压缩器
compressor = ContextCompressor(
    max_history_slides=3,      # 保留最近3页的详细信息
    include_all_titles=True,   # 包含所有页面的标题
    track_duplicates=True      # 追踪重复内容
)

# 压缩历史上下文
compressed_context = compressor.compress_history(
    all_slides_xml=["<SECTION>...</SECTION>", ...],  # 所有已生成的XML
    current_index=9  # 当前生成第10页（索引从0开始）
)

# 使用压缩后的上下文
print(compressed_context)
```

### 2. 集成到现有代码

在 `ppt_writer/agent.py` 中已经集成，无需额外配置。系统会自动：
- 在生成第1页时初始化压缩器
- 在生成后续页面时自动压缩历史上下文
- 在日志中显示节省效果

### 3. 自定义配置

```python
# 保守配置（最大压缩）
compressor = ContextCompressor(
    max_history_slides=1,       # 仅保留最近1页
    include_all_titles=True,    # 保留所有标题
    track_duplicates=True
)
# 节省：85.9%

# 平衡配置（推荐）
compressor = ContextCompressor(
    max_history_slides=3,       # 保留最近3页
    include_all_titles=True,
    track_duplicates=True
)
# 节省：79.4%

# 详细配置（更多上下文）
compressor = ContextCompressor(
    max_history_slides=5,       # 保留最近5页
    include_all_titles=True,
    track_duplicates=True
)
# 节省：72.8%
```

---

## 🔧 工作原理

### 1. 信息提取

从完整的 XML 幻灯片中提取关键信息：
- ✅ 标题（H1 标签）
- ✅ 布局类型（vertical, left, columns 等）
- ✅ 关键要点（前5个要点）
- ✅ 图片链接
- ✅ 关键词（用于去重）

### 2. 智能压缩

```python
# 原始（3,473 字符）
<SECTION layout="vertical" page_number=1>
  <H1>人工智能的发展历程</H1>
  <BULLETS>
    <DIV><H3>关键点1</H3><P>这是第1页的第一个重要要点，包含了详细说明和背景信息。</P></DIV>
    <DIV><H3>关键点2</H3><P>这是第1页的第二个要点，展示了关键数据和事实。</P></DIV>
    <DIV><P>第三个补充要点，用于支持前面的论点和观点。</P></DIV>
  </BULLETS>
  <IMG src="https://example.com/image1.jpg" alt="第1页的配图" background="false" />
</SECTION>
...

# 压缩后（790 字符）
## 已生成页面总览:
第1页: 人工智能的发展历程、第2页: 机器学习基础概念、...

## 最近几页详细内容:

【第8页】未来发展趋势
布局: vertical
要点: 这是第8页的第一个重要要点，包含了详细说明和背景信息。, ...
图片: 1张

【第9页】实际案例分析
布局: vertical
要点: ...
图片: 1张
```

### 3. 去重追踪

自动追踪已使用的关键词和图片，避免重复：

```python
# 检查重复
dup_check = compressor.check_duplication(new_slide_xml)

if dup_check['has_duplicate']:
    print(f"重复关键词: {dup_check['duplicate_keywords']}")
    print(f"建议: {dup_check['suggestions']}")
```

---

## 📈 性能分析

### 不同页数的节省效果

| 页码 | 原始tokens | 压缩后tokens | 节省比例 |
|------|-----------|-------------|---------|
| 第1页 | 241 | 209 | 13.3% |
| 第2页 | 487 | 335 | 31.2% |
| 第3页 | 730 | 458 | 37.3% |
| 第4页 | 975 | 489 | 49.8% |
| 第5页 | 1,218 | 503 | 58.7% |
| 第10页 | 2,446 | 574 | 76.5% |

**结论**：页数越多，节省效果越显著。

### 不同配置的对比

| 配置 | 压缩后字符数 | 节省比例 | 适用场景 |
|------|------------|---------|---------|
| 保守（1页详细） | 483 | 85.9% | 成本敏感，简单主题 |
| 平衡（3页详细） | 709 | 79.4% | **推荐**，大多数场景 |
| 详细（5页详细） | 935 | 72.8% | 复杂主题，需要更多上下文 |
| 精简（3页，无标题） | 603 | 82.4% | 标题不重要时 |

---

## 🛠️ API 参考

### ContextCompressor

```python
class ContextCompressor:
    def __init__(
        self,
        max_history_slides: int = 3,
        include_all_titles: bool = True,
        track_duplicates: bool = True
    )
```

**参数：**
- `max_history_slides`: 保留最近几页的详细信息（默认3）
- `include_all_titles`: 是否包含所有页面的标题（默认True）
- `track_duplicates`: 是否追踪重复内容（默认True）

**方法：**

#### compress_history()

```python
def compress_history(
    self,
    all_slides_xml: List[str],
    current_index: int
) -> str
```

压缩历史上下文。

**参数：**
- `all_slides_xml`: 所有已生成页面的完整 XML 列表
- `current_index`: 当前正在生成的页码索引

**返回：**
- 压缩后的上下文字符串

#### extract_slide_info()

```python
def extract_slide_info(
    self,
    slide_xml: str,
    page_number: int
) -> SlideInfo
```

从 XML 中提取关键信息。

**返回：**
- `SlideInfo` 对象，包含标题、布局、要点、图片、关键词

#### check_duplication()

```python
def check_duplication(self, slide_xml: str) -> Dict
```

检查当前页面是否有重复内容。

**返回：**
```python
{
    "has_duplicate": bool,
    "duplicate_keywords": List[str],
    "duplicate_images": List[str],
    "suggestions": str
}
```

#### get_token_savings()

```python
def get_token_savings(
    self,
    original_length: int,
    compressed_length: int
) -> Dict
```

计算 token 节省情况。

**返回：**
```python
{
    "original_chars": int,
    "compressed_chars": int,
    "estimated_original_tokens": int,
    "estimated_compressed_tokens": int,
    "estimated_saved_tokens": int,
    "saved_percentage": float,
    "cost_savings_gpt4o": float,
    "cost_savings_gpt4o_mini": float
}
```

#### reset()

```python
def reset()
```

重置压缩器状态（用于新的生成任务）。

---

## 🧪 测试

运行测试脚本验证压缩效果：

```bash
cd backend/common
python test_context_compressor.py
```

测试内容：
1. ✅ 基本压缩功能
2. ✅ 渐进式压缩（模拟生成过程）
3. ✅ 重复内容检测
4. ✅ 不同配置对比

---

## 🔍 日志示例

生成PPT时的日志输出：

```
--- 正在生成第10页PPT ---
[INFO] 📊 上下文压缩: 原始=3473字符 → 压缩=790字符 (节省 77.3%, 约 1878 tokens)
```

---

## 💡 最佳实践

1. **推荐配置**：`max_history_slides=3`
   - 平衡了上下文保留和压缩率
   - 适用于大多数场景

2. **复杂主题**：`max_history_slides=5`
   - 需要更多上下文时使用
   - 仍能节省70%+的tokens

3. **成本敏感**：`max_history_slides=1`
   - 主题简单时使用
   - 最大化节省

4. **启用去重**：`track_duplicates=True`
   - 避免内容重复
   - 提升质量

5. **保留标题**：`include_all_titles=True`
   - 帮助LLM理解整体结构
   - 仅增加少量tokens

---

## 📝 注意事项

1. **估算误差**：Token 数量是估算值（字符数 × 0.7），实际可能略有差异
2. **向后兼容**：如果压缩器未初始化，系统会自动创建（不会影响现有功能）
3. **内存占用**：压缩器会追踪所有历史页面，内存占用极小
4. **准确性**：压缩保留了所有关键信息，不影响生成质量

---

## 🔄 回滚方法

如果需要回滚到原始实现，修改 `ppt_writer/agent.py` 中的第122-152行：

```python
# 原始实现（未压缩）
if current_slide_index == 0:
    callback_context.state["history_slides_xml"] = ""
else:
    all_generated_slides_content: List[str] = callback_context.state.get(
        "generated_slides_content", []
    )
    history_slides_xml = "\n\n".join(all_generated_slides_content)  # 完整XML
    callback_context.state["history_slides_xml"] = history_slides_xml
```

---

## 📧 反馈

如有问题或建议，请提交 Issue 或 PR。
