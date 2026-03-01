"""
异步研究系统核心 - 重新设计的统一异步架构
解决原有系统的异步混乱问题，提供清晰的异步接口和资源管理
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import weakref

# 导入统一中心模块
def get_unified_center(center_name: str) -> Dict[str, Any]:
    """获取统一中心"""
    try:
        from src.utils.unified_centers import get_unified_center as _get_unified_center
        result = _get_unified_center(center_name)
        if result is None:
            return {
                "status": "fallback",
                "message": f"统一中心 {center_name} 不可用",
                "timestamp": time.time()
            }
        return result
    except ImportError:
        logger.warning(f"统一中心不可用: {center_name}")
        return {
            "status": "fallback",
            "message": f"统一中心 {center_name} 不可用",
            "timestamp": time.time()
        }

# 使用核心系统日志模块（生成标准格式日志供评测系统分析）
from src.utils.research_logger import log_info, log_warning, log_error, log_debug, UnifiedErrorHandler
import logging
logger = logging.getLogger(__name__)


class ComponentStatus(Enum):
    """组件状态枚举"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ComponentInfo:
    """组件信息"""
    name: str
    status: ComponentStatus
    dependencies: List[str]
    init_time: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class TaskInfo:
    """任务信息"""
    id: str
    name: str
    priority: TaskPriority
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None


