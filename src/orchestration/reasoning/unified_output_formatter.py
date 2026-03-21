"""
统一输出格式器 - 统一处理所有模板的输出格式
"""
import logging
import re
import json
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class UnifiedOutputFormatter:
    """统一输出格式器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def format(
        self,
        response: str,
        template_used: str,
        evidence_quality: Optional[str] = None,
        query_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """统一格式化输出
        
        Args:
            response: LLM原始响应
            template_used: 使用的模板名称
            evidence_quality: 证据质量（high/medium/low/none）
            query_type: 查询类型
            
        Returns:
            统一格式的输出字典
        """
        try:
            # 提取答案
            answer_content = self._extract_final_answer(response)
            answer_format = self._detect_answer_format(answer_content, query_type)
            
            # 提取置信度
            confidence = self._extract_confidence(response)
            
            # 提取推理步骤（如果有）
            reasoning_steps = self._extract_reasoning_steps(response)
            
            # 构建统一输出
            formatted_output = {
                "metadata": {
                    "template_used": template_used,
                    "template_version": "2.0",
                    "timestamp": datetime.now().isoformat()
                },
                "reasoning": {
                    "steps": reasoning_steps,
                    "confidence": confidence,
                    "evidence_quality": evidence_quality or "none"
                },
                "answer": {
                    "content": answer_content,
                    "format": answer_format,
                    "validation_status": "unverified"  # 默认未验证，后续可以添加验证逻辑
                }
            }
            
            return formatted_output
            
        except Exception as e:
            self.logger.error(f"格式化输出失败: {e}")
            # 返回最小可用格式
            return {
                "metadata": {
                    "template_used": template_used,
                    "template_version": "2.0",
                    "timestamp": datetime.now().isoformat()
                },
                "reasoning": {
                    "steps": [],
                    "confidence": {"score": 0.5, "level": "medium"},
                    "evidence_quality": evidence_quality or "none"
                },
                "answer": {
                    "content": response[:200] if response else "",
                    "format": "text",
                    "validation_status": "unverified"
                }
            }
    
    def _extract_final_answer(self, response: str) -> str:
        """🚀 P0修复：提取最终答案，避免提取单个常见词（如"The"）"""
        if not response:
            return ""
        
        # 优先提取标准格式的答案
        final_answer_patterns = [
            r'---\s*\n\s*Final Answer[：:]\s*([^\n]+)',
            r'Final Answer[：:]\s*([^\n]+)',
            r'最终答案[：:]\s*([^\n]+)',
            r'---\s*\n\s*FINAL ANSWER[：:]\s*([^\n]+)',
            r'FINAL ANSWER[：:]\s*([^\n]+)',
        ]
        
        for pattern in final_answer_patterns:
            match = re.search(pattern, response, re.IGNORECASE | re.MULTILINE)
            if match:
                answer = match.group(1).strip()
                # 清理答案（移除可能的标记）
                answer = re.sub(r'^[-*•]\s*', '', answer)
                
                # 🚀 P0修复：验证答案不是单个常见词
                answer_words = answer.split()
                if len(answer_words) == 1:
                    single_word = answer_words[0].lower()
                    incomplete_words = ['the', 'a', 'an', 'this', 'that', 'these', 'those', 'it', 'is', 'was', 'are', 'were']
                    if single_word in incomplete_words:
                        # 单个常见词，可能是提取错误，继续查找其他模式
                        continue
                
                if answer:
                    return answer
        
        # 如果没有找到标准格式，尝试从JSON中提取
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                if isinstance(parsed, dict):
                    # 尝试多种可能的字段名
                    for key in ['final_answer', 'answer', 'result', 'content']:
                        if key in parsed:
                            answer = str(parsed[key]).strip()
                            # 🚀 P0修复：验证答案不是单个常见词
                            answer_words = answer.split()
                            if len(answer_words) == 1:
                                single_word = answer_words[0].lower()
                                incomplete_words = ['the', 'a', 'an', 'this', 'that', 'these', 'those', 'it', 'is', 'was', 'are', 'were']
                                if single_word in incomplete_words:
                                    # 单个常见词，可能是提取错误，继续查找
                                    continue
                            if answer:
                                return answer
        except (json.JSONDecodeError, KeyError):
            pass
        
        # 🚀 P0修复：如果没有找到标准格式，尝试提取第一句话（但避免单个常见词）
        # 提取第一句话
        sentences = re.split(r'[.!?。！？]\s+', response)
        if sentences:
            first_sentence = sentences[0].strip()
            # 验证不是单个常见词
            first_words = first_sentence.split()
            if len(first_words) > 1 or (len(first_words) == 1 and first_words[0].lower() not in ['the', 'a', 'an', 'this', 'that', 'these', 'those', 'it', 'is', 'was', 'are', 'were']):
                if len(first_sentence) > 3:  # 至少4个字符
                    return first_sentence
        
        # 如果都没有找到，返回空字符串
        return ""
    
    def _extract_confidence(self, response: str) -> Dict[str, Any]:
        """提取置信度（统一格式）"""
        # 默认置信度
        default_confidence = {"score": 0.7, "level": "medium"}
        
        if not response:
            return default_confidence
        
        # 尝试从文本中提取置信度
        confidence_patterns = [
            r'confidence[：:]\s*(high|medium|low)',
            r'置信度[：:]\s*(高|中|低)',
            r'"confidence"[：:]\s*([0-9.]+)',
            r'"confidence"[：:]\s*"([^"]+)"',
        ]
        
        for pattern in confidence_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                value = match.group(1).lower()
                
                # 处理文本格式
                if value in ['high', '高']:
                    return {"score": 0.9, "level": "high"}
                elif value in ['medium', '中']:
                    return {"score": 0.7, "level": "medium"}
                elif value in ['low', '低']:
                    return {"score": 0.3, "level": "low"}
                
                # 处理数值格式
                try:
                    score = float(value)
                    if 0.0 <= score <= 1.0:
                        if score > 0.8:
                            level = "high"
                        elif score > 0.5:
                            level = "medium"
                        else:
                            level = "low"
                        return {"score": score, "level": level}
                except ValueError:
                    pass
        
        # 尝试从JSON中提取
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                if isinstance(parsed, dict):
                    # 检查是否有置信度字段
                    if 'confidence' in parsed:
                        conf = parsed['confidence']
                        if isinstance(conf, dict):
                            # 已经是统一格式
                            if 'score' in conf and 'level' in conf:
                                return conf
                        elif isinstance(conf, (int, float)):
                            # 数值格式
                            score = float(conf)
                            if score > 0.8:
                                level = "high"
                            elif score > 0.5:
                                level = "medium"
                            else:
                                level = "low"
                            return {"score": score, "level": level}
                        elif isinstance(conf, str):
                            # 文本格式
                            conf_lower = conf.lower()
                            if conf_lower in ['high', '高']:
                                return {"score": 0.9, "level": "high"}
                            elif conf_lower in ['medium', '中']:
                                return {"score": 0.7, "level": "medium"}
                            elif conf_lower in ['low', '低']:
                                return {"score": 0.3, "level": "low"}
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
        
        return default_confidence
    
    def _extract_reasoning_steps(self, response: str) -> list:
        """提取推理步骤"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                if isinstance(parsed, dict) and 'steps' in parsed:
                    return parsed['steps']
                elif isinstance(parsed, list):
                    return parsed
        except (json.JSONDecodeError, KeyError):
            pass
        
        return []
    
    def _detect_answer_format(self, answer: str, query_type: Optional[str] = None) -> str:
        """检测答案格式"""
        if not answer:
            return "text"
        
        # 基于查询类型判断
        if query_type:
            type_mapping = {
                'numerical': 'numerical',
                'mathematical': 'numerical',
                'ranking': 'ranking',
                'name': 'name',
                'person': 'name',
                'location': 'location',
                'country': 'location'
            }
            if query_type in type_mapping:
                return type_mapping[query_type]
        
        # 基于答案内容判断
        answer_clean = answer.strip()
        
        # 检查是否是数字
        if re.match(r'^-?\d+(\.\d+)?$', answer_clean):
            return "numerical"
        
        # 检查是否是序数
        if re.match(r'^\d+(st|nd|rd|th)$', answer_clean, re.IGNORECASE):
            return "ranking"
        
        # 检查是否是姓名（包含空格，首字母大写）
        if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+', answer_clean):
            return "name"
        
        # 默认返回文本
        return "text"

