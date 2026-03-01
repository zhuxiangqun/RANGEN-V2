#!/usr/bin/env python3
"""
专家Agent基类
所有专家Agent继承此类，实现标准Agent循环
"""

import time
import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

from .base_agent import BaseAgent, AgentResult, AgentConfig
from .react_agent import Action
from src.visualization.orchestration_tracker import get_orchestration_tracker

logger = logging.getLogger(__name__)


class ExpertAgent(BaseAgent):
    """专家Agent基类 - 所有专家Agent继承此类
    
    专家Agent是符合标准Agent定义的Agent，有自己的Agent循环。
    它们使用对应的Service来执行具体的任务。
    """
    
    def __init__(self, agent_id: str, domain_expertise: str, 
                 capability_level: float = 0.9, 
                 collaboration_style: str = "supportive"):
        """初始化专家Agent
        
        Args:
            agent_id: Agent ID
            domain_expertise: 专业领域
            capability_level: 能力水平（0-1）
            collaboration_style: 协作风格（supportive, analytical, synthesizing等）
        """
        config = AgentConfig(
            agent_id=agent_id,
            agent_type="expert_agent"
        )
        super().__init__(
            agent_id=agent_id,
            capabilities=[domain_expertise, "collaboration"],
            config=config
        )
        
        self.domain_expertise = domain_expertise
        self.capability_level = capability_level
        self.collaboration_style = collaboration_style
        
        # 对应的Service（封装原有功能，作为回退方案）
        self.service = None
        
        # 🚀 方案1：工具注册表（优先使用Tools）
        self.tool_registry = None
        try:
            from .tools.tool_registry import get_tool_registry
            self.tool_registry = get_tool_registry()
            logger.debug(f"✅ 专家Agent工具注册表初始化成功: {agent_id}")
        except Exception as e:
            logger.debug(f"⚠️ 专家Agent工具注册表初始化失败: {e}，将使用Service作为回退")
        
        # Agent状态
        self.observations: List[Dict[str, Any]] = []
        self.thoughts: List[str] = []
        self.actions: List[Action] = []
        
        # LLM客户端（用于思考）
        self.llm_client = None
        self._init_llm_client()
        
        logger.info(f"✅ 专家Agent初始化完成: {agent_id}, 领域={domain_expertise}, 能力水平={capability_level}")
    
    def _init_llm_client(self):
        """初始化LLM客户端"""
        try:
            from src.core.llm_integration import LLMIntegration
            from src.utils.unified_centers import get_unified_config_center
            
            config_center = get_unified_config_center()
            llm_config = {
                'llm_provider': config_center.get_env_config('llm', 'LLM_PROVIDER', 'deepseek'),
                'api_key': config_center.get_env_config('llm', 'DEEPSEEK_API_KEY', ''),
                'model': config_center.get_env_config('llm', 'FAST_MODEL', 'deepseek-chat'),
                'base_url': config_center.get_env_config('llm', 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
            }
            
            self.llm_client = LLMIntegration(llm_config)
            logger.info("✅ LLM客户端初始化成功（用于思考阶段）")
        except Exception as e:
            logger.warning(f"⚠️ LLM客户端初始化失败: {e}，思考功能可能受限")
            self.llm_client = None
    
    @abstractmethod
    def _get_service(self):
        """获取对应的Service - 子类必须实现"""
        raise NotImplementedError
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行任务 - 专家Agent循环
        
        Args:
            context: 上下文，包含query、dependencies等
            
        Returns:
            AgentResult: 执行结果
        """
        start_time = time.time()
        
        # 🎯 编排追踪：Agent 开始执行
        tracker = getattr(self, '_orchestration_tracker', None)
        agent_start_event_id = None
        if tracker:
            try:
                agent_start_event_id = tracker.track_agent_start(
                    self.agent_id or "expert_agent",
                    "expert_agent",
                    context
                )
                # 保存事件ID供子事件使用
                self._current_agent_event_id = agent_start_event_id
                logger.debug(f"✅ [Expert Agent] 编排事件已记录: {self.agent_id}, 事件ID: {agent_start_event_id}, 追踪器事件总数: {len(tracker.events)}")
            except Exception as e:
                logger.warning(f"⚠️ [Expert Agent] 记录编排事件失败: {e}", exc_info=True)
        else:
            logger.debug(f"⚠️ [Expert Agent] 没有编排追踪器，无法记录事件: {self.agent_id}")
        
        try:
            query = context.get("query", "")
            dependencies = context.get("dependencies", {})
            
            # 重置状态
            self.observations = []
            self.thoughts = []
            self.actions = []
            
            # 🚀 P0修复：记录查询内容（用于诊断）
            if query:
                logger.info(f"🧠 专家Agent开始执行: {self.agent_id}, 查询='{query[:100]}...' (长度={len(query)})")
            else:
                logger.warning(f"⚠️ [查询传递] 专家Agent开始执行: {self.agent_id}, 查询为空！context.keys={list(context.keys()) if isinstance(context, dict) else 'N/A'}")
            
            # Agent循环
            iteration = 0
            max_iterations = 10
            task_complete = False
            
            while iteration < max_iterations and not task_complete:
                # 1. 思考
                thought = await self._think(query, dependencies, self.observations)
                self.thoughts.append(thought)
                
                # 2. 规划行动
                action = await self._plan_action(thought, query, dependencies)
                if not action or not action.tool_name:
                    break
                
                self.actions.append(action)
                
                # 3. 执行（调用Service或工具）
                observation = await self._execute_action(action, dependencies)
                self.observations.append(observation)
                
                # 4. 判断是否完成
                task_complete = self._is_task_complete(observation)
                
                iteration += 1
            
            # 5. 生成结果
            result = self._generate_result(self.observations, self.thoughts, self.actions)
            result.processing_time = time.time() - start_time
            
            # 🎯 编排追踪：Agent 执行结束（成功）
            if tracker:
                tracker.track_agent_end(
                    self.agent_id or "expert_agent",
                    result.to_dict() if hasattr(result, 'to_dict') else {"success": True, "data": result.data},
                    None
                )
            
            logger.info(f"✅ 专家Agent执行完成: {self.agent_id}, 耗时={result.processing_time:.2f}秒")
            return result
            
        except Exception as e:
            logger.error(f"❌ 专家Agent执行失败: {self.agent_id}, 错误={e}")
            error_result = AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
            
            # 🎯 编排追踪：Agent 执行结束（错误）
            if tracker:
                tracker.track_agent_end(
                    self.agent_id or "expert_agent",
                    error_result.to_dict() if hasattr(error_result, 'to_dict') else {"success": False, "error": str(e)},
                    str(e)
                )
            
            return error_result
    
    async def _think(self, query: str, dependencies: Dict, observations: List[Dict]) -> str:
        """思考阶段 - 分析任务和上下文"""
        # 🎯 编排追踪：Agent 思考开始
        tracker = getattr(self, '_orchestration_tracker', None)
        parent_event_id = getattr(self, '_current_agent_event_id', None)
        
        if not self.llm_client:
            thought = f"分析任务: {query}"
            # 🎯 编排追踪：Agent 思考完成（无LLM）
            if tracker:
                tracker.track_agent_think(
                    self.agent_id or "expert_agent",
                    thought,
                    parent_event_id
                )
            return thought
        
        prompt = f"""
        你是一个{self.domain_expertise}专家，需要分析以下任务：
        
        任务: {query}
        依赖信息: {dependencies}
        历史观察: {observations}
        
        请分析：
        1. 任务的核心需求是什么？
        2. 如何利用依赖信息？
        3. 需要执行什么操作？
        
        思考过程:
        """
        
        try:
            # 🚀 修复：检查_call_llm是否是异步方法
            import inspect
            if inspect.iscoroutinefunction(self.llm_client._call_llm):
                response = await self.llm_client._call_llm(prompt)
            else:
                # 如果是同步方法，在线程池中执行
                import asyncio
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, lambda: self.llm_client._call_llm(prompt))
            
            # 🎯 编排追踪：Agent 思考完成
            if tracker:
                tracker.track_agent_think(
                    self.agent_id or "expert_agent",
                    response,
                    parent_event_id
                )
            
            return response
        except Exception as e:
            logger.warning(f"思考阶段失败: {e}", exc_info=True)
            error_thought = f"分析任务: {query}"
            
            # 🎯 编排追踪：Agent 思考失败
            if tracker:
                tracker.track_agent_think(
                    self.agent_id or "expert_agent",
                    error_thought,
                    parent_event_id
                )
            
            return error_thought
    
    async def _plan_action(self, thought: str, query: str, dependencies: Dict) -> Optional[Action]:
        """规划行动阶段 - 决定执行什么操作"""
        # 🎯 编排追踪：Agent 规划开始
        tracker = getattr(self, '_orchestration_tracker', None)
        parent_event_id = getattr(self, '_current_agent_event_id', None)
        
        # 🚀 方案1：优先使用Tools，如果不可用则使用Service
        # 根据agent_id映射到对应的工具名称
        tool_name_mapping = {
            "knowledge_retrieval_expert": "knowledge_retrieval",
            "reasoning_expert": "reasoning",
            "answer_generation_expert": "answer_generation",
            "citation_expert": "citation"
        }
        
        # 尝试使用Tools
        if self.tool_registry:
            tool_name = tool_name_mapping.get(self.agent_id)
            if tool_name and self.tool_registry.get_tool(tool_name):
                logger.debug(f"🚀 [ExpertAgent] {self.agent_id} 使用工具: {tool_name}")
                # 🚀 根据工具类型准备不同的参数
                if tool_name == "citation":
                    # CitationTool需要content和sources
                    answer = dependencies.get("answer", "") or query
                    knowledge = dependencies.get("knowledge", []) or dependencies.get("sources", [])
                    return Action(
                        tool_name=tool_name,
                        params={
                            "content": answer,
                            "sources": knowledge,
                            "query": query,
                            "context": dependencies
                        },
                        reasoning=thought
                    )
                elif tool_name == "answer_generation":
                    # AnswerGenerationTool需要query, knowledge_data, reasoning_data
                    action = Action(
                        tool_name=tool_name,
                        params={
                            "query": query,
                            "knowledge_data": dependencies.get("knowledge_data", []) or dependencies.get("knowledge", []),
                            "reasoning_data": dependencies.get("reasoning_data", {}) or dependencies.get("reasoning", {}),
                            "context": dependencies
                        },
                        reasoning=thought
                    )
                    
                    # 🎯 编排追踪：Agent 规划完成
                    if tracker:
                        tracker.track_agent_plan(
                            self.agent_id or "expert_agent",
                            {"action": action.to_dict()},
                            parent_event_id
                        )
                    
                    return action
                else:
                    # 其他工具（knowledge_retrieval, reasoning）使用标准参数
                    action = Action(
                        tool_name=tool_name,
                        params={
                            "query": query,
                            "context": dependencies
                        },
                        reasoning=thought
                    )
                    
                    # 🎯 编排追踪：Agent 规划完成
                    if tracker:
                        tracker.track_agent_plan(
                            self.agent_id or "expert_agent",
                            {"action": action.to_dict()},
                            parent_event_id
                        )
                    
                    return action
        
        # 回退到Service
        logger.debug(f"🔄 [ExpertAgent] {self.agent_id} 回退到Service")
        service_action = Action(
            tool_name="service_call",
            params={
                "query": query,
                **dependencies
            },
            reasoning=thought
        )
        
        # 🎯 编排追踪：Agent 规划完成（Service回退）
        if tracker:
            tracker.track_agent_plan(
                self.agent_id or "expert_agent",
                {"action": service_action.to_dict(), "fallback": "service"},
                parent_event_id
            )
        
        return service_action
    
    async def _execute_action(self, action: Action, dependencies: Dict) -> Dict[str, Any]:
        """执行行动 - 🚀 方案1：优先使用Tools，如果不可用则调用Service"""
        # 🚀 方案1：如果action.tool_name不是"service_call"，尝试使用Tools
        if action.tool_name != "service_call" and self.tool_registry:
            tool = self.tool_registry.get_tool(action.tool_name)
            if tool:
                try:
                    logger.info(f"🚀 [ExpertAgent] {self.agent_id} 使用工具: {action.tool_name}")
                    
                    # 🚀 P0修复：对于答案生成工具，需要传递dependencies
                    # 确保dependencies能够正确传递到工具中
                    tool_params = dict(action.params)  # 复制参数，避免修改原始参数
                    
                    # 🚀 P0修复：如果工具是answer_generation，且dependencies不为空，将其添加到context中
                    if action.tool_name == "answer_generation" and dependencies:
                        # 确保context存在
                        if "context" not in tool_params:
                            tool_params["context"] = {}
                        elif not isinstance(tool_params["context"], dict):
                            tool_params["context"] = {}
                        
                        # 将dependencies添加到context中
                        tool_params["context"]["dependencies"] = dependencies
                        logger.info(f"🔍 [ExpertAgent] {self.agent_id} 为答案生成工具添加dependencies: keys={list(dependencies.keys())}")
                    
                    # 调用工具
                    tool_result = await tool.call(**tool_params)
                    # 将ToolResult转换为观察结果格式（兼容不同类型的返回值）
                    success = getattr(tool_result, "success", True)
                    error = getattr(tool_result, "error", None)
                    confidence = getattr(tool_result, "confidence", 0.7)
                    execution_time = getattr(tool_result, "execution_time", 0.0)

                    data = None
                    if hasattr(tool_result, "data"):
                        data = getattr(tool_result, "data")
                    elif isinstance(tool_result, dict):
                        data = tool_result.get("data", tool_result)
                    elif hasattr(tool_result, "output"):
                        data = getattr(tool_result, "output")
                    else:
                        data = tool_result

                    return {
                        "success": success,
                        "data": data,
                        "error": error,
                        "confidence": confidence,
                        "tool_name": action.tool_name,
                        "execution_time": execution_time
                    }
                except Exception as e:
                    logger.warning(f"⚠️ [ExpertAgent] {self.agent_id} 工具调用失败: {e}，回退到Service", exc_info=True)
                    # 继续执行Service回退逻辑
        
        # 回退到Service（原有逻辑）
        if not self.service:
            self.service = self._get_service()
        
        # 🚀 P0修复：准备上下文，确保query不被覆盖
        # 优先使用action.params中的query，如果为空则使用dependencies中的query
        query_from_params = action.params.get("query", "")
        query_from_deps = dependencies.get("query", "")
        final_query = query_from_params or query_from_deps
        
        # 记录查询传递日志（用于诊断）
        if not final_query:
            logger.warning(f"⚠️ [查询传递] ExpertAgent._execute_action: query为空！action.params.query={query_from_params[:50] if query_from_params else 'None'}, dependencies.query={query_from_deps[:50] if query_from_deps else 'None'}")
        else:
            logger.debug(f"🔍 [查询传递] ExpertAgent._execute_action: query={final_query[:100]}")
        
        # 准备上下文，确保query不被覆盖
        # 🚀 P0修复：dependencies应该作为独立的字典传递，而不是展开
        # 因为AnswerGenerationService等Service期望从context['dependencies']获取依赖结果
        # 但是，为了向后兼容，我们也保留展开dependencies的方式（如果Service需要直接访问）
        service_context = {
            **action.params,  # 先展开action.params（包含query）
            "query": final_query,  # 🚀 P0修复：最后设置query，确保不被覆盖
            "dependencies": dependencies  # 🚀 P0修复：将dependencies作为独立字典传递，而不是展开
        }
        
        # 🚀 P0修复：添加诊断日志，记录dependencies的内容
        if dependencies and self.agent_id == "answer_generation_expert":
            logger.info(f"🔍 [ExpertAgent] {self.agent_id} 准备service_context，dependencies keys: {list(dependencies.keys())}")
            for dep_key, dep_val in dependencies.items():
                logger.info(f"   - {dep_key}: type={type(dep_val)}")
                if hasattr(dep_val, 'data'):
                    data = dep_val.data
                    if isinstance(data, dict):
                        if 'final_answer' in data:
                            logger.info(f"      ✅ {dep_key}.data包含final_answer: {str(data['final_answer'])[:100]}")
                        if 'answer' in data:
                            logger.info(f"      ✅ {dep_key}.data包含answer: {str(data['answer'])[:100]}")
        
        # 调用Service（支持同步和异步）
        try:
            import asyncio
            import inspect
            
            # 检查Service的execute方法是同步还是异步
            execute_method = getattr(self.service, 'execute', None)
            if execute_method is None:
                # 🚀 修复：如果Service没有execute方法，返回错误结果而不是抛出异常
                # 注意：某些Agent（如MemoryAgent）直接实现execute方法，不通过Service，这是正常的
                # 只在debug级别记录，避免产生过多警告
                logger.debug(f"Service {type(self.service).__name__} 没有execute方法（某些Agent直接实现execute方法，这是正常的）")
                return {
                    "success": False,
                    "error": f"Service {type(self.service).__name__} 没有execute方法",
                    "data": None,
                    "confidence": 0.0
                }
            
            is_async = inspect.iscoroutinefunction(execute_method)
            
            if is_async:
                # 🚀 添加超时保护，防止Service执行时间过长
                result = await asyncio.wait_for(
                    self.service.execute(service_context),
                    timeout=300.0  # 5分钟超时
                )
            else:
                # 同步方法，在线程池中执行，添加超时保护
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: self.service.execute(service_context)),
                    timeout=300.0  # 5分钟超时
                )
            
            return {
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "confidence": getattr(result, 'confidence', 0.8)
            }
        except asyncio.TimeoutError:
            logger.error(f"❌ Service调用超时（5分钟）: {self.agent_id}")
            return {
                "success": False,
                "error": "Service执行超时（5分钟）"
            }
        except Exception as e:
            logger.error(f"Service调用失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_task_complete(self, observation: Dict[str, Any]) -> bool:
        """判断任务是否完成"""
        if observation.get("success") and observation.get("data"):
            return True
        return False
    
    def _generate_result(self, observations: List[Dict], thoughts: List[str], 
                        actions: List[Action]) -> AgentResult:
        """生成最终结果"""
        # 从最后一个观察中提取结果
        if observations:
            last_obs = observations[-1]
            if last_obs.get("success"):
                return AgentResult(
                    success=True,
                    data=last_obs.get("data"),
                    confidence=last_obs.get("confidence", 0.8),
                    processing_time=0.0,  # 🚀 修复：添加processing_time参数
                    metadata={
                        "thoughts": thoughts,
                        "actions": [a.to_dict() for a in actions],
                        "observations_count": len(observations)
                    }
                )
        
        return AgentResult(
            success=False,
            data=None,
            processing_time=0.0,  # 🚀 修复：添加processing_time参数
            error="未找到有效结果",
            confidence=0.0
        )
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        处理查询（实现BaseAgent的抽象方法）
        
        Args:
            query: 查询文本
            context: 上下文信息（可选）
            
        Returns:
            AgentResult: 处理结果
        """
        # 同步包装异步execute方法
        import asyncio
        
        # 准备上下文
        exec_context = {"query": query}
        if context:
            exec_context.update(context)
        
        try:
            # 如果已有事件循环，使用它
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果循环正在运行，使用线程池执行
                import concurrent.futures
                def run_in_thread():
                    return asyncio.run(self._execute_async(exec_context))
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result()
            else:
                return loop.run_until_complete(self._execute_async(exec_context))
        except RuntimeError:
            # 没有事件循环，创建新的
            return asyncio.run(self._execute_async(exec_context))
    
    async def _execute_async(self, context: Dict[str, Any]) -> AgentResult:
        """异步执行方法（内部方法）"""
        return await self.execute(context)
