"""通用工具函数集合

提供项目中常用的工具函数
"""

import re
import hashlib
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import os


def slugify(text: str) -> str:
    """将文本转换为URL友好的slug

    Args:
        text: 原始文本

    Returns:
        Slug字符串
    """
    # 转小写
    text = text.lower()
    # 替换空格和特殊字符
    text = re.sub(r'[\s\-]+', '-', text)
    text = re.sub(r'[^\w\-]', '', text)
    return text.strip('-')


def generate_hash(content: Any) -> str:
    """生成内容的哈希值

    Args:
        content: 任意可序列化的内容

    Returns:
        MD5哈希字符串
    """
    if isinstance(content, (dict, list)):
        content = json.dumps(content, sort_keys=True)
    elif not isinstance(content, str):
        content = str(content)

    return hashlib.md5(content.encode()).hexdigest()


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """截断文本到指定长度

    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后添加的后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_duration(seconds: float) -> str:
    """格式化时长

    Args:
        seconds: 秒数

    Returns:
        格式化的时长字符串 (如 "1h 23m 45s")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        格式化的文件大小字符串 (如 "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def validate_email(email: str) -> bool:
    """验证邮箱格式

    Args:
        email: 邮箱地址

    Returns:
        是否有效
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def safe_json_loads(text: str, default: Any = None) -> Any:
    """安全地解析JSON

    Args:
        text: JSON文本
        default: 解析失败时返回的默认值

    Returns:
        解析结果或默认值
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """递归合并多个字典

    Args:
        *dicts: 要合并的字典

    Returns:
        合并后的字典
    """
    result = {}

    for d in dicts:
        for key, value in d.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value)
            else:
                result[key] = value

    return result


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """将列表分块

    Args:
        items: 原始列表
        chunk_size: 块大小

    Returns:
        分块后的列表
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def ensure_dir(path: str) -> str:
    """确保目录存在，不存在则创建

    Args:
        path: 目录路径

    Returns:
        目录路径
    """
    os.makedirs(path, exist_ok=True)
    return path


def get_timestamp() -> str:
    """获取当前时间戳字符串

    Returns:
        ISO格式的时间戳
    """
    return datetime.now().isoformat()


def parse_bool(value: Any) -> bool:
    """解析布尔值

    Args:
        value: 要解析的值

    Returns:
        布尔值
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除不安全字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    # 移除路径字符
    filename = os.path.basename(filename)
    # 替换不安全字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除首尾空格和点
    filename = filename.strip('. ')
    return filename or "unnamed"
