#!/usr/bin/env python3
"""
动态Chunk大小管理器
基于ML/RL动态调整chunk大小，优化检索效果
"""

import json
import time
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict
from ..utils.logger import get_logger

logger = get_logger()


@dataclass
class ChunkConfig:
    """Chunk配置"""
    max_chunk_size: int
    overlap_ratio: float
    chunk_strategy: str
    enable_lazy_chunking: bool


@dataclass
class ChunkPerformance:
    """Chunk性能指标"""
    query_type: str
    query_complexity: str
    chunk_size: int
    retrieval_precision: float
    answer_accuracy: float
    processing_time: float
    timestamp: float


class DynamicChunkManager:
    """动态Chunk大小管理器 - 基于ML/RL优化"""
    
    def __init__(
        self,
        data_path: str = "data/learning/chunk_optimization.json",
        base_chunk_size: int = 3000,
        base_overlap_ratio: float = 0.2
    ):
        """
        初始化动态Chunk管理器
        
        Args:
            data_path: 学习数据存储路径
            base_chunk_size: 基础chunk大小（字符数）
            base_overlap_ratio: 基础重叠比例
        """
        self.logger = logger
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 基础配置
        self.base_chunk_size = base_chunk_size
        self.base_overlap_ratio = base_overlap_ratio
        
        # 性能历史记录
        self.performance_history: List[ChunkPerformance] = []
        
        # ML学习数据：查询特征 -> 最优chunk大小
        self.ml_learning_data: Dict[str, Dict[str, Any]] = {}
        
        # RL Q表：状态 -> 动作 -> Q值
        self.rl_q_table: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        # 统计信息
        self.stats = {
            'total_queries': 0,
            'ml_predictions': 0,
            'rl_optimizations': 0,
            'avg_improvement': 0.0
        }
        
        # 加载历史数据
        self._load_history()
        
        # 初始化ML/RL组件
        self._init_ml_rl_components()
    
    def _init_ml_rl_components(self):
        """初始化ML/RL组件"""
        try:
            # 尝试导入ML/RL组件
            from src.core.reinforcement_learning_optimizer import ReinforcementLearningOptimizer
            from src.agents.learning_system import LearningSystem
            
            self.rl_optimizer = ReinforcementLearningOptimizer()
            self.learning_system = LearningSystem()
            self.ml_rl_enabled = True
            self.logger.info("✅ ML/RL组件初始化成功")
        except Exception as e:
            self.logger.warning(f"⚠️ ML/RL组件初始化失败: {e}，将使用基于规则的动态调整")
            self.rl_optimizer = None
            self.learning_system = None
            self.ml_rl_enabled = False
    
    def _load_history(self):
        """加载历史学习数据"""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if 'performance_history' in data:
                        # 加载性能历史（最近1000条）
                        history = data['performance_history'][-1000:]
                        self.performance_history = [
                            ChunkPerformance(**item) for item in history
                        ]
                    
                    if 'ml_learning_data' in data:
                        self.ml_learning_data = data['ml_learning_data']
                    
                    if 'rl_q_table' in data:
                        self.rl_q_table = defaultdict(
                            lambda: defaultdict(float),
                            {k: defaultdict(float, v) for k, v in data['rl_q_table'].items()}
                        )
                    
                    if 'stats' in data:
                        self.stats.update(data['stats'])
                    
                    self.logger.info(f"✅ 加载Chunk优化历史数据: 性能记录={len(self.performance_history)}, ML数据={len(self.ml_learning_data)}")
        except Exception as e:
            self.logger.warning(f"加载Chunk优化历史数据失败: {e}")
    
    def _save_history(self):
        """保存历史学习数据"""
        try:
            # 只保存最近1000条性能记录
            recent_history = self.performance_history[-1000:]
            
            data = {
                'performance_history': [asdict(perf) for perf in recent_history],
                'ml_learning_data': self.ml_learning_data,
                'rl_q_table': {
                    state: dict(actions)
                    for state, actions in self.rl_q_table.items()
                },
                'stats': self.stats
            }
            
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存Chunk优化历史数据失败: {e}")
    
    def get_optimal_chunk_config(
        self,
        query: str,
        query_type: Optional[str] = None,
        query_complexity: Optional[str] = None,
        document_type: Optional[str] = None,
        document_length: Optional[int] = None
    ) -> ChunkConfig:
        """
        🚀 获取最优Chunk配置（基于ML/RL）
        
        Args:
            query: 查询文本
            query_type: 查询类型（factual, multi_hop, comparative等）
            query_complexity: 查询复杂度（simple, medium, complex, very_complex）
            document_type: 文档类型（technical, legal, general等）
            document_length: 文档长度（字符数）
            
        Returns:
            ChunkConfig: 最优chunk配置
        """
        try:
            # 1. 提取特征
            features = self._extract_features(
                query, query_type, query_complexity, document_type, document_length
            )
            
            # 2. ML预测：根据历史数据预测最优chunk大小
            predicted_config = self._ml_predict_chunk_size(features)
            
            # 3. RL优化：根据Q表选择最优动作（调整chunk大小）
            if self.ml_rl_enabled and self.rl_optimizer:
                optimized_config = self._rl_optimize_chunk_size(features, predicted_config)
                if optimized_config:
                    predicted_config = optimized_config
            
            # 4. 应用约束：确保chunk大小在合理范围内
            final_config = self._apply_constraints(predicted_config)
            
            self.stats['total_queries'] += 1
            if predicted_config != final_config:
                self.stats['ml_predictions'] += 1
            
            return final_config
            
        except Exception as e:
            self.logger.warning(f"获取最优Chunk配置失败: {e}，使用默认配置")
            return ChunkConfig(
                max_chunk_size=self.base_chunk_size,
                overlap_ratio=self.base_overlap_ratio,
                chunk_strategy="recursive",
                enable_lazy_chunking=True
            )
    
    def _extract_features(
        self,
        query: str,
        query_type: Optional[str],
        query_complexity: Optional[str],
        document_type: Optional[str],
        document_length: Optional[int]
    ) -> Dict[str, Any]:
        """提取特征用于ML/RL"""
        # 如果没有提供，尝试推断
        if not query_type:
            query_type = self._infer_query_type(query)
        
        if not query_complexity:
            query_complexity = self._infer_complexity(query)
        
        return {
            'query_type': query_type,
            'query_complexity': query_complexity,
            'query_length': len(query),
            'document_type': document_type or 'general',
            'document_length': document_length or 0
        }
    
    def _infer_query_type(self, query: str) -> str:
        """推断查询类型"""
        query_lower = query.lower()
        
        # 多跳查询
        if any(keyword in query_lower for keyword in ['same as', 'mother', 'father', 'named after', 'from the']):
            return 'multi_hop'
        
        # 比较查询
        if any(keyword in query_lower for keyword in ['compare', 'difference', 'vs', 'versus']):
            return 'comparative'
        
        # 因果查询
        if any(keyword in query_lower for keyword in ['why', 'because', 'cause', 'reason']):
            return 'causal'
        
        # 数值查询
        if any(keyword in query_lower for keyword in ['how many', 'how much', 'number', 'count']):
            return 'numerical'
        
        # 事实查询
        if any(keyword in query_lower for keyword in ['who', 'what', 'when', 'where']):
            return 'factual'
        
        return 'general'
    
    def _infer_complexity(self, query: str) -> str:
        """推断查询复杂度"""
        query_length = len(query)
        
        # 简单查询：短且直接
        if query_length < 50:
            return 'simple'
        
        # 复杂查询：长且包含多个实体/关系
        if query_length > 150 or query.count(' and ') > 1 or query.count(' or ') > 1:
            return 'complex'
        
        # 非常复杂：包含多个关系
        if query.count("'s ") > 2 or query.count(' of ') > 2:
            return 'very_complex'
        
        return 'medium'
    
    def _ml_predict_chunk_size(self, features: Dict[str, Any]) -> ChunkConfig:
        """
        🚀 ML预测：根据历史数据预测最优chunk大小
        """
        try:
            # 构建特征键
            feature_key = self._features_to_key(features)
            
            # 查找历史数据中的最优配置
            if feature_key in self.ml_learning_data:
                learned_config = self.ml_learning_data[feature_key]
                return ChunkConfig(
                    max_chunk_size=learned_config.get('optimal_chunk_size', self.base_chunk_size),
                    overlap_ratio=learned_config.get('optimal_overlap_ratio', self.base_overlap_ratio),
                    chunk_strategy=learned_config.get('optimal_strategy', 'recursive'),
                    enable_lazy_chunking=learned_config.get('enable_lazy_chunking', True)
                )
            
            # 如果没有历史数据，使用基于规则的预测
            return self._rule_based_predict(features)
            
        except Exception as e:
            self.logger.warning(f"ML预测失败: {e}，使用基于规则的预测")
            return self._rule_based_predict(features)
    
    def _rule_based_predict(self, features: Dict[str, Any]) -> ChunkConfig:
        """
        基于规则的预测（当ML数据不足时使用）
        """
        query_type = features.get('query_type', 'general')
        query_complexity = features.get('query_complexity', 'medium')
        
        # 根据查询类型和复杂度调整chunk大小
        chunk_size = self.base_chunk_size
        overlap_ratio = self.base_overlap_ratio
        strategy = "recursive"
        
        # 复杂查询：使用更大的chunk（更多上下文）
        if query_complexity in ['complex', 'very_complex']:
            chunk_size = int(self.base_chunk_size * 1.2)  # 增加20%
            overlap_ratio = 0.25  # 增加重叠
        
        # 多跳查询：使用更大的chunk（需要更多上下文）
        if query_type == 'multi_hop':
            chunk_size = int(self.base_chunk_size * 1.3)  # 增加30%
            overlap_ratio = 0.25
        
        # 简单查询：可以使用较小的chunk（更快）
        if query_complexity == 'simple':
            chunk_size = int(self.base_chunk_size * 0.8)  # 减少20%
            overlap_ratio = 0.15  # 减少重叠
        
        # 数值查询：使用中等chunk（精确匹配）
        if query_type == 'numerical':
            chunk_size = self.base_chunk_size
            overlap_ratio = 0.2
        
        return ChunkConfig(
            max_chunk_size=chunk_size,
            overlap_ratio=overlap_ratio,
            chunk_strategy=strategy,
            enable_lazy_chunking=True
        )
    
    def _rl_optimize_chunk_size(
        self,
        features: Dict[str, Any],
        ml_config: ChunkConfig
    ) -> Optional[ChunkConfig]:
        """
        🚀 RL优化：根据Q表选择最优动作（调整chunk大小）
        """
        try:
            if not self.ml_rl_enabled or not self.rl_optimizer:
                return None
            
            # 构建状态
            state_key = self._features_to_key(features)
            
            # 生成可用动作（调整chunk大小）
            available_actions = self._generate_chunk_actions(ml_config)
            
            # 使用RL选择最优动作
            if state_key in self.rl_q_table and self.rl_q_table[state_key]:
                # 选择Q值最高的动作
                best_action_key = max(
                    self.rl_q_table[state_key].items(),
                    key=lambda x: x[1]
                )[0]
                
                # 解析动作并应用
                optimized_config = self._apply_action(ml_config, best_action_key)
                if optimized_config:
                    self.stats['rl_optimizations'] += 1
                    return optimized_config
            
            return None
            
        except Exception as e:
            self.logger.debug(f"RL优化失败: {e}，使用ML预测结果")
            return None
    
    def _generate_chunk_actions(self, base_config: ChunkConfig) -> List[str]:
        """生成可用的chunk调整动作"""
        actions = []
        
        # 动作：调整chunk大小（±10%, ±20%, ±30%）
        for adjustment in [-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3]:
            new_size = int(base_config.max_chunk_size * (1 + adjustment))
            if 1000 <= new_size <= 5000:  # 合理范围
                actions.append(f"size_{adjustment:.1f}")
        
        # 动作：调整overlap比例
        for overlap in [0.1, 0.15, 0.2, 0.25, 0.3]:
            actions.append(f"overlap_{overlap:.2f}")
        
        return actions
    
    def _apply_action(self, base_config: ChunkConfig, action_key: str) -> Optional[ChunkConfig]:
        """应用RL动作"""
        try:
            if action_key.startswith("size_"):
                adjustment = float(action_key.split("_")[1])
                new_size = int(base_config.max_chunk_size * (1 + adjustment))
                if 1000 <= new_size <= 5000:
                    return ChunkConfig(
                        max_chunk_size=new_size,
                        overlap_ratio=base_config.overlap_ratio,
                        chunk_strategy=base_config.chunk_strategy,
                        enable_lazy_chunking=base_config.enable_lazy_chunking
                    )
            elif action_key.startswith("overlap_"):
                new_overlap = float(action_key.split("_")[1])
                return ChunkConfig(
                    max_chunk_size=base_config.max_chunk_size,
                    overlap_ratio=new_overlap,
                    chunk_strategy=base_config.chunk_strategy,
                    enable_lazy_chunking=base_config.enable_lazy_chunking
                )
        except Exception:
            pass
        return None
    
    def _apply_constraints(self, config: ChunkConfig) -> ChunkConfig:
        """应用约束：确保chunk大小在合理范围内"""
        # 约束：chunk大小在1000-5000字符之间
        chunk_size = max(1000, min(5000, config.max_chunk_size))
        
        # 约束：overlap比例在0.1-0.3之间
        overlap_ratio = max(0.1, min(0.3, config.overlap_ratio))
        
        return ChunkConfig(
            max_chunk_size=chunk_size,
            overlap_ratio=overlap_ratio,
            chunk_strategy=config.chunk_strategy,
            enable_lazy_chunking=config.enable_lazy_chunking
        )
    
    def _features_to_key(self, features: Dict[str, Any]) -> str:
        """将特征转换为键"""
        return f"{features.get('query_type', 'general')}_{features.get('query_complexity', 'medium')}"
    
    def record_performance(
        self,
        query_type: str,
        query_complexity: str,
        chunk_size: int,
        retrieval_precision: float,
        answer_accuracy: float,
        processing_time: float
    ):
        """
        🚀 记录性能数据，用于ML/RL学习
        
        Args:
            query_type: 查询类型
            query_complexity: 查询复杂度
            chunk_size: 使用的chunk大小
            retrieval_precision: 检索精度
            answer_accuracy: 答案准确率
            processing_time: 处理时间
        """
        try:
            performance = ChunkPerformance(
                query_type=query_type,
                query_complexity=query_complexity,
                chunk_size=chunk_size,
                retrieval_precision=retrieval_precision,
                answer_accuracy=answer_accuracy,
                processing_time=processing_time,
                timestamp=time.time()
            )
            
            self.performance_history.append(performance)
            
            # 更新ML学习数据
            self._update_ml_learning_data(performance)
            
            # 更新RL Q表
            if self.ml_rl_enabled:
                self._update_rl_q_table(performance)
            
            # 定期保存
            if len(self.performance_history) % 10 == 0:
                self._save_history()
            
        except Exception as e:
            self.logger.warning(f"记录性能数据失败: {e}")
    
    def _update_ml_learning_data(self, performance: ChunkPerformance):
        """更新ML学习数据"""
        try:
            feature_key = f"{performance.query_type}_{performance.query_complexity}"
            
            if feature_key not in self.ml_learning_data:
                self.ml_learning_data[feature_key] = {
                    'chunk_sizes': [],
                    'performances': [],
                    'optimal_chunk_size': performance.chunk_size,
                    'optimal_overlap_ratio': 0.2,
                    'optimal_strategy': 'recursive',
                    'best_accuracy': performance.answer_accuracy
                }
            
            data = self.ml_learning_data[feature_key]
            data['chunk_sizes'].append(performance.chunk_size)
            data['performances'].append({
                'accuracy': performance.answer_accuracy,
                'precision': performance.retrieval_precision,
                'time': performance.processing_time
            })
            
            # 只保留最近100条记录
            if len(data['chunk_sizes']) > 100:
                data['chunk_sizes'] = data['chunk_sizes'][-100:]
                data['performances'] = data['performances'][-100:]
            
            # 更新最优配置（基于答案准确率）
            if performance.answer_accuracy > data['best_accuracy']:
                data['best_accuracy'] = performance.answer_accuracy
                data['optimal_chunk_size'] = performance.chunk_size
            
            # 计算平均性能，找到最优chunk大小
            if len(data['performances']) >= 5:
                # 按chunk大小分组，计算平均准确率
                size_performance = defaultdict(list)
                for i, size in enumerate(data['chunk_sizes']):
                    size_performance[size].append(data['performances'][i]['accuracy'])
                
                # 找到平均准确率最高的chunk大小
                best_size = max(
                    size_performance.items(),
                    key=lambda x: sum(x[1]) / len(x[1])
                )[0]
                
                data['optimal_chunk_size'] = best_size
            
        except Exception as e:
            self.logger.debug(f"更新ML学习数据失败: {e}")
    
    def _update_rl_q_table(self, performance: ChunkPerformance):
        """更新RL Q表"""
        try:
            if not self.ml_rl_enabled or not self.rl_optimizer:
                return
            
            # 构建状态键
            state_key = f"{performance.query_type}_{performance.query_complexity}"
            
            # 计算奖励（基于答案准确率和处理时间）
            reward = performance.answer_accuracy * 0.7 - (performance.processing_time / 200.0) * 0.3
            
            # 构建动作键
            action_key = f"size_{performance.chunk_size}"
            
            # 更新Q值（简化版Q-learning）
            if state_key not in self.rl_q_table:
                self.rl_q_table[state_key] = defaultdict(float)
            
            # Q-learning更新：Q(s,a) = Q(s,a) + α * (r - Q(s,a))
            learning_rate = 0.1
            current_q = self.rl_q_table[state_key][action_key]
            self.rl_q_table[state_key][action_key] = current_q + learning_rate * (reward - current_q)
            
        except Exception as e:
            self.logger.debug(f"更新RL Q表失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'performance_history_count': len(self.performance_history),
            'ml_learning_patterns': len(self.ml_learning_data),
            'rl_q_table_size': len(self.rl_q_table),
            'ml_rl_enabled': self.ml_rl_enabled
        }


# 单例模式
_dynamic_chunk_manager_instance = None

def get_dynamic_chunk_manager() -> DynamicChunkManager:
    """获取动态Chunk管理器单例"""
    global _dynamic_chunk_manager_instance
    if _dynamic_chunk_manager_instance is None:
        _dynamic_chunk_manager_instance = DynamicChunkManager()
    return _dynamic_chunk_manager_instance

