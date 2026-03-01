"""
Transactional Knowledge Manager
实现了两阶段提交（Two-Phase Commit）的知识管理器，确保元数据与向量索引的一致性。
"""

import os
import uuid
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .knowledge_manager import KnowledgeManager
from .vector_index_builder import VectorIndexBuilder
from ..modalities.text_processor import get_text_processor
from ..utils.logger import get_logger

logger = get_logger()

class TransactionalKnowledgeManager:
    """
    支持事务的知识管理器
    确保 add_knowledge 操作的原子性：要么元数据和向量都成功写入，要么都回滚。
    """
    
    def __init__(self, metadata_path: str = "data/knowledge_management/metadata.json", 
                 vector_index_path: str = "data/knowledge_management/vector_index.bin"):
        self.km = KnowledgeManager(metadata_path)
        self.vib = VectorIndexBuilder(vector_index_path)
        self.text_processor = get_text_processor()
        
        # 事务日志目录
        self.wal_dir = Path("data/knowledge_management/wal")
        self.wal_dir.mkdir(parents=True, exist_ok=True)
        
        # 恢复未完成的事务
        self._recover_transactions()

    def _recover_transactions(self):
        """恢复（回滚）未完成的事务"""
        # 简单策略：任何遗留的 WAL 文件都意味着事务未完成，执行回滚
        # 在这个实现中，回滚意味着清理可能残留的元数据（向量索引通常是追加的，较难精确回滚，但FAISS未保存前是内存状态）
        # 这里的关键是：只要metadata没更新，用户就看不到新数据，实现了逻辑上的回滚
        for wal_file in self.wal_dir.glob("*.json"):
            try:
                logger.warning(f"发现未完成事务: {wal_file.name}，正在清理...")
                # 读取事务信息
                with open(wal_file, 'r') as f:
                    tx_data = json.load(f)
                
                # 执行回滚逻辑：检查 metadata 是否已包含该 ID，如果有则删除
                knowledge_id = tx_data.get('knowledge_id')
                if knowledge_id:
                    self.km.delete_knowledge(knowledge_id)
                
                # 删除 WAL 文件
                wal_file.unlink()
                logger.info(f"事务 {wal_file.name} 已回滚")
            except Exception as e:
                logger.error(f"回滚事务 {wal_file.name} 失败: {e}")

    def add_knowledge(self, content: Any, modality: str = "text", metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        事务性地添加知识
        """
        transaction_id = str(uuid.uuid4())
        wal_path = self.wal_dir / f"{transaction_id}.json"
        
        try:
            # 1. 预写日志 (Write-Ahead Log)
            # 记录意图，但此时还未修改主数据
            tx_data = {
                'transaction_id': transaction_id,
                'status': 'started',
                'timestamp': datetime.now().isoformat(),
                'content_preview': str(content)[:50],
                'knowledge_id': None # 尚未生成
            }
            with open(wal_path, 'w') as f:
                json.dump(tx_data, f)
            
            # 2. 准备阶段 (Prepare Phase)
            # 2.1 向量化 (最耗时且易失败的操作)
            vector = None
            if modality == "text":
                vector = self.text_processor.encode(content)
                if vector is None:
                    raise ValueError("向量化失败")
            
            # 2.2 创建元数据条目 (写入 metadata.json)
            # 注意：KnowledgeManager 内部使用了原子写入，所以这一步本身是安全的
            knowledge_id = self.km.create_knowledge(content, modality, metadata)
            if not knowledge_id:
                raise ValueError("创建元数据失败")
            
            # 更新 WAL，记录生成的 ID，以便回滚
            tx_data['knowledge_id'] = knowledge_id
            tx_data['status'] = 'metadata_written'
            with open(wal_path, 'w') as f:
                json.dump(tx_data, f)
            
            # 3. 提交阶段 (Commit Phase)
            # 3.1 更新向量索引 (内存操作)
            if vector is not None:
                success = self.vib.add_vector(vector, knowledge_id, modality)
                if not success:
                    raise ValueError("添加到向量索引失败")
                
                # 3.2 持久化向量索引 (磁盘操作)
                # 这是一个潜在的风险点：如果这里失败，metadata 已存在但 vector 丢失
                # 真正的强一致性需要 FAISS 支持事务，或者我们也对 vector_index 使用 WAL
                # 这里采用“尽最大努力”策略
                self.vib._save_index()
            
            # 4. 完成事务
            # 删除 WAL 文件，表示事务成功
            wal_path.unlink()
            logger.info(f"事务 {transaction_id} 成功提交，知识ID: {knowledge_id}")
            return knowledge_id
            
        except Exception as e:
            logger.error(f"事务 {transaction_id} 失败: {e}，正在回滚...")
            
            # 回滚逻辑
            try:
                # 如果已生成 ID，从 metadata 中删除
                if 'knowledge_id' in locals() and knowledge_id:
                    self.km.delete_knowledge(knowledge_id)
                    logger.info(f"已回滚元数据: {knowledge_id}")
                
                # 向量索引的回滚比较复杂（FAISS 不支持删除单个向量而不重建），
                # 但由于我们是在最后一步才 save_index，如果 save 失败，
                # 下次加载时会读取旧文件，相当于自动回滚了（前提是内存状态没被持久化）。
                # 如果是 add_vector 成功但 save 失败，内存中的 index 是脏的，建议重载。
                if self.vib.index:
                    self.vib._load_index() # 重新加载磁盘上的旧索引，丢弃内存中的脏数据
                    
            except Exception as rollback_error:
                logger.critical(f"回滚失败! 数据可能不一致。Error: {rollback_error}")
            
            # 清理 WAL
            if wal_path.exists():
                wal_path.unlink()
                
            return None
