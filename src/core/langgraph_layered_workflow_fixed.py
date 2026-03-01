"""
修复版分层架构LangGraph工作流

解决LangGraph导入权限问题，同时保持API兼容性
使用条件导入和降级策略确保系统稳定性
"""

import logging
import asyncio
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from src.core.layered_architecture_types import (
    StrategicPlan, ExecutionParams, ExecutionResult, QueryAnalysis,
    SystemState, TaskType
)
from src.agents.strategic_chief_agent_wrapper import StrategicChiefAgentWrapper as StrategicChiefAgent
from src.agents.tactical_optimizer import TacticalOptimizer
from src.agents.execution_coordinator import ExecutionCoordinator

logger = logging.getLogger(__name__)

# 尝试导入LangGraph，如果失败则使用降级模式
LANGGRAPH_AVAILABLE = False
try:
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode
    LANGGRAPH_AVAILABLE = True
    logger.info("✅ LangGraph 导入成功")
except ImportError as e:
    logger.warning(f"⚠️ LangGraph 导入失败: {e}，使用降级模式")
    LANGGRAPH_AVAILABLE = False
except Exception as e:
    logger.error(f"❌ LangGraph 导入异常: {e}，使用降级模式")
    LANGGRAPH_AVAILABLE = False


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

    # 兼容性字段
    route_path: str = ""
    complexity_score: float = 1.0
    query_type: str = "general"


class BaseWorkflowEngine:
    """基础工作流引擎接口"""

    async def process_query(self, query: str) -> Dict[str, Any]:
        """处理查询"""
        raise NotImplementedError


