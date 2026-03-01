#!/usr/bin/env python3
"""
文档结构解析器 (Document Structure Parser)
解析PDF、Markdown等文档，提取文档结构信息

功能:
1. 从PDF提取文本和结构
2. 从Markdown提取标题层级
3. 识别章节边界
4. 生成结构化元数据
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..utils.logger import get_logger

logger = get_logger()


class DocumentType(Enum):
    """文档类型"""
    MARKDOWN = "markdown"
    PDF = "pdf"
    TEXT = "text"
    HTML = "html"
    UNKNOWN = "unknown"


@dataclass
class Section:
    """文档章节"""
    title: str
    level: int  # 标题层级 (1-6)
    start_line: int  # 起始行号
    end_line: int  # 结束行号
    start_char: int  # 起始字符位置
    end_char: int  # 结束字符位置
    content: str = ""  # 章节内容
    page_number: Optional[int] = None  # 起始页码
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "level": self.level,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "content_preview": self.content[:500] if self.content else "",
            "page_number": self.page_number
        }


@dataclass
class DocumentStructure:
    """文档结构"""
    document_id: str
    document_type: DocumentType
    title: str
    total_lines: int
    total_chars: int
    total_pages: int = 0
    sections: List[Section] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type.value,
            "title": self.title,
            "total_lines": self.total_lines,
            "total_chars": self.total_chars,
            "total_pages": self.total_pages,
            "section_count": len(self.sections),
            "sections": [s.to_dict() for s in self.sections],
            "metadata": self.metadata
        }
    
    def get_section_tree(self) -> Dict[str, Any]:
        """获取章节树结构"""
        if not self.sections:
            return {"title": self.title, "level": 0, "children": []}
        
        # 构建层级结构
        root = {"title": self.title, "level": 0, "children": []}
        stack = [root]
        
        for section in self.sections:
            node = {
                "title": section.title,
                "level": section.level,
                "start_line": section.start_line,
                "end_line": section.end_line,
                "children": []
            }
            
            # 找到合适的父节点
            while stack and stack[-1]["level"] >= section.level:
                stack.pop()
            
            if stack:
                stack[-1]["children"].append(node)
            
            stack.append(node)
        
        return root


class DocumentStructureParser:
    """文档结构解析器"""
    
    def __init__(self):
        self.logger = logger
        
        # 支持的文档类型及其解析器
        self.parsers = {
            DocumentType.MARKDOWN: self._parse_markdown,
            DocumentType.TEXT: self._parse_text,
        }
    
    def detect_document_type(self, file_path: str) -> DocumentType:
        """检测文档类型"""
        ext = Path(file_path).suffix.lower()
        
        type_mapping = {
            ".md": DocumentType.MARKDOWN,
            ".markdown": DocumentType.MARKDOWN,
            ".txt": DocumentType.TEXT,
            ".pdf": DocumentType.PDF,
            ".html": DocumentType.HTML,
            ".htm": DocumentType.HTML,
        }
        
        return type_mapping.get(ext, DocumentType.UNKNOWN)
    
    def parse(
        self,
        document_id: str,
        content: str,
        document_type: DocumentType = DocumentType.MARKDOWN,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentStructure:
        """
        解析文档结构
        
        Args:
            document_id: 文档ID
            content: 文档内容
            document_type: 文档类型
            metadata: 额外元数据
            
        Returns:
            DocumentStructure 对象
        """
        self.logger.info(f"解析文档结构: {document_id}, 类型: {document_type.value}")
        
        # 获取解析器
        parser = self.parsers.get(document_type, self._parse_text)
        
        # 调用解析器
        structure = parser(document_id, content)
        
        # 添加元数据
        if metadata:
            structure.metadata.update(metadata)
        
        self.logger.info(f"文档结构解析完成: {document_id}, 章节数: {len(structure.sections)}")
        return structure
    
    def _parse_markdown(self, document_id: str, content: str) -> DocumentStructure:
        """解析Markdown文档"""
        lines = content.split('\n')
        
        # 提取标题作为文档标题
        title = "Untitled Document"
        for line in lines[:10]:  # 检查前10行
            match = re.match(r'^#\s+(.+)$', line)
            if match:
                title = match.group(1).strip()
                break
        
        # 解析章节
        sections = []
        current_pos = 0
        
        for line_num, line in enumerate(lines):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                section_title = match.group(2).strip()
                
                # 计算字符位置
                start_char = content.find(line, current_pos)
                if start_char == -1:
                    start_char = current_pos
                
                # 找到下一个标题或文档结束
                end_char = len(content)
                for next_line in lines[line_num + 1:]:
                    if re.match(r'^#{1,6}\s+', next_line):
                        end_char = content.find(next_line, start_char)
                        break
                
                # 提取章节内容
                section_content = content[start_char:end_char].strip()
                
                section = Section(
                    title=section_title,
                    level=level,
                    start_line=line_num + 1,
                    end_line=line_num + 1,  # 标题行
                    start_char=start_char,
                    end_char=end_char,
                    content=section_content
                )
                sections.append(section)
                
                current_pos = end_char
        
        return DocumentStructure(
            document_id=document_id,
            document_type=DocumentType.MARKDOWN,
            title=title,
            total_lines=len(lines),
            total_chars=len(content),
            sections=sections
        )
    
    def _parse_text(self, document_id: str, content: str) -> DocumentStructure:
        """解析纯文本文档"""
        lines = content.split('\n')
        
        # 尝试识别标题模式
        sections = []
        
        # 常见的标题模式
        title_patterns = [
            r'^[A-Z][A-Za-z\s]{5,50}$',  # 全大写标题
            r'^\d+\.\s+[A-Z]',  # 数字编号 1. Title
            r'^[A-Z]\.\s+[A-Z]',  # 字母编号 A. Title
        ]
        
        title = "Untitled Document"
        
        for line_num, line in enumerate(lines[:20]):  # 检查前20行作为标题
            line = line.strip()
            if not line:
                continue
            
            # 检查是否为标题
            is_title = False
            for pattern in title_patterns:
                if re.match(pattern, line):
                    is_title = True
                    break
            
            if is_title and len(line) < 100:
                title = line
                break
        
        # 简单分块 - 按行数分组
        chunk_size = 100  # 每100行为一个chunk
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            start_char = sum(len(l) + 1 for l in lines[:i])
            end_char = start_char + sum(len(l) + 1 for l in chunk_lines)
            
            section = Section(
                title=f"Section {i // chunk_size + 1}",
                level=1,
                start_line=i + 1,
                end_line=min(i + chunk_size, len(lines)),
                start_char=start_char,
                end_char=end_char,
                content='\n'.join(chunk_lines)
            )
            sections.append(section)
        
        return DocumentStructure(
            document_id=document_id,
            document_type=DocumentType.TEXT,
            title=title,
            total_lines=len(lines),
            total_chars=len(content),
            sections=sections
        )
    
    def extract_table_of_contents(self, structure: DocumentStructure) -> List[Dict[str, Any]]:
        """提取目录结构"""
        toc = []
        
        for section in structure.sections:
            toc.append({
                "title": section.title,
                "level": section.level,
                "line_number": section.start_line,
                "page_number": section.page_number
            })
        
        return toc
    
    def get_section_hierarchy(self, structure: DocumentStructure) -> Dict[str, Any]:
        """获取章节层级"""
        return structure.get_section_tree()


# 单例模式
_parser_instance: Optional['DocumentStructureParser'] = None


def get_document_structure_parser() -> DocumentStructureParser:
    """获取DocumentStructureParser单例"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = DocumentStructureParser()
    return _parser_instance
