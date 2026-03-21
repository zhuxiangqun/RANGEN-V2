#!/usr/bin/env python3
"""
URL Discoverer Tool - URL 发现工具

从搜索结果和网页中发现 URL，用于数据采集工作流
"""

import re
import time
from typing import Dict, Any, List, Optional, Set
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
from collections import defaultdict

from .base_tool import BaseTool, ToolResult


@dataclass
class DiscoveredURL:
    """发现的 URL"""
    url: str
    source: str
    text: str
    domain: str
    url_type: str  # internal/external/resource


class URLDiscoverer(BaseTool):
    """
    URL 发现工具
    
    从搜索结果和网页中发现相关 URL
    """
    
    def __init__(self):
        super().__init__(
            tool_name="url_discoverer",
            description="从搜索结果和网页中发现相关 URL"
        )
        self._seen_urls: Set[str] = set()
        self._domain_counts: Dict[str, int] = defaultdict(int)
    
    async def call(
        self,
        action: str,
        search_results: List[Dict[str, Any]] = None,
        html: str = None,
        base_url: str = "",
        keywords: List[str] = None,
        max_urls: int = 50,
        filter_domain: str = None,
        url_type: str = "all",
        **kwargs
    ) -> ToolResult:
        """
        发现 URL
        
        Args:
            action: 操作类型 (discover/filter/categorize)
            search_results: 搜索结果列表
            html: HTML 内容
            base_url: 基础 URL（用于相对链接）
            keywords: 关键词过滤
            max_urls: 最大 URL 数量
            filter_domain: 过滤特定域名
            url_type: URL 类型过滤 (all/internal/external)
            
        Returns:
            ToolResult: 发现结果
        """
        start_time = time.time()
        
        try:
            if action == "discover":
                result = await self._discover_urls(
                    search_results=search_results,
                    html=html,
                    base_url=base_url,
                    keywords=keywords,
                    max_urls=max_urls,
                    url_type=url_type
                )
            elif action == "filter":
                urls = [r.get('url') for r in (search_results or []) if r.get('url')]
                result = await self._filter_urls(
                    urls=urls,
                    keywords=keywords,
                    filter_domain=filter_domain
                )
            elif action == "categorize":
                urls = [r.get('url') for r in (search_results or []) if r.get('url')]
                result = await self._categorize_urls(
                    urls=urls,
                    base_url=base_url
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown action: {action}",
                    execution_time=time.time() - start_time
                )
            
            return ToolResult(
                success=True,
                data=result if isinstance(result, dict) else result.__dict__,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"URL 发现失败: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _discover_urls(
        self,
        search_results: List[Dict[str, Any]],
        html: str,
        base_url: str,
        keywords: List[str],
        max_urls: int,
        url_type: str
    ) -> Dict[str, Any]:
        """从多个来源发现 URL"""
        
        discovered: List[DiscoveredURL] = []
        seen = set(self._seen_urls.copy())
        
        # 从搜索结果中发现
        if search_results:
            for result in search_results:
                url = result.get('url') or result.get('link', '')
                if not url:
                    continue
                
                if url in seen:
                    continue
                
                # 关键词过滤
                if keywords:
                    text = result.get('title', '') + ' ' + result.get('snippet', '')
                    if not any(kw.lower() in text.lower() for kw in keywords):
                        continue
                
                # URL 类型过滤
                parsed = urlparse(url)
                is_internal = parsed.netloc == urlparse(base_url).netloc if base_url else False
                
                if url_type == "internal" and not is_internal:
                    continue
                elif url_type == "external" and is_internal:
                    continue
                
                discovered.append(DiscoveredURL(
                    url=url,
                    source="search",
                    text=result.get('title', '')[:200],
                    domain=parsed.netloc,
                    url_type="internal" if is_internal else "external"
                ))
                seen.add(url)
                self._domain_counts[parsed.netloc] += 1
        
        # 从 HTML 中发现
        if html:
            html_urls = self._extract_urls_from_html(html, base_url)
            for url_info in html_urls:
                if url_info.url in seen:
                    continue
                
                if len(discovered) >= max_urls:
                    break
                
                discovered.append(url_info)
                seen.add(url_info.url)
                self._domain_counts[url_info.domain] += 1
        
        # 更新已见集合
        self._seen_urls.update(seen)
        
        return {
            "total_found": len(discovered),
            "urls": [d.__dict__ for d in discovered[:max_urls]],
            "domain_distribution": dict(self._domain_counts),
            "internal_count": sum(1 for d in discovered if d.url_type == "internal"),
            "external_count": sum(1 for d in discovered if d.url_type == "external")
        }
    
    def _extract_urls_from_html(self, html: str, base_url: str) -> List[DiscoveredURL]:
        """从 HTML 中提取 URL"""
        
        urls: List[DiscoveredURL] = []
        seen = set()
        
        # 使用正则提取链接
        pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>'
        
        for match in re.finditer(pattern, html, re.IGNORECASE):
            url = match.group(1)
            text = match.group(2).strip()[:200]
            
            # 过滤无效链接
            if not url or url.startswith(('javascript:', '#', 'mailto:', 'tel:')):
                continue
            
            # 转换为绝对 URL
            if base_url and not url.startswith('http'):
                url = urljoin(base_url, url)
            
            # 去重
            if url in seen:
                continue
            seen.add(url)
            
            parsed = urlparse(url)
            
            urls.append(DiscoveredURL(
                url=url,
                source="html",
                text=text,
                domain=parsed.netloc,
                url_type="internal" if parsed.netloc == urlparse(base_url).netloc else "external"
            ))
        
        return urls
    
    async def _filter_urls(
        self,
        urls: List[str],
        keywords: List[str],
        filter_domain: str
    ) -> Dict[str, Any]:
        """过滤 URL"""
        
        filtered = []
        removed = []
        
        for url in urls:
            parsed = urlparse(url)
            
            # 域名过滤
            if filter_domain and filter_domain not in parsed.netloc:
                removed.append({"url": url, "reason": "domain_mismatch"})
                continue
            
            # 关键词过滤
            if keywords:
                url_text = url.lower()
                if not any(kw.lower() in url_text for kw in keywords):
                    removed.append({"url": url, "reason": "no_keyword_match"})
                    continue
            
            filtered.append(url)
        
        return {
            "original_count": len(urls),
            "filtered_count": len(filtered),
            "filtered": filtered[:50],
            "removed": removed[:20]
        }
    
    async def _categorize_urls(
        self,
        urls: List[str],
        base_url: str
    ) -> Dict[str, Any]:
        """分类 URL"""
        
        categories = {
            "internal": [],
            "external": [],
            "resource": [],  # 图片/CSS/JS
            "social": [],    # 社交媒体
            "news": [],     # 新闻
            "blog": [],     # 博客
            "unknown": []
        }
        
        base_domain = urlparse(base_url).netloc if base_url else ""
        
        for url in urls:
            parsed = urlparse(url)
            
            # 判断类型
            url_type = "unknown"
            
            if parsed.netloc == base_domain:
                url_type = "internal"
            elif any(ext in parsed.path.lower() for ext in ['.jpg', '.png', '.css', '.js', '.svg', '.ico']):
                url_type = "resource"
            elif any(domain in parsed.netloc for domain in ['twitter.com', 'facebook.com', 'linkedin.com', 'weibo.com', 'zhihu.com']):
                url_type = "social"
            elif any(domain in parsed.netloc for domain in ['news.', 'bbc.com', 'reuters.com', '36kr.com']):
                url_type = "news"
            elif any(domain in parsed.netloc for domain in ['blog.', '.blogspot', '.medium.com']):
                url_type = "blog"
            else:
                url_type = "external"
            
            categories[url_type].append({
                "url": url,
                "domain": parsed.netloc,
                "path": parsed.path
            })
        
        return {
            "categories": {k: v[:20] for k, v in categories.items()},
            "total": len(urls),
            "distribution": {k: len(v) for k, v in categories.items()}
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_discovered": len(self._seen_urls),
            "domain_count": len(self._domain_counts),
            "top_domains": sorted(
                self._domain_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    
    def reset(self):
        """重置内部状态"""
        self._seen_urls.clear()
        self._domain_counts.clear()
