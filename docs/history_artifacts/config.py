"""系统配置管理

集中管理所有配置项
"""

from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field
import yaml
import os


@dataclass
class AnthropicConfig:
    """Anthropic API配置"""
    api_key: str
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 30


@dataclass
class OpenAIConfig:
    """OpenAI API配置（可选）"""
    api_key: str = ""
    model: str = "gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.7


@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    workers: int = 4


@dataclass
class LogConfig:
    """日志配置"""
    level: str = "INFO"
    file: Optional[str] = "logs/app.log"
    rotation: str = "10 MB"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class AgentConfig:
    """Agent配置"""
    timeout: int = 30
    max_retries: int = 3
    enable_cache: bool = True
    cache_ttl: int = 3600  # 秒


@dataclass
class SystemConfig:
    """系统总配置"""
    anthropic: AnthropicConfig = field(default_factory=lambda: AnthropicConfig(api_key=""))
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    log: LogConfig = field(default_factory=LogConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)

    @classmethod
    def from_yaml(cls, file_path: str) -> "SystemConfig":
        """从YAML文件加载配置"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "SystemConfig":
        """从字典创建配置对象"""
        config = cls()

        if "anthropic" in data:
            config.anthropic = AnthropicConfig(**data["anthropic"])
        if "openai" in data:
            config.openai = OpenAIConfig(**data["openai"])
        if "server" in data:
            config.server = ServerConfig(**data["server"])
        if "log" in data:
            config.log = LogConfig(**data["log"])
        if "agent" in data:
            config.agent = AgentConfig(**data["agent"])

        return config

    def validate(self) -> bool:
        """验证配置有效性"""
        if not self.anthropic.api_key:
            raise ValueError("Anthropic API密钥未设置")

        return True


# 全局配置实例
_config: Optional[SystemConfig] = None


def load_config(file_path: str = "config.yaml") -> SystemConfig:
    """加载配置文件"""
    global _config
    _config = SystemConfig.from_yaml(file_path)
    _config.validate()
    return _config


def get_config() -> SystemConfig:
    """获取当前配置"""
    if _config is None:
        # 尝试从环境变量加载
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            _config = SystemConfig(anthropic=AnthropicConfig(api_key=api_key))
        else:
            _config = SystemConfig()  # 使用默认配置
    return _config
