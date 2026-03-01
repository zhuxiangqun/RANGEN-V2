"""
分层架构LangGraph工作流：LayeredArchitectureWorkflow

基于分层架构设计的新一代LangGraph工作流：
战略决策层 → 战术优化层 → 执行协调层 → 任务执行层

替代原有的耦合式架构，实现职责分离和模块化设计。
"""

import logging
import time
from typing import Dict, List, Any, Optional, Annotated
from dataclasses import dataclass, field

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.core.layered_architecture_types import (
    StrategicPlan, ExecutionParams, ExecutionResult, QueryAnalysis,
    SystemState, TaskType
)
from src.agents.chief_agent import ChiefAgent as StrategicChiefAgent
from src.agents.tactical_optimizer import TacticalOptimizer
from src.agents.execution_coordinator import ExecutionCoordinator
from src.agents.task_executor_adapter import create_unified_executor

logger = logging.getLogger(__name__)


@dataclass
class LayeredWorkflowState:
    """分层工作流状态"""

    # 输入状态
    query: str = ""
    query_analysis: Optional[QueryAnalysis] = None
    system_state: Optional[SystemState] = None

    # 分层决策结果
    strategic_plan: Optional[StrategicPlan] = None
    execution_params: Optional[ExecutionParams] = None
    execution_result: Optional[ExecutionResult] = None

    # 最终输出
    final_answer: str = ""
    quality_score: float = 0.0

    # 元数据和监控
    metadata: Dict[str, Any] = field(default_factory=dict)
    node_execution_times: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # 兼容性字段（用于与现有系统集成）
    route_path: str = ""
    complexity_score: float = 1.0
    query_type: str = "general"


