"""
多智能体节点模块 - 阶段4.1
将 Agent 集成到 LangGraph 工作流中
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.agents.base_agent import BaseAgent

from src.core.langgraph_unified_workflow import ResearchSystemState

logger = logging.getLogger(__name__)


class AgentNodes:
    """Agent 节点集合 - 集成 Agent 到 LangGraph 工作流"""
    
    def __init__(self, system=None):
        """初始化 Agent 节点
        
        Args:
            system: UnifiedResearchSystem 实例（可选）
        """
        self.system = system
        self.chief_agent = None
        self.react_agent = None
        # 专家智能体池（用于在工作流中直接调用）
        self.expert_agents = {}
        self._initialize_agents()
        self._initialize_expert_agents()
    
    def _initialize_agents(self):
        """初始化 Agent"""
        try:
            # 初始化首席Agent（用于多智能体协调）
            from src.agents.chief_agent import ChiefAgent
            print("🔧 初始化ChiefAgent...")
            self.chief_agent = ChiefAgent()
            print(f"🔧 ChiefAgent初始化完成: {self.chief_agent is not None}")
            logger.info("✅ 首席Agent初始化成功")
        except Exception as e:
            print(f"❌ ChiefAgent初始化失败: {e}")
            logger.warning(f"⚠️ 首席Agent初始化失败: {e}")
            self.chief_agent = None
        
        # 🚀 优化：在尝试初始化ReAct Agent之前，先检查LangGraph是否可用
        try:
            from langgraph.graph import StateGraph
            LANGGRAPH_AVAILABLE = True
        except ImportError:
            LANGGRAPH_AVAILABLE = False
        
        if LANGGRAPH_AVAILABLE:
            try:
                # 初始化ReAct Agent（用于单Agent执行）
                from src.agents.langgraph_react_agent import LangGraphReActAgent
                self.react_agent = LangGraphReActAgent(agent_name="WorkflowReActAgent")
                logger.info("✅ ReAct Agent初始化成功")
            except Exception as e:
                # 🚀 优化：如果是因为LangGraph不可用，使用INFO级别；其他错误使用WARNING
                if "LangGraph is required" in str(e) or "LangGraph not available" in str(e):
                    logger.info("ℹ️ ReAct Agent不可用（LangGraph未安装，这是可选的，系统将使用其他Agent）")
                else:
                    logger.warning(f"⚠️ ReAct Agent初始化失败: {e}")
                self.react_agent = None
        else:
            # 🚀 优化：LangGraph不可用，直接跳过，不显示警告
            logger.debug("ℹ️ ReAct Agent不可用（LangGraph未安装，这是可选的，系统将使用其他Agent）")
            self.react_agent = None
    
    def _initialize_expert_agents(self):
        """初始化专家智能体（用于在工作流中直接调用）"""
        # 初始化专家智能体（延迟初始化，避免阻塞）
        self.expert_agents = {
            'memory': None,  # 延迟初始化
            'knowledge_retrieval': None,  # 延迟初始化
            'reasoning': None,  # 延迟初始化
            'answer_generation': None,  # 延迟初始化
            'citation': None  # 延迟初始化
        }
        
        logger.info("✅ 专家智能体节点准备完成（延迟初始化）")
    
    def _get_expert_agent(self, agent_name: str) -> Optional[Any]:
        """获取专家智能体（延迟初始化）"""
        if agent_name not in self.expert_agents:
            return None
        
        if self.expert_agents[agent_name] is None:
            try:
                # 根据不同Agent类型导入不同的类
                if agent_name == 'reasoning':
                    from src.agents.reasoning_agent import ReasoningAgent
                    # ReasoningAgent 需要 tool_registry
                    if self.system and hasattr(self.system, 'tool_registry'):
                        self.expert_agents[agent_name] = ReasoningAgent(self.system.tool_registry)
                        logger.info(f"✅ 专家智能体 {agent_name} 初始化成功")
                    else:
                        logger.warning(f"⚠️ 无法初始化 {agent_name}: 缺少 tool_registry")
                        return None
                
                elif agent_name == 'memory':
                    from backup_legacy_agents.memory_agent_wrapper import MemoryAgentWrapper
                    self.expert_agents[agent_name] = MemoryAgentWrapper(enable_gradual_replacement=True)
                    logger.info(f"✅ 专家智能体 {agent_name} 初始化成功")
                
                elif agent_name == 'knowledge_retrieval':
                    from backup_legacy_agents.knowledge_retrieval_agent_wrapper import KnowledgeRetrievalAgentWrapper
                    self.expert_agents[agent_name] = KnowledgeRetrievalAgentWrapper(enable_gradual_replacement=True)
                    logger.info(f"✅ 专家智能体 {agent_name} 初始化成功")
                
                elif agent_name == 'answer_generation':
                    from backup_legacy_agents.answer_generation_agent_wrapper import AnswerGenerationAgentWrapper
                    self.expert_agents[agent_name] = AnswerGenerationAgentWrapper(enable_gradual_replacement=True)
                    logger.info(f"✅ 专家智能体 {agent_name} 初始化成功")
                
                elif agent_name == 'citation':
                    from backup_legacy_agents.citation_agent_wrapper import CitationAgentWrapper
                    self.expert_agents[agent_name] = CitationAgentWrapper(enable_gradual_replacement=True)
                    logger.info(f"✅ 专家智能体 {agent_name} 初始化成功")
                    
            except Exception as e:
                logger.warning(f"⚠️ 专家智能体 {agent_name} 初始化失败: {e}")
                return None
        
        return self.expert_agents[agent_name]
    
    async def memory_agent_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """记忆智能体节点 - 存储和检索上下文"""
        logger.info("🧠 [Memory Agent] 开始记忆管理")
        start_time = time.time()
        
        # 🚀 学习集成：应用学习到的洞察
        try:
            from src.core.langgraph_learning_nodes import apply_learned_insights
            insights = apply_learned_insights(state, 'memory_agent')
            if insights:
                logger.debug(f"✅ [Memory Agent] 应用学习洞察: {list(insights.keys())}")
        except Exception as e:
            logger.debug(f"⚠️ [Memory Agent] 学习洞察应用失败: {e}")
        
        try:
            query = state.get('query', '')
            if not query:
                state['error'] = "查询为空，无法进行记忆管理"
                state['errors'].append({
                    'node': 'memory_agent',
                    'error': state['error'],
                    'timestamp': time.time()
                })
                return state
            
            agent = self._get_expert_agent('memory')
            if agent:
                # 🎯 编排追踪：设置编排追踪器到智能体
                try:
                    # 🚀 修复：优先从系统实例获取追踪器，如果没有则使用全局追踪器
                    tracker = None
                    if self.system and hasattr(self.system, '_orchestration_tracker'):
                        tracker = self.system._orchestration_tracker
                        logger.info(f"✅ [Memory Agent] 从系统实例获取编排追踪器: {id(tracker)}")
                    if not tracker:
                        from src.visualization.orchestration_tracker import get_orchestration_tracker
                        tracker = get_orchestration_tracker()
                        logger.info(f"✅ [Memory Agent] 使用全局编排追踪器: {id(tracker)}")
                    if tracker:
                        # 🚀 修复：使用setattr避免类型检查错误（动态属性）
                        setattr(agent, '_orchestration_tracker', tracker)
                        logger.info(f"✅ [Memory Agent] 编排追踪器已设置到智能体，追踪器事件数: {len(tracker.events)}")
                    else:
                        logger.warning(f"⚠️ [Memory Agent] 无法获取编排追踪器")
                except Exception as e:
                    logger.warning(f"⚠️ [Memory Agent] 无法设置编排追踪器: {e}", exc_info=True)
                context = {
                    'query': query,
                    'session_id': state.get('session_id'),
                    'user_context': state.get('user_context', {})
                }
                # 🚀 修复：使用getattr避免类型检查错误（动态方法）
                execute_method = getattr(agent, 'execute', None)
                if execute_method and callable(execute_method):
                    result = await execute_method(context)  # type: ignore[awaitable-return]
                else:
                    logger.error("❌ [Memory Agent] agent没有execute方法")
                    state['error'] = "Memory Agent执行失败：缺少execute方法"
                    return state
                
                if result.success:
                    if isinstance(result.data, dict):
                        state['user_context'] = result.data.get('user_context', state.get('user_context', {}))
                        state['context'] = result.data.get('context', state.get('context', {}))
                    logger.info("✅ [Memory Agent] 记忆管理完成")
                else:
                    state['error'] = result.error or "记忆管理失败"
                    logger.warning(f"⚠️ [Memory Agent] {state['error']}")
            else:
                logger.warning("⚠️ [Memory Agent] 记忆智能体不可用")
        except Exception as e:
            error_msg = f"记忆管理失败: {str(e)}"
            logger.error(f"❌ [Memory Agent] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'memory_agent',
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
            state['node_execution_times']['memory_agent'] = execution_time
            state['node_times']['memory_agent'] = execution_time
            
            # 🚀 学习集成：收集学习数据
            try:
                from src.core.langgraph_learning_nodes import collect_node_learning_data, learn_from_node_execution
                success = state.get('error') is None
                collect_node_learning_data(state, 'memory_agent', execution_time, success, {
                    'context_updated': 'user_context' in state or 'context' in state
                })
                learn_from_node_execution(state, 'memory_agent', {
                    'success': success,
                    'execution_time': execution_time,
                    'confidence': 0.8 if success else 0.0
                })
            except Exception as e:
                logger.debug(f"⚠️ [Memory Agent] 学习数据收集失败: {e}")
        
        return state
    
    async def _decompose_query(self, query: str) -> List[str]:
        """分解复杂查询为简单的关键词查询列表"""
        print(f"DEBUG: Starting _decompose_query for: {query}")
        try:
            # 尝试获取 LLM
            llm = None
            if self.system:
                print(f"DEBUG: system found: {type(self.system)}")
                # 1. 尝试从 llm_client 获取
                if hasattr(self.system, 'llm_client') and self.system.llm_client:
                    llm = self.system.llm_client
                    print("DEBUG: Got LLM from system.llm_client")
                
                # 2. 尝试从 reasoning_agent 获取
                if not llm and hasattr(self.system, '_reasoning_agent') and self.system._reasoning_agent:
                    if hasattr(self.system._reasoning_agent, 'llm'):
                        llm = self.system._reasoning_agent.llm
                        print("DEBUG: Got LLM from system._reasoning_agent.llm")
                    elif hasattr(self.system._reasoning_agent, 'llm_integration'):
                        llm = self.system._reasoning_agent.llm_integration
                        print("DEBUG: Got LLM from system._reasoning_agent.llm_integration")
                
                # 3. 尝试从 reasoning_engine 获取 (fallback)
                if not llm and hasattr(self.system, 'reasoning_engine') and self.system.reasoning_engine:
                    if hasattr(self.system.reasoning_engine, 'llm_integration'):
                        llm = self.system.reasoning_engine.llm_integration
                        print("DEBUG: Got LLM from system.reasoning_engine.llm_integration")
                    elif hasattr(self.system.reasoning_engine, 'llm'):
                        llm = self.system.reasoning_engine.llm
                        print("DEBUG: Got LLM from system.reasoning_engine.llm")
                
                # 4. 尝试从 system.llm_integration 获取 (fallback)
                if not llm and hasattr(self.system, 'llm_integration'):
                    llm = self.system.llm_integration
                    print("DEBUG: Got LLM from system.llm_integration")
            else:
                print("DEBUG: self.system is None")
            
            if not llm:
                logger.warning("⚠️ 无法获取 LLM 实例，跳过查询分解")
                print("DEBUG: LLM instance not found")
                return [query]
            
            print(f"DEBUG: LLM instance found: {type(llm)}")
            
            if not llm:
                logger.warning("⚠️ 无法获取 LLM 实例，跳过查询分解")
                return [query]
            
            prompt = f"""You are an expert research assistant. 
