"""
能力服务层 - 分层架构重构

将原本嵌入工作流的各种能力转换为独立的服务层：
1. 能力注册和发现
2. 能力执行引擎
3. 能力编排DSL
4. 能力监控和指标
5. 能力缓存和优化

替代原有的节点化能力架构，实现真正的服务化能力。
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Callable, Protocol
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class CapabilityInterface(Protocol):
    """能力接口协议"""

    @property
    def name(self) -> str:
        """能力名称"""
        ...

    @property
    def version(self) -> str:
        """能力版本"""
        ...

    @property
    def description(self) -> str:
        """能力描述"""
        ...

    @property
    def capabilities(self) -> List[str]:
        """支持的功能列表"""
        ...

    @property
    def metadata(self) -> Dict[str, Any]:
        """能力元数据"""
        ...

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行能力"""
        ...

    async def health_check(self) -> bool:
        """健康检查"""
        ...


@dataclass
class CapabilityMetrics:
    """能力执行指标"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    average_execution_time: float = 0.0
    last_execution_time: Optional[float] = None
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0


@dataclass
class CapabilityInfo:
    """能力信息"""
    capability: CapabilityInterface
    metrics: CapabilityMetrics = field(default_factory=CapabilityMetrics)
    registered_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None


class CapabilityService:
    """能力服务 - 统一的能力管理平台"""

    def __init__(self):
        self.capabilities: Dict[str, CapabilityInfo] = {}
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_enabled = True
        self.max_cache_size = 1000
        
        # 性能监控数据
        self.performance_metrics: Dict[str, List[Dict[str, Any]]] = {}  # 能力性能历史
        self.dependency_graph: Dict[str, List[str]] = {}  # 能力依赖关系图
        self.performance_alerts: List[Dict[str, Any]] = []  # 性能告警
        self.max_performance_history = 1000  # 最大性能记录数
        
        # 配置参数
        self.performance_config = {
            'response_time_threshold_ms': 1000.0,  # 响应时间阈值
            'error_rate_threshold': 0.1,  # 错误率阈值
            'success_rate_threshold': 0.9,  # 成功率阈值
            'concurrent_limit': 10,  # 并发限制
            'performance_check_interval': 300  # 性能检查间隔（秒）
        }
        
        # 指标收集器
        self.metrics_collector_enabled = True
        
        # 初始化内置能力
        self._register_builtin_capabilities()
        
        # 初始化依赖关系
        self._init_dependency_graph()

        logger.info(f"✅ 能力服务初始化完成，已注册 {len(self.capabilities)} 个能力")

    def _register_builtin_capabilities(self):
        """注册内置能力"""
        capabilities = [
            KnowledgeRetrievalCapability(),
            # ReasoningCapability(),  # Disable mock reasoning capability to use ReasoningExpert
            AnswerGenerationCapability(),
            CitationCapability(),
            CodeGenerationCapability(),
            DataAnalysisCapability()
        ]

        for capability in capabilities:
            self.register_capability(capability)

    def register_capability(self, capability: CapabilityInterface) -> bool:
        """注册能力"""
        try:
            name = capability.name
            if name in self.capabilities:
                logger.warning(f"⚠️ 能力 {name} 已存在，将被覆盖")

            self.capabilities[name] = CapabilityInfo(capability=capability)
            logger.info(f"✅ 能力注册成功: {name} v{capability.version}")
            return True

        except Exception as e:
            logger.error(f"❌ 能力注册失败: {e}")
            return False

    def unregister_capability(self, name: str) -> bool:
        """注销能力"""
        if name in self.capabilities:
            del self.capabilities[name]
            logger.info(f"✅ 能力注销成功: {name}")
            return True
        return False

    async def execute_capability(self, name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行能力"""
        if name not in self.capabilities:
            raise ValueError(f"能力不存在: {name}")

        capability_info = self.capabilities[name]
        capability = capability_info.capability
        metrics = capability_info.metrics

        # 缓存检查
        cache_key = self._generate_cache_key(name, context)
        if self.cache_enabled and cache_key in self.cache:
            metrics.cache_hit_rate = (metrics.cache_hit_rate * metrics.total_calls + 1) / (metrics.total_calls + 1)
            logger.debug(f"💾 缓存命中: {name}")
            
            # 记录缓存命中的性能指标
            self.record_performance_metric(name, {
                'response_time_ms': 0,  # 缓存命中，响应时间为0
                'cache_hit': True,
                'success': True,
                'success_rate': 1.0,
                'error_rate': 0.0,
                'execution_type': 'cached'
            })
            
            return self.cache[cache_key]

        metrics.cache_hit_rate = (metrics.cache_hit_rate * metrics.total_calls) / (metrics.total_calls + 1) if metrics.total_calls > 0 else 0

        # 执行能力
        start_time = time.time()
        try:
            # 健康检查
            if not await capability.health_check():
                raise RuntimeError(f"能力健康检查失败: {name}")

            # 执行能力
            result = await capability.execute(context)

            # 更新指标
            execution_time = time.time() - start_time
            execution_time_ms = execution_time * 1000  # 转换为毫秒
            metrics.total_calls += 1
            metrics.successful_calls += 1
            metrics.last_execution_time = execution_time
            metrics.average_execution_time = (
                (metrics.average_execution_time * (metrics.total_calls - 1)) + execution_time
            ) / metrics.total_calls
            metrics.error_rate = metrics.failed_calls / metrics.total_calls

            capability_info.last_used = datetime.now()

            # 缓存结果
            if self.cache_enabled:
                self._add_to_cache(cache_key, result)
            
            # 记录性能指标
            self.record_performance_metric(name, {
                'response_time_ms': execution_time_ms,
                'cache_hit': False,
                'success': True,
                'success_rate': 1.0,
                'error_rate': 0.0,
                'execution_type': 'direct',
                'result_size': len(str(result)) if result else 0
            })

            logger.debug(f"✅ 能力执行成功: {name} ({execution_time:.3f}s)")
            return result

        except Exception as e:
            # 更新失败指标
            execution_time = time.time() - start_time
            execution_time_ms = execution_time * 1000
            metrics.total_calls += 1
            metrics.failed_calls += 1
            metrics.last_execution_time = execution_time
            metrics.error_rate = metrics.failed_calls / metrics.total_calls
            
            # 记录失败性能指标
            self.record_performance_metric(name, {
                'response_time_ms': execution_time_ms,
                'cache_hit': False,
                'success': False,
                'success_rate': 0.0,
                'error_rate': 1.0,
                'execution_type': 'direct',
                'error_type': type(e).__name__,
                'error_message': str(e)
            })

            logger.error(f"❌ 能力执行失败: {name} - {e}")
            raise

    async def execute_workflow(self, workflow_spec: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行能力编排工作流"""
        try:
            # 解析工作流DSL
            workflow_plan = self._parse_workflow_dsl(workflow_spec)

            # 执行编排
            result = await self._execute_workflow_plan(workflow_plan, context)

            logger.info(f"✅ 能力工作流执行完成: {workflow_spec}")
            return result

        except Exception as e:
            logger.error(f"❌ 能力工作流执行失败: {e}")
            raise

    def get_capability_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取能力信息"""
        if name not in self.capabilities:
            return None

        info = self.capabilities[name]
        return {
            'name': info.capability.name,
            'version': info.capability.version,
            'description': info.capability.description,
            'capabilities': info.capability.capabilities,
            'metadata': info.capability.metadata,
            'metrics': {
                'total_calls': info.metrics.total_calls,
                'success_rate': info.metrics.successful_calls / info.metrics.total_calls if info.metrics.total_calls > 0 else 0,
                'average_execution_time': info.metrics.average_execution_time,
                'error_rate': info.metrics.error_rate,
                'cache_hit_rate': info.metrics.cache_hit_rate
            },
            'registered_at': info.registered_at.isoformat(),
            'last_used': info.last_used.isoformat() if info.last_used else None
        }

    def list_capabilities(self) -> List[Dict[str, Any]]:
        """列出所有能力"""
        return [self.get_capability_info(name) for name in self.capabilities.keys()]

    def get_service_metrics(self) -> Dict[str, Any]:
        """获取服务整体指标"""
        total_calls = sum(info.metrics.total_calls for info in self.capabilities.values())
        successful_calls = sum(info.metrics.successful_calls for info in self.capabilities.values())
        failed_calls = sum(info.metrics.failed_calls for info in self.capabilities.values())

        return {
            'total_capabilities': len(self.capabilities),
            'total_calls': total_calls,
            'success_rate': successful_calls / total_calls if total_calls > 0 else 0,
            'error_rate': failed_calls / total_calls if total_calls > 0 else 0,
            'cache_size': len(self.cache),
            'cache_enabled': self.cache_enabled
        }

    def _generate_cache_key(self, capability_name: str, context: Dict[str, Any]) -> str:
        """生成缓存键"""
        # 简化的缓存键生成（生产环境应该更复杂）
        key_data = {
            'capability': capability_name,
            'query': context.get('query', ''),
            'context_keys': sorted(context.keys())
        }
        return json.dumps(key_data, sort_keys=True)

    def _add_to_cache(self, key: str, result: Dict[str, Any]):
        """添加到缓存"""
        if len(self.cache) >= self.max_cache_size:
            # 简单的LRU策略：移除最旧的条目
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].get('_timestamp', 0))
            del self.cache[oldest_key]

        self.cache[key] = {
            **result,
            '_timestamp': time.time()
        }

    def _parse_workflow_dsl(self, workflow_spec: str) -> Dict[str, Any]:
        """解析工作流DSL - 增强版"""
        # 增强的DSL解析器，支持更复杂的编排模式
        # 支持格式: 
        # 1. 顺序执行: "cap1 -> cap2 -> cap3"
        # 2. 并行执行: "(cap1, cap2) -> cap3" 或 "cap1 | cap2 -> cap3"
        # 3. 条件分支: "cap1 ? cap2 : cap3"
        # 4. 循环: "cap1[3] -> cap2" (执行3次)
        # 5. 分组: "(cap1 -> cap2) | (cap3 -> cap4)"
        
        # 清理和标准化输入
        workflow_spec = workflow_spec.strip()
        
        # 检查是否是JSON格式的复杂工作流定义
        if workflow_spec.startswith('{') and workflow_spec.endswith('}'):
            try:
                import json
                return json.loads(workflow_spec)
            except json.JSONDecodeError:
                logger.warning(f"无法解析JSON工作流定义: {workflow_spec}")
        
        # 解析高级DSL结构
        return self._parse_advanced_dsl(workflow_spec)
    
    def _parse_advanced_dsl(self, workflow_spec: str) -> Dict[str, Any]:
        """解析高级DSL"""
        # 移除多余空格
        spec = workflow_spec.replace(' ', '')
        
        # 检查循环语法: cap[3]
        import re
        loop_pattern = r'(\w+)\[(\d+)\]'
        loop_match = re.search(loop_pattern, spec)
        if loop_match:
            capability = loop_match.group(1)
            count = int(loop_match.group(2))
            rest = spec.replace(loop_match.group(0), '')
            if rest.startswith('->'):
                next_cap = rest[2:] if rest[2:] else None
                return {
                    'type': 'loop_sequential',
                    'loop_capability': capability,
                    'loop_count': count,
                    'next_capability': next_cap
                }
            else:
                return {
                    'type': 'loop',
                    'capability': capability,
                    'count': count
                }
        
        # 检查条件分支语法: cap1 ? cap2 : cap3
        if '?' in spec and ':' in spec:
            condition_parts = spec.split('?')
            if len(condition_parts) == 2:
                condition_cap = condition_parts[0]
                branch_parts = condition_parts[1].split(':')
                if len(branch_parts) == 2:
                    true_branch = branch_parts[0]
                    false_branch = branch_parts[1]
                    return {
                        'type': 'conditional',
                        'condition': condition_cap,
                        'true_branch': true_branch if true_branch else None,
                        'false_branch': false_branch if false_branch else None
                    }
        
        # 检查并行分组语法: (cap1,cap2)->cap3 或 cap1|cap2->cap3
        if '(' in spec and ')' in spec:
            # 解析分组语法
            group_pattern = r'\(([^)]+)\)'
            group_match = re.search(group_pattern, spec)
            if group_match:
                group_content = group_match.group(1)
                group_caps = [cap.strip() for cap in group_content.split(',')]
                rest = spec.replace(group_match.group(0), '')
                
                if rest.startswith('->'):
                    next_cap = rest[2:] if rest[2:] else None
                    return {
                        'type': 'parallel_group_sequential',
                        'parallel_group': group_caps,
                        'next_capability': next_cap
                    }
                else:
                    return {
                        'type': 'parallel_group',
                        'capabilities': group_caps
                    }
        
        # 检查简单并行语法: cap1|cap2->cap3
        if '|' in spec:
            if '->' in spec:
                parts = spec.split('->')
                parallel_part = parts[0].strip()
                sequential_part = parts[1].strip() if len(parts) > 1 else None

                parallel_caps = [cap.strip() for cap in parallel_part.split('|')]
                sequential_caps = [sequential_part] if sequential_part else []

                return {
                    'type': 'parallel_sequential',
                    'parallel': parallel_caps,
                    'sequential': sequential_caps
                }
            else:
                # 纯并行
                parallel_caps = [cap.strip() for cap in spec.split('|')]
                return {
                    'type': 'parallel',
                    'capabilities': parallel_caps
                }
        
        # 检查顺序执行: cap1->cap2->cap3
        if '->' in spec:
            capabilities = [cap.strip() for cap in spec.split('->')]
            return {
                'type': 'sequential',
                'capabilities': capabilities
            }
        
        # 单能力执行
        return {
            'type': 'single',
            'capability': spec
        }

    async def _execute_workflow_plan(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流计划 - 增强版"""
        plan_type = plan['type']
        
        if plan_type == 'single':
            return await self._execute_single_capability(plan['capability'], context)
            
        elif plan_type == 'sequential':
            return await self._execute_sequential_workflow(plan['capabilities'], context)
            
        elif plan_type == 'parallel':
            return await self._execute_parallel_workflow(plan['capabilities'], context)
            
        elif plan_type == 'parallel_sequential':
            return await self._execute_parallel_sequential_workflow(plan['parallel'], plan.get('sequential', []), context)
            
        elif plan_type == 'parallel_group':
            return await self._execute_parallel_workflow(plan['capabilities'], context)
            
        elif plan_type == 'parallel_group_sequential':
            return await self._execute_parallel_sequential_workflow(plan['parallel_group'], [plan['next_capability']] if plan.get('next_capability') else [], context)
            
        elif plan_type == 'loop':
            return await self._execute_loop_workflow(plan['capability'], plan['count'], context)
            
        elif plan_type == 'loop_sequential':
            loop_result = await self._execute_loop_workflow(plan['loop_capability'], plan['loop_count'], context)
            if plan.get('next_capability'):
                combined_context = context.copy()
                if isinstance(loop_result, dict):
                    combined_context.update(loop_result)
                next_result = await self._execute_single_capability(plan['next_capability'], combined_context)
                return {
                    'workflow_type': 'loop_sequential',
                    'loop_result': loop_result,
                    'next_result': next_result,
                    'final_result': next_result
                }
            return {
                'workflow_type': 'loop',
                'result': loop_result,
                'final_result': loop_result
            }
            
        elif plan_type == 'conditional':
            return await self._execute_conditional_workflow(
                plan['condition'], 
                plan.get('true_branch'), 
                plan.get('false_branch'), 
                context
            )
            
        else:
            # 尝试作为JSON复杂工作流处理
            if 'workflow_type' in plan and 'steps' in plan:
                return await self._execute_complex_workflow(plan, context)
            else:
                raise ValueError(f"不支持的工作流类型: {plan_type}")
    
    async def _execute_single_capability(self, capability_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行单能力"""
        return await self.execute_capability(capability_name, context)
    
    async def _execute_sequential_workflow(self, capabilities: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行顺序工作流"""
        results = {}
        current_context = context.copy()

        for capability in capabilities:
            result = await self.execute_capability(capability, current_context)
            results[capability] = result
            # 将结果传递给下一个能力
            if isinstance(result, dict):
                current_context.update(result)

        return {
            'workflow_type': 'sequential',
            'results': results,
            'final_result': results[capabilities[-1]] if results else {}
        }
    
    async def _execute_parallel_workflow(self, capabilities: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行并行工作流"""
        parallel_results = {}
        parallel_tasks = []

        for capability in capabilities:
            task = self.execute_capability(capability, context)
            parallel_tasks.append(task)

        parallel_task_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)

        for i, capability in enumerate(capabilities):
            if isinstance(parallel_task_results[i], Exception):
                parallel_results[capability] = {'error': str(parallel_task_results[i])}
            else:
                parallel_results[capability] = parallel_task_results[i]

        # 合并所有结果
        combined_result = context.copy()
        for result in parallel_results.values():
            if isinstance(result, dict) and 'error' not in result:
                combined_result.update(result)

        return {
            'workflow_type': 'parallel',
            'results': parallel_results,
            'final_result': combined_result
        }
    
    async def _execute_parallel_sequential_workflow(self, parallel_caps: List[str], sequential_caps: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行并行-顺序混合工作流"""
        # 执行并行阶段
        parallel_result = await self._execute_parallel_workflow(parallel_caps, context)
        
        # 合并并行结果作为后续能力的上下文
        combined_context = context.copy()
        for result in parallel_result['results'].values():
            if isinstance(result, dict) and 'error' not in result:
                combined_context.update(result)
        
        # 执行顺序阶段
        sequential_results = {}
        current_context = combined_context.copy()
        
        for capability in sequential_caps:
            result = await self.execute_capability(capability, current_context)
            sequential_results[capability] = result
            if isinstance(result, dict):
                current_context.update(result)
        
        return {
            'workflow_type': 'parallel_sequential',
            'parallel_results': parallel_result['results'],
            'sequential_results': sequential_results,
            'final_result': sequential_results[sequential_caps[-1]] if sequential_caps else combined_context
        }
    
    async def _execute_loop_workflow(self, capability_name: str, count: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行循环工作流"""
        results = []
        current_context = context.copy()
        
        for i in range(count):
            result = await self.execute_capability(capability_name, current_context)
            results.append({
                'iteration': i + 1,
                'result': result
            })
            if isinstance(result, dict):
                current_context.update(result)
        
        # 最后一次迭代的结果作为最终结果
        final_result = results[-1]['result'] if results else {}
        
        return {
            'workflow_type': 'loop',
            'iterations': results,
            'iteration_count': count,
            'final_result': final_result
        }
    
    async def _execute_conditional_workflow(self, condition_cap: str, true_branch: Optional[str], false_branch: Optional[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行条件工作流"""
        # 执行条件能力
        condition_result = await self.execute_capability(condition_cap, context)
        
        # 判断条件结果（简单实现：检查结果中是否有truthy值）
        condition_met = False
        if isinstance(condition_result, dict):
            # 检查是否有明确的success或result字段
            if 'success' in condition_result and condition_result['success']:
                condition_met = True
            elif 'result' in condition_result and condition_result['result']:
                condition_met = True
            elif len(condition_result) > 0:
                # 如果有非空结果，视为条件满足
                condition_met = True
        elif condition_result:
            # 非字典的truthy值
            condition_met = True
        
        # 执行分支
        branch_to_execute = true_branch if condition_met else false_branch
        branch_result = None
        
        if branch_to_execute:
            combined_context = context.copy()
            if isinstance(condition_result, dict):
                combined_context.update(condition_result)
            branch_result = await self.execute_capability(branch_to_execute, combined_context)
        
        return {
            'workflow_type': 'conditional',
            'condition': condition_cap,
            'condition_result': condition_result,
            'condition_met': condition_met,
            'executed_branch': branch_to_execute,
            'branch_result': branch_result,
            'final_result': branch_result if branch_result else condition_result
        }
    
    async def _execute_complex_workflow(self, workflow_def: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行复杂JSON定义的工作流"""
        workflow_type = workflow_def.get('workflow_type', 'complex')
        steps = workflow_def.get('steps', [])
        
        results = {}
        current_context = context.copy()
        
        for step in steps:
            step_type = step.get('type', 'capability')
            step_name = step.get('name', f'step_{len(results)}')
            
            if step_type == 'capability':
                capability_name = step.get('capability')
                if capability_name:
                    result = await self.execute_capability(capability_name, current_context)
                    results[step_name] = result
                    if isinstance(result, dict):
                        current_context.update(result)
            
            elif step_type == 'parallel':
                parallel_caps = step.get('capabilities', [])
                if parallel_caps:
                    parallel_result = await self._execute_parallel_workflow(parallel_caps, current_context)
                    results[step_name] = parallel_result
                    if isinstance(parallel_result, dict) and 'final_result' in parallel_result:
                        if isinstance(parallel_result['final_result'], dict):
                            current_context.update(parallel_result['final_result'])
            
            # 可以添加更多步骤类型
        
        return {
            'workflow_type': workflow_type,
            'results': results,
            'final_result': current_context
        }


    def _init_dependency_graph(self):
        """初始化依赖关系图"""
        # 定义内置能力之间的依赖关系
        # 格式: {'source_capability': ['dependent_capability1', 'dependent_capability2']}
        self.dependency_graph = {
            'knowledge_retrieval': ['answer_generation', 'data_analysis'],
            'data_analysis': ['answer_generation'],
            'citation': ['answer_generation'],
            'code_generation': []  # 没有依赖其他内置能力
        }
        
        logger.info(f"初始化依赖关系图，包含 {len(self.dependency_graph)} 个能力节点")
    
    def add_dependency(self, source_capability: str, dependent_capability: str):
        """添加能力依赖关系"""
        if source_capability not in self.dependency_graph:
            self.dependency_graph[source_capability] = []
        
        if dependent_capability not in self.dependency_graph[source_capability]:
            self.dependency_graph[source_capability].append(dependent_capability)
            logger.debug(f"添加依赖关系: {source_capability} -> {dependent_capability}")
    
    def remove_dependency(self, source_capability: str, dependent_capability: str):
        """移除能力依赖关系"""
        if source_capability in self.dependency_graph:
            if dependent_capability in self.dependency_graph[source_capability]:
                self.dependency_graph[source_capability].remove(dependent_capability)
                logger.debug(f"移除依赖关系: {source_capability} -> {dependent_capability}")
    
    def get_dependencies(self, capability_name: str) -> List[str]:
        """获取能力依赖项"""
        return self.dependency_graph.get(capability_name, [])
    
    def get_dependents(self, capability_name: str) -> List[str]:
        """获取依赖此能力的能力"""
        dependents = []
        for source, deps in self.dependency_graph.items():
            if capability_name in deps:
                dependents.append(source)
        return dependents
    
    def check_dependency_cycle(self) -> bool:
        """检查依赖图中是否有循环依赖"""
        visited = set()
        rec_stack = set()
        
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.dependency_graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.dependency_graph:
            if node not in visited:
                if dfs(node):
                    return True
        
        return False
    
    def record_performance_metric(self, capability_name: str, metric_data: Dict[str, Any]):
        """记录能力性能指标"""
        if not self.metrics_collector_enabled:
            return
        
        if capability_name not in self.performance_metrics:
            self.performance_metrics[capability_name] = []
        
        # 添加时间戳
        metric_data['timestamp'] = time.time()
        metric_data['capability'] = capability_name
        
        # 添加到历史记录
        self.performance_metrics[capability_name].append(metric_data)
        
        # 限制历史记录大小
        if len(self.performance_metrics[capability_name]) > self.max_performance_history:
            self.performance_metrics[capability_name] = self.performance_metrics[capability_name][-self.max_performance_history:]
        
        # 检查是否需要触发告警
        self._check_performance_alert(capability_name, metric_data)
    
    def _check_performance_alert(self, capability_name: str, metric_data: Dict[str, Any]):
        """检查性能指标是否需要触发告警"""
        response_time = metric_data.get('response_time_ms', 0)
        error_rate = metric_data.get('error_rate', 0)
        success_rate = metric_data.get('success_rate', 1.0)
        
        alert_triggered = False
        alert_details = {
            'capability': capability_name,
            'timestamp': metric_data['timestamp'],
            'metrics': metric_data
        }
        
        if response_time > self.performance_config['response_time_threshold_ms']:
            alert_triggered = True
            alert_details['type'] = 'high_response_time'
            alert_details['message'] = f"能力 {capability_name} 响应时间过高: {response_time}ms"
        
        elif error_rate > self.performance_config['error_rate_threshold']:
            alert_triggered = True
            alert_details['type'] = 'high_error_rate'
            alert_details['message'] = f"能力 {capability_name} 错误率过高: {error_rate:.2%}"
        
        elif success_rate < self.performance_config['success_rate_threshold']:
            alert_triggered = True
            alert_details['type'] = 'low_success_rate'
            alert_details['message'] = f"能力 {capability_name} 成功率过低: {success_rate:.2%}"
        
        if alert_triggered:
            self.performance_alerts.append(alert_details)
            logger.warning(f"性能告警: {alert_details['message']}")
    
    def get_performance_summary(self, capability_name: str = None) -> Dict[str, Any]:
        """获取性能摘要"""
        if capability_name:
            metrics = self.performance_metrics.get(capability_name, [])
            if not metrics:
                return {'capability': capability_name, 'metrics_available': False}
            
            # 计算统计信息
            response_times = [m.get('response_time_ms', 0) for m in metrics]
            error_rates = [m.get('error_rate', 0) for m in metrics]
            success_rates = [m.get('success_rate', 1.0) for m in metrics]
            
            import statistics
            
            return {
                'capability': capability_name,
                'metrics_available': True,
                'total_executions': len(metrics),
                'avg_response_time_ms': statistics.mean(response_times) if response_times else 0,
                'max_response_time_ms': max(response_times) if response_times else 0,
                'min_response_time_ms': min(response_times) if response_times else 0,
                'avg_error_rate': statistics.mean(error_rates) if error_rates else 0,
                'avg_success_rate': statistics.mean(success_rates) if success_rates else 1.0,
                'recent_metrics': metrics[-10:] if len(metrics) > 10 else metrics
            }
        else:
            # 所有能力的摘要
            summary = {
                'total_capabilities': len(self.performance_metrics),
                'capabilities': {}
            }
            
            for cap_name in self.performance_metrics:
                cap_summary = self.get_performance_summary(cap_name)
                if cap_summary['metrics_available']:
                    summary['capabilities'][cap_name] = cap_summary
            
            return summary
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的性能告警"""
        return self.performance_alerts[-limit:] if self.performance_alerts else []
    
    def clear_alerts(self):
        """清空性能告警"""
        self.performance_alerts = []
    
    def update_performance_config(self, config: Dict[str, Any]):
        """更新性能配置"""
        self.performance_config.update(config)
        logger.info(f"更新性能配置: {config}")
    
    async def analyze_performance_trends(self) -> Dict[str, Any]:
        """分析性能趋势"""
        analysis = {
            'timestamp': time.time(),
            'performance_issues': [],
            'optimization_opportunities': [],
            'recommendations': []
        }
        
        for capability_name, metrics in self.performance_metrics.items():
            if len(metrics) < 5:
                continue  # 数据不足
            
            # 计算最近性能
            recent_metrics = metrics[-5:]
            avg_response_time = sum(m.get('response_time_ms', 0) for m in recent_metrics) / len(recent_metrics)
            avg_error_rate = sum(m.get('error_rate', 0) for m in recent_metrics) / len(recent_metrics)
            
            # 检查问题
            if avg_response_time > self.performance_config['response_time_threshold_ms']:
                analysis['performance_issues'].append({
                    'capability': capability_name,
                    'issue': 'high_response_time',
                    'value': avg_response_time,
                    'threshold': self.performance_config['response_time_threshold_ms']
                })
            
            if avg_error_rate > self.performance_config['error_rate_threshold']:
                analysis['performance_issues'].append({
                    'capability': capability_name,
                    'issue': 'high_error_rate',
                    'value': avg_error_rate,
                    'threshold': self.performance_config['error_rate_threshold']
                })
        
        # 生成建议
        if analysis['performance_issues']:
            analysis['recommendations'].append("考虑优化高响应时间的能力")
            analysis['recommendations'].append("检查高错误率能力的实现")
        
        return analysis

# 内置能力实现

class KnowledgeRetrievalCapability:
    """知识检索能力"""

    @property
    def name(self) -> str:
        return "knowledge_retrieval"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "从知识库检索相关信息"

    @property
    def capabilities(self) -> List[str]:
        return ["search", "retrieve", "filter"]

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "input_types": ["query", "context"],
            "output_types": ["evidence", "sources", "confidence"],
            "estimated_time": 0.5
        }

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行知识检索"""
        await asyncio.sleep(0.1)  # 模拟处理时间

        query = context.get("query", "")
        return {
            "evidence": [f"为查询'{query}'检索到的相关知识和证据"],
            "sources": ["knowledge_base_1", "knowledge_base_2"],
            "confidence": 0.85,
            "retrieved_at": datetime.now().isoformat()
        }

    async def health_check(self) -> bool:
        return True


class ReasoningCapability:
    """推理能力"""

    @property
    def name(self) -> str:
        return "reasoning"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "基于证据进行逻辑推理"

    @property
    def capabilities(self) -> List[str]:
        return ["analyze", "reason", "infer"]

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "input_types": ["query", "evidence", "context"],
            "output_types": ["reasoning_steps", "conclusion", "confidence"],
            "estimated_time": 0.8
        }

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行推理"""
        await asyncio.sleep(0.15)  # 模拟处理时间

        query = context.get("query", "")
        evidence = context.get("evidence", [])

        return {
            "reasoning_steps": [
                f"分析查询: {query}",
                "评估提供的证据",
                "应用逻辑推理规则",
                "得出结论"
            ],
            "conclusion": f"基于证据分析，对'{query}'的推理结论",
            "confidence": 0.75,
            "evidence_used": len(evidence)
        }

    async def health_check(self) -> bool:
        return True


class AnswerGenerationCapability:
    """答案生成能力"""

    @property
    def name(self) -> str:
        return "answer_generation"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "基于上下文生成自然语言答案"

    @property
    def capabilities(self) -> List[str]:
        return ["generate", "format", "summarize"]

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "input_types": ["query", "evidence", "reasoning", "context"],
            "output_types": ["answer", "confidence", "sources"],
            "estimated_time": 0.6
        }

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行答案生成"""
        await asyncio.sleep(0.12)  # 模拟处理时间

        query = context.get("query", "")
        route_path = context.get("route_path", "simple")

        # 根据复杂度调整答案
        if route_path == "complex":
            answer = f"这是对复杂查询'{query}'的详细、全面答案。"
        elif route_path == "medium":
            answer = f"这是对查询'{query}'的中等复杂度答案。"
        else:
            answer = f"这是对简单查询'{query}'的直接答案。"

        return {
            "answer": answer,
            "confidence": 0.88,
            "sources": ["generated"],
            "generated_at": datetime.now().isoformat()
        }

    async def health_check(self) -> bool:
        return True


class CitationCapability:
    """引用能力"""

    @property
    def name(self) -> str:
        return "citation"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "生成学术引用和来源标注"

    @property
    def capabilities(self) -> List[str]:
        return ["cite", "reference", "validate"]

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "input_types": ["content", "sources"],
            "output_types": ["citations", "formatted_citations"],
            "estimated_time": 0.3
        }

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行引用生成"""
        await asyncio.sleep(0.08)  # 模拟处理时间

        content = context.get("content", context.get("answer", ""))

        return {
            "citations": [{
                "text": f"引用内容片段: {content[:50]}...",
                "source": "Academic Source 2024",
                "year": 2024,
                "page": "1-5"
            }],
            "formatted_citations": "[1] Academic Source. 2024.",
            "citation_count": 1
        }

    async def health_check(self) -> bool:
        return True


class CodeGenerationCapability:
    """代码生成能力"""

    @property
    def name(self) -> str:
        return "code_generation"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "生成编程代码和代码示例"

    @property
    def capabilities(self) -> List[str]:
        return ["codegen", "syntax_check", "optimize"]

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "input_types": ["query", "language", "requirements"],
            "output_types": ["code", "explanation", "complexity"],
            "estimated_time": 0.7
        }

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行代码生成"""
        await asyncio.sleep(0.15)  # 模拟处理时间

        query = context.get("query", "")
        language = context.get("language", "python")

        return {
            "code": f"# Generated code for: {query}\nprint('Hello, {language}!')",
            "language": language,
            "explanation": f"为查询'{query}'生成的{language}代码",
            "complexity": "simple",
            "line_count": 2
        }

    async def health_check(self) -> bool:
        return True


class DataAnalysisCapability:
    """数据分析能力"""

    @property
    def name(self) -> str:
        return "data_analysis"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "分析数据并生成洞察"

    @property
    def capabilities(self) -> List[str]:
        return ["analyze", "visualize", "summarize"]

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "input_types": ["data", "query", "context"],
            "output_types": ["insights", "visualization", "summary"],
            "estimated_time": 1.0
        }

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据分析"""
        await asyncio.sleep(0.2)  # 模拟处理时间

        query = context.get("query", "")
        data = context.get("data", [])

        return {
            "insights": [f"为查询'{query}'分析得出的关键洞察"],
            "visualization": "data_visualization_placeholder",
            "summary": f"数据分析摘要: 处理了{len(data)}个数据点",
            "confidence": 0.82
        }

    async def health_check(self) -> bool:
        return True


# 全局能力服务实例
_capability_service_instance: Optional[CapabilityService] = None


def get_capability_service() -> CapabilityService:
    """获取能力服务实例（单例模式）"""
    global _capability_service_instance
    if _capability_service_instance is None:
        _capability_service_instance = CapabilityService()
    return _capability_service_instance
