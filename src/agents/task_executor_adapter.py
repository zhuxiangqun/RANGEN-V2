"""
任务执行器适配器：TaskExecutorAdapter

将现有的LangGraph节点适配为标准化的TaskExecutor接口，
实现新架构与现有系统的无缝集成。
"""

import logging
from typing import Dict, List, Any, Optional, Protocol
from abc import ABC, abstractmethod

from src.core.layered_architecture_types import TaskResult, TaskType

logger = logging.getLogger(__name__)


class TaskExecutor(Protocol):
    """任务执行器协议"""

    async def execute(self, task_input: Dict[str, Any]) -> Any:
        """执行任务"""
        ...


class LangGraphNodeAdapter(TaskExecutor):
    """
    LangGraph节点适配器

    将现有的LangGraph节点适配为TaskExecutor接口
    """

    def __init__(self, node_func: callable, node_name: str):
        self.node_func = node_func
        self.node_name = node_name
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def execute(self, task_input: Dict[str, Any]) -> Any:
        """执行任务（适配LangGraph节点）"""

        try:
            # 构建LangGraph状态
            state = self._build_langgraph_state(task_input)

            # 调用节点函数
            result_state = await self.node_func(state)

            # 提取执行结果
            result = self._extract_result(result_state, task_input)

            self.logger.debug(f"✅ [LangGraphNodeAdapter] {self.node_name} 执行成功")
            return result

        except Exception as e:
            self.logger.error(f"❌ [LangGraphNodeAdapter] {self.node_name} 执行失败: {e}")
            raise

    def _build_langgraph_state(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """构建LangGraph状态"""
        # 基础状态
        state = {
            'query': task_input.get('query', ''),
            'task_id': task_input.get('task_id', ''),
            'task_type': task_input.get('task_type', ''),
            'metadata': task_input.get('metadata', {}),
        }

        # 根据任务类型添加特定字段
        task_type = task_input.get('task_type')

        if task_type == 'knowledge_retrieval':
            state.update({
                'knowledge_sources': [],
                'evidence': [],
                'retrieval_timeout': task_input.get('timeout', 30.0)
            })

        elif task_type == 'reasoning':
            state.update({
                'reasoning_chain': [],
                'intermediate_steps': [],
                'reasoning_timeout': task_input.get('timeout', 120.0)
            })

        elif task_type == 'answer_generation':
            state.update({
                'final_answer': '',
                'citations': [],
                'answer_quality_score': 0.0
            })

        elif task_type == 'citation':
            state.update({
                'citation_sources': [],
                'citation_format': 'academic'
            })

        return state

    def _extract_result(self, result_state: Dict[str, Any], task_input: Dict[str, Any]) -> Any:
        """从LangGraph结果状态提取执行结果"""

        task_type = task_input.get('task_type')

        if task_type == 'knowledge_retrieval':
            return {
                'knowledge': result_state.get('knowledge', []),
                'evidence': result_state.get('evidence', []),
                'sources': result_state.get('knowledge_sources', []),
                'quality_score': 0.8
            }

        elif task_type == 'reasoning':
            return {
                'reasoning': result_state.get('reasoning', ''),
                'intermediate_steps': result_state.get('intermediate_steps', []),
                'confidence_score': result_state.get('confidence_score', 0.7),
                'quality_score': 0.8
            }

        elif task_type == 'answer_generation':
            return {
                'answer': result_state.get('final_answer', ''),
                'citations': result_state.get('citations', []),
                'quality_score': result_state.get('answer_quality_score', 0.8)
            }

        elif task_type == 'citation':
            return {
                'citations': result_state.get('citation_sources', []),
                'formatted_citations': result_state.get('formatted_citations', []),
                'quality_score': 0.9
            }

        else:
            # 默认结果
            return {
                'result': result_state.get('result', ''),
                'quality_score': 0.7
            }


class TaskExecutorRegistry:
    """
    任务执行器注册表

    管理所有任务类型的执行器注册和查找
    """

    def __init__(self):
        self._executors: Dict[str, TaskExecutor] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def register(self, task_type: str, executor: TaskExecutor):
        """注册任务执行器"""
        self._executors[task_type] = executor
        self.logger.info(f"✅ [TaskExecutorRegistry] 注册执行器: {task_type}")

    def get_executor(self, task_type: str) -> Optional[TaskExecutor]:
        """获取任务执行器"""
        return self._executors.get(task_type)

    def list_executors(self) -> List[str]:
        """列出所有已注册的执行器"""
        return list(self._executors.keys())

    def unregister(self, task_type: str):
        """注销任务执行器"""
        if task_type in self._executors:
            del self._executors[task_type]
            self.logger.info(f"✅ [TaskExecutorRegistry] 注销执行器: {task_type}")


class UnifiedTaskExecutor(TaskExecutor):
    """
    统一任务执行器

    根据任务类型自动选择合适的执行器
    """

    def __init__(self, registry: TaskExecutorRegistry):
        self.registry = registry
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def execute(self, task_input: Dict[str, Any]) -> Any:
        """统一执行任务"""

        task_type = task_input.get('task_type')
        if not task_type:
            raise ValueError("任务输入中必须包含task_type字段")

        # 获取执行器
        executor = self.registry.get_executor(task_type)
        if not executor:
            raise ValueError(f"未找到任务类型'{task_type}'的执行器")

        # 执行任务
        self.logger.debug(f"🎯 [UnifiedTaskExecutor] 执行任务: {task_type}")
        result = await executor.execute(task_input)

        return result


# 全局执行器注册表实例
_global_registry = TaskExecutorRegistry()


def get_global_registry() -> TaskExecutorRegistry:
    """获取全局执行器注册表"""
    return _global_registry


def create_unified_executor() -> UnifiedTaskExecutor:
    """创建统一任务执行器"""
    return UnifiedTaskExecutor(_global_registry)


def register_langgraph_node(task_type: str, node_func: callable, node_name: str):
    """
    便捷函数：注册LangGraph节点

    Args:
        task_type: 任务类型
        node_func: 节点函数
        node_name: 节点名称（用于日志）
    """
    adapter = LangGraphNodeAdapter(node_func, node_name)
    _global_registry.register(task_type, adapter)


def register_task_executor(task_type: str, executor: TaskExecutor):
    """注册任务执行器"""
    _global_registry.register(task_type, executor)


# 初始化常用执行器
def initialize_default_executors():
    """初始化默认执行器（基于现有LangGraph节点）"""

    try:
        # 导入现有节点（这需要根据实际项目结构调整）
        from src.core.langgraph_agent_nodes import (
            knowledge_retrieval_agent,
            reasoning_agent,
            answer_generation_agent,
            citation_agent
        )

        # 注册默认执行器
        register_langgraph_node('knowledge_retrieval', knowledge_retrieval_agent, 'knowledge_retrieval_agent')
        register_langgraph_node('reasoning', reasoning_agent, 'reasoning_agent')
        register_langgraph_node('answer_generation', answer_generation_agent, 'answer_generation_agent')
        register_langgraph_node('citation', citation_agent, 'citation_agent')

        logger.info("✅ [TaskExecutorAdapter] 默认执行器初始化完成")

    except ImportError as e:
        logger.warning(f"⚠️ [TaskExecutorAdapter] 无法导入现有节点: {e}")
        logger.info("ℹ️ [TaskExecutorAdapter] 将使用模拟执行器进行测试")


class MockTaskExecutor(TaskExecutor):
    """模拟任务执行器（用于测试）"""

    def __init__(self, task_type: str, success_rate: float = 0.9):
        self.task_type = task_type
        self.success_rate = success_rate
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._execution_count = 0

    @property
    def name(self) -> str:
        return f"MockTaskExecutor_{self.task_type}"

    @property
    def supported_task_types(self):
        from src.core.layered_architecture_types import TaskType
        # 将字符串转换为TaskType枚举
        task_type_map = {
            'knowledge_retrieval': TaskType.KNOWLEDGE_RETRIEVAL,
            'reasoning': TaskType.REASONING,
            'answer_generation': TaskType.ANSWER_GENERATION,
            'citation': TaskType.CITATION,
            'analysis': TaskType.ANALYSIS,
            'memory': TaskType.MEMORY
        }
        return [task_type_map.get(self.task_type, TaskType.KNOWLEDGE_RETRIEVAL)]

    def get_info(self):
        from src.agents.enhanced_task_executor_registry import ExecutorInfo
        return ExecutorInfo(
            name=self.name,
            task_types=self.supported_task_types,
            version="1.0.0",
            description=f"模拟任务执行器 - {self.task_type}",
            capabilities=["mock", "test"]
        )

    async def execute(self, task_input: Dict[str, Any]) -> Any:
        """模拟执行任务"""
        import random
        import asyncio

        # 模拟执行时间
        execution_time = random.uniform(0.1, 2.0)
        await asyncio.sleep(execution_time)

        # 模拟成功/失败
        if random.random() < self.success_rate:
            # 成功结果
            result = {
                'task_type': self.task_type,
                'task_id': task_input.get('task_id'),
                'result': f"模拟{self.task_type}执行结果",
                'execution_time': execution_time,
                'quality_score': random.uniform(0.7, 0.95)
            }

            if self.task_type == 'knowledge_retrieval':
                result.update({
                    'knowledge': [f"知识片段{i}" for i in range(3)],
                    'evidence': [f"证据{i}" for i in range(2)]
                })
            elif self.task_type == 'reasoning':
                result.update({
                    'reasoning': "基于证据的推理结果...",
                    'intermediate_steps': ["步骤1", "步骤2", "步骤3"]
                })
            elif self.task_type == 'answer_generation':
                result['answer'] = "基于推理和知识的最终答案..."
            elif self.task_type == 'citation':
                result['citations'] = ["[1] 参考文献1", "[2] 参考文献2"]

            self.logger.debug(f"✅ [MockTaskExecutor] {self.task_type} 执行成功")
            return result
        else:
            # 失败结果
            error_msg = f"模拟{self.task_type}执行失败"
            self.logger.warning(f"⚠️ [MockTaskExecutor] {self.task_type} 执行失败: {error_msg}")
            raise Exception(error_msg)


# 初始化模拟执行器（用于测试）
def initialize_mock_executors():
    """初始化模拟执行器"""
    mock_types = ['knowledge_retrieval', 'reasoning', 'answer_generation', 'citation', 'analysis', 'memory']

    for task_type in mock_types:
        mock_executor = MockTaskExecutor(task_type)
        register_task_executor(task_type, mock_executor)

    logger.info("✅ [TaskExecutorAdapter] 模拟执行器初始化完成")


# 自动初始化
try:
    initialize_default_executors()
except Exception:
    logger.info("ℹ️ [TaskExecutorAdapter] 使用模拟执行器模式")
    initialize_mock_executors()
