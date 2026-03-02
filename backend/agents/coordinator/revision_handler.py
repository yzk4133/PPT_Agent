"""
LangGraph 协调器的修订处理器

处理 PPT 生成的用户修订请求。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field, field_validator

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from infrastructure.config import get_llm_config

from ..models.state import PPTGenerationState

logger = logging.getLogger(__name__)


class RevisionRequest(BaseModel):
    """
    修订请求数据结构

    属性：
        type: 修订类型 (content/style/structure/research)
        target: 目标范围 (page_index/all)
        instructions: 用户指令
        page_indices: 要修订的具体页面索引（针对性修订）
    """

    type: Literal["content", "style", "structure", "research"] = Field(
        default="content", description="修订类型"
    )
    target: Literal["page_index", "all", "section"] = Field(
        default="all", description="目标范围"
    )
    instructions: str = Field(min_length=1, description="用户指令")
    page_indices: Optional[List[int]] = Field(default=None, description="要修订的页面索引")
    section_name: Optional[str] = Field(default=None, description="章节名称")

    @field_validator('page_indices')
    @classmethod
    def validate_page_indices(cls, v):
        """验证页面索引"""
        if v is not None:
            if not all(idx >= 0 for idx in v):
                raise ValueError("页面索引必须大于等于0")
        return v


class RevisionHandler:
    """
    处理 PPT 修订请求

    处理用户修订请求并相应地更新 PPT 内容。
    """

    def __init__(self, model: Optional[ChatOpenAI] = None):
        """
        初始化修订处理器

        参数：
            model: 用于内容修订的 LLM 模型
        """
        self.model = model

        if self.model is None:
            llm_config = get_llm_config(temperature=0.7)

            self.model = ChatOpenAI(
                **llm_config.to_langchain_config()
            )

        logger.info("[RevisionHandler] Initialized")

    async def handle_revision_request(
        self,
        state: PPTGenerationState,
        revision_request: Dict[str, Any],
    ) -> PPTGenerationState:
        """
        处理修订请求

        参数：
            state: 当前状态
            revision_request: 修订请求字典

        返回：
            应用修订后的更新状态
        """
        logger.info(
            f"[RevisionHandler] Handling revision request: " f"type={revision_request.get('type')}"
        )

        # Parse revision request
        request = self._parse_revision_request(revision_request)

        # Track revision in state
        if "revision_history" not in state:
            state["revision_history"] = []

        state["revision_history"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "type": request.type,
                "instructions": request.instructions,
                "target": request.target,
            }
        )

        # Route to appropriate handler
        if request.type == "content":
            return await self._revise_content(state, request)
        elif request.type == "style":
            return await self._revise_style(state, request)
        elif request.type == "structure":
            return await self._revise_structure(state, request)
        elif request.type == "research":
            return await self._revise_research(state, request)
        else:
            logger.warning(f"[RevisionHandler] Unknown revision type: {request.type}")
            return state

    async def _revise_content(
        self,
        state: PPTGenerationState,
        request: RevisionRequest,
    ) -> PPTGenerationState:
        """根据用户反馈修订内容"""
        logger.info("[RevisionHandler] Revising content")

        content_materials = state.get("content_materials", [])

        if not content_materials:
            logger.warning("[RevisionHandler] No content materials to revise")
            return state

        # Determine which pages to revise
        if request.target == "all":
            indices = range(len(content_materials))
        elif request.page_indices:
            indices = request.page_indices
        else:
            indices = []

        # Revise each targeted page
        for idx in indices:
            if idx >= len(content_materials):
                continue

            material = content_materials[idx]
            original_content = material.get("content", "")

            # Build revision prompt
            system_prompt = (
                """You are a content revision expert. Revise content based on user feedback."""
            )

            user_prompt = f"""Original Content:
{original_content}

User Revision Instructions:
{request.instructions}

Please provide revised content that addresses the user's feedback. Return only the revised content."""

            try:
                response = await self.model.ainvoke(
                    [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=user_prompt),
                    ]
                )

                # Update material
                content_materials[idx] = {
                    **material,
                    "content": response.content,
                    "revised": True,
                    "revision_note": request.instructions,
                }

                logger.debug(f"[RevisionHandler] Revised content for page {idx}")

            except Exception as e:
                logger.error(f"[RevisionHandler] Error revising page {idx}: {e}")

        state["content_materials"] = content_materials
        return state

    async def _revise_style(
        self,
        state: PPTGenerationState,
        request: RevisionRequest,
    ) -> PPTGenerationState:
        """修订内容的风格/语气"""
        logger.info("[RevisionHandler] Revising style")

        # Similar to content revision, but focus on style changes
        # For now, delegate to content revision
        return await self._revise_content(state, request)

    async def _revise_structure(
        self,
        state: PPTGenerationState,
        request: RevisionRequest,
    ) -> PPTGenerationState:
        """修订 PPT 结构"""
        logger.info("[RevisionHandler] Revising structure")

        framework = state.get("ppt_framework", {})
        pages = framework.get("ppt_framework", [])

        # Parse revision instructions for structure changes
        # This would involve regenerating the framework
        # For now, mark as needing framework redesign

        state["needs_framework_revision"] = True
        state["framework_revision_instructions"] = request.instructions

        return state

    async def _revise_research(
        self,
        state: PPTGenerationState,
        request: RevisionRequest,
    ) -> PPTGenerationState:
        """修订研究结果"""
        logger.info("[RevisionHandler] Revising research")

        # Mark for additional research
        state["needs_additional_research"] = True
        state["research_revision_instructions"] = request.instructions

        return state

    def _parse_revision_request(self, request: Dict[str, Any]) -> RevisionRequest:
        """从字典解析修订请求"""
        revision_type = request.get("type", "content")
        target = request.get("target", "all")

        # Normalize type
        if revision_type not in ["content", "style", "structure", "research"]:
            revision_type = "content"

        # Normalize target
        if target not in ["page_index", "all", "section"]:
            target = "all"

        return RevisionRequest(
            type=revision_type,
            target=target,
            instructions=request.get("instructions", ""),
            page_indices=request.get("page_indices"),
            section_name=request.get("section_name"),
        )

    async def apply_incremental_revision(
        self,
        state: PPTGenerationState,
        page_index: int,
        new_content: str,
    ) -> PPTGenerationState:
        """
        对特定页面应用增量修订

        参数：
            state: 当前状态
            page_index: 要修订的页面索引
            new_content: 页面的新内容

        返回：
            更新后的状态
        """
        content_materials = state.get("content_materials", [])

        if page_index < len(content_materials):
            content_materials[page_index]["content"] = new_content
            content_materials[page_index]["revised"] = True

            logger.info(f"[RevisionHandler] Applied incremental revision to page {page_index}")

        state["content_materials"] = content_materials
        return state

    def get_revision_summary(self, state: PPTGenerationState) -> Dict[str, Any]:
        """
        获取修订历史的摘要

        参数：
            state: 当前状态

        返回：
            修订摘要
        """
        history = state.get("revision_history", [])

        return {
            "total_revisions": len(history),
            "latest_revision": history[-1] if history else None,
            "revision_types": [r["type"] for r in history],
        }
