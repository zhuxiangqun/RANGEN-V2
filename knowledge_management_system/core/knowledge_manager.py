#!/usr/bin/env python3
"""
知识管理器
提供知识的CRUD操作、版本控制、分类管理
"""

import json
import time
import uuid
import hashlib
import os  # 🆕 引入os模块用于fsync
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from ..utils.logger import get_logger
from ..utils.validators import validate_knowledge_data

logger = get_logger()


class KnowledgeManager:
    """知识管理器"""
    
    def __init__(self, metadata_path: str = "data/knowledge_management/metadata.json"):
        self.logger = logger
        self.metadata_path = Path(metadata_path)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        self._metadata: Dict[str, Any] = {}
        self._load_metadata()
    
    def _load_metadata(self):
        """加载元数据"""
        try:
            if self.metadata_path.exists():
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self._metadata = json.load(f)
                self.logger.info(f"已加载 {len(self._metadata.get('entries', {}))} 条知识元数据")
            else:
                self._metadata = {
                    'version': '1.0',
                    'created_at': datetime.now().isoformat(),
                    'entries': {},
                    'content_hash_index': {}  # 🆕 内容哈希索引，用于查重
                }
                self._save_metadata()
        except Exception as e:
            self.logger.error(f"加载元数据失败: {e}")
            self._metadata = {'entries': {}, 'content_hash_index': {}}
        
        # 🆕 确保内容哈希索引存在
        if 'content_hash_index' not in self._metadata:
            self._metadata['content_hash_index'] = {}
            # 重建哈希索引
            self._rebuild_hash_index()
    
    def _save_metadata(self):
        """保存元数据（使用原子性写入，避免文件损坏）"""
        try:
            self._metadata['updated_at'] = datetime.now().isoformat()
            # 🚀 修复：使用临时文件写入，然后原子性重命名，避免写入过程中崩溃导致文件损坏
            temp_file = self.metadata_path.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._metadata, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            # 原子性重命名（在POSIX系统上是原子操作）
            temp_file.replace(self.metadata_path)
            self.logger.debug(f"元数据文件已保存: {self.metadata_path}")
        except Exception as e:
            self.logger.error(f"保存元数据失败: {e}")
            # 如果临时文件存在但重命名失败，尝试清理
            temp_file = self.metadata_path.with_suffix('.tmp')
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass
    
    def _compute_content_hash(self, content: Any) -> str:
        """
        计算内容哈希值（用于查重）
        
        Args:
            content: 知识内容
        
        Returns:
            哈希值（SHA256）
        """
        try:
            # 将内容转换为字符串并标准化
            if isinstance(content, str):
                content_str = content.strip()
            else:
                content_str = str(content).strip()
            
            # 计算SHA256哈希
            hash_obj = hashlib.sha256(content_str.encode('utf-8'))
            return hash_obj.hexdigest()
        except Exception as e:
            self.logger.error(f"计算内容哈希失败: {e}")
            return ""
    
    def _rebuild_hash_index(self):
        """重建内容哈希索引"""
        try:
            hash_index = {}
            entries = self._metadata.get('entries', {})
            
            for knowledge_id, entry in entries.items():
                # 从元数据中获取完整内容（如果存在）
                content = entry.get('metadata', {}).get('content')
                if not content:
                    # 如果没有完整内容，使用预览
                    content = entry.get('content_preview', '')
                
                if content:
                    content_hash = self._compute_content_hash(content)
                    if content_hash:
                        hash_index[content_hash] = knowledge_id
            
            self._metadata['content_hash_index'] = hash_index
            self.logger.info(f"重建哈希索引: {len(hash_index)} 条")
        except Exception as e:
            self.logger.error(f"重建哈希索引失败: {e}")
    
    def check_duplicate(self, content: Any) -> Optional[str]:
        """
        检查内容是否已存在（查重）
        
        Args:
            content: 知识内容
        
        Returns:
            如果存在重复，返回已存在的知识ID；否则返回None
        """
        try:
            # 🚀 改进：如果content为空或太短，不进行查重（避免空内容干扰）
            if not content or (isinstance(content, str) and len(content.strip()) < 3):
                self.logger.debug("跳过空内容或过短内容的查重")
                return None
            
            content_hash = self._compute_content_hash(content)
            if not content_hash:
                return None
            
            # 🚀 改进：空字符串的hash不应该用于查重（避免空内容干扰）
            empty_hash = hashlib.sha256(''.encode('utf-8')).hexdigest()
            if content_hash == empty_hash:
                self.logger.debug("跳过空内容的查重（hash为空字符串）")
                return None
            
            hash_index = self._metadata.get('content_hash_index', {})
            existing_id = hash_index.get(content_hash)
            
            if existing_id:
                # 验证该ID是否真的存在
                entries = self._metadata.get('entries', {})
                if existing_id in entries:
                    # 🚀 改进：验证已存在条目的content是否真的相同
                    existing_entry = entries[existing_id]
                    existing_content = existing_entry.get('metadata', {}).get('content', '') or existing_entry.get('content_preview', '')
                    current_content = content.strip() if isinstance(content, str) else str(content).strip()
                    
                    if existing_content.strip() == current_content:
                        self.logger.debug(f"检测到重复内容，已存在知识ID: {existing_id}")
                        return existing_id
                    else:
                        # 内容不匹配，可能是hash冲突，清理索引并继续
                        self.logger.warning(f"Hash冲突检测：已存在ID的内容不匹配，清理索引")
                        del hash_index[content_hash]
                else:
                    # 哈希索引中有但条目不存在，清理无效索引
                    del hash_index[content_hash]
            
            return None
        except Exception as e:
            self.logger.error(f"查重失败: {e}")
            return None
    
    def create_knowledge(
        self, 
        content: Any, 
        modality: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
        skip_duplicate: bool = True
    ) -> Optional[str]:
        """
        创建知识条目（🆕 支持查重）
        
        Args:
            content: 知识内容
            modality: 模态类型
            metadata: 额外元数据
            skip_duplicate: 如果发现重复内容，是否跳过创建（返回已存在的ID）
        
        Returns:
            知识ID（如果重复且skip_duplicate=True，返回已存在的ID），如果失败返回None
        """
        try:
            # 🆕 查重处理
            if skip_duplicate:
                existing_id = self.check_duplicate(content)
                if existing_id:
                    self.logger.info(f"跳过重复知识条目（已存在: {existing_id}）")
                    return existing_id
            
            # 🚀 改进：构建知识数据时，确保metadata中的'content'不会覆盖传入的content
            # 如果metadata中有'content'，先移除它，避免覆盖
            safe_metadata = {k: v for k, v in (metadata or {}).items() if k != 'content'}
            knowledge_data = {
                'content': content,
                **safe_metadata
            }
            
            # 验证
            is_valid, error = validate_knowledge_data(knowledge_data, modality)
            if not is_valid:
                self.logger.error(f"无效知识数据: {error}")
                return None
            
            # 生成ID
            knowledge_id = str(uuid.uuid4())
            
            # 计算内容哈希并添加到索引
            content_hash = self._compute_content_hash(content)
            
            # 保存元数据
            self._metadata.setdefault('entries', {})
            self._metadata['entries'][knowledge_id] = {
                'id': knowledge_id,
                'modality': modality,
                'content_preview': str(content)[:200] if isinstance(content, str) else str(type(content)),
                'metadata': {**(metadata or {}), 'content': content},  # 🆕 保存完整内容用于查重
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'version': 1,
                'content_hash': content_hash  # 🆕 保存哈希值
            }
            
            # 🆕 更新哈希索引
            self._metadata.setdefault('content_hash_index', {})
            self._metadata['content_hash_index'][content_hash] = knowledge_id
            
            self._save_metadata()
            self.logger.info(f"创建知识条目: {knowledge_id}")
            return knowledge_id
            
        except Exception as e:
            self.logger.error(f"创建知识条目失败: {e}")
            return None
    
    def get_knowledge(self, knowledge_id: str) -> Optional[Dict[str, Any]]:
        """
        获取知识条目
        
        Args:
            knowledge_id: 知识ID
        
        Returns:
            知识条目，如果不存在返回None
        """
        entries = self._metadata.get('entries', {})
        return entries.get(knowledge_id)
    
    def update_knowledge(
        self, 
        knowledge_id: str, 
        content: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        更新知识条目
        
        Args:
            knowledge_id: 知识ID
            content: 新内容（可选）
            metadata: 新元数据（可选）
        
        Returns:
            是否成功
        """
        try:
            entries = self._metadata.get('entries', {})
            if knowledge_id not in entries:
                self.logger.error(f"知识条目不存在: {knowledge_id}")
                return False
            
            entry = entries[knowledge_id]
            
            # 更新内容
            if content is not None:
                entry['content_preview'] = str(content)[:200] if isinstance(content, str) else str(type(content))
            
            # 更新元数据
            if metadata:
                entry['metadata'].update(metadata)
            
            # 更新版本和时间
            entry['version'] = entry.get('version', 1) + 1
            entry['updated_at'] = datetime.now().isoformat()
            
            self._save_metadata()
            self.logger.info(f"更新知识条目: {knowledge_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新知识条目失败: {e}")
            return False
    
    def delete_knowledge(self, knowledge_id: str) -> bool:
        """
        删除知识条目
        
        Args:
            knowledge_id: 知识ID
        
        Returns:
            是否成功
        """
        try:
            entries = self._metadata.get('entries', {})
            if knowledge_id not in entries:
                self.logger.error(f"知识条目不存在: {knowledge_id}")
                return False
            
            del entries[knowledge_id]
            self._save_metadata()
            self.logger.info(f"删除知识条目: {knowledge_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"删除知识条目失败: {e}")
            return False
    
    def list_knowledge(
        self, 
        modality: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        列出知识条目
        
        Args:
            modality: 模态类型过滤（可选）
            limit: 返回数量限制
        
        Returns:
            知识条目列表
        """
        entries = self._metadata.get('entries', {})
        result = []
        
        for knowledge_id, entry in entries.items():
            if modality is None or entry.get('modality') == modality:
                result.append(entry)
                if len(result) >= limit:
                    break
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取知识库统计信息
        
        Returns:
            统计信息字典
        """
        entries = self._metadata.get('entries', {})
        
        # 按模态统计
        modality_stats = {}
        for entry in entries.values():
            modality = entry.get('modality', 'unknown')
            modality_stats[modality] = modality_stats.get(modality, 0) + 1
        
        return {
            'total_entries': len(entries),
            'modality_distribution': modality_stats,
            'created_at': self._metadata.get('created_at'),
            'updated_at': self._metadata.get('updated_at')
        }

