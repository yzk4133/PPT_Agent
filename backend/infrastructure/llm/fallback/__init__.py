"""
降级策略框架

提供多级降级链，支持：
- JSON 解析降级（完整解析 → 正则提取 → 默认结构）
- LLM 调用降级（主模型 → 备用模型 → 缓存结果）
- 并行搜索降级（全部成功 → 部分成功 → 默认数据）
- 自定义降级链
"""

import json
import re
import logging
from typing import Any, Callable, List, Optional, Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class FallbackLevel(str, Enum):
    """降级级别"""

    PRIMARY = "primary"  # 主策略
    SECONDARY = "secondary"  # 次级策略
    TERTIARY = "tertiary"  # 三级策略
    DEFAULT = "default"  # 默认策略（最后保底）

@dataclass
class FallbackResult:
    """降级结果"""

    success: bool
    data: Any
    level: FallbackLevel
    error: Optional[str] = None
    metadata: Optional[Dict] = None

class FallbackChain:
    """
    降级链

    按顺序尝试多个策略，直到成功或所有策略都失败
    """

    def __init__(self, name: str):
        """
        Args:
            name: 降级链名称（用于日志）
        """
        self.name = name
        self._strategies: List[tuple[FallbackLevel, Callable, str]] = []

    def add_strategy(
        self, level: FallbackLevel, strategy_func: Callable, description: str = ""
    ):
        """
        添加降级策略

        Args:
            level: 降级级别
            strategy_func: 策略函数，返回 (success: bool, data: Any)
            description: 策略描述
        """
        self._strategies.append((level, strategy_func, description))
        logger.debug(f"Added {level} strategy to {self.name}: {description}")

    def execute(self, *args, **kwargs) -> FallbackResult:
        """
        执行降级链

        Args:
            *args, **kwargs: 传递给策略函数的参数

        Returns:
            FallbackResult
        """
        if not self._strategies:
            return FallbackResult(
                success=False,
                data=None,
                level=FallbackLevel.DEFAULT,
                error="No strategies configured",
            )

        for level, strategy_func, description in self._strategies:
            try:
                logger.debug(f"{self.name}: Trying {level} strategy - {description}")
                success, data = strategy_func(*args, **kwargs)

                if success:
                    logger.info(f"{self.name}: {level} strategy succeeded")
                    return FallbackResult(
                        success=True,
                        data=data,
                        level=level,
                        metadata={"description": description},
                    )
                else:
                    logger.warning(f"{self.name}: {level} strategy returned failure")

            except Exception as e:
                logger.warning(f"{self.name}: {level} strategy raised exception: {e}")
                continue

        # 所有策略都失败
        logger.error(f"{self.name}: All strategies failed")
        return FallbackResult(
            success=False,
            data=None,
            level=FallbackLevel.DEFAULT,
            error="All fallback strategies failed",
        )

# ==================== JSON 解析降级 ====================

class JSONFallbackParser:
    """JSON 解析降级器"""

    @staticmethod
    def parse_with_fallback(
        json_string: str, default_structure: Optional[Dict] = None
    ) -> FallbackResult:
        """
        带降级的 JSON 解析

        Args:
            json_string: JSON 字符串
            default_structure: 默认结构（最后保底）

        Returns:
            FallbackResult
        """
        chain = FallbackChain("JSON Parser")

        # 策略 1：标准 JSON 解析
        def standard_parse():
            try:
                data = json.loads(json_string)
                return True, data
            except:
                return False, None

        chain.add_strategy(
            FallbackLevel.PRIMARY, standard_parse, "Standard JSON parsing"
        )

        # 策略 2：修复常见错误后解析
        def parse_with_fixes():
            try:
                # 修复常见问题
                fixed = json_string.strip()
                fixed = fixed.replace("'", '"')  # 单引号 → 双引号
                fixed = re.sub(r",\s*}", "}", fixed)  # 移除尾随逗号
                fixed = re.sub(r",\s*]", "]", fixed)
                data = json.loads(fixed)
                return True, data
            except:
                return False, None

        chain.add_strategy(
            FallbackLevel.SECONDARY, parse_with_fixes, "Parse with common fixes"
        )

        # 策略 3：正则提取关键字段
        def regex_extraction():
            try:
                # 假设是 topics 结构
                topics = []
                title_pattern = r'"title"\s*:\s*"([^"]+)"'
                id_pattern = r'"id"\s*:\s*(\d+)'

                titles = re.findall(title_pattern, json_string)
                ids = re.findall(id_pattern, json_string)

                if not titles:
                    return False, None

                for i, title in enumerate(titles):
                    topic_id = int(ids[i]) if i < len(ids) else i + 1
                    topics.append(
                        {
                            "id": topic_id,
                            "title": title,
                            "keywords": [],  # 无法提取 keywords，使用空列表
                        }
                    )

                return True, {"topics": topics}
            except:
                return False, None

        chain.add_strategy(
            FallbackLevel.TERTIARY, regex_extraction, "Regex extraction of key fields"
        )

        # 策略 4：使用默认结构
        def use_default():
            if default_structure:
                return True, default_structure
            else:
                # 最小可用结构
                return True, {
                    "topics": [{"id": 1, "title": "General Topic", "keywords": []}]
                }

        chain.add_strategy(FallbackLevel.DEFAULT, use_default, "Use default structure")

        return chain.execute()

# ==================== 部分成功处理 ====================

