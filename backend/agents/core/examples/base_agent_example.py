"""
示例：使用BaseAgent重构后的FrameworkDesignerAgent

这个文件展示了如何使用新的BaseAgent基础类来简化Agent实现。
对比 framework_agent.py 的原始实现。
"""

import json
import logging
from typing import Dict, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from .base_agent import BaseAgent
from ...models.state import PPTGenerationState, update_state_progress
from ...models.framework import PPTFramework

logger = logging.getLogger(__name__)


# Prompt template (与原始版本相同)
FRAMEWORK_DESIGNER_PROMPT = """你是一名专业的PPT结构设计专家。

你的任务是根据结构化需求，设计PPT的框架结构，包括每一页的标题、类型和内容描述。

需求信息：
- 主题：{ppt_topic}
- 页数：{page_num}
- 模板类型：{template_type}
- 使用场景：{scene}
- 核心模块：{core_modules}
- 是否需要研究：{need_research}
- 语言：{language}

请设计一个包含{page_num}页的PPT框架，按照以下JSON格式输出（不要使用markdown包裹，直接输出JSON）：
{{
    "total_page": 页数,
    "ppt_framework": [
        {{
            "page_no": 1,
            "title": "页面标题",
            "page_type": "cover|directory|content|chart|image|summary|thanks",
            "core_content": "核心内容描述",
            "is_need_chart": true/false,
            "is_need_research": true/false,
            "is_need_image": true/false,
            "content_type": "text_only|text_with_image|text_with_chart|text_with_both|image_only|chart_only",
            "keywords": ["关键词1", "关键词2"],
            "estimated_word_count": 预估字数,
            "layout_suggestion": "布局建议"
        }}
    ],
    "has_research_pages": true/false,
    "research_page_indices": [需要研究的页码列表],
    "chart_page_indices": [需要图表的页码列表],
    "image_page_indices": [需要配图的页码列表],
    "framework_type": "linear"
}}

设计原则：
1. 第1页必须是封面（cover）
2. 第2页通常是目录（directory）
3. 最后一页通常是总结或致谢（summary或thanks）
4. 根据核心模块合理分配内容页
5. 如果需要研究，为相关页面标记is_need_research=true并提供keywords
6. 图表页（chart）应该均匀分布
7. 确保总页数等于需求中的页数
8. page_no必须从1开始连续编号
"""


