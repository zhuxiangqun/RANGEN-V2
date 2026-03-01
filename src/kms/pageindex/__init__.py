"""
PageIndex: Vectorless, Reasoning-based RAG for RANGEN

基于PageIndex框架的推理式检索增强生成系统
- 无需向量数据库
- 无需分块
- LLM推理式树搜索

核心思想：像人类专家一样导航文档结构
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class DocumentFormat(Enum):
    """文档格式"""
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"


@dataclass
class TreeNode:
    """
    树节点 - 文档的层次化表示
    
    类似"目录"但为LLM优化，包含:
    - node_id: 节点唯一标识
    - title: 章节标题
    - summary: 内容摘要
    - start_index/end_index: 页面范围
    - sub_nodes: 子节点
    """
    node_id: str
    title: str
    summary: str = ""
    start_index: int = 0
    end_index: int = 0
    level: int = 0
    content: str = ""  # 原始内容
    sub_nodes: List['TreeNode'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "node_id": self.node_id,
            "title": self.title,
            "summary": self.summary,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "level": self.level,
            "content": self.content if self.content else "",  # Full content for retrieval
            "nodes": [node.to_dict() for node in self.sub_nodes],
            "metadata": self.metadata
        }
    
    @property
    def page_range(self) -> str:
        """页面范围字符串"""
        if self.start_index == self.end_index:
            return f"Page {self.start_index}"
        return f"Pages {self.start_index}-{self.end_index}"
    
    def find_node(self, node_id: str) -> Optional['TreeNode']:
        """根据ID查找节点"""
        if self.node_id == node_id:
            return self
        for child in self.sub_nodes:
            found = child.find_node(node_id)
            if found:
                return found
        return None
    
    def get_all_nodes(self) -> List['TreeNode']:
        """获取所有节点"""
        nodes = [self]
        for child in self.sub_nodes:
            nodes.extend(child.get_all_nodes())
        return nodes


@dataclass
class RetrievalResult:
    """检索结果"""
    node_id: str
    title: str
    content: str
    page_range: str
    relevance_score: float = 0.0
    reasoning: str = ""  # LLM推理过程
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PageIndexConfig:
    """PageIndex配置"""
    # 模型配置
    model: str = "deepseek-chat"
    temperature: float = 0.0
    max_tokens: int = 4000
    
    # 索引配置
    max_pages_per_node: int = 10
    max_tokens_per_node: int = 20000
    toc_check_pages: int = 20  # 检查目录的页数
    
    # 检索配置
    top_k: int = 5
    reasoning_depth: int = 3  # 树搜索深度
    
    # 存储配置
    index_storage_path: str = "./data/pageindex"
    
    # 启用功能
    add_node_id: bool = True
    add_node_summary: bool = True
    add_doc_description: bool = True


class DocumentParser:
    """
    文档解析器
    
    支持解析PDF、Markdown、HTML等格式
    """
    
    def __init__(self):
        self._pdf_available = self._check_pdf()
    
    def _check_pdf(self) -> bool:
        """检查PDF库可用性"""
        try:
            import pypdf
            return True
        except ImportError:
            logger.warning("pypdf not installed. Install with: pip install pypdf")
            return False
    
    async def parse(self, file_path: str) -> Dict[str, Any]:
        """
        解析文档
        
        Returns:
            {
                "text": str,  # 完整文本
                "pages": List[str],  # 按页分割
                "headings": List[Dict],  # 提取的标题
                "metadata": Dict  # 元数据
            }
        """
        ext = Path(file_path).suffix.lower()
        
        if ext == ".pdf":
            return await self._parse_pdf(file_path)
        elif ext == ".md":
            return await self._parse_markdown(file_path)
        elif ext == ".txt":
            return await self._parse_text(file_path)
        elif ext == ".html":
            return await self._parse_html(file_path)
        else:
            raise ValueError(f"Unsupported format: {ext}")
    
    async def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """解析PDF"""
        if not self._pdf_available:
            # 尝试使用其他库
            try:
                import fitz  # PyMuPDF
                return await self._parse_pdf_pymupdf(file_path)
            except ImportError:
                raise ImportError("Please install pypdf or PyMuPDF: pip install pypdf PyMuPDF")
        
        from pypdf import PdfReader
        
        reader = PdfReader(file_path)
        pages = []
        full_text = []
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            pages.append(text)
            full_text.append(text)
        
        # 提取标题（简化版：假设加粗文本或大字体为标题）
        headings = self._extract_headings(pages)
        
        return {
            "text": "\n\n".join(full_text),
            "pages": pages,
            "headings": headings,
            "metadata": {
                "num_pages": len(pages),
                "source": file_path
            }
        }
    
    async def _parse_pdf_pymupdf(self, file_path: str) -> Dict[str, Any]:
        """使用PyMuPDF解析PDF"""
        import fitz
        
        doc = fitz.open(file_path)
        pages = []
        headings = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            pages.append(text)
            
            # 提取标题（基于字体大小）
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if span["size"] > 12:  # 假设大字体为标题
                                headings.append({
                                    "text": span["text"].strip(),
                                    "page": page_num + 1,
                                    "level": self._guess_heading_level(span["text"])
                                })
        
        return {
            "text": "\n\n".join(pages),
            "pages": pages,
            "headings": headings,
            "metadata": {
                "num_pages": len(pages),
                "source": file_path
            }
        }
    
    async def _parse_markdown(self, file_path: str) -> Dict[str, Any]:
        """解析Markdown"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        pages = []
        current_page = []
        headings = []
        page_num = 1
        
        for line in lines:
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                headings.append({
                    "text": line.lstrip('#').strip(),
                    "page": page_num,
                    "level": level
                })
            
            # 简单的分页：每30行作为一页
            current_page.append(line)
            if len(current_page) >= 30:
                pages.append('\n'.join(current_page))
                current_page = []
                page_num += 1
        
        if current_page:
            pages.append('\n'.join(current_page))
        
        return {
            "text": content,
            "pages": pages,
            "headings": headings,
            "metadata": {
                "num_pages": len(pages),
                "source": file_path
            }
        }
    
    async def _parse_text(self, file_path: str) -> Dict[str, Any]:
        """解析纯文本"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简单分页
        lines = content.split('\n')
        pages = []
        for i in range(0, len(lines), 30):
            pages.append('\n'.join(lines[i:i+30]))
        
        return {
            "text": content,
            "pages": pages,
            "headings": [],
            "metadata": {
                "num_pages": len(pages),
                "source": file_path
            }
        }
    
    async def _parse_html(self, file_path: str) -> Dict[str, Any]:
        """解析HTML"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("Please install beautifulsoup4: pip install beautifulsoup4")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # 提取文本
        text = soup.get_text(separator='\n\n')
        headings = []
        
        for i, tag in enumerate(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])):
            level = int(tag.name[1])
            headings.append({
                "text": tag.get_text().strip(),
                "page": i // 10 + 1,
                "level": level
            })
        
        # 分页
        lines = text.split('\n')
        pages = []
        for i in range(0, len(lines), 30):
            pages.append('\n'.join(lines[i:i+30]))
        
        return {
            "text": text,
            "pages": pages,
            "headings": headings,
            "metadata": {
                "num_pages": len(pages),
                "source": file_path
            }
        }
    
    def _extract_headings(self, pages: List[str]) -> List[Dict]:
        """从页面提取标题"""
        headings = []
        
        for page_num, page in enumerate(pages):
            lines = page.split('\n')
            for line in lines:
                line = line.strip()
                # 检测Markdown标题 (#, ##, ###)
                if line.startswith('#'):
                    level = len(line) - len(line.lstrip('#'))
                    text = line.lstrip('#').strip()
                    if text:
                        headings.append({
                            "text": text,
                            "page": page_num + 1,
                            "level": level
                        })
        
        return headings
        """从页面提取标题（简化版）"""
        headings = []
        
        # 这里可以使用更复杂的逻辑，如字体大小检测
        # 简化：假设全大写或以数字开头的行是标题
        for page_num, page in enumerate(pages):
            lines = page.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line.isupper() or line.startswith(('1.', '2.', '3.'))):
                    headings.append({
                        "text": line,
                        "page": page_num + 1,
                        "level": 1
                    })
        
        return headings
    
    def _guess_heading_level(self, text: str) -> int:
        """猜测标题级别"""
        # 简化逻辑
        return 1


