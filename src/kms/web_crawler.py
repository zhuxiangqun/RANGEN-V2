"""
网页抓取与PageIndex集成模块

功能:
- 从wiki-link抓取网页内容 (可选)
- 直接使用HuggingFace已处理的Wikipedia内容
- 转换为HTML/Markdown
- 索引到PageIndex

支持数据源:
- HuggingFace datasets (google/frames-benchmark等)
- parasail-ai/frames-benchmark-wikipedia (已处理内容)
- URL列表
- 本地HTML文件
"""

import re
import asyncio
import logging
import hashlib
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

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
    """网页抓取器"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self._requests_available = self._check_lib("requests")
        self._beautifulsoup_available = self._check_lib("bs4")
    
    def _check_lib(self, lib: str) -> bool:
        try:
            __import__(lib if lib != "bs4" else "bs4")
            return True
        except ImportError:
            return False
    
    async def crawl(self, url: str) -> CrawlResult:
        """抓取单个网页"""
        if not self._requests_available:
            return CrawlResult(success=False, url=url, error="requests not installed")
        
        import requests
        
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            if self._beautifulsoup_available:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.title.string if soup.title else url
                
                for tag in soup(['script', 'style', 'nav', 'footer']):
                    tag.decompose()
                
                content = soup.get_text(separator='\n', strip=True)
                content = re.sub(r'\n{3,}', '\n\n', content)
            else:
                title = url.split('/')[-1]
                content = response.text[:10000]
            
            return CrawlResult(success=True, url=url, title=title, content=content)
            
        except Exception as e:
            return CrawlResult(success=False, url=url, error=str(e))
    
    async def crawl_batch(self, urls: List[str], delay: float = 1.0) -> List[CrawlResult]:
        """批量抓取"""
        results = []
        for i, url in enumerate(urls):
            result = await self.crawl(url)
            results.append(result)
            if i < len(urls) - 1:
                await asyncio.sleep(delay)
        return results


class HuggingFaceDatasetLoader:
    """HuggingFace数据集加载器"""
    
    def __init__(self):
        self._hf_available = self._check_lib("datasets")
    
    def _check_lib(self, lib: str) -> bool:
        try:
            __import__(lib)
            return True
        except ImportError:
            logger.warning(f"{lib} not installed: pip install {lib}")
            return False
    
    async def load_dataset(
        self,
        dataset_name: str,
        split: str = "train"
    ) -> List[Dict[str, Any]]:
        """加载数据集"""
        if not self._hf_available:
            raise ImportError("datasets not installed")
        
        from datasets import load_dataset
        
        logger.info(f"Loading: {dataset_name}")
        dataset = load_dataset(dataset_name, split=split)
        items = [dict(item) for item in dataset]
        logger.info(f"Loaded {len(items)} items")
        return items
    
    def get_content_field(self, items: List[Dict[str, Any]]) -> Optional[str]:
        """获取content字段名"""
        if not items:
            return None
        
        fields = ["text", "content", "article", "body", "wiki_text"]
        item = items[0]
        
        for f in fields:
            if f in item and item[f]:
                return f
        return None
    
    def extract_links(self, items: List[Dict[str, Any]], field: str = "link") -> List[str]:
        """提取链接"""
        urls = []
        for item in items:
            if field in item and item[field]:
                urls.append(item[field])
        return urls


class ContentConverter:
    """内容转换器"""
    
    @staticmethod
    def create_markdown(title: str, content: str, source_url: str = "") -> str:
        """创建Markdown"""
        return f"""# {title}

Source: {source_url}

---

{content}
"""


class WikiLinkPageIndexer:
    """
    Wiki-Link页面索引器
    
    支持:
    - parasail-ai/frames-benchmark-wikipedia (直接使用content)
    - google/frames-benchmark (需要抓取wiki-link)
    """
    
    def __init__(self, pageindex=None, output_dir: str = "./data/wiki_content"):
        self.pageindex = pageindex
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.crawler = WebCrawler()
        self.converter = ContentConverter()
        self.loader = HuggingFaceDatasetLoader()
    
    async def index_from_dataset(
        self,
        dataset_name: str,
        link_field: str = "link",
        content_field: Optional[str] = None,
        title_field: str = "title",
        max_items: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        从数据集索引
        
        智能检测:
        - 如果有content字段 → 直接使用
        - 如果没有 → 抓取wiki-link
        """
        stats = {"total": 0, "success": 0, "failed": 0, "source": "unknown", "errors": []}
        
        try:
            items = await self.loader.load_dataset(dataset_name)
        except Exception as e:
            stats["errors"].append(str(e))
            return stats
        
        if max_items:
            items = items[:max_items]
        
        stats["total"] = len(items)
        
        # 自动检测content字段
        if content_field is None:
            content_field = self.loader.get_content_field(items)
        
        if content_field and content_field in items[0]:
            # ✅ 有content，直接使用 (推荐!)
            logger.info(f"Using '{content_field}' field - no crawling needed!")
            stats["source"] = "dataset_content"
            
            for i, item in enumerate(items):
                title = item.get(title_field, f"Article_{i}")
                content = item.get(content_field, "")
                url = item.get(link_field, "")
                
                if content:
                    await self._save_and_index(url, title, content, f"item_{i}")
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                
                if (i + 1) % 50 == 0:
                    logger.info(f"Progress: {i+1}/{len(items)}")
        else:
            # ❌ 需要抓取
            logger.info("No content field - will crawl wiki links")
            stats["source"] = "crawled"
            
            urls = self.loader.extract_links(items, link_field)
            results = await self.crawler.crawl_batch(urls)
            
            for i, result in enumerate(results):
                if result.success:
                    await self._save_and_index(result.url, result.title, result.content, f"page_{i}")
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                    stats["errors"].append(result.error)
        
        return stats
    
    async def _save_and_index(self, url: str, title: str, content: str, name: str):
        """保存并索引"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"{name}_{url_hash}.md"
        
        md_path = self.output_dir / filename
        markdown = self.converter.create_markdown(title, content, url)
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        if self.pageindex:
            try:
                await self.pageindex.index_document(str(md_path), title)
            except Exception as e:
                logger.warning(f"Index failed: {e}")


# ==================== 便捷函数 ====================

_indexer: Optional[WikiLinkPageIndexer] = None


def get_wiki_indexer(pageindex=None, output_dir: str = "./data/wiki_content") -> WikiLinkPageIndexer:
    global _indexer
    if _indexer is None:
        _indexer = WikiLinkPageIndexer(pageindex, output_dir)
    return _indexer
