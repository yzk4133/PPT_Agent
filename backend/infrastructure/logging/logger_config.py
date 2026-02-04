"""
统一日志系统配置

提供结构化、可配置的日志系统，支持：
- JSON 和文本格式输出
- 控制台和文件输出
- 日志轮转（按大小和时间）
- 请求 ID 追踪
- 敏感信息脱敏
"""

import logging
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Set
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from contextvars import ContextVar

# 请求 ID 上下文变量
REQUEST_ID_CTX: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class SensitiveDataFilter(logging.Filter):
    """
    敏感信息过滤器

    自动脱敏以下敏感信息：
    - API Keys
    - JWT Tokens
    - Passwords
    - Email addresses (可选)
    - Phone numbers (可选)
    """

    # 敏感信息模式
    PATTERNS = {
        "api_key": [
            r'(?:api[_-]?key|apikey|api_key)["\']?\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
            r'Bearer\s+([a-zA-Z0-9_\-\.]{20,})',
        ],
        "jwt": [
            r'eyJ[a-zA-Z0-9_\-]+\.(?:eyJ[a-zA-Z0-9_\-]+\.)?[a-zA-Z0-9_\-]+',
        ],
        "password": [
            r'["\']?(?:password|passwd|pwd)["\']?\s*[:=]\s*["\']([^"\']+)["\']',
        ],
        "email": [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        ],
        "phone": [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            r'\b\+?1?[-.]?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b',
        ],
    }

    def __init__(self, mask_emails: bool = True, mask_phones: bool = True):
        """
        初始化敏感信息过滤器

        Args:
            mask_emails: 是否脱敏邮箱
            mask_phones: 是否脱敏电话号码
        """
        super().__init__()
        self.mask_emails = mask_emails
        self.mask_phones = mask_phones
        self._compile_patterns()

    def _compile_patterns(self):
        """编译正则表达式模式"""
        self.compiled_patterns = []

        for category, patterns in self.PATTERNS.items():
            if category == "email" and not self.mask_emails:
                continue
            if category == "phone" and not self.mask_phones:
                continue

            for pattern in patterns:
                try:
                    self.compiled_patterns.append(re.compile(pattern))
                except re.error:
                    pass

    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤并脱敏日志记录

        Args:
            record: 日志记录

        Returns:
            Always True (允许所有记录通过，但修改内容)
        """
        if hasattr(record, "msg"):
            record.msg = self._mask_sensitive(str(record.msg))

        if record.args:
            record.args = tuple(
                self._mask_sensitive(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )

        return True

    def _mask_sensitive(self, text: str) -> str:
        """脱敏敏感信息"""
        for pattern in self.compiled_patterns:
            text = pattern.sub(lambda m: self._mask_match(m), text)
        return text

    def _mask_match(self, match) -> str:
        """脱敏匹配到的内容"""
        matched = match.group(0)
        if len(matched) <= 8:
            return "***"
        # 保留前3位和后4位，中间用***代替
        return f"{matched[:3]}***{matched[-4:]}"


class JSONFormatter(logging.Formatter):
    """
    JSON 格式化器

    输出结构化的 JSON 日志，便于日志聚合和分析
    """

    def __init__(
        self,
        service_name: str = "multiagent-ppt",
        environment: str = "development",
        include_extra: bool = True,
    ):
        """
        初始化 JSON 格式化器

        Args:
            service_name: 服务名称
            environment: 环境名称
            include_extra: 是否包含额外的上下文信息
        """
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录为 JSON

        Args:
            record: 日志记录

        Returns:
            JSON 字符串
        """
        # 基础日志信息
        log_data = {
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "@version": "1",
            "service": self.service_name,
            "environment": self.environment,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # 添加请求 ID（如果存在）
        request_id = REQUEST_ID_CTX.get()
        if request_id:
            log_data["request_id"] = request_id

        # 添加额外字段
        if self.include_extra:
            for key, value in record.__dict__.items():
                if key not in {
                    "name", "msg", "args", "levelname", "levelno", "pathname",
                    "filename", "module", "lineno", "funcName", "created", "msecs",
                    "relativeCreated", "thread", "threadName", "processName",
                    "process", "exc_info", "exc_text", "stack_info",
                }:
                    if not key.startswith("_"):
                        log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """
    文本格式化器

    输出易读的文本格式日志
    """

    # 颜色代码（ANSI）
    COLORS = {
        "DEBUG": "\033[36m",      # 青色
        "INFO": "\033[32m",       # 绿色
        "WARNING": "\033[33m",    # 黄色
        "ERROR": "\033[31m",      # 红色
        "CRITICAL": "\033[35m",   # 紫色
    }
    RESET = "\033[0m"

    def __init__(
        self,
        use_colors: bool = True,
        include_request_id: bool = True,
    ):
        """
        初始化文本格式化器

        Args:
            use_colors: 是否使用颜色（仅控制台）
            include_request_id: 是否包含请求 ID
        """
        self.use_colors = use_colors and sys.stderr.isatty()  # 仅在 TTY 终端使用颜色
        self.include_request_id = include_request_id

        # 构建格式字符串
        base_format = "%(asctime)s [%(levelname)8s] %(name)s: %(message)s"
        if include_request_id:
            base_format = "%(asctime)s [%(levelname)8s] [%(request_id)s] %(name)s: %(message)s"

        super().__init__(base_format, datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 添加请求 ID 到记录
        if self.include_request_id:
            request_id = REQUEST_ID_CTX.get()
            record.request_id = request_id or "N/A"

        # 应用颜色
        if self.use_colors:
            levelname = record.levelname
            color = self.COLORS.get(levelname, "")
            record.levelname = f"{color}{levelname}{self.RESET}"

        result = super().format(record)

        # 恢复原始 levelname（避免影响其他处理器）
        if self.use_colors:
            record.levelname = levelname

        return result


def setup_logger(
    name: str,
    level: str = "INFO",
    log_format: str = "json",  # "json" or "text"
    output: str = "stdout",     # "stdout", "file", "both"
    log_file: Optional[str] = None,
    service_name: str = "multiagent-ppt",
    environment: str = "development",
    rotation_type: str = "size",  # "size" or "time"
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    mask_sensitive: bool = True,
    mask_emails: bool = True,
    mask_phones: bool = True,
) -> logging.Logger:
    """
    配置统一的日志系统

    Args:
        name: Logger 名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: 日志格式 ("json" 或 "text")
        output: 输出位置 ("stdout", "file", "both")
        log_file: 日志文件路径（output 为 file 或 both 时必需）
        service_name: 服务名称
        environment: 环境名称
        rotation_type: 日志轮转类型 ("size" 或 "time")
        max_bytes: 单个日志文件最大字节数（size 轮转时）
        backup_count: 保留的备份文件数量
        mask_sensitive: 是否脱敏敏感信息
        mask_emails: 是否脱敏邮箱
        mask_phones: 是否脱敏电话号码

    Returns:
        配置好的 Logger 实例

    Example:
        >>> logger = setup_logger("my_app", level="DEBUG", log_format="json")
        >>> logger.info("Application started")
    """
    # 获取或创建 logger
    logger = logging.getLogger(name)

    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger

    # 设置日志级别
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 移除默认处理器
    logger.propagate = False

    # 创建格式化器
    if log_format == "json":
        formatter = JSONFormatter(
            service_name=service_name,
            environment=environment,
        )
    else:
        formatter = TextFormatter(
            use_colors=True,
            include_request_id=True,
        )

    # 创建处理器
    handlers = []

    # 控制台处理器
    if output in ("stdout", "both"):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    # 文件处理器
    if output in ("file", "both"):
        if not log_file:
            # 默认日志文件路径
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f"{name}.log"

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        if rotation_type == "size":
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
        else:  # time
            file_handler = TimedRotatingFileHandler(
                log_path,
                when="midnight",
                interval=1,
                backupCount=backup_count,
                encoding="utf-8",
            )

        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # 添加敏感信息过滤器
    if mask_sensitive:
        sensitive_filter = SensitiveDataFilter(
            mask_emails=mask_emails,
            mask_phones=mask_phones,
        )
        for handler in handlers:
            handler.addFilter(sensitive_filter)

    # 添加处理器到 logger
    for handler in handlers:
        logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取已配置的 Logger

    如果 Logger 未配置，使用默认配置

    Args:
        name: Logger 名称

    Returns:
        Logger 实例
    """
    logger = logging.getLogger(name)

    # 如果未配置，使用默认设置
    if not logger.handlers:
        logger = setup_logger(
            name=name,
            level="INFO",
            log_format="text",
            output="stdout",
        )

    return logger


def set_request_id(request_id: Optional[str]):
    """
    设置当前请求 ID

    Args:
        request_id: 请求 ID（None 表示清除）

    Example:
        >>> set_request_id("req-12345")
        >>> logger.info("Processing request")
        >>> set_request_id(None)
    """
    REQUEST_ID_CTX.set(request_id)


def get_request_id() -> Optional[str]:
    """
    获取当前请求 ID

    Returns:
        当前请求 ID 或 None
    """
    return REQUEST_ID_CTX.get()


class LoggerContext:
    """
    Logger 上下文管理器

    用于临时设置请求 ID

    Example:
        >>> with LoggerContext("req-12345"):
        ...     logger.info("This log will have request_id")
    """

    def __init__(self, request_id: Optional[str]):
        self.request_id = request_id
        self.previous_id = None

    def __enter__(self):
        self.previous_id = REQUEST_ID_CTX.get()
        REQUEST_ID_CTX.set(self.request_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        REQUEST_ID_CTX.set(self.previous_id)
        return False


# 便捷函数
def log_function_call(logger: Optional[logging.Logger] = None):
    """
    日志函数调用装饰器

    Args:
        logger: Logger 实例（None 则使用 __name__ 创建）

    Example:
        >>> @log_function_call()
        ... def my_function(x, y):
        ...     return x + y
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)

            logger.debug(
                f"Calling {func.__name__} with args={args}, kwargs={kwargs}"
            )
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} returned successfully")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
                raise

        return wrapper
    return decorator


# 预配置的日志器
def get_app_logger() -> logging.Logger:
    """获取应用主日志器"""
    return get_logger("app")


def get_api_logger() -> logging.Logger:
    """获取 API 日志器"""
    return get_logger("api")


def get_agent_logger() -> logging.Logger:
    """获取 Agent 日志器"""
    return get_logger("agent")


def get_infrastructure_logger() -> logging.Logger:
    """获取基础设施日志器"""
    return get_logger("infrastructure")


if __name__ == "__main__":
    # 测试日志系统
    logger = setup_logger(
        name="test",
        level="DEBUG",
        log_format="text",
        output="both",
        log_file="logs/test.log",
    )

    # 测试敏感信息脱敏
    logger.info("API Key: sk-1234567890abcdef")
    logger.info("Password: mypassword123")
    logger.info("Email: user@example.com")
    logger.info("JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test")

    # 测试请求 ID
    with LoggerContext("req-test-123"):
        logger.info("This log has a request ID")

    # 测试异常
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("Division by zero occurred")

    print("Logs generated. Check logs/test.log")
