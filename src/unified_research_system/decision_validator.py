"""
决策验证器模块

从 UnifiedResearchSystem 拆分出来的决策验证功能
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class Decision:
    """决策记录"""
    query_id: str
    decision: str
    timestamp: float
    result: Any = None


@dataclass
class EvidenceTrajectory:
    """证据轨迹"""
    knowledge_confidence: float = 0.0
    reasoning_confidence: float = 0.0
    answer_confidence: float = 0.0
    citations_count: int = 0


class DecisionValidator:
    """
    决策验证器
    
    验证:
    - 决策是否已提交
    - 答案长度是否有效
    - 证据置信度
    - 动态阈值
    """
    
    def __init__(self):
        # 决策缓存 (query_id -> 决策)
        self._committed_decisions: Dict[str, Decision] = {}
        
        # 最小/最大答案长度
        self._min_answer_length = 10
        self._max_answer_length = 10000
        
        # 基础阈值
        self._base_threshold = 0.5
    
    def _is_decision_committed(self, query_id: str) -> bool:
        """检查决策是否已提交"""
        return query_id in self._committed_decisions
    
    def _get_committed_decision(self, query_id: str) -> Optional[Any]:
        """获取已提交的决策"""
        decision = self._committed_decisions.get(query_id)
        if decision:
            return decision.result
        return None
    
    def commit_decision(
        self, 
        query_id: str, 
        decision: str, 
        result: Any
    ) -> None:
        """提交决策"""
        self._committed_decisions[query_id] = Decision(
            query_id=query_id,
            decision=decision,
            timestamp=time.time(),
            result=result,
        )
        
        # 清理旧决策 (保留最近1000条)
        if len(self._committed_decisions) > 1000:
            oldest = min(
                self._committed_decisions.items(),
                key=lambda x: x[1].timestamp
            )
            del self._committed_decisions[oldest[0]]
    
    def _is_valid_answer_length(self, answer: str) -> bool:
        """
        检查答案长度是否有效
        """
        length = len(answer)
        return self._min_answer_length <= length <= self._max_answer_length
    
    def _calculate_evidence_confidence(
        self, 
        evidence_trajectory: Dict[str, Any]
    ) -> float:
        """
        计算证据置信度
        
        基于:
        - 知识检索置信度
        - 推理置信度
        - 答案置信度
        - 引用数量
        """
        # 提取置信度
        knowledge_conf = evidence_trajectory.get("knowledge_confidence", 0.5)
        reasoning_conf = evidence_trajectory.get("reasoning_confidence", 0.5)
        answer_conf = evidence_trajectory.get("answer_confidence", 0.5)
        citations_count = evidence_trajectory.get("citations_count", 0)
        
        # 计算引用因子
        citation_factor = min(0.2, citations_count * 0.02)
        
        # 加权平均
        confidence = (
            knowledge_conf * 0.3 +
            reasoning_conf * 0.3 +
            answer_conf * 0.4 +
            citation_factor
        )
        
        return min(1.0, confidence)
    def _calculate_dynamic_threshold(
        self, 
        request: Any,
        evidence_trajectory: Dict[str, Any]
    ) -> float:
        """
        计算动态阈值
        
        根据查询复杂度和证据质量调整阈值
        """
        # 基础阈值
        threshold = self._base_threshold
        
        # 尝试获取查询复杂度
        try:
            query_len = len(request.query)
            
            # 长查询使用更低的阈值
            if query_len > 200:
                threshold -= 0.1
            elif query_len > 100:
                threshold -= 0.05
        except Exception:
            pass
        
        # 根据证据质量调整
        evidence_quality = self._calculate_evidence_confidence(evidence_trajectory)
        
        # 证据质量高，使用更低阈值
        if evidence_quality > 0.8:
            threshold -= 0.1
        elif evidence_quality > 0.6:
            threshold -= 0.05
        
        return max(0.3, min(0.9, threshold))  # 限制范围
    
    def validate_result(
        self,
        result: Any,
        threshold: float
    ) -> Dict[str, Any]:
        """
        验证结果
        
        检查答案和置信度
        """
        # 提取答案和置信度
        answer = ""
        confidence = 0.0
        
        if hasattr(result, "answer"):
            answer = result.answer or ""
        
        if hasattr(result, "confidence"):
            confidence = result.confidence
        elif hasattr(result, "data") and isinstance(result.data, dict):
            confidence = result.data.get("confidence", 0.0)
        
        # 检查答案长度
        if not self._is_valid_answer_length(answer):
            return {
                "valid": False,
                "reason": "invalid_length",
                "confidence": confidence,
            }
        
        # 检查置信度
        if confidence < threshold:
            return {
                "valid": False,
                "reason": "low_confidence",
                "confidence": confidence,
                "threshold": threshold,
            }
        
        return {
            "valid": True,
            "confidence": confidence,
            "answer": answer[:500],  # 截断
        }
    
    def multi_agent_validation(
        self,
        agent_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        多Agent协同验证
        
        检查多个Agent结果的一致性
        """
        if not agent_results:
            return {
                "passed": False,
                "reason": "no_results",
                "agreement_ratio": 0.0,
            }
        
        # 提取答案
        answers = []
        for result in agent_results:
            if isinstance(result, dict):
                answer = result.get("answer", "")
            else:
                answer = str(result) if result else ""
            answers.append(answer)
        
        # 计算一致性
        # 简单方法：检查答案长度是否相似
        lengths = [len(a) for a in answers if a]
        if not lengths:
            return {
                "passed": False,
                "reason": "no_answers",
                "agreement_ratio": 0.0,
            }
        
        avg_length = sum(lengths) / len(lengths)
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
        
        # 长度方差小于平均值20%认为一致
        if variance < (avg_length * 0.2) ** 2:
            agreement = 1.0
        else:
            agreement = max(0.0, 1.0 - variance / (avg_length ** 2))
        
        return {
            "passed": agreement >= 0.5,
            "agreement_ratio": agreement,
            "answers": answers,
            "avg_length": avg_length,
        }
    
    def clear_old_decisions(self, max_age_seconds: int = 3600) -> int:
        """
        清理旧决策
        
        返回清理的数量
        """
        current_time = time.time()
        old_keys = []
        
        for query_id, decision in self._committed_decisions.items():
            if current_time - decision.timestamp > max_age_seconds:
                old_keys.append(query_id)
        
        for key in old_keys:
            del self._committed_decisions[key]
        
        return len(old_keys)
