#!/usr/bin/env python3
"""
专家Agent实现
各个领域的专家Agent
"""

import logging
from typing import Dict, Any, Optional

from src.agents.expert_agent import ExpertAgent
from backup_legacy_agents.base_agent import AgentResult
from backup_legacy_agents.react_agent import Action

# 🚀 修复循环导入：延迟导入RAGAgent，避免循环依赖
# from .rag_agent import RAGAgent  # 延迟导入，在需要时导入

logger = logging.getLogger(__name__)

# 🚀 修复循环导入：提供延迟导入函数
def get_rag_agent():
    """获取RAGAgent（延迟导入，避免循环依赖）"""
    from .rag_agent import RAGAgent
    return RAGAgent


class KnowledgeRetrievalAgent(ExpertAgent):
    """知识检索专家Agent
    
    🚀 修复：使用ExpertAgent基类的标准Agent循环（think -> plan_action -> execute_action -> is_task_complete）
    符合标准Agent定义，有完整的Agent状态管理（observations、thoughts、actions）
    """
    
    def __init__(self):
        super().__init__(
            agent_id="knowledge_retrieval_expert",
            domain_expertise="知识检索和信息收集",
            capability_level=0.9,
            collaboration_style="supportive"
        )
    
    def _get_service(self):
        """获取知识检索服务"""
        if self.service is None:
            from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
            self.service = KnowledgeRetrievalService()
        return self.service
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行任务 - 覆盖基类方法，直接调用Service以提高速度
        
        知识检索任务通常不需要复杂的Think-Plan-Act循环，
        直接调用Service可以显著减少延迟（省去2次LLM调用）。
        """
        import time
        start_time = time.time()
        
        try:
            # 记录开始
            logger.info(f"🚀 [KnowledgeRetrievalAgent] 快速执行模式: {self.agent_id}")
            
            # 获取服务
            service = self._get_service()
            
            # 准备参数
            query = context.get("query", "")
            
            # 直接调用Service
            # Service.execute 支持 (payload, context)
            result = await service.execute(query, context)
            
            # 记录结束
            execution_time = time.time() - start_time
            logger.info(f"✅ [KnowledgeRetrievalAgent] 执行完成, 耗时={execution_time:.2f}秒")
            
            # 确保返回 AgentResult
            if not isinstance(result, AgentResult):
                if isinstance(result, dict):
                    return AgentResult(
                        success=result.get("success", False),
                        data=result.get("data"),
                        confidence=result.get("confidence", 0.0),
                        error=result.get("error"),
                        processing_time=execution_time
                    )
                else:
                    return AgentResult(
                        success=True,
                        data=result,
                        confidence=1.0,
                        processing_time=execution_time
                    )
            
            # 更新处理时间
            result.processing_time = execution_time
            return result
            
        except Exception as e:
            logger.error(f"❌ [KnowledgeRetrievalAgent] 执行失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                confidence=0.0,
                processing_time=time.time() - start_time,
                error=str(e)
            )


class ReasoningAgent(ExpertAgent):
    """推理专家Agent
    
    🚀 修复：使用ExpertAgent基类的标准Agent循环（think -> plan_action -> execute_action -> is_task_complete）
    符合标准Agent定义，有完整的Agent状态管理（observations、thoughts、actions）
    """
    
    def __init__(self):
        super().__init__(
            agent_id="reasoning_expert",
            domain_expertise="逻辑推理和问题分析",
            capability_level=0.95,
            collaboration_style="analytical"
        )
    
    def _get_service(self):
        """获取推理服务"""
        if self.service is None:
            from src.services.reasoning_service import ReasoningService
            self.service = ReasoningService()
        return self.service
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行任务 - 覆盖基类方法，直接调用Service以提高速度
        
        推理任务通常是计算密集型的，但Agent层的Think-Plan-Act循环会引入不必要的LLM延迟。
        直接调用ReasoningService，让Service内部的ReasoningEngine处理推理逻辑。
        """
        import time
        start_time = time.time()
        
        try:
            # 记录开始
            logger.info(f"🚀 [ReasoningAgent] 快速执行模式: {self.agent_id}")
            
            # 获取服务
            service = self._get_service()
            
            # 准备参数
            # Service.execute 需要 context 包含 query
            if "query" not in context:
                # 尝试从输入参数中获取
                if "input" in context:
                    context["query"] = context["input"]
            
            # 直接调用Service
            result = await service.execute(context)
            
            # 记录结束
            execution_time = time.time() - start_time
            logger.info(f"✅ [ReasoningAgent] 执行完成, 耗时={execution_time:.2f}秒")
            
            # 确保返回 AgentResult
            if not isinstance(result, AgentResult):
                if isinstance(result, dict):
                    return AgentResult(
                        success=result.get("success", False),
                        data=result.get("data"),
                        confidence=result.get("confidence", 0.0),
                        error=result.get("error"),
                        processing_time=execution_time
                    )
                else:
                    return AgentResult(
                        success=True,
                        data=result,
                        confidence=1.0,
                        processing_time=execution_time
                    )
            
            # 更新处理时间
            result.processing_time = execution_time
            return result
            
        except Exception as e:
            logger.error(f"❌ [ReasoningAgent] 执行失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                confidence=0.0,
                processing_time=time.time() - start_time,
                error=str(e)
            )