class TreeBuilder:
    """
    树结构构建器
    
    将文档转换为层次化树结构
    """
    
    def __init__(self, config: PageIndexConfig, llm_client: Optional[Callable] = None):
        self.config = config
        self.llm_client = llm_client
        self._node_counter = 0
    
    def _generate_node_id(self) -> str:
        """生成节点ID"""
        self._node_counter += 1
        return f"{self._node_counter:04d}"
    
    async def build_tree(
        self, 
        parsed_doc: Dict[str, Any],
        document_description: str = ""
    ) -> TreeNode:
        """
        构建树结构
        
        使用LLM为每个节点生成摘要
        """
        pages = parsed_doc["pages"]
        headings = parsed_doc["headings"]
        num_pages = len(pages)
        
        # 构建初始结构（基于标题）
        root = TreeNode(
            node_id="0000",
            title=Path(parsed_doc["metadata"]["source"]).stem,
            level=0,
            start_index=1,
            end_index=num_pages
        )
        
        # 如果有标题，使用标题构建树
        if headings:
            root = await self._build_tree_from_headings(
                pages, headings, root, document_description
            )
        else:
            # 无标题：自动生成分层结构
            root = await self._build_tree_auto(pages, root, document_description)
        
        # 生成所有节点摘要
        if self.llm_client and self.config.add_node_summary:
            await self._generate_summaries(root, pages)
        
        return root
    
    async def _build_tree_from_headings(
        self,
        pages: List[str],
        headings: List[Dict],
        root: TreeNode,
        document_description: str
    ) -> TreeNode:
        """基于标题构建树"""
        
        if not headings:
            return root
        
        # 按页码分组标题
        heading_by_page = {}
        for h in headings:
            page = h["page"]
            if page not in heading_by_page:
                heading_by_page[page] = []
            heading_by_page[page].append(h)
        
        # 构建节点
        current_level1 = None
        
        # 简化：把所有内容放到根节点
        all_content = "\n\n".join(pages)
        root.content = all_content[:self.config.max_tokens_per_node]
        
        for page_num in range(1, len(pages) + 1):
            page_headings = heading_by_page.get(page_num, [])
            
            for h in page_headings:
                level = h.get("level", 1)
                text = h["text"]
                
                if level == 1:
                    # 一级标题
                    node = TreeNode(
                        node_id=self._generate_node_id(),
                        title=text,
                        level=1,
                        start_index=page_num,
                        end_index=page_num
                    )
                    root.sub_nodes.append(node)
                    current_level1 = node
                    current_level2 = None
                    
                elif level == 2 and current_level1:
                    # 二级标题
                    node = TreeNode(
                        node_id=self._generate_node_id(),
                        title=text,
                        level=2,
                        start_index=page_num,
                        end_index=page_num
                    )
                    current_level1.sub_nodes.append(node)
                    current_level2 = node
                    
                elif level >= 3 and current_level2:
                    # 三级及以下
                    node = TreeNode(
                        node_id=self._generate_node_id(),
                        title=text,
                        level=level,
                        start_index=page_num,
                        end_index=page_num
                    )
                    current_level2.sub_nodes.append(node)
        
        # 更新end_index
        self._update_end_indices(root, len(pages))
        
        return root
    
    async def _build_tree_auto(
        self,
        pages: List[str],
        root: TreeNode,
        document_description: str
    ) -> TreeNode:
        """自动构建树（无标题时）"""
        
        # 将每页作为一个节点
        for page_num, page_text in enumerate(pages, 1):
            node = TreeNode(
                node_id=self._generate_node_id(),
                title=f"Page {page_num}",
                level=1,
                start_index=page_num,
                end_index=page_num,
                content=page_text[:500]  # 截取
            )
            root.sub_nodes.append(node)
        
        return root
    
    def _update_end_indices(self, node: TreeNode, total_pages: int):
        """更新节点的结束页码"""
        if not node.sub_nodes:
            return
        
        for i, child in enumerate(node.sub_nodes):
            self._update_end_indices(child, total_pages)
            
            # 设置结束页码
            if i < len(node.sub_nodes) - 1:
                child.end_index = node.sub_nodes[i + 1].start_index - 1
            else:
                child.end_index = total_pages
    
    async def _generate_summaries(self, root: TreeNode, pages: List[str]):
        """为所有节点生成摘要"""
        
        async def process_node(node: TreeNode):
            if node.content:
                # 已经提取了内容
                return
            
            # 收集节点覆盖的页面内容
            page_contents = []
            for page_num in range(node.start_index, node.end_index + 1):
                if page_num <= len(pages):
                    page_contents.append(pages[page_num - 1])
            
            full_content = "\n\n".join(page_contents)
            
            if len(full_content) < 50:
                node.summary = full_content
                node.content = full_content
                return
            
            # 截取内容（避免超出token限制）
            truncated = full_content[:self.config.max_tokens_per_node]
            node.content = truncated
            
            # 生成摘要
            if self.llm_client:
                prompt = f"""请为以下文档内容生成简洁的摘要（50-100字）:

标题: {node.title}
内容:
{truncated}

摘要:"""
                
                try:
                    response = await self.llm_client(prompt)
                    node.summary = response.strip()
                except Exception as e:
                    logger.warning(f"生成摘要失败: {e}")
                    node.summary = truncated[:200]
            else:
                node.summary = truncated[:200]
            
            # 递归处理子节点
            for child in node.sub_nodes:
                await process_node(child)
        
        await process_node(root)


