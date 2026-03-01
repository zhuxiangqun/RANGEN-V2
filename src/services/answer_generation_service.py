"""
答案生成服务 - 从EnhancedAnswerGenerationAgent重命名

注意：这是一个服务组件，不是Agent。它提供答案生成功能，可以被Agent使用。
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import logging
import time
import re
import threading
import asyncio

from src.agents.base_agent import BaseAgent, AgentResult, AgentConfig
from src.utils.unified_centers import get_unified_config_center

logger = logging.getLogger(__name__)

class AnswerGenerationService(BaseAgent):
    """答案生成服务 - 从EnhancedAnswerGenerationAgent重命名
    
    这是一个服务组件，不是Agent。它提供答案生成功能，可以被Agent使用。
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__("AnswerGenerationService")

        self.is_executing = False
        self._execution_lock = threading.Lock()
        self._checked_queries = set()  # 🚀 优化：记录已检查的查询，避免重复警告

        self.unified_config = None
        try:
            self.unified_config = get_unified_config_center()
            logger.debug("✅ 统一配置管理中心初始化成功")
        except Exception as e:
            logger.warning(f"统一配置管理中心初始化失败: {e}")
            self.unified_config = None

        if config:
            self.config = config

    async def _generate_structured_answer(self, query: str, knowledge_data: List[Dict[str, Any]], reasoning_data: Dict[str, Any]) -> str:
        """生成结构化答案 - 真正的智能答案生成实现"""
        try:
            # 分析查询类型和复杂度
            query_analysis = self._analyze_query_complexity(query)
            
            # 基于查询类型选择生成策略
            if query_analysis['type'] == 'factual':
                return await self._generate_factual_answer(query, knowledge_data, reasoning_data)
            elif query_analysis['type'] == 'analytical':
                return await self._generate_analytical_answer(query, knowledge_data, reasoning_data)
            elif query_analysis['type'] == 'comparative':
                return self._generate_comparative_answer(query, knowledge_data, reasoning_data)
            elif query_analysis['type'] == 'explanatory':
                return self._generate_explanatory_answer(query, knowledge_data, reasoning_data)
            else:
                return await self._generate_general_answer(query, knowledge_data, reasoning_data)
            
        except Exception as e:
            logger.error(f"答案生成失败: {e}")
            return f"基于查询 '{query}' 的答案生成失败：{str(e)}"

    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行答案生成任务"""
        start_time = time.time()
        success = False
        answer = ""
        
        # 🚀 优化：每次execute调用时重置检查标记（因为可能是新的查询）
        # 但使用context中的query作为key来区分不同的查询
        query = context.get('query', '')
        current_query_key = f"query_{hash(query)}"
        if not hasattr(self, '_checked_queries'):
            self._checked_queries = set()
        is_first_call_for_query = current_query_key not in self._checked_queries
        if is_first_call_for_query:
            self._checked_queries.add(current_query_key)
        
        try:
            with self._execution_lock:
                self.is_executing = True

            knowledge_data = context.get('knowledge_data', [])
            if knowledge_data:
                logger.info(f"🔍 [AnswerGenerationService] 从context获取到 knowledge_data, 长度: {len(knowledge_data)}")
            else:
                logger.info(f"🔍 [AnswerGenerationService] context中没有 knowledge_data 或为空")
            
            reasoning_data = context.get('reasoning_data', {})
            
            # 🚀 P0修复：优先从dependencies中获取reasoning_expert的结果
            # 避免重复执行推理，直接使用推理Agent已经生成的答案
            dependencies = context.get('dependencies', {})
            
            # 🚀 优化：只在第一次调用时输出详细日志，避免重复警告
            is_first_call = is_first_call_for_query
            if is_first_call:
                logger.info(f"🔍 [AnswerGeneration] 检查dependencies: keys={list(dependencies.keys()) if dependencies else 'empty'}")
                if dependencies:
                    for dep_key, dep_value in dependencies.items():
                        logger.info(f"🔍 [AnswerGeneration] 依赖项: key={dep_key}, value_type={type(dep_value)}, has_data={hasattr(dep_value, 'data') if hasattr(dep_value, '__class__') else 'N/A'}")
                        if hasattr(dep_value, 'data'):
                            logger.info(f"🔍 [AnswerGeneration] {dep_key}.data类型={type(dep_value.data)}, 内容预览={str(dep_value.data)[:200] if dep_value.data else 'None'}")
                        elif isinstance(dep_value, dict):
                            logger.info(f"🔍 [AnswerGeneration] {dep_key}是dict, keys={list(dep_value.keys())[:10]}")
            
            if dependencies:
                # 🚀 修复：查找reasoning任务的结果（支持多种key格式：task_2, reasoning, reasoning_expert等）
                # 推理任务通常是task_2（在标准流程中），但也支持其他命名
                reasoning_keys = ['task_2', 'reasoning', 'reasoning_expert', 'reasoning_agent']
                
                # 🚀 彻底修复：详细日志，记录所有dependencies的内容
                if is_first_call:
                    logger.info(f"🔍 [AnswerGeneration] dependencies详细内容:")
                    for dep_key, dep_val in dependencies.items():
                        logger.info(f"   - {dep_key}: type={type(dep_val)}")
                        if hasattr(dep_val, '__dict__'):
                            logger.info(f"      attributes: {list(dep_val.__dict__.keys())[:10]}")
                        elif isinstance(dep_val, dict):
                            logger.info(f"      keys: {list(dep_val.keys())[:10]}")
                            # 检查是否包含data字段
                            if 'data' in dep_val:
                                data_val = dep_val['data']
                                logger.info(f"      data type: {type(data_val)}")
                                if isinstance(data_val, dict):
                                    logger.info(f"      data keys: {list(data_val.keys())[:10]}")
                                    if 'final_answer' in data_val:
                                        logger.info(f"      ✅ 找到final_answer: {data_val['final_answer'][:100]}")
                                    if 'answer' in data_val:
                                        logger.info(f"      ✅ 找到answer: {data_val['answer'][:100]}")
                
                # 首先尝试按优先级查找推理任务
                dep_value = None
                reasoning_key = None
                for reasoning_key in reasoning_keys:
                    if reasoning_key in dependencies:
                        dep_value = dependencies[reasoning_key]
                        if is_first_call:
                            logger.info(f"🔍 [AnswerGeneration] 找到推理任务: key={reasoning_key}, value_type={type(dep_value)}")
                        break
                
                if dep_value is None:
                    # 如果没有找到标准key，遍历所有dependencies查找
                    for dep_key, dep_val in dependencies.items():
                        # 检查是否是reasoning任务的结果（通过key名称或value类型判断）
                        if 'reasoning' in dep_key.lower() or (isinstance(dep_val, dict) and dep_key.startswith('task_')):
                            # 对于task_*格式，需要进一步判断是否是推理任务
                            # 通常task_2是推理任务，但为了兼容性，也检查value的内容
                            if dep_key == 'task_2' or (isinstance(dep_val, dict) and ('final_answer' in str(dep_val) or 'answer' in str(dep_val))):
                                dep_value = dep_val
                                reasoning_key = dep_key
                                if is_first_call:
                                    logger.info(f"🔍 [AnswerGeneration] 通过内容判断找到推理任务: key={reasoning_key}")
                                break
                
                if dep_value is not None:
                    # 尝试从依赖结果中提取推理答案
                    dep_data = None
                    
                    # 情况1: dep_value是AgentResult对象
                    if hasattr(dep_value, 'data'):
                        dep_data = dep_value.data
                        logger.info(f"🔍 [AnswerGeneration] 从AgentResult.data提取: {type(dep_data)}, 内容预览={str(dep_data)[:200] if dep_data else 'None'}")
                    # 情况2: dep_value是字典，包含data字段
                    elif isinstance(dep_value, dict):
                        # 🚀 修复：优先检查是否有直接的final_answer或answer字段（我们传递的格式）
                        if 'final_answer' in dep_value:
                            dep_data = {'final_answer': dep_value['final_answer'], 'answer': dep_value.get('answer', dep_value['final_answer'])}
                            logger.info(f"🔍 [AnswerGeneration] 从dict直接提取final_answer: {dep_value['final_answer'][:100] if dep_value['final_answer'] else 'None'}")
                        elif 'answer' in dep_value:
                            dep_data = {'answer': dep_value['answer'], 'final_answer': dep_value['answer']}
                            logger.info(f"🔍 [AnswerGeneration] 从dict直接提取answer: {dep_value['answer'][:100] if dep_value['answer'] else 'None'}")
                        elif 'data' in dep_value:
                            dep_data = dep_value['data']
                            logger.info(f"🔍 [AnswerGeneration] 从dict['data']提取: {type(dep_data)}, 内容预览={str(dep_data)[:200] if dep_data else 'None'}")
                        elif 'result' in dep_value:
                            result_obj = dep_value['result']
                            if hasattr(result_obj, 'data'):
                                dep_data = result_obj.data
                                logger.info(f"🔍 [AnswerGeneration] 从dict['result'].data提取: {type(dep_data)}, 内容预览={str(dep_data)[:200] if dep_data else 'None'}")
                            elif isinstance(result_obj, dict) and 'data' in result_obj:
                                dep_data = result_obj['data']
                                logger.info(f"🔍 [AnswerGeneration] 从dict['result']['data']提取: {type(dep_data)}, 内容预览={str(dep_data)[:200] if dep_data else 'None'}")
                        else:
                            # 直接使用dep_value作为data
                            dep_data = dep_value
                            logger.info(f"🔍 [AnswerGeneration] 直接使用dep_value作为data: {type(dep_data)}, 内容预览={str(dep_data)[:200] if dep_data else 'None'}")
                    
                    # 尝试提取final_answer或answer
                    if dep_data:
                        if isinstance(dep_data, dict):
                            reasoning_answer = dep_data.get('final_answer') or dep_data.get('answer', '')
                            logger.info(f"🔍 [AnswerGeneration] 从dict提取答案: final_answer={bool(dep_data.get('final_answer'))}, answer={bool(dep_data.get('answer'))}, 提取结果={reasoning_answer[:100] if reasoning_answer else 'None'}")
                        elif isinstance(dep_data, str):
                            # 如果dep_data是字符串，直接使用
                            reasoning_answer = dep_data.strip()
                            logger.info(f"🔍 [AnswerGeneration] dep_data是字符串，直接使用: {reasoning_answer[:100]}")
                        else:
                            reasoning_answer = None
                            logger.warning(f"⚠️ [AnswerGeneration] dep_data类型不支持: {type(dep_data)}")
                        
                        if reasoning_answer and reasoning_answer.strip():
                            logger.info(f"✅ [AnswerGeneration] 从依赖任务({reasoning_key})中获取推理答案: {reasoning_answer[:50]}...")
                            # 🚀 答案生成Agent的作用：格式化和优化推理答案
                            # 1. 获取推理答案
                            answer = reasoning_answer.strip()
                            
                            # 2. 增强答案结构（如果需要）
                            answer = self._enhance_answer_structure(answer)
                            
                            # 3. 验证答案质量
                            quality_metrics = self._validate_answer_quality(answer)
                            
                            # 4. 计算智能置信度
                            confidence = self._calculate_intelligent_confidence('answer_generation_success')
                            
                            # 5. 生成元数据
                            metadata = self._generate_metadata(query, answer, time.time() - start_time)
                            metadata.update(quality_metrics)
                            
                            success = True
                            execution_time = time.time() - start_time
                            
                            logger.info(f"✅ [AnswerGeneration] 答案格式化完成: 长度={len(answer)}, 质量={quality_metrics.get('completeness', 0.0):.2f}")
                            
                            return AgentResult(
                                success=True,
                                data={
                                    "answer": answer,
                                    "final_answer": answer,
                                    "confidence": confidence,
                                    "metadata": metadata,
                                    "generation_method": "answer_formatting_and_optimization"
                                },
                                confidence=confidence,
                                processing_time=execution_time
                            )
                        else:
                            if is_first_call:
                                logger.warning(f"⚠️ [AnswerGeneration] 从{reasoning_key}提取的推理答案为空或无效: reasoning_answer={reasoning_answer}")
                else:
                    # 🚀 优化：检查推理任务是否还在执行中（可能还没有完成）
                    # 如果task_2在dependencies中但值为None或状态不是completed，说明还在执行中
                    reasoning_task_in_progress = False
                    for dep_key in ['task_2', 'reasoning', 'reasoning_expert']:
                        if dep_key in dependencies:
                            dep_value = dependencies[dep_key]
                            # 如果值是None或包含"in_progress"等状态，说明还在执行中
                            if dep_value is None or (isinstance(dep_value, dict) and dep_value.get('status') in ['in_progress', 'pending']):
                                reasoning_task_in_progress = True
                                if is_first_call:
                                    logger.debug(f"🔍 [AnswerGeneration] 推理任务({dep_key})还在执行中，等待完成...")
                                break
                    
                    if not reasoning_task_in_progress and is_first_call:
                        logger.warning(f"⚠️ [AnswerGeneration] 未找到推理任务结果，dependencies keys={list(dependencies.keys())}")
            
            # 🚀 P0修复：如果没有从dependencies获取到推理答案，不应该重新推理
            # 答案生成Agent的职责是格式化和优化，而不是重新生成答案
            # 🚀 优化：只在第一次调用时输出警告，避免重复警告
            if is_first_call:
                logger.warning(f"⚠️ [AnswerGeneration] 未能从dependencies获取推理答案，答案生成Agent不应该重新推理。返回错误。")
            return AgentResult(
                success=False,
                data=None,
                error="答案生成Agent需要推理Agent的结果，但未能从dependencies中获取。答案生成Agent不应该重新推理。",
                confidence=0.0,
                processing_time=time.time() - start_time
            )

            # 生成答案
            answer = await self._generate_structured_answer(query, knowledge_data, reasoning_data)
            
            # 增强答案结构
            answer = self._enhance_answer_structure(answer)
            
            # 计算智能置信度
            confidence = self._calculate_intelligent_confidence('answer_generation_success')
            
            execution_time = time.time() - start_time
            success = True

            # 记录生成事件
            self._log_generation_event(query, answer, success, execution_time)

            # 生成元数据
            metadata = self._generate_metadata(query, answer, execution_time)

            return AgentResult(
                success=True,
                data={
                    'answer': answer,
                    'confidence': confidence,
                    'generation_method': 'enhanced_answer_generation',
                    'metadata': metadata
                },
                confidence=confidence,
                processing_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"答案生成失败: {e}")
            
            # 生成回退答案
            answer = self._generate_fallback_answer(context.get('query', ''), str(e))
            
            # 记录失败事件
            self._log_generation_event(context.get('query', ''), answer, False, execution_time)
            
            return AgentResult(
                success=False,
                data={
                    'answer': answer,
                    'error': str(e),
                    'generation_method': 'fallback_answer_generation'
                },
                confidence=0.0,
                processing_time=execution_time,
                error=str(e)
            )
        finally:
            with self._execution_lock:
                self.is_executing = False

    def _get_default_confidence(self, confidence_type: str) -> float:
        """获取默认置信度 - 使用统一智能评分器"""
        try:
            # 使用统一智能评分器
            try:
                # 尝试使用统一中心获取智能评分器
                if self.unified_config:
                    scorer = self.unified_config.get_config_value("ai_algorithms", "intelligent_scorer", None)
                    if scorer and hasattr(scorer, 'get_intelligent_confidence'):
                        return scorer.get_intelligent_confidence(confidence_type)
            except (ImportError, AttributeError, KeyError):
                # 回退到默认置信度计算
                return self._calculate_default_confidence(confidence_type)
            
            # 如果没有找到智能评分器，使用默认计算
            return self._calculate_default_confidence(confidence_type)
            
        except Exception as e:
            # 最终回退
            return self._calculate_default_confidence(confidence_type)
    
    def _calculate_default_confidence(self, confidence_type: str) -> float:
        """计算默认置信度"""
        try:
            if confidence_type == 'semantic':
                return 0.8
            elif confidence_type == 'syntactic':
                return 0.7
            elif confidence_type == 'contextual':
                return 0.75
            elif confidence_type == 'temporal':
                return 0.6
            else:
                return 0.5
        except Exception:
            return 0.5
    
    def _get_minimum_confidence(self, confidence_type: str) -> float:
        """获取最小置信度"""
        try:
            # 智能回退
            min_confidences = {
                "answer_generation_success": 0.6,
                "answer_quality": 0.7,
                "answer_completeness": 0.8,
                "answer_accuracy": 0.9
            }
            return min_confidences.get(confidence_type, 0.7)
        except Exception as e:
            logger.warning(f"获取智能置信度失败: {e}，使用最小化回退值")
            return 0.7

    def _get_intelligent_limit(self, limit_type: str) -> int:
        """获取智能限制值"""
        try:
            if self.unified_config:
                limit_value = self.unified_config.get_config_value("limits", f"limit_{limit_type}", None)
                if limit_value is not None:
                    return int(limit_value)

            return self._get_default_limit(limit_type)

        except Exception as e:
            logger.warning(f"获取智能限制值失败: {e}，使用默认值")
            return self._get_default_limit(limit_type)

    def _get_default_limit(self, limit_type: str) -> int:
        """获取默认限制值（回退值）"""
        try:
            if self.unified_config:
                limit_value = self.unified_config.get_config_value("limits", f"limit_{limit_type}", None)
                if limit_value is not None:
                    return int(limit_value)

            # 默认限制值
            default_limits = {
                "knowledge_items": 5,
                "reasoning_steps": 3,
                "max_knowledge_content_length": 200,
                "max_reasoning_content_length": 150
            }
            return default_limits.get(limit_type, 5)

        except Exception as e:
            logger.warning(f"获取智能限制值失败: {e}，使用最小化回退值")
            min_limits = {
                "knowledge_items": 3,
                "reasoning_steps": 3,
                "max_knowledge_content_length": 100,
                "max_reasoning_content_length": 100
            }
            return min_limits.get(limit_type, 3)

    def _get_current_query_context(self) -> Dict[str, Any]:
        """获取当前查询上下文"""
        return {
            "query_type": getattr(self, 'current_query_type', 'general'),
            "generation_method": 'enhanced_answer_generation'
        }

    def _generate_intelligent_answer_framework(self, query: str) -> str:
        """生成智能答案框架 - 零硬编码"""
        try:
            # 使用统一智能标识符
            identifier = self._get_intelligent_identifier()
            
            if identifier:
                query_lower = query.lower()
                if identifier.is_question_word(query_lower):
                    return self._generate_question_framework(query)
                elif identifier.is_mathematical_word(query_lower):
                    return self._generate_calculation_framework(query)
                elif identifier.is_comparative_word(query_lower):
                    return self._generate_comparison_framework(query)
                else:
                    return self._generate_general_framework(query)
            else:
                return self._generate_fallback_framework(query)

        except Exception as e:
            logger.warning(f"智能框架生成失败: {e}")
            return self._generate_fallback_framework(query)
    
    def _get_intelligent_identifier(self):
        """获取智能标识符"""
        try:
            if self.unified_config:
                return self.unified_config.get_config_value("ai_algorithms", "identifier", None)
            return None
        except Exception as e:
            logger.debug(f"获取智能标识符失败: {e}")
            return None

    def _generate_question_framework(self, query: str) -> str:
        """生成疑问句框架"""
        try:
            if self.unified_config:
                template = self.unified_config.get_config_value("answer_frameworks", "question", "")
                if template:
                    return template.format(query=query)
        except Exception as e:
            logger.debug(f"获取疑问句框架模板失败: {e}")

        return f"针对'{query}'的分析：\n\n"

    def _generate_calculation_framework(self, query: str) -> str:
        """生成计算类框架"""
        try:
            if self.unified_config:
                template = self.unified_config.get_config_value("answer_frameworks", "calculation", "")
                if template:
                    return template.format(query=query)
        except Exception as e:
            logger.debug(f"获取计算类框架模板失败: {e}")

        return f"关于'{query}'的计算分析：\n\n"

    def _generate_comparison_framework(self, query: str) -> str:
        """生成比较类框架"""
        try:
            if self.unified_config:
                template = self.unified_config.get_config_value("answer_frameworks", "comparison", "")
                if template:
                    return template.format(query=query)
        except Exception as e:
            logger.debug(f"获取比较类框架模板失败: {e}")

        return f"'{query}'的比较分析：\n\n"

    def _generate_general_framework(self, query: str) -> str:
        """生成通用框架"""
        try:
            if self.unified_config:
                template = self.unified_config.get_config_value("answer_frameworks", "general", "")
                if template:
                    return template.format(query=query)
        except Exception as e:
            logger.debug(f"获取通用框架模板失败: {e}")

        return f"关于'{query}'：\n\n"

    def _generate_fallback_framework(self, query: str) -> str:
        """生成回退框架"""
        try:
            if self.unified_config:
                template = self.unified_config.get_config_value("answer_frameworks", "general", "")
                if template:
                    return template.format(query=query)
        except Exception as e:
            logger.debug(f"获取回退框架模板失败: {e}")

        return f"回答：\n\n"

    def _generate_knowledge_section_header(self) -> str:
        """生成知识部分标题"""
        try:
            if self.unified_config:
                header = self.unified_config.get_config_value("section_headers", "knowledge", "")
                if header:
                    return header
        except Exception as e:
            logger.debug(f"获取知识部分标题模板失败: {e}")

        return "相关信息：\n"

    def _generate_reasoning_section_header(self) -> str:
        """生成推理部分标题"""
        try:
            if self.unified_config:
                header = self.unified_config.get_config_value("section_headers", "reasoning", "")
                if header:
                    return header
        except Exception as e:
            logger.debug(f"获取推理部分标题模板失败: {e}")

        return "分析过程：\n"

    def _is_answer_framework_empty(self, answer_framework: str, query: str) -> bool:
        """检查答案框架是否为空"""
        cleaned = answer_framework.strip()
        fallback_patterns = [
            f"针对'{query}'的分析：",
            f"关于'{query}'的计算分析：",
            f"'{query}'的比较分析：",
            f"关于'{query}'：",
            "回答："
        ]

        for pattern in fallback_patterns:
            if cleaned == pattern:
                return True

        return len(cleaned) < 20

    def _process_knowledge_data(self, knowledge_data: List[Dict]) -> str:
        """处理知识数据，提取有效内容"""
        try:
            if not knowledge_data:
                return ""

            content_parts = []
            limit = self._get_intelligent_limit("knowledge_items")

            if limit is None or not isinstance(limit, int) or limit <= 0:
                limit = 5  # 默认限制

            limited_knowledge = knowledge_data[:limit] if limit <= len(knowledge_data) else knowledge_data

            for i, knowledge in enumerate(limited_knowledge):
                if isinstance(knowledge, dict):
                    content = (knowledge.get('content') or
                             knowledge.get('text') or
                             knowledge.get('summary') or
                             knowledge.get('description', ''))

                    if content and content.strip():
                        max_length = self._get_intelligent_limit("max_knowledge_content_length") or 200
                        if len(content) > max_length:
                            content = content[:max_length] + "..."
                        content_parts.append(f"- {content}")
                    elif knowledge.get('title'):
                        content_parts.append(f"- {knowledge.get('title')}")

            return "\n".join(content_parts) if content_parts else ""

        except Exception as e:
            logger.warning(f"处理知识数据失败: {e}")
            return ""

    def _process_reasoning_data(self, reasoning_data: Dict) -> str:
        """处理推理数据，提取有效内容"""
        try:
            if not reasoning_data:
                return ""

            content_parts = []
            limit = self._get_intelligent_limit("reasoning_steps")

            if isinstance(reasoning_data, dict):
                if 'reasoning_steps' in reasoning_data and reasoning_data['reasoning_steps']:
                    steps = reasoning_data['reasoning_steps']
                    limited_steps = steps[:limit] if limit <= len(steps) else steps
                    for step in limited_steps:
                        if isinstance(step, str) and step.strip():
                            content_parts.append(f"- {step}")
                        elif isinstance(step, dict):
                            step_text = step.get('text') or step.get('content') or str(step)
                            if step_text and step_text.strip():
                                content_parts.append(f"- {step_text}")

                elif 'reasoning' in reasoning_data:
                    reasoning_text = reasoning_data['reasoning']
                    if isinstance(reasoning_text, str) and reasoning_text.strip():
                        content_parts.append(f"- {reasoning_text}")

                elif 'analysis' in reasoning_data:
                    analysis_text = reasoning_data['analysis']
                    if isinstance(analysis_text, str) and analysis_text.strip():
                        content_parts.append(f"- {analysis_text}")

            return "\n".join(content_parts) if content_parts else ""

        except Exception as e:
            logger.warning(f"处理推理数据失败: {e}")
            return ""

    def _generate_intelligent_fallback_answer(self, query: str) -> str:
        """生成智能回退答案"""
        try:
            query_lower = query.lower()

            if any(word in query_lower for word in ['what', 'who', 'when', 'where', 'why', 'how']):
                if 'capital' in query_lower:
                    return "根据地理知识，每个国家都有其首都城市。"
                elif 'wrote' in query_lower or 'author' in query_lower:
                    return "根据文学知识，每部作品都有其创作者。"
                elif 'chemical' in query_lower or 'symbol' in query_lower:
                    return "根据化学知识，每种元素都有其符号。"
                elif 'year' in query_lower or 'when' in query_lower:
                    return "根据历史知识，每个事件都有其发生时间。"
                elif 'planet' in query_lower or 'largest' in query_lower:
                    return "根据天文知识，太阳系中有多个行星。"
                else:
                    return f"这是一个疑问句查询，正在分析：{query[:50]}..."

            elif any(word in query_lower for word in ['calculate', 'compute', 'solve', 'find']):
                return "这是一个计算类查询，需要数值分析。"

            else:
                return f"正在处理查询：{query[:50]}..."

        except Exception as e:
            logger.warning(f"生成智能回退答案失败: {e}")
            return "正在处理您的查询..."

    def _generate_basic_answer(self, query: str) -> str:
        """生成基础答案"""
        try:
            query_lower = query.lower()

            if 'capital' in query_lower:
                return "根据地理知识，每个国家都有其首都城市。"
            elif 'wrote' in query_lower or 'author' in query_lower:
                return "根据文学知识，每部作品都有其创作者。"
            elif 'chemical' in query_lower or 'symbol' in query_lower:
                return "根据化学知识，每种元素都有其符号。"
            elif 'year' in query_lower or 'when' in query_lower:
                return "根据历史知识，每个事件都有其发生时间。"
            elif 'planet' in query_lower or 'largest' in query_lower:
                return "根据天文知识，太阳系中有多个行星。"
            else:
                return "正在分析您的查询，请稍候..."

        except Exception as e:
            logger.warning(f"生成基础答案失败: {e}")
            return "正在处理您的查询..."

    def _generate_fallback_answer(self, query: str, error_msg: str = "") -> str:
        """生成最终回退答案"""
        try:
            base_answer = f"基于查询'{query}'的回答：\n\n"

            if error_msg:
                base_answer += f"处理过程中遇到问题：{error_msg}\n\n"

            base_answer += "基础信息：\n"
            base_answer += "- 这是一个有效的查询\n"
            base_answer += "- 系统正在处理中\n"
            base_answer += "- 请稍候获取完整答案\n"

            return base_answer

        except Exception as e:
            logger.error(f"生成最终回退答案失败: {e}")
            return f"基于查询'{query}'的回答：\n\n系统正在处理您的查询，请稍候..."
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """处理查询 - 同步接口，保持功能完整性"""
        try:
            # 使用线程池执行异步方法
            import concurrent.futures
            import asyncio
            
            # 在同步上下文中运行异步方法
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.execute(context or {}))
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"同步查询处理失败: {e}")
            return AgentResult(
                success=False,
                data={"content": f"查询处理失败: {str(e)}"},
                confidence=0.0,
                processing_time=0.0,
                error=str(e)
            )
    
    def _calculate_intelligent_confidence(self, confidence_type: str) -> float:
        """计算智能置信度"""
        try:
            # 尝试使用统一智能评分器
            if self.unified_config:
                try:
                    scorer = self.unified_config.get_config_value("ai_algorithms", "intelligent_scorer", None)
                    if scorer and hasattr(scorer, 'get_intelligent_confidence'):
                        return scorer.get_intelligent_confidence(confidence_type)
                except (ImportError, AttributeError, KeyError):
                    pass
            
            # 回退到默认计算
            return self._calculate_default_confidence(confidence_type)
            
        except Exception as e:
            logger.warning(f"智能置信度计算失败: {e}")
            return self._calculate_default_confidence(confidence_type)
    
    def _validate_answer_quality(self, answer: str) -> Dict[str, Any]:
        """验证答案质量"""
        try:
            quality_metrics = {
                "length": len(answer),
                "has_content": bool(answer.strip()),
                "has_structure": any(marker in answer for marker in ["：", ":", "\n", "-", "1.", "2."]),
                "completeness": 0.0
            }
            
            # 计算完整性
            if quality_metrics["has_content"]:
                if quality_metrics["length"] > 100:
                    quality_metrics["completeness"] = 0.8
                elif quality_metrics["length"] > 50:
                    quality_metrics["completeness"] = 0.6
                else:
                    quality_metrics["completeness"] = 0.4
            
            return quality_metrics
            
        except Exception as e:
            logger.warning(f"答案质量验证失败: {e}")
            return {"length": 0, "has_content": False, "has_structure": False, "completeness": 0.0}
    
    def _enhance_answer_structure(self, answer: str) -> str:
        """增强答案结构"""
        try:
            if not answer or not answer.strip():
                return answer
            
            # 确保答案有适当的结构
            lines = answer.split('\n')
            enhanced_lines = []
            
            for line in lines:
                line = line.strip()
                if line:
                    # 如果行以数字或破折号开头，保持原样
                    if re.match(r'^[\d\-\.]', line):
                        enhanced_lines.append(line)
                    # 如果是标题行（包含冒号）
                    elif '：' in line or ':' in line:
                        enhanced_lines.append(line)
                    # 其他内容行添加适当的前缀
                    elif line and not line.startswith(('查询', '回答', '分析')):
                        enhanced_lines.append(f"  {line}")
                    else:
                        enhanced_lines.append(line)
            
            return '\n'.join(enhanced_lines)
            
        except Exception as e:
            logger.warning(f"答案结构增强失败: {e}")
            return answer
    
    def _generate_metadata(self, query: str, answer: str, processing_time: float) -> Dict[str, Any]:
        """生成元数据"""
        try:
            metadata = {
                "query_length": len(query),
                "answer_length": len(answer),
                "processing_time": processing_time,
                "generation_method": "enhanced_answer_generation",
                "timestamp": datetime.now().isoformat(),
                "agent_version": "1.0.0"
            }
            
            # 添加质量指标
            quality = self._validate_answer_quality(answer)
            metadata.update(quality)
            
            return metadata
            
        except Exception as e:
            logger.warning(f"元数据生成失败: {e}")
            return {
                "query_length": len(query),
                "answer_length": len(answer),
                "processing_time": processing_time,
                "generation_method": "enhanced_answer_generation",
                "timestamp": datetime.now().isoformat()
            }
    
    def _log_generation_event(self, query: str, answer: str, success: bool, processing_time: float):
        """记录生成事件"""
        try:
            event_data = {
                "query": query[:100],  # 限制长度
                "answer_length": len(answer),
                "success": success,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }
            
            if success:
                logger.info(f"答案生成成功: {event_data}")
            else:
                logger.warning(f"答案生成失败: {event_data}")
                
        except Exception as e:
            logger.error(f"事件记录失败: {e}")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        try:
            return {
                "name": getattr(self, 'name', 'EnhancedAnswerGenerationAgent'),
                "is_executing": self.is_executing,
                "unified_config_available": self.unified_config is not None,
                "config_loaded": hasattr(self, 'config') and self.config is not None,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取智能体状态失败: {e}")
            return {
                "name": getattr(self, 'name', 'EnhancedAnswerGenerationAgent'),
                "is_executing": False,
                "unified_config_available": False,
                "config_loaded": False,
                "error": str(e)
            }
    
    # ==================== 新增方法实现 ====================
    
    def _analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """分析查询复杂度和类型 - 🚀 重构：使用统一复杂度服务（LLM判断）"""
        try:
            from src.utils.unified_complexity_model_service import get_unified_complexity_model_service
            complexity_service = get_unified_complexity_model_service()
            complexity_result = complexity_service.assess_complexity(
                query=query,
                query_type=None,
                evidence_count=0,
                use_cache=True
            )
            
            # 基础特征提取（用于查询类型判断）
            word_count = len(query.split())
            has_question_words = any(word in query.lower() for word in ['what', 'how', 'why', 'when', 'where', 'who', 'which', '什么', '如何', '为什么', '何时', '哪里', '谁', '哪个'])
            has_comparison_words = any(word in query.lower() for word in ['vs', 'versus', 'compare', 'difference', 'similar', '对比', '比较', '差异', '相似'])
            has_explanation_words = any(word in query.lower() for word in ['explain', 'describe', 'tell me about', '解释', '描述', '告诉我'])
            
            # 确定查询类型
            if has_comparison_words:
                query_type = 'comparative'
            elif has_explanation_words:
                query_type = 'explanatory'
            elif has_question_words and word_count > 10:
                query_type = 'analytical'
            elif has_question_words:
                query_type = 'factual'
            else:
                query_type = 'general'
            
            # 使用统一服务的复杂度评分（转换为0-1）
            complexity = complexity_result.score / 10.0
            
            return {
                'type': query_type,
                'complexity': complexity,
                'complexity_level': complexity_result.level.value,  # 'simple', 'medium', 'complex'
                'word_count': word_count,
                'has_question_words': has_question_words,
                'has_comparison_words': has_comparison_words,
                'has_explanation_words': has_explanation_words
            }
            
        except Exception as e:
            logger.error(f"查询分析失败: {e}")
            return {'type': 'general', 'complexity': 0.5, 'word_count': 0}
    
    async def _generate_factual_answer(self, query: str, knowledge_data: List[Dict[str, Any]], reasoning_data: Dict[str, Any]) -> str:
        """生成事实性答案 - 基于真正推理的简洁答案"""
        try:
            # 使用真正的推理引擎
            from src.core.reasoning import RealReasoningEngine
            
            reasoning_engine = RealReasoningEngine()
            
            # 准备推理上下文
            context = {
                'knowledge': knowledge_data,
                'reasoning_data': reasoning_data,
                'query': query
            }
            
            # 执行推理 - 在异步上下文中直接await
            reasoning_result = await reasoning_engine.reason(query, context)
            
            if reasoning_result.success:
                return reasoning_result.final_answer
            else:
                # 回退到简单答案提取
                if knowledge_data:
                    best_fact = max(knowledge_data, key=lambda x: x.get('confidence', 0.0))
                    content = best_fact.get('content', '')
                    
                    if content:
                        # 直接返回核心答案，不添加模板
                        lines = content.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith(('分析', '推理', '基于', '支持')):
                                return line
                        return content
                
                return "需要更多信息来提供准确答案"
            
        except Exception as e:
            logger.error(f"事实性答案生成失败: {e}")
            # 回退到简单答案
            if knowledge_data:
                best_fact = max(knowledge_data, key=lambda x: x.get('confidence', 0.0))
                content = best_fact.get('content', '')
                if content:
                    return content
            return "无法生成答案"
    
    def _synthesize_primary_answer(self, query: str, relevant_facts: List[Dict[str, Any]]) -> str:
        """综合主要答案"""
        try:
            if not relevant_facts:
                return "暂无足够信息提供准确答案。"
            
            # 选择置信度最高的事实作为主要答案
            best_fact = max(relevant_facts, key=lambda x: x.get('confidence', 0.0))
            content = best_fact.get('content', '')
            
            # 如果内容太短，尝试综合多个事实
            if len(content) < 50 and len(relevant_facts) > 1:
                combined_content = []
                for fact in relevant_facts[:2]:  # 取前两个最相关的事实
                    fact_content = fact.get('content', '')
                    if fact_content and fact_content not in combined_content:
                        combined_content.append(fact_content)
                
                if combined_content:
                    content = " ".join(combined_content)
            
            return content if content else "这是一个需要进一步研究的问题。"
            
        except Exception as e:
            logger.error(f"主要答案综合失败: {e}")
            return "答案综合过程中出现错误。"
    
    async def _generate_analytical_answer(self, query: str, knowledge_data: List[Dict[str, Any]], reasoning_data: Dict[str, Any]) -> str:
        """生成分析性答案 - 基于真正推理的简洁答案"""
        try:
            # 使用真正的推理引擎
            from src.core.reasoning import RealReasoningEngine
            
            reasoning_engine = RealReasoningEngine()
            
            # 准备推理上下文
            context = {
                'knowledge': knowledge_data,
                'reasoning_data': reasoning_data,
                'query': query
            }
            
            # 执行推理 - 在异步上下文中直接await
            reasoning_result = await reasoning_engine.reason(query, context)
            
            if reasoning_result.success:
                return reasoning_result.final_answer
            else:
                # 回退到简单答案提取
                if knowledge_data:
                    best_knowledge = max(knowledge_data, key=lambda x: x.get('confidence', 0.0))
                    content = best_knowledge.get('content', '')
                    
                    if content:
                        # 直接返回核心答案，不添加模板
                        lines = content.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith(('分析', '推理', '基于', '支持')):
                                return line
                        return content
                
                return "需要更多信息来提供准确答案"
            
        except Exception as e:
            logger.error(f"分析性答案生成失败: {e}")
            return f"分析性答案生成失败: {str(e)}"
    
    def _generate_comparative_answer(self, query: str, knowledge_data: List[Dict[str, Any]], reasoning_data: Dict[str, Any]) -> str:
        """生成比较性答案 - 简洁直接的答案"""
        try:
            if not knowledge_data:
                return f"关于'{query}'的答案：需要更多信息来提供准确答案。"
            
            # 生成简洁答案
            if knowledge_data:
                # 选择置信度最高的知识作为主要答案
                best_knowledge = max(knowledge_data, key=lambda x: x.get('confidence', 0.0))
                content = best_knowledge.get('content', '')
                
                # 提取核心答案
                if content:
                    # 如果是回退知识，直接使用
                    if best_knowledge.get('source') == 'fallback':
                        return content
                    
                    # 提取第一行作为核心答案
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith(('分析', '推理', '基于', '支持')):
                            return line
                    
                    return content
                
                return f"关于'{query}'的答案：{content}"
            else:
                return f"关于'{query}'的答案：需要更多信息来提供准确答案。"
            
        except Exception as e:
            logger.error(f"比较性答案生成失败: {e}")
            return f"答案生成失败: {str(e)}"
    
    def _generate_explanatory_answer(self, query: str, knowledge_data: List[Dict[str, Any]], reasoning_data: Dict[str, Any]) -> str:
        """生成解释性答案 - 简洁直接的答案"""
        try:
            if not knowledge_data:
                return f"关于'{query}'的答案：需要更多信息来提供准确答案。"
            
            # 生成简洁答案
            if knowledge_data:
                # 选择置信度最高的知识作为主要答案
                best_knowledge = max(knowledge_data, key=lambda x: x.get('confidence', 0.0))
                content = best_knowledge.get('content', '')
                
                # 提取核心答案
                if content:
                    # 如果是回退知识，直接使用
                    if best_knowledge.get('source') == 'fallback':
                        return content
                    
                    # 提取第一行作为核心答案
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith(('分析', '推理', '基于', '支持')):
                            return line
                    
                    return content
                
                return f"关于'{query}'的答案：{content}"
            else:
                return f"关于'{query}'的答案：需要更多信息来提供准确答案。"
            
        except Exception as e:
            logger.error(f"解释性答案生成失败: {e}")
            return f"解释性答案生成失败: {str(e)}"
    
    async def _generate_general_answer(self, query: str, knowledge_data: List[Dict[str, Any]], reasoning_data: Dict[str, Any]) -> str:
        """生成通用答案 - 增强版本（更智能的答案提取）"""
        try:
            # 🚀 优化：增强答案提取逻辑 - 多层备选机制
            
            def normalize_answer(text: str) -> str:
                """规范化答案文本"""
                if not text:
                    return ""
                text = text.strip()
                # 移除多余的空格
                text = ' '.join(text.split())
                # 移除引号
                text = text.strip('"').strip("'")
                return text
            
            def is_good_answer(answer: str) -> bool:
                """检查答案质量"""
                if not answer or len(answer) < 2:
                    return False
                # 过滤掉"无法确定"等无用答案
                bad_keywords = ['无法确定', '不确定', '需要更多', '缺乏', 'cannot determine', 'unknown', 
                               'please provide', '请问', '需要', 'based on my analysis']
                answer_lower = answer.lower()
                return not any(keyword in answer_lower for keyword in bad_keywords)
            
            def extract_short_answers(text: str) -> List[str]:
                """提取简短答案（人名、地名、数字等）"""
                short_answers = []
                # 尝试提取长度为2-50的短语
                for word_group in text.split(','):
                    cleaned = word_group.strip()
                    if 2 <= len(cleaned) <= 50 and cleaned[0].isalnum():
                        short_answers.append(cleaned)
                return short_answers
            
            def try_extract_specific_answer(text: str, query_lower: str) -> Optional[str]:
                """尝试从文本中提取特定答案"""
                # 提取可能的答案短语
                sentences = text.split('.')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if 5 <= len(sentence) <= 300:
                        # 检查是否包含查询关键词
                        sentence_lower = sentence.lower()
                        query_words = set(query_lower.split())
                        sentence_words = set(sentence_lower.split())
                        overlap = len(query_words & sentence_words)
                        if overlap > 0:
                            return sentence
                return None
            
            # 1. 优先从knowledge中提取答案（增强版 - 多层备选）
            candidate_answers = []
            query_lower = query.lower()
            
            if knowledge_data:
                for knowledge in knowledge_data:
                    if not isinstance(knowledge, dict):
                        continue
                        
                    content = knowledge.get('content', '')
                    confidence = knowledge.get('confidence', 0.5)
                    
                    if not content or len(content.strip()) < 3:
                        continue
                    
                    # 策略1：尝试提取特定答案（基于查询关键词匹配）
                    specific_answer = try_extract_specific_answer(content, query_lower)
                    if specific_answer:
                        cleaned = normalize_answer(specific_answer)
                        if cleaned and is_good_answer(cleaned):
                            candidate_answers.append({
                                'text': cleaned,
                                'confidence': confidence * 1.2,  # 提高匹配查询的答案的置信度
                                'length': len(cleaned)
                            })
                    
                    # 策略2：提取简短答案
                    short_answers = extract_short_answers(content)
                    for short in short_answers:
                        cleaned = normalize_answer(short)
                        if cleaned and is_good_answer(cleaned):
                            candidate_answers.append({
                                'text': cleaned,
                                'confidence': confidence,
                                'length': len(cleaned)
                            })
                    
                    # 策略3：按行提取答案
                    lines = content.split('\n')
                    for line in lines:
                        cleaned = normalize_answer(line)
                        if cleaned and is_good_answer(cleaned) and 5 <= len(cleaned) <= 500:
                            candidate_answers.append({
                                'text': cleaned,
                                'confidence': confidence,
                                'length': len(cleaned)
                            })
            
            # 2. 从candidate_answers中选择最佳答案
            if candidate_answers:
                # 按置信度和长度综合排序
                def score_candidate(candidate):
                    confidence = candidate['confidence']
                    length = candidate['length']
                    # 偏好中等长度的答案（10-200字符）
                    if 10 <= length <= 200:
                        length_score = 1.0
                    elif length < 10:
                        length_score = length / 10.0
                    else:
                        length_score = max(0.5, 1.0 - (length - 200) / 300)
                    return confidence * 0.7 + length_score * 0.3
                
                best = max(candidate_answers, key=score_candidate)
                return best['text'][:250]  # 限制最终长度
            
            # 3. 最终回退策略 - 尝试从原始knowledge中提取任何可用信息
            if knowledge_data:
                for knowledge in knowledge_data:
                    if not isinstance(knowledge, dict):
                        continue
                    content = knowledge.get('content', '')
                    if content and len(content) > 10:
                        # 策略A：提取第一个句子
                        sentences = content.split('.')
                        for sent in sentences:
                            sent = sent.strip()
                            if len(sent) > 5 and len(sent) < 300:
                                # 避免返回问题本身
                                if '?' not in sent and '？' not in sent:
                                    return sent[:200]
                        
                        # 策略B：提取第一个短语
                        phrases = content.split(',')
                        for phrase in phrases:
                            phrase = phrase.strip()
                            if 5 <= len(phrase) <= 100 and phrase[0].isalnum():
                                # 避免返回问题本身
                                if '?' not in phrase and '？' not in phrase:
                                    return phrase[:150]
            
            # 4. 如果knowledge存在但格式不对，尝试直接返回（避免"无法确定"）
            if knowledge_data:
                for knowledge in knowledge_data:
                    if isinstance(knowledge, dict):
                        content = knowledge.get('content', '')
                        if content and len(content) > 20:
                            # 提取前100字符
                            preview = content[:100].strip()
                            if preview and not ('无法确定' in preview or '不确定' in preview):
                                return preview
            
            # 5. 绝对最后的回退 - 给出通用提示但避免"无法确定"
            return "基于当前信息，无法提供精确答案"
            
        except Exception as e:
            logger.error(f"通用答案生成失败: {e}")
            return "缺乏足够信息来准确回答这个问题"
    
    def _extract_relevant_facts(self, query: str, knowledge_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取相关事实"""
        try:
            relevant_facts = []
            query_words = set(query.lower().split())
            
            for knowledge in knowledge_data:
                if isinstance(knowledge, dict):
                    content = knowledge.get('content', '')
                    content_words = set(content.lower().split())
                    
                    # 计算相关性
                    overlap = len(query_words & content_words)
                    if overlap > 0:
                        confidence = overlap / len(query_words)
                        relevant_facts.append({
                            'content': content,
                            'source': knowledge.get('source', '未知来源'),
                            'confidence': confidence
                        })
            
            # 按置信度排序
            relevant_facts.sort(key=lambda x: x['confidence'], reverse=True)
            return relevant_facts[:5]  # 返回前5个最相关的事实
            
        except Exception as e:
            logger.error(f"提取相关事实失败: {e}")
            return []
    
    def _extract_analysis_points(self, query: str, knowledge_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取分析要点"""
        try:
            analysis_points = []
            
            for i, knowledge in enumerate(knowledge_data, 1):
                if isinstance(knowledge, dict):
                    content = knowledge.get('content', '')
                    source = knowledge.get('source', '未知来源')
                    
                    analysis_points.append({
                        'title': f"分析要点 {i}",
                        'content': content,
                        'source': source
                    })
            
            return analysis_points
            
        except Exception as e:
            logger.error(f"提取分析要点失败: {e}")
            return []
    
    def _extract_comparison_objects(self, query: str, knowledge_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取比较对象"""
        try:
            comparison_objects = []
            
            for i, knowledge in enumerate(knowledge_data, 1):
                if isinstance(knowledge, dict):
                    content = knowledge.get('content', '')
                    source = knowledge.get('source', '未知来源')
                    
                    comparison_objects.append({
                        'name': f"对象 {i}",
                        'features': content,
                        'advantages': f"基于 {source} 的优势",
                        'disadvantages': f"基于 {source} 的劣势"
                    })
            
            return comparison_objects
            
        except Exception as e:
            logger.error(f"提取比较对象失败: {e}")
            return []
    
    def _extract_explanation_points(self, query: str, knowledge_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取解释要点"""
        try:
            explanation_points = []
            
            for i, knowledge in enumerate(knowledge_data, 1):
                if isinstance(knowledge, dict):
                    content = knowledge.get('content', '')
                    source = knowledge.get('source', '未知来源')
                    
                    explanation_points.append({
                        'title': f"解释要点 {i}",
                        'content': content,
                        'source': source
                    })
            
            return explanation_points
            
        except Exception as e:
            logger.error(f"提取解释要点失败: {e}")
            return []
    
    def _generate_analytical_conclusion(self, analysis_points: List[Dict[str, Any]], reasoning_data: Dict[str, Any]) -> str:
        """生成分析结论 - 简洁直接的结论"""
        try:
            if not analysis_points:
                return "需要更多信息来提供准确答案"
            
            # 提取第一个分析要点的核心内容作为结论
            first_point = analysis_points[0]
            content = first_point.get('content', '')
            
            if content:
                # 提取第一行作为核心结论
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith(('分析', '推理', '基于', '支持')):
                        return line
                
                return content
            
            return "需要更多信息来提供准确答案"
            
        except Exception as e:
            logger.error(f"生成分析结论失败: {e}")
            return "无法生成分析结论"
    
    def _generate_comparison_summary(self, comparison_objects: List[Dict[str, Any]]) -> str:
        """生成比较总结"""
        try:
            if not comparison_objects:
                return "无法进行比较总结"
            
            # 简单的比较总结
            summary = f"基于 {len(comparison_objects)} 个对象的比较"
            summary += "，各对象都有其独特的特点和优劣势。"
            
            return summary
            
        except Exception as e:
            logger.error(f"生成比较总结失败: {e}")
            return "无法生成比较总结"
