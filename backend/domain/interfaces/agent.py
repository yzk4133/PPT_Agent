"""
Agent Interfaces

定义Agent相关的接口，用于抽象和标准化Agent的实现。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncIterator
from dataclasses import dataclass


@dataclass
class IAgentConfig:
    """
    Agent配置接口

    Attributes:
        name: Agent名称
        model: 模型名称
        provider: 模型提供商
        temperature: 温度参数
        max_tokens: 最大token数
        timeout: 超时时间（秒）
    """

    name: str
    model: str = "deepseek-chat"
    provider: str = "deepseek"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60
    enable_fallback: bool = True


@dataclass
class IAgentContext:
    """
    Agent执行上下文接口

    Attributes:
        session_id: 会话ID
        user_id: 用户ID
        state: 会话状态
        metadata: 元数据
    """

    session_id: str
    user_id: str = "anonymous"
    state: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.state is None:
            self.state = {}
        if self.metadata is None:
            self.metadata = {}

    def get(self, key: str, default: Any = None) -> Any:
        """从状态中获取值"""
        return self.state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置状态值"""
        self.state[key] = value


@dataclass
class IAgentResult:
    """
    Agent执行结果接口

    Attributes:
        success: 是否成功
        content: 结果内容
        error: 错误信息
        metadata: 元数据
        events: 事件列表
    """

    success: bool
    content: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    events: List[Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.events is None:
            self.events = []


class IAgent(ABC):
    """
    Agent接口

    定义Agent的基本行为和契约。
    """

    @abstractmethod
    def get_name(self) -> str:
        """获取Agent名称"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """获取Agent描述"""
        pass

    @abstractmethod
    async def run(
        self,
        context: IAgentContext,
        input_data: Any
    ) -> IAgentResult:
        """
        执行Agent任务

        Args:
            context: Agent上下文
            input_data: 输入数据

        Returns:
            IAgentResult: 执行结果
        """
        pass

    @abstractmethod
    async def run_stream(
        self,
        context: IAgentContext,
        input_data: Any
    ) -> AsyncIterator[Any]:
        """
        流式执行Agent任务

        Args:
            context: Agent上下文
            input_data: 输入数据

        Yields:
            流式事件或数据
        """
        pass


class ITopicSplitterAgent(IAgent):
    """
    主题拆分Agent接口

    专门负责将大纲拆分为多个研究主题。
    """

    @abstractmethod
    async def split_topics(
        self,
        context: IAgentContext,
        outline: str
    ) -> List[Dict[str, Any]]:
        """
        拆分大纲为多个主题

        Args:
            context: Agent上下文
            outline: 大纲内容

        Returns:
            主题列表
        """
        pass


class IResearchAgent(IAgent):
    """
    研究Agent接口

    专门负责对主题进行深入研究。
    """

    @abstractmethod
    async def research_topic(
        self,
        context: IAgentContext,
        topic: Dict[str, Any]
    ) -> str:
        """
        研究单个主题

        Args:
            context: Agent上下文
            topic: 主题信息

        Returns:
            研究结果
        """
        pass

    @abstractmethod
    async def research_topics_parallel(
        self,
        context: IAgentContext,
        topics: List[Dict[str, Any]]
    ) -> List[str]:
        """
        并行研究多个主题

        Args:
            context: Agent上下文
            topics: 主题列表

        Returns:
            研究结果列表
        """
        pass


class IContentGeneratorAgent(IAgent):
    """
    内容生成Agent接口

    专门负责生成内容（如PPT幻灯片）。
    """

    @abstractmethod
    async def generate_content(
        self,
        context: IAgentContext,
        research_data: Any
    ) -> str:
        """
        生成内容

        Args:
            context: Agent上下文
            research_data: 研究数据

        Returns:
            生成的内容
        """
        pass


class ISlideWriterAgent(IContentGeneratorAgent):
    """
    幻灯片写入Agent接口

    专门负责生成PPT幻灯片。
    """

    @abstractmethod
    async def generate_slide(
        self,
        context: IAgentContext,
        page_number: int,
        research_content: str
    ) -> str:
        """
        生成单张幻灯片

        Args:
            context: Agent上下文
            page_number: 页码
            research_content: 研究内容

        Returns:
            XML格式的幻灯片内容
        """
        pass

    @abstractmethod
    async def generate_presentation(
        self,
        context: IAgentContext,
        research_contents: List[str]
    ) -> str:
        """
        生成完整演示文稿

        Args:
            context: Agent上下文
            research_contents: 所有研究内容

        Returns:
            完整的PPT XML内容
        """
        pass


class IQualityCheckerAgent(IAgent):
    """
    质量检查Agent接口

    专门负责检查生成内容的质量。
    """

    @abstractmethod
    async def check_quality(
        self,
        context: IAgentContext,
        content: str,
        reference_content: str = ""
    ) -> Dict[str, Any]:
        """
        检查内容质量

        Args:
            context: Agent上下文
            content: 待检查的内容
            reference_content: 参考内容

        Returns:
            检查结果，包含 pass/fail 和建议
        """
        pass


# Agent工厂接口
class IAgentFactory(ABC):
    """
    Agent工厂接口

    用于创建不同类型的Agent实例。
    """

    @abstractmethod
    def create_topic_splitter(self, config: IAgentConfig) -> ITopicSplitterAgent:
        """创建主题拆分Agent"""
        pass

    @abstractmethod
    def create_research_agent(self, config: IAgentConfig) -> IResearchAgent:
        """创建研究Agent"""
        pass

    @abstractmethod
    def create_slide_writer(self, config: IAgentConfig) -> ISlideWriterAgent:
        """创建幻灯片写入Agent"""
        pass

    @abstractmethod
    def create_quality_checker(self, config: IAgentConfig) -> IQualityCheckerAgent:
        """创建质量检查Agent"""
        pass


if __name__ == "__main__":
    # 测试代码
    config = IAgentConfig(name="test_agent")
    context = IAgentContext(session_id="test_123")
    result = IAgentResult(success=True, content="测试结果")
    print(config)
    print(context)
    print(result)
