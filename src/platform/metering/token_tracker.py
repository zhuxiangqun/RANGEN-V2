"""
Token 计量服务 - 按应用追踪 Token 使用

功能:
- 按 App 追踪 Token 使用
- 与 QuotaManager 集成
- 用量聚合与报表

纯新增，不影响现有系统
"""

import os
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ModelType(Enum):
    """模型类型"""
    DEEPSEEK_REASONER = "deepseek-reasoner"
    DEEPSEEK_CHAT = "deepseek-chat"
    OPENAI_GPT4 = "openai-gpt4"
    OPENAI_GPT35 = "openai-gpt35"
    GEMINI = "gemini"
    LOCAL_LLAMA = "local-llama"
    LOCAL_QWEN = "local-qwen"
    OTHER = "other"


@dataclass
class TokenRecord:
    """Token 记录"""
    app_id: str
    request_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class TokenUsageSummary:
    """Token 使用汇总"""
    app_id: str
    total_requests: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    model_breakdown: Dict[str, int] = field(default_factory=dict)  # model -> token count


class TokenTracker:
    """
    Token 计量器 - 单例模式
    
    功能:
    - 按应用追踪 Token 使用
    - 模型价格计算
    - 用量聚合
    """
    
    _instance: Optional['TokenTracker'] = None
    
    # 模型价格 ($ per 1M tokens)
    MODEL_PRICING = {
        ModelType.DEEPSEEK_REASONER.value: {'prompt': 2.0, 'completion': 4.0},
        ModelType.DEEPSEEK_CHAT.value: {'prompt': 0.14, 'completion': 0.28},
        ModelType.OPENAI_GPT4.value: {'prompt': 30.0, 'completion': 60.0},
        ModelType.OPENAI_GPT35.value: {'prompt': 0.5, 'completion': 1.5},
        ModelType.GEMINI.value: {'prompt': 0.125, 'completion': 0.5},
        ModelType.LOCAL_LLAMA.value: {'prompt': 0.0, 'completion': 0.0},
        ModelType.LOCAL_QWEN.value: {'prompt': 0.0, 'completion': 0.0},
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Token 记录列表 (内存存储)
        self._records: List[TokenRecord] = []
        self._max_records = 100000  # 最多保留 10 万条记录
        
        # 按应用的汇总
        self._summaries: Dict[str, TokenUsageSummary] = {}
        
        # 当前月份
        self._current_month = datetime.now().strftime('%Y-%m')
        
        self._initialized = True
    
    def record(
        self,
        app_id: str,
        request_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> TokenRecord:
        """
        记录 Token 使用
        
        Args:
            app_id: 应用 ID
            request_id: 请求 ID
            model: 模型名称
            prompt_tokens: Prompt Token 数
            completion_tokens: Completion Token 数
            session_id: 会话 ID
            metadata: 元数据
            
        Returns:
            TokenRecord: 记录对象
        """
        total_tokens = prompt_tokens + completion_tokens
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)
        
        record = TokenRecord(
            app_id=app_id,
            request_id=request_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            session_id=session_id,
            metadata=metadata or {}
        )
        
        # 添加到记录列表
        self._records.append(record)
        
        # 清理过旧的记录
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]
        
        # 更新汇总
        self._update_summary(app_id, record)
        
        return record
    
    def _calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """计算成本"""
        # 尝试获取价格
        pricing = self.MODEL_PRICING.get(
            model,
            self.MODEL_PRICING.get(ModelType.OTHER.value, {'prompt': 1.0, 'completion': 1.0})
        )
        
        prompt_cost = (prompt_tokens / 1_000_000) * pricing['prompt']
        completion_cost = (completion_tokens / 1_000_000) * pricing['completion']
        
        return prompt_cost + completion_cost
    
    def _update_summary(self, app_id: str, record: TokenRecord):
        """更新应用汇总"""
        if app_id not in self._summaries:
            self._summaries[app_id] = TokenUsageSummary(app_id=app_id)
        
        summary = self._summaries[app_id]
        
        summary.total_requests += 1
        summary.total_prompt_tokens += record.prompt_tokens
        summary.total_completion_tokens += record.completion_tokens
        summary.total_tokens += record.total_tokens
        summary.total_cost += record.cost
        
        # 更新模型分解
        if record.model not in summary.model_breakdown:
            summary.model_breakdown[record.model] = 0
        summary.model_breakdown[record.model] += record.total_tokens
    
    def get_summary(self, app_id: str) -> Optional[TokenUsageSummary]:
        """获取应用汇总"""
        return self._summaries.get(app_id)
    
    def get_all_summaries(self) -> Dict[str, TokenUsageSummary]:
        """获取所有应用汇总"""
        return self._summaries.copy()
    
    def get_records(
        self,
        app_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """获取记录"""
        records = self._records
        
        if app_id:
            records = [r for r in records if r.app_id == app_id]
        
        if session_id:
            records = [r for r in records if r.session_id == session_id]
        
        # 返回最新的记录
        records = records[-limit:]
        
        return [
            {
                'app_id': r.app_id,
                'request_id': r.request_id,
                'model': r.model,
                'prompt_tokens': r.prompt_tokens,
                'completion_tokens': r.completion_tokens,
                'total_tokens': r.total_tokens,
                'cost': r.cost,
                'timestamp': r.timestamp.isoformat(),
                'session_id': r.session_id
            }
            for r in records
        ]
    
    def get_session_usage(self, app_id: str, session_id: str) -> Dict:
        """获取会话使用情况"""
        session_records = [
            r for r in self._records
            if r.app_id == app_id and r.session_id == session_id
        ]
        
        if not session_records:
            return {
                'app_id': app_id,
                'session_id': session_id,
                'total_requests': 0,
                'total_tokens': 0,
                'total_cost': 0.0
            }
        
        return {
            'app_id': app_id,
            'session_id': session_id,
            'total_requests': len(session_records),
            'total_tokens': sum(r.total_tokens for r in session_records),
            'total_cost': sum(r.cost for r in session_records)
        }
    
    def get_model_breakdown(self, app_id: str) -> Dict[str, Dict]:
        """获取模型使用分解"""
        summary = self._summaries.get(app_id)
        if not summary:
            return {}
        
        result = {}
        for model, token_count in summary.model_breakdown.items():
            pricing = self.MODEL_PRICING.get(
                model,
                {'prompt': 1.0, 'completion': 1.0}
            )
            # 估算成本
            avg_ratio = 0.3  # 假设 30% 是 completion
            estimated_cost = (token_count / 1_000_000) * (
                pricing['prompt'] * (1 - avg_ratio) + 
                pricing['completion'] * avg_ratio
            )
            
            result[model] = {
                'token_count': token_count,
                'estimated_cost': estimated_cost,
                'percentage': (token_count / summary.total_tokens * 100) if summary.total_tokens > 0 else 0
            }
        
        return result
    
    def reset_monthly(self, app_id: Optional[str] = None):
        """重置月度数据"""
        if app_id:
            if app_id in self._summaries:
                self._summaries[app_id] = TokenUsageSummary(app_id=app_id)
        else:
            # 重置所有
            self._summaries = {}
        
        self._current_month = datetime.now().strftime('%Y-%m')
    
    def __len__(self) -> int:
        """获取记录数量"""
        return len(self._records)


# 全局单例
_token_tracker: Optional[TokenTracker] = None


def get_token_tracker() -> TokenTracker:
    """获取 Token 计量器实例"""
    global _token_tracker
    if _token_tracker is None:
        _token_tracker = TokenTracker()
    return _token_tracker