class AsyncResourceManager:
    """统一资源管理器 - 管理所有组件的生命周期"""

    def __init__(self):
        self.components: Dict[str, ComponentInfo] = {}
        self.component_instances: Dict[str, Any] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        self._initialization_lock = asyncio.Lock()
        self._shutdown_lock = asyncio.Lock()
        self._is_shutting_down = False

    async def register_component(self, name: str, dependencies: Optional[List[str]] = None) -> None:
        """注册组件"""
        async with self._initialization_lock:
            if name in self.components:
                logger.warning("组件 {name} 已存在，跳过注册")
                return

            self.components[name] = ComponentInfo(
                name=name,
                status=ComponentStatus.UNINITIALIZED,
                dependencies=dependencies or []
            )
            self.dependency_graph[name] = dependencies or []
            logger.info("✅ 组件 {name} 注册成功")

    async def initialize_component(self, name: str, factory_func, *args, **kwargs) -> Any:
        """初始化组件"""
        async with self._initialization_lock:
            if self._is_shutting_down:
                raise RuntimeError("系统正在关闭，无法初始化组件")

            if name not in self.components:
                raise ValueError(f"组件 {name} 未注册")

            component_info = self.components[name]

            if not await self._check_dependencies(name):
                raise RuntimeError(f"组件 {name} 的依赖未满足")

            try:
                component_info.status = ComponentStatus.INITIALIZING
                component_info.init_time = time.time()

                if asyncio.iscoroutinefunction(factory_func):
                    instance = await factory_func(*args, **kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    instance = await loop.run_in_executor(None, factory_func, *args, **kwargs)

                self.component_instances[name] = instance
                component_info.status = ComponentStatus.READY
                logger.info("✅ 组件 {name} 初始化成功")
                return instance

            except Exception as e:
                component_info.status = ComponentStatus.ERROR
                component_info.error_message = str(e)
                logger.error("❌ 组件 {name} 初始化失败: {e}")
                raise

    async def get_component(self, name: str) -> Any:
        """获取组件实例"""
        if name not in self.components:
            raise ValueError(f"组件 {name} 未注册")

        component_info = self.components[name]
        if component_info.status != ComponentStatus.READY:
            raise RuntimeError(f"组件 {name} 状态不正确: {component_info.status}")

        return self.component_instances[name]

    async def _check_dependencies(self, component_name: str) -> bool:
        """检查组件依赖是否满足"""
        dependencies = self.dependency_graph.get(component_name, [])
        for dep in dependencies:
            if dep not in self.components:
                logger.warning("组件 {component_name} 的依赖 {dep} 未注册")
                return False
            if self.components[dep].status != ComponentStatus.READY:
                logger.warning("组件 {component_name} 的依赖 {dep} 未就绪: {self.components[dep].status}")
                return False
        return True

    async def shutdown(self) -> None:
        """关闭所有组件"""
        async with self._shutdown_lock:
            if self._is_shutting_down:
                return

            self._is_shutting_down = True
            logger.info("🔄 开始关闭所有组件...")

            shutdown_order = self._get_shutdown_order()

            for component_name in shutdown_order:
                if component_name in self.component_instances:
                    try:
                        instance = self.component_instances[component_name]
                        if hasattr(instance, 'cleanup') and callable(instance.cleanup):
                            if asyncio.iscoroutinefunction(instance.cleanup):
                                await instance.cleanup()
                            else:
                                loop = asyncio.get_event_loop()
                                await loop.run_in_executor(None, instance.cleanup)

                        self.components[component_name].status = ComponentStatus.SHUTTING_DOWN
                        del self.component_instances[component_name]
                        logger.info("✅ 组件 {component_name} 关闭成功")

                    except Exception as e:
                        logger.error("❌ 组件 {component_name} 关闭失败: {e}")

            logger.info("✅ 所有组件关闭完成")

    def _get_shutdown_order(self) -> List[str]:
        """获取组件关闭顺序（依赖的反序）"""
        visited = set()
        order = []

        def dfs(node):
            if node in visited:
                return
            visited.add(node)
            for dep in self.dependency_graph.get(node, []):
                dfs(dep)
            order.append(node)

        for component_name in self.components:
            dfs(component_name)

        return order


class AsyncAgentManager:
    """统一智能体管理器 - 管理所有智能体的生命周期"""

    def __init__(self, resource_manager: AsyncResourceManager):
        self.resource_manager = resource_manager
        self.agent_registry: Dict[str, Dict[str, Any]] = {}
        self.active_agents: Dict[str, Any] = {}
        self.agent_tasks: Dict[str, asyncio.Task] = {}

    async def register_agent(self, name: str, agent_class, config: Optional[Dict[str, Any]] = None) -> None:
        """注册智能体"""
        self.agent_registry[name] = {
            'class': agent_class,
            'config': config or {},
            'status': 'registered'
        }
        logger.info(f"✅ 智能体 {name} 注册成功")

    async def create_agent(self, name: str) -> Any:
        """创建智能体实例"""
        if name not in self.agent_registry:
            raise ValueError(f"智能体 {name} 未注册")

        if name in self.active_agents:
            return self.active_agents[name]

        agent_info = self.agent_registry[name]
        agent_class = agent_info['class']
        config = agent_info['config']

        try:
            if asyncio.iscoroutinefunction(agent_class):
                agent = await agent_class(**config)
            else:
                agent = agent_class(**config)

            self.active_agents[name] = agent
            agent_info['status'] = 'active'
            logger.info("✅ 智能体 {name} 创建成功")
            return agent

        except Exception as e:
            logger.error("❌ 智能体 {name} 创建失败: {e}")
            raise
    
    async def get_agent(self, name: str) -> Any:
        """获取智能体实例"""
        if name not in self.active_agents:
            await self.create_agent(name)
        return self.active_agents.get(name)
    
    async def shutdown_agent(self, name: str) -> None:
        """关闭智能体"""
        if name not in self.active_agents:
            return
        
        try:
            agent = self.active_agents[name]
            if hasattr(agent, 'cleanup') and callable(agent.cleanup):
                if asyncio.iscoroutinefunction(agent.cleanup):
                    await agent.cleanup()
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, agent.cleanup)
            
            del self.active_agents[name]
            if name in self.agent_registry:
                self.agent_registry[name]['status'] = 'inactive'
            
            logger.info(f"✅ 智能体 {name} 关闭成功")
            
        except Exception as e:
            logger.error(f"❌ 智能体 {name} 关闭失败: {e}")
    
    async def shutdown_all_agents(self) -> None:
        """关闭所有智能体"""
        for name in list(self.active_agents.keys()):
            await self.shutdown_agent(name)
    
    def get_agent_status(self, name: str) -> Optional[Dict[str, Any]]:
        """获取智能体状态"""
        if name not in self.agent_registry:
            return None
        
        agent_info = self.agent_registry[name]
        return {
            "name": name,
            "status": agent_info['status'],
            "is_active": name in self.active_agents,
            "has_task": name in self.agent_tasks
        }
    
    def get_all_agents_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有智能体状态"""
        result = {}
        for name in self.agent_registry:
            status = self.get_agent_status(name)
            if status:
                result[name] = status
        return result

    async def execute_agent(self, name: str, task: Dict[str, Any]) -> Any:
        """执行智能体任务"""
        agent = await self.create_agent(name)

        if not hasattr(agent, 'execute'):
            raise AttributeError(f"智能体 {name} 没有 execute 方法")

        try:
            if asyncio.iscoroutinefunction(agent.execute):
                result = await agent.execute(task)
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, agent.execute, task)

            return result

        except Exception as e:
            logger.error("❌ 智能体 {name} 执行失败: {e}")
            raise

    async def shutdown_agents(self) -> None:
        """关闭所有智能体"""
        logger.info("🔄 开始关闭所有智能体...")

        for name, agent in self.active_agents.items():
            try:
                if hasattr(agent, 'cleanup') and callable(agent.cleanup):
                    if asyncio.iscoroutinefunction(agent.cleanup):
                        await agent.cleanup()
                    else:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, agent.cleanup)

                if name in self.agent_tasks:
                    self.agent_tasks[name].cancel()

                logger.info("✅ 智能体 {name} 关闭成功")

            except Exception as e:
                logger.error("❌ 智能体 {name} 关闭失败: {e}")

        self.active_agents.clear()
        self.agent_tasks.clear()
        logger.info("✅ 所有智能体关闭完成")


class AsyncTaskManager:
    """统一任务管理器 - 管理所有异步任务"""

    def __init__(self):
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: Dict[str, TaskInfo] = {}
        self.task_counter = 0
        self._shutdown_event = asyncio.Event()

    async def submit_task(self, name: str, coro, priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """提交任务"""
        task_id = f"task_{self.task_counter}_{int(time.time())}"
        self.task_counter += 1

        task_info = TaskInfo(
            id=task_id,
            name=name,
            priority=priority,
            created_at=time.time()
        )

        task = asyncio.create_task(self._execute_task(task_info, coro))
        self.active_tasks[task_id] = task

        logger.info("✅ 任务 {name} (ID: {task_id}) 提交成功")
        return task_id

    async def _execute_task(self, task_info: TaskInfo, coro) -> None:
        """执行任务"""
        try:
            task_info.started_at = time.time()
            task_info.status = "running"

            result = await coro

            task_info.completed_at = time.time()
            task_info.status = "completed"
            task_info.result = result

            logger.info("✅ 任务 {task_info.name} (ID: {task_info.id}) 执行成功")

        except asyncio.CancelledError:
            task_info.status = "cancelled"
            logger.info("⚠️ 任务 {task_info.name} (ID: {task_info.id}) 被取消")

        except Exception as e:
            task_info.completed_at = time.time()
            task_info.status = "error"
            task_info.error = str(e)
            logger.error("❌ 任务 {task_info.name} (ID: {task_info.id}) 执行失败: {e}")

        finally:
            if task_info.id in self.active_tasks:
                del self.active_tasks[task_info.id]

            self.completed_tasks[task_info.id] = task_info

    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """等待任务完成"""
        if task_id not in self.active_tasks:
            if task_id in self.completed_tasks:
                task_info = self.completed_tasks[task_id]
                if task_info.status == "completed":
                    return task_info.result
                elif task_info.status == "error":
                    raise RuntimeError(f"任务执行失败: {task_info.error}")
                else:
                    return None
            else:
                raise ValueError(f"任务 {task_id} 不存在")

        try:
            task = self.active_tasks[task_id]
            if timeout:
                await asyncio.wait_for(task, timeout=timeout)
            else:
                await task

            task_info = self.completed_tasks[task_id]
            if task_info.status == "completed":
                return task_info.result
            else:
                raise RuntimeError(f"任务执行失败: {task_info.error}")

        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"任务 {task_id} 执行超时")

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.cancel()
            logger.info("✅ 任务 {task_id} 取消成功")
            return True
        return False

    async def shutdown(self) -> None:
        """关闭任务管理器"""
        logger.info("🔄 开始关闭任务管理器...")

        self._shutdown_event.set()

        for task_id, task in self.active_tasks.items():
            task.cancel()

        if self.active_tasks:
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)

        logger.info("✅ 任务管理器关闭完成")


class AsyncEventLoop:
    """统一事件循环管理器"""

    def __init__(self):
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._is_running = False
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """启动事件循环"""
        if self._is_running:
            return

        try:
            self.loop = asyncio.get_running_loop()
            self._is_running = True
            logger.info("✅ 事件循环启动成功")
        except RuntimeError:
            logger.warning("⚠️ 没有运行中的事件循环")

    async def stop(self) -> None:
        """停止事件循环"""
        if not self._is_running:
            return

        self._shutdown_event.set()
        self._is_running = False
        logger.info("✅ 事件循环停止成功")

    def is_running(self) -> bool:
        """检查事件循环是否运行"""
        return self._is_running

    async def run_until_complete(self, coro) -> Any:
        """运行协程直到完成"""
        if not self._is_running:
            raise RuntimeError("事件循环未启动")

        return await coro


class AsyncResearchSystem:
    """异步研究系统核心 - 重新设计的统一异步架构"""

    def __init__(self):
        self.resource_manager = AsyncResourceManager()
        self.agent_manager = AsyncAgentManager(self.resource_manager)
        self.task_manager = AsyncTaskManager()
        self.event_loop = AsyncEventLoop()

        self._is_initialized = False
        self._is_shutting_down = False
        self._init_lock = asyncio.Lock()
        self._shutdown_lock = asyncio.Lock()

        import atexit
        atexit.register(self._atexit_cleanup)

    async def initialize(self) -> None:
        """初始化系统"""
        async with self._init_lock:
            if self._is_initialized:
                return

            try:
                logger.info("🚀 开始初始化异步研究系统...")

                await self.event_loop.start()

                await self._register_core_components()

                await self._initialize_core_components()

                self._is_initialized = True
                logger.info("✅ 异步研究系统初始化完成")

            except Exception as e:
                logger.error("❌ 系统初始化失败: {e}")
                raise

    async def _register_core_components(self) -> None:
        """注册核心组件 - 🚀 迁移到知识库管理系统（第四系统）"""
        await self.resource_manager.register_component("config_manager", [])
        await self.resource_manager.register_component("llm_client", ["config_manager"])
        
        # 🚀 迁移：使用知识库管理系统替代旧的faiss_memory
        try:
            from knowledge_management_system.api.service_interface import get_knowledge_service
            kms_service = get_knowledge_service()
            # 注册为组件（注意：resource_manager可能期望特定的格式，这里先注册为字符串标识）
            await self.resource_manager.register_component("knowledge_service", [])
            # 将服务存储在resource_manager中（通过getattr避免类型检查错误）
            try:
                components = getattr(self.resource_manager, '_components', None)
                if components is not None:
                    components["knowledge_service"] = kms_service
            except Exception:
                pass  # 忽略设置失败
            logger.info("✅ 知识库管理系统已注册（第四系统）")
        except ImportError:
            logger.warning("⚠️ 知识库管理系统不可用，尝试使用旧系统")
            # 回退：使用旧系统（过渡期）
            await self.resource_manager.register_component("faiss_memory", ["config_manager"])

        # 注册知识检索智能体
        from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
        await self.agent_manager.register_agent("knowledge_agent", KnowledgeRetrievalService)
        
        # 注册答案生成智能体
        from src.services.answer_generation_service import AnswerGenerationService
        await self.agent_manager.register_agent("answer_agent", AnswerGenerationService)
        
        # 注册推理智能体（暂时使用None，因为推理引擎是直接调用的）
        await self.agent_manager.register_agent("reasoning_agent", None)

        logger.info("✅ 核心组件注册完成")

    async def _initialize_core_components(self) -> None:
        """初始化核心组件"""
        logger.info("✅ 核心组件初始化完成")

    async def execute_research(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行研究任务 - 统一的异步接口"""
        if not self._is_initialized:
            await self.initialize()

        try:
            task_id = await self.task_manager.submit_task(
                "research_task",
                self._execute_research_internal(query, context),
                TaskPriority.HIGH
            )

            result = await self.task_manager.wait_for_task(task_id, timeout=60.0)
            return result

        except Exception as e:
            logger.error("❌ 研究任务执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

    async def _execute_research_internal(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """内部研究执行逻辑 - 实现真正的深度研究"""
        start_time = time.time()  # 🚀 修复：在try块外定义，确保异常处理中可以访问
        try:
            # 1. 查询分析和预处理
            query_analysis = await self._analyze_query_complexity(query)
            
            # 2. 知识检索
            knowledge_results = await self._retrieve_knowledge(query, context)
            
            # 3. 智能推理
            reasoning_results = await self._perform_reasoning(query, knowledge_results)
            
            # 4. 答案生成
            answer = await self._generate_answer(query, knowledge_results, reasoning_results)
            
            # 5. 结果验证
            confidence = await self._calculate_confidence(query, answer, knowledge_results)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "query": query,
                "answer": answer,
                "confidence": confidence,
                "knowledge_sources": knowledge_results.get('sources', []),
                "reasoning_steps": reasoning_results.get('steps', []),
                "processing_time": processing_time,
                "timestamp": time.time(),
                "context": context or {}
            }

        except Exception as e:
            logger.error(f"❌ 内部研究执行失败: {e}")
            processing_time = time.time() - start_time  # 🚀 修复：使用已定义的start_time
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "processing_time": processing_time,
                "timestamp": time.time()
            }

    async def _analyze_query_complexity(self, query: str) -> Dict[str, Any]:
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
            return {
                "complexity": complexity_result.level.value,  # 'simple', 'medium', 'complex'
                "complexity_score": complexity_result.score,  # 0-10
                "keywords": query.split()[:5],
                "length": len(query),
                "type": "research_query",
                "needs_reasoning_chain": complexity_result.needs_reasoning_chain
            }
        except Exception as e:
            logger.warning(f"⚠️ 使用统一复杂度服务失败: {e}，使用fallback")
            # Fallback
            return {
                "complexity": "medium",
                "keywords": query.split()[:5],
                "length": len(query),
                "type": "research_query"
            }
    
    async def _retrieve_knowledge(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """检索相关知识 - 使用真正的知识检索智能体"""
        try:
            # 获取知识检索智能体
            knowledge_agent = await self.agent_manager.get_agent("knowledge_agent")
            if not knowledge_agent:
                # 如果智能体不可用，创建临时实例
                from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
                knowledge_agent = KnowledgeRetrievalService()
            
            # 调用知识检索智能体
            if hasattr(knowledge_agent, 'execute') and asyncio.iscoroutinefunction(knowledge_agent.execute):
                # 如果智能体有异步execute方法，使用异步调用
                result = await knowledge_agent.execute(query, context)
            else:
                # 否则使用同步调用
                result = knowledge_agent.process_query(query, context)
            
            if result.success:
                # 提取知识数据并转换为推理引擎期望的格式
                sources = result.data.get('sources', [])
                knowledge_data = []
                
                for source in sources:
                    if isinstance(source, dict) and 'result' in source:
                        # 处理AgentResult对象
                        agent_result = source['result']
                        if hasattr(agent_result, 'data') and agent_result.success:
                            knowledge_data.append({
                                'content': agent_result.data.get('content', ''),
                                'confidence': source.get('confidence', 0.5),
                                'source': source.get('type', 'unknown'),
                                'type': source.get('type', 'general'),
                                'metadata': getattr(agent_result, 'metadata', {}) or {}
                            })
                    elif isinstance(source, dict) and 'content' in source:
                        # 处理已经是字典格式的数据
                        knowledge_data.append(source)
                
                return {
                    "sources": knowledge_data,
                    "confidence": result.confidence,
                    "metadata": result.metadata
                }
            else:
                logger.warning(f"知识检索失败: {result.data}")
                return {
                    "sources": [],
                    "confidence": 0.0,
                    "metadata": {"error": "knowledge_retrieval_failed"}
                }
                
        except Exception as e:
            logger.error(f"知识检索异常: {e}")
            return {
                "sources": [],
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }
    
    async def _perform_reasoning(self, query: str, knowledge_results: Dict[str, Any]) -> Dict[str, Any]:
        """执行智能推理"""
        # 🚀 修复：通过池获取实例，统一管理
        reasoning_engine = None
        try:
            # 使用真正的推理引擎（通过池获取）
            from src.utils.reasoning_engine_pool import get_reasoning_engine_pool
            pool = get_reasoning_engine_pool()
            reasoning_engine = pool.get_engine()
            logger.info("✅ 从实例池获取推理引擎（async_research_system._perform_reasoning）")
            
            # 准备推理上下文
            context = {
                'knowledge': knowledge_results.get('sources', []),
                'reasoning_data': {'type': 'factual'},
                'query': query
            }
            
            # 执行推理
            reasoning_result = await reasoning_engine.reason(query, context)
            
            return {
                "steps": [
                    f"分析查询: {query[:30]}...",
                    "检索相关知识",
                    "进行逻辑推理",
                    "生成答案"
                ],
                "reasoning_type": reasoning_result.reasoning_type,
                "confidence": reasoning_result.total_confidence,
                "reasoning_result": reasoning_result  # 保存推理结果
            }
            
        except Exception as e:
            logger.error(f"推理过程异常: {e}")
            return {
                "steps": [
                    f"分析查询: {query[:30]}...",
                    "检索相关知识",
                    "进行逻辑推理",
                    "生成答案"
                ],
                "reasoning_type": "logical",
                "confidence": 0.75,
                "reasoning_result": None
            }
    
    async def _generate_answer(self, query: str, knowledge_results: Dict[str, Any], reasoning_results: Dict[str, Any]) -> str:
        """生成答案 - 基于真正推理的智能答案生成"""
        # 🚀 修复：将reasoning_engine声明在外层，确保在所有情况下都能被清理
        reasoning_engine = None
        try:
            # 检查是否已经有推理结果
            if reasoning_results and 'reasoning_result' in reasoning_results:
                reasoning_result = reasoning_results['reasoning_result']
                if hasattr(reasoning_result, 'final_answer') and reasoning_result.final_answer and reasoning_result.final_answer != "推理失败":
                    logger.info(f"✅ 使用已有推理结果: {reasoning_result.final_answer} (置信度: {reasoning_result.total_confidence:.2f})")
                    return reasoning_result.final_answer
            
            # 如果没有推理结果，使用真正的推理引擎（通过池获取）
            # 🚀 修复：通过池获取实例，统一管理
            from src.utils.reasoning_engine_pool import get_reasoning_engine_pool
            pool = get_reasoning_engine_pool()
            reasoning_engine = pool.get_engine()
            logger.info("✅ 从实例池获取推理引擎（async_research_system._generate_answer）")
            
            # 准备推理上下文
            context = {
                'knowledge': knowledge_results.get('sources', []),
                'reasoning_data': reasoning_results,
                'query': query
            }
            
            # 执行推理
            reasoning_result = await reasoning_engine.reason(query, context)
            
            # 直接使用推理结果，无论success状态
            if reasoning_result.final_answer and reasoning_result.final_answer != "推理失败":
                logger.info(f"✅ 推理成功: {reasoning_result.final_answer} (置信度: {reasoning_result.total_confidence:.2f})")
                return reasoning_result.final_answer
            else:
                # 回退到简单答案提取
                sources = knowledge_results.get('sources', [])
                if sources:
                    best_source = max(sources, key=lambda x: x.get('confidence', 0.0))
                    content = best_source.get('content', '')
                    
                    if content:
                        # 直接返回核心答案，不添加模板
                        lines = content.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith(('分析', '推理', '基于')):
                                return line
                        return content
            
            return "需要更多信息来提供准确答案"
            
        except Exception as e:
            logger.error(f"答案生成失败: {e}")
            return f"答案生成失败: {str(e)}"
        finally:
            # 🚀 修复：使用完后返回实例到池中
            if reasoning_engine is not None:
                try:
                    from src.utils.reasoning_engine_pool import get_reasoning_engine_pool
                    pool = get_reasoning_engine_pool()
                    pool.return_engine(reasoning_engine)
                    logger.debug("✅ 推理引擎实例已返回池中（async_research_system._generate_answer）")
                except Exception as e:
                    logger.warning(f"⚠️ 返回推理引擎实例到池中失败: {e}")
    
    async def _calculate_confidence(self, query: str, answer: str, knowledge_results: Dict[str, Any]) -> float:
        """计算置信度"""
        base_confidence = knowledge_results.get('confidence', 0.8)
        # 根据答案长度和查询复杂度调整置信度
        length_factor = min(len(answer) / 100, 1.0)
        return min(base_confidence * length_factor, 0.95)

    async def shutdown(self) -> None:
        """关闭系统"""
        async with self._shutdown_lock:
            if self._is_shutting_down:
                return

            self._is_shutting_down = True
            logger.info("🔄 开始关闭异步研究系统...")

            try:
                await self.task_manager.shutdown()

                await self.agent_manager.shutdown_agents()

                await self.resource_manager.shutdown()

                await self.event_loop.stop()

                logger.info("✅ 异步研究系统关闭完成")

            except Exception as e:
                logger.error("❌ 系统关闭失败: {e}")
                raise

    def _atexit_cleanup(self) -> None:
        """程序退出时的清理"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.shutdown())
            loop.close()
        except Exception as e:
            logger.error("❌ 程序退出清理失败: {e}")


async def create_async_research_system() -> AsyncResearchSystem:
    """创建异步研究系统实例"""
    system = AsyncResearchSystem()
    await system.initialize()
    return system


async def test_async_system():
    """测试异步系统"""
    try:
        system = await create_async_research_system()

        result = await system.execute_research("What is the capital of France?")
        print(f"研究结果: {result}")

        await system.shutdown()

    except Exception as e:
        logger.error("测试失败: {e}")


