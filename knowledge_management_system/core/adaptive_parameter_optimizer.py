#!/usr/bin/env python3
"""
自适应参数优化器 - 阶段1：改进自适应学习
基于统计学习优化检索参数，实现多目标优化（准确率 + 效率）
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict
from ..utils.logger import get_logger

logger = get_logger()


@dataclass
class QueryPerformance:
    """查询性能记录"""
    query: str
    top_k: int
    similarity_threshold: float
    use_rerank: bool
    result_count: int
    max_similarity: float
    avg_similarity: float
    processing_time: float
    success: bool
    timestamp: float


@dataclass
class OptimizedParameters:
    """优化后的参数"""
    top_k: int
    similarity_threshold: float
    use_rerank: bool
    rerank_weight: float
    confidence: float  # 参数置信度（基于历史数据量）


class AdaptiveParameterOptimizer:
    """自适应参数优化器"""
    
    def __init__(self, data_path: str = "data/knowledge_management/adaptive_params.json"):
        self.logger = logger
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 性能历史记录
        self.performance_history: List[QueryPerformance] = []
        
        # 优化后的参数（按查询类型分类）
        self.optimized_params: Dict[str, OptimizedParameters] = {}
        
        # 统计信息
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'avg_processing_time': 0.0,
            'avg_result_count': 0.0,
            'avg_similarity': 0.0
        }
        
        # 加载历史数据
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
                            QueryPerformance(**item) 
                            for item in data['performance_history']
                        ]
                    
                    # 加载优化后的参数
                    if 'optimized_params' in data:
                        self.optimized_params = {
                            query_type: OptimizedParameters(**params)
                            for query_type, params in data['optimized_params'].items()
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
                'optimized_params': {
                    query_type: asdict(params)
                    for query_type, params in self.optimized_params.items()
                },
                'stats': self.stats
            }
            
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存历史数据失败: {e}")
    
    def record_query_performance(
        self,
        query: str,
        top_k: int,
        similarity_threshold: float,
        use_rerank: bool,
        result_count: int,
        max_similarity: float,
        avg_similarity: float,
        processing_time: float,
        success: bool
    ) -> None:
        """记录查询性能"""
        try:
            performance = QueryPerformance(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                use_rerank=use_rerank,
                result_count=result_count,
                max_similarity=max_similarity,
                avg_similarity=avg_similarity,
                processing_time=processing_time,
                success=success,
                timestamp=time.time()
            )
            
            self.performance_history.append(performance)
            
            # 更新统计信息
            self.stats['total_queries'] += 1
            if success:
                self.stats['successful_queries'] += 1
            else:
                self.stats['failed_queries'] += 1
            
            # 更新平均值（使用移动平均）
            alpha = 0.1  # 学习率
            self.stats['avg_processing_time'] = (
                alpha * processing_time + (1 - alpha) * self.stats['avg_processing_time']
            )
            self.stats['avg_result_count'] = (
                alpha * result_count + (1 - alpha) * self.stats['avg_result_count']
            )
            self.stats['avg_similarity'] = (
                alpha * avg_similarity + (1 - alpha) * self.stats['avg_similarity']
            )
            
            # 每10条记录保存一次（避免频繁IO）
            if len(self.performance_history) % 10 == 0:
                self._save_history()
                # 触发参数优化
                self._optimize_parameters()
        except Exception as e:
            self.logger.error(f"记录查询性能失败: {e}")
    
    def _classify_query_type(self, query: str) -> str:
        """分类查询类型（简化版，可以后续增强）"""
        query_lower = query.lower()
        
        # 简单分类逻辑
        if any(word in query_lower for word in ['who', 'what', 'when', 'where', 'why', 'how']):
            return 'factual'
        elif any(word in query_lower for word in ['compare', 'difference', 'similar', 'versus']):
            return 'comparison'
        elif any(word in query_lower for word in ['explain', 'describe', 'detail']):
            return 'explanatory'
        elif any(word in query_lower for word in ['calculate', 'compute', 'solve', 'formula']):
            return 'computational'
        else:
            return 'general'
    
    def _optimize_parameters(self) -> None:
        """优化参数（基于统计学习）"""
        try:
            if len(self.performance_history) < 10:  # 至少需要10条记录
                return
            
            # 按查询类型分组
            query_type_performances: Dict[str, List[QueryPerformance]] = defaultdict(list)
            for perf in self.performance_history[-100:]:  # 只使用最近100条记录
                query_type = self._classify_query_type(perf.query)
                query_type_performances[query_type].append(perf)
            
            # 为每个查询类型优化参数
            for query_type, performances in query_type_performances.items():
                if len(performances) < 5:  # 至少需要5条记录
                    continue
                
                optimized = self._optimize_for_query_type(query_type, performances)
                if optimized:
                    self.optimized_params[query_type] = optimized
                    self.logger.debug(
                        f"✅ 优化{query_type}类型参数: "
                        f"top_k={optimized.top_k}, "
                        f"threshold={optimized.similarity_threshold:.2f}, "
                        f"rerank={optimized.use_rerank}, "
                        f"confidence={optimized.confidence:.2f}"
                    )
            
            # 保存优化后的参数
            self._save_history()
        except Exception as e:
            self.logger.error(f"优化参数失败: {e}")
    
    def _optimize_for_query_type(
        self,
        query_type: str,
        performances: List[QueryPerformance]
    ) -> Optional[OptimizedParameters]:
        """为特定查询类型优化参数（多目标优化：准确率 + 效率）"""
        try:
            # 过滤成功的查询
            successful = [p for p in performances if p.success]
            if len(successful) < 3:
                return None
            
            # 计算多目标分数（准确率 + 效率）
            # 准确率指标：结果数量、相似度
            # 效率指标：处理时间
            
            # 1. 分析top_k参数
            top_k_scores: Dict[int, float] = {}
            for top_k in [5, 10, 15, 20, 30, 50]:
                top_k_perfs = [p for p in successful if p.top_k == top_k]
                if not top_k_perfs:
                    continue
                
                # 计算准确率分数（基于结果数量和相似度）
                avg_result_count = sum(p.result_count for p in top_k_perfs) / len(top_k_perfs)
                avg_similarity = sum(p.avg_similarity for p in top_k_perfs) / len(top_k_perfs)
                accuracy_score = (avg_result_count / top_k) * 0.5 + avg_similarity * 0.5
                
                # 计算效率分数（基于处理时间，时间越短分数越高）
                avg_time = sum(p.processing_time for p in top_k_perfs) / len(top_k_perfs)
                efficiency_score = 1.0 / (1.0 + avg_time)  # 归一化
                
                # 多目标分数（准确率权重0.7，效率权重0.3）
                top_k_scores[top_k] = accuracy_score * 0.7 + efficiency_score * 0.3
            
            if not top_k_scores:
                return None
            
            # 选择最优top_k
            best_top_k = max(top_k_scores.items(), key=lambda x: x[1])[0]
            
            # 2. 分析similarity_threshold参数
            threshold_scores: Dict[float, float] = {}
            for threshold in [0.5, 0.6, 0.7, 0.75, 0.8, 0.85]:
                threshold_perfs = [
                    p for p in successful
                    if abs(p.similarity_threshold - threshold) < 0.05
                ]
                if not threshold_perfs:
                    continue
                
                # 计算准确率分数
                avg_result_count = sum(p.result_count for p in threshold_perfs) / len(threshold_perfs)
                avg_similarity = sum(p.avg_similarity for p in threshold_perfs) / len(threshold_perfs)
                accuracy_score = (avg_result_count / best_top_k) * 0.5 + avg_similarity * 0.5
                
                # 计算效率分数
                avg_time = sum(p.processing_time for p in threshold_perfs) / len(threshold_perfs)
                efficiency_score = 1.0 / (1.0 + avg_time)
                
                threshold_scores[threshold] = accuracy_score * 0.7 + efficiency_score * 0.3
            
            if not threshold_scores:
                return None
            
            # 选择最优threshold
            best_threshold = max(threshold_scores.items(), key=lambda x: x[1])[0]
            
            # 3. 分析use_rerank参数
            rerank_perfs = [p for p in successful if p.use_rerank]
            no_rerank_perfs = [p for p in successful if not p.use_rerank]
            
            rerank_score = 0.0
            no_rerank_score = 0.0
            
            if rerank_perfs:
                avg_result_count = sum(p.result_count for p in rerank_perfs) / len(rerank_perfs)
                avg_similarity = sum(p.avg_similarity for p in rerank_perfs) / len(rerank_perfs)
                avg_time = sum(p.processing_time for p in rerank_perfs) / len(rerank_perfs)
                accuracy_score = (avg_result_count / best_top_k) * 0.5 + avg_similarity * 0.5
                efficiency_score = 1.0 / (1.0 + avg_time)
                rerank_score = accuracy_score * 0.7 + efficiency_score * 0.3
            
            if no_rerank_perfs:
                avg_result_count = sum(p.result_count for p in no_rerank_perfs) / len(no_rerank_perfs)
                avg_similarity = sum(p.avg_similarity for p in no_rerank_perfs) / len(no_rerank_perfs)
                avg_time = sum(p.processing_time for p in no_rerank_perfs) / len(no_rerank_perfs)
                accuracy_score = (avg_result_count / best_top_k) * 0.5 + avg_similarity * 0.5
                efficiency_score = 1.0 / (1.0 + avg_time)
                no_rerank_score = accuracy_score * 0.7 + efficiency_score * 0.3
            
            best_use_rerank = rerank_score > no_rerank_score if rerank_perfs and no_rerank_perfs else (rerank_perfs is not None and len(rerank_perfs) > 0)
            
            # 4. 计算置信度（基于数据量）
            confidence = min(1.0, len(successful) / 50.0)  # 50条记录达到最大置信度
            
            return OptimizedParameters(
                top_k=best_top_k,
                similarity_threshold=best_threshold,
                use_rerank=best_use_rerank,
                rerank_weight=0.6 if best_use_rerank else 0.0,
                confidence=confidence
            )
        except Exception as e:
            self.logger.error(f"为{query_type}类型优化参数失败: {e}")
            return None
    
    def get_optimized_parameters(
        self,
        query: str,
        default_top_k: int = 5,
        default_threshold: float = 0.7,
        default_use_rerank: bool = True
    ) -> Tuple[int, float, bool]:
        """获取优化后的参数"""
        try:
            query_type = self._classify_query_type(query)
            
            # 如果有优化后的参数且置信度足够高，使用优化后的参数
            if query_type in self.optimized_params:
                optimized = self.optimized_params[query_type]
                if optimized.confidence >= 0.3:  # 至少30%置信度
                    return (
                        optimized.top_k,
                        optimized.similarity_threshold,
                        optimized.use_rerank
                    )
            
            # 否则使用默认参数
            return (default_top_k, default_threshold, default_use_rerank)
        except Exception as e:
            self.logger.error(f"获取优化参数失败: {e}")
            return (default_top_k, default_threshold, default_use_rerank)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_queries': self.stats['total_queries'],
            'successful_queries': self.stats['successful_queries'],
            'failed_queries': self.stats['failed_queries'],
            'success_rate': (
                self.stats['successful_queries'] / self.stats['total_queries']
                if self.stats['total_queries'] > 0 else 0.0
            ),
            'avg_processing_time': self.stats['avg_processing_time'],
            'avg_result_count': self.stats['avg_result_count'],
            'avg_similarity': self.stats['avg_similarity'],
            'optimized_query_types': list(self.optimized_params.keys()),
            'optimized_params': {
                query_type: {
                    'top_k': params.top_k,
                    'similarity_threshold': params.similarity_threshold,
                    'use_rerank': params.use_rerank,
                    'confidence': params.confidence
                }
                for query_type, params in self.optimized_params.items()
            }
        }

