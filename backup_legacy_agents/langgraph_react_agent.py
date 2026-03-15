"""
LangGraph 版本的 ReAct Agent
使用 LangGraph 框架实现可描述、可治理、可复用、可恢复的 Agent 工作流
"""
import logging
import time
import json
import re
from typing import TypedDict, Annotated, Literal, Optional, Dict, Any, List
from dataclasses import dataclass

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.checkpoint.sqlite import SqliteSaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # 🚀 优化：使用DEBUG级别，因为这是可选的依赖，系统有fallback机制
    logging.debug("LangGraph not available. Install with: pip install langgraph (这是可选的，系统将使用其他Agent)")

from src.agents.base_agent import BaseAgent, AgentResult, AgentConfig
from src.agents.react_agent import Action
from src.utils.logging_helper import get_module_logger, ModuleType
from src.visualization.orchestration_tracker import get_orchestration_tracker

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """Agent 状态定义 - 统一管理所有状态"""
    query: str
    thoughts: Annotated[List[str], "思考历史"]
    observations: Annotated[List[Dict[str, Any]], "观察结果历史"]
    actions: Annotated[List[Dict[str, Any]], "行动历史"]
    task_complete: bool
    iteration: int
    max_iterations: int
    error: Optional[str]
    current_thought: Optional[str]
    current_action: Optional[Dict[str, Any]]
    current_observation: Optional[Dict[str, Any]]


