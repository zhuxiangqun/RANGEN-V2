#!/usr/bin/env python3
"""
ReasoningExpert - 推理专家 (L5高级认知)
复杂逻辑推理、策略制定与评估、因果关系分析
from ..utils.unified_centers import get_unified_config_center
from ..utils.unified_threshold_manager import get_unified_threshold_manager


优化特性：
- 并行推理引擎：多推理路径并发执行
- 推理结果缓存：避免重复推理计算
- 知识图谱集成：增强推理能力
- 自适应推理策略：根据问题复杂度选择推理方法
"""

import time
import logging
import asyncio
import hashlib
import json
import threading
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import re

from .expert_agent import ExpertAgent
from .base_agent import AgentResult
from ..utils.unified_centers import get_unified_config_center
from ..utils.unified_threshold_manager import get_unified_threshold_manager
from src.utils.logging_helper import get_module_logger, ModuleType

logger = logging.getLogger(__name__)


class ReasoningType(Enum):
    """推理类型"""
    DEDUCTIVE = "deductive"  # 演绎推理
    INDUCTIVE = "inductive"  # 归纳推理
    ABDUCTIVE = "abductive"  # 溯因推理
    ANALOGICAL = "analogical"  # 类比推理
    CAUSAL = "causal"  # 因果推理
    PROBABILISTIC = "probabilistic"  # 概率推理


class ReasoningComplexity(Enum):
    """推理复杂度"""
    SIMPLE = "simple"      # 简单推理 (1-2步)
    MODERATE = "moderate"  # 中等推理 (3-5步)
    COMPLEX = "complex"    # 复杂推理 (6-10步)
    ADVANCED = "advanced"  # 高级推理 (10+步)


@dataclass
class ReasoningTask:
    """推理任务"""
    id: str
    query: str
    context: Dict[str, Any]
    reasoning_type: ReasoningType = ReasoningType.DEDUCTIVE
    complexity: ReasoningComplexity = ReasoningComplexity.MODERATE
    max_parallel_paths: int = 3
    timeout_seconds: int = 300  # 5分钟超时
    submitted_time: float = field(default_factory=time.time)


@dataclass
class ReasoningPath:
    """推理路径"""
    id: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    reasoning_type: ReasoningType = ReasoningType.DEDUCTIVE
    execution_time: float = 0.0
    is_completed: bool = False
    error: Optional[str] = None
    final_answer: Optional[str] = None



