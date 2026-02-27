"""
LangChain 多Agent PPT 生成集成测试

本测试脚本验证基于 LangChain 的新系统的端到端功能。
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# 将父目录添加到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agents.coordinator.master_graph import create_master_graph
from agents.models.state import PPTGenerationState

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResult:
    """测试结果跟踪器"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, test_name: str):
        self.passed += 1
        logger.info(f"✓ {test_name} 通过")

    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append((test_name, error))
        logger.error(f"✗ {test_name} 失败: {error}")

    def summary(self):
        total = self.passed + self.failed
        logger.info(f"\n{'='*60}")
        logger.info(f"测试摘要: {self.passed}/{total} 通过")
        if self.failed > 0:
            logger.error(f"失败的测试:")
            for test_name, error in self.errors:
                logger.error(f"  - {test_name}: {error}")
        logger.info(f"{'='*60}\n")


def assert_equal(actual, expected, test_name: str, results: TestResult):
    """相等断言辅助函数"""
    if actual == expected:
        results.add_pass(test_name)
    else:
        results.add_fail(test_name, f"期望 {expected}，实际 {actual}")


def assert_true(condition, test_name: str, results: TestResult):
    """真值断言辅助函数"""
    if condition:
        results.add_pass(test_name)
    else:
        results.add_fail(test_name, "条件为 False")


def assert_not_none(value, test_name: str, results: TestResult):
    """非 None 断言辅助函数"""
    if value is not None:
        results.add_pass(test_name)
    else:
        results.add_fail(test_name, "值为 None")


async def test_requirement_parsing(results: TestResult):
    """测试 1: 需求解析"""
    logger.info("\n" + "="*60)
    logger.info("测试 1: 需求解析")
    logger.info("="*60)

    from agents.core.requirements.requirement_agent import create_requirement_parser

    agent = create_requirement_parser()

    test_input = "生成一份关于人工智能的PPT，15页，学术风格，需要研究资料"

    try:
        result = await agent.parse(test_input)

        assert_not_none(result, "解析结果不为 None", results)
        assert_equal(result.get("page_num"), 15, "正确的页数", results)
        assert_equal(result.get("need_research"), True, "检测到需要研究", results)
        assert_not_none(result.get("ppt_topic"), "主题已提取", results)

        logger.info(f"解析的主题: {result.get('ppt_topic')}")
        logger.info(f"语言: {result.get('language')}")
        logger.info(f"核心模块: {result.get('core_modules')}")

    except Exception as e:
        results.add_fail("需求解析", str(e))


async def test_framework_design(results: TestResult):
    """测试 2: 框架设计"""
    logger.info("\n" + "="*60)
    logger.info("测试 2: 框架设计")
    logger.info("="*60)

    from agents.core.planning.framework_agent import create_framework_designer

    agent = create_framework_designer()

    requirement = {
        "ppt_topic": "人工智能概述",
        "page_num": 10,
        "template_type": "business_template",
        "scene": "business_report",
        "core_modules": ["封面", "目录", "AI介绍", "应用场景", "未来展望", "总结"],
        "need_research": True,
        "language": "ZH-CN"
    }

    try:
        result = await agent.design(requirement)

        assert_not_none(result, "框架结果不为 None", results)
        assert_equal(result.get("total_page"), 10, "正确的页数", results)

        pages = result.get("ppt_framework", [])
        assert_true(len(pages) == 10, "正确的页面数量", results)
        assert_true(pages[0].get("page_type") == "cover", "第一页是封面", results)

        logger.info(f"已创建框架: {len(pages)} 页")
        logger.info(f"研究页面: {result.get('research_page_indices')}")
        logger.info(f"图表页面: {result.get('chart_page_indices')}")

    except Exception as e:
        results.add_fail("框架设计", str(e))