class LayeredArchitectureWorkflow:
    """
    分层架构工作流

    实现战略决策 → 战术优化 → 执行协调的三层架构
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 初始化组件
        self.strategic_agent = StrategicChiefAgent()
        self.tactical_optimizer = TacticalOptimizer()
        self.execution_coordinator = ExecutionCoordinator()

        # 注册任务执行器
        self._register_task_executors()

        # 构建工作流
        self.workflow = self._build_workflow()

        # 编译工作流
        self.app = self.workflow.compile()

    def _register_task_executors(self):
        """注册任务执行器"""
        try:
            # 创建统一执行器并注册到协调器
            unified_executor = create_unified_executor()

            # 注册所有任务类型
            task_types = [
                TaskType.KNOWLEDGE_RETRIEVAL,
                TaskType.REASONING,
                TaskType.ANSWER_GENERATION,
                TaskType.CITATION,
                TaskType.ANALYSIS,
                TaskType.MEMORY
            ]

            for task_type in task_types:
                # 这里可以根据需要添加特定的执行器
                # 目前使用统一执行器
                pass

            self.logger.info("✅ [LayeredArchitectureWorkflow] 任务执行器注册完成")

        except Exception as e:
            self.logger.error(f"❌ [LayeredArchitectureWorkflow] 任务执行器注册失败: {e}")

    def _build_workflow(self) -> StateGraph:
        """构建分层工作流"""

        workflow = StateGraph(LayeredWorkflowState)

        # 添加节点
        workflow.add_node("query_analysis", self.query_analysis_node)
        workflow.add_node("strategic_decision", self.strategic_decision_node)
        workflow.add_node("tactical_optimization", self.tactical_optimization_node)
        workflow.add_node("execution_coordination", self.execution_coordination_node)
        workflow.add_node("result_processing", self.result_processing_node)

        # 定义边
        workflow.add_edge("query_analysis", "strategic_decision")
        workflow.add_edge("strategic_decision", "tactical_optimization")
        workflow.add_edge("tactical_optimization", "execution_coordination")
        workflow.add_edge("execution_coordination", "result_processing")
        workflow.add_edge("result_processing", END)

        # 设置入口点
        workflow.set_entry_point("query_analysis")

        self.logger.info("✅ [LayeredArchitectureWorkflow] 工作流构建完成")
        return workflow

    async def query_analysis_node(self, state: LayeredWorkflowState) -> LayeredWorkflowState:
        """查询分析节点"""

        self.logger.info("🔍 [LayeredWorkflow] 开始查询分析")
        start_time = time.time()

        try:
            query = state.query

            # 构建查询分析结果
            # 这里可以集成现有的查询分析逻辑
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

            # 评估系统状态（可选）
            system_state = self._assess_system_state()

            state.query_analysis = query_analysis
            state.system_state = system_state
            state.complexity_score = query_analysis.complexity_score
            state.query_type = query_analysis.query_type

            self.logger.info("✅ [LayeredWorkflow] 查询分析完成")

        except Exception as e:
            error_msg = f"查询分析失败: {e}"
            self.logger.error(f"❌ [LayeredWorkflow] {error_msg}", exc_info=True)
            state.errors.append(error_msg)

        finally:
            execution_time = time.time() - start_time
            state.node_execution_times["query_analysis"] = execution_time

        return state

    async def strategic_decision_node(self, state: LayeredWorkflowState) -> LayeredWorkflowState:
        """战略决策节点"""

        self.logger.info("🎯 [LayeredWorkflow] 开始战略决策")
        start_time = time.time()

        try:
            query_analysis = state.query_analysis
            system_state = state.system_state

            if not query_analysis:
                raise ValueError("缺少查询分析结果")

            # 执行战略决策
            strategic_plan = await self.strategic_agent.decide_strategy(
                query_analysis, system_state
            )

            state.strategic_plan = strategic_plan

            # 记录元数据
            state.metadata["strategic_decision"] = {
                "task_count": len(strategic_plan.tasks),
                "execution_strategy": strategic_plan.execution_strategy.value,
                "estimated_complexity": strategic_plan.resource_requirements.get("estimated_complexity", 0)
            }

            self.logger.info(f"✅ [LayeredWorkflow] 战略决策完成: {len(strategic_plan.tasks)}个任务, 策略={strategic_plan.execution_strategy.value}")

        except Exception as e:
            error_msg = f"战略决策失败: {e}"
            self.logger.error(f"❌ [LayeredWorkflow] {error_msg}", exc_info=True)
            state.errors.append(error_msg)

            # 创建fallback计划
            state.strategic_plan = self._create_fallback_strategic_plan(state)

        finally:
            execution_time = time.time() - start_time
            state.node_execution_times["strategic_decision"] = execution_time

        return state

    async def tactical_optimization_node(self, state: LayeredWorkflowState) -> LayeredWorkflowState:
        """战术优化节点"""

        self.logger.info("🎯 [LayeredWorkflow] 开始战术优化")
        start_time = time.time()

        try:
            strategic_plan = state.strategic_plan
            query_features = self._extract_query_features(state)

            if not strategic_plan:
                raise ValueError("缺少战略决策结果")

            # 执行战术优化
            execution_params = await self.tactical_optimizer.optimize_execution(
                strategic_plan, query_features, state.system_state
            )

            state.execution_params = execution_params

            # 记录元数据
            state.metadata["tactical_optimization"] = {
                "timeout_tasks": len(execution_params.timeouts),
                "parallel_tasks": sum(execution_params.parallelism.values()),
                "total_resources": sum(execution_params.resource_allocation.values())
            }

            self.logger.info("✅ [LayeredWorkflow] 战术优化完成")

        except Exception as e:
            error_msg = f"战术优化失败: {e}"
            self.logger.error(f"❌ [LayeredWorkflow] {error_msg}", exc_info=True)
            state.errors.append(error_msg)

            # 使用默认参数
            state.execution_params = self._create_default_execution_params(state)

        finally:
            execution_time = time.time() - start_time
            state.node_execution_times["tactical_optimization"] = execution_time

        return state

    async def execution_coordination_node(self, state: LayeredWorkflowState) -> LayeredWorkflowState:
        """执行协调节点"""

        self.logger.info("🎯 [LayeredWorkflow] 开始执行协调")
        start_time = time.time()

        try:
            strategic_plan = state.strategic_plan
            execution_params = state.execution_params

            if not strategic_plan or not execution_params:
                raise ValueError("缺少战略决策或战术优化结果")

            # 执行任务协调
            execution_result = await self.execution_coordinator.coordinate_execution(
                strategic_plan, execution_params
            )

            state.execution_result = execution_result

            # 记录元数据
            state.metadata["execution_coordination"] = {
                "successful_tasks": execution_result.execution_metrics.get("successful_tasks", 0),
                "failed_tasks": execution_result.execution_metrics.get("failed_tasks", 0),
                "total_time": execution_result.execution_metrics.get("total_execution_time", 0),
                "quality_score": execution_result.quality_score
            }

            self.logger.info("✅ [LayeredWorkflow] 执行协调完成")
        except Exception as e:
            error_msg = f"执行协调失败: {e}"
            self.logger.error(f"❌ [LayeredWorkflow] {error_msg}", exc_info=True)
            state.errors.append(error_msg)

            # 创建错误结果
            state.execution_result = ExecutionResult(
                final_answer="执行失败，请稍后重试",
                task_results={},
                execution_metrics={"error": str(e)},
                quality_score=0.0,
                errors=[str(e)]
            )

        finally:
            execution_time = time.time() - start_time
            state.node_execution_times["execution_coordination"] = execution_time

        return state

    async def result_processing_node(self, state: LayeredWorkflowState) -> LayeredWorkflowState:
        """结果处理节点"""

        self.logger.info("📋 [LayeredWorkflow] 开始结果处理")
        start_time = time.time()

        try:
            execution_result = state.execution_result

            if execution_result:
                # 设置最终输出
                state.final_answer = execution_result.final_answer
                state.quality_score = execution_result.quality_score

                # 合并错误和警告
                state.errors.extend(execution_result.errors)
                state.warnings.extend(execution_result.warnings)

                # 添加执行摘要到元数据
                state.metadata["execution_summary"] = {
                    "final_answer_length": len(execution_result.final_answer),
                    "task_results_count": len(execution_result.task_results),
                    "overall_quality": execution_result.quality_score,
                    "has_errors": len(execution_result.errors) > 0,
                    "has_warnings": len(execution_result.warnings) > 0
                }

            # 计算总执行时间
            total_time = sum(state.node_execution_times.values())
            state.metadata["total_execution_time"] = total_time

            self.logger.info("✅ [LayeredWorkflow] 结果处理完成")
        except Exception as e:
            error_msg = f"结果处理失败: {e}"
            self.logger.error(f"❌ [LayeredWorkflow] {error_msg}", exc_info=True)
            state.errors.append(error_msg)

        finally:
            execution_time = time.time() - start_time
            state.node_execution_times["result_processing"] = execution_time

        return state

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

    def _assess_system_state(self) -> SystemState:
        """评估系统状态"""
        # 这里可以集成系统监控信息
        return SystemState()

    def _extract_query_features(self, state: LayeredWorkflowState) -> Dict[str, Any]:
        """提取查询特征"""
        if state.query_analysis:
            return {
                "query_length": len(state.query_analysis.query),
                "query_type": state.query_analysis.query_type,
                "complexity_score": state.query_analysis.complexity_score,
                "domain_knowledge": state.query_analysis.domain_knowledge,
                "reasoning_required": state.query_analysis.reasoning_requirements.get("requires_reasoning", False)
            }
        return {}

    def _create_fallback_strategic_plan(self, state: LayeredWorkflowState) -> StrategicPlan:
        """创建fallback战略计划"""
        from src.core.layered_architecture_types import TaskDefinition, ExecutionStrategy

        tasks = [
            TaskDefinition(
                task_id="knowledge_retrieval_fallback",
                task_type=TaskType.KNOWLEDGE_RETRIEVAL,
                description="基础知识检索",
                priority=0.9
            ),
            TaskDefinition(
                task_id="answer_generation_fallback",
                task_type=TaskType.ANSWER_GENERATION,
                description="基础答案生成",
                dependencies=["knowledge_retrieval_fallback"],
                priority=1.0
            )
        ]

        return StrategicPlan(
            tasks=tasks,
            execution_strategy=ExecutionStrategy.SERIAL
        )

    def _create_default_execution_params(self, state: LayeredWorkflowState) -> ExecutionParams:
        """创建默认执行参数"""
        from src.core.layered_architecture_types import ExecutionParams

        # 为fallback任务创建默认参数
        return ExecutionParams(
            timeouts={"knowledge_retrieval_fallback": 30.0, "answer_generation_fallback": 60.0},
            parallelism={"knowledge_retrieval_fallback": False, "answer_generation_fallback": False},
            resource_allocation={"knowledge_retrieval_fallback": 1, "answer_generation_fallback": 1},
            retry_strategy={"knowledge_retrieval_fallback": 2, "answer_generation_fallback": 1}
        )

    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        处理查询的主入口

        Args:
            query: 用户查询

        Returns:
            处理结果字典
        """
        self.logger.info(f"🚀 [LayeredArchitectureWorkflow] 开始处理查询: {query[:100]}...")

        # 初始化状态
        initial_state = LayeredWorkflowState(query=query)

        try:
            # 执行工作流
            final_state = await self.app.ainvoke(initial_state)

            # 转换为结果字典
            result = {
                "final_answer": final_state.final_answer,
                "quality_score": final_state.quality_score,
                "execution_time": final_state.metadata.get("total_execution_time", 0),
                "metadata": final_state.metadata,
                "errors": final_state.errors,
                "warnings": final_state.warnings,
                "node_times": final_state.node_execution_times
            }

            self.logger.info(f"✅ [LayeredArchitectureWorkflow] 查询处理完成, 质量评分: {result['quality_score']:.2f}")
            return result

        except Exception as e:
            error_msg = f"工作流执行失败: {e}"
            self.logger.error(f"❌ [LayeredArchitectureWorkflow] {error_msg}", exc_info=True)

            return {
                "final_answer": "系统处理出现错误，请稍后重试",
                "quality_score": 0.0,
                "execution_time": 0.0,
                "metadata": {},
                "errors": [error_msg],
                "warnings": [],
                "node_times": {}
            }


# 全局工作流实例
_layered_workflow_instance = None

def get_layered_workflow() -> LayeredArchitectureWorkflow:
    """获取分层架构工作流实例"""
    global _layered_workflow_instance
    if _layered_workflow_instance is None:
        _layered_workflow_instance = LayeredArchitectureWorkflow()
    return _layered_workflow_instance
