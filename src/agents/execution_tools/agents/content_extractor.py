#!/usr/bin/env python3
"""
Content Extractor Tool - 内容提取工具

从 HTML 中提取结构化内容：标题、正文、链接、图片等
"""

import re
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .base_tool import BaseTool, ToolResult


@dataclass
class ExtractedContent:
    """提取的内容"""
    title: str
    text: str
    links: List[Dict[str, str]]
    images: List[str]
    meta: Dict[str, str]
    word_count: int
    html_length: int


class ContentExtractor(BaseTool):
    """
    内容提取工具
    
    从 HTML 中提取结构化内容，用于数据采集工作流
    """
    
    def __init__(self):
        super().__init__(
            tool_name="content_extractor",
            description="从 HTML 中提取结构化内容：标题、正文、链接、图片等"
        )
    
    async def call(
        self,
        html: str,
        extract_links: bool = True,
        extract_images: bool = True,
        extract_meta: bool = True,
        min_text_length: int = 100,
        **kwargs
    ) -> ToolResult:
        """
        提取 HTML 内容
        
        Args:
            html: HTML 内容
            extract_links: 是否提取链接
            extract_images: 是否提取图片
            extract_meta: 是否提取 meta 信息
            min_text_length: 最小文本长度（用于过滤噪音）
            
        Returns:
            ToolResult: 提取结果
        """
        start_time = time.time()
        
        try:
            result = self._extract_content(
                html=html,
                extract_links=extract_links,
                extract_images=extract_images,
                extract_meta=extract_meta,
                min_text_length=min_text_length
            )
            
            return ToolResult(
                success=True,
                data=result.__dict__,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"内容提取失败: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _extract_content(
        self,
        html: str,
        extract_links: bool,
        extract_images: bool,
        extract_meta: bool,
        min_text_length: int
    ) -> ExtractedContent:
        """执行内容提取"""
        
        # 尝试使用 BeautifulSoup
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            use_bs4 = True
        except ImportError:
            use_bs4 = False
        
        if use_bs4:
            # 使用 BeautifulSoup 提取
            title = self._extract_title_bs4(soup)
            text = self._extract_text_bs4(soup)
            links = self._extract_links_bs4(soup) if extract_links else []
            images = self._extract_images_bs4(soup) if extract_images else []
            meta = self._extract_meta_bs4(soup) if extract_meta else {}
        else:
            # 使用正则表达式提取
            title = self._extract_title_regex(html)
            text = self._extract_text_regex(html)
            links = self._extract_links_regex(html) if extract_links else []
            images = self._extract_images_regex(html) if extract_images else []
            meta = self._extract_meta_regex(html) if extract_meta else {}
        
        # 过滤噪音内容
        if len(text) < min_text_length:
            text = self._clean_noise(text)
        
        return ExtractedContent(
            title=title,
            text=text.strip(),
            links=links,
            images=images,
            meta=meta,
            word_count=len(text.split()),
            html_length=len(html)
        )
    
    def _extract_title_bs4(self, soup) -> str:
        """BeautifulSoup 提取标题"""
        title = soup.title
        if title and title.string:
            return title.string.strip()
        
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()
        
        return ""
    
    def _extract_text_bs4(self, soup) -> str:
        """BeautifulSoup 提取正文"""
        # 移除噪音标签
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
            tag.decompose()
        
        # 获取主要文本区域
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|article|post'))
        
        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
        else:
            text = soup.get_text(separator=' ', strip=True)
        
        return self._normalize_text(text)
    
    def _extract_links_bs4(self, soup) -> List[Dict[str, str]]:
        """BeautifulSoup 提取链接"""
        links = []
        base_url = ""
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            
            # 过滤空链接和脚本链接
            if not href or href.startswith(('javascript:', '#', 'mailto:')):
                continue
            
            # 转换为绝对 URL
            if not href.startswith('http'):
                if base_url:
                    from urllib.parse import urljoin
                    href = urljoin(base_url, href)
            
            links.append({
                "text": a.get_text().strip()[:100],
                "url": href,
                "rel": a.get('rel', ['external'])[0] if a.get('rel') else 'external'
            })
        
        return links[:50]  # 限制数量
    
    def _extract_images_bs4(self, soup) -> List[str]:
        """BeautifulSoup 提取图片"""
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and not src.startswith(('data:', 'javascript:')):
                images.append(src)
        
        return images[:20]  # 限制数量
    
    def _extract_meta_bs4(self, soup) -> Dict[str, str]:
        """BeautifulSoup 提取 meta 信息"""
        meta = {}
        
        # 标准 meta
        for tag in soup.find_all('meta'):
            name = tag.get('name') or tag.get('property')
            content = tag.get('content', '')
            
            if name and content:
                meta[name] = content[:500]  # 限制长度
        
        return meta
    
    def _extract_title_regex(self, html: str) -> str:
        """正则表达式提取标题"""
        match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _extract_text_regex(self, html: str) -> str:
        """正则表达式提取文本"""
        # 移除脚本和样式
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # 移除标签
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 清理空白
        text = re.sub(r'\s+', ' ', text)
        
        return self._normalize_text(text)
    
    def _extract_links_regex(self, html: str) -> List[Dict[str, str]]:
        """正则表达式提取链接"""
        links = []
        pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>'
        
        for match in re.finditer(pattern, html, re.IGNORECASE):
            href = match.group(1)
            text = match.group(2).strip()[:100]
            
            if href and not href.startswith(('javascript:', '#', 'mailto:')):
                links.append({
                    "text": text,
                    "url": href,
                    "rel": "external"
                })
        
        return links[:50]
    
    def _extract_images_regex(self, html: str) -> List[str]:
        """正则表达式提取图片"""
        pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
        return [m.group(1) for m in re.finditer(pattern, html, re.IGNORECASE)][:20]
    
    def _extract_meta_regex(self, html: str) -> Dict[str, str]:
        """正则表达式提取 meta"""
        meta = {}
        pattern = r'<meta[^>]+(name|property)=["\']([^"\']+)["\'][^>]+content=["\']([^"\']+)["\']'
        
        for match in re.finditer(pattern, html, re.IGNORECASE):
            key = match.group(2)
            value = match.group(3)[:500]
            meta[key] = value
        
        return meta
    
    def _normalize_text(self, text: str) -> str:
        """规范化文本"""
        # 解码 HTML 实体
        import html as html_module
        text = html_module.unescape(text)
        
        # 清理空白
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _clean_noise(self, text: str) -> str:
        """清理噪音内容"""
        noise_patterns = [
            r'登录|注册|订阅|分享到|版权声明',
            r'更多精彩内容|相关新闻|推荐阅读',
            r'^\s*[$¥€£]\d+[\.\d]*\s*$',  # 价格
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text)
        
        return text.strip()
