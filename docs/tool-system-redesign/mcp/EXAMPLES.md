# MCP使用示例

> MultiAgentPPT项目中MCP服务器的实际使用代码示例

---

## 📋 目录

1. [基础使用](#基础使用)
2. [完整示例](#完整示例)
3. [最佳实践](#最佳实践)
4. [常见场景](#常见场景)

---

## 🚀 基础使用

### 示例1: 使用智谱搜索资料

```python
from backend.tools.domain.resource.zhipu_search_tool import zhipu_search_tool

# 使用智谱搜索
results = await zhipu_search_tool.invoke(
    query="AI人工智能发展趋势 2025",
    count=5
)

# 处理搜索结果
print(f"找到 {len(results)} 条结果")
for result in results:
    print(f"标题: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"摘要: {result['snippet']}")
    print("---")
```

### 示例2: 使用Zai视觉理解图片

```python
from backend.tools.domain.resource.zai_vision_tool import zai_vision_tool

# 图片内容理解
analysis = await zai_vision_tool.invoke(
    tool_name="vision_understand",
    image_url="https://example.com/image.jpg",
    detail_level="high"
)

print(f"图片描述: {analysis['description']}")
print(f"主要元素: {analysis['objects']}")
print(f"颜色风格: {analysis['style']}")
```

### 示例3: 视觉问答

```python
# 针对图片提问
qa_result = await zai_vision_tool.invoke(
    tool_name="vision_qa",
    image_url="https://example.com/chart.jpg",
    question="这张图表展示了什么数据？"
)

print(f"回答: {qa_result['answer']}")
print(f"置信度: {qa_result['confidence']}")
```

---

## 🎯 完整示例

### 示例4: PPT生成完整流程

```python
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from backend.tools.application.tool_registry import NativeToolRegistry
from backend.agents.core.agent.agent import Agent

async def main():
    """完整的PPT生成流程"""

    # 1. 加载环境变量
    load_dotenv()

    # 2. 初始化LLM
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    # 3. 获取工具注册表
    registry = NativeToolRegistry()

    # 4. 创建Agent
    agent = Agent(llm=llm, tool_registry=registry)

    # 5. 生成PPT
    topic = "人工智能在医疗领域的应用"
    result = await agent.run(f"""
    请生成一份关于"{topic}"的PPT，要求:
    - 10页内容
    - 包含案例分析
    - 包含数据图表
    - 使用现代化设计风格

    请先搜索相关资料，然后为每页选择合适的配图。
    """)

    print(f"✅ PPT生成完成: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 示例5: 智能配图选择

```python
async def select_best_image_for_slide(slide_content: str, image_candidates: list):
    """
    为幻灯片内容选择最合适的配图

    Args:
        slide_content: 幻灯片文字内容
        image_candidates: 候选图片URL列表

    Returns:
        最合适的图片URL
    """

    best_image = None
    best_score = 0

    for image_url in image_candidates:
        # 使用Zai视觉理解图片
        analysis = await zai_vision_tool.invoke(
            tool_name="vision_understand",
            image_url=image_url,
            detail_level="medium"
        )

        # 提取图片描述
        image_description = analysis['description']

        # 使用LLM评估匹配度
        score = await llm.ainvoke(f"""
        请评估图片与内容的匹配度（0-100分）:

        幻灯片内容: {slide_content}

        图片描述: {image_description}

        只返回数字分数。
        """)

        score = int(score.strip())

        if score > best_score:
            best_score = score
            best_image = image_url

    return best_image
```

---

## 🏗️ 高级用法

### 示例6: 批量图片分析

```python
async def batch_analyze_images(image_urls: list[str]) -> list[dict]:
    """批量分析图片"""

    tasks = []
    for url in image_urls:
        task = zai_vision_tool.invoke(
            tool_name="vision_understand",
            image_url=url,
            detail_level="medium"
        )
        tasks.append(task)

    # 并发执行
    results = await asyncio.gather(*tasks)

    return results

# 使用示例
images = [
    "https://example.com/img1.jpg",
    "https://example.com/img2.jpg",
    "https://example.com/img3.jpg"
]

analyses = await batch_analyze_images(images)
for img, analysis in zip(images, analyses):
    print(f"{img}: {analysis['description']}")
```

### 示例7: OCR文字识别

```python
async def extract_text_from_image(image_url: str) -> str:
    """从图片中提取文字"""

    ocr_result = await zai_vision_tool.invoke(
        tool_name="vision_ocr",
        image_url=image_url,
        language="zh"  # 中文识别
    )

    return ocr_result['text']

# 使用示例
text = await extract_text_from_image("https://example.com/document.jpg")
print(f"识别出的文字:\n{text}")
```

### 示例8: 图片对比

```python
async def compare_images(image_url1: str, image_url2: str) -> dict:
    """对比两张图片的相似度"""

    comparison = await zai_vision_tool.invoke(
        tool_name="vision_compare",
        image_url1=image_url1,
        image_url2=image_url2
    )

    return {
        "similarity": comparison['similarity'],
        "differences": comparison['differences'],
        "recommendation": comparison['recommendation']
    }
```

---

## 🎨 最佳实践

### 1. 智能配图工作流

```python
async def smart_image_workflow(slide_content: str):
    """智能配图完整流程"""

    # Step 1: 搜索图片
    search_results = await search_images_tool.invoke(
        query=slide_content[:50],  # 使用前50个字符搜索
        count=5
    )

    # Step 2: 筛选图片
    candidate_urls = [r['url'] for r in search_results]

    # Step 3: 选择最佳图片
    best_image = await select_best_image_for_slide(
        slide_content,
        candidate_urls
    )

    # Step 4: 分析选中图片
    analysis = await zai_vision_tool.invoke(
        tool_name="vision_understand",
        image_url=best_image,
        detail_level="high"
    )

    return {
        "image_url": best_image,
        "analysis": analysis
    }
```

### 2. 错误处理

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def safe_vision_call(tool, **kwargs):
    """带重试的安全视觉调用"""

    try:
        result = await tool.invoke(**kwargs)
        logger.info(f"✅ 视觉分析成功")
        return result

    except Exception as e:
        logger.error(f"❌ 视觉分析失败: {str(e)}")
        # 返回默认值
        return {
            "description": "图片分析失败",
            "objects": [],
            "style": "unknown"
        }
```

### 3. 缓存策略

```python
from cachetools import TTLCache

class CachedVisionTool:
    """带缓存的视觉工具"""

    def __init__(self, vision_tool, ttl: int = 3600):
        self.tool = vision_tool
        self.cache = TTLCache(maxsize=100, ttl=ttl)

    async def invoke(self, tool_name: str, image_url: str, **kwargs):
        # 生成缓存键
        cache_key = f"{tool_name}:{image_url}"

        # 检查缓存
        if cache_key in self.cache:
            logger.info(f"缓存命中: {cache_key}")
            return self.cache[cache_key]

        # 调用视觉工具
        result = await self.tool.invoke(
            tool_name=tool_name,
            image_url=image_url,
            **kwargs
        )

        # 存入缓存
        self.cache[cache_key] = result

        return result

# 使用
cached_vision = CachedVisionTool(zai_vision_tool, ttl=1800)
```

---

## 🔧 常见场景

### 场景1: 生成带配图的幻灯片

```python
async def create_slide_with_image(title: str, content: str):
    """创建带配图的幻灯片"""

    # 1. 搜索配图
    images = await search_images_tool.invoke(
        query=title,
        count=3
    )

    # 2. 选择最佳配图
    best_image = await select_best_image_for_slide(
        content,
        [img['url'] for img in images]
    )

    # 3. 分析图片
    analysis = await zai_vision_tool.invoke(
        tool_name="vision_understand",
        image_url=best_image
    )

    # 4. 生成幻灯片
    slide = {
        "title": title,
        "content": content.split('\n'),
        "image": best_image,
        "image_description": analysis['description']
    }

    return slide
```

### 场景2: 批量处理PPT配图

```python
async def process_all_slides(slides: list[dict]):
    """为所有幻灯片添加配图"""

    processed_slides = []

    for slide in slides:
        title = slide['title']
        content = slide['content']

        # 生成配图
        slide_with_image = await create_slide_with_image(title, content)
        processed_slides.append(slide_with_image)

        logger.info(f"✅ 已处理: {title}")

    return processed_slides
```

### 场景3: 搜索并分析资料

```python
async def search_and_analyze(topic: str):
    """搜索并分析资料"""

    # 1. 搜索资料
    search_results = await zhipu_search_tool.invoke(
        query=topic,
        count=5
    )

    analyzed_results = []

    for result in search_results:
        # 2. 如果有图片，分析图片
        if 'image' in result:
            try:
                analysis = await zai_vision_tool.invoke(
                    tool_name="vision_understand",
                    image_url=result['image']
                )
                result['image_analysis'] = analysis
            except Exception as e:
                logger.warning(f"图片分析失败: {e}")

        analyzed_results.append(result)

    return analyzed_results
```

---

## 📊 调试技巧

### 1. 详细日志

```python
import logging

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_debug.log'),
        logging.StreamHandler()
    ]
)
```

### 2. 请求追踪

```python
import time

class TracedMCPTool:
    """带追踪的MCP工具"""

    async def invoke(self, **kwargs):
        logger.info(f"🔵 调用工具: {self.name}")
        logger.debug(f"参数: {kwargs}")

        start = time.time()
        result = await super().invoke(**kwargs)
        duration = time.time() - start

        logger.info(f"🟢 工具完成: {self.name} (耗时: {duration:.2f}s)")

        return result
```

### 3. 性能分析

```python
import cProfile

def profile_mcp_call():
    """性能分析"""
    cProfile.run('await zhipu_search_tool.invoke(query="AI")', 'mcp_profile.stats')

# 查看分析结果
# pip install snakeviz
# snakeviz mcp_profile.stats
```

---

## 🔗 工具组合示例

### 示例: 完整的PPT生成流程

```python
async def generate_ppt_with_mcp(topic: str):
    """使用MCP工具生成完整PPT"""

    # 1. 搜索资料
    logger.info("🔍 搜索相关资料...")
    references = await zhipu_search_tool.invoke(
        query=topic,
        count=10
    )

    # 2. 生成大纲
    logger.info("📝 生成PPT大纲...")
    outline = await llm.ainvoke(f"""
    基于"{topic}"和相关资料，生成一个10页的PPT大纲。
    资料: {references}
    """)

    # 3. 为每页生成内容和配图
    slides = []
    for slide_info in outline['slides']:
        # 生成内容
        content = await llm.ainvoke(f"""
        为幻灯片"{slide_info['title']}"生成详细内容。
        """)

        # 搜索配图
        images = await search_images_tool.invoke(
            query=slide_info['title'],
            count=3
        )

        # 选择最佳配图
        if images:
            best_image = await select_best_image_for_slide(
                content,
                [img['url'] for img in images]
            )
        else:
            best_image = None

        slides.append({
            'title': slide_info['title'],
            'content': content,
            'image': best_image
        })

    # 4. 生成PPT
    logger.info("📊 生成PPT文件...")
    ppt_result = await create_pptx_tool.invoke(
        slides=slides,
        template_path="templates/default.pptx"
    )

    return ppt_result
```

---

**文档版本**: v2.0
**更新日期**: 2026-03-07
**适用项目**: MultiAgentPPT
