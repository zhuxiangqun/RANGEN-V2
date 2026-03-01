"""
查询编排器 - 实现推理引导的检索策略选择

基于RAG_OPTIMIZATION_PLAN.md设计，支持根据DDL β参数动态选择检索策略
包括Simple、HyDE、CoT-RAG等策略的统一编排
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional

from .base_strategy import BaseRetrievalStrategy, RetrievalResult, strategy_registry
from .hyde_strategy import HyDEStrategy

logger = logging.getLogger(__name__)


class QueryOrchestrator:
    """
    查询编排器 - 实现推理引导的检索
    
    根据DDL β参数动态选择检索策略：
    β < 0.3: Simple (直觉/记忆)
    β < 1.3: HyDE (假设/联想)
    β >= 1.3: CoT-RAG (辩证/推理)
    """
    
    def __init__(
        self,
        llm_service,
        knowledge_service,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化查询编排器
        
        Args:
            llm_service: LLM服务接口
            knowledge_service: 知识检索服务
            config: 配置参数
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.llm_service = llm_service
        self.knowledge_service = knowledge_service
        self.config = config or {}
        
        # 初始化策略
        self.strategies = {}
        self._initialize_strategies()
        
        # 阈值配置
        self.simple_to_hyde_threshold = self.config.get('simple_to_hyde_threshold', 0.3)
        self.hyde_to_cot_threshold = self.config.get('hyde_to_cot_threshold', 1.3)
        
        # 默认策略配置
        self.default_strategy = self.config.get('default_strategy', 'simple')
        self.enable_strategy_selection = self.config.get('enable_strategy_selection', True)
        
        self.logger.info("查询编排器初始化完成")
    
    def _initialize_strategies(self):
        """初始化所有可用的检索策略"""
        try:
            # 注册HyDE策略
            hyde_config = self.config.get('hyde', {})
            hyde_strategy = HyDEStrategy(
                llm_service=self.llm_service,
                knowledge_service=self.knowledge_service,
                config=hyde_config
            )
            self.strategies['hyde'] = hyde_strategy
            strategy_registry.register('hyde', hyde_strategy)
            
            # 注册Simple策略（基础检索）
            simple_strategy = SimpleStrategy(
                knowledge_service=self.knowledge_service,
                config=self.config.get('simple', {})
            )
            self.strategies['simple'] = simple_strategy
            strategy_registry.register('simple', simple_strategy)
            
            self.logger.info(f"已初始化策略: {list(self.strategies.keys())}")
            
        except Exception as e:
            self.logger.error(f"策略初始化失败: {e}")
    
    async def orchestrate_retrieval(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        beta: Optional[float] = None
    ) -> RetrievalResult:
        """
        根据DDL β参数编排检索过程
        
        Args:
            query: 用户查询
            context: 上下文信息
            beta: DDL β参数（如果不提供，尝试从context获取）
            
        Returns:
            检索结果
        """
        start_time = time.time()
        context = context or {}
        
        try:
            self.logger.info(f"开始编排检索: {query[:50]}...")
            
            # 1. 策略选择
            if beta is None:
                beta = context.get('beta', 0.5)
            
            if not self.enable_strategy_selection:
                strategy_name = self.default_strategy
                self.logger.info(f"策略选择已禁用，使用默认策略: {strategy_name}")
            else:
                strategy_name = self._select_strategy_by_beta(beta)
                self.logger.info(f"根据Beta={beta}选择策略: {strategy_name}")
            
            # 2. 获取策略实例
            strategy = self.strategies.get(strategy_name)
            if not strategy or not strategy.is_enabled():
                self.logger.warning(f"策略{strategy_name}不可用，回退到默认策略")
                strategy_name = self.default_strategy
                strategy = self.strategies.get(strategy_name)
            
            if not strategy:
                raise ValueError(f"无可用的检索策略: {strategy_name}")
            
            # 3. 准备检索上下文
            enhanced_context = context.copy()
            enhanced_context.update({
                'orchestrator': 'query_orchestrator',
                'selected_strategy': strategy_name,
                'beta': beta,
                'timestamp': time.time()
            })
            
            # 4. 执行策略
            self.logger.info(f"执行检索策略: {strategy_name}")
            result = await strategy.execute(query, enhanced_context)
            
            # 5. 增强结果
            if result.success:
                result.metadata['orchestrator'] = {
                    'strategy_selected': strategy_name,
                    'beta_used': beta,
                    'selection_thresholds': {
                        'simple_to_hyde': self.simple_to_hyde_threshold,
                        'hyde_to_cot': self.hyde_to_cot_threshold
                    },
                    'total_orchestration_time': time.time() - start_time
                }
            
            self.logger.info(f"检索编排完成: {strategy_name}, 成功={result.success}, 文档数={len(result.documents)}")
            return result
            
        except Exception as e:
            self.logger.error(f"检索编排失败: {e}")
            return RetrievalResult.from_error('orchestrator', str(e))
    
    def _select_strategy_by_beta(self, beta: float) -> str:
        """根据β值选择策略"""
        if beta < self.simple_to_hyde_threshold:
            return "simple"
        elif beta < self.hyde_to_cot_threshold:
            return "hyde"
        else:
            return "cot_rag"  # 暂时回退到hyde，直到CoT-RAG实现
    
    def get_available_strategies(self) -> List[str]:
        """获取可用的策略列表"""
        return [
            name for name, strategy in self.strategies.items() 
            if strategy.is_enabled()
        ]
    
    def update_strategy_config(self, strategy_name: str, new_config: Dict[str, Any]) -> bool:
        """更新策略配置"""
        strategy = self.strategies.get(strategy_name)
        if strategy:
            strategy.update_config(new_config)
            self.logger.info(f"已更新策略{strategy_name}的配置")
            return True
        else:
            self.logger.warning(f"策略不存在: {strategy_name}")
            return False
    
    def enable_strategy(self, strategy_name: str) -> bool:
        """启用策略"""
        strategy = self.strategies.get(strategy_name)
        if strategy:
            strategy.enable()
            self.logger.info(f"已启用策略: {strategy_name}")
            return True
        else:
            self.logger.warning(f"策略不存在: {strategy_name}")
            return False
    
    def disable_strategy(self, strategy_name: str) -> bool:
        """禁用策略"""
        strategy = self.strategies.get(strategy_name)
        if strategy and strategy_name != self.default_strategy:
            strategy.disable()
            self.logger.info(f"已禁用策略: {strategy_name}")
            return True
        else:
            self.logger.warning(f"无法禁用策略: {strategy_name} (不存在或为默认策略)")
            return False
    
    def get_orchestrator_info(self) -> Dict[str, Any]:
        """获取编排器信息"""
        return {
            "name": "QueryOrchestrator",
            "description": "查询编排器 - 实现推理引导的检索策略选择",
            "version": "1.0.0",
            "strategies": {
                name: strategy.get_strategy_info() if hasattr(strategy, 'get_strategy_info') 
                else {"name": name, "enabled": strategy.is_enabled()}
                for name, strategy in self.strategies.items()
            },
            "thresholds": {
                "simple_to_hyde": self.simple_to_hyde_threshold,
                "hyde_to_cot": self.hyde_to_cot_threshold
            },
            "config": {
                "default_strategy": self.default_strategy,
                "enable_strategy_selection": self.enable_strategy_selection
            }
        }


class SimpleStrategy(BaseRetrievalStrategy):
    """
    简单检索策略 - 基础向量搜索
    
    作为基线策略，提供最基本的检索功能
    """
    
    def __init__(self, knowledge_service, config: Optional[Dict[str, Any]] = None):
        """
        初始化简单策略
        
        Args:
            knowledge_service: 知识检索服务
            config: 配置参数
        """
        super().__init__(name="simple", config=config)
        self.kms = knowledge_service
        self.top_k = self.config.get('top_k', 5)
        self.use_rerank = self.config.get('use_rerank', True)
    
    async def execute(self, query: str, context: Dict[str, Any]) -> RetrievalResult:
        """
        执行简单检索
        
        Args:
            query: 查询字符串
            context: 上下文信息
            
        Returns:
            检索结果
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"执行简单检索: {query[:50]}...")
            
            # 使用基础检索接口
            if hasattr(self.kms, 'search_vector'):
                search_results = await self.kms.search_vector(query, top_k=self.top_k)
            else:
                search_results = self.kms.query_knowledge(
                    query=query,
                    top_k=self.top_k,
                    use_rerank=self.use_rerank
                )
            
            # 标准化结果格式
            if isinstance(search_results, list):
                documents = search_results
            elif isinstance(search_results, dict) and "documents" in search_results:
                documents = search_results["documents"]
            else:
                documents = []
            
            execution_time = time.time() - start_time
            
            return RetrievalResult(
                documents=documents,
                strategy_name=self.name,
                execution_time=execution_time,
                metadata={
                    "original_query": query,
                    "top_k": self.top_k,
                    "use_rerank": self.use_rerank
                },
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"简单检索失败: {e}")
            return RetrievalResult.from_error("simple", str(e))


# 便捷函数
def create_query_orchestrator(
    llm_service,
    knowledge_service,
    config: Optional[Dict[str, Any]] = None
) -> QueryOrchestrator:
    """
    创建查询编排器实例
    
    Args:
        llm_service: LLM服务
        knowledge_service: 知识检索服务
        config: 配置参数
        
    Returns:
        查询编排器实例
    """
    return QueryOrchestrator(llm_service, knowledge_service, config)