class LangGraphReActAgent(BaseAgent):
    """基于 LangGraph 的 ReAct Agent
    
    优势：
    1. 可描述：工作流用图结构清晰描述
    2. 可治理：状态检查点、条件路由、错误处理
    3. 可复用：节点和边可以复用
    4. 可恢复：支持检查点和状态恢复
    """
    
    def __init__(self, agent_name: str = "LangGraphReActAgent", use_intelligent_config: bool = True):
        """初始化 LangGraph ReAct Agent"""
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph is required. Install with: pip install langgraph")
        
        config = AgentConfig(
            agent_id=agent_name,
            agent_type="langgraph_react_agent"
        )
        super().__init__(agent_name, ["react", "tool_calling", "autonomous_decision", "state_management"], config)
        
        self.module_logger = get_module_logger(ModuleType.AGENT, agent_name)
        
        # 工具注册表
        from src.utils.tool_registry import get_tool_registry
        self.tool_registry = get_tool_registry()
        self._register_default_tools()
        
        # LLM客户端
        self.llm_client = None
        self._init_llm_client()
        
        # 检查点配置
        self.checkpointer = MemorySaver()  # 开发环境使用内存，生产环境可以使用 SQLiteSaver
        
        # 构建工作流图
        self.workflow = self._build_workflow()
        
        self.module_logger.info(f"✅ LangGraph ReAct Agent初始化完成: {agent_name}")
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """处理查询 - 实现 BaseAgent 抽象方法"""
        import asyncio
        try:
            # 如果是异步环境，使用异步执行
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 已经在异步环境中，创建新任务
                return asyncio.create_task(self.execute(context or {"query": query}))
            else:
                # 同步环境，直接运行
                return loop.run_until_complete(self.execute(context or {"query": query}))
        except RuntimeError:
            # 没有事件循环，创建新的
            return asyncio.run(self.execute(context or {"query": query}))
    
    def _init_llm_client(self):
        """初始化 LLM 客户端"""
        try:
            from src.core.llm_integration import LLMIntegration
            self.llm_client = LLMIntegration()
        except Exception as e:
            self.module_logger.warning(f"LLM客户端初始化失败: {e}")
    
    def _register_default_tools(self):
        """注册默认工具"""
        # 工具注册逻辑与原有 ReActAgent 相同
        pass
    
    def _build_workflow(self) -> StateGraph:
        """构建 LangGraph 工作流
        
        工作流结构：
        START → think → plan → act → observe → (条件判断) → think 或 END
        """
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("think", self._think_node)
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("act", self._act_node)
        workflow.add_node("observe", self._observe_node)
        
        # 设置入口点
        workflow.set_entry_point("think")
        
        # 定义边
        workflow.add_edge("think", "plan")
        workflow.add_edge("plan", "act")
        workflow.add_edge("act", "observe")
        
        # 条件路由：根据观察结果决定是否继续
        workflow.add_conditional_edges(
            "observe",
            self._should_continue,
            {
                "continue": "think",
                "end": END
            }
        )
        
        # 编译工作流（启用检查点）
        return workflow.compile(checkpointer=self.checkpointer)
    
    async def _think_node(self, state: AgentState) -> AgentState:
        """思考节点"""
        # 🎯 编排追踪：Agent 思考开始
        tracker = getattr(self, '_orchestration_tracker', None) or get_orchestration_tracker()
        parent_event_id = None
        if tracker:
            parent_event_id = tracker.track_agent_think(
                self.agent_id or "langgraph_react_agent",
                f"思考迭代 {state['iteration'] + 1}",
                parent_event_id
            )
        
        try:
            self.module_logger.info(f"💭 [Think] 开始思考，迭代: {state['iteration'] + 1}")
            
            # 检查是否已完成
            if state.get('task_complete', False):
                return state
            
            # 调用思考逻辑
            query = state['query']
            observations = state.get('observations', [])
            
            thought = await self._think(query, observations)
            
            # 🎯 编排追踪：思考完成
            if tracker and parent_event_id:
                tracker.track_agent_think(
                    self.agent_id or "langgraph_react_agent",
                    thought[:200],  # 限制长度
                    parent_event_id
                )
            
            # 更新状态
            state['current_thought'] = thought
            state['thoughts'].append(thought)
            state['iteration'] += 1
            
            self.module_logger.info(f"✅ [Think] 思考完成: {thought[:100]}...")
            return state
            
        except Exception as e:
            self.module_logger.error(f"❌ [Think] 思考失败: {e}", exc_info=True)
            state['error'] = f"思考失败: {str(e)}"
            state['task_complete'] = True
            return state
    
    async def _plan_node(self, state: AgentState) -> AgentState:
        """规划节点"""
        # 🎯 编排追踪：Agent 规划开始
        tracker = getattr(self, '_orchestration_tracker', None) or get_orchestration_tracker()
        parent_event_id = None
        if tracker:
            parent_event_id = tracker.track_agent_plan(
                self.agent_id or "langgraph_react_agent",
                state.get('current_thought', '')[:200],
                parent_event_id
            )
        
        try:
            self.module_logger.info(f"📋 [Plan] 开始规划行动")
            
            query = state['query']
            thought = state.get('current_thought', '')
            observations = state.get('observations', [])
            
            # 调用规划逻辑
            action = await self._plan_action(thought, query, observations)
            
            if action:
                action_dict = action.to_dict()
                state['current_action'] = action_dict
                state['actions'].append(action_dict)
                
                # 🎯 编排追踪：规划完成
                if tracker and parent_event_id:
                    tracker.track_agent_plan(
                        self.agent_id or "langgraph_react_agent",
                        f"规划工具: {action.tool_name}",
                        parent_event_id
                    )
                
                self.module_logger.info(f"✅ [Plan] 规划完成: {action.tool_name}")
            else:
                self.module_logger.warning("⚠️ [Plan] 无法规划行动")
                state['task_complete'] = True
                state['error'] = "无法规划行动"
            
            return state
            
        except Exception as e:
            self.module_logger.error(f"❌ [Plan] 规划失败: {e}", exc_info=True)
            state['error'] = f"规划失败: {str(e)}"
            state['task_complete'] = True
            return state
    
    async def _act_node(self, state: AgentState) -> AgentState:
        """行动节点"""
        # 🎯 编排追踪：Agent 行动开始
        tracker = getattr(self, '_orchestration_tracker', None) or get_orchestration_tracker()
        tool_event_id = None
        action = None
        action_dict = None
        
        try:
            self.module_logger.info(f"🎯 [Act] 开始执行行动")
            
            action_dict = state.get('current_action')
            if not action_dict:
                state['error'] = "没有可执行的行动"
                state['task_complete'] = True
                return state
            
            # 重建 Action 对象
            action = Action.from_dict(action_dict)
            
            # 🎯 编排追踪：工具调用开始
            if tracker:
                tool_event_id = tracker.track_tool_start(
                    action.tool_name,
                    action.parameters or {}
                )
            
            # 执行行动
            observation = await self._act(action)
            
            # 🎯 编排追踪：工具调用结束
            if tracker and tool_event_id:
                tracker.track_tool_end(
                    action.tool_name,
                    observation if isinstance(observation, dict) else {"result": str(observation)}
                )
            
            state['current_observation'] = observation
            self.module_logger.info(f"✅ [Act] 行动完成: {action.tool_name}")
            
            return state
            
        except Exception as e:
            # 🎯 编排追踪：工具调用失败
            if tracker and tool_event_id:
                tool_name = action.tool_name if action else (action_dict.get('tool_name', 'unknown') if action_dict else 'unknown')
                tracker.track_tool_end(
                    tool_name,
                    None,
                    str(e)
                )
            
            self.module_logger.error(f"❌ [Act] 行动失败: {e}", exc_info=True)
            state['error'] = f"行动失败: {str(e)}"
            state['task_complete'] = True
            return state
    
    async def _observe_node(self, state: AgentState) -> AgentState:
        """观察节点"""
        # 🎯 编排追踪：Agent 观察开始
        tracker = getattr(self, '_orchestration_tracker', None) or get_orchestration_tracker()
        parent_event_id = None
        if tracker:
            parent_event_id = tracker.track_agent_observe(
                self.agent_id or "langgraph_react_agent",
                "处理观察结果",
                parent_event_id
            )
        
        try:
            self.module_logger.info(f"👁️ [Observe] 处理观察结果")
            
            observation = state.get('current_observation')
            if observation:
                state['observations'].append(observation)
                
                # 🎯 编排追踪：观察完成
                if tracker and parent_event_id:
                    obs_data = observation if isinstance(observation, dict) else {"observation": str(observation)}
                    tracker.track_agent_observe(
                        self.agent_id or "langgraph_react_agent",
                        f"观察结果: {str(obs_data)[:200]}",
                        parent_event_id
                    )
                
                # 检查任务是否完成
                task_complete = self._is_task_complete(
                    state.get('current_thought', ''),
                    [observation]
                )
                state['task_complete'] = task_complete
                
                if task_complete:
                    self.module_logger.info("✅ [Observe] 任务完成")
                else:
                    self.module_logger.info(f"🔄 [Observe] 任务未完成，继续迭代")
            
            return state
            
        except Exception as e:
            self.module_logger.error(f"❌ [Observe] 观察处理失败: {e}", exc_info=True)
            state['error'] = f"观察处理失败: {str(e)}"
            state['task_complete'] = True
            return state
    
    def _should_continue(self, state: AgentState) -> Literal["continue", "end"]:
        """条件路由：判断是否继续循环"""
        # 检查是否完成
        if state.get('task_complete', False):
            return "end"
        
        # 检查迭代次数
        if state['iteration'] >= state['max_iterations']:
            self.module_logger.warning(f"⚠️ 达到最大迭代次数: {state['max_iterations']}")
            return "end"
        
        # 检查错误
        if state.get('error'):
            return "end"
        
        return "continue"
    
    async def _think(self, query: str, observations: List[Dict[str, Any]]) -> str:
        """思考逻辑（与原有 ReActAgent 相同）"""
        if not self.llm_client:
            return "需要继续收集信息"
        
        try:
            # 构建思考提示词
            observations_text = self._format_observations(observations)
            available_tools = self.tool_registry.list_tools()
            tools_info = "\n".join([
                f"- {name}: {(tool_info.get('description', '') if tool_info else '')}"
                for name in available_tools
                if (tool_info := self.tool_registry.get_tool_info(name))
            ])
            
            think_prompt = f"""你是一个智能助手，正在处理以下任务：

任务: {query}

已观察到的信息:
{observations_text if observations_text else "（暂无观察信息）"}

可用工具:
{tools_info}

请思考：
1. 当前任务完成情况如何？
2. 还需要什么信息？
3. 下一步应该做什么？

请简要回答（不超过200字）。"""
            
            # 调用 LLM
            import asyncio
            loop = asyncio.get_event_loop()
            llm_client = self.llm_client  # 避免 lambda 中的类型检查问题
            response = await loop.run_in_executor(
                None,
                lambda: llm_client._call_llm(
                    think_prompt,
                    dynamic_complexity="simple",
                    max_tokens_override=200
                )
            )
            
            return response.strip() if response else "需要继续收集信息"
            
        except Exception as e:
            self.module_logger.error(f"思考失败: {e}", exc_info=True)
            return "需要继续收集信息"
    
    async def _plan_action(self, thought: str, query: str, observations: List[Dict[str, Any]]) -> Optional[Action]:
        """规划行动逻辑（与原有 ReActAgent 相同）"""
        try:
            # 如果已有足够信息，不需要继续行动
            if self._is_task_complete(thought, observations):
                return None
            
            if not self.llm_client:
                return None
            
            # 构建规划提示词
            observations_text = self._format_observations(observations)
            available_tools = self.tool_registry.list_tools()
            
            tools_schema = {}
            for tool_name in available_tools:
                tool = self.tool_registry.get_tool(tool_name)
                if tool:
                    tools_schema[tool_name] = tool.get_parameters_schema()
            
            plan_prompt = f"""Based on the following information, decide the next action:

Task: {query}
Thought: {thought}
Observations: {observations_text if observations_text else "(none)"}

Available tools:
{json.dumps(tools_schema, indent=2, ensure_ascii=False)}

Return the action plan in JSON format:
{{
    "tool_name": "tool_name",
    "params": {{"parameter_name": "parameter_value"}},
    "reasoning": "reason for choosing this tool"
}}

**CRITICAL REQUIREMENTS**:
1. For the "rag" tool, the "query" parameter MUST be the EXACT original query text
2. Return ONLY JSON, no other content."""
            
            # 调用 LLM
            import asyncio
            loop = asyncio.get_event_loop()
            llm_client = self.llm_client
            response = await loop.run_in_executor(
                None,
                lambda: llm_client._call_llm(
                    plan_prompt,
                    dynamic_complexity="simple",
                    max_tokens_override=300
                )
            )
            
            if not response:
                return None
            
            # 解析 JSON 响应
            action_dict = self._parse_action_response(response)
            if action_dict and 'tool_name' in action_dict:
                return Action.from_dict(action_dict)
            
            return None
            
        except Exception as e:
            self.module_logger.error(f"规划行动失败: {e}", exc_info=True)
            return None
    
    def _format_observations(self, observations: List[Dict[str, Any]]) -> str:
        """格式化观察结果"""
        if not observations:
            return ""
        
        formatted = []
        for i, obs in enumerate(observations[-5:], 1):  # 只显示最近5个观察
            tool_name = obs.get('tool_name', 'unknown')
            success = obs.get('success', False)
            data = obs.get('data', '')
            error = obs.get('error')
            
            if success:
                data_str = str(data)[:200] if data else ""
                formatted.append(f"观察{i}: 工具={tool_name}, 结果={data_str}")
            else:
                formatted.append(f"观察{i}: 工具={tool_name}, 失败={error}")
        
        return "\n".join(formatted)
    
    def _parse_action_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析行动响应（与 UnifiedResearchSystem 相同）"""
        try:
            # 尝试提取JSON（使用文件顶部已导入的 json 和 re）
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            
            return json.loads(response.strip())
        except Exception as e:
            self.module_logger.warning(f"解析行动响应失败: {e}")
            return None
    
    async def _act(self, action: Action) -> Dict[str, Any]:
        """执行行动逻辑（与原有 ReActAgent 相同）"""
        try:
            tool = self.tool_registry.get_tool(action.tool_name)
            if not tool:
                return {
                    'success': False,
                    'tool_name': action.tool_name,
                    'error': f'工具未找到: {action.tool_name}',
                    'data': None
                }
            
            # 执行工具
            result = await tool.execute(action.params)
            
            return {
                'success': True,
                'tool_name': action.tool_name,
                'data': result,
                'error': None
            }
        except Exception as e:
            self.module_logger.error(f"执行工具失败: {e}", exc_info=True)
            return {
                'success': False,
                'tool_name': action.tool_name,
                'error': str(e),
                'data': None
            }
    
    def _is_task_complete(self, thought: str, observations: List[Dict[str, Any]]) -> bool:
        """判断任务是否完成（与原有 ReActAgent 相同）"""
        # 实现与原有 ReActAgent._is_task_complete 相同
        if not observations:
            return False
        
        # 检查最新的观察结果
        latest_obs = observations[-1]
        if latest_obs.get('success') and latest_obs.get('data'):
            data = latest_obs.get('data')
            if isinstance(data, str) and len(data) > 10:
                return True
        
        return False
    
    def _build_think_prompt(self, query: str, observations: List[Dict[str, Any]]) -> str:
        """构建思考提示词"""
        obs_text = "\n".join([
            f"观察{i+1}: {obs.get('data', '')}"
            for i, obs in enumerate(observations[-3:])  # 只使用最近3个观察
        ])
        
        return f"""基于以下查询和观察结果，思考下一步应该做什么。

