"""
推理引擎数据模型
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional


class ReasoningStepType:
    """推理步骤类型 - LLM驱动版（保持智能性和扩展性）"""
    
    @staticmethod
    def generate_step_type(query: str, context: str, llm_integration=None, fast_llm_integration=None, prompt_engineering=None) -> str:
        """使用LLM生成推理步骤类型（🚀 优化：使用统一分类服务）
        
        🚀 优化：
        1. 优先使用快速模型（3-10秒），如果不可用则使用推理模型
        2. 使用统一分类服务处理分类逻辑
        """
        try:
            # 🚀 优化：使用统一分类服务
            from src.utils.unified_classification_service import get_unified_classification_service
            
            classification_service = get_unified_classification_service(
                prompt_engineering=prompt_engineering,
                llm_integration=llm_integration,
                fast_llm_integration=fast_llm_integration
            )
            
            valid_types = [
                'evidence_gathering', 'query_analysis', 'logical_deduction',
                'pattern_recognition', 'causal_reasoning', 'analogical_reasoning',
                'mathematical_reasoning', 'answer_synthesis'
            ]
            
            # 构建fallback提示词（如果统一服务失败）
            # 🚀 修复：使用完整查询，不截断（分类服务本身没有长度限制）
            def fallback_prompt():
                # 对于fallback提示词，如果查询过长，可以适当截断用于显示，但不影响实际分类
                query_preview = query[:200] if len(query) > 200 else query
                return f"Query: {query_preview}\nReturn only the type name: {','.join(valid_types)}"
            
            # 🚀 修复：使用完整查询进行分类，不截断（确保分类准确性）
            return classification_service.classify(
                query=query,  # 使用完整查询，不截断
                classification_type="reasoning_step_type",
                valid_types=valid_types,
                template_name="reasoning_step_type_classification",
                default_type="logical_deduction",
                context=str(context)[:500] if context else ""  # 增加context长度限制到500字符
            )
                
        except Exception as e:
            # 回退到默认类型
            return "logical_deduction"
    
    @staticmethod
    def get_all_types() -> List[str]:
        """获取所有可用的推理步骤类型"""
        return [
            "evidence_gathering",
            "query_analysis", 
            "logical_deduction",
            "pattern_recognition",
            "pattern_analysis",
            "causal_reasoning",
            "analogical_reasoning",
            "mathematical_reasoning",
            "answer_synthesis"
        ]


@dataclass
class Evidence:
    """证据"""
    content: str
    source: str
    confidence: float
    relevance_score: float
    evidence_type: str
    metadata: Dict[str, Any]


@dataclass
class ReasoningStep:
    """推理步骤"""
    step_id: int
    step_type: ReasoningStepType
    description: str
    input_evidence: List[Evidence]
    output_evidence: List[Evidence]
    reasoning_process: str
    confidence: float
    timestamp: float


@dataclass
class ReasoningResult:
    """推理结果"""
    final_answer: str
    reasoning_steps: List[ReasoningStep]
    total_confidence: float
    evidence_chain: List[Evidence]
    reasoning_type: str
    processing_time: float
    success: bool
    answer_source: Optional[str] = None  # 🚀 P1新增：答案来源标记（"knowledge_base", "reasoning_steps", "llm_internal_knowledge"）
    answer_source_details: Optional[Dict[str, Any]] = None  # 🚀 P1新增：答案来源详细信息
    warnings: Optional[List[str]] = None  # 🚀 P2新增：非致命警告信息收集

