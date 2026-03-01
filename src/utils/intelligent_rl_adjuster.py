import os
import os
import os
import os
import os
import os
import os
import os
import os
import os
import os
import os
import os
import os
import os
#!/usr/bin/env python3
"""
智能RL参数调整器 - 简化版本
功能已合并到utils模块中
"""

import logging
import time
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from src.utils.security_utils import security_utils


logger = logging.getLogger(__name__)


def validate_input_data(data: str) -> bool:
    """增强的输入数据验证 - 使用安全模块"""
    max_length = int(os.getenv("DEFAULT_TIMEOUT", "100"))
    validation_result = security_utils.validate_string(data, max_length=max_length)
    return validation_result.is_valid


@dataclass
class RLParameterAdjustmentRecord:
    """RL参数调整记录"""
    episode: int
    parameter_name: str
    old_value: float
    new_value: float
    adjustment_reason: str
    performance_impact: float
    timestamp: float


@dataclass
class RLTrainingRoundResult:
    """RL训练回合结果"""
    episode: int
    total_reward: float
    accuracy: float
    execution_time: float
    success_rate: float
    exploration_rate: float
    learning_rate: float
    loss: float


@dataclass
class RLPerformanceMetrics:
    """RL性能指标"""
    avg_reward: float
    avg_accuracy: float
    avg_execution_time: float
    avg_success_rate: float
    convergence_rate: float


