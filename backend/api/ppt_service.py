"""
PPT Service - LangChain 版本

使用 LangChain 架构的 PPT 生成服务
"""

import logging
import os
import re
import uuid
from typing import Optional, Dict, Any, List, AsyncGenerator

from langchain_openai import ChatOpenAI

# 导入 LangChain 组件（相对路径从 api/ 调整）
from agents.coordinator.master_graph import MasterGraph
from agents.models.state import PPTGenerationState, create_initial_state

logger = logging.getLogger(__name__)


class PptGenerationServiceLangChain:
    """
    PPT 生成服务 - LangChain 版本

    使用 LangGraph 和多 Agent 架构生成 PPT
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化服务

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 模型配置
        self._model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self._api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        self._base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL")
        self._temperature = 0.7
        self._llm_ready = bool(self._api_key)

        # 创建共享的 LLM 实例
        self._model = ChatOpenAI(
            model=self._model_name,
            api_key=self._api_key or "sk-mock",
            base_url=self._base_url,
            temperature=self._temperature,
        )

        # 质量控制配置
        self._enable_quality_checks = True
        self._quality_threshold = 0.8
        self._max_refinements = 3

        logger.info(
            f"[PptGenerationServiceLangChain] Initialized with model: {self._model_name}, "
            f"quality_checks={self._enable_quality_checks}"
        )

        if not self._llm_ready:
            logger.warning(
                "[PptGenerationServiceLangChain] No OPENAI_API_KEY/DEEPSEEK_API_KEY detected. "
                "Generation endpoints will return explicit configuration errors instead of placeholder output."
            )

    def _missing_llm_error(self) -> str:
        return (
            "未配置 LLM API Key（OPENAI_API_KEY 或 DEEPSEEK_API_KEY）。"
            "请先配置可用模型密钥后再生成大纲或PPT。"
        )

    def _create_master_graph(self) -> MasterGraph:
        """
        创建 MasterGraph 实例

        Returns:
            MasterGraph 实例
        """
        return MasterGraph(
            model=self._model,
            enable_quality_checks=self._enable_quality_checks,
            quality_threshold=self._quality_threshold,
            max_refinements=self._max_refinements,
        )

    # ==================== 大纲生成 ====================

    async def generate_outline(
        self,
        user_input: str,
        language: str = "zh-CN",
        model_name: str = None,
        expected_cards: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        生成大纲

        Args:
            user_input: 用户输入
            language: 语言
            model_name: 模型名称（可选，覆盖默认配置）

        Yields:
            生成的文本片段
        """
        if not self._llm_ready:
            yield f"错误：{self._missing_llm_error()}"
            return

        try:
            # 直接使用需求解析和框架设计 Agent
            from agents.core.requirements.requirement_agent import create_requirement_parser
            from agents.core.planning.framework_agent import create_framework_designer

            requirement_agent = create_requirement_parser(self._model)
            requirement_state = create_initial_state(
                user_input=user_input,
                task_id=f"outline_{uuid.uuid4().hex[:8]}",
            )

            # 解析需求
            parsed_state = await requirement_agent.run_node(requirement_state)
            requirements = parsed_state.get("structured_requirements", {})

            if isinstance(expected_cards, int) and 1 <= expected_cards <= 50:
                requirements["page_num"] = expected_cards
                parsed_state["structured_requirements"] = requirements

            framework_agent = create_framework_designer(self._model)
            framework_state = await framework_agent.run_node(parsed_state)

            # 提取框架信息
            framework = framework_state.get("ppt_framework", {})
            pages = framework.get("ppt_framework", [])

            if not pages:
                yield "错误：未能生成框架"
                return

            content_pages = [p for p in pages if p.get("page_type") == "content"]
            generic_title_count = 0
            generic_content_count = 0
            for page in content_pages:
                title = str(page.get("title") or "")
                core_content = str(page.get("core_content") or "")
                if re.match(r"^第\d+部分$", title):
                    generic_title_count += 1
                if "核心内容" in core_content:
                    generic_content_count += 1

            if (
                content_pages
                and generic_title_count == len(content_pages)
                and generic_content_count == len(content_pages)
            ):
                logger.error("[generate_outline] Detected placeholder fallback framework")
                yield "错误：模型返回了降级占位目录（可能是 API Key 无效或模型调用失败），请检查模型配置后重试。"
                return

            # 仅流式输出每一页标题，避免把状态文案或整段 markdown 混入前端卡片
            emitted_count = 0
            for page in pages:
                title = (page.get("title") or "").strip()
                if not title:
                    continue
                emitted_count += 1
                yield f"# {title}\n"

            # 兜底：如果标题都为空，至少返回一个主题标题
            if emitted_count == 0:
                fallback_title = requirements.get("ppt_topic", framework.get("title", "PPT大纲"))
                yield f"# {fallback_title}\n"

            logger.info("[generate_outline] 大纲生成成功")

        except Exception as e:
            logger.error(f"[generate_outline] 生成失败: {e}", exc_info=True)
            yield f"错误：{str(e)}"

    # ==================== PPT 生成 ====================

    async def generate_slides(
        self,
        title: str,
        outline: List[str],
        language: str = "zh-CN",
        tone: str = "professional",
        num_slides: int = 10,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        生成幻灯片

        Args:
            title: 标题
            outline: 大纲列表
            language: 语言
            tone: 语气
            num_slides: 幻灯片数量

        Yields:
            事件数据字典
        """
        if not self._llm_ready:
            yield {"type": "error", "message": self._missing_llm_error()}
            return

        yield {"type": "status", "stage": "init", "message": "开始生成PPT..."}

        try:
            # 将 outline 列表转换为用户输入
            outline_text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(outline)])
            user_input = f"""生成一份关于「{title}」的PPT

语言：{language}
风格：{tone}
页数：{num_slides}

大纲：
{outline_text}
"""

            # 创建 MasterGraph
            graph = self._create_master_graph()

            # 创建初始状态
            state = create_initial_state(
                user_input=user_input,
                task_id=f"slides_{uuid.uuid4().hex[:8]}",
            )

            # 使用带进度的生成
            async def on_progress(update):
                yield {"type": "progress", "stage": update.stage, "progress": update.progress}

            async def on_stage_complete(stage, state):
                yield {"type": "stage_complete", "stage": stage}

            # 执行生成
            final_state = await graph.generate_with_callbacks(
                user_input=user_input,
                on_progress=lambda u: on_progress(u),
                on_stage_complete=lambda s, st: on_stage_complete(s, st),
            )

            # 返回结果
            ppt_output = final_state.get("ppt_output", {})
            if ppt_output:
                yield {
                    "type": "complete",
                    "file_path": ppt_output.get("file_path"),
                    "total_pages": ppt_output.get("total_pages"),
                    "preview": ppt_output.get("preview_data"),
                }
            else:
                yield {"type": "error", "message": "未能生成PPT"}

        except Exception as e:
            logger.error(f"[generate_slides] 生成失败: {e}", exc_info=True)
            yield {"type": "error", "message": str(e)}

    # ==================== 完整 PPT 生成 ====================

    async def generate_ppt_full(
        self,
        user_input: str,
        user_id: str = "anonymous",
        enable_page_pipeline: bool = True,
        execution_mode: str = "full",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        完整生成 PPT

        Args:
            user_input: 用户输入
            user_id: 用户ID
            enable_page_pipeline: 是否启用页面级流水线（LangChain 默认启用）
            execution_mode: 执行模式 (full, phase_1, phase_2)

        Yields:
            事件数据字典
        """
        task_id = f"ppt_{uuid.uuid4().hex[:8]}"

        if not self._llm_ready:
            yield {
                "type": "error",
                "task_id": task_id,
                "message": self._missing_llm_error(),
            }
            return

        logger.info(f"[generate_ppt_full] 开始任务: {task_id}, user: {user_id}")

        yield {
            "type": "start",
            "task_id": task_id,
            "message": "开始生成PPT...",
        }

        try:
            # 创建 MasterGraph
            graph = self._create_master_graph()

            # 进度回调
            progress_updates = []

            def on_progress(update):
                """收集进度更新"""
                progress_updates.append(
                    {
                        "stage": update.stage,
                        "progress": update.progress,
                        "message": update.message,
                    }
                )

            def on_stage_complete(stage, state):
                """阶段完成回调"""
                logger.info(f"[generate_ppt_full] 阶段完成: {stage}")

            # 执行生成
            final_state = await graph.generate_with_callbacks(
                user_input=user_input,
                user_id=user_id,
                on_progress=on_progress,
                on_stage_complete=on_stage_complete,
            )

            # 发送进度更新
            for update in progress_updates:
                yield {
                    "type": "progress",
                    "stage": update["stage"],
                    "progress": update["progress"],
                    "message": update["message"],
                }

            # 检查质量评估
            quality_assessment = final_state.get("quality_assessment", {})
            if quality_assessment:
                yield {
                    "type": "quality",
                    "score": quality_assessment.get("overall_score"),
                    "passes": quality_assessment.get("passes_threshold"),
                    "threshold": quality_assessment.get("threshold"),
                }

            # 返回最终结果
            ppt_output = final_state.get("ppt_output", {})
            framework = final_state.get("ppt_framework", {})

            if ppt_output:
                yield {
                    "type": "complete",
                    "task_id": task_id,
                    "file_path": ppt_output.get("file_path"),
                    "total_pages": ppt_output.get("total_pages"),
                    "preview": ppt_output.get("preview_data"),
                    "framework": framework,
                }
                logger.info(f"[generate_ppt_full] 任务完成: {task_id}")
            else:
                yield {
                    "type": "error",
                    "task_id": task_id,
                    "message": "未能生成PPT输出",
                }

        except Exception as e:
            logger.error(f"[generate_ppt_full] 任务失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "task_id": task_id,
                "message": str(e),
            }


# 全局服务实例
_global_service: Optional[PptGenerationServiceLangChain] = None


def get_ppt_generation_service_langchain(
    config: Optional[Dict[str, Any]] = None,
) -> PptGenerationServiceLangChain:
    """获取全局 PPT 生成服务实例（LangChain 版本）"""
    global _global_service
    if _global_service is None:
        _global_service = PptGenerationServiceLangChain(config)
    return _global_service


def reset_ppt_generation_service_langchain():
    """重置全局 PPT 生成服务实例"""
    global _global_service
    _global_service = None
