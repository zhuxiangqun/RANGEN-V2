"""
Execution Coordinator Implementation using LangGraph

Harness Engineering 集成:
- task_contract: 任务契约系统
- harness_entropy_manager: 熵管理系统
- agent_linter: Agent 友好的 Linter
- agent_reviewer: Agent 自动化评审
- agent_observability_client: 可观测性接入
"""
from typing import Dict, Any, TypedDict, Annotated, Literal, Optional, List, Union
import operator
import uuid
import time
from langgraph.graph import StateGraph, END
from src.interfaces.coordinator import ICoordinator
from src.interfaces.agent import ExecutionStatus
from src.core.configurable_router import ConfigurableRouter, RouteTarget
from src.core.context_manager import ContextManager
from src.core.neural.factory import NeuralServiceFactory
from src.core.llm_integration import LLMIntegration

from src.services.logging_service import get_logger
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.tools.tool_registry import ToolRegistry
from src.core.monitoring.monitor_decorator import monitor
from src.core.nodes.quality_evaluator import QualityEvaluatorNode

# Harness Engineering 模块
from src.core.task_contract import (
    create_contract, check_contract_status, get_contract_registry,
    TaskContract, ContractStatus, VerificationItem, VerificationType
)
from src.core.harness_entropy_manager import check_harness_health, needs_harness_cleanup
from src.core.agent_linter import get_agent_linter
from src.core.agent_reviewer import get_review_system, CodeChange
from src.core.agent_observability_client import get_observability_client

# 核心 Agent 模块
try:
    from src.agents.security_guardian import SecurityGuardian
except ImportError:
    SecurityGuardian = None
try:
    from src.core.reflection import ReflectionAgent
except ImportError:
    ReflectionAgent = None
try:
    from src.core.adaptive_optimizer import AdaptiveOptimizer
except ImportError:
    AdaptiveOptimizer = None
try:
    from src.agents.validation_agent import ValidationAgent
except ImportError:
    ValidationAgent = None

# CLI Executor - 直接 CLI 工具调用（替代 MCP）
try:
    from src.core.cli_executor import CLIExecutor, get_cli_executor
except ImportError:
    CLIExecutor = None
    get_cli_executor = None

# Unified Tool Executor - 统一工具执行器（自动优先级选择）
try:
    from src.core.unified_tool_executor import UnifiedToolExecutor, get_unified_tool_executor
except ImportError:
    UnifiedToolExecutor = None
    get_unified_tool_executor = None

# Phase 3: 资源优化模块
try:
    from src.services.cost_control import get_cost_controller
except ImportError:
    get_cost_controller = None
try:
    from src.core.cache_system import get_cache_system
except ImportError:
    get_cache_system = None
try:
    from src.services.context_optimization_service import get_context_optimization_service
except ImportError:
    get_context_optimization_service = None

# Phase 4: 扩展能力模块
try:
    from src.services.skill_service import get_skill_service
except ImportError:
    get_skill_service = None
try:
    from src.core.event_system import EventBus
except ImportError:
    EventBus = None
try:
    from src.agents.citation_agent import CitationAgent
except ImportError:
    CitationAgent = None

logger = get_logger(__name__)

# Extended state schema with harness fields
class AgentState(TypedDict):
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
    # Harness fields
    task_id: str
    lint_issues: List[Dict[str, Any]]
    review_passed: bool
    review_feedback: str
    contract_fulfilled: bool
    harness_metrics: Dict[str, Any]


