#!/usr/bin/env python3
"""
贝叶斯优化器 - 阶段2：贝叶斯优化
使用贝叶斯优化找到全局最优参数组合
"""

import json
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from ..utils.logger import get_logger

logger = get_logger()

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
    """贝叶斯优化器"""
    
    def __init__(
        self,
        data_path: str = "data/knowledge_management/bayesian_optimization.json",
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
            # 🚀 修复：将OptimizationResult转换为可JSON序列化的字典
            history_data = []
            for result in self.optimization_history[-10:]:  # 只保留最近10次优化
                result_dict = asdict(result)
                # 确保所有值都可以JSON序列化（处理bool等类型）
                history_data.append(self._make_json_serializable(result_dict))
            
            data = {
                'optimization_history': history_data,
                'best_params': self._make_json_serializable(self.best_params) if self.best_params else {},
                'best_score': float(self.best_score) if self.best_score else 0.0
            }
            
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存历史优化数据失败: {e}")
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """将对象转换为JSON可序列化的格式"""
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, (bool, np.bool_)):
            return bool(obj)
        elif isinstance(obj, (int, np.integer)):
            return int(obj)
        elif isinstance(obj, (float, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    def optimize_retrieval_parameters(
        self,
        evaluation_function: Callable[[Dict[str, Any]], float],
        n_calls: int = 50,
        random_state: int = 42
    ) -> OptimizationResult:
        """
        优化检索参数
        
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
        start_time = time.time()  # 🚀 修复：在方法内部定义start_time
        
        # 定义参数空间
        space = [
            Integer(5, 50, name='top_k'),
            Real(0.5, 0.9, name='similarity_threshold'),
            Integer(0, 1, name='use_rerank')  # 0或1表示False或True
        ]
        
        # 定义目标函数（兼容新旧版本的 use_named_args API）
        try:
            # 新版本 API：直接传递 dimensions 列表
            @use_named_args(dimensions=space)
            def objective(top_k, similarity_threshold, use_rerank):
                params = {
                    'top_k': int(top_k),
                    'similarity_threshold': float(similarity_threshold),
                    'use_rerank': bool(use_rerank)
                }
                score = evaluation_function(params)
                return -score  # 最小化负分数（因为gp_minimize是最小化）
        except TypeError:
            try:
                # 旧版本 API：使用 space 参数
                @use_named_args(space=space)
                def objective(top_k, similarity_threshold, use_rerank):
                    params = {
                        'top_k': int(top_k),
                        'similarity_threshold': float(similarity_threshold),
                        'use_rerank': bool(use_rerank)
                    }
                    score = evaluation_function(params)
                    return -score
            except TypeError:
                # 如果都不支持，使用手动参数处理
                def objective(params_list):
                    """手动处理参数列表（当use_named_args不可用时）"""
                    params = {
                        'top_k': int(params_list[0]),
                        'similarity_threshold': float(params_list[1]),
                        'use_rerank': bool(params_list[2])
                    }
                    score = evaluation_function(params)
                    return -score
                self.logger.warning("⚠️ use_named_args API不兼容，使用手动参数处理")
        
        # 运行贝叶斯优化
        # 🚀 优化：增加初始点数量，减少重复评估警告
        # 计算合适的初始点数量（至少是参数空间大小的3倍，但不超过总评估次数的1/2）
        # 对于小参数空间（如只有3个参数），需要更多初始点来充分探索
        n_initial_points = min(max(30, int(n_calls * 0.5)), n_calls - 3)
        
        # 🚀 优化：抑制重复评估警告（这是skopt内部的警告，不影响功能）
        # skopt会自动处理重复评估，使用随机点替代，这个警告是信息性的
        import warnings
        with warnings.catch_warnings():
            # 只抑制"objective has been evaluated"警告，保留其他警告
            warnings.filterwarnings('ignore', message='.*objective has been evaluated.*', category=UserWarning)
            
            # 🚀 优化：使用更智能的采集函数和更多重启
            result = gp_minimize(
                func=objective,
                dimensions=space,
                n_calls=n_calls,
                random_state=random_state,
                n_initial_points=n_initial_points,  # 🚀 增加初始点数量，减少重复评估
                n_restarts_optimizer=10,  # 🚀 进一步增加重启次数，提高探索多样性
                acq_func='EI',  # 使用期望改进（Expected Improvement）作为采集函数
                n_jobs=1  # 单线程执行，避免并发问题
            )
        
        # 提取最优参数
        best_params = {
            'top_k': int(result.x[0]),
            'similarity_threshold': float(result.x[1]),
            'use_rerank': bool(result.x[2])
        }
        
        best_score = -result.fun  # 转换为最大化分数
        
        # 构建优化历史
        optimization_history = []
        for i, (x, y) in enumerate(zip(result.x_iters, result.func_vals)):
            params = {
                'top_k': int(x[0]),
                'similarity_threshold': float(x[1]),
                'use_rerank': bool(x[2])
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
        start_time = time.time()  # 🚀 修复：在方法内部定义start_time
        np.random.seed(random_state)
        
        # 参数空间
        top_k_range = (5, 50)
        threshold_range = (0.5, 0.9)
        use_rerank_options = [True, False]
        
        # 初始随机采样
        n_initial = min(10, n_calls // 2)
        best_params = None
        best_score = float('-inf')
        optimization_history = []
        
        # 随机搜索阶段
        for i in range(n_initial):
            params = {
                'top_k': np.random.randint(*top_k_range),
                'similarity_threshold': np.random.uniform(*threshold_range),
                'use_rerank': np.random.choice(use_rerank_options)
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
            param_to_adjust = np.random.choice(['top_k', 'similarity_threshold', 'use_rerank'])
            
            if param_to_adjust == 'top_k':
                # 在±5范围内调整
                new_value = max(
                    top_k_range[0],
                    min(top_k_range[1], current_params['top_k'] + np.random.randint(-5, 6))
                )
                new_params['top_k'] = new_value
            elif param_to_adjust == 'similarity_threshold':
                # 在±0.05范围内调整
                new_value = max(
                    threshold_range[0],
                    min(threshold_range[1], current_params['similarity_threshold'] + np.random.uniform(-0.05, 0.05))
                )
                new_params['similarity_threshold'] = new_value
            else:
                # 切换 use_rerank
                new_params['use_rerank'] = not current_params['use_rerank']
            
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

