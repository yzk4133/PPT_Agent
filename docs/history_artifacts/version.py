"""版本信息管理

集中管理项目的版本信息
"""

from typing import Final


# 项目元数据
__name__: Final = "MultiAgent PPT"
__version__: Final = "0.1.0"
__author__: Final = "Your Name"
__email__: Final = "your.email@example.com"
__description__: Final = "基于多Agent协作的智能PPT生成系统"
__url__: Final = "https://github.com/yourusername/MultiAgentPPT"
__license__: Final = "MIT"


# 版本历史
VERSION_HISTORY = {
    "0.1.0": "2026-02-02",  # MVP版本
}


def get_version() -> str:
    """获取当前版本号"""
    return __version__


def get_version_info() -> dict:
    """获取完整的版本信息"""
    return {
        "name": __name__,
        "version": __version__,
        "author": __author__,
        "email": __email__,
        "description": __description__,
        "url": __url__,
        "license": __license__,
    }


def check_version_compatibility(required_version: str) -> bool:
    """检查版本兼容性

    Args:
        required_version: 需要的最低版本

    Returns:
        是否兼容
    """
    from packaging import version as pkg_version

    return pkg_version.parse(__version__) >= pkg_version.parse(required_version)