class AnswerGenerationAgent(ExpertAgent):
    """答案生成专家Agent
    
    🚀 修复：使用ExpertAgent基类的标准Agent循环（think -> plan_action -> execute_action -> is_task_complete）
    符合标准Agent定义，有完整的Agent状态管理（observations、thoughts、actions）
    """
    
    def __init__(self):
        super().__init__(
            agent_id="answer_generation_expert",
            domain_expertise="答案生成和格式化",
            capability_level=0.9,
            collaboration_style="synthesizing"
        )
    
    def _get_service(self):
        """获取答案生成服务"""
        if self.service is None:
            from src.services.answer_generation_service import AnswerGenerationService
            self.service = AnswerGenerationService()
        return self.service
    
    # 🚀 修复：移除重写的execute()方法，使用ExpertAgent基类的标准Agent循环
    # 基类的_execute_action()已经有5分钟超时保护，满足答案生成任务需求


class CitationAgent(ExpertAgent):
    """引用专家Agent
    
    🚀 修复：使用ExpertAgent基类的标准Agent循环（think -> plan_action -> execute_action -> is_task_complete）
    符合标准Agent定义，有完整的Agent状态管理（observations、thoughts、actions）
    """
    
    def __init__(self):
        super().__init__(
            agent_id="citation_expert",
            domain_expertise="引用和来源生成",
            capability_level=0.85,
            collaboration_style="supportive"
        )
    
    def _get_service(self):
        """获取引用服务"""
        if self.service is None:
            from src.services.citation_service import CitationService
            self.service = CitationService()
        return self.service
    
    async def _plan_action(self, thought: str, query: str, dependencies: Dict) -> Optional[Action]:
        """规划行动阶段 - 为CitationAgent准备answer和knowledge参数
        
        🚀 方案1：优先使用Tools，如果不可用则使用Service
        """
        # 🚀 方案1：优先使用Tools
        if self.tool_registry:
            tool_name = "citation"
            if self.tool_registry.get_tool(tool_name):
                logger.debug(f"🚀 [CitationAgent] 使用工具: {tool_name}")
                # CitationTool需要content和sources
                answer = dependencies.get("answer", "") or query
                knowledge = dependencies.get("knowledge", []) or dependencies.get("sources", [])
                return Action(
                    tool_name=tool_name,
                    params={
                        "content": answer,
                        "sources": knowledge,
                        "context": dependencies
                    },
                    reasoning=thought
                )
        
        # 回退到Service（原有逻辑）
        # CitationService需要answer和knowledge
        answer = dependencies.get("answer", "") or query
        knowledge = dependencies.get("knowledge", [])
        
        # 尝试从dependencies中提取knowledge（支持多种格式）
        if not knowledge:
            knowledge_retrieval_result = dependencies.get("knowledge_retrieval", {})
            if isinstance(knowledge_retrieval_result, dict):
                result_obj = knowledge_retrieval_result.get("result")
                if hasattr(result_obj, 'data') and isinstance(result_obj.data, dict):
                    knowledge = result_obj.data.get("sources", [])
                elif isinstance(result_obj, dict):
                    knowledge = result_obj.get("data", {}).get("sources", [])
        
        return Action(
            tool_name="service_call",
            params={
                "query": query,
                "answer": answer,
                "knowledge": knowledge,
                **dependencies
            },
            reasoning=thought
        )
    
    # 🚀 修复：移除重写的execute()方法，使用ExpertAgent基类的标准Agent循环
    # 基类的_execute_action()已经有5分钟超时保护，满足引用生成任务需求


