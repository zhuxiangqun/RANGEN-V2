"""
能力编排引擎 - P3阶段能力架构优化

实现强大的能力编排和动态管理：
1. 能力编排DSL (Domain Specific Language)
2. 动态能力加载和热插拔
3. 能力依赖管理和版本控制
4. 复合能力构建和组合
5. 编排执行优化和监控
6. 智能资源调度

替代简单的能力调用，实现复杂的能力编排和智能化管理。
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, List, Optional, Union, Callable, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import importlib
import inspect

logger = logging.getLogger(__name__)


class OrchestrationMode(Enum):
    """编排模式"""
    SEQUENTIAL = "sequential"      # 顺序执行
    PARALLEL = "parallel"          # 并行执行
    CONDITIONAL = "conditional"    # 条件执行
    LOOP = "loop"                  # 循环执行
    PIPELINE = "pipeline"          # 管道执行
    DAG = "dag"                    # 有向无环图执行


class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class CapabilityNode:
    """编排图中的能力节点"""
    node_id: str
    capability_name: str
    version: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # 前置节点ID
    timeout: Optional[float] = None
    retry_count: int = 0
    retry_delay: float = 1.0
    condition: Optional[str] = None  # 条件表达式

    # 执行状态
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_count: int = 0


@dataclass
class OrchestrationPlan:
    """编排执行计划"""
    plan_id: str
    name: str
    description: str
    mode: OrchestrationMode
    nodes: Dict[str, CapabilityNode] = field(default_factory=dict)
    entry_points: List[str] = field(default_factory=list)  # 入口节点ID
    exit_points: List[str] = field(default_factory=list)   # 出口节点ID

    # 执行配置
    global_timeout: Optional[float] = None
    max_parallel: int = 5
    fail_fast: bool = True  # 遇到失败是否立即停止

    # 监控和统计
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    status: ExecutionStatus = ExecutionStatus.PENDING


@dataclass
class ExecutionContext:
    """执行上下文"""
    plan_id: str
    node_id: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 父子关系
    parent_context: Optional['ExecutionContext'] = None
    child_contexts: List['ExecutionContext'] = field(default_factory=list)


class CapabilityOrchestrationEngine:
    """能力编排引擎

    核心功能：
    1. DSL解析和编排图构建
    2. 智能执行调度（顺序/并行/条件）
    3. 动态能力加载和管理
    4. 依赖关系解析和死锁检测
    5. 执行监控和性能优化
    6. 错误处理和恢复机制
    """

    def __init__(self):
        # 能力服务集成
        from .capability_service import get_capability_service
        self.capability_service = get_capability_service()

        # 编排计划缓存
        self.plan_cache: Dict[str, OrchestrationPlan] = {}
        self.execution_cache: Dict[str, ExecutionContext] = {}

        # 动态能力加载器
        self.capability_loader = DynamicCapabilityLoader()

        # 编排统计
        self.orchestration_stats = OrchestrationStatistics()

        logger.info("✅ 能力编排引擎初始化完成")

    async def execute_orchestration(self, plan_or_dsl: Union[str, OrchestrationPlan],
                                   inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行编排计划"""
        start_time = time.time()

        try:
            # 解析计划
            if isinstance(plan_or_dsl, str):
                plan = self._parse_dsl(plan_or_dsl)
            else:
                plan = plan_or_dsl

            plan.executed_at = datetime.now()
            plan.status = ExecutionStatus.RUNNING

            # 创建执行上下文
            root_context = ExecutionContext(
                plan_id=plan.plan_id,
                node_id="root",
                inputs=inputs or {},
                metadata={"plan_name": plan.name}
            )

            # 执行编排
            result = await self._execute_plan(plan, root_context)

            # 更新统计
            plan.execution_time = time.time() - start_time
            plan.status = ExecutionStatus.COMPLETED

            self.orchestration_stats.record_execution(plan, True, plan.execution_time)

            logger.info(f"✅ 编排执行完成: {plan.name} ({plan.execution_time:.3f}s)")
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 编排执行失败: {e}")

            if 'plan' in locals():
                plan.status = ExecutionStatus.FAILED
                plan.execution_time = execution_time
                self.orchestration_stats.record_execution(plan, False, execution_time)

            raise

    def _parse_dsl(self, dsl: str) -> OrchestrationPlan:
        """解析编排DSL"""
        # 检查缓存
        if dsl in self.plan_cache:
            return self.plan_cache[dsl]

        try:
            # 解析DSL
            plan_data = self._parse_dsl_string(dsl)

            # 转换节点为CapabilityNode对象
            nodes = {}
            for node_id, node_data in plan_data.get("nodes", {}).items():
                if isinstance(node_data, dict):
                    nodes[node_id] = CapabilityNode(
                        node_id=node_id,
                        capability_name=node_data.get("capability_name", node_id),
                        version=node_data.get("version"),
                        parameters=node_data.get("parameters", {}),
                        dependencies=node_data.get("dependencies", []),
                        timeout=node_data.get("timeout"),
                        retry_count=node_data.get("retry_count", 0),
                        retry_delay=node_data.get("retry_delay", 1.0),
                        condition=node_data.get("condition")
                    )
                else:
                    nodes[node_id] = node_data

            # 创建编排计划
            plan = OrchestrationPlan(
                plan_id=f"plan_{int(time.time())}_{hash(dsl) % 10000}",
                name=plan_data.get("name", f"DSL_Plan_{len(self.plan_cache)}"),
                description=plan_data.get("description", ""),
                mode=plan_data.get("mode", OrchestrationMode.SEQUENTIAL),
                nodes=nodes,
                entry_points=plan_data.get("entry_points", []),
                exit_points=plan_data.get("exit_points", []),
                global_timeout=plan_data.get("global_timeout"),
                max_parallel=plan_data.get("max_parallel", 5),
                fail_fast=plan_data.get("fail_fast", True)
            )

            # 缓存计划
            self.plan_cache[dsl] = plan

            return plan

        except Exception as e:
            logger.error(f"DSL解析失败: {e}")
            raise ValueError(f"无效的编排DSL: {e}")

    def _parse_dsl_string(self, dsl: str) -> Dict[str, Any]:
        """解析DSL字符串

        支持的DSL格式：
        1. 简单序列: "cap1 -> cap2 -> cap3"
        2. 并行执行: "cap1 | cap2 -> cap3"
        3. 条件执行: "cap1 ? cap2 : cap3"
        4. 复杂DSL: JSON格式或YAML格式
        """
        dsl = dsl.strip()

        # 检查是否为JSON格式
        if dsl.startswith('{'):
            return json.loads(dsl)

        # 检查是否为YAML格式（简化处理）
        if dsl.startswith('name:') or dsl.startswith('mode:'):
            # 简化的YAML解析（实际应该使用PyYAML）
            return self._parse_simple_yaml(dsl)

        # 解析简单DSL
        return self._parse_simple_dsl(dsl)

    def _parse_simple_dsl(self, dsl: str) -> Dict[str, Any]:
        """解析简单DSL格式"""
        plan_data = {
            "name": f"Simple_Plan_{hash(dsl) % 1000}",
            "description": "自动生成的简单编排计划",
            "mode": OrchestrationMode.SEQUENTIAL,
            "nodes": {},
            "entry_points": [],
            "exit_points": []
        }

        # 解析管道和并行
        if '|' in dsl and '->' in dsl:
            # 并行-顺序组合: "cap1 | cap2 -> cap3"
            parts = dsl.split('->')
            parallel_part = parts[0].strip()
            sequential_part = parts[1].strip() if len(parts) > 1 else None

            parallel_caps = [cap.strip() for cap in parallel_part.split('|')]
            sequential_caps = [sequential_part] if sequential_part else []

            plan_data["mode"] = OrchestrationMode.PIPELINE

            # 创建并行节点
            for i, cap in enumerate(parallel_caps):
                node_id = f"parallel_{i}"
                plan_data["nodes"][node_id] = {
                    "node_id": node_id,
                    "capability_name": cap,
                    "dependencies": []
                }
                plan_data["entry_points"].append(node_id)

            # 创建顺序节点
            if sequential_caps:
                for i, cap in enumerate(sequential_caps):
                    node_id = f"sequential_{i}"
                    deps = [f"parallel_{j}" for j in range(len(parallel_caps))] if i == 0 else [f"sequential_{i-1}"]
                    plan_data["nodes"][node_id] = {
                        "node_id": node_id,
                        "capability_name": cap,
                        "dependencies": deps
                    }
                    if i == len(sequential_caps) - 1:
                        plan_data["exit_points"].append(node_id)

        elif '->' in dsl:
            # 纯顺序执行: "cap1 -> cap2 -> cap3"
            capabilities = [cap.strip() for cap in dsl.split('->')]
            plan_data["mode"] = OrchestrationMode.SEQUENTIAL

            for i, cap in enumerate(capabilities):
                node_id = f"seq_{i}"
                deps = [f"seq_{i-1}"] if i > 0 else []
                plan_data["nodes"][node_id] = {
                    "node_id": node_id,
                    "capability_name": cap,
                    "dependencies": deps
                }
                if i == 0:
                    plan_data["entry_points"].append(node_id)
                if i == len(capabilities) - 1:
                    plan_data["exit_points"].append(node_id)

        else:
            # 单能力执行
            plan_data["nodes"]["single"] = {
                "node_id": "single",
                "capability_name": dsl,
                "dependencies": []
            }
            plan_data["entry_points"] = ["single"]
            plan_data["exit_points"] = ["single"]

        return plan_data

    def _parse_simple_yaml(self, yaml_str: str) -> Dict[str, Any]:
        """简化的YAML解析（实际应该使用PyYAML）"""
        # 这是一个简化的实现，实际项目中应该使用专业的YAML解析库
        lines = yaml_str.split('\n')
        result = {}

        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                if value.startswith('[') and value.endswith(']'):
                    # 数组
                    result[key] = [item.strip() for item in value[1:-1].split(',')]
                else:
                    result[key] = value

        return result

    async def _execute_plan(self, plan: OrchestrationPlan, root_context: ExecutionContext) -> Dict[str, Any]:
        """执行编排计划"""
        if plan.mode == OrchestrationMode.SEQUENTIAL:
            return await self._execute_sequential(plan, root_context)
        elif plan.mode == OrchestrationMode.PARALLEL:
            return await self._execute_parallel(plan, root_context)
        elif plan.mode == OrchestrationMode.PIPELINE:
            return await self._execute_pipeline(plan, root_context)
        elif plan.mode == OrchestrationMode.DAG:
            return await self._execute_dag(plan, root_context)
        else:
            raise ValueError(f"不支持的编排模式: {plan.mode}")

    async def _execute_sequential(self, plan: OrchestrationPlan, context: ExecutionContext) -> Dict[str, Any]:
        """顺序执行"""
        current_inputs = context.inputs.copy()
        results = {}

        for node_id in self._get_execution_order(plan):
            node = plan.nodes[node_id]
            if node.status == ExecutionStatus.COMPLETED:
                continue

            try:
                # 执行节点
                node.status = ExecutionStatus.RUNNING
                node.start_time = time.time()

                # 准备输入
                node_inputs = self._prepare_node_inputs(node, current_inputs, results)

                # 执行能力
                result = await self._execute_capability_node(node, node_inputs, context)

                # 更新结果
                results[node_id] = result
                current_inputs.update(result)  # 结果传递给后续节点

                node.status = ExecutionStatus.COMPLETED
                node.end_time = time.time()
                node.result = result

            except Exception as e:
                node.status = ExecutionStatus.FAILED
                node.error = str(e)
                node.end_time = time.time()

                if plan.fail_fast:
                    raise
                else:
                    logger.warning(f"节点执行失败，继续执行: {node_id} - {e}")

        return self._collect_final_results(plan, results)

    async def _execute_parallel(self, plan: OrchestrationPlan, context: ExecutionContext) -> Dict[str, Any]:
        """并行执行"""
        # 获取可并行执行的节点
        executable_nodes = [node_id for node_id in plan.entry_points
                          if self._are_dependencies_satisfied(plan.nodes[node_id], plan.nodes)]

        if not executable_nodes:
            return {}

        # 限制并行度
        max_parallel = min(plan.max_parallel, len(executable_nodes))
        executable_nodes = executable_nodes[:max_parallel]

        # 创建并行任务
        tasks = []
        for node_id in executable_nodes:
            node = plan.nodes[node_id]
            task = self._execute_single_node(node, context)
            tasks.append((node_id, task))

        # 执行并等待
        results = {}
        completed_tasks = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

        for i, result in enumerate(completed_tasks):
            node_id, _ = tasks[i]
            if isinstance(result, Exception):
                plan.nodes[node_id].status = ExecutionStatus.FAILED
                plan.nodes[node_id].error = str(result)
                if plan.fail_fast:
                    raise result
            else:
                results[node_id] = result
                plan.nodes[node_id].status = ExecutionStatus.COMPLETED
                plan.nodes[node_id].result = result

        return results

    async def _execute_pipeline(self, plan: OrchestrationPlan, context: ExecutionContext) -> Dict[str, Any]:
        """管道执行（并行阶段 + 顺序阶段）"""
        # 首先执行并行阶段
        parallel_results = await self._execute_parallel(plan, context)

        # 然后执行顺序阶段
        sequential_context = ExecutionContext(
            plan_id=context.plan_id,
            node_id="sequential_phase",
            inputs={**context.inputs, **parallel_results},
            parent_context=context
        )

        # 找到顺序阶段的入口节点
        sequential_entries = []
        for node_id, node in plan.nodes.items():
            if all(dep in parallel_results for dep in node.dependencies):
                sequential_entries.append(node_id)

        if sequential_entries:
            # 执行顺序阶段
            sequential_results = {}
            current_inputs = {**parallel_results}

            for node_id in sequential_entries:
                node = plan.nodes[node_id]
                node_inputs = self._prepare_node_inputs(node, current_inputs, sequential_results)
                result = await self._execute_capability_node(node, node_inputs, sequential_context)
                sequential_results[node_id] = result
                current_inputs.update(result)

            parallel_results.update(sequential_results)

        return parallel_results

    async def _execute_dag(self, plan: OrchestrationPlan, context: ExecutionContext) -> Dict[str, Any]:
        """DAG执行（有向无环图）"""
        results = {}
        visited = set()
        executing = set()

        async def execute_node(node_id: str) -> Any:
            if node_id in visited:
                return results.get(node_id)

            if node_id in executing:
                raise ValueError(f"检测到循环依赖: {node_id}")

            executing.add(node_id)
            node = plan.nodes[node_id]

            try:
                # 等待依赖完成
                dep_tasks = []
                for dep_id in node.dependencies:
                    if dep_id not in results:
                        dep_tasks.append(execute_node(dep_id))

                if dep_tasks:
                    dep_results = await asyncio.gather(*dep_tasks)

                # 准备输入
                node_inputs = self._prepare_node_inputs(node, context.inputs, results)

                # 执行节点
                result = await self._execute_capability_node(node, node_inputs, context)
                results[node_id] = result

                node.status = ExecutionStatus.COMPLETED
                return result

            finally:
                executing.remove(node_id)
                visited.add(node_id)

        # 执行所有节点
        execution_tasks = [execute_node(node_id) for node_id in plan.entry_points]
        await asyncio.gather(*execution_tasks)

        return self._collect_final_results(plan, results)

    def _get_execution_order(self, plan: OrchestrationPlan) -> List[str]:
        """获取执行顺序（拓扑排序）"""
        # 简化的拓扑排序实现
        order = []
        visited = set()
        visiting = set()

        def visit(node_id: str):
            if node_id in visiting:
                raise ValueError(f"检测到循环依赖: {node_id}")
            if node_id in visited:
                return

            visiting.add(node_id)

            # 访问依赖
            for dep_id in plan.nodes[node_id].dependencies:
                visit(dep_id)

            visiting.remove(node_id)
            visited.add(node_id)
            order.append(node_id)

        # 从入口点开始
        for entry_id in plan.entry_points:
            visit(entry_id)

        return order

    async def _execute_single_node(self, node: CapabilityNode, context: ExecutionContext) -> Any:
        """执行单个节点"""
        node.status = ExecutionStatus.RUNNING
        node.start_time = time.time()
        node.execution_count += 1

        try:
            # 准备输入
            node_inputs = self._prepare_node_inputs(node, context.inputs, {})

            # 执行能力
            result = await self._execute_capability_node(node, node_inputs, context)

            node.status = ExecutionStatus.COMPLETED
            node.end_time = time.time()
            node.result = result

            return result

        except Exception as e:
            node.status = ExecutionStatus.FAILED
            node.error = str(e)
            node.end_time = time.time()
            raise

    def _prepare_node_inputs(self, node: CapabilityNode, global_inputs: Dict[str, Any],
                           previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """准备节点输入"""
        inputs = global_inputs.copy()

        # 添加前置节点结果
        for dep_id in node.dependencies:
            if dep_id in previous_results:
                inputs.update(previous_results[dep_id])

        # 添加节点特定参数
        inputs.update(node.parameters)

        return inputs

    async def _execute_capability_node(self, node: CapabilityNode, inputs: Dict[str, Any],
                                     context: ExecutionContext) -> Any:
        """执行能力节点"""
        # 动态加载能力
        capability = await self.capability_loader.load_capability(node.capability_name, node.version)

        # 设置超时
        timeout = node.timeout or 30.0  # 默认30秒超时

        try:
            # 执行能力（带重试）
            result = await self._execute_with_retry(
                capability, inputs, node.retry_count, node.retry_delay, timeout
            )

            return result

        except Exception as e:
            logger.error(f"能力执行失败: {node.capability_name} - {e}")
            raise

    async def _execute_with_retry(self, capability: Callable, inputs: Dict[str, Any],
                                retry_count: int, retry_delay: float, timeout: float) -> Any:
        """带重试的执行"""
        last_exception = None

        for attempt in range(retry_count + 1):
            try:
                # 创建超时任务
                execution_task = capability(inputs)
                result = await asyncio.wait_for(execution_task, timeout=timeout)
                return result

            except Exception as e:
                last_exception = e
                if attempt < retry_count:
                    logger.warning(f"执行失败，重试 {attempt + 1}/{retry_count}: {e}")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"执行失败，已达到最大重试次数: {e}")

        # 确保有有效的异常对象
        if last_exception is not None:
            raise last_exception
        else:
            # 这不应该发生，但为了安全起见
            raise RuntimeError("执行失败，但没有捕获到异常信息")

    def _collect_final_results(self, plan: OrchestrationPlan, results: Dict[str, Any]) -> Dict[str, Any]:
        """收集最终结果"""
        final_result = {}

        # 收集出口节点的结果
        for exit_id in plan.exit_points:
            if exit_id in results:
                final_result.update(results[exit_id])

        # 如果没有指定出口节点，返回所有结果
        if not final_result:
            final_result = results

        return final_result

    def _are_dependencies_satisfied(self, node: CapabilityNode, all_nodes: Dict[str, CapabilityNode]) -> bool:
        """检查依赖是否满足"""
        for dep_id in node.dependencies:
            if dep_id not in all_nodes:
                return False
            dep_node = all_nodes[dep_id]
            if dep_node.status != ExecutionStatus.COMPLETED:
                return False
        return True

    def get_orchestration_stats(self) -> Dict[str, Any]:
        """获取编排统计信息"""
        return self.orchestration_stats.get_stats()

    def create_composite_capability(self, name: str, orchestration_dsl: str,
                                  description: str = "") -> str:
        """创建复合能力"""
        composite_cap_id = f"composite_{name}_{int(time.time())}"

        # 将编排注册为复合能力
        async def composite_execute(context: Dict[str, Any]) -> Dict[str, Any]:
            return await self.execute_orchestration(orchestration_dsl, context)

        # 注册到能力服务
        from .capability_service import CapabilityInterface

        class CompositeCapability(CapabilityInterface):
            @property
            def name(self) -> str:
                return composite_cap_id

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def description(self) -> str:
                return description or f"复合能力: {name}"

            @property
            def capabilities(self) -> List[str]:
                return ["composite", "orchestration"]

            @property
            def metadata(self) -> Dict[str, Any]:
                return {
                    "type": "composite",
                    "base_dsl": orchestration_dsl,
                    "created_at": datetime.now().isoformat()
                }

            async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
                return await composite_execute(context)

            async def health_check(self) -> bool:
                return True

        self.capability_service.register_capability(CompositeCapability())

        logger.info(f"✅ 复合能力创建成功: {composite_cap_id}")
        return composite_cap_id


