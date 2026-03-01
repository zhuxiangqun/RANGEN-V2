#!/usr/bin/env python3
"""
ReAct Agent
实现思考-行动-观察循环的智能体
"""

import time
import json
import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentResult, AgentConfig
from .tools.base_tool import BaseTool, ToolResult
from .tools.tool_registry import get_tool_registry
# 🚀 架构优化：RAGTool现在内部使用RAGAgent
# from .tools.rag_tool import RAGTool  # 延迟导入，在_register_default_tools中使用
from src.utils.logging_helper import get_module_logger, ModuleType
from src.visualization.orchestration_tracker import get_orchestration_tracker

logger = logging.getLogger(__name__)


@dataclass
class Action:
    """行动定义"""
    tool_name: str
    params: Dict[str, Any]
    reasoning: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        """从字典创建Action"""
        return cls(
            tool_name=data.get('tool_name', ''),
            params=data.get('params', {}),
            reasoning=data.get('reasoning', '')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'tool_name': self.tool_name,
            'params': self.params,
            'reasoning': self.reasoning
        }


class ReActAgent(BaseAgent):
    """ReAct模式的Agent - 实现思考-行动-观察循环"""
    
    def __init__(self, agent_name: str = "ReActAgent", use_intelligent_config: bool = True):
        """初始化ReAct Agent"""
        config = AgentConfig(
            agent_id=agent_name,
            agent_type="react_agent"
        )
        super().__init__(agent_name, ["react", "tool_calling", "autonomous_decision"], config)
        
        # 使用模块日志器
        self.module_logger = get_module_logger(ModuleType.AGENT, agent_name)
        
        # 🚀 初始化统一规则管理器（用于管理关键词和阈值）
        self._init_rule_manager()
        
        # 工具注册表
        self.tool_registry = get_tool_registry()
        
        # 注册默认工具
        self._register_default_tools()
        
        # ReAct循环状态
        self.observations: List[Dict[str, Any]] = []
        self.thoughts: List[str] = []
        self.actions: List[Action] = []
        
        # 🚀 从统一配置中心获取最大迭代次数
        from src.utils.unified_centers import get_unified_config_center
        config_center = get_unified_config_center()
        self.max_iterations = config_center.get_config_value(
            'thresholds', 'react_agent.complex_max_iterations', 10
        )
        self.max_think_time = 30.0  # 思考阶段最大时间（秒）
        
        # LLM客户端（用于思考阶段）
        self.llm_client = None
        self._init_llm_client()
        
        self.module_logger.info(f"✅ ReAct Agent初始化完成: {agent_name}")
    
    def _init_rule_manager(self):
        """🚀 初始化统一规则管理器"""
        try:
            from src.utils.unified_rule_manager import UnifiedRuleManager
            from src.utils.unified_centers import get_unified_config_center
            from src.utils.semantic_understanding_pipeline import get_semantic_understanding_pipeline
            
            config_center = get_unified_config_center()
            semantic_pipeline = get_semantic_understanding_pipeline()
            
            self.rule_manager = UnifiedRuleManager(
                config_center=config_center,
                semantic_pipeline=semantic_pipeline
            )
            self.module_logger.info("✅ 统一规则管理器初始化成功")
        except Exception as e:
            self.module_logger.warning(f"⚠️ 统一规则管理器初始化失败: {e}，将使用默认配置")
            self.rule_manager = None
    
    def _init_llm_client(self):
        """初始化LLM客户端（用于思考阶段）"""
        try:
            from src.core.llm_integration import LLMIntegration
            from src.utils.unified_centers import get_unified_config_center
            
            # 获取配置中心
            config_center = get_unified_config_center()
            
            # 构建LLM配置
            llm_config = {
                'llm_provider': config_center.get_env_config('llm', 'LLM_PROVIDER', 'deepseek'),
                'api_key': config_center.get_env_config('llm', 'DEEPSEEK_API_KEY', ''),
                'model': config_center.get_env_config('llm', 'FAST_MODEL', 'deepseek-chat'),
                'base_url': config_center.get_env_config('llm', 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
            }
            
            self.llm_client = LLMIntegration(llm_config)
            self.module_logger.info("✅ LLM客户端初始化成功（用于思考阶段）")
        except Exception as e:
            self.module_logger.warning(f"⚠️ LLM客户端初始化失败: {e}，思考功能可能受限")
            self.llm_client = None
    
    def _register_default_tools(self):
        """注册默认工具"""
        # 🚀 架构优化：支持两种方式注册RAG工具
        # 方式1（推荐）：直接使用RAGExpert.as_tool() - 架构更简洁，减少包装层
        # 方式2（向后兼容）：使用RAGTool - 保持原有接口
        if not self.tool_registry.get_tool("rag") and not self.tool_registry.get_tool("rag_expert"):
            # 优先使用RAGExpert.as_tool()（新方式）
            try:
                from .rag_agent import RAGExpert
                rag_expert = RAGExpert()
                rag_tool = rag_expert.as_tool()
                self.tool_registry.register_tool(rag_tool, {
                    "category": "knowledge",
                    "priority": 1,
                    "source": "rag_expert_as_tool"
                })
                self.module_logger.info("✅ RAG工具已注册（使用RAGExpert.as_tool()，架构优化）")
            except Exception as e:
                # 如果新方式失败，回退到传统RAGTool（向后兼容）
                self.module_logger.warning(f"⚠️ 使用RAGExpert.as_tool()失败，回退到RAGTool: {e}")
                from .tools.rag_tool import RAGTool
                rag_tool = RAGTool()
                self.tool_registry.register_tool(rag_tool, {
                    "category": "knowledge",
                    "priority": 1,
                    "source": "rag_tool"
                })
                self.module_logger.info("✅ RAG工具已注册（使用RAGTool，向后兼容）")
        else:
            self.module_logger.info("ℹ️ RAG工具已存在，跳过注册")
    
    def register_tool(self, tool: BaseTool, metadata: Optional[Dict[str, Any]] = None):
        """注册新工具"""
        return self.tool_registry.register_tool(tool, metadata)
    
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
        try:
            # 如果已有事件循环，使用它
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果循环正在运行，创建任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._execute_async(query, context))
                    return future.result()
            else:
                return loop.run_until_complete(self._execute_async(query, context))
        except RuntimeError:
            # 没有事件循环，创建新的
            return asyncio.run(self._execute_async(query, context))
    
    async def _execute_async(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """异步执行方法（内部方法）"""
        exec_context = {"query": query}
        if context:
            exec_context.update(context)
        return await self.execute(exec_context)
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        执行ReAct循环
        
        Args:
            context: 上下文，必须包含'query'字段
            
        Returns:
            AgentResult: 执行结果
        """
        start_time = time.time()
        
        try:
            # 提取查询
            query = context.get('query', '')
            if not query:
                return AgentResult(
                    success=False,
                    data=None,
                    error="查询为空",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
            
            # 🎯 编排追踪：Agent 开始执行
            tracker = getattr(self, '_orchestration_tracker', None)
            agent_start_event_id = None
            if tracker:
                agent_start_event_id = tracker.track_agent_start(
                    self.agent_id or "react_agent",
                    "react_agent",
                    context
                )
            
            self.module_logger.info(f"🧠 ReAct Agent开始执行: {query[:100]}...")
            
            # 重置状态
            self.observations = []
            self.thoughts = []
            self.actions = []
            
            # 🔍 优先级1: 添加详细的诊断日志 - 在循环开始前
            self.module_logger.info(f"🔍 [诊断] ========== ReAct循环初始化 ==========")
            self.module_logger.info(f"🔍 [诊断] max_iterations={self.max_iterations}, 初始观察数={len(self.observations)}")
            self.module_logger.info(f"🔍 [诊断] 可用工具: {self.tool_registry.list_tools()}")
            self.module_logger.info(f"🔍 [诊断] LLM客户端可用: {self.llm_client is not None}")
            
            # 🚀 优化：动态调整最大迭代次数（根据查询复杂度）
            max_iterations = self._get_dynamic_max_iterations(query)
            self.module_logger.info(f"🚀 [优化] 动态最大迭代次数: {max_iterations} (原始: {self.max_iterations})")
            
            # ReAct循环
            iteration = 0
            task_complete = False
            
            # 🔍 优先级1: 添加循环开始日志
            self.module_logger.info(f"🔍 [诊断] ========== ReAct循环开始 ==========")
            self.module_logger.info(f"🔍 [诊断] 循环条件: iteration < {max_iterations} and not task_complete")
            self.module_logger.info(f"🔍 [诊断] 初始状态: iteration={iteration}, task_complete={task_complete}")
            
            while iteration < max_iterations and not task_complete:
                self.module_logger.info(f"🔄 ReAct循环迭代 {iteration + 1}/{max_iterations}")
                self.module_logger.info(f"🔍 [诊断] 迭代{iteration+1}开始: 当前观察数={len(self.observations)}, 思考数={len(self.thoughts)}, 行动数={len(self.actions)}")
                
                # 🚀 优化：在思考之前，先检查是否已有有效答案（避免不必要的思考）
                if iteration > 0:  # 第一次迭代必须执行，后续迭代可以提前检查
                    task_complete = self._is_task_complete("", self.observations)  # 不依赖thought，直接检查observations
                    if task_complete:
                        self.module_logger.info("✅ [优化] 在思考前检测到任务已完成，跳过思考阶段")
                        self.module_logger.info(f"🔍 [诊断] 退出原因: task_complete=True (提前检测), 观察数={len(self.observations)}")
                        break
                
                # 思考（Reason）
                self.module_logger.info(f"🔍 [诊断] ========== 思考阶段开始 ==========")
                thought = await self._think(query, self.observations)
                self.thoughts.append(thought)
                self.module_logger.info(f"🔍 [诊断] 思考阶段完成: thought长度={len(thought)}, 内容前100字符={thought[:100]}...")
                
                # 判断是否完成
                self.module_logger.info(f"🔍 [诊断] ========== 任务完成判断开始 ==========")
                task_complete = self._is_task_complete(thought, self.observations)
                self.module_logger.info(f"🔍 [诊断] 任务完成判断: task_complete={task_complete}, 观察数={len(self.observations)}")
                self.module_logger.info(f"🔍 [诊断] thought内容: {thought[:200]}...")
                if task_complete:
                    self.module_logger.info("✅ 任务完成，退出循环")
                    self.module_logger.info(f"🔍 [诊断] 退出原因: task_complete=True, 观察数={len(self.observations)}")
                    break
                
                # 🚀 优化：检查是否已经调用过RAG工具且返回了有效答案（避免重复调用）
                has_valid_rag_answer = self._has_valid_rag_answer(self.observations)
                if has_valid_rag_answer:
                    self.module_logger.info("✅ [优化] 已检测到有效的RAG答案，跳过后续工具调用")
                    task_complete = True
                    break
                
                # 规划行动（Plan Action）
                self.module_logger.info(f"🔍 [诊断] ========== 规划行动阶段开始 ==========")
                action = await self._plan_action(thought, query, self.observations)
                self.module_logger.info(f"🔍 [诊断] 规划行动结果: action={action.tool_name if action else None}, params={action.params if action else None}")
                if not action or not action.tool_name:
                    self.module_logger.warning("⚠️ 无法规划行动，退出循环")
                    self.module_logger.warning(f"🔍 [诊断] 退出原因: action={action}, action.tool_name={action.tool_name if action else None}")
                    break
                
                # 🚀 架构优化：RAGTool已移除，统一使用RealReasoningEngine
                # 此检查逻辑已不再需要，因为RealReasoningEngine通过IntelligentOrchestrator的ReasoningPlan直接调用
                # 保留此代码块但注释掉，以防将来需要类似的检查逻辑
                # if action.tool_name == 'rag' and self._has_called_rag_tool(self.observations):
                #     # 如果已经调用过RAG工具，检查是否需要重复调用（例如：答案无效或需要更多信息）
                #     if not has_valid_rag_answer:
                #         # 如果之前的RAG调用没有返回有效答案，允许再次调用
                #         self.module_logger.info("⚠️ [优化] 之前的RAG调用未返回有效答案，允许再次调用")
                #     else:
                #         # 如果已经有有效答案，跳过这次调用
                #         self.module_logger.info("✅ [优化] 已有有效的RAG答案，跳过重复调用")
                #         task_complete = True
                #         break
                
                self.actions.append(action)
                self.module_logger.info(f"🔍 [诊断] 规划行动完成: 工具={action.tool_name}, 参数={action.params}")
                
                # 行动（Act）
                self.module_logger.info(f"🔍 [诊断] ========== 行动阶段开始 ==========")
                observation = await self._act(action)
                self.observations.append(observation)
                
                # 🔍 诊断：记录观察结果
                self.module_logger.info(f"🔍 [诊断] ========== 观察结果 ==========")
                self.module_logger.info(f"🔍 [诊断] 观察结果: success={observation.get('success')}, tool_name={observation.get('tool_name')}, has_data={observation.get('data') is not None}, error={observation.get('error')}")
                if observation.get('data'):
                    data_str = str(observation.get('data'))
                    self.module_logger.info(f"🔍 [诊断] 观察数据长度: {len(data_str)}, 前200字符: {data_str[:200]}...")
                
                # 🚀 架构优化：统一使用RAGTool（内部使用RAGAgent）
                # ReasoningTool已移除，只检查RAG工具的结果
                if observation.get('success') and observation.get('tool_name') == 'rag':
                    task_complete = self._is_task_complete("", [observation])  # 只检查最新的观察结果
                    if task_complete:
                        self.module_logger.info("✅ [优化] RAG工具返回有效答案，任务完成，立即退出循环")
                        self.module_logger.info(f"🔍 [诊断] 退出原因: RAG工具返回有效答案, 迭代次数={iteration+1}")
                        iteration += 1  # 确保迭代计数正确
                        break
                
                iteration += 1
                self.module_logger.info(f"🔍 [诊断] 迭代{iteration}完成: 观察数={len(self.observations)}, 准备进入下一次迭代")
            
            # 🔍 优先级1: 添加循环结束日志
            self.module_logger.info(f"🔍 [诊断] ========== ReAct循环结束 ==========")
            self.module_logger.info(f"🔍 [诊断] 循环结束原因: iteration={iteration}, task_complete={task_complete}, max_iterations={self.max_iterations}")
            self.module_logger.info(f"🔍 [诊断] 最终状态: 观察数={len(self.observations)}, 思考数={len(self.thoughts)}, 行动数={len(self.actions)}")
            
            # 🔍 诊断：详细记录每个观察的状态
            for i, obs in enumerate(self.observations):
                self.module_logger.info(f"🔍 [诊断] 观察{i+1}详情: success={obs.get('success')}, tool_name={obs.get('tool_name')}, has_data={obs.get('data') is not None}, error={obs.get('error')}")
                if obs.get('data'):
                    data_str = str(obs.get('data'))
                    self.module_logger.info(f"🔍 [诊断] 观察{i+1}数据: 类型={type(obs.get('data'))}, 长度={len(data_str)}, 前200字符: {data_str[:200]}...")
            
            # 生成最终答案
            final_answer = await self._synthesize_answer(query, self.observations, self.thoughts)
            
            processing_time = time.time() - start_time
            
            # 🔧 修复：根据实际执行情况判断success
            has_successful_observations = any(
                obs.get('success') and obs.get('data') 
                for obs in self.observations
            )
            is_fallback_message = final_answer == "抱歉，无法获取足够的信息来回答这个问题。"
            # 🚀 修复：将"unable to determine"视为失败
            # 🚀 修复：将"unable to determine"视为失败
            # 🚀 修复：检查"unable to determine"（包括中文版本）
            final_answer_lower = final_answer.lower().strip() if final_answer else ""
            final_answer_stripped = final_answer.strip() if final_answer else ""
            is_unable_to_determine = (final_answer and 
                                     (final_answer_lower == "unable to determine" or
                                      final_answer_lower.startswith("unable to determine") or
                                      final_answer_stripped == "无法确定" or
                                      final_answer_stripped.startswith("无法确定") or
                                      final_answer_stripped == "不确定" or
                                      final_answer_stripped.startswith("不确定")))
            
            # 判断是否真正成功
            actual_success = (has_successful_observations and 
                            not is_fallback_message and 
                            not is_unable_to_determine)
            
            # 计算置信度
            if actual_success:
                # 根据成功观察的数量和质量计算置信度
                successful_count = sum(1 for obs in self.observations if obs.get('success') and obs.get('data'))
                confidence = min(0.8 + (successful_count - 1) * 0.05, 0.95)
            else:
                confidence = 0.3  # 失败时使用低置信度
            
            self.module_logger.info(f"✅ ReAct Agent执行完成，迭代次数: {iteration}，耗时: {processing_time:.2f}秒")
            self.module_logger.info(f"🔍 [诊断] ========== 成功判断 ==========")
            self.module_logger.info(f"🔍 [诊断] has_successful_observations={has_successful_observations}")
            self.module_logger.info(f"🔍 [诊断] is_fallback_message={is_fallback_message}")
            self.module_logger.info(f"🔍 [诊断] is_unable_to_determine={is_unable_to_determine}")
            self.module_logger.info(f"🔍 [诊断] actual_success={actual_success}")
            self.module_logger.info(f"🔍 [诊断] confidence={confidence}")
            self.module_logger.info(f"🔍 [诊断] final_answer长度={len(final_answer)}, 前100字符: {final_answer[:100]}...")
            
            return AgentResult(
                success=actual_success,  # 🔧 修复：使用实际成功状态
                data={
                    "answer": final_answer,
                    "thoughts": self.thoughts,
                    "actions": [a.to_dict() for a in self.actions],
                    "observations": self.observations,
                    "iterations": iteration
                },
                confidence=confidence,  # 🔧 修复：根据成功状态调整置信度
                processing_time=processing_time,
                metadata={
                    "react_iterations": iteration,
                    "tools_used": [a.tool_name for a in self.actions],
                    "task_completed": task_complete,
                    "has_successful_observations": has_successful_observations,  # 🔧 新增：记录是否有成功观察
                    "is_fallback_message": is_fallback_message,  # 🔧 新增：记录是否是fallback消息
                    "is_unable_to_determine": is_unable_to_determine  # 🚀 新增：记录是否是"unable to determine"
                }
            )
            
        except Exception as e:
            self.module_logger.error(f"❌ ReAct Agent执行失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _think(self, query: str, observations: List[Dict[str, Any]]) -> str:
        """
        思考阶段 - 分析当前状态，决定下一步
        
        Args:
            query: 原始查询
            observations: 已观察到的信息
            
        Returns:
            str: 思考结果
        """
        # 🎯 编排追踪：Agent 思考开始
        tracker = getattr(self, '_orchestration_tracker', None)
        parent_event_id = getattr(self, '_current_agent_event_id', None)
        
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

重要提示：
- 请用简洁的语言描述你的思考过程（不超过200字）
- 不要使用"完成"、"足够"等可能被误判为任务完成的词汇
- 如果还没有收集到信息，请明确说明"需要先查询知识库"
- 如果已经收集到信息，请说明"已收集到信息，可以继续处理"
- 不要直接说"任务完成"或"可以回答"，而是描述当前状态

请用简洁的语言描述你的思考过程（不超过200字）。"""
            
            # 调用LLM进行思考
            if self.llm_client:
                try:
                    # 使用快速模型进行思考（快速响应）
                    # 注意：_call_llm是同步方法，模型在初始化时已确定
                    import asyncio
                    # 在线程池中执行同步LLM调用，避免阻塞
                    if not self.llm_client:
                        thought = "需要继续收集信息"
                    else:
                        # 在lambda外捕获llm_client引用，避免类型检查问题
                        llm_client = self.llm_client
                        loop = asyncio.get_event_loop()
                        response = await loop.run_in_executor(
                            None,
                            lambda: llm_client._call_llm(
                                think_prompt,
                                dynamic_complexity="simple",  # 简单任务，快速响应
                                max_tokens_override=200
                            )
                        )
                        thought = response.strip() if response else "需要继续收集信息"
                except Exception as e:
                    self.module_logger.warning(f"⚠️ LLM思考失败: {e}，使用默认思考")
                    thought = "需要继续收集信息"
            else:
                # 🔧 优先级3: 如果没有LLM客户端，使用简单规则（避免使用完成关键词）
                if not observations:
                    thought = "需要先查询知识库获取相关信息"
                elif len(observations) >= 3:
                    # 🔧 修复：避免使用"足够"等关键词，改用描述性语言
                    thought = "已收集到多条信息，可以继续处理"
                else:
                    thought = "需要继续收集信息"
            
            # 🔍 优先级1: 添加思考结果日志
            self.module_logger.info(f"💭 [诊断] 思考结果: 长度={len(thought)}, 内容={thought[:200]}...")
            
            # 🎯 编排追踪：Agent 思考完成
            if tracker:
                tracker.track_agent_think(
                    self.agent_id or "react_agent",
                    thought,
                    parent_event_id
                )
            
            return thought
            
        except Exception as e:
            self.module_logger.error(f"❌ 思考阶段失败: {e}", exc_info=True)
            error_thought = "思考过程出错，继续执行"
            
            # 🎯 编排追踪：Agent 思考失败
            if tracker:
                tracker.track_agent_think(
                    self.agent_id or "react_agent",
                    error_thought,
                    parent_event_id
                )
            
            return error_thought
    
    async def _plan_action(self, thought: str, query: str, observations: List[Dict[str, Any]]) -> Optional[Action]:
        """
        规划行动 - 决定调用哪个工具
        
        Args:
            thought: 思考结果
            query: 原始查询
            observations: 已观察到的信息
            
        Returns:
            Action: 行动计划，如果无法规划返回None
        """
        # 🎯 编排追踪：Agent 规划开始
        tracker = getattr(self, '_orchestration_tracker', None)
        parent_event_id = getattr(self, '_current_agent_event_id', None)
        
        try:
            # 如果已有足够信息，不需要继续行动
            if self._is_task_complete(thought, observations):
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
1. For the "rag" tool, the "query" parameter MUST be the EXACT original query text, DO NOT translate or modify it
2. If the original query is in English, keep it in English
3. If the original query is in Chinese, keep it in Chinese
4. DO NOT translate the query to another language
5. Return ONLY JSON, no other content."""

            # 调用LLM规划行动
            if not self.llm_client:
                self.module_logger.warning("⚠️ [规划诊断] LLM客户端未初始化")
                print("⚠️ [规划诊断] LLM客户端未初始化，无法进行规划")
                print("⚠️ [规划诊断] 可能原因: 1) LLM客户端初始化失败 2) 语法错误导致初始化中断 3) API密钥未设置")
            else:
                self.module_logger.debug(f"✅ [规划诊断] LLM客户端已初始化，类型: {type(self.llm_client)}")
                print(f"✅ [规划诊断] LLM客户端已初始化，类型: {type(self.llm_client)}")
                
                try:
                    # 注意：_call_llm是同步方法，模型在初始化时已确定
                    import asyncio
                    import time
                    
                    # 🚀 增强诊断：记录LLM调用开始时间
                    start_time = time.time()
                    self.module_logger.debug(f"🔍 [规划诊断] 开始调用LLM规划，提示词长度: {len(plan_prompt)}字符")
                    print(f"🔍 [规划诊断] 开始调用LLM规划，提示词长度: {len(plan_prompt)}字符")
                    
                    # 在lambda外捕获llm_client引用，避免类型检查问题
                    llm_client = self.llm_client
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        lambda: llm_client._call_llm(
                            plan_prompt,
                            dynamic_complexity="simple",  # 简单任务，快速响应
                            max_tokens_override=300
                        )
                    )
                    
                    elapsed_time = time.time() - start_time
                    self.module_logger.debug(f"✅ [规划诊断] LLM调用完成，耗时: {elapsed_time:.2f}秒")
                    print(f"✅ [规划诊断] LLM调用完成，耗时: {elapsed_time:.2f}秒")
                    
                    # 🚀 增强诊断：检查响应
                    if not response:
                        self.module_logger.warning("⚠️ [规划诊断] LLM规划响应为空")
                        print("⚠️ [规划诊断] LLM规划响应为空")
                        print("⚠️ [规划诊断] 可能原因: 1) API返回空响应 2) 网络连接中断 3) API调用超时")
                    else:
                        self.module_logger.debug(f"✅ [规划诊断] LLM返回响应，长度: {len(response)}字符")
                        print(f"✅ [规划诊断] LLM返回响应，长度: {len(response)}字符")
                        print(f"🔍 [规划诊断] 响应内容预览: {response[:300]}...")
                    
                    # 解析JSON响应
                    if response:
                        action_dict = self._parse_json_response(response)
                        if action_dict:
                            self.module_logger.debug(f"✅ [规划诊断] JSON解析成功，action_dict keys: {list(action_dict.keys())}")
                            print(f"✅ [规划诊断] JSON解析成功，action_dict keys: {list(action_dict.keys())}")
                        else:
                            self.module_logger.warning(f"⚠️ [规划诊断] JSON解析失败，原始响应: {response[:500]}...")
                            print(f"⚠️ [规划诊断] JSON解析失败，原始响应: {response[:500]}...")
                            print("⚠️ [规划诊断] 可能原因: 1) JSON格式错误 2) 响应包含非JSON内容 3) 正则提取失败")
                    else:
                        action_dict = None
                        self.module_logger.warning("⚠️ [规划诊断] 响应为空，无法解析")
                        print("⚠️ [规划诊断] 响应为空，无法解析")
                    
                    if action_dict and 'tool_name' in action_dict:
                        action = Action.from_dict(action_dict)
                        # 如果tool_name无效或不在可用工具列表，直接兜底RAG
                        if (not action.tool_name) or (action.tool_name not in available_tools):
                            self.module_logger.warning(
                                f"⚠️ [规划诊断] LLM规划返回无效工具({action.tool_name})，使用RAG兜底"
                            )
                            print(f"⚠️ [规划诊断] LLM规划返回无效工具({action.tool_name})，使用RAG兜底")
                            print(f"⚠️ [规划诊断] 可用工具列表: {available_tools}")
                            return Action(
                                tool_name='rag',
                                params={'query': query},
                                reasoning='LLM返回无效tool，兜底RAG'
                            )
                        # 🚀 架构优化：统一使用RAGTool（内部使用RAGAgent）
                        if action.tool_name == 'rag' and 'query' in action.params:
                            original_query = action.params.get('query', '')
                            # 如果LLM返回的query与原始query不同，使用原始query
                            if original_query != query:
                                self.module_logger.warning(
                                    f"⚠️ LLM返回的query与原始query不同，使用原始query | "
                                    f"原始: {query[:100]} | LLM返回: {original_query[:100]}"
                                )
                                action.params['query'] = query  # 强制使用原始查询
                            self.module_logger.debug(f"📋 规划行动: {action.tool_name} - {action.reasoning}")
                            return action
                        # 若LLM选择了其他可用工具，则直接使用
                        self.module_logger.debug(f"📋 规划行动(非rag): {action.tool_name} - {action.reasoning}")
                        return action
                except Exception as e:
                    elapsed_time = time.time() - start_time if 'start_time' in locals() else 0
                    self.module_logger.warning(f"⚠️ [规划诊断] LLM规划失败: {e}，耗时: {elapsed_time:.2f}秒，使用默认策略", exc_info=True)
                    print(f"⚠️ [规划诊断] LLM规划失败: {e}，耗时: {elapsed_time:.2f}秒")
                    print(f"⚠️ [规划诊断] 异常类型: {type(e).__name__}")
                    print(f"⚠️ [规划诊断] 可能原因: 1) 网络连接问题 2) API调用超时 3) SSL错误 4) API密钥无效")
            
            # 🚀 架构优化：统一使用RAGTool（内部使用RAGAgent）
            # ReasoningTool已移除，统一使用RAGTool，符合架构设计
            if 'rag' in available_tools:
                fallback_action = Action(
                    tool_name='rag',
                    params={'query': query},  # 🚀 修复：确保使用原始查询
                    reasoning="使用RAG工具查询知识库（内部使用RAGAgent）；LLM规划为空或无效时的兜底"
                )
                
                # 🎯 编排追踪：Agent 规划（使用兜底方案）
                if tracker:
                    tracker.track_agent_plan(
                        self.agent_id or "react_agent",
                        {"action": fallback_action.to_dict(), "fallback": True},
                        parent_event_id
                    )
                
                return fallback_action
            # 🚀 架构优化：ReasoningTool已移除，不再作为备选方案
            # 如果RAG工具不可用，返回None让系统处理
            
            return None
            
        except Exception as e:
            self.module_logger.error(f"❌ 规划行动失败: {e}", exc_info=True)
            # 发生异常时也兜底到RAG
            return Action(
                tool_name='rag',
                params={'query': query},
                reasoning="规划异常兜底RAG"
            )
    
    
    async def _act(self, action: Action) -> Dict[str, Any]:
        """
        行动阶段 - 调用工具
        
        Args:
            action: 行动计划
            
        Returns:
            Dict: 观察结果
        """
        # 🎯 编排追踪：Agent 行动开始
        tracker = getattr(self, '_orchestration_tracker', None)
        parent_event_id = getattr(self, '_current_agent_event_id', None)
        tool_event_id = None
        
        try:
            tool = self.tool_registry.get_tool(action.tool_name)
            if not tool:
                self.module_logger.error(f"❌ [诊断] 工具不存在: {action.tool_name}, 可用工具: {self.tool_registry.list_tools()}")
                error_result = {
                    "success": False,
                    "error": f"工具不存在: {action.tool_name}",
                    "tool_name": action.tool_name
                }
                
                # 🎯 编排追踪：Agent 行动失败
                if tracker:
                    tracker.track_agent_act(
                        self.agent_id or "react_agent",
                        {"action": action.to_dict(), "error": error_result["error"]},
                        parent_event_id
                    )
                
                return error_result
            
            # 🎯 编排追踪：Agent 行动（调用工具）
            if tracker:
                tracker.track_agent_act(
                    self.agent_id or "react_agent",
                    {"action": action.to_dict()},
                    parent_event_id
                )
            
            # 🎯 编排追踪：工具调用开始
            if tracker and action.tool_name:
                tool_event_id = tracker.track_tool_start(
                    action.tool_name,
                    action.params,
                    parent_event_id
                )
                # 传递追踪器到工具
                if hasattr(tool, '_orchestration_tracker'):
                    tool._orchestration_tracker = tracker
            
            # 🔍 优先级1: 添加工具调用前的详细日志
            self.module_logger.info(f"🔧 [Agent:ReActAgent] 调用工具: {action.tool_name}, 参数: {action.params}")
            self.module_logger.info(f"🔍 [诊断] 工具调用前: 工具类型={type(tool)}, 工具名称={tool.tool_name if hasattr(tool, 'tool_name') else 'N/A'}")
            
            # 🚀 P0修复：对于答案生成工具，需要从observations中构建dependencies
            tool_params = dict(action.params)  # 复制参数，避免修改原始参数
            
            if action.tool_name == "answer_generation":
                # 从observations中提取推理结果，构建dependencies
                dependencies = {}
                
                # 🚀 架构优化：统一使用RAGTool（内部使用RAGAgent）
                # ReasoningTool已移除，查找RAG工具的结果
                for obs in self.observations:
                    if obs.get("tool_name") == "rag" and obs.get("success"):
                        # 找到RAG结果，添加到dependencies
                        rag_data = obs.get("data", {})
                        if rag_data:
                            dependencies["rag"] = {
                                "data": rag_data,  # 🚀 修复：使用rag_data而不是reasoning_data
                                "success": True
                            }
                            self.module_logger.info(f"🔍 [ReActAgent] 为答案生成工具添加推理结果到dependencies")
                            break
                
                # 如果找到了推理结果，将其添加到context中
                if dependencies:
                    if "context" not in tool_params:
                        tool_params["context"] = {}
                    elif not isinstance(tool_params["context"], dict):
                        tool_params["context"] = {}
                    
                    tool_params["context"]["dependencies"] = dependencies
                    self.module_logger.info(f"🔍 [ReActAgent] 为答案生成工具添加dependencies: keys={list(dependencies.keys())}")
            
            # 调用工具
            try:
                self.module_logger.info(f"🔍 [诊断] 开始调用工具: {action.tool_name}")
                result: ToolResult = await tool.call(**tool_params)
                self.module_logger.info(f"🔍 [诊断] 工具调用完成: {action.tool_name}")
                
                # 🎯 编排追踪：工具调用结束（成功）
                if tracker and action.tool_name:
                    tracker.track_tool_end(
                        action.tool_name,
                        result.to_dict() if hasattr(result, 'to_dict') else {"success": result.success, "data": result.data},
                        None
                    )
            except Exception as e:
                self.module_logger.error(f"❌ [诊断] 工具调用异常: {action.tool_name}, 错误={e}", exc_info=True)
                
                # 🎯 编排追踪：工具调用结束（失败）
                if tracker and action.tool_name:
                    tracker.track_tool_end(
                        action.tool_name,
                        None,
                        str(e)
                    )
                
                # 返回失败的观察结果
                return {
                    "success": False,
                    "tool_name": action.tool_name,
                    "data": None,
                    "error": f"工具调用异常: {str(e)}",
                    "execution_time": 0.0,
                    "timestamp": None
                }
            
            # 🔍 优先级1: 添加详细的工具调用结果日志
            self.module_logger.info(f"🔍 [诊断] ========== 工具调用结果 ==========")
            self.module_logger.info(f"🔍 [诊断] 工具: {action.tool_name}")
            self.module_logger.info(f"🔍 [诊断] success: {result.success}")
            self.module_logger.info(f"🔍 [诊断] has_data: {result.data is not None}")
            self.module_logger.info(f"🔍 [诊断] error: {result.error}")
            self.module_logger.info(f"🔍 [诊断] execution_time: {result.execution_time:.2f}秒")
            if result.data:
                data_str = str(result.data)
                self.module_logger.info(f"🔍 [诊断] data类型: {type(result.data)}, 长度: {len(data_str)}, 前200字符: {data_str[:200]}...")
            
            # 构建观察结果
            observation = {
                "success": result.success,
                "tool_name": action.tool_name,
                "data": result.data,
                "error": result.error,
                "execution_time": result.execution_time,
                "timestamp": result.timestamp.isoformat() if result.timestamp else None
            }
            
            if result.success:
                self.module_logger.info(f"✅ 工具调用成功: {action.tool_name}")
            else:
                self.module_logger.warning(f"⚠️ 工具调用失败: {action.tool_name} - {result.error}")
            
            # 🎯 编排追踪：Agent 观察（行动结果）
            if tracker:
                tracker.track_agent_observe(
                    self.agent_id or "react_agent",
                    observation,
                    parent_event_id
                )
            
            return observation
            
        except Exception as e:
            self.module_logger.error(f"❌ 行动阶段失败: {e}", exc_info=True)
            error_observation = {
                "success": False,
                "error": str(e),
                "tool_name": action.tool_name if action else "unknown"
            }
            
            # 🎯 编排追踪：Agent 观察（错误）
            if tracker:
                tracker.track_agent_observe(
                    self.agent_id or "react_agent",
                    error_observation,
                    parent_event_id
                )
            
            return error_observation
    
    async def _synthesize_answer(self, query: str, observations: List[Dict[str, Any]], thoughts: List[str]) -> str:
        """
        综合答案 - 基于所有观察和思考生成最终答案
        
        Args:
            query: 原始查询
            observations: 所有观察结果
            thoughts: 所有思考过程
            
        Returns:
            str: 最终答案
        """
        try:
            # 提取所有成功的观察结果
            # 🚀 修复：检查答案内容是否包含错误消息
            successful_observations = []
            for obs in observations:
                if obs.get('success') and obs.get('data'):
                    # 检查答案内容是否包含错误消息
                    data = obs.get('data')
                    if isinstance(data, dict):
                        answer = data.get('answer', '')
                        if answer and ("Error processing query" in answer or 
                                       answer.startswith("Error processing")):
                            self.module_logger.warning(f"⚠️ 检测到错误答案，拒绝: {answer[:50]}")
                            continue  # 跳过这个观察
                    successful_observations.append(obs)
            
            # 🔍 优先级1: 添加详细的综合答案阶段日志
            self.module_logger.info(f"🔍 [诊断] ========== 综合答案阶段开始 ==========")
            self.module_logger.info(f"🔍 [诊断] 总观察数: {len(observations)}, 成功观察数: {len(successful_observations)}")
            self.module_logger.info(f"🔍 [诊断] 总思考数: {len(thoughts)}, 总行动数: {len(self.actions) if hasattr(self, 'actions') else 0}")
            
            for i, obs in enumerate(observations):
                self.module_logger.info(f"🔍 [诊断] 观察{i+1}: success={obs.get('success')}, tool_name={obs.get('tool_name')}, has_data={obs.get('data') is not None}, error={obs.get('error')}")
                if obs.get('data'):
                    data_str = str(obs.get('data'))
                    self.module_logger.info(f"🔍 [诊断] 观察{i+1}数据: 类型={type(obs.get('data'))}, 长度={len(data_str)}, 前200字符: {data_str[:200]}...")
            
            if not successful_observations:
                # 🔧 优化：尝试从失败的观察中提取部分信息
                partial_observations = [
                    obs for obs in observations 
                    if obs.get('data') and not obs.get('success')
                ]
                
                if partial_observations:
                    self.module_logger.warning(f"⚠️ [诊断] 没有成功的观察结果，但有{len(partial_observations)}个部分观察，尝试提取信息")
                    # 尝试从部分观察中提取信息
                    for obs in partial_observations:
                        data = obs.get('data')
                        if isinstance(data, dict) and 'answer' in data:
                            answer = data.get('answer', '')
                            if answer and answer.strip():
                                self.module_logger.info(f"🔍 [诊断] 从部分观察中提取到答案: {answer[:100]}...")
                                return answer
                        elif isinstance(data, str) and data.strip():
                            self.module_logger.info(f"🔍 [诊断] 从部分观察中提取到数据: {data[:100]}...")
                            return data
                
                self.module_logger.warning(f"⚠️ [诊断] 没有成功的观察结果，也没有部分观察，返回fallback消息")
                return "抱歉，无法获取足够的信息来回答这个问题。"
            
            # 🚀 架构优化：统一使用RAGTool（内部使用RAGAgent）
            # ReasoningTool已移除，只检查RAG工具的结果
            for obs in successful_observations:
                if obs.get('tool_name') == 'rag' and obs.get('data'):
                    data = obs['data']
                    if isinstance(data, dict) and 'answer' in data:
                        answer = data['answer']
                        if answer and answer.strip():
                            # 🚀 修复：检查答案是否包含错误消息或"unable to determine"（包括中文版本）
                            answer_lower = answer.lower().strip()
                            answer_stripped = answer.strip()
                            # 检查英文和中文的"无法确定"
                            is_unable_to_determine = (
                                answer_lower == "unable to determine" or
                                answer_lower.startswith("unable to determine") or
                                answer_stripped == "无法确定" or
                                answer_stripped.startswith("无法确定") or
                                answer_stripped == "不确定" or
                                answer_stripped.startswith("不确定")
                            )
                            if ("Error processing query" in answer or 
                                answer.startswith("Error processing") or
                                is_unable_to_determine):
                                self.module_logger.warning(f"⚠️ [诊断] RAG工具返回无效答案，跳过此观察: {answer[:50]}")
                                continue # 跳过此观察，尝试下一个
                            
                            # 🚀 新增：进行二次答案提取和验证（确保答案质量）
                            # 🚀 优化：使用实例池获取推理引擎，避免重复初始化
                            reasoning_engine = None
                            try:
                                # 从实例池获取推理引擎实例
                                from src.utils.reasoning_engine_pool import get_reasoning_engine_pool
                                pool = get_reasoning_engine_pool()
                                reasoning_engine = pool.get_engine()
                                self.module_logger.info("✅ [答案优化] 从实例池获取推理引擎")
                                
                                # 获取查询类型（如果有）
                                query_type = None
                                if isinstance(data, dict):
                                    query_type = data.get('reasoning_type')
                                elif hasattr(data, 'reasoning_type'):
                                    query_type = getattr(data, 'reasoning_type', None)
                                
                                # 使用推理引擎的答案提取方法进行二次提取
                                optimized_answer = reasoning_engine._extract_answer_generic(
                                    query, answer, query_type=query_type
                                )
                                
                                if optimized_answer and optimized_answer.strip():
                                    # 检查优化后的答案是否与原始答案不同
                                    if optimized_answer.strip() != answer.strip():
                                        self.module_logger.info(f"✅ [答案优化] 答案已优化: 原始长度={len(answer)}, 优化后长度={len(optimized_answer)}")
                                        self.module_logger.info(f"✅ [答案优化] 原始答案: {answer[:100]}")
                                        self.module_logger.info(f"✅ [答案优化] 优化后答案: {optimized_answer[:100]}")
                                        answer = optimized_answer
                                    else:
                                        self.module_logger.info(f"ℹ️ [答案优化] 答案无需优化，使用原始答案")
                                else:
                                    self.module_logger.warning(f"⚠️ [答案优化] 答案优化失败，使用原始答案")
                            except Exception as e:
                                self.module_logger.warning(f"⚠️ [答案优化] 答案优化异常: {e}，使用原始答案", exc_info=True)
                                # 优化失败，使用原始答案（fallback）
                            finally:
                                # 🚀 优化：使用完后返回实例到池中
                                if reasoning_engine is not None:
                                    try:
                                        from src.utils.reasoning_engine_pool import get_reasoning_engine_pool
                                        pool = get_reasoning_engine_pool()
                                        pool.return_engine(reasoning_engine)
                                        self.module_logger.debug("✅ [答案优化] 推理引擎实例已返回池中")
                                    except Exception as e:
                                        self.module_logger.warning(f"⚠️ [答案优化] 返回推理引擎实例到池中失败: {e}")
                                        # 忽略错误，不影响主流程
                            
                            # 🚀 P0修复：在返回答案前，验证答案是否有效（使用NER验证）
                            # 如果答案包含换行符、列表项等无效内容，拒绝该答案
                            if answer and answer.strip():
                                import re
                                # 检查答案是否包含明显无效的内容
                                invalid_patterns = [
                                    r'\n',  # 包含换行符（可能是列表项）
                                    r'^\s*[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z]',  # 多个连续大写单词（可能是列表）
                                    r'(?:Hill|May|Naval|Affairs|Commit|Education|Facial)',  # 明显不是人名的词
                                ]
                                is_invalid = any(re.search(pattern, answer, re.IGNORECASE) for pattern in invalid_patterns)
                                if is_invalid:
                                    self.module_logger.warning(f"⚠️ [答案验证] 答案包含无效内容（换行符、列表项等），拒绝: {answer[:100]}")
                                    print(f"⚠️ [答案验证] 答案包含无效内容，拒绝: {answer[:100]}")
                                    # 不返回此答案，继续处理下一个观察结果
                                    continue
                            
                            self.module_logger.info(f"✅ [答案综合] 使用RAG工具返回的答案: {answer[:100]}...")
                            return answer.strip()
            
            # 否则，综合所有观察结果生成答案
            if self.llm_client:
                synthesize_prompt = f"""基于以下信息，回答用户的问题：

问题: {query}

收集到的信息:
{self._format_observations(successful_observations)}

请生成一个完整、准确的答案。"""
                
                try:
                    # 注意：_call_llm是同步方法，模型在初始化时已确定
                    import asyncio
                    # 在线程池中执行同步LLM调用，避免阻塞
                    if not self.llm_client:
                        return "无法生成答案（LLM客户端未初始化）"
                    else:
                        # 在lambda外捕获llm_client引用，避免类型检查问题
                        llm_client = self.llm_client
                        loop = asyncio.get_event_loop()
                        answer = await loop.run_in_executor(
                            None,
                            lambda: llm_client._call_llm(
                                synthesize_prompt,
                                dynamic_complexity="medium",  # 中等复杂度
                                max_tokens_override=500
                            )
                        )
                        return answer.strip() if answer else "无法生成答案"
                except Exception as e:
                    self.logger.warning(f"⚠️ 综合答案生成失败: {e}")
            
            # 回退：使用第一个成功的观察结果
            first_obs = successful_observations[0]
            if isinstance(first_obs.get('data'), dict):
                return str(first_obs['data'].get('answer', '无法生成答案'))
            else:
                return str(first_obs.get('data', '无法生成答案'))
                
        except Exception as e:
            self.logger.error(f"❌ 综合答案失败: {e}", exc_info=True)
            return "生成答案时出错"
    
    def _is_task_complete(self, thought: str, observations: List[Dict[str, Any]]) -> bool:
        """
        判断任务是否完成 - 🚀 优化：简化逻辑，提高判断准确性
        
        Args:
            thought: 当前思考（可选，如果为空字符串则只检查observations）
            observations: 已观察到的信息
            
        Returns:
            bool: 任务是否完成
        """
        # 🚀 优化：优先检查是否有成功的RAG结果（最可靠的判断依据）
        for obs in observations:
            # 🚀 架构优化：统一使用RAGTool（内部使用RAGAgent）
            # ReasoningTool已移除，只检查RAG工具的结果
            if (obs.get('success') and 
                obs.get('tool_name') == 'rag' and 
                obs.get('data') and 
                isinstance(obs['data'], dict) and 
                obs['data'].get('answer')):
                answer = obs['data'].get('answer', '')
                if answer and answer.strip():
                    answer_lower = answer.lower().strip()
                    answer_stripped = answer.strip()
                    # 🚀 修复：将"unable to determine"（包括中文版本）视为未完成
                    is_unable_to_determine = (
                        answer_lower == "unable to determine" or
                        answer_lower.startswith("unable to determine") or
                        answer_stripped == "无法确定" or
                        answer_stripped.startswith("无法确定") or
                        answer_stripped == "不确定" or
                        answer_stripped.startswith("不确定")
                    )
                    is_error = (
                        "error" in answer_lower or
                        "错误" in answer or
                        "抱歉" in answer or
                        answer_lower == "抱歉，无法获取足够的信息来回答这个问题。"
                    )
                    if not is_unable_to_determine and not is_error:
                        self.module_logger.info(f"✅ [诊断] 任务完成判断: 有成功的RAG结果，答案={answer[:50]}...")
                        return True
                    else:
                        self.module_logger.debug(f"🔍 [诊断] 任务完成判断: RAG结果无效（unable to determine或error），继续执行")
        
        # 🔧 优先级2: 只有在有观察结果的情况下，才检查thought中的完成关键词
        # 避免在第一次迭代时（没有观察结果）就错误判断任务完成
        if len(observations) == 0:
            self.module_logger.debug(f"🔍 [诊断] 任务完成判断: 无观察结果，返回False（避免第一次迭代就退出）")
            return False
        
        # 🔧 优先级2: 如果thought为空，只检查observations（用于快速判断）
        if not thought or not thought.strip():
            self.module_logger.debug(f"🔍 [诊断] 任务完成判断: thought为空，只检查observations，返回False")
            return False
        
        # 🔧 优先级2: 使用更精确的匹配规则，避免误判
        # 只检查明确的完成语句，而不是简单的关键词匹配
        import re
        complete_patterns = [
            r'任务.*已经.*完成',
            r'已经.*收集.*足够.*信息.*可以.*回答',
            r'可以.*生成.*最终.*答案',
            r'可以.*回答.*问题',
            r'已经.*获得.*足够.*信息'
        ]
        
        thought_lower = thought.lower()
        for pattern in complete_patterns:
            if re.search(pattern, thought_lower):
                # 进一步验证：确保有成功的观察结果
                has_successful_obs = any(obs.get('success') for obs in observations)
                if has_successful_obs:
                    self.module_logger.info(f"✅ [诊断] 任务完成判断: thought匹配完成模式，且有成功观察结果")
                    return True
                else:
                    self.module_logger.debug(f"🔍 [诊断] 任务完成判断: thought匹配完成模式，但无成功观察结果，返回False")
        
        # 🔧 优先级2: 如果thought中包含"需要"、"还需要"等关键词，说明任务未完成
        incomplete_keywords = ['需要', '还需要', '缺少', '不足', '无法', '不能']
        if any(keyword in thought for keyword in incomplete_keywords):
            self.module_logger.debug(f"🔍 [诊断] 任务完成判断: thought包含未完成关键词，返回False")
            return False
        
        self.module_logger.debug(f"🔍 [诊断] 任务完成判断: 默认返回False")
        return False
    
    def _has_valid_rag_answer(self, observations: List[Dict[str, Any]]) -> bool:
        """
        🚀 优化：检查是否已有有效的RAG答案（避免重复调用）
        
        Args:
            observations: 已观察到的信息
            
        Returns:
            bool: 是否有有效的RAG答案
        """
        return self._is_task_complete("", observations)  # 只检查observations，不依赖thought
    
    def _has_called_rag_tool(self, observations: List[Dict[str, Any]]) -> bool:
        """
        🚀 架构优化：RAGTool已移除，统一使用RealReasoningEngine
        此方法保留用于向后兼容，但实际检查的是reasoning工具
        
        Args:
            observations: 已观察到的信息
            
        Returns:
            bool: 是否已经调用过推理工具（原RAG工具）
        """
        # 🚀 架构优化：统一使用RAGTool（内部使用RAGAgent）
        # ReasoningTool已移除，只检查RAG工具
        return any(obs.get('tool_name') == 'rag' for obs in observations)
    
    def _get_dynamic_max_iterations(self, query: str) -> int:
        """
        🚀 优化：根据查询复杂度动态调整最大迭代次数
        🚀 重构：使用统一复杂度服务（LLM判断），消除硬编码关键词匹配
        
        Args:
            query: 查询文本
            
        Returns:
            int: 动态最大迭代次数
        """
        try:
            # 🚀 使用统一复杂度服务（优先使用LLM判断）
            from src.utils.unified_complexity_model_service import get_unified_complexity_model_service
            from src.utils.unified_centers import get_unified_config_center
            
            complexity_service = get_unified_complexity_model_service()
            config_center = get_unified_config_center()
            
            # 🚀 使用统一复杂度服务评估查询复杂度（优先使用LLM）
            complexity_result = complexity_service.assess_complexity(
                query=query,
                query_type=None,  # 可以后续从查询分析中获取
                evidence_count=0,  # ReAct Agent在开始时还没有证据
                use_cache=True  # 使用缓存提高性能
            )
            
            # 获取复杂度级别
            complexity_level = complexity_result.level.value  # 'simple', 'medium', 'complex'
            
            # 🚀 从统一配置中心获取迭代次数配置
            simple_max_iterations = config_center.get_config_value(
                'thresholds', 'react_agent.simple_max_iterations', 3
            )
            medium_max_iterations = config_center.get_config_value(
                'thresholds', 'react_agent.medium_max_iterations', 5
            )
            complex_max_iterations = config_center.get_config_value(
                'thresholds', 'react_agent.complex_max_iterations', 10
            )
            
            # 根据复杂度级别返回对应的迭代次数
            if complexity_level == 'simple':
                self.module_logger.info(
                    f"🚀 [优化] LLM判断为简单查询（评分: {complexity_result.score:.2f}），"
                    f"最大迭代次数: {simple_max_iterations}"
                )
                return simple_max_iterations
            elif complexity_level == 'medium':
                self.module_logger.info(
                    f"🚀 [优化] LLM判断为中等查询（评分: {complexity_result.score:.2f}），"
                    f"最大迭代次数: {medium_max_iterations}"
                )
                return medium_max_iterations
            else:  # complex
                self.module_logger.info(
                    f"🚀 [优化] LLM判断为复杂查询（评分: {complexity_result.score:.2f}），"
                    f"最大迭代次数: {complex_max_iterations}"
                )
                return complex_max_iterations
                
        except Exception as e:
            self.module_logger.warning(
                f"⚠️ 动态迭代次数计算失败（使用统一复杂度服务）: {e}，"
                f"使用默认值: {self.max_iterations}"
            )
            return self.max_iterations
    
    def _format_observations(self, observations: List[Dict[str, Any]]) -> str:
        """格式化观察结果"""
        if not observations:
            return ""
        
        formatted = []
        for i, obs in enumerate(observations, 1):
            tool_name = obs.get('tool_name', 'unknown')
            success = obs.get('success', False)
            data = obs.get('data', {})
            
            if success:
                if isinstance(data, dict) and 'answer' in data:
                    formatted.append(f"{i}. {tool_name}工具返回: {data['answer'][:200]}")
                else:
                    formatted.append(f"{i}. {tool_name}工具执行成功")
            else:
                error = obs.get('error', '未知错误')
                formatted.append(f"{i}. {tool_name}工具失败: {error}")
        
        return "\n".join(formatted)
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析JSON响应"""
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            return None

