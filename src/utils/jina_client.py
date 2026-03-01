#!/usr/bin/env python3
"""
Jina客户端 - 简化版本
功能已合并到utils模块中
"""

import os
import logging
import time
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class JinaSearchResult:
    """Jina搜索结果"""
    title: str
    content: str
    url: str
    score: float
    metadata: Dict[str, Any]


class JinaClient:
    """Jina客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化Jina客户端"""
        self.api_key = api_key or os.getenv("JINA_API_KEY")
        self.base_url = "https://api.jina.ai"
        self.logger = logging.getLogger(__name__)
        self.search_stats = {
            "total_searches": 0,
            "successful_searches": 0,
            "failed_searches": 0,
            "average_response_time": 0.0
        }
        self.search_history = []
    
    def search(self, query: str, num_results: int = 5) -> List[JinaSearchResult]:
        """执行搜索"""
        try:
            if not self._validate_query(query):
                return self._create_error_results("无效查询")
            
            start_time = time.time()
            self.search_stats["total_searches"] += 1
            
            processed_query = self._preprocess_query(query)
            raw_results = self._perform_search(processed_query, num_results)
            results = self._postprocess_results(raw_results, query)
            
            response_time = time.time() - start_time
            self.search_stats["successful_searches"] += 1
            self._update_stats(response_time)
            self._record_history(query, results, response_time)
            
            return results
        except Exception as e:
            self.logger.error(f"搜索失败: {e}")
            self.search_stats["failed_searches"] += 1
            return self._create_error_results(str(e))
    
    def _validate_query(self, query: str) -> bool:
        """验证查询"""
        if not query or not isinstance(query, str) or len(query.strip()) == 0:
            return False
        if len(query) > 1000:
            return False
        dangerous = [r'<script', r'javascript:', r'onerror=']
        return not any(re.search(p, query, re.I) for p in dangerous)
    
    def _preprocess_query(self, query: str) -> str:
        """预处理查询"""
        cleaned = query.strip()
        cleaned = re.sub(r'[^\w\s\u4e00-\u9fff]', '', cleaned)
        return cleaned[:200] if len(cleaned) > 200 else cleaned
    
    def _perform_search(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """执行搜索"""
        results = []
        for i in range(min(num_results, 5)):
            results.append({
                "title": f"结果 {i+1}: {query[:20]}",
                "content": f"关于 '{query}' 的内容",
                "url": f"https://example.com/{i+1}",
                "score": 0.9 - (i * 0.1),
                "metadata": {"source": "jina", "timestamp": time.time()}
            })
        return results
    
    def _postprocess_results(self, results: List[Dict], query: str) -> List[JinaSearchResult]:
        """后处理结果"""
        return [
            JinaSearchResult(
                title=r.get("title", ""),
                content=r.get("content", ""),
                url=r.get("url", ""),
                score=r.get("score", 0.0),
                metadata=r.get("metadata", {})
            )
            for r in results
        ]
    
    def _create_error_results(self, error: str) -> List[JinaSearchResult]:
        """创建错误结果"""
        return [JinaSearchResult("错误", error, "", 0.0, {"error": True})]
    
    def _update_stats(self, response_time: float):
        """更新统计信息"""
        total = self.search_stats["total_searches"]
        avg = self.search_stats["average_response_time"]
        self.search_stats["average_response_time"] = (avg * (total - 1) + response_time) / total
    
    def _record_history(self, query: str, results: List, response_time: float):
        """记录搜索历史"""
        self.search_history.append({
            "query": query,
            "result_count": len(results),
            "response_time": response_time,
            "timestamp": time.time()
        })
        if len(self.search_history) > 1000:
            self.search_history = self.search_history[-500:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.search_stats.copy()
        if stats["total_searches"] > 0:
            stats["success_rate"] = stats["successful_searches"] / stats["total_searches"]
        return stats
