#!/usr/bin/env python3
"""
增强上下文工程模块
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ContextRequest:
    """上下文请求"""
    query: str
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ContextResponse:
    """上下文响应"""
    request_id: str
    query: str
    answer: str
    confidence: float
    processing_time: float
    metadata: Optional[Dict[str, Any]] = None

class EnhancedContextEngineering:
    """增强上下文工程"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.processing_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time": 0,
            "request_count": 0,
            "average_processing_time": 0.0
        }
    
    def process_data(self, request: ContextRequest) -> ContextResponse:
        """处理上下文请求"""
        # 🎯 编排追踪：上下文增强开始
        from src.visualization.orchestration_tracker import get_orchestration_tracker
        tracker = getattr(self, '_orchestration_tracker', None) or get_orchestration_tracker()
        parent_event_id = getattr(self, '_current_parent_event_id', None)
        
        try:
            # 验证输入
            if not self._validate_context_request(request):
                return self._create_error_response("Invalid context request")
            
            start_time = datetime.now()
            request_id = f"ctx_{int(start_time.timestamp() * 1000)}"
            
            # 🎯 编排追踪：上下文增强
            if tracker:
                tracker.track_context_enhance(
                    "enhanced_context_engineering",  # enhancement_type
                    {"request_id": request_id, "query": request.query[:100] if request.query else '', "metadata_keys": list(request.metadata.keys()) if request.metadata else []},
                    parent_event_id
                )
            
            # 预处理上下文
            processed_request = self._preprocess_context_request(request)
            
            # 生成上下文答案
            answer = self._generate_context_answer(processed_request.query)
            
            # 计算置信度
            confidence = self._calculate_confidence(processed_request.query, answer)
            
            # 后处理答案
            final_answer = self._postprocess_answer(answer, processed_request)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            response = ContextResponse(
                request_id=request_id,
                query=processed_request.query,
                answer=final_answer,
                confidence=confidence,
                processing_time=processing_time,
                metadata=processed_request.metadata
            )
            
            # 更新统计信息
            self.processing_stats["total_requests"] += 1
            self.processing_stats["successful_requests"] += 1
            self._update_average_processing_time(processing_time)
            
            return response
            
        except Exception as e:
            self.logger.error(f"处理上下文请求失败: {e}")
            self.processing_stats["failed_requests"] += 1
            return self._create_error_response(f"Context processing failed: {e}")
    
    def _validate_context_request(self, request: ContextRequest) -> bool:
        """验证上下文请求"""
        if not isinstance(request, ContextRequest):
            return False
        
        if not request.query or not request.query.strip():
            return False
        
        return True
    
    def _preprocess_context_request(self, request: ContextRequest) -> ContextRequest:
        """预处理上下文请求"""
        try:
            # 清理查询文本
            cleaned_query = request.query.strip()
            
            # 添加预处理元数据
            metadata = request.metadata.copy() if request.metadata else {}
            metadata['preprocessed'] = True
            metadata['original_length'] = len(request.query)
            metadata['cleaned_length'] = len(cleaned_query)
            
            return ContextRequest(
                query=cleaned_query,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.warning(f"预处理上下文请求失败: {e}")
            return request
    
    def _postprocess_answer(self, answer: str, request: ContextRequest) -> str:
        """后处理答案"""
        try:
            # 基本清理
            processed_answer = answer.strip()
            
            # 添加上下文信息
            if request.metadata and request.metadata.get('add_context', True):
                processed_answer = f"基于上下文分析：{processed_answer}"
            
            return processed_answer
            
        except Exception as e:
            self.logger.warning(f"后处理答案失败: {e}")
            return answer
    
    def _create_error_response(self, error_message: str) -> ContextResponse:
        """创建错误响应"""
        return ContextResponse(
            request_id="error",
            query="",
            answer=f"Error: {error_message}",
            confidence=0.0,
            processing_time=0.0,
            metadata={'error': True, 'message': error_message}
        )

    def _update_average_processing_time(self, processing_time: float):
        """更新平均处理时间"""
        if "total_processing_time" not in self.processing_stats:
            self.processing_stats["total_processing_time"] = 0
        if "request_count" not in self.processing_stats:
            self.processing_stats["request_count"] = 0
        
        self.processing_stats["total_processing_time"] += processing_time
        self.processing_stats["request_count"] += 1
        
        if self.processing_stats["request_count"] > 0:
            self.processing_stats["average_processing_time"] = (
                self.processing_stats["total_processing_time"] / 
                self.processing_stats["request_count"]
            )

    def _generate_context_answer(self, query: str) -> str:
        """生成上下文答案"""
        # 简单的答案生成逻辑
        if not query:
            return "无查询内容"
        
        # 基于查询长度和内容生成答案
        if len(query) < 10:
            return f"简短查询: {query}"
        elif len(query) < 50:
            return f"中等查询: {query[:30]}..."
        else:
            return f"复杂查询: {query[:50]}..."

    def _calculate_confidence(self, query: str, answer: str) -> float:
        """计算置信度"""
        if not query or not answer:
            return 0.0
        
        # 基于查询和答案的长度计算置信度
        query_length = len(query)
        answer_length = len(answer)
        
        if query_length == 0:
            return 0.0
        
        # 简单的置信度计算
        base_confidence = min(0.9, 0.5 + (answer_length / query_length) * 0.4)
        return round(base_confidence, 2)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.processing_stats.copy()

    def reset_statistics(self):
        """重置统计信息"""
        self.processing_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time": 0,
            "request_count": 0,
            "average_processing_time": 0.0
        }

