"""
知识库管理系统工具模块
"""

# 导出jina服务
from .jina_service import get_jina_service, JinaService

# 导出Wikipedia抓取器
from .wikipedia_fetcher import get_wikipedia_fetcher, WikipediaFetcher

__all__ = ['get_jina_service', 'JinaService', 'get_wikipedia_fetcher', 'WikipediaFetcher']

