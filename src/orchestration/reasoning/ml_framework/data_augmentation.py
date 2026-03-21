"""
数据增强模块 - 生成更多并行查询样本

用于解决数据不平衡问题，通过数据增强技术生成更多并行查询样本。
"""
import logging
import random
import re
from typing import List, Dict, Any, Optional
from copy import deepcopy

logger = logging.getLogger(__name__)


class DataAugmentation:
    """数据增强器 - 生成更多并行查询样本"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化数据增强器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 并行查询模板
        self.parallel_query_templates = [
            # 模板1: "If X and Y, what is Z?"
            {
                "pattern": r"if\s+(.+?)\s+and\s+(.+?),\s+what\s+is\s+(.+?)\?",
                "variations": [
                    "If {condition1} and {condition2}, what is {result}?",
                    "Given that {condition1} and {condition2}, what is {result}?",
                    "When {condition1} and {condition2}, what is {result}?",
                ]
            },
            # 模板2: "What is X and Y?"
            {
                "pattern": r"what\s+is\s+(.+?)\s+and\s+(.+?)\?",
                "variations": [
                    "What is {item1} and {item2}?",
                    "Tell me about {item1} and {item2}.",
                    "I need to know {item1} and {item2}.",
                ]
            },
            # 模板3: "Who was X and Y?"
            {
                "pattern": r"who\s+was\s+(.+?)\s+and\s+(.+?)\?",
                "variations": [
                    "Who was {person1} and {person2}?",
                    "Tell me about {person1} and {person2}.",
                ]
            },
        ]
        
        # 实体替换规则
        self.entity_replacements = {
            "first lady": ["first lady", "president's wife", "presidential spouse"],
            "president": ["president", "commander-in-chief", "head of state"],
            "mother": ["mother", "mom", "parent"],
            "father": ["father", "dad", "parent"],
            "maiden name": ["maiden name", "birth name", "family name"],
        }
    
    def augment_parallel_queries(
        self,
        queries: List[str],
        labels: List[bool],
        target_ratio: float = 0.1
    ) -> tuple[List[str], List[bool]]:
        """增强并行查询数据
        
        Args:
            queries: 原始查询列表
            labels: 原始标签列表（True表示并行查询）
            target_ratio: 目标正样本比例（默认0.1，即10%）
            
        Returns:
            (增强后的查询列表, 增强后的标签列表)
        """
        try:
            # 分离正负样本
            positive_queries = [q for q, l in zip(queries, labels) if l]
            negative_queries = [q for q, l in zip(queries, labels) if not l]
            
            if not positive_queries:
                self.logger.warning("⚠️ 没有正样本，无法进行数据增强")
                return queries, labels
            
            # 计算需要生成的正样本数量
            total_samples = len(queries)
            current_positive = len(positive_queries)
            target_positive = int(total_samples * target_ratio)
            needed_positive = max(0, target_positive - current_positive)
            
            if needed_positive == 0:
                self.logger.info(f"✅ 正样本比例已达到目标 ({current_positive}/{total_samples} = {current_positive/total_samples:.2%})")
                return queries, labels
            
            self.logger.info(f"📊 数据增强: 当前正样本 {current_positive}/{total_samples} ({current_positive/total_samples:.2%})")
            self.logger.info(f"   目标正样本: {target_positive} ({target_ratio:.1%})")
            self.logger.info(f"   需要生成: {needed_positive} 个正样本")
            
            # 生成增强样本
            augmented_queries = []
            augmented_labels = []
            
            # 方法1: 基于模板生成
            template_generated = self._generate_from_templates(positive_queries, needed_positive // 2)
            augmented_queries.extend(template_generated)
            augmented_labels.extend([True] * len(template_generated))
            
            # 方法2: 实体替换
            replacement_generated = self._generate_by_replacement(positive_queries, needed_positive - len(template_generated))
            augmented_queries.extend(replacement_generated)
            augmented_labels.extend([True] * len(replacement_generated))
            
            # 合并结果
            result_queries = queries + augmented_queries
            result_labels = labels + augmented_labels
            
            self.logger.info(f"✅ 数据增强完成: 生成了 {len(augmented_queries)} 个正样本")
            self.logger.info(f"   最终正样本: {len([l for l in result_labels if l])}/{len(result_labels)} ({len([l for l in result_labels if l])/len(result_labels):.2%})")
            
            return result_queries, result_labels
            
        except Exception as e:
            self.logger.error(f"❌ 数据增强失败: {e}", exc_info=True)
            return queries, labels
    
    def _generate_from_templates(
        self,
        positive_queries: List[str],
        count: int
    ) -> List[str]:
        """基于模板生成新查询"""
        generated = []
        
        for _ in range(count):
            if not positive_queries:
                break
            
            # 随机选择一个正样本作为基础
            base_query = random.choice(positive_queries)
            
            # 尝试匹配模板
            for template in self.parallel_query_templates:
                match = re.search(template["pattern"], base_query.lower())
                if match:
                    # 使用模板生成变体
                    variation = random.choice(template["variations"])
                    # 这里可以进一步处理，提取匹配组并替换
                    # 简化版本：直接使用变体模板
                    generated.append(variation)
                    break
        
        return generated[:count]
    
    def _generate_by_replacement(
        self,
        positive_queries: List[str],
        count: int
    ) -> List[str]:
        """通过实体替换生成新查询"""
        generated = []
        
        for _ in range(count):
            if not positive_queries:
                break
            
            # 随机选择一个正样本
            base_query = random.choice(positive_queries)
            
            # 进行实体替换
            augmented_query = base_query
            for entity, replacements in self.entity_replacements.items():
                if entity in augmented_query.lower():
                    replacement = random.choice(replacements)
                    # 简单替换（可以改进为更智能的替换）
                    augmented_query = re.sub(
                        r'\b' + re.escape(entity) + r'\b',
                        replacement,
                        augmented_query,
                        flags=re.IGNORECASE
                    )
            
            if augmented_query != base_query:
                generated.append(augmented_query)
        
        return generated[:count]
    
    def augment_with_synonyms(
        self,
        query: str,
        max_variations: int = 3
    ) -> List[str]:
        """通过同义词替换生成查询变体
        
        Args:
            query: 原始查询
            max_variations: 最大变体数量
            
        Returns:
            查询变体列表
        """
        variations = [query]  # 包含原始查询
        
        # 同义词替换规则
        synonym_rules = {
            r'\bwho\b': ['who', 'what person', 'which person'],
            r'\bwhat\b': ['what', 'which', 'tell me about'],
            r'\bwhen\b': ['when', 'at what time', 'on what date'],
            r'\bwhere\b': ['where', 'in what place', 'at what location'],
            r'\bthe same\b': ['the same', 'identical', 'equal'],
            r'\band\b': ['and', 'as well as', 'plus'],
        }
        
        for pattern, synonyms in list(synonym_rules.items())[:max_variations]:
            if re.search(pattern, query, re.IGNORECASE):
                for synonym in synonyms[1:]:  # 跳过第一个（原始词）
                    variation = re.sub(
                        pattern,
                        synonym,
                        query,
                        flags=re.IGNORECASE,
                        count=1
                    )
                    if variation not in variations:
                        variations.append(variation)
                        if len(variations) >= max_variations + 1:
                            break
                if len(variations) >= max_variations + 1:
                    break
        
        return variations[1:]  # 返回变体（不包含原始查询）

