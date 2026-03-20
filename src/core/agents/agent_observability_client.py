"""
Agent 可观测性客户端

核心功能：
- Agent 可查询运行时日志
- Agent 可查询指标
- Agent 可进行自我验证
- 闭环反馈机制
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class LogQuery:
    """日志查询"""
    query: str
    time_range: str = "1h"  # 1h, 24h, 7d
    limit: int = 100


@dataclass
class MetricQuery:
    """指标查询"""
    metric_name: str
    time_range: str = "1h"
    aggregation: str = "avg"  # avg, sum, max, min


@dataclass
class QueryResult:
    """查询结果"""
    success: bool
    data: Any
    error: Optional[str] = None


class AgentObservabilityClient:
    """
    Agent 可观测性客户端
    
    允许 Agent 查询运行时数据，进行自我验证
    """
    
    def __init__(self):
        # 可用的查询接口
        self.log_sources = {
            "app": self._query_app_logs,
            "system": self._query_system_logs,
            "agent": self._query_agent_logs,
        }
        
        self.metric_sources = {
            "latency": self._query_latency,
            "errors": self._query_errors,
            "tokens": self._query_tokens,
            "quality": self._query_quality,
        }
    
    # ============ 日志查询 ============
    
    async def query_logs(self, query: LogQuery) -> QueryResult:
        """查询日志"""
        # 解析查询类型
        source = "app"  # 默认
        for src in self.log_sources.keys():
            if src in query.query.lower():
                source = src
                break
        
        try:
            data = await self.log_sources[source](query)
            return QueryResult(success=True, data=data)
        except Exception as e:
            logger.error(f"Log query failed: {e}")
            return QueryResult(success=False, data=None, error=str(e))
    
    async def _query_app_logs(self, query: LogQuery) -> List[Dict]:
        """查询应用日志"""
        # 实际实现时，这里会调用日志服务
        # 返回模拟数据
        return [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": f"Simulated log: {query.query}",
                "source": "app"
            }
        ]
    
    async def _query_system_logs(self, query: LogQuery) -> List[Dict]:
        """查询系统日志"""
        return []
    
    async def _query_agent_logs(self, query: LogQuery) -> List[Dict]:
        """查询 Agent 日志"""
        return []
    
    # ============ 指标查询 ============
    
    async def query_metrics(self, query: MetricQuery) -> QueryResult:
        """查询指标"""
        if query.metric_name not in self.metric_sources:
            return QueryResult(
                success=False,
                data=None,
                error=f"Unknown metric: {query.metric_name}"
            )
        
        try:
            data = await self.metric_sources[query.metric_name](query)
            return QueryResult(success=True, data=data)
        except Exception as e:
            logger.error(f"Metric query failed: {e}")
            return QueryResult(success=False, data=None, error=str(e))
    
    async def _query_latency(self, query: MetricQuery) -> Dict:
        """查询延迟指标"""
        return {
            "metric": "latency",
            "avg_ms": 150,
            "p95_ms": 300,
            "p99_ms": 500,
            "time_range": query.time_range
        }
    
    async def _query_errors(self, query: MetricQuery) -> Dict:
        """查询错误指标"""
        return {
            "metric": "errors",
            "total": 5,
            "by_type": {
                "timeout": 2,
                "validation": 3
            },
            "time_range": query.time_range
        }
    
    async def _query_tokens(self, query: MetricQuery) -> Dict:
        """查询 Token 使用"""
        return {
            "metric": "tokens",
            "input": 125000,
            "output": 45000,
            "total": 170000,
            "cost_estimate": 0.05,
            "time_range": query.time_range
        }
    
    async def _query_quality(self, query: MetricQuery) -> Dict:
        """查询质量指标"""
        return {
            "metric": "quality",
            "score": 0.85,
            "by_dimension": {
                "accuracy": 0.88,
                "relevance": 0.82,
                "coherence": 0.90
            },
            "time_range": query.time_range
        }
    
    # ============ Agent 自我验证 ============
    
    async def verify_execution(self, task_id: str, expected_outcome: str) -> QueryResult:
        """
        验证执行结果
        
        Agent 可以调用此方法来验证自己的执行是否符合预期
        """
        # 查询相关日志
        log_query = LogQuery(
            query=f"task_id={task_id}",
            time_range="24h",
            limit=50
        )
        
        logs = await self.query_logs(log_query)
        
        if not logs.success:
            return logs
        
        # 简单验证：检查是否有错误
        has_error = any(
            log.get("level") == "ERROR" 
            for log in logs.data
        )
        
        if has_error:
            return QueryResult(
                success=False,
                data={"verified": False, "reason": "Found errors in execution logs"},
                error=None
            )
        
        return QueryResult(
            success=True,
            data={
                "verified": True,
                "task_id": task_id,
                "expected": expected_outcome,
                "logs_checked": len(logs.data)
            }
        )
    
    async def get_health_status(self) -> Dict:
        """获取系统健康状态"""
        return {
            "status": "healthy",
            "components": {
                "api": "up",
                "database": "up",
                "cache": "up",
                "llm": "up"
            },
            "timestamp": datetime.now().isoformat()
        }


class AgentFeedbackLoop:
    """
    Agent 反馈闭环
    
    核心思想：让 Agent 能够观察结果 → 判断对错 → 自我修正
    """
    
    def __init__(self, observability: AgentObservabilityClient):
        self.observability = observability
        self.feedback_history: List[Dict] = []
    
    async def execute_with_feedback(
        self, 
        task_id: str,
        action_fn,  # 要执行的操作
        verify_fn   # 验证函数
    ) -> Dict:
        """
        带反馈的执行
        
        1. 执行操作
        2. 查询结果
        3. 验证是否符合预期
        4. 如有问题，尝试自我修正
        """
        # 1. 执行
        result = await action_fn()
        
        # 2. 等待一小段时间让日志产生
        await asyncio.sleep(0.5)
        
        # 3. 查询执行结果
        verification = await self.observability.verify_execution(
            task_id, 
            "success"
        )
        
        feedback = {
            "task_id": task_id,
            "action_result": result,
            "verification": verification.data if verification.success else None,
            "success": verification.success and verification.data.get("verified", False)
        }
        
        self.feedback_history.append(feedback)
        
        return feedback
    
    def get_feedback_summary(self) -> Dict:
        """获取反馈总结"""
        if not self.feedback_history:
            return {"total": 0, "success_rate": 0}
        
        total = len(self.feedback_history)
        success = sum(1 for f in self.feedback_history if f["success"])
        
        return {
            "total": total,
            "success": success,
            "failed": total - success,
            "success_rate": success / total if total > 0 else 0
        }


# 全局单例
_global_observability: Optional[AgentObservabilityClient] = None

def get_observability_client() -> AgentObservabilityClient:
    """获取全局可观测性客户端"""
    global _global_observability
    if _global_observability is None:
        _global_observability = AgentObservabilityClient()
    return _global_observability


# ============ 便捷函数 ============

async def query_logs(query: str, time_range: str = "1h") -> Dict:
    """快速查询日志"""
    q = LogQuery(query=query, time_range=time_range)
    result = await get_observability_client().query_logs(q)
    return {"success": result.success, "data": result.data, "error": result.error}


async def query_metric(metric: str, time_range: str = "1h") -> Dict:
    """快速查询指标"""
    q = MetricQuery(metric_name=metric, time_range=time_range)
    result = await get_observability_client().query_metrics(q)
    return {"success": result.success, "data": result.data, "error": result.error}


async def verify_task(task_id: str) -> Dict:
    """验证任务执行"""
    result = await get_observability_client().verify_execution(task_id, "success")
    return {"success": result.success, "data": result.data, "error": result.error}
