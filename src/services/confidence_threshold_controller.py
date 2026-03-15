"""
RAG检索置信度阈值控制服务
RAG Retrieval Confidence Threshold Control Service

基于Context Engineering文章建议：
- 置信度阈值：0.6（文章建议值）
- 低于阈值触发人工复核

核心功能：
1. 检索结果置信度评估
2. 阈值过滤与分级处理
3. 人工复核触发机制
4. 置信度统计与分析
"""

import logging
import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class ConfidenceLevel(str, Enum):
    """置信度级别"""
    HIGH = "high"           # >= 0.8 高置信度
    MEDIUM = "medium"       # 0.6-0.8 中等置信度
    LOW = "low"            # 0.4-0.6 低置信度
    CRITICAL = "critical"  # < 0.4 临界置信度


class ReviewAction(str, Enum):
    """复核动作"""
    AUTO_PROCEED = "auto_proceed"      # 自动通过
    WARNING = "warning"                 # 警告但继续
    REVIEW_REQUIRED = "review_required"  # 需要人工复核
    REJECT = "reject"                 # 拒绝/重新检索


@dataclass
class RetrievalResult:
    """检索结果"""
    content: str
    source: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThresholdDecision:
    """阈值决策结果"""
    action: ReviewAction
    confidence_level: ConfidenceLevel
    confidence: float
    threshold: float
    reason: str
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ReviewTask:
    """人工复核任务"""
    task_id: str
    query: str
    results: List[RetrievalResult]
    decision: ThresholdDecision
    created_at: float = field(default_factory=time.time)
    reviewed: bool = False
    review_result: Optional[str] = None


