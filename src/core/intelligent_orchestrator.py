#!/usr/bin/env python3
"""
智能协调层 - 基于ReAct Agent的核心大脑
负责全局任务理解、规划和协调执行
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.agents.reasoning_expert import ReasoningExpert as ReActAgent
from src.agents.base_agent import AgentResult
from src.agents.tools.tool_registry import get_tool_registry
from src.utils.logging_helper import get_module_logger, ModuleType
from src.core.reasoning.ml_framework.model_auto_loader import auto_load_model

logger = logging.getLogger(__name__)


@dataclass
class Plan:
    """执行计划基类"""
    query: str
    tools: Any = None


@dataclass
class QuickPlan(Plan):
    """快速执行计划 - 用于简单任务"""
    executor: Any = None


@dataclass
class ParallelPlan(Plan):
    """并行执行计划 - 用于可分解的复杂任务"""
    executor: Any = None
    tasks: List[Any] = None


@dataclass
class ReasoningPlan(Plan):
    """深度推理计划 - 用于需要深度推理的任务"""
    steps: List[Any] = None
    orchestrator: Any = None


@dataclass
class ConservativePlan(Plan):
    """保守执行计划 - 用于回退方案"""
    executor: Any = None


@dataclass
class HybridPlan(Plan):
    """混合执行计划 - 用于多资源协同执行"""
    mas_tasks: List[Any] = None
    tool_tasks: List[Any] = None
    standard_tasks: List[Any] = None


class IntelligentOrchestrator(ReActAgent):
    """智能协调层 - 基于ReAct Agent的核心大脑
    
    职责：
    1. 全局任务理解和规划
    2. 智能选择执行策略
    3. 协调多个执行资源
    4. 支持动态调整
    """
    
    def __init__(self, agent_name: str = "IntelligentOrchestrator", use_intelligent_config: bool = True):
        """初始化智能协调层"""
        # ReasoningExpert.__init__ does not take arguments
        super().__init__()
        
        # Manually set agent_name if needed, or rely on ReasoningExpert's defaults
        # ExpertAgent sets agent_id="reasoning_expert", we might want to override it
        self.agent_id = agent_name
        
        # 使用模块日志器
        self.module_logger = get_module_logger(ModuleType.AGENT, agent_name)
        
        # 执行资源（将在后续步骤中注册）
        self.mas = None  # 多智能体系统（ChiefAgent）
        self.standard_loop = None  # 标准Agent循环（UnifiedResearchSystem自身）
        self.traditional = None  # 传统流程（UnifiedResearchSystem自身）
        
        # 步骤5.4：统一工具注册中心
        # 优先使用父类（ReActAgent）的工具注册中心，如果没有则创建新的
        if hasattr(self, 'tool_registry') and self.tool_registry:
            self.tools = self.tool_registry
        else:
            self.tools = get_tool_registry()
            # 确保父类也有工具注册中心
            if not hasattr(self, 'tool_registry'):
                self.tool_registry = self.tools
        
        # 资源状态
        self._resource_states: Dict[str, Dict[str, Any]] = {}
        
        # 🚀 步骤7.1：ML优化智能规划 - 初始化ML模型
        self.complexity_predictor = None
        self.execution_time_predictor = None
        self._initialize_ml_models()
        
        # 🚀 步骤7.2：动态调整机制 - 执行状态跟踪
        self._execution_history: List[Dict[str, Any]] = []  # 执行历史记录
        self._max_history_size = 100  # 最多保留100条历史记录
        self._current_execution_context: Optional[Dict[str, Any]] = None  # 当前执行上下文
        
        # 🚀 步骤7.3：性能监控 - 初始化性能监控器
        self._performance_monitor = None
        self._performance_metrics: Dict[str, Any] = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_response_time': 0.0,
            'path_usage': {
                'standard_loop': 0,
                'mas': 0,
                'react': 0,
                'traditional': 0,
                'hybrid': 0
            },
            'ml_model_usage': {
                'complexity_predictor': 0,
                'execution_time_predictor': 0
            },
            'error_rate': 0.0,
            'avg_response_time': 0.0,
            'avg_confidence': 0.0
        }
        self._initialize_performance_monitoring()
        
        self.module_logger.info(f"✅ 智能协调层初始化完成: {agent_name}")
        self.module_logger.info(f"✅ 工具注册中心已统一: {self.tools is not None}")
    
    def register_resource(self, name: str, resource: Any):
        """注册执行资源
        
        Args:
            name: 资源名称（'mas', 'standard_loop', 'traditional', 'tools'）
            resource: 资源对象
        """
        if name == 'mas':
            self.mas = resource
            self.module_logger.info("✅ MAS资源已注册")
        elif name == 'standard_loop':
            self.standard_loop = resource
            self.module_logger.info("✅ 标准循环资源已注册")
        elif name == 'traditional':
            self.traditional = resource
            self.module_logger.info("✅ 传统流程资源已注册")
        elif name == 'tools':
            self.tools = resource
            self.module_logger.info("✅ 工具注册中心已注册")
        else:
            self.module_logger.warning(f"⚠️ 未知资源类型: {name}")
        
        # 更新资源状态
        self._resource_states[name] = {
            'resource': resource,
            'registered': True,
            'healthy': self._check_resource_health(name, resource)
        }
    
    def _check_resource_health(self, name: str, resource: Any) -> bool:
        """检查资源健康状态"""
        if resource is None:
            return False
        
        # 基础健康检查
        try:
            if hasattr(resource, 'is_healthy'):
                return resource.is_healthy()
            elif hasattr(resource, '_is_initialized'):
                return resource._is_initialized
            else:
                return True  # 默认认为健康
        except Exception as e:
            self.module_logger.warning(f"⚠️ 检查资源健康状态失败: {name}, 错误: {e}")
            return False
    
    async def orchestrate(self, query: str, context: Dict[str, Any]) -> AgentResult:
        """🚀 P0修复：智能协调层 - 添加查询验证"""
        # 🚀 P0修复：验证查询是否为空
        if not query or not query.strip():
            error_msg = "查询为空，无法执行"
            self.module_logger.error(f"❌ {error_msg}")
            print(f"❌ [智能协调层] {error_msg}")
            return AgentResult(
                success=False,
                data={"answer": "[ERROR] 查询为空，无法执行"},
                error=error_msg,
                confidence=0.0,
                processing_time=0.0
            )
        
        # 🚀 P0修复：记录查询内容（用于诊断）
        self.module_logger.info(f"🔍 [智能协调层] 开始处理查询: query='{query[:100]}...' (长度={len(query)})")
        print(f"🔍 [智能协调层] 开始处理查询: query='{query[:100]}...' (长度={len(query)})")
        """智能协调执行 - 唯一入口
        
        Args:
            query: 用户查询
            context: 上下文信息（包含系统状态等）
            
        Returns:
            AgentResult: 执行结果
        """
        start_time = time.time()
        
        try:
            self.module_logger.info(f"🧠 智能协调层开始处理: {query[:100]}...")
            print(f"🧠 [DEBUG] 智能协调层开始处理: {query[:100]}...")  # 🚀 添加print确保日志可见
            
            # 🚀 步骤7.2：记录当前执行上下文
            self._current_execution_context = {
                'query': query,
                'context': context,
                'start_time': start_time,
                'execution_path': None  # 将在执行计划时设置
            }
            
            # 1. Think: 快速判断 + 深度规划
            plan = await self._think_and_plan(query, context)
            
            # 🚀 添加日志：记录生成的计划类型
            plan_type = type(plan).__name__
            self.module_logger.info(f"📋 [Orchestrate] 生成的计划类型: {plan_type}")
            print(f"📋 [DEBUG] [Orchestrate] 生成的计划类型: {plan_type}")  # 🚀 添加print确保日志可见
            if isinstance(plan, ReasoningPlan):
                steps_count = len(plan.steps) if plan.steps else 0
                self.module_logger.info(f"📋 [Orchestrate] ReasoningPlan包含 {steps_count} 个推理步骤")
                print(f"📋 [DEBUG] [Orchestrate] ReasoningPlan包含 {steps_count} 个推理步骤")  # 🚀 添加print确保日志可见
            
            # 记录执行路径
            if isinstance(plan, QuickPlan):
                self._current_execution_context['execution_path'] = 'standard_loop'
            elif isinstance(plan, ParallelPlan):
                self._current_execution_context['execution_path'] = 'mas'
            elif isinstance(plan, ReasoningPlan):
                self._current_execution_context['execution_path'] = 'react'
            elif isinstance(plan, ConservativePlan):
                self._current_execution_context['execution_path'] = 'traditional'
            elif isinstance(plan, HybridPlan):
                self._current_execution_context['execution_path'] = 'hybrid'
            
            # 2. Act: 智能协调执行
            self.module_logger.info(f"🚀 [Orchestrate] 开始执行计划: {plan_type}")
            result = await self._execute_plan(plan)
            
            # 3. Observe: 监控和动态调整
            final_result = await self._observe_and_adjust(result)
            
            final_result.processing_time = time.time() - start_time
            self.module_logger.info(f"✅ 智能协调层处理完成，耗时: {final_result.processing_time:.2f}秒")
            
            # 清理执行上下文
            self._current_execution_context = None
            
            return final_result
            
        except Exception as e:
            self.module_logger.error(f"❌ 智能协调层处理失败: {e}", exc_info=True)
            # 清理执行上下文
            self._current_execution_context = None
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _think_and_plan(self, query: str, context: Dict[str, Any]) -> Plan:
        """智能规划 - 深度任务理解和规划
        
        🚀 P2改进：移除Entry Router功能，只保留深度规划功能
        Entry Router的快速路由功能已独立实现
        
        Args:
            query: 用户查询
            context: 上下文信息（可能包含route_path，由Entry Router提供）
            
        Returns:
            Plan: 执行计划
        """
        # 🚀 P2改进：增加Think阶段的详细日志，明确区分深度规划阶段
        self.module_logger.info("=" * 60)
        self.module_logger.info("🧠 [Think阶段-深度规划] 开始深度任务理解和规划")
        self.module_logger.info(f"📝 [Think阶段-深度规划] 查询: {query[:100]}...")
        
        # 🚀 P2改进：如果context中包含route_path，记录路由信息
        route_path = context.get('route_path') if context else None
        if route_path:
            self.module_logger.info(f"🔄 [Think阶段-深度规划] Entry Router路由路径: {route_path}")
        else:
            self.module_logger.warning(f"⚠️ [Think阶段-深度规划] context中没有route_path，context keys: {list(context.keys()) if context else 'None'}")
        
        # 步骤2.1：系统状态检查（用于资源可用性检查，不是路由决策）
        system_state = self._check_system_state()
        load = system_state.get("load", 0)
        self.module_logger.info(f"💻 [Think阶段-深度规划] 系统状态: load={load:.1f}%")
        
        # 🚀 步骤7.1优化：使用ML模型预测执行时间，辅助决策
        execution_time_predictions = None
        if self.execution_time_predictor:
            try:
                import time
                start_time = time.time()
                # 使用中等复杂度作为默认值（因为Entry Router已经做了快速路由）
                complexity = context.get('complexity', 'medium') if context else 'medium'
                execution_time_predictions = self.execution_time_predictor.predict_all_paths(
                    query, complexity, system_state
                )
                execution_time = time.time() - start_time
                
                # 🚀 步骤7.3：记录ML模型使用情况
                self._record_ml_model_usage('execution_time_predictor', execution_time)
                
                self.module_logger.info(f"⏱️ [Think阶段-深度规划] 执行时间预测完成 (耗时: {execution_time:.3f}秒)")
                if execution_time_predictions:
                    for path, pred in execution_time_predictions.items():
                        pred_time = pred.get('predicted_time', 0)
                        self.module_logger.info(f"   - {path}: {pred_time:.2f}秒")
            except Exception as e:
                self.module_logger.warning(f"⚠️ [Think阶段-深度规划] 执行时间预测失败: {e}")
        
        # 🚀 P2改进：深度规划 - 所有到达这里的任务都需要深度理解
        # 步骤2.2：深度任务理解
        self.module_logger.info("🔍 [Think阶段-深度规划] 开始深度任务理解...")
        understanding = await self._understand_task(query, context)
        can_parallelize = understanding.get("can_be_parallelized", False)
        requires_reasoning = understanding.get("requires_deep_reasoning", False)
        subtasks_count = len(understanding.get("subtasks", []))
        steps_count = len(understanding.get("steps", []))
        self.module_logger.info(f"💡 [Think阶段-深度规划] 任务理解结果:")
        self.module_logger.info(f"   - 可并行化: {can_parallelize}")
        self.module_logger.info(f"   - 需要深度推理: {requires_reasoning}")
        self.module_logger.info(f"   - 子任务数量: {subtasks_count}")
        self.module_logger.info(f"   - 推理步骤数量: {steps_count}")
        if understanding.get("reasoning"):
            self.module_logger.info(f"   - 分析理由: {understanding.get('reasoning', 'N/A')[:200]}...")
        
        # 步骤2.3：根据理解结果和路由路径选择执行策略
        # 🚀 P2改进：如果Entry Router已经路由到MAS或ReAct，优先使用该路径
        # 🚀 步骤7.1优化：如果执行时间预测可用，优先选择预测时间最短的路径
        
        # 如果Entry Router已经路由到MAS，优先使用MAS
        if route_path == "mas" and understanding.get("can_be_parallelized") and self.is_resource_available('mas'):
            # 检查MAS的预测时间
            if execution_time_predictions:
                mas_time = execution_time_predictions.get('mas', {}).get('predicted_time', float('inf'))
                standard_time = execution_time_predictions.get('standard_loop', {}).get('predicted_time', float('inf'))
                
                # 如果标准循环明显更快，且差异较大，使用标准循环
                if standard_time < mas_time * 0.7:  # 标准循环快30%以上
                    self.module_logger.info(f"✅ [Think阶段] 选择执行路径: Standard Loop")
                    self.module_logger.info(f"   📌 选择理由: 虽然可并行，但标准循环更快（MAS: {mas_time:.2f}秒 vs 标准: {standard_time:.2f}秒，快{((mas_time-standard_time)/mas_time*100):.1f}%）")
                    self.module_logger.info("=" * 60)
                    return QuickPlan(
                        query=query,
                        executor=self.standard_loop,
                        tools=self.tools
                    )
            
            self.module_logger.info(f"✅ [Think阶段-深度规划] 选择执行路径: MAS (并行执行)")
            mas_time = execution_time_predictions.get('mas', {}).get('predicted_time', 0) if execution_time_predictions and 'mas' in execution_time_predictions else 0
            self.module_logger.info(f"   📌 选择理由: Entry Router路由到MAS，任务可并行化，MAS资源可用" + (f"，预测执行时间: {mas_time:.2f}秒" if mas_time > 0 else ""))
            self.module_logger.info(f"   📋 子任务数量: {subtasks_count}")
            self.module_logger.info("=" * 60)
            return ParallelPlan(
                query=query,
                executor=self.mas,
                tasks=understanding.get("subtasks", []),
                tools=self.tools
            )
        
        # 🚀 修复：如果Entry Router已经路由到ReAct Agent，强制使用ReAct循环（ReasoningPlan）
        # 这是最高优先级，因为Entry Router已经判断这个查询需要深度推理
        if route_path == "react_agent":
            self.module_logger.info(f"✅ [Think阶段-深度规划] 选择执行路径: ReAct循环 (深度推理)")
            self.module_logger.info(f"   📌 选择理由: Entry Router路由到ReAct Agent（强制使用ReasoningPlan）")
            self.module_logger.info(f"   📋 推理步骤数量: {steps_count}")
            self.module_logger.info("=" * 60)
            return ReasoningPlan(
                query=query,
                tools=self.tools,
                steps=understanding.get("steps", []),
                orchestrator=self
            )
        
        # 如果需要深度推理，使用ReAct循环
        if understanding.get("requires_deep_reasoning"):
            self.module_logger.info(f"✅ [Think阶段-深度规划] 选择执行路径: ReAct循环 (深度推理)")
            self.module_logger.info(f"   📌 选择理由: 需要深度推理，推理步骤数量: {steps_count}")
            self.module_logger.info("=" * 60)
            return ReasoningPlan(
                query=query,
                tools=self.tools,
                steps=understanding.get("steps", []),
                orchestrator=self
            )
        
        # 如果Entry Router路由到MAS但任务不可并行化，或需要深度推理，使用ReAct循环
        if route_path == "mas" and not understanding.get("can_be_parallelized"):
            self.module_logger.info(f"✅ [Think阶段-深度规划] 选择执行路径: ReAct循环 (深度推理)")
            self.module_logger.info(f"   📌 选择理由: Entry Router路由到MAS但任务不可并行化，使用深度推理")
            self.module_logger.info("=" * 60)
            return ReasoningPlan(
                query=query,
                tools=self.tools,
                steps=understanding.get("steps", []),
                orchestrator=self
            )
        
        # 默认：如果Entry Router路由到MAS，使用MAS（即使任务理解认为不可并行化，也尝试）
        if route_path == "mas" and self.is_resource_available('mas'):
            self.module_logger.info(f"✅ [Think阶段-深度规划] 选择执行路径: MAS (默认)")
            self.module_logger.info(f"   📌 选择理由: Entry Router路由到MAS，使用MAS执行")
            self.module_logger.info("=" * 60)
            return ParallelPlan(
                query=query,
                executor=self.mas,
                tasks=understanding.get("subtasks", []),
                tools=self.tools
            )
        
        # 回退：使用传统流程
        self.module_logger.info(f"✅ [Think阶段-深度规划] 选择执行路径: Traditional Flow (回退路径)")
        self.module_logger.info(f"   📌 选择理由: 默认回退方案，确保稳定性")
        self.module_logger.info("=" * 60)
        return ConservativePlan(
            query=query,
            executor=self.traditional,
            tools=self.tools
        )
    
    async def _understand_task(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """深度任务理解（原StrategySelector功能）
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            任务理解结果字典，包含：
            - can_be_parallelized: 是否可以并行化
            - requires_deep_reasoning: 是否需要深度推理
            - subtasks: 子任务列表（如果可以分解）
            - steps: 推理步骤列表（如果需要深度推理）
        """
        if not self.llm_client:
            # 如果没有LLM客户端，使用规则判断
            return self._understand_task_by_rules(query)
        
        try:
            prompt = f"""分析以下任务，判断执行策略：

