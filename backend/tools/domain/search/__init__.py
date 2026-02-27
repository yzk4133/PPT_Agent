"""
Search Tools - LangChain Native

Web search and URL fetching tools.
"""

from backend.tools.domain.search.web_search_tool import tool as web_search
from backend.tools.domain.search.fetch_url_tool import tool as fetch_url
from backend.tools.domain.search.weixin_search_tool import tool as weixin_search

__all__ = ["web_search", "fetch_url", "weixin_search"]
