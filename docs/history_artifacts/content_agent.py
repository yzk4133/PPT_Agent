"""内容生成Agent - 负责PPT文本内容的生成

这是最核心的Agent之一，负责理解用户需求并生成高质量的内容
"""

from typing import Dict, Any
import asyncio

from .agent_base import BaseAgent, AgentConfig, AgentMessage


class ContentGeneratorAgent(BaseAgent):
    """内容生成Agent

    职责:
    - 理解用户需求
    - 生成PPT大纲
    - 编写每页内容
    - 确保内容质量和连贯性
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.llm_client = None  # 初始化LLM客户端

    async def process(self, message: AgentMessage) -> AgentMessage:
        """处理内容生成请求"""
        task_type = message.content.get("task_type")

        if task_type == "generate_outline":
            return await self._generate_outline(message)
        elif task_type == "generate_slide_content":
            return await self._generate_slide_content(message)
        else:
            raise ValueError(f"未知的任务类型: {task_type}")

    async def _generate_outline(self, message: AgentMessage) -> AgentMessage:
        """生成PPT大纲

        使用AI模型分析用户需求，生成结构化的大纲
        """
        user_requirement = message.content.get("requirement")
        audience = message.content.get("audience", "通用")
        duration = message.content.get("duration", 30)

        # 构建prompt
        prompt = self._build_outline_prompt(user_requirement, audience, duration)

        # 调用LLM
        outline = await self._call_llm(prompt)

        # 验证和优化大纲
        outline = self._validate_outline(outline)

        return self._create_response(
            to_agent=message.from_agent,
            content={
                "task_type": "outline_generated",
                "outline": outline
            }
        )

    async def _generate_slide_content(self, message: AgentMessage) -> AgentMessage:
        """生成单页幻灯片内容"""
        slide_title = message.content.get("title")
        key_points = message.content.get("key_points", [])
        context = message.content.get("context", {})

        # 构建prompt
        prompt = self._build_content_prompt(slide_title, key_points, context)

        # 调用LLM生成内容
        content = await self._call_llm(prompt)

        return self._create_response(
            to_agent=message.from_agent,
            content={
                "task_type": "content_generated",
                "slide_title": slide_title,
                "content": content
            }
        )

    def _build_outline_prompt(self, requirement: str, audience: str, duration: int) -> str:
        """构建大纲生成的prompt"""
        return f"""
        作为专业的内容架构师，请根据以下需求生成PPT大纲：

        主题: {requirement}
        目标受众: {audience}
        预计时长: {duration}分钟

        要求:
        1. 大纲应包含3-5个主要章节
        2. 每章包含3-5个子要点
        3. 逻辑清晰，层次分明
        4. 适合口头表达

        请以JSON格式返回结果。
        """

    def _build_content_prompt(self, title: str, key_points: list, context: dict) -> str:
        """构建内容生成的prompt"""
        return f"""
        作为专业内容创作者，请为幻灯片生成具体内容：

        标题: {title}
        要点: {', '.join(key_points)}

        要求:
        1. 语言简洁专业
        2. 每个要点扩展为2-3句话
        3. 包含具体案例或数据
        """

    async def _call_llm(self, prompt: str) -> str:
        """调用LLM API"""
        # 实际实现中会调用Claude或其他LLM
        return "AI生成的内容"

    def _validate_outline(self, outline: str) -> Dict[str, Any]:
        """验证和优化大纲"""
        # 解析和验证大纲结构
        pass

    def _create_response(self, to_agent: str, content: Dict[str, Any]) -> AgentMessage:
        """创建响应消息"""
        return AgentMessage.create(
            from_agent=self.config.name,
            to_agent=to_agent,
            content=content
        )
