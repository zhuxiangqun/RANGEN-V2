"""
详细处理节点模块 - 将原有系统的内部处理步骤显式化为独立节点
包括：查询分析、调度优化、知识检索、推理分析、答案生成、引用生成等
"""
import logging
import time
import asyncio
from typing import Dict, Any, Optional, List
from src.core.langgraph_unified_workflow import ResearchSystemState

logger = logging.getLogger(__name__)


class DetailedProcessingNodes:
    """详细处理节点集合 - 显式化原有系统的内部处理步骤"""
    
    def __init__(self, system=None):
        """初始化详细处理节点
        
        Args:
            system: UnifiedResearchSystem 实例（必需）
        """
        self.system = system
        if not system:
            logger.warning("⚠️ 详细处理节点需要 system 实例，某些功能可能不可用")
    
    async def query_analysis_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """查询分析节点
        
        分析查询类型和复杂度，为后续调度优化提供依据
        🚀 使用统一复杂度服务（LLM判断）进行复杂度评估
        """
        logger.info("🔍 [Query Analysis] 开始查询分析（使用LLM判断复杂度）...")
        start_time = time.time()
        
        try:
            query = state.get('query', '')
            if not query:
                state['error'] = "查询为空，无法进行分析"
                state['errors'].append({
                    'node': 'query_analysis',
                    'error': state['error'],
                    'timestamp': time.time()
                })
                return state
            
            query_length = len(query)
            
            # 🚀 使用统一复杂度服务（LLM判断）进行复杂度评估
            query_complexity = 'medium'
            complexity_score = 0.0
            query_type = 'general'
            
            try:
                from src.utils.unified_complexity_model_service import get_unified_complexity_model_service
                complexity_service = get_unified_complexity_model_service()
                
                # 调用统一复杂度服务（优先使用LLM判断）
                complexity_result = complexity_service.assess_complexity(
                    query=query,
                    query_type=None,
                    evidence_count=0,
                    use_cache=True
                )
                
                # 提取复杂度信息
                query_complexity = complexity_result.level.value  # 'simple', 'medium', 'complex'
                complexity_score = complexity_result.score  # 0-10 分数
                
                logger.info(f"✅ [Query Analysis] LLM复杂度判断: {query_complexity} (评分: {complexity_score:.2f})")
                
            except Exception as e:
                logger.warning(f"⚠️ [Query Analysis] 统一复杂度服务失败: {e}，使用fallback规则")
                # Fallback: 简单的规则判断
                query_lower = query.lower()
                if query_length < 50:
                    query_complexity = 'simple'
                    complexity_score = 2.0
                elif query_length > 150 or query.count(' and ') > 1:
                    query_complexity = 'complex'
                    complexity_score = 8.0
                elif query.count("'s ") > 2:
                    query_complexity = 'very_complex'
                    complexity_score = 9.0
                else:
                    query_complexity = 'medium'
                    complexity_score = 5.0
            
            # 🚀 推断查询类型（用于调度优化）
            query_lower = query.lower()
            if any(kw in query_lower for kw in ['same as', 'mother', 'father', 'named after']):
                query_type = 'multi_hop'
            elif any(kw in query_lower for kw in ['compare', 'difference', 'vs']):
                query_type = 'comparative'
            elif any(kw in query_lower for kw in ['why', 'because', 'cause']):
                query_type = 'causal'
            elif any(kw in query_lower for kw in ['how many', 'how much', 'number']):
                query_type = 'numerical'
            elif any(kw in query_lower for kw in ['who', 'what', 'when', 'where']):
                query_type = 'factual'
            else:
                query_type = 'general'
            
            # 更新状态
            state['query_type'] = query_type
            state['query_complexity'] = query_complexity
            state['query_length'] = query_length
            state['complexity_score'] = complexity_score  # 更新复杂度分数（0-10）
            
            # 记录元数据
            if 'metadata' not in state:
                state['metadata'] = {}
            state['metadata']['query_analysis'] = {
                'query_type': query_type,
                'query_complexity': query_complexity,
                'query_length': query_length,
                'complexity_score': complexity_score,
                'used_llm': True  # 标记是否使用了LLM判断
            }
            
            logger.info(f"✅ [Query Analysis] 分析完成: 类型={query_type}, 复杂度={query_complexity} (LLM评分: {complexity_score:.2f}), 长度={query_length}")
            
        except Exception as e:
            error_msg = f"查询分析失败: {str(e)}"
            logger.error(f"❌ [Query Analysis] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'query_analysis',
                'error': error_msg,
                'timestamp': time.time()
            })
            # 设置默认值
            state['query_type'] = 'general'
            state['query_complexity'] = 'medium'
            state['complexity_score'] = 5.0
        
        finally:
            execution_time = time.time() - start_time
            # 🚀 修复：确保 node_execution_times 和 node_times 存在
            if 'node_execution_times' not in state:
                state['node_execution_times'] = {}
            if 'node_times' not in state:
                state['node_times'] = {}
            state['node_execution_times']['query_analysis'] = execution_time
            state['node_times']['query_analysis'] = execution_time
        
        return state
    
    async def scheduling_optimization_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """调度优化节点
        
        使用 ML/RL 调度优化器选择最优调度策略
        """
        logger.info("⚙️ [Scheduling Optimization] 开始调度优化...")
        start_time = time.time()
        
        try:
            if not self.system:
                logger.warning("⚠️ [Scheduling Optimization] 系统实例不可用，使用默认策略")
                state['scheduling_strategy'] = 'default'
                return state
            
            query_type = state.get('query_type', 'general')
            query_complexity = state.get('query_complexity', 'medium')
            query_length = state.get('query_length', 0)
            
            ml_strategy = None
            rl_action = None
            
            # ML 调度优化
            if hasattr(self.system, 'ml_scheduling_optimizer') and self.system.ml_scheduling_optimizer:
                try:
                    ml_strategy = self.system.ml_scheduling_optimizer.get_optimal_strategy(
                        query=state.get('query', ''),
                        query_type=query_type,
                        query_complexity=query_complexity
                    )
                    logger.info(f"✅ [Scheduling Optimization] ML策略: 知识超时={ml_strategy.knowledge_timeout}s, 推理超时={ml_strategy.reasoning_timeout}s, 并行={ml_strategy.parallel_knowledge_reasoning}")
                except Exception as e:
                    logger.debug(f"ML调度优化失败: {e}")
            
            # RL 调度优化
            if hasattr(self.system, 'rl_scheduling_optimizer') and self.system.rl_scheduling_optimizer:
                try:
                    from src.utils.rl_scheduling_optimizer import SchedulingState
                    rl_state = SchedulingState(
                        query_type=query_type,
                        query_complexity=query_complexity,
                        query_length=query_length,
                        has_knowledge=False,
                        knowledge_quality=0.0
                    )
                    rl_action = self.system.rl_scheduling_optimizer.select_action(rl_state)
                    logger.info(f"✅ [Scheduling Optimization] RL策略: 知识超时={rl_action.knowledge_timeout}s, 推理超时={rl_action.reasoning_timeout}s, 并行={rl_action.parallel_execution}")
                except Exception as e:
                    logger.debug(f"RL调度优化失败: {e}")
            
            # 更新状态
            scheduling_strategy = {
                'ml_strategy': ml_strategy,
                'rl_action': rl_action,
                'strategy_type': 'ml' if ml_strategy else ('rl' if rl_action else 'default')
            }
            state['scheduling_strategy'] = scheduling_strategy
            
            # 记录元数据
            if 'metadata' not in state:
                state['metadata'] = {}
            state['metadata']['scheduling_optimization'] = {
                'strategy_type': scheduling_strategy['strategy_type'],
                'knowledge_timeout': (ml_strategy.knowledge_timeout if ml_strategy else (rl_action.knowledge_timeout if rl_action else 12.0)),
                'reasoning_timeout': (ml_strategy.reasoning_timeout if ml_strategy else (rl_action.reasoning_timeout if rl_action else 200.0)),
                'parallel_execution': (ml_strategy.parallel_knowledge_reasoning if ml_strategy else (rl_action.parallel_execution if rl_action else False))
            }
            
            logger.info(f"✅ [Scheduling Optimization] 调度优化完成: 策略类型={scheduling_strategy['strategy_type']}")
            
        except Exception as e:
            error_msg = f"调度优化失败: {str(e)}"
            logger.error(f"❌ [Scheduling Optimization] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'scheduling_optimization',
                'error': error_msg,
                'timestamp': time.time()
            })
            # 设置默认策略
            state['scheduling_strategy'] = {'strategy_type': 'default'}
        
        finally:
            execution_time = time.time() - start_time
            # 🚀 修复：确保 node_execution_times 和 node_times 存在
            if 'node_execution_times' not in state:
                state['node_execution_times'] = {}
            if 'node_times' not in state:
                state['node_times'] = {}
            state['node_execution_times']['scheduling_optimization'] = execution_time
            state['node_times']['scheduling_optimization'] = execution_time
        
        return state
    
    async def knowledge_retrieval_detailed_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """知识检索详细节点
        
        执行知识检索，显式展示检索过程
        """
        logger.info("📚 [Knowledge Retrieval] 开始知识检索...")
        start_time = time.time()
        
        try:
            if not self.system:
                logger.warning("⚠️ [Knowledge Retrieval] 系统实例不可用")
                state['evidence'] = []
                state['knowledge'] = []
                return state
            
            query = state.get('query', '')
            if not query:
                state['error'] = "查询为空，无法进行知识检索"
                state['errors'].append({
                    'node': 'knowledge_retrieval_detailed',
                    'error': state['error'],
                    'timestamp': time.time()
                })
                return state
            
            # 获取调度策略
            scheduling_strategy = state.get('scheduling_strategy', {})
            knowledge_timeout = 12.0
            if scheduling_strategy.get('ml_strategy'):
                knowledge_timeout = scheduling_strategy['ml_strategy'].knowledge_timeout
            elif scheduling_strategy.get('rl_action'):
                knowledge_timeout = scheduling_strategy['rl_action'].knowledge_timeout
            
            # 创建知识检索上下文
            knowledge_context = {
                "query": query,
                "type": "knowledge_retrieval"
            }
            
            # 执行知识检索
            knowledge_result = None
            if self.system.tool_registry and self.system.tool_registry.get_tool("knowledge_retrieval"):
                # 使用工具
                try:
                    if hasattr(self.system, '_execute_tool_with_timeout'):
                        knowledge_result = await self.system._execute_tool_with_timeout(
                            "knowledge_retrieval",
                            {"query": query, "context": knowledge_context},
                            "knowledge_retrieval",
                            timeout=knowledge_timeout
                        )
                    else:
                        # 降级：直接调用工具
                        knowledge_tool = self.system.tool_registry.get_tool("knowledge_retrieval")
                        knowledge_result = await knowledge_tool.execute({"query": query, "context": knowledge_context})
                except Exception as e:
                    logger.warning(f"⚠️ [Knowledge Retrieval] 工具执行失败: {e}")
                    knowledge_result = None
            
            if not knowledge_result and hasattr(self.system, '_knowledge_agent') and self.system._knowledge_agent:
                # 使用 Agent
                try:
                    if hasattr(self.system, '_execute_agent_with_timeout'):
                        knowledge_result = await self.system._execute_agent_with_timeout(
                            self.system._knowledge_agent,
                            knowledge_context,
                            "knowledge_retrieval",
                            timeout=knowledge_timeout
                        )
                    else:
                        # 降级：直接调用 Agent
                        knowledge_result = await self.system._knowledge_agent.execute(knowledge_context)
                except Exception as e:
                    logger.warning(f"⚠️ [Knowledge Retrieval] Agent执行失败: {e}")
                    knowledge_result = None
            
            if not knowledge_result:
                # 🚀 优化：如果已有答案（简单查询已成功），这是正常行为，降低警告级别
                if state.get('answer') or state.get('final_answer'):
                    logger.info("ℹ️ [Knowledge Retrieval] 知识检索工具和Agent都不可用（已有答案，这是正常行为）")
                else:
                    logger.warning("⚠️ [Knowledge Retrieval] 知识检索工具和Agent都不可用或执行失败")
                state['evidence'] = []
                state['knowledge'] = []
                return state
            
            # 处理知识检索结果
            if isinstance(knowledge_result, Exception):
                logger.error(f"❌ [Knowledge Retrieval] 知识检索失败: {knowledge_result}")
                state['evidence'] = []
                state['knowledge'] = []
                state['error'] = str(knowledge_result)
            elif hasattr(knowledge_result, 'success') and knowledge_result.success:
                # 提取知识
                knowledge_list = []
                if hasattr(knowledge_result, 'data'):
                    knowledge_data = knowledge_result.data
                    if isinstance(knowledge_data, dict):
                        sources = knowledge_data.get('sources', [])
                        if sources:
                            for source_item in sources:
                                if isinstance(source_item, dict):
                                    result_obj = source_item.get('result')
                                    if result_obj and hasattr(result_obj, 'data'):
                                        source_data = result_obj.data
                                        if isinstance(source_data, list):
                                            knowledge_list.extend(source_data)
                        else:
                            knowledge_list = knowledge_data.get('knowledge', [])
                    elif isinstance(knowledge_data, list):
                        knowledge_list = knowledge_data
                
                state['evidence'] = knowledge_list
                state['knowledge'] = knowledge_list
                logger.info(f"✅ [Knowledge Retrieval] 检索完成，找到 {len(knowledge_list)} 条知识")
            else:
                logger.warning("⚠️ [Knowledge Retrieval] 知识检索未成功")
                state['evidence'] = []
                state['knowledge'] = []
            
        except Exception as e:
            error_msg = f"知识检索失败: {str(e)}"
            logger.error(f"❌ [Knowledge Retrieval] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'knowledge_retrieval_detailed',
                'error': error_msg,
                'timestamp': time.time()
            })
            state['evidence'] = []
            state['knowledge'] = []
        
        finally:
            execution_time = time.time() - start_time
            # 🚀 修复：确保 node_execution_times 和 node_times 存在
            if 'node_execution_times' not in state:
                state['node_execution_times'] = {}
            if 'node_times' not in state:
                state['node_times'] = {}
            state['node_execution_times']['knowledge_retrieval_detailed'] = execution_time
            state['node_times']['knowledge_retrieval_detailed'] = execution_time
        
        return state
    
    async def reasoning_analysis_detailed_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """推理分析详细节点
        
        执行推理分析，显式展示推理过程
        """
        logger.info("🧠 [Reasoning Analysis] 开始推理分析...")
        start_time = time.time()
        
        try:
            if not self.system:
                logger.warning("⚠️ [Reasoning Analysis] 系统实例不可用")
                return state
            
            query = state.get('query', '')
            if not query:
                state['error'] = "查询为空，无法进行推理分析"
                state['errors'].append({
                    'node': 'reasoning_analysis_detailed',
                    'error': state['error'],
                    'timestamp': time.time()
                })
                return state
            
            # 获取调度策略
            scheduling_strategy = state.get('scheduling_strategy', {})
            reasoning_timeout = 200.0
            if scheduling_strategy.get('ml_strategy'):
                reasoning_timeout = scheduling_strategy['ml_strategy'].reasoning_timeout
            elif scheduling_strategy.get('rl_action'):
                reasoning_timeout = scheduling_strategy['rl_action'].reasoning_timeout
            
            # 构建推理上下文
            reasoning_context = {
                "query": query,
                "knowledge": state.get('knowledge', []),
                "knowledge_data": state.get('knowledge', []),
                "type": "reasoning_analysis",
                "preliminary": False
            }
            
            # 执行推理分析
            reasoning_result = None
            if self.system.tool_registry and self.system.tool_registry.get_tool("rag"):
                # 使用 RAG 工具
                try:
                    if hasattr(self.system, '_execute_tool_with_timeout'):
                        reasoning_result = await self.system._execute_tool_with_timeout(
                            "rag",
                            {"query": query, "context": reasoning_context},
                            "reasoning_analysis",
                            timeout=reasoning_timeout
                        )
                    else:
                        # 降级：直接调用工具
                        rag_tool = self.system.tool_registry.get_tool("rag")
                        reasoning_result = await rag_tool.execute({"query": query, "context": reasoning_context})
                except Exception as e:
                    logger.warning(f"⚠️ [Reasoning Analysis] 工具执行失败: {e}")
                    reasoning_result = None
            
            if not reasoning_result and hasattr(self.system, '_reasoning_agent') and self.system._reasoning_agent:
                # 使用推理 Agent
                try:
                    if hasattr(self.system, '_execute_agent_with_timeout'):
                        reasoning_result = await self.system._execute_agent_with_timeout(
                            self.system._reasoning_agent,
                            reasoning_context,
                            "reasoning_analysis",
                            timeout=reasoning_timeout
                        )
                    else:
                        # 降级：直接调用 Agent
                        reasoning_result = await self.system._reasoning_agent.execute(reasoning_context)
                except Exception as e:
                    logger.warning(f"⚠️ [Reasoning Analysis] Agent执行失败: {e}")
                    reasoning_result = None
            
            if not reasoning_result:
                # 🚀 优化：如果已有答案（简单查询已成功），这是正常行为，降低警告级别
                if state.get('answer') or state.get('final_answer'):
                    logger.info("ℹ️ [Reasoning Analysis] 推理工具和Agent都不可用（已有答案，这是正常行为）")
                else:
                    logger.warning("⚠️ [Reasoning Analysis] 推理工具和Agent都不可用或执行失败")
                return state
            
            # 处理推理结果
            if isinstance(reasoning_result, Exception):
                logger.error(f"❌ [Reasoning Analysis] 推理分析失败: {reasoning_result}")
                state['error'] = str(reasoning_result)
            elif hasattr(reasoning_result, 'success') and reasoning_result.success:
                # 提取推理答案
                reasoning_answer = None
                if hasattr(reasoning_result, 'final_answer'):
                    reasoning_answer = getattr(reasoning_result, 'final_answer', '')
                elif hasattr(reasoning_result, 'data'):
                    reasoning_data = reasoning_result.data
                    if isinstance(reasoning_data, str):
                        reasoning_answer = reasoning_data.strip()
                    elif isinstance(reasoning_data, dict):
                        reasoning_answer = (
                            reasoning_data.get('answer', '') or
                            reasoning_data.get('result', '') or
                            reasoning_data.get('reasoning', '') or
                            reasoning_data.get('final_answer', '')
                        )
                
                if reasoning_answer:
                    state['answer'] = reasoning_answer
                    state.setdefault('reasoning_answer', [])
                    state['reasoning_answer'].append(str(reasoning_answer))
                    logger.info(f"✅ [Reasoning Analysis] 推理完成，答案长度: {len(reasoning_answer)}")
                else:
                    logger.warning("⚠️ [Reasoning Analysis] 推理完成但未提取到答案")
            
        except Exception as e:
            error_msg = f"推理分析失败: {str(e)}"
            logger.error(f"❌ [Reasoning Analysis] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'reasoning_analysis_detailed',
                'error': error_msg,
                'timestamp': time.time()
            })
        
        finally:
            execution_time = time.time() - start_time
            # 🚀 修复：确保 node_execution_times 和 node_times 存在
            if 'node_execution_times' not in state:
                state['node_execution_times'] = {}
            if 'node_times' not in state:
                state['node_times'] = {}
            state['node_execution_times']['reasoning_analysis_detailed'] = execution_time
            state['node_times']['reasoning_analysis_detailed'] = execution_time
        
        return state
    
    async def answer_generation_detailed_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """答案生成详细节点
        
        生成最终答案，显式展示答案生成过程
        """
        logger.info("📝 [Answer Generation] 开始答案生成...")
        start_time = time.time()
        
        try:
            # 如果已经有答案（从推理分析获得），可以跳过或优化
            if state.get('answer'):
                logger.info("✅ [Answer Generation] 已有答案，跳过生成")
                state['final_answer'] = state['answer']
                return state
            
            # 使用答案生成 Agent
            if self.system and hasattr(self.system, '_answer_agent') and self.system._answer_agent:
                context = {
                    "query": state.get('query', ''),
                    "evidence": state.get('evidence', []),
                    "knowledge": state.get('knowledge', []),
                    "reasoning": state.get('reasoning_answer', '')
                }
                
                result = await self.system._answer_agent.execute(context)
                
                if result.success and hasattr(result, 'data'):
                    answer_data = result.data
                    if isinstance(answer_data, dict):
                        state['final_answer'] = answer_data.get('answer', '')
                    elif isinstance(answer_data, str):
                        state['final_answer'] = answer_data
                    logger.info(f"✅ [Answer Generation] 答案生成完成，长度: {len(state.get('final_answer', ''))}")
                else:
                    logger.warning("⚠️ [Answer Generation] 答案生成未成功")
                    state['final_answer'] = state.get('answer', '')
            else:
                # 降级：使用已有答案
                state['final_answer'] = state.get('answer', '')
                logger.info("⚠️ [Answer Generation] 答案生成Agent不可用，使用已有答案")
            
        except Exception as e:
            error_msg = f"答案生成失败: {str(e)}"
            logger.error(f"❌ [Answer Generation] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'answer_generation_detailed',
                'error': error_msg,
                'timestamp': time.time()
            })
            # 降级：使用已有答案
            state['final_answer'] = state.get('answer', '')
        
        finally:
            execution_time = time.time() - start_time
            # 🚀 修复：确保 node_execution_times 和 node_times 存在
            if 'node_execution_times' not in state:
                state['node_execution_times'] = {}
            if 'node_times' not in state:
                state['node_times'] = {}
            state['node_execution_times']['answer_generation_detailed'] = execution_time
            state['node_times']['answer_generation_detailed'] = execution_time
        
        return state
    
    async def citation_generation_detailed_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """引用生成详细节点
        
        生成引用列表，显式展示引用生成过程
        """
        logger.info("📖 [Citation Generation] 开始引用生成...")
        start_time = time.time()
        
        try:
            # 使用引用生成 Agent
            if self.system and hasattr(self.system, '_citation_agent') and self.system._citation_agent:
                context = {
                    "query": state.get('query', ''),
                    "answer": state.get('final_answer', ''),
                    "knowledge": state.get('knowledge', []),
                    "evidence": state.get('evidence', [])
                }
                
                result = await self.system._citation_agent.execute(context)
                
                if result.success and hasattr(result, 'data'):
                    citation_data = result.data
                    if isinstance(citation_data, dict):
                        state['citations'] = citation_data.get('citations', [])
                    elif isinstance(citation_data, list):
                        state['citations'] = citation_data
                    logger.info(f"✅ [Citation Generation] 引用生成完成，数量: {len(state.get('citations', []))}")
                else:
                    logger.warning("⚠️ [Citation Generation] 引用生成未成功")
                    state['citations'] = []
            else:
                # 降级：从知识中提取引用
                knowledge = state.get('knowledge', [])
                citations = []
                for item in knowledge:
                    if isinstance(item, dict):
                        citations.append({
                            'content': item.get('content', ''),
                            'source': item.get('source', 'unknown')
                        })
                state['citations'] = citations
                logger.info(f"⚠️ [Citation Generation] 引用生成Agent不可用，从知识中提取 {len(citations)} 个引用")
            
        except Exception as e:
            error_msg = f"引用生成失败: {str(e)}"
            logger.error(f"❌ [Citation Generation] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'citation_generation_detailed',
                'error': error_msg,
                'timestamp': time.time()
            })
            state['citations'] = []
        
        finally:
            execution_time = time.time() - start_time
            # 🚀 修复：确保 node_execution_times 和 node_times 存在
            if 'node_execution_times' not in state:
                state['node_execution_times'] = {}
            if 'node_times' not in state:
                state['node_times'] = {}
            state['node_execution_times']['citation_generation_detailed'] = execution_time
            state['node_times']['citation_generation_detailed'] = execution_time
        
        return state
