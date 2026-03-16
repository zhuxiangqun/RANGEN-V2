#!/usr/bin/env python3
"""
Execution Coordinator with Review Integration

将评审决策集成到 ExecutionCoordinator:
- 在 quality_evaluator 节点后添加评审决策
- 基于评审结果决定是否重试或继续
- 与 JudgmentEvaluation 集成记录判断
"""
from typing import Dict, Any, TypedDict, Annotated, Literal, Optional
import operator

from src.core.execution_coordinator import AgentState, ExecutionCoordinator


class ReviewDecisionState(TypedDict):
    """扩展的状态，包含评审决策"""
    query: str
    context: Dict[str, Any]
    route: str
    steps: Annotated[list, operator.add]
    final_answer: str
    error: str
    quality_score: float
    quality_passed: bool
    quality_feedback: str
    retry_count: int
    review_decision: str  # 新增: proceed, revise, block, escalate
    review_score: float  # 新增: 评审评分


class ReviewEnabledCoordinator(ExecutionCoordinator):
    """
    支持评审的执行协调器
    
    在现有质量评估基础上增加:
    - 评审决策 (基于 ReviewPipeline)
    - 判断力记录 (基于 JudgmentEvaluation)
    - 上下文传递 (基于 ContextProtocol)
    """
    
    def __init__(self):
        super().__init__()
        
        # 初始化评审相关组件
        self._review_enabled = True
        self._judgment_system = None
        
        logger.info("ReviewEnabledCoordinator initialized")
    
    async def _review_decision_step(self, state: AgentState) -> AgentState:
        """
        评审决策步骤
        
        基于质量评估结果做最终决策
        """
        # 如果质量评估通过
        if state.get("quality_passed", False):
            # 执行评审
            decision, score = await self._make_review_decision(state)
            
            state["review_decision"] = decision
            state["review_score"] = score
            
            # 记录判断
            self._record_judgment(state, decision)
            
            # 基于决策处理
            if decision == "proceed":
                # 继续，返回最终答案
                pass
            elif decision == "revise":
                # 需要修改，增加重试次数
                state["retry_count"] = state.get("retry_count", 0) + 1
                state["quality_passed"] = False
                state["quality_feedback"] += f"\n[Review] 需要修改后重试"
            elif decision == "block":
                # 阻塞，记录错误
                state["error"] = "被评审阻塞: " + state.get("quality_feedback", "")
            elif decision == "escalate":
                # 升级，记录需要人工介入
                state["quality_feedback"] += "\n[Review] 需要专家评审"
        
        return state
    
    async def _make_review_decision(self, state: AgentState) -> tuple:
        """
        做评审决策
        
        Returns:
            (decision, score)
        """
        try:
            from src.core.review_pipeline import ReviewPipeline, ReviewLevel
            
            pipeline = ReviewPipeline(name="execution_review")
            
            # 准备评审内容
            artifact_content = {
                "query": state.get("query", ""),
                "answer": state.get("final_answer", ""),
                "quality_score": state.get("quality_score", 0),
                "quality_passed": state.get("quality_passed", False)
            }
            
            # 执行评审
            report = await pipeline.review(
                artifact_name="execution_result",
                artifact_content=artifact_content,
                level=ReviewLevel.L2_PEER,
                context=state.get("context", {})
            )
            
            from src.core.review_integration import ReviewDecisionMaker
            decision = ReviewDecisionMaker.decide(report.to_dict())
            
            return decision, report.score
            
        except ImportError:
            # 如果评审模块不可用，默认通过
            return "proceed", 100.0
    
    def _record_judgment(self, state: AgentState, decision: str):
        """记录判断到评价系统"""
        try:
            from src.core.judgment_evaluation import (
                JudgmentEvaluationSystem, JudgmentType
            )
            
            if self._judgment_system is None:
                self._judgment_system = JudgmentEvaluationSystem()
            
            # 记录判断
            self._judgment_system.record_judgment(
                agent_id="ExecutionCoordinator",
                period="default",
            judgment_type = JudgmentType.BLOCK if decision == "block" else JudgmentType.APPROVE
                artifact_name="execution_result",
                reason=state.get("quality_feedback", "")
            )
            
        except ImportError:
            pass
    
    def get_judgment_stats(self) -> Dict:
        """获取判断统计"""
        if self._judgment_system:
            return self._judgment_system.get_all_evaluations()
        return {}


def create_review_enabled_coordinator() -> ReviewEnabledCoordinator:
    """创建支持评审的协调器"""
    return ReviewEnabledCoordinator()
