"""统一异常处理模块

定义系统中所有异常类型和错误码
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(Enum):
    """错误码定义

    格式: E + 三位数字
    - 001-099: 系统级错误
    - 100-199: Agent相关错误
    - 200-299: 内容生成错误
    - 300-399: PPT构建错误
    """
    # 系统级错误
    UNKNOWN_ERROR = "E001"
    CONFIGURATION_ERROR = "E002"
    TIMEOUT_ERROR = "E003"

    # Agent相关
    AGENT_NOT_FOUND = "E100"
    AGENT_INIT_FAILED = "E101"
    AGENT_TIMEOUT = "E102"
    MESSAGE_SEND_FAILED = "E103"

    # 内容生成
    CONTENT_GENERATION_FAILED = "E200"
    PROMPT_TEMPLATE_MISSING = "E201"
    LLM_API_ERROR = "E202"
    CONTENT_VALIDATION_FAILED = "E203"

    # PPT构建
    PPT_BUILD_FAILED = "E300"
    TEMPLATE_PARSE_ERROR = "E301"
    RESOURCE_LOAD_FAILED = "E302"
    OUTPUT_SAVE_FAILED = "E303"


class PPTSystemException(Exception):
    """PPT系统基础异常类"""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{code.value}] {message}")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.code.value,
            "message": self.message,
            "details": self.details
        }


class AgentException(PPTSystemException):
    """Agent相关异常"""
    pass


class ContentException(PPTSystemException):
    """内容生成异常"""
    pass


class BuildException(PPTSystemException):
    """PPT构建异常"""
    pass


def handle_exception(exc: Exception) -> Dict[str, Any]:
    """统一异常处理函数

    Args:
        exc: 捕获的异常

    Returns:
        错误响应字典
    """
    if isinstance(exc, PPTSystemException):
        return exc.to_dict()
    else:
        return {
            "error_code": ErrorCode.UNKNOWN_ERROR.value,
            "message": str(exc),
            "details": {}
        }
