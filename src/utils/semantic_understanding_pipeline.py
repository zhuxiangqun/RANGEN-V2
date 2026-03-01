#!/usr/bin/env python3
"""
分层语义理解管道 - 整合多种NLP技术进行语义理解

核心思想：
1. 词汇语义层：词向量、词义消歧、词性标注
2. 句法语义层：依存句法分析、语义角色标注
3. 上下文语义层：上下文词向量（BERT、Sentence-BERT）
4. 篇章语义层：文档向量、主题模型
5. 意图与情感层：意图识别、情感分析
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class SemanticUnderstandingPipeline:
    """分层语义理解管道"""
    
    def __init__(self):
        """初始化语义理解管道"""
        self.logger = logging.getLogger(__name__)
        
        # 初始化各种NLP工具（延迟加载）
        self._spacy_nlp = None
        self._sentence_transformer = None
        self._nlp_engine = None
        self._models_checked = False
        self._available_models = []
        
        self.logger.info("语义理解管道初始化完成")

    def are_models_available(self) -> bool:
        """检查是否有可用的语义模型"""
        if not self._models_checked:
            # 尝试获取模型以触发加载检查
            self._get_sentence_transformer()
            self._get_spacy_nlp()
            self._models_checked = True
            
        return len(self._available_models) > 0
    
    def _get_spacy_nlp(self):
        """获取spaCy NLP实例（延迟加载）"""
        if self._spacy_nlp is None:
            try:
                import spacy
                model_names = ['en_core_web_sm', 'en_core_web_md', 'en_core_web_lg', 'en_core_web_trf']
                for model_name in model_names:
                    try:
                        self._spacy_nlp = spacy.load(model_name)
                        self.logger.info(f"✅ 加载spaCy模型: {model_name}")
                        if 'spacy' not in self._available_models:
                            self._available_models.append('spacy')
                        break
                    except OSError:
                        continue
            except ImportError:
                self.logger.debug("spaCy未安装")
        return self._spacy_nlp
    
    def _get_sentence_transformer(self):
        """获取Sentence-BERT模型（延迟加载）"""
        if self._sentence_transformer is None:
            try:
                from sentence_transformers import SentenceTransformer, util
                # 优先使用轻量级模型
                model_names = ['all-MiniLM-L6-v2', 'all-mpnet-base-v2', 'paraphrase-MiniLM-L6-v2']
                for model_name in model_names:
                    try:
                        self._sentence_transformer = SentenceTransformer(model_name)
                        self._sentence_transformer_util = util
                        self.logger.info(f"✅ 加载Sentence-BERT模型: {model_name}")
                        if 'sentence_bert' not in self._available_models:
                            self._available_models.append('sentence_bert')
                        break
                    except Exception as e:
                        self.logger.debug(f"加载Sentence-BERT模型{model_name}失败: {e}")
                        continue
            except ImportError:
                self.logger.debug("sentence-transformers未安装")
        return self._sentence_transformer
    
    def _get_nlp_engine(self):
        """获取NLP引擎实例（延迟加载）"""
        if self._nlp_engine is None:
            try:
                from src.ai.nlp_engine import NLPEngine
                self._nlp_engine = NLPEngine()
            except ImportError:
                self.logger.debug("NLP引擎不可用")
        return self._nlp_engine
    
    def understand_query(self, query: str) -> Dict[str, Any]:
        """🚀 分层语义理解：理解查询的多个层次
        
        Args:
            query: 查询文本
            
        Returns:
            包含多个层次语义理解的字典
        """
        result = {
            'query': query,
            'lexical': {},      # 词汇语义层
            'syntactic': {},    # 句法语义层
            'contextual': {},   # 上下文语义层
            'intent': {},       # 意图层
            'embedding': None   # 语义向量
        }
        
        try:
            # 1. 词汇语义层：词性标注、实体识别
            result['lexical'] = self._analyze_lexical_semantics(query)
            
            # 2. 句法语义层：依存句法分析、语义角色标注
            result['syntactic'] = self._analyze_syntactic_semantics(query)
            
            # 3. 上下文语义层：生成语义向量
            result['contextual'] = self._analyze_contextual_semantics(query)
            result['embedding'] = result['contextual'].get('embedding')
            
            # 4. 意图层：查询意图分类
            result['intent'] = self._analyze_intent(query)
            
        except Exception as e:
            self.logger.error(f"语义理解失败: {e}")
        
        return result
    
    def _analyze_lexical_semantics(self, query: str) -> Dict[str, Any]:
        """词汇语义层：词性标注、实体识别"""
        result = {
            'pos_tags': [],
            'entities': [],
            'keywords': []
        }
        
        # 使用spaCy进行词性标注和实体识别
        nlp = self._get_spacy_nlp()
        if nlp:
            doc = nlp(query)
            
            # 词性标注
            result['pos_tags'] = [(token.text, token.pos_, token.tag_) for token in doc]
            
            # 实体识别
            result['entities'] = [
                {
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                }
                for ent in doc.ents
            ]
            
            # 提取关键词（名词和专有名词）
            result['keywords'] = [
                token.text for token in doc 
                if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop
            ]
        
        return result
    
    def _analyze_syntactic_semantics(self, query: str) -> Dict[str, Any]:
        """句法语义层：依存句法分析、语义角色标注"""
        result = {
            'dependency_tree': [],
            'root': None,
            'subject': None,
            'object': None,
            'relationships': []
        }
        
        # 使用spaCy进行依存句法分析
        nlp = self._get_spacy_nlp()
        if nlp:
            doc = nlp(query)
            
            # 依存树
            result['dependency_tree'] = [
                {
                    'token': token.text,
                    'dep': token.dep_,
                    'head': token.head.text,
                    'head_pos': token.head.pos_
                }
                for token in doc
            ]
            
            # 找到根节点
            for token in doc:
                if token.dep_ == "ROOT":
                    result['root'] = token.text
                    break
            
            # 找到主语和宾语
            for token in doc:
                if token.dep_ == "nsubj":  # 名词主语
                    result['subject'] = token.text
                elif token.dep_ in ["dobj", "pobj"]:  # 直接宾语、介词宾语
                    result['object'] = token.text
            
            # 🚀 重构：使用依存句法分析智能提取关系（而非硬编码关键词）
            # 检测关系结构：通过依存句法分析检测关系模式
            seen_relationships = set()  # 避免重复添加
            
            for token in doc:
                # 方法1: 检测所有格结构（"X's Y"）
                # 在 "X's mother" 中，"mother" 是名词，有 'case' 或 'nmod:poss' 子词（"'s"）
                if token.pos_ == 'NOUN':
                    # 检查是否有所有格修饰（"'s"）
                    for child in token.children:
                        # spaCy中，所有格标记可能是 'case'（对于 "'s"）或 'nmod:poss'
                        if child.dep_ in ['case', 'nmod:poss'] and ("'s" in child.text or child.text == "'s"):
                            # 这是一个关系名词（如 "mother" in "X's mother"）
                            rel_key = f"{token.lemma_.lower()}_{token.i}"
                            if rel_key not in seen_relationships:
                                result['relationships'].append({
                                    'type': token.lemma_.lower(),
                                    'text': token.text,
                                    'dependents': [c.text for c in token.children],
                                    'pattern': 'possessive'  # 所有格模式
                                })
                                seen_relationships.add(rel_key)
                            break
                    
                    # 方法2: 检测介词结构（"Y of X"）
                    # 在 "mother of X" 中，"mother" 是名词，有 'prep' 子词（"of"）
                    for child in token.children:
                        if child.dep_ == 'prep' and child.lemma_.lower() == 'of':
                            # 这是一个关系名词（如 "mother" in "mother of X"）
                            rel_key = f"{token.lemma_.lower()}_{token.i}"
                            if rel_key not in seen_relationships:
                                result['relationships'].append({
                                    'type': token.lemma_.lower(),
                                    'text': token.text,
                                    'dependents': [c.text for c in token.children],
                                    'pattern': 'prepositional'  # 介词模式
                                })
                                seen_relationships.add(rel_key)
                            break
                
                # 方法3: 检测已知的关系词（作为补充，但不完全依赖）
                # 只检测最通用的关系词，其他通过依存句法分析检测
                elif token.lemma_.lower() in ['mother', 'father', 'parent', 'spouse', 'child', 'son', 'daughter', 'wife', 'husband', 'sibling', 'brother', 'sister']:
                    rel_key = f"{token.lemma_.lower()}_{token.i}"
                    if rel_key not in seen_relationships:
                        result['relationships'].append({
                            'type': token.lemma_.lower(),
                            'text': token.text,
                            'dependents': [c.text for c in token.children],
                            'pattern': 'keyword'  # 关键词模式
                        })
                        seen_relationships.add(rel_key)
        
        return result
    
    def _analyze_contextual_semantics(self, query: str) -> Dict[str, Any]:
        """上下文语义层：生成语义向量"""
        result = {
            'embedding': None,
            'model': None
        }
        
        # 优先使用Sentence-BERT
        sbert = self._get_sentence_transformer()
        if sbert:
            try:
                embedding = sbert.encode(query, convert_to_numpy=True, show_progress_bar=False)
                result['embedding'] = embedding.tolist()
                result['model'] = 'sentence-bert'
                return result
            except Exception as e:
                self.logger.debug(f"Sentence-BERT编码失败: {e}")
        
        # Fallback：使用spaCy的向量
        nlp = self._get_spacy_nlp()
        if nlp and nlp.has_pipe('tok2vec'):
            try:
                doc = nlp(query)
                if doc.vector is not None and doc.vector.any():
                    result['embedding'] = doc.vector.tolist()
                    result['model'] = 'spacy'
                    return result
            except Exception as e:
                self.logger.debug(f"spaCy向量编码失败: {e}")
        
        return result
    
    def _analyze_intent(self, query: str) -> Dict[str, Any]:
        """意图层：查询意图分类"""
        result = {
            'intent_type': 'unknown',
            'is_factual': False,
            'is_reasoning': False,
            'requires_multi_hop': False
        }
        
        # 使用简单的规则进行初步分类（可以后续用LLM增强）
        query_lower = query.lower()
        
        # 事实查询关键词
        factual_keywords = ['what', 'who', 'where', 'when', 'which', 'name', 'is', 'was']
        # 推理查询关键词
        reasoning_keywords = ['why', 'how', 'explain', 'analyze', 'compare', 'calculate']
        # 多跳查询关键词
        multi_hop_keywords = ['of', "'s", 'mother', 'father', 'first', 'second', 'third']
        
        has_factual = any(keyword in query_lower for keyword in factual_keywords)
        has_reasoning = any(keyword in query_lower for keyword in reasoning_keywords)
        has_multi_hop = any(keyword in query_lower for keyword in multi_hop_keywords)
        
        if has_reasoning:
            result['intent_type'] = 'reasoning'
            result['is_reasoning'] = True
        elif has_factual:
            result['intent_type'] = 'factual'
            result['is_factual'] = True
        
        if has_multi_hop:
            result['requires_multi_hop'] = True
        
        return result
    
    def calculate_semantic_similarity(
        self, 
        text1: str, 
        text2: str,
        use_sentence_bert: bool = True
    ) -> float:
        """🚀 计算两个文本的语义相似度（优先使用Sentence-BERT）
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            use_sentence_bert: 是否优先使用Sentence-BERT
            
        Returns:
            语义相似度分数 (0.0-1.0)
        """
        try:
            # 优先使用Sentence-BERT
            if use_sentence_bert:
                sbert = self._get_sentence_transformer()
                if sbert and hasattr(self, '_sentence_transformer_util'):
                    try:
                        embeddings = sbert.encode([text1, text2], convert_to_numpy=True, show_progress_bar=False)
                        similarity = self._sentence_transformer_util.cos_sim(
                            embeddings[0], embeddings[1]
                        ).item()
                        return float(similarity)
                    except Exception as e:
                        self.logger.debug(f"Sentence-BERT相似度计算失败: {e}")
            
            # Fallback：使用spaCy向量
            nlp = self._get_spacy_nlp()
            if nlp:
                try:
                    doc1 = nlp(text1)
                    doc2 = nlp(text2)
                    if doc1.vector is not None and doc2.vector is not None:
                        similarity = doc1.similarity(doc2)
                        return float(similarity)
                except Exception as e:
                    self.logger.debug(f"spaCy相似度计算失败: {e}")
            
            # 最后fallback：使用简单的词级相似度
            return self._word_level_similarity(text1, text2)
            
        except Exception as e:
            self.logger.debug(f"语义相似度计算失败: {e}")
            return 0.0
    
    def _word_level_similarity(self, text1: str, text2: str) -> float:
        """词级相似度（fallback方法）"""
        try:
            words1 = set(re.findall(r'\b\w+\b', text1.lower()))
            words2 = set(re.findall(r'\b\w+\b', text2.lower()))
            
            if not words1 or not words2:
                return 0.0
            
            # Jaccard相似度
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            return intersection / union if union > 0 else 0.0
        except Exception:
            return 0.0
    
    def validate_relevance(
        self, 
        query: str, 
        retrieved_text: str, 
        threshold: float = 0.7
    ) -> Tuple[bool, float]:
        """🚀 验证检索结果的相关性（使用语义相似度）
        
        Args:
            query: 查询文本
            retrieved_text: 检索到的文本
            threshold: 相似度阈值
            
        Returns:
            (是否相关, 相似度分数)
        """
        similarity = self.calculate_semantic_similarity(query, retrieved_text)
        is_relevant = similarity >= threshold
        return (is_relevant, similarity)
    
    def classify_query_intent(self, query: str) -> Dict[str, Any]:
        """🚀 分类查询意图（事实查询 vs 推理查询）
        
        Args:
            query: 查询文本
            
        Returns:
            意图分类结果
        """
        return self._analyze_intent(query)
    
    def extract_entities_intelligent(self, text: str) -> List[Dict[str, Any]]:
        """🚀 智能实体提取（使用多层策略）
        
        Args:
            text: 文本
            
        Returns:
            实体列表
        """
        entities = []
        
        # 优先使用spaCy
        nlp = self._get_spacy_nlp()
        if nlp:
            doc = nlp(text)
            for ent in doc.ents:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': 0.9  # spaCy的置信度
                })
        
        # 如果spaCy没有找到实体，使用NLP引擎
        if not entities:
            nlp_engine = self._get_nlp_engine()
            if nlp_engine:
                try:
                    ner_result = nlp_engine.extract_entities(text)
                    if ner_result and ner_result.entities:
                        for entity in ner_result.entities:
                            entities.append({
                                'text': entity.get('text', '') if isinstance(entity, dict) else str(entity),
                                'label': entity.get('label', '') if isinstance(entity, dict) else 'UNKNOWN',
                                'confidence': entity.get('confidence', 0.8) if isinstance(entity, dict) else 0.8
                            })
                except Exception as e:
                    self.logger.debug(f"NLP引擎实体提取失败: {e}")
        
        return entities


def get_semantic_understanding_pipeline() -> SemanticUnderstandingPipeline:
    """获取语义理解管道实例（单例模式）"""
    if not hasattr(get_semantic_understanding_pipeline, '_instance'):
        get_semantic_understanding_pipeline._instance = SemanticUnderstandingPipeline()
    return get_semantic_understanding_pipeline._instance

