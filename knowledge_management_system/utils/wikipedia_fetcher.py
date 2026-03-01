#!/usr/bin/env python3
"""
Wikipedia 内容抓取工具
用于从 Wikipedia URL 抓取页面内容
"""

import requests
import re
import time
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from urllib.parse import unquote, urlparse
from ..utils.logger import get_logger

logger = get_logger()


class WikipediaFetcher:
    """Wikipedia 内容抓取器"""
    
    def __init__(self):
        """初始化 Wikipedia 抓取器"""
        self.base_url = "https://en.wikipedia.org/api/rest_v1/page"
        self.session = requests.Session()
        # 🚀 改进 User-Agent（符合 Wikipedia 推荐格式）
        self.session.headers.update({
            'User-Agent': 'KnowledgeManagementSystem/1.0 (https://github.com/yourproject; contact@example.com) Wikipedia Content Fetcher'
        })
        self.request_delay = 0.1  # 🚀 性能优化：请求之间的延迟（秒），从0.2秒降低到0.1秒，进一步提升速度
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 2  # 重试延迟（秒）
    
    def _clean_url(self, url: str) -> Optional[str]:
        """
        清理和规范化 URL（处理格式异常）
        
        Args:
            url: 原始 URL（可能包含列表符号、引号等）
            
        Returns:
            清理后的 URL，如果无效则返回 None
        """
        if not url or not isinstance(url, str):
            return None
        
        # 移除列表符号和引号
        url = url.strip()
        url = url.strip("['\"]")  # 移除列表符号和引号
        url = url.strip()
        
        # 检查是否是有效的 Wikipedia URL
        if not url.startswith('http://') and not url.startswith('https://'):
            # 如果是相对路径或只有标题，尝试补全
            if url.startswith('wiki/') or url.startswith('/wiki/'):
                url = f"https://en.wikipedia.org{url}" if url.startswith('/') else f"https://en.wikipedia.org/{url}"
            elif not url.startswith('_') and not url.startswith('in%'):  # 过滤明显无效的URL片段
                # 尝试补全为标准 Wikipedia URL
                url = f"https://en.wikipedia.org/wiki/{url}"
            else:
                # 明显无效的URL
                return None
        
        # 确保是 Wikipedia URL
        if 'wikipedia.org' not in url.lower():
            return None
        
        return url
    
    def extract_title_from_url(self, url: str) -> Optional[str]:
        """
        从 Wikipedia URL 中提取页面标题
        
        Args:
            url: Wikipedia 页面 URL
            
        Returns:
            页面标题，如果无法提取则返回 None
        """
        try:
            # 🚀 先清理 URL
            cleaned_url = self._clean_url(url)
            if not cleaned_url:
                return None
            url = cleaned_url
            
            # 处理标准 Wikipedia URL
            # 例如: https://en.wikipedia.org/wiki/Article_Title
            if '/wiki/' in url:
                title = url.split('/wiki/')[-1]
                # 处理 URL 编码
                title = unquote(title)
                # 处理片段（#后面的部分）
                if '#' in title:
                    title = title.split('#')[0]
                # 处理查询参数
                if '?' in title:
                    title = title.split('?')[0]
                # 处理片段标识符（:~:text=）
                if ':' in title and '~' in title:
                    title = title.split(':~')[0]
                return title.strip()
            
            # 处理 API URL
            if '/page/' in url:
                parts = url.split('/page/')
                if len(parts) > 1:
                    title = parts[-1]
                    # 移除可能的查询参数
                    if '?' in title:
                        title = title.split('?')[0]
                    return unquote(title).strip()
            
            return None
            
        except Exception as e:
            logger.debug(f"从 URL 提取标题失败: {url}, 错误: {e}")
            return None
    
    def fetch_page_summary(self, url: str) -> Optional[Dict[str, Any]]:
        """
        抓取 Wikipedia 页面的摘要信息（快速方法）
        
        Args:
            url: Wikipedia 页面 URL
            
        Returns:
            包含标题、摘要、URL 的字典，失败返回 None
        """
        # 🚀 清理 URL
        cleaned_url = self._clean_url(url)
        if not cleaned_url:
            return None
        url = cleaned_url
        
        for attempt in range(self.max_retries):
            try:
                title = self.extract_title_from_url(url)
                if not title:
                    logger.warning(f"无法从 URL 提取标题: {url}")
                    return None
                
                # 使用 Wikipedia REST API 获取摘要
                summary_url = f"{self.base_url}/summary/{title}"
                response = self.session.get(summary_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'title': data.get('title', title),
                        'summary': data.get('extract', ''),
                        'url': data.get('content_urls', {}).get('desktop', {}).get('page', url),
                        'source': 'wikipedia_api_summary'
                    }
                elif response.status_code == 404:
                    logger.warning(f"Wikipedia 页面不存在: {title}")
                    return None
                elif response.status_code == 403:
                    # 🚀 403 错误：速率限制或访问被拒绝
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (attempt + 1)  # 递增延迟
                        logger.debug(f"遇到 403 错误，等待 {wait_time} 秒后重试 ({attempt + 1}/{self.max_retries})...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.warning(f"获取 Wikipedia 摘要失败 (状态码 403，可能是速率限制): {title}")
                        return None
                else:
                    logger.warning(f"获取 Wikipedia 摘要失败 (状态码 {response.status_code}): {title}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return None
                    
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    logger.debug(f"请求超时，等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                    continue
                logger.warning(f"抓取 Wikipedia 摘要超时: {url}")
                return None
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    logger.debug(f"请求异常，等待 {self.retry_delay} 秒后重试: {e}")
                    time.sleep(self.retry_delay)
                    continue
                logger.warning(f"抓取 Wikipedia 摘要失败: {url}, 错误: {e}")
                return None
            except Exception as e:
                logger.warning(f"处理 Wikipedia 摘要失败: {url}, 错误: {e}")
                return None
        
        return None
    
    def fetch_page_content(self, url: str, include_full_text: bool = True) -> Optional[Dict[str, Any]]:
        """
        抓取 Wikipedia 页面的完整内容
        
        Args:
            url: Wikipedia 页面 URL
            include_full_text: 是否抓取完整文本（否则只抓取摘要）
            
        Returns:
            包含标题、内容、摘要、URL 的字典，失败返回 None
        """
        # 🚀 清理 URL
        cleaned_url = self._clean_url(url)
        if not cleaned_url:
            return None
        url = cleaned_url
        
        try:
            title = self.extract_title_from_url(url)
            if not title:
                logger.warning(f"无法从 URL 提取标题: {url}")
                return None
            
            if not include_full_text:
                # 只抓取摘要（更快）
                return self.fetch_page_summary(url)
            
            # 使用 Wikipedia REST API 获取完整文本
            text_url = f"{self.base_url}/html/{title}"
            
            # 🚀 添加重试逻辑
            for attempt in range(self.max_retries):
                try:
                    response = self.session.get(text_url, timeout=15)
                    
                    if response.status_code == 200:
                        html_content = response.text
                        
                        # 提取文本内容（简单实现，可以改进）
                        # 移除 HTML 标签和脚本
                        text_content = self._extract_text_from_html(html_content)
                        
                        # 同时获取摘要
                        summary_data = self.fetch_page_summary(url)
                        summary = summary_data.get('summary', '') if summary_data else ''
                        
                        return {
                            'title': title,
                            'content': text_content,
                            'summary': summary,
                            'url': url,
                            'source': 'wikipedia_api_full'
                        }
                    elif response.status_code == 404:
                        logger.warning(f"Wikipedia 页面不存在: {title}")
                        return None
                    elif response.status_code == 403:
                        # 403 错误：速率限制
                        if attempt < self.max_retries - 1:
                            wait_time = self.retry_delay * (attempt + 1)
                            logger.debug(f"遇到 403 错误，等待 {wait_time} 秒后重试...")
                            time.sleep(wait_time)
                            continue
                        # 回退到摘要
                        logger.debug(f"获取 Wikipedia 完整内容失败（403），回退到摘要: {title}")
                        return self.fetch_page_summary(url)
                    else:
                        # 其他错误，回退到摘要
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                            continue
                        logger.debug(f"获取 Wikipedia 完整内容失败（状态码 {response.status_code}），回退到摘要: {title}")
                        return self.fetch_page_summary(url)
                        
                except requests.exceptions.Timeout:
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    # 超时，回退到摘要
                    return self.fetch_page_summary(url)
                except requests.exceptions.RequestException:
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    # 其他请求异常，回退到摘要
                    return self.fetch_page_summary(url)
            
            # 所有重试都失败，回退到摘要
            return self.fetch_page_summary(url)
                
        except Exception as e:
            logger.warning(f"处理 Wikipedia 内容失败: {url}, 错误: {e}")
            # 尝试获取摘要作为后备
            return self.fetch_page_summary(url)
    
    def _extract_text_from_html(self, html: str) -> str:
        """
        从 HTML 中提取文本内容（改进版：使用BeautifulSoup进行彻底清理）
        
        Args:
            html: HTML 内容
            
        Returns:
            提取的文本内容
        """
        try:
            # 🚀 改进：优先使用BeautifulSoup进行更彻底的清理
            try:
                from bs4 import BeautifulSoup
                from bs4 import Comment
                
                # 使用BeautifulSoup解析HTML
                soup = BeautifulSoup(html, 'lxml')
                
                # 移除脚本和样式
                for script in soup(["script", "style", "noscript"]):
                    script.decompose()
                
                # 移除引用标记（如 <sup>1</sup>）
                for sup in soup.find_all("sup"):
                    sup.decompose()
                
                # 移除注释
                for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                    comment.extract()
                
                # 移除所有HTML属性中的JSON数据（如 id="mwBXM"）
                for tag in soup.find_all():
                    # 移除所有属性
                    tag.attrs = {}
                
                # 提取文本
                text = soup.get_text(separator='\n')
                
            except ImportError:
                # 回退到原来的方法
                logger.debug("BeautifulSoup未安装，使用简单清理方法")
                # 移除脚本和样式
                html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
                html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
                
                # 移除 HTML 标签（保留段落结构）
                text = re.sub(r'<[^>]+>', '\n', html)
            
            # 🚀 改进：清理引用标记（如 [ 82 ], [ 83 ]）
            text = re.sub(r'\[\s*\d+\s*\]', '', text)
            
            # 🚀 改进：清理JSON属性残留（如 "}},"i":0}}]}' id="mwBXM"）
            # 匹配各种JSON属性格式
            text = re.sub(r'["\']?\}\},"[^"]*":\d+\}\}\}\]?["\']?\s*id=["\'][^"\']*["\']', '', text)
            text = re.sub(r'["\']?\}\},"[^"]*":\d+\}\}\}\]?["\']?', '', text)
            # 清理单独的id属性（如 id="mwBXM"）
            text = re.sub(r'\s*id=["\'][^"\']*["\']', '', text)
            # 清理JSON片段（如 "}},"i":0}}]}'）
            text = re.sub(r'["\']?\}\}[^"\']*["\']?', '', text)
            
            # 🚀 改进：清理HTML实体
            try:
                import html as html_module
                text = html_module.unescape(text)
            except Exception:
                pass
            
            # 🚀 改进：清理多余的空白字符
            lines = [line.strip() for line in text.split('\n')]
            lines = [line for line in lines if line]  # 移除空行
            text = '\n'.join(lines)
            
            # 清理多余的空白字符
            text = re.sub(r'[ \t]+', ' ', text)
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
            
            # 🚀 改进：增加长度限制（从50000增加到100000字符）
            max_length = 100000  # 增加到100000字符
            if len(text) > max_length:
                # 智能截断：保留开头和结尾
                truncate_marker = "\n\n[... 内容已截断 ...]\n\n"
                marker_length = len(truncate_marker)
                available_length = max_length - marker_length
                first_part = text[:available_length // 2]
                last_part = text[-(available_length // 2):]
                text = first_part + truncate_marker + last_part
            
            return text.strip()
            
        except Exception as e:
            logger.debug(f"HTML 文本提取失败: {e}")
            return ""
    
    def fetch_multiple_pages(
        self, 
        urls: List[str], 
        include_full_text: bool = True,  # ✅ 修改：默认抓取完整内容而非摘要
        deduplicate: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量抓取多个 Wikipedia 页面
        
        Args:
            urls: Wikipedia URL 列表
            include_full_text: 是否抓取完整文本
            deduplicate: 是否去重（基于 URL）
            
        Returns:
            抓取结果列表
        """
        # 🚀 清理和规范化所有 URL
        cleaned_urls = []
        for url in urls:
            if not url or not isinstance(url, str):
                continue
            cleaned = self._clean_url(url)
            if cleaned:
                cleaned_urls.append(cleaned)
        
        urls = cleaned_urls
        
        # 去重
        if deduplicate:
            seen_urls = set()
            unique_urls = []
            for url in urls:
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_urls.append(url)
            urls = unique_urls
        
        results = []
        total = len(urls)
        success_count = 0
        fail_count = 0
        
        logger.info(f"📥 开始批量抓取 {total} 个 Wikipedia 页面...")
        
        for i, url in enumerate(urls, 1):
            if not url:
                continue
            
            # 🚀 添加请求延迟，避免速率限制
            if i > 1:
                time.sleep(self.request_delay)
            
            logger.info(f"抓取 Wikipedia 页面 [{i}/{total}]: {url}")
            result = self.fetch_page_content(url, include_full_text=include_full_text)
            
            if result:
                results.append(result)
                success_count += 1
                logger.debug(f"✅ 成功抓取: {result.get('title', 'Unknown')}")
            else:
                fail_count += 1
                # 只在调试模式下记录详细失败信息，减少日志噪音
                logger.debug(f"❌ 抓取失败: {url}")
            
            # 每 50 个请求输出一次进度
            if i % 50 == 0:
                logger.info(f"📊 进度: {i}/{total} ({success_count} 成功, {fail_count} 失败)")
        
        logger.info(f"✅ 批量抓取完成: {success_count}/{total} 成功, {fail_count} 失败")
        return results
    
    async def fetch_multiple_pages_async(
        self, 
        urls: List[str], 
        include_full_text: bool = True,
        deduplicate: bool = True,
        max_concurrent: int = 10  # 🚀 性能优化：并发数，从5增加到10，提高抓取速度
    ) -> List[Dict[str, Any]]:
        """
        异步批量抓取多个 Wikipedia 页面（并发版本）
        
        Args:
            urls: Wikipedia URL 列表
            include_full_text: 是否抓取完整文本
            deduplicate: 是否去重（基于 URL）
            max_concurrent: 最大并发数
            
        Returns:
            抓取结果列表
        """
        # 🚀 清理和规范化所有 URL
        cleaned_urls = []
        for url in urls:
            if not url or not isinstance(url, str):
                continue
            cleaned = self._clean_url(url)
            if cleaned:
                cleaned_urls.append(cleaned)
        
        urls = cleaned_urls
        
        # 去重
        if deduplicate:
            seen_urls = set()
            unique_urls = []
            for url in urls:
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_urls.append(url)
            urls = unique_urls
        
        total = len(urls)
        if total == 0:
            return []
        
        logger.info(f"📥 开始异步批量抓取 {total} 个 Wikipedia 页面（并发数: {max_concurrent}）...")
        
        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_single_page(url: str, index: int) -> Optional[Dict[str, Any]]:
            """异步抓取单个页面"""
            async with semaphore:
                try:
                    # 添加小延迟避免速率限制
                    if index > 0:
                        await asyncio.sleep(self.request_delay)
                    
                    # 使用同步方法（因为fetch_page_content是同步的）
                    # 在线程池中执行以避免阻塞
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, 
                        self.fetch_page_content, 
                        url, 
                        include_full_text
                    )
                    return result
                except Exception as e:
                    logger.debug(f"❌ 异步抓取失败: {url}, 错误: {e}")
                    return None
        
        # 创建所有任务
        tasks = [fetch_single_page(url, i) for i, url in enumerate(urls)]
        
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        valid_results = []
        success_count = 0
        fail_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.debug(f"❌ 任务 {i+1} 异常: {result}")
                fail_count += 1
            elif result:
                valid_results.append(result)
                success_count += 1
            else:
                fail_count += 1
        
        logger.info(f"✅ 异步批量抓取完成: {success_count}/{total} 成功, {fail_count} 失败")
        return valid_results


# 单例实例
_wikipedia_fetcher_instance: Optional[WikipediaFetcher] = None


def get_wikipedia_fetcher() -> WikipediaFetcher:
    """
    获取 Wikipedia 抓取器实例（单例）
    
    Returns:
        WikipediaFetcher 实例
    """
    global _wikipedia_fetcher_instance
    if _wikipedia_fetcher_instance is None:
        _wikipedia_fetcher_instance = WikipediaFetcher()
    return _wikipedia_fetcher_instance

