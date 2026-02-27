"""
内容改进节点 - LangGraph 集成

该模块为 LangGraph 工作流提供内容改进节点。
"""

import logging
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from infrastructure.config import get_llm_config

from ....models.state import PPTGenerationState

logger = logging.getLogger(__name__)


async def refine_content(
    state: PPTGenerationState,
    model: Optional[ChatOpenAI] = None,
) -> PPTGenerationState:
    """
    LangGraph 节点：基于质量评估改进内容

    使用 LLM 改进未通过质量检查的内容。

    Args:
        state: 包含质量评估的当前状态
        model: 可选的 LLM 模型（如果为 None 则创建默认模型）

    Returns:
        包含改进后内容的更新后状态
    """
    logger.info("[RefinementNode] Starting content refinement")

    # Get quality assessment
    assessment = state.get("quality_assessment", {})
    issues = assessment.get("issues", [])

    if not issues:
        logger.warning("[RefinementNode] No issues found, skipping refinement")
        return state

    # Get content materials
    content_materials = state.get("content_materials", [])

    if not content_materials:
        logger.warning("[RefinementNode] No content materials to refine")
        return state

    # Create LLM if needed
    if model is None:
        llm_config = get_llm_config(temperature=0.7)

        model = ChatOpenAI(
            **llm_config.to_langchain_config()
        )

    # Track refinement count
    refinement_count = state.get("refinement_count", 0)
    state["refinement_count"] = refinement_count + 1

    # Refine each material
    refined_materials = []
    for idx, material in enumerate(content_materials):
        content = material.get("content", "")

        # Check if this page has issues
        page_issues = [i for i in issues if f"[Page {idx}]" in i]

        if not page_issues:
            # No issues, keep as-is
            refined_materials.append(material)
            continue

        # Build refinement prompt
        system_prompt = """You are a content refinement expert. Your task is to improve content based on quality feedback.

Focus on:
1. Completeness - Ensure all required information is present
2. Clarity - Make content clear and easy to understand
3. Length - Ensure appropriate length (not too short, not too long)

Provide improved content that addresses the specific issues identified."""

        issues_text = "\n".join([f"- {issue}" for issue in page_issues])

        user_prompt = f"""Original Content:
{content}

Quality Issues:
{issues_text}

Please provide refined content that addresses these issues. Return only the refined content, no explanations."""

        try:
            # Call LLM
            response = await model.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ])

            refined_content = response.content

            # Update material
            refined_material = material.copy()
            refined_material["content"] = refined_content
            refined_material["refined"] = True
            refined_material["refinement_iteration"] = refinement_count + 1
            refined_material["issues_addressed"] = page_issues

            refined_materials.append(refined_material)

            logger.debug(
                f"[RefinementNode] Refined page {idx} "
                f"(iteration {refinement_count + 1})"
            )

        except Exception as e:
            logger.error(
                f"[RefinementNode] Error refining page {idx}: {e}",
                exc_info=True,
            )
            # Keep original on error
            refined_materials.append(material)

    # Update state
    state["content_materials"] = refined_materials
    state["last_refinement_count"] = len([m for m in refined_materials if m.get("refined")])

    logger.info(
        f"[RefinementNode] Refinement complete: "
        f"{state['last_refinement_count']} pages refined "
        f"(iteration {refinement_count + 1})"
    )

    return state


async def refine_framework(
    state: PPTGenerationState,
    model: Optional[ChatOpenAI] = None,
) -> PPTGenerationState:
    """
    LangGraph 节点：改进 PPT 框架结构

    Args:
        state: 当前状态
        model: 可选的 LLM 模型

    Returns:
        包含改进后框架的更新后状态
    """
    logger.info("[RefinementNode] Starting framework refinement")

    # Get assessment
    assessment = state.get("framework_quality_assessment", {})
    missing_fields = assessment.get("missing_fields", 0)

    if missing_fields == 0:
        logger.info("[RefinementNode] No framework issues, skipping refinement")
        return state

    # Get framework
    framework = state.get("ppt_framework", {})
    pages = framework.get("ppt_framework", [])

    if not pages:
        return state

    # Create LLM if needed
    if model is None:
        llm_config = get_llm_config(temperature=0.7)

        model = ChatOpenAI(
            **llm_config.to_langchain_config()
        )

    # Refine pages with missing fields
    refined_pages = []
    for page in pages:
        required_fields = ["page_type", "title", "content_description"]
        missing = [f for f in required_fields if f not in page or not page[f]]

        if not missing:
            refined_pages.append(page)
            continue

        # Need to generate missing fields
        system_prompt = """You are a PPT framework designer. Generate missing fields for PPT page definitions."""

        page_info = f"Page: {page.get('title', 'Untitled')}"
        missing_text = ", ".join(missing)
        user_prompt = f"""{page_info}

Missing fields: {missing_text}

Please generate appropriate values for these fields. Return as JSON with field names as keys."""

        try:
            response = await model.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ])

            # Parse response and update page
            import json

            try:
                generated_data = json.loads(response.content)
                refined_page = {**page, **generated_data}
                refined_page["refined"] = True
            except json.JSONDecodeError:
                # If not JSON, use text for content_description
                refined_page = page.copy()
                if "content_description" in missing:
                    refined_page["content_description"] = response.content
                refined_page["refined"] = True

            refined_pages.append(refined_page)

        except Exception as e:
            logger.error(f"[RefinementNode] Error refining framework page: {e}")
            refined_pages.append(page)

    # Update framework
    framework["ppt_framework"] = refined_pages
    framework["refined"] = True

    state["ppt_framework"] = framework

    logger.info(f"[RefinementNode] Framework refinement complete")

    return state


async def refine_with_llm(
    content: str,
    issues: List[str],
    context: Optional[Dict[str, Any]] = None,
    model: Optional[ChatOpenAI] = None,
) -> str:
    """
    通用的基于 LLM 的改进函数

    Args:
        content: 要改进的内容
        issues: 要解决的问题列表
        context: 可选的上下文信息
        model: 可选的 LLM 模型

    Returns:
        改进后的内容
    """
    if model is None:
        llm_config = get_llm_config(temperature=0.7)

        model = ChatOpenAI(
            **llm_config.to_langchain_config()
        )

    system_prompt = """You are a content refinement expert. Improve content based on quality feedback."""

    issues_text = "\n".join([f"- {issue}" for issue in issues])
    context_text = f"\nContext: {context}" if context else ""

    user_prompt = f"""Original Content:
{content}
{context_text}

Quality Issues:
{issues_text}

Provide refined content that addresses these issues."""

    try:
        response = await model.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        return response.content
    except Exception as e:
        logger.error(f"[refine_with_llm] Error: {e}")
        return content  # Return original on error
