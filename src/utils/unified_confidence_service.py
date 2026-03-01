#!/usr/bin/env python3
"""
统一置信度服务 - Unified Confidence Service
统一处理核心系统中的所有置信度计算和校准任务
"""
import logging
from typing import Dict, Any, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """置信度级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UnifiedConfidenceService:
    """统一置信度服务 - 统一处理所有置信度计算和校准"""
    
    _instance: Optional['UnifiedConfidenceService'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化统一置信度服务"""
        if self._initialized:
            return
        
        self.logger = logging.getLogger(__name__)
        self._initialized = True
        
        # 导入置信度相关组件
        self._confidence_calibrator = None
        self._deep_confidence_estimator = None
        self._init_components()
        
        # 统一阈值配置
        self._thresholds = {
            'high': 0.8,
            'medium': 0.5,
            'low': 0.3
        }
    
    def _init_components(self):
        """初始化置信度相关组件"""
        try:
            # 导入置信度校准器
            from src.core.reasoning.confidence_calibrator import ConfidenceCalibrator
            self._confidence_calibrator = ConfidenceCalibrator()
            self.logger.debug("✅ 置信度校准器已初始化")
        except Exception as e:
            self.logger.warning(f"⚠️ 置信度校准器初始化失败: {e}")
        
        try:
            # 导入深度置信度评估器（可选）
            from src.core.reasoning.ml_framework.deep_confidence_estimator import DeepConfidenceEstimator
            self._deep_confidence_estimator = DeepConfidenceEstimator()
            self.logger.debug("✅ 深度置信度评估器已初始化")
        except Exception as e:
            self.logger.debug(f"深度置信度评估器不可用: {e}，将使用规则方法")
    
    def calculate_confidence(
        self,
        query: str,
        answer: str,
        evidence: Optional[list] = None,
        context: Optional[Dict[str, Any]] = None,
        evidence_quality: Optional[str] = None,
        query_complexity: Optional[str] = None,
        use_ml: bool = True
    ) -> Dict[str, Any]:
        """计算置信度 - 🚀 统一入口
        
        Args:
            query: 查询文本
            answer: 答案文本
            evidence: 证据列表（可选）
            context: 上下文信息（可选）
            evidence_quality: 证据质量（high/medium/low/none，可选）
            query_complexity: 查询复杂度（simple/medium/complex，可选）
            use_ml: 是否使用ML模型（默认True）
            
        Returns:
            统一格式的置信度字典:
            {
                "score": 0.85,  # 0-1范围的评分
                "level": "high",  # low/medium/high
                "method": "ml" or "rule",  # 计算方法
                "factors": {...},  # 影响因素
                "calibrated": True  # 是否已校准
            }
        """
        try:
            # 1. 优先使用ML模型计算置信度
            if use_ml and self._deep_confidence_estimator:
                try:
                    input_data = {
                        "query": query,
                        "answer": answer,
                        "evidence": evidence or [],
                        "context": context or {}
                    }
                    
                    ml_result = self._deep_confidence_estimator.predict(input_data)
                    
                    if ml_result and 'confidence' in ml_result:
                        confidence_score = float(ml_result['confidence'])
                        confidence_score = max(0.0, min(1.0, confidence_score))
                        
                        result = {
                            "score": confidence_score,
                            "level": self._score_to_level(confidence_score),
                            "method": "ml",
                            "factors": ml_result.get('factors', {}),
                            "calibrated": False
                        }
                        
                        # 2. 校准置信度（根据证据质量和查询复杂度）
                        if self._confidence_calibrator:
                            calibrated = self._confidence_calibrator.calibrate(
                                confidence=result,
                                evidence_quality=evidence_quality,
                                query_complexity=query_complexity
                            )
                            result.update(calibrated)
                            result["calibrated"] = True
                        
                        return result
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ ML置信度计算失败: {e}，使用规则方法")
            
            # 3. Fallback: 使用规则方法计算置信度
            return self._calculate_confidence_by_rules(
                query=query,
                answer=answer,
                evidence=evidence,
                context=context,
                evidence_quality=evidence_quality,
                query_complexity=query_complexity
            )
            
        except Exception as e:
            self.logger.error(f"置信度计算失败: {e}", exc_info=True)
            # 返回默认置信度
            return {
                "score": 0.5,
                "level": "medium",
                "method": "default",
                "factors": {},
                "calibrated": False
            }
    
    def _calculate_confidence_by_rules(
        self,
        query: str,
        answer: str,
        evidence: Optional[list] = None,
        context: Optional[Dict[str, Any]] = None,
        evidence_quality: Optional[str] = None,
        query_complexity: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用规则方法计算置信度"""
        confidence_score = 0.5  # 基础置信度
        factors = {}
        
        # 1. 基于答案长度（太短或太长都降低置信度）
        answer_length = len(answer.strip())
        if 5 <= answer_length <= 100:
            confidence_score += 0.1
            factors['answer_length'] = 'good'
        elif answer_length < 5:
            confidence_score -= 0.2
            factors['answer_length'] = 'too_short'
        else:
            confidence_score -= 0.1
            factors['answer_length'] = 'too_long'
        
        # 2. 基于证据数量
        if evidence:
            evidence_count = len(evidence)
            if evidence_count >= 3:
                confidence_score += 0.15
                factors['evidence_count'] = 'sufficient'
            elif evidence_count >= 1:
                confidence_score += 0.05
                factors['evidence_count'] = 'moderate'
            else:
                confidence_score -= 0.1
                factors['evidence_count'] = 'insufficient'
        else:
            confidence_score -= 0.15
            factors['evidence_count'] = 'none'
        
        # 3. 基于证据质量
        if evidence_quality:
            quality_adjustment = {
                'high': 0.2,
                'medium': 0.0,
                'low': -0.2,
                'none': -0.3
            }
            adjustment = quality_adjustment.get(evidence_quality.lower(), 0.0)
            confidence_score += adjustment
            factors['evidence_quality'] = evidence_quality.lower()
        
        # 4. 基于查询复杂度
        if query_complexity:
            complexity_adjustment = {
                'simple': 0.1,
                'medium': 0.0,
                'complex': -0.1
            }
            adjustment = complexity_adjustment.get(query_complexity.lower(), 0.0)
            confidence_score += adjustment
            factors['query_complexity'] = query_complexity.lower()
        
        # 确保在0-1范围内
        confidence_score = max(0.0, min(1.0, confidence_score))
        
        result = {
            "score": confidence_score,
            "level": self._score_to_level(confidence_score),
            "method": "rule",
            "factors": factors,
            "calibrated": False
        }
        
        # 校准置信度
        if self._confidence_calibrator:
            calibrated = self._confidence_calibrator.calibrate(
                confidence=result,
                evidence_quality=evidence_quality,
                query_complexity=query_complexity
            )
            result.update(calibrated)
            result["calibrated"] = True
        
        return result
    
    def normalize_confidence(self, confidence: Union[str, float, Dict[str, Any]]) -> Dict[str, Any]:
        """标准化置信度格式
        
        Args:
            confidence: 置信度（可能是字符串、数值或字典）
            
        Returns:
            统一格式的置信度字典 {"score": 0.85, "level": "high"}
        """
        if self._confidence_calibrator:
            return self._confidence_calibrator.normalize(confidence)
        else:
            # Fallback: 简单标准化
            if isinstance(confidence, dict):
                if 'score' in confidence:
                    score = float(confidence['score'])
                    return {
                        "score": max(0.0, min(1.0, score)),
                        "level": self._score_to_level(score)
                    }
            elif isinstance(confidence, (int, float)):
                score = float(confidence)
                return {
                    "score": max(0.0, min(1.0, score)),
                    "level": self._score_to_level(score)
                }
            elif isinstance(confidence, str):
                level_mapping = {
                    'high': 0.9,
                    'medium': 0.7,
                    'low': 0.3,
                    '高': 0.9,
                    '中': 0.7,
                    '低': 0.3
                }
                score = level_mapping.get(confidence.lower(), 0.7)
                return {
                    "score": score,
                    "level": self._score_to_level(score)
                }
            
            return {"score": 0.7, "level": "medium"}
    
    def _score_to_level(self, score: float) -> str:
        """将评分转换为等级"""
        if score >= self._thresholds['high']:
            return "high"
        elif score >= self._thresholds['medium']:
            return "medium"
        else:
            return "low"


def get_unified_confidence_service() -> UnifiedConfidenceService:
    """获取统一置信度服务实例（单例）"""
    if UnifiedConfidenceService._instance is None:
        UnifiedConfidenceService._instance = UnifiedConfidenceService()
    return UnifiedConfidenceService._instance