async def test_research_agent(results: TestResult):
    """测试 3: 研究智能体"""
    logger.info("\n" + "="*60)
    logger.info("测试 3: 研究智能体")
    logger.info("="*60)

    from agents.core.research.research_agent import create_research_agent

    agent = create_research_agent()

    test_page = {
        "page_no": 3,
        "title": "AI发展历史",
        "core_content": "介绍人工智能的发展历程",
        "is_need_research": True,
        "keywords": ["AI", "历史", "发展"],
        "page_type": "content"
    }

    try:
        result = await agent.research_page(test_page)

        assert_not_none(result, "研究结果不为 None", results)
        assert_equal(result.get("page_no"), 3, "正确的页码", results)
        assert_equal(result.get("status"), "completed", "状态为已完成", results)
        assert_not_none(result.get("research_content"), "研究内容已生成", results)

        logger.info(f"第 {result['page_no']} 页研究已完成")
        logger.info(f"内容长度: {len(result['research_content'])} 字符")

    except Exception as e:
        results.add_fail("研究智能体", str(e))


async def test_content_generation(results: TestResult):
    """测试 4: 内容生成"""
    logger.info("\n" + "="*60)
    logger.info("测试 4: 内容生成")
    logger.info("="*60)

    from agents.core.generation.content_agent import create_content_agent

    agent = create_content_agent()

    test_page = {
        "page_no": 3,
        "title": "AI应用场景",
        "page_type": "content",
        "core_content": "介绍AI在各个领域的应用",
        "is_need_chart": True,
        "is_need_image": False,
        "estimated_word_count": 200
    }

    test_research = [{
        "page_no": 3,
        "research_content": "AI在医疗、金融、教育等领域有广泛应用...",
        "status": "completed"
    }]

    try:
        result = await agent.generate_content_for_page(test_page, test_research)

        assert_not_none(result, "内容结果不为 None", results)
        assert_equal(result.get("page_no"), 3, "正确的页码", results)
        assert_not_none(result.get("content_text"), "内容文本已生成", results)
        assert_true(result.get("has_chart") == True, "图表标志正确", results)

        logger.info(f"第 {result['page_no']} 页内容已生成")
        logger.info(f"内容长度: {len(result['content_text'])} 字符")
        logger.info(f"有图表: {result.get('has_chart')}")
        logger.info(f"有配图: {result.get('has_image')}")

    except Exception as e:
        results.add_fail("内容生成", str(e))


async def test_template_rendering(results: TestResult):
    """测试 5: 模板渲染"""
    logger.info("\n" + "="*60)
    logger.info("测试 5: 模板渲染")
    logger.info("="*60)

    from agents.core.rendering.renderer_agent import create_renderer_agent

    agent = create_renderer_agent(output_dir="test_output")

    test_framework = {
        "total_page": 3,
        "ppt_framework": [
            {
                "page_no": 1,
                "title": "封面",
                "page_type": "cover",
                "core_content": "主题\\n副标题"
            },
            {
                "page_no": 2,
                "title": "目录",
                "page_type": "directory",
                "core_content": ""
            },
            {
                "page_no": 3,
                "title": "总结",
                "page_type": "summary",
                "core_content": ""
            }
        ]
    }

    test_content = [
        {
            "page_no": 1,
            "content_text": "封面内容",
            "has_chart": False,
            "has_image": True
        },
        {
            "page_no": 2,
            "content_text": "目录内容",
            "has_chart": False,
            "has_image": False
        },
        {
            "page_no": 3,
            "content_text": "总结内容",
            "has_chart": False,
            "has_image": False
        }
    ]

    test_requirement = {
        "ppt_topic": "测试主题",
        "page_num": 3,
        "template_type": "business_template"
    }

    try:
        result = await agent.render(test_framework, test_content, test_requirement, "test_001")

        assert_not_none(result, "渲染结果不为 None", results)
        assert_not_none(result.get("file_path"), "文件路径已生成", results)
        assert_not_none(result.get("preview_data"), "预览数据已生成", results)
        assert_equal(result.get("total_pages"), 3, "正确的页数", results)

        logger.info(f"文件已保存: {result['file_path']}")
        logger.info(f"总页数: {result['total_pages']}")
        logger.info(f"预览页数: {len(result['preview_data'].get('pages', []))}")

    except Exception as e:
        results.add_fail("模板渲染", str(e))