class ExecutionCoordinator(ICoordinator):
    """
    Orchestrates the execution flow using LangGraph.
    Connects Router -> Agents -> Tools based on the defined workflow.
    
    With integrated Harness Engineering:
    - Observability: Tracks execution at each node
    - Linting: Checks agent output quality
    - Review: Automated review of outputs
    - Contracts: Task completion verification
    """
    
    def __init__(self):
        self.router = ConfigurableRouter()
        self.llm_service = LLMIntegration(config={})
        
        self.context_manager = ContextManager(llm_service=self.llm_service)
        
        self.tool_registry = ToolRegistry()
        
        self.reasoning_agent = ReasoningAgent(tool_registry=self.tool_registry)
        self.quality_evaluator = QualityEvaluatorNode()
        
        # Harness Engineering 组件
        self.linter = get_agent_linter()
        self.reviewer = get_review_system()
        self.observability = get_observability_client()
        self.contract_registry = get_contract_registry()
        
        # Phase 1: 执行增强模块 (with graceful fallback)
        try:
            self.security_guardian = SecurityGuardian()
        except Exception as e:
            logger.warning(f"SecurityGuardian initialization failed: {e}")
            self.security_guardian = None
        
        try:
            self.reflection_agent = ReflectionAgent()
        except Exception as e:
            logger.warning(f"ReflectionAgent initialization failed: {e}")
            self.reflection_agent = None
        
        try:
            self.adaptive_optimizer = AdaptiveOptimizer()
        except Exception as e:
            logger.warning(f"AdaptiveOptimizer initialization failed: {e}")
            self.adaptive_optimizer = None
        
        try:
            self.validation_agent = ValidationAgent()
        except Exception as e:
            logger.warning(f"ValidationAgent initialization failed: {e}")
            self.validation_agent = None
        
        # Phase 3: 资源优化模块
        try:
            self.cost_controller = get_cost_controller() if get_cost_controller else None
        except Exception as e:
            logger.warning(f"CostController initialization failed: {e}")
            self.cost_controller = None
        
        try:
            self.cache_system = get_cache_system() if get_cache_system else None
        except Exception as e:
            logger.warning(f"CacheSystem initialization failed: {e}")
            self.cache_system = None
        
        try:
            self.context_optimizer = get_context_optimization_service() if get_context_optimization_service else None
        except Exception as e:
            logger.warning(f"ContextOptimization initialization failed: {e}")
            self.context_optimizer = None
        
        # Phase 4: 扩展能力模块
        try:
            self.skill_service = get_skill_service() if get_skill_service else None
        except Exception as e:
            logger.warning(f"SkillService initialization failed: {e}")
            self.skill_service = None
        
        try:
            self.event_bus = EventBus() if EventBus else None
        except Exception as e:
            logger.warning(f"EventBus initialization failed: {e}")
            self.event_bus = None
        
        try:
            self.citation_agent = CitationAgent() if CitationAgent else None
        except Exception as e:
            logger.warning(f"CitationAgent initialization failed: {e}")
            self.citation_agent = None
        
        # CLI Executor - 直接 CLI 工具调用（无需 MCP）
        try:
            if CLIExecutor:
                self.cli_executor = get_cli_executor() if get_cli_executor else CLIExecutor()
                logger.info(f"CLI Executor initialized with {len(self.cli_executor.list_tools())} tools discovered")
            else:
                self.cli_executor = None
        except Exception as e:
            logger.warning(f"CLIExecutor initialization failed: {e}")
            self.cli_executor = None
        
        # Unified Tool Executor - 统一工具执行器（自动优先级选择）
        try:
            if UnifiedToolExecutor:
                self.unified_tool_executor = get_unified_tool_executor() if get_unified_tool_executor else UnifiedToolExecutor(
                    skill_registry=None,
                    tool_registry=self.tool_registry,
                    cli_executor=self.cli_executor
                )
                logger.info("UnifiedToolExecutor initialized with priority routing")
            else:
                self.unified_tool_executor = None
        except Exception as e:
            logger.warning(f"UnifiedToolExecutor initialization failed: {e}")
            self.unified_tool_executor = None
        
        # 检查 Harness 健康状态
        health = check_harness_health()
        if health["health_score"] < 70:
            logger.warning(f"Harness health low: {health['health_score']}, issues: {health['issues_found']}")
        
        self.graph = self._build_graph()
        logger.info("ExecutionCoordinator initialized with LangGraph and Harness Engineering")

    def _build_graph(self) -> Any:
        """Construct the execution graph with harness integration"""
        workflow = StateGraph(AgentState)

        # Define Nodes - including all phases
        workflow.add_node("router", self._route_step)
        workflow.add_node("adaptive_optimize", self._adaptive_optimize_step)
        workflow.add_node("direct_executor", self._direct_execution_step)
        workflow.add_node("reasoning_engine", self._reasoning_step)
        workflow.add_node("harness_lint", self._harness_lint_step)
        workflow.add_node("harness_review", self._harness_review_step)
        workflow.add_node("security_check", self._security_check_step)
        workflow.add_node("reflection", self._reflection_step)
        workflow.add_node("validation", self._validation_step)
        workflow.add_node("citation", self._citation_step)
        workflow.add_node("quality_evaluator", self.quality_evaluator.evaluate)
        workflow.add_node("error_handler", self._error_handling_step)

        # Define Edges
        workflow.set_entry_point("router")
        
        # After router, go to adaptive optimization first
        workflow.add_conditional_edges(
            "router",
            self._decide_next_node,
            {
                RouteTarget.DIRECT.value: "adaptive_optimize",
                RouteTarget.COT.value: "adaptive_optimize",
                RouteTarget.REACT.value: "adaptive_optimize",
                "error": "error_handler"
            }
        )
        
        # After optimization, execute
        workflow.add_edge("adaptive_optimize", "direct_executor")
        workflow.add_edge("direct_executor", "harness_lint")
        workflow.add_edge("reasoning_engine", "harness_lint")
        
        # After execution: lint -> review -> security -> reflection -> validation -> citation -> quality
        workflow.add_edge("harness_lint", "harness_review")
        workflow.add_edge("harness_review", "security_check")
        workflow.add_edge("security_check", "reflection")
        workflow.add_edge("reflection", "validation")
        workflow.add_edge("validation", "citation")
        workflow.add_edge("citation", "quality_evaluator")
        
        workflow.add_conditional_edges(
            "quality_evaluator",
            self._decide_after_eval,
            {
                "pass": END,
                "retry": "reasoning_engine"
            }
        )
        
        workflow.add_edge("error_handler", END)

        return workflow.compile()

    # --- Harness Node Implementations ---

    async def _harness_lint_step(self, state: AgentState) -> Dict[str, Any]:
        """Harness Node: Lint the agent output"""
        answer = state.get("final_answer", "")
        
        if not answer:
            return {"lint_issues": [], "harness_metrics": {}}
        
        # 使用新增的 check_output_quality 方法
        quality = self.linter.check_output_quality(answer)
        
        lint_issues = []
        if quality.get("issues_count", 0) > 0:
            lint_issues = [
                {"type": "code", "count": quality["issues_count"], "suggestions": quality.get("suggestions", [])}
            ]
        
        logger.info(f"Harness Lint: {quality.get('issues_count', 0)} issues found")
        
        return {
            "lint_issues": lint_issues,
            "harness_metrics": {"lint_checked": True, "issues_found": quality.get("issues_count", 0)}
        }

    async def _harness_review_step(self, state: AgentState) -> Dict[str, Any]:
        """Harness Node: Review the agent output"""
        answer = state.get("final_answer", "")
        
        if not answer:
            return {"review_passed": True, "review_feedback": "No content to review"}
        
        result = self.reviewer.review_text(answer, content_type="answer")

        review_passed = result.decision.value == "approve"
        review_feedback = result.summary
        
        logger.info(f"Harness Review: {result.decision.value}, score: {result.score}")
        
        return {
            "review_passed": review_passed,
            "review_feedback": review_feedback,
            "harness_metrics": {**state.get("harness_metrics", {}), "review_score": result.score}
        }

    # --- Phase 1: 执行增强节点 ---

    async def _adaptive_optimize_step(self, state: AgentState) -> Dict[str, Any]:
        """Phase 1 Node: Adaptive optimization based on query type"""
        if not self.adaptive_optimizer:
            return {"context": state.get("context", {}), "harness_metrics": {}}
        
        optimized_config = {}
        try:
            model_result = self.adaptive_optimizer.get_optimized_model_selection("general")
            evidence_result = self.adaptive_optimizer.get_optimized_evidence_count("general")
            config_result = self.adaptive_optimizer.get_optimized_config_updates("general")
            
            optimized_config = {
                "preferred_model": model_result[0] if model_result else "fast",
                "complexity_threshold": model_result[1] if model_result else 0.7,
                "evidence_count": evidence_result[0] if evidence_result else 3,
                "config_updates": config_result if isinstance(config_result, dict) else {}
            }
            logger.info(f"Adaptive Optimization: model={optimized_config['preferred_model']}, evidence={optimized_config['evidence_count']}")
        except Exception as e:
            logger.warning(f"Adaptive optimization failed: {e}")
        
        return {
            "context": {**state.get("context", {}), "optimized_config": optimized_config},
            "harness_metrics": {**state.get("harness_metrics", {}), "adaptive_optimized": True}
        }

    async def _security_check_step(self, state: AgentState) -> Dict[str, Any]:
        """Phase 1 Node: Security scanning of output"""
        if not self.security_guardian:
            return {"harness_metrics": {**state.get("harness_metrics", {}), "security_passed": True}}
        
        answer = state.get("final_answer", "")
        
        if not answer:
            return {"harness_metrics": {**state.get("harness_metrics", {}), "security_passed": True}}
        
        threats = await self.security_guardian.detect_threats(answer, state.get("context"))
        privacy_result = await self.security_guardian.protect_privacy(answer, state.get("context"))
        
        security_passed = len(threats) == 0 and privacy_result.get("risk_level") != "high"
        
        logger.info(f"Security Check: {len(threats)} threats, privacy risk: {privacy_result.get('risk_level', 'unknown')}")
        
        final_answer = answer
        if threats or privacy_result.get("risk_level") == "high":
            final_answer = privacy_result.get("protected_content", answer)
        
        return {
            "final_answer": final_answer,
            "harness_metrics": {
                **state.get("harness_metrics", {}),
                "security_passed": security_passed,
                "threats_count": len(threats),
                "privacy_risk": privacy_result.get("risk_level", "unknown")
            }
        }

    async def _reflection_step(self, state: AgentState) -> Dict[str, Any]:
        """Phase 1 Node: Self-criticism and improvement"""
        if not self.reflection_agent:
            return {"harness_metrics": {**state.get("harness_metrics", {}), "reflection_done": True}}
        
        answer = state.get("final_answer", "")
        
        if not answer:
            return {"harness_metrics": {**state.get("harness_metrics", {}), "reflection_done": True}}
        
        result = await self.reflection_agent.reflect(
            task=state.get("query", ""),
            output=answer,
            context=state.get("context", {})
        )
        
        improved_output = result.improved_output if result.improved_output else answer
        
        logger.info(f"Reflection: type={result.reflection_type.value}, confidence={result.confidence:.2f}")
        
        return {
            "final_answer": improved_output,
            "harness_metrics": {
                **state.get("harness_metrics", {}),
                "reflection_done": True,
                "reflection_type": result.reflection_type.value,
                "reflection_confidence": result.confidence
            }
        }

    # --- Phase 2: 质量保障节点 ---

    async def _validation_step(self, state: AgentState) -> Dict[str, Any]:
        """Phase 2 Node: Detailed validation"""
        if not self.validation_agent:
            return {"harness_metrics": {**state.get("harness_metrics", {}), "validation_passed": True}}
        
        answer = state.get("final_answer", "")
        
        if not answer:
            return {"harness_metrics": {**state.get("harness_metrics", {}), "validation_passed": False}}
        
        result = await self.validation_agent.execute(
            inputs={"query": state.get("query", ""), "answer": answer},
            context=state.get("context", {})
        )
        
        validation_passed = result.status == ExecutionStatus.COMPLETED
        
        logger.info(f"Validation: {result.status.value}")
        
        return {
            "harness_metrics": {
                **state.get("harness_metrics", {}),
                "validation_passed": validation_passed
            }
        }

    # --- Phase 3: 资源优化节点 ---

    async def _context_optimize_step(self, state: AgentState) -> Dict[str, Any]:
        """Phase 3 Node: Context optimization"""
        if not self.context_optimizer:
            return {"context": state.get("context", {}), "harness_metrics": {}}
        
        context = state.get("context", {})
        query = state.get("query", "")
        
        try:
            from src.services.context_optimization_service import OptimizationStrategy
            result = self.context_optimizer.optimize_context(
                content=query,
                context_type="query",
                strategies=[OptimizationStrategy.AUTO],
                max_tokens=2000
            )
            logger.info(f"Context Optimization: reduced tokens from {len(query)} to {len(result.optimized_content)}")
            return {
                "context": {**context, "optimized_query": result.optimized_content},
                "harness_metrics": {**state.get("harness_metrics", {}), "context_optimized": True}
            }
        except Exception as e:
            logger.warning(f"Context optimization failed: {e}")
            return {"context": context, "harness_metrics": {}}

    # --- Phase 4: 扩展能力节点 ---

    async def _citation_step(self, state: AgentState) -> Dict[str, Any]:
        """Phase 4 Node: Citation generation"""
        if not self.citation_agent:
            return {"harness_metrics": {**state.get("harness_metrics", {}), "citations_added": False}}
        
        answer = state.get("final_answer", "")
        
        if not answer:
            return {"harness_metrics": {**state.get("harness_metrics", {}), "citations_added": False}}
        
        try:
            context = state.get("context", {})
            evidence = context.get("evidence", [])
            
            if evidence:
                result = await self.citation_agent.execute(
                    inputs={"answer": answer, "evidence": evidence},
                    context=context
                )
                logger.info(f"Citation: executed with status {result.status}")
                return {
                    "harness_metrics": {
                        **state.get("harness_metrics", {}),
                        "citations_added": result.status == ExecutionStatus.COMPLETED
                    }
                }
        except Exception as e:
            logger.warning(f"Citation generation failed: {e}")
        
        return {"harness_metrics": {**state.get("harness_metrics", {}), "citations_added": False}}

    # --- Node Implementations ---

    @monitor.trace_node("router")
    async def _route_step(self, state: AgentState) -> Dict[str, Any]:
        """Node: Determine the route"""
        # Track observability - node start
        node_start = time.time()
        
        try:
            route = await self.router.route(state["query"], state.get("context"))
            
            # Track observability - node end
            duration = time.time() - node_start
            self._track_node("router", duration, success=True)
            
            return {"route": route.value}
        except Exception as e:
            duration = time.time() - node_start
            self._track_node("router", duration, success=False, error=str(e))
            logger.error(f"Routing failed: {e}")
            return {"route": "error", "error": str(e)}

    def _track_node(self, node_name: str, duration: float, success: bool, error: str = None):
        """Track node execution for observability"""
        logger.debug(f"Node {node_name} completed in {duration:.3f}s, success={success}")

    def _decide_next_node(self, state: AgentState) -> str:
        """Edge: Conditional logic based on route"""
        return state.get("route", "error")

    def _decide_after_eval(self, state: AgentState) -> str:
        """Edge: Decide whether to retry based on quality"""
        retry_count = state.get("retry_count", 0)
        if retry_count >= 1:
            return "pass"
            
        passed = state.get("quality_passed", True)
        if passed:
            return "pass"
        
        state["retry_count"] = retry_count + 1
        return "retry"

    @monitor.trace_node("direct_executor")
    async def _direct_execution_step(self, state: AgentState) -> Dict[str, Any]:
        """Node: Direct execution"""
        node_start = time.time()
        logger.info("Executing Direct Workflow")
        
        try:
            result = await self.reasoning_agent.execute({
                "query": state["query"],
            }, context=state.get("context"))
            
            duration = time.time() - node_start
            self._track_node("direct_executor", duration, success=True)
            
            if result.status == ExecutionStatus.COMPLETED:
                 return {
                    "final_answer": result.output.get("answer", str(result.output)), 
                    "steps": ["direct_execution"]
                }
            else:
                 return {"error": result.error or "Direct execution failed"}
        except Exception as e:
            duration = time.time() - node_start
            self._track_node("direct_executor", duration, success=False, error=str(e))
            return {"error": str(e)}

    @monitor.trace_node("reasoning_engine")
    async def _reasoning_step(self, state: AgentState) -> Dict[str, Any]:
        """Node: Complex reasoning via ReasoningAgent"""
        node_start = time.time()
        logger.info(f"Executing Reasoning Workflow ({state['route']})")
        
        try:
            result = await self.reasoning_agent.execute(
                inputs={"query": state["query"]},
                context=state.get("context")
            )
            
            duration = time.time() - node_start
            self._track_node("reasoning_engine", duration, success=True)
            
            if result.status == ExecutionStatus.COMPLETED:
                output = result.output
                return {
                    "final_answer": output.get("answer", ""),
                    "steps": [f"steps: {output.get('steps', 0)}", output.get("trace", "")]
                }
            else:
                return {
                    "error": result.error or "Reasoning execution failed",
                    "final_answer": "Failed to generate answer."
                }
                
        except Exception as e:
            duration = time.time() - node_start
            self._track_node("reasoning_engine", duration, success=False, error=str(e))
            logger.error(f"Reasoning step failed: {e}")
            return {"error": str(e)}

    @monitor.trace_node("error_handler")
    async def _error_handling_step(self, state: AgentState) -> Dict[str, Any]:
        """Node: Global error handler"""
        return {"final_answer": "I encountered an error while processing your request.", "error": state.get("error", "Unknown error")}

    # --- Public Interface ---

    async def run_task(self, task: str, context: Optional[Dict[str, Any]] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Entry point for running a task"""
        
        # ===== Intelligent Tool Selection =====
        # 在 workflow 执行之前，先尝试智能工具选择
        logger.info(f"Intelligent tool selection for task: {task}")
        
        if self.unified_tool_executor:
            # 尝试智能工具选择
            try:
                tool_result = await self.unified_tool_executor.execute_with_intelligent_selection(task)
                if tool_result and tool_result.get("success"):
                    logger.info(f"Intelligent tool execution successful: {tool_result.get('tool_name')}")
                    return {
                        "answer": tool_result.get("answer", "操作完成"),
                        "steps": ["intelligent_tool_selection"],
                        "status": "completed",
                        "error": None,
                        "tool_executed": tool_result.get("tool_name"),
                        "execution_time": tool_result.get("execution_time", 0)
                    }
            except Exception as e:
                logger.warning(f"Intelligent tool selection failed: {e}, falling back to workflow")
        # ===== End Intelligent Tool Selection =====
        
        # 生成任务ID用于追踪
        task_id = str(uuid.uuid4())[:8]
        
        # 创建任务契约
        contract = self._create_task_contract(task_id, task)
        
        # Resolve Session Context
        session_ctx = {}
        session = None
        if session_id:
            try:
                session = await self.context_manager.get_session(session_id)
                await session.add_message("user", task)
                session_ctx = session.to_dict()
                if context:
                    session_ctx.update(context)
            except Exception as e:
                logger.warning(f"Failed to retrieve/update session {session_id}: {e}")
                session_ctx = context or {}
        else:
            session_ctx = context or {}

        initial_state = {
            "query": task,
            "context": session_ctx,
            "steps": [],
            "route": "",
            "final_answer": "",
            "error": "",
            "quality_score": 0.0,
            "quality_passed": True,
            "quality_feedback": "",
            "retry_count": 0,
            "task_id": task_id,
            "lint_issues": [],
            "review_passed": True,
            "review_feedback": "",
            "contract_fulfilled": False,
            "harness_metrics": {"task_id": task_id}
        }
        
        try:
            # Execute the graph
            result = await self.graph.ainvoke(initial_state)
            
            # 验证契约完成状态
            contract_fulfilled = self._verify_contract(task_id, result)
            result["contract_fulfilled"] = contract_fulfilled
            
            # 如果契约未完成，标记
            if not contract_fulfilled:
                logger.warning(f"Task {task_id} contract not fully fulfilled")
                result["contract_status"] = "incomplete"
            
            # 更新契约状态
            self._update_contract_status(task_id, contract_fulfilled)
            
            # 保存上下文
            if session:
                if result.get("final_answer"):
                     await session.add_message("assistant", result["final_answer"])
                await session.save()
            
            # 添加最终指标
            result["harness_metrics"] = {
                **result.get("harness_metrics", {}),
                "task_id": task_id,
                "contract_verified": contract_fulfilled,
                "lint_issues_count": len(result.get("lint_issues", [])),
                "review_passed": result.get("review_passed", True)
            }
            
            return result
        except Exception as e:
            logger.error(f"Graph execution failed: {e}")
            return {"error": str(e), "final_answer": "System Error", "task_id": task_id}

    def _create_task_contract(self, task_id: str, task: str) -> TaskContract:
        """创建任务契约"""
        verifications = [
            VerificationItem(
                id=f"{task_id}_has_answer",
                type=VerificationType.ASSERTION,
                description="生成有效回答",
                criteria="final_answer 不为空且不包含错误信息",
                weight=1.0,
                required=True
            ),
            VerificationItem(
                id=f"{task_id}_no_errors",
                type=VerificationType.ASSERTION,
                description="无执行错误",
                criteria="error 字段为空或不存在",
                weight=1.0,
                required=True
            )
        ]
        
        contract = self.contract_registry.create(
            task_id=task_id,
            description=task[:100],  # 截断描述
            verifications=verifications,
            context={"original_task": task}
        )
        
        logger.info(f"Created contract for task {task_id}")
        return contract

    def _verify_contract(self, task_id: str, result: Dict[str, Any]) -> bool:
        """验证任务契约"""
        contract = self.contract_registry.get(task_id)
        if not contract:
            return True  # 没有契约，默认通过
        
        # 验证回答存在
        has_answer = bool(result.get("final_answer")) and "error" not in result.get("final_answer", "").lower()
        no_errors = "error" not in result or not result.get("error")
        
        # 更新验证项
        self.contract_registry.update_verification(
            task_id, 
            f"{task_id}_has_answer", 
            has_answer,
            evidence=result.get("final_answer", "")[:200]
        )
        self.contract_registry.update_verification(
            task_id, 
            f"{task_id}_no_errors", 
            no_errors,
            evidence=str(result.get("error", ""))
        )
        
        # 检查契约是否完成
        return contract.is_completed()

    def _update_contract_status(self, task_id: str, fulfilled: bool):
        """更新契约状态"""
        contract = self.contract_registry.get(task_id)
        if contract:
            from src.core.task_contract import ContractStatus
            contract.status = ContractStatus.COMPLETED if fulfilled else ContractStatus.FAILED

    async def run_workflow(self, workflow_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific workflow (bypass router)"""
        pass
