"""
异步研究系统集成器 - 将现有的智能体和组件集成到新的异步架构中
提供向后兼容性，同时享受新架构的优势
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Union
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from async_research_system import AsyncResearchSystem
from async_agent_adapter import AsyncAgentRegistry, AsyncAgentAdapterFactory
from async_component_manager import AsyncComponentManager, ComponentType

logger = logging.getLogger(__name__)


class AsyncResearchIntegrator:
    """异步研究系统集成器"""

    def __init__(self):
        self.async_system = AsyncResearchSystem()
        self.agent_registry = AsyncAgentRegistry()
        self.component_manager = AsyncComponentManager()
        self._is_initialized = False
        self._init_lock = asyncio.Lock()
    
    async def _validate_initialization_environment(self) -> bool:
        """验证初始化环境"""
        try:
            # 检查必要的组件
            if not self.async_system:
                return False
            
            if not self.agent_registry:
                return False
            
            if not self.component_manager:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"环境验证失败: {e}")
            return False
    
    async def _record_initialization(self):
        """记录初始化历史"""
        try:
            if not hasattr(self, 'initialization_history'):
                self.initialization_history = []
            
            self.initialization_history.append({
                'timestamp': time.time(),
                'status': 'success',
                'components_initialized': len(self.component_manager.components) if hasattr(self.component_manager, 'components') else 0,
                'agents_registered': len(self.agent_registry.agents) if hasattr(self.agent_registry, 'agents') else 0
            })
            
        except Exception as e:
            logger.warning(f"记录初始化历史失败: {e}")

    async def initialize(self) -> None:
        """初始化集成器"""
        async with self._init_lock:
            if self._is_initialized:
                return

            try:
                logger.info("🚀 开始初始化异步研究系统集成器...")

                # 验证初始化环境
                if not await self._validate_initialization_environment():
                    raise RuntimeError("初始化环境验证失败")

                await self.async_system.initialize()

                await self._register_core_components()
                await self._initialize_core_components()

                await self._register_agents()
                await self._initialize_agents()

                # 记录初始化历史
                await self._record_initialization()

                self._is_initialized = True
                logger.info("✅ 异步研究系统集成器初始化完成")

            except Exception as e:
                logger.error("❌ 集成器初始化失败: {e}")
                raise

    async def _register_core_components(self) -> None:
        """注册核心组件"""
        logger.info("🔄 注册核心组件...")

        await self.component_manager.register_component(
            "config_manager", ComponentType.CONFIG,
            factory_func=self._create_config_manager,
            priority=0
        )

        await self.component_manager.register_component(
            "llm_client", ComponentType.LLM_CLIENT,
            factory_func=self._create_llm_client,
            dependencies=["config_manager"],
            priority=1
        )

        await self.component_manager.register_component(
            "faiss_memory", ComponentType.MEMORY,
            factory_func=self._create_faiss_memory,
            dependencies=["config_manager"],
            priority=1
        )

        logger.info("✅ 核心组件注册完成")

    async def _initialize_core_components(self) -> None:
        """初始化核心组件"""
        logger.info("🔄 初始化核心组件...")

        try:
            await self.component_manager.initialize_all_components()
            logger.info("✅ 核心组件初始化完成")
        except Exception as e:
            logger.error("❌ 核心组件初始化失败: {e}")
            raise

    async def _create_config_manager(self) -> Any:
        """创建配置管理器"""
        try:
            from utils.intelligent_config_manager import IntelligentConfigManager
            return IntelligentConfigManager()
        except ImportError:
            logger.warning("⚠️ 无法导入IntelligentConfigManager，使用默认配置")
            return self._create_default_config_manager()

    async def _create_llm_client(self) -> Any:
        """创建LLM客户端"""
        try:
            from utils.llm_client import LLMClient
            config_manager = await self.component_manager.get_component("config_manager")
            return LLMClient(config_manager)
        except ImportError:
            logger.warning("⚠️ 无法导入LLMClient，使用默认客户端")
            return self._create_default_llm_client()

    def _create_default_llm_client(self) -> Any:
        """创建默认LLM客户端"""
        class DefaultLLMClient:
            def __init__(self, config_manager):
                self.config = config_manager
                self.name = "DefaultLLMClient"

            async def generate_text(self, prompt: str, **kwargs) -> str:
                await asyncio.sleep(0.1)
                return f"LLM响应: {prompt[:50]}..."

            async def cleanup(self, *args, **kwargs):
                logger.info("Component cleaned up")

        return DefaultLLMClient(self.component_manager.get_component("config_manager"))

    def _create_default_config_manager(self) -> Any:
        """创建默认配置管理器"""
        class DefaultConfigManager:
            def __init__(self):
                self.config = {}
                self.name = "DefaultConfigManager"

            def get(self, key: str, default: Any = None) -> Any:
                return self.config.get(key, default)

            def set(self, key: str, value: Any) -> None:
                self.config[key] = value

        return DefaultConfigManager()

    async def _create_faiss_memory(self) -> Any:
        """创建FAISS内存"""
        try:
            from memory.enhanced_faiss_memory import EnhancedFAISSMemory
            return EnhancedFAISSMemory()
        except ImportError:
            logger.warning("⚠️ 无法导入EnhancedFAISSMemory，使用默认内存")
            return self._create_default_memory()

    def _create_default_memory(self) -> Any:
        """创建默认内存"""
        class DefaultMemory:
            def __init__(self, config_manager):
                self.config = config_manager
                self.data = {}

            async def store(self, key: str, value: Any) -> None:
                self.data[key] = value

            async def retrieve(self, key: str) -> Any:
                return self.data.get(key)

            async def cleanup(self):
                self.data.clear()

        return DefaultMemory(self.component_manager.get_component("config_manager"))

    async def _register_agents(self) -> None:
        """注册智能体"""
        logger.info("🔄 注册智能体...")

        try:
            await self._register_existing_agents()
        except Exception as e:
            logger.error("❌ 注册现有智能体失败: {e}")
            raise RuntimeError(f"智能体注册失败，系统无法继续: {e}")

        logger.info("✅ 智能体注册完成")

    async def _register_existing_agents(self) -> None:
        """注册现有的智能体"""
        try:
            # 注册知识检索智能体
            from ..services.knowledge_retrieval_service import KnowledgeRetrievalService
            config_manager = await self.component_manager.get_component("config_manager")
            knowledge_agent = KnowledgeRetrievalService()
            
            await self.agent_registry.register_agent("knowledge_retrieval", knowledge_agent)
            
            # 注册答案生成智能体
            from ..services.answer_generation_service import AnswerGenerationService
            answer_agent = AnswerGenerationService()
            await self.agent_registry.register_agent("answer_generation", answer_agent)
            
            # 注册策略智能体
            from .agents.intelligent_strategy_agent_wrapper import IntelligentStrategyAgentWrapper as IntelligentStrategyAgent
            strategy_agent = IntelligentStrategyAgentWrapper(config_manager, enable_gradual_replacement=True)
            await self.agent_registry.register_agent("strategy", strategy_agent)
            
            # 注册引用智能体
            from ..services.citation_service import CitationService
            citation_agent = CitationService()
            await self.agent_registry.register_agent("citation", citation_agent)
            
            # 注册分析智能体
            from .agents.enhanced_analysis_agent_wrapper import EnhancedAnalysisAgentWrapper as EnhancedAnalysisAgent
            analysis_agent = EnhancedAnalysisAgentWrapper(config_manager, enable_gradual_replacement=True)
            await self.agent_registry.register_agent("analysis", analysis_agent)
            
            logger.info("✅ 现有智能体注册完成")
            
        except Exception as e:
            logger.error(f"❌ 注册现有智能体失败: {e}")
            raise

    async def _register_mock_agents(self) -> None:
        """注册模拟智能体 - 已禁用，系统必须使用真实智能体"""
        logger.error("❌ 系统不允许使用Mock智能体，必须使用真实的增强智能体")
        raise RuntimeError("Mock智能体已被禁用，请确保真实智能体可用")
    
    async def _initialize_agents(self) -> None:
        """初始化智能体"""
        logger.info("🔄 初始化智能体...")
        
        try:
            # 获取所有已注册的智能体
            agents = await self.agent_registry.get_all_agents()
            
            for agent_name, agent in agents.items():
                try:
                    if hasattr(agent, 'initialize'):
                        await agent.initialize()
                    logger.info(f"✅ 智能体 {agent_name} 初始化完成")
                except Exception as e:
                    logger.error(f"❌ 智能体 {agent_name} 初始化失败: {e}")
                    raise
            
            logger.info("✅ 所有智能体初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 智能体初始化失败: {e}")
            raise
    
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理查询"""
        try:
            if not self._is_initialized:
                await self.initialize()
            
            logger.info(f"🔍 处理查询: {query[:100]}...")
            
            # 使用异步系统处理查询
            result = await self.async_system.process_query(query, context)
            
            logger.info("✅ 查询处理完成")
            return result
            
        except Exception as e:
            logger.error(f"❌ 查询处理失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            status = {
                "initialized": self._is_initialized,
                "async_system_status": await self.async_system.get_status() if hasattr(self.async_system, 'get_status') else "unknown",
                "agent_count": len(await self.agent_registry.get_all_agents()) if hasattr(self.agent_registry, 'get_all_agents') else 0,
                "component_count": len(self.component_manager.components) if hasattr(self.component_manager, 'components') else 0,
                "timestamp": time.time()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"❌ 获取系统状态失败: {e}")
            return {
                "initialized": False,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def shutdown(self) -> None:
        """关闭集成器"""
        try:
            logger.info("🔄 关闭异步研究系统集成器...")
            
            # 关闭异步系统
            if hasattr(self.async_system, 'shutdown'):
                await self.async_system.shutdown()
            
            # 关闭所有智能体
            agents = await self.agent_registry.get_all_agents()
            for agent_name, agent in agents.items():
                try:
                    if hasattr(agent, 'cleanup'):
                        await agent.cleanup()
                    logger.info(f"✅ 智能体 {agent_name} 已关闭")
                except Exception as e:
                    logger.warning(f"⚠️ 智能体 {agent_name} 关闭时出现问题: {e}")
            
            # 关闭组件管理器
            if hasattr(self.component_manager, 'shutdown'):
                await self.component_manager.shutdown()
            
            self._is_initialized = False
            logger.info("✅ 异步研究系统集成器已关闭")
            
        except Exception as e:
            logger.error(f"❌ 关闭集成器失败: {e}")
            raise
    
    async def restart(self) -> None:
        """重启集成器"""
        try:
            logger.info("🔄 重启异步研究系统集成器...")
            
            # 先关闭
            await self.shutdown()
            
            # 重新初始化
            await self.initialize()
            
            logger.info("✅ 异步研究系统集成器重启完成")
            
        except Exception as e:
            logger.error(f"❌ 重启集成器失败: {e}")
            raise

            answer_result = await self._execute_answer_generation(query, context, knowledge_result, reasoning_result)

            execution_time = time.time() - start_time

            result = {
                "success": True,
                "query": query,
                "knowledge_result": knowledge_result,
                "reasoning_result": reasoning_result,
                "answer_result": answer_result,
                "execution_time": execution_time,
                "timestamp": time.time()
            }

            logger.info("✅ 研究任务完成，耗时: {execution_time:.2f}秒")
            return result

        except Exception as e:
            logger.error("❌ 研究任务执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "timestamp": time.time()
            }

    async def _execute_knowledge_retrieval(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """执行知识检索"""
        try:
            task = {
                "query": query,
                "context": context,
                "type": "knowledge_retrieval"
            }

            result = await self.agent_registry.execute_agent("knowledge_agent", task)
            return result

        except Exception as e:
            logger.error("❌ 知识检索失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": f"知识检索失败，使用备用方案: {query}"
            }

    async def _execute_reasoning(self, query: str, context: Optional[Dict[str, Any]],
                                knowledge_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行推理分析"""
        try:
            task = {
                "query": query,
                "context": context,
                "knowledge": knowledge_result,
                "type": "reasoning"
            }

            result = await self.agent_registry.execute_agent("reasoning_agent", task)
            return result

        except Exception as e:
            logger.error("❌ 推理分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": f"推理分析失败，使用备用方案: {query}"
            }

    async def _execute_answer_generation(self, query: str, context: Optional[Dict[str, Any]],
                                       knowledge_result: Dict[str, Any],
                                       reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行答案生成"""
        try:
            task = {
                "query": query,
                "context": context,
                "knowledge": knowledge_result,
                "reasoning": reasoning_result,
                "type": "answer_generation"
            }

            result = await self.agent_registry.execute_agent("answer_agent", task)
            return result

        except Exception as e:
            logger.error("❌ 答案生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": f"答案生成失败，使用备用方案: {query}"
            }

    async def shutdown(self) -> None:
        """关闭集成器"""
        logger.info("🔄 开始关闭异步研究系统集成器...")

        try:
            await self.agent_registry.shutdown_all_agents()

            await self.component_manager.shutdown_all_components()

            await self.async_system.shutdown()

            logger.info("✅ 异步研究系统集成器关闭完成")

        except Exception as e:
            logger.error("❌ 集成器关闭失败: {e}")
            raise

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "initialized": self._is_initialized,
            "components": self.component_manager.get_all_components_status(),
            "agents": self.agent_registry.get_all_agents_status() if self._is_initialized else {}
        }


async def create_async_research_integrator() -> AsyncResearchIntegrator:
    """创建异步研究系统集成器实例"""
    integrator = AsyncResearchIntegrator()
    await integrator.initialize()
    return integrator


async def test_integrator():
    """测试集成器"""
    try:
        integrator = await create_async_research_integrator()

        result = await integrator.execute_research("What is artificial intelligence?")
        print(f"研究结果: {result}")

        status = integrator.get_system_status()
        print(f"系统状态: {status}")

        await integrator.shutdown()

        print("✅ 集成器测试完成")

    except Exception as e:
        logger.error("测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_integrator())
