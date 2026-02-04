"""
Research State Domain Model

Domain model for the research stage state.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ResearchResultState:
    """
    单个研究结果

    表示单个页面的研究结果状态。

    Attributes:
        page_no: 页码
        page_title: 页面标题
        research_type: 研究类型
        content: 研究内容
        source: 资料来源
        data_points: 数据点列表
        is_visualizable: 是否可可视化
    """

    page_no: int
    page_title: str
    research_type: str = "通用类"
    content: str = ""
    source: str = ""
    data_points: List[Dict[str, str]] = field(default_factory=list)
    is_visualizable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "page_no": self.page_no,
            "page_title": self.page_title,
            "research_type": self.research_type,
            "content": self.content,
            "source": self.source,
            "data_points": self.data_points,
            "is_visualizable": self.is_visualizable
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchResultState":
        """从字典创建"""
        return cls(
            page_no=data.get("page_no", 1),
            page_title=data.get("page_title", ""),
            research_type=data.get("research_type", "通用类"),
            content=data.get("content", ""),
            source=data.get("source", ""),
            data_points=data.get("data_points", []),
            is_visualizable=data.get("is_visualizable", False)
        )

@dataclass
class ResearchState:
    """
    研究阶段后的状态

    表示研究阶段完成后的结构化状态。

    Attributes:
        results: 研究结果列表
        total_researched: 已研究的页面数
    """

    results: List[ResearchResultState] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "research_results": [r.to_dict() for r in self.results],
            "total_researched": len(self.results)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchState":
        """从字典创建"""
        results_data = data.get("research_results", [])
        results = [ResearchResultState.from_dict(r) for r in results_data]

        return cls(results=results)

    def add_result(self, result: ResearchResultState) -> None:
        """添加研究结果"""
        self.results.append(result)

    def get_result_for_page(self, page_no: int) -> ResearchResultState:
        """获取指定页码的研究结果"""
        for result in self.results:
            if result.page_no == page_no:
                return result
        # 返回空结果
        return ResearchResultState(page_no=page_no, page_title="")

    @property
    def total_researched(self) -> int:
        """已研究的页面数"""
        return len(self.results)

if __name__ == "__main__":
    # 测试代码
    result1 = ResearchResultState(
        page_no=1,
        page_title="行业分析",
        research_type="数据类",
        content="根据最新报告...",
        source="艾瑞咨询",
        data_points=[{"key": "市场规模", "value": "1000亿"}],
        is_visualizable=True
    )

    result2 = ResearchResultState(
        page_no=2,
        page_title="技术趋势",
        research_type="观点类",
        content="AI技术正在快速发展..."
    )

    research_state = ResearchState(results=[result1, result2])

    print("ResearchState Test:")
    print(f"Total researched: {research_state.total_researched}")

    page_1_result = research_state.get_result_for_page(1)
    print(f"Page 1 result: {page_1_result.page_title} - {page_1_result.source}")

    page_3_result = research_state.get_result_for_page(3)
    print(f"Page 3 result (empty): {page_3_result.page_title}")

    dict_data = research_state.to_dict()
    restored = ResearchState.from_dict(dict_data)
    print(f"Restored: {restored.total_researched} results")
