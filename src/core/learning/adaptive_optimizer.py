#!/usr/bin/env python3
"""
核心系统自适应优化器 - 阶段1：改进自适应学习
基于历史表现优化模型选择、证据选择和配置参数
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict
import logging

from src.core.unified_parameter_learner import get_parameter_learner


logger = logging.getLogger(__name__)


@dataclass
class TaskPerformance:
    """任务性能记录"""
    query: str
    query_type: str
    model_type: str  # 'fast' or 'reasoning'
    evidence_count: int
    config_params: Dict[str, Any]
    processing_time: float
    confidence: float
    success: bool
    timestamp: float


@dataclass
class OptimizedModelSelection:
    """优化后的模型选择策略"""
    query_type: str
    preferred_model: str  # 'fast' or 'reasoning'
    confidence: float
    complexity_threshold: float  # 复杂度阈值


@dataclass
class OptimizedEvidenceSelection:
    """优化后的证据选择策略"""
    query_type: str
    optimal_evidence_count: int
    min_evidence_count: int
    max_evidence_count: int
    confidence: float


@dataclass
class OptimizedConfigParams:
    """优化后的配置参数"""
    query_type: str
    config_updates: Dict[str, Any]
    confidence: float


class AdaptiveOptimizer:
    """核心系统自适应优化器"""
    
    def __init__(self, data_path: str = "data/learning/adaptive_optimization.json"):
        self.logger = logger
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 性能历史记录
        self.performance_history: List[TaskPerformance] = []
        
        # 优化后的策略
        self.optimized_model_selection: Dict[str, OptimizedModelSelection] = {}
        self.optimized_evidence_selection: Dict[str, OptimizedEvidenceSelection] = {}
        self.optimized_config_params: Dict[str, OptimizedConfigParams] = {}
        
        # 统计信息
        self.stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'avg_processing_time': 0.0,
            'avg_confidence': 0.0,
            'fast_model_usage': 0,
            'reasoning_model_usage': 0
        }
        
        # 加载历史数据
        self._load_history()
        
        # 集成统一参数学习器
        self.parameter_learner = get_parameter_learner()

        self._load_history()
    
    def _load_history(self) -> None:
        """加载历史性能数据"""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 加载性能历史
                    if 'performance_history' in data:
                        self.performance_history = [
                            TaskPerformance(**item) 
                            for item in data['performance_history']
                        ]
                    
                    # 加载优化后的模型选择策略
                    if 'optimized_model_selection' in data:
                        self.optimized_model_selection = {
                            query_type: OptimizedModelSelection(**params)
                            for query_type, params in data['optimized_model_selection'].items()
                        }
                    
                    # 加载优化后的证据选择策略
                    if 'optimized_evidence_selection' in data:
                        self.optimized_evidence_selection = {
                            query_type: OptimizedEvidenceSelection(**params)
                            for query_type, params in data['optimized_evidence_selection'].items()
                        }
                    
                    # 加载优化后的配置参数
                    if 'optimized_config_params' in data:
                        self.optimized_config_params = {
                            query_type: OptimizedConfigParams(**params)
                            for query_type, params in data['optimized_config_params'].items()
                        }
                    
                    # 加载统计信息
                    if 'stats' in data:
                        self.stats.update(data['stats'])
                    
                    self.logger.info(f"✅ 加载历史性能数据: {len(self.performance_history)}条记录")
        except Exception as e:
            self.logger.warning(f"加载历史数据失败: {e}")
    
    def _save_history(self) -> None:
        """保存历史性能数据"""
        try:
            data = {
                'performance_history': [asdict(perf) for perf in self.performance_history[-1000:]],  # 只保留最近1000条
                'optimized_model_selection': {
                    query_type: asdict(params)
                    for query_type, params in self.optimized_model_selection.items()
                },
                'optimized_evidence_selection': {
                    query_type: asdict(params)
                    for query_type, params in self.optimized_evidence_selection.items()
                },
                'optimized_config_params': {
                    query_type: asdict(params)
                    for query_type, params in self.optimized_config_params.items()
                },
                'stats': self.stats
            }
            
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存历史数据失败: {e}")
    
    def record_task_performance(
        self,
        query: str,
        query_type: str,
        model_type: str,
        evidence_count: int,
        config_params: Dict[str, Any],
        processing_time: float,
        confidence: float,
        success: bool
    ) -> None:
        """记录任务性能"""
        try:
            performance = TaskPerformance(
                query=query,
                query_type=query_type,
                model_type=model_type,
                evidence_count=evidence_count,
                config_params=config_params,
                processing_time=processing_time,
                confidence=confidence,
                success=success,
                timestamp=time.time()
            )
            
            self.performance_history.append(performance)
            
            # 更新统计信息
            self.stats['total_tasks'] += 1
            if success:
                self.stats['successful_tasks'] += 1
            else:
                self.stats['failed_tasks'] += 1
            
            if model_type == 'fast':
                self.stats['fast_model_usage'] += 1
            elif model_type == 'reasoning':
                self.stats['reasoning_model_usage'] += 1
            
            # 更新平均值（使用移动平均）
            alpha = 0.1  # 学习率
            self.stats['avg_processing_time'] = (
                alpha * processing_time + (1 - alpha) * self.stats['avg_processing_time']
            )
            self.stats['avg_confidence'] = (
                alpha * confidence + (1 - alpha) * self.stats['avg_confidence']
            )
            
            # 每10条记录保存一次（避免频繁IO）
            if len(self.performance_history) % 10 == 0:
                self._save_history()
                # 触发策略优化
                self._optimize_strategies()
        except Exception as e:
            self.logger.error(f"记录任务性能失败: {e}")
    
    def _optimize_strategies(self) -> None:
        """优化策略（基于统计学习）"""
        try:
            # 🚀 ML/RL优化：降低优化触发条件（从10条降低到5条）
            if len(self.performance_history) < 5:  # 至少需要5条记录（从10降低到5）
                return
            
            # 按查询类型分组
            query_type_performances: Dict[str, List[TaskPerformance]] = defaultdict(list)
            for perf in self.performance_history[-100:]:  # 只使用最近100条记录
                query_type_performances[perf.query_type].append(perf)
            
            # 为每个查询类型优化策略
            for query_type, performances in query_type_performances.items():
                # 🚀 ML/RL优化：降低优化触发条件（从5条降低到3条）
                if len(performances) < 3:  # 至少需要3条记录（从5降低到3）
                    # 🚀 ML/RL优化：使用迁移学习，从相似查询类型学习
                    similar_query_type = self._find_similar_query_type(query_type, query_type_performances)
                    if similar_query_type and len(query_type_performances[similar_query_type]) >= 3:
                        self.logger.info(
                            f"🔄 使用迁移学习: 查询类型 {query_type} 数据不足（{len(performances)}条），"
                            f"从相似类型 {similar_query_type} 学习（{len(query_type_performances[similar_query_type])}条）"
                        )
                        # 使用相似查询类型的策略作为默认策略
                        self._apply_transfer_learning(query_type, similar_query_type, query_type_performances[similar_query_type])
                    continue
                
                # 优化模型选择
                optimized_model = self._optimize_model_selection(query_type, performances)
                if optimized_model:
                    self.optimized_model_selection[query_type] = optimized_model
                
                # 优化证据选择
                optimized_evidence = self._optimize_evidence_selection(query_type, performances)
                if optimized_evidence:
                    self.optimized_evidence_selection[query_type] = optimized_evidence
                
                # 优化配置参数
                optimized_config = self._optimize_config_params(query_type, performances)
                if optimized_config:
                    self.optimized_config_params[query_type] = optimized_config
            
            # 保存优化后的策略
            self._save_history()
        except Exception as e:
            self.logger.error(f"优化策略失败: {e}")
    
    def _optimize_model_selection(
        self,
        query_type: str,
        performances: List[TaskPerformance]
    ) -> Optional[OptimizedModelSelection]:
        """优化模型选择策略"""
        try:
            # 过滤成功的查询
            successful = [p for p in performances if p.success]
            if len(successful) < 3:
                return None
            
            # 分析快速模型和推理模型的表现
            fast_perfs = [p for p in successful if p.model_type == 'fast']
            reasoning_perfs = [p for p in successful if p.model_type == 'reasoning']
            
            if not fast_perfs and not reasoning_perfs:
                return None
            
            # 计算多目标分数（准确率 + 效率）
            # 准确率指标：置信度
            # 效率指标：处理时间
            
            fast_score = 0.0
            reasoning_score = 0.0
            
            if fast_perfs:
                avg_confidence = sum(p.confidence for p in fast_perfs) / len(fast_perfs)
                avg_time = sum(p.processing_time for p in fast_perfs) / len(fast_perfs)
                accuracy_score = avg_confidence
                efficiency_score = 1.0 / (1.0 + avg_time / 100.0)  # 归一化（假设100秒为基准）
                fast_score = accuracy_score * 0.7 + efficiency_score * 0.3
            
            if reasoning_perfs:
                avg_confidence = sum(p.confidence for p in reasoning_perfs) / len(reasoning_perfs)
                avg_time = sum(p.processing_time for p in reasoning_perfs) / len(reasoning_perfs)
                accuracy_score = avg_confidence
                efficiency_score = 1.0 / (1.0 + avg_time / 100.0)
                reasoning_score = accuracy_score * 0.7 + efficiency_score * 0.3
            
            # 选择最优模型
            if fast_perfs and reasoning_perfs:
                preferred_model = 'fast' if fast_score > reasoning_score else 'reasoning'
                # 计算复杂度阈值（基于两种模型的平均置信度差异）
                fast_avg_conf = sum(p.confidence for p in fast_perfs) / len(fast_perfs)
                reasoning_avg_conf = sum(p.confidence for p in reasoning_perfs) / len(reasoning_perfs)
                complexity_threshold = (fast_avg_conf + reasoning_avg_conf) / 2.0
            elif fast_perfs:
                preferred_model = 'fast'
                complexity_threshold = 0.7
            else:
                preferred_model = 'reasoning'
                complexity_threshold = 0.8
            
            # 计算置信度（基于数据量）
            confidence = min(1.0, len(successful) / 50.0)  # 50条记录达到最大置信度
            
            return OptimizedModelSelection(
                query_type=query_type,
                preferred_model=preferred_model,
                confidence=confidence,
                complexity_threshold=complexity_threshold
            )
        except Exception as e:
            self.logger.error(f"优化{query_type}类型模型选择失败: {e}")
            return None
    
    def _optimize_evidence_selection(
        self,
        query_type: str,
        performances: List[TaskPerformance]
    ) -> Optional[OptimizedEvidenceSelection]:
        """优化证据选择策略"""
        try:
            # 过滤成功的查询
            successful = [p for p in performances if p.success]
            if len(successful) < 3:
                return None
            
            # 分析不同证据数量的表现
            evidence_count_scores: Dict[int, float] = {}
            for evidence_count in range(1, 21):  # 1-20个证据
                count_perfs = [p for p in successful if p.evidence_count == evidence_count]
                if not count_perfs:
                    continue
                
                # 计算多目标分数
                avg_confidence = sum(p.confidence for p in count_perfs) / len(count_perfs)
                avg_time = sum(p.processing_time for p in count_perfs) / len(count_perfs)
                accuracy_score = avg_confidence
                efficiency_score = 1.0 / (1.0 + avg_time / 100.0)
                evidence_count_scores[evidence_count] = accuracy_score * 0.7 + efficiency_score * 0.3
            
            if not evidence_count_scores:
                return None
            
            # 选择最优证据数量
            optimal_count = max(evidence_count_scores.items(), key=lambda x: x[1])[0]
            
            # 计算最小和最大证据数量（基于表现较好的范围）
            sorted_counts = sorted(evidence_count_scores.items(), key=lambda x: x[1], reverse=True)
            top_3_counts = [count for count, _ in sorted_counts[:3]]
            min_count = min(top_3_counts)
            max_count = max(top_3_counts)
            
            # 计算置信度
            confidence = min(1.0, len(successful) / 50.0)
            
            return OptimizedEvidenceSelection(
                query_type=query_type,
                optimal_evidence_count=optimal_count,
                min_evidence_count=max(1, min_count - 2),
                max_evidence_count=min(20, max_count + 2),
                confidence=confidence
            )
        except Exception as e:
            self.logger.error(f"优化{query_type}类型证据选择失败: {e}")
            return None
    
    def _optimize_config_params(
        self,
        query_type: str,
        performances: List[TaskPerformance]
    ) -> Optional[OptimizedConfigParams]:
        """优化配置参数"""
        try:
            # 过滤成功的查询
            successful = [p for p in performances if p.success]
            if len(successful) < 5:
                return None
            
            # 分析配置参数的影响（简化版，可以后续增强）
            # 这里主要分析置信度阈值等关键参数
            
            config_updates = {}
            
            # 分析平均置信度，调整置信度阈值
            avg_confidence = sum(p.confidence for p in successful) / len(successful)
            if avg_confidence > 0.8:
                # 高置信度，可以提高阈值
                config_updates['confidence_threshold'] = min(0.9, avg_confidence * 0.95)
            elif avg_confidence < 0.6:
                # 低置信度，降低阈值
                config_updates['confidence_threshold'] = max(0.5, avg_confidence * 1.05)
            
            if not config_updates:
                return None
            
            # 计算置信度
            confidence = min(1.0, len(successful) / 50.0)
            
            return OptimizedConfigParams(
                query_type=query_type,
                config_updates=config_updates,
                confidence=confidence
            )
        except Exception as e:
            self.logger.error(f"优化{query_type}类型配置参数失败: {e}")
            return None
    
    def _find_similar_query_type(self, query_type: str, query_type_performances: Dict[str, List[TaskPerformance]]) -> Optional[str]:
        """🚀 ML/RL优化：找到相似的查询类型（用于迁移学习）
        
        Args:
            query_type: 当前查询类型
            query_type_performances: 所有查询类型的性能数据
            
        Returns:
            最相似的查询类型，如果没有则返回None
        """
        try:
            # 定义查询类型的相似性映射
            similarity_groups = {
                'factual': ['general', 'name', 'location', 'country'],
                'numerical': ['temporal', 'comparative'],
                'temporal': ['numerical', 'factual'],
                'causal': ['comparative', 'multi_hop'],
                'comparative': ['causal', 'multi_hop'],
                'multi_hop': ['causal', 'comparative'],
                'general': ['factual', 'name'],
                'name': ['factual', 'general'],
                'location': ['factual', 'country'],
                'country': ['location', 'factual']
            }
            
            # 查找相似类型
            similar_types = similarity_groups.get(query_type, [])
            
            # 找到有足够数据的相似类型
            for similar_type in similar_types:
                if similar_type in query_type_performances and len(query_type_performances[similar_type]) >= 3:
                    return similar_type
            
            # 如果没有找到，尝试查找任何有足够数据的类型
            for other_type, perfs in query_type_performances.items():
                if other_type != query_type and len(perfs) >= 3:
                    return other_type
            
            return None
        except Exception as e:
            self.logger.error(f"查找相似查询类型失败: {e}")
            return None
    
    def _apply_transfer_learning(
        self,
        target_query_type: str,
        source_query_type: str,
        source_performances: List[TaskPerformance]
    ) -> None:
        """🚀 ML/RL优化：应用迁移学习，从相似查询类型学习
        
        Args:
            target_query_type: 目标查询类型（数据不足）
            source_query_type: 源查询类型（有足够数据）
            source_performances: 源查询类型的性能数据
        """
        try:
            # 使用源查询类型的策略作为目标类型的默认策略（降低置信度）
            # 优化模型选择
            optimized_model = self._optimize_model_selection(source_query_type, source_performances)
            if optimized_model:
                # 降低置信度（因为是迁移学习）
                optimized_model.query_type = target_query_type
                optimized_model.confidence = optimized_model.confidence * 0.7  # 降低30%置信度
                self.optimized_model_selection[target_query_type] = optimized_model
                self.logger.info(
                    f"✅ 迁移学习模型选择: {source_query_type} → {target_query_type} | "
                    f"置信度: {optimized_model.confidence:.2f}"
                )
            
            # 优化证据选择
            optimized_evidence = self._optimize_evidence_selection(source_query_type, source_performances)
            if optimized_evidence:
                optimized_evidence.query_type = target_query_type
                optimized_evidence.confidence = optimized_evidence.confidence * 0.7
                self.optimized_evidence_selection[target_query_type] = optimized_evidence
                self.logger.info(
                    f"✅ 迁移学习证据选择: {source_query_type} → {target_query_type} | "
                    f"置信度: {optimized_evidence.confidence:.2f}"
                )
            
            # 优化配置参数
            optimized_config = self._optimize_config_params(source_query_type, source_performances)
            if optimized_config:
                optimized_config.query_type = target_query_type
                optimized_config.confidence = optimized_config.confidence * 0.7
                self.optimized_config_params[target_query_type] = optimized_config
                self.logger.info(
                    f"✅ 迁移学习配置参数: {source_query_type} → {target_query_type} | "
                    f"置信度: {optimized_config.confidence:.2f}"
                )
        except Exception as e:
            self.logger.error(f"应用迁移学习失败: {e}")
    

        except Exception as e:
            self.logger.error(f"获取默认策略失败: {e}")
            return None
    
    def get_optimized_model_selection(
        self,
        query_type: str,
        default_model: str = 'fast'
    ) -> Tuple[str, float]:
        """获取优化后的模型选择"""
        try:
            if query_type in self.optimized_model_selection:
                optimized = self.optimized_model_selection[query_type]
                if optimized.confidence >= 0.3:
                    return (optimized.preferred_model, optimized.complexity_threshold)
            return (default_model, 0.7)
        except Exception as e:
            self.logger.error(f"获取优化模型选择失败: {e}")
            return (default_model, 0.7)
    
    def get_optimized_evidence_count(
        self,
        query_type: str,
        default_count: int = 5
    ) -> Tuple[int, int, int]:
        """获取优化后的证据数量"""
        try:
            learned_count = self.parameter_learner.get_evidence_count(query_type, default_count)
            if learned_count > 0:
                return (learned_count, max(1, learned_count - 2), learned_count + 5)
            
            if query_type in self.optimized_evidence_selection:
                optimized = self.optimized_evidence_selection[query_type]
                if optimized.confidence >= 0.3:
                    return (optimized.optimal_evidence_count, optimized.min_evidence_count, optimized.max_evidence_count)
            
            return (default_count, max(1, default_count - 2), default_count + 5)
        except Exception as e:
            self.logger.error(f"获取优化证据数量失败: {e}")
            return (default_count, max(1, default_count - 2), default_count + 5)
    
    def get_optimized_config_updates(
        self,
        query_type: str
    ) -> Dict[str, Any]:
        """获取优化后的配置更新"""
        try:
            if query_type in self.optimized_config_params:
                optimized = self.optimized_config_params[query_type]
                if optimized.confidence >= 0.3:
                    return optimized.config_updates
            return {}
        except Exception as e:
            self.logger.error(f"获取优化配置更新失败: {e}")
            return {}

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_tasks': self.stats['total_tasks'],
            'successful_tasks': self.stats['successful_tasks'],
            'failed_tasks': self.stats['failed_tasks'],
            'success_rate': (
                self.stats['successful_tasks'] / self.stats['total_tasks']
                if self.stats['total_tasks'] > 0 else 0.0
            ),
            'avg_processing_time': self.stats['avg_processing_time'],
            'avg_confidence': self.stats['avg_confidence'],
            'fast_model_usage': self.stats['fast_model_usage'],
            'reasoning_model_usage': self.stats['reasoning_model_usage'],
            'optimized_query_types': {
                'model_selection': list(self.optimized_model_selection.keys()),
                'evidence_selection': list(self.optimized_evidence_selection.keys()),
                'config_params': list(self.optimized_config_params.keys())
            }
        }