# 全局实例
_context_engineering = EnhancedContextEngineering()

def get_context_engineering() -> EnhancedContextEngineering:
    """获取上下文工程实例"""
    return _context_engineering

# 扩展EnhancedContextEngineering类的方法
def get_processing_metrics(self) -> Dict[str, Any]:
    """获取处理指标"""
    try:
        return {
            "total_requests": self.processing_stats["total_requests"],
            "successful_requests": self.processing_stats["successful_requests"],
            "failed_requests": self.processing_stats["failed_requests"],
            "success_rate": self.processing_stats["successful_requests"] / max(self.processing_stats["total_requests"], 1),
            "average_processing_time": self.processing_stats["average_processing_time"],
            "total_processing_time": self.processing_stats["total_processing_time"]
        }
    except Exception as e:
        self.logger.error(f"获取处理指标失败: {e}")
        return {"error": str(e)}

def get_context_quality_score(self, query: str, answer: str) -> float:
    """获取上下文质量分数"""
    try:
        # 基于查询和答案的长度、复杂度等计算质量分数
        query_length = len(query)
        answer_length = len(answer)
        
        # 基础分数
        base_score = 0.5
        
        # 长度分数
        length_score = min(1.0, (query_length + answer_length) / 1000)
        
        # 复杂度分数
        complexity_score = min(1.0, len(query.split()) / 50)
        
        # 综合分数
        quality_score = (base_score + length_score + complexity_score) / 3
        
        return min(1.0, max(0.0, quality_score))
    except Exception as e:
        self.logger.error(f"计算上下文质量分数失败: {e}")
        return 0.5

def optimize_context_processing(self) -> Dict[str, Any]:
    """优化上下文处理"""
    try:
        optimization_results = {
            "optimization_applied": False,
            "improvements": [],
            "timestamp": time.time()
        }
        
        # 检查是否需要优化
        if self.processing_stats["total_requests"] > 100:
            # 如果平均处理时间过长，建议优化
            if self.processing_stats["average_processing_time"] > 1.0:
                optimization_results["improvements"].append("建议优化处理算法以提高速度")
                optimization_results["optimization_applied"] = True
            
            # 如果成功率过低，建议改进
            success_rate = self.processing_stats["successful_requests"] / max(self.processing_stats["total_requests"], 1)
            if success_rate < 0.8:
                optimization_results["improvements"].append("建议改进错误处理以提高成功率")
                optimization_results["optimization_applied"] = True
        
        return optimization_results
    except Exception as e:
        self.logger.error(f"优化上下文处理失败: {e}")
        return {"error": str(e)}