class ReasoningRetriever:
    """
    推理式检索器
    
    使用LLM推理在树结构中导航，找到相关内容
    """
    
    def __init__(self, tree: TreeNode, config: PageIndexConfig, llm_client: Optional[Callable] = None):
        self.tree = tree
        self.config = config
        self.llm_client = llm_client
    
    async def retrieve(
        self,
        query: str,
        top_k: int = None
    ) -> List[RetrievalResult]:
        """
        推理式检索
        
        1. 从根节点开始
        2. LLM判断哪些子节点相关
        3. 深入相关节点
        4. 重复直到找到足够内容
        """
        if top_k is None:
            top_k = self.config.top_k
        
        if not self.llm_client:
            top_k = self.config.top_k
        
        results = []
        
        if not self.llm_client:
            # 无LLM：使用简单的文本匹配
            return await self._simple_retrieve(query, top_k)
        
        # 使用LLM进行推理检索
        return await self._reasoning_retrieve(query, top_k)
    
    async def _simple_retrieve(self, query: str, top_k: int) -> List[RetrievalResult]:
        """简单检索（无LLM时）- 使用词级匹配和评分"""
        import re
        from collections import Counter
        
        results = []
        
        # 提取查询词（去除停用词和短词）
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 
                     'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
                     'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
                     'into', 'through', 'during', 'before', 'after', 'above', 'below',
                     'between', 'under', 'again', 'further', 'then', 'once', 'here',
                     'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
                     'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
                     'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't',
                     'just', 'don', 'now', 'if', 'and', 'or', 'but', 'what', 'which',
                     'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'it'}
        
        # 提取有意义的查询词
        query_words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{2,}\b', query)]
        query_words = [w for w in query_words if w not in stop_words]
        
        if not query_words:
            return []
        
        for node in self.tree.get_all_nodes():
            if not node.content:
                continue
            
            content_lower = node.content.lower()
            
            # 计算匹配分数
            matched_words = sum(1 for w in query_words if w in content_lower)
            score = matched_words / len(query_words)
            
            if score > 0:
                # 提取匹配片段
                matched_contexts = []
                for word in query_words:
                    if word in content_lower:
                        idx = content_lower.find(word)
                        start = max(0, idx - 50)
                        end = min(len(node.content), idx + len(word) + 50)
                        matched_contexts.append(node.content[start:end])
                
                results.append(RetrievalResult(
                    node_id=node.node_id,
                    title=node.title,
                    content=node.content,
                    page_range=node.page_range,
                    relevance_score=score,
                    reasoning=f"Matched {matched_words}/{len(query_words)} query words"
                ))
        
        # 按分数排序
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:top_k]
    
    async def _reasoning_retrieve(self, query: str, top_k: int) -> List[RetrievalResult]:
    
    async def _reasoning_retrieve(self, query: str, top_k: int) -> List[RetrievalResult]:
        """基于LLM推理的检索"""
        
        # 构建树结构摘要（用于推理）
        tree_summary = self._build_tree_summary(self.tree)
        
        # LLM提示词
        prompt = f"""你是一个专业的文档检索专家。用户有一个问题，你需要判断文档的哪些部分可能包含答案。

问题: {query}

文档结构:
{tree_summary}

请分析文档结构，找出最可能包含答案的节点ID列表。
按相关性排序，最多返回{top_k}个节点。
每个节点用以下格式返回:
[node_id] - 原因简短说明

只返回节点ID列表，不要其他内容。"""
        
        try:
            results = []
            
            response = await self.llm_client(prompt)
            response = await self.llm_client(prompt)
            
            # 解析响应，提取节点ID
            relevant_ids = self._parse_llm_response(response)
            
            # 获取节点内容
            for node_id in relevant_ids[:top_k]:
                node = self.tree.find_node(node_id)
                if node:
                    results.append(RetrievalResult(
                        node_id=node.node_id,
                        title=node.title,
                        content=node.content or self._get_node_content(node),
                        page_range=node.page_range,
                        relevance_score=1.0 - (len(results) * 0.1),
                        reasoning=f"LLM identified as relevant"
                    ))
            
            # 如果没有找到足够的节点，添加一些备用节点
            if len(results) < top_k:
                for node in self.tree.get_all_nodes():
                    if node.node_id not in relevant_ids and len(results) < top_k:
                        results.append(RetrievalResult(
                            node_id=node.node_id,
                            title=node.title,
                            content=self._get_node_content(node),
                            page_range=node.page_range,
                            relevance_score=0.3,
                            reasoning="Additional context"
                        ))
        
        except Exception as e:
            logger.warning(f"LLM推理检索失败: {e}")
            # 回退到简单检索
            return await self._simple_retrieve(query, top_k)
        
        return results[:top_k]
    
    def _build_tree_summary(self, node: TreeNode, max_depth: int = 3) -> str:
        """构建树结构摘要"""
        lines = []
        
        def add_node(n: TreeNode, indent: int = 0):
            if indent > max_depth:
                return
            
            prefix = "  " * indent
            summary = n.summary[:100] if n.summary else ""
            lines.append(f"{prefix}[{n.node_id}] {n.title} - {summary}")
            
            for child in n.sub_nodes:
                add_node(child, indent + 1)
        
        add_node(node)
        return "\n".join(lines)
    
    def _parse_llm_response(self, response: str) -> List[str]:
        """解析LLM响应，提取节点ID"""
        import re
        
        # 匹配 [xxxx] 格式的节点ID
        pattern = r'\[(\d+)\]'
        matches = re.findall(pattern, response)
        
        # 转换为完整ID格式
        node_ids = []
        for match in matches:
            # 补齐前导零到4位
            node_id = match.zfill(4)
            node_ids.append(node_id)
        
        return node_ids
    
    def _get_node_content(self, node: TreeNode) -> str:
        """获取节点内容"""
        if node.content:
            return node.content
        
        # 如果没有预提取的内容，收集子节点内容
        contents = []
        for child in node.sub_nodes:
            content = self._get_node_content(child)
            if content:
                contents.append(content)
        
        return "\n\n".join(contents)


