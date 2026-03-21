#!/usr/bin/env python3
"""
响应生成器 - 生成用户响应的核心工具
"""

import logging
import time
import json
import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ResponseType(Enum):
    """响应类型枚举"""
    ANSWER = "answer"
    EXPLANATION = "explanation"
    SUGGESTION = "suggestion"
    ERROR = "error"
    CONFIRMATION = "confirmation"
    QUESTION = "question"
    TEXT = "text"

class ResponseTone(Enum):
    """响应语调枚举"""
    FORMAL = "formal"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    TECHNICAL = "technical"
    NEUTRAL = "neutral"

@dataclass
class ResponseContext:
    """响应上下文数据类"""
    query_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    response_type: ResponseType = ResponseType.ANSWER
    tone: ResponseTone = ResponseTone.FRIENDLY
    include_examples: bool = False
    include_references: bool = False
    max_length: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class GeneratedResponse:
    """生成响应数据类"""
    response_id: str
    content: str
    response_type: ResponseType
    tone: ResponseTone
    confidence: float
    generation_time: float
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ResponseGenerator:
    """响应生成器 - AI增强版"""
    
    def __init__(self):
        """初始化响应生成器"""
        self.generation_history = []
        self.performance_metrics = {
            "total_responses": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "average_generation_time": 0.0,
            "response_type_distribution": {},
            "tone_distribution": {}
        }
        self.templates = self._load_response_templates()
        self.initialized = True
        logger.info("响应生成器初始化完成")
    
    def generate_response(self, 
                         result: Any, 
                         context: ResponseContext) -> GeneratedResponse:
        """生成响应 - AI增强版"""
        try:
            # 验证输入
            if not self._validate_generation_input(result, context):
                return self._create_error_response("Invalid generation input")
            
            start_time = time.time()
            
            # 分析结果
            analysis = self._analyze_result(result)
            
            # 选择响应模板
            template = self._select_template(context, analysis)
            
            # 生成响应内容
            response_content = self._generate_response_content(result, context, template, analysis)
            
            # 后处理响应
            final_response = self._postprocess_response(response_content, context, analysis)
            
            # 更新性能指标
            self._update_performance_metrics(start_time, True)
            
            # 记录生成历史
            self._record_generation_history(result, context, final_response)
            
            return final_response
            
        except Exception as e:
            logger.error(f"响应生成失败: {e}")
            self._update_performance_metrics(time.time(), False)
            return self._create_error_response(f"Response generation failed: {e}")
    
    def _validate_generation_input(self, result: Any, context: ResponseContext) -> bool:
        """验证生成输入"""
        if result is None:
            return False
        
        if not isinstance(context, ResponseContext):
            return False
        
        return True
    
    def _generate_response_content(self, result: Any, context: ResponseContext, template: str, analysis: Dict[str, Any]) -> str:
        """生成响应内容"""
        try:
            # 根据模板类型生成内容
            if template == "structured":
                return self._generate_structured_response(result, context, analysis)
            elif template == "narrative":
                return self._generate_narrative_response(result, context, analysis)
            elif template == "technical":
                return self._generate_technical_response(result, context, analysis)
            else:
                return self._generate_default_response(result, context, analysis)
                
        except Exception as e:
            logger.error(f"响应内容生成失败: {e}")
            return str(result)
    
    def _generate_structured_response(self, result: Any, context: ResponseContext, analysis: Dict[str, Any]) -> str:
        """生成结构化响应"""
        if isinstance(result, dict):
            response = "## 分析结果\n\n"
            for key, value in result.items():
                response += f"**{key}**: {value}\n\n"
            return response
        else:
            return f"## 结果\n\n{result}"
    
    def _generate_narrative_response(self, result: Any, context: ResponseContext, analysis: Dict[str, Any]) -> str:
        """生成叙述性响应"""
        query_type = context.metadata.get('query_type', 'general') if context.metadata else 'general'
        return f"根据分析，{result}。这个结果基于{query_type}类型的查询，置信度为{analysis.get('confidence', 0.8):.2f}。"
    
    def _generate_technical_response(self, result: Any, context: ResponseContext, analysis: Dict[str, Any]) -> str:
        """生成技术性响应"""
        return f"技术分析结果：\n```\n{result}\n```\n\n技术指标：\n- 复杂度: {analysis.get('complexity', 'unknown')}\n- 置信度: {analysis.get('confidence', 0.8):.2f}"
    
    def _generate_default_response(self, result: Any, context: ResponseContext, analysis: Dict[str, Any]) -> str:
        """生成默认响应"""
        return str(result)
    
    def _postprocess_response(self, response_content: str, context: ResponseContext, analysis: Dict[str, Any]) -> GeneratedResponse:
        """后处理响应"""
        try:
            # 添加元数据
            metadata = {
                'generated_at': time.time(),
                'template_used': analysis.get('template', 'default'),
                'confidence': analysis.get('confidence', 0.8),
                'tone': context.tone.value if hasattr(context.tone, 'value') else str(context.tone)
            }
            
            return GeneratedResponse(
                response_id=f"resp_{int(time.time())}_{hash(response_content) % 10000}",
                content=response_content,
                response_type=context.response_type,
                tone=context.tone,
                confidence=0.8,
                generation_time=time.time(),
                metadata=metadata
            )
            
        except Exception as e:
            logger.warning(f"响应后处理失败: {e}")
            return GeneratedResponse(
                response_id=f"resp_error_{int(time.time())}_{hash(response_content) % 10000}",
                content=response_content,
                response_type=context.response_type,
                tone=context.tone,
                confidence=0.5,
                generation_time=time.time(),
                metadata={'error': str(e)}
            )
    
    def _update_performance_metrics(self, start_time: float, success: bool):
        """更新性能指标"""
        end_time = time.time()
        generation_time = end_time - start_time
        
        self.performance_metrics["total_responses"] += 1
        
        if success:
            self.performance_metrics["successful_responses"] += 1
        else:
            self.performance_metrics["failed_responses"] += 1
        
        # 更新平均生成时间
        total = self.performance_metrics["total_responses"]
        current_avg = self.performance_metrics["average_generation_time"]
        self.performance_metrics["average_generation_time"] = (
            (current_avg * (total - 1) + generation_time) / total
        )
    
    def _record_generation_history(self, result: Any, context: ResponseContext, response: GeneratedResponse):
        """记录生成历史"""
        self.generation_history.append({
            'timestamp': time.time(),
            'result_type': type(result).__name__,
            'response_type': context.response_type.value if hasattr(context.response_type, 'value') else str(context.response_type),
            'tone': context.tone.value if hasattr(context.tone, 'value') else str(context.tone),
            'success': True
        })
        
        # 保持历史记录在合理范围内
        if len(self.generation_history) > 1000:
            self.generation_history = self.generation_history[-1000:]
    
    def _create_error_response(self, error_message: str) -> GeneratedResponse:
        """创建错误响应"""
        return GeneratedResponse(
            response_id=f"resp_error_{int(time.time())}_{hash(error_message) % 10000}",
            content=f"Error: {error_message}",
            response_type=ResponseType.TEXT,
            tone=ResponseTone.NEUTRAL,
            confidence=0.0,
            generation_time=time.time(),
            metadata={'error': True, 'message': error_message, 'timestamp': time.time()}
        )
    
    def _analyze_result(self, result: Any) -> Dict[str, Any]:
        """分析结果"""
        analysis = {
            "result_type": type(result).__name__,
            "complexity": "simple",
            "has_error": False,
            "key_points": [],
            "suggestions": []
        }
        
        if isinstance(result, dict):
            if "error" in result or "has_error" in result:
                analysis["has_error"] = True
                analysis["complexity"] = "error"
            
            # 提取关键点
            for key, value in result.items():
                if key in self._get_key_point_keys():
                    analysis["key_points"].append(str(value))
                elif key in self._get_suggestion_keys():
                    if isinstance(value, list):
                        analysis["suggestions"].extend(value)
                    else:
                        analysis["suggestions"].append(str(value))
        
        return analysis
    
    def _select_template(self, context: ResponseContext, analysis: Dict[str, Any]) -> str:
        """选择响应模板"""
        template_key = f"{context.response_type.value}_{context.tone.value}"
        
        if template_key in self.templates:
            return self.templates[template_key]
        elif context.response_type.value in self.templates:
            return self.templates[context.response_type.value]
        else:
            return self.templates["default"]
    
    def _generate_content(self, 
                         result: Any, 
                         context: ResponseContext, 
                         template: str, 
                         analysis: Dict[str, Any]) -> str:
        """生成响应内容"""
        if analysis["has_error"]:
            return "抱歉，处理过程中发生错误。"
        
        # 生成答案响应
        if isinstance(result, dict) and "response" in result:
            return str(result["response"])
        elif isinstance(result, dict) and "answer" in result:
            return str(result["answer"])
        
        # 生成解释响应
        explanation_parts = []
        
        if isinstance(result, dict):
            if "response" in result:
                explanation_parts.append(f"根据分析，{result['response']}")
            
            if "analysis" in result:
                explanation_parts.append(f"详细分析：{result['analysis']}")
            
            if "steps" in result:
                explanation_parts.append("处理步骤：")
                for i, step in enumerate(result["steps"], 1):
                    explanation_parts.append(f"{i}. {step}")
            
            if explanation_parts:
                return "\n".join(explanation_parts)
        
        # 生成默认响应
        return str(result)
    
    def _apply_tone(self, content: str, tone: ResponseTone) -> str:
        """应用语调"""
        if tone == ResponseTone.FORMAL:
            return content.replace("你", "您").replace("的", "的")
        elif tone == ResponseTone.CASUAL:
            return content.replace("您", "你")
        elif tone == ResponseTone.FRIENDLY:
            return f"😊 {content}"
        elif tone == ResponseTone.PROFESSIONAL:
            return f"【专业建议】{content}"
        elif tone == ResponseTone.TECHNICAL:
            return f"技术说明：{content}"
        else:
            return content
    
    def _apply_length_limit(self, content: str, max_length: int) -> str:
        """应用长度限制"""
        if len(content) <= max_length:
            return content
        return content[:max_length-3] + "..."
    
    def _add_examples(self, content: str, examples: Any) -> str:
        """添加示例"""
        if examples:
            if isinstance(examples, list):
                example_text = "\n\n示例：\n" + "\n".join(f"- {ex}" for ex in examples)
                return content + example_text
        return content
    
    def _add_references(self, content: str, result: Any) -> str:
        """添加引用"""
        if isinstance(result, dict) and "sources" in result:
            sources = result["sources"]
            if isinstance(sources, list):
                ref_text = "\n\n参考来源：\n" + "\n".join(f"- {src}" for src in sources)
                return content + ref_text
        return content
    
    def _calculate_confidence(self, result: Any, content: str) -> float:
        """计算置信度"""
        base_confidence = float(os.getenv("DEFAULT_CONFIDENCE", "0.5"))
        
        if isinstance(result, dict):
            if "confidence" in result:
                base_confidence = float(result["confidence"])
            elif "success" in result and result["success"]:
                base_confidence = float(os.getenv("HIGH_CONFIDENCE", "0.8"))
            elif "error" in result:
                base_confidence = 0.2
        
        # 基于内容长度调整置信度
        min_length = int(os.getenv("MIN_CONTENT_LENGTH", "20"))
        if len(content) < min_length:
            base_confidence = max(base_confidence - 0.1, 0.0)
        
        return base_confidence
    
    def _load_response_templates(self) -> Dict[str, str]:
        """加载响应模板"""
        return {
            "default": "{{content}}",
            "answer": "根据您的问题，{{content}}",
            "explanation": "让我为您详细解释：{{content}}",
            "suggestion": "基于分析，我建议：{{content}}",
            "confirmation": "{{content}}",
            "question": "{{content}}",
            "answer_friendly": "😊 根据您的问题，{{content}}",
            "explanation_professional": "【专业解释】{{content}}",
            "suggestion_casual": "建议：{{content}}"
        }
    
    def _update_metrics(self, generated_response: GeneratedResponse):
        """更新性能指标"""
        self.performance_metrics["total_responses"] += 1
        
        if generated_response.response_type != ResponseType.ERROR:
            self.performance_metrics["successful_responses"] += 1
        else:
            self.performance_metrics["failed_responses"] += 1
        
        # 更新平均生成时间
        total_responses = self.performance_metrics["total_responses"]
        current_avg = self.performance_metrics["average_generation_time"]
        self.performance_metrics["average_generation_time"] = (
            (current_avg * (total_responses - 1) + generated_response.generation_time) / total_responses
        )
        
        # 更新响应类型分布
        response_type = generated_response.response_type.value
        if response_type not in self.performance_metrics["response_type_distribution"]:
            self.performance_metrics["response_type_distribution"][response_type] = 0
        self.performance_metrics["response_type_distribution"][response_type] += 1
        
        # 更新语调分布
        tone = generated_response.tone.value
        if tone not in self.performance_metrics["tone_distribution"]:
            self.performance_metrics["tone_distribution"][tone] = 0
        self.performance_metrics["tone_distribution"][tone] += 1
    
    def _get_key_point_keys(self) -> List[str]:
        """获取关键点键列表"""
        return ["response", "answer", "result", "solution"]
    
    def _get_suggestion_keys(self) -> List[str]:
        """获取建议键列表"""
        return ["suggestions", "recommendations"]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.performance_metrics.copy()
    
    def get_generation_history(self, limit: Optional[int] = None) -> List[GeneratedResponse]:
        """获取生成历史"""
        if limit:
            return self.generation_history[-limit:]
        return self.generation_history


# 全局实例
response_generator = ResponseGenerator()


def get_response_generator() -> ResponseGenerator:
    """获取响应生成器实例"""
    return response_generator