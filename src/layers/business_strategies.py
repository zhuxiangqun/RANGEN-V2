#!/usr/bin/env python3
"""
业务层 - 策略模式实现
Business Strategy Pattern Implementations

提供数据评估、查询评估、性能评估、质量评估等策略类
"""
from abc import ABC, abstractmethod
from typing import Any


class EvaluationStrategy(ABC):
    """评估策略基类"""
    
    @abstractmethod
    def evaluate(self, data: Any) -> float:
        """评估数据"""
        try:
            # 数据质量评估
            quality_score = self._evaluate_data_quality(data)
            
            # 完整性评估
            completeness_score = self._evaluate_completeness(data)
            
            # 一致性评估
            consistency_score = self._evaluate_consistency(data)
            
            # 准确性评估
            accuracy_score = self._evaluate_accuracy(data)
            
            # 综合评分
            overall_score = (
                quality_score * 0.3 +
                completeness_score * 0.25 +
                consistency_score * 0.25 +
                accuracy_score * 0.2
            )
            
            return min(1.0, max(0.0, overall_score))
            
        except Exception as e:
            # 评估失败时返回低分
            return 0.1
    
    def _evaluate_data_quality(self, data: Any) -> float:
        """评估数据质量"""
        if data is None:
            return 0.0
        elif isinstance(data, (str, int, float, bool)):
            return 0.8
        elif isinstance(data, (list, dict)):
            return 0.6 if len(data) > 0 else 0.2
        else:
            return 0.4
    
    def _evaluate_completeness(self, data: Any) -> float:
        """评估数据完整性"""
        if data is None:
            return 0.0
        elif isinstance(data, dict):
            # 检查必需字段
            required_fields = ['id', 'name', 'type']
            present_fields = sum(1 for field in required_fields if field in data)
            return present_fields / len(required_fields)
        elif isinstance(data, list):
            return 0.8 if len(data) > 0 else 0.2
        else:
            return 0.6
    
    def _evaluate_consistency(self, data: Any) -> float:
        """评估数据一致性"""
        if data is None:
            return 0.0
        elif isinstance(data, dict):
            # 检查数据类型一致性
            type_consistency = 0.8
            return type_consistency
        elif isinstance(data, list):
            # 检查列表元素类型一致性
            if len(data) > 0:
                first_type = type(data[0])
                consistent = all(isinstance(item, first_type) for item in data)
                return 0.9 if consistent else 0.5
            return 0.3
        else:
            return 0.7
    
    def _evaluate_accuracy(self, data: Any) -> float:
        """评估数据准确性"""
        if data is None:
            return 0.0
        elif isinstance(data, (int, float)):
            # 数值范围检查
            if isinstance(data, int) and 0 <= data <= 100:
                return 0.9
            elif isinstance(data, float) and 0.0 <= data <= 1.0:
                return 0.9
            else:
                return 0.6
        elif isinstance(data, str):
            # 字符串长度和内容检查
            if len(data) > 0 and not data.isspace():
                return 0.8
            else:
                return 0.3
        else:
            return 0.5


class QueryEvaluationStrategy(EvaluationStrategy):
    """查询评估策略"""
    
    def evaluate(self, data: Any) -> float:
        """评估查询质量"""
        try:
            if isinstance(data, str):
                # 基于查询长度和复杂度评估
                length_score = min(len(data) / 100.0, 1.0)
                complexity_score = len(data.split()) / 50.0
                return (length_score + complexity_score) / 2
            return 0.5
        except Exception:
            return 0.0


class PerformanceEvaluationStrategy(EvaluationStrategy):
    """性能评估策略"""
    
    def evaluate(self, data: Any) -> float:
        """评估性能指标"""
        try:
            if isinstance(data, dict) and 'response_time' in data:
                response_time = data['response_time']
                if response_time < 100:
                    return 1.0
                elif response_time < 500:
                    return 0.8
                elif response_time < 1000:
                    return 0.6
                else:
                    return 0.4
            return 0.5
        except Exception:
            return 0.0


class QualityEvaluationStrategy(EvaluationStrategy):
    """质量评估策略"""
    
    def evaluate(self, data: Any) -> float:
        """评估数据质量"""
        try:
            if isinstance(data, dict):
                quality_indicators = ['accuracy', 'completeness', 'consistency', 'timeliness']
                scores = []
                for indicator in quality_indicators:
                    if indicator in data:
                        scores.append(data[indicator])
                if scores:
                    return sum(scores) / len(scores)
            return 0.5
        except Exception:
            return 0.0
