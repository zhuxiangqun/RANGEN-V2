"""
网页抓取与 PageIndex 集成模块

⚠️ 此模块现在通过 HTTP API 调用独立的 KMS 服务

功能:
- 从 URL 抓取网页内容
- 索引到 KMS 服务

使用方式:
    from src.kms.web_crawler import WebCrawler
    
    crawler = WebCrawler()
    crawler.crawl_and_index("https://example.com")
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from .kms_client import KMSClient, get_kms_client

logger = logging.getLogger(__name__)


class ContentFormat(Enum):
    """内容格式"""
    HTML = "html"
    MARKDOWN = "markdown"
    TEXT = "text"


@dataclass
class CrawlResult:
    """抓取结果"""
    success: bool
    url: str
    title: str = ""
    content: str = ""
    error: str = ""


class WebCrawler:
    """
    网页抓取器
    
    ⚠️ 现在通过 KMS API 调用独立服务
    """
    
    def __init__(
        self,
        kms_client: Optional[KMSClient] = None,
        api_url: Optional[str] = None
    ):
        """
        初始化网页抓取器
        
        Args:
            kms_client: KMS 客户端实例
            api_url: KMS API 地址
        """
        if kms_client:
            self.client = kms_client
        elif api_url:
            self.client = KMSClient(api_url=api_url)
        else:
            self.client = get_kms_client()
    
    def crawl_url(self, url: str) -> CrawlResult:
        """
        抓取单个 URL
        
        注意: 此功能需要 KMS 服务支持
        """
        try:
            # 通过 KMS API 抓取
            result = self.client.crawl_url(url)
            
            return CrawlResult(
                success=result.get("success", True),
                url=url,
                title=result.get("title", ""),
                content=result.get("content", ""),
                error=result.get("error", "")
            )
        except Exception as e:
            logger.error(f"Failed to crawl URL {url}: {e}")
            return CrawlResult(
                success=False,
                url=url,
                error=str(e)
            )
    
    def crawl_and_index(
        self,
        url: str,
        document_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        抓取并索引
        
        Args:
            url: 网页 URL
            document_description: 文档描述
        """
        try:
            # 1. 抓取内容
            crawl_result = self.crawl_url(url)
            
            if not crawl_result.success:
                return {
                    "success": False,
                    "error": crawl_result.error
                }
            
            # 2. 导入到 KMS
            import_result = self.client.import_knowledge(
                data={
                    "url": url,
                    "title": crawl_result.title,
                    "content": crawl_result.content,
                    "source": "web"
                },
                modality="text",
                metadata={
                    "source_type": "web",
                    "url": url,
                    "title": crawl_result.title
                }
            )
            
            return {
                "success": True,
                "url": url,
                "title": crawl_result.title,
                "knowledge_id": import_result.get("knowledge_id")
            }
        except Exception as e:
            logger.error(f"Failed to crawl and index {url}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def crawl_batch(self, urls: List[str]) -> List[CrawlResult]:
        """批量抓取"""
        return [self.crawl_url(url) for url in urls]
    
    def is_available(self) -> bool:
        """检查 KMS 服务是否可用"""
        return self.client.is_available()


# ==================== 便捷函数 ====================

_web_crawler: Optional[WebCrawler] = None


def get_web_crawler(
    kms_client: Optional[KMSClient] = None,
    api_url: Optional[str] = None
) -> WebCrawler:
    """获取网页抓取器实例"""
    global _web_crawler
    if _web_crawler is None:
        _web_crawler = WebCrawler(kms_client=kms_client, api_url=api_url)
    return _web_crawler


def reset_web_crawler():
    """重置网页抓取器"""
    global _web_crawler
    _web_crawler = None
