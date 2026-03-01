"""
模板选择器 - 根据问题类型、复杂度、证据质量智能选择模板
"""
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class TemplateSelector:
    """模板选择器"""
    
    def __init__(self, learning_manager=None):
        self.logger = logging.getLogger(__name__)
        self.learning_manager = learning_manager
        
        # 模板选择规则
        self.selection_rules = [
            {
                "condition": lambda ctx: ctx.get('has_evidence') and ctx.get('evidence_quality_score', 0) > 0.7,
                "primary": "reasoning_with_evidence",
                "fallback": ["reasoning_without_evidence", "general_query"]
            },
            {
                "condition": lambda ctx: ctx.get('query_type') == 'creative',
                "primary": "creative_writing",
                "fallback": ["general_query"]
            },
            {
                "condition": lambda ctx: ctx.get('query_type') in ['numerical', 'mathematical'],
                "primary": "reasoning_without_evidence",  # 数值问题可能不需要证据
                "fallback": ["reasoning_with_evidence", "general_query"]
            },
            {
                "condition": lambda ctx: ctx.get('complexity') == 'complex',
                "primary": "reasoning_steps_generation",  # 复杂问题需要推理步骤
                "fallback": ["reasoning_with_evidence", "reasoning_without_evidence"]
            },
            {
                "condition": lambda ctx: True,  # 默认规则
                "primary": "reasoning_without_evidence",
                "fallback": ["general_query"]
            }
        ]
    
    def select(
        self,
        query_type: str = "general",
        complexity: str = "medium",
        evidence_quality: Optional[str] = None,
        has_evidence: bool = False,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """选择模板
        
        Args:
            query_type: 查询类型
            complexity: 复杂度（simple/medium/complex）
            evidence_quality: 证据质量（high/medium/low/none）
            has_evidence: 是否有证据
            query: 查询文本（可选，用于学习管理器）
            
        Returns:
            包含模板名称和fallback链的字典
        """
        try:
            # 构建上下文
            context = {
                'query_type': query_type,
                'complexity': complexity,
                'evidence_quality': evidence_quality,
                'evidence_quality_score': self._quality_to_score(evidence_quality),
                'has_evidence': has_evidence
            }
            
            # 如果学习管理器可用，尝试使用学习到的选择
            if self.learning_manager and query:
                # 检查learning_manager是否有get_optimal_template方法
                if hasattr(self.learning_manager, 'get_optimal_template'):
                    try:
                        learned_template = self.learning_manager.get_optimal_template(
                            "reasoning_with_evidence", query_type, query
                        )
                        if learned_template:
                            self.logger.info(f"✅ 使用学习到的模板: {learned_template}")
                            return {
                                "template_name": learned_template,
                                "fallback_chain": ["reasoning_without_evidence", "general_query"],
                                "selection_reason": "learned_from_performance"
                            }
                    except Exception as e:
                        self.logger.debug(f"学习管理器选择模板失败，使用规则选择: {e}")
            
            # 应用选择规则
            for rule in self.selection_rules:
                if rule["condition"](context):
                    template_name = rule["primary"]
                    fallback_chain = rule["fallback"]
                    
                    self.logger.info(
                        f"✅ 选择模板: {template_name} "
                        f"(query_type={query_type}, complexity={complexity}, "
                        f"evidence_quality={evidence_quality})"
                    )
                    
                    return {
                        "template_name": template_name,
                        "fallback_chain": fallback_chain,
                        "selection_reason": "rule_based"
                    }
            
            # 默认返回
            return {
                "template_name": "reasoning_without_evidence",
                "fallback_chain": ["general_query"],
                "selection_reason": "default"
            }
            
        except Exception as e:
            self.logger.error(f"模板选择失败: {e}")
            return {
                "template_name": "general_query",
                "fallback_chain": [],
                "selection_reason": "error_fallback"
            }
    
    def _quality_to_score(self, quality: Optional[str]) -> float:
        """将质量等级转换为数值"""
        if not quality:
            return 0.0
        
        quality_lower = quality.lower()
        mapping = {
            'high': 0.9,
            'medium': 0.7,
            'low': 0.3,
            'none': 0.0
        }
        
        return mapping.get(quality_lower, 0.5)

