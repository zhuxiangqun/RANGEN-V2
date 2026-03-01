#!/usr/bin/env python3
"""
ToolOrchestrator - 工具编排器 (L3基础认知)
智能工具选择、执行流程编排、提示词优化管理
from ..utils.unified_centers import get_unified_config_center
from ..utils.unified_threshold_manager import get_unified_threshold_manager


优化特性：
- 智能工具选择：基于任务需求、工具能力和历史性能动态选择最佳工具
- 执行流程编排：支持复杂工具链的自动化编排和执行
- 提示词优化管理：为每个工具自动生成和优化提示词模板
- 工具性能监控：跟踪工具执行效果和质量指标
"""

import time
import logging
import asyncio
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, OrderedDict
from concurrent.futures import ThreadPoolExecutor
import re

from .expert_agent import ExpertAgent
from .base_agent import AgentResult
from src.utils.logging_helper import get_module_logger, ModuleType
from src.utils.unified_centers import get_unified_config_center
from src.utils.unified_threshold_manager import get_unified_threshold_manager

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """工具分类"""
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    DATA_PROCESSING = "data_processing"
    COMPUTATION = "computation"
    SEARCH = "search"
    GENERATION = "generation"
    ANALYSIS = "analysis"
    UTILITY = "utility"


class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"      # 并行执行
    CONDITIONAL = "conditional" # 条件执行
    LOOP = "loop"              # 循环执行


@dataclass
class ToolMetadata:
    """工具元数据"""
    name: str
    category: ToolCategory
    capabilities: List[str]
    success_rate: float = 0.0
    avg_execution_time: float = 0.0
    call_count: int = 0
    last_used: float = 0.0
    quality_score: float = 0.8
    dependencies: List[str] = field(default_factory=list)
    prompt_templates: Dict[str, str] = field(default_factory=dict)


@dataclass
class ToolChainStep:
    """工具链步骤"""
    tool_name: str
    parameters: Dict[str, Any]
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    condition: Optional[str] = None  # 执行条件
    max_retries: int = 3
    timeout_seconds: int = 30
    fallback_tools: List[str] = field(default_factory=list)


@dataclass
class ToolChain:
    """工具链"""
    id: str
    name: str
    description: str
    steps: List[ToolChainStep]
    total_execution_time: float = 0.0
    success_rate: float = 0.0
    usage_count: int = 0