class ConfidenceThresholdController:
    """
    置信度阈值控制器
    
    遵循文章建议：
    - 如果检索结果的"执行置信度"低于0.6，要触发人工复核
    - 单次查询最多扫描50个文件，避免"检索范围过载"
    """
    
    # 默认阈值配置（基于文章建议）
    DEFAULT_CONFIDENCE_THRESHOLD = 0.6
    DEFAULT_HIGH_CONFIDENCE = 0.8
    DEFAULT_MEDIUM_CONFIDENCE = 0.6
    DEFAULT_LOW_CONFIDENCE = 0.4
    
    # 检索范围限制
    DEFAULT_MAX_FILES = 50
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 阈值配置
        self.confidence_threshold = self.config.get(
            'confidence_threshold', 
            self.DEFAULT_CONFIDENCE_THRESHOLD
        )
        self.high_confidence = self.config.get(
            'high_confidence',
            self.DEFAULT_HIGH_CONFIDENCE
        )
        self.medium_confidence = self.config.get(
            'medium_confidence',
            self.DEFAULT_MEDIUM_CONFIDENCE
        )
        self.low_confidence = self.config.get(
            'low_confidence',
            self.DEFAULT_LOW_CONFIDENCE
        )
        
        # 检索范围限制
        self.max_files = self.config.get('max_files', self.DEFAULT_MAX_FILES)
        
        # 人工复核回调
        self.review_callbacks: List[Callable] = []
        
        # 统计信息
        self.stats = {
            'total_queries': 0,
            'auto_proceed': 0,
            'warnings': 0,
            'review_required': 0,
            'rejected': 0,
            'review_completed': 0
        }
        
        # 待复核任务队列
        self.pending_reviews: Dict[str, ReviewTask] = {}
        
        # 历史决策记录
        self.decision_history: List[ThresholdDecision] = []
        self.max_history = 1000
        
        logger.info(f"置信度阈值控制器初始化完成: 阈值={self.confidence_threshold}")
    
    def set_threshold(self, threshold: float) -> None:
        """设置置信度阈值"""
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("阈值必须在0-1之间")
        self.confidence_threshold = threshold
        logger.info(f"置信度阈值已更新: {threshold}")
    
    def get_threshold(self) -> float:
        """获取当前置信度阈值"""
        return self.confidence_threshold
    
    def evaluate_results(
        self,
        query: str,
        results: List[RetrievalResult],
        file_count: Optional[int] = None
    ) -> ThresholdDecision:
        """
        评估检索结果置信度
        
        核心逻辑：
        1. 计算平均置信度
        2. 检查检索范围是否超限
        3. 根据阈值做出决策
        """
        self.stats['total_queries'] += 1
        
        # 如果没有结果，直接拒绝
        if not results:
            decision = ThresholdDecision(
                action=ReviewAction.REJECT,
                confidence_level=ConfidenceLevel.CRITICAL,
                confidence=0.0,
                threshold=self.confidence_threshold,
                reason="无检索结果",
                suggestions=["尝试扩大检索范围", "检查知识库是否为空", "调整查询关键词"]
            )
            self._record_decision(decision)
            self.stats['rejected'] += 1
            return decision
        
        # 计算置信度统计
        confidences = [r.confidence for r in results]
        avg_confidence = sum(confidences) / len(confidences)
        max_confidence = max(confidences)
        min_confidence = min(confidences)
        
        # 检查检索范围
        actual_file_count = file_count or len(results)
        range_warning = ""
        if actual_file_count > self.max_files:
            range_warning = f"检索范围超限: {actual_file_count} > {self.max_files}"
            logger.warning(range_warning)
        
        # 确定置信度级别
        confidence_level = self._get_confidence_level(avg_confidence)
        
        # 决策逻辑
        if avg_confidence >= self.high_confidence:
            # 高置信度 - 自动通过
            action = ReviewAction.AUTO_PROCEED
            reason = f"高置信度 (avg={avg_confidence:.2f})"
            self.stats['auto_proceed'] += 1
            
        elif avg_confidence >= self.confidence_threshold:
            # 中等置信度 - 警告但继续
            action = ReviewAction.WARNING
            reason = f"中等置信度 (avg={avg_confidence:.2f})"
            suggestions = [
                "建议检查关键结果的相关性",
                "可考虑补充更多检索来源"
            ]
            self.stats['warnings'] += 1
            
        elif avg_confidence >= self.low_confidence:
            # 低置信度 - 需要人工复核
            action = ReviewAction.REVIEW_REQUIRED
            reason = f"低置信度 (avg={avg_confidence:.2f})"
            suggestions = [
                "强烈建议人工复核检索结果",
                "考虑使用不同检索策略",
                "或补充外部知识源"
            ]
            self.stats['review_required'] += 1
            
        else:
            # 临界置信度 - 拒绝
            action = ReviewAction.REJECT
            reason = f"临界置信度 (avg={avg_confidence:.2f})"
            suggestions = [
                "检索结果置信度过低",
                "建议重新设计检索策略",
                "或使用其他知识来源"
            ]
            self.stats['rejected'] += 1
        
        # 添加范围警告
        if range_warning:
            reason += f"; {range_warning}"
            suggestions.append("考虑优化检索范围")
        
        decision = ThresholdDecision(
            action=action,
            confidence_level=confidence_level,
            confidence=avg_confidence,
            threshold=self.confidence_threshold,
            reason=reason,
            suggestions=suggestions
        )
        
        self._record_decision(decision)
        
        # 如果需要人工复核，触发回调
        if action == ReviewAction.REVIEW_REQUIRED:
            self._trigger_review(query, results, decision)
        
        logger.info(
            f"置信度评估: {action.value} "
            f"(avg={avg_confidence:.2f}, threshold={self.confidence_threshold})"
        )
        
        return decision
    
    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """获取置信度级别"""
        if confidence >= self.high_confidence:
            return ConfidenceLevel.HIGH
        elif confidence >= self.medium_confidence:
            return ConfidenceLevel.MEDIUM
        elif confidence >= self.low_confidence:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.CRITICAL
    
    def _record_decision(self, decision: ThresholdDecision) -> None:
        """记录决策到历史"""
        self.decision_history.append(decision)
        if len(self.decision_history) > self.max_history:
            self.decision_history.pop(0)
    
    def _trigger_review(
        self,
        query: str,
        results: List[RetrievalResult],
        decision: ThresholdDecision
    ) -> None:
        """触发人工复核"""
        task_id = f"review_{int(time.time() * 1000)}"
        
        review_task = ReviewTask(
            task_id=task_id,
            query=query,
            results=results,
            decision=decision
        )
        
        self.pending_reviews[task_id] = review_task
        
        # 触发回调
        for callback in self.review_callbacks:
            try:
                callback(review_task)
            except Exception as e:
                logger.error(f"复核回调执行失败: {e}")
        
        logger.info(f"创建人工复核任务: {task_id}")
    
    def register_review_callback(self, callback: Callable) -> None:
        """注册人工复核回调"""
        self.review_callbacks.append(callback)
        logger.info("已注册人工复核回调")
    
    def complete_review(
        self,
        task_id: str,
        review_result: str,
        approved: bool
    ) -> bool:
        """完成人工复核"""
        if task_id not in self.pending_reviews:
            logger.warning(f"复核任务不存在: {task_id}")
            return False
        
        task = self.pending_reviews[task_id]
        task.reviewed = True
        task.review_result = review_result
        
        self.stats['review_completed'] += 1
        
        # 从待复核队列移除
        del self.pending_reviews[task_id]
        
        logger.info(f"复核完成: {task_id}, approved={approved}")
        return approved
    
    def get_pending_reviews(self) -> List[ReviewTask]:
        """获取待复核任务"""
        return list(self.pending_reviews.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = self.stats['total_queries']
        
        return {
            **self.stats,
            'auto_proceed_rate': self.stats['auto_proceed'] / total if total > 0 else 0,
            'review_required_rate': self.stats['review_required'] / total if total > 0 else 0,
            'rejection_rate': self.stats['rejected'] / total if total > 0 else 0,
            'review_completion_rate': (
                self.stats['review_completed'] / self.stats['review_required']
                if self.stats['review_required'] > 0 else 0
            ),
            'pending_review_count': len(self.pending_reviews),
            'current_threshold': self.confidence_threshold
        }
    
    def get_recent_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近决策"""
        recent = self.decision_history[-limit:]
        
        return [
            {
                'action': d.action.value,
                'confidence_level': d.confidence_level.value,
                'confidence': d.confidence,
                'threshold': d.threshold,
                'reason': d.reason
            }
            for d in recent
        ]


class RetrievalWithThreshold:
    """带置信度控制的检索包装器"""
    
    def __init__(self, retrieval_service, config: Optional[Dict[str, Any]] = None):
        self.retrieval_service = retrieval_service
        self.controller = ConfidenceThresholdController(config)
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        require_threshold_check: bool = True
    ) -> Tuple[List[RetrievalResult], ThresholdDecision]:
        """
        执行检索并进行置信度评估
        
        Returns:
            (results, decision): 检索结果和阈值决策
        """
        # 执行检索
        raw_results = await self._execute_retrieval(query, top_k)
        
        # 转换为检索结果对象
        results = [
            RetrievalResult(
                content=r.get('content', ''),
                source=r.get('source', ''),
                confidence=r.get('confidence', r.get('similarity', 0.0)),
                metadata=r
            )
            for r in raw_results
        ]
        
        # 评估置信度
        if require_threshold_check:
            decision = self.controller.evaluate_results(
                query=query,
                results=results,
                file_count=len(raw_results)
            )
        else:
            # 不进行阈值检查，直接通过
            decision = ThresholdDecision(
                action=ReviewAction.AUTO_PROCEED,
                confidence_level=ConfidenceLevel.HIGH,
                confidence=results[0].confidence if results else 0.0,
                threshold=self.controller.confidence_threshold,
                reason="跳过阈值检查"
            )
        
        return results, decision
    
    async def _execute_retrieval(self, query: str, top_k: int) -> List[Dict]:
        """执行实际检索（适配不同服务）"""
        # 根据服务类型调用
        if hasattr(self.retrieval_service, 'retrieve'):
            result = await self.retrieval_service.retrieve(query, top_k)
            if hasattr(result, 'data'):
                return result.data.get('sources', [])
            return result.get('sources', []) if isinstance(result, dict) else []
        
        elif hasattr(self.retrieval_service, 'execute'):
            result = await self.retrieval_service.execute(query)
            if hasattr(result, 'data'):
                return result.data.get('sources', [])
            return result.get('sources', []) if isinstance(result, dict) else []
        
        return []


# 全局实例
_confidence_controller: Optional[ConfidenceThresholdController] = None


def get_confidence_controller(config: Optional[Dict[str, Any]] = None) -> ConfidenceThresholdController:
    """获取置信度控制器实例"""
    global _confidence_controller
    if _confidence_controller is None:
        _confidence_controller = ConfidenceThresholdController(config)
    return _confidence_controller


def create_confidence_controller(config: Optional[Dict[str, Any]] = None) -> ConfidenceThresholdController:
    """创建置信度控制器实例"""
    return ConfidenceThresholdController(config)
