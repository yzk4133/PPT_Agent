"""
工具系统异常定义

定义工具系统相关的异常类型。
"""


class ToolException(Exception):
    """工具系统基础异常"""

    pass


class ToolRegistrationError(ToolException):
    """工具注册错误"""

    pass


class ToolExecutionError(ToolException):
    """工具执行错误"""

    pass


class ToolConfigurationError(ToolException):
    """工具配置错误"""

    pass


class ToolDiscoveryError(ToolException):
    """工具发现错误"""

    pass


class AdapterError(ToolException):
    """适配器错误"""

    pass


class SkillLoadError(ToolException):
    """技能加载错误"""

    pass
