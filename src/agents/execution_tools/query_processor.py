#!/usr/bin/env python3
"""
查询处理器 - 处理用户查询的核心工具
"""

import os
import logging
import time
import json
import numpy as np
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """查询类型枚举"""
    SIMPLE = "simple"
    COMPLEX = "complex"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    RESEARCH = "research"

class QueryPriority(Enum):
    """查询优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class QueryContext:
    """查询上下文数据类"""
    query_id: str
    query_text: str
    query_type: QueryType
    priority: QueryPriority
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[float] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = time.time()

@dataclass
class ProcessingResult:
    """处理结果数据类"""
    query_id: str
    success: bool
    result: Any
    confidence: float
    processing_time: float
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class QueryProcessor:
    """查询处理器"""
    
    def __init__(self):
        """初始化查询处理器"""
        self.processing_history = []
        self.performance_metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "average_processing_time": 0.0,
            "query_type_distribution": {}
        }
        self.initialized = True
        logger.info("查询处理器初始化完成")
    
    def process_query(self, query_context: QueryContext) -> ProcessingResult:
        """处理查询 - AI增强版"""
        try:
            # 验证查询上下文
            if not self._validate_query_context(query_context):
                return self._create_error_result("Invalid query context")
            
            start_time = time.time()
            
            # 分析查询
            query_analysis = self._analyze_query(query_context)
            
            # 选择处理策略
            strategy = self._select_processing_strategy(query_analysis)
            
            # 查询预处理
            processed_query = self._preprocess_query(query_context)
            
            # 执行查询处理
            result = self._execute_query_processing(processed_query, strategy)
            
            # 后处理结果
            final_result = self._postprocess_result(result, query_context, query_analysis)
            
            # 更新性能指标
            self._update_performance_metrics(start_time, True)
            
            # 记录处理历史
            self._record_processing_history(query_context, final_result)
            
            return final_result
            
        except Exception as e:
            logger.error(f"查询处理失败: {e}")
            self._update_performance_metrics(time.time(), False)
            return self._create_error_result(f"Query processing failed: {e}")
    
    def _validate_query_context(self, query_context: QueryContext) -> bool:
        """验证查询上下文"""
        if not isinstance(query_context, QueryContext):
            return False
        
        if not query_context.query_text or not query_context.query_text.strip():
            return False
        
        return True
    
    def _execute_query_processing(self, processed_query: QueryContext, strategy: str) -> ProcessingResult:
        """执行查询处理"""
        try:
            # 根据策略执行处理
            if strategy == "simple":
                return self._execute_simple_processing(processed_query)
            elif strategy == "complex":
                return self._execute_complex_processing(processed_query)
            elif strategy == "ai_enhanced":
                return self._execute_ai_enhanced_processing(processed_query)
            else:
                return self._execute_default_processing(processed_query)
                
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            raise e
    
    def _execute_simple_processing(self, query_context: QueryContext) -> ProcessingResult:
        """执行简单处理"""
        return ProcessingResult(
            query_id=query_context.query_id,
            success=True,
            result=f"Simple processing result for: {query_context.query_text}",
            confidence=0.8,
            processing_time=0.1,
            metadata={'strategy': 'simple', 'timestamp': time.time()}
        )
    
    def _execute_complex_processing(self, query_context: QueryContext) -> ProcessingResult:
        """执行复杂处理"""
        return ProcessingResult(
            query_id=query_context.query_id,
            success=True,
            result=f"Complex processing result for: {query_context.query_text}",
            confidence=0.9,
            processing_time=0.5,
            metadata={'strategy': 'complex', 'timestamp': time.time()}
        )
    
    def _execute_ai_enhanced_processing(self, query_context: QueryContext) -> ProcessingResult:
        """执行AI增强处理"""
        return ProcessingResult(
            query_id=query_context.query_id,
            success=True,
            result=f"AI-enhanced processing result for: {query_context.query_text}",
            confidence=0.95,
            processing_time=1.0,
            metadata={'strategy': 'ai_enhanced', 'timestamp': time.time()}
        )
    
    def _execute_default_processing(self, query_context: QueryContext) -> ProcessingResult:
        """执行默认处理"""
        return ProcessingResult(
            query_id=query_context.query_id,
            success=True,
            result=f"Default processing result for: {query_context.query_text}",
            confidence=0.7,
            processing_time=0.2,
            metadata={'strategy': 'default', 'timestamp': time.time()}
        )
    
    def _postprocess_result(self, result: ProcessingResult, query_context: QueryContext, analysis: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """后处理结果"""
        try:
            # 添加查询上下文信息
            if not result.metadata:
                result.metadata = {}
            
            result.metadata.update({
                'original_query': query_context.query_text,
                'user_id': query_context.user_id,
                'postprocessed_at': time.time()
            })
            
            # 添加分析信息
            if analysis:
                result.metadata['analysis'] = analysis
            
            return result
            
        except Exception as e:
            logger.warning(f"结果后处理失败: {e}")
            return result
    
    def _analyze_query(self, query_context: QueryContext) -> Dict[str, Any]:
        """分析查询"""
        try:
            query_text = query_context.query_text
            query_length = len(query_text)
            word_count = len(query_text.split())
            
            # 分析查询复杂度
            complexity_score = self._calculate_complexity_score(query_text)
            
            # 分析查询类型
            query_type = self._classify_query_type(query_text)
            
            # 分析关键词
            keywords = self._extract_keywords(query_text)
            
            return {
                "query_length": query_length,
                "word_count": word_count,
                "complexity_score": complexity_score,
                "query_type": query_type,
                "keywords": keywords,
                "analysis_timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"查询分析失败: {e}")
            return {
                "query_length": 0,
                "word_count": 0,
                "complexity_score": 0.5,
                "query_type": "unknown",
                "keywords": [],
                "error": str(e)
            }
    
    def _calculate_complexity_score(self, query_text: str) -> float:
        """计算查询复杂度分数"""
        try:
            score = 0.0
            
            # 基于长度
            length_score = min(1.0, len(query_text) / 100.0)
            score += length_score * 0.3
            
            # 基于词汇数量
            word_count = len(query_text.split())
            word_score = min(1.0, word_count / 20.0)
            score += word_score * 0.3
            
            # 基于特殊字符
            special_chars = sum(1 for c in query_text if c in "?!@#$%^&*()[]{}|\\:;\"'<>?/.,")
            special_score = min(1.0, special_chars / 10.0)
            score += special_score * 0.2
            
            # 基于问号数量
            question_marks = query_text.count('?')
            question_score = min(1.0, question_marks / 3.0)
            score += question_score * 0.2
            
            return min(1.0, score)
            
        except Exception as e:
            logger.warning(f"复杂度计算失败: {e}")
            return 0.5
    
    def _classify_query_type(self, query_text: str) -> str:
        """分类查询类型 - 🚀 重构：使用统一分类服务（LLM判断）"""
        try:
            # 🚀 使用统一分类服务（优先使用LLM判断）
            from src.utils.unified_classification_service import get_unified_classification_service
            
            # 获取统一分类服务（需要LLM集成）
            # 如果不可用，使用fallback
            try:
                classification_service = get_unified_classification_service()
                
                # 定义有效的查询类型（与QueryType枚举对应）
                valid_types = [
                    'simple', 'complex', 'analytical', 'creative', 
                    'technical', 'research', 'normal', 'question'
                ]
                
                # 使用统一分类服务进行分类
                query_type = classification_service.classify(
                    query=query_text,
                    classification_type="query_type",
                    valid_types=valid_types,
                    template_name="query_type_classification",
                    default_type="normal",
                    rules_fallback=self._classify_query_type_fallback
                )
                
                return query_type
                
            except Exception as e:
                logger.warning(f"⚠️ 使用统一分类服务失败: {e}，使用fallback")
                return self._classify_query_type_fallback(query_text)
                
        except Exception as e:
            logger.warning(f"查询类型分类失败: {e}")
            return "unknown"
    
    def _classify_query_type_fallback(self, query_text: str) -> str:
        """Fallback查询类型分类（仅在统一服务不可用时使用）"""
        try:
            query_lower = query_text.lower()
            
            # 简单规则判断（作为fallback）
            # 检查是否有问号
            if "?" in query_text or "？" in query_text:
                return "question"
            
            # 根据词数判断简单/复杂
            word_count = len(query_text.split())
            if word_count <= 5:
                return "simple"
            elif word_count > 15:
                return "complex"
            
            return "normal"
            
        except Exception as e:
            logger.warning(f"Fallback查询类型分类失败: {e}")
            return "unknown"
    
    def _extract_keywords(self, query_text: str) -> List[str]:
        """提取关键词"""
        try:
            # 简单的关键词提取
            words = query_text.lower().split()
            
            # 过滤停用词
            stop_words = {"的", "是", "在", "有", "和", "与", "或", "但", "然而", "因为", "所以", "the", "is", "are", "was", "were", "a", "an", "and", "or", "but"}
            keywords = [word for word in words if word not in stop_words and len(word) > 2]
            
            # 限制关键词数量
            return keywords[:10]
            
        except Exception as e:
            logger.warning(f"关键词提取失败: {e}")
            return []
    
    def _select_processing_strategy(self, analysis: Dict[str, Any]) -> str:
        """选择处理策略"""
        try:
            complexity_score = analysis.get("complexity_score", 0.5)
            query_type = analysis.get("query_type", "unknown")
            
            # 基于复杂度选择策略
            if complexity_score > 0.8:
                return "ai_enhanced"
            elif complexity_score > 0.6:
                return "complex"
            elif query_type in ["technical", "research"]:
                return "ai_enhanced"
            elif query_type == "simple":
                return "simple"
            else:
                return "default"
                
        except Exception as e:
            logger.warning(f"策略选择失败: {e}")
            return "default"
    
    def _preprocess_query(self, query_context: QueryContext) -> QueryContext:
        """预处理查询"""
        try:
            # 清理查询文本
            cleaned_query = query_context.query_text.strip()
            
            # 标准化格式
            normalized_query = self._normalize_query(cleaned_query)
            
            # 创建新的查询上下文
            processed_context = QueryContext(
                query_id=query_context.query_id,
                query_text=normalized_query,
                query_type=query_context.query_type,
                priority=query_context.priority,
                user_id=query_context.user_id,
                session_id=query_context.session_id,
                metadata=query_context.metadata.copy() if query_context.metadata else {},
                created_at=query_context.created_at
            )
            
            # 添加预处理信息
            if processed_context.metadata is not None:
                processed_context.metadata["preprocessed"] = True
                processed_context.metadata["preprocessing_time"] = time.time()
            
            return processed_context
            
        except Exception as e:
            logger.warning(f"查询预处理失败: {e}")
            return query_context
    
    def _normalize_query(self, query_text: str) -> str:
        """标准化查询文本"""
        try:
            # 移除多余空格
            normalized = " ".join(query_text.split())
            
            # 统一标点符号
            normalized = normalized.replace("？", "?").replace("！", "!")
            
            # 确保以问号结尾（如果是疑问句）
            if not normalized.endswith(("?", "!", ".")):
                if any(word in normalized.lower() for word in ["什么", "如何", "为什么", "哪里", "什么时候", "who", "what", "how", "why", "where", "when"]):
                    normalized += "?"
            
            return normalized
            
        except Exception as e:
            logger.warning(f"查询标准化失败: {e}")
            return query_text
    
    def _create_error_result(self, error_message: str) -> ProcessingResult:
        """创建错误结果"""
        return ProcessingResult(
            query_id="error",
            success=False,
            result=error_message,
            confidence=0.0,
            processing_time=0.0,
            metadata={"error": True, "timestamp": time.time()}
        )
    
    def _update_performance_metrics(self, start_time: float, success: bool):
        """更新性能指标"""
        try:
            processing_time = time.time() - start_time
            
            self.performance_metrics["total_queries"] += 1
            
            if success:
                self.performance_metrics["successful_queries"] += 1
            else:
                self.performance_metrics["failed_queries"] += 1
            
            # 更新平均处理时间
            total_queries = self.performance_metrics["total_queries"]
            current_avg = self.performance_metrics["average_processing_time"]
            new_avg = (current_avg * (total_queries - 1) + processing_time) / total_queries
            self.performance_metrics["average_processing_time"] = new_avg
            
        except Exception as e:
            logger.warning(f"性能指标更新失败: {e}")
    
    def _record_processing_history(self, query_context: QueryContext, result: ProcessingResult):
        """记录处理历史"""
        try:
            history_entry = {
                "query_id": query_context.query_id,
                "query_text": query_context.query_text[:100],  # 限制长度
                "query_type": query_context.query_type.value if hasattr(query_context.query_type, 'value') else str(query_context.query_type),
                "success": result.success,
                "processing_time": result.processing_time,
                "confidence": result.confidence,
                "timestamp": time.time()
            }
            
            self.processing_history.append(history_entry)
            
            # 限制历史记录数量
            if len(self.processing_history) > 1000:
                self.processing_history = self.processing_history[-500:]
                
        except Exception as e:
            logger.warning(f"处理历史记录失败: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            return self.performance_metrics.copy()
        except Exception as e:
            logger.error(f"获取性能指标失败: {e}")
            return {}
    
    def get_processing_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取处理历史"""
        try:
            return self.processing_history[-limit:] if limit > 0 else self.processing_history
        except Exception as e:
            logger.error(f"获取处理历史失败: {e}")
            return []
    
    def clear_history(self):
        """清空处理历史"""
        try:
            self.processing_history.clear()
            logger.info("处理历史已清空")
        except Exception as e:
            logger.error(f"清空历史失败: {e}")
    
    def get_processor_status(self) -> Dict[str, Any]:
        """获取处理器状态"""
        try:
            return {
                "initialized": self.initialized,
                "total_queries": self.performance_metrics["total_queries"],
                "success_rate": self.performance_metrics["successful_queries"] / max(1, self.performance_metrics["total_queries"]),
                "average_processing_time": self.performance_metrics["average_processing_time"],
                "history_size": len(self.processing_history),
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"获取处理器状态失败: {e}")
            return {
                "initialized": False,
                "error": str(e)
            }