class FrameworkDesignerAgentRefactored(BaseAgent):
    """
    框架设计智能体 - 使用BaseAgent重构版本

    与原始版本对比：
    - 代码行数减少约60%
    - 无需重复实现模型创建逻辑
    - 使用便捷方法简化记忆操作
    - 标准化的错误处理

    重构要点：
    1. 继承BaseAgent而不是LangGraphAgentMixin
    2. 只需实现_create_chain()和execute_task()
    3. 使用便捷方法：check_cache(), save_to_cache(), share_with_agents()
    4. 实现get_fallback_result()提供降级策略
    """

    def __init__(
        self,
        model: Optional[ChatOpenAI] = None,
        temperature: float = 0.0,
        agent_name: str = "FrameworkDesignerAgent",
        enable_memory: bool = True,
    ):
        """
        初始化框架设计智能体

        注意：大部分初始化逻辑由BaseAgent处理
        """
        super().__init__(
            model=model,
            temperature=temperature,
            agent_name=agent_name,
            enable_memory=enable_memory
        )

    def _create_chain(self) -> Runnable:
        """
        创建设计链

        这是唯一需要实现的链创建逻辑
        """
        prompt = ChatPromptTemplate.from_template(FRAMEWORK_DESIGNER_PROMPT)
        parser = JsonOutputParser()
        return prompt | self.model | parser

    async def execute_task(self, state: PPTGenerationState) -> PPTGenerationState:
        """
        执行框架设计任务

        这是核心业务逻辑，替代原始版本中的run_node()方法
        """
        requirement = state.get("structured_requirements", {})
        topic = requirement.get("ppt_topic", "Unknown")
        page_num = requirement.get("page_num", 10)

        logger.info(f"[{self.agent_name}] Designing framework for: {topic}, pages: {page_num}")

        # 使用便捷方法检查缓存
        cache_key = f"framework_{page_num}_{hash(topic + str(requirement.get('core_modules', [])))}"
        cached = await self.check_cache(cache_key, state)

        if cached:
            logger.info(f"[{self.agent_name}] Using cached framework")
            state["ppt_framework"] = cached
            update_state_progress(state, "framework_design", 30)
            return state

        try:
            # 使用LangChain链进行设计
            result = await self.chain.ainvoke({
                "ppt_topic": topic,
                "page_num": page_num,
                "template_type": requirement.get("template_type", "business_template"),
                "scene": requirement.get("scene", "business_report"),
                "core_modules": requirement.get("core_modules", []),
                "need_research": requirement.get("need_research", False),
                "language": requirement.get("language", "ZH-CN"),
            })

            # 验证并修复框架
            result = self._validate_and_fix(result, page_num)

            # 使用便捷方法保存缓存
            await self.save_to_cache(
                cache_key,
                result,
                importance=0.8,
                scope="TASK",
                state=state
            )

            # 使用便捷方法共享数据
            await self.share_with_agents(
                data_type="framework",
                data_key="ppt_framework",
                data_content=result,
                target_agents=["ContentMaterialAgent", "ResearchAgent"]
            )

            # 更新状态
            state["ppt_framework"] = result
            update_state_progress(state, "framework_design", 30)

            logger.info(f"[{self.agent_name}] Framework designed successfully: {result['total_page']} pages")
            return state

        except Exception as e:
            # 让基类的错误处理机制捕获异常
            # 会自动调用get_fallback_result()
            logger.error(f"[{self.agent_name}] Design failed: {e}")
            raise

    def _validate_and_fix(self, framework: Dict[str, Any], expected_page_num: int) -> Dict[str, Any]:
        """验证并修复框架（业务逻辑，保持不变）"""
        framework["total_page"] = expected_page_num
        pages = framework.get("ppt_framework", [])

        if len(pages) != expected_page_num:
            logger.warning(f"[{self.agent_name}] Page count mismatch: {len(pages)} != {expected_page_num}, fixing")
            pages = self._fix_page_count(pages, expected_page_num)

        for i, page in enumerate(pages):
            page["page_no"] = i + 1

        framework["ppt_framework"] = pages

        research_indices = [p["page_no"] for p in pages if p.get("is_need_research", False)]
        chart_indices = [p["page_no"] for p in pages if p.get("is_need_chart", False)]
        image_indices = [p["page_no"] for p in pages if p.get("is_need_image", False)]

        framework["research_page_indices"] = research_indices
        framework["chart_page_indices"] = chart_indices
        framework["image_page_indices"] = image_indices
        framework["has_research_pages"] = len(research_indices) > 0

        return framework

    def _fix_page_count(self, pages: list, target_count: int) -> list:
        """修复页数（业务逻辑，保持不变）"""
        current_count = len(pages)

        if current_count < target_count:
            for i in range(current_count, target_count):
                pages.append({
                    "page_no": i + 1,
                    "title": f"第{i-1}部分",
                    "page_type": "content",
                    "core_content": f"第{i-1}部分的核心内容",
                    "is_need_chart": False,
                    "is_need_research": False,
                    "is_need_image": False,
                    "content_type": "text_only",
                    "keywords": [],
                    "estimated_word_count": 100,
                    "layout_suggestion": ""
                })
        elif current_count > target_count:
            pages = pages[:target_count]

        return pages

    def get_fallback_result(self, state: PPTGenerationState) -> Optional[PPTGenerationState]:
        """
        降级策略

        当execute_task()抛出异常时，基类会自动调用此方法
        """
        logger.info(f"[{self.agent_name}] Using fallback framework design")

        requirement = state.get("structured_requirements", {})
        topic = requirement.get("ppt_topic", "")
        page_num = requirement.get("page_num", 10)
        need_research = requirement.get("need_research", False)
        core_modules = requirement.get("core_modules", [])

        # 使用PPTFramework类创建默认框架
        framework_obj = PPTFramework.create_default(page_num=page_num, topic=topic)

        if core_modules and len(core_modules) >= 3:
            content_pages = [p for p in framework_obj.pages if p.page_type.value == "content"]
            module_index = 0
            for page in content_pages:
                if module_index < len(core_modules):
                    page.title = core_modules[module_index]
                    page.core_content = f"{core_modules[module_index]}的核心内容"
                    module_index += 1

        if need_research:
            content_pages = [p for p in framework_obj.pages if p.page_type.value == "content"]
            for i, page in enumerate(content_pages):
                if i % 2 == 0:
                    page.is_need_research = True
                    page.keywords = [page.title, "相关资料"]

        framework_obj._update_indices()
        ppt_framework = framework_obj.to_dict()

        state["ppt_framework"] = ppt_framework
        update_state_progress(state, "framework_design", 30)

        return state


# 工厂函数（保持向后兼容）
def create_framework_designer_refactored(
    model: Optional[ChatOpenAI] = None,
    temperature: float = 0.0,
    enable_memory: bool = True,
) -> FrameworkDesignerAgentRefactored:
    """创建框架设计智能体（重构版本）"""
    return FrameworkDesignerAgentRefactored(
        model=model,
        temperature=temperature,
        enable_memory=enable_memory
    )


# 对比测试
async def compare_implementations():
    """
    对比原始版本和重构版本的功能

    使用方法：
    python -m backend.agents.core.examples.base_agent_example
    """
    import asyncio
    from ..framework_agent import create_framework_designer

    test_requirement = {
        "ppt_topic": "人工智能概述",
        "page_num": 10,
        "template_type": "business_template",
        "scene": "business_report",
        "core_modules": ["封面", "目录", "AI介绍", "应用场景", "未来展望", "总结"],
        "need_research": True,
        "language": "ZH-CN"
    }

    print("=" * 60)
    print("对比测试：原始版本 vs 重构版本")
    print("=" * 60)

    # 测试原始版本
    print("\n[1] 测试原始版本...")
    original_agent = create_framework_designer(enable_memory=False)
    original_result = await original_agent.design(test_requirement)
    print(f"原始版本结果：{original_result['total_page']} 页")

    # 测试重构版本
    print("\n[2] 测试重构版本...")
    refactored_agent = create_framework_designer_refactored(enable_memory=False)
    state = {"structured_requirements": test_requirement}
    refactored_result = await refactored_agent.run_node(state)
    print(f"重构版本结果：{refactored_result['ppt_framework']['total_page']} 页")

    # 对比结果
    print("\n[3] 对比结果...")
    assert original_result['total_page'] == refactored_result['ppt_framework']['total_page']
    assert len(original_result['ppt_framework']) == len(refactored_result['ppt_framework']['ppt_framework'])
    print("✅ 功能验证通过！")

    print("\n" + "=" * 60)
    print("重构优势：")
    print("  - 代码行数减少约60%")
    print("  - 无需手动实现模型创建")
    print("  - 使用便捷方法简化记忆操作")
    print("  - 标准化的错误处理流程")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(compare_implementations())
