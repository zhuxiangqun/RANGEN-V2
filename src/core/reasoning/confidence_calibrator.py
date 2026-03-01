"""
置信度校准器 - 统一置信度格式并校准评分
"""
import logging
from typing import Dict, Any, Union, Optional

logger = logging.getLogger(__name__)


class ConfidenceCalibrator:
    """置信度校准器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def normalize(self, confidence: Union[str, float, Dict[str, Any]]) -> Dict[str, Any]:
        """标准化置信度格式
        
        Args:
            confidence: 置信度（可能是字符串、数值或字典）
            
        Returns:
            统一格式的置信度字典 {"score": 0.85, "level": "high"}
        """
        try:
            # 如果已经是统一格式
            if isinstance(confidence, dict):
                if 'score' in confidence and 'level' in confidence:
                    return confidence
                # 如果只有score，补充level
                if 'score' in confidence:
                    score = float(confidence['score'])
                    return {
                        "score": score,
                        "level": self._score_to_level(score)
                    }
                # 如果只有level，补充score
                if 'level' in confidence:
                    level = confidence['level'].lower()
                    return {
                        "score": self._level_to_score(level),
                        "level": level
                    }
            
            # 如果是数值
            if isinstance(confidence, (int, float)):
                score = float(confidence)
                # 确保在0-1范围内
                score = max(0.0, min(1.0, score))
                return {
                    "score": score,
                    "level": self._score_to_level(score)
                }
            
            # 如果是字符串
            if isinstance(confidence, str):
                conf_lower = confidence.lower().strip()
                
                # 尝试解析数值
                try:
                    score = float(conf_lower)
                    score = max(0.0, min(1.0, score))
                    return {
                        "score": score,
                        "level": self._score_to_level(score)
                    }
                except ValueError:
                    pass
                
                # 处理文本格式
                level_mapping = {
                    'high': 'high',
                    'medium': 'medium',
                    'low': 'low',
                    '高': 'high',
                    '中': 'medium',
                    '低': 'low'
                }
                
                if conf_lower in level_mapping:
                    level = level_mapping[conf_lower]
                    return {
                        "score": self._level_to_score(level),
                        "level": level
                    }
            
            # 默认值
            return {"score": 0.7, "level": "medium"}
            
        except Exception as e:
            self.logger.error(f"置信度标准化失败: {e}")
            return {"score": 0.7, "level": "medium"}
    
    def calibrate(
        self,
        confidence: Dict[str, Any],
        evidence_quality: Optional[str] = None,
        query_complexity: Optional[str] = None
    ) -> Dict[str, Any]:
        """校准置信度（根据证据质量和查询复杂度调整）
        
        Args:
            confidence: 原始置信度
            evidence_quality: 证据质量（high/medium/low/none）
            query_complexity: 查询复杂度（simple/medium/complex）
            
        Returns:
            校准后的置信度
        """
        try:
            # 先标准化
            normalized = self.normalize(confidence)
            score = normalized["score"]
            
            # 根据证据质量调整
            if evidence_quality:
                quality_adjustment = {
                    'high': 0.1,    # 高质量证据增加置信度
                    'medium': 0.0,  # 中等质量不调整
                    'low': -0.2,    # 低质量证据降低置信度
                    'none': -0.3    # 无证据显著降低置信度
                }
                adjustment = quality_adjustment.get(evidence_quality.lower(), 0.0)
                score += adjustment
            
            # 根据查询复杂度调整
            if query_complexity:
                complexity_adjustment = {
                    'simple': 0.05,   # 简单问题稍微增加置信度
                    'medium': 0.0,    # 中等复杂度不调整
                    'complex': -0.1   # 复杂问题降低置信度
                }
                adjustment = complexity_adjustment.get(query_complexity.lower(), 0.0)
                score += adjustment
            
            # 确保在0-1范围内
            score = max(0.0, min(1.0, score))
            
            return {
                "score": score,
                "level": self._score_to_level(score),
                "original_score": normalized["score"],
                "calibration_applied": True
            }
            
        except Exception as e:
            self.logger.error(f"置信度校准失败: {e}")
            return self.normalize(confidence)
    
    def _score_to_level(self, score: float) -> str:
        """将评分转换为等级"""
        if score > 0.8:
            return "high"
        elif score > 0.5:
            return "medium"
        else:
            return "low"
    
    def _level_to_score(self, level: str) -> float:
        """将等级转换为评分"""
        level_mapping = {
            'high': 0.9,
            'medium': 0.7,
            'low': 0.3
        }
        return level_mapping.get(level.lower(), 0.7)

