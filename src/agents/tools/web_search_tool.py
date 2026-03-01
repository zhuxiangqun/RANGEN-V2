#!/usr/bin/env python3
"""
Web Search Tool - 基于Browser的网页搜索工具
使用DuckDuckGo作为搜索引擎（无反爬虫）
"""

import asyncio
import re
from typing import Dict, Any, Optional

from .base_tool import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    """
    网页搜索工具 - 基于Browser
    
    特点：
    - 使用 DuckDuckGo（无反爬虫）
    - 返回纯文本结果
    - 支持截图
    """
    
    def __init__(self):
        super().__init__(
            tool_name="web_search",
            description="网页搜索工具：使用DuckDuckGo搜索网页，返回搜索结果和摘要"
        )
        self._browser = None
    
    async def _get_browser(self):
        """获取或创建浏览器"""
        if self._browser is None:
            from src.gateway.tools.browser import BrowserTool as GatewayBrowserTool
            self._browser = GatewayBrowserTool()
            await self._browser.initialize()
        return self._browser
    
    async def call(
        self, 
        query: str, 
        max_results: int = 5,
        take_screenshot: bool = False,
        **kwargs
    ) -> ToolResult:
        """
        执行网页搜索
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数
            take_screenshot: 是否截图
            
        Returns:
            ToolResult: 搜索结果
        """
        import time
        start_time = time.time()
        
        try:
            browser = await self._get_browser()
            
            # 访问 DuckDuckGo
            await browser.navigate("https://duckduckgo.com/")
            
            # 填入搜索词
            search_selectors = [
                '#search_form_input_homepage',
                'input[name="q"]',
                '#search_form_input'
            ]
            
            filled = False
            for selector in search_selectors:
                try:
                    await browser.page.fill(selector, query)
                    filled = True
                    break
                except:
                    continue
            
            if not filled:
                # 使用 JavaScript 填充
                await browser.page.evaluate(f'document.querySelector("#search_form_input_homepage").value = "{query}"')
            
            # 按回车
            await browser.page.keyboard.press("Enter")
            await browser.page.wait_for_load_state("networkidle")
            await asyncio.sleep(1)
            
            # 提取结果
            results = []
            
            # 尝试获取结果链接
            try:
                # 获取搜索结果链接
                link_elements = await browser.page.query_selector_all('.result__a')
                
                for i, link in enumerate(link_elements[:max_results]):
                    try:
                        href = await link.get_attribute('href')
                        text = await link.inner_text()
                        if href and text:
                            results.append({
                                'title': text[:100],
                                'url': href[:200]
                            })
                    except:
                        continue
            except Exception as e:
                self.logger.warning(f"提取链接失败: {e}")
            
            # 尝试获取结果摘要
            snippets = []
            try:
                snippet_elements = await browser.page.query_selector_all('.result__snippet')
                for snippet in snippet_elements[:max_results]:
                    try:
                        text = await snippet.inner_text()
                        if text:
                            snippets.append(text)
                    except:
                        continue
            except:
                pass
            
            # 合并结果
            final_results = []
            for i in range(min(len(results), max_results)):
                item = results[i]
                snippet = snippets[i] if i < len(snippets) else ""
                final_results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'snippet': snippet[:200]
                })
            
            # 截图
            screenshot_path = None
            if take_screenshot:
                screenshot_path = f'/tmp/search_{int(time.time())}.png'
                await browser.screenshot(screenshot_path)
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=True,
                data={
                    'query': query,
                    'results': final_results,
                    'count': len(final_results),
                    'screenshot': screenshot_path
                },
                metadata={
                    'engine': 'duckduckgo',
                    'max_results': max_results,
                    'execution_time': execution_time
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"搜索失败: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def close(self):
        """关闭浏览器"""
        if self._browser:
            await self._browser.close()
            self._browser = None
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """获取参数模式"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询"
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大结果数",
                    "default": 5
                },
                "take_screenshot": {
                    "type": "boolean",
                    "description": "是否截图",
                    "default": False
                }
            },
            "required": ["query"]
        }