class ReasoningExpert(ExpertAgent):
    """ReasoningExpert - 推理专家 (L5高级认知)

    核心职责：
    1. 复杂逻辑推理 - 多步骤推理链
    2. 策略制定与评估 - 决策树构建
    3. 因果关系分析 - 因果图谱推理
    4. 问题深度剖析 - 不确定性量化

    优化特性：
    - 并行推理引擎：多推理路径并发执行
    - 推理结果缓存：LRU缓存推理结果
    - 知识图谱集成：动态图谱构建和推理
    - 自适应策略选择：基于复杂度自动选择推理方法
    """

    def __init__(self):
        """初始化ReasoningExpert"""
        # 初始化统一配置中心
        self.config_center = get_unified_config_center()
        self.threshold_manager = get_unified_threshold_manager()

        # 获取Agent特定配置
        self.agent_config = self.config_center.get_config_section(self.__class__.__name__) or {
            'enabled': True,
            'max_retries': 3,
            'timeout': 30,
            'debug_mode': False
        }

        # 获取阈值配置
        self.thresholds = {
            'performance_warning_threshold': self.threshold_manager.get_dynamic_threshold('performance', default_value=5.0),
            'error_rate_threshold': self.threshold_manager.get_dynamic_threshold('error_rate', default_value=0.1),
            'memory_usage_threshold': self.threshold_manager.get_dynamic_threshold('memory', default_value=80.0)
        }

        super().__init__(
            agent_id="reasoning_expert",
            domain_expertise="逻辑推理与分析",
            capability_level=0.95,  # L5高级认知
            collaboration_style="analytical"
        )

        # 使用模块日志器
        self.module_logger = get_module_logger(ModuleType.AGENT, "ReasoningExpert")

        # 🚀 优化：推理缓存和并行处理配置
        from collections import OrderedDict
        self._reasoning_cache = OrderedDict()  # 使用有序字典实现LRU缓存
        self._cache_max_size = 1000  # 增加缓存容量
        self._cache_ttl = 3600  # 延长缓存有效期（1小时）
        self._parallel_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="reasoning_parallel")  # 降低并行度以避免OOM

        # 🚀 新增：推理引擎配置
        self._active_tasks: Dict[str, ReasoningTask] = {}  # 活跃推理任务
        self._reasoning_paths: Dict[str, List[ReasoningPath]] = {}  # 推理路径存储
        self._knowledge_graph = {}  # 知识图谱缓存

        # 🚀 新增：监控和统计
        self._stats = {
            'tasks_processed': 0,
            'cache_hits': 0,
            'parallel_executions': 0,
            'avg_reasoning_time': 0.0,
            'complexity_distribution': {}
        }

        # 启动清理线程
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = False
        self._start_cleanup_thread()

    def _get_service(self):
        """ReasoningExpert不直接使用单一Service"""
        return None

    def register_tool(self, tool, metadata: Optional[Dict[str, Any]] = None):
        """
        注册工具（为兼容性提供的方法）

        ReasoningExpert主要进行推理，不直接使用工具。
        这个方法是为了与ReActAgent的接口兼容而提供的。
        """
        self.module_logger.info(f"ℹ️ ReasoningExpert收到工具注册请求: {tool}, metadata: {metadata}")
        # ReasoningExpert不直接管理工具，记录日志即可
        return True

    # 🚀 新增：缓存管理方法
    def _get_cache_key(self, task: ReasoningTask) -> str:
        """生成推理缓存键"""
        key_data = {
            'query': task.query,
            'reasoning_type': task.reasoning_type.value,
            'complexity': task.complexity.value,
            'context_keys': sorted(task.context.keys())
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存的推理结果（LRU策略）"""
        if cache_key in self._reasoning_cache:
            cached_item = self._reasoning_cache[cache_key]
            if time.time() - cached_item['timestamp'] < self._cache_ttl:
                # LRU：将访问的项移到末尾（最近使用）
                self._reasoning_cache.move_to_end(cache_key)
                self.module_logger.debug(f"✅ 推理缓存命中: {cache_key}")
                self._stats['cache_hits'] += 1
                return cached_item['data']
            else:
                # 缓存过期，删除
                del self._reasoning_cache[cache_key]
        return None

    def _set_cached_result(self, cache_key: str, data: Dict[str, Any]):
        """设置缓存的推理结果（LRU策略）"""
        current_time = time.time()

        # 如果缓存已满，移除最旧的项（LRU）
        if len(self._reasoning_cache) >= self._cache_max_size:
            # 移除最旧的项（OrderedDict的第一个）
            oldest_key, _ = next(iter(self._reasoning_cache.items()))
            del self._reasoning_cache[oldest_key]
            self.module_logger.debug(f"🗑️ 缓存已满，移除最旧项: {oldest_key}")

        # 清理过期缓存（批量清理，提高效率）
        expired_keys = [
            k for k, v in list(self._reasoning_cache.items())
            if current_time - v['timestamp'] >= self._cache_ttl
        ]
        for k in expired_keys:
            del self._reasoning_cache[k]

        # 添加新缓存（新项自动添加到末尾）
        self._reasoning_cache[cache_key] = {
            'data': data,
            'timestamp': current_time
        }
        self.module_logger.debug(f"✅ 推理结果已缓存: {cache_key} (总缓存数: {len(self._reasoning_cache)})")

    # 🚀 新增：并行推理引擎
    async def _parallel_reasoning_engine(self, task: ReasoningTask) -> Dict[str, Any]:
        """并行推理引擎"""
        start_time = time.time()
        task_id = task.id

        self.module_logger.info(f"🔄 启动并行推理引擎: {task_id}, 类型={task.reasoning_type.value}, 复杂度={task.complexity.value}")

        # 初始化推理路径
        paths = []
        for i in range(task.max_parallel_paths):
            path = ReasoningPath(
                id=f"{task_id}_path_{i}",
                reasoning_type=task.reasoning_type
            )
            paths.append(path)

        self._reasoning_paths[task_id] = paths

        # 根据推理类型和复杂度选择推理策略
        if task.complexity == ReasoningComplexity.SIMPLE:
            # 简单推理：单路径执行
            result = await self._execute_single_path_reasoning(task, paths[0])
        elif task.complexity == ReasoningComplexity.MODERATE:
            # 中等推理：2-3路径并行
            parallel_paths = paths[:3]
            result = await self._execute_parallel_paths_reasoning(task, parallel_paths)
        else:
            # 复杂/高级推理：全并行执行 + 结果融合
            result = await self._execute_parallel_paths_reasoning(task, paths)
            if result['success']:
                result = await self._fuse_reasoning_results(task, paths)

        # 更新统计信息
        execution_time = time.time() - start_time
        self._stats['tasks_processed'] += 1
        self._stats['parallel_executions'] += 1
        self._stats['avg_reasoning_time'] = (
            (self._stats['avg_reasoning_time'] * (self._stats['tasks_processed'] - 1)) + execution_time
        ) / self._stats['tasks_processed']

        # 更新复杂度分布统计
        complexity_key = task.complexity.value
        if complexity_key not in self._stats['complexity_distribution']:
            self._stats['complexity_distribution'][complexity_key] = 0
        self._stats['complexity_distribution'][complexity_key] += 1

        result['execution_time'] = execution_time
        result['parallel_paths_used'] = len(paths)

        self.module_logger.info(f"✅ 并行推理完成: {task_id}, 耗时={execution_time:.2f}秒, 并行路径={len(paths)}")
        return result

    async def _execute_single_path_reasoning(self, task: ReasoningTask, path: ReasoningPath) -> Dict[str, Any]:
        """单路径推理执行"""
        try:
            import sys
            sys.stdout.write(f"🔍 [DEBUG] ReasoningExpert 单路径推理开始: {task.id}\n")
            sys.stdout.flush()

            # 🚀 优化：优先使用LLM进行推理
            if hasattr(self, 'llm_client') and self.llm_client:
                sys.stdout.write(f"🔍 [DEBUG] ReasoningExpert 使用LLM推理\n")
                sys.stdout.flush()
                return await self._execute_llm_reasoning(task, path)
            
            sys.stdout.write(f"⚠️ [DEBUG] ReasoningExpert LLM不可用，回退到传统Service\n")
            sys.stdout.flush()

            # 回退：调用传统推理服务
            from src.services.reasoning_service import ReasoningService
            service = ReasoningService()

            # 提取知识作为前提
            knowledge = task.context.get('knowledge', [])
            premises = []
            if isinstance(knowledge, list):
                for item in knowledge:
                    if isinstance(item, str):
                        premises.append(item)
                    elif isinstance(item, dict) and 'content' in item:
                        premises.append(item['content'])
            
            # 构建上下文，传递premises给ReasoningService
            context = {
                'query': task.query,
                'input': {
                    'premises': premises,
                    'observations': premises,  # 为归纳推理提供观察数据
                    'observation': task.query, # 为溯因推理提供观察现象
                    'conclusion': task.query   # 为演绎推理提供待验证结论
                },
                'reasoning_type': task.reasoning_type.value,
                'premises': premises,          # 兼容性字段
                'knowledge': knowledge         # 原始知识
            }

            # 直接调用同步方法
            agent_result = service.execute(context)


            if not agent_result.success:
                return {
                    'success': False,
                    'error': agent_result.error or '推理服务执行失败'
                }

            # 处理AgentResult对象
            result_data = agent_result.data if isinstance(agent_result.data, dict) else {}

            path.is_completed = True
            path.confidence = agent_result.confidence
            path.execution_time = agent_result.processing_time
            path.steps = result_data.get('reasoning_steps', [])

            return {
                'success': True,
                'reasoning': result_data.get('reasoning', ''),
                'final_answer': result_data.get('final_answer', ''),
                'confidence': path.confidence,
                'reasoning_steps': path.steps
            }

        except Exception as e:
            path.error = str(e)
            self.module_logger.warning(f"单路径推理失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _execute_llm_reasoning(self, task: ReasoningTask, path: ReasoningPath) -> Dict[str, Any]:
        """使用LLM执行推理"""
        import inspect
        import asyncio
        import json
        
        # 构造提示词
        context_str = json.dumps(task.context, ensure_ascii=False, default=str)
        prompt = f"""
        You are a Reasoning Expert (L5). Please answer the following query using {task.reasoning_type.value} reasoning.
        
        Query: {task.query}
        
        Context/Knowledge:
        {context_str}
        
        Please provide a step-by-step reasoning process and a final answer.
        
        Output format (JSON):
        {{
            "reasoning_steps": [
                {{"step": 1, "description": "...", "result": "..."}},
                ...
            ],
            "reasoning": "Summary of reasoning process...",
            "final_answer": "The final concise answer...",
            "confidence": 0.95
        }}
        """
        
        try:
            response = None
            # 检查call_llm是否是异步方法
            call_method = self.llm_client.call_llm
            if inspect.iscoroutinefunction(call_method):
                response = await call_method(prompt)
            else:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, lambda: call_method(prompt))
            
            if not response:
                raise ValueError("LLM returned empty response")
                
            # 解析JSON
            # 处理可能的Markdown代码块
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
                
            try:
                result_data = json.loads(json_str)
            except json.JSONDecodeError:
                # 尝试修复JSON或作为纯文本处理
                self.module_logger.warning(f"LLM响应JSON解析失败: {json_str[:100]}...")
                result_data = {
                    "reasoning": response,
                    "final_answer": response,
                    "confidence": 0.5,
                    "reasoning_steps": []
                }
            
            # 更新路径状态
            path.is_completed = True
            path.confidence = float(result_data.get('confidence', 0.8))
            path.steps = result_data.get('reasoning_steps', [])
            path.final_answer = result_data.get('final_answer', '')
            
            return {
                'success': True,
                'reasoning': result_data.get('reasoning', ''),
                'final_answer': result_data.get('final_answer', ''),
                'confidence': path.confidence,
                'reasoning_steps': path.steps
            }
            
        except Exception as e:
            self.module_logger.error(f"LLM推理执行失败: {e}")
            raise e  # 抛出异常以便回退到传统服务

    def shutdown(self):
        """关闭资源"""
        if self._parallel_executor:
            self._parallel_executor.shutdown(wait=True)
            self._parallel_executor = None

    def __del__(self):
        """析构函数"""
        self.shutdown()

    async def _execute_parallel_paths_reasoning(self, task: ReasoningTask, paths: List[ReasoningPath]) -> Dict[str, Any]:
        """并行多路径推理执行"""
        # 创建并行推理任务
        reasoning_tasks = []
        for path in paths:
            task_coro = self._execute_single_path_reasoning(task, path)
            reasoning_tasks.append(task_coro)

        # 并行执行
        self.module_logger.debug(f"🔄 并行执行 {len(paths)} 条推理路径")
        results = await asyncio.gather(*reasoning_tasks, return_exceptions=True)

        # 处理结果
        successful_paths = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                paths[i].error = str(result)
                self.module_logger.warning(f"推理路径 {i} 异常: {result}")
            elif result['success']:
                successful_paths.append(paths[i])

        if not successful_paths:
            return {
                'success': False,
                'error': '所有推理路径均失败'
            }

        # 返回最优路径结果
        best_path = max(successful_paths, key=lambda p: p.confidence)
        return {
            'success': True,
            'reasoning': f"并行推理结果 (置信度: {best_path.confidence:.2f})",
            'final_answer': best_path.final_answer or "并行推理完成",
            'confidence': best_path.confidence,
            'parallel_paths': len(successful_paths),
            'reasoning_steps': best_path.steps
        }

    async def _fuse_reasoning_results(self, task: ReasoningTask, paths: List[ReasoningPath]) -> Dict[str, Any]:
        """融合多路径推理结果"""
        # 筛选成功的路径
        successful_paths = [p for p in paths if p.is_completed and p.error is None]

        if not successful_paths:
            return {
                'success': False,
                'error': '无有效的推理结果可融合'
            }

        # 基于置信度加权融合
        total_confidence = sum(p.confidence for p in successful_paths)
        if total_confidence == 0:
            # 如果所有置信度都是0，使用第一个结果
            best_path = successful_paths[0]
        else:
            # 选择置信度最高的路径
            best_path = max(successful_paths, key=lambda p: p.confidence)

        # 这里可以实现更复杂的融合逻辑，比如：
        # - 多路径结果投票
        # - 置信度加权平均
        # - 矛盾检测和解决

        # 提取最佳路径的答案
        final_answer = best_path.final_answer
        if not final_answer and best_path.steps:
             # 尝试从最后一个步骤提取答案
             last_step = best_path.steps[-1]
             final_answer = last_step.get('result', {}).get('answer', '')

        return {
            'success': True,
            'reasoning': f"多路径推理融合 (路径数: {len(successful_paths)}, 最佳置信度: {best_path.confidence:.2f})",
            'final_answer': final_answer or "无法从最佳路径提取答案",
            'confidence': best_path.confidence,
            'fused_paths': len(successful_paths),
            'reasoning_steps': best_path.steps
        }

    # 🚀 新增：自适应推理策略选择
    def _analyze_reasoning_complexity(self, query: str, context: Dict[str, Any]) -> ReasoningComplexity:
        """分析推理复杂度"""
        # 基于查询长度和关键词分析复杂度
        query_length = len(query)
        has_logical_keywords = any(word in query.lower() for word in
                                 ['if', 'then', 'because', 'therefore', 'however', 'although'])
        has_quantitative_keywords = any(word in query.lower() for word in
                                      ['how many', 'percentage', 'ratio', 'calculate', 'compute'])
        has_causal_keywords = any(word in query.lower() for word in
                                ['why', 'cause', 'effect', 'result', 'lead to', 'because of'])

        complexity_score = 0

        # 长度因素
        if query_length > 200:
            complexity_score += 2
        elif query_length > 100:
            complexity_score += 1

        # 逻辑关键词
        if has_logical_keywords:
            complexity_score += 2

        # 量化关键词
        if has_quantitative_keywords:
            complexity_score += 1

        # 因果关键词
        if has_causal_keywords:
            complexity_score += 2

        # 上下文复杂度
        context_size = len(str(context))
        if context_size > 1000:
            complexity_score += 1

        # 根据分数确定复杂度
        if complexity_score >= 5:
            return ReasoningComplexity.ADVANCED
        elif complexity_score >= 3:
            return ReasoningComplexity.COMPLEX
        elif complexity_score >= 2:
            return ReasoningComplexity.MODERATE
        else:
            return ReasoningComplexity.SIMPLE

    def _select_reasoning_type(self, query: str, context: Dict[str, Any]) -> ReasoningType:
        """选择推理类型"""
        query_lower = query.lower()

        # 因果推理关键词
        if any(word in query_lower for word in ['why', 'cause', 'effect', 'because', 'lead to']):
            return ReasoningType.CAUSAL

        # 溯因推理关键词
        if any(word in query_lower for word in ['probably', 'likely', 'might be', 'could be']):
            return ReasoningType.ABDUCTIVE

        # 归纳推理关键词
        if any(word in query_lower for word in ['generally', 'usually', 'tend to', 'based on']):
            return ReasoningType.INDUCTIVE

        # 类比推理关键词
        if any(word in query_lower for word in ['similar to', 'like', 'analogous', 'compare']):
            return ReasoningType.ANALOGICAL

        # 默认演绎推理
        return ReasoningType.DEDUCTIVE

    # 🚀 新增：知识图谱集成
    def _build_knowledge_graph(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """构建知识图谱"""
        # 从上下文构建简单的知识图谱
        # 这里可以集成更复杂的图谱构建算法

        entities = []
        relations = []

        # 简单的实体提取（可以替换为更复杂的NLP模型）
        text_content = str(context.get('knowledge', '')) + str(context.get('evidence', []))

        # 查找可能的实体（大写开头的词组）
        entity_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        found_entities = re.findall(entity_pattern, text_content)

        for entity in found_entities[:10]:  # 限制实体数量
            if entity not in entities:
                entities.append(entity)

        # 简单的关系提取
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                if entity1 in text_content and entity2 in text_content:
                    # 检查两个实体是否在同一句子中
                    sentences = re.split(r'[.!?]+', text_content)
                    for sentence in sentences:
                        if entity1 in sentence and entity2 in sentence:
                            relations.append({
                                'subject': entity1,
                                'relation': 'related_to',
                                'object': entity2
                            })
                            break

        return {
            'entities': entities,
            'relations': relations,
            'entity_count': len(entities),
            'relation_count': len(relations)
        }

    async def _graph_based_reasoning(self, task: ReasoningTask) -> Dict[str, Any]:
        """基于图谱的推理"""
        # 构建知识图谱
        graph = self._build_knowledge_graph(task.context)

        # 使用图谱进行推理
        # 这里可以实现图遍历、路径发现等图推理算法

        self.module_logger.debug(f"📊 构建知识图谱: {graph['entity_count']} 个实体, {graph['relation_count']} 个关系")

        # 简单的图推理：查找相关路径
        reasoning_result = {
            'graph_entities': graph['entities'],
            'graph_relations': graph['relations'],
            'reasoning_type': 'graph_based'
        }

        return reasoning_result

    def shutdown(self):
        """关闭资源"""
        self._running = False
        if self._parallel_executor:
            try:
                self._parallel_executor.shutdown(wait=False)
            except Exception:
                pass
            self._parallel_executor = None
        
        # 停止清理线程
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            # 这里的线程是daemon线程，不需要join，但可以设置标志位
            pass
            
        self.module_logger.info("🛑 ReasoningExpert资源已释放")

    def __del__(self):
        """析构函数，确保资源释放"""
        try:
            self.shutdown()
        except Exception:
            pass

    def _start_cleanup_thread(self):
        """启动缓存清理线程"""
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        self.module_logger.debug("🧹 缓存清理线程已启动")

    def _cleanup_worker(self):
        """缓存清理工作线程"""
        while self._running:
            try:
                time.sleep(300)  # 每5分钟清理一次

                # 清理过期缓存
                current_time = time.time()
                expired_keys = [
                    k for k, v in self._reasoning_cache.items()
                    if current_time - v['timestamp'] >= self._cache_ttl
                ]

                for k in expired_keys:
                    del self._reasoning_cache[k]

                if expired_keys:
                    self.module_logger.debug(f"🧹 清理过期缓存: {len(expired_keys)} 项")

                # 清理完成的推理任务
                completed_tasks = [
                    task_id for task_id, task in self._active_tasks.items()
                    if current_time - task.submitted_time > 3600  # 1小时后清理
                ]

                for task_id in completed_tasks:
                    if task_id in self._active_tasks:
                        del self._active_tasks[task_id]
                    if task_id in self._reasoning_paths:
                        del self._reasoning_paths[task_id]

            except Exception as e:
                self.module_logger.warning(f"缓存清理异常: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            'cache_size': len(self._reasoning_cache),
            'active_tasks': len(self._active_tasks),
            'cache_hit_rate': self._stats['cache_hits'] / max(self._stats['tasks_processed'], 1)
        }

    # 核心执行方法
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        执行推理任务（优化版）

        Args:
            context: 推理请求上下文
                - query: 推理查询（必需）
                - reasoning_type: 推理类型（可选，默认自动分析）
                - complexity: 推理复杂度（可选，默认自动分析）
                - max_parallel_paths: 最大并行路径数（可选，默认3）
                - use_cache: 是否使用缓存（可选，默认True）
                - use_graph: 是否使用图谱推理（可选，默认False）

        Returns:
            AgentResult: 推理结果
        """
        start_time = time.time()
        query = context.get("query", "")

        if not query:
            return AgentResult(
                success=False,
                data=None,
                error="推理查询不能为空",
                confidence=0.0,
                processing_time=time.time() - start_time
            )

        self.module_logger.info(f"🧠 ReasoningExpert开始推理: {query[:100]}...")

        # 🚀 新增：缓存检查
        use_cache = context.get('use_cache', True)
        if use_cache:
            # 创建推理任务对象用于缓存键生成
            temp_task = ReasoningTask(
                id=f"temp_{int(time.time() * 1000)}",
                query=query,
                context=context,
                reasoning_type=self._select_reasoning_type(query, context),
                complexity=self._analyze_reasoning_complexity(query, context)
            )
            cache_key = self._get_cache_key(temp_task)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.module_logger.info("✅ 使用推理缓存结果")
                return AgentResult(
                    success=True,
                    data=cached_result,
                    confidence=cached_result.get('confidence', 0.8),
                    processing_time=time.time() - start_time
                )

        # 创建推理任务
        task = ReasoningTask(
            id=f"reasoning_{int(time.time() * 1000)}_{hash(query) % 10000}",
            query=query,
            context=context,
            reasoning_type=self._select_reasoning_type(query, context),
            complexity=self._analyze_reasoning_complexity(query, context),
            max_parallel_paths=context.get('max_parallel_paths', 3),
            timeout_seconds=context.get('timeout_seconds', 300)
        )

        self._active_tasks[task.id] = task

        try:
            # 执行并行推理
            use_graph = context.get('use_graph', False)
            if use_graph and task.complexity in [ReasoningComplexity.COMPLEX, ReasoningComplexity.ADVANCED]:
                # 复杂推理使用图谱增强
                self.module_logger.info("📊 使用图谱增强推理")
                graph_result = await self._graph_based_reasoning(task)
                reasoning_result = await self._parallel_reasoning_engine(task)
                reasoning_result.update(graph_result)
            else:
                # 标准并行推理
                reasoning_result = await self._parallel_reasoning_engine(task)

            if not reasoning_result['success']:
                return AgentResult(
                    success=False,
                    data=None,
                    error=reasoning_result.get('error', '推理失败'),
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )

            # 构建返回结果
            result_data = {
                "reasoning": reasoning_result.get('reasoning', ''),
                "final_answer": reasoning_result.get('final_answer', ''),
                "confidence": reasoning_result.get('confidence', 0.7),
                "reasoning_steps": reasoning_result.get('reasoning_steps', []),
                "execution_time": reasoning_result.get('execution_time', 0.0),
                "parallel_paths_used": reasoning_result.get('parallel_paths_used', 1),
                "reasoning_type": task.reasoning_type.value,
                "complexity": task.complexity.value,
                "query": query
            }

            # 🚀 新增：设置缓存
            if use_cache:
                cache_key = self._get_cache_key(task)
                self._set_cached_result(cache_key, result_data)

            self.module_logger.info(f"✅ ReasoningExpert推理成功，耗时: {reasoning_result.get('execution_time', 0.0):.2f}秒")

            return AgentResult(
                success=True,
                data=result_data,
                confidence=result_data['confidence'],
                processing_time=time.time() - start_time,
                metadata={
                    "reasoning_type": task.reasoning_type.value,
                    "complexity": task.complexity.value,
                    "parallel_paths": result_data["parallel_paths_used"],
                    "cached": False
                }
            )

        except Exception as e:
            self.module_logger.error(f"❌ ReasoningExpert推理异常: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
        finally:
            # 清理完成的推理任务
            if task.id in self._active_tasks:
                del self._active_tasks[task.id]
            if task.id in self._reasoning_paths:
                del self._reasoning_paths[task.id]

    def shutdown(self):
        """关闭推理专家"""
        self._running = False
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)

        self._parallel_executor.shutdown(wait=True)
        self.module_logger.info("🛑 ReasoningExpert已关闭")
