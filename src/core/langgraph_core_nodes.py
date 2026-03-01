"""
核心功能节点模块 - RAG、提示词工程、上下文工程
将这些核心功能作为独立的工作流节点，使其在工作流图中可见
"""
import logging
import time
from typing import Dict, Any, Optional, List
from src.core.langgraph_unified_workflow import ResearchSystemState

logger = logging.getLogger(__name__)


class CoreNodes:
    """核心功能节点集合 - RAG、提示词工程、上下文工程"""
    
    def __init__(self, system=None):
        """初始化核心功能节点
        
        Args:
            system: UnifiedResearchSystem 实例（可选）
        """
        self.system = system
        self.knowledge_retrieval_agent = None
        self.prompt_engineering_agent = None
        self.context_engineering_agent = None
        self._initialize_agents()
    
    def _initialize_agents(self):
        """初始化核心功能智能体"""
        # 初始化知识检索智能体（RAG）
        try:
            # 尝试导入 EnhancedKnowledgeRetrievalAgent
            try:
                from src.agents.enhanced_knowledge_retrieval_agent import EnhancedKnowledgeRetrievalAgent
                self.knowledge_retrieval_agent = EnhancedKnowledgeRetrievalAgent()
                logger.info("✅ 知识检索智能体（EnhancedKnowledgeRetrievalAgent）初始化成功")
            except ImportError:
                # 降级：尝试导入 RAGAgent
                try:
                    from src.agents.rag_agent_wrapper import RAGAgentWrapper as RAGAgent
                    self.knowledge_retrieval_agent = RAGAgentWrapper(enable_gradual_replacement=True)
                    logger.info("✅ RAG智能体初始化成功")
                except ImportError:
                    # 再降级：尝试通过系统获取
                    if self.system and hasattr(self.system, 'tool_registry'):
                        # 使用工具注册表中的知识检索工具
                        self.knowledge_retrieval_agent = None  # 将通过工具调用
                        logger.info("✅ 将通过系统工具注册表进行知识检索")
                    else:
                        raise ImportError("无法导入知识检索智能体")
        except Exception as e:
            logger.warning(f"⚠️ 知识检索智能体初始化失败: {e}")
            self.knowledge_retrieval_agent = None
        
        # 初始化提示词工程智能体
        try:
            from src.agents.prompt_engineering_agent_wrapper import PromptEngineeringAgentWrapper as PromptEngineeringAgent
            self.prompt_engineering_agent = PromptEngineeringAgentWrapper(enable_gradual_replacement=True)
            logger.info("✅ 提示词工程智能体初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 提示词工程智能体初始化失败: {e}")
            self.prompt_engineering_agent = None
        
        # 初始化上下文工程智能体
        try:
            from src.agents.context_engineering_agent_wrapper import ContextEngineeringAgentWrapper as ContextEngineeringAgent
            self.context_engineering_agent = ContextEngineeringAgentWrapper(enable_gradual_replacement=True)
            logger.info("✅ 上下文工程智能体初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 上下文工程智能体初始化失败: {e}")
            self.context_engineering_agent = None
    
    async def rag_retrieval_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """RAG 知识检索节点
        
        从知识库中检索相关知识
        """
        logger.info("🔍 [RAG Retrieval] 开始知识检索...")
        start_time = time.time()
        
        try:
            query = state.get('query', '')
            if not query:
                state['error'] = "查询为空，无法进行知识检索"
                state['errors'].append({
                    'node': 'rag_retrieval',
                    'error': state['error'],
                    'timestamp': time.time()
                })
                return state
            
            # 使用知识检索智能体进行检索
            if self.knowledge_retrieval_agent:
                context = {
                    'query': query,
                    'query_type': state.get('query_type', 'general'),
                    'context': state.get('context', {})
                }
                
                result = await self.knowledge_retrieval_agent.execute(context)
                
                if result.success:
                    # 提取检索结果
                    if isinstance(result.data, dict):
                        state['evidence'] = result.data.get('chunks', result.data.get('evidence', []))
                        state['knowledge'] = result.data.get('sources', result.data.get('knowledge', []))
                        state['citations'] = result.data.get('citations', [])
                    else:
                        # 降级处理
                        state['evidence'] = [{"content": str(result.data)}] if result.data else []
                        state['knowledge'] = []
                    
                    logger.info(f"✅ [RAG Retrieval] 检索完成，找到 {len(state.get('evidence', []))} 条证据")
                else:
                    logger.warning(f"⚠️ [RAG Retrieval] 检索失败: {result.error}")
                    state['error'] = result.error or "知识检索失败"
                    state['evidence'] = []
                    state['knowledge'] = []
            else:
                # 降级：尝试通过系统工具注册表访问
                if self.system and hasattr(self.system, 'tool_registry'):
                    tool_registry = self.system.tool_registry
                    if tool_registry:
                        knowledge_tool = tool_registry.get_tool("knowledge_retrieval") or tool_registry.get_tool("rag")
                        if knowledge_tool:
                            try:
                                tool_result = await knowledge_tool.execute({"query": query})
                                if tool_result and hasattr(tool_result, 'data'):
                                    state['evidence'] = tool_result.data.get('chunks', [])
                                    state['knowledge'] = tool_result.data.get('sources', [])
                                    logger.info(f"✅ [RAG Retrieval] 通过工具检索到 {len(state.get('evidence', []))} 条证据")
                                else:
                                    state['evidence'] = []
                                    state['knowledge'] = []
                            except Exception as e:
                                logger.warning(f"⚠️ [RAG Retrieval] 工具执行失败: {e}")
                                state['evidence'] = []
                                state['knowledge'] = []
                        else:
                            logger.warning("⚠️ [RAG Retrieval] 知识检索工具不可用")
                            state['evidence'] = []
                            state['knowledge'] = []
                    else:
                        logger.warning("⚠️ [RAG Retrieval] 工具注册表不可用")
                        state['evidence'] = []
                        state['knowledge'] = []
                else:
                    logger.warning("⚠️ [RAG Retrieval] 知识检索智能体和系统都不可用")
                    state['evidence'] = []
                    state['knowledge'] = []
            
            # 记录执行时间
            execution_time = time.time() - start_time
            # 🚀 修复：确保 node_execution_times 和 node_times 存在
            if 'node_execution_times' not in state:
                state['node_execution_times'] = {}
            if 'node_times' not in state:
                state['node_times'] = {}
            state['node_execution_times']['rag_retrieval'] = execution_time
            state['node_times']['rag_retrieval'] = execution_time
            
        except Exception as e:
            error_msg = f"RAG知识检索失败: {str(e)}"
            logger.error(f"❌ [RAG Retrieval] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'rag_retrieval',
                'error': error_msg,
                'timestamp': time.time()
            })
            state['evidence'] = []
            state['knowledge'] = []
        
        return state
    
    async def prompt_engineering_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """提示词工程节点
        
        生成和优化提示词
        """
        logger.info("📝 [Prompt Engineering] 开始生成提示词...")
        start_time = time.time()
        
        try:
            query = state.get('query', '')
            if not query:
                state['error'] = "查询为空，无法生成提示词"
                state['errors'].append({
                    'node': 'prompt_engineering',
                    'error': state['error'],
                    'timestamp': time.time()
                })
                return state
            
            # 使用提示词工程智能体生成提示词
            if self.prompt_engineering_agent:
                context = {
                    'task_type': 'generate_prompt',
                    'query': query,
                    'template_name': state.get('prompt_template', 'general_query'),
                    'query_type': state.get('query_type', 'general'),
                    'evidence': state.get('evidence', []),
                    'enhanced_context': state.get('enhanced_context', {})
                }
                
                result = await self.prompt_engineering_agent.execute(context)
                
                if result.success:
                    # 提取生成的提示词
                    if isinstance(result.data, dict):
                        state['generated_prompt'] = result.data.get('prompt', '')
                        state['prompt_template'] = result.data.get('template_name', 'general_query')
                    else:
                        state['generated_prompt'] = str(result.data) if result.data else ''
                    
                    # 记录提示词元数据
                    if 'metadata' not in state:
                        state['metadata'] = {}
                    state['metadata']['prompt_engineering'] = {
                        'template_used': state.get('prompt_template', 'general_query'),
                        'prompt_length': len(state.get('generated_prompt', '')),
                        'confidence': result.confidence
                    }
                    
                    logger.info(f"✅ [Prompt Engineering] 提示词生成完成，长度: {len(state.get('generated_prompt', ''))}")
                else:
                    logger.warning(f"⚠️ [Prompt Engineering] 提示词生成失败: {result.error}")
                    # 降级：使用简单提示词
                    state['generated_prompt'] = f"Query: {query}\n\nPlease provide a comprehensive answer."
            else:
                # 降级：使用简单提示词
                logger.warning("⚠️ [Prompt Engineering] 提示词工程智能体不可用，使用简单提示词")
                state['generated_prompt'] = f"Query: {query}\n\nPlease provide a comprehensive answer."
            
            # 记录执行时间
            execution_time = time.time() - start_time
            # 🚀 修复：确保 node_execution_times 和 node_times 存在
            if 'node_execution_times' not in state:
                state['node_execution_times'] = {}
            if 'node_times' not in state:
                state['node_times'] = {}
            state['node_execution_times']['prompt_engineering'] = execution_time
            state['node_times']['prompt_engineering'] = execution_time
            
        except Exception as e:
            error_msg = f"提示词工程失败: {str(e)}"
            logger.error(f"❌ [Prompt Engineering] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'prompt_engineering',
                'error': error_msg,
                'timestamp': time.time()
            })
            # 降级：使用简单提示词
            state['generated_prompt'] = f"Query: {query}\n\nPlease provide a comprehensive answer."
        
        return state
    
    async def context_engineering_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """上下文工程节点
        
        增强和管理上下文信息
        """
        logger.info("🔗 [Context Engineering] 开始增强上下文...")
        start_time = time.time()
        
        try:
            query = state.get('query', '')
            session_id = state.get('session_id') or f"temp_{hash(query) % 10000}"
            
            # 使用上下文工程智能体增强上下文
            if self.context_engineering_agent:
                context = {
                    'task_type': 'get_context',
                    'query': query,
                    'session_id': session_id,
                    'max_fragments': 20,
                    'context': state.get('context', {})
                }
                
                result = await self.context_engineering_agent.execute(context)
                
                if result.success:
                    # 提取增强的上下文
                    if isinstance(result.data, dict):
                        enhanced_context = result.data.get('enhanced_context', {})
                        fragments = result.data.get('fragments', [])
                        
                        # 更新状态
                        state['enhanced_context'] = enhanced_context
                        state['context_fragments'] = fragments
                        
                        # 合并到原始上下文
                        if 'context' not in state:
                            state['context'] = {}
                        state['context'].update(enhanced_context)
                        
                        # 记录上下文元数据
                        if 'metadata' not in state:
                            state['metadata'] = {}
                        state['metadata']['context_engineering'] = {
                            'fragments_count': len(fragments),
                            'session_id': session_id,
                            'confidence': result.confidence
                        }
                        
                        logger.info(f"✅ [Context Engineering] 上下文增强完成，片段数: {len(fragments)}")
                    else:
                        logger.warning("⚠️ [Context Engineering] 上下文数据格式不正确")
                        state['enhanced_context'] = {}
                else:
                    logger.warning(f"⚠️ [Context Engineering] 上下文增强失败: {result.error}")
                    state['enhanced_context'] = {}
            else:
                # 降级：使用原始上下文
                logger.warning("⚠️ [Context Engineering] 上下文工程智能体不可用，使用原始上下文")
                state['enhanced_context'] = state.get('context', {})
            
            # 记录执行时间
            execution_time = time.time() - start_time
            # 🚀 修复：确保 node_execution_times 和 node_times 存在
            if 'node_execution_times' not in state:
                state['node_execution_times'] = {}
            if 'node_times' not in state:
                state['node_times'] = {}
            state['node_execution_times']['context_engineering'] = execution_time
            state['node_times']['context_engineering'] = execution_time
            
        except Exception as e:
            error_msg = f"上下文工程失败: {str(e)}"
            logger.error(f"❌ [Context Engineering] {error_msg}", exc_info=True)
            state['error'] = error_msg
            state['errors'].append({
                'node': 'context_engineering',
                'error': error_msg,
                'timestamp': time.time()
            })
            # 降级：使用原始上下文
            state['enhanced_context'] = state.get('context', {})
        
        return state

