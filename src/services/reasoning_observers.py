#!/usr/bin/env python3
"""
推理服务 - 观察者模式实现
Reasoning Service - Observer Pattern Implementations

提供推理过程观察者、记录器和指标收集器
"""
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ReasoningObserver(ABC):
    """推理观察者基类"""
    
    @abstractmethod
    def update(self, event: str, data: Any = None):
        """更新方法"""
        # 记录事件
        if not hasattr(self, 'event_history'):
            self.event_history = []
        
        self.event_history.append({
            'timestamp': time.time(),
            'event': event,
            'data': data
        })
        
        # 根据事件类型执行相应操作
        if event == 'reasoning_started':
            self._handle_reasoning_started(data)
        elif event == 'reasoning_completed':
            self._handle_reasoning_completed(data)
        elif event == 'reasoning_failed':
            self._handle_reasoning_failed(data)
        elif event == 'context_updated':
            self._handle_context_updated(data)
        else:
            self._handle_default_event(event, data)
    
    def _handle_reasoning_started(self, data: Any):
        """处理推理开始事件"""
        if hasattr(self, 'active_reasoning_count'):
            self.active_reasoning_count += 1
    
    def _handle_reasoning_completed(self, data: Any):
        """处理推理完成事件"""
        if hasattr(self, 'completed_reasoning_count'):
            self.completed_reasoning_count += 1
        if hasattr(self, 'active_reasoning_count'):
            self.active_reasoning_count = max(0, self.active_reasoning_count - 1)
    
    def _handle_reasoning_failed(self, data: Any):
        """处理推理失败事件"""
        if hasattr(self, 'failed_reasoning_count'):
            self.failed_reasoning_count += 1
        if hasattr(self, 'active_reasoning_count'):
            self.active_reasoning_count = max(0, self.active_reasoning_count - 1)
    
    def _handle_context_updated(self, data: Any):
        """处理上下文更新事件"""
        pass
    
    def _handle_default_event(self, event: str, data: Any):
        """处理默认事件"""
        pass


class ReasoningLogger(ReasoningObserver):
    """推理日志记录器"""
    
    def __init__(self):
        self.event_history: List[Dict[str, Any]] = []
        self.logger_entries: List[Dict[str, Any]] = []
    
    def update(self, event: str, data: Any = None):
        """记录推理事件"""
        super().update(event, data)
        
        # 记录日志
        self.logger_entries.append({
            'timestamp': time.time(),
            'level': 'INFO',
            'event': event,
            'data': data
        })
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """获取日志"""
        return self.logger_entries
    
    def clear_logs(self):
        """清空日志"""
        self.logger_entries.clear()


class ReasoningMetrics(ReasoningObserver):
    """推理指标收集器"""
    
    def __init__(self):
        self.event_history: List[Dict[str, Any]] = []
        self.active_reasoning_count = 0
        self.completed_reasoning_count = 0
        self.failed_reasoning_count = 0
        self.total_reasoning_time = 0.0
        self.metrics: Dict[str, Any] = {}
    
    def update(self, event: str, data: Any = None):
        """收集推理指标"""
        super().update(event, data)
        
        if event == 'reasoning_started' and isinstance(data, dict):
            self.metrics['last_start_time'] = time.time()
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        return {
            'active_count': self.active_reasoning_count,
            'completed_count': self.completed_reasoning_count,
            'failed_count': self.failed_reasoning_count,
            'total_time': self.total_reasoning_time,
            'success_rate': self._calculate_success_rate()
        }
    
    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        total = self.completed_reasoning_count + self.failed_reasoning_count
        if total == 0:
            return 0.0
        return self.completed_reasoning_count / total
    
    def reset(self):
        """重置指标"""
        self.active_reasoning_count = 0
        self.completed_reasoning_count = 0
        self.failed_reasoning_count = 0
        self.total_reasoning_time = 0.0
        self.metrics.clear()
