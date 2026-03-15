"""
性能监控器模块

从 UnifiedResearchSystem 拆分出来的性能监控功能
"""

import time
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque


class PerformanceMonitor:
    """
    性能监控器
    
    监控:
    - 系统负载
    - 内存使用
    - Agent 性能
    - 调度性能
    """
    
    def __init__(self):
        # 系统监控
        self._system_load_history = deque(maxlen=100)
        self._memory_history = deque(maxlen=100)
        
        # Agent 性能记录
        self._agent_performance: Dict[str, List[Dict[str, Any]]] = {}
        
        # 调度性能记录
        self._scheduling_performance: List[Dict[str, Any]] = []
        
        # 总体性能指标
        self._total_requests = 0
        self._total_success = 0
        self._total_failure = 0
        self._total_execution_time = 0.0
    
    def _get_system_load(self) -> float:
        """获取系统负载 (0-1)"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            load = cpu_percent / 100.0
            self._system_load_history.append(load)
            return load
        except Exception:
            return 0.0
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        try:
            memory = psutil.virtual_memory()
            
            memory_data = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent,
                "timestamp": time.time(),
            }
            
            self._memory_history.append(memory_data)
            return memory_data
        except Exception:
            return {"total": 0, "available": 0, "used": 0, "percent": 0}
    
    def _calculate_memory_trend(self) -> str:
        """计算内存趋势"""
        if len(self._memory_history) < 2:
            return "stable"
        
        recent = list(self._memory_history)[-10:]
        if not recent:
            return "stable"
        
        first_half = sum(m["percent"] for m in recent[:5]) / 5
        second_half = sum(m["percent"] for m in recent[5:]) / 5
        
        if second_half - first_half > 5:
            return "increasing"
        elif first_half - second_half > 5:
            return "decreasing"
        else:
            return "stable"
    
    def _get_memory_status(self, percent: float) -> str:
        """获取内存状态"""
        if percent < 50:
            return "healthy"
        elif percent < 70:
            return "normal"
        elif percent < 85:
            return "warning"
        else:
            return "critical"
    
    def _record_performance(
        self, 
        agent_type: str, 
        success: bool, 
        execution_time: float
    ) -> None:
        """记录 Agent 性能"""
        if agent_type not in self._agent_performance:
            self._agent_performance[agent_type] = []
        
        record = {
            "success": success,
            "execution_time": execution_time,
            "timestamp": time.time(),
        }
        
        self._agent_performance[agent_type].append(record)
        
        # 只保留最近 1000 条记录
        if len(self._agent_performance[agent_type]) > 1000:
            self._agent_performance[agent_type] = self._agent_performance[agent_type][-1000:]
        
        # 更新总体统计
        self._total_requests += 1
        if success:
            self._total_success += 1
        else:
            self._total_failure += 1
        self._total_execution_time += execution_time
    
    def _adaptive_load_balancing(self, agent_type: str) -> float:
        """
        自适应负载均衡
        
        根据 Agent 历史性能返回调整系数
        """
        if agent_type not in self._agent_performance:
            return 1.0
        
        records = self._agent_performance[agent_type][-100:]
        if not records:
            return 1.0
        
        # 计算成功率
        success_count = sum(1 for r in records if r["success"])
        success_rate = success_count / len(records)
        
        # 计算平均执行时间
        avg_time = sum(r["execution_time"] for r in records) / len(records)
        
        # 计算调整系数
        # 成功率低 → 降低优先级
        # 执行时间长 → 降低优先级
        load_factor = 1.0
        
        if success_rate < 0.5:
            load_factor *= 0.5
        elif success_rate < 0.8:
            load_factor *= 0.8
        
        if avg_time > 60:  # > 60秒
            load_factor *= 0.7
        elif avg_time > 30:
            load_factor *= 0.85
        
        return load_factor
    
    def _update_performance_metrics(
        self, 
        success: bool, 
        execution_time: float
    ) -> None:
        """更新总体性能指标"""
        self._total_requests += 1
        if success:
            self._total_success += 1
        else:
            self._total_failure += 1
        self._total_execution_time += execution_time
    
    def _record_scheduling_performance(
        self,
        query: str,
        agent_type: str,
        decision: str,
        execution_time: float,
        success: bool
    ) -> None:
        """记录调度性能"""
        record = {
            "query": query[:100],  # 截断
            "agent_type": agent_type,
            "decision": decision,
            "execution_time": execution_time,
            "success": success,
            "timestamp": time.time(),
        }
        
        self._scheduling_performance.append(record)
        
        # 只保留最近 1000 条
        if len(self._scheduling_performance) > 1000:
            self._scheduling_performance = self._scheduling_performance[-1000:]
    
    def get_performance_analytics(self) -> Dict[str, Any]:
        """获取性能分析数据"""
        # 系统负载
        system_load = self._get_system_load()
        avg_system_load = sum(self._system_load_history) / len(self._system_load_history) if self._system_load_history else 0
        
        # 内存
        memory = self._get_memory_usage()
        memory_trend = self._calculate_memory_trend()
        memory_status = self._get_memory_status(memory.get("percent", 0))
        
        # 总体性能
        avg_execution_time = (
            self._total_execution_time / self._total_requests 
            if self._total_requests > 0 else 0
        )
        success_rate = (
            self._total_success / self._total_requests 
            if self._total_requests > 0 else 0
        )
        
        return {
            "system": {
                "current_load": system_load,
                "avg_load": avg_system_load,
                "memory": memory,
                "memory_trend": memory_trend,
                "memory_status": memory_status,
            },
            "overall": {
                "total_requests": self._total_requests,
                "success": self._total_success,
                "failure": self._total_failure,
                "success_rate": success_rate,
                "avg_execution_time": avg_execution_time,
            },
            "agent_performance": {
                agent_type: {
                    "records": len(records),
                    "avg_execution_time": sum(r["execution_time"] for r in records) / len(records) if records else 0,
                    "success_rate": sum(1 for r in records if r["success"]) / len(records) if records else 0,
                }
                for agent_type, records in self._agent_performance.items()
            },
        }
    
    def get_agent_performance(self, agent_type: str) -> Dict[str, Any]:
        """获取特定 Agent 的性能"""
        if agent_type not in self._agent_performance:
            return {"records": 0}
        
        records = self._agent_performance[agent_type]
        
        return {
            "records": len(records),
            "avg_execution_time": sum(r["execution_time"] for r in records) / len(records) if records else 0,
            "success_rate": sum(1 for r in records if r["success"]) / len(records) if records else 0,
            "recent": records[-10:] if records else [],
        }
