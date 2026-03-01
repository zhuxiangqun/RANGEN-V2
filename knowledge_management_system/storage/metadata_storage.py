#!/usr/bin/env python3
"""
元数据存储模块
管理知识元数据的存储
"""

import json
import os  # 🆕 引入os模块用于fsync
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..core.knowledge_manager import KnowledgeManager
from ..utils.logger import get_logger

logger = get_logger()


class MetadataStorage:
    """元数据存储管理器"""
    
    def __init__(self, metadata_path: str = "data/knowledge_management/metadata.json"):
        self.logger = logger
        self.manager = KnowledgeManager(metadata_path)
        # 🆕 失败条目记录文件路径
        self.failed_entries_path = Path(metadata_path).parent / "failed_entries.json"
        self._failed_entries: Dict[str, Any] = {}
        self._load_failed_entries()
    
    def get_manager(self) -> KnowledgeManager:
        """获取知识管理器"""
        return self.manager
    
    def _load_failed_entries(self) -> None:
        """加载失败条目记录"""
        try:
            if self.failed_entries_path.exists():
                with open(self.failed_entries_path, 'r', encoding='utf-8') as f:
                    self._failed_entries = json.load(f)
                failed_count = len(self._failed_entries.get('entries', []))
                if failed_count > 0:
                    self.logger.info(f"📋 检测到 {failed_count} 条失败记录，将在重新导入时自动加载")
        except Exception as e:
            self.logger.warning(f"加载失败条目记录失败: {e}")
            self._failed_entries = {'entries': [], 'last_updated': None}
    
    def _save_failed_entries(self) -> None:
        """保存失败条目记录"""
        try:
            self.failed_entries_path.parent.mkdir(parents=True, exist_ok=True)
            self._failed_entries['last_updated'] = datetime.now().isoformat()
            
            # 🚀 修复：使用临时文件写入，然后原子性重命名，避免写入过程中崩溃导致文件损坏
            temp_file = self.failed_entries_path.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._failed_entries, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())  # 强制刷入磁盘
            
            # 原子性重命名
            temp_file.replace(self.failed_entries_path)
        except Exception as e:
            self.logger.error(f"保存失败条目记录失败: {e}")
    
    def record_failed_entry(
        self,
        entry: Dict[str, Any],
        error_type: str,
        error_message: str,
        source_type: str = "unknown",
        modality: str = "text"
    ) -> None:
        """
        记录失败的条目
        
        Args:
            entry: 失败的条目数据
            error_type: 错误类型（如：chunking_failed, validation_failed, vectorization_failed等）
            error_message: 错误信息
            source_type: 数据源类型
            modality: 模态类型
        """
        if 'entries' not in self._failed_entries:
            self._failed_entries['entries'] = []
        
        failed_entry = {
            'entry': entry,
            'error_type': error_type,
            'error_message': str(error_message)[:500],  # 限制错误信息长度
            'source_type': source_type,
            'modality': modality,
            'failed_at': datetime.now().isoformat(),
            'retry_count': 0
        }
        
        self._failed_entries['entries'].append(failed_entry)
        self._save_failed_entries()
        self.logger.debug(f"已记录失败条目: {error_type} - {error_message[:100]}")
    
    def get_failed_entries(self) -> List[Dict[str, Any]]:
        """获取所有失败条目"""
        return self._failed_entries.get('entries', [])
    
    def clear_failed_entries(self, success_entry_ids: Optional[List[str]] = None) -> int:
        """
        清理失败记录
        
        Args:
            success_entry_ids: 成功处理的条目ID列表（可选，用于精确清理）
        
        Returns:
            清理的条目数量
        """
        if not success_entry_ids:
            # 清理所有记录
            count = len(self._failed_entries.get('entries', []))
            self._failed_entries['entries'] = []
            self._save_failed_entries()
            self.logger.info(f"已清理 {count} 条失败记录")
            return count
        else:
            # 根据成功ID清理（需要匹配条目的内容哈希）
            original_count = len(self._failed_entries.get('entries', []))
            remaining_entries = []
            
            for failed_entry in self._failed_entries.get('entries', []):
                entry = failed_entry.get('entry', {})
                entry_content = entry.get('content', '')
                
                # 计算内容哈希来判断是否匹配
                import hashlib
                content_hash = hashlib.md5(entry_content.encode('utf-8')).hexdigest()
                
                # 简单匹配：如果内容在成功ID对应的条目中，则移除
                # 这里简化处理，实际可以根据需要改进匹配逻辑
                should_remove = False
                for success_id in success_entry_ids:
                    # 这里可以添加更精确的匹配逻辑
                    if content_hash in str(success_id) or str(success_id) in entry_content[:100]:
                        should_remove = True
                        break
                
                if not should_remove:
                    remaining_entries.append(failed_entry)
            
            removed_count = original_count - len(remaining_entries)
            self._failed_entries['entries'] = remaining_entries
            self._save_failed_entries()
            
            if removed_count > 0:
                self.logger.info(f"已清理 {removed_count} 条失败记录（基于成功条目）")
            
            return removed_count
    
    def has_failed_entries(self) -> bool:
        """检查是否有失败记录"""
        return len(self._failed_entries.get('entries', [])) > 0

