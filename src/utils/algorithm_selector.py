#!/usr/bin/env python3
"""
Algorithm Selector
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)


class AlgorithmSelector:
    """算法选择器"""
    
    def __init__(self) -> None:
        """初始化"""
        self.initialized = True
        self.algorithms = {}
        self.performance_metrics = {}
        self.selection_history = []
    
    def process_data(self, data: Any) -> Any:
        """处理数据"""
        return data
    
    def validate(self, data: Any) -> bool:
        """验证数据"""
        return data is not None
    
    def add_algorithm(self, name: str, algorithm: Any) -> None:
        """添加算法"""
        self.algorithms[name] = algorithm
    
    def select_algorithm(self, context: Dict[str, Any]) -> str:
        """选择最佳算法"""
        if not self.algorithms:
            return "default"
        
        # 基于上下文和性能指标选择算法
        best_algorithm = "default"
        best_score = 0.0
        
        for name, algorithm in self.algorithms.items():
            score = self._calculate_algorithm_score(name, context)
            if score > best_score:
                best_score = score
                best_algorithm = name
        
        self.selection_history.append({
            "algorithm": best_algorithm,
            "score": best_score,
            "context": context,
            "timestamp": time.time()
        })
        
        return best_algorithm
    
    def _calculate_algorithm_score(self, algorithm_name: str, context: Dict[str, Any]) -> float:
        """计算算法得分"""
        if algorithm_name not in self.performance_metrics:
            return 0.5  # 默认得分
        
        metrics = self.performance_metrics[algorithm_name]
        success_rate = metrics.get("success_rate", 0.5)
        avg_performance = metrics.get("avg_performance", 0.5)
        
        # 简单的加权平均
        return (success_rate * 0.6 + avg_performance * 0.4)
    
    def update_performance(self, algorithm_name: str, success: bool, performance: float) -> None:
        """更新算法性能"""
        if algorithm_name not in self.performance_metrics:
            self.performance_metrics[algorithm_name] = {
                "success_count": 0,
                "total_count": 0,
                "success_rate": 0.0,
                "avg_performance": 0.0,
                "performance_sum": 0.0
            }
        
        metrics = self.performance_metrics[algorithm_name]
        metrics["total_count"] += 1
        if success:
            metrics["success_count"] += 1
        metrics["success_rate"] = metrics["success_count"] / metrics["total_count"]
        
        metrics["performance_sum"] += performance
        metrics["avg_performance"] = metrics["performance_sum"] / metrics["total_count"]
    
    def get_algorithm_info(self, algorithm_name: str) -> Dict[str, Any]:
        """获取算法信息"""
        return self.performance_metrics.get(algorithm_name, {})
    
    def get_all_algorithms(self) -> List[str]:
        """获取所有算法名称"""
        return list(self.algorithms.keys())
    
    def get_selection_history(self) -> List[Dict[str, Any]]:
        """获取选择历史"""
        return self.selection_history.copy()
    
    def clear_history(self) -> None:
        """清除历史记录"""
        self.selection_history.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "initialized": self.initialized,
            "algorithm_count": len(self.algorithms),
            "history_count": len(self.selection_history),
            "algorithms": list(self.algorithms.keys())
        }


# 便捷函数
def get_algorithm_selector() -> AlgorithmSelector:
    """获取实例"""
    return AlgorithmSelector()