class DynamicCapabilityLoader:
    """动态能力加载器"""

    def __init__(self):
        self.loaded_capabilities: Dict[str, Any] = {}
        self.capability_versions: Dict[str, Dict[str, Any]] = {}

    async def load_capability(self, name: str, version: Optional[str] = None) -> Callable:
        """动态加载能力"""
        cache_key = f"{name}:{version or 'latest'}"

        if cache_key in self.loaded_capabilities:
            return self.loaded_capabilities[cache_key]

        try:
            # 首先尝试从能力服务获取
            from .capability_service import get_capability_service
            capability_service = get_capability_service()

            try:
                # 这里应该有一个方法来获取能力的执行函数
                # 暂时使用mock实现
                capability = await self._load_from_service(capability_service, name, version)
                self.loaded_capabilities[cache_key] = capability
                return capability

            except Exception:
                # 如果服务中没有，尝试动态导入
                capability = await self._load_from_module(name, version)
                self.loaded_capabilities[cache_key] = capability
                return capability

        except Exception as e:
            logger.error(f"能力加载失败: {name} v{version} - {e}")
            raise

    async def _load_from_service(self, service, name: str, version: Optional[str]) -> Callable:
        """从能力服务加载"""
        # 这里需要能力服务提供获取执行函数的接口
        # 暂时使用mock
        async def mock_execute(context: Dict[str, Any]) -> Dict[str, Any]:
            await asyncio.sleep(0.1)  # 模拟执行时间
            return {f"{name}_result": f"Executed {name} with {context}"}

        return mock_execute

    async def _load_from_module(self, name: str, version: Optional[str]) -> Callable:
        """从模块动态加载"""
        # 尝试导入对应的模块
        module_name = f"src.agents.capabilities.{name}"

        try:
            module = importlib.import_module(module_name)

            # 查找执行函数
            if hasattr(module, 'execute'):
                return module.execute
            elif hasattr(module, f'execute_{name}'):
                return getattr(module, f'execute_{name}')
            else:
                # 查找类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (inspect.isclass(attr) and
                        hasattr(attr, 'execute') and
                        callable(getattr(attr, 'execute'))):
                        instance = attr()
                        return instance.execute

        except ImportError:
            pass

        # 如果都找不到，返回mock实现
        logger.warning(f"使用mock实现能力: {name}")
        async def mock_execute(context: Dict[str, Any]) -> Dict[str, Any]:
            await asyncio.sleep(0.05)
            return {f"mock_{name}_result": f"Mock executed {name}"}

        return mock_execute


