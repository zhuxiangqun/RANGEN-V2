#!/usr/bin/env python3
"""
Real Search API Tool - 真实搜索API工具
集成 Tavily 搜索引擎API
"""

import os
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .base_tool import BaseTool, ToolResult


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    content: str
    score: float


class RealSearchTool(BaseTool):
    """
    真实搜索工具 - 基于 Tavily API
    
    特点：
    - 实时网络搜索
    - 高质量搜索结果
    - 支持中文搜索
    - 返回摘要内容
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化搜索工具"""
        super().__init__(
            tool_name="real_search",
            description="真实网络搜索工具：基于Tavily API，提供实时、准确的搜索结果"
        )
        
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self._client = None
        
        if not self.api_key:
            self.logger.warning("⚠️ TAVILY_API_KEY 未设置，请设置环境变量")
    
    def _get_client(self):
        """获取Tavily客户端"""
        if self._client is None:
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=self.api_key)
            except ImportError:
                self.logger.error("❌ Tavily未安装: pip install tavily")
                return None
        return self._client
    
    async def call(
        self, 
        query: str, 
        max_results: int = 5,
        include_answer: bool = True,
        include_raw_content: bool = False,
        **kwargs
    ) -> ToolResult:
        """
        执行搜索
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数
            include_answer: 是否包含AI摘要
            include_raw_content: 是否包含原始内容
            
        Returns:
            ToolResult: 搜索结果
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"🔍 搜索: {query}")
            
            client = self._get_client()
            if not client:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Tavily API 不可用，请设置 TAVILY_API_KEY",
                    execution_time=time.time() - start_time
                )
            
            # 执行搜索
            results = client.search(
                query=query,
                max_results=max_results,
                include_answer=include_answer,
                include_raw_content=include_raw_content
            )
            
            # 格式化结果
            search_results = []
            for item in results.get("results", []):
                search_results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", "")[:500],
                    "score": item.get("score", 0.0)
                })
            
            answer = results.get("answer", "")
            
            execution_time = time.time() - start_time
            self._record_call(True)
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "answer": answer,
                    "results": search_results,
                    "count": len(search_results)
                },
                metadata={
                    "max_results": max_results,
                    "execution_time": execution_time
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"❌ 搜索失败: {str(e)[:100]}")
            self._record_call(False)
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """获取工具参数模式"""
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
                "include_answer": {
                    "type": "boolean",
                    "description": "是否包含AI摘要",
                    "default": True
                },
                "include_raw_content": {
                    "type": "boolean",
                    "description": "是否包含原始内容",
                    "default": False
                }
            },
            "required": ["query"]
        }


class BingSearchTool(BaseTool):
    """
    Bing 搜索工具 - 备用搜索引擎
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            tool_name="bing_search",
            description="Bing搜索引擎API"
        )
        self.api_key = api_key or os.getenv("BING_API_KEY", "")
    
    async def call(self, query: str, count: int = 10, **kwargs) -> ToolResult:
        """执行Bing搜索"""
        start_time = time.time()
        
        try:
            if not self.api_key:
                return ToolResult(
                    success=False,
                    data=None,
                    error="BING_API_KEY 未设置",
                    execution_time=time.time() - start_time
                )
            
            # 使用 Bing Web Search API
            import requests
            
            endpoint = "https://api.bing.microsoft.com/v7.0/search"
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            params = {"q": query, "count": count, "textFormat": "Raw"}
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("webPages", {}).get("value", [])[:count]:
                results.append({
                    "title": item.get("name", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", "")
                })
            
            return ToolResult(
                success=True,
                data={"query": query, "results": results, "count": len(results)},
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索查询"},
                "count": {"type": "integer", "description": "结果数", "default": 10}
            },
            "required": ["query"]
        }
