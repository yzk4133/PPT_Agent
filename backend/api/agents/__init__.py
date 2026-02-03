"""
API 层 - Agent 服务入口

职责：
- API 服务器配置（uvicorn、端口）
- 路由配置（健康检查、Agent Card）
- 中间件配置（CORS）
- Agent Card 元数据定义
"""

from .outline_api import main as outline_main
from .presentation_api import main as presentation_main

__all__ = ["outline_main", "presentation_main"]
