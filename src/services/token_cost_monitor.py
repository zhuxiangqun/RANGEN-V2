"""
Token成本监控服务
Token Cost Monitoring Service

基于Context Engineering文章建议：
- 简单任务可能消耗50万Token，成本$1-2
- 需要跟踪Token消耗，优化资源分配
- 核心指标从"准确率"转向"命中率"等效能指标

核心功能：
1. Token消耗跟踪 - 实时监控每次请求的Token使用
2. 成本计算 - 基于模型价格计算实际成本
3. 告警机制 - 异常消耗自动告警
4. 优化建议 - 基于数据分析的优化推荐
5. 效能指标 - 命中率、成本效率等
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """模型类型"""
    DEEPSEEK_REASONER = "deepseek-reasoner"
    DEEPSEEK_CHAT = "deepseek-chat"
    STEPSFLASH = "step-3.5-flash"
    LOCAL_LLAMA = "local-llama"
    LOCAL_QWEN = "local-qwen"
    CUSTOM_TRAINED = "custom-trained"


class CostAlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class TokenUsage:
    """Token使用记录"""
    request_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    timestamp: float
    session_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class CostAlert:
    """成本告警"""
    level: CostAlertLevel
    message: str
    current_cost: float
    threshold: float
    timestamp: float
    request_id: Optional[str] = None


class TokenCostMonitor:
    """
    Token成本监控服务
    
    遵循文章建议：
    - 简单任务可能消耗50万Token，成本$1-2
    - 需要跟踪Token消耗，优化资源分配
    - 核心指标从"准确率"转向"命中率"等效能指标
    """
    
    # 模型价格（$ per 1M tokens）- 示例价格
    MODEL_PRICING = {
        ModelType.DEEPSEEK_REASONER.value: {
            'prompt': 2.0,    # $2 per 1M prompt tokens (推理模型较贵)
            'completion': 4.0  # $4 per 1M completion tokens
        },
        ModelType.DEEPSEEK_CHAT.value: {
            'prompt': 0.14,   # $0.14 per 1M prompt tokens (DeepSeek Chat定价)
            'completion': 0.28 # $0.28 per 1M completion tokens
        },
        ModelType.STEPSFLASH.value: {
            'prompt': 0.0,    # 免费或极低成本 (OpenRouter免费层)
            'completion': 0.0  # 免费或极低成本
        },
        ModelType.LOCAL_LLAMA.value: {
            'prompt': 0.0,    # 完全本地，零API成本
            'completion': 0.0  # 完全本地，零API成本
        },
        ModelType.LOCAL_QWEN.value: {
            'prompt': 0.0,    # 完全本地，零API成本
            'completion': 0.0  # 完全本地，零API成本
        },
        ModelType.CUSTOM_TRAINED.value: {
            'prompt': 0.0,    # 自定义训练模型，仅训练成本，推理免费
            'completion': 0.0  # 自定义训练模型，仅训练成本，推理免费
        }
    }
    
    # 告警阈值
    DEFAULT_REQUEST_COST_THRESHOLD = 1.0   # 单次请求$1
    DEFAULT_SESSION_COST_THRESHOLD = 10.0    # 单会话$10
    DEFAULT_DAILY_COST_THRESHOLD = 100.0    # 每日$100
    DEFAULT_TOKEN_THRESHOLD = 500000        # 50万Token
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 告警阈值
        self.request_cost_threshold = self.config.get(
            'request_cost_threshold',
            self.DEFAULT_REQUEST_COST_THRESHOLD
        )
        self.session_cost_threshold = self.config.get(
            'session_cost_threshold',
            self.DEFAULT_SESSION_COST_THRESHOLD
        )
        self.daily_cost_threshold = self.config.get(
            'daily_cost_threshold',
            self.DEFAULT_DAILY_COST_THRESHOLD
        )
        self.token_threshold = self.config.get(
            'token_threshold',
            self.DEFAULT_TOKEN_THRESHOLD
        )
        
        # 数据存储
        self._usage_history: deque = deque(maxlen=10000)
        self._session_usage: Dict[str, Dict] = defaultdict(lambda: {
            'total_cost': 0.0,
            'total_tokens': 0,
            'request_count': 0
        })
        self._daily_usage: Dict[str, Dict] = defaultdict(lambda: {
            'total_cost': 0.0,
            'total_tokens': 0,
            'request_count': 0
        })
        
        self._lock = Lock()
        
        # 告警回调
        self._alert_callbacks: List[Callable] = []
        
        # 效能指标
        self._total_requests = 0
        self._total_cost = 0.0
        self._total_tokens = 0
        
        logger.info("Token成本监控服务初始化完成")
    
    def record_usage(
        self,
        request_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> TokenUsage:
        """
        记录Token使用
        
        计算成本：
        - prompt_tokens * prompt_price / 1M
        - completion_tokens * completion_price / 1M
        """
        total_tokens = prompt_tokens + completion_tokens
        
        # 计算成本
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)
        
        # 创建使用记录
        usage = TokenUsage(
            request_id=request_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            timestamp=time.time(),
            session_id=session_id,
            metadata=metadata or {}
        )
        
        # 存储记录
        with self._lock:
            self._usage_history.append(usage)
            
            # 更新会话统计
            if session_id:
                self._session_usage[session_id]['total_cost'] += cost
                self._session_usage[session_id]['total_tokens'] += total_tokens
                self._session_usage[session_id]['request_count'] += 1
            
            # 更新每日统计
            today = datetime.now().strftime('%Y-%m-%d')
            self._daily_usage[today]['total_cost'] += cost
            self._daily_usage[today]['total_tokens'] += total_tokens
            self._daily_usage[today]['request_count'] += 1
            
            # 更新总统计
            self._total_requests += 1
            self._total_cost += cost
            self._total_tokens += total_tokens
        
        # 检查是否触发告警
        self._check_alerts(usage, session_id)
        
        logger.debug(
            f"Token使用记录: request={request_id}, "
            f"tokens={total_tokens}, cost=${cost:.4f}"
        )
        
        return usage
    
    def _calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """计算成本"""
        pricing = self.MODEL_PRICING.get(model, {
            'prompt': 1.0,
            'completion': 1.0
        })
        
        prompt_cost = (prompt_tokens / 1_000_000) * pricing['prompt']
        completion_cost = (completion_tokens / 1_000_000) * pricing['completion']
        
        return prompt_cost + completion_cost
    
    def _check_alerts(
        self,
        usage: TokenUsage,
        session_id: Optional[str]
    ) -> None:
        """检查并触发告警"""
        alerts = []
        
        # 单次请求告警
        if usage.cost > self.request_cost_threshold:
            alerts.append(CostAlert(
                level=CostAlertLevel.WARNING if usage.cost < self.request_cost_threshold * 2 
                     else CostAlertLevel.CRITICAL,
                message=f"单次请求成本过高: ${usage.cost:.2f}",
                current_cost=usage.cost,
                threshold=self.request_cost_threshold,
                timestamp=time.time(),
                request_id=usage.request_id
            ))
        
        # Token数量告警
        if usage.total_tokens > self.token_threshold:
            alerts.append(CostAlert(
                level=CostAlertLevel.CRITICAL,
                message=f"Token消耗超限: {usage.total_tokens} > {self.token_threshold}",
                current_cost=usage.cost,
                threshold=float(self.token_threshold),
                timestamp=time.time(),
                request_id=usage.request_id
            ))
        
        # 会话成本告警
        if session_id and self._session_usage[session_id]['total_cost'] > self.session_cost_threshold:
            alerts.append(CostAlert(
                level=CostAlertLevel.WARNING,
                message=f"会话成本超限: ${self._session_usage[session_id]['total_cost']:.2f}",
                current_cost=self._session_usage[session_id]['total_cost'],
                threshold=self.session_cost_threshold,
                timestamp=time.time(),
                request_id=usage.request_id
            ))
        
        # 触发告警回调
        for alert in alerts:
            self._trigger_alert(alert)
    
    def _trigger_alert(self, alert: CostAlert) -> None:
        """触发告警"""
        logger.warning(f"成本告警: [{alert.level.value}] {alert.message}")
        
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调失败: {e}")
    
    def register_alert_callback(self, callback: Callable) -> None:
        """注册告警回调"""
        self._alert_callbacks.append(callback)
    
    def get_stats(
        self,
        since: Optional[float] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取统计数据"""
        with self._lock:
            # 筛选数据
            if since:
                usages = [u for u in self._usage_history if u.timestamp >= since]
            else:
                usages = list(self._usage_history)
            
            if session_id:
                usages = [u for u in usages if u.session_id == session_id]
            
            if not usages:
                return {
                    'total_requests': 0,
                    'total_cost': 0.0,
                    'total_tokens': 0,
                    'avg_cost_per_request': 0.0,
                    'avg_tokens_per_request': 0
                }
            
            total_cost = sum(u.cost for u in usages)
            total_tokens = sum(u.total_tokens for u in usages)
            
            return {
                'total_requests': len(usages),
                'total_cost': total_cost,
                'total_tokens': total_tokens,
                'avg_cost_per_request': total_cost / len(usages),
                'avg_tokens_per_request': total_tokens // len(usages),
                'max_cost_per_request': max(u.cost for u in usages),
                'max_tokens_per_request': max(u.total_tokens for u in usages),
                'min_cost_per_request': min(u.cost for u in usages),
                'min_tokens_per_request': min(u.total_tokens for u in usages)
            }
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """获取会话统计"""
        with self._lock:
            stats = self._session_usage.get(session_id, {
                'total_cost': 0.0,
                'total_tokens': 0,
                'request_count': 0
            })
            
            return {
                **stats,
                'avg_cost_per_request': (
                    stats['total_cost'] / stats['request_count']
                    if stats['request_count'] > 0 else 0
                )
            }
    
    def get_daily_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """获取每日统计"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        with self._lock:
            stats = self._daily_usage.get(date, {
                'total_cost': 0.0,
                'total_tokens': 0,
                'request_count': 0
            })
            
            return {
                **stats,
                'date': date,
                'avg_cost_per_request': (
                    stats['total_cost'] / stats['request_count']
                    if stats['request_count'] > 0 else 0
                )
            }
    
    def get_efficiency_metrics(self) -> Dict[str, Any]:
        """
        获取效能指标
        
        遵循文章建议：
        - 核心指标从"准确率"转向"命中率"等效能指标
        """
        with self._lock:
            # 计算命中率（这里简化为成功请求率）
            # 实际应该结合业务结果来计算
            successful_requests = sum(
                1 for u in self._usage_history
                if u.metadata.get('success', True)
            )
            hit_rate = (
                successful_requests / self._total_requests
                if self._total_requests > 0 else 0
            )
            
            # 成本效率（每次成功的成本）
            cost_efficiency = (
                self._total_cost / successful_requests
                if successful_requests > 0 else 0
            )
            
            # Token效率（每次成功的Token消耗）
            token_efficiency = (
                self._total_tokens / successful_requests
                if successful_requests > 0 else 0
            )
            
            return {
                'total_requests': self._total_requests,
                'total_cost': self._total_cost,
                'total_tokens': self._total_tokens,
                'hit_rate': hit_rate,  # 命中率
                'cost_efficiency': cost_efficiency,  # 每次成功请求的成本
                'token_efficiency': token_efficiency,  # 每次成功请求的Token消耗
                'avg_cost_per_1k_tokens': (
                    (self._total_cost / self._total_tokens * 1000)
                    if self._total_tokens > 0 else 0
                )
            }
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取优化建议"""
        suggestions = []
        
        # 获取最近100条记录分析
        recent = list(self._usage_history)[-100:]
        
        if not recent:
            return ["暂无数据"]
        
        # 分析平均Token消耗
        avg_tokens = sum(u.total_tokens for u in recent) / len(recent)
        
        if avg_tokens > 100000:
            suggestions.append(
                f"⚠️ 平均Token消耗较高 ({avg_tokens:.0f})，建议优化上下文管理"
            )
        
        # 分析高成本请求
        high_cost_requests = [u for u in recent if u.cost > 1.0]
        
        if len(high_cost_requests) > len(recent) * 0.1:
            suggestions.append(
                f"⚠️ 高成本请求占比 {(len(high_cost_requests)/len(recent))*100:.1f}%，需检查是否有异常"
            )
        
        # 分析会话成本
        with self._lock:
            high_session_costs = [
                (sid, stats) for sid, stats in self._session_usage.items()
                if stats['total_cost'] > self.session_cost_threshold
            ]
        
        if high_session_costs:
            suggestions.append(
                f"⚠️ {len(high_session_costs)} 个会话成本超限"
            )
        
        if not suggestions:
            suggestions.append("✅ Token消耗正常")
        
        return suggestions
    
    def get_recent_usage(self, limit: int = 10) -> List[Dict]:
        """获取最近使用记录"""
        recent = list(self._usage_history)[-limit:]
        
        return [
            {
                'request_id': u.request_id,
                'model': u.model,
                'prompt_tokens': u.prompt_tokens,
                'completion_tokens': u.completion_tokens,
                'total_tokens': u.total_tokens,
                'cost': u.cost,
                'timestamp': datetime.fromtimestamp(u.timestamp).isoformat(),
                'session_id': u.session_id
            }
            for u in recent
        ]


# 全局实例
_token_cost_monitor: Optional[TokenCostMonitor] = None


def get_token_cost_monitor(config: Optional[Dict[str, Any]] = None) -> TokenCostMonitor:
    """获取Token成本监控实例"""
    global _token_cost_monitor
    if _token_cost_monitor is None:
        _token_cost_monitor = TokenCostMonitor(config)
    return _token_cost_monitor


def create_token_cost_monitor(config: Optional[Dict[str, Any]] = None) -> TokenCostMonitor:
    """创建Token成本监控实例"""
    return TokenCostMonitor(config)
