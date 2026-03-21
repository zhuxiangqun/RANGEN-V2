"""
配额管理器 - 纯新增，不影响现有系统

功能:
- 配额限制设置
- 用量检查与记录
- 多维度配额控制 (请求频率、Token、成本)

使用单例模式，确保全局唯一实例
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
from datetime import datetime


@dataclass
class QuotaLimit:
    """配额限制"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    tokens_per_month: int = 1_000_000
    cost_per_month: float = 100.0


@dataclass
class QuotaUsage:
    """配额使用情况"""
    requests_minute: int = 0
    requests_hour: int = 0
    requests_day: int = 0
    tokens_month: int = 0
    cost_month: float = 0.0
    last_reset_minute: datetime = field(default_factory=datetime.now)
    last_reset_hour: datetime = field(default_factory=datetime.now)
    last_reset_day: datetime = field(default_factory=datetime.now)


class QuotaManager:
    """
    配额管理器 - 单例模式
    
    功能:
    - 设置应用配额
    - 检查配额是否允许
    - 记录使用量
    - 获取用量报表
    
    使用内存存储，Phase 1 不涉及数据库
    """
    
    _instance: Optional['QuotaManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._quotas: Dict[str, QuotaLimit] = {}  # app_id -> QuotaLimit
        self._usage: Dict[str, QuotaUsage] = {}  # app_id -> QuotaUsage
        self._initialized = True
        
        # 从环境变量加载默认值
        self._default_requests_per_minute = int(
            os.getenv("RANGEN_DEFAULT_QUOTA_REQUESTS_PER_MINUTE", "60")
        )
        self._default_tokens_per_month = int(
            os.getenv("RANGEN_DEFAULT_QUOTA_TOKENS_PER_MONTH", "1000000")
        )
        self._default_cost_per_month = float(
            os.getenv("RANGEN_DEFAULT_QUOTA_COST_PER_MONTH", "100.0")
        )
    
    def set_quota(self, app_id: str, quota: QuotaLimit) -> None:
        """
        设置应用配额
        
        Args:
            app_id: 应用ID
            quota: 配额限制
        """
        self._quotas[app_id] = quota
        if app_id not in self._usage:
            self._usage[app_id] = QuotaUsage()
    
    def get_quota(self, app_id: str) -> Optional[QuotaLimit]:
        """获取应用配额"""
        return self._quotas.get(app_id)
    
    def check_quota(
        self,
        app_id: str,
        tokens: int = 0,
        cost: float = 0.0
    ) -> Tuple[bool, Optional[str]]:
        """
        检查配额是否允许请求
        
        Args:
            app_id: 应用ID
            tokens: 本次请求消耗的 Token 数
            cost: 本次请求消耗的成本
            
        Returns:
            Tuple[bool, Optional[str]]: (是否允许, 拒绝原因)
        """
        quota = self._quotas.get(app_id)
        usage = self._usage.get(app_id)
        
        # 如果没有设置配额，使用默认值或允许通过
        if not quota:
            return True, None
        
        if not usage:
            return True, None
        
        # 清理过期的计数器
        self._reset_if_needed(app_id)
        
        now = datetime.now()
        
        # 检查请求频率 (每分钟)
        if quota.requests_per_minute > 0:
            if usage.requests_minute >= quota.requests_per_minute:
                return False, f"请求频率超限: 每分钟最多 {quota.requests_per_minute} 请求"
        
        # 检查请求频率 (每小时)
        if quota.requests_per_hour > 0:
            if usage.requests_hour >= quota.requests_per_hour:
                return False, f"请求频率超限: 每小时最多 {quota.requests_per_hour} 请求"
        
        # 检查请求频率 (每天)
        if quota.requests_per_day > 0:
            if usage.requests_day >= quota.requests_per_day:
                return False, f"请求频率超限: 每天最多 {quota.requests_per_day} 请求"
        
        # 检查 Token 配额
        if quota.tokens_per_month > 0:
            if usage.tokens_month + tokens > quota.tokens_per_month:
                remaining = quota.tokens_per_month - usage.tokens_month
                return False, f"Token配额不足: 剩余 {remaining}, 需要 {tokens}"
        
        # 检查成本配额
        if quota.cost_per_month > 0:
            if usage.cost_month + cost > quota.cost_per_month:
                remaining = quota.cost_per_month - usage.cost_month
                return False, f"成本配额不足: 剩余 ${remaining:.2f}, 需要 ${cost:.2f}"
        
        return True, None
    
    def record_usage(
        self,
        app_id: str,
        tokens: int = 0,
        cost: float = 0.0
    ) -> None:
        """
        记录使用量
        
        Args:
            app_id: 应用ID
            tokens: 消耗的 Token 数
            cost: 消耗的成本
        """
        if app_id not in self._usage:
            self._usage[app_id] = QuotaUsage()
        
        usage = self._usage[app_id]
        now = datetime.now()
        
        # 清理过期的计数器
        self._reset_if_needed(app_id)
        
        # 更新计数
        usage.requests_minute += 1
        usage.requests_hour += 1
        usage.requests_day += 1
        usage.tokens_month += tokens
        usage.cost_month += cost
    
    def get_usage(self, app_id: str) -> Optional[Dict]:
        """
        获取应用使用情况
        
        Args:
            app_id: 应用ID
            
        Returns:
            Optional[Dict]: 使用情况字典
        """
        usage = self._usage.get(app_id)
        quota = self._quotas.get(app_id)
        
        if not usage:
            return None
        
        # 清理过期的计数器
        self._reset_if_needed(app_id)
        
        result = {
            'app_id': app_id,
            'requests': {
                'minute': usage.requests_minute,
                'hour': usage.requests_hour,
                'day': usage.requests_day
            },
            'tokens_month': usage.tokens_month,
            'cost_month': usage.cost_month,
            'last_reset': {
                'minute': usage.last_reset_minute.isoformat(),
                'hour': usage.last_reset_hour.isoformat(),
                'day': usage.last_reset_day.isoformat()
            }
        }
        
        if quota:
            result['quota'] = {
                'requests_per_minute': quota.requests_per_minute,
                'requests_per_hour': quota.requests_per_hour,
                'requests_per_day': quota.requests_per_day,
                'tokens_per_month': quota.tokens_per_month,
                'cost_per_month': quota.cost_per_month
            }
            
            # 计算使用百分比
            result['usage_percent'] = {
                'tokens': (
                    usage.tokens_month / quota.tokens_per_month * 100
                    if quota.tokens_per_month > 0 else 0
                ),
                'cost': (
                    usage.cost_month / quota.cost_per_month * 100
                    if quota.cost_per_month > 0 else 0
                )
            }
        
        return result
    
    def reset_usage(self, app_id: str) -> bool:
        """重置应用使用量"""
        if app_id not in self._usage:
            return False
        
        self._usage[app_id] = QuotaUsage()
        return True
    
    def _reset_if_needed(self, app_id: str) -> None:
        """检查并重置过期的计数器"""
        usage = self._usage.get(app_id)
        if not usage:
            return
        
        now = datetime.now()
        
        # 检查分钟级重置
        if (now - usage.last_reset_minute).total_seconds() >= 60:
            usage.requests_minute = 0
            usage.last_reset_minute = now
        
        # 检查小时级重置
        if (now - usage.last_reset_hour).total_seconds() >= 3600:
            usage.requests_hour = 0
            usage.last_reset_hour = now
        
        # 检查天级重置
        if (now - usage.last_reset_day).total_seconds() >= 86400:
            usage.requests_day = 0
            usage.tokens_month = 0
            usage.cost_month = 0.0
            usage.last_reset_day = now
    
    def list_all_usage(self) -> Dict[str, Dict]:
        """获取所有应用的使用情况"""
        result = {}
        for app_id in self._usage:
            usage_info = self.get_usage(app_id)
            if usage_info:
                result[app_id] = usage_info
        return result
    
    def __len__(self) -> int:
        """获取已设置配额的应用数量"""
        return len(self._quotas)


# 全局单例
_quota_manager: Optional[QuotaManager] = None


def get_quota_manager() -> QuotaManager:
    """获取配额管理器实例"""
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = QuotaManager()
    return _quota_manager
