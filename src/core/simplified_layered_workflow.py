"""
简化版分层工作流：SimplifiedLayeredWorkflow

避免LangGraph依赖，使用自定义工作流引擎实现分层架构。
用于验证架构设计和解决集成问题。
"""

import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from src.core.layered_architecture_types import (
    StrategicPlan, ExecutionParams, ExecutionResult, QueryAnalysis,
    SystemState, TaskType
)
from src.agents.chief_agent import ChiefAgent as StrategicChiefAgent
from src.agents.tactical_optimizer import TacticalOptimizer
from src.agents.execution_coordinator import ExecutionCoordinator

logger = logging.getLogger(__name__)


class WorkflowState(Enum):
    """工作流状态枚举"""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """工作流步骤"""
    name: str
    func: Callable
    description: str
    timeout: float = 30.0
    retry_count: int = 0


@dataclass
class WorkflowExecution:
    """工作流执行记录"""
    workflow_id: str
    state: WorkflowState = WorkflowState.CREATED
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SimplifiedLayeredWorkflow:
    """
    简化版分层工作流

    使用自定义工作流引擎，避免LangGraph依赖。
    实现完整的分层架构：战略 → 战术 → 协调 → 执行
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 初始化组件
        self.strategic_agent = StrategicChiefAgent()
        self.tactical_optimizer = TacticalOptimizer()
        self.execution_coordinator = ExecutionCoordinator()

        # 定义工作流步骤
        self.workflow_steps = self._define_workflow_steps()

        # 执行记录
        self.executions: Dict[str, WorkflowExecution] = {}

    def _define_workflow_steps(self) -> List[WorkflowStep]:
        """定义工作流步骤"""
        return [
            WorkflowStep(
                name="query_analysis",
                func=self._execute_query_analysis,
                description="查询分析步骤",
                timeout=10.0
            ),
            WorkflowStep(
                name="strategic_decision",
                func=self._execute_strategic_decision,
                description="战略决策步骤",
                timeout=15.0
            ),
            WorkflowStep(
                name="tactical_optimization",
                func=self._execute_tactical_optimization,
                description="战术优化步骤",
                timeout=10.0
            ),
            WorkflowStep(
                name="execution_coordination",
                func=self._execute_coordination,
                description="执行协调步骤",
                timeout=60.0
            ),
            WorkflowStep(
                name="result_processing",
                func=self._execute_result_processing,
                description="结果处理步骤",
                timeout=5.0
            )
        ]

    async def process_query(self, query: str, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        处理查询的主入口

        Args:
            query: 用户查询
            workflow_id: 可选的工作流ID

        Returns:
            处理结果字典
        """
        if workflow_id is None:
            workflow_id = f"workflow_{int(time.time() * 1000)}"

        self.logger.info(f"🚀 [SimplifiedLayeredWorkflow] 开始处理查询: {workflow_id}")

        # 创建执行记录
        execution = WorkflowExecution(workflow_id=workflow_id)
        self.executions[workflow_id] = execution

        execution.start_time = time.time()
        execution.state = WorkflowState.RUNNING

        try:
            # 初始化工作流上下文
            context = {
                'query': query,
                'workflow_id': workflow_id,
                'metadata': {},
                'node_execution_times': {},
                'errors': [],
                'warnings': []
            }

            # 按顺序执行工作流步骤
            for step in self.workflow_steps:
                execution.current_step = step.name

                step_start_time = time.time()

                try:
                    self.logger.info(f"📋 执行步骤: {step.name} - {step.description}")

                    # 执行步骤
                    result = await asyncio.wait_for(
                        step.func(context),
                        timeout=step.timeout
                    )

                    # 更新上下文
                    context.update(result)

                    # 记录步骤执行信息
                    step_execution_time = time.time() - step_start_time
                    context['node_execution_times'][step.name] = step_execution_time

                    step_record = {
                        'name': step.name,
                        'status': 'success',
                        'execution_time': step_execution_time,
                        'timestamp': time.time()
                    }
                    execution.steps.append(step_record)

                    self.logger.info(f"✅ 步骤 {step.name} 完成，耗时 {step_execution_time:.2f}s")

                except asyncio.TimeoutError:
                    error_msg = f"步骤 {step.name} 执行超时 ({step.timeout}s)"
                    self.logger.error(f"❌ {error_msg}")
                    execution.steps.append({
                        'name': step.name,
                        'status': 'timeout',
                        'execution_time': time.time() - step_start_time,
                        'timestamp': time.time(),
                        'error': error_msg
                    })
                    raise Exception(error_msg)

                except Exception as e:
                    error_msg = f"步骤 {step.name} 执行失败: {e}"
                    self.logger.error(f"❌ {error_msg}", exc_info=True)
                    execution.steps.append({
                        'name': step.name,
                        'status': 'failed',
                        'execution_time': time.time() - step_start_time,
                        'timestamp': time.time(),
                        'error': str(e)
                    })

                    # 记录错误但继续执行（除非是关键步骤）
                    if step.name in ['query_analysis', 'strategic_decision']:
                        raise Exception(error_msg)
                    else:
                        context['errors'].append(error_msg)

            # 工作流完成
            execution.end_time = time.time()
            execution.state = WorkflowState.COMPLETED

            # 构建最终结果
            result = self._build_final_result(context)

            total_time = execution.end_time - execution.start_time
            self.logger.info(f"✅ [SimplifiedLayeredWorkflow] 查询处理完成，耗时 {total_time:.2f}s")

            return result

        except Exception as e:
            # 工作流失败
            execution.end_time = time.time()
            execution.state = WorkflowState.FAILED
            execution.error = str(e)

            error_msg = f"工作流执行失败: {e}"
            self.logger.error(f"❌ [SimplifiedLayeredWorkflow] {error_msg}", exc_info=True)

            return {
                "final_answer": "系统处理出现错误，请稍后重试",
                "quality_score": 0.0,
                "execution_time": execution.end_time - execution.start_time,
                "metadata": {},
                "errors": [error_msg],
                "warnings": [],
                "node_times": {},
                "workflow_id": workflow_id
            }

    async def _execute_query_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行查询分析步骤"""
        query = context['query']

        # 构建查询分析结果
        query_analysis = QueryAnalysis(
            query=query,
            query_type=self._analyze_query_type(query),
            complexity_score=self._calculate_complexity_score(query),
            estimated_tasks=self._estimate_required_tasks(query),
            domain_knowledge=self._extract_domain_knowledge(query),
            reasoning_requirements=self._analyze_reasoning_requirements(query),
            evidence_requirements=self._analyze_evidence_requirements(query),
            quality_requirements=self._define_quality_requirements(query)
        )

        # 评估系统状态（简化版）
        system_state = SystemState()

        return {
            'query_analysis': query_analysis,
            'system_state': system_state,
            'complexity_score': query_analysis.complexity_score,
            'query_type': query_analysis.query_type
        }

    async def _execute_strategic_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行战略决策步骤"""
        query_analysis = context['query_analysis']
        system_state = context.get('system_state')

        # 执行战略决策
        strategic_plan = await self.strategic_agent.decide_strategy(
            query_analysis, system_state
        )

        # 记录元数据
        metadata = context.get('metadata', {})
        metadata["strategic_decision"] = {
            "task_count": len(strategic_plan.tasks),
            "execution_strategy": strategic_plan.execution_strategy.value,
            "estimated_complexity": strategic_plan.resource_requirements.get("estimated_complexity", 0)
        }

        return {
            'strategic_plan': strategic_plan,
            'metadata': metadata
        }

    async def _execute_tactical_optimization(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行战术优化步骤"""
        strategic_plan = context['strategic_plan']
        query_analysis = context['query_analysis']

        # 执行战术优化
        execution_params = await self.tactical_optimizer.optimize_execution(
            strategic_plan, {}, context.get('system_state')
        )

        # 记录元数据
        metadata = context.get('metadata', {})
        metadata["tactical_optimization"] = {
            "timeout_tasks": len(execution_params.timeouts),
            "parallel_tasks": sum(execution_params.parallelism.values()),
            "total_resources": sum(execution_params.resource_allocation.values())
        }

        return {
            'execution_params': execution_params,
            'metadata': metadata
        }

    async def _execute_coordination(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行协调步骤"""
        strategic_plan = context['strategic_plan']
        execution_params = context['execution_params']

        # 执行任务协调
        execution_result = await self.execution_coordinator.coordinate_execution(
            strategic_plan, execution_params
        )

        # 记录元数据
        metadata = context.get('metadata', {})
        metadata["execution_coordination"] = {
            "successful_tasks": execution_result.execution_metrics.get("successful_tasks", 0),
            "failed_tasks": execution_result.execution_metrics.get("failed_tasks", 0),
            "total_time": execution_result.execution_metrics.get("total_execution_time", 0),
            "quality_score": execution_result.quality_score
        }

        return {
            'execution_result': execution_result,
            'metadata': metadata
        }

    async def _execute_result_processing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行结果处理步骤"""
        execution_result = context['execution_result']

        # 设置最终输出
        final_answer = execution_result.final_answer
        quality_score = execution_result.quality_score

        # 合并错误和警告
        errors = context.get('errors', []) + execution_result.errors
        warnings = context.get('warnings', []) + execution_result.warnings

        # 添加执行摘要到元数据
        metadata = context.get('metadata', {})
        node_times = context.get('node_execution_times', {})
        total_time = sum(node_times.values())

        metadata["execution_summary"] = {
            "final_answer_length": len(execution_result.final_answer),
            "task_results_count": len(execution_result.task_results),
            "overall_quality": execution_result.quality_score,
            "has_errors": len(execution_result.errors) > 0,
            "has_warnings": len(execution_result.warnings) > 0,
            "total_execution_time": total_time
        }

        return {
            'final_answer': final_answer,
            'quality_score': quality_score,
            'errors': errors,
            'warnings': warnings,
            'metadata': metadata
        }

    def _build_final_result(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """构建最终结果"""
        return {
            "final_answer": context.get('final_answer', ''),
            "quality_score": context.get('quality_score', 0.0),
            "execution_time": context.get('node_execution_times', {}).get('total_execution_time', 0),
            "metadata": context.get('metadata', {}),
            "errors": context.get('errors', []),
            "warnings": context.get('warnings', []),
            "node_times": context.get('node_execution_times', {}),
            "workflow_id": context.get('workflow_id')
        }

    def _analyze_query_type(self, query: str) -> str:
        """分析查询类型"""
        query_lower = query.lower()

        if any(word in query_lower for word in ['为什么', '如何', '怎么', 'why', 'how']):
            return "reasoning"
        elif any(word in query_lower for word in ['比较', '对比', '区别', 'compare', 'difference']):
            return "analysis"
        elif any(word in query_lower for word in ['列出', '列举', 'list', 'enumerate']):
            return "factual"
        else:
            return "general"

    def _calculate_complexity_score(self, query: str) -> float:
        """计算复杂度评分"""
        # 基于查询长度、关键词复杂度等计算
        length_score = min(len(query) / 500, 1.0) * 2  # 最高2分

        # 复杂关键词检测
        complex_keywords = [
            '分析', '比较', '评估', '优化', '设计', '架构', '系统', '算法',
            'analyze', 'compare', 'evaluate', 'optimize', 'design', 'architecture', 'system', 'algorithm'
        ]
        keyword_score = sum(1 for kw in complex_keywords if kw in query.lower()) * 0.5

        # 逻辑连接词检测
        logic_words = ['如果', '那么', '因为', '所以', '但是', '然而', 'if', 'then', 'because', 'so', 'but', 'however']
        logic_score = sum(1 for word in logic_words if word in query.lower()) * 0.3

        total_score = length_score + keyword_score + logic_score
        return min(total_score, 5.0)  # 最高5分

    def _estimate_required_tasks(self, query: str) -> List[str]:
        """估算需要的任务"""
        tasks = []

        # 基础任务：知识检索
        tasks.append("knowledge_retrieval")

        # 根据查询类型添加任务
        query_lower = query.lower()
        if any(word in query_lower for word in ['为什么', '如何', '分析', 'why', 'how', 'analyze']):
            tasks.append("reasoning")

        if len(query) > 100:  # 长查询可能需要分析
            tasks.append("analysis")

        # 所有查询都需要答案生成
        tasks.append("answer_generation")
        tasks.append("citation")

        return tasks

    def _extract_domain_knowledge(self, query: str) -> List[str]:
        """提取领域知识"""
        # 这里可以集成NLP模型来提取领域知识
        # 暂时使用关键词匹配
        domains = []

        domain_keywords = {
            "technology": ["技术", "编程", "软件", "算法", "AI", "机器学习"],
            "science": ["科学", "物理", "化学", "生物", "数学"],
            "business": ["商业", "经济", "市场", "管理", "金融"],
            "history": ["历史", "事件", "人物", "时代"],
            "health": ["健康", "医疗", "疾病", "治疗"]
        }

        query_lower = query.lower()
        for domain, keywords in domain_keywords.items():
            if any(kw in query_lower for kw in keywords):
                domains.append(domain)

        return domains if domains else ["general"]

    def _analyze_reasoning_requirements(self, query: str) -> Dict[str, Any]:
        """分析推理需求"""
        reasoning_indicators = [
            '为什么', '如何', '怎么做', '原因', '解释',
            'why', 'how', 'reason', 'explain'
        ]

        requires_reasoning = any(indicator in query.lower() for indicator in reasoning_indicators)

        return {
            "requires_reasoning": requires_reasoning,
            "reasoning_depth": "deep" if len(query) > 200 else "standard",
            "logic_complexity": "high" if requires_reasoning else "low"
        }

    def _analyze_evidence_requirements(self, query: str) -> Dict[str, Any]:
        """分析证据需求"""
        return {
            "evidence_strength": "strong" if len(query) > 150 else "standard",
            "source_diversity": True,
            "verification_required": True
        }

    def _define_quality_requirements(self, query: str) -> Dict[str, Any]:
        """定义质量要求"""
        complexity = self._calculate_complexity_score(query)

        if complexity > 3.0:
            return {
                "min_quality_score": 0.9,
                "require_evidence": True,
                "require_reasoning": True,
                "require_citations": True
            }
        else:
            return {
                "min_quality_score": 0.7,
                "require_evidence": True,
                "require_reasoning": False,
                "require_citations": True
            }

    def get_execution_status(self, workflow_id: str) -> Optional[WorkflowExecution]:
        """获取执行状态"""
        return self.executions.get(workflow_id)

    def list_executions(self, limit: int = 10) -> List[WorkflowExecution]:
        """列出最近的执行记录"""
        executions = list(self.executions.values())
        executions.sort(key=lambda x: x.start_time or 0, reverse=True)
        return executions[:limit]

    def cancel_execution(self, workflow_id: str) -> bool:
        """取消执行"""
        execution = self.executions.get(workflow_id)
        if execution and execution.state == WorkflowState.RUNNING:
            execution.state = WorkflowState.CANCELLED
            execution.end_time = time.time()
            self.logger.info(f"✅ 执行已取消: {workflow_id}")
            return True
        return False


# 全局工作流实例
_simplified_workflow_instance = None

def get_simplified_workflow() -> SimplifiedLayeredWorkflow:
    """获取简化版分层工作流实例"""
    global _simplified_workflow_instance
    if _simplified_workflow_instance is None:
        _simplified_workflow_instance = SimplifiedLayeredWorkflow()
    return _simplified_workflow_instance
