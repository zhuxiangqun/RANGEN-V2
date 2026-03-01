#!/usr/bin/env python3
"""
知识导入器
支持多种数据源的 knowledge 导入
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from ..utils.logger import get_logger
from ..utils.validators import validate_knowledge_data

logger = get_logger()


class KnowledgeImporter:
    """知识导入器"""
    
    def __init__(self):
        self.logger = logger
        # 🆕 可选：LlamaIndex 文档加载器（阶段3：增强文档处理能力）
        import os
        self.llamaindex_enabled = os.getenv("ENABLE_LLAMAINDEX", "false").lower() == "true"
        if self.llamaindex_enabled:
            try:
                from ..integrations.llamaindex_document_loader import LlamaIndexDocumentLoader
                self.llamaindex_loader = LlamaIndexDocumentLoader()
                if self.llamaindex_loader.enabled:
                    self.logger.info("✅ LlamaIndex 文档加载器已启用")
                else:
                    self.llamaindex_loader = None
            except Exception as e:
                self.logger.warning(f"LlamaIndex 文档加载器初始化失败: {e}")
                self.llamaindex_loader = None
        else:
            self.llamaindex_loader = None
        
        # 🆕 加载过滤配置（黑/灰/白名单、长度限制）
        self._load_filtering_config()

    def _load_filtering_config(self):
        """加载过滤配置，集中管理黑/灰/白名单和长度限制"""
        try:
            import json
            from pathlib import Path
            config_path = Path(__file__).parent.parent / "config" / "system_config.json"
            cfg = {}
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f) or {}
            filtering = cfg.get("filtering", {}) if isinstance(cfg, dict) else {}
        except Exception as e:
            filtering = {}
            self.logger.debug(f"加载过滤配置失败，使用默认值: {e}")

        self.blacklist_terms = [t.lower() for t in filtering.get("blacklist_terms", [])]
        self.graylist_terms = [t.lower() for t in filtering.get("graylist_terms", [])]
        self.whitelist_terms = [t.lower() for t in filtering.get("whitelist_core_facts", [])]
        self.max_content_length = filtering.get("max_content_length", 2000)

    def _apply_filters(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """应用黑/灰/白名单和长度过滤，返回保留后的条目或None"""
        content = entry.get("content", "")
        if not isinstance(content, str):
            return entry

        content_lower = content.lower()
        metadata = entry.get("metadata", {}) or {}
        has_whitelist = any(term in content_lower for term in self.whitelist_terms) if self.whitelist_terms else False

        # 黑名单：命中且未命中白名单则丢弃
        if (not has_whitelist) and self.blacklist_terms and any(term in content_lower for term in self.blacklist_terms):
            self.logger.info("⛔️ 导入过滤: 命中黑名单，已丢弃条目")
            return None

        # 长度限制：未命中白名单且超过长度则丢弃
        if (not has_whitelist) and self.max_content_length and len(content) > self.max_content_length:
            self.logger.info(f"⛔️ 导入过滤: 内容长度 {len(content)} 超过阈值 {self.max_content_length}，已丢弃条目")
            return None

        # 灰名单：保留但标记
        if self.graylist_terms and any(term in content_lower for term in self.graylist_terms):
            metadata = {**metadata, "graylist_flag": True}

        if metadata:
            entry["metadata"] = metadata
        return entry
    
    def import_from_json(self, file_path: str, modality: str = "text") -> List[Dict[str, Any]]:
        """
        从JSON文件导入知识
        
        Args:
            file_path: JSON文件路径
            modality: 模态类型
        
        Returns:
            知识条目列表
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.error(f"文件不存在: {file_path}")
                return []
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 处理不同的JSON格式
            if isinstance(data, list):
                entries = data
            elif isinstance(data, dict):
                # 尝试常见键名
                entries = data.get('entries', []) or data.get('knowledge', []) or data.get('data', [])
            else:
                self.logger.error(f"不支持的JSON格式: {type(data)}")
                return []
            
            # 验证和过滤
            valid_entries = []
            for entry in entries:
                entry = self._apply_filters(entry) or None
                if not entry:
                    continue
                is_valid, error = validate_knowledge_data(entry, modality)
                if is_valid:
                    valid_entries.append(entry)
                else:
                    self.logger.warning(f"无效知识条目: {error}")
            
            self.logger.info(f"从JSON导入 {len(valid_entries)} 条有效知识（共 {len(entries)} 条）")
            return valid_entries
            
        except Exception as e:
            self.logger.error(f"从JSON导入知识失败: {e}")
            return []
    
    def import_from_csv(self, file_path: str, content_column: str = "content") -> List[Dict[str, Any]]:
        """
        从CSV文件导入知识
        
        Args:
            file_path: CSV文件路径
            content_column: 内容列名
        
        Returns:
            知识条目列表
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.error(f"文件不存在: {file_path}")
                return []
            
            entries = []
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if content_column in row and row[content_column]:
                        entry = {
                            'content': row[content_column],
                            'metadata': {k: v for k, v in row.items() if k != content_column}
                        }
                        entry = self._apply_filters(entry) or None
                        if entry:
                            entries.append(entry)
            
            self.logger.info(f"从CSV导入 {len(entries)} 条知识")
            return entries
            
        except Exception as e:
            self.logger.error(f"从CSV导入知识失败: {e}")
            return []
    
    def import_from_dict(self, data: Dict[str, Any], modality: str = "text") -> List[Dict[str, Any]]:
        """
        从字典数据导入知识
        
        Args:
            data: 知识数据字典
            modality: 模态类型
        
        Returns:
            知识条目列表
        """
        try:
            # 验证数据
            data = self._apply_filters(data) or None
            if not data:
                return []

            is_valid, error = validate_knowledge_data(data, modality)
            if not is_valid:
                self.logger.error(f"无效知识数据: {error}")
                return []
            
            return [data]
            
        except Exception as e:
            self.logger.error(f"从字典导入知识失败: {e}")
            return []
    
    def import_from_list(self, data_list: List[Dict[str, Any]], modality: str = "text") -> List[Dict[str, Any]]:
        """
        从列表数据导入知识
        
        Args:
            data_list: 知识数据列表
            modality: 模态类型
        
        Returns:
            知识条目列表（超长条目会被分块）
        """
        try:
            # 🆕 导入文档分块器（用于处理超长内容）
            from ..utils.document_chunker import DocumentChunker
            chunker = DocumentChunker(
                max_chunk_size=3000,  # 🚀 优化：从8000降低到3000（约1024 token，符合文章建议的甜点区）
                overlap_ratio=0.2,
                chunk_strategy="recursive"
            )
            
            valid_entries = []
            chunked_count = 0
            
            for data in data_list:
                content = data.get('content', '')
                metadata = data.get('metadata', {})
                
                # 🆕 检查是否需要分块（超过验证器限制时，必须先分块）
                if isinstance(content, str):
                    content_length = len(content)
                    needs_chunking = False
                    
                    if content_length > 10000000:
                        # 超过验证器限制，必须先分块
                        self.logger.info(f"📄 检测到超长条目（{content_length}字符），自动分块处理（验证器限制: 10000000字符）")
                        needs_chunking = True
                    elif content_length > 10000:
                        # 超过推荐阈值，推荐分块（但由import_knowledge处理）
                        # 这里只处理必须分块的情况（超过验证器限制）
                        needs_chunking = False
                    
                    if needs_chunking:
                        # 分块处理
                        chunks = chunker.chunk_document(content, metadata=metadata)
                        
                        if chunks and len(chunks) > 1:
                            chunked_count += 1
                            self.logger.info(f"    → 分成{len(chunks)}块")
                            
                            # 将每个块作为一个独立的条目
                            for chunk_data in chunks:
                                chunk_content = chunk_data['content']
                                chunk_metadata = {
                                    **metadata,
                                    **chunk_data.get('parent_metadata', {}),
                                    'chunk_info': {
                                        'chunk_index': chunk_data['chunk_index'],
                                        'total_chunks': chunk_data['total_chunks'],
                                        'is_first': chunk_data['chunk_metadata'].get('is_first', False),
                                        'is_last': chunk_data['chunk_metadata'].get('is_last', False),
                                        'chunk_length': chunk_data['chunk_metadata'].get('chunk_length', 0),
                                        'parent_document_length': content_length
                                    },
                                    'source': metadata.get('source', 'unknown') + '_chunked'
                                }
                                
                                # 验证分块后的条目
                                chunk_entry = {
                                    'content': chunk_content,
                                    'metadata': chunk_metadata
                                }
                                is_valid, error = validate_knowledge_data(chunk_entry, modality)
                                if is_valid:
                                    valid_entries.append(chunk_entry)
                                else:
                                    self.logger.warning(f"分块后的条目验证失败: {error}")
                            continue
                        elif chunks and len(chunks) == 1:
                            # 如果分块后只有一个块，使用该块的内容
                            data = {
                                'content': chunks[0]['content'],
                                'metadata': {**metadata, **chunks[0].get('parent_metadata', {})}
                            }
                
                # 验证条目（对于未分块或单个块的条目）
                data = self._apply_filters(data) or None
                if not data:
                    continue

                is_valid, error = validate_knowledge_data(data, modality)
                if is_valid:
                    valid_entries.append(data)
                else:
                    self.logger.warning(f"无效知识条目: {error}")
            
            info_msg = f"从列表导入 {len(valid_entries)} 条有效知识（共 {len(data_list)} 条）"
            if chunked_count > 0:
                info_msg += f"，分块处理 {chunked_count} 条超长文档"
            self.logger.info(info_msg)
            return valid_entries
            
        except Exception as e:
            self.logger.error(f"从列表导入知识失败: {e}")
            import traceback
            self.logger.debug(f"详细错误:\n{traceback.format_exc()}")
            return []
    
    def import_from_file(
        self, 
        file_path: str, 
        file_type: str = None,
        use_llamaindex: bool = False,
        chunk_strategy: str = "sentence"
    ) -> List[Dict[str, Any]]:
        """
        从文件导入知识（🆕 支持多种格式，阶段3：增强文档处理能力）
        
        Args:
            file_path: 文件路径
            file_type: 文件类型（pdf, markdown, txt, html等，如果为None则自动检测）
            use_llamaindex: 是否使用 LlamaIndex 加载器（支持PDF、Markdown、网页等）
            chunk_strategy: 分块策略（仅 LlamaIndex 模式，可选：sentence, semantic, simple）
        
        Returns:
            知识条目列表
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.error(f"文件不存在: {file_path}")
                return []
            
            # 如果启用 LlamaIndex 且文件格式支持
            if use_llamaindex and self.llamaindex_loader and self.llamaindex_loader.enabled:
                # 使用 LlamaIndex 加载文档
                documents = self.llamaindex_loader.load_document(file_path, file_type)
                
                if not documents:
                    self.logger.warning(f"LlamaIndex 未能加载文档: {file_path}")
                    return []
                
                # 使用 LlamaIndex 分块器进行智能分块
                from ..integrations.llamaindex_chunker import LlamaIndexChunker
                chunker = LlamaIndexChunker(chunk_strategy=chunk_strategy)
                
                # 转换为知识条目格式
                entries = []
                for doc in documents:
                    # 对文档进行智能分块
                    chunks = chunker.chunk_document(doc['text'], doc.get('metadata', {}))
                    
                    for chunk in chunks:
                        entries.append({
                            'content': chunk['content'],
                            'metadata': {
                                **doc.get('metadata', {}),
                                **chunk.get('metadata', {}),
                                'source': doc.get('file_path', file_path),
                                'file_type': doc.get('file_type', file_type or 'unknown'),
                                'chunk_id': chunk.get('node_id', '')
                            }
                        })
                
                self.logger.info(f"✅ 使用 LlamaIndex 从文件导入 {len(entries)} 条知识（文件: {file_path}）")
                # 分块结果同样应用过滤
                filtered_entries = []
                for entry in entries:
                    entry = self._apply_filters(entry) or None
                    if entry:
                        filtered_entries.append(entry)
                entries = filtered_entries
                return entries
            else:
                # 使用现有逻辑（JSON、CSV等）
                if file_type is None:
                    file_type = path.suffix.lower()
                
                if file_type == '.json':
                    return self.import_from_json(file_path)
                elif file_type == '.csv':
                    return self.import_from_csv(file_path)
                else:
                    self.logger.warning(f"不支持的文件格式: {file_type}，请使用 use_llamaindex=True 或使用支持的格式（JSON、CSV）")
                    return []
            
        except Exception as e:
            self.logger.error(f"从文件导入知识失败: {file_path}, 错误: {e}")
            import traceback
            self.logger.debug(f"错误详情:\n{traceback.format_exc()}")
            return []

