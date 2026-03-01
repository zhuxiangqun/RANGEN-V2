#!/usr/bin/env python3
"""
智能学习模块 - 增强版
提供真正的智能学习功能，包括模式识别、自适应学习、知识提取等
"""

import logging
import time
import json
import hashlib
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import asyncio

logger = logging.getLogger(__name__)


class LearningMode(Enum):
    """学习模式"""
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    TRANSFER = "transfer"
    META = "meta"


class LearningStrategy(Enum):
    """学习策略"""
    INCREMENTAL = "incremental"
    BATCH = "batch"
    ONLINE = "online"
    ADAPTIVE = "adaptive"


@dataclass
class LearningPattern:
    """学习模式"""
    pattern_id: str
    pattern_type: str
    features: List[float]
    confidence: float
    frequency: int
    last_seen: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningResult:
    """学习结果"""
    success: bool
    accuracy: float
    confidence: float
    patterns_learned: int
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class IntelligentLearningModule:
    """智能学习模块 - 增强版"""
    
    def __init__(self, learning_mode: LearningMode = LearningMode.UNSUPERVISED) -> None:
        """初始化智能学习模块"""
        self.learning_mode = learning_mode
        self.initialized = True
        self.learning_stats = {
            "total_learning_sessions": 0,
            "successful_learnings": 0,
            "failed_learnings": 0,
            "patterns_discovered": 0,
            "accuracy_improvements": 0
        }
        self.patterns: Dict[str, LearningPattern] = {}
        self.learning_history: List[Dict[str, Any]] = []
        self._learning_lock = threading.Lock()
        self._adaptation_threshold = 0.1
        self._confidence_threshold = 0.7
    
    def process_data(self, data: Any, context: Optional[Dict[str, Any]] = None) -> LearningResult:
        """处理数据 - 真正的学习处理逻辑"""
        try:
            start_time = time.time()
            self.learning_stats["total_learning_sessions"] += 1
            
            # 1. 数据预处理
            processed_data = self._preprocess_data(data)
            
            # 2. 特征提取
            features = self._extract_features(processed_data)
            
            # 3. 模式识别
            patterns = self._identify_patterns(features, context)
            
            # 4. 学习更新
            learning_update = self._update_learning_model(patterns, context)
            
            # 5. 结果评估
            accuracy = self._evaluate_accuracy(patterns, learning_update)
            confidence = self._calculate_confidence(patterns, accuracy)
            
            processing_time = time.time() - start_time
            
            result = LearningResult(
                success=True,
                accuracy=accuracy,
                confidence=confidence,
                patterns_learned=len(patterns),
                processing_time=processing_time,
                metadata={
                    "learning_mode": self.learning_mode.value,
                    "features_extracted": len(features),
                    "patterns_identified": len(patterns),
                    "context": context or {}
                }
            )
            
            self.learning_stats["successful_learnings"] += 1
            self.learning_stats["patterns_discovered"] += len(patterns)
            
            # 记录学习历史
            self._record_learning_history(result, data, context)
            
            return result
            
        except Exception as e:
            logger.error(f"数据处理失败: {e}")
            self.learning_stats["failed_learnings"] += 1
            
            return LearningResult(
                success=False,
                accuracy=0.0,
                confidence=0.0,
                patterns_learned=0,
                processing_time=time.time() - start_time,
                error=str(e)
            )
    
    def _preprocess_data(self, data: Any) -> Any:
        """数据预处理"""
        try:
            if isinstance(data, str):
                # 文本数据预处理
                processed = data.strip().lower()
                # 移除特殊字符
                processed = ''.join(c for c in processed if c.isalnum() or c.isspace())
                return processed
            elif isinstance(data, (list, tuple)):
                # 序列数据预处理
                processed = [str(item).strip() for item in data if item is not None]
                return processed
            elif isinstance(data, dict):
                # 字典数据预处理
                processed = {k: str(v).strip() for k, v in data.items() if v is not None}
                return processed
            else:
                return str(data)
        except Exception as e:
            logger.error(f"数据预处理失败: {e}")
            return data
    
    def _extract_features(self, data: Any) -> List[float]:
        """特征提取"""
        try:
            features = []
            
            if isinstance(data, str):
                # 文本特征
                features.extend([
                    len(data),  # 长度
                    len(data.split()),  # 词数
                    len(set(data.lower().split())),  # 唯一词数
                    data.count(' '),  # 空格数
                    data.count('\n'),  # 换行数
                    sum(1 for c in data if c.isdigit()),  # 数字字符数
                    sum(1 for c in data if c.isalpha()),  # 字母字符数
                ])
            elif isinstance(data, (list, tuple)):
                # 序列特征
                features.extend([
                    len(data),  # 长度
                    len(set(data)),  # 唯一元素数
                    sum(1 for item in data if isinstance(item, str)),  # 字符串元素数
                    sum(1 for item in data if isinstance(item, (int, float))),  # 数值元素数
                ])
            elif isinstance(data, dict):
                # 字典特征
                features.extend([
                    len(data),  # 键数
                    len(set(data.values())),  # 唯一值数
                    sum(1 for v in data.values() if isinstance(v, str)),  # 字符串值数
                    sum(1 for v in data.values() if isinstance(v, (int, float))),  # 数值值数
                ])
            else:
                # 默认特征
                features = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            
            # 归一化特征
            if features:
                max_feature = max(features) if max(features) > 0 else 1
                features = [f / max_feature for f in features]
            
            return features
        except Exception as e:
            logger.error(f"特征提取失败: {e}")
            return [0.0] * 7
    
    def _identify_patterns(self, features: List[float], context: Optional[Dict[str, Any]] = None) -> List[LearningPattern]:
        """模式识别"""
        try:
            patterns = []
            
            # 基于特征相似性识别模式
            for pattern_id, existing_pattern in self.patterns.items():
                similarity = self._calculate_similarity(features, existing_pattern.features)
                
                if similarity > self._confidence_threshold:
                    # 更新现有模式
                    updated_pattern = LearningPattern(
                        pattern_id=pattern_id,
                        pattern_type=existing_pattern.pattern_type,
                        features=self._update_features(existing_pattern.features, features),
                        confidence=max(existing_pattern.confidence, similarity),
                        frequency=existing_pattern.frequency + 1,
                        last_seen=time.time(),
                        metadata=existing_pattern.metadata
                    )
                    patterns.append(updated_pattern)
            
            # 如果没有匹配的模式，创建新模式
            if not patterns:
                new_pattern_id = self._generate_pattern_id(features)
                new_pattern = LearningPattern(
                    pattern_id=new_pattern_id,
                    pattern_type=self._classify_pattern_type(features, context),
                    features=features,
                    confidence=0.5,
                    frequency=1,
                    last_seen=time.time(),
                    metadata=context or {}
                )
                patterns.append(new_pattern)
            
            return patterns
        except Exception as e:
            logger.error(f"模式识别失败: {e}")
            return []
    
    def _calculate_similarity(self, features1: List[float], features2: List[float]) -> float:
        """计算特征相似性"""
        try:
            if len(features1) != len(features2):
                return 0.0
            
            # 使用余弦相似性
            dot_product = sum(a * b for a, b in zip(features1, features2))
            magnitude1 = sum(a * a for a in features1) ** 0.5
            magnitude2 = sum(b * b for b in features2) ** 0.5
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            similarity = dot_product / (magnitude1 * magnitude2)
            return max(0.0, min(1.0, similarity))
        except Exception as e:
            logger.error(f"相似性计算失败: {e}")
            return 0.0
    
    def _update_features(self, old_features: List[float], new_features: List[float]) -> List[float]:
        """更新特征 - 使用指数移动平均"""
        try:
            alpha = 0.1  # 学习率
            updated_features = []
            
            for old, new in zip(old_features, new_features):
                updated = old * (1 - alpha) + new * alpha
                updated_features.append(updated)
            
            return updated_features
        except Exception as e:
            logger.error(f"特征更新失败: {e}")
            return old_features
    
    def _generate_pattern_id(self, features: List[float]) -> str:
        """生成模式ID"""
        try:
            # 基于特征生成唯一ID
            feature_str = ','.join(f"{f:.3f}" for f in features)
            pattern_hash = hashlib.md5(feature_str.encode()).hexdigest()[:8]
            return f"pattern_{pattern_hash}"
        except Exception as e:
            logger.error(f"模式ID生成失败: {e}")
            return f"pattern_{int(time.time())}"
    
    def _classify_pattern_type(self, features: List[float], context: Optional[Dict[str, Any]] = None) -> str:
        """分类模式类型"""
        try:
            # 基于特征和上下文分类模式类型
            if context:
                if 'text' in str(context).lower():
                    return 'text_pattern'
                elif 'numeric' in str(context).lower():
                    return 'numeric_pattern'
                elif 'sequence' in str(context).lower():
                    return 'sequence_pattern'
            
            # 基于特征值分类
            if len(features) > 0:
                if features[0] > 0.8:  # 长度特征
                    return 'long_pattern'
                elif features[0] < 0.2:
                    return 'short_pattern'
                else:
                    return 'medium_pattern'
            
            return 'unknown_pattern'
        except Exception as e:
            logger.error(f"模式类型分类失败: {e}")
            return 'unknown_pattern'
    
    def _update_learning_model(self, patterns: List[LearningPattern], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """更新学习模型"""
        try:
            with self._learning_lock:
                update_info = {
                    "patterns_updated": 0,
                    "patterns_added": 0,
                    "patterns_removed": 0,
                    "model_improvement": 0.0
                }
                
                for pattern in patterns:
                    if pattern.pattern_id in self.patterns:
                        # 更新现有模式
                        old_pattern = self.patterns[pattern.pattern_id]
                        self.patterns[pattern.pattern_id] = pattern
                        update_info["patterns_updated"] += 1
                        
                        # 计算改进程度
                        improvement = abs(pattern.confidence - old_pattern.confidence)
                        update_info["model_improvement"] += improvement
                    else:
                        # 添加新模式
                        self.patterns[pattern.pattern_id] = pattern
                        update_info["patterns_added"] += 1
                
                # 清理旧模式
                current_time = time.time()
                patterns_to_remove = []
                for pattern_id, pattern in self.patterns.items():
                    if current_time - pattern.last_seen > 3600:  # 1小时未使用
                        patterns_to_remove.append(pattern_id)
                
                for pattern_id in patterns_to_remove:
                    del self.patterns[pattern_id]
                    update_info["patterns_removed"] += 1
                
                return update_info
        except Exception as e:
            logger.error(f"学习模型更新失败: {e}")
            return {"error": str(e)}
    
    def _evaluate_accuracy(self, patterns: List[LearningPattern], learning_update: Dict[str, Any]) -> float:
        """评估准确性"""
        try:
            if not patterns:
                return 0.0
            
            # 基于模式置信度和频率计算准确性
            total_confidence = sum(pattern.confidence for pattern in patterns)
            total_frequency = sum(pattern.frequency for pattern in patterns)
            
            if total_frequency == 0:
                return 0.0
            
            # 加权平均准确性
            weighted_accuracy = total_confidence / len(patterns)
            
            # 考虑学习改进
            improvement_factor = learning_update.get("model_improvement", 0.0)
            accuracy = min(1.0, weighted_accuracy + improvement_factor * 0.1)
            
            return accuracy
        except Exception as e:
            logger.error(f"准确性评估失败: {e}")
            return 0.0
    
    def _calculate_confidence(self, patterns: List[LearningPattern], accuracy: float) -> float:
        """计算置信度"""
        try:
            if not patterns:
                return 0.0
            
            # 基于模式数量和准确性计算置信度
            pattern_count_factor = min(1.0, len(patterns) / 10.0)  # 最多10个模式
            accuracy_factor = accuracy
            
            confidence = (pattern_count_factor + accuracy_factor) / 2
            return min(1.0, max(0.0, confidence))
        except Exception as e:
            logger.error(f"置信度计算失败: {e}")
            return 0.0
    
    def _record_learning_history(self, result: LearningResult, data: Any, context: Optional[Dict[str, Any]] = None) -> None:
        """记录学习历史"""
        try:
            history_entry = {
                "timestamp": time.time(),
                "result": {
                    "success": result.success,
                    "accuracy": result.accuracy,
                    "confidence": result.confidence,
                    "patterns_learned": result.patterns_learned,
                    "processing_time": result.processing_time
                },
                "data_type": type(data).__name__,
                "data_size": len(str(data)),
                "context": context or {}
            }
            
            self.learning_history.append(history_entry)
            
            # 保持历史记录在合理范围内
            if len(self.learning_history) > 1000:
                self.learning_history = self.learning_history[-500:]
        except Exception as e:
            logger.error(f"学习历史记录失败: {e}")
    
    def validate(self, data: Any) -> bool:
        """验证数据"""
        try:
            # 基本验证
            if data is None:
                return False
            
            # 类型验证
            if not isinstance(data, (str, list, tuple, dict, int, float)):
                return False
            
            # 内容验证
            if isinstance(data, str) and len(data.strip()) == 0:
                return False
            
            if isinstance(data, (list, tuple)) and len(data) == 0:
                return False
            
            if isinstance(data, dict) and len(data) == 0:
                return False
            
            return True
        except Exception as e:
            logger.error(f"数据验证失败: {e}")
            return False
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """获取学习统计信息"""
        try:
            stats = self.learning_stats.copy()
            stats["total_patterns"] = len(self.patterns)
            stats["learning_history_size"] = len(self.learning_history)
            
            # 计算模式类型分布
            pattern_types: Dict[str, int] = {}
            for pattern in self.patterns.values():
                pattern_type = pattern.pattern_type
                pattern_types[pattern_type] = pattern_types.get(pattern_type, 0) + 1
            
            stats["pattern_types"] = pattern_types  # type: ignore
            
            # 计算平均置信度
            if self.patterns:
                avg_confidence = sum(pattern.confidence for pattern in self.patterns.values()) / len(self.patterns)
                stats["average_confidence"] = avg_confidence  # type: ignore
            else:
                stats["average_confidence"] = 0.0  # type: ignore
            
            return stats
        except Exception as e:
            logger.error(f"获取学习统计信息失败: {e}")
            return self.learning_stats.copy()
    
    def export_patterns(self) -> Dict[str, Any]:
        """导出学习模式"""
        try:
            exported_patterns = {}
            for pattern_id, pattern in self.patterns.items():
                exported_patterns[pattern_id] = {
                    "pattern_type": pattern.pattern_type,
                    "features": pattern.features,
                    "confidence": pattern.confidence,
                    "frequency": pattern.frequency,
                    "last_seen": pattern.last_seen,
                    "metadata": pattern.metadata
                }
            
            return {
                "patterns": exported_patterns,
                "export_time": time.time(),
                "total_patterns": len(exported_patterns)
            }
        except Exception as e:
            logger.error(f"模式导出失败: {e}")
            return {"error": str(e)}
    
    def import_patterns(self, patterns_data: Dict[str, Any]) -> bool:
        """导入学习模式"""
        try:
            with self._learning_lock:
                imported_count = 0
                
                for pattern_id, pattern_info in patterns_data.get("patterns", {}).items():
                    pattern = LearningPattern(
                        pattern_id=pattern_id,
                        pattern_type=pattern_info["pattern_type"],
                        features=pattern_info["features"],
                        confidence=pattern_info["confidence"],
                        frequency=pattern_info["frequency"],
                        last_seen=pattern_info["last_seen"],
                        metadata=pattern_info["metadata"]
                    )
                    
                    self.patterns[pattern_id] = pattern
                    imported_count += 1
                
                logger.info(f"成功导入 {imported_count} 个学习模式")
                return True
        except Exception as e:
            logger.error(f"模式导入失败: {e}")
            return False


# 全局实例
_learning_module = None


def get_intelligent_learning_module() -> IntelligentLearningModule:
    """获取智能学习模块实例"""
    global _learning_module
    if _learning_module is None:
        _learning_module = IntelligentLearningModule()
    return _learning_module