class MemoryAgent(ExpertAgent):
    """记忆专家Agent - 负责上下文和记忆管理"""
    
    def __init__(self):
        super().__init__(
            agent_id="memory_expert",
            domain_expertise="上下文工程和记忆管理",
            capability_level=0.95,
            collaboration_style="supportive"
        )
    
    def _get_service(self):
        """获取上下文工程中心服务"""
        if self.service is None:
            # 🚀 修复：UnifiedContextEngineeringCenter的初始化已经改为延迟加载模式
            # 不再在初始化时加载长期上下文，避免阻塞事件循环
            from src.utils.unified_context_engineering_center import UnifiedContextEngineeringCenter
            self.service = UnifiedContextEngineeringCenter()
        return self.service
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行记忆管理任务 - 管理上下文和记忆
        
        🚀 注意：MemoryAgent直接实现execute方法，不通过ExpertAgent的标准流程，
        因为UnifiedContextEngineeringCenter不是Service，没有execute方法。
        """
        import time
        start_time = time.time()
        
        if not self.service:
            self.service = self._get_service()
        
        # 解析任务类型
        task_type = context.get("task_type", "retrieve")
        session_id = context.get("session_id", "default")
        
        try:
            import asyncio
            
            # 根据任务类型执行不同的操作
            if task_type == "store":
                # 存储上下文片段
                content = context.get("content", "")
                category_str = context.get("category", "informational")
                scope_str = context.get("scope", "short_term")
                source_str = context.get("source", "user_input")
                metadata = context.get("metadata", {})
                
                # 转换字符串为枚举类型
                from src.utils.unified_context_engineering_center import (
                    ContextCategory, ContextScope, ContextSource
                )
                
                category_map = {
                    "guiding": ContextCategory.GUIDING,
                    "informational": ContextCategory.INFORMATIONAL,
                    "actionable": ContextCategory.ACTIONABLE
                }
                scope_map = {
                    "short_term": ContextScope.SHORT_TERM,
                    "long_term": ContextScope.LONG_TERM,
                    "implicit": ContextScope.IMPLICIT
                }
                source_map = {
                    "user_input": ContextSource.USER_INPUT,
                    "system_log": ContextSource.SYSTEM_LOG,
                    "knowledge_base": ContextSource.KNOWLEDGE_BASE,
                    "tool_definition": ContextSource.TOOL_DEFINITION,
                    "tool_call": ContextSource.TOOL_CALL,
                    "tool_result": ContextSource.TOOL_RESULT,
                    "environment": ContextSource.ENVIRONMENT
                }
                
                category = category_map.get(category_str, ContextCategory.INFORMATIONAL)
                scope = scope_map.get(scope_str, ContextScope.SHORT_TERM)
                source = source_map.get(source_str, ContextSource.USER_INPUT)
                
                # 调用Service的同步方法，添加超时保护
                try:
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: self.service.add_context_fragment(
                                session_id=session_id,
                                content=content,
                                category=category,
                                scope=scope,
                                source=source,
                                metadata=metadata
                            )
                        ),
                        timeout=60.0  # 1分钟超时
                    )
                    
                    return AgentResult(
                        success=True,
                        data={"fragment_id": result, "session_id": session_id},
                        confidence=0.9,
                        processing_time=time.time() - start_time
                    )
                except asyncio.TimeoutError:
                    logger.error(f"❌ MemoryAgent存储上下文超时（1分钟）")
                    return AgentResult(
                        success=False,
                        data=None,
                        error="存储上下文超时（1分钟）",
                        confidence=0.0,
                        processing_time=time.time() - start_time
                    )
            
            elif task_type == "retrieve":
                # 检索上下文 - 使用get_enhanced_context方法
                max_fragments = context.get("max_fragments", 20)
                
                try:
                    loop = asyncio.get_event_loop()
                    enhanced_context = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: self.service.get_enhanced_context(
                                session_id=session_id,
                                max_fragments=max_fragments
                            )
                        ),
                        timeout=60.0  # 1分钟超时
                    )
                    
                    # 提取fragments（从字典中提取）
                    fragments_data = enhanced_context.get("fragments", [])
                    # fragments_data 是字典列表，不是ContextFragment对象
                    fragments = fragments_data
                    if max_fragments and len(fragments) > max_fragments:
                        fragments = fragments[:max_fragments]
                    
                    return AgentResult(
                        success=True,
                        data={
                            "fragments": fragments,
                            "count": len(fragments),
                            "session_id": session_id,
                            "enhanced_context": enhanced_context
                        },
                        confidence=0.9,
                        processing_time=time.time() - start_time
                    )
                except asyncio.TimeoutError:
                    logger.error(f"❌ MemoryAgent检索上下文超时（1分钟）")
                    return AgentResult(
                        success=False,
                        data=None,
                        error="检索上下文超时（1分钟）",
                        confidence=0.0,
                        processing_time=time.time() - start_time
                    )
            
            elif task_type == "get_enhanced_context":
                # 获取增强上下文（用于推理）
                max_fragments = context.get("max_fragments", None) or context.get("max_length", 8000)
                
                try:
                    loop = asyncio.get_event_loop()
                    enhanced_context = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: self.service.get_enhanced_context(
                                session_id=session_id,
                                max_fragments=max_fragments
                            )
                        ),
                        timeout=60.0  # 1分钟超时
                    )
                    
                    return AgentResult(
                        success=True,
                        data={
                            "enhanced_context": enhanced_context,
                            "session_id": session_id
                        },
                        confidence=0.95,
                        processing_time=time.time() - start_time
                    )
                except asyncio.TimeoutError:
                    logger.error(f"❌ MemoryAgent获取增强上下文超时（1分钟）")
                    return AgentResult(
                        success=False,
                        data=None,
                        error="获取增强上下文超时（1分钟）",
                        confidence=0.0,
                        processing_time=time.time() - start_time
                    )
            
            else:
                return AgentResult(
                    success=False,
                    data=None,
                    error=f"未知的任务类型: {task_type}",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"记忆管理服务调用失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )


class MultimodalAgent(ExpertAgent):
    """多模态处理专家Agent - 处理图像、音频、视频等多模态内容
    
    🚀 修复：使用ExpertAgent基类的标准Agent循环（think -> plan_action -> execute_action -> is_task_complete）
    符合标准Agent定义，有完整的Agent状态管理（observations、thoughts、actions）
    """
    
    def __init__(self):
        super().__init__(
            agent_id="multimodal_expert",
            domain_expertise="多模态内容处理和分析",
            capability_level=0.9,
            collaboration_style="supportive"
        )
    
    def _get_service(self):
        """获取多模态处理服务"""
        if self.service is None:
            from src.services.multimodal_service import MultimodalService
            self.service = MultimodalService()
        return self.service
    
    async def _plan_action(self, thought: str, query: str, dependencies: Dict) -> Optional[Action]:
        """规划行动阶段 - 为MultimodalAgent准备task_type、input_data和modality参数
        
        🚀 修复：重写_plan_action方法，从dependencies中提取多模态相关参数
        """
        # 获取任务类型和输入数据
        task_type = dependencies.get("task_type", "process")
        input_data = dependencies.get("input_data") or dependencies.get("data") or dependencies.get("content")
        modality = dependencies.get("modality", "auto")  # auto, image, audio, video
        
        return Action(
            tool_name="service_call",
            params={
                "query": query,
                "task_type": task_type,
                "input_data": input_data,
                "modality": modality,
                **dependencies
            },
            reasoning=thought
        )
    
    # 🚀 修复：移除重写的execute()方法，使用ExpertAgent基类的标准Agent循环
    # 基类的_execute_action()已经有5分钟超时保护，满足多模态处理任务需求


# 🚀 新增：提示词工程和上下文工程智能体
# 注意：为了避免循环导入，这里使用延迟导入
def _get_prompt_engineering_agent():
    """延迟导入PromptEngineeringAgent"""
    from .prompt_engineering_agent import PromptEngineeringAgent as PromptAgentImpl
    return PromptAgentImpl

def _get_context_engineering_agent():
    """延迟导入ContextEngineeringAgent"""
    from .context_engineering_agent import ContextEngineeringAgent as ContextAgentImpl
    return ContextAgentImpl


class PromptEngineeringAgent(ExpertAgent):
    """提示词工程专家Agent - 自我学习和优化提示词"""
    
    def __init__(self):
        super().__init__(
            agent_id="prompt_engineering_expert",
            domain_expertise="提示词工程和模板优化",
            capability_level=0.95,
            collaboration_style="analytical"
        )
        # 实际的Agent实现（延迟初始化）
        self._prompt_agent_impl = None
    
    def _get_service(self):
        """获取提示词工程服务"""
        if self._prompt_agent_impl is None:
            PromptAgentImpl = _get_prompt_engineering_agent()
            self._prompt_agent_impl = PromptAgentImpl()
        return self._prompt_agent_impl
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行提示词工程任务"""
        if not self._prompt_agent_impl:
            self._prompt_agent_impl = self._get_service()
        
        # 直接调用PromptEngineeringAgent的execute方法
        return await self._prompt_agent_impl.execute(context)