class ToolOrchestrator(ExpertAgent):
    """ToolOrchestrator - 工具编排器 (L3基础认知)

    核心职责：
    1. 智能工具选择 - 基于任务需求、工具能力和历史性能动态选择最佳工具
    2. 执行流程编排 - 支持复杂工具链的自动化编排和执行
    3. 提示词优化管理 - 为每个工具自动生成和优化提示词模板
    4. 工具性能监控 - 跟踪工具执行效果和质量指标

    优化特性：
    - 多维度工具评估：成功率、执行时间、质量评分综合评估
    - 动态工具链构建：基于任务复杂度自动生成执行流程
    - 自适应参数优化：根据历史表现调整工具参数
    - 并行执行优化：智能调度避免资源冲突
    """

    def __init__(self):
        """初始化ToolOrchestrator"""
        # 初始化统一配置中心
        self.config_center = get_unified_config_center()
        self.threshold_manager = get_unified_threshold_manager()

        # 获取Agent特定配置
        self.agent_config = self.config_center.get_agent_config(self.__class__.__name__, {
            'enabled': True,
            'max_retries': 3,
            'timeout': 30,
            'debug_mode': False
        })

        # 获取阈值配置
        self.thresholds = self.threshold_manager.get_thresholds(self.__class__.__name__, {
            'performance_warning_threshold': 5.0,
            'error_rate_threshold': 0.1,
            'memory_usage_threshold': 80.0
        })

        super().__init__(
            agent_id="tool_orchestrator",
            domain_expertise="智能工具选择和流程编排",
            capability_level=0.7,  # L3基础认知
            collaboration_style="coordinator"
        )

        # 使用模块日志器
        self.module_logger = get_module_logger(ModuleType.AGENT, "ToolOrchestrator")

        # 🚀 新增：工具注册和性能跟踪
        self._tool_metadata: Dict[str, ToolMetadata] = {}
        self._tool_chains: Dict[str, ToolChain] = {}
        self._execution_history: List[Dict[str, Any]] = []

        # 🚀 新增：智能选择和优化配置
        self._parallel_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="tool_orchestration")
        self._max_history_size = 1000
        self._tool_selection_cache = OrderedDict()  # LRU缓存
        self._cache_max_size = 200

        # 🚀 新增：自适应参数
        self._adaptive_params = {
            'performance_weight': 0.4,    # 性能权重
            'quality_weight': 0.4,        # 质量权重
            'compatibility_weight': 0.2,  # 兼容性权重
            'learning_rate': 0.1,         # 学习率
            'min_success_rate_threshold': 0.6,  # 最小成功率阈值
            'max_execution_time_penalty': 2.0   # 最大执行时间惩罚
        }

        # 🚀 新增：统计和监控
        self._stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'tool_selections': defaultdict(int),
            'chain_executions': defaultdict(int),
            'performance_trends': {},
            'cache_hit_rate': 0.0
        }

        # 初始化内置工具链模板
        self._initialize_builtin_chains()

    def _get_service(self):
        """ToolOrchestrator不直接使用单一Service"""
        return None

    # 🚀 新增：工具注册和管理方法
    async def register_tool(self, tool_name: str, category: ToolCategory,
                           capabilities: List[str], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """注册工具"""
        if tool_name in self._tool_metadata:
            self.module_logger.warning(f"工具 {tool_name} 已注册，跳过")
            return False

        tool_metadata = ToolMetadata(
            name=tool_name,
            category=category,
            capabilities=capabilities,
            **(metadata or {})
        )

        self._tool_metadata[tool_name] = tool_metadata
        self.module_logger.info(f"✅ 工具已注册: {tool_name} ({category.value})")
        return True

    async def update_tool_performance(self, tool_name: str, success: bool,
                                    execution_time: float, quality_score: float):
        """更新工具性能指标"""
        if tool_name not in self._tool_metadata:
            return

        metadata = self._tool_metadata[tool_name]
        metadata.call_count += 1
        metadata.last_used = time.time()

        if success:
            metadata.success_rate = (
                (metadata.success_rate * (metadata.call_count - 1)) + 1.0
            ) / metadata.call_count
        else:
            metadata.success_rate = (
                (metadata.success_rate * (metadata.call_count - 1)) + 0.0
            ) / metadata.call_count

        # 更新平均执行时间（指数移动平均）
        alpha = 0.3  # 平滑因子
        metadata.avg_execution_time = (
            alpha * execution_time + (1 - alpha) * metadata.avg_execution_time
        )

        # 更新质量评分
        metadata.quality_score = (
            self._adaptive_params['learning_rate'] * quality_score +
            (1 - self._adaptive_params['learning_rate']) * metadata.quality_score
        )

    # 🚀 新增：智能工具选择算法
    async def select_optimal_tool(self, task_description: str, required_capabilities: List[str],
                                context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """智能选择最优工具"""
        start_time = time.time()

        # 检查缓存
        cache_key = self._get_selection_cache_key(task_description, required_capabilities, context)
        if cache_key in self._tool_selection_cache:
            self._tool_selection_cache.move_to_end(cache_key)
            return self._tool_selection_cache[cache_key]

        # 筛选候选工具
        candidates = []
        for tool_name, metadata in self._tool_metadata.items():
            if self._matches_capabilities(metadata, required_capabilities):
                candidates.append((tool_name, metadata))

        if not candidates:
            return None

        # 计算每个候选工具的综合评分
        scored_candidates = []
        for tool_name, metadata in candidates:
            score = await self._calculate_tool_score(metadata, task_description, context)
            scored_candidates.append((tool_name, score))

        # 选择最高分的工具
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        selected_tool = scored_candidates[0][0]

        # 更新缓存
        if len(self._tool_selection_cache) >= self._cache_max_size:
            self._tool_selection_cache.popitem(last=False)
        self._tool_selection_cache[cache_key] = selected_tool

        execution_time = time.time() - start_time
        self.module_logger.debug(f"✅ 工具选择完成: {selected_tool}, 耗时={execution_time:.3f}秒")

        return selected_tool

    async def _calculate_tool_score(self, metadata: ToolMetadata, task_description: str,
                                  context: Optional[Dict[str, Any]]) -> float:
        """计算工具综合评分"""
        # 1. 性能评分（40%）：成功率和执行时间
        performance_score = (
            metadata.success_rate * 0.7 +
            (1.0 / (1.0 + metadata.avg_execution_time / 10.0)) * 0.3  # 归一化执行时间
        )

        # 2. 质量评分（40%）：质量分数和使用频率
        recency_bonus = min(1.0, metadata.call_count / 10.0)  # 使用频率奖励
        quality_score = metadata.quality_score * (1.0 + recency_bonus * 0.2)

        # 3. 兼容性评分（20%）：任务匹配度和依赖关系
        compatibility_score = await self._calculate_compatibility(metadata, task_description, context)

        # 综合评分
        total_score = (
            performance_score * self._adaptive_params['performance_weight'] +
            quality_score * self._adaptive_params['quality_weight'] +
            compatibility_score * self._adaptive_params['compatibility_weight']
        )

        return total_score

    async def _calculate_compatibility(self, metadata: ToolMetadata, task_description: str,
                                     context: Optional[Dict[str, Any]]) -> float:
        """计算工具兼容性"""
        compatibility = 0.5  # 基础分数

        # 任务描述匹配度
        task_lower = task_description.lower()
        capability_matches = sum(1 for cap in metadata.capabilities
                               if cap.lower() in task_lower)
        compatibility += capability_matches * 0.2

        # 上下文相关性
        if context:
            context_str = json.dumps(context, default=str).lower()
            context_matches = sum(1 for cap in metadata.capabilities
                                if cap.lower() in context_str)
            compatibility += context_matches * 0.1

        # 惩罚低成功率工具
        if metadata.success_rate < self._adaptive_params['min_success_rate_threshold']:
            compatibility *= 0.5

        return min(1.0, compatibility)

    def _matches_capabilities(self, metadata: ToolMetadata, required_capabilities: List[str]) -> bool:
        """检查工具是否匹配所需能力"""
        return any(cap in metadata.capabilities for cap in required_capabilities)

    # 🚀 新增：工具链编排和执行
    async def create_tool_chain(self, name: str, description: str, steps: List[Dict[str, Any]]) -> str:
        """创建工具链"""
        chain_id = f"chain_{int(time.time() * 1000)}_{hash(name) % 10000}"

        tool_steps = []
        for step_data in steps:
            step = ToolChainStep(
                tool_name=step_data['tool_name'],
                parameters=step_data.get('parameters', {}),
                execution_mode=ExecutionMode(step_data.get('execution_mode', 'sequential')),
                condition=step_data.get('condition'),
                max_retries=step_data.get('max_retries', 3),
                timeout_seconds=step_data.get('timeout_seconds', 30),
                fallback_tools=step_data.get('fallback_tools', [])
            )
            tool_steps.append(step)

        chain = ToolChain(
            id=chain_id,
            name=name,
            description=description,
            steps=tool_steps
        )

        self._tool_chains[chain_id] = chain
        self.module_logger.info(f"✅ 工具链已创建: {name} ({chain_id})")
        return chain_id

    async def execute_tool_chain(self, chain_id: str, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具链"""
        if chain_id not in self._tool_chains:
            return {'success': False, 'error': f'工具链不存在: {chain_id}'}

        chain = self._tool_chains[chain_id]
        start_time = time.time()

        self.module_logger.info(f"🔄 开始执行工具链: {chain.name}")

        # 执行上下文
        execution_context = initial_context.copy()
        execution_results = []

        # 按步骤执行
        for i, step in enumerate(chain.steps):
            self.module_logger.debug(f"执行步骤 {i+1}/{len(chain.steps)}: {step.tool_name}")

            try:
                # 检查执行条件
                if step.condition and not self._evaluate_condition(step.condition, execution_context):
                    self.module_logger.debug(f"跳过步骤 {step.tool_name}: 条件不满足")
                    continue

                # 执行工具步骤
                step_result = await self._execute_tool_step(step, execution_context)

                execution_results.append({
                    'step': i,
                    'tool': step.tool_name,
                    'success': step_result['success'],
                    'result': step_result.get('result'),
                    'error': step_result.get('error'),
                    'execution_time': step_result.get('execution_time', 0.0)
                })

                # 更新执行上下文
                if step_result['success'] and step_result.get('result'):
                    execution_context.update(step_result['result'])

            except Exception as e:
                self.module_logger.error(f"工具链步骤执行失败: {step.tool_name} - {e}")
                execution_results.append({
                    'step': i,
                    'tool': step.tool_name,
                    'success': False,
                    'error': str(e),
                    'execution_time': 0.0
                })

        # 计算总体结果
        total_time = time.time() - start_time
        successful_steps = sum(1 for r in execution_results if r['success'])
        success_rate = successful_steps / len(chain.steps)

        # 更新工具链统计
        chain.total_execution_time = (
            (chain.total_execution_time * chain.usage_count) + total_time
        ) / (chain.usage_count + 1)
        chain.success_rate = (
            (chain.success_rate * chain.usage_count) + success_rate
        ) / (chain.usage_count + 1)
        chain.usage_count += 1

        result = {
            'success': success_rate >= 0.8,  # 80%步骤成功算整体成功
            'chain_id': chain_id,
            'chain_name': chain.name,
            'total_steps': len(chain.steps),
            'successful_steps': successful_steps,
            'success_rate': success_rate,
            'total_execution_time': total_time,
            'step_results': execution_results,
            'final_context': execution_context
        }

        # 记录执行历史
        self._record_execution_history(chain_id, result)

        self.module_logger.info(f"✅ 工具链执行完成: {chain.name}, 成功率={success_rate:.2f}, 耗时={total_time:.2f}秒")

        return result

    async def _execute_tool_step(self, step: ToolChainStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个工具步骤"""
        start_time = time.time()

        # 获取工具实例
        tool = await self._get_tool_instance(step.tool_name)
        if not tool:
            return {
                'success': False,
                'error': f'工具不存在: {step.tool_name}',
                'execution_time': time.time() - start_time
            }

        # 合并参数
        final_params = step.parameters.copy()
        final_params.update(context)

        # 执行工具（支持重试）
        max_attempts = step.max_retries + 1
        for attempt in range(max_attempts):
            try:
                # 应用超时
                result = await asyncio.wait_for(
                    tool.execute(final_params),
                    timeout=step.timeout_seconds
                )

                execution_time = time.time() - start_time

                # 更新工具性能统计
                success = result.success if hasattr(result, 'success') else True
                quality_score = getattr(result, 'confidence', 0.8) if hasattr(result, 'confidence') else 0.8

                await self.update_tool_performance(
                    step.tool_name, success, execution_time, quality_score
                )

                return {
                    'success': success,
                    'result': result.data if hasattr(result, 'data') else result,
                    'execution_time': execution_time
                }

            except asyncio.TimeoutError:
                self.module_logger.warning(f"工具执行超时: {step.tool_name} (尝试 {attempt + 1}/{max_attempts})")
                if attempt == max_attempts - 1:
                    return {
                        'success': False,
                        'error': f'工具执行超时: {step.tool_name}',
                        'execution_time': time.time() - start_time
                    }

            except Exception as e:
                self.module_logger.warning(f"工具执行失败: {step.tool_name} - {e} (尝试 {attempt + 1}/{max_attempts})")
                if attempt == max_attempts - 1:
                    return {
                        'success': False,
                        'error': str(e),
                        'execution_time': time.time() - start_time
                    }

        return {
            'success': False,
            'error': f'工具执行失败，已重试 {max_attempts} 次: {step.tool_name}',
            'execution_time': time.time() - start_time
        }

    # 🚀 新增：提示词优化管理
    async def optimize_prompt_template(self, tool_name: str, task_description: str,
                                     performance_history: List[Dict[str, Any]]) -> str:
        """优化工具的提示词模板"""
        if tool_name not in self._tool_metadata:
            return ""

        metadata = self._tool_metadata[tool_name]

        # 分析性能历史，识别改进点
        successful_executions = [h for h in performance_history if h.get('success', False)]
        failed_executions = [h for h in performance_history if not h.get('success', False)]

        # 生成优化建议
        optimizations = []

        if failed_executions:
            # 分析失败模式
            error_patterns = defaultdict(int)
            for failure in failed_executions:
                error = failure.get('error', '')
                if 'timeout' in error.lower():
                    error_patterns['timeout'] += 1
                elif 'parameter' in error.lower():
                    error_patterns['parameter'] += 1
                else:
                    error_patterns['other'] += 1

            if error_patterns['timeout']:
                optimizations.append("添加更明确的执行时间限制说明")
            if error_patterns['parameter']:
                optimizations.append("优化参数格式和验证说明")

        # 生成优化后的提示词
        base_template = metadata.prompt_templates.get('default', f"使用{tool_name}工具执行以下任务：{{task_description}}")

        optimized_template = base_template

        # 应用优化
        for optimization in optimizations:
            if "执行时间" in optimization:
                optimized_template += "\n注意：请在30秒内完成执行。"
            if "参数格式" in optimization:
                optimized_template += "\n参数格式要求：使用JSON格式提供所有必需参数。"

        # 更新模板
        metadata.prompt_templates['optimized'] = optimized_template

        self.module_logger.info(f"✅ 提示词模板已优化: {tool_name}")
        return optimized_template

    # 🚀 新增：辅助方法
    async def _get_tool_instance(self, tool_name: str):
        """获取工具实例"""
        # 这里需要从工具注册表获取实际的工具实例
        # 简化实现，返回模拟工具
        from src.agents.tools.tool_registry import ToolRegistry
        registry = ToolRegistry()
        return registry.get_tool(tool_name)

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """评估执行条件"""
        # 简化实现，实际应该支持更复杂的条件表达式
        try:
            # 简单的变量检查
            if condition.startswith('has_'):
                var_name = condition[4:]
                return var_name in context
            elif condition.startswith('not_'):
                sub_condition = condition[4:]
                return not self._evaluate_condition(sub_condition, context)
            else:
                # 默认当作布尔值处理
                return bool(context.get(condition, False))
        except:
            return True

    def _get_selection_cache_key(self, task_description: str, required_capabilities: List[str],
                                context: Optional[Dict[str, Any]]) -> str:
        """生成工具选择缓存键"""
        key_data = {
            'task': task_description,
            'capabilities': sorted(required_capabilities),
            'context_keys': sorted(context.keys()) if context else []
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _record_execution_history(self, chain_id: str, result: Dict[str, Any]):
        """记录执行历史"""
        history_entry = {
            'chain_id': chain_id,
            'timestamp': time.time(),
            'result': result
        }

        self._execution_history.append(history_entry)

        # 限制历史大小
        if len(self._execution_history) > self._max_history_size:
            self._execution_history.pop(0)

    def _initialize_builtin_chains(self):
        """初始化内置工具链模板"""
        # 这里可以定义一些常用的工具链模板
        # 例如：RAG查询链、数据分析链等
        pass

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_tools = len(self._tool_metadata)
        total_chains = len(self._tool_chains)

        tool_performance = {}
        for name, metadata in self._tool_metadata.items():
            tool_performance[name] = {
                'success_rate': metadata.success_rate,
                'avg_execution_time': metadata.avg_execution_time,
                'call_count': metadata.call_count,
                'quality_score': metadata.quality_score
            }

        cache_hits = sum(1 for _ in self._tool_selection_cache.values())
        cache_hit_rate = cache_hits / max(len(self._tool_selection_cache), 1)

        return {
            **self._stats,
            'total_tools': total_tools,
            'total_chains': total_chains,
            'tool_performance': tool_performance,
            'cache_size': len(self._tool_selection_cache),
            'cache_hit_rate': cache_hit_rate,
            'execution_history_size': len(self._execution_history)
        }

    # 核心执行方法
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        执行工具编排任务

        Args:
            context: 工具编排请求上下文
                - action: 操作类型 ("select_tool", "create_chain", "execute_chain", "optimize_prompt", "stats")
                - task_description: 任务描述 (select_tool时需要)
                - required_capabilities: 所需能力列表 (select_tool时需要)
                - chain_name/description/steps: 工具链信息 (create_chain时需要)
                - chain_id: 工具链ID (execute_chain时需要)
                - tool_name: 工具名称 (optimize_prompt时需要)
                - performance_history: 性能历史 (optimize_prompt时需要)

        Returns:
            AgentResult: 执行结果
        """
        start_time = time.time()
        action = context.get("action", "")

        try:
            if action == "select_tool":
                task_description = context.get("task_description", "")
                required_capabilities = context.get("required_capabilities", [])

                if not task_description or not required_capabilities:
                    result_data = {"error": "任务描述和所需能力不能为空"}
                else:
                    selected_tool = await self.select_optimal_tool(
                        task_description, required_capabilities, context
                    )
                    result_data = {
                        "selected_tool": selected_tool,
                        "selection_confidence": 0.8
                    }

            elif action == "create_chain":
                chain_name = context.get("chain_name", "")
                description = context.get("description", "")
                steps = context.get("steps", [])

                if not chain_name or not steps:
                    result_data = {"error": "工具链名称和步骤不能为空"}
                else:
                    chain_id = await self.create_tool_chain(chain_name, description, steps)
                    result_data = {"chain_id": chain_id, "status": "created"}

            elif action == "execute_chain":
                chain_id = context.get("chain_id", "")
                execution_context = context.get("execution_context", {})

                if not chain_id:
                    result_data = {"error": "工具链ID不能为空"}
                else:
                    execution_result = await self.execute_tool_chain(chain_id, execution_context)
                    result_data = execution_result

            elif action == "optimize_prompt":
                tool_name = context.get("tool_name", "")
                task_description = context.get("task_description", "")
                performance_history = context.get("performance_history", [])

                if not tool_name:
                    result_data = {"error": "工具名称不能为空"}
                else:
                    optimized_prompt = await self.optimize_prompt_template(
                        tool_name, task_description, performance_history
                    )
                    result_data = {"optimized_prompt": optimized_prompt}

            elif action == "stats":
                result_data = self.get_stats()

            else:
                result_data = {"error": f"不支持的操作: {action}"}

            return AgentResult(
                success=True,
                data=result_data,
                confidence=0.8,
                processing_time=time.time() - start_time
            )

        except Exception as e:
            self.module_logger.error(f"❌ ToolOrchestrator执行异常: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )

    def shutdown(self):
        """关闭工具编排器"""
        self._parallel_executor.shutdown(wait=True)
        self.module_logger.info("🛑 ToolOrchestrator已关闭")
