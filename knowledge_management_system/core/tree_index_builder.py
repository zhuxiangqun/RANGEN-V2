#!/usr/bin/env python3
"""
树形索引构建器 (Tree Index Builder)
参考 PageIndex 框架 - 构建文档的层级树结构索引

核心功能:
1. 将文档解析为层级树结构 (类似目录)
2. 为每个节点生成摘要
3. 支持页面范围标记
4. 支持 Markdown 文件的标题层级解析

参考: https://github.com/VectifyAI/PageIndex
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger()


@dataclass
class TreeNode:
    """树节点 - 表示文档的一个章节/部分"""
    title: str
    node_id: str
    start_index: int  # 起始页码或字符位置
    end_index: int    # 结束页码或字符位置
    summary: str = ""  # 章节摘要 (由LLM生成)
    nodes: List['TreeNode'] = field(default_factory=list)  # 子节点
    level: int = 1  # 标题层级 (1, 2, 3, ...)
    content: str = ""  # 原始内容 (可选，用于检索)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "title": self.title,
            "node_id": self.node_id,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "summary": self.summary,
            "level": self.level,
        }
        if self.nodes:
            result["nodes"] = [node.to_dict() for node in self.nodes]
        if self.content:
            result["content"] = self.content
        return result
    
    def get_all_nodes(self) -> List['TreeNode']:
        """获取所有节点 (包括子节点)"""
        result = [self]
        for child in self.nodes:
            result.extend(child.get_all_nodes())
        return result
    
    def find_node_by_id(self, node_id: str) -> Optional['TreeNode']:
        """根据ID查找节点"""
        if self.node_id == node_id:
            return self
        for child in self.nodes:
            found = child.find_node_by_id(node_id)
            if found:
                return found
        return None
    
    def get_path(self) -> str:
        """获取节点路径"""
        return self.node_id


@dataclass
class DocumentIndex:
    """文档索引 - 包含完整文档的树形结构"""
    document_id: str
    title: str
    description: str = ""  # 文档描述
    total_pages: int = 0  # 总页数
    created_at: str = ""
    root: Optional[TreeNode] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "document_id": self.document_id,
            "title": self.title,
            "description": self.description,
            "total_pages": self.total_pages,
            "created_at": self.created_at,
        }
        if self.root:
            result["tree"] = self.root.to_dict()
        return result
    
    def get_all_nodes(self) -> List[TreeNode]:
        """获取所有节点"""
        if self.root:
            return self.root.get_all_nodes()
        return []
    
    def find_node(self, node_id: str) -> Optional[TreeNode]:
        """查找节点"""
        if self.root:
            return self.root.find_node_by_id(node_id)
        return None


class TreeIndexBuilder:
    """树形索引构建器 - 构建文档的层级树结构"""
    
    def __init__(
        self,
        index_path: str = "data/knowledge_management/tree_index",
        max_pages_per_node: int = 10,
        max_tokens_per_node: int = 20000,
        if_add_summary: bool = True,
        if_add_doc_description: bool = True,
    ):
        """
        初始化树形索引构建器
        
        Args:
            index_path: 索引保存路径
            max_pages_per_node: 每个节点最大页数
            max_tokens_per_node: 每个节点最大token数
            if_add_summary: 是否添加节点摘要
            if_add_doc_description: 是否添加文档描述
        """
        self.logger = logger
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.max_pages_per_node = max_pages_per_node
        self.max_tokens_per_node = max_tokens_per_node
        self.if_add_summary = if_add_summary
        self.if_add_doc_description = if_add_doc_description
        
        # 索引存储
        self.indices: Dict[str, DocumentIndex] = {}
        
        # LLM服务 (用于生成摘要)
        self.llm_service = None
        
        # 加载现有索引
        self._load_indices()
    
    def _load_indices(self):
        """加载现有索引"""
        if self.index_path.exists() and self.index_path.is_dir():
            for json_file in self.index_path.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        doc_index = self._dict_to_document_index(data)
                        self.indices[doc_index.document_id] = doc_index
                        self.logger.debug(f"加载树索引: {doc_index.document_id}")
                except Exception as e:
                    self.logger.warning(f"加载索引失败 {json_file}: {e}")
    
    def _dict_to_document_index(self, data: Dict[str, Any]) -> DocumentIndex:
        """将字典转换为DocumentIndex"""
        doc_index = DocumentIndex(
            document_id=data.get("document_id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            total_pages=data.get("total_pages", 0),
            created_at=data.get("created_at", ""),
        )
        if "tree" in data:
            doc_index.root = self._dict_to_tree_node(data["tree"])
        return doc_index
    
    def _dict_to_tree_node(self, data: Dict[str, Any]) -> TreeNode:
        """将字典转换为TreeNode"""
        node = TreeNode(
            title=data.get("title", ""),
            node_id=data.get("node_id", ""),
            start_index=data.get("start_index", 0),
            end_index=data.get("end_index", 0),
            summary=data.get("summary", ""),
            level=data.get("level", 1),
            content=data.get("content", ""),
        )
        if "nodes" in data:
            node.nodes = [self._dict_to_tree_node(n) for n in data["nodes"]]
        return node
    
    def _save_index(self, doc_index: DocumentIndex):
        """保存索引到文件"""
        file_path = self.index_path / f"{doc_index.document_id}.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(doc_index.to_dict(), f, ensure_ascii=False, indent=2)
            self.logger.info(f"保存树索引: {doc_index.document_id}")
        except Exception as e:
            self.logger.error(f"保存索引失败: {e}")
    
    def set_llm_service(self, llm_service):
        """设置LLM服务 (用于生成摘要)"""
        self.llm_service = llm_service
    
    def build_from_markdown(
        self,
        document_id: str,
        title: str,
        markdown_content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentIndex:
        """
        从Markdown内容构建树索引
        
        Args:
            document_id: 文档ID
            title: 文档标题
            markdown_content: Markdown内容
            metadata: 额外元数据
            
        Returns:
            DocumentIndex 对象
        """
        self.logger.info(f"从Markdown构建树索引: {document_id}")
        
        # 解析Markdown标题层级
        headings = self._parse_markdown_headings(markdown_content)
        
        if not headings:
            # 没有标题，创建一个根节点包含全部内容
            root = TreeNode(
                title=title,
                node_id="0001",
                start_index=0,
                end_index=len(markdown_content),
                level=0,
                content=markdown_content[:5000]  # 截取部分内容
            )
            
            # 如果有LLM服务，生成摘要
            if self.if_add_summary and self.llm_service:
                root.summary = self._generate_summary(root.content)
        else:
            # 构建树结构
            root = self._build_tree_from_headings(headings, markdown_content, title)
        
        # 创建文档索引
        doc_index = DocumentIndex(
            document_id=document_id,
            title=title,
            total_pages=max(1, len(markdown_content) // 2000),  # 估算页数
            created_at=datetime.now().isoformat(),
            root=root
        )
        
        # 添加文档描述
        if self.if_add_doc_description and self.llm_service:
            doc_index.description = self._generate_description(markdown_content)
        
        # 保存索引
        self.indices[document_id] = doc_index
        self._save_index(doc_index)
        
        self.logger.info(f"树索引构建完成: {document_id}, 节点数: {len(doc_index.get_all_nodes())}")
        return doc_index
    
    def _parse_markdown_headings(self, content: str) -> List[Dict[str, Any]]:
        """
        解析Markdown标题
        
        Returns:
            标题列表 [{level, title, position, line_number}]
        """
        headings = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines):
            # 匹配 Markdown 标题 (# ## ### 等)
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                position = line_num
                headings.append({
                    "level": level,
                    "title": title,
                    "position": position,
                    "line_number": line_num + 1
                })
        
        return headings
    
    def _build_tree_from_headings(
        self,
        headings: List[Dict[str, Any]],
        content: str,
        doc_title: str
    ) -> TreeNode:
        """从标题列表构建树结构"""
        if not headings:
            return TreeNode(
                title=doc_title,
                node_id="0001",
                start_index=0,
                end_index=len(content),
                level=0
            )
        
        # 生成节点ID
        def generate_node_id(index: int) -> str:
            return f"{index:04d}"
        
        # 构建树
        lines = content.split('\n')
        
        # 创建根节点
        root = TreeNode(
            title=doc_title,
            node_id="0000",
            start_index=0,
            end_index=headings[0]["position"] if headings else len(content),
            level=0
        )
        
        # 使用栈来维护层级关系
        stack: List[Tuple[TreeNode, int]] = [(root, 0)]  # (node, level)
        
        for i, heading in enumerate(headings):
            node = TreeNode(
                title=heading["title"],
                node_id=generate_node_id(i + 1),
                start_index=heading["position"],
                end_index=headings[i + 1]["position"] if i + 1 < len(headings) else len(lines),
                level=heading["level"],
                content=self._get_section_content(lines, heading, headings, i)
            )
            
            # 生成摘要
            if self.if_add_summary and self.llm_service:
                node.summary = self._generate_summary(node.content)
            elif node.content:
                # 不使用LLM时，生成简单的摘要
                node.summary = node.content[:200] + "..." if len(node.content) > 200 else node.content
            
            # 找到合适的父节点
            while stack and stack[-1][1] >= heading["level"]:
                stack.pop()
            
            if stack:
                stack[-1][0].nodes.append(node)
            
            stack.append((node, heading["level"]))
        
        return root
    
    def _get_section_content(
        self,
        lines: List[str],
        heading: Dict[str, Any],
        all_headings: List[Dict[str, Any]],
        heading_index: int
    ) -> str:
        """获取章节内容"""
        start = heading["position"]
        end = all_headings[heading_index + 1]["position"] if heading_index + 1 < len(all_headings) else len(lines)
        
        section_lines = lines[start:end]
        content = '\n'.join(section_lines)
        
        # 截取部分内容 (避免过长)
        max_chars = 10000
        if len(content) > max_chars:
            content = content[:max_chars] + "..."
        
        return content
    
    def _generate_summary(self, content: str) -> str:
        """使用LLM生成摘要"""
        if not self.llm_service:
            return content[:200] + "..." if len(content) > 200 else content
        
        try:
            prompt = f"请为以下内容生成一个简洁的摘要 (50-100字): \n\n{content[:3000]}"
            response = self.llm_service.generate(prompt)
            if response:
                return response.strip()[:200]  # 限制摘要长度
        except Exception as e:
            self.logger.warning(f"生成摘要失败: {e}")
        
        return content[:200] + "..." if len(content) > 200 else content
    
    def _generate_description(self, content: str) -> str:
        """使用LLM生成文档描述"""
        if not self.llm_service:
            return ""
        
        try:
            prompt = f"请为以下文档生成一个简洁的描述 (100-200字): \n\n{content[:5000]}"
            response = self.llm_service.generate(prompt)
            if response:
                return response.strip()[:300]
        except Exception as e:
            self.logger.warning(f"生成文档描述失败: {e}")
        
        return ""
    
    def build_from_pdf_pages(
        self,
        document_id: str,
        title: str,
        pages: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentIndex:
        """
        从PDF页面列表构建树索引
        
        Args:
            document_id: 文档ID
            title: 文档标题
            pages: PDF页面内容列表
            metadata: 额外元数据
            
        Returns:
            DocumentIndex 对象
        """
        self.logger.info(f"从PDF页面构建树索引: {document_id}, 页数: {len(pages)}")
        
        # 简单的页面分组策略
        # 在实际使用中，可以结合LLM来识别章节
        nodes = []
        pages_per_node = self.max_pages_per_node
        
        for i in range(0, len(pages), pages_per_node):
            node_pages = pages[i:i + pages_per_node]
            content = '\n\n'.join(node_pages)
            
            node = TreeNode(
                title=f"Section {len(nodes) + 1}",
                node_id=f"{len(nodes) + 1:04d}",
                start_index=i,
                end_index=min(i + pages_per_node, len(pages)),
                level=1,
                content=content[:10000]
            )
            
            # 生成摘要
            if self.if_add_summary:
                if self.llm_service:
                    node.summary = self._generate_summary(content)
                else:
                    node.summary = content[:200] + "..." if len(content) > 200 else content
            
            nodes.append(node)
        
        # 创建根节点
        root = TreeNode(
            title=title,
            node_id="0000",
            start_index=0,
            end_index=len(pages),
            level=0,
            nodes=nodes
        )
        
        # 创建文档索引
        doc_index = DocumentIndex(
            document_id=document_id,
            title=title,
            total_pages=len(pages),
            created_at=datetime.now().isoformat(),
            root=root
        )
        
        # 保存索引
        self.indices[document_id] = doc_index
        self._save_index(doc_index)
        
        self.logger.info(f"树索引构建完成: {document_id}")
        return doc_index
    
    def get_index(self, document_id: str) -> Optional[DocumentIndex]:
        """获取文档索引"""
        return self.indices.get(document_id)
    
    def get_all_indices(self) -> Dict[str, DocumentIndex]:
        """获取所有索引"""
        return self.indices
    
    def delete_index(self, document_id: str) -> bool:
        """删除索引"""
        if document_id in self.indices:
            del self.indices[document_id]
            
            # 删除文件
            file_path = self.index_path / f"{document_id}.json"
            if file_path.exists():
                file_path.unlink()
            
            self.logger.info(f"删除树索引: {document_id}")
            return True
        return False
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """列出所有索引的文档"""
        result = []
        for doc_id, doc_index in self.indices.items():
            result.append({
                "document_id": doc_id,
                "title": doc_index.title,
                "total_pages": doc_index.total_pages,
                "node_count": len(doc_index.get_all_nodes()),
                "created_at": doc_index.created_at
            })
        return result


# 单例模式
_tree_index_builder_instance: Optional['TreeIndexBuilder'] = None


def get_tree_index_builder() -> TreeIndexBuilder:
    """获取TreeIndexBuilder单例"""
    global _tree_index_builder_instance
    if _tree_index_builder_instance is None:
        _tree_index_builder_instance = TreeIndexBuilder()
    return _tree_index_builder_instance
