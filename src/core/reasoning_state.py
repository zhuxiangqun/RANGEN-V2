from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import time

@dataclass
class ReasoningState:
    """推理状态机"""
    query: str
    facts: List[Dict[str, Any]] = field(default_factory=list)
    hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    information_gaps: List[str] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    
    start_time: float = field(default_factory=time.time)
    max_duration: float = 60.0
    
    def is_solved(self) -> bool:
        """检查是否已解决 (Phase 3 简化版)"""
        # 如果有高置信度的假设被验证为真
        verified_hypotheses = [h for h in self.hypotheses if h.get('status') == 'verified']
        return len(verified_hypotheses) > 0
        
    def budget_exhausted(self) -> bool:
        """检查预算是否耗尽"""
        return (time.time() - self.start_time) > self.max_duration
        
    def update(self, result: Any):
        """更新状态"""
        self.history.append({
            "timestamp": time.time(),
            "result": result
        })
        # 实际逻辑应解析result并更新facts/hypotheses
        
    def is_stuck(self) -> bool:
        """检查是否卡住"""
        if len(self.history) < 3:
            return False
        # 简单规则：最近3步没有新增Fact
        # (Phase 3 简化实现)
        return False
