#!/usr/bin/env python3
"""
NLP引擎 - 提供自然语言处理功能
"""
import os
import re
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from src.utils.unified_centers import get_unified_config_center


@dataclass
class SentimentResult:
    """情感分析结果"""
    sentiment: str
    confidence: float
    scores: Dict[str, float]


@dataclass
class NERResult:
    """命名实体识别结果"""
    entities: List[Dict[str, Any]]
    confidence: float


@dataclass
class TextAnalysisResult:
    """文本分析结果"""
    sentiment: SentimentResult
    entities: NERResult
    keywords: List[str]
    summary: str
    confidence: float


class NLPEngine:
    """NLP引擎"""
    
    def __init__(self):
        """初始化NLP引擎"""
        self.logger = logging.getLogger(__name__)
        self.recent_analyses: List[Dict[str, Any]] = []
        
        # 情感词典
        self.positive_words = {
            "好", "棒", "优秀", "完美", "喜欢", "爱", "满意", "高兴", "开心", "快乐",
            "great", "good", "excellent", "perfect", "love", "like", "happy", "joy"
        }
        
        self.negative_words = {
            "坏", "差", "糟糕", "讨厌", "恨", "不满", "生气", "愤怒", "悲伤", "痛苦",
            "bad", "terrible", "awful", "hate", "angry", "sad", "pain", "disappointed"
        }
        
        # 实体模式
        self.entity_patterns = {
            "PERSON": r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            "ORG": r'\b[A-Z][a-z]+ (?:Inc|Corp|LLC|Ltd|Company|Corporation)\b',
            "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "PHONE": r'\b\d{3}-\d{3}-\d{4}\b',
            "URL": r'https?://[^\s]+'
        }
        
        self.logger.info("NLP引擎初始化完成")
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        """分析情感"""
        try:
            words = text.lower().split()
            
            # 计算情感分数
            positive_score = sum(1 for word in words if word in self.positive_words)
            negative_score = sum(1 for word in words if word in self.negative_words)
            
            # 计算置信度
            total_sentiment_words = positive_score + negative_score
            if total_sentiment_words == 0:
                sentiment = "neutral"
                confidence = float(os.getenv("DEFAULT_CONFIDENCE", "0.5"))
            elif positive_score > negative_score:
                sentiment = "positive"
                confidence = positive_score / total_sentiment_words
            elif negative_score > positive_score:
                sentiment = "negative"
                confidence = negative_score / total_sentiment_words
            else:
                sentiment = "neutral"
                confidence = float(os.getenv("DEFAULT_CONFIDENCE", "0.5"))
            
            scores = {
                "positive": float(positive_score),
                "negative": float(negative_score),
                "neutral": float(max(0, total_sentiment_words - positive_score - negative_score))
            }
            
            return SentimentResult(
                sentiment=sentiment,
                confidence=confidence,
                scores=scores
            )
            
        except Exception as e:
            self.logger.error(f"情感分析失败: {e}")
            return SentimentResult(
                sentiment="neutral",
                confidence=0.0,
                scores={"positive": 0.0, "negative": 0.0, "neutral": 1.0}
            )
    
    def extract_entities(self, text: str) -> NERResult:
        """命名实体识别"""
        try:
            entities = []
            
            # 使用正则表达式提取实体
            for entity_type, pattern in self.entity_patterns.items():
                matches = re.finditer(pattern, text)
                for match in matches:
                    entities.append({
                        "text": match.group(),
                        "label": entity_type,
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.8
                    })
            
            # 简化的置信度计算
            confidence = min(0.9, len(entities) * 0.1 + 0.5)
            
            return NERResult(
                entities=entities,
                confidence=confidence
            )
            
        except Exception as e:
            self.logger.error(f"实体识别失败: {e}")
            return NERResult(
                entities=[],
                confidence=0.0
            )
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """提取关键词"""
        try:
            # 简化的关键词提取
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            
            # 过滤停用词
            stop_words = {
                "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
                "by", "is", "are", "was", "were", "be", "been", "have", "has", "had",
                "do", "does", "did", "will", "would", "could", "should", "may", "might"
            }
            
            filtered_words = [word for word in words if word not in stop_words]
            
            # 计算词频
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # 按频率排序并返回前N个
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            keywords = [word for word, freq in sorted_words[:max_keywords]]
            
            return keywords
            
        except Exception as e:
            self.logger.error(f"关键词提取失败: {e}")
            return []
    
    def generate_summary(self, text: str, max_sentences: int = 3) -> str:
        """生成摘要 - 增强版"""
        try:
            if not text or not text.strip():
                return ""
            
            # 1. 文本预处理
            cleaned_text = self._preprocess_text_for_summarization(text)
            
            # 2. 句子分割和清理
            sentences = self._split_into_sentences(cleaned_text)
            
            if not sentences:
                return ""
            
            # 3. 句子评分
            sentence_scores = self._score_sentences(sentences)
            
            # 4. 选择最佳句子
            selected_sentences = self._select_best_sentences(sentences, sentence_scores, max_sentences)
            
            # 5. 重新排序句子（保持原文顺序）
            ordered_sentences = self._reorder_sentences(sentences, selected_sentences)
            
            # 6. 生成最终摘要
            summary = self._format_summary(ordered_sentences)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"摘要生成失败: {e}")
            return ""
    
    def _preprocess_text_for_summarization(self, text: str) -> str:
        """为摘要预处理文本"""
        try:
            if not text or not text.strip():
                return ""
            
            # 移除多余的空白字符
            text = re.sub(r'\s+', ' ', text.strip())
            
            # 移除HTML标签
            text = re.sub(r'<[^>]+>', '', text)
            
            # 移除URL链接
            text = re.sub(r'https?://\S+', '', text)
            
            # 移除邮箱地址
            text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
            
            # 移除特殊字符和符号，但保留基本标点
            text = re.sub(r'[^\w\s.,!?;:()"\'-]', '', text)
            
            # 标准化标点符号
            text = re.sub(r'[.]{2,}', '.', text)
            text = re.sub(r'[!]{2,}', '!', text)
            text = re.sub(r'[?]{2,}', '?', text)
            text = re.sub(r'[,]{2,}', ',', text)
            
            # 移除多余的引号
            text = re.sub(r'["\']{2,}', '"', text)
            
            # 清理多余的空白
            text = re.sub(r'\s+', ' ', text)
            
            # 确保句子以标点结尾
            if text and not re.search(r'[.!?]$', text.strip()):
                text = text.strip() + '.'
            
            return text.strip()
            
        except Exception as e:
            self.logger.warning(f"文本预处理失败: {e}")
            return text
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """将文本分割成句子"""
        try:
            # 使用更精确的句子分割
            sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
            sentences = re.split(sentence_pattern, text)
            
            # 清理和过滤句子
            cleaned_sentences = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 10:  # 过滤太短的句子
                    cleaned_sentences.append(sentence)
            
            return cleaned_sentences
            
        except Exception as e:
            self.logger.warning(f"句子分割失败: {e}")
            return [text]
    
    def _score_sentences(self, sentences: List[str]) -> List[float]:
        """为句子评分"""
        try:
            scores = []
            
            for sentence in sentences:
                score = 0.0
                
                # 1. 长度评分（中等长度的句子得分更高）
                length_score = self._calculate_length_score(sentence)
                score += length_score * 0.2
                
                # 2. 关键词评分
                keyword_score = self._calculate_keyword_score(sentence)
                score += keyword_score * 0.3
                
                # 3. 位置评分（开头和结尾的句子得分更高）
                position_score = self._calculate_position_score(sentence, sentences)
                score += position_score * 0.2
                
                # 4. 可读性评分
                readability_score = self._calculate_readability_score(sentence)
                score += readability_score * 0.2
                
                # 5. 信息密度评分
                density_score = self._calculate_information_density(sentence)
                score += density_score * 0.1
                
                scores.append(score)
            
            return scores
            
        except Exception as e:
            self.logger.warning(f"句子评分失败: {e}")
            return [0.5] * len(sentences)
    
    def _calculate_length_score(self, sentence: str) -> float:
        """计算长度评分"""
        try:
            if not sentence or not sentence.strip():
                return 0.0
            
            words = sentence.split()
            word_count = len(words)
            char_count = len(sentence)
            
            # 基于词数的评分
            if word_count < 3:
                word_score = 0.1  # 太短
            elif 3 <= word_count < 8:
                word_score = 0.3  # 较短
            elif 8 <= word_count < 15:
                word_score = 0.6  # 中等偏短
            elif 15 <= word_count <= 30:
                word_score = 1.0  # 理想长度
            elif 30 < word_count <= 50:
                word_score = 0.8  # 较长但可接受
            elif 50 < word_count <= 80:
                word_score = 0.5  # 太长
            else:
                word_score = 0.2  # 非常长
            
            # 基于字符数的评分
            config_center = get_unified_config_center()
            if char_count < 20:
                char_score = 0.1
            elif 20 <= char_count < 50:
                char_score = 0.4
            elif 50 <= char_count <= (config_center.get_config_value('system', 'medium_text_length', 150) if config_center else 150):
                char_score = 1.0
            elif (config_center.get_config_value('system', 'medium_text_length', 150) if config_center else 150) < char_count <= 300:
                char_score = 0.7
            elif 300 < char_count <= (config_center.get_config_value('system', 'long_text_length', 500) if config_center else 500):
                char_score = 0.4
            else:
                char_score = 0.2
            
            # 综合评分（词数和字符数各占50%）
            final_score = (word_score * 0.6 + char_score * 0.4)
            
            return min(max(final_score, 0.0), 1.0)
                
        except Exception as e:
            self.logger.warning(f"长度评分计算失败: {e}")
            return 0.5
    
    def _calculate_keyword_score(self, sentence: str) -> float:
        """计算关键词评分"""
        try:
            # 定义重要关键词
            important_keywords = [
                'important', 'significant', 'key', 'main', 'primary', 'essential',
                'critical', 'crucial', 'vital', 'fundamental', 'core', 'central',
                'conclusion', 'summary', 'result', 'finding', 'discovery', 'analysis'
            ]
            
            sentence_lower = sentence.lower()
            keyword_count = sum(1 for keyword in important_keywords if keyword in sentence_lower)
            
            # 归一化评分
            max_keywords = 3
            return min(keyword_count / max_keywords, 1.0)
            
        except Exception as e:
            self.logger.warning(f"关键词评分计算失败: {e}")
            return 0.5
    
    def _calculate_position_score(self, sentence: str, all_sentences: List[str]) -> float:
        """计算位置评分"""
        try:
            if not all_sentences or not sentence:
                return 0.5
            
            try:
                sentence_index = all_sentences.index(sentence)
            except ValueError:
                # 如果找不到句子，返回中等分数
                return 0.5
            
            total_sentences = len(all_sentences)
            
            if total_sentences <= 1:
                return 1.0
            
            # 计算相对位置
            relative_position = sentence_index / (total_sentences - 1)
            
            # 位置评分策略
            if sentence_index == 0:  # 第一句 - 通常包含主题
                position_score = 1.0
            elif sentence_index == total_sentences - 1:  # 最后一句 - 通常包含结论
                position_score = 0.9
            elif relative_position < 0.1:  # 前10% - 引言部分
                position_score = 0.8
            elif relative_position > 0.9:  # 后10% - 结论部分
                position_score = 0.7
            elif relative_position < 0.2:  # 前20% - 重要信息
                position_score = 0.6
            elif relative_position > 0.8:  # 后20% - 重要信息
                position_score = 0.6
            elif 0.3 <= relative_position <= 0.7:  # 中间部分
                position_score = 0.4
            else:  # 其他位置
                position_score = 0.3
            
            # 考虑段落结构（如果有的话）
            # 这里可以添加更复杂的段落分析逻辑
            
            return min(max(position_score, 0.0), 1.0)
                
        except Exception as e:
            self.logger.warning(f"位置评分计算失败: {e}")
            return 0.5
    
    def _calculate_readability_score(self, sentence: str) -> float:
        """计算可读性评分"""
        try:
            if not sentence or not sentence.strip():
                return 0.0
            
            words = sentence.split()
            if not words:
                return 0.0
            
            # 计算平均词长
            avg_word_length = sum(len(word) for word in words) / len(words)
            
            # 计算句子长度
            sentence_length = len(words)
            
            # 计算音节数（简化版）
            syllable_count = 0
            for word in words:
                # 简化的音节计算：每个元音字母算一个音节
                vowels = 'aeiouAEIOU'
                syllables = sum(1 for char in word if char in vowels)
                syllable_count += max(1, syllables)  # 至少一个音节
            
            avg_syllables_per_word = syllable_count / len(words) if words else 0
            
            # 计算句子复杂度
            complexity_indicators = ['and', 'or', 'but', 'however', 'therefore', 'because', 'although', 'while', 'since', 'unless']
            complexity_count = sum(1 for word in words if word.lower() in complexity_indicators)
            
            # 计算标点符号复杂度
            punctuation_count = len([char for char in sentence if char in '.,;:!?()[]{}"'])
            punctuation_ratio = punctuation_count / len(sentence) if sentence else 0
            
            # 计算数字和特殊字符比例
            special_chars = len([char for char in sentence if char.isdigit() or char in '@#$%^&*+='])
            special_ratio = special_chars / len(sentence) if sentence else 0
            
            # 综合可读性评分
            readability_score = 1.0
            
            # 词长评分（4-6个字母为最佳）
            if avg_word_length < 3:
                readability_score *= 0.8  # 太短可能不完整
            elif 3 <= avg_word_length <= 6:
                readability_score *= 1.0  # 理想长度
            elif 6 < avg_word_length <= 8:
                readability_score *= 0.8  # 稍长
            elif 8 < avg_word_length <= 10:
                readability_score *= 0.6  # 较长
            else:
                readability_score *= 0.4  # 太长
            
            # 句子长度评分（10-20个词为最佳）
            if sentence_length < 5:
                readability_score *= 0.7  # 太短
            elif 5 <= sentence_length <= 20:
                readability_score *= 1.0  # 理想长度
            elif 20 < sentence_length <= 30:
                readability_score *= 0.8  # 稍长
            elif 30 < sentence_length <= 50:
                readability_score *= 0.6  # 较长
            else:
                readability_score *= 0.4  # 太长
            
            # 音节复杂度评分
            if avg_syllables_per_word < 1.5:
                readability_score *= 1.0  # 简单
            elif 1.5 <= avg_syllables_per_word <= 2.5:
                readability_score *= 0.9  # 中等
            elif 2.5 < avg_syllables_per_word <= 3.5:
                readability_score *= 0.7  # 复杂
            else:
                readability_score *= 0.5  # 很复杂
            
            # 连接词复杂度评分
            if complexity_count == 0:
                readability_score *= 1.0  # 简单
            elif complexity_count == 1:
                readability_score *= 0.9  # 稍复杂
            elif complexity_count == 2:
                readability_score *= 0.8  # 复杂
            else:
                readability_score *= 0.6  # 很复杂
            
            # 标点符号复杂度评分
            if punctuation_ratio < 0.05:
                readability_score *= 1.0  # 简单
            elif punctuation_ratio < 0.1:
                readability_score *= 0.9  # 稍复杂
            elif punctuation_ratio < 0.2:
                readability_score *= 0.8  # 复杂
            else:
                readability_score *= 0.6  # 很复杂
            
            # 特殊字符评分
            if special_ratio < 0.05:
                readability_score *= 1.0  # 正常
            else:
                readability_score *= 0.8  # 包含特殊字符
            
            return min(max(readability_score, 0.0), 1.0)
                
        except Exception as e:
            self.logger.warning(f"可读性评分计算失败: {e}")
            return 0.5
    
    def _calculate_information_density(self, sentence: str) -> float:
        """计算信息密度评分"""
        try:
            words = sentence.split()
            if not words:
                return 0.0
            
            # 计算名词、动词、形容词的比例
            content_words = []
            for word in words:
                # 简单的词性判断（实际应用中可以使用NLP库）
                if len(word) > 3 and not word.lower() in ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']:
                    content_words.append(word)
            
            density = len(content_words) / len(words)
            return min(density, 1.0)
            
        except Exception as e:
            self.logger.warning(f"信息密度计算失败: {e}")
            return 0.5
    
    def _select_best_sentences(self, sentences: List[str], scores: List[float], max_sentences: int) -> List[str]:
        """选择最佳句子"""
        try:
            if not sentences or not scores:
                return []
            
            if len(sentences) <= max_sentences:
                return sentences
            
            # 确保分数和句子数量匹配
            if len(sentences) != len(scores):
                self.logger.warning("句子和分数数量不匹配")
                return sentences[:max_sentences]
            
            # 创建句子-分数对
            sentence_score_pairs = list(zip(sentences, scores))
            
            # 按分数排序
            sentence_score_pairs.sort(key=lambda x: x[1], reverse=True)
            
            # 选择策略：确保多样性
            selected_sentences = []
            selected_indices = set()
            
            # 首先选择分数最高的句子
            for sentence, score in sentence_score_pairs:
                if len(selected_sentences) >= max_sentences:
                    break
                
                # 检查是否已经选择过
                if sentence not in selected_sentences:
                    selected_sentences.append(sentence)
                    # 记录原始索引
                    try:
                        original_index = sentences.index(sentence)
                        selected_indices.add(original_index)
                    except ValueError:
                        pass
            
            # 如果还需要更多句子，按原始顺序添加
            if len(selected_sentences) < max_sentences:
                for i, sentence in enumerate(sentences):
                    if len(selected_sentences) >= max_sentences:
                        break
                    if sentence not in selected_sentences:
                        selected_sentences.append(sentence)
                        selected_indices.add(i)
            
            # 确保至少选择一些句子
            if not selected_sentences and sentences:
                selected_sentences = sentences[:max_sentences]
            
            return selected_sentences
            
        except Exception as e:
            self.logger.warning(f"句子选择失败: {e}")
            return sentences[:max_sentences] if sentences else []
    
    def _reorder_sentences(self, original_sentences: List[str], selected_sentences: List[str]) -> List[str]:
        """重新排序句子（保持原文顺序）"""
        try:
            if not original_sentences or not selected_sentences:
                return selected_sentences if selected_sentences else []
            
            # 🚀 优化：使用模糊匹配处理文本变化（如标点、空格等）
            ordered_sentences = []
            selected_remaining = list(selected_sentences)  # 使用列表而不是集合，保留顺序
            
            # 按原始顺序遍历，尝试匹配选中的句子
            for original_sentence in original_sentences:
                original_normalized = original_sentence.strip()
                if not original_normalized:
                    continue
                
                # 尝试精确匹配
                matched = False
                for i, selected_sentence in enumerate(selected_remaining):
                    selected_normalized = selected_sentence.strip()
                    if original_normalized == selected_normalized:
                        ordered_sentences.append(original_sentence)
                        selected_remaining.pop(i)
                        matched = True
                        break
                
                # 如果精确匹配失败，尝试模糊匹配（忽略标点和空格差异）
                if not matched:
                    original_clean = ''.join(c for c in original_normalized if c.isalnum() or c.isspace()).strip()
                    for i, selected_sentence in enumerate(selected_remaining):
                        selected_normalized = selected_sentence.strip()
                        selected_clean = ''.join(c for c in selected_normalized if c.isalnum() or c.isspace()).strip()
                        if original_clean == selected_clean and len(original_clean) > 10:  # 只对较长文本进行模糊匹配
                            ordered_sentences.append(original_sentence)
                            selected_remaining.pop(i)
                            matched = True
                            break
            
            # 如果还有未匹配的选中句子，添加到末尾（保持原始顺序）
            if selected_remaining:
                # 按selected_sentences的原始顺序添加
                for selected_sentence in selected_sentences:
                    if selected_sentence in selected_remaining:
                        ordered_sentences.append(selected_sentence)
                        selected_remaining.remove(selected_sentence)
            
            # 确保返回的句子数量正确
            if len(ordered_sentences) != len(selected_sentences):
                self.logger.debug(f"重排序后句子数量不匹配: 期望{len(selected_sentences)}, 实际{len(ordered_sentences)}，返回选中的句子")
                # 如果数量不匹配，返回选中的句子（保持原始顺序）
                return selected_sentences
            
            return ordered_sentences
            
        except Exception as e:
            self.logger.warning(f"句子重排序失败: {e}")
            return selected_sentences if selected_sentences else []
    
    def _format_summary(self, sentences: List[str]) -> str:
        """格式化摘要"""
        try:
            if not sentences:
                return ""
            
            # 连接句子
            summary = '. '.join(sentences)
            
            # 确保以句号结尾
            if summary and not summary.endswith('.'):
                summary += '.'
            
            # 清理多余的标点符号
            summary = re.sub(r'[.]{2,}', '.', summary)
            summary = re.sub(r'\s+', ' ', summary)
            
            return summary.strip()
            
        except Exception as e:
            self.logger.warning(f"摘要格式化失败: {e}")
            return '. '.join(sentences)
    
    def analyze_text(self, text: str) -> TextAnalysisResult:
        """综合分析文本"""
        try:
            # 情感分析
            sentiment_result = self.analyze_sentiment(text)
            
            # 实体识别
            entities_result = self.extract_entities(text)
            
            # 关键词提取
            keywords = self.extract_keywords(text)
            
            # 生成摘要
            summary = self.generate_summary(text)
            
            # 计算整体置信度
            overall_confidence = (
                sentiment_result.confidence + 
                entities_result.confidence
            ) / 2.0
            
            return TextAnalysisResult(
                sentiment=sentiment_result,
                entities=entities_result,
                keywords=keywords,
                summary=summary,
                confidence=overall_confidence
            )
            
        except Exception as e:
            self.logger.error(f"文本分析失败: {e}")
            return TextAnalysisResult(
                sentiment=SentimentResult("neutral", 0.0, {}),
                entities=NERResult([], 0.0),
                keywords=[],
                summary="",
                confidence=0.0
            )
    
    def preprocess_text(self, text: str) -> str:
        """预处理文本"""
        try:
            # 移除多余的空格
            text = re.sub(r'\s+', ' ', text)
            
            # 移除特殊字符
            text = re.sub(r'[^\w\s.,!?]', '', text)
            
            # 转换为小写
            text = text.lower()
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"文本预处理失败: {e}")
            return text
    
    def tokenize(self, text: str) -> List[str]:
        """分词 - 使用统一分词管理器"""
        try:
            # 尝试使用统一分词管理器
            # tokenization_manager = get_unified_center('get_unified_tokenization_manager')
            # if tokenization_manager:
            #     # 使用智能分词策略
            #     result = tokenization_manager.tokenize_text(text, strategy='hybrid')
            #     return result.get('tokens', [])
            # else:
                # 回退到简化分词
            tokens = re.findall(r'\b\w+\b', text.lower())
            return tokens
            
        except Exception as e:
            self.logger.error(f"分词失败: {e}")
            # 最终回退
            tokens = re.findall(r'\b\w+\b', text.lower())
            return tokens
    
    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """获取文本统计信息"""
        try:
            words = self.tokenize(text)
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            return {
                "character_count": len(text),
                "word_count": len(words),
                "sentence_count": len(sentences),
                "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
                "average_sentence_length": len(words) / len(sentences) if sentences else 0,
                "unique_words": len(set(words)),
                "readability_score": self._calculate_readability(text, words, sentences)
            }
            
        except Exception as e:
            self.logger.error(f"文本统计失败: {e}")
            return {}
    
    def _calculate_readability(self, text: str, words: List[str], sentences: List[str]) -> float:
        """计算可读性分数"""
        try:
            if not text or not words or not sentences:
                return 0.0
            
            # 计算基本指标
            word_count = len(words)
            sentence_count = len(sentences)
            character_count = len(text)
            
            if word_count == 0 or sentence_count == 0:
                return 0.0
            
            # 平均句子长度（词数）
            avg_sentence_length = word_count / sentence_count
            
            # 平均词长（字符数）
            avg_word_length = sum(len(word) for word in words) / word_count
            
            # 计算音节数（简化版）
            syllable_count = 0
            for word in words:
                # 简化的音节计算
                vowels = 'aeiouAEIOU'
                syllables = sum(1 for char in word if char in vowels)
                syllable_count += max(1, syllables)
            
            avg_syllables_per_word = syllable_count / word_count
            
            # 计算复杂词比例（超过3个音节的词）
            complex_words = 0
            for word in words:
                vowels = 'aeiouAEIOU'
                syllables = sum(1 for char in word if char in vowels)
                if syllables > 3:
                    complex_words += 1
            
            complex_word_ratio = complex_words / word_count if word_count > 0 else 0
            
            # 计算标点符号密度
            punctuation_chars = '.,;:!?()[]{}"\'\''
            punctuation_count = sum(1 for char in text if char in punctuation_chars)
            punctuation_ratio = punctuation_count / character_count if character_count > 0 else 0
            
            # 基于Flesch Reading Ease的简化计算
            # 理想值：平均句子长度15-20词，平均词长4-5字符
            
            # 句子长度评分（15-20词为最佳）
            if avg_sentence_length < 10:
                sentence_score = 0.6  # 太短
            elif 10 <= avg_sentence_length <= 20:
                sentence_score = 1.0  # 理想
            elif 20 < avg_sentence_length <= 30:
                sentence_score = 0.8  # 稍长
            elif 30 < avg_sentence_length <= 40:
                sentence_score = 0.6  # 较长
            else:
                sentence_score = 0.4  # 太长
            
            # 词长评分（4-5字符为最佳）
            if avg_word_length < 3:
                word_score = 0.6  # 太短
            elif 3 <= avg_word_length <= 5:
                word_score = 1.0  # 理想
            elif 5 < avg_word_length <= 7:
                word_score = 0.8  # 稍长
            elif 7 < avg_word_length <= 9:
                word_score = 0.6  # 较长
            else:
                word_score = 0.4  # 太长
            
            # 音节复杂度评分
            if avg_syllables_per_word < 1.5:
                syllable_score = 1.0  # 简单
            elif 1.5 <= avg_syllables_per_word <= 2.0:
                syllable_score = 0.9  # 理想
            elif 2.0 < avg_syllables_per_word <= 2.5:
                syllable_score = 0.7  # 稍复杂
            elif 2.5 < avg_syllables_per_word <= 3.0:
                syllable_score = 0.5  # 复杂
            else:
                syllable_score = 0.3  # 很复杂
            
            # 复杂词比例评分
            if complex_word_ratio < 0.1:
                complex_score = 1.0  # 简单
            elif 0.1 <= complex_word_ratio <= 0.2:
                complex_score = 0.8  # 适中
            elif 0.2 < complex_word_ratio <= 0.3:
                complex_score = 0.6  # 复杂
            else:
                complex_score = 0.4  # 很复杂
            
            # 标点符号评分（适中的标点密度为最佳）
            if punctuation_ratio < 0.02:
                punctuation_score = 0.6  # 标点太少
            elif 0.02 <= punctuation_ratio <= 0.08:
                punctuation_score = 1.0  # 理想
            elif 0.08 < punctuation_ratio <= 0.15:
                punctuation_score = 0.8  # 稍多
            else:
                punctuation_score = 0.6  # 太多
            
            # 综合可读性评分
            readability = (
                sentence_score * 0.3 +
                word_score * 0.25 +
                syllable_score * 0.2 +
                complex_score * 0.15 +
                punctuation_score * 0.1
            )
            
            return min(max(readability, 0.0), 1.0)
            
        except Exception as e:
            self.logger.error(f"可读性计算失败: {e}")
            return 0.5
    
    def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            "status": "active",
            "positive_words_count": len(self.positive_words),
            "negative_words_count": len(self.negative_words),
            "entity_patterns_count": len(self.entity_patterns),
            "capabilities": [
                "sentiment_analysis",
                "entity_recognition", 
                "keyword_extraction",
                "text_summarization",
                "text_preprocessing",
                "tokenization",
                "text_statistics"
            ]
        }
    
    def get_processing_metrics(self) -> Dict[str, Any]:
        """获取处理指标"""
        try:
            if not hasattr(self, 'processing_metrics'):
                self.processing_metrics = {
                    'total_processed': 0,
                    'successful_processes': 0,
                    'failed_processes': 0,
                    'average_processing_time': 0.0,
                    'average_confidence': 0.0,
                    'total_processing_time': 0.0
                }
            
            return self.processing_metrics.copy()
        except Exception as e:
            self.logger.error(f"获取处理指标失败: {e}")
            return {"error": str(e)}
    
    def update_processing_metrics(self, success: bool, processing_time: float, confidence: float = 0.0) -> None:
        """更新处理指标"""
        try:
            if not hasattr(self, 'processing_metrics'):
                self.processing_metrics = {
                    'total_processed': 0,
                    'successful_processes': 0,
                    'failed_processes': 0,
                    'average_processing_time': 0.0,
                    'average_confidence': 0.0,
                    'total_processing_time': 0.0
                }
            
            self.processing_metrics['total_processed'] += 1
            self.processing_metrics['total_processing_time'] += processing_time
            
            if success:
                self.processing_metrics['successful_processes'] += 1
            else:
                self.processing_metrics['failed_processes'] += 1
            
            # 更新平均值
            self.processing_metrics['average_processing_time'] = (
                self.processing_metrics['total_processing_time'] / 
                self.processing_metrics['total_processed']
            )
            
            # 更新平均置信度
            if success and confidence > 0:
                current_avg = self.processing_metrics['average_confidence']
                total_successful = self.processing_metrics['successful_processes']
                self.processing_metrics['average_confidence'] = (
                    (current_avg * (total_successful - 1) + confidence) / total_successful
                )
            
        except Exception as e:
            self.logger.error(f"更新处理指标失败: {e}")
    
    def get_processing_history(self) -> List[Dict[str, Any]]:
        """获取处理历史"""
        try:
            if not hasattr(self, 'processing_history'):
                self.processing_history = []
            
            config_center = get_unified_config_center()
            return self.processing_history[-(config_center.get_config_value('system', 'default_limit', 100) if config_center else 100):]  # 返回最近100条记录
        except Exception as e:
            self.logger.error(f"获取处理历史失败: {e}")
            return []
    
    def clear_processing_history(self) -> bool:
        """清除处理历史"""
        try:
            # 清除处理历史
            if hasattr(self, 'processing_history'):
                history_count = len(self.processing_history)
                self.processing_history.clear()
                self.logger.info(f"已清除 {history_count} 条处理历史记录")
            else:
                self.logger.info("没有处理历史需要清除")
            
            # 重置处理指标
            if hasattr(self, 'processing_metrics'):
                self.processing_metrics = {
                    'total_processed': 0,
                    'successful_processes': 0,
                    'failed_processes': 0,
                    'average_processing_time': 0.0,
                    'average_confidence': 0.0,
                    'total_processing_time': 0.0
                }
                self.logger.info("处理指标已重置")
            
            # 清理其他相关数据
            if hasattr(self, 'recent_analyses'):
                self.recent_analyses.clear()
                self.logger.info("最近分析记录已清除")
            
            # 记录清理操作
            cleanup_time = time.time()
            if hasattr(self, 'last_cleanup_time'):
                self.last_cleanup_time = cleanup_time
            
            self.logger.info("处理历史清除完成")
            return True
            
        except Exception as e:
            self.logger.error(f"清除处理历史失败: {e}")
            return False
    
    def get_engine_statistics(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        try:
            stats = {
                'positive_words_count': len(self.positive_words),
                'negative_words_count': len(self.negative_words),
                'entity_patterns_count': len(self.entity_patterns),
                'capabilities_count': 7,  # 当前支持的功能数量
                'processing_metrics': self.get_processing_metrics(),
                'timestamp': time.time()
            }
            
            # 添加处理历史统计
            if hasattr(self, 'processing_history'):
                stats['processing_history_count'] = len(self.processing_history)
            else:
                stats['processing_history_count'] = 0
            
            return stats
        except Exception as e:
            self.logger.error(f"获取引擎统计信息失败: {e}")
            return {"error": str(e)}
    
    def optimize_engine_performance(self) -> Dict[str, Any]:
        """优化引擎性能"""
        try:
            optimizations = []
            
            # 优化情感词典
            if len(self.positive_words) < 50:
                self.positive_words.update({
                    "excellent", "outstanding", "fantastic", "wonderful", "brilliant",
                    "superb", "magnificent", "exceptional", "remarkable", "incredible"
                })
                optimizations.append("扩展了积极情感词典")
            
            if len(self.negative_words) < 50:
                self.negative_words.update({
                    "terrible", "awful", "horrible", "disgusting", "repulsive",
                    "atrocious", "appalling", "dreadful", "miserable", "pathetic"
                })
                optimizations.append("扩展了消极情感词典")
            
            # 优化实体模式
            if len(self.entity_patterns) < 10:
                self.entity_patterns.update({
                    "DATE": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                    "TIME": r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b',
                    "MONEY": r'\$\d+(?:\.\d{2})?\b',
                    "PERCENT": r'\d+(?:\.\d+)?%\b'
                })
                optimizations.append("扩展了实体识别模式")
            
            # 清理处理历史
            config_center = get_unified_config_center()
            if hasattr(self, 'processing_history') and len(self.processing_history) > (config_center.get_config_value('system', 'large_limit', 1000) if config_center else 1000):
                self.processing_history = self.processing_history[-(config_center.get_config_value('system', 'medium_buffer', 500) if config_center else 500):]  # 保留最近500条
                optimizations.append("清理了过长的处理历史")
            
            return {
                'optimizations_applied': optimizations,
                'optimization_count': len(optimizations),
                'timestamp': time.time()
            }
        except Exception as e:
            self.logger.error(f"优化引擎性能失败: {e}")
            return {"error": str(e)}
    
    def export_engine_config(self) -> Dict[str, Any]:
        """导出引擎配置"""
        try:
            config = {
                'positive_words': list(self.positive_words),
                'negative_words': list(self.negative_words),
                'entity_patterns': self.entity_patterns,
                'processing_metrics': self.get_processing_metrics(),
                'timestamp': time.time()
            }
            return config
        except Exception as e:
            self.logger.error(f"导出引擎配置失败: {e}")
            return {"error": str(e)}
    
    def import_engine_config(self, config: Dict[str, Any]) -> bool:
        """导入引擎配置"""
        try:
            if not config or not isinstance(config, dict):
                self.logger.error("配置数据无效")
                return False
            
            imported_items = []
            
            # 导入积极情感词典
            if 'positive_words' in config:
                if isinstance(config['positive_words'], (list, set)):
                    old_count = len(self.positive_words)
                    self.positive_words.update(config['positive_words'])
                    new_count = len(self.positive_words)
                    imported_items.append(f"积极情感词典: +{new_count - old_count} 个词")
                else:
                    self.logger.warning("积极情感词典格式无效")
            
            # 导入消极情感词典
            if 'negative_words' in config:
                if isinstance(config['negative_words'], (list, set)):
                    old_count = len(self.negative_words)
                    self.negative_words.update(config['negative_words'])
                    new_count = len(self.negative_words)
                    imported_items.append(f"消极情感词典: +{new_count - old_count} 个词")
                else:
                    self.logger.warning("消极情感词典格式无效")
            
            # 导入实体模式
            if 'entity_patterns' in config:
                if isinstance(config['entity_patterns'], dict):
                    old_count = len(self.entity_patterns)
                    self.entity_patterns.update(config['entity_patterns'])
                    new_count = len(self.entity_patterns)
                    imported_items.append(f"实体模式: +{new_count - old_count} 个模式")
                else:
                    self.logger.warning("实体模式格式无效")
            
            # 导入处理指标
            if 'processing_metrics' in config:
                if isinstance(config['processing_metrics'], dict):
                    self.processing_metrics = config['processing_metrics'].copy()
                    imported_items.append("处理指标已更新")
                else:
                    self.logger.warning("处理指标格式无效")
            
            # 导入其他配置
            if 'max_keywords' in config:
                self.max_keywords = config['max_keywords']
                imported_items.append(f"最大关键词数: {self.max_keywords}")
            
            if 'max_sentences' in config:
                self.max_sentences = config['max_sentences']
                imported_items.append(f"最大句子数: {self.max_sentences}")
            
            if 'confidence_threshold' in config:
                self.confidence_threshold = config['confidence_threshold']
                imported_items.append(f"置信度阈值: {self.confidence_threshold}")
            
            # 记录导入结果
            if imported_items:
                self.logger.info(f"引擎配置导入成功: {', '.join(imported_items)}")
            else:
                self.logger.warning("没有有效的配置项被导入")
            
            return len(imported_items) > 0
            
        except Exception as e:
            self.logger.error(f"导入引擎配置失败: {e}")
            return False
    
    def get_engine_metrics(self) -> Dict[str, Any]:
        """获取引擎指标"""
        try:
            metrics = {
                'vocabulary_size': len(self.positive_words) + len(self.negative_words),
                'entity_patterns_count': len(self.entity_patterns),
                'processing_efficiency': self._calculate_processing_efficiency(),
                'accuracy_score': self._calculate_accuracy_score(),
                'response_time': self._calculate_average_response_time(),
                'memory_usage': self._estimate_memory_usage(),
                'timestamp': time.time()
            }
            return metrics
        except Exception as e:
            self.logger.error(f"获取引擎指标失败: {e}")
            return {"error": str(e)}
    
    def _calculate_processing_efficiency(self) -> float:
        """计算处理效率"""
        try:
            if not hasattr(self, 'processing_metrics'):
                return 0.0
            
            total = self.processing_metrics.get('total_processed', 0)
            successful = self.processing_metrics.get('successful_processes', 0)
            failed = self.processing_metrics.get('failed_processes', 0)
            
            if total == 0:
                return 0.0
            
            # 基本成功率
            success_rate = successful / total
            
            # 考虑处理时间效率
            avg_time = self.processing_metrics.get('average_processing_time', 0.0)
            time_efficiency = 1.0
            if avg_time > 0:
                # 理想处理时间：0.1-1.0秒
                if avg_time <= 0.1:
                    time_efficiency = 1.0  # 非常快
                elif avg_time <= 0.5:
                    time_efficiency = 0.9  # 快
                elif avg_time <= 1.0:
                    time_efficiency = 0.8  # 正常
                elif avg_time <= 2.0:
                    time_efficiency = 0.6  # 稍慢
                elif avg_time <= 5.0:
                    time_efficiency = 0.4  # 慢
                else:
                    time_efficiency = 0.2  # 很慢
            
            # 考虑置信度效率
            avg_confidence = self.processing_metrics.get('average_confidence', 0.0)
            confidence_efficiency = avg_confidence  # 置信度越高，效率越高
            
            # 考虑错误率
            error_rate = failed / total if total > 0 else 0
            error_penalty = 1.0 - (error_rate * 0.5)  # 错误率越高，效率越低
            
            # 综合效率计算
            efficiency = (
                success_rate * 0.4 +           # 成功率权重40%
                time_efficiency * 0.3 +        # 时间效率权重30%
                confidence_efficiency * 0.2 +  # 置信度效率权重20%
                error_penalty * 0.1            # 错误惩罚权重10%
            )
            
            return min(max(efficiency, 0.0), 1.0)
            
        except Exception as e:
            self.logger.error(f"计算处理效率失败: {e}")
            return 0.0
    
    def _calculate_accuracy_score(self) -> float:
        """计算准确度分数"""
        try:
            if not hasattr(self, 'processing_metrics'):
                return 0.0
            
            return self.processing_metrics.get('average_confidence', 0.0)
        except Exception as e:
            self.logger.error(f"计算准确度分数失败: {e}")
            return 0.0
    
    def _calculate_average_response_time(self) -> float:
        """计算平均响应时间"""
        try:
            if not hasattr(self, 'processing_metrics'):
                return 0.0
            
            return self.processing_metrics.get('average_processing_time', 0.0)
        except Exception as e:
            self.logger.error(f"计算平均响应时间失败: {e}")
            return 0.0
    
    def _estimate_memory_usage(self) -> int:
        """估算内存使用量"""
        try:
            memory_usage = 0
            
            # 情感词典内存
            memory_usage += len(self.positive_words) * 20  # 假设每个词20字节
            memory_usage += len(self.negative_words) * 20
            
            # 实体模式内存
            memory_usage += len(self.entity_patterns) * 100  # 假设每个模式100字节
            
            # 处理历史内存
            if hasattr(self, 'processing_history'):
                memory_usage += len(self.processing_history) * 200  # 假设每条记录200字节
            
            return memory_usage
        except Exception as e:
            self.logger.error(f"估算内存使用量失败: {e}")
            return 0
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            health_status = {
                'overall_health': 'healthy',
                'components': {},
                'issues': [],
                'timestamp': time.time()
            }
            
            # 检查情感词典
            if len(self.positive_words) < 10:
                health_status['issues'].append("积极情感词典过少")
                health_status['overall_health'] = 'degraded'
            
            if len(self.negative_words) < 10:
                health_status['issues'].append("消极情感词典过少")
                health_status['overall_health'] = 'degraded'
            
            health_status['components']['sentiment_dictionaries'] = 'healthy' if len(self.positive_words) >= 10 and len(self.negative_words) >= 10 else 'degraded'
            
            # 检查实体模式
            if len(self.entity_patterns) < 5:
                health_status['issues'].append("实体识别模式过少")
                health_status['overall_health'] = 'degraded'
            
            health_status['components']['entity_patterns'] = 'healthy' if len(self.entity_patterns) >= 5 else 'degraded'
            
            # 检查处理指标
            if hasattr(self, 'processing_metrics'):
                success_rate = self.processing_metrics.get('successful_processes', 0) / max(1, self.processing_metrics.get('total_processed', 1))
                if success_rate < 0.8:
                    health_status['issues'].append(f"处理成功率过低: {success_rate:.2%}")
                    health_status['overall_health'] = 'degraded'
                
                health_status['components']['processing_success_rate'] = f"{success_rate:.2%}"
            else:
                health_status['components']['processing_success_rate'] = 'unknown'
            
            return health_status
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return {"error": str(e), "overall_health": "unhealthy"}
    
    def get_engine_info(self) -> Dict[str, Any]:
        """获取引擎信息"""
        try:
            info = {
                'engine_name': 'NLPEngine',
                'version': '1.0.0',
                'description': '自然语言处理引擎，提供情感分析、实体识别、关键词提取、文本摘要等功能',
                'capabilities': [
                    '情感分析',
                    '命名实体识别',
                    '关键词提取',
                    '文本摘要',
                    '文本预处理',
                    '分词',
                    '文本统计'
                ],
                'supported_languages': ['中文', '英文'],
                'positive_words_count': len(self.positive_words),
                'negative_words_count': len(self.negative_words),
                'entity_patterns_count': len(self.entity_patterns),
                'timestamp': time.time()
            }
            return info
        except Exception as e:
            self.logger.error(f"获取引擎信息失败: {e}")
            return {"error": str(e)}


def get_nlp_engine() -> NLPEngine:
    """获取NLP引擎实例"""
    return NLPEngine()


if __name__ == "__main__":
    # 测试NLP引擎
    engine = NLPEngine()
    
    # 测试文本
    test_text = "I love this product! It's amazing and works perfectly. The customer service is excellent too."
    
    # 情感分析
    sentiment = engine.analyze_sentiment(test_text)
    print(f"情感分析: {sentiment}")
    
    # 实体识别
    entities = engine.extract_entities(test_text)
    print(f"实体识别: {entities}")
    
    # 关键词提取
    keywords = engine.extract_keywords(test_text)
    print(f"关键词: {keywords}")
    
    # 生成摘要
    summary = engine.generate_summary(test_text)
    print(f"摘要: {summary}")
    
    # 综合分析
    analysis = engine.analyze_text(test_text)
    print(f"综合分析: {analysis}")
    
    # 获取引擎状态
    status = engine.get_engine_status()
    print(f"引擎状态: {status}")