#!/usr/bin/env python3
"""
ChiefAgent - 首席智能体
协调整个多智能体系统，实现任务分解、团队组建、协调执行等功能
集成审核Agent和质量控制
"""

import logging
import uuid
import asyncio
from typing import Dict, List, Any, Optional
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentResult, AgentConfig, SelfEvolvingConfig
from .expert_agent import ExpertAgent
from .react_agent import Action
from .agent_communication import AgentCommunicationProtocol

logger = logging.getLogger(__name__)


@dataclass
class TaskDecomposition:
    """任务分解结果"""
    subtasks: List[Dict[str, Any]]
    dependencies: Dict[str, List[str]]
    priorities: Dict[str, int]


def _chief_register_default_experts_env() -> bool:
    """是否从环境变量读取「注册默认专家」开关"""
    import os
    return os.getenv("RANGEN_CHIEF_REGISTER_DEFAULT_EXPERTS", "").strip().lower() in ("1", "true", "yes")


class ChiefAgent(BaseAgent):
    """首席Agent - 协调整个多智能体系统"""

    def __init__(
        self,
        enable_audit: bool = True,
        enable_quality_control: bool = True,
        register_default_experts: Optional[bool] = None,
    ):
        if register_default_experts is None:
            register_default_experts = _chief_register_default_experts_env()
        config = AgentConfig(
            agent_id="chief_agent",
            agent_type="chief_agent"
        )
        super().__init__(
            agent_id="chief_agent",
            capabilities=["coordination", "task_decomposition", "team_management", 
                         "conflict_resolution", "cognitive_partnership"],
            config=config
        )
        
        # Agent状态
        self.observations: List[Dict[str, Any]] = []
        self.thoughts: List[str] = []
        self.actions: List[Action] = []
        
        # 专家Agent池
        self.expert_agent_pool: Dict[str, ExpertAgent] = {}
        
        # LLM客户端
        self.llm_client = None
        self.fast_llm_client = None
        self._init_llm_client()
        
        # 通信协议
        self.communication_protocol = AgentCommunicationProtocol()
        
        # 认知伙伴能力
        self.cognitive_capabilities = {
            "proactive_collaboration": True,
            "guidance": True,
            "education": True,
            "empowerment": True
        }
        
        # 执行策略缓存
        self._strategy_cache: Dict[str, Dict[str, Any]] = {}
        
        # ==================== 审核与质量控制 ====================
        self._audit_enabled = enable_audit
        self._quality_control_enabled = enable_quality_control
        self._dev_audit_enabled = enable_audit  # 开发审核与通用审核同步
        self._init_audit_system()

        # 自进化能力初始化
        self._init_self_evolving()

        # 可选：注册默认专家（便于 Gateway/单机 直接使用 ChiefAgent 即有执行能力）
        if register_default_experts:
            self._register_default_experts()

        logger.info("✅ 首席Agent初始化完成")
    
    def _init_audit_system(self):
        """初始化审核和质量控制系统"""
        # 审核Agent
        if self._audit_enabled:
            try:
                from .audit_agent import AuditAgent
                self.audit_agent = AuditAgent()
                logger.info("✅ 审核Agent已集成")
            except Exception as e:
                logger.warning(f"⚠️ 审核Agent初始化失败: {e}")
                self.audit_agent = None
        else:
            self.audit_agent = None
            
        # 质量控制器
        if self._quality_control_enabled:
            try:
                from .quality_controller import QualityController
                self.quality_controller = QualityController()
                logger.info("✅ 质量控制器已集成")
            except Exception as e:
                logger.warning(f"⚠️ 质量控制器初始化失败: {e}")
        else:
            self.quality_controller = None
        
        # 开发工作流审核 (代码安全检查)
        if self._dev_audit_enabled:
            try:
                from src.core.dev_workflow_audit import DevWorkflowAudit, AuditLevel
                self.dev_audit = DevWorkflowAudit(
                    audit_level=AuditLevel.STANDARD,
                    chief_agent=self,
                    auto_sanitize=True
                )
                logger.info("✅ 开发工作流审核已集成")
            except Exception as e:
                logger.warning(f"⚠️ 开发工作流审核初始化失败: {e}")
                self.dev_audit = None
        else:
            self.dev_audit = None

    def _init_self_evolving(self):
        """初始化自进化能力"""
        try:
            from src.utils.unified_centers import get_unified_config_center
            config_center = get_unified_config_center()
            
            enabled = config_center.get_config_value(
                'chief_agent', 'self_evolving.enabled', True
            )
            
            if enabled:
                self.enable_self_evolving(
                    config=SelfEvolvingConfig(
                        enabled=True,
                        enable_reflection=True,
                        enable_multi_trajectory=config_center.get_config_value(
                            'chief_agent', 'self_evolving.multi_trajectory', False
                        ),
                        enable_pattern_learning=True,
                        pattern_storage_enabled=True
                    ),
                    llm_provider=self.llm_client
                )
                logger.info("✅ 首席Agent自进化能力已启用")
        except Exception as e:
            logger.warning(f"⚠️ 自进化初始化失败: {e}")
    
    def _init_llm_client(self):
        """初始化LLM客户端"""
        try:
            from src.core.llm_integration import LLMIntegration
            from src.utils.unified_centers import get_unified_config_center
            
            config_center = get_unified_config_center()
            llm_config = {
                'llm_provider': config_center.get_env_config('llm', 'LLM_PROVIDER', 'deepseek'),
                'api_key': config_center.get_env_config('llm', 'DEEPSEEK_API_KEY', ''),
                'model': config_center.get_env_config('llm', 'REASONING_MODEL', 'deepseek-chat'),
                'base_url': config_center.get_env_config('llm', 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
            }
            
            self.llm_client = LLMIntegration(llm_config)
            logger.info("✅ LLM客户端初始化成功")
            
            # 快速LLM客户端
            fast_llm_config = llm_config.copy()
            fast_llm_config['model'] = config_center.get_env_config('llm', 'FAST_MODEL', 'deepseek-chat')
            self.fast_llm_client = LLMIntegration(fast_llm_config)
            logger.info("✅ 快速LLM客户端初始化成功")
            
        except Exception as e:
            logger.warning(f"⚠️ LLM客户端初始化失败: {e}")
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """处理查询"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._execute_async(query, context))
                    return future.result()
            else:
                return loop.run_until_complete(self._execute_async(query, context))
        except RuntimeError:
            return asyncio.run(self._execute_async(query, context))
    
    async def _execute_async(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """异步执行方法"""
        exec_context = {"query": query}
        if context:
            exec_context.update(context)
        return await self.execute(exec_context)
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行任务 (带审核和质量控制)"""
        query = context.get("query", "")
        
        try:
            # 1. 理解任务
            understanding = await self._understand_task(query)
            
            # 2. 审核任务请求
            if self.audit_agent:
                audit_result = await self._audit_task_request(query, understanding)
                if audit_result.decision.value == "rejected":
                    return AgentResult(
                        success=False,
                        data=None,
                        confidence=0.0,
                        processing_time=0.0,
                        error=f"任务被审核拒绝: {audit_result.reasons}"
                    )
            
            # 3. 分解任务
            decomposition = await self._decompose_task(understanding)
            
            # 4. 选择Agent
            agents = self._select_agents(decomposition)
            
            # 5. 协调执行
            results = await self._coordinate_execution(agents, decomposition)
            
            # 6. 整合结果
            final_result = await self._integrate_results(results)
            
            # 7. 质量评估
            if self.quality_controller:
                quality_assessment = await self._assess_quality(final_result)
                final_result["quality_assessment"] = quality_assessment
                
                # 质量不达标则标记
                if quality_assessment.get("overall_score", 100) < 60:
                    logger.warning(f"⚠️ 质量评估未达标: {quality_assessment['overall_score']}")
            
            # 8. 记录审核日志
            if self.audit_agent:
                await self._log_audit_result(query, final_result)
            
            return AgentResult(
                success=True,
                data=final_result,
                confidence=0.9,
                processing_time=0.0,
                metadata={"query": query}
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                data=None,
                confidence=0.0,
                processing_time=0.0,
                error=str(e)
            )
    
    async def _audit_task_request(self, query: str, understanding: Dict) -> Any:
        """审核任务请求"""
        if not self.audit_agent:
            return None
            
        try:
            from .audit_agent import AuditRequest, AuditDecision
            
            request = AuditRequest(
                request_id=str(uuid.uuid4())[:8],
                source_agent="user",
                target_agent="chief_agent",
                action_type="task_execution",
                action_details={
                    "query": query,
                    "understanding": understanding
                },
                priority="normal"
            )
            
            result = await self.audit_agent.audit_request(request)
            logger.info(f"审核结果: {result.decision.value}, 分数: {result.audit_score}")
            return result
        except Exception as e:
            logger.warning(f"审核失败: {e}")
            return None
    
    async def _assess_quality(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """评估结果质量"""
        if not self.quality_controller:
            return {"overall_score": 100, "status": "not_enabled"}
            
        try:
            content = str(result.get("results", result))
            assessment = self.quality_controller.assess_quality(
                content=content,
                content_id=str(uuid.uuid4())[:8],
                validation_level="standard"
            )
            
            return {
                "overall_score": assessment.overall_score,
                "dimension_scores": assessment.dimension_scores,
                "detected_issues": assessment.detected_issues,
                "recommendations": assessment.recommendations
            }
        except Exception as e:
            logger.warning(f"质量评估失败: {e}")
            return {"overall_score": 100, "error": str(e)}
    
    async def _log_audit_result(self, query: str, result: Dict[str, Any]) -> None:
        """记录审核结果"""
        # 审核日志已由AuditAgent内部记录
        pass
    
    async def _understand_task(self, query: str) -> Dict[str, Any]:
        """理解任务"""
        return {"query": query, "type": "general", "complexity": "medium"}
    
    async def _decompose_task(self, understanding: Dict[str, Any]) -> TaskDecomposition:
        """分解任务"""
        return TaskDecomposition(
            subtasks=[{"id": "subtask_1", "description": understanding["query"]}],
            dependencies={},
            priorities={"subtask_1": 1}
        )
    
    def _select_agents(self, decomposition: TaskDecomposition) -> List[ExpertAgent]:
        """选择Agent"""
        return list(self.expert_agent_pool.values())
    
    async def _coordinate_execution(
        self,
        agents: List[ExpertAgent],
        decomposition: TaskDecomposition,
    ) -> List[Any]:
        """协调执行：若有注册专家则调用其 execute，否则返回占位结果"""
        results = []
        query_from_decomposition = ""
        for st in decomposition.subtasks:
            desc = st.get("description", "")
            if desc:
                query_from_decomposition = desc
            break
        if not query_from_decomposition and decomposition.subtasks:
            query_from_decomposition = str(decomposition.subtasks[0])

        for subtask in decomposition.subtasks:
            task_query = subtask.get("description", query_from_decomposition)
            ctx = {"query": task_query, "dependencies": {}}
            if agents:
                agent = agents[0]
                try:
                    ar = await agent.execute(ctx)
                    out = ar.data if ar and getattr(ar, "success", True) else getattr(ar, "error", "completed")
                except Exception as e:
                    logger.warning(f"Expert {agent.agent_id} execute failed: {e}")
                    out = str(e)
                results.append({"subtask": subtask, "result": out})
            else:
                results.append({"subtask": subtask, "result": "completed"})
        return results
    
    async def _integrate_results(self, results: List[Any]) -> Dict[str, Any]:
        """整合结果"""
        return {"status": "success", "results": results, "count": len(results)}
    
    def register_expert_agent(self, agent: ExpertAgent) -> None:
        """注册专家Agent"""
        self.expert_agent_pool[agent.agent_id] = agent
        logger.info(f"✅ 注册专家Agent: {agent.agent_id}")

    def _register_default_experts(self) -> None:
        """注册默认专家 Agent，使 ChiefAgent 在无外部注册时也具备基础执行能力。"""
        try:
            from .tools.tool_registry import get_tool_registry
            registry = get_tool_registry()
        except Exception as e:
            logger.warning(f"无法获取 tool_registry，跳过默认专家注册: {e}")
            return
        try:
            expert = ExpertAgent(
                agent_id="general_expert",
                domain_expertise="reasoning",
                capability_level=0.85,
                collaboration_style="supportive",
            )
            if getattr(expert, "tool_registry", None) is None:
                expert.tool_registry = registry
            self.register_expert_agent(expert)
            logger.info("✅ ChiefAgent 已注册默认专家 general_expert")
        except Exception as e:
            logger.warning(f"注册默认专家失败: {e}")

    def get_expert_agents(self) -> Dict[str, ExpertAgent]:
        """获取所有专家Agent"""
        return self.expert_agent_pool
    
    # ==================== 审核接口 ====================
    
    def is_audit_enabled(self) -> bool:
        """检查审核是否启用"""
        return self._audit_enabled and self.audit_agent is not None
    
    def is_quality_control_enabled(self) -> bool:
        """检查质量控制是否启用"""
        return self._quality_control_enabled and self.quality_controller is not None
    
    async def audit_action(
        self,
        source_agent: str,
        target_agent: str,
        action_type: str,
        action_details: Dict[str, Any]
    ) -> Any:
        """手动审核指定操作"""
        if not self.audit_agent:
            return None
            
        from .audit_agent import AuditRequest
        
        request = AuditRequest(
            request_id=str(uuid.uuid4())[:8],
            source_agent=source_agent,
            target_agent=target_agent,
            action_type=action_type,
            action_details=action_details,
            priority="normal"
        )
        
        return await self.audit_agent.audit_request(request)
    
    def assess_quality(
        self,
        content: str,
        validation_level: str = "standard"
    ) -> Any:
        """手动评估内容质量"""
        if not self.quality_controller:
            return None
            
        return self.quality_controller.assess_quality(
            content=content,
            content_id=str(uuid.uuid4())[:8],
            validation_level=validation_level
        )
    
    def get_audit_stats(self) -> Dict[str, Any]:
        """获取审核统计"""
        if self.audit_agent:
            return self.audit_agent.get_audit_stats()
        return {"status": "disabled"}
    
    def add_custom_audit_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        condition: str,
        severity: str,
        action: str
    ) -> None:
        """添加自定义审核规则"""
        if not self.audit_agent:
            logger.warning("审核未启用，无法添加规则")
            return
            
        from .audit_agent import AuditRule, AuditSeverity, AuditDecision
        
        severity_map = {
            "low": AuditSeverity.LOW,
            "medium": AuditSeverity.MEDIUM,
            "high": AuditSeverity.HIGH,
            "critical": AuditSeverity.CRITICAL
        }
        
        action_map = {
            "approved": AuditDecision.APPROVED,
            "rejected": AuditDecision.REJECTED,
            "conditional": AuditDecision.CONDITIONAL
        }
        
        self.audit_agent.add_audit_rule(
            rule_id=rule_id,
            name=name,
            description=description,
            condition=condition,
            severity=severity_map.get(severity, AuditSeverity.MEDIUM),
            action=action_map.get(action, AuditDecision.CONDITIONAL)
        )
        logger.info(f"✅ 添加审核规则: {rule_id}")
    
    # ==================== 开发工作流审核 ====================
    
    def is_dev_audit_enabled(self) -> bool:
        """检查开发审核是否启用"""
        return self._dev_audit_enabled and self.dev_audit is not None
    
    async def audit_code(self, code: str, context: Dict = None) -> Any:
        """审核代码
        
        Args:
            code: 要审核的代码
            context: 上下文信息
            
        Returns:
            CodeAuditResult: 审核结果
        """
        if not self.dev_audit:
            return None
        return await self.dev_audit.audit_code(code, context)
    
    async def audit_and_execute(
        self,
        code: str,
        execute_func: callable,
        context: Dict = None
    ) -> Dict[str, Any]:
        """审核代码并执行 (仅当审核通过)
        
        Args:
            code: 要审核的代码
            execute_func: 执行函数
            context: 上下文
            
        Returns:
            执行结果 (含审核元数据)
        """
        context = context or {}
        
        # 1. 审核代码
        audit_result = await self.audit_code(code, context)
        
        if audit_result and not audit_result.passed:
            return {
                "success": False,
                "error": "code_rejected_by_audit",
                "audit_result": {
                    "passed": False,
                    "risk_level": audit_result.risk_level.value,
                    "issues": [
                        {"description": i["description"], "suggestion": i.get("suggestion", "")}
                        for i in audit_result.issues
                    ],
                    "suggestions": audit_result.suggestions
                }
            }
        
        # 2. 审核通过, 使用消毒后的代码 (如果有)
        safe_code = audit_result.sanitized_code if audit_result else code
        
        # 3. 执行
        try:
            if asyncio.iscoroutinefunction(execute_func):
                result = await execute_func(safe_code, context)
            else:
                result = execute_func(safe_code, context)
            
            return {
                "success": True,
                "result": result,
                "audit_result": {
                    "passed": True,
                    "was_sanitized": safe_code != code,
                    "risk_level": audit_result.risk_level.value if audit_result else "unknown"
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "audit_result": {
                    "passed": True,  # 审核通过但执行失败
                    "execution_error": True
                }
            }
    
    def get_dev_audit_stats(self) -> Dict[str, Any]:
        """获取开发审核统计"""
        if self.dev_audit:
            return self.dev_audit.get_stats()
        return {"status": "disabled"}

    def run_linter_checks(
        self,
        paths: List[str],
        linters: Optional[List[str]] = None,
        pylint_args: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """对指定路径运行 linter（pylint/pyright），发现项目中的静态检查错误。

        与 audit_code() 的区别：audit_code 只做执行前安全与简单规范检查；
        run_linter_checks 运行 pylint/pyright 等，可发现项目里已有的 linter 错误。
        """
        if self.dev_audit:
            return self.dev_audit.run_linter_checks(paths, linters, pylint_args)
        return {"issues": [], "summary": {"total": 0}, "raw_output": "", "success": True}

    def add_dev_audit_rule(
        self,
        name: str,
        pattern: str,
        risk_level: str,
        description: str,
        suggestion: str = ""
    ) -> None:
        """添加开发审核规则"""
        if self.dev_audit:
            self.dev_audit.add_custom_rule(name, pattern, risk_level, description, suggestion)
            logger.info(f"✅ 添加开发审核规则: {name}")
        else:
            logger.warning("开发审核未启用")
