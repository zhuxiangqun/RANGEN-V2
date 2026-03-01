#!/usr/bin/env python3
"""
LlamaIndex 文档加载器
支持从多种格式加载文档（PDF、Markdown、网页等）
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..utils.logger import get_logger

logger = get_logger()

# 尝试导入 LlamaIndex（可选依赖）
try:
    from llama_index.core import SimpleDirectoryReader
    from llama_index.readers.file import PDFReader, MarkdownReader
    from llama_index.readers.web import BeautifulSoupWebReader
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    logger.warning("LlamaIndex 未安装，文档加载功能将不可用。如需使用，请运行: pip install 'llama-index[readers]'")


class LlamaIndexDocumentLoader:
    """使用 LlamaIndex 加载和处理各种格式的文档"""
    
    def __init__(self):
        """初始化文档加载器"""
        self.enabled = LLAMAINDEX_AVAILABLE
        self.logger = logger
        
        if self.enabled:
            self._init_readers()
        else:
            self.readers = {}
    
    def _init_readers(self):
        """初始化各种格式的读取器"""
        try:
            self.readers = {
                'pdf': PDFReader() if LLAMAINDEX_AVAILABLE else None,  # type: ignore
                'markdown': MarkdownReader() if LLAMAINDEX_AVAILABLE else None,  # type: ignore
                'web': BeautifulSoupWebReader() if LLAMAINDEX_AVAILABLE else None,  # type: ignore
            }
            self.logger.info("✅ LlamaIndex 文档加载器初始化成功")
        except Exception as e:
            self.logger.error(f"LlamaIndex 文档加载器初始化失败: {e}")
            self.enabled = False
            self.readers = {}
    
    def _is_url(self, path: str) -> bool:
        """
        检测是否为URL
        
        Args:
            path: 路径或URL
        
        Returns:
            是否为URL
        """
        return path.startswith('http://') or path.startswith('https://')
    
    def _detect_file_type(self, file_path: str) -> str:
        """
        自动检测文件类型
        
        Args:
            file_path: 文件路径或URL
        
        Returns:
            文件类型（pdf, markdown, txt, html, web等）
        """
        # 如果是URL，返回 'web'
        if self._is_url(file_path):
            return 'web'
        
        path = Path(file_path)
        ext = path.suffix.lower()
        
        type_map = {
            '.pdf': 'pdf',
            '.md': 'markdown',
            '.markdown': 'markdown',
            '.txt': 'txt',
            '.html': 'html',
            '.htm': 'html',
            '.json': 'json',
            '.csv': 'csv',
        }
        
        return type_map.get(ext, 'txt')
    
    def load_document(
        self, 
        file_path: str, 
        file_type: Optional[str] = None  # type: ignore
    ) -> List[Dict[str, Any]]:
        """
        加载文档（支持本地文件和URL）
        
        Args:
            file_path: 文件路径或URL
            file_type: 文件类型（如果为None，自动检测）
        
        Returns:
            文档列表，每个文档包含 text 和 metadata
        """
        if not self.enabled:
            self.logger.warning("LlamaIndex 未安装，无法加载文档")
            return []
        
        try:
            if file_type is None:
                file_type = self._detect_file_type(file_path) or 'txt'
            
            # 使用 LlamaIndex 加载文档
            if file_type == 'web' and self.readers.get('web'):
                # 🆕 支持从URL加载网页内容
                if self._is_url(file_path):
                    self.logger.info(f"🌐 正在从URL加载网页: {file_path}")
                    # BeautifulSoupWebReader 支持URL
                    documents = self.readers['web'].load_data(urls=[file_path])
                else:
                    # 本地HTML文件
                    documents = self.readers['web'].load_data(file_path)
            elif file_type == 'pdf' and self.readers.get('pdf'):
                documents = self.readers['pdf'].load_data(file_path)
            elif file_type == 'markdown' and self.readers.get('markdown'):
                documents = self.readers['markdown'].load_data(file_path)
            elif file_type in ['html', 'htm'] and self.readers.get('web'):
                documents = self.readers['web'].load_data(file_path)
            else:
                # 使用通用加载器（仅支持本地文件）
                if self._is_url(file_path):
                    self.logger.error(f"URL格式不支持通用加载器: {file_path}")
                    return []
                documents = SimpleDirectoryReader(input_files=[file_path]).load_data()  # type: ignore
            
            # 转换为统一格式
            result = []
            for doc in documents:
                result.append({
                    'text': doc.text,
                    'metadata': doc.metadata or {},
                    'file_path': file_path,
                    'file_type': file_type
                })
            
            source_type = "URL" if self._is_url(file_path) else "文件"
            self.logger.info(f"✅ 成功从{source_type}加载文档: {file_path} ({file_type}), 共 {len(result)} 个文档片段")
            return result
            
        except Exception as e:
            self.logger.error(f"加载文档失败: {file_path}, 错误: {e}")
            import traceback
            self.logger.debug(f"详细错误:\n{traceback.format_exc()}")
            return []
    
    def load_from_directory(self, directory: str) -> List[Dict[str, Any]]:
        """
        从目录加载所有支持的文档
        
        Args:
            directory: 目录路径
        
        Returns:
            文档列表
        """
        if not self.enabled:
            self.logger.warning("LlamaIndex 未安装，无法加载文档")
            return []
        
        try:
            documents = SimpleDirectoryReader(directory).load_data()  # type: ignore
            
            # 转换为统一格式
            result = []
            for doc in documents:
                result.append({
                    'text': doc.text,
                    'metadata': doc.metadata or {},
                    'file_path': doc.metadata.get('file_path', ''),
                    'file_type': self._detect_file_type(doc.metadata.get('file_path', ''))
                })
            
            self.logger.info(f"✅ 成功从目录加载文档: {directory}, 共 {len(result)} 个文档片段")
            return result
            
        except Exception as e:
            self.logger.error(f"从目录加载文档失败: {directory}, 错误: {e}")
            return []

