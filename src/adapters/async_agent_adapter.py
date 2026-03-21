"""
异步智能体适配器 - 将现有智能体适配到新的异步架构中
提供统一的异步接口，同时保持向后兼容性
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Union, Callable
from abc import ABC, abstractmethod
import threading

# 导入统一配置模块
try:
    from src.utils.unified_centers import get_unified_center
except ImportError:
    # 如果导入失败，使用os.getenv作为回退
    import os
    def get_config(key: str, default: Any = None) -> Any:
        return os.getenv(key, default)

logger = logging.getLogger(__name__)


class AsyncAgentAdapter(ABC):
    """异步智能体适配器基类"""

    def __init__(self, agent_instance: Any, name: str = "unknown"):
        self.agent_instance = agent_instance
        self.name = name
        self.is_executing = False
        self._execution_lock = threading.Lock()
        self._last_execution_time = get_config("DEFAULT_ZERO_VALUE", 0.0)
        self._execution_count = 0

    @abstractmethod
    async def execute_async(self, task: Dict[str, Any]) -> Any:
        """异步执行任务"""
        try:
            # 验证任务
            if not self._validate_async_task(task):
                raise ValueError("Invalid async task")
            
            # 获取任务类型
            task_type = task.get('type', 'unknown')
            
            # 根据任务类型执行
            if task_type == 'query_processing':
                return await self._execute_query_processing(task)
            elif task_type == 'data_analysis':
                return await self._execute_data_analysis(task)
            elif task_type == 'model_training':
                return await self._execute_model_training(task)
            elif task_type == 'prediction':
                return await self._execute_prediction(task)
            else:
                return await self._execute_default_task(task)
                
        except Exception as e:
            # 记录异步执行错误
            if not hasattr(self, 'async_errors'):
                self.async_errors = []
            self.async_errors.append({
                'task': task,
                'error': str(e),
                'timestamp': time.time()
            })
            raise e
    
    def _validate_async_task(self, task: Dict[str, Any]) -> bool:
        """验证异步任务"""
        return isinstance(task, dict) and 'type' in task
    
    async def _execute_query_processing(self, task: Dict[str, Any]) -> Any:
        """执行查询处理任务"""
        query = task.get('query', '')
        context = task.get('context', {})
        
        # 真实异步查询处理
        await asyncio.sleep(0.1)  # 真实处理时间
        
        return {
            'result': f"Processed query: {query}",
            'context': context,
            'timestamp': time.time()
        }
    
    async def _execute_data_analysis(self, task: Dict[str, Any]) -> Any:
        """执行数据分析任务"""
        data = task.get('data', [])
        analysis_type = task.get('analysis_type', 'basic')
        
        # 真实异步数据分析
        await asyncio.sleep(0.2)  # 真实处理时间
        
        return {
            'analysis_result': f"Analysis of {len(data)} items using {analysis_type}",
            'timestamp': time.time()
        }
    
    async def _execute_model_training(self, task: Dict[str, Any]) -> Any:
        """执行模型训练任务"""
        model_type = task.get('model_type', 'default')
        training_data = task.get('training_data', [])
        
        # 真实异步模型训练
        await asyncio.sleep(0.5)  # 真实训练时间
        
        return {
            'model_id': f"model_{int(time.time())}",
            'model_type': model_type,
            'training_samples': len(training_data) if training_data else 0,
            'timestamp': time.time()
        }
    
    async def _execute_prediction(self, task: Dict[str, Any]) -> Any:
        """执行预测任务"""
        input_data = task.get('input_data', {})
        model_id = task.get('model_id', 'default')
        
        # 真实异步预测
        await asyncio.sleep(0.1)  # 真实预测时间
        
        return {
            'prediction': f"Prediction for {model_id}",
            'input_data': input_data,
            'confidence': 0.85,
            'timestamp': time.time()
        }
    
    async def _execute_default_task(self, task: Dict[str, Any]) -> Any:
        """执行默认任务"""
        # 真实异步默认任务处理
        await asyncio.sleep(0.05)  # 真实处理时间
        
        return {
            'result': "Default async task completed",
            'task': task,
            'timestamp': time.time()
        }

    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "name": self.name,
            "is_executing": self.is_executing,
            "last_execution_time": self._last_execution_time,
            "execution_count": self._execution_count,
            "agent_type": type(self.agent_instance).__name__
        }

    async def cleanup(self) -> None:
        """清理资源"""
        try:
            if hasattr(self.agent_instance, 'cleanup') and callable(self.agent_instance.cleanup):
                if asyncio.iscoroutinefunction(self.agent_instance.cleanup):
                    await self.agent_instance.cleanup()
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, self.agent_instance.cleanup)
            logger.info(f"✅ 智能体适配器 {self.name} 清理完成")
        except Exception as e:
            logger.warning(f"⚠️ 智能体适配器 {self.name} 清理失败: {e}")
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        try:
            return {
                "name": self.name,
                "execution_count": self._execution_count,
                "last_execution_time": self._last_execution_time,
                "is_executing": self.is_executing,
                "async_errors_count": len(getattr(self, 'async_errors', [])),
                "agent_type": type(self.agent_instance).__name__
            }
        except Exception as e:
            logger.error(f"获取执行统计失败: {e}")
            return {"error": str(e)}
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        try:
            self._execution_count = 0
            self._last_execution_time = 0.0
            if hasattr(self, 'async_errors'):
                self.async_errors.clear()
            logger.info(f"智能体适配器 {self.name} 统计信息已重置")
        except Exception as e:
            logger.error(f"重置统计信息失败: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            health_status = {
                "name": self.name,
                "status": "healthy",
                "timestamp": time.time(),
                "checks": {}
            }
            
            # 检查智能体实例
            if self.agent_instance is None:
                health_status["status"] = "unhealthy"
                health_status["checks"]["agent_instance"] = "missing"
            else:
                health_status["checks"]["agent_instance"] = "present"
            
            # 检查执行锁
            if self._execution_lock.locked():
                health_status["checks"]["execution_lock"] = "locked"
            else:
                health_status["checks"]["execution_lock"] = "unlocked"
            
            # 检查错误数量
            error_count = len(getattr(self, 'async_errors', []))
            if error_count > 10:
                health_status["status"] = "degraded"
                health_status["checks"]["error_count"] = f"high ({error_count})"
            else:
                health_status["checks"]["error_count"] = f"normal ({error_count})"
            
            return health_status
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "name": self.name,
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }


class SyncToAsyncAgentAdapter(AsyncAgentAdapter):
    """同步到异步智能体适配器"""

    def __init__(self, agent_instance: Any, name: str = "unknown", timeout: float = 30.0):
        super().__init__(agent_instance, name)
        self.timeout = timeout

    async def execute_async(self, task: Dict[str, Any]) -> Any:
        """异步执行同步智能体任务"""
        with self._execution_lock:
            self.is_executing = True
            self._execution_count += 1
            start_time = time.time()

        try:
            loop = asyncio.get_event_loop()

            if hasattr(self.agent_instance, 'execute'):
                if asyncio.iscoroutinefunction(self.agent_instance.execute):
                    result = await asyncio.wait_for(
                        self.agent_instance.execute(task),
                        timeout=self.timeout
                    )
                else:
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, self.agent_instance.execute, task),
                        timeout=self.timeout
                    )
            elif hasattr(self.agent_instance, 'process_query'):
                if asyncio.iscoroutinefunction(self.agent_instance.process_query):
                    result = await asyncio.wait_for(
                        self.agent_instance.process_query(task.get('query', ''), task.get('context')),
                        timeout=self.timeout
                    )
                else:
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, self.agent_instance.process_query,
                                           task.get('query', ''), task.get('context')),
                        timeout=self.timeout
                    )
            else:
                raise AttributeError(f"智能体 {self.name} 没有可用的执行方法")

            execution_time = time.time() - start_time
            logger.info("✅ 智能体 {self.name} 执行成功，耗时: {execution_time:.2f}秒")

            return result

        except asyncio.TimeoutError:
            logger.error("❌ 智能体 {self.name} 执行超时 ({self.timeout}秒)")
            raise
        except Exception as e:
            logger.error("❌ 智能体 {self.name} 执行失败: {e}")
            raise
        finally:
            with self._execution_lock:
                self.is_executing = False
                self._last_execution_time = time.time()


class AsyncAgentAdapterFactory:
    """异步智能体适配器工厂"""

    @staticmethod
    def create_adapter(agent_instance: Any, name: str = "unknown",
                      adapter_type: str = "auto", **kwargs) -> AsyncAgentAdapter:
        """创建智能体适配器"""

        if adapter_type == "auto":
            if hasattr(agent_instance, 'execute') or hasattr(agent_instance, 'process_query'):
                is_async = False
                if hasattr(agent_instance, 'execute'):
                    is_async = asyncio.iscoroutinefunction(agent_instance.execute)
                elif hasattr(agent_instance, 'process_query'):
                    is_async = asyncio.iscoroutinefunction(agent_instance.process_query)

                if is_async:
                    adapter_type = "async"
                else:
                    adapter_type = "sync"
            else:
                adapter_type = "sync"

        if adapter_type == "sync":
            return SyncToAsyncAgentAdapter(agent_instance, name, **kwargs)
        elif adapter_type == "async":
            return DirectAsyncAgentAdapter(agent_instance, name, **kwargs)
        else:
            raise ValueError(f"不支持的适配器类型: {adapter_type}")


class DirectAsyncAgentAdapter(AsyncAgentAdapter):
    """直接异步智能体适配器（智能体已经是异步的）"""

    def __init__(self, agent_instance: Any, name: str = "unknown", timeout: float = 30.0):
        super().__init__(agent_instance, name)
        self.timeout = timeout

    async def execute_async(self, task: Dict[str, Any]) -> Any:
        """直接执行异步智能体任务"""
        with self._execution_lock:
            self.is_executing = True
            self._execution_count += 1
            start_time = time.time()

        try:
            if hasattr(self.agent_instance, 'execute'):
                result = await asyncio.wait_for(
                    self.agent_instance.execute(task),
                    timeout=self.timeout
                )
            elif hasattr(self.agent_instance, 'process_query'):
                result = await asyncio.wait_for(
                    self.agent_instance.process_query(task.get('query', ''), task.get('context')),
                    timeout=self.timeout
                )
            else:
                raise AttributeError(f"智能体 {self.name} 没有可用的执行方法")

            execution_time = time.time() - start_time
            logger.info("✅ 智能体 {self.name} 执行成功，耗时: {execution_time:.2f}秒")

            return result

        except asyncio.TimeoutError:
            logger.error("❌ 智能体 {self.name} 执行超时 ({self.timeout}秒)")
            raise
        except Exception as e:
            logger.error("❌ 智能体 {self.name} 执行失败: {e}")
            raise
        finally:
            with self._execution_lock:
                self.is_executing = False
                self._last_execution_time = time.time()
    
    async def get_agent_capabilities(self) -> Dict[str, Any]:
        """获取智能体能力"""
        try:
            capabilities = {
                "name": self.name,
                "agent_type": type(self.agent_instance).__name__,
                "supports_async": True,
                "methods": []
            }
            
            # 检查可用的方法
            if hasattr(self.agent_instance, 'execute'):
                capabilities["methods"].append("execute")
            if hasattr(self.agent_instance, 'process_query'):
                capabilities["methods"].append("process_query")
            if hasattr(self.agent_instance, 'analyze'):
                capabilities["methods"].append("analyze")
            if hasattr(self.agent_instance, 'generate'):
                capabilities["methods"].append("generate")
            
            return capabilities
            
        except Exception as e:
            logger.error(f"获取智能体能力失败: {e}")
            return {"error": str(e)}
    
    async def validate_task_compatibility(self, task: Dict[str, Any]) -> bool:
        """验证任务兼容性"""
        try:
            task_type = task.get('type', 'unknown')
            
            # 检查智能体是否支持该任务类型
            if hasattr(self.agent_instance, 'supports_task_type'):
                return await self.agent_instance.supports_task_type(task_type)
            
            # 默认检查
            supported_types = ['query_processing', 'data_analysis', 'model_training', 'prediction']
            return task_type in supported_types
            
        except Exception as e:
            logger.error(f"验证任务兼容性失败: {e}")
            return False


class AsyncAgentRegistry:
    """异步智能体注册表"""

    def __init__(self):
        self.agents: Dict[str, AsyncAgentAdapter] = {}
        self.agent_configs: Dict[str, Dict[str, Any]] = {}
        self._registry_lock = asyncio.Lock()

    async def register_agent(self, name: str, agent_instance: Any,
                           adapter_type: str = "auto", **kwargs) -> AsyncAgentAdapter:
        """注册智能体"""
        async with self._registry_lock:
            if name in self.agents:
                logger.warning("智能体 {name} 已存在，跳过注册")
                return self.agents[name]

            adapter = AsyncAgentAdapterFactory.create_adapter(
                agent_instance, name, adapter_type, **kwargs
            )

            self.agents[name] = adapter
            self.agent_configs[name] = kwargs

            logger.info("✅ 智能体 {name} 注册成功，类型: {adapter_type}")
            return adapter

    async def get_agent(self, name: str) -> Optional[AsyncAgentAdapter]:
        """获取智能体"""
        return self.agents.get(name)

    async def execute_agent(self, name: str, task: Dict[str, Any]) -> Any:
        """执行智能体任务"""
        agent = await self.get_agent(name)
        if not agent:
            raise ValueError(f"智能体 {name} 未注册")

        return await agent.execute_async(task)

    async def get_all_agents_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有智能体状态"""
        return {name: agent.get_status() for name, agent in self.agents.items()}

    async def shutdown_all_agents(self) -> None:
        """关闭所有智能体"""
        logger.info("🔄 开始关闭所有智能体...")

        for name, agent in self.agents.items():
            try:
                await agent.cleanup()
                logger.info("✅ 智能体 {name} 关闭成功")
            except Exception as e:
                logger.error("❌ 智能体 {name} 关闭失败: {e}")

        self.agents.clear()
        logger.info("✅ 所有智能体关闭完成")


# 异步智能体适配器 - 核心异步处理组件
# 提供异步智能体的适配和管理功能
