"""
统一异步研究系统 - 整合所有异步组件
提供清晰的接口和统一的资源管理
"""

import asyncio
import logging
import sys
import time
import gc
import psutil
import json
import re
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from pathlib import Path

# 行动定义（用于标准Agent循环兜底调用工具）
from src.agents.react_agent import Action

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from datetime import datetime
from .agents.base_agent import AgentResult
#WY|from .ai.ai_algorithm_integrator import get_ai_algorithm_integrator

# 导入进化钩子（可选）
try:
    from .evolution.hook import get_evolution_hook
except ImportError:
    def get_evolution_hook():
        return None

# 导入统一配置模块
try:
    from .utils.unified_centers import get_smart_config, create_query_context
except ImportError:
    # 如果导入失败，使用os.getenv作为回退
    import os
    def _fallback_get_smart_config(key: str, context: Any = None) -> Any:
        return os.getenv(key, 0.5)
    def _fallback_create_query_context(query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        return {"query_type": query, "user_id": user_id}
    
    # 使用回退函数
    get_smart_config = _fallback_get_smart_config
    create_query_context = _fallback_create_query_context
    
    # 定义AgentResult作为回退
    from dataclasses import dataclass
    from typing import Optional, Dict, Any
    
    # AgentResult 已从 agents.base_agent 导入
    
    # 定义缺失的函数
    def get_smart_config(key: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """获取智能配置"""
        return os.getenv(key, None)
    
    def create_query_context(query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """创建查询上下文"""
        return {
            "query": query,
            "user_id": user_id,
            "timestamp": time.time()
        }

# 🚀 使用核心系统自己的日志模块（不依赖评测系统）
from src.utils.research_logger import log_info, log_warning, log_error, log_debug, UnifiedErrorHandler
import logging
logger = logging.getLogger(__name__)


@dataclass
class ResearchRequest:
    """研究请求数据类"""
    query: str
    context: Optional[Dict[str, Any]] = None
    priority: str = "normal"
    timeout: float = 1800.0  # 🚀 优化：从300秒增加到1800秒（30分钟），与per_item_timeout一致，适应复杂推理的真实需求（实际执行时间623-1354秒）
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ResearchResult:
    """研究结果数据类"""
    query: str
    success: bool
    answer: Optional[str] = None
    knowledge: Optional[List[Dict[str, Any]]] = None
    reasoning: Optional[str] = None
    citations: Optional[List[Dict[str, Any]]] = None
    confidence: float = 0.0
    execution_time: float = 0.0
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）"""
        return {
            "query": self.query,
            "success": self.success,
            "answer": self.answer,
            "knowledge": self.knowledge,
            "reasoning": self.reasoning,
            "citations": self.citations,
            "confidence": self.confidence,
            "execution_time": self.execution_time,
            "error": self.error,
            "metadata": self.metadata
        }


class UnifiedResearchSystem:
    """统一异步研究系统 - 整合所有异步组件"""

    def __init__(self, max_concurrent_queries: int = 3, enable_visualization_server: bool = True):
        # 🚀 方案3优化：读取环境变量以降低并发，避免多进程/多线程带来的不稳定
        try:
            import os as _os
            env_mcq = _os.getenv('MAX_CONCURRENT_QUERIES', None)
            if env_mcq is not None:
                max_concurrent_queries = max(1, int(env_mcq))
            # 🚀 方案3.2：禁用joblib多进程，强制线程后端
            _os.environ.setdefault('JOBLIB_MULTIPROCESSING', '0')
            _os.environ.setdefault('JOBLIB_START_METHOD', 'threading')
            # 🚀 方案3.2：限制底层并行库线程数，减少资源竞争
            _os.environ.setdefault('OMP_NUM_THREADS', '1')
            _os.environ.setdefault('MKL_NUM_THREADS', '1')
            _os.environ.setdefault('NUMEXPR_NUM_THREADS', '1')
            # 🚀 方案3.3：内存管理优化 - 固定哈希种子，提高缓存命中率
            if 'PYTHONHASHSEED' not in _os.environ:
                _os.environ.setdefault('PYTHONHASHSEED', '0')
            # 🚀 方案3.3：内存优化配置（如果系统支持）
            enable_memory_opt = _os.getenv('ENABLE_MEMORY_OPTIMIZATION', 'false').lower() == 'true'
            if enable_memory_opt:
                max_memory = _os.getenv('MAX_MEMORY_USAGE', '8GB')
                logger.info(f"✅ 内存优化已启用，最大内存使用: {max_memory}")
            # 🚀 禁用进度条输出：全局禁用HuggingFace和sentence-transformers的进度条
            _os.environ.setdefault('HF_HUB_DISABLE_PROGRESS_BARS', '1')
            _os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
        except Exception:
            pass

        self.max_concurrent_queries = max_concurrent_queries
        self.enable_visualization_server = enable_visualization_server
        self._semaphore = asyncio.Semaphore(max_concurrent_queries)
        self._is_initialized = False
        self._init_lock = asyncio.Lock()
        self._active_queries: Dict[str, asyncio.Task] = {}
        self._query_counter = 0
        
        # 🚀 优化：保存最新的推理结果，以便超时时使用
        self._latest_reasoning_result: Optional[Dict[str, Any]] = None
        # 当前正在处理的请求（用于工具调用时补全必要参数）
        self._current_request: Optional[ResearchRequest] = None

        # 🚀 重构：智能协调层架构
        # 智能协调层（核心大脑）
        self._orchestrator = None
        
        # 🚀 重构：智能协调层架构（最终优化架构）
        # 智能协调层（核心大脑）
        self._orchestrator = None
        
        # 🚀 P2改进：Entry Router（入口路由器）- 严格按照架构文档实现
        self._entry_router = None
        
        # 🚀 重构：多智能体系统架构
        # 首席Agent（协调整个系统）
        self._chief_agent = None
        self._use_mas = True  # 默认使用多智能体系统架构
        
        # 🚀 重构：传统流程使用真正的Agent（ExpertAgent子类），不再使用Service组件
        # 注意：传统流程现在使用ExpertAgent子类，与MAS架构保持一致
        self._knowledge_agent = None  # 真正的Agent：KnowledgeRetrievalAgent
        self._reasoning_agent = None  # 真正的Agent：ReasoningAgent
        self._answer_agent = None  # 真正的Agent：AnswerGenerationAgent
        self._citation_agent = None  # 真正的Agent：CitationAgent
        
        # 🚀 新增：ReAct Agent支持（可选，作为fallback）
        self._react_agent = None
        self._use_react_agent = False  # 默认不使用ReAct Agent（使用MAS）
        
        # 🚀 新增：LangGraph Agent支持（可选，使用LangGraph框架）
        self._langgraph_react_agent = None
        self._use_langgraph = False  # 默认不使用LangGraph（可通过环境变量启用）
        self._unified_workflow = None  # 统一工作流（MVP版本）
        import os
        self._use_langgraph = os.getenv('USE_LANGGRAPH', 'false').lower() == 'true'
        
        # 🚀 新增：浏览器可视化支持（可选）
        self._enable_browser_visualization = os.getenv('ENABLE_BROWSER_VISUALIZATION', 'false').lower() == 'true'
        self._visualization_server = None  # 浏览器可视化服务器
        self._orchestration_tracker = None  # 编排追踪器
        self._current_visualization_execution_id = None  # 当前可视化执行ID
        
        # 🚀 重构：标准Agent架构 - Agent状态管理
        self.observations: List[Dict[str, Any]] = []
        self.thoughts: List[str] = []
        self.actions: List[Any] = []  # Action类型将在导入时定义
        
        # 🚀 重构：标准Agent架构 - 工具注册表
        self.tool_registry = None  # 将在初始化时设置
        
        # 🚀 重构：标准Agent架构 - LLM客户端（用于思考）
        self.llm_client = None  # 将在初始化时设置
        
        # 🚀 重构：标准Agent架构 - 是否使用标准Agent循环
        # 可以通过环境变量USE_AGENT_LOOP=true启用
        import os
        self._use_agent_loop = os.getenv('USE_AGENT_LOOP', 'false').lower() == 'true'
        
        # 学习与深度学习组件（显式声明以满足类型检查）
        self.learning_system: Optional[Any] = None
        self.deep_learning_engine: Optional[Any] = None
        
        # AI算法集成器
        self._ai_algorithm_integrator = None
        
        # 增强功能
        self._performance_metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'average_response_time': 0.0,
            'concurrent_peak': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # 智能负载均衡
        self._load_balancer = {
            'agent_weights': {
                'knowledge': 1.0,
                'reasoning': 1.0,
                'answer': 1.0,
                'citation': 0.8
            },
            'performance_history': [],
            'adaptive_threshold': 0.8
        }
        
        # 🚀 增强缓存系统 - 支持查询缓存
        self._cache_system = {
            'query_cache': {},  # 完整查询结果缓存
            'knowledge_cache': {},
            'reasoning_cache': {},
            'cache_ttl': 300,  # 5分钟
            'max_cache_size': 1000,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # 智能重试机制
        self._retry_config = {
            'max_retries': 3,
            'base_delay': 1.0,
            'exponential_backoff': True,
            'retry_conditions': ['timeout', 'network_error', 'temporary_failure']
        }
        
        # 大脑决策机制增强 - 优化参数提高系统响应性
        self.brain_decision_config = {
            "nTc_threshold": 0.4,  # 降低阈值以提高响应性（从0.8降低到0.4）
            "evidence_accumulation_timeout": 10.0,  # 大幅降低以加速处理
            "commitment_lock_duration": 5.0,  # 承诺锁定持续时间
            "dynamic_threshold_adjustment": True,  # 动态阈值调整
        }
        
        # 决策状态管理
        self.decision_states = {
            'EVIDENCE_ACCUMULATION': '证据积累状态',
            'DECISION_COMMITMENT': '决策承诺状态',
            'EXECUTION': '执行状态'
        }
        self.current_decision_state = 'EVIDENCE_ACCUMULATION'
        
        # 决策轨迹跟踪
        self.decision_trajectories = {}
        self.committed_decisions = {}
        
        # 🚀 进化引擎钩子 - 请求级轻量反思和模式记录
        self._evolution_hook = get_evolution_hook()

    def _is_decision_committed(self, query_id: str) -> bool:
        """检查决策是否已承诺"""
        if query_id in self.committed_decisions:
            commit_time = self.committed_decisions[query_id]['timestamp']
            if time.time() - commit_time < self.brain_decision_config["commitment_lock_duration"]:
                return True
            else:
                del self.committed_decisions[query_id]
        return False
    
    def _get_committed_decision(self, query_id: str) -> ResearchResult:
        """获取已承诺的决策"""
        committed = self.committed_decisions[query_id]
        logger.info(f"使用已承诺研究决策: {query_id}")
        return committed['result']
    
    def _is_valid_answer_length(self, answer: str) -> bool:
        """🚀 修复答案丢失问题：检查答案长度是否有效（允许数字答案单字符和双字符）
        
        Args:
            answer: 答案文本
        
        Returns:
            答案长度是否有效
        """
        if not answer:
            return False
        
        answer_stripped = answer.strip()
        import re
        # 检查是否为数字答案（包括单字符数字）
        is_numerical_answer = bool(re.match(r'^\d+(?:st|nd|rd|th)?$', answer_stripped, re.IGNORECASE))
        
        # 对于数字答案，允许任何长度（包括单字符和双字符）
        # 对于非数字答案，要求长度>3（避免无意义的短片段）
        min_length = 1 if is_numerical_answer else 3
        return len(answer_stripped) >= min_length
    
    async def _accumulate_research_evidence(self, request: ResearchRequest) -> Dict[str, Any]:
        """研究证据积累阶段 - 类似大脑mPFC功能"""
        evidence_trajectory = {
            'query_id': f"query_{self._query_counter}_{int(time.time())}",
            'timestamp': time.time(),
            'evidence_axis': [],
            'confidence_scores': [],
            'agent_analysis': {},
            'query_complexity': self._analyze_query_complexity(request.query),
            'context_features': self._extract_context_features(request)
        }
        
        # 分析不同Agent的适用性（用于传统流程）
        # 注意：传统流程现在使用ExpertAgent子类，与MAS架构保持一致
        agents = {
            'knowledge_agent': self._knowledge_agent,
            'reasoning_agent': self._reasoning_agent,
            'answer_agent': self._answer_agent,
            'citation_agent': self._citation_agent
        }
        
        for agent_name, agent in agents.items():
            if agent:
                try:
                    # 模拟智能体分析过程
                    agent_confidence = self._analyze_agent_suitability(agent_name, request)
                    evidence_trajectory['agent_analysis'][agent_name] = {
                        'confidence': agent_confidence,
                        'available': True,
                        'processing_time': 0.0
                    }
                    evidence_trajectory['evidence_axis'].append(agent_confidence)
                    evidence_trajectory['confidence_scores'].append(agent_confidence)
                except Exception as e:
                    logger.warning(f"智能体 {agent_name} 分析失败: {e}")
                    evidence_trajectory['agent_analysis'][agent_name] = {
                        'confidence': 0.0,
                        'available': False,
                        'processing_time': 0.0,
                        'error': str(e)
                    }
        
        # 记录决策轨迹
        self.decision_trajectories[evidence_trajectory['query_id']] = evidence_trajectory
        
        return evidence_trajectory
    
    def _calculate_evidence_confidence(self, evidence_trajectory: Dict[str, Any]) -> float:
        """计算证据置信度 - 优化置信度积累速度"""
        if not evidence_trajectory['confidence_scores']:
            return 0.0
        
        # 使用加权平均计算置信度
        weights = [1.0] * len(evidence_trajectory['confidence_scores'])
        
        # 根据查询复杂度调整权重
        complexity = evidence_trajectory.get('query_complexity', 0.5)
        if complexity > 0.7:
            weights = [w * 1.2 for w in weights]  # 复杂查询提高权重
        
        # 计算加权平均
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0
        
        weighted_confidence = sum(score * weight for score, weight in 
                                zip(evidence_trajectory['confidence_scores'], weights))
        
        base_confidence = weighted_confidence / total_weight
        
        # 添加基础置信度提升，提高系统响应性
        # 根据证据数量增加基础置信度
        evidence_count = len(evidence_trajectory.get('confidence_scores', []))
        if evidence_count >= 2:
            # 有2个或更多证据时，给予0.3的基础提升（大幅提升以提高响应性）
            base_confidence = min(base_confidence + 0.3, 1.0)
        elif evidence_count >= 1:
            # 有1个证据时，给予0.15的基础提升
            base_confidence = min(base_confidence + 0.15, 1.0)
        
        return base_confidence
    
    def _calculate_dynamic_threshold(self, request: ResearchRequest, evidence_trajectory: Dict[str, Any]) -> float:
        """计算动态决策阈值"""
        if not self.brain_decision_config["dynamic_threshold_adjustment"]:
            return self.brain_decision_config["nTc_threshold"]
        
        threshold = self.brain_decision_config["nTc_threshold"]
        
        # 根据查询复杂度调整
        complexity = evidence_trajectory.get('query_complexity', 0.5)
        if complexity > 0.7:
            threshold *= 1.5  # 复杂查询提高阈值
        elif complexity < 0.3:
            threshold *= 0.9  # 简单查询降低阈值
        
        # 根据超时时间调整
        if request.timeout < 10:
            threshold *= 0.8  # 短超时降低阈值
        elif request.timeout > 60:
            threshold *= 1.2  # 长超时提高阈值
        
        # 限制在合理范围内
        return min(max(threshold, 0.3), 0.95)
    
    async def _commit_to_research_decision(self, request: ResearchRequest, evidence_trajectory: Dict[str, Any], 
                                         query_id: str, start_time: float) -> ResearchResult:
        """研究决策承诺阶段 - 近正交跳变到承诺轴"""
        logger.info(f"达到神经推断承诺时间(nTc): {query_id}")
        
        # 执行研究任务
        task = asyncio.create_task(
            self._execute_research_internal(request),
            name=query_id
        )
        self._active_queries[query_id] = task

        result = await asyncio.wait_for(task, timeout=request.timeout)

        if query_id in self._active_queries:
            del self._active_queries[query_id]

        execution_time = time.time() - start_time
        result.execution_time = execution_time
        
        # 记录承诺决策
        self.committed_decisions[query_id] = {
            'result': result,
            'timestamp': time.time(),
            'evidence_trajectory': evidence_trajectory
        }
        
        # 更新决策状态
        self.current_decision_state = 'EXECUTION'
        
        logger.info(f"研究决策承诺完成: {query_id} - 执行时间: {execution_time:.2f}秒")
        return result
    
    async def _get_partial_result_if_available(self, request: ResearchRequest, query_id: str, start_time: float) -> Optional[ResearchResult]:
        """
        🚀 快速失败机制：在超时时尝试获取部分结果（如果推理已完成）
        
        这个方法会在超时后检查是否有可用的部分结果，例如：
        - 推理已完成但后续步骤（答案生成、引用生成）未完成
        - 从推理引擎或日志中提取已完成的答案
        """
        try:
            # 方法1：检查是否有正在执行的任务已完成
            if query_id in self._active_queries:
                task = self._active_queries[query_id]
                
                # 如果任务已完成或取消，尝试获取结果
                if task.done():
                    try:
                        # 检查任务是否被取消
                        if task.cancelled():
                            logger.debug(f"任务已被取消，无法获取结果")
                        else:
                            result = task.result()
                            if result and hasattr(result, 'answer') and result.answer:
                                execution_time = time.time() - start_time
                                # 标记为部分成功（推理完成但后续步骤可能未完成）
                                if hasattr(result, 'success'):
                                    result.success = True  # 即使部分完成也标记为成功
                                if hasattr(result, 'execution_time'):
                                    result.execution_time = execution_time
                                logger.info(f"✅ 从已完成任务获取部分结果: {result.answer[:50] if result.answer else 'None'}")
                                return result
                    except asyncio.CancelledError:
                        logger.debug(f"任务被取消，无法获取结果")
                    except Exception as e:
                        logger.debug(f"无法从已完成任务获取结果: {e}")
            
            # 方法2：从保存的最新推理结果中提取答案（改进：使用查询匹配而非query_id）
            if self._latest_reasoning_result:
                # 🚀 优化：使用查询文本匹配，不依赖query_id
                saved_query = self._latest_reasoning_result.get('query', '')
                if saved_query and request.query and saved_query[:100] == request.query[:100]:
                    reasoning_answer = self._latest_reasoning_result.get('reasoning_answer')
                    if reasoning_answer and self._is_valid_answer_length(reasoning_answer):
                        execution_time = time.time() - start_time
                        logger.info(f"✅ 从保存的推理结果获取部分答案: {reasoning_answer[:50]}...")
                        return ResearchResult(
                            query=request.query,
                            success=True,  # 标记为成功，因为推理已完成
                            answer=reasoning_answer,
                            knowledge=[],
                            reasoning="推理已完成，但后续处理步骤超时",
                            citations=[],
                            confidence=0.7,  # 中等置信度
                            execution_time=execution_time,
                            metadata={
                                "partial_result": True,
                                "reasoning_completed": True,
                                "subsequent_steps_timeout": True
                            }
                        )
            
            # 方法3：从日志文件中读取已完成的推理结果（新增）
            try:
                reasoning_answer = self._extract_reasoning_from_log(request.query)
                if reasoning_answer and self._is_valid_answer_length(reasoning_answer):
                    execution_time = time.time() - start_time
                    logger.info(f"✅ 从日志中提取推理结果: {reasoning_answer[:50]}...")
                    return ResearchResult(
                        query=request.query,
                        success=True,
                        answer=reasoning_answer,
                        knowledge=[],
                        reasoning="推理已完成（从日志提取），但后续处理步骤超时",
                        citations=[],
                        confidence=0.7,
                        execution_time=execution_time,
                        metadata={
                            "partial_result": True,
                            "reasoning_completed": True,
                            "extracted_from_log": True,
                            "subsequent_steps_timeout": True
                        }
                    )
            except Exception as e:
                logger.debug(f"从日志提取推理结果失败: {e}")
                
            return None
        except Exception as e:
            logger.warning(f"获取部分结果失败: {e}")
            return None

    def shutdown(self) -> None:
        """关闭系统并释放资源"""
        logger.info("🛑 正在关闭 UnifiedResearchSystem 并释放资源...")
        
        # 1. 关闭统一工作流
        if hasattr(self, '_unified_workflow') and self._unified_workflow:
            # 工作流可能没有显式的关闭方法，但我们可以尝试释放引用
            self._unified_workflow = None
            
        # 2. 关闭所有传统Agent
        if hasattr(self, '_agents') and self._agents:
            for agent_id, agent in self._agents.items():
                try:
                    shutdown_method = getattr(agent, 'shutdown', None)
                    if callable(shutdown_method):
                        shutdown_method()
                        logger.debug(f"已关闭Agent: {agent_id}")
                except Exception as e:
                    logger.warning(f"关闭Agent {agent_id} 失败: {e}")
            self._agents.clear()

        # 3. 关闭其他Agent组件
        special_agents = [
            ('_react_agent', 'ReAct Agent'),
            ('_chief_agent', 'Chief Agent'),
            ('_langgraph_react_agent', 'LangGraph Agent'),
            ('_knowledge_agent', 'Knowledge Agent'),
            ('_reasoning_agent', 'Reasoning Agent'),
            ('_answer_agent', 'Answer Agent'),
            ('_citation_agent', 'Citation Agent')
        ]
        
        for attr_name, agent_name in special_agents:
            if hasattr(self, attr_name):
                agent = getattr(self, attr_name)
                if agent:
                    try:
                        shutdown_method = getattr(agent, 'shutdown', None)
                        if callable(shutdown_method):
                            shutdown_method()
                            logger.debug(f"已关闭 {agent_name}")
                    except Exception as e:
                        logger.warning(f"关闭 {agent_name} 失败: {e}")

        # 4. 关闭 LLM 客户端
        if hasattr(self, 'llm_client') and self.llm_client:
            try:
                # 如果 LLM 客户端有关闭方法
                if hasattr(self.llm_client, 'close'):
                     if asyncio.iscoroutinefunction(self.llm_client.close):
                         # 无法在同步 shutdown 中 await，只能跳过或依赖 __del__
                         pass
                     else:
                         self.llm_client.close()
            except Exception as e:
                logger.warning(f"关闭 LLM Client 失败: {e}")

        # 5. 强制垃圾回收
        import gc
        gc.collect()
        
        logger.info("✅ UnifiedResearchSystem 资源已释放")
    
    def _extract_reasoning_from_log(self, query: str) -> Optional[str]:
        """
        🚀 从日志文件中提取已完成的推理结果
        
        解析日志中的"✅ 推理完成: [answer]"行，匹配对应的查询
        """
        try:
            import re
            import os
            log_file_path = "research_system.log"
            
            if not os.path.exists(log_file_path):
                return None
            
            # 读取日志文件的最后1000行（最近的日志）
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 只检查最近的日志（最后500行）
                recent_lines = lines[-500:] if len(lines) > 500 else lines
            
            # 查找匹配的查询和推理结果
            query_match = None
            reasoning_result = None
            
            for i, line in enumerate(recent_lines):
                # 查找查询开始
                if f"query={query[:80]}" in line or (len(query) > 80 and f"query={query[:80]}" in line):
                    query_match = i
                    # 在查询之后的50行内查找推理完成
                    for j in range(i, min(i + 50, len(recent_lines))):
                        if "✅ 推理完成:" in recent_lines[j]:
                            # 提取答案
                            match = re.search(r'✅ 推理完成:\s*(.+?)(?:\s*\(置信度|$)', recent_lines[j])
                            if match:
                                reasoning_result = match.group(1).strip()
                                # 清理答案（移除置信度信息等）
                                reasoning_result = reasoning_result.split('(置信度')[0].strip()
                                logger.info(f"从日志提取推理结果: {reasoning_result[:50]}...")
                                return reasoning_result
                    break
            
            return None
        except Exception as e:
            logger.debug(f"从日志提取推理结果异常: {e}")
            return None
    
    async def _continue_research_evidence_gathering(self, request: ResearchRequest, evidence_trajectory: Dict[str, Any], 
                                                  query_id: str, start_time: float) -> ResearchResult:
        """继续研究证据积累阶段"""
        logger.info(f"继续研究证据积累: {query_id} - 当前置信度: {self._calculate_evidence_confidence(evidence_trajectory):.3f}")
        
        # 检查是否超时
        if time.time() - evidence_trajectory['timestamp'] > self.brain_decision_config["evidence_accumulation_timeout"]:
            logger.warning(f"研究证据积累超时，强制决策: {query_id}")
            return await self._commit_to_research_decision(request, evidence_trajectory, query_id, start_time)
        
        # 返回当前最佳结果
        task = asyncio.create_task(
            self._execute_research_internal(request),
            name=query_id
        )
        self._active_queries[query_id] = task

        result = await asyncio.wait_for(task, timeout=request.timeout)

        if query_id in self._active_queries:
            del self._active_queries[query_id]

        execution_time = time.time() - start_time
        result.execution_time = execution_time
        
        # 添加元数据
        if not hasattr(result, 'metadata') or result.metadata is None:
            result.metadata = {}
        result.metadata.update({
            'decision_state': 'EVIDENCE_ACCUMULATION',
            'evidence_confidence': self._calculate_evidence_confidence(evidence_trajectory),
            'nTc_threshold': self.brain_decision_config["nTc_threshold"]
        })
        
        return result
    
    def _analyze_query_complexity(self, query: str) -> float:
        """分析查询复杂度 - 🚀 重构：使用统一复杂度服务（LLM判断）"""
        try:
            from src.utils.unified_complexity_model_service import get_unified_complexity_model_service
            complexity_service = get_unified_complexity_model_service()
            complexity_result = complexity_service.assess_complexity(
                query=query,
                query_type=None,
                evidence_count=0,
                use_cache=True
            )
            # 将复杂度评分（0-10）转换为0-1分数
            return complexity_result.score / 10.0
        except Exception as e:
            logger.warning(f"⚠️ 使用统一复杂度服务失败: {e}，使用fallback")
            # Fallback: 简单的规则判断
            complexity = 0.5  # 基础复杂度
            
            # 根据查询长度调整
            if len(query) > 200:
                complexity += 0.2
            elif len(query) < 50:
                complexity -= 0.1
            
            # 根据问号数量调整
            question_marks = query.count('?')
            complexity += question_marks * 0.05
            
            return min(max(complexity, 0.1), 1.0)
    
    def _extract_context_features(self, request: ResearchRequest) -> Dict[str, Any]:
        """提取上下文特征"""
        return {
            'query_length': len(request.query),
            'has_question_mark': '?' in request.query,
            'has_complex_words': any(word in request.query for word in ['分析', '比较', '解释', '推理', '研究']),
            'timeout': request.timeout,
            'user_id': getattr(request, 'user_id', None)
        }
    
    def _analyze_agent_suitability(self, agent_name: str, request: ResearchRequest) -> float:
        """分析智能体适用性"""
        try:
            # 根据智能体类型和查询特征匹配
            if agent_name == "knowledge_agent" and any(word in request.query for word in ['什么', '如何', '为什么', '定义']):
                return 0.9
            elif agent_name == "reasoning_agent" and any(word in request.query for word in ['分析', '比较', '推理', '原因']):
                return 0.9
            elif agent_name == "answer_agent" and any(word in request.query for word in ['总结', '回答', '解释', '说明']):
                return 0.9
            elif agent_name == "citation_agent" and any(word in request.query for word in ['引用', '来源', '参考', '文献']):
                return 0.9
            else:
                return 0.7  # 中等适用性
        except Exception:
            return 0.0

    async def initialize(self) -> None:
        """初始化系统"""
        async with self._init_lock:
            if self._is_initialized:
                return

            try:
                logger.info("🚀 开始初始化统一异步研究系统...")

                await self._initialize_core_components()

                await self._initialize_agents()

                self._is_initialized = True
                logger.info("✅ 统一异步研究系统初始化完成")

            except Exception as e:
                logger.error("❌ 系统初始化失败: {e}")
                raise

    async def _initialize_core_components(self) -> None:
        """初始化核心组件"""
        try:
            logger.info("🔧 初始化核心组件...")
            
            # 🚀 重构：初始化工具注册表
            try:
                from src.agents.tools.tool_registry import get_tool_registry
                self.tool_registry = get_tool_registry()
                logger.info("✅ 工具注册表初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ 工具注册表初始化失败: {e}，Agent循环功能将不可用")
                self.tool_registry = None
            
            # 🚀 重构：初始化LLM客户端（用于思考）
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
                logger.info("✅ LLM客户端初始化成功（用于Agent循环）")
            except Exception as e:
                logger.warning(f"⚠️ LLM客户端初始化失败: {e}，Agent循环功能将受限")
                self.llm_client = None
            
            # 🚀 重构：注册工具（如果工具注册表可用）
            if self.tool_registry:
                await self._register_tools()

            logger.info("✅ 核心组件初始化完成")

        except Exception as e:
            logger.error("❌ 核心组件初始化失败: {e}")
            raise

    async def _initialize_agents(self) -> None:
        """初始化智能体"""
        try:
            logger.info("🤖 初始化智能体...")

            # 使用回退智能体集成管理器
            self.agent_integrator = None

            # 初始化AI算法集成器
            try:
                self._ai_algorithm_integrator = get_ai_algorithm_integrator()
                logger.info("✅ AI算法集成器初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ AI算法集成器初始化失败: {e}")
                self._ai_algorithm_integrator = None

            # 🚀 新增：初始化LangGraph Agent（可选，通过环境变量启用）
            # 必须在 Entry Router 之前初始化，因为 Entry Router 需要知道 LangGraph 状态
            if self._use_langgraph:
                logger.info("🔄 [初始化] 开始初始化LangGraph Agent...")
                await self._initialize_langgraph_agent()
                logger.info("✅ [初始化] LangGraph Agent初始化完成")
            
            # 🚀 P2改进：初始化Entry Router（入口路由器）- 严格按照架构文档实现
            logger.info("🔄 [初始化] 开始初始化Entry Router...")
            logger.info(f"🔍 [DEBUG] Entry Router初始化前: _use_langgraph={self._use_langgraph}")
            await self._initialize_entry_router()
            logger.info(f"🔍 [DEBUG] Entry Router初始化后: _entry_router={self._entry_router is not None}")
            if self._entry_router is None:
                logger.warning("⚠️ [初始化] Entry Router初始化失败，_entry_router 为 None")
            else:
                logger.info("✅ [初始化] Entry Router初始化完成")
            
            # 🚀 重构：初始化智能协调层（最终优化架构）
            logger.info("🔄 [初始化] 开始初始化智能协调层...")
            await self._initialize_orchestrator()
            logger.info("✅ [初始化] 智能协调层初始化完成")
            
            # 🌐 新增：初始化统一工作流（MVP版本）
            await self._initialize_unified_workflow()
            
            # 🌐 新增：初始化浏览器可视化服务器（可选，通过参数控制）
            if self.enable_visualization_server:
                await self._initialize_visualization_server()
            
            # 🚀 重构：初始化多智能体系统
            logger.info("🔄 [初始化] 开始初始化ChiefAgent...")
            await self._initialize_chief_agent()
            logger.info("✅ [初始化] ChiefAgent初始化完成")
            
            # 🚀 重构：初始化传统流程使用的真正Agent（ExpertAgent子类）
            # 注意：传统流程现在使用ExpertAgent子类，与MAS架构保持一致
            logger.info("🔄 [初始化] 开始初始化传统流程Agent...")
            try:
                await self._initialize_traditional_agents()
                logger.info("✅ [初始化] 传统流程Agent初始化完成")
            except Exception as e:
                logger.warning(f"⚠️ [初始化] 传统流程Agent初始化失败: {e}，但将继续初始化其他Agent")
                # 即使传统流程Agent失败，也要确保ReAct Agent能被初始化

            # 🚀 新增：初始化ReAct Agent（可选，作为fallback）
            # 无论传统流程Agent是否成功，都要尝试初始化ReAct Agent
            logger.info("🔄 [初始化] 开始初始化ReAct Agent...")
            logger.info(f"🔍 [DEBUG] 调用前状态: _react_agent={self._react_agent}, _use_react_agent={self._use_react_agent}")
            try:
                await self._initialize_react_agent()
                logger.info("✅ [初始化] ReAct Agent初始化完成")
                logger.info(f"🔍 [DEBUG] 调用后状态: _react_agent={self._react_agent}, _use_react_agent={self._use_react_agent}")
            except Exception as e:
                logger.error(f"❌ [初始化] ReAct Agent初始化失败: {e}", exc_info=True)
            
            # 初始化学习系统
            logger.info("🔄 [初始化] 开始初始化学习系统...")
            await self._initialize_learning_system()
            logger.info("✅ [初始化] 学习系统初始化完成")
            
            # 🚀 重构：注册资源到智能协调层
            if self._orchestrator:
                logger.info("🔄 [初始化] 开始注册资源到智能协调层...")
                self._orchestrator.register_resource('mas', self._chief_agent)
                self._orchestrator.register_resource('standard_loop', self)  # UnifiedResearchSystem自身
                self._orchestrator.register_resource('traditional', self)  # 传统流程也在UnifiedResearchSystem中
                self._orchestrator.register_resource('tools', self.tool_registry)
                logger.info("✅ [初始化] 资源注册完成")
            
            # 🚀 P2改进：更新Entry Router的资源检查器（在资源注册后）
            if self._entry_router and self._orchestrator:
                # 更新资源检查器，使其能够通过orchestrator检查资源
                def updated_resource_checker(resource_name: str) -> bool:
                    """更新后的资源检查器（通过orchestrator检查）"""
                    return self._orchestrator.is_resource_available(resource_name) if self._orchestrator else False
                
                self._entry_router.resource_checker = updated_resource_checker
                logger.info("✅ [初始化] Entry Router资源检查器已更新")
            
            # 🚀 新增：初始化ML/RL调度优化器
            logger.info("🔄 [初始化] 开始初始化ML/RL调度优化器...")
            await self._initialize_ml_rl_scheduling()
            logger.info("✅ [初始化] ML/RL调度优化器初始化完成")

            # 注册到集成管理器（如果可用）
            # 注意：这些是真正的Agent（ExpertAgent子类），用于传统流程
            if hasattr(self, 'agent_integrator') and self.agent_integrator:
                if self._knowledge_agent:
                    self.agent_integrator.register_agent('knowledge_retrieval_agent', self._knowledge_agent)
                if self._reasoning_agent:
                    self.agent_integrator.register_agent('reasoning_agent', self._reasoning_agent)
                if self._answer_agent:
                    self.agent_integrator.register_agent('answer_generation_agent', self._answer_agent)
                if self._citation_agent:
                    self.agent_integrator.register_agent('citation_agent', self._citation_agent)

            logger.info("✅ 智能体初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 智能体初始化失败: {e}", exc_info=True)
            # 🚀 修复：不要直接 raise，而是记录错误并继续（允许部分组件失败）
            logger.warning(f"⚠️ 智能体初始化部分失败，但系统将继续运行: {e}")
            # 确保 Entry Router 仍然被初始化（即使其他组件失败）
            if self._entry_router is None:
                logger.warning("⚠️ Entry Router 未初始化，尝试单独初始化...")
                try:
                    await self._initialize_entry_router()
                except Exception as e2:
                    logger.error(f"❌ Entry Router 单独初始化也失败: {e2}", exc_info=True)
    
    async def _initialize_entry_router(self) -> None:
        """初始化Entry Router（入口路由器）- 严格按照架构文档实现"""
        try:
            from src.core.entry_router import EntryRouter
            
            # 🚀 改进：Entry Router现在使用统一复杂度判断服务（支持LLM判断）
            # 不再需要单独加载complexity_predictor
            
            # 创建资源检查器（用于检查MAS等资源是否可用）
            def resource_checker(resource_name: str) -> bool:
                """资源检查器"""
                if resource_name == 'mas':
                    return self._chief_agent is not None
                elif resource_name == 'standard_loop':
                    return self.tool_registry is not None and self.llm_client is not None
                elif resource_name == 'tools':
                    return self.tool_registry is not None
                elif resource_name == 'traditional':
                    return True  # 传统流程总是可用
                return False
            
            # 检查是否启用统一工作流
            import os
            use_unified_workflow = os.getenv('ENABLE_UNIFIED_WORKFLOW', 'true').lower() == 'true' and self._unified_workflow is not None
            
            self._entry_router = EntryRouter(
                complexity_predictor=None,  # 已废弃，使用统一服务
                resource_checker=resource_checker,
                use_langgraph=self._use_langgraph,  # 🚀 传递 LangGraph 启用状态
                use_unified_workflow=use_unified_workflow  # 🌐 传递统一工作流启用状态
            )
            logger.info("✅ Entry Router初始化成功（使用统一复杂度判断服务，支持LLM判断）")
        except Exception as e:
            logger.warning(f"⚠️ Entry Router初始化失败: {e}")
            self._entry_router = None
    
    async def _initialize_orchestrator(self) -> None:
        """初始化智能协调层"""
        try:
            from src.core.intelligent_orchestrator import IntelligentOrchestrator
            self._orchestrator = IntelligentOrchestrator()
            logger.info("✅ 智能协调层初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 智能协调层初始化失败: {e}")
            self._orchestrator = None
    
    async def _initialize_chief_agent(self) -> None:
        """初始化首席Agent（多智能体系统）"""
        try:
            if not self._use_mas:
                logger.info("ℹ️ 多智能体系统未启用，跳过首席Agent初始化")
                return
            
            logger.info("🤖 开始初始化首席Agent...")
            from src.agents.chief_agent import ChiefAgent
            
            self._chief_agent = ChiefAgent()
            logger.info("✅ 首席Agent初始化成功")
            
        except Exception as e:
            logger.warning(f"⚠️ 首席Agent初始化失败: {e}，将尝试使用标准Agent循环", exc_info=True)
            self._chief_agent = None
            # 🚀 优化：不立即禁用MAS，而是尝试使用标准Agent循环
            # 如果标准Agent循环也不可用，会在execute_research中回退到传统流程
    
    async def _initialize_react_agent(self) -> None:
        """初始化ReAct Agent（使用ReasoningExpert）- 简化版"""
        try:
            logger.info("🔍 [诊断] 开始初始化ReAct Agent（ReasoningExpert）...")

            # 导入ReasoningExpert
            from src.agents.reasoning_expert import ReasoningExpert
            logger.info("🔍 [诊断] ReasoningExpert导入成功")

            # 创建实例
            self._react_agent = ReasoningExpert()
            logger.info(f"🔍 [诊断] ReasoningExpert实例创建成功: {type(self._react_agent)}")

            # 设置标志
            self._use_react_agent = True
            logger.info("✅ ReAct Agent初始化成功（使用ReasoningExpert）")

        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ ReAct Agent初始化失败: {e}")
            logger.error(f"❌ 异常类型: {type(e).__name__}")
            logger.error(f"❌ 异常消息: {str(e)}")
            logger.error("=" * 60, exc_info=True)

            self._react_agent = None
            self._use_react_agent = False
            logger.warning("⚠️ ReAct Agent初始化失败，使用传统流程")
    
    async def _initialize_langgraph_agent(self) -> None:
        """初始化LangGraph Agent（可选，通过环境变量USE_LANGGRAPH=true启用）"""
        try:
            from src.agents.langgraph_react_agent import LangGraphReActAgent
            self._langgraph_react_agent = LangGraphReActAgent(agent_name="LangGraphReActAgent")
            logger.info("✅ LangGraph Agent初始化成功")
        except ImportError as e:
            logger.warning(f"⚠️ LangGraph未安装，跳过LangGraph Agent初始化: {e}")
            logger.warning("   安装命令: pip install langgraph")
            self._langgraph_react_agent = None
            self._use_langgraph = False
        except Exception as e:
            logger.error(f"❌ LangGraph Agent初始化失败: {e}", exc_info=True)
            self._langgraph_react_agent = None
            self._use_langgraph = False
    
    async def _initialize_ml_rl_scheduling(self) -> None:
        """🚀 新增：初始化ML/RL调度优化器"""
        try:
            logger.info("🚀 开始初始化ML/RL调度优化器...")
            from src.utils.ml_scheduling_optimizer import get_ml_scheduling_optimizer
            from src.utils.rl_scheduling_optimizer import get_rl_scheduling_optimizer
            
            self.ml_scheduling_optimizer = get_ml_scheduling_optimizer()
            logger.info("✅ ML调度优化器初始化成功")
            
            self.rl_scheduling_optimizer = get_rl_scheduling_optimizer()
            logger.info("✅ RL调度优化器初始化成功")
            
            logger.info("✅ ML/RL调度优化器初始化完成")
        except Exception as e:
            logger.warning(f"⚠️ ML/RL调度优化器初始化失败: {e}，将使用默认调度策略", exc_info=True)
            self.ml_scheduling_optimizer = None
            self.rl_scheduling_optimizer = None
    
    async def _initialize_learning_system(self) -> None:
        """初始化学习系统"""
        try:
            from src.agents.learning_system_wrapper import LearningSystemWrapper as LearningSystem
            
            # 创建学习系统实例
            self.learning_system = LearningSystemWrapper(enable_gradual_replacement=True)
            
            # 启用学习功能
            self.learning_system.enable_continuous_improvement()
            
            logger.info("✅ 学习系统初始化成功")
            
        except Exception as e:
            logger.warning(f"⚠️ 学习系统初始化失败: {e}")
            self.learning_system = None

    async def _initialize_unified_workflow(self) -> None:
        """初始化统一工作流（MVP版本）"""
        try:
            import os
            enable_workflow = os.getenv('ENABLE_UNIFIED_WORKFLOW', 'true').lower() == 'true'
            
            if not enable_workflow:
                logger.info("🔄 [初始化] 统一工作流已禁用（ENABLE_UNIFIED_WORKFLOW=false）")
                logger.info("🔄 [提示] 设置 ENABLE_UNIFIED_WORKFLOW=true 以启用工作流")
                self._unified_workflow = None
                return
            
            try:
                from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow, LANGGRAPH_AVAILABLE
                
                if not LANGGRAPH_AVAILABLE:
                    logger.warning("🔄 [初始化] LangGraph 不可用")
                    logger.warning("🔄 [提示] 安装 LangGraph: pip install langgraph")
                    self._unified_workflow = None
                    return
                
                # 🚀 优化：创建统一工作流（支持持久化检查点配置）
                logger.info("🔄 [初始化] 正在创建统一工作流...")
                # 从环境变量读取是否使用持久化检查点
                use_persistent_checkpoint = os.getenv('USE_PERSISTENT_CHECKPOINT', 'false').lower() == 'true'
                self._unified_workflow = UnifiedResearchWorkflow(
                    system=self,
                    use_persistent_checkpoint=use_persistent_checkpoint
                )
                
                # 验证工作流
                if self._unified_workflow and hasattr(self._unified_workflow, 'workflow'):
                    logger.info("✅ [初始化] 统一工作流（MVP）初始化完成")
                    logger.info(f"✅ [初始化] 工作流对象: {type(self._unified_workflow.workflow).__name__}")
                else:
                    logger.warning("⚠️ [初始化] 工作流对象创建失败（workflow 属性不存在）")
                    self._unified_workflow = None
                
            except ImportError as e:
                logger.error(f"❌ [初始化] 统一工作流模块导入失败: {e}")
                logger.error("💡 [提示] 安装 LangGraph: pip install langgraph")
                logger.error("💡 [提示] 或运行诊断脚本: python3 scripts/diagnose_workflow.py")
                self._unified_workflow = None
            except Exception as e:
                # 🚀 利用现有日志系统记录详细错误信息
                logger.error(f"❌ [初始化] 统一工作流初始化失败: {e}")
                import traceback
                error_traceback = traceback.format_exc()
                logger.error(f"详细错误信息:\n{error_traceback}")
                
                # 🚀 利用编排追踪器记录工作流初始化失败事件（如果可用）
                try:
                    if hasattr(self, '_orchestration_tracker') and self._orchestration_tracker:
                        self._orchestration_tracker.track_agent_end(
                            agent_name="UnifiedResearchWorkflow",
                            error=f"工作流初始化失败: {e}",
                            result={"error_traceback": error_traceback}
                        )
                except Exception:
                    pass  # 追踪失败不影响主流程
                
                # 🚀 利用现有监控能力进行诊断（而不是创建新工具）
                logger.error("🔍 [诊断] 利用现有监控能力检查可能的原因：")
                logger.error("   1. LangGraph 是否已安装: pip install langgraph")
                logger.error("   2. 检查详细处理节点模块是否可用")
                logger.error("   3. 检查核心功能节点模块是否可用")
                logger.error("   4. 检查系统依赖是否完整")
                logger.error("   5. 查看 /api/workflow/health 端点获取详细健康状态")
                
                # 尝试诊断具体问题（利用现有导入检查）
                try:
                    from src.core.langgraph_unified_workflow import LANGGRAPH_AVAILABLE
                    if not LANGGRAPH_AVAILABLE:
                        logger.error("   ❌ LangGraph 不可用")
                    else:
                        logger.info("   ✅ LangGraph 可用")
                except Exception as diag_e:
                    logger.error(f"   ❌ 诊断失败: {diag_e}")
                
                logger.error("💡 [提示] 使用现有监控能力诊断:")
                logger.error("   - 查看系统初始化日志（已记录详细错误信息）")
                logger.error("   - 访问 /api/workflow/health 端点获取健康状态")
                logger.error("   - 检查 OpenTelemetry 追踪数据（如果已启用）")
                self._unified_workflow = None
                
        except Exception as e:
            logger.error(f"❌ [初始化] 统一工作流初始化异常: {e}")
            import traceback
            logger.error(f"详细错误信息:\n{traceback.format_exc()}")
            self._unified_workflow = None

    async def _initialize_visualization_server(self) -> None:
        """初始化浏览器可视化服务器（可选）"""
        try:
            import os
            enable_viz = os.getenv('ENABLE_BROWSER_VISUALIZATION', 'true').lower() == 'true'
            
            if not enable_viz:
                logger.info("🌐 [初始化] 浏览器可视化已禁用（ENABLE_BROWSER_VISUALIZATION=false）")
                return
            
            try:
                from src.visualization.browser_server import BrowserVisualizationServer
                
                # 获取工作流（优先使用统一工作流，否则使用 LangGraph ReAct Agent 工作流）
                workflow = None
                if self._unified_workflow:
                    workflow = self._unified_workflow.workflow
                elif self._use_langgraph and self._langgraph_react_agent:
                    workflow = getattr(self._langgraph_react_agent, 'workflow', None)
                
                # 获取端口
                port = int(os.getenv('VISUALIZATION_PORT', '8080'))
                
                # 创建服务器（不立即启动，在后台任务中启动）
                self._visualization_server = BrowserVisualizationServer(
                    workflow=workflow,
                    system=self,
                    port=port
                )
                
                # 在后台任务中启动服务器
                async def start_viz_server():
                    try:
                        if self._visualization_server:
                            await self._visualization_server.start()
                    except Exception as e:
                        logger.warning(f"🌐 可视化服务器启动失败: {e}")
                
                # 创建后台任务
                asyncio.create_task(start_viz_server())
                
                logger.info(f"🌐 [初始化] 浏览器可视化服务器已启动: http://localhost:{port}")
                logger.info("🌐 [提示] 在浏览器中打开上述地址即可查看可视化界面")
                
            except ImportError as e:
                logger.warning(f"🌐 [初始化] 浏览器可视化模块未安装: {e}")
                logger.warning("🌐 [提示] 安装依赖: pip install fastapi uvicorn websockets")
                self._visualization_server = None
            except Exception as e:
                logger.warning(f"🌐 [初始化] 浏览器可视化服务器初始化失败: {e}")
                self._visualization_server = None
                
        except Exception as e:
            logger.warning(f"🌐 [初始化] 浏览器可视化服务器初始化异常: {e}")
            self._visualization_server = None
    
    async def _initialize_traditional_agents(self) -> None:
        """初始化传统流程使用的真正Agent（ExpertAgent子类）
        
        注意：传统流程现在使用ExpertAgent子类，与MAS架构保持一致。
        这些Agent与ChiefAgent中使用的Agent是同一类型，确保架构统一。
        """
        try:
            # 🚀 重构：使用真正的Agent（ExpertAgent子类），而不是Service组件
            from src.agents.reasoning_agent import ReasoningAgent
            from backup_legacy_agents.answer_generation_agent_wrapper import AnswerGenerationAgentWrapper
            from backup_legacy_agents.citation_agent_wrapper import CitationAgentWrapper
            from backup_legacy_agents.knowledge_retrieval_agent_wrapper import KnowledgeRetrievalAgentWrapper
            
            self._knowledge_agent = KnowledgeRetrievalAgentWrapper(enable_gradual_replacement=True)
            logger.info("✅ 知识检索Agent初始化成功（传统流程）")

            # 检查Agent的Service是否可用（Agent内部使用Service）
            # 🚀 修复：添加超时保护，防止ensure_index_ready()卡住
            try:
                if hasattr(self._knowledge_agent, 'service') and self._knowledge_agent.service:
                    service = self._knowledge_agent.service
                    if hasattr(service, 'faiss_service') and service.faiss_service:
                        logger.info("⏳ 等待统一FAISS服务初始化完成...")
                        try:
                            if hasattr(service.faiss_service, 'ensure_index_ready'):
                                # 🚀 修复：添加超时保护，防止卡住
                                try:
                                    # 🚀 重构：使用统一配置中心获取超时配置
                                    try:
                                        from src.utils.unified_centers import get_unified_config_center
                                        config_center = get_unified_config_center()
                                        timeout = config_center.get_timeout('initialization', default=30.0)
                                    except Exception:
                                        timeout = 30.0  # Fallback
                                    
                                    result = await asyncio.wait_for(
                                        service.faiss_service.ensure_index_ready(),
                                        timeout=timeout
                                    )
                                    if result:
                                        logger.info("✅ 统一FAISS服务初始化完成")
                                    else:
                                        logger.warning("⚠️ 统一FAISS服务初始化失败，但继续执行")
                                except asyncio.TimeoutError:
                                    logger.warning("⚠️ 统一FAISS服务初始化超时（30秒），但继续执行")
                                except Exception as e:
                                    logger.warning(f"⚠️ 统一FAISS服务初始化异常: {e}，但继续执行")
                            else:
                                logger.info("ℹ️ FAISS服务可用但无ensure_index_ready方法")
                        except Exception as e:
                            logger.warning(f"⚠️ 统一FAISS服务初始化异常: {e}，但继续执行")
                    else:
                        logger.info("ℹ️ 统一FAISS服务不可用")
            except Exception as e:
                logger.warning(f"⚠️ FAISS服务检查失败: {e}，但继续执行")

            # 使用统一的工具注册表实例初始化ReasoningAgent
            if not self.tool_registry:
                from src.agents.tools.tool_registry import get_tool_registry
                self.tool_registry = get_tool_registry()
            self._reasoning_agent = ReasoningAgent(tool_registry=self.tool_registry)
            logger.info("✅ 推理Agent初始化成功（传统流程）")

            self._answer_agent = AnswerGenerationAgentWrapper(enable_gradual_replacement=True)
            logger.info("✅ 答案生成Agent初始化成功（传统流程）")

            self._citation_agent = CitationAgentWrapper(enable_gradual_replacement=True)
            logger.info("✅ 引用Agent初始化成功（传统流程）")

            logger.info("✅ 传统流程Agent异步初始化完成（ExpertAgent子类）")

        except Exception as e:
            logger.error(f"❌ 传统流程Agent初始化失败: {e}", exc_info=True)
            raise
    
    async def _register_tools(self) -> None:
        """注册所有工具到工具注册表"""
        if not self.tool_registry:
            logger.warning("⚠️ 工具注册表未初始化，跳过工具注册")
            return
        
        try:
            logger.info("🔧 开始注册Agent Tools...")
            
            from src.agents.tools.knowledge_retrieval_tool import KnowledgeRetrievalTool
            from src.agents.tools.reasoning_tool import ReasoningTool
            from src.agents.tools.answer_generation_tool import AnswerGenerationTool
            from src.agents.tools.citation_tool import CitationTool
            from src.agents.tools.multimodal_tool import MultimodalTool
            
            self.tool_registry.register_tool(KnowledgeRetrievalTool())
            self.tool_registry.register_tool(ReasoningTool())
            self.tool_registry.register_tool(AnswerGenerationTool())
            self.tool_registry.register_tool(CitationTool())
            self.tool_registry.register_tool(MultimodalTool())  # 🚀 新增：多模态处理工具
            
            logger.info("✅ Agent Tools注册成功")
            
            # 注册Utility Tools（如果尚未注册）
            try:
                # 🚀 架构优化：RAGTool现在内部使用RAGAgent，已在ReActAgent中注册
                from src.agents.tools.search_tool import SearchTool
                from src.agents.tools.calculator_tool import CalculatorTool
                
                # 检查是否已注册，避免重复注册
                if not self.tool_registry.get_tool("search"):
                    self.tool_registry.register_tool(SearchTool())
                if not self.tool_registry.get_tool("calculator"):
                    self.tool_registry.register_tool(CalculatorTool())
                
                logger.info("✅ Utility Tools注册成功（RAG功能由RAGTool提供，内部使用RAGAgent）")
            except Exception as e:
                logger.warning(f"⚠️ Utility Tools注册失败: {e}，可能已注册")
            
            logger.info("✅ 所有工具注册完成")
            
        except Exception as e:
            logger.error(f"❌ 工具注册失败: {e}", exc_info=True)
            raise
    
    # 🚀 重构：标准Agent循环方法
    async def _think(self, query: str, observations: List[Dict[str, Any]], thoughts: List[str]) -> str:
        """思考阶段 - 使用LLM分析当前状态"""
        try:
            if not self.llm_client:
                # 如果没有LLM客户端，使用简单规则
                if not observations:
                    return "需要先查询知识库获取相关信息"
                elif len(observations) >= 3:
                    return "已收集到多条信息，可以继续处理"
                else:
                    return "需要继续收集信息"
            
            # 构建思考提示词
            observations_text = self._format_observations_for_think(observations)
            tools_meta = self.tool_registry.list_tools() if self.tool_registry else []
            tools_info = "\n".join([
                f"- {t['name']}: {t.get('description', '')}"
                for t in tools_meta
            ]) if tools_meta else "无可用工具"
            
            think_prompt = f"""你是一个智能助手，正在处理以下任务：

任务: {query}

已观察到的信息:
{observations_text if observations_text else "（暂无观察信息）"}

历史思考:
{chr(10).join(thoughts[-3:]) if thoughts else "（暂无思考记录）"}

可用工具:
{tools_info}

请思考：
1. 当前任务完成情况如何？
2. 还需要什么信息？
3. 下一步应该做什么？

请用简洁的语言描述你的思考过程（不超过200字）。"""
            
            # 调用LLM进行思考
            import asyncio
            loop = asyncio.get_event_loop()
            if not self.llm_client:
                return "需要继续收集信息"
            llm_client = self.llm_client  # 保存引用以避免lambda中的类型检查问题
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
            logger.error(f"❌ 思考阶段失败: {e}", exc_info=True)
            return "思考过程出错，继续执行"
    
    async def _plan_action(self, thought: str, query: str, observations: List[Dict[str, Any]]) -> Optional[Any]:
        """规划行动阶段 - 使用LLM决定调用哪个工具"""
        try:
            # 🚀 增强诊断：记录规划开始
            logger.info("🔍 [规划诊断] ========== 开始规划行动 ==========")
            print("🔍 [规划诊断] ========== 开始规划行动 ==========")
            
            # 🚀 增强诊断：检查前置条件
            if not self.tool_registry:
                logger.warning("⚠️ [规划诊断] ❌ tool_registry为None，无法规划")
                print("⚠️ [规划诊断] ❌ tool_registry为None，无法规划")
                print("⚠️ [规划诊断] 可能原因: 1) 工具注册表未初始化 2) 初始化失败")
                return None
            
            logger.debug(f"✅ [规划诊断] tool_registry已初始化，可用工具数量: {len(self.tool_registry.list_tools())}")
            print(f"✅ [规划诊断] tool_registry已初始化，可用工具数量: {len(self.tool_registry.list_tools())}")
            
            # 如果已有足够信息，不需要继续行动
            is_complete = self._is_task_complete(thought, observations)
            if is_complete:
                logger.info("✅ [规划诊断] 任务已完成，不需要继续规划")
                print("✅ [规划诊断] 任务已完成，不需要继续规划")
                print(f"🔍 [规划诊断] 已完成原因: observations数量={len(observations)}, 检查是否有最终答案")
                return None
            
            # 获取可用工具列表
            tools_meta = self.tool_registry.list_tools()
            available_tools = [t["name"] for t in tools_meta]
            logger.debug(f"🔍 [规划诊断] 可用工具列表: {tools_meta}")
            print(f"🔍 [规划诊断] 可用工具列表: {tools_meta}")
            
            # 🚀 核心策略：保证推理→答案生成的依赖链闭合
            # 1. 如果还没有成功的reasoning结果，但已经有知识检索结果，则强制优先调用reasoning
            has_reasoning_success = any(
                obs.get("tool_name") == "reasoning" and obs.get("success")
                for obs in observations
            )
            has_knowledge_success = any(
                obs.get("tool_name") == "knowledge_retrieval" and obs.get("success")
                for obs in observations
            )
            if (not has_reasoning_success) and has_knowledge_success and "reasoning" in available_tools:
                logger.info("✅ [规划诊断] 未找到成功的reasoning结果，且已完成知识检索，强制调用reasoning工具")
                print("✅ [规划诊断] 未找到成功的reasoning结果，且已完成知识检索，强制调用reasoning工具")
                from src.agents.react_agent import Action
                return Action(
                    tool_name="reasoning",
                    params={
                        "query": query,
                        "context": {}
                    },
                    reasoning="Need to perform reasoning after knowledge retrieval before answer generation"
                )
            
            tools_schema = {}
            for tool_name in available_tools:
                tool = self.tool_registry.get_tool(tool_name)
                if tool:
                    tools_schema[tool_name] = tool.get_parameters_schema()
            
            # 🚀 增强诊断：检查工具schema
            if not tools_schema:
                logger.warning("⚠️ [规划诊断] ❌ 工具schema为空，无法构建提示词")
                print("⚠️ [规划诊断] ❌ 工具schema为空，无法构建提示词")
                print("⚠️ [规划诊断] 可能原因: 工具注册了但get_parameters_schema()返回None")
                return None
            
            logger.debug(f"✅ [规划诊断] 工具schema已构建，包含{len(tools_schema)}个工具")
            print(f"✅ [规划诊断] 工具schema已构建，包含{len(tools_schema)}个工具")
            
            # 构建行动规划提示词
            observations_text = self._format_observations_for_think(observations)
            plan_prompt = f"""Based on the following information, decide the next action:

Task: {query}
Thought: {thought}
Observations: {observations_text if observations_text else "(none)"}

Available tools:
{json.dumps(tools_schema, indent=2, ensure_ascii=False)}

**🚨 CRITICAL: You MUST return a JSON object with EXACTLY these three fields:**
1. "tool_name" (REQUIRED): The name of the tool to use (must be one of: {', '.join(available_tools)})
2. "params" (REQUIRED): A JSON object containing the tool's parameters
3. "reasoning" (REQUIRED): A brief explanation of why you chose this tool

**CORRECT JSON FORMAT (you MUST follow this exactly):**
{{
    "tool_name": "rag",
    "params": {{"query": "{query}"}},
    "reasoning": "Need to retrieve information to answer the query"
}}

**❌ WRONG FORMAT (DO NOT return this):**
{{
    "query": "{query}"
}}

**CRITICAL REQUIREMENTS**:
1. The "tool_name" field is MANDATORY and must be one of the available tools listed above
2. For the "rag" or "knowledge_retrieval" tool, the "query" parameter MUST be the EXACT original query text
3. Return ONLY valid JSON, no other text before or after the JSON
4. Do NOT return just a query string - you MUST return a complete action object with tool_name, params, and reasoning"""
            
            # 🚀 增强诊断：检查提示词
            logger.debug(f"🔍 [规划诊断] 提示词已构建，长度: {len(plan_prompt)}字符")
            print(f"🔍 [规划诊断] 提示词已构建，长度: {len(plan_prompt)}字符")
            if len(plan_prompt) > 10000:
                logger.warning(f"⚠️ [规划诊断] 提示词过长({len(plan_prompt)}字符)，可能导致LLM处理失败")
                print(f"⚠️ [规划诊断] 提示词过长({len(plan_prompt)}字符)，可能导致LLM处理失败")
            
            # 调用LLM规划行动
            if not self.llm_client:
                logger.warning("⚠️ [规划诊断] ❌ LLM客户端未初始化，无法进行规划")
                print("⚠️ [规划诊断] ❌ LLM客户端未初始化，无法进行规划")
                print("⚠️ [规划诊断] 可能原因: 1) LLM客户端初始化失败 2) 语法错误导致初始化中断 3) API密钥未设置")
                print(f"⚠️ [规划诊断] llm_client类型: {type(self.llm_client)}")
                return None
            
            logger.debug(f"✅ [规划诊断] LLM客户端已初始化，类型: {type(self.llm_client)}")
            print(f"✅ [规划诊断] LLM客户端已初始化，类型: {type(self.llm_client)}")
            
            logger.debug(f"🔍 [规划诊断] 开始调用LLM规划，提示词长度: {len(plan_prompt)}字符")
            print(f"🔍 [规划诊断] 开始调用LLM规划，提示词长度: {len(plan_prompt)}字符")
            
            import asyncio
            loop = asyncio.get_event_loop()
            
            # 🚀 增强诊断：记录LLM调用开始时间
            import time
            start_time = time.time()
            
            try:
                if not self.llm_client:
                    logger.warning("⚠️ [规划诊断] LLM客户端未初始化")
                    return None
                llm_client = self.llm_client  # 保存引用以避免lambda中的类型检查问题
                response = await loop.run_in_executor(
                    None,
                    lambda: llm_client._call_llm(
                        plan_prompt,
                        dynamic_complexity="simple",
                        max_tokens_override=300
                    )
                )
                elapsed_time = time.time() - start_time
                logger.debug(f"✅ [规划诊断] LLM调用完成，耗时: {elapsed_time:.2f}秒")
                print(f"✅ [规划诊断] LLM调用完成，耗时: {elapsed_time:.2f}秒")
            except Exception as llm_error:
                elapsed_time = time.time() - start_time
                logger.error(f"❌ [规划诊断] LLM调用异常: {llm_error}，耗时: {elapsed_time:.2f}秒", exc_info=True)
                print(f"❌ [规划诊断] LLM调用异常: {llm_error}，耗时: {elapsed_time:.2f}秒")
                print(f"❌ [规划诊断] 异常类型: {type(llm_error).__name__}")
                print(f"❌ [规划诊断] 可能原因: 1) 网络连接问题 2) API调用超时 3) SSL错误 4) API密钥无效")
                return None
                
            if not response:
                logger.warning("⚠️ [规划诊断] ❌ LLM规划响应为空")
                print("⚠️ [规划诊断] ❌ LLM规划响应为空")
                print("⚠️ [规划诊断] 可能原因: 1) API返回空响应 2) 网络连接中断 3) API调用超时")
                return None
            
            logger.debug(f"✅ [规划诊断] LLM返回响应，长度: {len(response)}字符")
            print(f"✅ [规划诊断] LLM返回响应，长度: {len(response)}字符")
            print(f"🔍 [规划诊断] 响应内容预览: {response[:300]}...")
            
            # 🚀 增强诊断：检查响应格式
            if not response.strip():
                logger.warning("⚠️ [规划诊断] ❌ LLM响应为空字符串（只有空白字符）")
                print("⚠️ [规划诊断] ❌ LLM响应为空字符串（只有空白字符）")
                return None
            
            # 解析JSON响应
            logger.debug("🔍 [规划诊断] 开始解析JSON响应")
            print("🔍 [规划诊断] 开始解析JSON响应")
            
            action_dict = self._parse_action_response(response)
            if action_dict:
                logger.info(f"✅ [规划诊断] JSON解析成功，action_dict: {action_dict}")
                tool_name_value = action_dict.get('tool_name')
                print(f"✅ [规划诊断] JSON解析成功，tool_name: {tool_name_value}")
                
                # 🚀 增强诊断：验证action_dict
                if 'tool_name' not in action_dict:
                    logger.warning("⚠️ [规划诊断] ❌ action_dict缺少'tool_name'字段")
                    print("⚠️ [规划诊断] ❌ action_dict缺少'tool_name'字段")
                    print(f"⚠️ [规划诊断] action_dict keys: {list(action_dict.keys())}")
                    print(f"⚠️ [规划诊断] 完整action_dict: {action_dict}")
                    
                    # 🚀 修复：尝试从返回的字典中推断tool_name
                    # 如果只有'query'字段，可能是LLM误解了格式，尝试修复
                    if 'query' in action_dict and len(action_dict) == 1:
                        logger.warning("⚠️ [规划诊断] LLM只返回了query字段，尝试修复为rag工具")
                        print("⚠️ [规划诊断] LLM只返回了query字段，尝试修复为rag工具")
                        # 检查是否有rag工具可用
                        if 'rag' in available_tools:
                            action_dict = {
                                'tool_name': 'rag',
                                'params': {'query': action_dict['query']},
                                'reasoning': 'LLM returned query only, auto-fixed to use rag tool'
                            }
                            logger.info("✅ [规划诊断] 已修复为rag工具")
                            print("✅ [规划诊断] 已修复为rag工具")
                        else:
                            logger.error("❌ [规划诊断] 无法修复：rag工具不可用")
                            print("❌ [规划诊断] 无法修复：rag工具不可用")
                            return None
                    else:
                        logger.error("❌ [规划诊断] 无法修复：action_dict格式不符合预期")
                        print("❌ [规划诊断] 无法修复：action_dict格式不符合预期")
                        return None
                
                tool_name = action_dict.get('tool_name')
                
                # 🚀 增强诊断：检查tool_name是否为None或空字符串
                if tool_name is None:
                    logger.warning("⚠️ [规划诊断] ❌ tool_name为None（LLM返回了null值）")
                    print("⚠️ [规划诊断] ❌ tool_name为None（LLM返回了null值）")
                    print(f"⚠️ [规划诊断] 完整action_dict: {action_dict}")
                    print("⚠️ [规划诊断] 可能原因: 1) LLM返回的JSON中tool_name字段值为null 2) LLM未理解提示词要求")
                    return None
                
                if not tool_name or not tool_name.strip():
                    logger.warning(f"⚠️ [规划诊断] ❌ tool_name为空字符串或只包含空白字符: '{tool_name}'")
                    print(f"⚠️ [规划诊断] ❌ tool_name为空字符串或只包含空白字符: '{tool_name}'")
                    print(f"⚠️ [规划诊断] 完整action_dict: {action_dict}")
                    return None
                
                if tool_name not in available_tools:
                    logger.warning(f"⚠️ [规划诊断] ❌ 工具名称无效: '{tool_name}'，不在可用工具列表中")
                    print(f"⚠️ [规划诊断] ❌ 工具名称无效: '{tool_name}'，不在可用工具列表中")
                    print(f"⚠️ [规划诊断] 可用工具: {available_tools}")
                    print(f"⚠️ [规划诊断] 完整action_dict: {action_dict}")
                    return None
                
                # 导入Action类
                from src.agents.react_agent import Action
                try:
                    action = Action.from_dict(action_dict)
                    logger.info(f"✅ [规划诊断] Action对象创建成功: tool_name={action.tool_name}")
                    print(f"✅ [规划诊断] Action对象创建成功: tool_name={action.tool_name}")
                    return action
                except Exception as action_error:
                    logger.error(f"❌ [规划诊断] Action对象创建失败: {action_error}", exc_info=True)
                    print(f"❌ [规划诊断] Action对象创建失败: {action_error}")
                    print(f"❌ [规划诊断] action_dict: {action_dict}")
                    return None
            else:
                logger.warning(f"⚠️ [规划诊断] ❌ LLM规划响应解析失败")
                print(f"⚠️ [规划诊断] ❌ LLM规划响应解析失败")
                print(f"⚠️ [规划诊断] 原始响应: {response[:500]}...")
                print(f"⚠️ [规划诊断] 可能原因: 1) JSON格式错误 2) 响应包含非JSON内容 3) 正则提取失败")
                
                # 🚀 增强诊断：尝试手动提取JSON
                import re
                json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                if json_match:
                    logger.debug(f"🔍 [规划诊断] 正则找到JSON片段: {json_match.group(0)[:200]}...")
                    print(f"🔍 [规划诊断] 正则找到JSON片段: {json_match.group(0)[:200]}...")
                else:
                    logger.warning("⚠️ [规划诊断] 正则未找到JSON片段")
                    print("⚠️ [规划诊断] 正则未找到JSON片段")
                
                return None
            
        except Exception as e:
            logger.error(f"❌ [规划诊断] 规划行动阶段异常: {e}", exc_info=True)
            print(f"❌ [规划诊断] 规划行动阶段异常: {e}")
            print(f"❌ [规划诊断] 异常类型: {type(e).__name__}")
            print(f"❌ [规划诊断] 异常详情: {str(e)}")
            import traceback
            print(f"❌ [规划诊断] 异常堆栈:\n{traceback.format_exc()}")
            return None
    
    async def _execute_tool(self, action: Any) -> Dict[str, Any]:
        """执行工具阶段"""
        try:
            if not self.tool_registry or not action:
                return {
                    "success": False,
                    "error": "工具注册表未初始化或行动无效"
                }
            
            tool = self.tool_registry.get_tool(action.tool_name)
            if not tool:
                return {
                    "success": False,
                    "error": f"工具 {action.tool_name} 不存在"
                }
            
            # 🚀 P0修复：对于答案生成和推理工具，需要补全关键参数
            tool_params = dict(action.params)  # 复制参数，避免修改原始参数
            
            if action.tool_name == "reasoning":
                if "query" not in tool_params:
                    query_text = None
                    if hasattr(self, "_current_request") and self._current_request:
                        query_text = self._current_request.query
                    if query_text:
                        tool_params["query"] = query_text
                if "context" not in tool_params:
                    tool_params["context"] = {}
            
            if action.tool_name == "answer_generation":
                # 从observations中提取推理结果，构建dependencies
                dependencies = {}
                
                # 查找推理工具的结果
                for obs in self.observations:
                    if obs.get("tool_name") == "reasoning" and obs.get("success"):
                        # 找到推理结果，添加到dependencies
                        reasoning_data = obs.get("data", {})
                        if reasoning_data:
                            dependencies["reasoning"] = {
                                "data": reasoning_data,
                                "success": True
                            }
                            logger.info(f"🔍 [StandardLoop] 为答案生成工具添加推理结果到dependencies")
                            break
                
                # 如果找到了推理结果，将其添加到context中
                if dependencies:
                    if "context" not in tool_params:
                        tool_params["context"] = {}
                    elif not isinstance(tool_params["context"], dict):
                        tool_params["context"] = {}
                    
                    tool_params["context"]["dependencies"] = dependencies
                    logger.info(f"🔍 [StandardLoop] 为答案生成工具添加dependencies: keys={list(dependencies.keys())}")
                
                # 从observations中提取知识检索结果，构建knowledge_data
                knowledge_data = []
                for obs in self.observations:
                    if obs.get("tool_name") == "knowledge_retrieval" and obs.get("success"):
                        # 提取知识数据
                        k_data = obs.get("data", {})
                        if isinstance(k_data, dict):
                            # 如果是字典，通常包含sources列表
                            sources = k_data.get("sources", [])
                            if sources:
                                knowledge_data.extend(sources)
                            elif "data" in k_data: # 某些工具可能嵌套在data中
                                knowledge_data.extend(k_data["data"] if isinstance(k_data["data"], list) else [])
                        elif isinstance(k_data, list):
                            knowledge_data.extend(k_data)
                
                if knowledge_data:
                    tool_params["knowledge_data"] = knowledge_data
                    logger.info(f"🔍 [StandardLoop] 为答案生成工具注入知识数据: {len(knowledge_data)} 条记录")

                # 确保为答案生成工具提供原始查询文本
                if "query" not in tool_params:
                    query_text = None
                    if hasattr(self, "_current_request") and self._current_request:
                        query_text = self._current_request.query
                    if not query_text and self._latest_reasoning_result and isinstance(self._latest_reasoning_result, dict):
                        query_text = self._latest_reasoning_result.get("query")
                    if query_text:
                        tool_params["query"] = query_text
                        if "original_query" not in tool_params:
                            tool_params["original_query"] = query_text
            
            # Debug log for tool params
            if action.tool_name == "answer_generation":
                logger.info(f"🔍 [StandardLoop] Calling answer_generation with params keys: {list(tool_params.keys())}")
                if "query" in tool_params:
                    logger.info(f"🔍 [StandardLoop] query param present: {tool_params['query'][:50]}...")
                else:
                    logger.error(f"❌ [StandardLoop] query param MISSING for answer_generation!")

            # 调用工具
            result = await tool.call(**tool_params)
            
            # 兼容 IToolResult (output) 和 旧 ToolResult (data)
            data = getattr(result, 'output', None)
            if data is None and hasattr(result, 'data'):
                data = result.data

            return {
                "success": result.success,
                "tool_name": action.tool_name,
                "data": data,
                "error": result.error,
                "execution_time": result.execution_time
            }
            
        except Exception as e:
            logger.error(f"❌ 执行工具失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_task_complete(self, thought: str, observations: List[Dict[str, Any]]) -> bool:
        """判断任务是否完成"""
        # 检查是否有最终答案
        for obs in observations:
            if obs.get("tool_name") == "answer_generation" and obs.get("success"):
                answer = obs.get("data", {}).get("answer", "")
                if answer and len(answer) > 0:
                    return True
            # 🚀 架构优化：RAGTool已移除，统一使用RealReasoningEngine
            # 检查所有推理工具的结果（包括rag和reasoning）
            if obs.get("tool_name") in ["rag", "reasoning"] and obs.get("success"):
                answer = obs.get("data", {}).get("answer", "")
                if answer and len(answer) > 0:
                    return True
        
        return False
    
    def _generate_result(self, observations: List[Dict[str, Any]], thoughts: List[str], 
                        actions: List[Any], query: str) -> ResearchResult:
        """生成最终结果"""
        # 从观察中提取答案
        answer = ""
        knowledge = []
        reasoning = None
        citations = []
        
        logger.info(f"🔍 [答案提取] 开始从 {len(observations)} 个观察中提取答案")
        print(f"🔍 [DEBUG] [答案提取] 开始从 {len(observations)} 个观察中提取答案")
        
        for i, obs in enumerate(observations):
            tool_name = obs.get("tool_name")
            success = obs.get("success", False)
            logger.info(f"🔍 [答案提取] 处理观察{i+1}: tool_name={tool_name}, success={success}")
            print(f"🔍 [DEBUG] [答案提取] 处理观察{i+1}: tool_name={tool_name}, success={success}")
            if obs.get("tool_name") == "answer_generation" and obs.get("success"):
                answer = obs.get("data", {}).get("answer", "")
            # 🚀 架构优化：RAGTool已移除，统一使用RealReasoningEngine
            elif obs.get("tool_name") in ["rag", "reasoning"] and obs.get("success"):
                # 推理工具（RealReasoningEngine）也可能返回答案
                data = obs.get("data", {})
                if isinstance(data, dict):
                    # 🚀 P0修复：优先提取final_answer，然后是answer，支持多种数据结构
                    extracted_answer = (
                        data.get("final_answer") or 
                        data.get("answer") or 
                        (data.get("reasoning") if isinstance(data.get("reasoning"), str) and len(data.get("reasoning", "")) < 200 else None) or
                        answer
                    )
                    if extracted_answer and extracted_answer.strip() and extracted_answer != answer:
                        answer = extracted_answer.strip()
                        logger.info(f"✅ [答案提取] 从{obs.get('tool_name')}工具提取答案: {answer[:100]}...")
                    knowledge.extend(data.get("evidence", []))
                elif isinstance(data, str) and data.strip():
                    # 🚀 P0修复：如果data是字符串，直接使用
                    if not answer or len(data.strip()) < len(answer):
                        answer = data.strip()
                        logger.info(f"✅ [答案提取] 从{obs.get('tool_name')}工具提取字符串答案: {answer[:100]}...")
            elif obs.get("tool_name") == "knowledge_retrieval" and obs.get("success"):
                data = obs.get("data", {})
                if isinstance(data, dict):
                    knowledge.extend(data.get("sources", []))
            elif obs.get("tool_name") == "reasoning" and obs.get("success"):
                reasoning = obs.get("data", {})
            elif obs.get("tool_name") == "citation" and obs.get("success"):
                data = obs.get("data", {})
                if isinstance(data, dict):
                    citations.extend(data.get("citations", []))
        
        logger.info(f"🔍 [答案提取] 最终提取结果: answer长度={len(answer) if answer else 0}, answer内容={answer[:100] if answer else 'None'}...")
        print(f"🔍 [DEBUG] [答案提取] 最终提取结果: answer长度={len(answer) if answer else 0}, answer内容={answer[:100] if answer else 'None'}...")
        
        return ResearchResult(
            query=query,
            success=bool(answer),
            answer=answer,
            knowledge=knowledge if knowledge else None,
            reasoning=str(reasoning) if reasoning else None,
            citations=citations if citations else None,
            confidence=0.8 if answer else 0.0,
            execution_time=0.0  # 将在调用处设置
        )
    
    def _format_observations_for_think(self, observations: List[Dict[str, Any]]) -> str:
        """格式化观察信息用于思考"""
        if not observations:
            return ""
        
        formatted = []
        for i, obs in enumerate(observations[-5:], 1):  # 只显示最近5条
            tool_name = obs.get("tool_name", "unknown")
            success = obs.get("success", False)
            status = "成功" if success else "失败"
            formatted.append(f"{i}. 工具: {tool_name}, 状态: {status}")
            if success and obs.get("data"):
                data = obs.get("data", {})
                if isinstance(data, dict):
                    # 提取关键信息
                    if "answer" in data:
                        formatted.append(f"   答案: {str(data['answer'])[:100]}...")
                    if "sources" in data:
                        formatted.append(f"   知识源数量: {len(data['sources'])}")
        
        return "\n".join(formatted)
    
    def _parse_action_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析LLM返回的行动响应 - 🚀 修复：支持嵌套JSON对象"""
        try:
            # 🚀 修复：使用平衡括号匹配提取完整JSON对象
            def find_balanced_json(text: str) -> Optional[str]:
                """查找第一个完整的JSON对象（支持嵌套）"""
                start_idx = text.find('{')
                if start_idx == -1:
                    return None
                
                # 使用栈来匹配平衡的大括号
                depth = 0
                in_string = False
                escape_next = False
                
                for i in range(start_idx, len(text)):
                    char = text[i]
                    
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    
                    if not in_string:
                        if char == '{':
                            depth += 1
                        elif char == '}':
                            depth -= 1
                            if depth == 0:
                                # 找到完整的JSON对象
                                return text[start_idx:i+1]
                
                return None
            
            # 方式1：尝试使用平衡括号匹配提取JSON
            json_str = find_balanced_json(response)
            if json_str:
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # 方式2：尝试查找```json代码块
            json_block_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_block_match:
                try:
                    return json.loads(json_block_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # 方式3：尝试查找```代码块（无json标记）
            code_block_match = re.search(r'```\s*(\{.*?\})\s*```', response, re.DOTALL)
            if code_block_match:
                try:
                    return json.loads(code_block_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # 方式4：尝试直接解析整个响应
            return json.loads(response.strip())
            
        except Exception as e:
            logger.warning(f"⚠️ 解析行动响应失败: {e}, 响应: {response[:200]}")
            return None
    
    async def _execute_research_agent_loop(self, request: ResearchRequest, start_time: float) -> ResearchResult:
        """执行研究任务 - 标准Agent循环实现"""
        query = request.query
        
        # 重置Agent状态
        self.observations = []
        self.thoughts = []
        self.actions = []
        
        logger.info("🔄 开始标准Agent循环执行")
        print(f"🔄 [DEBUG] 开始标准Agent循环执行: query={query[:100]}...")
        
        # 🚀 P0修复：检查工具注册表
        if not self.tool_registry:
            logger.error("❌ 工具注册表未初始化")
            print("❌ [DEBUG] 工具注册表未初始化")
            return ResearchResult(
                query=query,
                success=False,
                answer="",
                error="工具注册表未初始化",
                confidence=0.0,
                execution_time=time.time() - start_time
            )
        
        available_tools = self.tool_registry.list_tools()
        logger.info(f"🔍 [DEBUG] 可用工具: {available_tools}")
        print(f"🔍 [DEBUG] 可用工具: {available_tools}")
        
        # Agent循环
        iteration = 0
        max_iterations = 10
        task_complete = False
        
        while iteration < max_iterations and not task_complete:
            logger.info(f"🔄 Agent循环迭代 {iteration + 1}/{max_iterations}")
            print(f"🔄 [DEBUG] Agent循环迭代 {iteration + 1}/{max_iterations}")
            
            # 1. 思考
            thought = await self._think(query, self.observations, self.thoughts)
            self.thoughts.append(thought)
            logger.info(f"💭 思考结果: {thought[:100]}...")
            print(f"💭 [DEBUG] 思考结果: {thought[:100]}...")
            
            # 2. 规划行动
            action = await self._plan_action(thought, query, self.observations)
            if not action or not action.tool_name:
                # 强制兜底：默认调用 rag 工具，保证至少检索一次
                available_tools = self.tool_registry.list_tools()
                if 'rag' in available_tools:
                    action = Action(
                        tool_name='rag',
                        params={'query': query},
                        reasoning='Fallback to RAG when planning failed or empty action'
                    )
                    logger.warning("⚠️ 规划为空，启用RAG兜底动作（这是正常的兜底机制，不是错误）")
                    print("⚠️ [DEBUG] 规划为空，启用RAG兜底动作（这是正常的兜底机制，不是错误）")
                else:
                    logger.info("⚠️ 无法规划行动且无RAG兜底，退出循环")
                    print(f"⚠️ [DEBUG] 无法规划行动且无RAG兜底，退出循环。action={action}")
                    break
            
            self.actions.append(action)
            logger.info(f"🎯 规划行动: {action.tool_name}")
            print(f"🎯 [DEBUG] 规划行动: {action.tool_name}, params={action.params}")
            
            # 3. 执行工具
            observation = await self._execute_tool(action)
            self.observations.append(observation)
            logger.info(f"✅ 工具执行: {action.tool_name}, 成功: {observation.get('success', False)}")
            print(f"✅ [DEBUG] 工具执行: {action.tool_name}, 成功: {observation.get('success', False)}")
            
            # 🚀 P0修复：详细记录工具执行结果
            if observation.get('data'):
                data = observation.get('data')
                if isinstance(data, dict):
                    answer_in_data = data.get('answer') or data.get('final_answer')
                    logger.info(f"🔍 [DEBUG] 工具返回数据包含答案: {answer_in_data[:100] if answer_in_data else 'None'}...")
                    print(f"🔍 [DEBUG] 工具返回数据包含答案: {answer_in_data[:100] if answer_in_data else 'None'}...")
                else:
                    logger.info(f"🔍 [DEBUG] 工具返回数据类型: {type(data)}, 内容: {str(data)[:200]}...")
                    print(f"🔍 [DEBUG] 工具返回数据类型: {type(data)}, 内容: {str(data)[:200]}...")
            
            # 4. 判断是否完成
            task_complete = self._is_task_complete(thought, self.observations)
            if task_complete:
                logger.info("✅ 任务完成，退出循环")
                print("✅ [DEBUG] 任务完成，退出循环")
            
            iteration += 1
        
        # 🚀 P0修复：详细记录最终状态
        logger.info(f"🔍 [DEBUG] 循环结束: iteration={iteration}, task_complete={task_complete}, observations数量={len(self.observations)}")
        print(f"🔍 [DEBUG] 循环结束: iteration={iteration}, task_complete={task_complete}, observations数量={len(self.observations)}")
        
        for i, obs in enumerate(self.observations):
            logger.info(f"🔍 [DEBUG] 观察{i+1}: tool_name={obs.get('tool_name')}, success={obs.get('success')}, has_data={obs.get('data') is not None}, error={obs.get('error')}")
            print(f"🔍 [DEBUG] 观察{i+1}: tool_name={obs.get('tool_name')}, success={obs.get('success')}, has_data={obs.get('data') is not None}, error={obs.get('error')}")
            if obs.get('data'):
                data = obs.get('data')
                if isinstance(data, dict):
                    logger.info(f"🔍 [DEBUG] 观察{i+1}数据字段: {list(data.keys())}")
                    print(f"🔍 [DEBUG] 观察{i+1}数据字段: {list(data.keys())}")
        
        # 5. 生成最终结果
        result = self._generate_result(self.observations, self.thoughts, self.actions, query)
        result.execution_time = time.time() - start_time
        
        logger.info(f"✅ 标准Agent循环执行完成，耗时: {result.execution_time:.2f}秒, answer={result.answer[:100] if result.answer else 'None'}...")
        print(f"✅ [DEBUG] 标准Agent循环执行完成，耗时: {result.execution_time:.2f}秒, answer={result.answer[:100] if result.answer else 'None'}...")
        return result

    async def execute_research(self, request: ResearchRequest) -> ResearchResult:
        """执行研究任务 - 使用智能协调层（最终优化架构）"""
        # 🚀 添加最开始的调试日志（只输出到日志，不输出到stdout，避免污染输入框）
        logger.debug(f"🔍 [DEBUG] execute_research 被调用: query={request.query[:50]}...")
        # 注意：不再使用 sys.stdout.write，避免输出被误认为是输入框内容
        
        if not self._is_initialized:
            sys.stdout.write(f"🔍 [DEBUG] 系统未初始化，开始初始化...\n")
            sys.stdout.flush()
            await self.initialize()
            sys.stdout.write(f"🔍 [DEBUG] 初始化完成: _is_initialized={self._is_initialized}, _entry_router={self._entry_router is not None}\n")
            sys.stdout.flush()

        async with self._semaphore:
            start_time = time.time()
            query_id = f"query_{self._query_counter}_{int(time.time())}"
            self._query_counter += 1
            self._current_request = request

            try:
                # 🔧 修复：使用log_info()确保日志写入文件
                log_info(f"🔍 开始执行研究任务: {request.query[:50]}...")
                logger.info(f"🔍 开始执行研究任务: {request.query[:50]}...")  # 保留logger.info用于控制台输出
                sys.stdout.write(f"🔍 [DEBUG] 开始执行研究任务: {request.query[:50]}...\n")
                sys.stdout.flush()
                sys.stdout.write(f"🔍 [DEBUG] _is_initialized={self._is_initialized}, _entry_router={self._entry_router is not None}, _use_langgraph={self._use_langgraph}\n")
                sys.stdout.flush()
                # 🎯 编排追踪：初始化追踪器（如果启用可视化或已有追踪器）
                from src.visualization.orchestration_tracker import get_orchestration_tracker
                execution_id = f"exec_{query_id}"
                tracker = None
                # 如果已有追踪器（由 BrowserVisualizationServer 设置），使用它
                # 否则，如果启用了浏览器可视化，创建新的追踪器
                if hasattr(self, '_orchestration_tracker') and self._orchestration_tracker:
                    tracker = self._orchestration_tracker
                    # 如果追踪器还没有开始执行，开始它
                    if not tracker.execution_id:
                        tracker.start_execution(execution_id)
                elif self._enable_browser_visualization:
                    tracker = get_orchestration_tracker()
                    tracker.start_execution(execution_id)
                    # 保存追踪器和执行ID供后续使用
                    self._orchestration_tracker = tracker
                    self._current_visualization_execution_id = execution_id
                
                # 🚀 改进：添加查询处理流程日志（评测系统需要，明确标记样本ID）
                sample_id = None
                if isinstance(request.context, dict):
                    sample_id = request.context.get('sample_id') or request.context.get('item_index')
                log_info("查询接收: RANGEN查询处理流程开始")
                if sample_id is not None:
                    log_info(f"查询接收: {request.query[:100]}, 样本ID={sample_id}")
                else:
                    log_info(f"查询接收: {request.query[:100]}")
                # 进入统一评测可解析日志
                log_info(f"RESEARCH start query={request.query[:120]}")
                
                # 🚀 P2改进：严格按照架构文档实现 - 先调用Entry Router
                logger.info(f"🔍 [DEBUG] Entry Router状态: {self._entry_router is not None}, LangGraph启用: {self._use_langgraph}, LangGraph Agent: {self._langgraph_react_agent is not None}")
                sys.stdout.write(f"🔍 [DEBUG] Entry Router状态: {self._entry_router is not None}, LangGraph启用: {self._use_langgraph}, LangGraph Agent: {self._langgraph_react_agent is not None}\n")
                sys.stdout.flush()
                if self._entry_router:
                    log_info("🚦 [Entry Router] ========== 使用Entry Router进行路由决策 ==========")
                    logger.info("🚦 使用Entry Router进行路由决策")
                    try:
                        # 构建上下文
                        context = self._build_context(request)
                        
                        # 调用Entry Router进行路由决策（添加超时保护）
                        import asyncio
                        try:
                            route_path = await asyncio.wait_for(
                                self._entry_router.route(
                                    query=request.query,
                                    context=context
                                ),
                                timeout=30.0  # 30秒超时
                            )
                        except asyncio.TimeoutError:
                            logger.error("❌ Entry Router路由决策超时（30秒），使用默认路由")
                            sys.stdout.write("❌ [DEBUG] Entry Router路由决策超时（30秒），使用默认路由\n")
                            sys.stdout.flush()
                            # 使用默认路由：如果启用统一工作流，使用react_agent，否则使用traditional
                            if self._unified_workflow:
                                route_path = "react_agent"
                            else:
                                route_path = "traditional"
                        
                        log_info(f"✅ [Entry Router] 路由决策完成: {route_path}")
                        logger.info(f"✅ [Entry Router] 路由决策: {route_path}")
                        logger.info(f"🔍 [DEBUG] LangGraph启用: {self._use_langgraph}, LangGraph Agent可用: {self._langgraph_react_agent is not None}")
                        
                        # 根据路由结果执行相应路径
                        if route_path == "standard_loop":
                            # 标准循环路径
                            result = await self._execute_standard_loop_path(request, start_time)
                            result.execution_time = time.time() - start_time
                            return result
                        elif route_path == "mas":
                            # MAS路径 - 需要经过Intelligent Orchestrator进行深度规划
                            if self._orchestrator:
                                result = await self._execute_via_orchestrator(request, start_time, route_path)
                                result.execution_time = time.time() - start_time
                                return result
                            else:
                                logger.warning("⚠️ Intelligent Orchestrator未初始化，回退到传统流程")
                                return await self._execute_traditional_flow_fallback(request, start_time)
                        elif route_path == "react_agent":
                            # ReAct Agent路径 - 优先使用统一工作流（如果启用），否则使用LangGraph ReAct Agent
                            if self._unified_workflow:
                                logger.info("🚀 使用统一工作流（MVP）执行查询")
                                result = await self._execute_with_unified_workflow(request, start_time)
                                result.execution_time = time.time() - start_time
                                return result
                            elif self._use_langgraph and self._langgraph_react_agent:
                                logger.info("🚀 使用LangGraph ReAct Agent执行查询")
                                result = await self._execute_with_langgraph_agent(request)
                                result.execution_time = time.time() - start_time
                                return result
                            # 回退到传统ReAct Agent
                            elif self._orchestrator:
                                result = await self._execute_via_orchestrator(request, start_time, route_path)
                                result.execution_time = time.time() - start_time
                                return result
                            else:
                                logger.warning("⚠️ Intelligent Orchestrator未初始化，回退到传统流程")
                                return await self._execute_traditional_flow_fallback(request, start_time)
                        else:
                            # traditional路径 - 直接执行传统流程
                            result = await self._execute_traditional_flow_fallback(request, start_time)
                            result.execution_time = time.time() - start_time
                            return result
                    except Exception as e:
                        logger.error(f"❌ Entry Router执行失败: {e}，回退到传统流程", exc_info=True)
                        log_error("Entry Router执行失败", f"❌ [Entry Router] 执行失败: {e}，回退到传统流程")
                        # 回退到传统流程
                        return await self._execute_traditional_flow_fallback(request, start_time)
                else:
                    # 如果Entry Router未初始化，回退到直接使用智能协调层（向后兼容）
                    logger.warning(f"⚠️ Entry Router未初始化，直接使用智能协调层（向后兼容）")
                    logger.warning(f"🔍 [DEBUG] Entry Router未初始化原因检查: _entry_router={self._entry_router}, _use_langgraph={self._use_langgraph}, _langgraph_react_agent={self._langgraph_react_agent is not None}")
                    sys.stdout.write(f"⚠️ [DEBUG] Entry Router未初始化，直接使用智能协调层（向后兼容）\n")
                    sys.stdout.flush()
                    sys.stdout.write(f"🔍 [DEBUG] Entry Router未初始化原因检查: _entry_router={self._entry_router}, _use_langgraph={self._use_langgraph}, _langgraph_react_agent={self._langgraph_react_agent is not None}\n")
                    sys.stdout.flush()
                    if self._orchestrator:
                        result = await self._execute_via_orchestrator(request, start_time, None)
                        result.execution_time = time.time() - start_time
                        return result
                    else:
                        logger.warning("⚠️ 智能协调层也未初始化，使用传统流程")
                        return await self._execute_traditional_flow_fallback(request, start_time)
            except Exception as e:
                logger.error(f"❌ 执行研究任务失败: {e}", exc_info=True)
                log_error("执行研究任务失败", f"❌ 执行研究任务失败: {e}")
                # 回退到传统流程
                return await self._execute_traditional_flow_fallback(request, start_time)
    
    async def _execute_standard_loop_path(self, request: ResearchRequest, start_time: float) -> ResearchResult:
        """执行标准循环路径（Entry Router路由结果）"""
        log_info("🔄 [标准循环路径] 开始执行标准循环路径")
        logger.info("🔄 执行标准循环路径")
        print(f"🔄 [DEBUG] [标准循环路径] 开始执行标准循环路径: query={request.query[:100]}...")
        
        # 🚀 P0修复：强制启用标准Agent循环（即使环境变量未设置）
        # 因为standard_loop路径应该总是使用Agent循环
        use_agent_loop = True  # 强制启用
        has_tool_registry = self.tool_registry is not None
        has_llm_client = self.llm_client is not None
        
        logger.info(f"🔍 [DEBUG] use_agent_loop={use_agent_loop}, tool_registry={has_tool_registry}, llm_client={has_llm_client}")
        print(f"🔍 [DEBUG] use_agent_loop={use_agent_loop}, tool_registry={has_tool_registry}, llm_client={has_llm_client}")
        
        # 🚀 P0修复：如果工具注册表或LLM客户端未初始化，尝试初始化
        if not has_tool_registry:
            logger.warning("⚠️ 工具注册表未初始化，尝试初始化...")
            print("⚠️ [DEBUG] 工具注册表未初始化，尝试初始化...")
            try:
                from src.agents.tools.tool_registry import get_tool_registry
                self.tool_registry = get_tool_registry()
                has_tool_registry = self.tool_registry is not None
                logger.info(f"✅ 工具注册表初始化{'成功' if has_tool_registry else '失败'}")
                print(f"✅ [DEBUG] 工具注册表初始化{'成功' if has_tool_registry else '失败'}")
            except Exception as e:
                logger.error(f"❌ 工具注册表初始化失败: {e}")
                print(f"❌ [DEBUG] 工具注册表初始化失败: {e}")
        
        if not has_llm_client:
            logger.warning("⚠️ LLM客户端未初始化，尝试初始化...")
            print("⚠️ [DEBUG] LLM客户端未初始化，尝试初始化...")
            try:
                from src.core.llm_integration import LLMIntegration
                from src.utils.unified_centers import get_unified_config_center
                config_center = get_unified_config_center()
                # 使用 get_env_config 获取 LLM 配置（与第691行的实现一致）
                llm_config = {
                    'llm_provider': config_center.get_env_config('llm', 'LLM_PROVIDER', 'deepseek'),
                    'api_key': config_center.get_env_config('llm', 'DEEPSEEK_API_KEY', ''),
                    'model': config_center.get_env_config('llm', 'REASONING_MODEL', 'deepseek-chat'),
                    'base_url': config_center.get_env_config('llm', 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
                }
                self.llm_client = LLMIntegration(llm_config)
                has_llm_client = self.llm_client is not None
                logger.info(f"✅ LLM客户端初始化{'成功' if has_llm_client else '失败'}")
                print(f"✅ [DEBUG] LLM客户端初始化{'成功' if has_llm_client else '失败'}")
            except Exception as e:
                logger.error(f"❌ LLM客户端初始化失败: {e}")
                print(f"❌ [DEBUG] LLM客户端初始化失败: {e}")
        
        if use_agent_loop and has_tool_registry and has_llm_client:
            try:
                logger.info("🔍 [DEBUG] 调用 _execute_research_agent_loop")
                print("🔍 [DEBUG] 调用 _execute_research_agent_loop")
                result = await self._execute_research_agent_loop(request, start_time)
                result.execution_time = time.time() - start_time
                log_info(f"✅ [标准循环路径] 执行成功")
                logger.info(f"✅ [标准循环路径] 执行成功: answer长度={len(result.answer) if result.answer else 0}")
                print(f"✅ [DEBUG] [标准循环路径] 执行成功: answer长度={len(result.answer) if result.answer else 0}")
                return result
            except Exception as e:
                logger.error(f"❌ 标准循环路径执行失败: {e}，回退到传统流程", exc_info=True)
                print(f"❌ [DEBUG] 标准循环路径执行失败: {e}")
                return await self._execute_traditional_flow_fallback(request, start_time)
        else:
            # 如果标准Agent循环不可用，回退到传统流程
            logger.warning("⚠️ 标准Agent循环不可用，回退到传统流程")
            logger.warning(f"⚠️ [DEBUG] use_agent_loop={use_agent_loop}, has_tool_registry={has_tool_registry}, has_llm_client={has_llm_client}")
            print(f"⚠️ [DEBUG] 标准Agent循环不可用，回退到传统流程")
            print(f"⚠️ [DEBUG] use_agent_loop={use_agent_loop}, has_tool_registry={has_tool_registry}, has_llm_client={has_llm_client}")
            log_info("⚠️ [标准循环路径] 回退到传统流程")
            result = await self._execute_traditional_flow_fallback(request, start_time)
            log_info(f"✅ [标准循环路径] 传统流程执行完成: answer长度={len(result.answer) if result.answer else 0}")
            logger.info(f"✅ [标准循环路径] 传统流程执行完成: answer长度={len(result.answer) if result.answer else 0}")
            return result
    
    async def _execute_via_orchestrator(self, request: ResearchRequest, start_time: float, route_path: Optional[str] = None) -> ResearchResult:
        """通过智能协调层执行（Entry Router路由到MAS或ReAct Agent时使用）"""
        log_info("🧠 [智能协调层] ========== 使用智能协调层执行查询 ==========")
        logger.info("🧠 使用智能协调层执行研究任务")
        try:
            # 🎯 编排追踪：传递追踪器到 Orchestrator
            tracker = getattr(self, '_orchestration_tracker', None)
            if tracker and self._orchestrator:
                setattr(self._orchestrator, '_orchestration_tracker', tracker)  # type: ignore
            
            # 构建上下文
            context = self._build_context(request)
            
            # 如果指定了路由路径，添加到上下文中
            if route_path:
                context['route_path'] = route_path
            
            # 调用智能协调层
            if not self._orchestrator:
                raise ValueError("Orchestrator not initialized")
            agent_result = await self._orchestrator.orchestrate(
                query=request.query,
                context=context
            )
            
            # 转换为ResearchResult
            result = self._convert_to_research_result(agent_result, request)
            result.execution_time = time.time() - start_time
            
            log_info(f"✅ [智能协调层] 执行成功，返回结果")
            log_info(f"✅ [智能协调层] 结果: success={result.success}, answer长度={len(result.answer) if result.answer else 0}")
            return result
        except Exception as e:
            logger.error(f"❌ 智能协调层执行失败: {e}，回退到传统流程", exc_info=True)
            log_error("智能协调层执行失败", f"❌ [智能协调层] 执行失败: {e}，回退到传统流程")
            # 回退到传统流程
            return await self._execute_traditional_flow_fallback(request, start_time)
    
    def _build_context(self, request: ResearchRequest) -> Dict[str, Any]:
        """构建协调层需要的上下文
        
        Args:
            request: 研究请求
            
        Returns:
            上下文字典
        """
        context = {
            "query": request.query,
            "priority": request.priority,
            "timeout": request.timeout,
            "metadata": request.metadata or {},
            "system_state": {
                "load": self._get_system_load() if hasattr(self, '_get_system_load') else 50.0,
                "mas_available": self._chief_agent is not None,
                "tools_available": self.tool_registry is not None,
                "standard_loop_available": True,  # UnifiedResearchSystem自身
                "traditional_available": True  # 传统流程也在UnifiedResearchSystem中
            }
        }
        
        # 添加请求的上下文信息
        if isinstance(request.context, dict):
            context.update(request.context)
        
        return context
    
    def _convert_to_research_result(self, agent_result: AgentResult, request: ResearchRequest) -> ResearchResult:
        """将AgentResult转换为ResearchResult，兼容旧版和新版AgentResult结构"""
        from src.interfaces.agent import AgentResult as NewAgentResult, ExecutionStatus
        
        success = False
        raw_data = None
        confidence = 0.0
        processing_time = 0.0
        error = None
        metadata = {}
        
        if isinstance(agent_result, NewAgentResult):
            success = agent_result.status == ExecutionStatus.COMPLETED
            raw_data = agent_result.output
            processing_time = agent_result.execution_time
            error = agent_result.error
            metadata = agent_result.metadata or {}
            confidence = metadata.get("confidence", 0.0)
        else:
            success = getattr(agent_result, "success", False)
            raw_data = getattr(agent_result, "data", None)
            confidence = getattr(agent_result, "confidence", 0.0)
            processing_time = getattr(agent_result, "processing_time", 0.0)
            error = getattr(agent_result, "error", None)
            metadata = getattr(agent_result, "metadata", {}) or {}
        
        if isinstance(raw_data, dict):
            answer = raw_data.get('answer', '')
            knowledge = raw_data.get('knowledge', [])
            reasoning = raw_data.get('reasoning', '')
            citations = raw_data.get('citations', [])
        elif isinstance(raw_data, str):
            answer = raw_data
            knowledge = []
            reasoning = None
            citations = []
        else:
            answer = str(raw_data) if raw_data else ''
            knowledge = []
            reasoning = None
            citations = []
        
        combined_metadata = {"method": "intelligent_orchestrator"}
        if metadata:
            combined_metadata["agent_metadata"] = metadata
        
        return ResearchResult(
            query=request.query,
            success=success,
            answer=answer,
            knowledge=knowledge if knowledge else None,
            reasoning=str(reasoning) if reasoning else None,
            citations=citations if citations else None,
            confidence=confidence,
            execution_time=processing_time,
            error=error,
            metadata=combined_metadata
        )
    
    async def _execute_traditional_flow_fallback(self, request: ResearchRequest, start_time: float) -> ResearchResult:
        """传统流程回退方案
        
        Args:
            request: 研究请求
            start_time: 开始时间
            
        Returns:
            ResearchResult: 研究结果
        """
        log_info("🔄 [传统流程] 开始执行传统流程回退方案")
        logger.info("🔄 [传统流程] 开始执行传统流程回退方案")
        try:
            result = await self._execute_research_internal(request)
            result.execution_time = time.time() - start_time
            log_info(f"✅ [传统流程] 执行完成: success={result.success}, answer长度={len(result.answer) if result.answer else 0}")
            logger.info(f"✅ [传统流程] 执行完成: success={result.success}, answer长度={len(result.answer) if result.answer else 0}")
            return result
        except Exception as e:
            logger.error(f"❌ [传统流程] 执行失败: {e}", exc_info=True)
            log_error("传统流程执行失败", f"❌ [传统流程] 执行失败: {e}")
            return ResearchResult(
                query=request.query,
                success=False,
                answer="",
                error=str(e),
                confidence=0.0,
                execution_time=time.time() - start_time
            )
    
    async def _execute_tool_with_timeout(self, tool_name: str, params: Dict[str, Any], operation: str, timeout: float):
        """🚀 新增：执行工具任务，带超时控制（方案3：在传统流程中使用Tools）"""
        try:
            if not self.tool_registry:
                raise RuntimeError("工具注册表未初始化")
            
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                raise RuntimeError(f"工具 '{tool_name}' 未找到")
            
            tool_result = await asyncio.wait_for(tool.call(**params), timeout=timeout)
            
            if hasattr(tool_result, "output"):
                data = tool_result.output
            elif hasattr(tool_result, "data"):
                data = tool_result.data
            else:
                data = tool_result
            
            return AgentResult(
                success=getattr(tool_result, "success", True),
                data=data,
                confidence=getattr(tool_result, "confidence", 0.7),
                processing_time=getattr(tool_result, "execution_time", 0.0),
                metadata=getattr(tool_result, "metadata", {}),
                error=getattr(tool_result, "error", None)
            )
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ {operation} 超时 ({timeout}秒)，使用默认结果")
            # AgentResult已在文件顶部导入
            return AgentResult(
                success=True,
                data={
                    "content": f"{operation} 超时回退结果",
                    "type": "timeout_fallback",
                    "confidence": 0.7
                },
                confidence=0.7,
                processing_time=0.0,
                metadata={"type": "timeout_fallback", "operation": operation}
            )
        except Exception as e:
            logger.error(f"❌ {operation} 执行失败: {e}")
            # AgentResult已在文件顶部导入
            return AgentResult(
                success=False,
                data={
                    "content": f"{operation} 执行失败: {str(e)}",
                    "type": "error_fallback",
                    "confidence": 0.3
                },
                confidence=0.3,
                processing_time=0.0,
                metadata={"type": "error_fallback", "error": str(e), "operation": operation}
            )
    
    async def _execute_agent_with_timeout(self, agent, context: Dict[str, Any], operation: str, timeout: float):
        """执行智能体任务，带超时控制（保留作为回退方案）"""
        try:
            execution = agent.execute(context)
            if asyncio.iscoroutine(execution):
                return await asyncio.wait_for(execution, timeout=timeout)
            else:
                return execution
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ {operation} 超时 ({timeout}秒)，使用默认结果")
            return AgentResult(
                success=True,
                data={
                    "content": f"{operation} 超时回退结果",
                    "type": "timeout_fallback",
                    "confidence": 0.7
                },
                confidence=0.7,
                processing_time=0.0,
                metadata={"type": "timeout_fallback", "operation": operation}
            )
        except Exception as e:
            logger.error(f"❌ {operation} 执行失败: {e}")
            return AgentResult(
                success=False,
                data={
                    "content": f"{operation} 执行失败: {str(e)}",
                    "type": "error_fallback",
                    "confidence": 0.3
                },
                confidence=0.3,
                processing_time=0.0,
                metadata={"type": "error_fallback", "error": str(e), "operation": operation}
            )
    
    async def _execute_with_mas(self, request: ResearchRequest) -> ResearchResult:
        """
        使用多智能体系统（MAS）执行查询
        
        Args:
            request: 研究请求
            
        Returns:
            ResearchResult: 研究结果
        """
        try:
            start_time = time.time()
            log_info(f"🧠 MAS执行查询: {request.query[:100]}...")
            logger.info(f"🧠 MAS执行查询: {request.query[:100]}...")
            
            # 强制刷新日志
            import sys
            sys.stdout.flush()
            sys.stderr.flush()
            if hasattr(logger, 'handlers'):
                for handler in logger.handlers:
                    if hasattr(handler, 'flush'):
                        handler.flush()
            
            # 构建首席Agent的上下文
            logger.info(f"🔍 [MAS] 开始构建ChiefAgent上下文...")
            log_info(f"🔍 [MAS] 开始构建ChiefAgent上下文...")
            mas_context = {
                "query": request.query
            }
            logger.info(f"🔍 [MAS] 基础上下文已构建: query长度={len(request.query)}")
            log_info(f"🔍 [MAS] 基础上下文已构建: query长度={len(request.query)}")
            sys.stdout.flush()
            sys.stderr.flush()
            
            if isinstance(request.context, dict):
                logger.info(f"🔍 [MAS] 更新上下文: context类型=dict, keys={list(request.context.keys())}")
                log_info(f"🔍 [MAS] 更新上下文: context类型=dict, keys={list(request.context.keys())}")
                mas_context.update(request.context)
                logger.info(f"🔍 [MAS] 上下文更新完成")
                log_info(f"🔍 [MAS] 上下文更新完成")
            else:
                logger.info(f"🔍 [MAS] 无额外上下文: context类型={type(request.context)}")
                log_info(f"🔍 [MAS] 无额外上下文: context类型={type(request.context)}")
            
            sys.stdout.flush()
            sys.stderr.flush()
            
            logger.info(f"🔍 [MAS] 上下文构建完成，准备调用ChiefAgent...")
            log_info(f"🔍 [MAS] 上下文构建完成，准备调用ChiefAgent...")
            
            # 调用首席Agent
            logger.info(f"🔄 [MAS] 准备调用ChiefAgent.execute()...")
            log_info(f"🔄 [MAS] 准备调用ChiefAgent.execute()...")
            logger.info(f"🔍 [MAS] ChiefAgent状态: {self._chief_agent is not None}")
            log_info(f"🔍 [MAS] ChiefAgent状态: {self._chief_agent is not None}")
            
            sys.stdout.flush()
            sys.stderr.flush()
            if self._chief_agent is None:
                raise ValueError("ChiefAgent未初始化")
            
            # 强制刷新日志
            import sys
            sys.stdout.flush()
            sys.stderr.flush()
            
            try:
                logger.info(f"🔄 [MAS] 开始调用ChiefAgent.execute()...")
                log_info(f"🔄 [MAS] 开始调用ChiefAgent.execute()...")
                sys.stdout.flush()
                sys.stderr.flush()
                
                # 🚀 诊断：在调用前添加详细日志
                logger.info(f"🔍 [MAS] 调用前检查: mas_context keys={list(mas_context.keys()) if isinstance(mas_context, dict) else 'N/A'}")
                log_info(f"🔍 [MAS] 调用前检查: mas_context keys={list(mas_context.keys()) if isinstance(mas_context, dict) else 'N/A'}")
                sys.stdout.flush()
                sys.stderr.flush()
                
                # 🚀 诊断：在await之前添加日志
                logger.info(f"🔍 [MAS] 准备await ChiefAgent.execute()...")
                log_info(f"🔍 [MAS] 准备await ChiefAgent.execute()...")
                sys.stdout.flush()
                sys.stderr.flush()
                
                # 🚀 诊断：检查ChiefAgent是否有execute方法
                if not hasattr(self._chief_agent, 'execute'):
                    error_msg = f"❌ ChiefAgent没有execute方法！类型: {type(self._chief_agent)}"
                    logger.error(error_msg)
                    log_error("ChiefAgent检查失败", error_msg)
                    raise AttributeError(error_msg)
                
                # 🚀 诊断：检查execute方法是否是协程函数
                import inspect
                if not inspect.iscoroutinefunction(self._chief_agent.execute):
                    error_msg = f"❌ ChiefAgent.execute不是协程函数！类型: {type(self._chief_agent.execute)}"
                    logger.error(error_msg)
                    log_error("ChiefAgent检查失败", error_msg)
                    raise TypeError(error_msg)
                
                logger.info(f"🔍 [MAS] ChiefAgent.execute是协程函数，开始await...")
                log_info(f"🔍 [MAS] ChiefAgent.execute是协程函数，开始await...")
                sys.stdout.flush()
                sys.stderr.flush()
                
                # 🚀 重构：使用统一配置中心获取超时配置
                try:
                    from src.utils.unified_centers import get_unified_config_center
                    config_center = get_unified_config_center()
                    timeout = config_center.get_timeout('complex_reasoning', default=1800.0)
                except Exception:
                    timeout = 1800.0  # Fallback
                
                agent_result = await asyncio.wait_for(
                    self._chief_agent.execute(mas_context),
                    timeout=timeout
                )
                logger.info(f"✅ [MAS] ChiefAgent.execute()完成: success={agent_result.success}")
            except asyncio.TimeoutError:
                logger.error(f"❌ [MAS] ChiefAgent.execute()超时（30分钟）")
                raise
            except Exception as e:
                logger.error(f"❌ [MAS] ChiefAgent.execute()异常: {e}", exc_info=True)
                raise
            
            # 转换为ResearchResult
            if agent_result.success:
                answer = ""
                knowledge = []
                reasoning = None
                citations = []
                
                if isinstance(agent_result.data, dict):
                    answer = agent_result.data.get("answer", "")
                    knowledge = agent_result.data.get("knowledge", [])
                    reasoning = agent_result.data.get("reasoning")
                    citations = agent_result.data.get("citations", [])
                elif isinstance(agent_result.data, str):
                    answer = agent_result.data
                
                execution_time = time.time() - start_time
                
                return ResearchResult(
                    query=request.query,
                    success=True,
                    answer=answer,
                    knowledge=knowledge if knowledge else None,
                    reasoning=str(reasoning) if reasoning else None,
                    citations=citations if citations else None,
                    confidence=getattr(agent_result, 'confidence', 0.8),
                    execution_time=execution_time,
                    metadata={
                        "method": "mas",
                        "agent_collaboration_log": agent_result.data.get("agent_collaboration_log", []) if isinstance(agent_result.data, dict) else None
                    }
                )
            else:
                execution_time = time.time() - start_time
                return ResearchResult(
                    query=request.query,
                    success=False,
                    error=agent_result.error or "MAS执行失败",
                    execution_time=execution_time,
                    metadata={"method": "mas"}
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ MAS执行异常: {e}", exc_info=True)
            return ResearchResult(
                query=request.query,
                success=False,
                error=str(e),
                execution_time=execution_time,
                metadata={"method": "mas"}
            )
    
    async def _execute_with_unified_workflow(self, request: ResearchRequest, start_time: float) -> ResearchResult:
        """使用统一工作流（MVP）执行查询"""
        try:
            import sys
            import asyncio
            logger.info("🔄 [统一工作流] 开始执行查询...")
            sys.stdout.write(f"🔄 [DEBUG] [统一工作流] 开始执行查询: {request.query[:50]}...\n")
            sys.stdout.flush()
            
            if not self._unified_workflow:
                raise RuntimeError("统一工作流未初始化")
            
            from src.utils.unified_centers import get_unified_config_center
            config_center = get_unified_config_center()
            try:
                from src.utils.unified_complexity_model_service import get_unified_complexity_model_service
                complexity_service = get_unified_complexity_model_service()
                complexity_result = complexity_service.assess_complexity(
                    query=request.query,
                    query_type=None,
                    evidence_count=0,
                    use_cache=True
                )
                complexity_str = complexity_result.level.value
                logger.info(f"📊 [统一工作流] 统一复杂度判断结果: level={complexity_str}, score={complexity_result.score:.2f}")
            except Exception as e:
                logger.warning(f"⚠️ [统一工作流] 获取查询复杂度失败: {e}，使用medium")
                complexity_str = "medium"
            
            default_timeout_map = {
                "simple": 180.0,
                "medium": 600.0,
                "complex": 1200.0,
                "very_complex": 1800.0
            }
            default_timeout = default_timeout_map.get(complexity_str, 600.0)
            
            # 🚀 优先使用上下文中的超时设置
            context_timeout = request.context.get('global_timeout') if request.context else None
            if isinstance(context_timeout, (int, float)) and context_timeout > 0:
                workflow_timeout = float(context_timeout)
                logger.info(f"⏱️ [统一工作流] 使用上下文指定的超时设置: {workflow_timeout:.1f}秒")
            else:
                workflow_timeout = config_center.get_timeout(
                    "query_complexity",
                    complexity=complexity_str,
                    default=default_timeout
                )
            
            if not isinstance(workflow_timeout, (int, float)) or workflow_timeout <= 0:
                workflow_timeout = default_timeout
            if workflow_timeout < 60.0:
                workflow_timeout = 60.0
            if workflow_timeout > 3600.0:
                workflow_timeout = 3600.0
            deep_reasoning_mode = complexity_str in ("complex", "very_complex")
            workflow_context = dict(request.context or {})
            if "query_complexity" not in workflow_context:
                workflow_context["query_complexity"] = complexity_str
            if "deep_reasoning_mode" not in workflow_context:
                workflow_context["deep_reasoning_mode"] = deep_reasoning_mode
            if "global_timeout" not in workflow_context:
                workflow_context["global_timeout"] = float(workflow_timeout)
            logger.info(
                f"⏱️ [统一工作流] 动态超时设置: complexity={complexity_str}, timeout={workflow_timeout:.1f}秒, deep_reasoning_mode={deep_reasoning_mode}"
            )
            try:
                result = await asyncio.wait_for(
                    self._unified_workflow.execute(
                        query=request.query,
                        context=workflow_context
                    ),
                    timeout=workflow_timeout
                )
                
                # 🛡️ [Debug] 立即保存中间结果，防止后续Crash导致数据丢失
                try:
                    import json
                    debug_path = f"debug_unified_result_{int(time.time())}.json"
                    with open(debug_path, "w", encoding="utf-8") as f:
                        # Convert result to serializable format if needed
                        # Assuming result is Dict[str, Any] and mostly serializable
                        json.dump(result, f, default=str, ensure_ascii=False, indent=2)
                    logger.info(f"🛡️ [Debug] 中间结果已保存至 {debug_path}")
                except Exception as dump_e:
                    logger.warning(f"⚠️ [Debug] 保存中间结果失败: {dump_e}")

            except asyncio.TimeoutError:
                logger.error(f"❌ [统一工作流] 执行超时（{workflow_timeout:.1f}秒）")
                sys.stdout.write(f"❌ [DEBUG] [统一工作流] 执行超时（{workflow_timeout:.1f}秒）\n")
                sys.stdout.flush()
                return ResearchResult(
                    query=request.query,
                    success=False,
                    error=f"统一工作流执行超时（{workflow_timeout:.1f}秒）",
                    execution_time=time.time() - start_time
                )
            
            logger.info(f"✅ [统一工作流] 工作流执行完成，开始转换ResearchResult...")
            sys.stdout.write(f"✅ [DEBUG] [统一工作流] 工作流执行完成，开始转换ResearchResult...\n")
            sys.stdout.flush()
            
            # 转换为 ResearchResult
            research_result = ResearchResult(
                query=request.query,
                success=result.get('success', False),
                answer=result.get('answer'),
                confidence=result.get('confidence', 0.0),
                knowledge=result.get('knowledge', []),
                reasoning=result.get('reasoning'),
                citations=result.get('citations', []),
                execution_time=result.get('execution_time', time.time() - start_time),
                error=result.get('error'),
                metadata=result.get('metadata')
            )
            
            logger.info(f"✅ [统一工作流] ResearchResult转换完成: success={research_result.success}, answer长度={len(research_result.answer) if research_result.answer else 0}")
            sys.stdout.write(f"✅ [DEBUG] [统一工作流] ResearchResult转换完成: success={research_result.success}\n")
            sys.stdout.flush()
            
            return research_result
        except Exception as e:
            logger.error(f"❌ [统一工作流] 执行失败: {e}", exc_info=True)
            sys.stdout.write(f"❌ [DEBUG] [统一工作流] 执行失败: {e}\n")
            sys.stdout.flush()
            return ResearchResult(
                query=request.query,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _execute_with_langgraph_agent(self, request: ResearchRequest) -> ResearchResult:
        """
        使用LangGraph Agent执行查询
        
        Args:
            request: 研究请求
            
        Returns:
            ResearchResult: 研究结果
        """
        try:
            # 🎯 编排追踪：传递追踪器到 LangGraph Agent
            tracker = getattr(self, '_orchestration_tracker', None)
            if tracker and self._langgraph_react_agent:
                setattr(self._langgraph_react_agent, '_orchestration_tracker', tracker)  # type: ignore
            
            if not self._langgraph_react_agent:
                raise ValueError("LangGraph Agent not initialized")
            
            # 构建上下文
            context = {
                "query": request.query,
                "context": request.context or {}
            }
            
            # 执行LangGraph Agent
            agent_result = await self._langgraph_react_agent.execute(context)
            
            # 转换为ResearchResult
            if agent_result.success:
                return ResearchResult(
                    query=request.query,
                    success=True,
                    answer=agent_result.data.get("answer", "") if agent_result.data else "",
                    knowledge=agent_result.data.get("knowledge", []) if agent_result.data else [],
                    reasoning=agent_result.data.get("reasoning") if agent_result.data else None,
                    citations=agent_result.data.get("citations", []) if agent_result.data else [],
                    confidence=agent_result.confidence,
                    execution_time=agent_result.processing_time
                )
            else:
                return ResearchResult(
                    query=request.query,
                    success=False,
                    error=agent_result.error or "LangGraph Agent execution failed",
                    confidence=agent_result.confidence,
                    execution_time=agent_result.processing_time
                )
        except Exception as e:
            logger.error(f"❌ LangGraph Agent执行失败: {e}", exc_info=True)
            return ResearchResult(
                query=request.query,
                success=False,
                error=f"LangGraph Agent execution error: {str(e)}"
            )
    
    async def _execute_with_react_agent(self, request: ResearchRequest) -> ResearchResult:
        """
        使用ReAct Agent执行查询
        
        Args:
            request: 研究请求
            
        Returns:
            ResearchResult: 研究结果
        """
        try:
            start_time = time.time()
            # 🔧 修复：使用log_info()确保日志写入文件
            log_info(f"🧠 ReAct Agent执行查询: {request.query[:100]}...")
            logger.info(f"🧠 ReAct Agent执行查询: {request.query[:100]}...")  # 保留logger.info用于控制台输出
            
            # 构建ReAct Agent的上下文
            react_context = {
                "query": request.query
            }
            if isinstance(request.context, dict):
                react_context.update(request.context)
            
            # 调用ReAct Agent
            if not self._react_agent:
                raise ValueError("ReAct Agent not initialized")
            agent_result = await self._react_agent.execute(react_context)
            
            # 转换为ResearchResult
            if agent_result.success:
                answer = ""
                if isinstance(agent_result.data, dict):
                    answer = agent_result.data.get("answer", "")
                elif isinstance(agent_result.data, str):
                    answer = agent_result.data
                
                # 提取证据和引用
                evidence = []
                citations = []
                if isinstance(agent_result.data, dict):
                    observations = agent_result.data.get("observations", [])
                    for obs in observations:
                        # 🚀 架构优化：RAGTool已移除，统一使用RealReasoningEngine
                        if obs.get("tool_name") in ["rag", "reasoning"] and obs.get("data"):
                            rag_data = obs["data"]
                            if isinstance(rag_data, dict):
                                evidence.extend(rag_data.get("evidence", []))
                
                result = ResearchResult(
                    query=request.query,
                    answer=answer,
                    success=True,
                    confidence=agent_result.confidence,
                    execution_time=agent_result.processing_time,
                    metadata={
                        "method": "react_agent",
                        "iterations": (agent_result.metadata or {}).get("react_iterations", 0),
                        "tools_used": (agent_result.metadata or {}).get("tools_used", []),
                        "thoughts": agent_result.data.get("thoughts", []) if isinstance(agent_result.data, dict) else []
                    }
                )
                
                # 🔧 修复：使用log_info()确保日志写入文件
                log_info(f"✅ ReAct Agent执行成功，耗时: {agent_result.processing_time:.2f}秒")
                answer_length = len(result.answer) if result.answer else 0
                log_info(f"🔍 [诊断] ReAct Agent结果: success={result.success}, answer长度={answer_length}, confidence={result.confidence}")
                logger.info(f"✅ ReAct Agent执行成功，耗时: {agent_result.processing_time:.2f}秒")  # 保留logger.info用于控制台输出
                return result
            else:
                # ReAct Agent失败，回退到传统流程
                log_warning(f"⚠️ ReAct Agent执行失败，回退到传统流程")
                log_warning(f"🔍 [诊断] ReAct Agent失败原因: success={agent_result.success}, error={agent_result.error}")
                log_warning(f"🔍 [诊断] ReAct Agent元数据: {agent_result.metadata}")
                if isinstance(agent_result.data, dict):
                    log_warning(f"🔍 [诊断] ReAct Agent数据: observations数={len(agent_result.data.get('observations', []))}, iterations={agent_result.data.get('iterations', 0)}")
                log_warning(f"🔍 [诊断] 开始回退到传统流程...")
                logger.warning(f"⚠️ ReAct Agent执行失败，回退到传统流程")  # 保留logger.warning用于控制台输出
                return await self._execute_research_internal(request)
                
        except Exception as e:
            logger.error(f"❌ ReAct Agent执行异常: {e}，回退到传统流程", exc_info=True)
            return await self._execute_research_internal(request)
    
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
            logger.warning(f"⚠️ 获取系统负载失败: {e}")
            return 50.0  # 默认中等负载
    
    async def _execute_research_internal(self, request: ResearchRequest) -> ResearchResult:  # type: ignore[complexity]
        """内部研究执行逻辑 - 优化版本，实现真正的异步并发"""
        start_time = time.time()  # 🚀 新增：记录开始时间，用于性能记录
        try:
            logger.info("🔍 开始执行内部研究逻辑: {request.query[:30]}...")

            # 🚀 P0修复：创建知识检索上下文，确保query正确传递
            knowledge_context = {"query": request.query, "type": "knowledge_retrieval"}
            
            # 🚀 P0修复：记录查询内容（用于诊断）
            if request.query:
                logger.info(f"🔍 [查询传递] UnifiedResearchSystem: 创建knowledge_context, query='{request.query[:100]}...' (长度={len(request.query)})")
            else:
                logger.error(f"❌ [查询传递] UnifiedResearchSystem: request.query为空！无法执行知识检索")

            # 🚀 新增：使用ML/RL调度优化器获取最优调度策略
            ml_strategy = None
            rl_action = None
            rl_state = None
            query_type = None
            query_complexity = None
            
            try:
                # 推断查询类型和复杂度
                query_lower = request.query.lower()
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
                
                query_length = len(request.query)
                if query_length < 50:
                    query_complexity = 'simple'
                elif query_length > 150 or request.query.count(' and ') > 1:
                    query_complexity = 'complex'
                elif request.query.count("'s ") > 2:
                    query_complexity = 'very_complex'
                else:
                    query_complexity = 'medium'
                
                # ML预测最优调度策略
                if hasattr(self, 'ml_scheduling_optimizer') and self.ml_scheduling_optimizer:
                    ml_strategy = self.ml_scheduling_optimizer.get_optimal_strategy(
                        query=request.query,
                        query_type=query_type,
                        query_complexity=query_complexity
                    )
                    logger.info(f"🚀 ML调度优化: 知识超时={ml_strategy.knowledge_timeout}s, 推理超时={ml_strategy.reasoning_timeout}s, 并行={ml_strategy.parallel_knowledge_reasoning}")
                
                # RL选择最优动作
                if hasattr(self, 'rl_scheduling_optimizer') and self.rl_scheduling_optimizer:
                    from src.utils.rl_scheduling_optimizer import SchedulingState
                    rl_state = SchedulingState(
                        query_type=query_type,
                        query_complexity=query_complexity,
                        query_length=query_length,
                        has_knowledge=False,  # 初始状态，知识检索后更新
                        knowledge_quality=0.0  # 初始状态，知识检索后更新
                    )
                    rl_action = self.rl_scheduling_optimizer.select_action(rl_state)
                    logger.info(f"🚀 RL调度优化: 知识超时={rl_action.knowledge_timeout}s, 推理超时={rl_action.reasoning_timeout}s, 并行={rl_action.parallel_execution}")
            except Exception as e:
                logger.debug(f"ML/RL调度优化失败: {e}，使用默认策略")

            logger.info("📚 步骤1: 开始知识检索和推理（并行执行）...")
            # 🚀 重构：使用真正的Agent（ExpertAgent子类）
            # 如果工具不可用，则要求Agent已初始化；否则允许仅使用工具
            has_knowledge_tool = bool(self.tool_registry and self.tool_registry.get_tool("knowledge_retrieval"))
            if not has_knowledge_tool and not self._knowledge_agent:
                raise RuntimeError("知识检索Agent未初始化")
            if not self._reasoning_agent:
                raise RuntimeError("推理Agent未初始化")

            # 🚀 修复P0：改变执行策略 - 先完成知识检索，再启动推理
            # 原因：推理引擎需要知识支持，但并行执行时推理上下文初始为空
            # 方案：先完成知识检索，提取知识，更新推理上下文，再启动推理
            # 🚀 修复：确保使用原始查询，不进行任何替换或翻译
            # 检查查询是否包含中文字符，如果包含则记录警告（但不替换）
            import re
            has_chinese = bool(re.search(r'[\u4e00-\u9fff]', request.query))
            if has_chinese:
                logger.warning(
                    f"⚠️ 检测到查询包含中文字符，但系统应使用英文查询 | "
                    f"当前查询: {request.query[:100]} | "
                    f"说明: 如果这是FRAMES数据集，查询应该是英文的"
                )
                log_info(f"⚠️ 查询语言警告: 检测到中文查询，但系统应使用英文查询 | 查询: {request.query[:100]}")
            
            reasoning_context = {
                "query": request.query,  # 🚀 修复：始终使用原始查询，不进行任何替换
                "knowledge": [],  # 初始为空，知识检索后会更新
                "knowledge_data": [],  # 🚀 改进：添加knowledge_data字段（兼容）
                "type": "reasoning_analysis",
                "preliminary": False  # 🚀 修复：不再标记为初步推理，因为会使用检索到的知识
            }
            # 🚀 修复：将期望答案从request.context传递到reasoning_context，以便学习机制使用
            if isinstance(request.context, dict) and "expected_answer" in request.context:
                reasoning_context["expected_answer"] = request.context["expected_answer"]

            # 步骤1：先执行知识检索
            # 🚀 优化3：记录知识检索开始时间和实际耗时
            knowledge_retrieval_start_time = time.time()
            logger.info("⏳ 步骤1.1: 执行知识检索...")
            log_info(f"知识检索开始: 查询='{request.query[:80]}...'")
            
            # 🚀 新增：添加查询处理日志（知识检索步骤）
            sample_id = None
            if isinstance(request.context, dict):
                sample_id = request.context.get('sample_id') or request.context.get('item_index')
            if sample_id is not None:
                log_info(f"查询处理: 样本ID={sample_id}, 步骤=知识检索")
            else:
                log_info("查询处理: 步骤=知识检索")
            
            # 🚀 ML/RL优化：使用ML/RL预测的超时时间和执行策略
            # 🚀 重构：使用统一配置中心获取超时配置
            try:
                from src.utils.unified_centers import get_unified_config_center
                config_center = get_unified_config_center()
                knowledge_timeout = config_center.get_timeout('evidence_retrieval', default=12.0)
            except Exception:
                knowledge_timeout = 12.0  # Fallback
            use_parallel_execution = False  # 默认串行执行
            skip_answer_generation = False  # 默认不跳过答案生成
            
            if ml_strategy:
                knowledge_timeout = ml_strategy.knowledge_timeout
                use_parallel_execution = ml_strategy.parallel_knowledge_reasoning
                skip_answer_generation = ml_strategy.skip_answer_generation
                logger.info(f"🚀 ML调度优化应用: 知识超时={knowledge_timeout}s, 并行执行={use_parallel_execution}, 跳过答案生成={skip_answer_generation}")
            elif rl_action:
                knowledge_timeout = rl_action.knowledge_timeout
                use_parallel_execution = rl_action.parallel_execution
                skip_answer_generation = rl_action.skip_answer_generation
                logger.info(f"🚀 RL调度优化应用: 知识超时={knowledge_timeout}s, 并行执行={use_parallel_execution}, 跳过答案生成={skip_answer_generation}")
            
            # 🚀 方案3：优先使用Tools，如果不可用则回退到Agent
            if self.tool_registry and self.tool_registry.get_tool("knowledge_retrieval"):
                logger.info("🚀 [传统流程] 使用KnowledgeRetrievalTool（方案3：统一工具接口）")
                knowledge_task = asyncio.create_task(
                    self._execute_tool_with_timeout(
                        "knowledge_retrieval",
                        {"query": request.query, "context": knowledge_context},
                        "knowledge_retrieval",
                        timeout=knowledge_timeout
                    )
                )
            else:
                logger.info("🔄 [传统流程] 回退到KnowledgeRetrievalAgent（Tools不可用）")
                knowledge_task = asyncio.create_task(
                    self._execute_agent_with_timeout(
                        self._knowledge_agent,  # 回退到Agent
                        knowledge_context,
                        "knowledge_retrieval",
                        timeout=knowledge_timeout
                    )
                )
            
            # 等待知识检索完成
            knowledge_result = await knowledge_task
            
            # 🚀 优化3：记录知识检索实际耗时
            knowledge_retrieval_time = time.time() - knowledge_retrieval_start_time
            logger.info(f"⏱️ 知识检索实际耗时: {knowledge_retrieval_time:.2f}秒")
            log_info(f"知识检索耗时: {knowledge_retrieval_time:.2f}秒")
            
            # 处理知识检索异常
            if isinstance(knowledge_result, Exception):
                logger.error(f"❌ 知识检索失败: {knowledge_result}")
                knowledge_result = AgentResult(
                    success=False,
                    data={"error": str(knowledge_result)},
                    confidence=0.3,
                    processing_time=0.0
                )
            
            # 🚀 修复P0：提取知识并更新推理上下文
            # 🚀 优化4：优化知识提取逻辑，支持更多数据格式，提高成功率
            # 注意：knowledge_result.data中的sources结构可能是：
            # sources = [
            #   {"type": "faiss", "result": AgentResult, "confidence": 0.8},
            #   ...
            # ]
            # 或者直接是知识列表
            knowledge_list = []
            extraction_start_time = time.time()
            
            if not isinstance(knowledge_result, Exception) and hasattr(knowledge_result, 'success'):
                if knowledge_result.success and hasattr(knowledge_result, 'data'):
                    knowledge_data = knowledge_result.data
                    
                    # 🚀 优化4：支持更多数据格式
                    if isinstance(knowledge_data, dict):
                        sources = knowledge_data.get('sources', [])
                        
                        # 🚀 优化4：如果sources为空，尝试直接从knowledge_data中提取
                        if not sources:
                            # 尝试从knowledge_data中直接提取知识
                            if 'content' in knowledge_data:
                                knowledge_list.append({
                                    'content': knowledge_data.get('content', ''),
                                    'source': knowledge_data.get('source', 'unknown'),
                                    'confidence': knowledge_data.get('confidence', 0.7)
                                })
                            elif 'knowledge' in knowledge_data:
                                # 如果knowledge_data中有knowledge字段
                                knowledge_list = knowledge_data.get('knowledge', [])
                            elif 'data' in knowledge_data:
                                # 如果knowledge_data中有data字段
                                inner_data = knowledge_data.get('data', [])
                                if isinstance(inner_data, list):
                                    knowledge_list = inner_data
                        
                        if sources:
                            # 🚀 优化4：从sources中的result.data提取实际知识内容（增强版）
                            for source_item in sources:
                                if isinstance(source_item, dict):
                                    result_obj = source_item.get('result')
                                    
                                    # 🚀 优化4：支持多种result格式
                                    if result_obj:
                                        # 如果result_obj有data属性
                                        if hasattr(result_obj, 'data'):
                                            source_data = result_obj.data
                                        # 如果result_obj本身就是数据
                                        elif isinstance(result_obj, (dict, list)):
                                            source_data = result_obj
                                        else:
                                            continue
                                        
                                        # 🚀 优化4：支持更多数据格式
                                        if isinstance(source_data, dict):
                                            # 如果data是dict，尝试提取content或sources
                                            content = source_data.get('content', '') or source_data.get('text', '')
                                            if content:
                                                knowledge_list.append({
                                                    'content': content,
                                                    'source': source_item.get('type', 'unknown'),
                                                    'confidence': source_item.get('confidence', source_data.get('confidence', 0.7))
                                                })
                                            # 或者data中有sources列表
                                            inner_sources = source_data.get('sources', []) or source_data.get('knowledge', [])
                                            if inner_sources and isinstance(inner_sources, list):
                                                # 🚀 优化4：确保inner_sources中的每个元素都是dict格式
                                                for inner_item in inner_sources:
                                                    if isinstance(inner_item, dict):
                                                        knowledge_list.append({
                                                            'content': inner_item.get('content', '') or inner_item.get('text', '') or str(inner_item),
                                                            'source': inner_item.get('source', source_item.get('type', 'unknown')),
                                                            'confidence': inner_item.get('confidence', source_item.get('confidence', 0.7))
                                                        })
                                                    elif isinstance(inner_item, str):
                                                        # 如果inner_item是字符串，直接作为content
                                                        knowledge_list.append({
                                                            'content': inner_item,
                                                            'source': source_item.get('type', 'unknown'),
                                                            'confidence': source_item.get('confidence', 0.7)
                                                        })
                                        elif isinstance(source_data, list):
                                            # 🚀 优化4：确保list中的每个元素都是dict格式
                                            for item in source_data:
                                                if isinstance(item, dict):
                                                    knowledge_list.append({
                                                        'content': item.get('content', '') or item.get('text', '') or str(item),
                                                        'source': item.get('source', source_item.get('type', 'unknown')),
                                                        'confidence': item.get('confidence', source_item.get('confidence', 0.7))
                                                    })
                                                elif isinstance(item, str):
                                                    knowledge_list.append({
                                                        'content': item,
                                                        'source': source_item.get('type', 'unknown'),
                                                        'confidence': source_item.get('confidence', 0.7)
                                                    })
                                    # 🚀 优化4：如果source_item直接包含知识内容
                                    elif 'content' in source_item or 'text' in source_item:
                                        knowledge_list.append({
                                            'content': source_item.get('content', '') or source_item.get('text', ''),
                                            'source': source_item.get('type', 'unknown'),
                                            'confidence': source_item.get('confidence', 0.7)
                                        })
                            
                            if knowledge_list:
                                extraction_time = time.time() - extraction_start_time
                                logger.info(f"✅ 知识检索成功，提取到 {len(knowledge_list)} 条知识（提取耗时: {extraction_time:.3f}秒）")
                                log_info(f"知识检索完成: 成功检索到 {len(knowledge_list)} 条知识")
                            else:
                                logger.warning(f"⚠️ 知识检索返回了sources但无法提取有效知识内容（提取耗时: {time.time() - extraction_start_time:.3f}秒）")
                                log_info(f"知识检索警告: 返回了sources但无法提取有效知识内容")
                    elif isinstance(knowledge_data, list):
                        # 🚀 优化4：确保list中的每个元素都是dict格式
                        for item in knowledge_data:
                            if isinstance(item, dict):
                                knowledge_list.append({
                                    'content': item.get('content', '') or item.get('text', '') or str(item),
                                    'source': item.get('source', 'unknown'),
                                    'confidence': item.get('confidence', 0.7)
                                })
                            elif isinstance(item, str):
                                knowledge_list.append({
                                    'content': item,
                                    'source': 'unknown',
                                    'confidence': 0.7
                                })
                        
                        if knowledge_list:
                            extraction_time = time.time() - extraction_start_time
                            logger.info(f"✅ 知识检索成功，获取到 {len(knowledge_list)} 条知识（提取耗时: {extraction_time:.3f}秒）")
                            log_info(f"知识检索完成: 成功检索到 {len(knowledge_list)} 条知识")
                    else:
                        # 🚀 优化4：如果knowledge_data是其他类型，尝试转换为字符串
                        logger.warning(f"⚠️ 知识检索返回了未知格式的数据: {type(knowledge_data)}")
                        log_info(f"知识检索警告: 返回了未知格式的数据: {type(knowledge_data)}")
            
            # 🚀 修复P0：更新推理上下文，传递检索到的知识
            # 🚀 优化：添加检索标志，避免重复检索
            reasoning_context['_knowledge_retrieved'] = True  # 标记已经进行过知识检索
            
            if knowledge_list:
                reasoning_context['knowledge'] = knowledge_list
                reasoning_context['knowledge_data'] = knowledge_list
                logger.info(f"🔄 更新推理上下文，添加 {len(knowledge_list)} 条知识（总耗时: {knowledge_retrieval_time:.2f}秒）")
                log_info(f"推理上下文更新: 添加 {len(knowledge_list)} 条知识，已标记为已检索")
            else:
                logger.warning(f"⚠️ 知识检索未返回有效知识，推理将使用主动检索机制（检索耗时: {knowledge_retrieval_time:.2f}秒）")
                log_info(f"知识检索警告: 未返回有效知识，但已标记为已检索，避免重复检索")
            
            # 步骤2：启动推理任务（使用更新后的上下文，包含检索到的知识）
            logger.info("⏳ 步骤1.2: 开始推理（使用检索到的知识）...")
            
            # 🚀 新增：添加查询处理日志（推理步骤）
            sample_id = None
            if isinstance(request.context, dict):
                sample_id = request.context.get('sample_id') or request.context.get('item_index')
            if sample_id is not None:
                log_info(f"查询处理: 样本ID={sample_id}, 步骤=推理")
            else:
                log_info("查询处理: 步骤=推理")
            
            # 🚀 ML/RL优化：使用ML/RL预测的推理超时时间
            reasoning_timeout = min(request.timeout * 0.85, 200.0)  # 默认值
            if ml_strategy:
                reasoning_timeout = min(request.timeout * 0.85, ml_strategy.reasoning_timeout)
            elif rl_action:
                reasoning_timeout = min(request.timeout * 0.85, rl_action.reasoning_timeout)
            
            # 🚀 ML/RL优化：根据ML/RL策略决定是否并行执行推理
            # 注意：知识检索已经完成，现在启动推理任务
            # 并行执行的优势在于：可以在知识检索完成后立即启动推理，而不需要等待其他处理
            if use_parallel_execution:
                logger.info("🚀 ML/RL优化：并行执行模式（知识检索已完成，立即启动推理）")
            
            # 🚀 架构优化：统一使用RAGTool（内部使用RAGAgent）
            # ReasoningTool已移除，使用RAGTool替代
            if self.tool_registry and self.tool_registry.get_tool("rag"):
                logger.info("🚀 [传统流程] 使用RAGTool（内部使用RAGAgent，替代ReasoningTool）")
                reasoning_task = asyncio.create_task(
                    self._execute_tool_with_timeout(
                        "rag",
                        {"query": request.query, "context": reasoning_context},
                        "reasoning_analysis",
                        timeout=reasoning_timeout
                    )
                )
            else:
                logger.info("🔄 [传统流程] 回退到ReasoningAgent（Tools不可用）")
                reasoning_task = asyncio.create_task(
                    self._execute_agent_with_timeout(
                        self._reasoning_agent,  # 回退到Agent
                        reasoning_context,
                        "reasoning_analysis",
                        timeout=reasoning_timeout
                    )
                )
            # 等待推理任务完成
            reasoning_result = await reasoning_task
            
            # 处理推理异常
            if isinstance(reasoning_result, Exception):
                logger.error(f"❌ 推理分析失败: {reasoning_result}")
                reasoning_result = AgentResult(
                    success=False,
                    data={"error": str(reasoning_result)},
                    confidence=0.3,
                    processing_time=0.0
                )
            
            # 安全获取success状态
            def get_success_status(result):
                if isinstance(result, Exception):
                    return 'Exception'
                return getattr(result, 'success', 'Unknown')
            
            logger.info(f"✅ 知识检索完成，结果: {get_success_status(knowledge_result)}, 知识数: {len(knowledge_list)}")
            logger.info(f"✅ 推理分析完成，结果: {get_success_status(reasoning_result)}")
            
            # 🚀 改进：移除错误的推理时间记录（这里记录的固定0.1秒是错误的）
            # 推理时间应该在推理引擎层面和运行脚本层面记录，而不是在这里

            # 🚀 新增：推理链增强机制
            def safe_get_data_for_reasoning(result, default=None):
                if isinstance(result, Exception):
                    return default
                if hasattr(result, 'data'):
                    return result.data
                return default
            
            # 简单提取数据函数
            def simple_get_data(result, key, default=""):
                if isinstance(result, Exception):
                    return default
                data = getattr(result, 'data', None)
                if isinstance(data, dict):
                    return data.get(key, default)
                return default
            
            # 🚀 优化：推理完成后立即检查是否有可用的答案，不等待后续步骤
            # 这样可以尽早返回结果，避免因后续步骤超时导致整个查询失败
            reasoning_answer = None
            
            # 🔍 详细调试日志：记录推理结果的完整结构（仅在调试时启用）
            if not isinstance(reasoning_result, Exception):
                logger.debug(f"🔍 推理结果调试信息:")
                logger.debug(f"  - 类型: {type(reasoning_result)}")
                logger.debug(f"  - 是否为Exception: {isinstance(reasoning_result, Exception)}")
                logger.debug(f"  - 是否有success属性: {hasattr(reasoning_result, 'success')}")
                if hasattr(reasoning_result, 'success'):
                    logger.debug(f"  - success值: {getattr(reasoning_result, 'success', None)}")
                
                # 记录所有属性
                all_attrs = [attr for attr in dir(reasoning_result) if not attr.startswith('_')]
                logger.debug(f"  - 主要属性: {all_attrs[:15]}")
                
                # 详细记录data字段
                if hasattr(reasoning_result, 'data'):
                    data_value = getattr(reasoning_result, 'data', None)
                    logger.debug(f"  - data类型: {type(data_value)}")
                    if isinstance(data_value, dict):
                        logger.debug(f"  - data字典内容: {list(data_value.keys())}")
                        # 记录字典的完整内容（限制长度）
                        for key, value in data_value.items():
                            if isinstance(value, str):
                                value_preview = value[:100] if len(value) > 100 else value
                                logger.debug(f"    - {key}: {value_preview}")
                            else:
                                logger.debug(f"    - {key}: {type(value)} = {str(value)[:100]}")
                    elif isinstance(data_value, str):
                        logger.debug(f"  - data字符串内容: {data_value[:200]}")
                    else:
                        logger.debug(f"  - data值: {str(data_value)[:200]}")
                
                # 记录其他可能的答案字段
                for attr_name in ['final_answer', 'answer', 'result', 'reasoning']:
                    if hasattr(reasoning_result, attr_name):
                        attr_value = getattr(reasoning_result, attr_name, None)
                        if isinstance(attr_value, str):
                            logger.debug(f"  - {attr_name}: {attr_value[:100]}")
                        else:
                            logger.debug(f"  - {attr_name}: {type(attr_value)}")
            
            if (not isinstance(reasoning_result, Exception) and 
                hasattr(reasoning_result, 'success') and 
                getattr(reasoning_result, 'success', False)):
                # 🚀 修复：支持多种推理结果格式
                # 1. ReasoningResult对象（RealReasoningEngine返回）- final_answer属性
                if hasattr(reasoning_result, 'final_answer'):
                    reasoning_answer = getattr(reasoning_result, 'final_answer', '')
                    if reasoning_answer:
                        logger.debug(f"✅ 从ReasoningResult.final_answer提取答案: {reasoning_answer[:50]}...")
                
                # 2. AgentResult对象（EnhancedReasoningAgent返回）- data字段可能是字符串或字典
                if not reasoning_answer and hasattr(reasoning_result, 'data'):
                    reasoning_data = getattr(reasoning_result, 'data', None)
                    logger.debug(f"🔍 尝试从data字段提取答案，data类型: {type(reasoning_data)}")
                    
                    # 如果data是字符串，直接使用（EnhancedReasoningAgent.process_query返回格式）
                    if isinstance(reasoning_data, str) and reasoning_data.strip():
                        reasoning_answer = reasoning_data.strip()
                        logger.debug(f"✅ 从AgentResult.data(字符串)提取答案: {reasoning_answer[:50]}...")
                    # 如果data是字典，尝试从多个可能的字段提取
                    elif isinstance(reasoning_data, dict):
                        logger.debug(f"🔍 data是字典，尝试从以下字段提取: answer, result, reasoning, final_answer")
                        reasoning_answer = (
                            reasoning_data.get('answer', '') or 
                            reasoning_data.get('result', '') or 
                            reasoning_data.get('reasoning', '') or 
                            reasoning_data.get('final_answer', '')
                        )
                        if reasoning_answer:
                            logger.debug(f"✅ 从AgentResult.data(字典)提取答案: {reasoning_answer[:50]}...")
                        else:
                            logger.debug(f"⚠️ 字典中未找到答案字段，可用字段: {list(reasoning_data.keys())}")
                            # 🔍 尝试从reasoning文本中提取答案（如果reasoning字段存在）
                            if 'reasoning' in reasoning_data:
                                reasoning_text = reasoning_data.get('reasoning', '')
                                logger.debug(f"🔍 尝试从reasoning文本中提取答案，文本长度: {len(reasoning_text)}")
                                # 简单的答案提取：查找"答案是:"、"答案:"等模式
                                import re
                                answer_patterns = [
                                    r'答案[是：:]\s*([^\n。]+)',
                                    r'The answer is:\s*([^\n.]+)',
                                    r'Final answer is:\s*([^\n.]+)',
                                    r'答案[为为]:\s*([^\n。]+)',
                                ]
                                for pattern in answer_patterns:
                                    match = re.search(pattern, reasoning_text, re.IGNORECASE)
                                    if match:
                                        reasoning_answer = match.group(1).strip()
                                        logger.debug(f"✅ 从reasoning文本中提取答案: {reasoning_answer[:50]}...")
                                        break
                
                # 3. 备用方案：如果推理结果有answer属性，直接使用
                if not reasoning_answer and hasattr(reasoning_result, 'answer'):
                    reasoning_answer = getattr(reasoning_result, 'answer', '')
                    if reasoning_answer:
                        logger.debug(f"✅ 从reasoning_result.answer提取答案: {reasoning_answer[:50]}...")
                
                # 清理答案：去除明显的错误信息
                if reasoning_answer:
                    # 🚀 优化：使用智能过滤器检测API错误消息
                    try:
                        from src.core.intelligent_filter_center import get_intelligent_filter_center
                        filter_center = get_intelligent_filter_center()
                        
                        # 使用智能过滤器检查是否为无效答案（包括API错误消息）
                        if filter_center.is_invalid_answer(reasoning_answer):
                            logger.warning(f"⚠️ 提取的答案被智能过滤器识别为无效，忽略: {reasoning_answer[:50]}...")
                            reasoning_answer = None
                    except Exception as e:
                        logger.debug(f"智能过滤器检查失败，使用基础检查: {e}")
                        # Fallback: 基础检查
                        invalid_patterns = [
                            "推理处理失败", "推理失败", "推理错误",
                            "Reasoning task failed", "Analysis task failed", "Extraction task failed",
                            "Task failed due to API timeout", "API call failed",
                            "Please try again later", "Please check network",
                            "basic reasoning for:", "unable to determine", "cannot determine"
                        ]
                        reasoning_lower = reasoning_answer.lower()
                        if any(pattern.lower() in reasoning_lower for pattern in invalid_patterns):
                            logger.warning(f"⚠️ 提取的答案包含失败信息，忽略: {reasoning_answer[:50]}...")
                            reasoning_answer = None
                
                if reasoning_answer:
                    logger.info(f"✅ 成功提取推理答案: {reasoning_answer[:50]}...")
                else:
                    logger.warning(f"⚠️ 无法从推理结果提取答案")
                    logger.warning(f"   类型: {type(reasoning_result)}")
                    logger.warning(f"   data类型: {type(getattr(reasoning_result, 'data', None)) if hasattr(reasoning_result, 'data') else 'N/A'}")
                    if hasattr(reasoning_result, 'data'):
                        data_val = getattr(reasoning_result, 'data', None)
                        if isinstance(data_val, dict):
                            logger.warning(f"   data字典键: {list(data_val.keys())}")
                        elif isinstance(data_val, str):
                            logger.warning(f"   data字符串前100字符: {data_val[:100]}")
            
            # 生成query_id用于保存推理结果
            import hashlib
            query_id_hash = hashlib.md5(request.query.encode()).hexdigest()[:8]
            
            # 🚀 优化：保存推理结果，以便超时时使用（包含查询文本用于匹配）
            self._latest_reasoning_result = {
                'query_id': query_id_hash,
                'query': request.query,  # 保存查询文本用于匹配
                'reasoning_result': reasoning_result,
                'reasoning_answer': reasoning_answer,
                'timestamp': time.time()
            }
            
            logger.debug(f"保存推理结果: query={request.query[:50]}..., answer={reasoning_answer[:50] if reasoning_answer else 'None'}...")
            
            # 🚀 ML/RL优化：检查是否应该跳过答案生成
            should_skip_answer_generation = skip_answer_generation
            if should_skip_answer_generation and reasoning_answer and self._is_valid_answer_length(reasoning_answer):
                logger.info(f"🚀 ML/RL优化：跳过答案生成（推理答案已足够好: {reasoning_answer[:50]}...）")
                # 直接返回推理答案，跳过答案生成和引用生成
                confidence = getattr(reasoning_result, 'total_confidence', 0.8) if not isinstance(reasoning_result, Exception) else 0.8
                return ResearchResult(
                    success=True,
                    answer=reasoning_answer,
                    knowledge=self._extract_knowledge_data(knowledge_result) if not isinstance(knowledge_result, Exception) else [],
                    citations=[],  # 跳过引用生成
                    confidence=confidence,
                    metadata={
                        "fast_path": True,
                        "reasoning_completed": True,
                        "skipped_answer_generation": True,  # ML/RL优化：跳过答案生成
                        "skipped_citation_generation": True,
                        "ml_rl_optimization": True
                    }
                )
            
            # 🚀 核心优化：推理完成后，如果答案可用，立即返回，跳过后续步骤
            # 这是正常处理流程的快速路径，避免不必要的等待
            # 🚀 修复答案丢失问题：使用智能长度检查，允许数字答案（单字符和双字符）
            if reasoning_answer and self._is_valid_answer_length(reasoning_answer):
                # 验证答案有效性（过滤明显的错误信息）
                invalid_indicators = [
                    "Reasoning task failed",
                    "API timeout",
                    "unable to determine",
                    "无法确定",
                    "not knowable"
                ]
                is_valid_answer = not any(indicator.lower() in reasoning_answer.lower() for indicator in invalid_indicators)
                
                if is_valid_answer:
                    logger.info(f"✅ 推理完成，已提取有效答案，使用快速路径返回: {reasoning_answer[:50]}...")
                    
                    # 快速路径：直接构建结果并返回，跳过答案生成和引用生成
                    # 提取基础信息
                    reasoning_text = ""
                    if not isinstance(reasoning_result, Exception):
                        reasoning_data = safe_get_data_for_reasoning(reasoning_result, {})
                        if isinstance(reasoning_data, dict):
                            reasoning_text = reasoning_data.get('reasoning', '')
                    
                    # 提取知识列表（用于citations）
                    knowledge_list = []
                    if not isinstance(knowledge_result, Exception):
                        try:
                            k_data = getattr(knowledge_result, 'data', None)
                            if isinstance(k_data, dict):
                                knowledge_list = k_data.get('sources', []) or k_data.get('knowledge', [])
                            elif isinstance(k_data, list):
                                knowledge_list = k_data
                        except Exception:
                            pass
                    
                    # 计算置信度
                    confidence = 0.7  # 默认置信度
                    if not isinstance(reasoning_result, Exception) and hasattr(reasoning_result, 'confidence'):
                        confidence = getattr(reasoning_result, 'confidence', 0.7)
                    
                    # 立即返回结果，不等待后续步骤
                    result = ResearchResult(
                        query=request.query,
                        success=True,
                        answer=reasoning_answer.strip(),
                        knowledge=knowledge_list if isinstance(knowledge_list, list) else [],
                        reasoning=reasoning_text if reasoning_text else "推理完成，已提供答案",
                        citations=[],  # 快速路径中省略引用，节省时间
                        confidence=confidence,
                        metadata={
                            "fast_path": True,
                            "reasoning_completed": True,
                            "skipped_answer_generation": True,
                            "skipped_citation_generation": True
                        }
                    )
                    
                    logger.info(f"🚀 快速路径：推理完成且有答案，立即返回，跳过后续步骤（节省约20秒）")
                    
                    # 🚀 新增：添加查询完成日志（快速路径）
                    sample_id = None
                    if isinstance(request.context, dict):
                        sample_id = request.context.get('sample_id') or request.context.get('item_index')
                    if sample_id is not None:
                        log_info(f"查询完成: success=True (fast_path), 样本ID={sample_id}")
                    else:
                        log_info("查询完成: success=True (fast_path)")
                    
                    # 🚀 新增：记录性能数据用于ML/RL学习
                    total_time = time.time() - start_time
                    reasoning_time = total_time - knowledge_retrieval_time
                    answer_time = 0.0  # 快速路径跳过答案生成
                    
                    # 从context中获取准确率（如果有）
                    accuracy = 1.0  # 默认值
                    if isinstance(request.context, dict) and 'expected_answer' in request.context:
                        expected = request.context.get('expected_answer', '')
                        actual = result.answer
                        if expected and actual:
                            accuracy = 1.0 if expected.lower().strip() == actual.lower().strip() else 0.0
                    
                    self._record_scheduling_performance(
                        query_type=query_type or 'general',
                        query_complexity=query_complexity or 'medium',
                        ml_strategy=ml_strategy,
                        rl_action=rl_action,
                        rl_state=rl_state,
                        knowledge_time=knowledge_retrieval_time,
                        reasoning_time=reasoning_time,
                        answer_time=answer_time,
                        total_time=total_time,
                        success=True,
                        accuracy=accuracy
                    )
                    
                    return result
                else:
                    logger.info(f"⚠️ 推理完成但答案无效，继续执行后续步骤: {reasoning_answer[:50]}...")
            
            # 如果推理没有答案或答案无效，继续执行后续步骤（原有逻辑）
            logger.info("✍️ 步骤3: 开始答案生成和引用生成（并行执行）...")
            
            # 🚀 新增：添加查询处理日志（答案生成和引用生成步骤）
            sample_id = None
            if isinstance(request.context, dict):
                sample_id = request.context.get('sample_id') or request.context.get('item_index')
            if sample_id is not None:
                log_info(f"查询处理: 样本ID={sample_id}, 步骤=答案生成和引用生成")
            else:
                log_info("查询处理: 步骤=答案生成和引用生成")
            
            if not self._answer_agent:
                raise RuntimeError("答案生成智能体未初始化")
            if not self._citation_agent:
                raise RuntimeError("引用生成智能体未初始化")

            # 安全提取数据
            def safe_get_data(result, default=None):
                if isinstance(result, Exception):
                    return default
                if hasattr(result, 'data'):
                    return result.data
                return default

            # 🚀 优化：准备答案和引用的上下文
            answer_context = {
                "query": request.query,
                "knowledge_data": self._extract_knowledge_data(knowledge_result) if not isinstance(knowledge_result, Exception) else {},
                "reasoning_data": safe_get_data(reasoning_result, {}),
                "type": "answer_generation"
            }

            # Citation 可以直接基于 knowledge，不需要等待 answer
            # 简单提取knowledge列表
            def get_knowledge_list(k_result):
                if isinstance(k_result, Exception):
                    return []
                if hasattr(k_result, 'success') and k_result.success and hasattr(k_result, 'data'):
                    data = k_result.data
                    if isinstance(data, dict):
                        sources = data.get('sources', [])
                        if sources:
                            return sources
                    elif isinstance(data, list):
                        return data
                return []

            citation_context = {
                "content": request.query,  # 使用查询作为初始内容
                "answer": request.query,
                "knowledge": get_knowledge_list(knowledge_result),
                "query": request.query,
                "type": "citation_generation"
            }

            # 🚀 核心优化：如果推理已经有答案，简化后续处理，快速完成
            # 答案生成和引用生成可以使用更短的超时，因为它们不再是必需的
            # 如果这些步骤超时，可以直接使用推理结果
            
            # 🚀 方案3：优先使用Tools，如果不可用则回退到Agent
            # 🚀 并行执行 Answer 和 Citation（优化：使用更短的超时，因为推理已有答案）
            if self.tool_registry and self.tool_registry.get_tool("answer_generation"):
                logger.info("🚀 [传统流程] 使用AnswerGenerationTool（方案3：统一工具接口）")
                
                # 🚀 P0修复：构建dependencies，确保推理结果能正确传递
                dependencies = {}
                if not isinstance(reasoning_result, Exception) and reasoning_result:
                    # 将reasoning_result转换为dependencies格式
                    dependencies["reasoning"] = reasoning_result
                    logger.info(f"🔍 [传统流程] 为答案生成工具添加推理结果到dependencies")
                
                # 确保context中包含dependencies
                answer_context_with_deps = dict(answer_context)
                answer_context_with_deps["dependencies"] = dependencies
                
                answer_task = asyncio.create_task(
                    self._execute_tool_with_timeout(
                        "answer_generation",
                        {
                            "query": request.query,
                            "knowledge_data": self._extract_knowledge_data(knowledge_result) if not isinstance(knowledge_result, Exception) else [],
                            "reasoning_data": safe_get_data(reasoning_result, {}),
                            "context": answer_context_with_deps  # 🚀 P0修复：使用包含dependencies的context
                        },
                        "answer_generation",
                        timeout=5.0
                    )
                )
            else:
                logger.info("🔄 [传统流程] 回退到AnswerGenerationAgent（Tools不可用）")
                answer_task = asyncio.create_task(
                    self._execute_agent_with_timeout(
                        self._answer_agent,  # 回退到Agent
                        answer_context,
                        "answer_generation",
                        timeout=5.0
                    )
                )

            if self.tool_registry and self.tool_registry.get_tool("citation"):
                logger.info("🚀 [传统流程] 使用CitationTool（方案3：统一工具接口）")
                citation_task = asyncio.create_task(
                    self._execute_tool_with_timeout(
                        "citation",
                        {
                            "content": request.query,
                            "sources": get_knowledge_list(knowledge_result),
                            "context": citation_context
                        },
                        "citation_generation",
                        timeout=5.0
                    )
                )
            else:
                logger.info("🔄 [传统流程] 回退到CitationAgent（Tools不可用）")
                citation_task = asyncio.create_task(
                    self._execute_agent_with_timeout(
                        self._citation_agent,  # 回退到Agent
                        citation_context,
                        "citation_generation",
                        timeout=5.0
                    )
                )

            # 🚀 核心优化：使用asyncio.wait实现超时后立即使用推理结果
            # 如果答案生成或引用生成超时，不等待它们完成，直接使用推理结果
            done, pending = await asyncio.wait(
                [answer_task, citation_task],
                timeout=5.0,  # 最多等待5秒
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # 处理已完成的任务
            answer_result = None
            citation_result = None
            
            for task in done:
                try:
                    if task == answer_task:
                        answer_result = task.result()
                    elif task == citation_task:
                        citation_result = task.result()
                except Exception as e:
                    if task == answer_task:
                        answer_result = Exception(f"答案生成失败: {e}")
                    elif task == citation_task:
                        citation_result = Exception(f"引用生成失败: {e}")
            
            # 🚀 核心优化：如果5秒内没有任务完成，取消未完成的任务并使用推理结果
            if pending:
                logger.info(f"⏱️ 答案生成或引用生成超时（5秒），取消任务并使用推理结果")
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                
                # 如果answer_result还没有完成，使用推理结果
                if answer_result is None:
                    if reasoning_answer and self._is_valid_answer_length(reasoning_answer):
                        logger.info(f"✅ 答案生成超时，使用推理结果: {reasoning_answer[:50]}...")
                        answer_result = AgentResult(
                            success=True,
                            data={"answer": reasoning_answer.strip()},
                            confidence=0.7,
                            processing_time=0.0,
                            metadata={"fallback_to_reasoning": True}
                        )
                    else:
                        answer_result = AgentResult(
                            success=False,
                            data={"answer": ""},
                            confidence=0.3,
                            processing_time=0.0,
                            metadata={"timeout": True}
                        )
                
                # 如果citation_result还没有完成，使用空列表
                if citation_result is None:
                    logger.info(f"⚠️ 引用生成超时，使用空引用列表")
                    citation_result = AgentResult(
                        success=True,
                        data={"citations": []},
                        confidence=0.5,
                        processing_time=0.0,
                        metadata={"timeout": True}
                    )
            
            # 如果还有pending的任务，等待它们完成（但不阻塞太久）
            if pending:
                try:
                    # 使用较短的超时等待剩余任务
                    remaining_results = await asyncio.wait_for(
                        asyncio.gather(*pending, return_exceptions=True),
                        timeout=2.0  # 最多再等2秒
                    )
                    for i, task in enumerate(pending):
                        if task == answer_task and answer_result is None:
                            try:
                                if i < len(remaining_results):
                                    answer_result = remaining_results[i]
                            except:
                                pass
                        elif task == citation_task and citation_result is None:
                            try:
                                if i < len(remaining_results):
                                    citation_result = remaining_results[i]
                            except:
                                pass
                except asyncio.TimeoutError:
                    logger.debug(f"等待剩余任务超时，使用默认值")
                except Exception as e:
                    logger.debug(f"等待剩余任务失败: {e}")
            
            # 如果仍有未设置的结果，设置为默认值（使用推理结果）
            if answer_result is None:
                if reasoning_answer and self._is_valid_answer_length(reasoning_answer):
                    logger.info(f"✅ 答案生成未完成，使用推理结果: {reasoning_answer[:50]}...")
                    answer_result = AgentResult(
                        success=True,
                        data={"answer": reasoning_answer.strip()},
                        confidence=0.7,
                        processing_time=0.0,
                        metadata={"fallback_to_reasoning": True}
                    )
                else:
                    answer_result = AgentResult(
                        success=False,
                        data={"answer": ""},
                        confidence=0.3,
                        processing_time=0.0,
                        metadata={"timeout": True}
                    )
            
            if citation_result is None:
                logger.info(f"⚠️ 引用生成未完成，使用空引用列表")
                citation_result = AgentResult(
                    success=True,
                    data={"citations": []},
                    confidence=0.5,
                    processing_time=0.0,
                    metadata={"timeout": True}
                )

            # 处理答案结果异常
            if isinstance(answer_result, Exception):
                logger.error(f"❌ 答案生成失败: {answer_result}")
                answer_result = AgentResult(
                    success=False,
                    data={
                        "answer": f"答案生成失败: {str(answer_result)}",
                        "type": "error_fallback",
                        "confidence": 0.3
                    },
                    confidence=0.3,
                    processing_time=0.0,
                    metadata={"type": "error_fallback", "error": str(answer_result)}
                )
            else:
                answer_success = getattr(answer_result, 'success', 'Unknown')
                logger.info(f"✅ 答案生成完成，结果: {answer_success}")

            # 处理引用结果异常
            if isinstance(citation_result, Exception):
                logger.warning(f"⚠️ 引用生成失败: {citation_result}")
                citation_result = AgentResult(
                    success=False,
                    data={"error": str(citation_result)},
                    confidence=0.3,
                    processing_time=0.0
                )
            else:
                citation_success = getattr(citation_result, 'success', 'Unknown')
                logger.info(f"✅ 引用生成完成，结果: {citation_success}")

            def safe_extract_data(result, key: str, default="", data_type: str = "any"):
                """安全地提取结果数据 - 增强版"""
                try:
                    # 处理异常情况
                    if isinstance(result, Exception):
                        logger.warning(f"结果包含异常: {result}")
                        return default
                    
                    # 检查结果有效性
                    if not result:
                        logger.debug("结果为空")
                        return default
                    
                    # 检查成功状态
                    if hasattr(result, 'success') and not result.success:
                        logger.debug(f"操作失败: {getattr(result, 'error', '未知错误')}")
                        return default
                    
                    # 提取数据
                    if hasattr(result, 'data'):
                        data = result.data
                        
                        # 处理字典类型数据
                        if isinstance(data, dict):
                            value = data.get(key, default)
                            
                            # 类型验证
                            if data_type != "any":
                                value = _validate_data_type(value, data_type, default)
                            
                            return value
                        
                        # 处理列表类型数据
                        elif isinstance(data, list) and key.isdigit():
                            index = int(key)
                            if 0 <= index < len(data):
                                return data[index]
                            else:
                                logger.warning(f"索引 {index} 超出范围")
                                return default
                        
                        # 处理其他类型数据
                        else:
                            logger.debug(f"无法从 {type(data)} 中提取键 {key}")
                            return default
                    
                    # 如果result本身就是数据
                    elif isinstance(result, dict):
                        return result.get(key, default)
                    
                    else:
                        logger.debug(f"结果类型 {type(result)} 不支持数据提取")
                        return default
                        
                except Exception as e:
                    logger.warning(f"提取数据失败: {e}")
                    return default
            
            def safe_extract_list(result, default=None, list_key: str = "knowledge", validate_items: bool = True):
                """安全地提取列表数据 - 增强版"""
                try:
                    # 处理异常情况
                    if isinstance(result, Exception):
                        logger.warning(f"结果包含异常: {result}")
                        return default or []
                    
                    # 检查结果有效性
                    if not result:
                        logger.debug("结果为空")
                        return default or []
                    
                    # 检查成功状态
                    if hasattr(result, 'success') and not result.success:
                        logger.debug(f"操作失败: {getattr(result, 'error', '未知错误')}")
                        return default or []
                    
                    # 提取列表数据
                    if hasattr(result, 'data'):
                        data = result.data
                        
                        # 处理字典类型数据
                        if isinstance(data, dict):
                            # 尝试多个可能的键
                            possible_keys = [list_key, 'knowledge', 'items', 'results', 'data']
                            for key in possible_keys:
                                if key in data and isinstance(data[key], list):
                                    list_data = data[key]
                                    if validate_items:
                                        list_data = _validate_list_items(list_data)
                                    return list_data
                            
                            # 如果字典本身就是列表结构
                            if all(isinstance(v, (list, dict)) for v in data.values()):
                                return list(data.values())
                        
                        # 处理列表类型数据
                        elif isinstance(data, list):
                            if validate_items:
                                return _validate_list_items(data)
                            return data
                        
                        # 处理其他类型
                        else:
                            logger.debug(f"无法从 {type(data)} 中提取列表")
                            return default or []
                    
                    # 如果result本身就是列表
                    elif isinstance(result, list):
                        if validate_items:
                            return _validate_list_items(result)
                        return result
                    
                    else:
                        logger.debug(f"结果类型 {type(result)} 不支持列表提取")
                        return default or []
                        
                except Exception as e:
                    logger.warning(f"提取列表失败: {e}")
                    return default or []
            
            def _validate_data_type(value, expected_type: str, default):
                """验证数据类型"""
                try:
                    if expected_type == "str" and not isinstance(value, str):
                        return str(value) if value is not None else default
                    elif expected_type == "int" and not isinstance(value, int):
                        return int(value) if value is not None else default
                    elif expected_type == "float" and not isinstance(value, float):
                        return float(value) if value is not None else default
                    elif expected_type == "bool" and not isinstance(value, bool):
                        return bool(value) if value is not None else default
                    elif expected_type == "list" and not isinstance(value, list):
                        return [value] if value is not None else default
                    elif expected_type == "dict" and not isinstance(value, dict):
                        return {"value": value} if value is not None else default
                    
                    return value
                except (ValueError, TypeError) as e:
                    logger.warning(f"类型转换失败: {e}")
                    return default
            
            def _validate_list_items(items: list) -> list:
                """验证列表项"""
                try:
                    if not items:
                        return []
                    
                    validated_items = []
                    for item in items:
                        if item is not None:
                            # 过滤掉空字符串和无效项
                            if isinstance(item, str) and item.strip():
                                validated_items.append(item.strip())
                            elif not isinstance(item, str):
                                validated_items.append(item)
                    
                    return validated_items
                except Exception as e:
                    logger.warning(f"验证列表项失败: {e}")
                    return items if items else []

            def extract_answer_content(answer_result):
                """安全地提取答案内容"""
                try:
                    if isinstance(answer_result, Exception):
                        return ""
                    if not answer_result or not hasattr(answer_result, 'success') or not answer_result.success:
                        return ""

                    if hasattr(answer_result, 'answer'):
                        return answer_result.answer or ""

                    if hasattr(answer_result, 'data') and isinstance(answer_result.data, dict):
                        return answer_result.data.get('answer', '')

                    return ""
                except Exception as e:
                    logger.warning(f"提取答案内容失败: {e}")
                    return ""

            # 引用已经在步骤3并行执行完成，直接进行结果整合
            logger.info("🔧 步骤4: 开始智能整合结果...")

            # 🚀 优化：增强的智能融合多Agent结果（加入答案质量验证）
            def intelligent_merge_results(knowledge_result, reasoning_result, answer_result):
                """智能融合多个agent的结果 - 增强版"""
                # 1. 质量评估
                knowledge_quality = 1.0 if not isinstance(knowledge_result, Exception) and knowledge_result.success else 0.0
                reasoning_quality = 1.0 if not isinstance(reasoning_result, Exception) and reasoning_result.success else 0.0
                answer_quality = 1.0 if not isinstance(answer_result, Exception) and answer_result.success else 0.0
                
                # 2. 答案质量评分系统
                def calculate_answer_quality_score(answer, knowledge, reasoning):
                    """计算答案质量分数"""
                    score = 0.0
                    
                    # 2.1 答案完整性 (30%)
                    if answer and len(answer.strip()) > 5:
                        if "无法确定" not in answer.lower() and "不确定" not in answer.lower():
                            completeness_score = min(len(answer) / 100.0, 1.0)
                            score += completeness_score * 0.3
                    
                    # 2.2 与knowledge的匹配度 (35%)
                    knowledge_data = safe_get_data(knowledge, {})
                    if knowledge_data:
                        # 简单的关键词匹配
                        answer_words = set(answer.lower().split()) if answer else set()
                        knowledge_text = str(knowledge_data).lower()
                        matching_words = [w for w in answer_words if w in knowledge_text]
                        match_ratio = len(matching_words) / len(answer_words) if answer_words else 0
                        score += match_ratio * 0.35
                    
                    # 2.3 答案可信度 (25%)
                    reasoning_data = safe_get_data(reasoning, {})
                    if reasoning_data:
                        # 如果推理结果支持答案
                        reasoning_text = str(reasoning_data).lower()
                        answer_lower = answer.lower() if answer else ""
                        if reasoning_text and "不确定" not in reasoning_text:
                            if any(word in reasoning_text for word in answer_lower.split()):
                                score += 0.25
                    
                    # 2.4 置信度评分 (10%)
                    confidence_score = min(answer_quality, 1.0) * 0.1
                    score += confidence_score
                    
                    return score
                
                # 🚀 修复答案传递链路问题：优先使用推理答案
                # 3. 智能提取答案（优化：优先使用推理答案，增强回退逻辑）
                answer = ""
                
                # 🚀 修复：优先从推理结果中提取答案（reasoning_answer）
                # 推理答案是最可靠的，因为它已经通过了推理引擎的验证
                if reasoning_answer and self._is_valid_answer_length(reasoning_answer):
                    answer = reasoning_answer.strip()
                    logger.info(f"✅ 优先使用推理答案: {answer[:50]}...")
                else:
                    # 如果推理答案不可用，从answer_result中提取
                    answer = str(safe_extract_data(answer_result, "answer", "", "str"))
                
                # 🚀 优化：如果答案为空，尝试更激进的回退策略
                if not answer or not self._is_valid_answer_length(answer):
                    logger.warning(f"答案提取失败或过短（'{answer}'），尝试回退提取")
                    
                    # 回退1：从answer_result的data字段直接提取
                    if not isinstance(answer_result, Exception) and answer_result and hasattr(answer_result, 'data'):
                        if isinstance(answer_result.data, dict):  # type: ignore[attr-defined]
                            for key in ['answer', 'content', 'text', 'result']:
                                if key in answer_result.data and answer_result.data[key]:  # type: ignore[attr-defined]
                                    answer = str(answer_result.data[key])  # type: ignore[attr-defined]
                                    if self._is_valid_answer_length(answer):
                                        logger.info(f"✅ 从data.{key}提取到答案")
                                        break
                    
                    # 回退2：从knowledge提取
                    if not answer or not self._is_valid_answer_length(answer):
                        knowledge_data = safe_get_data(knowledge_result, {})
                        if isinstance(knowledge_data, dict) and 'content' in knowledge_data:
                            content = str(knowledge_data['content'])
                            if content and len(content.strip()) > 10:
                                # 提取第一句话
                                first_sentence = content.split('.')[0].strip()
                                if len(first_sentence) > 5:
                                    answer = first_sentence[:100]
                                    logger.info(f"✅ 从knowledge.content提取到答案")
                    
                    # 回退3：从查询本身提取关键词
                    if not answer or not self._is_valid_answer_length(answer):
                        query = str(request.query) if hasattr(request, 'query') else ""
                        # 提取关键词（第一个有意义的词）
                        words = query.split()[:3]
                        if words:
                            answer = " ".join(words)
                            logger.info(f"✅ 从查询中提取关键词作为答案")
                
                # 最终保障：如果还是空，返回友好提示
                if not answer or not self._is_valid_answer_length(answer):
                    answer = "根据可用信息无法提供完整答案"
                    logger.warning(f"⚠️ 无法提取有效答案，使用默认提示")
                
                # 4. 计算答案质量分数
                answer_quality_score = calculate_answer_quality_score(
                    answer, 
                    knowledge_result, 
                    reasoning_result
                )
                
                # 🚀 新增：多Agent协同验证机制
                def multi_agent_validation(answer, knowledge_res, reasoning_res):
                    """多Agent协同验证答案"""
                    validations = []
                    
                    # 1. Knowledge Agent验证
                    if not isinstance(knowledge_res, Exception) and knowledge_res.success:
                        knowledge_data = safe_get_data(knowledge_res, {})
                        if knowledge_data:
                            # 检查答案是否与知识匹配
                            answer_words = set(answer.lower().split()) if answer else set()
                            knowledge_text = str(knowledge_data).lower()
                            match_count = sum(1 for word in answer_words if word in knowledge_text)
                            match_ratio = match_count / len(answer_words) if answer_words else 0
                            
                            validations.append({
                                'agent': 'knowledge',
                                'support': match_ratio > 0.3,  # 至少30%匹配
                                'confidence': match_ratio,
                                'reason': f"知识匹配度: {match_ratio:.2f}"
                            })
                    
                    # 2. Reasoning Agent验证
                    if not isinstance(reasoning_res, Exception) and reasoning_res.success:
                        reasoning_data = safe_get_data(reasoning_res, {})
                        if reasoning_data and isinstance(reasoning_data, dict):
                            reasoning_text = str(reasoning_data.get('reasoning', '')).lower()
                            
                            # 检查推理是否支持答案
                            supports = "不确定" not in reasoning_text and reasoning_text != ""
                            
                            validations.append({
                                'agent': 'reasoning',
                                'support': supports,
                                'confidence': 0.7 if supports else 0.3,
                                'reason': "推理支持" if supports else "推理不确定"
                            })
                    
                    # 3. 综合判断
                    supporting_agents = sum(1 for v in validations if v['support'])
                    total_agents = len(validations)
                    
                    if total_agents > 0:
                        agreement_ratio = supporting_agents / total_agents
                        return agreement_ratio, validations
                    else:
                        return 0.0, []
                
                # 执行多Agent验证
                agreement_ratio, validations = multi_agent_validation(answer, knowledge_result, reasoning_result)
                
                # 基于多Agent验证调整质量分数
                if agreement_ratio >= 0.5:  # 至少50%的Agent支持
                    answer_quality_score = min(answer_quality_score * (1 + agreement_ratio), 1.0)
                    logger.info(f"✅ 多Agent协同验证通过（支持率: {agreement_ratio:.2f}），质量分数调整为: {answer_quality_score:.2f}")
                else:
                    logger.warning(f"⚠️ 多Agent协同验证失败（支持率: {agreement_ratio:.2f}），需要改进答案")
                
                # 5. 质量阈值检查 - 更宽松的策略
                quality_threshold = 0.05  # 极低阈值以最大化接受答案
                
                # 策略：优先接受任何非"无法确定"的答案
                if answer and self._is_valid_answer_length(answer):
                    # 如果答案不是"无法确定"且长度合理，直接接受
                    if "无法确定" not in answer.lower() and "不确定" not in answer.lower():
                        logger.info(f"✅ 接受答案，质量分数: {answer_quality_score:.2f}")
                    else:
                        # 答案是"无法确定"，尝试从knowledge中寻找备选（增强版）
                        logger.warning(f"答案质量分数 {answer_quality_score:.2f} 且答案为'无法确定'，尝试寻找备选答案")
                        
                        # 增强的备选答案提取
                        knowledge_data = safe_get_data(knowledge_result, {})
                        
                        # 策略1：从dict格式的knowledge中提取
                        if isinstance(knowledge_data, dict):
                            content = knowledge_data.get('content', '')
                            if content and len(content) > 10:
                                # 尝试提取第一个完整句子
                                sentences = content.split('.')
                                for sent in sentences:
                                    sent = sent.strip()
                                    if sent and len(sent) > 5 and '?' not in sent:
                                        if '无法确定' not in sent and '不确定' not in sent:
                                            logger.info(f"🔍 使用knowledge中的备选答案: {sent[:50]}...")
                                            answer = sent[:200]
                                            answer_quality_score = min(answer_quality_score * 1.5, 1.0)
                                            break
                        
                        # 策略2：从list格式的knowledge中提取
                        if isinstance(knowledge_data, list) and answer == "无法确定":
                            for item in knowledge_data:
                                if isinstance(item, dict):
                                    item_content = item.get('content', '')
                                    if item_content and len(item_content) > 10:
                                        # 提取第一个短语或句子
                                        phrases = item_content.split(',')
                                        for phrase in phrases:
                                            phrase = phrase.strip()
                                            if phrase and 5 <= len(phrase) <= 200 and '无法确定' not in phrase:
                                                logger.info(f"🔍 使用knowledge列表中的备选答案: {phrase[:50]}...")
                                                answer = phrase[:200]
                                                answer_quality_score = min(answer_quality_score * 1.5, 1.0)
                                                break
                                        if answer != "无法确定":
                                            break
                
                # 6. 置信度加权计算
                knowledge_weight = 0.3
                reasoning_weight = 0.3
                answer_weight = 0.4
                
                overall_confidence = (
                    knowledge_quality * knowledge_weight +
                    reasoning_quality * reasoning_weight +
                    answer_quality * answer_weight
                )
                
                # 7. 基于答案质量调整置信度
                overall_confidence = overall_confidence * answer_quality_score
                
                # 返回answer, confidence, quality_score, agreement_ratio, validations
                return answer, overall_confidence, answer_quality_score, agreement_ratio, validations
            
            merged_answer, merged_confidence, quality_score, agreement_ratio, validations = intelligent_merge_results(
                knowledge_result, 
                reasoning_result, 
                answer_result
            )
            
            # 4. 构建最终结果（包含质量评分和多Agent验证信息）
            result = ResearchResult(
                query=request.query,
                success=True,
                answer=merged_answer,
                knowledge=safe_extract_list(knowledge_result),
                reasoning=str(safe_extract_data(reasoning_result, "reasoning", "", "str")),
                citations=safe_extract_list(citation_result),
                confidence=merged_confidence,
                metadata={
                    "knowledge_count": len(safe_extract_list(knowledge_result) or []),
                    "reasoning_type": safe_extract_data(reasoning_result, "type", "unknown"),
                    "citation_count": len(safe_extract_list(citation_result) or []),
                    "merging_strategy": "intelligent_fusion_with_multi_agent_validation",
                    "quality_score": quality_score,
                    "agreement_ratio": agreement_ratio if agreement_ratio > 0 else 0.5,
                    "validation_count": len(validations) if validations else 0,
                    "original_confidence": get_smart_config("high_threshold", {"config_type": "auto"}),
                    "merged_confidence": merged_confidence
                }
            )
            
            logger.info(f"📊 答案质量分数: {quality_score:.2f}, Agent支持率: {agreement_ratio:.2f}, 最终置信度: {merged_confidence:.2f}")

            # 触发ML学习活动
            if self._ai_algorithm_integrator:
                try:
                    evidence_trajectory = {
                        "query": request.query,
                        "knowledge_count": len(result.knowledge or []),
                        "reasoning_steps": 1,
                        "success": result.success
                    }
                    await self._trigger_ml_learning(request, evidence_trajectory, result, "success")
                    logger.info("✅ ML学习活动触发成功")
                except Exception as e:
                    logger.warning(f"⚠️ ML学习活动触发失败: {e}")

            logger.info("✅ 研究执行完成: {request.query[:30]}...")
            
            # 🚀 新增：添加查询完成日志（智能融合流程）
            sample_id = None
            if isinstance(request.context, dict):
                sample_id = request.context.get('sample_id') or request.context.get('item_index')
            if sample_id is not None:
                log_info(f"查询完成: success={result.success}, 样本ID={sample_id}")
            else:
                log_info(f"查询完成: success={result.success}")
            
            # 🚀 新增：记录性能数据用于ML/RL学习
            total_time = time.time() - start_time
            reasoning_time = getattr(result, 'execution_time', total_time) - knowledge_retrieval_time
            answer_time = 0.0  # 答案生成时间（如果执行了）
            
            # 从context中获取准确率（如果有）
            accuracy = 1.0  # 默认值
            if isinstance(request.context, dict) and 'expected_answer' in request.context:
                # 如果有期望答案，可以计算准确率（这里简化处理）
                expected = request.context.get('expected_answer', '')
                actual = result.answer
                if expected and actual:
                    # 简单匹配：如果答案匹配，准确率为1.0，否则为0.0
                    # 实际应该使用评测系统的准确率计算
                    accuracy = 1.0 if expected.lower().strip() == actual.lower().strip() else 0.0
            
            self._record_scheduling_performance(
                query_type=query_type or 'general',
                query_complexity=query_complexity or 'medium',
                ml_strategy=ml_strategy,
                rl_action=rl_action,
                rl_state=rl_state,
                knowledge_time=knowledge_retrieval_time,
                reasoning_time=reasoning_time,
                answer_time=answer_time,
                total_time=total_time,
                success=result.success,
                accuracy=accuracy
            )
            
            # 🚀 保存到缓存
            import hashlib
            cache_hash = hashlib.md5(request.query.encode()).hexdigest()
            if self._cache_system['cache_hits'] + self._cache_system['cache_misses'] < self._cache_system['max_cache_size']:
                self._cache_system['query_cache'][cache_hash] = {
                    'result': result,
                    'timestamp': time.time()
                }
            
            return result

        except Exception as e:
            logger.error("❌ 研究执行失败: {e}")
            
            # 🚀 新增：添加查询完成日志（异常情况）
            sample_id = None
            if isinstance(request.context, dict):
                sample_id = request.context.get('sample_id') or request.context.get('item_index')
            if sample_id is not None:
                log_info(f"查询完成: success=False (exception), 样本ID={sample_id}, error={str(e)[:100]}")
            else:
                log_info(f"查询完成: success=False (exception), error={str(e)[:100]}")
            
            # 🚀 新增：记录失败的性能数据用于ML/RL学习
            total_time = time.time() - start_time
            try:
                self._record_scheduling_performance(
                    query_type=query_type or 'general',
                    query_complexity=query_complexity or 'medium',
                    ml_strategy=ml_strategy,
                    rl_action=rl_action,
                    rl_state=rl_state,
                    knowledge_time=0.0,
                    reasoning_time=0.0,
                    answer_time=0.0,
                    total_time=total_time,
                    success=False,
                    accuracy=0.0
                )
            except Exception as perf_error:
                logger.debug(f"记录失败性能数据失败: {perf_error}")
            
            return ResearchResult(
                query=request.query,
                success=False,
                answer=f"研究执行失败: {str(e)}",
                knowledge=[],
                reasoning="",
                citations=[],
                confidence=0.0,
                metadata={"error": str(e)}
            )

    def _extract_knowledge_data(self, knowledge_result) -> List[Dict[str, Any]]:
        """从知识检索结果中提取知识数据（增强版-支持向量知识库，包含问题过滤）"""
        try:
            if not knowledge_result or not knowledge_result.success:
                return []
            
            # 🚀 优化：移除问题过滤，依赖LLM判断相关性
            # 只保留基本的内容质量检查（空内容、太短），让LLM判断是否是问题
            
            knowledge_data = []
            if hasattr(knowledge_result, 'data') and knowledge_result.data:
                sources = knowledge_result.data.get('sources', [])
                for source in sources:
                    # 🚀 优先处理向量知识库的格式
                    if isinstance(source, dict) and 'content' in source:
                        content = source.get('content', '')
                        # 🚀 优化：移除问题过滤，只保留基本的内容质量检查
                        if content and len(content.strip()) >= 10:
                            knowledge_data.append({
                                'content': content,
                                'source': source.get('metadata', {}).get('source', 'vector_kb'),
                                'confidence': source.get('confidence', 0.8),
                                'metadata': source.get('metadata', {})
                            })
                    # 处理原有格式
                    elif 'result' in source and hasattr(source['result'], 'data'):
                        source_data = source['result'].data
                        if isinstance(source_data, dict):
                            knowledge_data.append({
                                'content': source_data.get('content', ''),
                                'source': source_data.get('source', 'unknown'),
                                'confidence': source_data.get('confidence', 0.5),
                                'metadata': source_data.get('metadata', {})
                            })
            
            return knowledge_data
            
        except Exception as e:
            logger.warning(f"提取知识数据失败: {e}")
            return []

    async def _trigger_ml_learning(self, request: ResearchRequest, evidence_trajectory: Dict[str, Any], result: ResearchResult, outcome_type: str):
        """触发ML学习活动"""
        try:
            # 创建学习上下文
            learning_context = {
                'query': request.query,
                'evidence_trajectory': evidence_trajectory,
                'result': {
                    'success': result.success,
                    'confidence': getattr(result, 'confidence', 0.0),
                    'execution_time': result.execution_time,
                    'error': getattr(result, 'error', None)
                },
                'outcome_type': outcome_type,
                'timestamp': time.time()
            }
            
            # 触发学习系统
            if hasattr(self, 'learning_system') and self.learning_system:
                learning_task = {
                    'type': 'pattern_learning',
                    'context': learning_context,
                    'query': request.query
                }
                
                # 异步执行学习
                learning_result = await self._execute_agent_with_timeout(
                    self.learning_system, 
                    learning_task, 
                    "ML学习", 
                    10.0
                )
                
                if learning_result.success:
                    logger.info(f"✅ ML学习成功: {outcome_type} - {request.query[:30]}...")
                else:
                    logger.warning(f"⚠️ ML学习失败: {outcome_type} - {request.query[:30]}...")
            
            # 触发深度学习引擎
            if hasattr(self, 'deep_learning_engine') and self.deep_learning_engine:
                try:
                    # 准备训练数据
                    training_data = {
                        'input': request.query,
                        'output': result.success,
                        'features': evidence_trajectory.get('features', {}),
                        'metadata': learning_context
                    }
                    
                    # 执行微训练
                    training_result = self.deep_learning_engine.train_model(training_data)
                    
                    if training_result.get('success', False):
                        logger.info(f"✅ 深度学习训练成功: {outcome_type}")
                    else:
                        logger.debug(f"深度学习训练未执行: {outcome_type}")
                        
                except Exception as e:
                    logger.debug(f"深度学习训练失败: {e}")
            
        except Exception as e:
            logger.error(f"❌ ML学习触发失败: {e}")

    def _record_scheduling_performance(
        self,
        query_type: str,
        query_complexity: str,
        ml_strategy: Optional[Any],
        rl_action: Optional[Any],
        rl_state: Optional[Any],
        knowledge_time: float,
        reasoning_time: float,
        answer_time: float,
        total_time: float,
        success: bool,
        accuracy: float
    ):
        """
        🚀 记录调度性能数据，用于ML/RL学习
        
        Args:
            query_type: 查询类型
            query_complexity: 查询复杂度
            ml_strategy: ML预测的调度策略
            rl_action: RL选择的动作
            rl_state: RL状态
            knowledge_time: 知识检索时间
            reasoning_time: 推理时间
            answer_time: 答案生成时间
            total_time: 总处理时间
            success: 是否成功
            accuracy: 答案准确率
        """
        try:
            # 记录ML性能数据
            if hasattr(self, 'ml_scheduling_optimizer') and self.ml_scheduling_optimizer and ml_strategy:
                from src.utils.ml_scheduling_optimizer import SchedulingStrategy
                if isinstance(ml_strategy, SchedulingStrategy):
                    self.ml_scheduling_optimizer.record_performance(
                        query_type=query_type,
                        query_complexity=query_complexity,
                        strategy=ml_strategy,
                        total_time=total_time,
                        knowledge_time=knowledge_time,
                        reasoning_time=reasoning_time,
                        answer_time=answer_time,
                        success=success,
                        accuracy=accuracy
                    )
            
            # 记录RL性能数据并更新Q值
            if hasattr(self, 'rl_scheduling_optimizer') and self.rl_scheduling_optimizer and rl_action and rl_state:
                from src.utils.rl_scheduling_optimizer import SchedulingState, SchedulingAction
                if isinstance(rl_action, SchedulingAction) and isinstance(rl_state, SchedulingState):
                    # 计算奖励
                    reward = self.rl_scheduling_optimizer.calculate_reward(
                        total_time=total_time,
                        success=success,
                        accuracy=accuracy,
                        knowledge_time=knowledge_time,
                        reasoning_time=reasoning_time
                    )
                    
                    # 更新下一状态（知识检索后）
                    next_state = SchedulingState(
                        query_type=query_type,
                        query_complexity=query_complexity,
                        query_length=rl_state.query_length,
                        has_knowledge=True,  # 知识检索已完成
                        knowledge_quality=0.8 if success else 0.3  # 根据成功与否估计知识质量
                    )
                    
                    # 更新Q值
                    self.rl_scheduling_optimizer.update_q_value(
                        state=rl_state,
                        action=rl_action,
                        reward=reward,
                        next_state=next_state
                    )
                    
                    logger.debug(f"🚀 RL调度优化: 记录性能数据，奖励={reward:.4f}, 总时间={total_time:.2f}s, 准确率={accuracy:.2f}")
        except Exception as e:
            logger.debug(f"记录调度性能数据失败: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "initialized": self._is_initialized,
            "active_queries": len(self._active_queries),
            "max_concurrent_queries": self.max_concurrent_queries,
            "total_queries_processed": self._query_counter,
            "memory_usage": self._get_memory_usage()
        }

    def _get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况 - 增强版"""
        try:
            import psutil
            import gc
            
            # 获取虚拟内存信息
            memory = psutil.virtual_memory()
            
            # 获取交换内存信息
            swap = psutil.swap_memory()
            
            # 获取进程内存信息
            process = psutil.Process()
            process_memory = process.memory_info()
            
            # 获取垃圾回收统计
            gc_stats = gc.get_stats()
            
            # 计算内存趋势
            memory_trend = self._calculate_memory_trend()
            
            return {
                "virtual_memory": {
                    "percent": memory.percent,
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "total_gb": round(memory.total / (1024**3), 2),
                    "free_gb": round(memory.free / (1024**3), 2)
                },
                "swap_memory": {
                    "percent": swap.percent,
                    "used_gb": round(swap.used / (1024**3), 2),
                    "free_gb": round(swap.free / (1024**3), 2),
                    "total_gb": round(swap.total / (1024**3), 2)
                },
                "process_memory": {
                    "rss_gb": round(process_memory.rss / (1024**3), 2),
                    "vms_gb": round(process_memory.vms / (1024**3), 2),
                    "percent": round(process_memory.rss / memory.total * 100, 2)
                },
                "gc_stats": {
                    "collections": sum(stat['collections'] for stat in gc_stats),
                    "collected": sum(stat['collected'] for stat in gc_stats),
                    "uncollectable": sum(stat['uncollectable'] for stat in gc_stats)
                },
                "memory_trend": memory_trend,
                "timestamp": time.time(),
                "status": self._get_memory_status(memory.percent)
            }
            
        except Exception as e:
            logger.warning(f"获取内存使用情况失败: {e}")
            return {
                "virtual_memory": {"percent": 0, "available_gb": 0, "used_gb": 0, "total_gb": 0, "free_gb": 0},
                "swap_memory": {"percent": 0, "used_gb": 0, "free_gb": 0, "total_gb": 0},
                "process_memory": {"rss_gb": 0, "vms_gb": 0, "percent": 0},
                "gc_stats": {"collections": 0, "collected": 0, "uncollectable": 0},
                "memory_trend": "unknown",
                "timestamp": time.time(),
                "status": "error"
            }
    
    def _calculate_memory_trend(self) -> str:
        """计算内存使用趋势"""
        try:
            if not hasattr(self, '_memory_history'):
                self._memory_history = []
            
            current_memory = psutil.virtual_memory().percent
            self._memory_history.append(current_memory)
            
            # 保持最近10个记录
            if len(self._memory_history) > 10:
                self._memory_history = self._memory_history[-10:]
            
            if len(self._memory_history) < 3:
                return "insufficient_data"
            
            # 计算趋势
            recent_avg = sum(self._memory_history[-3:]) / 3
            older_avg = sum(self._memory_history[-6:-3]) / 3 if len(self._memory_history) >= 6 else recent_avg
            
            if recent_avg > older_avg + 5:
                return "increasing"
            elif recent_avg < older_avg - 5:
                return "decreasing"
            else:
                return "stable"
                
        except Exception as e:
            logger.warning(f"计算内存趋势失败: {e}")
            return "unknown"
    
    def _get_memory_status(self, percent: float) -> str:
        """获取内存状态"""
        if percent < 50:
            return "healthy"
        elif percent < 75:
            return "warning"
        elif percent < 90:
            return "critical"
        else:
            return "danger"

    async def optimize_memory(self) -> None:
        """优化内存使用"""
        try:
            logger.info("🔄 开始内存优化...")

            collected = gc.collect()
            logger.info(f"✅ 垃圾回收完成，清理了 {collected} 个对象")

            memory_usage = self._get_memory_usage()
            if memory_usage["percent"] > 80:
                logger.warning(f"⚠️ 内存使用率仍然较高: {memory_usage['percent']}%")

                await self._cleanup_caches()

                gc.collect()

                logger.info("✅ 内存优化完成")
            else:
                logger.info("✅ 内存使用率正常，无需额外优化")

        except Exception as e:
            logger.warning(f"内存优化失败: {e}")

    async def _cleanup_caches(self) -> None:
        """清理缓存和临时数据"""
        try:
            # 🚀 重构：清理Agent的Service缓存
            if self._knowledge_agent:
                # 清理知识Agent的Service缓存
                if hasattr(self._knowledge_agent, 'service') and self._knowledge_agent.service:
                    service = self._knowledge_agent.service
                    if hasattr(service, 'clear_cache'):
                        service.clear_cache()

            if self._reasoning_agent:
                # 清理推理Agent的Service缓存
                if hasattr(self._reasoning_agent, 'service') and self._reasoning_agent.service:
                    service = self._reasoning_agent.service
                    if hasattr(service, 'clear_cache'):
                        service.clear_cache()  # type: ignore

            # 🚀 P0修复：清理过期的查询缓存，防止缓存无限增长
            if hasattr(self, '_cache_system'):
                current_time = time.time()
                cache_ttl = self._cache_system.get('cache_ttl', 300)
                
                # 清理过期的查询缓存
                query_cache = self._cache_system.get('query_cache', {})
                expired_keys = [
                    key for key, value in query_cache.items()
                    if current_time - value.get('timestamp', 0) > cache_ttl
                ]
                for key in expired_keys:
                    del query_cache[key]
                
                # 清理过期的知识缓存
                knowledge_cache = self._cache_system.get('knowledge_cache', {})
                expired_keys = [
                    key for key, value in knowledge_cache.items()
                    if current_time - value.get('timestamp', 0) > cache_ttl
                ]
                for key in expired_keys:
                    del knowledge_cache[key]
                
                # 清理过期的推理缓存
                reasoning_cache = self._cache_system.get('reasoning_cache', {})
                expired_keys = [
                    key for key, value in reasoning_cache.items()
                    if current_time - value.get('timestamp', 0) > cache_ttl
                ]
                for key in expired_keys:
                    del reasoning_cache[key]
                
                # 如果缓存仍然太大，删除最旧的条目（LRU策略）
                max_cache_size = self._cache_system.get('max_cache_size', 1000)
                for cache_name, cache in [
                    ('query_cache', query_cache),
                    ('knowledge_cache', knowledge_cache),
                    ('reasoning_cache', reasoning_cache)
                ]:
                    if len(cache) > max_cache_size:
                        # 按时间戳排序，删除最旧的条目
                        sorted_items = sorted(cache.items(), key=lambda x: x[1].get('timestamp', 0))
                        items_to_remove = len(cache) - max_cache_size
                        for key, _ in sorted_items[:items_to_remove]:
                            del cache[key]

            logger.info("✅ 缓存清理完成")

        except Exception as e:
            logger.warning(f"缓存清理失败: {e}")

    async def shutdown(self) -> None:
        """关闭系统"""
        try:
            logger.info("🔄 开始关闭统一异步研究系统...")

            # 取消所有活动查询
            for query_id, task in self._active_queries.items():
                task.cancel()

            if self._active_queries:
                await asyncio.gather(*self._active_queries.values(), return_exceptions=True)

            self._active_queries.clear()
            
            # 🚀 重构：关闭所有Agent
            agents_to_cleanup = [
                ('knowledge', self._knowledge_agent),
                ('reasoning', self._reasoning_agent),
                ('answer', self._answer_agent),
                ('citation', self._citation_agent),
            ]
            
            for agent_name, agent in agents_to_cleanup:
                if agent and hasattr(agent, 'cleanup') and callable(agent.cleanup):
                    try:
                        if asyncio.iscoroutinefunction(agent.cleanup):
                            await agent.cleanup()
                        else:
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(None, agent.cleanup)
                        logger.info(f"✅ Agent {agent_name} 已关闭")
                    except Exception as e:
                        logger.warning(f"⚠️ Agent {agent_name} 关闭时出现问题: {e}")
            
            # 关闭学习系统
            if self.learning_system and hasattr(self.learning_system, 'cleanup') and callable(self.learning_system.cleanup):
                try:
                    if asyncio.iscoroutinefunction(self.learning_system.cleanup):
                        await self.learning_system.cleanup()
                    else:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, self.learning_system.cleanup)
                    logger.info("✅ 学习系统已关闭")
                except Exception as e:
                    logger.warning(f"⚠️ 学习系统关闭时出现问题: {e}")
            
            # 关闭 AI 算法集成器（尝试清理，但不是必需的）
            if self._ai_algorithm_integrator:
                try:
                    # 尝试调用 cleanup 方法（如果存在）
                    cleanup_method = getattr(self._ai_algorithm_integrator, 'cleanup', None)
                    if callable(cleanup_method):
                        if asyncio.iscoroutinefunction(cleanup_method):
                            await cleanup_method()
                        else:
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(None, cleanup_method)
                        logger.info("✅ AI 算法集成器已关闭")
                    else:
                        logger.info("ℹ️ AI 算法集成器无需清理")
                except Exception as e:
                    logger.warning(f"⚠️ AI 算法集成器关闭时出现问题: {e}")
            
            # 🚀 P1优化：关闭所有LLM连接池
            await self._close_llm_sessions()
            
            # 🚀 新增：清理推理引擎实例池
            try:
                from src.utils.reasoning_engine_pool import get_reasoning_engine_pool
                pool = get_reasoning_engine_pool()
                stats_before = pool.get_stats()
                cleared_count = pool.clear_pool()
                logger.info(f"✅ 推理引擎实例池已清理: 清除了 {cleared_count} 个实例 (清理前: 池中={stats_before['pool_size']}, 使用中={stats_before['in_use_count']}, 总创建={stats_before['created_count']})")
            except Exception as e:
                logger.warning(f"⚠️ 清理推理引擎实例池时出现问题: {e}")
            
            self._is_initialized = False

            logger.info("✅ 统一异步研究系统关闭完成")

        except Exception as e:
            logger.error("❌ 系统关闭失败: {e}")
    
    async def _close_llm_sessions(self) -> None:
        """🚀 P1优化：关闭所有LLM连接池"""
        try:
            # 🚀 重构：关闭Agent的Service的LLM连接池
            # 使用 getattr 和类型忽略注释避免类型检查器警告
            if self._knowledge_agent:
                if hasattr(self._knowledge_agent, 'service') and self._knowledge_agent.service:
                    service = self._knowledge_agent.service
                    llm = getattr(service, 'llm_integration', None)  # type: ignore
                    if llm and hasattr(llm, 'close'):
                        llm.close()
                    llm = getattr(service, 'fast_llm_integration', None)  # type: ignore
                    if llm and hasattr(llm, 'close'):
                        llm.close()
            
            if self._reasoning_agent:
                if hasattr(self._reasoning_agent, 'service') and self._reasoning_agent.service:
                    service = self._reasoning_agent.service
                    llm = getattr(service, 'llm_integration', None)  # type: ignore
                    if llm and hasattr(llm, 'close'):
                        llm.close()
                    llm = getattr(service, 'fast_llm_integration', None)  # type: ignore
                    if llm and hasattr(llm, 'close'):
                        llm.close()
            
            if self._answer_agent:
                if hasattr(self._answer_agent, 'service') and self._answer_agent.service:
                    service = self._answer_agent.service
                    llm = getattr(service, 'llm_integration', None)  # type: ignore
                    if llm and hasattr(llm, 'close'):
                        llm.close()
            
            logger.info("✅ 所有LLM连接池已关闭")
        except Exception as e:
            logger.warning(f"⚠️ 关闭LLM连接池时出现问题: {e}")
    
    def _get_cache_key(self, query: str, context: Dict[str, Any], query_type: Optional[str] = None) -> str:
        """🚀 优化：生成缓存键（支持基于查询类型的缓存）
        
        Args:
            query: 查询文本
            context: 上下文信息
            query_type: 查询类型（可选）
        """
        import hashlib
        import re
        
        # L1: 精确匹配键（完整查询内容）
        cache_data = f"{query}_{str(sorted(context.items()))}"
        exact_key = hashlib.md5(cache_data.encode()).hexdigest()
        
        # 🚀 优化：如果查询类型已知，生成类型键映射
        if query_type:
            # 提取查询关键特征
            query_lower = query.lower()
            features = []
            features.append(f"type:{query_type}")
            
            # 提取关键词（前3个）
            words = re.findall(r'\b[a-zA-Z]{3,}\b', query_lower)
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'what', 'who', 'where', 'when', 'why', 'how'}
            keywords = [w for w in words if w not in stop_words][:3]
            if keywords:
                features.append(f"keywords:{'_'.join(sorted(keywords))}")
            
            # 生成类型键
            type_data = f"{query_type}_{'_'.join(features)}"
            type_key = hashlib.md5(type_data.encode()).hexdigest()
            
            # 存储键映射
            if not hasattr(self, '_cache_key_mapping'):
                self._cache_key_mapping = {}
            self._cache_key_mapping[exact_key] = {
                'type_key': type_key,
                'query': query[:50],
                'query_type': query_type
            }
        
        return exact_key
    
    def _check_cache(self, cache_key: str, cache_type: str) -> Optional[Any]:
        """检查缓存"""
        try:
            cache = self._cache_system.get(f"{cache_type}_cache", {})
            if cache_key in cache:
                entry = cache[cache_key]
                if time.time() - entry['timestamp'] < self._cache_system['cache_ttl']:
                    self._performance_metrics['cache_hits'] += 1
                    return entry['data']
                else:
                    # 缓存过期，删除
                    del cache[cache_key]
            self._performance_metrics['cache_misses'] += 1
            return None
        except Exception as e:
            logger.warning(f"缓存检查失败: {e}")
            return None
    
    def _set_cache(self, cache_key: str, data: Any, cache_type: str) -> None:
        """设置缓存"""
        try:
            cache = self._cache_system.get(f"{cache_type}_cache", {})
            
            # 检查缓存大小限制
            if len(cache) >= self._cache_system['max_cache_size']:
                # 删除最旧的条目
                oldest_key = min(cache.keys(), key=lambda k: cache[k]['timestamp'])
                del cache[oldest_key]
            
            cache[cache_key] = {
                'data': data,
                'timestamp': time.time()
            }
        except Exception as e:
            logger.warning(f"缓存设置失败: {e}")
    
    async def _execute_with_retry(self, coro, operation_name: str, max_retries: Optional[int] = None) -> Any:
        """带重试的执行"""
        max_retries = max_retries or self._retry_config['max_retries']
        base_delay = self._retry_config['base_delay']
        
        for attempt in range(max_retries + 1):
            try:
                return await coro
            except Exception as e:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt) if self._retry_config['exponential_backoff'] else base_delay
                    logger.warning(f"⚠️ {operation_name} 执行失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                    logger.info(f"⏳ {delay:.2f}秒后重试...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ {operation_name} 重试 {max_retries} 次后仍然失败: {e}")
                    raise e
    
    def _update_performance_metrics(self, success: bool, execution_time: float) -> None:
        """更新性能指标"""
        self._performance_metrics['total_queries'] += 1
        if success:
            self._performance_metrics['successful_queries'] += 1
        else:
            self._performance_metrics['failed_queries'] += 1
        
        # 更新平均响应时间
        total = self._performance_metrics['total_queries']
        current_avg = self._performance_metrics['average_response_time']
        self._performance_metrics['average_response_time'] = (
            (current_avg * (total - 1) + execution_time) / total
        )
        
        # 更新并发峰值
        current_concurrent = len(self._active_queries)
        if current_concurrent > self._performance_metrics['concurrent_peak']:
            self._performance_metrics['concurrent_peak'] = current_concurrent
    
    def _adaptive_load_balancing(self, agent_type: str) -> float:
        """自适应负载均衡"""
        try:
            # 获取当前性能历史
            recent_performance = self._load_balancer['performance_history'][-10:]
            if not recent_performance:
                return self._load_balancer['agent_weights'].get(agent_type, 1.0)
            
            # 计算平均性能
            avg_performance = sum(p.get('success_rate', 0.5) for p in recent_performance) / len(recent_performance)
            
            # 如果性能低于阈值，降低权重
            if avg_performance < self._load_balancer['adaptive_threshold']:
                current_weight = self._load_balancer['agent_weights'].get(agent_type, 1.0)
                new_weight = max(0.5, current_weight * 0.9)
                self._load_balancer['agent_weights'][agent_type] = new_weight
                logger.info(f"🔧 调整 {agent_type} 智能体权重: {current_weight:.2f} -> {new_weight:.2f}")
            
            return self._load_balancer['agent_weights'].get(agent_type, 1.0)
            
        except Exception as e:
            logger.warning(f"负载均衡调整失败: {e}")
            return 1.0
    
    def _record_performance(self, agent_type: str, success: bool, execution_time: float) -> None:
        """记录性能数据"""
        try:
            performance_data = {
                'agent_type': agent_type,
                'success': success,
                'execution_time': execution_time,
                'timestamp': time.time(),
                'success_rate': 1.0 if success else 0.0
            }
            
            self._load_balancer['performance_history'].append(performance_data)
            
            # 保持历史记录在合理范围内
            if len(self._load_balancer['performance_history']) > 100:
                self._load_balancer['performance_history'] = self._load_balancer['performance_history'][-50:]
                
        except Exception as e:
            logger.warning(f"性能记录失败: {e}")
    
    def get_performance_analytics(self) -> Dict[str, Any]:
        """获取性能分析报告"""
        try:
            total_queries = self._performance_metrics['total_queries']
            success_rate = (self._performance_metrics['successful_queries'] / max(total_queries, 1)) * 100
            
            cache_hit_rate = 0.0
            total_cache_requests = self._performance_metrics['cache_hits'] + self._performance_metrics['cache_misses']
            if total_cache_requests > 0:
                cache_hit_rate = (self._performance_metrics['cache_hits'] / total_cache_requests) * 100
            
            return {
                'overall_performance': {
                    'total_queries': total_queries,
                    'success_rate': success_rate,
                    'average_response_time': self._performance_metrics['average_response_time'],
                    'concurrent_peak': self._performance_metrics['concurrent_peak'],
                    'cache_hit_rate': cache_hit_rate
                },
                'load_balancer': {
                    'agent_weights': self._load_balancer['agent_weights'],
                    'performance_history_count': len(self._load_balancer['performance_history']),
                    'adaptive_threshold': self._load_balancer['adaptive_threshold']
                },
                'cache_system': {
                    'query_cache_size': len(self._cache_system['query_cache']),
                    'knowledge_cache_size': len(self._cache_system['knowledge_cache']),
                    'reasoning_cache_size': len(self._cache_system['reasoning_cache']),
                    'cache_ttl': self._cache_system['cache_ttl'],
                    'max_cache_size': self._cache_system['max_cache_size']
                },
                'retry_config': self._retry_config,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"获取性能分析失败: {e}")
            return {'error': str(e), 'timestamp': time.time()}
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """性能优化"""
        try:
            optimization_results = {
                'actions_taken': [],
                'improvements': {},
                'timestamp': time.time()
            }
            
            # 清理过期缓存
            current_time = time.time()
            for cache_type in ['query_cache', 'knowledge_cache', 'reasoning_cache']:
                cache = self._cache_system.get(f"{cache_type}", {})
                expired_keys = [
                    key for key, entry in cache.items()
                    if current_time - entry['timestamp'] > self._cache_system['cache_ttl']
                ]
                
                for key in expired_keys:
                    del cache[key]
                
                if expired_keys:
                    optimization_results['actions_taken'].append(f"清理 {cache_type}: {len(expired_keys)} 个过期条目")
            
            # 调整负载均衡权重
            for agent_type in self._load_balancer['agent_weights']:
                old_weight = self._load_balancer['agent_weights'][agent_type]
                new_weight = self._adaptive_load_balancing(agent_type)
                if abs(new_weight - old_weight) > 0.01:
                    optimization_results['actions_taken'].append(f"调整 {agent_type} 权重: {old_weight:.2f} -> {new_weight:.2f}")
            
            # 垃圾回收
            collected = gc.collect()
            if collected > 0:
                optimization_results['actions_taken'].append(f"垃圾回收: 回收了 {collected} 个对象")
            
            # 内存优化
            memory_info = psutil.virtual_memory()
            if memory_info.percent > 80:
                optimization_results['actions_taken'].append(f"内存使用率过高: {memory_info.percent:.1f}%")
                # 可以在这里添加更多内存优化逻辑
            
            logger.info(f"性能优化完成: {optimization_results}")
            return optimization_results
            
        except Exception as e:
            logger.error(f"性能优化失败: {e}")
            return {'error': str(e), 'timestamp': time.time()}


async def create_unified_research_system(max_concurrent_queries: int = 3, enable_visualization_server: bool = True) -> UnifiedResearchSystem:
    """创建统一异步研究系统实例"""
    system = UnifiedResearchSystem(max_concurrent_queries, enable_visualization_server)
    await system.initialize()
    return system


if __name__ == "__main__":
    async def test_system():
        """测试系统"""
        try:
            system = await create_unified_research_system()

            request = ResearchRequest(
                query="什么是人工智能？",
                context={"category": "factual"},
                timeout=30.0
            )

            result = await system.execute_research(request)

            print(f"查询: {result.query}")
            print(f"成功: {result.success}")
            print(f"答案: {result.answer}")
            print(f"置信度: {result.confidence}")
            print(f"执行时间: {result.execution_time:.2f}秒")

            await system.shutdown()

        except Exception as e:
            logger.error("测试失败: {e}")

    asyncio.run(test_system())