@dataclass
class OrchestrationStatistics:
    """编排统计信息"""

    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0.0
    total_execution_time: float = 0.0

    # 按模式统计
    mode_stats: Dict[OrchestrationMode, Dict[str, Any]] = field(default_factory=dict)

    def record_execution(self, plan: OrchestrationPlan, success: bool, execution_time: float):
        """记录执行统计"""
        self.total_executions += 1
        self.total_execution_time += execution_time

        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1

        self.average_execution_time = self.total_execution_time / self.total_executions

        # 按模式统计
        if plan.mode not in self.mode_stats:
            self.mode_stats[plan.mode] = {
                'count': 0,
                'success_count': 0,
                'total_time': 0.0,
                'avg_time': 0.0
            }

        mode_stat = self.mode_stats[plan.mode]
        mode_stat['count'] += 1
        mode_stat['total_time'] += execution_time
        mode_stat['avg_time'] = mode_stat['total_time'] / mode_stat['count']

        if success:
            mode_stat['success_count'] += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = self.successful_executions / self.total_executions if self.total_executions > 0 else 0

        return {
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'success_rate': success_rate,
            'average_execution_time': self.average_execution_time,
            'total_execution_time': self.total_execution_time,
            'mode_breakdown': {
                mode.value: stats for mode, stats in self.mode_stats.items()
            }
        }


# 全局编排引擎实例
_orchestration_engine_instance: Optional[CapabilityOrchestrationEngine] = None


def get_orchestration_engine() -> CapabilityOrchestrationEngine:
    """获取编排引擎实例"""
    global _orchestration_engine_instance
    if _orchestration_engine_instance is None:
        _orchestration_engine_instance = CapabilityOrchestrationEngine()
    return _orchestration_engine_instance