任务：{query}

请分析：
1. 这个任务是否可以分解为多个可以并行执行的子任务？
2. 这个任务是否需要深度推理（多步骤思考、逻辑推理、综合分析）？
3. 如果需要分解，请列出子任务
4. 如果需要深度推理，请列出推理步骤

返回JSON格式：
{{
    "can_be_parallelized": true/false,
    "requires_deep_reasoning": true/false,
    "subtasks": ["子任务1", "子任务2", ...],
    "steps": ["步骤1", "步骤2", ...],
    "reasoning": "分析理由"
}}"""
            
            response = await self.llm_client._call_llm(prompt)
            
            # 解析响应
            import json
            try:
                # 尝试提取JSON
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0].strip()
                else:
                    json_str = response.strip()
                
                understanding = json.loads(json_str)
                self.module_logger.info(f"✅ 任务理解完成: {understanding.get('reasoning', 'N/A')[:100]}")
                return understanding
            except json.JSONDecodeError:
                self.module_logger.warning("⚠️ LLM响应不是有效JSON，使用规则判断")
                return self._understand_task_by_rules(query)
                
        except Exception as e:
            self.module_logger.warning(f"⚠️ 深度任务理解失败: {e}，使用规则判断")
            return self._understand_task_by_rules(query)
    
    def _understand_task_by_rules(self, query: str) -> Dict[str, Any]:
        """基于规则的任务理解（回退方案）"""
        query_lower = query.lower()
        
        # 判断是否可以并行化
        can_be_parallelized = any(word in query_lower for word in [
            '和', '以及', '同时', '分别', 'and', 'also', 'while', 'respectively',
            'compare', '比较', 'difference', '区别'
        ])
        
        # 判断是否需要深度推理
        requires_deep_reasoning = any(word in query_lower for word in [
            '分析', '解释', '为什么', '如何', 'analyze', 'explain', 'why', 'how',
            '设计', '规划', 'design', 'plan'
        ]) or query.count("'s ") > 2
        
        return {
            "can_be_parallelized": can_be_parallelized,
            "requires_deep_reasoning": requires_deep_reasoning,
            "subtasks": [],
            "steps": [],
            "reasoning": "基于规则判断"
        }
    
    def _initialize_ml_models(self):
        """🚀 步骤7.1：初始化ML模型"""
        try:
            # 初始化复杂度预测模型
            from src.core.reasoning.ml_framework.complexity_predictor import ComplexityPredictor
            self.complexity_predictor = ComplexityPredictor()
            auto_load_model(self.complexity_predictor, "complexity_predictor")
            
            # 初始化执行时间预测模型
            from src.core.reasoning.ml_framework.execution_time_predictor import ExecutionTimePredictor
            self.execution_time_predictor = ExecutionTimePredictor()
            auto_load_model(self.execution_time_predictor, "execution_time_predictor")
            
            self.module_logger.info("✅ ML模型初始化完成")
        except Exception as e:
            self.module_logger.warning(f"⚠️ ML模型初始化失败: {e}，将使用规则版本")
            self.complexity_predictor = None
            self.execution_time_predictor = None
    
    def _initialize_performance_monitoring(self):
        """🚀 步骤7.3：初始化性能监控"""
        try:
            from src.core.reasoning.ml_framework.model_performance_monitor import ModelPerformanceMonitor
            self._performance_monitor = ModelPerformanceMonitor()
            self.module_logger.info("✅ 性能监控器初始化完成")
        except Exception as e:
            self.module_logger.warning(f"⚠️ 性能监控器初始化失败: {e}")
            self._performance_monitor = None
    
    def _quick_analyze_complexity(self, query: str) -> str:
        """快速复杂度分析 - 🚀 重构：使用统一复杂度服务（LLM判断）
        
        Args:
            query: 用户查询
            
        Returns:
            复杂度级别：'simple', 'medium', 'complex'
        """
        # 🚀 优先使用统一复杂度服务（支持LLM判断）
        try:
            from src.utils.unified_complexity_model_service import get_unified_complexity_model_service
            complexity_service = get_unified_complexity_model_service()
            complexity_result = complexity_service.assess_complexity(
                query=query,
                query_type=None,
                evidence_count=0,
                use_cache=True
            )
            return complexity_result.level.value  # 'simple', 'medium', 'complex'
        except Exception as e:
            self.module_logger.warning(f"⚠️ 使用统一复杂度服务失败: {e}，使用fallback")
        
        # Fallback: 优先使用ML模型预测
        if self.complexity_predictor:
            try:
                import time
                start_time = time.time()
                result = self.complexity_predictor.predict(query)
                execution_time = time.time() - start_time
                complexity = result.get('complexity', 'medium')
                confidence = result.get('confidence', 0.0)
                
                # 🚀 步骤7.3：记录ML模型使用情况
                self._record_ml_model_usage('complexity_predictor', execution_time)
                
                # 如果置信度足够高，使用ML预测结果
                if confidence > 0.6:
                    self.module_logger.debug(f"✅ ML复杂度预测: {complexity} (置信度: {confidence:.2%})")
                    return complexity
                else:
                    self.module_logger.debug(f"⚠️ ML预测置信度较低 ({confidence:.2%})，使用规则判断")
            except Exception as e:
                self.module_logger.debug(f"⚠️ ML复杂度预测失败: {e}，使用规则判断")
        
        # 回退到规则判断
        query_lower = query.lower()
        query_length = len(query.split())
        
        # 简单任务：单句事实查询
        if query_length < 10 and not any(word in query_lower for word in ['分析', '比较', '设计', '解释', 'analyze', 'compare', 'design', 'explain']):
            return "simple"
        
        # 复杂任务：包含多个子任务或复杂逻辑
        if any(word in query_lower for word in ['和', '以及', '同时', '分别', 'and', 'also', 'while', 'respectively']):
            return "complex"
        if query_length > 20 or query.count("'s ") > 2:
            return "complex"
        
        return "medium"
    
    def is_resource_available(self, name: str) -> bool:
        """检查资源是否可用
        
        Args:
            name: 资源名称
            
        Returns:
            如果资源可用返回True，否则返回False
        """
        if name not in self._resource_states:
            return False
        
        state = self._resource_states[name]
        return state.get('registered', False) and state.get('healthy', False)
    
    def _check_system_state(self) -> Dict[str, Any]:
        """检查系统状态
        
        Returns:
            系统状态字典
        """
        return {
            "load": self._get_system_load(),
            "mas_healthy": self.is_resource_available('mas'),
            "tools_available": self.is_resource_available('tools'),
            "standard_loop_available": self.is_resource_available('standard_loop'),
            "traditional_available": self.is_resource_available('traditional')
        }
    
    def _get_system_load(self) -> float:
        """获取系统负载
        
        Returns:
            系统负载（0-100）
        """
        try:
            import psutil
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 综合负载（取CPU和内存的最大值）
            load = max(cpu_percent, memory_percent)
            return load
        except Exception as e:
            self.module_logger.warning(f"⚠️ 获取系统负载失败: {e}")
            return 50.0  # 默认中等负载
    
    async def _execute_plan(self, plan: Plan) -> AgentResult:
        """执行计划 - 真正的协作执行
        
        Args:
            plan: 执行计划
            
        Returns:
            AgentResult: 执行结果
        """
        plan_type = type(plan).__name__
        self.module_logger.info(f"🔍 [Execute Plan] 执行计划类型: {plan_type}")
        print(f"🔍 [DEBUG] [Execute Plan] 执行计划类型: {plan_type}")  # 🚀 添加print确保日志可见
        try:
            if isinstance(plan, QuickPlan):
                self.module_logger.info("🔍 [Execute Plan] 调用 _execute_quick_plan")
                print("🔍 [DEBUG] [Execute Plan] 调用 _execute_quick_plan")  # 🚀 添加print确保日志可见
                return await self._execute_quick_plan(plan)
            elif isinstance(plan, ParallelPlan):
                self.module_logger.info("🔍 [Execute Plan] 调用 _execute_parallel_plan")
                print("🔍 [DEBUG] [Execute Plan] 调用 _execute_parallel_plan")  # 🚀 添加print确保日志可见
                return await self._execute_parallel_plan(plan)
            elif isinstance(plan, ReasoningPlan):
                self.module_logger.info("🔍 [Execute Plan] 调用 _execute_reasoning_plan")
                print("🔍 [DEBUG] [Execute Plan] 调用 _execute_reasoning_plan")  # 🚀 添加print确保日志可见
                return await self._execute_reasoning_plan(plan)
            elif isinstance(plan, ConservativePlan):
                self.module_logger.info("🔍 [Execute Plan] 调用 _execute_conservative_plan")
                return await self._execute_conservative_plan(plan)
            elif isinstance(plan, HybridPlan):
                self.module_logger.info("🔍 [Execute Plan] 调用 _execute_hybrid_plan")
                return await self._execute_hybrid_plan(plan)
            else:
                raise ValueError(f"未知的计划类型: {type(plan)}")
        except Exception as e:
            self.module_logger.error(f"❌ 执行计划失败: {e}", exc_info=True)
            # 回退到保守方案
            if not isinstance(plan, ConservativePlan):
                self.module_logger.warning("⚠️ 回退到保守方案")
                return await self._execute_conservative_plan(
                    ConservativePlan(query=plan.query, executor=self.traditional, tools=self.tools)
                )
            else:
                raise
    
    async def _execute_quick_plan(self, plan: QuickPlan) -> AgentResult:
        """执行快速计划
        
        Args:
            plan: 快速执行计划
            
        Returns:
            AgentResult: 执行结果
        """
        self.module_logger.info("🚀 执行快速计划（标准循环）")
        if plan.executor is None:
            return AgentResult(
                success=False,
                data=None,
                error="标准循环资源未注册",
                confidence=0.0,
                processing_time=0.0
            )
        
        # 步骤5.2：适配标准循环接口
        try:
            # 如果executor是UnifiedResearchSystem，调用_execute_research_agent_loop
            if hasattr(plan.executor, '_execute_research_agent_loop'):
                from src.unified_research_system import ResearchRequest
                request = ResearchRequest(query=plan.query)
                start_time = time.time()
                result = await plan.executor._execute_research_agent_loop(request, start_time)
                
                # 转换为AgentResult
                agent_result = AgentResult(
                    success=result.success,
                    data={
                        "answer": result.answer,
                        "knowledge": result.knowledge or [],
                        "reasoning": result.reasoning,
                        "citations": result.citations or []
                    },
                    confidence=result.confidence,
                    processing_time=result.execution_time,
                    error=result.error
                )
                self.module_logger.info(f"✅ 快速计划执行成功: success={agent_result.success}, confidence={agent_result.confidence:.2f}")
                return agent_result
            elif hasattr(plan.executor, 'execute'):
                # 其他情况，尝试直接调用execute（标准Agent接口）
                context = {"query": plan.query}
                result = await plan.executor.execute(context)
                
                # 确保返回AgentResult
                if not isinstance(result, AgentResult):
                    raise TypeError(f"标准循环返回结果类型不正确: {type(result)}")
                
                self.module_logger.info(f"✅ 快速计划执行成功: success={result.success}, confidence={result.confidence:.2f}")
                return result
            else:
                raise AttributeError("标准循环资源没有可用的execute方法")
        except Exception as e:
            self.module_logger.error(f"❌ 快速计划执行失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=f"快速计划执行失败: {str(e)}",
                confidence=0.0,
                processing_time=0.0
            )
    
    async def _execute_parallel_plan(self, plan: ParallelPlan) -> AgentResult:
        """执行并行计划
        
        Args:
            plan: 并行执行计划
            
        Returns:
            AgentResult: 执行结果
        """
        self.module_logger.info(f"🚀 执行并行计划（MAS），任务数: {len(plan.tasks) if plan.tasks else 0}")
        if plan.executor is None:
            return AgentResult(
                success=False,
                data=None,
                error="MAS资源未注册",
                confidence=0.0,
                processing_time=0.0
            )
        
        # MAS（ChiefAgent）的execute方法接受context字典
        try:
            # 步骤5.1：适配MAS接口
            context = {
                "query": plan.query
            }
            # 如果有子任务，添加到context中
            if plan.tasks:
                context["subtasks"] = plan.tasks
            
            # 确保ChiefAgent有execute方法
            if not hasattr(plan.executor, 'execute'):
                raise AttributeError("ChiefAgent没有execute方法")
            
            # 调用ChiefAgent的execute方法
            result = await plan.executor.execute(context)
            
            # 验证返回结果类型
            if not isinstance(result, AgentResult):
                self.module_logger.warning(f"⚠️ MAS返回结果类型不正确: {type(result)}，尝试转换")
                # 尝试转换
                if hasattr(result, 'success') and hasattr(result, 'data'):
                    result = AgentResult(
                        success=getattr(result, 'success', False),
                        data=getattr(result, 'data', None),
                        confidence=getattr(result, 'confidence', 0.0),
                        processing_time=getattr(result, 'processing_time', 0.0),
                        error=getattr(result, 'error', None),
                        metadata=getattr(result, 'metadata', None)
                    )
                else:
                    raise TypeError(f"无法转换MAS返回结果: {type(result)}")
            
            self.module_logger.info(f"✅ 并行计划执行成功: success={result.success}, confidence={result.confidence:.2f}")
            return result
        except Exception as e:
            self.module_logger.error(f"❌ 并行计划执行失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=f"并行计划执行失败: {str(e)}",
                confidence=0.0,
                processing_time=0.0
            )
    
    async def _execute_reasoning_plan(self, plan: ReasoningPlan) -> AgentResult:
        """执行推理计划 - 直接使用RealReasoningEngine
        
        Args:
            plan: 深度推理计划
            
        Returns:
            AgentResult: 执行结果
        """
        import time
        start_time = time.time()
        self._reasoning_start_time = start_time  # 保存开始时间，用于错误处理
        
        self.module_logger.info("=" * 60)
        self.module_logger.info("🧠 [Execute Reasoning Plan] 执行推理计划（直接使用RealReasoningEngine）")
        print("=" * 60)  # 🚀 添加print确保日志可见
        print("🧠 [DEBUG] [Execute Reasoning Plan] 执行推理计划（直接使用RealReasoningEngine）")  # 🚀 添加print确保日志可见
        self.module_logger.info(f"📝 [Execute Reasoning Plan] 查询: {plan.query[:100]}...")
        print(f"📝 [DEBUG] [Execute Reasoning Plan] 查询: {plan.query[:100]}...")  # 🚀 添加print确保日志可见
        steps_count = len(plan.steps) if plan.steps else 0
        self.module_logger.info(f"📋 [Execute Reasoning Plan] 推理步骤数量: {steps_count}")
        print(f"📋 [DEBUG] [Execute Reasoning Plan] 推理步骤数量: {steps_count}")  # 🚀 添加print确保日志可见
        if plan.steps:
            for i, step in enumerate(plan.steps[:3]):  # 只显示前3个步骤
                step_desc = str(step)[:100] if step else "N/A"
                self.module_logger.info(f"   - 步骤{i+1}: {step_desc}...")
        self.module_logger.info("=" * 60)
        
        try:
            # 🚀 修复：对于复杂推理查询，直接使用RealReasoningEngine而不是通过RAG工具
            # 这样可以确保使用完整的推理步骤、占位符替换、实体补全等功能
            from src.core.reasoning.engine import RealReasoningEngine
            from src.utils.reasoning_engine_pool import get_reasoning_engine_pool
            
            # 从实例池获取推理引擎
            pool = get_reasoning_engine_pool()
            reasoning_engine = pool.get_engine()
            
            try:
                # 构建推理上下文（不预先检索知识，让RealReasoningEngine自己处理）
                reasoning_context = {
                    'query': plan.query,
                    'knowledge': [],  # 空列表，让RealReasoningEngine自己检索
                    'evidence': []    # 空列表，让RealReasoningEngine自己检索
                }
                
                # 如果plan中有额外的上下文，合并进去
                if hasattr(plan, 'context') and plan.context:
                    reasoning_context.update(plan.context)
                
                self.module_logger.info(f"🔍 [推理计划] 直接调用RealReasoningEngine，查询: {plan.query[:100]}...")
                print(f"🔍 [DEBUG] [推理计划] 直接调用RealReasoningEngine，查询: {plan.query[:100]}...")  # 🚀 添加print确保日志可见
                
                # 🚀 P0修复：添加性能计时
                reasoning_start_time = time.time()
                print(f"⏱️ [性能] 开始执行推理引擎，时间: {reasoning_start_time:.2f}")
                
                # 执行推理
                reasoning_result = await reasoning_engine.reason(plan.query, reasoning_context)
                
                # 🚀 P0修复：记录推理耗时
                reasoning_time = time.time() - reasoning_start_time
                self.module_logger.info(f"⏱️ [性能] 推理引擎执行完成，耗时: {reasoning_time:.2f}秒")
                print(f"⏱️ [性能] 推理引擎执行完成，耗时: {reasoning_time:.2f}秒")
                
                # 转换为AgentResult
                if reasoning_result and hasattr(reasoning_result, 'final_answer'):
                    return AgentResult(
                        success=True,
                        data={
                            "answer": reasoning_result.final_answer,
                            "reasoning": getattr(reasoning_result, 'reasoning', ''),
                            "reasoning_steps": getattr(reasoning_result, 'reasoning_steps', []),
                            "evidence": getattr(reasoning_result, 'evidence', []),
                            "confidence": getattr(reasoning_result, 'confidence', 0.7)
                        },
                        confidence=getattr(reasoning_result, 'confidence', 0.7),
                        processing_time=getattr(reasoning_result, 'processing_time', 0.0)
                    )
                else:
                    self.module_logger.warning("⚠️ RealReasoningEngine未返回有效结果")
                    print("⚠️ [DEBUG] RealReasoningEngine未返回有效结果")  # 🚀 添加print确保日志可见
                    # 🚀 修复：不要回退到ReAct循环（会使用RAG工具），而是返回错误结果
                    # 这样可以确保复杂查询始终使用RealReasoningEngine，而不是RAG工具
                    return AgentResult(
                        success=False,
                        data=None,
                        error="RealReasoningEngine未返回有效结果",
                        confidence=0.0,
                        processing_time=time.time() - start_time
                    )
            finally:
                # 返回实例到池中
                pool.return_engine(reasoning_engine)
        except Exception as e:
            self.module_logger.error(f"❌ 直接使用RealReasoningEngine失败: {e}", exc_info=True)
            print(f"❌ [DEBUG] 直接使用RealReasoningEngine失败: {e}")  # 🚀 添加print确保日志可见
            # 🚀 修复：不要回退到ReAct循环（会使用RAG工具），而是返回错误结果
            # 这样可以确保复杂查询始终使用RealReasoningEngine，而不是RAG工具
            return AgentResult(
                success=False,
                data=None,
                error=f"RealReasoningEngine执行失败: {str(e)}",
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _execute_conservative_plan(self, plan: ConservativePlan) -> AgentResult:
        """执行保守计划
        
        Args:
            plan: 保守执行计划
            
        Returns:
            AgentResult: 执行结果
        """
        self.module_logger.info("🛡️ 执行保守计划（传统流程）")
        if plan.executor is None:
            return AgentResult(
                success=False,
                data=None,
                error="传统流程资源未注册",
                confidence=0.0,
                processing_time=0.0
            )
        
        # 步骤5.3：适配传统流程接口
        try:
            # 如果executor是UnifiedResearchSystem，调用_execute_research_internal
            if hasattr(plan.executor, '_execute_research_internal'):
                from src.unified_research_system import ResearchRequest
                request = ResearchRequest(query=plan.query)
                result = await plan.executor._execute_research_internal(request)
                
                # 转换为AgentResult
                agent_result = AgentResult(
                    success=result.success,
                    data={
                        "answer": result.answer,
                        "knowledge": result.knowledge or [],
                        "reasoning": result.reasoning,
                        "citations": result.citations or []
                    },
                    confidence=result.confidence,
                    processing_time=result.execution_time,
                    error=result.error
                )
                self.module_logger.info(f"✅ 保守计划执行成功: success={agent_result.success}, confidence={agent_result.confidence:.2f}")
                return agent_result
            elif hasattr(plan.executor, 'execute'):
                # 其他情况，尝试直接调用execute（标准Agent接口）
                context = {"query": plan.query}
                result = await plan.executor.execute(context)
                
                # 确保返回AgentResult
                if not isinstance(result, AgentResult):
                    raise TypeError(f"传统流程返回结果类型不正确: {type(result)}")
                
                self.module_logger.info(f"✅ 保守计划执行成功: success={result.success}, confidence={result.confidence:.2f}")
                return result
            else:
                raise AttributeError("传统流程资源没有可用的execute方法")
        except Exception as e:
            self.module_logger.error(f"❌ 保守计划执行失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=f"保守计划执行失败: {str(e)}",
                confidence=0.0,
                processing_time=0.0
            )
    
    async def _execute_hybrid_plan(self, plan: HybridPlan) -> AgentResult:
        """执行混合计划 - 多资源协同执行
        
        混合计划允许同时使用多个执行资源（MAS、标准循环、工具）协同完成一个任务。
        这适用于需要并行处理多个子任务，同时某些子任务需要深度推理的场景。
        
        Args:
            plan: 混合执行计划
            
        Returns:
            AgentResult: 执行结果
        """
        self.module_logger.info("🔄 执行混合计划（多资源协同）")
        start_time = time.time()
        
        try:
            import asyncio
            
            # 收集所有需要执行的任务
            tasks = []
            task_descriptions = []
            
            # MAS任务
            if plan.mas_tasks and self.mas:
                self.module_logger.info(f"🔄 准备执行MAS任务: {len(plan.mas_tasks)}个")
                for task in plan.mas_tasks:
                    context = {
                        "query": task.get("query", plan.query) if isinstance(task, dict) else str(task),
                        "subtasks": task.get("subtasks", []) if isinstance(task, dict) else []
                    }
                    tasks.append(self.mas.execute(context))
                    task_descriptions.append(f"MAS: {context['query'][:50]}...")
            
            # 工具任务（通过标准循环执行）
            if plan.tool_tasks and self.standard_loop:
                self.module_logger.info(f"🔄 准备执行工具任务: {len(plan.tool_tasks)}个")
                for task in plan.tool_tasks:
                    if hasattr(self.standard_loop, '_execute_research_agent_loop'):
                        from src.unified_research_system import ResearchRequest
                        query = task.get("query", plan.query) if isinstance(task, dict) else str(task)
                        request = ResearchRequest(query=query)
                        task_start = time.time()
                        tasks.append(self.standard_loop._execute_research_agent_loop(request, task_start))
                        task_descriptions.append(f"Tool: {query[:50]}...")
            
            # 标准循环任务
            if plan.standard_tasks and self.standard_loop:
                self.module_logger.info(f"🔄 准备执行标准循环任务: {len(plan.standard_tasks)}个")
                for task in plan.standard_tasks:
                    if hasattr(self.standard_loop, '_execute_research_agent_loop'):
                        from src.unified_research_system import ResearchRequest
                        query = task.get("query", plan.query) if isinstance(task, dict) else str(task)
                        request = ResearchRequest(query=query)
                        task_start = time.time()
                        tasks.append(self.standard_loop._execute_research_agent_loop(request, task_start))
                        task_descriptions.append(f"Standard: {query[:50]}...")
            
            if not tasks:
                self.module_logger.warning("⚠️ 混合计划没有可执行的任务")
                return AgentResult(
                    success=False,
                    data=None,
                    error="混合计划没有可执行的任务",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
            
            # 并行执行所有任务
            self.module_logger.info(f"🔄 开始并行执行{len(tasks)}个任务")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            successful_results = []
            failed_results = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.module_logger.error(f"❌ 任务{i+1}执行异常: {result}")
                    failed_results.append({
                        "task": task_descriptions[i] if i < len(task_descriptions) else f"Task {i+1}",
                        "error": str(result)
                    })
                elif isinstance(result, AgentResult):
                    if result.success:
                        successful_results.append(result)
                    else:
                        failed_results.append({
                            "task": task_descriptions[i] if i < len(task_descriptions) else f"Task {i+1}",
                            "error": result.error
                        })
                else:
                    # 尝试转换为AgentResult（可能是ResearchResult）
                    try:
                        if hasattr(result, 'success'):
                            agent_result = AgentResult(
                                success=result.success,
                                data={
                                    "answer": getattr(result, 'answer', ''),
                                    "knowledge": getattr(result, 'knowledge', []),
                                    "reasoning": getattr(result, 'reasoning', ''),
                                    "citations": getattr(result, 'citations', [])
                                },
                                confidence=getattr(result, 'confidence', 0.0),
                                processing_time=getattr(result, 'execution_time', 0.0),
                                error=getattr(result, 'error', None)
                            )
                            if agent_result.success:
                                successful_results.append(agent_result)
                            else:
                                failed_results.append({
                                    "task": task_descriptions[i] if i < len(task_descriptions) else f"Task {i+1}",
                                    "error": agent_result.error
                                })
                    except Exception as e:
                        self.module_logger.error(f"❌ 任务{i+1}结果转换失败: {e}")
                        failed_results.append({
                            "task": task_descriptions[i] if i < len(task_descriptions) else f"Task {i+1}",
                            "error": f"结果转换失败: {str(e)}"
                        })
            
            # 聚合结果
            if successful_results:
                # 合并所有成功的结果
                combined_answer = []
                combined_knowledge = []
                combined_reasoning = []
                combined_citations = []
                total_confidence = 0.0
                
                for result in successful_results:
                    if isinstance(result.data, dict):
                        if result.data.get('answer'):
                            combined_answer.append(result.data['answer'])
                        if result.data.get('knowledge'):
                            combined_knowledge.extend(result.data['knowledge'] if isinstance(result.data['knowledge'], list) else [result.data['knowledge']])
                        if result.data.get('reasoning'):
                            combined_reasoning.append(result.data['reasoning'])
                        if result.data.get('citations'):
                            combined_citations.extend(result.data['citations'] if isinstance(result.data['citations'], list) else [result.data['citations']])
                    elif isinstance(result.data, str) and result.data:
                        combined_answer.append(result.data)
                    
                    total_confidence += result.confidence
                
                # 计算平均置信度
                avg_confidence = total_confidence / len(successful_results) if successful_results else 0.0
                
                # 构建最终结果
                final_answer = " | ".join(combined_answer) if combined_answer else ""
                final_knowledge = list(set(combined_knowledge)) if combined_knowledge else []
                final_reasoning = "\n\n".join(combined_reasoning) if combined_reasoning else None
                final_citations = list(set(combined_citations)) if combined_citations else []
                
                self.module_logger.info(f"✅ 混合计划执行成功: {len(successful_results)}/{len(tasks)}个任务成功")
                if failed_results:
                    self.module_logger.warning(f"⚠️ {len(failed_results)}个任务失败: {[r['task'] for r in failed_results]}")
                
                return AgentResult(
                    success=True,
                    data={
                        "answer": final_answer,
                        "knowledge": final_knowledge,
                        "reasoning": final_reasoning,
                        "citations": final_citations,
                        "task_summary": {
                            "total": len(tasks),
                            "successful": len(successful_results),
                            "failed": len(failed_results),
                            "failed_tasks": failed_results
                        }
                    },
                    confidence=avg_confidence,
                    processing_time=time.time() - start_time,
                    metadata={
                        "method": "hybrid_plan",
                        "tasks_executed": len(tasks),
                        "tasks_successful": len(successful_results),
                        "tasks_failed": len(failed_results)
                    }
                )
            else:
                # 所有任务都失败
                self.module_logger.error(f"❌ 混合计划所有任务都失败: {len(failed_results)}个任务")
                return AgentResult(
                    success=False,
                    data={
                        "failed_tasks": failed_results
                    },
                    error=f"所有{len(tasks)}个任务都执行失败",
                    confidence=0.0,
                    processing_time=time.time() - start_time,
                    metadata={
                        "method": "hybrid_plan",
                        "tasks_executed": len(tasks),
                        "tasks_successful": 0,
                        "tasks_failed": len(failed_results)
                    }
                )
                
        except Exception as e:
            self.module_logger.error(f"❌ 混合计划执行失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=f"混合计划执行失败: {str(e)}",
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _observe_and_adjust(self, result: AgentResult) -> AgentResult:
        """🚀 步骤7.2：监控和动态调整
        
        功能：
        1. 执行状态监控
        2. 动态策略切换
        3. 资源重新分配
        4. 超时处理
        5. 错误恢复
        6. 性能优化
        
        Args:
            result: 执行结果
            
        Returns:
            AgentResult: 调整后的结果
        """
        # 1. 执行状态监控
        execution_state = self._monitor_execution_state(result)
        
        # 2. 检查是否需要动态调整
        if execution_state.get('needs_adjustment', False):
            adjustment_reason = execution_state.get('adjustment_reason', 'N/A')
            self.module_logger.info("=" * 60)
            self.module_logger.info(f"🔄 [Observe阶段] 检测到需要动态调整: {adjustment_reason}")
            
            # 2.1 错误恢复
            if not result.success:
                self.module_logger.info(f"   🔧 [Observe阶段] 尝试错误恢复...")
                adjusted_result = await self._attempt_error_recovery(result, execution_state)
                if adjusted_result and adjusted_result.success:
                    self.module_logger.info(f"   ✅ [Observe阶段] 错误恢复成功")
                    result = adjusted_result
                else:
                    self.module_logger.warning(f"   ⚠️ [Observe阶段] 错误恢复失败")
            
            # 2.2 置信度提升
            elif result.confidence < 0.5:
                self.module_logger.info(f"   🔧 [Observe阶段] 尝试置信度提升...")
                adjusted_result = await self._attempt_confidence_boost(result, execution_state)
                if adjusted_result and adjusted_result.confidence > result.confidence:
                    self.module_logger.info(f"   ✅ [Observe阶段] 置信度提升: {result.confidence:.2f} -> {adjusted_result.confidence:.2f}")
                    result = adjusted_result
                else:
                    self.module_logger.info(f"   ⚠️ [Observe阶段] 置信度提升未生效")
            
            # 2.3 性能优化（如果执行时间过长）
            elif result.processing_time > 30.0:  # 超过30秒
                self.module_logger.warning(f"   ⚠️ [Observe阶段] 检测到性能问题: 执行时间{result.processing_time:.2f}秒 > 阈值30.00秒")
                self._record_performance_issue(result, execution_state)
                
                # 🚀 改进2：真正执行性能优化调整
                adjusted_result = await self._attempt_performance_optimization(result, execution_state)
                if adjusted_result:
                    self.module_logger.info(f"   ✅ [Observe阶段] 性能优化调整完成")
                    result = adjusted_result
                else:
                    self.module_logger.info(f"   ⚠️ [Observe阶段] 性能优化调整未生效（可能已是最优路径或优化后未改善）")
            
            self.module_logger.info("=" * 60)
        
        # 3. 记录执行历史
        self._record_execution_history(result, execution_state)
        
        # 4. 更新资源状态
        self._update_resource_states(execution_state)
        
        # 5. 🚀 步骤7.3：记录性能指标
        self._record_performance_metrics(result, execution_state)
        
        # 6. 记录执行统计
        self.module_logger.info(f"✅ 执行完成: success={result.success}, confidence={result.confidence:.2f}, time={result.processing_time:.2f}s")
        
        return result
    
    def _monitor_execution_state(self, result: AgentResult) -> Dict[str, Any]:
        """🚀 步骤7.2：监控执行状态
        
        Args:
            result: 执行结果
            
        Returns:
            执行状态字典
        """
        state = {
            'success': result.success,
            'confidence': result.confidence,
            'processing_time': result.processing_time,
            'has_data': result.data is not None,
            'has_error': result.error is not None,
            'needs_adjustment': False,
            'adjustment_reason': None,
            'system_load': self._get_system_load(),
            'timestamp': time.time()
        }
        
        # 判断是否需要调整
        if not result.success:
            state['needs_adjustment'] = True
            state['adjustment_reason'] = 'execution_failed'
        elif result.confidence < 0.5:
            state['needs_adjustment'] = True
            state['adjustment_reason'] = 'low_confidence'
        elif result.processing_time > 30.0:
            state['needs_adjustment'] = True
            state['adjustment_reason'] = 'performance_issue'
        elif not result.data:
            state['needs_adjustment'] = True
            state['adjustment_reason'] = 'empty_data'
        
        return state
    
    async def _attempt_error_recovery(self, result: AgentResult, execution_state: Dict[str, Any]) -> Optional[AgentResult]:
        """🚀 步骤7.2：尝试错误恢复
        
        Args:
            result: 失败的执行结果
            execution_state: 执行状态
            
        Returns:
            恢复后的结果，如果恢复失败返回None
        """
        if not self._current_execution_context:
            return None
        
        query = self._current_execution_context.get('query')
        if not query:
            return None
        
        self.module_logger.info("🔄 尝试错误恢复：切换到保守路径")
        
        # 策略1：切换到保守路径（传统流程）
        if self.is_resource_available('traditional') and self.traditional:
            try:
                from src.unified_research_system import ResearchRequest
                request = ResearchRequest(query=query)
                recovery_result = await self.traditional._execute_research_internal(request)
                
                # 转换为AgentResult
                if hasattr(recovery_result, 'success') and recovery_result.success:
                    return AgentResult(
                        success=True,
                        data={'answer': getattr(recovery_result, 'answer', None)},
                        confidence=getattr(recovery_result, 'confidence', 0.6),
                        processing_time=getattr(recovery_result, 'execution_time', 0.0)
                    )
            except Exception as e:
                self.module_logger.debug(f"保守路径恢复失败: {e}")
        
        # 策略2：如果保守路径也失败，尝试简化查询
        self.module_logger.info("🔄 尝试错误恢复：简化查询")
        try:
            # 提取查询的关键词
            query_words = query.split()
            simplified_query = ' '.join(query_words[:10])  # 只保留前10个词
            
            if self.is_resource_available('standard_loop') and self.standard_loop:
                from src.unified_research_system import ResearchRequest
                request = ResearchRequest(query=simplified_query)
                recovery_result = await self.standard_loop._execute_research_agent_loop(request, time.time())
                
                if hasattr(recovery_result, 'success') and recovery_result.success:
                    return AgentResult(
                        success=True,
                        data={'answer': getattr(recovery_result, 'answer', None)},
                        confidence=getattr(recovery_result, 'confidence', 0.5) * 0.9,  # 降低置信度
                        processing_time=getattr(recovery_result, 'execution_time', 0.0)
                    )
        except Exception as e:
            self.module_logger.debug(f"简化查询恢复失败: {e}")
        
        return None
    
    async def _attempt_confidence_boost(self, result: AgentResult, execution_state: Dict[str, Any]) -> Optional[AgentResult]:
        """🚀 步骤7.2：尝试提升置信度
        
        Args:
            result: 低置信度的执行结果
            execution_state: 执行状态
            
        Returns:
            提升后的结果，如果提升失败返回None
        """
        # 如果结果数据为空，无法提升
        if not result.data:
            return None
        
        # 策略：使用另一个执行路径验证结果
        if not self._current_execution_context:
            return result  # 无法验证，返回原结果
        
        query = self._current_execution_context.get('query')
        if not query:
            return result
        
        # 如果当前使用的是标准循环，尝试用传统流程验证
        current_path = self._current_execution_context.get('execution_path', 'unknown')
        
        if current_path == 'standard_loop' and self.is_resource_available('traditional'):
            try:
                from src.unified_research_system import ResearchRequest
                request = ResearchRequest(query=query)
                verification_result = await self.traditional._execute_research_internal(request)
                
                # 如果验证结果与当前结果一致，提升置信度
                if hasattr(verification_result, 'answer'):
                    current_answer = result.data.get('answer', '') if isinstance(result.data, dict) else str(result.data)
                    verification_answer = getattr(verification_result, 'answer', '')
                    
                    if current_answer and verification_answer:
                        # 简单的一致性检查
                        if current_answer.lower() in verification_answer.lower() or verification_answer.lower() in current_answer.lower():
                            # 结果一致，提升置信度
                            boosted_confidence = min(0.9, result.confidence + 0.2)
                            result.confidence = boosted_confidence
                            self.module_logger.info(f"✅ 置信度提升: {result.confidence:.2f} (验证结果一致)")
                            return result
            except Exception as e:
                self.module_logger.debug(f"置信度提升失败: {e}")
        
        return result
    
    async def _attempt_performance_optimization(self, result: AgentResult, execution_state: Dict[str, Any]) -> Optional[AgentResult]:
        """🚀 改进2：尝试性能优化调整
        
        当检测到性能问题时，尝试切换到更快的执行路径或优化执行策略。
        
        Args:
            result: 执行结果
            execution_state: 执行状态
            
        Returns:
            优化后的结果，如果优化失败或不需要优化返回None
        """
        if not self._current_execution_context:
            return None
        
        current_path = self._current_execution_context.get('execution_path', 'unknown')
        query = self._current_execution_context.get('query', '')
        
        if not query:
            return None
        
        self.module_logger.info(f"🔄 [Observe阶段] 尝试性能优化: 当前路径={current_path}, 执行时间={result.processing_time:.2f}秒")
        
        # 策略1: 如果当前使用MAS且执行时间过长，尝试切换到标准循环
        if current_path == 'mas' and result.processing_time > 60.0:  # 超过60秒
            if self.is_resource_available('standard_loop') and self.standard_loop:
                self.module_logger.info(f"   📌 优化策略: 从MAS切换到Standard Loop（MAS执行时间过长）")
                try:
                    from src.unified_research_system import ResearchRequest
                    request = ResearchRequest(query=query)
                    optimized_result = await self.standard_loop._execute_research_agent_loop(request, time.time())
                    
                    if hasattr(optimized_result, 'success') and optimized_result.success:
                        optimized_time = getattr(optimized_result, 'execution_time', 0.0)
                        if optimized_time < result.processing_time * 0.8:  # 优化后时间减少20%以上
                            self.module_logger.info(f"   ✅ 性能优化成功: {result.processing_time:.2f}秒 -> {optimized_time:.2f}秒 (减少{((result.processing_time-optimized_time)/result.processing_time*100):.1f}%)")
                            return AgentResult(
                                success=True,
                                data={'answer': getattr(optimized_result, 'answer', None)},
                                confidence=getattr(optimized_result, 'confidence', result.confidence),
                                processing_time=optimized_time,
                                metadata={'optimized': True, 'original_path': current_path, 'new_path': 'standard_loop'}
                            )
                        else:
                            self.module_logger.info(f"   ⚠️ 性能优化未改善: 优化后时间{optimized_time:.2f}秒，未明显减少")
                except Exception as e:
                    self.module_logger.debug(f"性能优化失败: {e}")
        
        # 策略2: 如果当前使用标准循环且执行时间过长，尝试简化查询
        elif current_path == 'standard_loop' and result.processing_time > 60.0:
            self.module_logger.info(f"   📌 优化策略: 简化查询（标准循环执行时间过长）")
            try:
                # 提取查询的关键词，简化查询
                query_words = query.split()
                simplified_query = ' '.join(query_words[:15])  # 只保留前15个词
                
                if self.is_resource_available('standard_loop') and self.standard_loop:
                    from src.unified_research_system import ResearchRequest
                    request = ResearchRequest(query=simplified_query)
                    optimized_result = await self.standard_loop._execute_research_agent_loop(request, time.time())
                    
                    if hasattr(optimized_result, 'success') and optimized_result.success:
                        optimized_time = getattr(optimized_result, 'execution_time', 0.0)
                        if optimized_time < result.processing_time * 0.8:
                            self.module_logger.info(f"   ✅ 性能优化成功: {result.processing_time:.2f}秒 -> {optimized_time:.2f}秒 (减少{((result.processing_time-optimized_time)/result.processing_time*100):.1f}%)")
                            return AgentResult(
                                success=True,
                                data={'answer': getattr(optimized_result, 'answer', None)},
                                confidence=getattr(optimized_result, 'confidence', result.confidence) * 0.95,  # 稍微降低置信度
                                processing_time=optimized_time,
                                metadata={'optimized': True, 'original_path': current_path, 'query_simplified': True}
                            )
            except Exception as e:
                self.module_logger.debug(f"性能优化失败: {e}")
        
        # 策略3: 记录性能问题到历史，供未来参考
        self.module_logger.info(f"   📝 记录性能问题到历史，供未来参考")
        return None  # 当前无法优化，但已记录问题
    
    def _record_performance_issue(self, result: AgentResult, execution_state: Dict[str, Any]):
        """🚀 步骤7.2：记录性能问题
        
        Args:
            result: 执行结果
            execution_state: 执行状态
        """
        performance_issue = {
            'query': self._current_execution_context.get('query', '') if self._current_execution_context else '',
            'execution_path': self._current_execution_context.get('execution_path', 'unknown') if self._current_execution_context else 'unknown',
            'processing_time': result.processing_time,
            'system_load': execution_state.get('system_load', 0.0),
            'timestamp': time.time()
        }
        
        # 记录到执行历史
        if len(self._execution_history) >= self._max_history_size:
            self._execution_history.pop(0)  # 移除最旧的记录
        
        self._execution_history.append({
            'type': 'performance_issue',
            'data': performance_issue
        })
        
        # 🚀 改进2：记录性能告警
        if result.processing_time > 10.0:  # 超过10秒阈值
            self.module_logger.warning(f"⚠️ [Observe阶段] [性能告警] 平均响应时间过长: {result.processing_time:.2f}秒 (阈值: 10.00秒)")
    
    def _record_execution_history(self, result: AgentResult, execution_state: Dict[str, Any]):
        """🚀 步骤7.2：记录执行历史
        
        Args:
            result: 执行结果
            execution_state: 执行状态
        """
        history_entry = {
            'query': self._current_execution_context.get('query', '') if self._current_execution_context else '',
            'execution_path': self._current_execution_context.get('execution_path', 'unknown') if self._current_execution_context else 'unknown',
            'success': result.success,
            'confidence': result.confidence,
            'processing_time': result.processing_time,
            'system_load': execution_state.get('system_load', 0.0),
            'timestamp': time.time()
        }
        
        # 限制历史记录大小
        if len(self._execution_history) >= self._max_history_size:
            self._execution_history.pop(0)  # 移除最旧的记录
        
        self._execution_history.append({
            'type': 'execution',
            'data': history_entry
        })
    
    def _update_resource_states(self, execution_state: Dict[str, Any]):
        """🚀 步骤7.2：更新资源状态
        
        Args:
            execution_state: 执行状态
        """
        # 根据执行状态更新资源健康状态
        system_load = execution_state.get('system_load', 0.0)
        
        # 如果系统负载过高，标记资源为不健康
        if system_load > 90.0:
            for resource_name in self._resource_states:
                if resource_name != 'tools':  # 工具不受负载影响
                    self._resource_states[resource_name]['healthy'] = False
                    self.module_logger.warning(f"⚠️ 资源 {resource_name} 标记为不健康（系统负载: {system_load:.1f}%）")
        
        # 如果系统负载恢复正常，恢复资源健康状态
        elif system_load < 70.0:
            for resource_name in self._resource_states:
                if resource_name != 'tools':
                    if not self._resource_states[resource_name].get('healthy', True):
                        self._resource_states[resource_name]['healthy'] = True
                        self.module_logger.info(f"✅ 资源 {resource_name} 恢复健康（系统负载: {system_load:.1f}%）")
    
    def _record_ml_model_usage(self, model_name: str, execution_time: float):
        """🚀 步骤7.3：记录ML模型使用情况
        
        Args:
            model_name: 模型名称
            execution_time: 执行时间（秒）
        """
        if model_name in self._performance_metrics['ml_model_usage']:
            self._performance_metrics['ml_model_usage'][model_name] += 1
        
        # 记录到性能监控器
        if self._performance_monitor:
            try:
                self._performance_monitor.record_prediction(
                    model_name=model_name,
                    input_data=None,  # 不记录输入数据（可能很大）
                    prediction={'execution_time': execution_time},
                    execution_time=execution_time
                )
            except Exception as e:
                self.module_logger.debug(f"记录ML模型使用情况失败: {e}")
    
    def _record_performance_metrics(self, result: AgentResult, execution_state: Dict[str, Any]):
        """🚀 步骤7.3：记录性能指标
        
        Args:
            result: 执行结果
            execution_state: 执行状态
        """
        # 更新基本指标
        self._performance_metrics['total_queries'] += 1
        
        if result.success:
            self._performance_metrics['successful_queries'] += 1
        else:
            self._performance_metrics['failed_queries'] += 1
        
        # 更新响应时间
        self._performance_metrics['total_response_time'] += result.processing_time
        self._performance_metrics['avg_response_time'] = (
            self._performance_metrics['total_response_time'] / 
            self._performance_metrics['total_queries']
        )
        
        # 更新置信度
        total_confidence = self._performance_metrics.get('total_confidence', 0.0)
        total_confidence += result.confidence
        self._performance_metrics['total_confidence'] = total_confidence
        self._performance_metrics['avg_confidence'] = (
            total_confidence / self._performance_metrics['total_queries']
        )
        
        # 更新错误率
        self._performance_metrics['error_rate'] = (
            self._performance_metrics['failed_queries'] / 
            self._performance_metrics['total_queries']
        )
        
        # 更新执行路径使用频率
        execution_path = self._current_execution_context.get('execution_path', 'unknown') if self._current_execution_context else 'unknown'
        if execution_path in self._performance_metrics['path_usage']:
            self._performance_metrics['path_usage'][execution_path] += 1
        
        # 🚀 步骤7.3：性能告警
        self._check_performance_alerts(result, execution_state)
    
    def _check_performance_alerts(self, result: AgentResult, execution_state: Dict[str, Any]):
        """🚀 步骤7.3：检查性能告警
        
        Args:
            result: 执行结果
            execution_state: 执行状态
        """
        # 告警阈值
        ALERT_THRESHOLDS = {
            'error_rate': 0.2,  # 错误率超过20%
            'avg_response_time': 10.0,  # 平均响应时间超过10秒
            'system_load': 90.0,  # 系统负载超过90%
            'low_confidence_rate': 0.3  # 低置信度（<0.5）比例超过30%
        }
        
        # 检查错误率
        if self._performance_metrics['error_rate'] > ALERT_THRESHOLDS['error_rate']:
            self.module_logger.warning(
                f"⚠️ [性能告警] 错误率过高: {self._performance_metrics['error_rate']:.2%} "
                f"(阈值: {ALERT_THRESHOLDS['error_rate']:.2%})"
            )
        
        # 检查平均响应时间
        if self._performance_metrics['avg_response_time'] > ALERT_THRESHOLDS['avg_response_time']:
            self.module_logger.warning(
                f"⚠️ [性能告警] 平均响应时间过长: {self._performance_metrics['avg_response_time']:.2f}秒 "
                f"(阈值: {ALERT_THRESHOLDS['avg_response_time']:.2f}秒)"
            )
        
        # 检查系统负载
        system_load = execution_state.get('system_load', 0.0)
        if system_load > ALERT_THRESHOLDS['system_load']:
            self.module_logger.warning(
                f"⚠️ [性能告警] 系统负载过高: {system_load:.1f}% "
                f"(阈值: {ALERT_THRESHOLDS['system_load']:.1f}%)"
            )
        
        # 检查低置信度比例（需要计算最近N次查询的低置信度比例）
        if len(self._execution_history) >= 10:
            recent_low_confidence = sum(
                1 for entry in self._execution_history[-10:]
                if entry.get('type') == 'execution' and 
                entry.get('data', {}).get('confidence', 1.0) < 0.5
            )
            low_confidence_rate = recent_low_confidence / 10.0
            if low_confidence_rate > ALERT_THRESHOLDS['low_confidence_rate']:
                self.module_logger.warning(
                    f"⚠️ [性能告警] 低置信度比例过高: {low_confidence_rate:.2%} "
                    f"(阈值: {ALERT_THRESHOLDS['low_confidence_rate']:.2%})"
                )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """🚀 步骤7.3：获取性能分析报告
        
        Returns:
            性能报告字典
        """
        report = {
            'summary': {
                'total_queries': self._performance_metrics['total_queries'],
                'successful_queries': self._performance_metrics['successful_queries'],
                'failed_queries': self._performance_metrics['failed_queries'],
                'error_rate': self._performance_metrics['error_rate'],
                'avg_response_time': self._performance_metrics['avg_response_time'],
                'avg_confidence': self._performance_metrics['avg_confidence']
            },
            'path_usage': self._performance_metrics['path_usage'],
            'ml_model_usage': self._performance_metrics['ml_model_usage'],
            'resource_states': {
                name: {
                    'registered': state.get('registered', False),
                    'healthy': state.get('healthy', False)
                }
                for name, state in self._resource_states.items()
            },
            'system_load': self._get_system_load()
        }
        
        return report