class IntelligentRLAdjuster:
    """智能RL参数调整器 - 简化版本"""
    
    def __init__(self):
        """初始化智能RL参数调整器"""
        self.logger = logging.getLogger(__name__)
        self.current_parameters = self._setup_default_parameters()
        self.adaptive_config = self._setup_adaptive_config()
        self.performance_history = []
        self.adjustment_history = []
        self.logger.info("智能RL参数调整器初始化完成")
    
    def _setup_default_parameters(self) -> Dict[str, float]:
        """设置默认参数"""
        return {
            "learning_rate": 0.01,
            "gamma": 0.95,
            "epsilon": float(os.getenv("MAX_CONFIDENCE", "1.0")),
            "epsilon_decay": 0.995,
            "epsilon_min": 0.01,
            "memory_size": int(os.getenv("DEFAULT_TIMEOUT", "100")),
            "batch_size": int(os.getenv("DEFAULT_TIMEOUT", "100")),
            "target_update_frequency": int(os.getenv("DEFAULT_TIMEOUT", "100")),
            "min_learning_rate": 0.001,
            "max_learning_rate": 0.1
        }
    
    def _setup_adaptive_config(self) -> Dict[str, Any]:
        """设置自适应配置"""
        return {
            "update_frequency": 4,
            "performance_window": 10,
            "adjustment_threshold": 0.1,
            "learning_rate_adjustment_factor": 0.1,
            "epsilon_adjustment_factor": 0.05,
            "gamma_adjustment_factor": 0.02,
            "min_performance_samples": 5,
            "max_adjustment_history": 1000
        }
    
    def adjust_parameters(self, performance_metrics: Dict[str, float]) -> Dict[str, float]:
        """调整RL参数"""
        try:
            # 验证输入
            if not self._validate_performance_metrics(performance_metrics):
                return self.current_parameters
            
            # 记录性能指标
            self._record_performance(performance_metrics)
            
            # 分析性能趋势
            performance_trend = self._analyze_performance_trend()
            
            # 根据趋势调整参数
            adjusted_parameters = self._adjust_parameters_based_on_trend(performance_trend)
            
            # 记录调整历史
            self._record_adjustment(adjusted_parameters, performance_metrics)
            
            # 更新当前参数
            self.current_parameters.update(adjusted_parameters)
            
            return self.current_parameters
            
        except Exception as e:
            self.logger.error(f"参数调整失败: {e}")
            return self.current_parameters
    
    def _validate_performance_metrics(self, metrics: Dict[str, float]) -> bool:
        """验证性能指标"""
        if not isinstance(metrics, dict):
            return False
        
        required_metrics = ['reward', 'loss', 'accuracy']
        for metric in required_metrics:
            if metric not in metrics:
                return False
            
            if not isinstance(metrics[metric], (int, float)):
                return False
        
        return True
    
    def _record_performance(self, metrics: Dict[str, float]):
        """记录性能指标"""
        try:
            performance_record = {
                'timestamp': time.time(),
                'metrics': metrics.copy(),
                'parameters': self.current_parameters.copy()
            }
            
            self.performance_history.append(performance_record)
            
            # 保持历史记录在合理范围内
            max_history = self.adaptive_config.get('max_adjustment_history', 1000)
            if len(self.performance_history) > max_history:
                self.performance_history = self.performance_history[-max_history:]
                
        except Exception as e:
            self.logger.warning(f"记录性能指标失败: {e}")
    
    def _analyze_performance_trend(self) -> str:
        """分析性能趋势"""
        try:
            if len(self.performance_history) < self.adaptive_config.get('min_performance_samples', 5):
                return "insufficient_data"
            
            # 获取最近的性能窗口
            window_size = self.adaptive_config.get('performance_window', 10)
            recent_performance = self.performance_history[-window_size:]
            
            # 计算平均奖励
            avg_rewards = [record['metrics']['reward'] for record in recent_performance]
            avg_reward = sum(avg_rewards) / len(avg_rewards)
            
            # 计算奖励趋势
            if len(avg_rewards) >= 2:
                trend = avg_rewards[-1] - avg_rewards[0]
                if trend > self.adaptive_config.get('adjustment_threshold', 0.1):
                    return "improving"
                elif trend < -self.adaptive_config.get('adjustment_threshold', 0.1):
                    return "declining"
                else:
                    return "stable"
            
            return "stable"
            
        except Exception as e:
            self.logger.warning(f"分析性能趋势失败: {e}")
            return "error"
    
    def _adjust_parameters_based_on_trend(self, trend: str) -> Dict[str, float]:
        """根据趋势调整参数"""
        adjustments = {}
        
        try:
            if trend == "improving":
                # 性能改善，可以稍微增加学习率
                adjustments['learning_rate'] = min(
                    self.current_parameters['learning_rate'] * 1.05,
                    self.current_parameters['max_learning_rate']
                )
            elif trend == "declining":
                # 性能下降，减少学习率和探索率
                adjustments['learning_rate'] = max(
                    self.current_parameters['learning_rate'] * 0.95,
                    self.current_parameters['min_learning_rate']
                )
                adjustments['epsilon'] = max(
                    self.current_parameters['epsilon'] * 0.9,
                    self.current_parameters['epsilon_min']
                )
            elif trend == "stable":
                # 性能稳定，微调参数
                adjustments['epsilon'] = max(
                    self.current_parameters['epsilon'] * self.current_parameters['epsilon_decay'],
                    self.current_parameters['epsilon_min']
                )
            
            return adjustments
            
        except Exception as e:
            self.logger.warning(f"参数调整计算失败: {e}")
            return {}
    
    def _record_adjustment(self, adjustments: Dict[str, float], performance_metrics: Dict[str, float]):
        """记录调整历史"""
        try:
            adjustment_record = {
                'timestamp': time.time(),
                'adjustments': adjustments.copy(),
                'performance': performance_metrics.copy(),
                'previous_parameters': self.current_parameters.copy()
            }
            
            self.adjustment_history.append(adjustment_record)
            
            # 保持历史记录在合理范围内
            max_history = self.adaptive_config.get('max_adjustment_history', 1000)
            if len(self.adjustment_history) > max_history:
                self.adjustment_history = self.adjustment_history[-max_history:]
                
        except Exception as e:
            self.logger.warning(f"记录调整历史失败: {e}")
    
    def record_episode_result(self, episode: int, total_reward: float, accuracy: float, 
                            execution_time: float, success_rate: float, exploration_rate: float,
                            learning_rate: float, loss: float) -> None:
        """记录训练回合结果"""
        max_history = int(os.getenv("DEFAULT_TIMEOUT", "100"))
        if len(self.performance_history) > max_history:
            self.performance_history = self.performance_history[-max_history:]
        
        episode_result = RLTrainingRoundResult(
            episode=episode,
            total_reward=total_reward,
            accuracy=accuracy,
            execution_time=execution_time,
            success_rate=success_rate,
            exploration_rate=exploration_rate,
            learning_rate=learning_rate,
            loss=loss
        )
        
        self.performance_history.append(episode_result)
        self.logger.info(f"记录训练回合结果: Episode {episode}")
    
    def get_performance_metrics(self) -> RLPerformanceMetrics:
        """获取性能指标"""
        if not self.performance_history:
            return RLPerformanceMetrics(
                avg_reward=0.0,
                avg_accuracy=0.0,
                avg_execution_time=0.0,
                avg_success_rate=0.0,
                convergence_rate=0.0
            )
        
        recent_performance = self.performance_history[-20:] if len(self.performance_history) >= 20 else self.performance_history
        
        avg_reward = np.mean([ep.total_reward for ep in recent_performance])
        avg_accuracy = np.mean([ep.accuracy for ep in recent_performance])
        avg_execution_time = np.mean([ep.execution_time for ep in recent_performance])
        avg_success_rate = np.mean([ep.success_rate for ep in recent_performance])
        
        # 计算收敛率
        if len(self.performance_history) >= 10:
            recent_accuracy = [ep.accuracy for ep in self.performance_history[-10:]]
            convergence_rate = np.std(recent_accuracy)  # 标准差越小，收敛越好
        else:
            convergence_rate = float(os.getenv("MAX_CONFIDENCE", "1.0"))
        
        return RLPerformanceMetrics(
            avg_reward=float(avg_reward),
            avg_accuracy=float(avg_accuracy),
            avg_execution_time=float(avg_execution_time),
            avg_success_rate=float(avg_success_rate),
            convergence_rate=float(convergence_rate)
        )
    
    def get_current_parameters(self) -> Dict[str, float]:
        """获取当前参数"""
        return self.current_parameters.copy()
    
    def reset_parameters(self):
        """重置参数"""
        self.current_parameters = self._setup_default_parameters()
        self.performance_history.clear()
        self.adjustment_history.clear()
        self.logger.info("参数已重置")


# 全局实例
intelligent_rl_adjuster = IntelligentRLAdjuster()


def get_intelligent_rl_adjuster() -> IntelligentRLAdjuster:
    """获取智能RL参数调整器实例"""
    return intelligent_rl_adjuster