class PartialSuccessHandler:
    """部分成功处理器"""

    @staticmethod
    def handle_parallel_results(
        results: List[tuple[bool, Any]], min_success_rate: float = 0.5
    ) -> FallbackResult:
        """
        处理并行任务的部分成功

        Args:
            results: [(success, data), ...] 列表
            min_success_rate: 最低成功率阈值（0.0-1.0）

        Returns:
            FallbackResult
        """
        if not results:
            return FallbackResult(
                success=False,
                data=[],
                level=FallbackLevel.DEFAULT,
                error="No results provided",
            )

        success_results = [data for success, data in results if success]
        failed_count = len(results) - len(success_results)
        success_rate = len(success_results) / len(results)

        # 判断级别
        if success_rate >= 1.0:
            level = FallbackLevel.PRIMARY
        elif success_rate >= 0.75:
            level = FallbackLevel.SECONDARY
        elif success_rate >= min_success_rate:
            level = FallbackLevel.TERTIARY
        else:
            level = FallbackLevel.DEFAULT

        logger.info(
            f"Partial success: {len(success_results)}/{len(results)} succeeded "
            f"(rate: {success_rate:.1%}, level: {level})"
        )

        return FallbackResult(
            success=success_rate >= min_success_rate,
            data=success_results,
            level=level,
            metadata={
                "total": len(results),
                "succeeded": len(success_results),
                "failed": failed_count,
                "success_rate": success_rate,
            },
        )

# ==================== LLM 调用降级 ====================

class LLMCallFallback:
    """LLM 调用降级器"""

    def __init__(self, cache: Optional[Dict] = None):
        """
        Args:
            cache: 结果缓存字典
        """
        self.cache = cache or {}

    def call_with_fallback(
        self,
        primary_model_func: Callable,
        fallback_model_func: Optional[Callable] = None,
        cache_key: Optional[str] = None,
        *args,
        **kwargs,
    ) -> FallbackResult:
        """
        带降级的 LLM 调用

        Args:
            primary_model_func: 主模型调用函数
            fallback_model_func: 备用模型调用函数
            cache_key: 缓存键（用于查找历史结果）
            *args, **kwargs: 传递给模型函数的参数

        Returns:
            FallbackResult
        """
        chain = FallbackChain("LLM Call")

        # 策略 1：主模型
        def call_primary():
            try:
                result = primary_model_func(*args, **kwargs)
                # 缓存结果
                if cache_key:
                    self.cache[cache_key] = result
                return True, result
            except Exception as e:
                logger.warning(f"Primary model failed: {e}")
                return False, None

        chain.add_strategy(FallbackLevel.PRIMARY, call_primary, "Primary model")

        # 策略 2：备用模型
        if fallback_model_func:

            def call_fallback():
                try:
                    result = fallback_model_func(*args, **kwargs)
                    return True, result
                except Exception as e:
                    logger.warning(f"Fallback model failed: {e}")
                    return False, None

            chain.add_strategy(FallbackLevel.SECONDARY, call_fallback, "Fallback model")

        # 策略 3：使用缓存
        if cache_key:

            def use_cache():
                if cache_key in self.cache:
                    logger.info(f"Using cached result for {cache_key}")
                    return True, self.cache[cache_key]
                return False, None

            chain.add_strategy(FallbackLevel.TERTIARY, use_cache, "Cached result")

        # 策略 4：默认响应
        def default_response():
            return True, {"error": "All models unavailable", "content": ""}

        chain.add_strategy(
            FallbackLevel.DEFAULT, default_response, "Default error response"
        )

        return chain.execute()

# ==================== 预定义降级配置 ====================

def create_default_json_parser() -> FallbackChain:
    """创建默认的 JSON 解析降级链"""
    return JSONFallbackParser()

def create_default_parallel_handler(
    min_success_rate: float = 0.5,
) -> PartialSuccessHandler:
    """创建默认的并行任务处理器"""
    return PartialSuccessHandler()

def create_default_llm_fallback(cache: Optional[Dict] = None) -> LLMCallFallback:
    """创建默认的 LLM 调用降级器"""
    return LLMCallFallback(cache=cache)

if __name__ == "__main__":
    # 测试降级策略
    logging.basicConfig(level=logging.INFO)

    # 测试 1：JSON 解析降级
    print("\n=== Test 1: JSON Parsing Fallback ===")

    # 正常 JSON
    result1 = JSONFallbackParser.parse_with_fallback(
        '{"topics": [{"id": 1, "title": "Test"}]}'
    )
    print(f"Normal JSON: success={result1.success}, level={result1.level}")

    # 有错误的 JSON（单引号）
    result2 = JSONFallbackParser.parse_with_fallback(
        "{'topics': [{'id': 1, 'title': 'Test'}]}"
    )
    print(f"Fixed JSON: success={result2.success}, level={result2.level}")

    # 严重损坏的 JSON（只能正则提取）
    result3 = JSONFallbackParser.parse_with_fallback('"title": "Topic1" ... "id": 1')
    print(
        f"Regex extraction: success={result3.success}, level={result3.level}, data={result3.data}"
    )

    # 测试 2：部分成功处理
    print("\n=== Test 2: Partial Success Handling ===")

    parallel_results = [
        (True, "Result 1"),
        (True, "Result 2"),
        (False, None),
        (True, "Result 3"),
        (False, None),
    ]

    result4 = PartialSuccessHandler.handle_parallel_results(
        parallel_results, min_success_rate=0.5
    )
    print(f"Partial success: success={result4.success}, level={result4.level}")
    print(f"Metadata: {result4.metadata}")
    print(f"Successful data: {result4.data}")

# ==================== Exports ====================

__all__ = [
    "FallbackLevel",
    "FallbackResult",
    "FallbackChain",
    "JSONFallbackParser",
    "PartialSuccessHandler",
    "LLMCallFallback",
    "create_default_json_parser",
    "create_default_parallel_handler",
    "create_default_llm_fallback",
]
