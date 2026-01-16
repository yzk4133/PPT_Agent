"""统一日志配置模块

提供结构化的日志记录功能
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""

    # ANSI颜色码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
    }
    RESET = '\033[0m'

    def format(self, record):
        # 添加颜色
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    colored: bool = True
) -> logging.Logger:
    """配置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径（可选）
        level: 日志级别
        colored: 是否使用彩色输出

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 清除已有的处理器
    logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # 格式化器
    fmt = '%(asctime)s | %(name)-12s | %(levelname)-8s | %(message)s'
    if colored:
        formatter = ColoredFormatter(fmt, datefmt='%Y-%m-%d %H:%M:%S')
    else:
        formatter = logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S')

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（如果指定）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(file_handler)

    return logger


# 预配置的日志记录器
def get_logger(name: str) -> logging.Logger:
    """获取预配置的日志记录器"""
    return setup_logger(name, log_file=f"logs/{name}.log")
