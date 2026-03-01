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

        # 初始化内置能力
        self._register_builtin_capabilities()

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

            logger.debug(f"✅ 能力执行成功: {name} ({execution_time:.3f}s)")
            return result

        except Exception as e:
            # 更新失败指标
            execution_time = time.time() - start_time
            metrics.total_calls += 1
            metrics.failed_calls += 1
            metrics.last_execution_time = execution_time
            metrics.error_rate = metrics.failed_calls / metrics.total_calls

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
        """解析工作流DSL"""
        # 简化的DSL解析器
        # 支持格式: "capability1 -> capability2 -> capability3"
        # 或 "capability1 | capability2 -> capability3"

        if '->' in workflow_spec:
            if '|' in workflow_spec:
                # 并行执行: "cap1 | cap2 -> cap3"
                parts = workflow_spec.split('->')
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
                # 顺序执行: "cap1 -> cap2 -> cap3"
                capabilities = [cap.strip() for cap in workflow_spec.split('->')]
                return {
                    'type': 'sequential',
                    'capabilities': capabilities
                }
        else:
            # 单能力执行
            return {
                'type': 'single',
                'capability': workflow_spec.strip()
            }

    async def _execute_workflow_plan(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流计划"""
        plan_type = plan['type']

        if plan_type == 'single':
            return await self.execute_capability(plan['capability'], context)

        elif plan_type == 'sequential':
            results = {}
            current_context = context.copy()

            for capability in plan['capabilities']:
                result = await self.execute_capability(capability, current_context)
                results[capability] = result
                # 将结果传递给下一个能力
                current_context.update(result)

            return {
                'workflow_type': 'sequential',
                'results': results,
                'final_result': results[plan['capabilities'][-1]] if results else {}
            }

        elif plan_type == 'parallel_sequential':
            # 并行执行第一阶段，然后顺序执行第二阶段
            parallel_results = {}
            parallel_tasks = []

            for capability in plan['parallel']:
                task = self.execute_capability(capability, context)
                parallel_tasks.append(task)

            parallel_task_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)

            for i, capability in enumerate(plan['parallel']):
                if isinstance(parallel_task_results[i], Exception):
                    parallel_results[capability] = {'error': str(parallel_task_results[i])}
                else:
                    parallel_results[capability] = parallel_task_results[i]

            # 合并并行结果作为后续能力的上下文
            combined_context = context.copy()
            for result in parallel_results.values():
                if isinstance(result, dict) and 'error' not in result:
                    combined_context.update(result)

            # 执行顺序阶段
            sequential_results = {}
            for capability in plan.get('sequential', []):
                result = await self.execute_capability(capability, combined_context)
                sequential_results[capability] = result
                combined_context.update(result)

            return {
                'workflow_type': 'parallel_sequential',
                'parallel_results': parallel_results,
                'sequential_results': sequential_results,
                'final_result': sequential_results[plan['sequential'][-1]] if plan.get('sequential') else combined_context
            }

        else:
            raise ValueError(f"不支持的工作流类型: {plan_type}")


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
