#!/usr/bin/env python3
"""
Judgment-Based Evaluation - 判断力评价体系

基于文章洞见：
- "最稀缺的资源从实现能力转向判断能力"
- "好的 PM 会更值钱，差判断会更贵"
- 需要量化"判断力"的价值
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class JudgmentType(Enum):
    """判断类型"""
    BLOCK = "block"             # 拦截错误方向
    APPROVE = "approve"        # 批准正确方向
    REFINE = "refine"          # 改进建议
    ESCALATE = "escalate"      # 升级处理


class EvaluationDimension(Enum):
    """评价维度"""
    OUTPUT_VOLUME = "output_volume"     # 产出量
    QUALITY = "quality"                 # 质量
    JUDGMENT = "judgment"               # 判断力 (新增)
    CONTEXT_TRANSFER = "context_transfer"  # 上下文传递


@dataclass
class JudgmentRecord:
    """判断记录"""
    judge_id: str              # 判断者 ID
    judgment_type: JudgmentType
    artifact_name: str
    reason: str
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class AgentEvaluation:
    """
    Agent 评价
    
    包含产出和判断力两个维度
    """
    agent_id: str
    period: str              # 评价周期
    
    # 产出维度
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    
    # 质量维度
    avg_quality_score: float = 0.0
    review_pass_rate: float = 0.0
    
    # 判断力维度 (新增)
    judgments_made: int = 0
    blocks_count: int = 0          # 拦截次数
    approvals_count: int = 0        # 批准次数
    correct_blocks: int = 0         # 正确拦截
    incorrect_blocks: int = 0       # 错误拦截
    
    # 上下文传递
    context_passed: int = 0
    context_quality_score: float = 0.0
    
    # 元数据
    last_updated: str = ""
    
    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
    
    @property
    def judgment_accuracy(self) -> float:
        """判断准确率"""
        if self.blocks_count == 0:
            return 0.0
        return self.correct_blocks / self.blocks_count
    
    @property
    def judgment_ratio(self) -> float:
        """判断占比 - 判断次数/总任务"""
        if self.total_tasks == 0:
            return 0.0
        return self.judgments_made / self.total_tasks
    
    @property
    def block_rate(self) -> float:
        """拦截率"""
        if self.total_tasks == 0:
            return 0.0
        return self.blocks_count / self.total_tasks
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "period": self.period,
            "output": {
                "total_tasks": self.total_tasks,
                "completed_tasks": self.completed_tasks,
                "failed_tasks": self.failed_tasks,
                "completion_rate": self.completed_tasks / self.total_tasks if self.total_tasks > 0 else 0
            },
            "quality": {
                "avg_quality_score": self.avg_quality_score,
                "review_pass_rate": self.review_pass_rate
            },
            "judgment": {
                "judgments_made": self.judgments_made,
                "blocks_count": self.blocks_count,
                "approvals_count": self.approvals_count,
                "judgment_accuracy": self.judgment_accuracy,
                "judgment_ratio": self.judgment_ratio,
                "block_rate": self.block_rate
            },
            "context_transfer": {
                "context_passed": self.context_passed,
                "context_quality_score": self.context_quality_score
            },
            "last_updated": self.last_updated
        }


class JudgmentEvaluationSystem:
    """
    判断力评价系统
    
    量化"判断力"的价值
    """
    
    def __init__(self):
        self._evaluations: Dict[str, AgentEvaluation] = {}
        self._judgment_history: List[JudgmentRecord] = []
    
    def record_task(self, agent_id: str, period: str, completed: bool):
        """记录任务执行"""
        key = f"{agent_id}_{period}"
        
        if key not in self._evaluations:
            self._evaluations[key] = AgentEvaluation(
                agent_id=agent_id,
                period=period
            )
        
        eval = self._evaluations[key]
        eval.total_tasks += 1
        if completed:
            eval.completed_tasks += 1
        else:
            eval.failed_tasks += 1
    
    def record_judgment(
        self,
        agent_id: str,
        period: str,
        judgment_type: JudgmentType,
        artifact_name: str,
        reason: str,
        is_correct: bool = None
    ):
        """记录判断"""
        # 记录判断
        record = JudgmentRecord(
            judge_id=agent_id,
            judgment_type=judgment_type,
            artifact_name=artifact_name,
            reason=reason
        )
        self._judgment_history.append(record)
        
        # 更新统计
        key = f"{agent_id}_{period}"
        if key not in self._evaluations:
            self._evaluations[key] = AgentEvaluation(
                agent_id=agent_id,
                period=period
            )
        
        eval = self._evaluations[key]
        eval.judgments_made += 1
        
        if judgment_type == JudgmentType.BLOCK:
            eval.blocks_count += 1
            if is_correct is True:
                eval.correct_blocks += 1
            elif is_correct is False:
                eval.incorrect_blocks += 1
        
        elif judgment_type == JudgmentType.APPROVE:
            eval.approvals_count += 1
    
    def record_context_pass(self, agent_id: str, period: str, quality: float):
        """记录上下文传递"""
        key = f"{agent_id}_{period}"
        
        if key not in self._evaluations:
            self._evaluations[key] = AgentEvaluation(
                agent_id=agent_id,
                period=period
            )
        
        eval = self._evaluations[key]
        eval.context_passed += 1
        eval.context_quality_score = (
            (eval.context_quality_score * (eval.context_passed - 1) + quality)
            / eval.context_passed
        )
    
    def get_evaluation(self, agent_id: str, period: str) -> Optional[AgentEvaluation]:
        """获取评价"""
        key = f"{agent_id}_{period}"
        return self._evaluations.get(key)
    
    def get_all_evaluations(self, period: str = None) -> List[AgentEvaluation]:
        """获取所有评价"""
        evaluations = list(self._evaluations.values())
        
        if period:
            evaluations = [e for e in evaluations if e.period == period]
        
        return evaluations
    
    def get_judgment_leaders(self, period: str, top_n: int = 5) -> List[Dict]:
        """获取判断力排名前 N"""
        evaluations = self.get_all_evaluations(period)
        
        # 按判断准确率排序
        sorted_evals = sorted(
            evaluations,
            key=lambda e: e.judgment_accuracy,
            reverse=True
        )
        
        return [
            {
                "agent_id": e.agent_id,
                "judgment_accuracy": e.judgment_accuracy,
                "blocks_count": e.blocks_count,
                "correct_blocks": e.correct_blocks,
                "judgment_ratio": e.judgment_ratio
            }
            for e in sorted_evals[:top_n]
        ]
    
    def generate_report(self, period: str) -> str:
        """生成评价报告"""
        evaluations = self.get_all_evaluations(period)
        
        lines = [
            f"# Agent 评价报告 - {period}",
            "",
            f"**总 Agent 数**: {len(evaluations)}",
            ""
        ]
        
        # 统计
        total_tasks = sum(e.total_tasks for e in evaluations)
        total_judgments = sum(e.judgments_made for e in evaluations)
        total_blocks = sum(e.blocks_count for e in evaluations)
        
        lines.append("## 总体统计")
        lines.append(f"- 总任务数: {total_tasks}")
        lines.append(f"- 总判断数: {total_judgments}")
        lines.append(f"- 总拦截数: {total_blocks}")
        lines.append(f"- 平均判断准确率: {sum(e.judgment_accuracy for e in evaluations)/len(evaluations) if evaluations else 0:.2%}")
        lines.append("")
        
        # 判断力排名
        lines.append("## 判断力排名")
        
        leaders = self.get_judgment_leaders(period)
        for i, leader in enumerate(leaders, 1):
            lines.append(
                f"{i}. {leader['agent_id']}: "
                f"准确率 {leader['judgment_accuracy']:.2%}, "
                f"拦截 {leader['blocks_count']} 次"
            )
        
        return "\n".join(lines)


# === 便捷函数 ===

def create_evaluation_system() -> JudgmentEvaluationSystem:
    """创建评价系统"""
    return JudgmentEvaluationSystem()


def quick_record_judgment(
    system: JudgmentEvaluationSystem,
    agent_id: str,
    judgment_type: str,
    artifact: str,
    period: str = "default"
):
    """快速记录判断"""
    jtype = JudgmentType(judgment_type)
    system.record_judgment(
        agent_id=agent_id,
        period=period,
        judgment_type=jtype,
        artifact_name=artifact,
        reason=""
    )