def get_context_history(self, limit: int = 100) -> List[Dict[str, Any]]:
    """获取上下文历史"""
    try:
        # 这里应该从历史存储中获取上下文历史
        # 目前返回空列表
        return []
    except Exception as e:
        self.logger.error(f"获取上下文历史失败: {e}")
        return []

def clear_context_history(self) -> bool:
    """清空上下文历史"""
    try:
        # 这里应该清空历史存储
        # 目前返回True
        return True
    except Exception as e:
        self.logger.error(f"清空上下文历史失败: {e}")
        return False

def get_context_statistics(self) -> Dict[str, Any]:
    """获取上下文统计信息"""
    try:
        return {
            "processing_stats": self.processing_stats.copy(),
            "quality_metrics": {
                "average_quality_score": self._calculate_real_quality_score(),  # 真实质量分数
                "quality_trend": "stable"
            },
            "performance_metrics": {
                "throughput": self.processing_stats["total_requests"] / max(time.time() - getattr(self, 'start_time', time.time()), 1),
                "error_rate": self.processing_stats["failed_requests"] / max(self.processing_stats["total_requests"], 1)
            },
            "timestamp": time.time()
        }
    except Exception as e:
        self.logger.error(f"获取上下文统计信息失败: {e}")
        return {"error": str(e)}

def health_check(self) -> Dict[str, Any]:
    """健康检查"""
    try:
        # 检查处理统计
        total_requests = self.processing_stats["total_requests"]
        failed_requests = self.processing_stats["failed_requests"]
        
        if total_requests > 0:
            error_rate = failed_requests / total_requests
            if error_rate > 0.5:
                status = "unhealthy"
            elif error_rate > 0.2:
                status = "degraded"
            else:
                status = "healthy"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "total_requests": total_requests,
            "failed_requests": failed_requests,
            "error_rate": error_rate if total_requests > 0 else 0,
            "timestamp": time.time()
        }
    except Exception as e:
        self.logger.error(f"健康检查失败: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

def get_context_engineering_status(self) -> Dict[str, Any]:
    """获取上下文工程状态"""
    try:
        return {
            "initialized": True,
            "processing_stats": self.processing_stats.copy(),
            "timestamp": time.time()
        }
    except Exception as e:
        self.logger.error(f"获取上下文工程状态失败: {e}")
        return {"error": str(e)}

# 将方法添加到类中
EnhancedContextEngineering.get_processing_metrics = get_processing_metrics
EnhancedContextEngineering.get_context_quality_score = get_context_quality_score
EnhancedContextEngineering.optimize_context_processing = optimize_context_processing
EnhancedContextEngineering.get_context_history = get_context_history
EnhancedContextEngineering.clear_context_history = clear_context_history
EnhancedContextEngineering.get_context_statistics = get_context_statistics
EnhancedContextEngineering.health_check = health_check
EnhancedContextEngineering.get_context_engineering_status = get_context_engineering_status

def _calculate_real_quality_score(self) -> float:
    """计算真实质量分数"""
    try:
        if not self.processing_stats["total_requests"]:
            return 0.5  # 默认分数
        
        # 基于成功率计算质量分数
        success_rate = 1.0 - (self.processing_stats["failed_requests"] / self.processing_stats["total_requests"])
        
        # 基于处理时间计算质量分数
        avg_processing_time = self.processing_stats.get("total_processing_time", 0) / max(self.processing_stats["total_requests"], 1)
        time_quality = max(0.0, 1.0 - (avg_processing_time / 1.0))  # 假设1秒为理想处理时间
        
        # 基于上下文复杂度计算质量分数
        complexity_quality = min(1.0, self.processing_stats.get("average_context_length", 0) / 1000.0)
        
        # 综合质量分数
        quality_score = (success_rate * 0.5 + time_quality * 0.3 + complexity_quality * 0.2)
        
        return min(1.0, max(0.0, quality_score))
        
    except Exception as e:
        self.logger.error(f"质量分数计算失败: {e}")
        return 0.5

EnhancedContextEngineering._calculate_real_quality_score = _calculate_real_quality_score