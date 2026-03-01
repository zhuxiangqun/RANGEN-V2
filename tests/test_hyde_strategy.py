"""
HyDE策略测试

测试Hypothetical Document Embeddings策略的功能和集成
包括基础功能、配置、错误处理等场景
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import time

from src.core.reasoning.retrieval_strategies.hyde_strategy import HyDEStrategy
from src.core.reasoning.retrieval_strategies.query_orchestrator import QueryOrchestrator
from src.core.reasoning.retrieval_strategies.base_strategy import RetrievalResult


class TestHyDEStrategy:
    """HyDE策略测试类"""
    
    @pytest.fixture
    def mock_llm_service(self):
        """模拟LLM服务"""
        mock_llm = Mock()
        mock_llm.generate = AsyncMock(return_value="这是一个假设性答案文档，包含关于量子计算的详细信息。")
        mock_llm.logger = Mock()
        return mock_llm
    
    @pytest.fixture
    def mock_knowledge_service(self):
        """模拟知识检索服务"""
        mock_kms = Mock()
        mock_kms.query_knowledge = AsyncMock(return_value=[
            {
                "id": "doc1",
                "content": "量子计算是利用量子力学原理进行信息处理的新型计算模式。",
                "source": "wikipedia",
                "score": 0.95
            },
            {
                "id": "doc2", 
                "content": "量子比特是量子计算的基本信息单元，可以同时处于0和1的叠加态。",
                "source": "science_journal",
                "score": 0.87
            }
        ])
        mock_kms.search_vector = AsyncMock(return_value=[
            {
                "id": "doc1",
                "content": "量子计算是利用量子力学原理进行信息处理的新型计算模式。",
                "source": "wikipedia",
                "score": 0.95
            }
        ])
        return mock_kms
    
    @pytest.fixture
    def hyde_strategy(self, mock_llm_service, mock_knowledge_service):
        """创建HyDE策略实例"""
        config = {
            "max_hypothetical_tokens": 300,
            "temperature": 0.3,
            "top_k": 5,
            "force_rerank": True
        }
        return HyDEStrategy(
            llm_service=mock_llm_service,
            knowledge_service=mock_knowledge_service,
            config=config
        )
    
    @pytest.mark.asyncio
    async def test_hyde_strategy_initialization(self, mock_llm_service, mock_knowledge_service):
        """测试HyDE策略初始化"""
        config = {
            "max_hypothetical_tokens": 200,
            "temperature": 0.5
        }
        
        strategy = HyDEStrategy(
            llm_service=mock_llm_service,
            knowledge_service=mock_knowledge_service,
            config=config
        )
        
        assert strategy.name == "hyde"
        assert strategy.max_hypothetical_tokens == 200
        assert strategy.temperature == 0.5
        assert strategy.llm == mock_llm_service
        assert strategy.kms == mock_knowledge_service
        assert strategy.is_enabled() is True
    
    @pytest.mark.asyncio
    async def test_hyde_strategy_standard_mode(self, hyde_strategy, mock_llm_service, mock_knowledge_service):
        """测试标准模式HyDE执行"""
        query = "什么是量子计算？"
        context = {"beta": 0.8}
        
        result = await hyde_strategy.execute(query, context)
        
        assert result.success is True
        assert result.strategy_name == "hyde"
        assert len(result.documents) > 0
        assert result.metadata["original_query"] == query
        assert result.metadata["beta"] == 0.8
        assert result.metadata["mode"] == "standard"
        assert "hypothetical_document" in result.metadata
        
        # 验证LLM调用
        mock_llm_service.generate.assert_called_once()
        call_args = mock_llm_service.generate.call_args[1]
        assert call_args["temperature"] == 0.3
        # 标准模式使用一半token
        assert call_args["max_tokens"] == 150  # max_hypothetical_tokens // 2
    
    @pytest.mark.asyncio
    async def test_hyde_strategy_relation_enhanced_mode(self, hyde_strategy, mock_llm_service, mock_knowledge_service):
        """测试关系增强模式HyDE执行"""
        query = "量子计算如何影响现代密码学？"
        context = {"beta": 1.5}
        
        result = await hyde_strategy.execute(query, context)
        
        assert result.success is True
        assert result.metadata["mode"] == "relation_enhanced"
        assert result.metadata["context_expansion"] is True
        
        # 验证LLM调用参数
        call_args = mock_llm_service.generate.call_args[1]
        assert call_args["max_tokens"] == 300  # 关系增强模式使用更多token
    
    @pytest.mark.asyncio
    async def test_hyde_strategy_with_phi3_context(self, hyde_strategy, mock_knowledge_service):
        """测试Phi-3预生成上下文集成"""
        query = "什么是量子计算？"
        phi3_generated = "预生成的量子计算假设文档"
        context = {
            "beta": 0.8,
            "hyde_context": {"phi3_generated": phi3_generated}
        }
        
        result = await hyde_strategy.execute(query, context)
        
        assert result.success is True
        assert result.metadata["hypothetical_document"] == phi3_generated
        
        # 验证没有调用LLM（因为使用了预生成文档）
        hyde_strategy.llm.generate.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_hyde_strategy_fallback_on_generation_failure(self, hyde_strategy, mock_llm_service, mock_knowledge_service):
        """测试假设文档生成失败时的回退机制"""
        # 模拟LLM生成失败
        mock_llm_service.generate.return_value = None
        
        query = "测试查询"
        context = {"beta": 0.8}
        
        result = await hyde_strategy.execute(query, context)
        
        # 应该回退到fallback检索
        assert result.success is True
        assert result.strategy_name == "hyde_fallback"
        assert result.metadata["fallback_reason"] == "hypothetical_document_generation_failed"
    
    @pytest.mark.asyncio
    async def test_hyde_strategy_error_handling(self, hyde_strategy, mock_llm_service, mock_knowledge_service):
        """测试错误处理"""
        # 模拟LLM异常，同时模拟KMS返回空列表（确保fallback也失败）
        mock_llm_service.generate.side_effect = Exception("LLM服务异常")
        mock_knowledge_service.query_knowledge.return_value = []
        
        query = "测试查询"
        context = {"beta": 0.8}
        
        result = await hyde_strategy.execute(query, context)
        
        print(f"Debug: result.success={result.success}, error_message={result.error_message}")
        assert result.success is False
        assert result.strategy_name == "hyde"
        assert "LLM服务异常" in result.error_message
    
    def test_hyde_strategy_enable_disable(self, hyde_strategy):
        """测试策略启用/禁用"""
        # 默认应该是启用的
        assert hyde_strategy.is_enabled() is True
        
        # 禁用策略
        hyde_strategy.disable()
        assert hyde_strategy.is_enabled() is False
        
        # 重新启用
        hyde_strategy.enable()
        assert hyde_strategy.is_enabled() is True
    
    def test_hyde_strategy_config_update(self, hyde_strategy):
        """测试配置更新"""
        new_config = {
            "temperature": 0.7,
            "top_k": 10,
            "custom_param": "test_value"
        }
        
        original_temp = hyde_strategy.temperature
        hyde_strategy.update_config(new_config)
        
        assert hyde_strategy.temperature == 0.7
        assert hyde_strategy.top_k == 10
        assert hyde_strategy.config["custom_param"] == "test_value"
        assert hyde_strategy.is_enabled() is True  # 配置更新不应影响启用状态
    
    def test_hyde_strategy_info(self, hyde_strategy):
        """测试策略信息获取"""
        info = hyde_strategy.get_strategy_info()
        
        assert info["name"] == "hyde"
        assert "Hypothetical Document Embeddings" in info["description"]
        assert "version" in info
        assert "capabilities" in info
        assert isinstance(info["capabilities"], list)
        assert "enabled" in info


class TestQueryOrchestrator:
    """查询编排器测试类"""
    
    @pytest.fixture
    def mock_llm_service(self):
        """模拟LLM服务"""
        mock_llm = Mock()
        mock_llm.generate = AsyncMock(return_value="假设性文档")
        mock_llm.logger = Mock()
        return mock_llm
    
    @pytest.fixture 
    def mock_knowledge_service(self):
        """模拟知识检索服务"""
        mock_kms = Mock()
        mock_kms.query_knowledge = AsyncMock(return_value=[
            {"id": "doc1", "content": "测试文档1", "score": 0.9},
            {"id": "doc2", "content": "测试文档2", "score": 0.8}
        ])
        mock_kms.search_vector = AsyncMock(return_value=[])
        return mock_kms
    
    @pytest.fixture
    def query_orchestrator(self, mock_llm_service, mock_knowledge_service):
        """创建查询编排器实例"""
        config = {
            "simple_to_hyde_threshold": 0.3,
            "hyde_to_cot_threshold": 1.3,
            "default_strategy": "simple",
            "hyde": {
                "enabled": True,
                "temperature": 0.3
            }
        }
        return QueryOrchestrator(
            llm_service=mock_llm_service,
            knowledge_service=mock_knowledge_service,
            config=config
        )
    
    @pytest.mark.asyncio
    async def test_orchestrator_strategy_selection_simple(self, query_orchestrator):
        """测试简单策略选择（beta < 0.3）"""
        result = await query_orchestrator.orchestrate_retrieval(
            query="测试查询",
            context={},
            beta=0.2
        )
        
        assert result.success is True
        assert result.metadata["orchestrator"]["strategy_selected"] == "simple"
        assert result.metadata["orchestrator"]["beta_used"] == 0.2
    
    @pytest.mark.asyncio
    async def test_orchestrator_strategy_selection_hyde(self, query_orchestrator):
        """测试HyDE策略选择（0.3 <= beta < 1.3）"""
        result = await query_orchestrator.orchestrate_retrieval(
            query="测试查询",
            context={},
            beta=0.8
        )
        
        assert result.success is True
        assert result.metadata["orchestrator"]["strategy_selected"] == "hyde"
    
    @pytest.mark.asyncio
    async def test_orchestrator_strategy_selection_cot(self, query_orchestrator):
        """测试CoT策略选择（beta >= 1.3，暂时回退到hyde）"""
        result = await query_orchestrator.orchestrate_retrieval(
            query="测试查询",
            context={},
            beta=1.5
        )
        
        assert result.success is True
        # 目前CoT未实现，会回退到simple策略（根据fallback逻辑）
        assert result.metadata["orchestrator"]["strategy_selected"] in ["hyde", "cot_rag", "simple"]
    
    @pytest.mark.asyncio
    async def test_orchestrator_disabled_strategy_selection(self, query_orchestrator):
        """测试禁用策略选择时使用默认策略"""
        query_orchestrator.enable_strategy_selection = False
        query_orchestrator.default_strategy = "simple"
        
        result = await query_orchestrator.orchestrate_retrieval(
            query="测试查询",
            context={},
            beta=1.5  # 高beta，但策略选择被禁用
        )
        
        assert result.success is True
        assert result.metadata["orchestrator"]["strategy_selected"] == "simple"
    
    def test_orchestrator_available_strategies(self, query_orchestrator):
        """测试获取可用策略列表"""
        strategies = query_orchestrator.get_available_strategies()
        
        assert "simple" in strategies
        assert "hyde" in strategies
        assert isinstance(strategies, list)
    
    def test_orchestrator_enable_disable_strategy(self, query_orchestrator):
        """测试策略启用/禁用"""
        # 禁用HyDE策略
        success = query_orchestrator.disable_strategy("hyde")
        assert success is True
        assert "hyde" not in query_orchestrator.get_available_strategies()
        
        # 重新启用
        success = query_orchestrator.enable_strategy("hyde")
        assert success is True
        assert "hyde" in query_orchestrator.get_available_strategies()
        
        # 禁用默认策略应该失败
        success = query_orchestrator.disable_strategy("simple")
        assert success is False
    
    def test_orchestrator_config_update(self, query_orchestrator):
        """测试策略配置更新"""
        new_config = {"temperature": 0.7}
        
        success = query_orchestrator.update_strategy_config("hyde", new_config)
        assert success is True
        
        # 验证配置已更新
        hyde_strategy = query_orchestrator.strategies["hyde"]
        assert hyde_strategy.temperature == 0.7
    
    def test_orchestrator_info(self, query_orchestrator):
        """测试编排器信息获取"""
        info = query_orchestrator.get_orchestrator_info()
        
        assert info["name"] == "QueryOrchestrator"
        assert "strategies" in info
        assert "thresholds" in info
        assert info["thresholds"]["simple_to_hyde"] == 0.3
        assert info["thresholds"]["hyde_to_cot"] == 1.3


class TestRetrievalStrategiesIntegration:
    """检索策略集成测试"""
    
    @pytest.mark.asyncio
    async def test_strategy_registry(self):
        """测试策略注册器"""
        from src.core.reasoning.retrieval_strategies.base_strategy import strategy_registry
        
        # 测试注册器存在
        assert strategy_registry is not None
        
        # 测试获取策略列表
        strategies = strategy_registry.list_strategies()
        assert isinstance(strategies, list)
    
    @pytest.mark.asyncio
    async def test_retrieval_result_creation(self):
        """测试检索结果创建"""
        documents = [{"id": "1", "content": "测试文档"}]
        
        # 成功结果
        result = RetrievalResult(
            documents=documents,
            strategy_name="test",
            execution_time=0.1
        )
        assert result.success is True
        assert len(result.documents) == 1
        assert result.strategy_name == "test"
        assert result.execution_time == 0.1
        
        # 错误结果
        error_result = RetrievalResult.from_error("test", "测试错误")
        assert error_result.success is False
        assert error_result.error_message == "测试错误"
        assert len(error_result.documents) == 0
        
        # 字典转换
        result_dict = result.to_dict()
        assert "documents" in result_dict
        assert "strategy_name" in result_dict
        assert "success" in result_dict


if __name__ == "__main__":
    # 简单测试运行
    print("运行HyDE策略测试...")
    
    async def run_test():
        mock_llm = Mock()
        mock_llm.generate = AsyncMock(return_value="假设性答案")
        mock_kms = Mock()
        mock_kms.query_knowledge = AsyncMock(return_value=[])
        
        strategy = HyDEStrategy(mock_llm, mock_kms)
        result = await strategy.execute("测试查询", {"beta": 0.8})
        
        print(f"测试结果: {result.to_dict()}")
    
    asyncio.run(run_test())