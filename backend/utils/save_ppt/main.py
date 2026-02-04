"""
PPT生成入口函数
"""

import json
import logging
from typing import Any, Optional

from .generator import PresentationGenerator

logger = logging.getLogger(__name__)

def start_generate_presentation(json_input: Any) -> Optional[str]:
    """PPT生成的入口函数"""
    print("\n" + "="*100)
    print("PPT生成器启动")
    print("="*100)

    try:
        json_data = json.loads(json_input) if isinstance(json_input, str) else json_input
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"JSON解析失败: {e}")
        return None

    generator = PresentationGenerator()
    output_path = generator.generate_presentation(json_data)

    return output_path