class LangGraphWorkflowEngine(BaseWorkflowEngine):
    """LangGraph工作流引擎"""

    def __init__(self):
        if not LANGGRAPH_AVAILABLE:
            raise RuntimeError("LangGraph不可用")

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 初始化组件
        self.strategic_agent = StrategicChiefAgentWrapper(enable_gradual_replacement=True)
        self.tactical_optimizer = TacticalOptimizer()
        self.execution_coordinator = ExecutionCoordinator()

        # 构建工作流
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()

    def _build_workflow(self):
        """构建LangGraph工作流"""
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

        return workflow

    async def query_analysis_node(self, state: LayeredWorkflowState) -> LayeredWorkflowState:
        """查询分析节点"""
        start_time = time.time()
        try:
            query = state.query
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
            system_state = SystemState()
            state.query_analysis = query_analysis
            state.system_state = system_state
            state.complexity_score = query_analysis.complexity_score
            state.query_type = query_analysis.query_type
        except Exception as e:
            error_msg = f"查询分析失败: {e}"
            self.logger.error(f"❌ {error_msg}", exc_info=True)
            state.errors.append(error_msg)
        finally:
            state.node_execution_times["query_analysis"] = time.time() - start_time
        return state

    async def strategic_decision_node(self, state: LayeredWorkflowState) -> LayeredWorkflowState:
        """战略决策节点"""
        start_time = time.time()
        try:
            query_analysis = state.query_analysis
            system_state = state.system_state
            if not query_analysis:
                raise ValueError("缺少查询分析结果")
            strategic_plan = await self.strategic_agent.decide_strategy(query_analysis, system_state)
            state.strategic_plan = strategic_plan
            state.metadata["strategic_decision"] = {
                "task_count": len(strategic_plan.tasks),
                "execution_strategy": strategic_plan.execution_strategy.value,
                "estimated_complexity": strategic_plan.resource_requirements.get("estimated_complexity", 0)
            }
        except Exception as e:
            error_msg = f"战略决策失败: {e}"
            self.logger.error(f"❌ {error_msg}", exc_info=True)
            state.errors.append(error_msg)
            state.strategic_plan = self._create_fallback_strategic_plan(state)
        finally:
            state.node_execution_times["strategic_decision"] = time.time() - start_time
        return state

    async def tactical_optimization_node(self, state: LayeredWorkflowState) -> LayeredWorkflowState:
        """战术优化节点"""
        start_time = time.time()
        try:
            strategic_plan = state.strategic_plan
            if not strategic_plan:
                raise ValueError("缺少战略决策结果")
            execution_params = await self.tactical_optimizer.optimize_execution(strategic_plan, {}, state.system_state)
            state.execution_params = execution_params
            state.metadata["tactical_optimization"] = {
                "timeout_tasks": len(execution_params.timeouts),
                "parallel_tasks": sum(execution_params.parallelism.values()),
                "total_resources": sum(execution_params.resource_allocation.values())
            }
        except Exception as e:
            error_msg = f"战术优化失败: {e}"
            self.logger.error(f"❌ {error_msg}", exc_info=True)
            state.errors.append(error_msg)
            state.execution_params = self._create_default_execution_params(state)
        finally:
            state.node_execution_times["tactical_optimization"] = time.time() - start_time
        return state

    async def execution_coordination_node(self, state: LayeredWorkflowState) -> LayeredWorkflowState:
        """执行协调节点"""
        start_time = time.time()
        try:
            strategic_plan = state.strategic_plan
            execution_params = state.execution_params
            if not strategic_plan or not execution_params:
                raise ValueError("缺少战略决策或战术优化结果")
            execution_result = await self.execution_coordinator.coordinate_execution(strategic_plan, execution_params)
            state.execution_result = execution_result
            state.metadata["execution_coordination"] = {
                "successful_tasks": execution_result.execution_metrics.get("successful_tasks", 0),
                "failed_tasks": execution_result.execution_metrics.get("failed_tasks", 0),
                "total_time": execution_result.execution_metrics.get("total_execution_time", 0),
                "quality_score": execution_result.quality_score
            }
        except Exception as e:
            error_msg = f"执行协调失败: {e}"
            self.logger.error(f"❌ {error_msg}", exc_info=True)
            state.errors.append(error_msg)
            state.execution_result = ExecutionResult(
                final_answer="系统处理出现错误，请稍后重试",
                task_results={},
                execution_metrics={"error": str(e)},
                quality_score=0.0,
                errors=[str(e)]
            )
        finally:
            state.node_execution_times["execution_coordination"] = time.time() - start_time
        return state

    async def result_processing_node(self, state: LayeredWorkflowState) -> LayeredWorkflowState:
        """结果处理节点"""
        start_time = time.time()
        try:
            execution_result = state.execution_result
            if execution_result:
                state.final_answer = execution_result.final_answer
                state.quality_score = execution_result.quality_score
                state.errors.extend(execution_result.errors)
                state.warnings.extend(execution_result.warnings)
                state.metadata["execution_summary"] = {
                    "final_answer_length": len(execution_result.final_answer),
                    "task_results_count": len(execution_result.task_results),
                    "overall_quality": execution_result.quality_score,
                    "has_errors": len(execution_result.errors) > 0,
                    "has_warnings": len(execution_result.warnings) > 0,
                    "total_execution_time": sum(state.node_execution_times.values())
                }
        except Exception as e:
            error_msg = f"结果处理失败: {e}"
            self.logger.error(f"❌ {error_msg}", exc_info=True)
            state.errors.append(error_msg)
        finally:
            state.node_execution_times["result_processing"] = time.time() - start_time
        return state

    async def process_query(self, query: str) -> Dict[str, Any]:
        """处理查询的主入口"""
        self.logger.info(f"🚀 [LangGraphWorkflow] 开始处理查询: {query[:100]}...")

        initial_state = LayeredWorkflowState(query=query)

        try:
            final_state = await self.app.ainvoke(initial_state)
            result = {
                "final_answer": final_state.final_answer,
                "quality_score": final_state.quality_score,
                "execution_time": final_state.metadata.get("total_execution_time", 0),
                "metadata": final_state.metadata,
                "errors": final_state.errors,
                "warnings": final_state.warnings,
                "node_times": final_state.node_execution_times
            }
            self.logger.info(f"✅ [LangGraphWorkflow] 查询处理完成")
            return result
        except Exception as e:
            error_msg = f"工作流执行失败: {e}"
            self.logger.error(f"❌ [LangGraphWorkflow] {error_msg}", exc_info=True)
            return {
                "final_answer": "系统处理出现错误，请稍后重试",
                "quality_score": 0.0,
                "execution_time": 0.0,
                "metadata": {},
                "errors": [error_msg],
                "warnings": [],
                "node_times": {}
            }

    # 辅助方法
    def _analyze_query_type(self, query: str) -> str:
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
        length_score = min(len(query) / 500, 1.0) * 2
        complex_keywords = ['分析', '比较', '评估', '优化', '设计', '架构', '系统', '算法']
        keyword_score = sum(1 for kw in complex_keywords if kw in query.lower()) * 0.5
        logic_words = ['如果', '那么', '因为', '所以', '但是', '然而', 'if', 'then', 'because', 'so', 'but', 'however']
        logic_score = sum(1 for word in logic_words if word in query.lower()) * 0.3
        total_score = length_score + keyword_score + logic_score
        return min(total_score, 5.0)

    def _estimate_required_tasks(self, query: str) -> List[str]:
        tasks = ["knowledge_retrieval"]
        query_lower = query.lower()
        if any(word in query_lower for word in ['为什么', '如何', '分析', 'why', 'how', 'analyze']):
            tasks.append("reasoning")
        if len(query) > 100:
            tasks.append("analysis")
        tasks.extend(["answer_generation", "citation"])
        return tasks

    def _extract_domain_knowledge(self, query: str) -> List[str]:
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
        reasoning_indicators = ['为什么', '如何', '怎么做', '原因', '解释', 'why', 'how', 'reason', 'explain']
        requires_reasoning = any(indicator in query.lower() for indicator in reasoning_indicators)
        return {
            "requires_reasoning": requires_reasoning,
            "reasoning_depth": "deep" if len(query) > 200 else "standard",
            "logic_complexity": "high" if requires_reasoning else "low"
        }

    def _analyze_evidence_requirements(self, query: str) -> Dict[str, Any]:
        return {
            "evidence_strength": "strong" if len(query) > 150 else "standard",
            "source_diversity": True,
            "verification_required": True
        }

    def _define_quality_requirements(self, query: str) -> Dict[str, Any]:
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

    def _create_fallback_strategic_plan(self, state: LayeredWorkflowState):
        from src.core.layered_architecture_types import TaskDefinition, ExecutionStrategy
        tasks = [
            TaskDefinition(task_id="knowledge_retrieval_fallback", task_type=TaskType.KNOWLEDGE_RETRIEVAL,
                         description="基础知识检索", priority=0.9),
            TaskDefinition(task_id="answer_generation_fallback", task_type=TaskType.ANSWER_GENERATION,
                         description="基础答案生成", dependencies=["knowledge_retrieval_fallback"], priority=1.0)
        ]
        return StrategicPlan(tasks=tasks, execution_strategy=ExecutionStrategy.SERIAL)

    def _create_default_execution_params(self, state: LayeredWorkflowState):
        return ExecutionParams(
            timeouts={"knowledge_retrieval_fallback": 30.0, "answer_generation_fallback": 60.0},
            parallelism={"knowledge_retrieval_fallback": False, "answer_generation_fallback": False},
            resource_allocation={"knowledge_retrieval_fallback": 1, "answer_generation_fallback": 1},
            retry_strategy={"knowledge_retrieval_fallback": 2, "answer_generation_fallback": 1}
        )


