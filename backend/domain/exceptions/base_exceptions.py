"""
Base Application Exceptions

定义应用级异常的基础类
"""

from typing import Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)

class BaseApplicationError(Exception):
    """
    应用异常基类

    所有应用级异常都应该继承此类。
    提供统一的错误信息格式和日志记录。
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        inner_exception: Optional[Exception] = None
    ):
        """
        初始化应用异常

        Args:
            message: 错误消息
            code: 错误代码（可选）
            details: 额外的错误详情（可选）
            inner_exception: 内部异常（可选）
        """
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.inner_exception = inner_exception

        # 记录异常日志
        self._log_exception()

        super().__init__(self.message)

    def _log_exception(self):
        """记录异常到日志"""
        log_level = self._get_log_level()

        if log_level == logging.ERROR:
            logger.error(
                f"[{self.code}] {self.message}",
                extra={"details": self.details, "exception_type": self.__class__.__name__},
                exc_info=self.inner_exception is not None
            )
        elif log_level == logging.WARNING:
            logger.warning(
                f"[{self.code}] {self.message}",
                extra={"details": self.details}
            )

    def _get_log_level(self) -> int:
        """获取日志级别（子类可覆盖）"""
        return logging.ERROR

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于API响应）"""
        result = {
            "error_code": self.code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - {self.details}"
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code}, message={self.message})"

class RecoverableError(BaseApplicationError):
    """
    可恢复异常

    表示一个可以重试或恢复的错误，不会导致系统崩溃。
    """

    def _get_log_level(self) -> int:
        return logging.WARNING

class CriticalError(BaseApplicationError):
    """
    严重错误

    表示一个严重的错误，需要立即处理。
    """

    def _get_log_level(self) -> int:
        return logging.CRITICAL
