#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WeChat Article Search MCP Tool

搜索微信公众号文章，先根据关键词搜索搜狗，获取链接，
然后使用get_real_url获取真实链接，最后获取公众号内容。

Converted to MCP tool format - 2025-02-03
"""

import json
import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

import requests
from lxml import html
from urllib.parse import quote

from .base_mcp_tool import BaseMCPTool

logger = logging.getLogger(__name__)


class WeChatSearchTool(BaseMCPTool):
    """
    WeChat Article Search Tool

    通过搜狗微信搜索 API 搜索微信公众号文章。
    """

    def __init__(self):
        super().__init__(name="weixin_search")

    async def execute(self, query: str, num_results: int = 5,
                     fetch_content: bool = True,
                     tool_context: Optional[Any] = None) -> str:
        """
        搜索微信公众号文章

        Args:
            query: 搜索关键词
            num_results: 返回结果数量 (1-20)，默认 5
            fetch_content: 是否获取文章正文内容，默认 True
            tool_context: 工具上下文（可选）

        Returns:
            JSON 格式的搜索结果
        """
        try:
            # 参数验证
            num_results = max(1, min(20, int(num_results)))

            # 步骤 1: 搜狗微信搜索
            search_results = await self._sogou_weixin_search(query, num_results)

            if not search_results:
                return self._success({
                    "query": query,
                    "total": 0,
                    "articles": [],
                    "message": f"没有搜索到与 '{query}' 相关的文章"
                })

            # 步骤 2: 如果需要，获取文章内容
            if fetch_content:
                articles = []
                for result in search_results:
                    real_url = await self._get_real_url(result["link"])
                    if real_url:
                        content = await self._get_article_content(real_url, result["link"])
                        articles.append({
                            "title": result["title"],
                            "publish_time": result["publish_time"],
                            "sogou_url": result["link"],
                            "real_url": real_url,
                            "content": content[:5000] + "..." if len(content) > 5000 else content
                        })
                    else:
                        # 无法获取真实 URL，只返回搜索结果
                        articles.append({
                            "title": result["title"],
                            "publish_time": result["publish_time"],
                            "sogou_url": result["link"],
                            "real_url": "",
                            "content": "无法获取文章正文"
                        })
            else:
                articles = [
                    {
                        "title": r["title"],
                        "publish_time": r["publish_time"],
                        "sogou_url": r["link"]
                    }
                    for r in search_results
                ]

            return self._success({
                "query": query,
                "total": len(articles),
                "articles": articles,
                "fetched_content": fetch_content
            })

        except Exception as e:
            logger.error(f"WeChat search failed: {e}")
            return self._error(f"搜索失败: {str(e)}", {
                "query": query,
                "num_results": num_results
            })

    async def _sogou_weixin_search(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """在搜狗微信搜索中搜索指定关键词并返回结果列表"""
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Referer": f"https://weixin.sogou.com/weixin?query={quote(query)}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        }

        params = {
            "type": "2",
            "s_from": "input",
            "query": query,
            "ie": "utf8",
            "_sug_": "n",
            "_sug_type_": "",
        }

        try:
            response = requests.get(
                "https://weixin.sogou.com/weixin",
                params=params,
                headers=headers,
                timeout=15
            )

            if response.status_code == 200:
                tree = html.fromstring(response.text)
                results = []

                elements = tree.xpath("//a[contains(@id, 'sogou_vr_11002601_title_')]")
                publish_time = tree.xpath(
                    "//li[contains(@id, 'sogou_vr_11002601_box_')]/div[@class='txt-box']/div[@class='s-p']/span[@class='s2']"
                )

                for element, time_elem in zip(elements[:num_results], publish_time[:num_results]):
                    title = element.text_content().strip()
                    link = element.get("href")
                    if link and not link.startswith("http"):
                        link = "https://weixin.sogou.com" + link
                    results.append({
                        "title": title,
                        "link": link,
                        "publish_time": time_elem.text_content().strip(),
                    })

                logger.info(f"Sogou WeChat search found {len(results)} results for '{query}'")
                return results
            else:
                logger.warning(f"Sogou returned status {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Sogou WeChat search failed: {e}")
            return []

    async def _get_real_url(self, sogou_url: str) -> str:
        """从搜狗微信链接获取真实的微信公众号文章链接"""
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        }

        try:
            response = requests.get(sogou_url, headers=headers, timeout=10)
            script_content = response.text

            # 解析 JavaScript 中的 URL
            start_index = script_content.find("url += '") + len("url += '")
            url_parts = []

            while True:
                part_start = script_content.find("url += '", start_index)
                if part_start == -1:
                    break
                part_end = script_content.find("'", part_start + len("url += '"))
                part = script_content[part_start + len("url += '") : part_end]
                url_parts.append(part)
                start_index = part_end + 1

            if url_parts:
                full_url = "".join(url_parts).replace("@", "")
                return "https://mp." + full_url
            return ""
        except Exception as e:
            logger.error(f"Get real URL failed: {e}")
            return ""

    async def _get_article_content(self, real_url: str, referer: str) -> str:
        """获取微信公众号文章的正文内容"""
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "referer": referer,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        }

        try:
            response = requests.get(real_url, headers=headers, timeout=10)
            tree = html.fromstring(response.text)
            content_elements = tree.xpath("//div[@id='js_content']//text()")
            cleaned_content = [text.strip() for text in content_elements if text.strip()]
            main_content = "\n".join(cleaned_content)
            return main_content
        except Exception as e:
            logger.error(f"Get article content failed: {e}")
            return f"获取文章内容失败: {str(e)}"


# 创建全局实例
_weixin_search_tool = WeChatSearchTool()


# 导出函数式接口（与 agents 工具兼容）
async def weixin_search(
    query: str,
    num_results: int = 5,
    fetch_content: bool = True,
    tool_context: Optional[Any] = None
) -> str:
    """
    搜索微信公众号文章

    Args:
        query: 搜索关键词
        num_results: 返回结果数量 (1-20)
        fetch_content: 是否获取文章正文内容
        tool_context: 工具上下文（可选）

    Returns:
        JSON 格式的搜索结果
    """
    return await _weixin_search_tool.execute(
        query=query,
        num_results=num_results,
        fetch_content=fetch_content,
        tool_context=tool_context
    )


# 便捷函数
async def search_wechat_articles(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    便捷函数：搜索微信公众号文章并返回解析后的结果列表

    Args:
        query: 搜索关键词
        num_results: 返回结果数量

    Returns:
        文章列表
    """
    result = await weixin_search(query=query, num_results=num_results)
    data = json.loads(result)
    if data.get("success"):
        return data["result"]["articles"]
    return []


if __name__ == "__main__":
    # 测试代码
    async def test():
        result = await weixin_search(query="吉利汽车", num_results=2)
        print(json.dumps(json.loads(result), ensure_ascii=False, indent=2))

    asyncio.run(test())
