#!/usr/bin/env python3
"""
Adaptive Strategy Selector
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)


class AdaptiveStrategySelector:
    """自适应策略选择器"""
    
    def __init__(self) -> None:
        """初始化"""
        self.initialized = True
        self.strategies = {}
        self.performance_metrics = {}
        self.selection_history = []
    
    def process_data(self, data: Any) -> Any:
        """处理数据"""
        return data
    
    def validate(self, data: Any) -> bool:
        """验证数据"""
        return data is not None
    
    def add_strategy(self, name: str, strategy: Any) -> None:
        """添加策略"""
        self.strategies[name] = strategy
    
    def select_strategy(self, context: Dict[str, Any]) -> str:
        """选择最佳策略"""
        if not self.strategies:
            return "default"
        
        # 基于上下文和性能指标选择策略
        best_strategy = "default"
        best_score = 0.0
        
        for name, strategy in self.strategies.items():
            score = self._calculate_strategy_score(name, context)
            if score > best_score:
                best_score = score
                best_strategy = name
        
        self.selection_history.append({
            "strategy": best_strategy,
            "score": best_score,
            "context": context,
            "timestamp": time.time()
        })
        
        return best_strategy
    
    def _calculate_strategy_score(self, strategy_name: str, context: Dict[str, Any]) -> float:
        """计算策略得分"""
        if strategy_name not in self.performance_metrics:
            return 0.5  # 默认得分
        
        metrics = self.performance_metrics[strategy_name]
        success_rate = metrics.get("success_rate", 0.5)
        avg_performance = metrics.get("avg_performance", 0.5)
        
        # 简单的加权平均
        return (success_rate * 0.6 + avg_performance * 0.4)
    
    def update_performance(self, strategy_name: str, success: bool, performance: float) -> None:
        """更新策略性能"""
        if strategy_name not in self.performance_metrics:
            self.performance_metrics[strategy_name] = {
                "success_count": 0,
                "total_count": 0,
                "success_rate": 0.0,
                "avg_performance": 0.0,
                "performance_sum": 0.0
            }
        
        metrics = self.performance_metrics[strategy_name]
        metrics["total_count"] += 1
        if success:
            metrics["success_count"] += 1
        metrics["success_rate"] = metrics["success_count"] / metrics["total_count"]
        
        metrics["performance_sum"] += performance
        metrics["avg_performance"] = metrics["performance_sum"] / metrics["total_count"]
    
    def get_strategy_info(self, strategy_name: str) -> Dict[str, Any]:
        """获取策略信息"""
        return self.performance_metrics.get(strategy_name, {})
    
    def get_all_strategies(self) -> List[str]:
        """获取所有策略名称"""
        return list(self.strategies.keys())
    
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
            "strategy_count": len(self.strategies),
            "history_count": len(self.selection_history),
            "strategies": list(self.strategies.keys())
        }


# 便捷函数
def get_adaptive_strategy_selector() -> AdaptiveStrategySelector:
    """获取实例"""
    return AdaptiveStrategySelector()