class SimplifiedWorkflowEngine(BaseWorkflowEngine):
    """简化版工作流引擎（降级模式）"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 导入简化版工作流
        try:
            from src.core.simplified_layered_workflow import get_simplified_workflow
            self.workflow = get_simplified_workflow()
            self.logger.info("✅ 使用简化版分层工作流")
        except ImportError as e:
            self.logger.error(f"❌ 无法导入简化版工作流: {e}")
            raise

    async def process_query(self, query: str) -> Dict[str, Any]:
        """处理查询"""
        return await self.workflow.process_query(query)


class LayeredArchitectureWorkflowManager:
    """
    分层架构工作流管理器

    自动选择最适合的工作流引擎
    支持LangGraph和简化版降级
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._current_engine = None
        self._engine_type = "unknown"

    async def initialize(self):
        """初始化工作流引擎"""
        try:
            # 优先尝试LangGraph
            if LANGGRAPH_AVAILABLE:
                self._current_engine = LangGraphWorkflowEngine()
                self._engine_type = "langgraph"
                self.logger.info("✅ 使用LangGraph工作流引擎")
            else:
                # 降级到简化版
                self._current_engine = SimplifiedWorkflowEngine()
                self._engine_type = "simplified"
                self.logger.info("⚠️ 降级使用简化版工作流引擎")

        except Exception as e:
            self.logger.error(f"❌ 工作流引擎初始化失败: {e}")
            # 创建最基本的降级引擎
            self._current_engine = BasicWorkflowEngine()
            self._engine_type = "basic"
            self.logger.warning("⚠️ 使用基础工作流引擎")

    async def process_query(self, query: str) -> Dict[str, Any]:
        """处理查询"""
        if not self._current_engine:
            await self.initialize()

        if not self._current_engine:
            return {
                "final_answer": "系统初始化失败，请稍后重试",
                "quality_score": 0.0,
                "execution_time": 0.0,
                "metadata": {"engine_type": "failed"},
                "errors": ["工作流引擎初始化失败"],
                "warnings": [],
                "node_times": {}
            }

        # 添加引擎类型信息
        result = await self._current_engine.process_query(query)
        result["metadata"]["engine_type"] = self._engine_type

        return result

    def get_engine_info(self) -> Dict[str, Any]:
        """获取引擎信息"""
        return {
            "engine_type": self._engine_type,
            "langgraph_available": LANGGRAPH_AVAILABLE,
            "engine_initialized": self._current_engine is not None
        }


class BasicWorkflowEngine(BaseWorkflowEngine):
    """基础工作流引擎（最后的降级方案）"""

    async def process_query(self, query: str) -> Dict[str, Any]:
        """基础查询处理"""
        logger.warning("⚠️ 使用基础工作流引擎")

        return {
            "final_answer": f"收到查询: {query[:100]}... (基础引擎响应)",
            "quality_score": 0.5,
            "execution_time": 0.1,
            "metadata": {"engine_type": "basic", "note": "降级模式"},
            "errors": [],
            "warnings": ["使用基础工作流引擎"],
            "node_times": {"basic_processing": 0.1}
        }


# 全局工作流管理器实例
_workflow_manager_instance = None

def get_layered_workflow_manager() -> LayeredArchitectureWorkflowManager:
    """获取分层架构工作流管理器实例"""
    global _workflow_manager_instance
    if _workflow_manager_instance is None:
        _workflow_manager_instance = LayeredArchitectureWorkflowManager()
    return _workflow_manager_instance

async def get_layered_workflow() -> LayeredArchitectureWorkflowManager:
    """获取分层架构工作流（向后兼容）"""
    manager = get_layered_workflow_manager()
    await manager.initialize()
    return manager