Your task is to break down a complex user query into 3-5 simple, keyword-focused search queries that can be used to retrieve factual evidence from a knowledge base.
The original query may be a multi-hop question requiring multiple pieces of information.
If you can identify specific entities (e.g., convert "15th president" to "James Buchanan"), please include specific names in the queries.

Original Query: {query}

Instructions:
1. Identify the key entities and relationships.
2. Break the query into sub-queries to find each piece of required information.
3. Keep queries simple and keyword-rich.
4. Output ONLY the queries, one per line. Do not include numbering or explanations.

Sub-queries:"""
            
            # 调用 LLM
            response = None
            try:
                if hasattr(llm, 'generate'):
                    response = await llm.generate(prompt) if asyncio.iscoroutinefunction(llm.generate) else llm.generate(prompt)
                elif hasattr(llm, '_call_llm'):
                     response = await llm._call_llm(prompt) if asyncio.iscoroutinefunction(llm._call_llm) else llm._call_llm(prompt)
            except Exception as e:
                logger.warning(f"LLM调用失败: {e}")
            
            if response:
                queries = [line.strip() for line in response.split('\n') if line.strip()]
                clean_queries = []
                import re
                for q in queries:
                    # 去除开头的列表编号 (如 "1.", "1)", "- ", "* ")，但保留像 "15th" 这样的内容
                    # 原来的正则 r'^[\d\-\.\s]+' 会错误地将 "15th" 变成 "th"
                    q = re.sub(r'^\s*(?:(?:\d+[.)])|[-*])\s+', '', q)
                    if q:
                        clean_queries.append(q)
                
                logger.info(f"✅ 查询分解成功: {clean_queries}")
                # 确保原始查询在第一个，并且结果去重
                unique_queries = []
                seen = set()
                # 添加原始查询
                if query not in seen:
                    unique_queries.append(query)
                    seen.add(query)
                # 添加分解查询
                for q in clean_queries:
                    if q not in seen:
                        unique_queries.append(q)
                        seen.add(q)
                return unique_queries[:6] # 最多保留6个查询
            
        except Exception as e:
            logger.warning(f"⚠️ 查询分解失败: {e}")
        
        return [query]

    async def knowledge_retrieval_agent_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """知识检索智能体节点 - 从知识库中检索相关知识，提供证据和引用"""
        logger.info("🔍 [Knowledge Retrieval Agent] 开始知识检索")
        start_time = time.time()
        
        # 🚀 学习集成：应用学习到的洞察
        try:
            from src.core.langgraph_learning_nodes import apply_learned_insights
            insights = apply_learned_insights(state, 'knowledge_retrieval_agent')
            if insights:
                logger.debug(f"✅ [Knowledge Retrieval Agent] 应用学习洞察: {list(insights.keys())}")
        except Exception as e:
            logger.debug(f"⚠️ [Knowledge Retrieval Agent] 学习洞察应用失败: {e}")
        
        try:
            query = state.get('query', '')
            if not query:
                state['error'] = "查询为空，无法进行知识检索"
                state['errors'].append({
                    'node': 'knowledge_retrieval_agent',
                    'error': state['error'],
                    'timestamp': time.time()
                })
                return state
            
            # 🚀 查询分解：将复杂查询分解为多个子查询
            search_queries = await self._decompose_query(query)
            metadata = state.get('metadata')
            if not isinstance(metadata, dict):
                metadata = {}
            metadata['decomposition'] = {
                'original_query': query,
                'sub_queries': list(search_queries),
            }
            if 'retrieval_trace' not in metadata or not isinstance(metadata.get('retrieval_trace'), list):
                metadata['retrieval_trace'] = []
            state['metadata'] = metadata
            retrieval_trace = metadata['retrieval_trace']
            print(f"\n{'='*20} DEBUG: DECOMPOSED QUERIES {'='*20}")
            for i, q in enumerate(search_queries):
                print(f"  {i+1}. {q}")
            print(f"{'='*60}\n")
            
            logger.info(f"🔍 [Knowledge Retrieval Agent] 将执行 {len(search_queries)} 个查询: {search_queries}")
            
            # 🚀 改进：能力节点应该作为主流程节点的内部能力，而不是独立的增强步骤
            # 首先尝试使用能力服务调用能力节点（如果可用）
            
            all_knowledge = []
            all_evidence = []
            all_sources = []
            capability_used = False
            
            try:
                from src.core.capability_service import get_capability_service
                capability_service = get_capability_service()
                
                # 检查是否有知识检索能力可用
                if 'knowledge_retrieval' in [cap.capability.name for cap in capability_service.capabilities.values()]:
                    capability_used = True
                    print(f"DEBUG: Using capability_service for knowledge_retrieval with {len(search_queries)} queries")
                    # 并行执行所有查询
                    tasks = []
                    for sub_query in search_queries:
                        capability_context = {
                            'query': sub_query,
                            'knowledge': state.get('knowledge', []),
                            'evidence': state.get('evidence', []),
                            'state': state  # 传递完整状态
                        }
                        tasks.append(capability_service.execute_capability('knowledge_retrieval', capability_context))
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for i, result in enumerate(results):
                        print(f"\n--- DEBUG: Result for query '{search_queries[i]}' ---")
                        trace_entry = {
                            'sub_query': search_queries[i],
                            'via': 'capability',
                            'success': False
                        }
                        if isinstance(result, Exception):
                            print(f"  FAILED: {result}")
                            logger.warning(f"⚠️ 查询 '{search_queries[i]}' 检索失败: {result}")
                            trace_entry['error'] = str(result)
                            retrieval_trace.append(trace_entry)
                            continue
                            
                        if result:
                            print(f"  SUCCESS. Data type: {type(result.data)}")
                            knowledge_count = 0
                            evidence_count = 0
                            source_count = 0
                            if hasattr(result, 'data') and isinstance(result.data, dict):
                                k_items = result.data.get('knowledge', [])
                                e_items = result.data.get('evidence', [])
                                s_items = result.data.get('sources', [])
                                print(f"  Knowledge items found: {len(k_items)}")
                                for k in k_items:
                                    print(f"    - {str(k)[:100]}...")
                                knowledge_count = len(k_items)
                                evidence_count = len(e_items)
                                source_count = len(s_items)

                            logger.info(f"✅ [Knowledge Retrieval Agent] 查询 '{search_queries[i]}' 检索成功")
                            if isinstance(result, dict):
                                k = result.get('knowledge')
                                e = result.get('evidence')
                                s = result.get('sources')
                                
                                if k: 
                                    if isinstance(k, list): all_knowledge.extend(k)
                                    else: all_knowledge.append(k)
                                if e:
                                    if isinstance(e, list): all_evidence.extend(e)
                                    else: all_evidence.append(e)
                                if s:
                                    if isinstance(s, list): all_sources.extend(s)
                                    else: all_sources.append(s)
                                knowledge_count = knowledge_count or (len(k) if isinstance(k, list) else (1 if k else 0))
                                evidence_count = evidence_count or (len(e) if isinstance(e, list) else (1 if e else 0))
                                source_count = source_count or (len(s) if isinstance(s, list) else (1 if s else 0))
                            trace_entry['success'] = True
                            trace_entry['knowledge_count'] = knowledge_count
                            trace_entry['evidence_count'] = evidence_count
                            trace_entry['source_count'] = source_count
                            retrieval_trace.append(trace_entry)
            except Exception as e:
                logger.debug(f"⚠️ [Knowledge Retrieval Agent] 能力服务不可用或执行失败: {e}，尝试使用专家智能体")
            
            # 如果能力服务没有被使用或没有返回结果，且没有收集到任何知识，尝试使用专家智能体
            if not capability_used or not all_knowledge:
                # 注意：专家智能体通常不支持并发查询，这里只用原始查询作为 fallback
                try:
                    expert_agent = self._get_expert_agent('knowledge_retrieval')
                    if expert_agent:
                        logger.info("✅ [Knowledge Retrieval Agent] 使用专家智能体执行知识检索 (Fallback)")
                        # 构建上下文
                        context = {
                            'query': query,
                            'query_type': state.get('query_type', 'general'),
                            'context': state.get('context', {})
                        }
                        
                        result = await expert_agent.execute(context)
                        
                        if result.success:
                            if isinstance(result.data, dict):
                                k = result.data.get('knowledge') or result.data.get('sources')
                                e = result.data.get('evidence') or result.data.get('chunks')
                                s = result.data.get('sources')
                                
                                if k: all_knowledge.extend(k if isinstance(k, list) else [k])
                                if e: all_evidence.extend(e if isinstance(e, list) else [e])
                                if s: all_sources.extend(s if isinstance(s, list) else [s])
                                
                                logger.info(f"✅ [Knowledge Retrieval Agent] 知识检索完成，获取 {len(all_knowledge)} 条知识")
                                retrieval_trace.append({
                                    'sub_query': query,
                                    'via': 'expert_agent',
                                    'success': True,
                                    'knowledge_count': len(all_knowledge),
                                    'evidence_count': len(all_evidence),
                                    'source_count': len(all_sources)
                                })
                            else:
                                state['error'] = result.error or "知识检索失败"
                                logger.warning(f"⚠️ [Knowledge Retrieval Agent] {state['error']}")
                                retrieval_trace.append({
                                    'sub_query': query,
                                    'via': 'expert_agent',
                                    'success': False,
                                    'error': state['error']
                                })
                        else:
                            logger.warning("⚠️ [Knowledge Retrieval Agent] 知识检索智能体不可用")
                            retrieval_trace.append({
                                'sub_query': query,
                                'via': 'expert_agent',
                                'success': False,
                                'error': "knowledge_retrieval_agent_unavailable"
                            })
                except Exception as ex:
                    logger.warning(f"⚠️ [Knowledge Retrieval Agent] 专家智能体执行失败: {ex}")
                    retrieval_trace.append({
                        'sub_query': query,
                        'via': 'expert_agent',
                        'success': False,
                        'error': str(ex)
                    })

            # 合并结果并更新状态
            if all_knowledge or all_evidence:
                existing_knowledge = state.get('knowledge', [])
                existing_evidence = state.get('evidence', [])
                
                # 合并现有知识
                all_knowledge = existing_knowledge + all_knowledge
                all_evidence = existing_evidence + all_evidence

                # 去重 (简单基于字符串表示)
                unique_knowledge = []
                seen_k = set()
                for k in all_knowledge:
                    k_str = str(k)
                    if k_str not in seen_k:
                        unique_knowledge.append(k)
                        seen_k.add(k_str)
                
                unique_evidence = []
                seen_e = set()
                for e in all_evidence:
                    e_str = str(e)
                    if e_str not in seen_e:
                        unique_evidence.append(e)
                        seen_e.add(e_str)
                
                state['knowledge'] = unique_knowledge
                state['evidence'] = unique_evidence
                # sources 结构复杂，暂时不去重
                if all_sources:
                    state['context'] = state.get('context', {})
                    state['context']['retrieved_sources'] = all_sources
                
                if 'capability_usage' not in state:
                    state['capability_usage'] = []
                state['capability_usage'].append({
                    'capability': 'knowledge_retrieval',
                    'node': 'knowledge_retrieval_agent',
                    'timestamp': time.time(),
                    'query_count': len(search_queries)
                })
                
                logger.info(f"✅ [Knowledge Retrieval Agent] 最终汇总: {len(unique_knowledge)} 条知识, {len(unique_evidence)} 条证据")
            else:
                logger.warning("⚠️ [Knowledge Retrieval Agent] 未检索到任何知识")

        except Exception as e:
            error_msg = f"知识检索失败: {str(e)}"
            logger.error(f"❌ [Knowledge Retrieval Agent] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'knowledge_retrieval_agent',
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
            state['node_execution_times']['knowledge_retrieval_agent'] = execution_time
            state['node_times']['knowledge_retrieval_agent'] = execution_time
            
            # 🚀 学习集成：收集学习数据
            try:
                from src.core.langgraph_learning_nodes import collect_node_learning_data, learn_from_node_execution
                success = state.get('error') is None
                knowledge_count = len(state.get('knowledge', []))
                evidence_count = len(state.get('evidence', []))
                collect_node_learning_data(state, 'knowledge_retrieval_agent', execution_time, success, {
                    'knowledge_count': knowledge_count,
                    'evidence_count': evidence_count
                })
                learn_from_node_execution(state, 'knowledge_retrieval_agent', {
                    'success': success,
                    'execution_time': execution_time,
                    'confidence': 0.8 if success else 0.0,
                    'knowledge_count': knowledge_count,
                    'evidence_count': evidence_count
                })
            except Exception as e:
                logger.debug(f"⚠️ [Knowledge Retrieval Agent] 学习数据收集失败: {e}")
        
        return state
    
    async def reasoning_agent_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """推理智能体节点 - 进行深度推理分析，处理复杂逻辑关系（支持推理链模式）"""
        logger.info("🧩 [Reasoning Agent] 开始推理分析")
        start_time = time.time()
        
        # 🚀 学习集成：应用学习到的洞察
        try:
            from src.core.langgraph_learning_nodes import apply_learned_insights
            insights = apply_learned_insights(state, 'reasoning_agent')
            if insights:
                logger.debug(f"✅ [Reasoning Agent] 应用学习洞察: {list(insights.keys())}")
                # 应用性能优化建议
                if 'performance_optimization' in insights:
                    perf_opt = insights['performance_optimization']
                    if 'suggested_timeout' in perf_opt:
                        # 使用metadata存储学习到的配置
                        if 'metadata' not in state:
                            state['metadata'] = {}
                        state['metadata']['reasoning_timeout'] = perf_opt['suggested_timeout']
        except Exception as e:
            logger.debug(f"⚠️ [Reasoning Agent] 学习洞察应用失败: {e}")
        
        try:
            query = state.get('query', '')
            if not query:
                state['error'] = "查询为空，无法进行推理分析"
                state['errors'].append({
                    'node': 'reasoning_agent',
                    'error': state['error'],
                    'timestamp': time.time()
                })
                return state
            
            agent = self._get_expert_agent('reasoning')
            if agent:
                # 🎯 编排追踪：设置编排追踪器到智能体
                try:
                    # 🚀 修复：优先从系统实例获取追踪器，如果没有则使用全局追踪器
                    tracker = None
                    if self.system and hasattr(self.system, '_orchestration_tracker'):
                        tracker = self.system._orchestration_tracker
                    if not tracker:
                        from src.visualization.orchestration_tracker import get_orchestration_tracker
                        tracker = get_orchestration_tracker()
                    if tracker:
                        # 🚀 修复：使用setattr避免类型检查错误（动态属性）
                        setattr(agent, '_orchestration_tracker', tracker)
                        logger.debug(f"✅ [Reasoning Agent] 编排追踪器已设置")
                except Exception as e:
                    logger.debug(f"⚠️ [Reasoning Agent] 无法设置编排追踪器: {e}")
                
                # 🚀 改进：能力节点应该作为主流程节点的内部能力
                # 首先尝试使用能力服务调用推理能力（如果可用）
                capability_result = None
                try:
                    from src.core.capability_service import get_capability_service
                    capability_service = get_capability_service()
                    
                    # 检查是否有推理能力可用
                    if 'reasoning' in [cap.capability.name for cap in capability_service.capabilities.values()]:
                        needs_reasoning_chain = state.get('needs_reasoning_chain') or state.get('context', {}).get('needs_reasoning_chain', False)
                        capability_context = {
                            'query': query,
                            'knowledge': state.get('knowledge', []),
                            'evidence': state.get('evidence', []),
                            'needs_reasoning_chain': needs_reasoning_chain,
                            'state': state  # 传递完整状态
                        }
                        capability_result = await capability_service.execute_capability('reasoning', capability_context)
                        logger.info(f"✅ [Reasoning Agent] 使用能力服务执行推理（推理链: {needs_reasoning_chain}）")
                except Exception as e:
                    logger.debug(f"⚠️ [Reasoning Agent] 能力服务不可用: {e}，使用专家智能体")
                
                # 如果能力服务执行成功，使用能力结果；否则使用专家智能体
                    if capability_result:
                        # 合并能力结果到状态
                        if isinstance(capability_result, dict):
                            reasoning_val = capability_result.get('final_answer') or capability_result.get('answer', '')
                            if reasoning_val:
                                state.setdefault('reasoning_answer', [])
                                state['reasoning_answer'].append(str(reasoning_val))
                        state['reasoning_result'] = capability_result.get('reasoning_result', capability_result)
                        try:
                            metadata = state.get('metadata')
                            if not isinstance(metadata, dict):
                                metadata = {}
                            metadata['reasoning_result'] = {
                                'success': True,
                                'data': capability_result,
                                'final_answer': reasoning_val if reasoning_val else '',
                                'confidence': capability_result.get('confidence', 0.0) if isinstance(capability_result, dict) else 0.0,
                                'error': None
                            }
                            if isinstance(capability_result, dict):
                                steps = capability_result.get('steps') or capability_result.get('reasoning_steps')
                                if isinstance(steps, list):
                                    metadata['reasoning_trace'] = steps
                                    # Populate step_answers
                                    step_answers = []
                                    for step in steps:
                                        if isinstance(step, dict):
                                            ans = step.get('result') or step.get('answer')
                                            if ans: step_answers.append(str(ans))
                                        elif hasattr(step, 'result'):
                                            ans = getattr(step, 'result', None)
                                            if ans: step_answers.append(str(ans))
                                    if step_answers:
                                        state['step_answers'] = step_answers
                                        logger.info(f"✅ [Reasoning Agent] (Capability) 提取了 {len(step_answers)} 个步骤答案")
                            state['metadata'] = metadata
                        except Exception:
                            pass
                        # 标记使用了能力节点
                        if 'capability_usage' not in state:
                            state['capability_usage'] = []
                        state['capability_usage'].append({
                            'capability': 'reasoning',
                            'node': 'reasoning_agent',
                            'timestamp': time.time()
                        })
                        logger.info("✅ [Reasoning Agent] 推理能力执行完成，结果已保存到state")
                else:
                    # 使用专家智能体（原有逻辑）
                    # 🚀 改进：传递 needs_reasoning_chain 标志，让 ReasoningService 智能选择推理模式
                    # 推理链能力是 reasoning_agent 的内部能力，不需要独立的推理链路径
                    needs_reasoning_chain = state.get('metadata', {}).get('deep_reasoning_mode', False) or \
                                           state.get('context', {}).get('needs_reasoning_chain', False) or \
                                           state.get('needs_reasoning_chain', False)
                    context = {
                        'query': query,
                        'knowledge': state.get('knowledge', []),
                        'evidence': state.get('evidence', []),
                        'needs_reasoning_chain': needs_reasoning_chain  # 传递推理链标志
                    }
                    logger.info(f"🧩 [Reasoning Agent] 推理链标志: {needs_reasoning_chain}")
                    # 🚀 修复：使用getattr避免类型检查错误（动态方法）
                    execute_method = getattr(agent, 'execute', None)
                    if execute_method and callable(execute_method):
                        # 适配 ReasoningAgent 的 execute(inputs, context) 签名
                        # inputs 必须包含 query，context 包含 knowledge/evidence 等
                        inputs = {'query': query}
                        try:
                            # 尝试使用双参数调用 (适配 ReasoningAgent)
                            result = await execute_method(inputs, context=context)
                        except TypeError as e:
                            # 如果失败（例如是旧版Agent只接受一个参数），回退到单参数调用
                            logger.debug(f"⚠️ [Reasoning Agent] 双参数调用失败，尝试单参数: {e}")
                            result = await execute_method(context)  # type: ignore[awaitable-return]
                    else:
                        logger.error("❌ [Reasoning Agent] agent没有execute方法")
                        state['error'] = "Reasoning Agent执行失败：缺少execute方法"
                        return state
                    
                    # 🚀 兼容性处理：处理不同类型的AgentResult
                    is_success = False
                    result_data = None
                    result_error = None
                    result_confidence = 0.0
                    
                    if hasattr(result, 'success'):
                         # Legacy AgentResult
                         is_success = result.success
                         result_data = result.data
                         result_error = result.error
                         result_confidence = getattr(result, 'confidence', 0.0)
                    elif hasattr(result, 'status'):
                         # New IAgent AgentResult
                         from src.interfaces.agent import ExecutionStatus
                         is_success = result.status == ExecutionStatus.COMPLETED
                         result_data = result.output
                         result_error = result.error
                         # Metadata might contain confidence
                         result_confidence = result.metadata.get('confidence', 0.0) if result.metadata else 0.0
                    else:
                         # Fallback for unknown result type
                         is_success = bool(result)
                         result_data = result
                    
                    if is_success:
                        if isinstance(result_data, dict):
                            state['evidence'] = result_data.get('evidence', state.get('evidence', []))
                            state['knowledge'] = result_data.get('knowledge', state.get('knowledge', []))
                            reasoning_val = result_data.get('final_answer') or result_data.get('answer', '')
                            if reasoning_val:
                                state.setdefault('reasoning_answer', [])
                                state['reasoning_answer'].append(str(reasoning_val))
                            # 🚀 修复：将完整的推理结果保存到metadata中，供answer_generation_agent构建dependencies
                            if 'metadata' not in state:
                                state['metadata'] = {}
                            state['metadata']['reasoning_result'] = {
                                'success': True,
                                'data': result_data,
                                'final_answer': result_data.get('final_answer') or result_data.get('answer', ''),
                                'confidence': result_data.get('confidence', result_confidence),
                                'error': result_error
                            }
                            try:
                                steps = result_data.get('steps') or result_data.get('reasoning_steps')
                                if isinstance(steps, list):
                                    state['metadata']['reasoning_trace'] = steps
                                    # Populate step_answers
                                    step_answers = []
                                    for step in steps:
                                        if isinstance(step, dict):
                                            ans = step.get('result') or step.get('answer')
                                            if ans: step_answers.append(str(ans))
                                        elif hasattr(step, 'result'):
                                            ans = getattr(step, 'result', None)
                                            if ans: step_answers.append(str(ans))
                                    if step_answers:
                                        state['step_answers'] = step_answers
                                        logger.info(f"✅ [Reasoning Agent] 提取了 {len(step_answers)} 个步骤答案")
                            except Exception:
                                pass
                            logger.info("✅ [Reasoning Agent] 推理分析完成，结果已保存到state")
                        else:
                            reasoning_val = str(result_data) if result_data else ''
                            if reasoning_val:
                                state.setdefault('reasoning_answer', [])
                                state['reasoning_answer'].append(reasoning_val)
                            if 'metadata' not in state:
                                state['metadata'] = {}
                            state['metadata']['reasoning_result'] = {
                                'success': True,
                                'data': result_data,
                                'final_answer': str(result_data) if result_data else '',
                                'confidence': result_confidence,
                                'error': result_error
                            }
                            logger.info("✅ [Reasoning Agent] 推理分析完成（非dict结果），结果已保存到state")
                    else:
                        state['error'] = result_error or "推理分析失败"
                        logger.warning(f"⚠️ [Reasoning Agent] {state['error']}")
                        # 🚀 修复：即使失败，也保存结果到metadata，供answer_generation_agent处理
                        if 'metadata' not in state:
                            state['metadata'] = {}
                        state['metadata']['reasoning_result'] = {
                            'success': False,
                            'data': None,
                            'final_answer': None,
                            'confidence': 0.0,
                            'error': result_error or "推理分析失败"
                        }
            else:
                logger.warning("⚠️ [Reasoning Agent] 推理智能体不可用")
        except Exception as e:
            error_msg = f"推理分析失败: {str(e)}"
            logger.error(f"❌ [Reasoning Agent] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'reasoning_agent',
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
            state['node_execution_times']['reasoning_agent'] = execution_time
            state['node_times']['reasoning_agent'] = execution_time
            
            # 🚀 学习集成：收集学习数据
            try:
                from src.core.langgraph_learning_nodes import collect_node_learning_data, learn_from_node_execution
                success = state.get('error') is None
                reasoning_answer = state.get('reasoning_answer', '')
                needs_reasoning_chain = state.get('needs_reasoning_chain', False)
                collect_node_learning_data(state, 'reasoning_agent', execution_time, success, {
                    'has_reasoning_answer': bool(reasoning_answer),
                    'needs_reasoning_chain': needs_reasoning_chain,
                    'reasoning_answer_length': len(reasoning_answer) if reasoning_answer else 0
                })
                learn_from_node_execution(state, 'reasoning_agent', {
                    'success': success,
                    'execution_time': execution_time,
                    'confidence': state.get('confidence', 0.0),
                    'needs_reasoning_chain': needs_reasoning_chain
                })
            except Exception as e:
                logger.debug(f"⚠️ [Reasoning Agent] 学习数据收集失败: {e}")
        
        return state
    
    async def answer_generation_agent_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """答案生成智能体节点 - 基于检索的知识和推理结果生成最终答案"""
        logger.info("📝 [Answer Generation Agent] 开始答案生成")
        start_time = time.time()
        
        # 🚀 学习集成：应用学习到的洞察
        try:
            from src.core.langgraph_learning_nodes import apply_learned_insights
            insights = apply_learned_insights(state, 'answer_generation_agent')
            if insights:
                logger.debug(f"✅ [Answer Generation Agent] 应用学习洞察: {list(insights.keys())}")
        except Exception as e:
            logger.debug(f"⚠️ [Answer Generation Agent] 学习洞察应用失败: {e}")
        
        try:
            query = state.get('query', '')
            if not query:
                state['error'] = "查询为空，无法进行答案生成"
                state['errors'].append({
                    'node': 'answer_generation_agent',
                    'error': state['error'],
                    'timestamp': time.time()
                })
                return state
            
            agent = self._get_expert_agent('answer_generation')
            if agent:
                # 🎯 编排追踪：设置编排追踪器到智能体
                try:
                    # 🚀 修复：优先从系统实例获取追踪器，如果没有则使用全局追踪器
                    tracker = None
                    if self.system and hasattr(self.system, '_orchestration_tracker'):
                        tracker = self.system._orchestration_tracker
                    if not tracker:
                        from src.visualization.orchestration_tracker import get_orchestration_tracker
                        tracker = get_orchestration_tracker()
                    if tracker:
                        # 🚀 修复：使用setattr避免类型检查错误（动态属性）
                        setattr(agent, '_orchestration_tracker', tracker)
                        logger.debug(f"✅ [Answer Generation Agent] 编排追踪器已设置")
                except Exception as e:
                    logger.debug(f"⚠️ [Answer Generation Agent] 无法设置编排追踪器: {e}")
                # 🎯 编排追踪：设置编排追踪器到智能体
                try:
                    from src.visualization.orchestration_tracker import get_orchestration_tracker
                    tracker = get_orchestration_tracker()
                    # 🚀 修复：使用setattr避免类型检查错误（动态属性）
                    setattr(agent, '_orchestration_tracker', tracker)
                except Exception as e:
                    logger.debug(f"⚠️ [Answer Generation Agent] 无法设置编排追踪器: {e}")
                
                # 🚀 修复：从state中提取推理结果，构建dependencies传递给答案生成Agent
                dependencies = {}
                reasoning_result = state.get('metadata', {}).get('reasoning_result')
                if reasoning_result:
                    # 构建dependencies，格式与answer_generation_service期望的格式一致
                    dependencies['reasoning'] = {
                        'data': reasoning_result.get('data', {}),
                        'success': reasoning_result.get('success', False),
                        'final_answer': reasoning_result.get('final_answer'),
                        'answer': reasoning_result.get('final_answer'),
                        'confidence': reasoning_result.get('confidence', 0.0),
                        'error': reasoning_result.get('error')
                    }
                    logger.info(f"🔍 [Answer Generation Agent] 从state中提取推理结果，构建dependencies: keys={list(dependencies.keys())}")
                elif state.get('reasoning_answer'):
                    # 如果只有reasoning_answer字段，也构建dependencies
                    dependencies['reasoning'] = {
                        'data': {'final_answer': state.get('reasoning_answer')},
                        'success': True,
                        'final_answer': state.get('reasoning_answer'),
                        'answer': state.get('reasoning_answer'),
                        'confidence': state.get('confidence', 0.0),
                        'error': None
                    }
                    logger.info(f"🔍 [Answer Generation Agent] 从reasoning_answer字段构建dependencies")
                else:
                    logger.warning(f"⚠️ [Answer Generation Agent] 未找到推理结果，dependencies为空")
                
                context = {
                    'query': query,
                    'knowledge': state.get('knowledge', []),
                    'evidence': state.get('evidence', []),
                    'dependencies': dependencies  # 🚀 修复：传递dependencies给答案生成Agent
                }
                result = await agent.execute(context)
                
                if result.success:
                    if isinstance(result.data, dict):
                        state['answer'] = result.data.get('answer', result.data.get('final_answer', ''))
                        state['final_answer'] = result.data.get('final_answer', result.data.get('answer', ''))
                    else:
                        state['answer'] = str(result.data) if result.data else ''
                        state['final_answer'] = state['answer']
                    logger.info("✅ [Answer Generation Agent] 答案生成完成")
                else:
                    state['error'] = result.error or "答案生成失败"
                    logger.warning(f"⚠️ [Answer Generation Agent] {state['error']}")
            else:
                logger.warning("⚠️ [Answer Generation Agent] 答案生成智能体不可用")
        except Exception as e:
            error_msg = f"答案生成失败: {str(e)}"
            logger.error(f"❌ [Answer Generation Agent] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'answer_generation_agent',
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
            state['node_execution_times']['answer_generation_agent'] = execution_time
            state['node_times']['answer_generation_agent'] = execution_time
            
            # 🚀 学习集成：收集学习数据
            try:
                from src.core.langgraph_learning_nodes import collect_node_learning_data, learn_from_node_execution
                success = state.get('error') is None
                answer = state.get('answer') or state.get('final_answer', '')
                collect_node_learning_data(state, 'answer_generation_agent', execution_time, success, {
                    'has_answer': bool(answer),
                    'answer_length': len(answer) if answer else 0
                })
                learn_from_node_execution(state, 'answer_generation_agent', {
                    'success': success,
                    'execution_time': execution_time,
                    'confidence': state.get('confidence', 0.0),
                    'answer_length': len(answer) if answer else 0
                })
            except Exception as e:
                logger.debug(f"⚠️ [Answer Generation Agent] 学习数据收集失败: {e}")
        
        return state
    
    async def citation_agent_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """引用智能体节点 - 为答案生成准确的引用和来源标注"""
        logger.info("📚 [Citation Agent] 开始引用生成")
        start_time = time.time()
        
        # 🚀 学习集成：应用学习到的洞察
        try:
            from src.core.langgraph_learning_nodes import apply_learned_insights
            insights = apply_learned_insights(state, 'citation_agent')
            if insights:
                logger.debug(f"✅ [Citation Agent] 应用学习洞察: {list(insights.keys())}")
        except Exception as e:
            logger.debug(f"⚠️ [Citation Agent] 学习洞察应用失败: {e}")
        
        try:
            query = state.get('query', '')
            answer = state.get('answer') or state.get('final_answer', '')
            if not answer:
                state['error'] = "答案为空，无法进行引用生成"
                state['errors'].append({
                    'node': 'citation_agent',
                    'error': state['error'],
                    'timestamp': time.time()
                })
                return state
            
            agent = self._get_expert_agent('citation')
            if agent:
                # 🎯 编排追踪：设置编排追踪器到智能体
                try:
                    # 🚀 修复：优先从系统实例获取追踪器，如果没有则使用全局追踪器
                    tracker = None
                    if self.system and hasattr(self.system, '_orchestration_tracker'):
                        tracker = self.system._orchestration_tracker
                    if not tracker:
                        from src.visualization.orchestration_tracker import get_orchestration_tracker
                        tracker = get_orchestration_tracker()
                    if tracker:
                        # 🚀 修复：使用setattr避免类型检查错误（动态属性）
                        setattr(agent, '_orchestration_tracker', tracker)
                        logger.debug(f"✅ [Citation Agent] 编排追踪器已设置")
                except Exception as e:
                    logger.debug(f"⚠️ [Citation Agent] 无法设置编排追踪器: {e}")
                # 🎯 编排追踪：设置编排追踪器到智能体
                try:
                    from src.visualization.orchestration_tracker import get_orchestration_tracker
                    tracker = get_orchestration_tracker()
                    # 🚀 修复：使用setattr避免类型检查错误（动态属性）
                    setattr(agent, '_orchestration_tracker', tracker)
                except Exception as e:
                    logger.debug(f"⚠️ [Citation Agent] 无法设置编排追踪器: {e}")
                
                context = {
                    'query': query,
                    'answer': answer,
                    'knowledge': state.get('knowledge', []),
                    'evidence': state.get('evidence', [])
                }
                result = await agent.execute(context)
                
                if result.success:
                    if isinstance(result.data, dict):
                        state['citations'] = result.data.get('citations', state.get('citations', []))
                    logger.info(f"✅ [Citation Agent] 引用生成完成，生成 {len(state.get('citations', []))} 条引用")
                else:
                    state['error'] = result.error or "引用生成失败"
                    logger.warning(f"⚠️ [Citation Agent] {state['error']}")
            else:
                logger.warning("⚠️ [Citation Agent] 引用智能体不可用")
        except Exception as e:
            error_msg = f"引用生成失败: {str(e)}"
            logger.error(f"❌ [Citation Agent] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'citation_agent',
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
            state['node_execution_times']['citation_agent'] = execution_time
            state['node_times']['citation_agent'] = execution_time
            
            # 🚀 学习集成：收集学习数据
            try:
                from src.core.langgraph_learning_nodes import collect_node_learning_data, learn_from_node_execution
                success = state.get('error') is None
                citations_count = len(state.get('citations', []))
                collect_node_learning_data(state, 'citation_agent', execution_time, success, {
                    'citations_count': citations_count
                })
                learn_from_node_execution(state, 'citation_agent', {
                    'success': success,
                    'execution_time': execution_time,
                    'confidence': 0.8 if success else 0.0,
                    'citations_count': citations_count
                })
            except Exception as e:
                logger.debug(f"⚠️ [Citation Agent] 学习数据收集失败: {e}")
        
        return state
    
    async def agent_think_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """Agent思考节点 - 分析查询并生成思考结果"""
        logger.info("🧠 [Agent Think] 开始Agent思考")
        start_time = time.time()
        
        try:
            query = state.get('query', '')
            if not query:
                state['error'] = "查询为空，无法进行Agent思考"
                state['errors'].append({
                    'node': 'agent_think',
                    'error': state['error'],
                    'timestamp': time.time()
                })
                return state
            
            # 初始化Agent思考历史
            if 'agent_thoughts' not in state:
                state['agent_thoughts'] = []
            
            # 使用ReAct Agent进行思考
            if self.react_agent:
                # 构建Agent状态
                agent_state = {
                    'query': query,
                    'thoughts': state.get('agent_thoughts', []),
                    'observations': state.get('agent_observations', []),
                    'actions': state.get('agent_actions', []),
                    'task_complete': False,
                    'iteration': state.get('iteration', 0),
                    'max_iterations': state.get('max_iterations', 10),
                    'error': None
                }
                
                # 调用思考节点（模拟）
                # 注意：这里我们直接调用Agent的思考逻辑，而不是执行完整工作流
                from src.agents.reasoning_expert import ReasoningExpert as ReActAgent
                react_agent = ReasoningExpert()
                thought = await react_agent._think(query, state.get('agent_observations', []))
                
                state['agent_thoughts'].append(thought)
                state['metadata']['current_thought'] = thought
            else:
                # 降级：简单思考
                thought = f"分析查询: {query[:100]}..."
                state['agent_thoughts'].append(thought)
                state['metadata']['current_thought'] = thought
                logger.warning("⚠️ [Agent Think] ReAct Agent不可用，使用降级方案")
            
            # 记录执行时间
            execution_time = time.time() - start_time
            state['node_execution_times']['agent_think'] = execution_time
            state['node_times']['agent_think'] = execution_time
            
            logger.info(f"✅ [Agent Think] 思考完成: {thought[:100]}... (耗时: {execution_time:.2f}s)")
        
        except Exception as e:
            error_msg = f"Agent思考失败: {str(e)}"
            logger.error(f"❌ [Agent Think] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'agent_think',
                'error': error_msg,
                'timestamp': time.time()
            })
            # 降级：添加简单思考
            if 'agent_thoughts' not in state:
                state['agent_thoughts'] = []
            state['agent_thoughts'].append("思考过程出错，使用降级方案")
        
        return state
    
    async def agent_plan_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """Agent规划节点 - 根据思考结果制定行动计划"""
        logger.info("📋 [Agent Plan] 开始Agent规划")
        start_time = time.time()
        
        try:
            query = state.get('query', '')
            current_thought = state.get('metadata', {}).get('current_thought', '')
            
            if not query:
                state['error'] = "查询为空，无法进行Agent规划"
                state['errors'].append({
                    'node': 'agent_plan',
                    'error': state['error'],
                    'timestamp': time.time()
                })
                return state
            
            # 初始化Agent行动历史
            if 'agent_actions' not in state:
                state['agent_actions'] = []
            
            # 使用ReAct Agent进行规划
            if self.react_agent:
                from src.agents.reasoning_expert import ReasoningExpert as ReActAgent
                react_agent = ReasoningExpert()
                
                # 规划行动
                action = await react_agent._plan_action(
                    thought=current_thought,
                    query=query,
                    observations=state.get('agent_observations', [])
                )
                
                if action:
                    # 🚀 修复：Action类使用params而不是parameters
                    action_dict = {
                        'tool_name': action.tool_name,
                        'parameters': getattr(action, 'params', getattr(action, 'parameters', {})),
                        'reasoning': action.reasoning,
                        'timestamp': time.time()
                    }
                    state['agent_actions'].append(action_dict)
                    state['metadata']['current_action'] = action_dict
                else:
                    logger.warning("⚠️ [Agent Plan] 未生成行动计划")
                    state['metadata']['current_action'] = None
            else:
                # 降级：简单规划
                action_dict = {
                    'tool_name': 'knowledge_retrieval',
                    'parameters': {'query': query},
                    'reasoning': '使用知识检索工具获取信息',
                    'timestamp': time.time()
                }
                state['agent_actions'].append(action_dict)
                state['metadata']['current_action'] = action_dict
                logger.warning("⚠️ [Agent Plan] ReAct Agent不可用，使用降级方案")
            
            # 记录执行时间
            execution_time = time.time() - start_time
            state['node_execution_times']['agent_plan'] = execution_time
            state['node_times']['agent_plan'] = execution_time
            
            logger.info(f"✅ [Agent Plan] 规划完成 (耗时: {execution_time:.2f}s)")
        
        except Exception as e:
            error_msg = f"Agent规划失败: {str(e)}"
            logger.error(f"❌ [Agent Plan] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'agent_plan',
                'error': error_msg,
                'timestamp': time.time()
            })
            # 降级：添加简单规划
            if 'agent_actions' not in state:
                state['agent_actions'] = []
            state['agent_actions'].append({
                'tool_name': 'knowledge_retrieval',
                'parameters': {'query': query},
                'reasoning': '规划过程出错，使用降级方案',
                'timestamp': time.time()
            })
        
        return state
    
    async def agent_act_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """Agent行动节点 - 执行规划的行动"""
        logger.info("⚡ [Agent Act] 开始Agent行动")
        start_time = time.time()
        
        try:
            current_action = state.get('metadata', {}).get('current_action')
            if not current_action:
                state['error'] = "没有当前行动计划"
                state['errors'].append({
                    'node': 'agent_act',
                    'error': state['error'],
                    'timestamp': time.time()
                })
                return state
            
            tool_name = current_action.get('tool_name', '')
            parameters = current_action.get('parameters', {})
            
            # 初始化Agent观察历史
            if 'agent_observations' not in state:
                state['agent_observations'] = []
            
            # 执行行动
            if self.system and hasattr(self.system, 'tool_registry'):
                # 🚀 修复：使用工具注册表执行行动，而不是调用不存在的_execute_action方法
                tool_registry = self.system.tool_registry
                if tool_registry:
                    tool = tool_registry.get_tool(tool_name)
                    if tool:
                        try:
                            # 执行工具
                            tool_result = await tool.execute(**parameters) if asyncio.iscoroutinefunction(tool.execute) else tool.execute(**parameters)
                            observation = {
                                'type': 'success',
                                'tool_name': tool_name,
                                'result': tool_result,
                                'timestamp': time.time()
                            }
                        except Exception as e:
                            observation = {
                                'type': 'error',
                                'tool_name': tool_name,
                                'error': str(e),
                                'timestamp': time.time()
                            }
                    else:
                        observation = {
                            'type': 'error',
                            'tool_name': tool_name,
                            'error': f'工具 {tool_name} 不可用',
                            'timestamp': time.time()
                        }
                    
                    state['agent_observations'].append(observation)
                    state['metadata']['current_observation'] = observation
                else:
                    # 降级：工具注册表不可用
                    observation = {
                        'type': 'error',
                        'error': '工具注册表不可用',
                        'timestamp': time.time()
                    }
                    state['agent_observations'].append(observation)
                    state['metadata']['current_observation'] = observation
            else:
                # 降级：系统不可用
                observation = {
                    'type': 'info',
                    'message': '系统不可用，跳过行动执行',
                    'timestamp': time.time()
                }
                state['agent_observations'].append(observation)
                state['metadata']['current_observation'] = observation
                logger.warning("⚠️ [Agent Act] 系统不可用，使用降级方案")
            
            # 记录执行时间
            execution_time = time.time() - start_time
            state['node_execution_times']['agent_act'] = execution_time
            state['node_times']['agent_act'] = execution_time
            
            logger.info(f"✅ [Agent Act] 行动完成 (耗时: {execution_time:.2f}s)")
        
        except Exception as e:
            error_msg = f"Agent行动失败: {str(e)}"
            logger.error(f"❌ [Agent Act] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'agent_act',
                'error': error_msg,
                'timestamp': time.time()
            })
            # 降级：添加错误观察
            if 'agent_observations' not in state:
                state['agent_observations'] = []
            state['agent_observations'].append({
                'type': 'error',
                'error': error_msg,
                'timestamp': time.time()
            })
        
        return state
    
    async def agent_observe_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """Agent观察节点 - 观察行动结果并判断任务是否完成"""
        logger.info("👁️ [Agent Observe] 开始Agent观察")
        start_time = time.time()
        
        try:
            current_observation = state.get('metadata', {}).get('current_observation', {})
            query = state.get('query', '')
            
            # 判断任务是否完成
            if self.react_agent:
                from src.agents.reasoning_expert import ReasoningExpert as ReActAgent
                react_agent = ReasoningExpert()
                
                # 判断任务是否完成
                task_complete = react_agent._is_task_complete(
                    thought="",  # 不依赖thought
                    observations=state.get('agent_observations', [])
                )
                
                state['task_complete'] = task_complete
                
                # 如果任务完成，提取答案
                if task_complete:
                    # 从观察中提取答案
                    observations = state.get('agent_observations', [])
                    if observations:
                        last_observation = observations[-1]
                        if isinstance(last_observation, dict):
                            result = last_observation.get('result', '')
                            if result:
                                state['answer'] = str(result)
                                state['final_answer'] = str(result)
                        elif isinstance(last_observation, str):
                            state['answer'] = last_observation
                            state['final_answer'] = last_observation
            else:
                # 降级：简单判断
                observations = state.get('agent_observations', [])
                if observations:
                    last_observation = observations[-1]
                    if isinstance(last_observation, dict):
                        result = last_observation.get('result', '')
                        if result:
                            state['task_complete'] = True
                            state['answer'] = str(result)
                            state['final_answer'] = str(result)
                        else:
                            state['task_complete'] = False
                    else:
                        state['task_complete'] = False
                else:
                    state['task_complete'] = False
                
                logger.warning("⚠️ [Agent Observe] ReAct Agent不可用，使用降级方案")
            
            # 更新迭代次数
            state['iteration'] = state.get('iteration', 0) + 1
            
            # 记录执行时间
            execution_time = time.time() - start_time
            state['node_execution_times']['agent_observe'] = execution_time
            state['node_times']['agent_observe'] = execution_time
            
            logger.info(f"✅ [Agent Observe] 观察完成，任务完成: {state.get('task_complete', False)} (耗时: {execution_time:.2f}s)")
        
        except Exception as e:
            error_msg = f"Agent观察失败: {str(e)}"
            logger.error(f"❌ [Agent Observe] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'agent_observe',
                'error': error_msg,
                'timestamp': time.time()
            })
            # 默认任务未完成
            state['task_complete'] = False
        
        return state
    
    async def chief_agent_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """核心大脑节点 - 协调整个多智能体系统，负责任务分解、规划、智能体协调和策略决策"""
        logger.info("🧠 [核心大脑] ChiefAgent 开始协调多智能体系统")
        start_time = time.time()
        
        try:
            query = state.get('query', '')
            if not query:
                state['error'] = "查询为空，无法进行多智能体协调"
                state['errors'].append({
                    'node': 'chief_agent',
                    'error': state['error'],
                    'timestamp': time.time()
                })
                return state
            
            # 🚀 统一架构：根据路由路径选择执行策略
            route_path = state.get('route_path', 'simple')
            complexity_score = state.get('complexity_score', 0)
            needs_reasoning_chain = state.get('needs_reasoning_chain', False)
            
            logger.info(f"🔍 [核心大脑] 路由路径: {route_path}, 复杂度: {complexity_score:.2f}, 需要推理链: {needs_reasoning_chain}")
            
            # 🚀 策略1：推理路径 - 使用推理引擎
            # 注意：route_path 可能是 "reasoning" 或 "reasoning_chain"，都表示推理路径
            if route_path in ("reasoning", "reasoning_chain") or needs_reasoning_chain:
                print(f"🧠 [核心大脑] 匹配策略1: route_path={route_path}, needs_reasoning_chain={needs_reasoning_chain}")
                logger.info("🧠 [核心大脑] 使用推理引擎策略（推理链处理）")
                return await self._handle_reasoning_path(state, query)

            # 🚀 策略2：简单查询 - 快速路径（跳过部分智能体，优化性能）
            elif route_path == "simple" or complexity_score < 3.0:
                print(f"⚡ [核心大脑] 匹配策略2: route_path={route_path}, complexity_score={complexity_score}")
                logger.info("⚡ [核心大脑] 使用快速路径策略（Simple查询优化）")
                return await self._handle_simple_path(state, query)

            # 🚀 策略3：复杂查询 - 完整智能体序列
            else:
                print(f"🔧 [核心大脑] 匹配策略3: route_path={route_path}, complexity_score={complexity_score}")
                logger.info("🔧 [核心大脑] 使用完整智能体序列策略（Complex/Multi-agent查询）")
                return await self._handle_full_agent_sequence(state, query)
        
        except Exception as e:
            error_msg = f"多智能体协调失败: {str(e)}"
            logger.error(f"❌ [核心大脑] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'chief_agent',
                'error': error_msg,
                'timestamp': time.time()
            })
            state['task_complete'] = False
        
        return state
    
    async def _handle_reasoning_path(self, state: ResearchSystemState, query: str) -> ResearchSystemState:
        """处理推理路径 - 使用推理引擎"""
        try:
            # 使用推理引擎处理推理链查询
            if self.system and hasattr(self.system, 'reasoning_engine') and self.system.reasoning_engine:
                from src.unified_research_system import ResearchRequest
                
                request = ResearchRequest(
                    query=query,
                    context=state.get('context', {})
                )
                
                result = await self.system.execute_research(request)
                
                if result.success:
                    state['evidence'] = result.knowledge or []
                    state['knowledge'] = result.knowledge or []
                    state['answer'] = result.answer
                    state['final_answer'] = result.answer
                    state['confidence'] = result.confidence
                    state['task_complete'] = True
                    logger.info(f"✅ [推理路径] 推理完成，答案长度: {len(result.answer) if result.answer else 0}")
                else:
                    state['error'] = result.error or "推理引擎执行失败"
                    state['task_complete'] = False
            else:
                # 降级：如果没有推理引擎，回退到完整智能体序列
                logger.warning("⚠️ [推理路径] 推理引擎不可用，回退到完整智能体序列")
                return await self._handle_full_agent_sequence(state, query)
        except Exception as e:
            logger.error(f"❌ [推理路径] 处理失败: {e}", exc_info=True)
            state['error'] = f"推理路径处理失败: {str(e)}"
            state['task_complete'] = False
        
        return state
    
    async def _handle_simple_path(self, state: ResearchSystemState, query: str) -> ResearchSystemState:
        """处理简单查询路径 - 快速路径（跳过部分智能体，优化性能）"""
        try:
            # ⚡ 快速路径：直接使用知识检索服务，跳过部分智能体
            from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
            knowledge_service = KnowledgeRetrievalService()
            
            logger.info("⚡ [快速路径] 直接检索知识库（跳过部分智能体）...")
            retrieval_result = await knowledge_service.execute(
                {"query": query},
                context=state.get('context', {})
            )
            
            if retrieval_result and retrieval_result.success:
                sources = []
                if isinstance(retrieval_result.data, dict):
                    sources = retrieval_result.data.get('sources', [])
                    if not sources and 'knowledge' in retrieval_result.data:
                        sources = retrieval_result.data.get('knowledge', [])
                elif isinstance(retrieval_result.data, list):
                    sources = retrieval_result.data
                
                if sources:
                    logger.info(f"✅ [快速路径] 检索到 {len(sources)} 条知识")
                    
                    # ⚡ 快速路径：使用简单的LLM调用生成答案（不需要推理链）
                    import os
                    from src.core.llm_integration import LLMIntegration
                    
                    # 尝试从系统获取LLM集成（如果可用）
                    llm = None
                    if self.system and hasattr(self.system, 'reasoning_engine'):
                        reasoning_engine = self.system.reasoning_engine
                        if hasattr(reasoning_engine, 'fast_llm_integration') and reasoning_engine.fast_llm_integration:
                            llm = reasoning_engine.fast_llm_integration
                    
                    # 如果系统没有可用的LLM集成，创建新的实例
                    if llm is None:
                        llm_config = {
                            'llm_provider': 'deepseek',
                            'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
                            'model': os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
                            'base_url': os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
                        }
                        llm = LLMIntegration(llm_config)
                    
                    # 构建知识上下文（最多使用5条知识）
                    knowledge_text = "\n\n".join([
                        f"[知识{i+1}]: {source.get('content', source.get('text', str(source)))}"
                        for i, source in enumerate(sources[:5])
                    ])
                    
                    # 构建简单的提示词
                    prompt = f"""基于以下知识回答问题。如果知识中包含答案，直接提取；如果不包含，基于知识进行合理推断。