class PageIndex:
    """
    PageIndex主类
    
    整合文档解析、树构建、推理检索
    """
    
    def __init__(
        self,
        config: Optional[PageIndexConfig] = None,
        llm_client: Optional[Callable] = None
    ):
        self.config = config or PageIndexConfig()
        self.llm_client = llm_client
        self.parser = DocumentParser()
        self.tree_builder = TreeBuilder(self.config, llm_client)
        self._indexes: Dict[str, TreeNode] = {}  # document_path -> tree
    
    async def index_document(
        self,
        document_path: str,
        document_description: str = ""
    ) -> TreeNode:
        """
        为文档建立索引
        
        1. 解析文档
        2. 构建树结构
        3. 存储索引
        """
        logger.info(f"Indexing document: {document_path}")
        
        # 解析文档
        parsed = await self.parser.parse(document_path)
        
        # 构建树
        tree = await self.tree_builder.build_tree(parsed, document_description)
        
        # 存储索引
        self._indexes[document_path] = tree
        
        # 保存到文件
        await self._save_index(tree, document_path)
        
        logger.info(f"Document indexed: {len(tree.get_all_nodes())} nodes")
        
        return tree
    
    async def retrieve(
        self,
        query: str,
        document_path: Optional[str] = None,
        top_k: int = None
    ) -> List[RetrievalResult]:
        """
        检索
        
        Args:
            query: 查询问题
            document_path: 可选，指定文档路径
            top_k: 返回结果数量
        """
        if document_path:
            # 检索指定文档
            tree = self._indexes.get(document_path)
            if not tree:
                raise ValueError(f"Document not indexed: {document_path}")
            
            retriever = ReasoningRetriever(tree, self.config, self.llm_client)
            return await retriever.retrieve(query, top_k)
        else:
            # 检索所有文档
            all_results = []
            
            for doc_path, tree in self._indexes.items():
                retriever = ReasoningRetriever(tree, self.config, self.llm_client)
                results = await retriever.retrieve(query, top_k)
                
                for r in results:
                    r.metadata["document"] = doc_path
                
                all_results.extend(results)
            
            # 按相关性排序
            all_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return all_results[:top_k or self.config.top_k]
    
    async def _save_index(self, tree: TreeNode, document_path: str):
        """保存索引到文件"""
        os.makedirs(self.config.index_storage_path, exist_ok=True)
        
        # 使用文档名作为索引文件名
        doc_name = Path(document_path).stem
        index_file = Path(self.config.index_storage_path) / f"{doc_name}.json"
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(tree.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Index saved to: {index_file}")
    
    async def load_index(self, document_path: str) -> TreeNode:
        """加载索引"""
        doc_name = Path(document_path).stem
        index_file = Path(self.config.index_storage_path) / f"{doc_name}.json"
        
        if not index_file.exists():
            raise FileNotFoundError(f"Index not found: {index_file}")
        
        with open(index_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tree = self._dict_to_tree(data)
        self._indexes[document_path] = tree
        
        return tree

    async def load_all_indexes(self) -> int:
        """加载所有索引文件"""
        storage_path = Path(self.config.index_storage_path)
        if not storage_path.exists():
            logger.warning(f"Index storage path not found: {storage_path}")
            return 0
        
        count = 0
        for fpath in storage_path.glob("*.json"):
            try:
                await self.load_index(str(fpath))
                count += 1
            except Exception as e:
                logger.warning(f"Failed to load index {fpath}: {e}")
        
        logger.info(f"Loaded {count} indexes from {storage_path}")
        return count
    
    def _dict_to_tree(self, data: Dict) -> TreeNode:
        """将字典转换为TreeNode"""
        node = TreeNode(
            node_id=data["node_id"],
            title=data["title"],
            summary=data.get("summary", ""),
            start_index=data.get("start_index", 0),
            end_index=data.get("end_index", 0),
            level=data.get("level", 0),
            content=data.get("content", ""),
            metadata=data.get("metadata", {})
        )
        
        for child_data in data.get("nodes", []):
            child = self._dict_to_tree(child_data)
            node.sub_nodes.append(child)
        
        return node
    
    def get_indexed_documents(self) -> List[str]:
        """获取已索引的文档列表"""
        return list(self._indexes.keys())


# ==================== 便捷函数 ====================

_pageindex_instance: Optional[PageIndex] = None


def get_pageindex(
    config: Optional[PageIndexConfig] = None,
    llm_client: Optional[Callable] = None
) -> PageIndex:
    """获取PageIndex实例"""
    global _pageindex_instance
    if _pageindex_instance is None:
        _pageindex_instance = PageIndex(config, llm_client)
    return _pageindex_instance