async def test_full_workflow(results: TestResult):
    """测试 6: 端到端完整工作流"""
    logger.info("\n" + "="*60)
    logger.info("测试 6: 端到端完整工作流")
    logger.info("="*60)

    graph = create_master_graph()

    test_input = "生成一份关于量子计算的PPT，5页，商务风格，不需要研究"

    try:
        start_time = datetime.now()

        result = await graph.generate(test_input)

        elapsed = (datetime.now() - start_time).total_seconds()

        assert_not_none(result, "工作流结果不为 None", results)
        assert_equal(result.get("current_stage"), "template_renderer", "到达最终阶段", results)
        assert_equal(result.get("progress"), 100, "100% 进度", results)
        assert_not_none(result.get("structured_requirements"), "需求已生成", results)
        assert_not_none(result.get("ppt_framework"), "框架已生成", results)
        assert_not_none(result.get("content_materials"), "内容素材已生成", results)
        assert_not_none(result.get("ppt_output"), "PPT 输出已生成", results)

        logger.info(f"工作流在 {elapsed:.2f} 秒内完成")
        logger.info(f"任务 ID: {result.get('task_id')}")
        logger.info(f"主题: {result.get('structured_requirements', {}).get('ppt_topic')}")
        logger.info(f"页数: {result.get('ppt_framework', {}).get('total_page')}")
        logger.info(f"输出: {result.get('ppt_output', {}).get('file_path')}")

        # 性能检查
        assert_true(elapsed < 200, f"性能: {elapsed:.2f}s < 200s", results)

    except Exception as e:
        results.add_fail("完整工作流", str(e))


async def test_page_pipeline(results: TestResult):
    """测试 7: 页面流水线并行执行"""
    logger.info("\n" + "="*60)
    logger.info("测试 7: 页面流水线并行执行")
    logger.info("="*60)

    from agents.coordinator.page_pipeline import create_page_pipeline

    pipeline = create_page_pipeline(max_concurrency=3)

    # 创建测试页面
    test_pages = [
        {"page_no": 1, "title": f"第 {i} 页"}
        for i in range(1, 6)
    ]

    # 模拟执行器
    async def mock_executor(page):
        await asyncio.sleep(0.5)  # 模拟工作
        return {"page_no": page["page_no"], "result": f"内容 for {page['title']}"}

    try:
        start_time = datetime.now()

        results_list = await pipeline.execute_pages(test_pages, mock_executor)

        elapsed = (datetime.now() - start_time).total_seconds()

        assert_equal(len(results_list), 5, "所有页面已处理", results)

        # 并发数=3，5个页面，每个0.5秒
        # 预期时间约1秒（2批）
        # 留一些余地
        assert_true(elapsed < 2.5, f"并行执行: {elapsed:.2f}s < 2.5s", results)

        logger.info(f"在 {elapsed:.2f} 秒内处理了 {len(results_list)} 页")
        logger.info(f"并行效率: {(5 * 0.5) / elapsed:.2f}x")

    except Exception as e:
        results.add_fail("页面流水线", str(e))


async def run_all_tests():
    """运行所有集成测试"""
    logger.info("\n" + "="*60)
    logger.info("LANGCHAIN 多Agent 集成测试")
    logger.info("="*60)

    results = TestResult()

    # 运行测试
    await test_requirement_parsing(results)
    await test_framework_design(results)
    await test_research_agent(results)
    await test_content_generation(results)
    await test_template_rendering(results)
    await test_page_pipeline(results)
    await test_full_workflow(results)

    # 打印摘要
    results.summary()

    return results.failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
