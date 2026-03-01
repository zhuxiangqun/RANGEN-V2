#!/usr/bin/env python3
"""
核心系统贝叶斯优化器 - 阶段2：贝叶斯优化
使用贝叶斯优化找到全局最优策略组合
"""

import json
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

# 尝试导入 scikit-optimize（可选依赖）
try:
    from skopt import gp_minimize
    from skopt.space import Real, Integer
    from skopt.utils import use_named_args
    SKOPT_AVAILABLE = True
except ImportError:
    SKOPT_AVAILABLE = False
    logger.warning("scikit-optimize 未安装，将使用简化版贝叶斯优化。如需使用完整功能，请安装: pip install scikit-optimize")


@dataclass
class OptimizationResult:
    """优化结果"""
    best_params: Dict[str, Any]
    best_score: float
    optimization_history: List[Dict[str, Any]]
    optimization_time: float
    n_evaluations: int
    confidence: float


class BayesianOptimizer:
    """核心系统贝叶斯优化器"""
    
    def __init__(
        self,
        data_path: str = "data/learning/bayesian_optimization.json",
        use_skopt: bool = True
    ):
        self.logger = logger
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self.use_skopt = use_skopt and SKOPT_AVAILABLE
        
        # 优化历史
        self.optimization_history: List[OptimizationResult] = []
        
        # 当前最优参数
        self.best_params: Optional[Dict[str, Any]] = {}
        self.best_score: float = 0.0
        
        # 加载历史数据
        self._load_history()
    
    def _load_history(self) -> None:
        """加载历史优化数据"""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if 'optimization_history' in data:
                        self.optimization_history = [
                            OptimizationResult(**item)
                            for item in data['optimization_history']
                        ]
                    
                    if 'best_params' in data:
                        self.best_params = data['best_params']
                    
                    if 'best_score' in data:
                        self.best_score = data['best_score']
                    
                    self.logger.info(f"✅ 加载历史优化数据: {len(self.optimization_history)}条记录")
        except Exception as e:
            self.logger.warning(f"加载历史优化数据失败: {e}")
    
    def _save_history(self) -> None:
        """保存历史优化数据"""
        try:
            data = {
                'optimization_history': [
                    asdict(result) for result in self.optimization_history[-10:]
                ],  # 只保留最近10次优化
                'best_params': self.best_params,
                'best_score': self.best_score
            }
            
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存历史优化数据失败: {e}")
    
    def optimize_core_parameters(
        self,
        evaluation_function: Callable[[Dict[str, Any]], float],
        n_calls: int = 50,
        random_state: int = 42
    ) -> OptimizationResult:
        """
        优化核心系统参数
        
        Args:
            evaluation_function: 评估函数，接收参数字典，返回分数（越高越好）
            n_calls: 评估次数
            random_state: 随机种子
            
        Returns:
            优化结果
        """
        try:
            start_time = time.time()
            
            if self.use_skopt:
                result = self._optimize_with_skopt(
                    evaluation_function, n_calls, random_state
                )
            else:
                result = self._optimize_simplified(
                    evaluation_function, n_calls, random_state
                )
            
            # 更新最优参数
            if result.best_score > self.best_score:
                self.best_params = result.best_params
                self.best_score = result.best_score
            
            # 保存历史
            self.optimization_history.append(result)
            self._save_history()
            
            self.logger.info(
                f"✅ 贝叶斯优化完成: 最优分数={result.best_score:.4f}, "
                f"评估次数={result.n_evaluations}, "
                f"耗时={result.optimization_time:.2f}秒"
            )
            
            return result
        except Exception as e:
            self.logger.error(f"贝叶斯优化失败: {e}")
            raise
    
    def _optimize_with_skopt(
        self,
        evaluation_function: Callable[[Dict[str, Any]], float],
        n_calls: int,
        random_state: int
    ) -> OptimizationResult:
        """使用 scikit-optimize 进行优化"""
        # 🚀 修复：记录优化开始时间
        start_time = time.time()
        
        # 🚀 ML/RL优化：优化贝叶斯优化的参数空间
        # 扩展参数空间，添加更多可优化参数
        space = [
            Real(0.4, 0.95, name='complexity_threshold', prior='uniform'),  # 复杂度阈值（扩展范围，使用均匀先验）
            Integer(3, 25, name='optimal_evidence_count'),  # 最优证据数量（扩展范围：3-25）
            Real(0.4, 0.95, name='confidence_threshold', prior='uniform'),  # 置信度阈值（扩展范围）
            Real(0.5, 0.95, name='min_confidence', prior='uniform'),  # 最小置信度（扩展范围）
            # 新增参数
            Real(0.1, 0.5, name='high_relevance_threshold', prior='uniform'),  # 高相关性阈值
            Real(0.3, 0.7, name='low_relevance_threshold', prior='uniform'),  # 低相关性阈值
            Real(0.05, 0.3, name='similarity_threshold', prior='uniform'),  # 相似度阈值
            Integer(5, 30, name='max_evidence_count'),  # 最大证据数量
        ]
        
        # 定义目标函数
        # 🚀 ML/RL优化：更新参数处理以支持扩展的参数空间（8个参数）
        try:
            # 尝试新版本API（使用dimensions参数）
            @use_named_args(dimensions=space)
            def objective(complexity_threshold, optimal_evidence_count, confidence_threshold, min_confidence,
                         high_relevance_threshold, low_relevance_threshold, similarity_threshold, max_evidence_count):
                params = {
                    'complexity_threshold': float(complexity_threshold),
                    'optimal_evidence_count': int(optimal_evidence_count),
                    'confidence_threshold': float(confidence_threshold),
                    'min_confidence': float(min_confidence),
                    'high_relevance_threshold': float(high_relevance_threshold),
                    'low_relevance_threshold': float(low_relevance_threshold),
                    'similarity_threshold': float(similarity_threshold),
                    'max_evidence_count': int(max_evidence_count)
                }
                score = evaluation_function(params)
                return -score  # 最小化负分数（因为gp_minimize是最小化）
        except (TypeError, ValueError) as e1:
            # Fallback：如果新版本API不支持，尝试旧版本API（直接传递space作为位置参数）
            try:
                @use_named_args(space)
                def objective(complexity_threshold, optimal_evidence_count, confidence_threshold, min_confidence,
                             high_relevance_threshold, low_relevance_threshold, similarity_threshold, max_evidence_count):
                    params = {
                        'complexity_threshold': float(complexity_threshold),
                        'optimal_evidence_count': int(optimal_evidence_count),
                        'confidence_threshold': float(confidence_threshold),
                        'min_confidence': float(min_confidence),
                        'high_relevance_threshold': float(high_relevance_threshold),
                        'low_relevance_threshold': float(low_relevance_threshold),
                        'similarity_threshold': float(similarity_threshold),
                        'max_evidence_count': int(max_evidence_count)
                    }
                    score = evaluation_function(params)
                    return -score
            except (TypeError, ValueError) as e2:
                # 如果都不支持，使用不带装饰器的版本（手动处理参数）
                # 这种情况下，gp_minimize会传递参数列表而不是命名参数
                def objective(params_list):
                    """手动处理参数列表（当use_named_args不可用时）"""
                    params = {
                        'complexity_threshold': float(params_list[0]),
                        'optimal_evidence_count': int(params_list[1]),
                        'confidence_threshold': float(params_list[2]),
                        'min_confidence': float(params_list[3]),
                        'high_relevance_threshold': float(params_list[4]),
                        'low_relevance_threshold': float(params_list[5]),
                        'similarity_threshold': float(params_list[6]),
                        'max_evidence_count': int(params_list[7])
                    }
                    score = evaluation_function(params)
                    return -score
                self.logger.warning(f"⚠️ use_named_args API不兼容，使用手动参数处理: {e1}, {e2}")
        
        # 运行贝叶斯优化
        result = gp_minimize(
            func=objective,
            dimensions=space,
            n_calls=n_calls,
            random_state=random_state,
            n_initial_points=10  # 初始随机采样点
        )
        
        # 🚀 ML/RL优化：提取最优参数（支持8个参数）
        best_params = {
            'complexity_threshold': float(result.x[0]),
            'optimal_evidence_count': int(result.x[1]),
            'confidence_threshold': float(result.x[2]),
            'min_confidence': float(result.x[3]),
            'high_relevance_threshold': float(result.x[4]),
            'low_relevance_threshold': float(result.x[5]),
            'similarity_threshold': float(result.x[6]),
            'max_evidence_count': int(result.x[7])
        }
        
        best_score = -result.fun  # 转换为最大化分数
        
        # 构建优化历史
        optimization_history = []
        for i, (x, y) in enumerate(zip(result.x_iters, result.func_vals)):
            params = {
                'complexity_threshold': float(x[0]),
                'optimal_evidence_count': int(x[1]),
                'confidence_threshold': float(x[2]),
                'min_confidence': float(x[3]),
                'high_relevance_threshold': float(x[4]) if len(x) > 4 else 0.8,
                'low_relevance_threshold': float(x[5]) if len(x) > 5 else 0.6,
                'similarity_threshold': float(x[6]) if len(x) > 6 else 0.25,
                'max_evidence_count': int(x[7]) if len(x) > 7 else 20
            }
            score = -float(y)  # 转换为最大化分数
            optimization_history.append({
                'iteration': i + 1,
                'params': params,
                'score': score
            })
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            optimization_history=optimization_history,
            optimization_time=time.time() - start_time,
            n_evaluations=n_calls,
            confidence=min(1.0, n_calls / 50.0)  # 置信度基于评估次数
        )
    
    def _optimize_simplified(
        self,
        evaluation_function: Callable[[Dict[str, Any]], float],
        n_calls: int,
        random_state: int
    ) -> OptimizationResult:
        """简化版贝叶斯优化（使用随机搜索 + 局部搜索）"""
        np.random.seed(random_state)
        
        # 参数空间
        complexity_threshold_range = (0.5, 0.9)
        evidence_count_range = (3, 20)
        confidence_threshold_range = (0.5, 0.9)
        min_confidence_range = (0.6, 0.9)
        
        # 初始随机采样
        n_initial = min(10, n_calls // 2)
        best_params = None
        best_score = float('-inf')
        optimization_history = []
        
        # 随机搜索阶段
        for i in range(n_initial):
            params = {
                'complexity_threshold': np.random.uniform(*complexity_threshold_range),
                'optimal_evidence_count': np.random.randint(*evidence_count_range),
                'confidence_threshold': np.random.uniform(*confidence_threshold_range),
                'min_confidence': np.random.uniform(*min_confidence_range)
            }
            score = evaluation_function(params)
            optimization_history.append({
                'iteration': i + 1,
                'params': params,
                'score': score
            })
            
            if score > best_score:
                best_score = score
                best_params = params
        
        # 局部搜索阶段（围绕当前最优解）
        n_local = n_calls - n_initial
        current_params = best_params.copy()
        
        for i in range(n_local):
            # 在当前最优解附近搜索
            new_params = current_params.copy()
            
            # 随机调整一个参数
            param_to_adjust = np.random.choice([
                'complexity_threshold', 'optimal_evidence_count',
                'confidence_threshold', 'min_confidence'
            ])
            
            if param_to_adjust == 'complexity_threshold':
                new_value = max(
                    complexity_threshold_range[0],
                    min(complexity_threshold_range[1],
                        current_params['complexity_threshold'] + np.random.uniform(-0.05, 0.05))
                )
                new_params['complexity_threshold'] = new_value
            elif param_to_adjust == 'optimal_evidence_count':
                new_value = max(
                    evidence_count_range[0],
                    min(evidence_count_range[1],
                        current_params['optimal_evidence_count'] + np.random.randint(-2, 3))
                )
                new_params['optimal_evidence_count'] = new_value
            elif param_to_adjust == 'confidence_threshold':
                new_value = max(
                    confidence_threshold_range[0],
                    min(confidence_threshold_range[1],
                        current_params['confidence_threshold'] + np.random.uniform(-0.05, 0.05))
                )
                new_params['confidence_threshold'] = new_value
            else:  # min_confidence
                new_value = max(
                    min_confidence_range[0],
                    min(min_confidence_range[1],
                        current_params['min_confidence'] + np.random.uniform(-0.05, 0.05))
                )
                new_params['min_confidence'] = new_value
            
            score = evaluation_function(new_params)
            optimization_history.append({
                'iteration': n_initial + i + 1,
                'params': new_params,
                'score': score
            })
            
            if score > best_score:
                best_score = score
                best_params = new_params
                current_params = new_params
            elif score > best_score * 0.95:  # 如果接近最优，也更新当前参数（探索）
                current_params = new_params
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            optimization_history=optimization_history,
            optimization_time=time.time() - start_time,
            n_evaluations=n_calls,
            confidence=min(1.0, n_calls / 50.0)
        )
    
    def get_best_parameters(self) -> Optional[Dict[str, Any]]:
        """获取当前最优参数"""
        return self.best_params.copy() if self.best_params else None
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        return {
            'best_score': self.best_score,
            'best_params': self.best_params,
            'total_optimizations': len(self.optimization_history),
            'last_optimization': (
                asdict(self.optimization_history[-1])
                if self.optimization_history else None
            ),
            'using_skopt': self.use_skopt
        }

