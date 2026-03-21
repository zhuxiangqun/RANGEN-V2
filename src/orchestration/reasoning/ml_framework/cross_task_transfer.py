"""
跨任务知识迁移 - 在不同查询类型之间迁移学习到的知识

功能：
- 模式复用
- 经验共享
- 知识迁移
"""
import logging
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class CrossTaskKnowledgeTransfer:
    """跨任务知识迁移
    
    在不同查询类型之间迁移学习到的知识：
    - 模式复用
    - 经验共享
    - 策略迁移
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化跨任务知识迁移
        
        Args:
            config: 配置字典
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # 知识库：存储不同任务类型的知识
        self.knowledge_base = defaultdict(dict)
        
        # 迁移历史
        self.transfer_history = []
        
        # 相似度阈值
        self.similarity_threshold = self.config.get("similarity_threshold", 0.7)
        
    def transfer_knowledge(
        self,
        source_task_type: str,
        target_task_type: str,
        knowledge_type: str = "pattern"
    ) -> Dict[str, Any]:
        """迁移知识从源任务类型到目标任务类型
        
        Args:
            source_task_type: 源任务类型（如"historical_query"）
            target_task_type: 目标任务类型（如"factual_query"）
            knowledge_type: 知识类型（"pattern", "strategy", "template"）
            
        Returns:
            迁移结果，包含：
                - success: 是否成功
                - transferred_items: 迁移的知识项
                - confidence: 迁移置信度
        """
        try:
            # 1. 检查源任务是否有知识
            if source_task_type not in self.knowledge_base:
                return {
                    "success": False,
                    "transferred_items": [],
                    "confidence": 0.0,
                    "error": f"源任务类型 '{source_task_type}' 没有知识"
                }
            
            source_knowledge = self.knowledge_base[source_task_type]
            
            # 2. 提取可迁移的知识
            transferable_items = self._extract_transferable_knowledge(
                source_knowledge, knowledge_type
            )
            
            if not transferable_items:
                return {
                    "success": False,
                    "transferred_items": [],
                    "confidence": 0.0,
                    "error": "没有可迁移的知识"
                }
            
            # 3. 计算迁移置信度
            confidence = self._calculate_transfer_confidence(
                source_task_type, target_task_type, transferable_items
            )
            
            # 4. 执行迁移
            if confidence >= self.similarity_threshold:
                transferred_items = self._execute_transfer(
                    target_task_type, transferable_items, knowledge_type
                )
                
                # 记录迁移历史
                self.transfer_history.append({
                    "source_task": source_task_type,
                    "target_task": target_task_type,
                    "knowledge_type": knowledge_type,
                    "items_count": len(transferred_items),
                    "confidence": confidence,
                })
                
                self.logger.info(
                    f"✅ 知识迁移成功: {source_task_type} -> {target_task_type}, "
                    f"迁移了 {len(transferred_items)} 项知识，置信度: {confidence:.2f}"
                )
                
                return {
                    "success": True,
                    "transferred_items": transferred_items,
                    "confidence": confidence,
                }
            else:
                return {
                    "success": False,
                    "transferred_items": [],
                    "confidence": confidence,
                    "error": f"迁移置信度 {confidence:.2f} 低于阈值 {self.similarity_threshold}"
                }
                
        except Exception as e:
            self.logger.error(f"知识迁移失败: {e}")
            return {
                "success": False,
                "transferred_items": [],
                "confidence": 0.0,
                "error": str(e)
            }
    
    def store_knowledge(
        self,
        task_type: str,
        knowledge_type: str,
        knowledge_item: Dict[str, Any]
    ) -> bool:
        """存储知识
        
        Args:
            task_type: 任务类型
            knowledge_type: 知识类型
            knowledge_item: 知识项
            
        Returns:
            是否存储成功
        """
        try:
            if knowledge_type not in self.knowledge_base[task_type]:
                self.knowledge_base[task_type][knowledge_type] = []
            
            self.knowledge_base[task_type][knowledge_type].append(knowledge_item)
            self.logger.debug(f"✅ 存储知识: {task_type}/{knowledge_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"存储知识失败: {e}")
            return False
    
    def get_knowledge(
        self,
        task_type: str,
        knowledge_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取知识
        
        Args:
            task_type: 任务类型
            knowledge_type: 知识类型（可选，如果为None则返回所有类型）
            
        Returns:
            知识字典
        """
        if task_type not in self.knowledge_base:
            return {}
        
        if knowledge_type:
            return self.knowledge_base[task_type].get(knowledge_type, [])
        else:
            return self.knowledge_base[task_type]
    
    def _extract_transferable_knowledge(
        self,
        source_knowledge: Dict[str, Any],
        knowledge_type: str
    ) -> List[Dict[str, Any]]:
        """提取可迁移的知识"""
        if knowledge_type not in source_knowledge:
            return []
        
        knowledge_items = source_knowledge[knowledge_type]
        
        # 过滤可迁移的知识（例如，通用模式可以迁移，特定模式不能）
        transferable = []
        for item in knowledge_items:
            if self._is_transferable(item):
                transferable.append(item)
        
        return transferable
    
    def _is_transferable(self, knowledge_item: Dict[str, Any]) -> bool:
        """判断知识项是否可迁移"""
        # 简单的判断：如果知识项标记为通用，则可以迁移
        if knowledge_item.get("is_generic", False):
            return True
        
        # 如果知识项有明确的适用范围，检查是否包含通用标记
        scope = knowledge_item.get("scope", [])
        if "generic" in scope or "universal" in scope:
            return True
        
        return False
    
    def _calculate_transfer_confidence(
        self,
        source_task_type: str,
        target_task_type: str,
        transferable_items: List[Dict[str, Any]]
    ) -> float:
        """计算迁移置信度"""
        # 简单的置信度计算：基于任务类型相似度
        # 未来可以基于语义相似度或历史迁移成功率
        
        # 任务类型相似度映射
        task_similarity_map = {
            ("historical_query", "factual_query"): 0.8,
            ("factual_query", "historical_query"): 0.8,
            ("relational_query", "factual_query"): 0.7,
            ("factual_query", "relational_query"): 0.7,
            # 相同类型
            ("historical_query", "historical_query"): 1.0,
            ("factual_query", "factual_query"): 1.0,
        }
        
        # 获取基础相似度
        base_similarity = task_similarity_map.get(
            (source_task_type, target_task_type), 0.5
        )
        
        # 根据可迁移知识项数量调整
        item_count_factor = min(len(transferable_items) / 10.0, 1.0)
        
        confidence = base_similarity * (0.7 + 0.3 * item_count_factor)
        
        return min(confidence, 1.0)
    
    def _execute_transfer(
        self,
        target_task_type: str,
        transferable_items: List[Dict[str, Any]],
        knowledge_type: str
    ) -> List[Dict[str, Any]]:
        """执行知识迁移"""
        transferred = []
        
        for item in transferable_items:
            # 创建迁移后的知识项
            transferred_item = item.copy()
            transferred_item["source"] = "transferred"
            transferred_item["original_task"] = item.get("task_type", "unknown")
            
            # 存储到目标任务类型
            if self.store_knowledge(target_task_type, knowledge_type, transferred_item):
                transferred.append(transferred_item)
        
        return transferred
    
    def find_similar_patterns(
        self,
        query: str,
        task_type: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """查找相似模式（跨任务类型）
        
        Args:
            query: 查询文本
            task_type: 当前任务类型
            top_k: 返回前k个相似模式
            
        Returns:
            相似模式列表
        """
        similar_patterns = []
        
        # 在所有任务类型中查找相似模式
        for other_task_type, knowledge in self.knowledge_base.items():
            if other_task_type == task_type:
                continue  # 跳过当前任务类型
            
            patterns = knowledge.get("pattern", [])
            for pattern in patterns:
                similarity = self._calculate_pattern_similarity(query, pattern)
                if similarity > 0.5:  # 相似度阈值
                    similar_patterns.append({
                        "pattern": pattern,
                        "task_type": other_task_type,
                        "similarity": similarity,
                    })
        
        # 按相似度排序
        similar_patterns.sort(key=lambda x: x["similarity"], reverse=True)
        
        return similar_patterns[:top_k]
    
    def _calculate_pattern_similarity(
        self,
        query: str,
        pattern: Dict[str, Any]
    ) -> float:
        """计算查询和模式的相似度"""
        # 简单的相似度计算：基于关键词重叠
        # 未来可以使用语义相似度（如Sentence-BERT）
        
        pattern_text = pattern.get("template", "") or pattern.get("text", "")
        if not pattern_text:
            return 0.0
        
        # 提取关键词
        import re
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        pattern_words = set(re.findall(r'\b\w+\b', pattern_text.lower()))
        
        # 移除占位符
        pattern_words = {w for w in pattern_words if not w.startswith('[') and not w.endswith(']')}
        
        # 计算重叠度
        if pattern_words:
            overlap = len(query_words & pattern_words) / len(pattern_words)
        else:
            overlap = 0.0
        
        return overlap