class ContextEngineeringAgent(ExpertAgent):
    """上下文工程专家Agent - 管理长期记忆和上下文"""
    
    def __init__(self):
        super().__init__(
            agent_id="context_engineering_expert",
            domain_expertise="上下文工程和长期记忆管理",
            capability_level=0.95,
            collaboration_style="supportive"
        )
        # 实际的Agent实现（延迟初始化）
        self._context_agent_impl = None
    
    def _get_service(self):
        """获取上下文工程服务"""
        if self._context_agent_impl is None:
            ContextAgentImpl = _get_context_engineering_agent()
            self._context_agent_impl = ContextAgentImpl()
        return self._context_agent_impl
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行上下文工程任务"""
        if not self._context_agent_impl:
            self._context_agent_impl = self._get_service()
        
        # 直接调用ContextEngineeringAgent的execute方法
        return await self._context_agent_impl.execute(context)


class PromptEngineeringAgent(ExpertAgent):
    """提示词工程专家Agent - 自我学习和优化提示词"""
    
    def __init__(self):
        super().__init__(
            agent_id="prompt_engineering_expert",
            domain_expertise="提示词工程和模板优化",
            capability_level=0.95,
            collaboration_style="analytical"
        )
    
    def _get_service(self):
        """获取提示词工程服务"""
        if self.service is None:
            from .prompt_engineering_agent import PromptEngineeringAgent as PromptAgent
            # 注意：这里返回的是实际的Agent实例，不是Service
            # 因为PromptEngineeringAgent直接实现了execute方法
            self.service = PromptAgent()
        return self.service
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行提示词工程任务"""
        if not self.service:
            self.service = self._get_service()
        
        # 直接调用PromptEngineeringAgent的execute方法
        return await self.service.execute(context)


class ContextEngineeringAgent(ExpertAgent):
    """上下文工程专家Agent - 管理长期记忆和上下文"""
    
    def __init__(self):
        super().__init__(
            agent_id="context_engineering_expert",
            domain_expertise="上下文工程和长期记忆管理",
            capability_level=0.95,
            collaboration_style="supportive"
        )
    
    def _get_service(self):
        """获取上下文工程服务"""
        if self.service is None:
            from .context_engineering_agent import ContextEngineeringAgent as ContextAgent
            # 注意：这里返回的是实际的Agent实例，不是Service
            # 因为ContextEngineeringAgent直接实现了execute方法
            self.service = ContextAgent()
        return self.service
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行上下文工程任务"""
        if not self.service:
            self.service = self._get_service()
        
        # 直接调用ContextEngineeringAgent的execute方法
        return await self.service.execute(context)