问题: {query}

知识:
{knowledge_text}

要求:
1. 直接回答问题，不要重复问题
2. 如果知识中包含明确答案，直接提取
3. 如果知识不完整，基于已有知识进行合理推断
4. 答案要简洁准确，不超过100字

答案:"""
                    
                    # 调用LLM生成答案
                    try:
                        answer = llm._call_llm(prompt)
                        if answer and answer.strip():
                            answer = answer.strip()
                            logger.info(f"✅ [快速路径] 直接答案生成成功: {answer[:100]}...")
                            
                            state['evidence'] = sources
                            state['knowledge'] = sources
                            state['answer'] = answer
                            state['final_answer'] = answer
                            state['confidence'] = 0.85  # 快速路径的置信度稍低
                            state['task_complete'] = True
                        else:
                            logger.warning("⚠️ [快速路径] LLM返回空答案，回退到完整智能体序列")
                            return await self._handle_full_agent_sequence(state, query)
                    except Exception as e:
                        logger.warning(f"⚠️ [快速路径] LLM调用失败: {e}，回退到完整智能体序列")
                        return await self._handle_full_agent_sequence(state, query)
                else:
                    logger.warning("⚠️ [快速路径] 未检索到知识，回退到完整智能体序列")
                    return await self._handle_full_agent_sequence(state, query)
            else:
                logger.warning("⚠️ [快速路径] 知识检索失败，回退到完整智能体序列")
                return await self._handle_full_agent_sequence(state, query)
        except Exception as e:
            logger.error(f"❌ [快速路径] 处理失败: {e}", exc_info=True)
            # 回退到完整智能体序列
            logger.warning("⚠️ [快速路径] 回退到完整智能体序列")
            return await self._handle_full_agent_sequence(state, query)
        
        return state
    
    async def _handle_full_agent_sequence(self, state: ResearchSystemState, query: str) -> ResearchSystemState:
        """处理完整智能体序列 - 使用 Chief Agent 协调所有专家智能体"""
        try:
            print(f"🔧 [完整智能体序列] 检查chief_agent: {self.chief_agent is not None}")
            # 🧠 完整智能体序列：使用首席Agent进行协调
            if self.chief_agent:
                # 构建上下文
                context = {
                    'query': query,
                    'knowledge': state.get('knowledge', []),
                    'evidence': state.get('evidence', []),
                    'user_context': state.get('user_context', {}),
                    'route_path': state.get('route_path', 'complex'),
                    'complexity_score': state.get('complexity_score', 0)
                }
                
                # 执行首席Agent协调
                print(f"🔧 [完整智能体序列] 开始执行Chief Agent...")
                result = await self.chief_agent.execute(context)
                print(f"🔧 [完整智能体序列] Chief Agent执行完成，success={result.success}")

                if result.success:
                    # 提取结果
                    if isinstance(result.data, dict):
                        state['answer'] = result.data.get('answer', result.data.get('final_answer', ''))
                        state['final_answer'] = result.data.get('final_answer', result.data.get('answer', ''))
                        state['knowledge'] = result.data.get('knowledge', state.get('knowledge', []))
                        state['evidence'] = result.data.get('evidence', state.get('evidence', []))
                        state['confidence'] = result.confidence
                    else:
                        state['answer'] = str(result.data) if result.data else ''
                        state['final_answer'] = state['answer']
                    
                    state['task_complete'] = True
                    
                    # 记录协调信息
                    if 'metadata' not in state:
                        state['metadata'] = {}
                    state['metadata']['coordination_result'] = {
                        'success': True,
                        'confidence': result.confidence,
                        'processing_time': result.processing_time if hasattr(result, 'processing_time') else 0
                    }
                    logger.info(f"✅ [完整智能体序列] 协调完成，置信度: {result.confidence:.2f}")
                else:
                    state['error'] = result.error or "多智能体协调失败"
                    state['errors'].append({
                        'node': 'chief_agent',
                        'error': state['error'],
                        'timestamp': time.time()
                    })
                    state['task_complete'] = False
            else:
                # 降级：使用单个Agent执行
                logger.warning("⚠️ [完整智能体序列] 首席Agent不可用，使用单个Agent执行")
                if self.react_agent:
                    context = {'query': query}
                    result = await self.react_agent.execute(context)
                    if result.success:
                        state['answer'] = str(result.data) if result.data else ''
                        state['final_answer'] = state['answer']
                        state['task_complete'] = True
                    else:
                        state['error'] = result.error or "Agent执行失败"
                        state['task_complete'] = False
                else:
                    state['error'] = "没有可用的Agent"
                    state['task_complete'] = False
        except Exception as e:
            logger.error(f"❌ [完整智能体序列] 处理失败: {e}", exc_info=True)
            state['error'] = f"完整智能体序列处理失败: {str(e)}"
            state['task_complete'] = False
        
        return state