查询: {query}

观察结果:
{obs_text}

请简要思考下一步行动。"""
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行 Agent 工作流
        
        Args:
            context: 上下文，必须包含'query'字段
            
        Returns:
            AgentResult: 执行结果
        """
        start_time = time.time()
        
        try:
            query = context.get('query', '')
            if not query:
                return AgentResult(
                    success=False,
                    data=None,
                    error="查询为空",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
            
            self.module_logger.info(f"🧠 LangGraph ReAct Agent开始执行: {query[:100]}...")
            
            # 初始化状态
            initial_state: AgentState = {
                'query': query,
                'thoughts': [],
                'observations': [],
                'actions': [],
                'task_complete': False,
                'iteration': 0,
                'max_iterations': 10,
                'error': None,
                'current_thought': None,
                'current_action': None,
                'current_observation': None
            }
            
            # 执行工作流
            config = {"configurable": {"thread_id": f"react_{int(time.time())}"}}
            final_state = await self.workflow.ainvoke(initial_state, config)
            
            # 构建结果
            answer = ""
            if final_state.get('observations'):
                latest_obs = final_state['observations'][-1]
                answer = str(latest_obs.get('data', ''))
            
            success = final_state.get('task_complete', False) and not final_state.get('error')
            
            return AgentResult(
                success=success,
                data={
                    'answer': answer,
                    'thoughts': final_state.get('thoughts', []),
                    'observations': final_state.get('observations', []),
                    'actions': final_state.get('actions', [])
                },
                error=final_state.get('error'),
                confidence=0.8 if success else 0.3,
                processing_time=time.time() - start_time,
                metadata={
                    'iterations': final_state.get('iteration', 0),
                    'method': 'langgraph_react'
                }
            )
            
        except Exception as e:
            self.module_logger.error(f"❌ LangGraph ReAct Agent执行失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    def get_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取检查点状态
        
        Args:
            thread_id: 线程ID
            
        Returns:
            检查点状态，如果不存在返回None
        """
        try:
            config = {"configurable": {"thread_id": thread_id}}
            # 获取最新检查点
            # 注意：这需要根据 LangGraph 的实际 API 调整
            return None
        except Exception as e:
            self.module_logger.warning(f"获取检查点失败: {e}")
            return None
    
    def resume_from_checkpoint(self, thread_id: str) -> Optional[AgentResult]:
        """从检查点恢复执行
        
        Args:
            thread_id: 线程ID
            
        Returns:
            恢复后的执行结果
        """
        try:
            config = {"configurable": {"thread_id": thread_id}}
            # 从检查点恢复
            # 注意：这需要根据 LangGraph 的实际 API 调整
            return None
        except Exception as e:
            self.module_logger.warning(f"从检查点恢复失败: {e}")
            return None

