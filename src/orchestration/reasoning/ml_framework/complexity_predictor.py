#!/usr/bin/env python3
"""
轻量级复杂度预测模型
用于预测查询的复杂度，辅助智能协调层的决策
"""

import logging
import pickle
import os
from typing import Dict, Any, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from .base_ml_component import BaseMLComponent

logger = logging.getLogger(__name__)


class ComplexityPredictor(BaseMLComponent):
    """轻量级复杂度预测模型
    
    预测查询的复杂度级别：simple, medium, complex
    """
    
    def __init__(self):
        """初始化复杂度预测模型"""
        super().__init__()
        self.model = None
        self.vectorizer = None
        self.complexity_labels = ['simple', 'medium', 'complex']
        self.model_name = "complexity_predictor"
    
    def _extract_features(self, query: str) -> np.ndarray:
        """提取查询特征
        
        Args:
            query: 查询文本
            
        Returns:
            特征向量
        """
        if self.vectorizer is None:
            # 如果vectorizer未初始化，使用简单的特征提取
            return self._extract_simple_features(query)
        
        # 使用TF-IDF向量化
        try:
            features = self.vectorizer.transform([query]).toarray()
            return features[0]
        except Exception as e:
            logger.warning(f"TF-IDF特征提取失败: {e}，使用简单特征")
            return self._extract_simple_features(query)
    
    def _extract_simple_features(self, query: str) -> np.ndarray:
        """提取简单特征（不依赖vectorizer）
        
        Args:
            query: 查询文本
            
        Returns:
            特征向量
        """
        query_lower = query.lower()
        words = query.split()
        
        features = [
            len(words),  # 查询长度
            len(query),  # 字符数
            query.count("'s "),  # 所有格数量
            query.count(" and "),  # 并列连接词
            query.count(" or "),  # 或连接词
            query.count(" if "),  # 条件词
            query.count("?"),  # 问号数量
            sum(1 for word in words if word[0].isupper() if word),  # 大写词数量
            query_lower.count("who"),  # who查询
            query_lower.count("what"),  # what查询
            query_lower.count("when"),  # when查询
            query_lower.count("where"),  # where查询
            query_lower.count("why"),  # why查询
            query_lower.count("how"),  # how查询
            query_lower.count("mother"),  # 关系查询
            query_lower.count("father"),  # 关系查询
            query_lower.count("wife"),  # 关系查询
            query_lower.count("husband"),  # 关系查询
        ]
        
        return np.array(features, dtype=np.float32)
    
    def train(self, training_data: Dict[str, Any]) -> Dict[str, Any]:
        """训练复杂度预测模型
        
        Args:
            training_data: 训练数据，包含 'queries' 和 'complexities'
            
        Returns:
            训练结果
        """
        try:
            queries = training_data.get('queries', [])
            complexities = training_data.get('complexities', [])
            
            if not queries or not complexities:
                logger.warning("训练数据为空")
                return {"success": False, "error": "训练数据为空"}
            
            if len(queries) != len(complexities):
                logger.warning("查询和复杂度数量不匹配")
                return {"success": False, "error": "数据数量不匹配"}
            
            # 初始化TF-IDF向量化器
            self.vectorizer = TfidfVectorizer(
                max_features=100,
                ngram_range=(1, 2),
                stop_words='english'
            )
            
            # 提取特征
            X = self.vectorizer.fit_transform(queries).toarray()
            
            # 将复杂度标签转换为数字
            label_to_num = {label: i for i, label in enumerate(self.complexity_labels)}
            y = np.array([label_to_num.get(c, 1) for c in complexities])  # 默认medium
            
            # 训练模型
            self.model = RandomForestClassifier(
                n_estimators=50,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.model.fit(X, y)
            
            # 评估模型
            accuracy = self.model.score(X, y)
            
            logger.info(f"✅ 复杂度预测模型训练完成，准确率: {accuracy:.2%}")
            
            return {
                "success": True,
                "accuracy": accuracy,
                "samples": len(queries),
                "model_type": "RandomForest"
            }
            
        except Exception as e:
            logger.error(f"训练复杂度预测模型失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def predict(self, query: str) -> Dict[str, Any]:
        """预测查询复杂度
        
        Args:
            query: 查询文本
            
        Returns:
            预测结果，包含 'complexity' 和 'confidence'
        """
        try:
            if self.model is None:
                # 如果模型未训练，使用规则预测
                return self._predict_by_rules(query)
            
            # 提取特征
            features = self._extract_features(query)
            
            # 如果使用简单特征，需要调整形状
            if self.vectorizer is None:
                # 简单特征需要reshape
                features = features.reshape(1, -1)
            else:
                features = features.reshape(1, -1)
            
            # 预测
            prediction = self.model.predict(features)[0]
            probabilities = self.model.predict_proba(features)[0]
            
            complexity = self.complexity_labels[prediction]
            confidence = float(probabilities[prediction])
            
            return {
                "complexity": complexity,
                "confidence": confidence,
                "probabilities": {
                    label: float(prob) 
                    for label, prob in zip(self.complexity_labels, probabilities)
                }
            }
            
        except Exception as e:
            logger.warning(f"复杂度预测失败: {e}，使用规则预测")
            return self._predict_by_rules(query)
    
    def _predict_by_rules(self, query: str) -> Dict[str, Any]:
        """基于规则的复杂度预测（回退方案）
        
        Args:
            query: 查询文本
            
        Returns:
            预测结果
        """
        query_lower = query.lower()
        words = query.split()
        query_length = len(words)
        
        # 简单任务
        if query_length < 10 and not any(word in query_lower for word in [
            '分析', '比较', '设计', '解释', 'analyze', 'compare', 'design', 'explain'
        ]):
            return {
                "complexity": "simple",
                "confidence": 0.7,
                "probabilities": {"simple": 0.7, "medium": 0.2, "complex": 0.1}
            }
        
        # 复杂任务
        if any(word in query_lower for word in [
            '和', '以及', '同时', '分别', 'and', 'also', 'while', 'respectively'
        ]) or query_length > 20 or query.count("'s ") > 2:
            return {
                "complexity": "complex",
                "confidence": 0.7,
                "probabilities": {"simple": 0.1, "medium": 0.2, "complex": 0.7}
            }
        
        # 中等复杂度
        return {
            "complexity": "medium",
            "confidence": 0.6,
            "probabilities": {"simple": 0.2, "medium": 0.6, "complex": 0.2}
        }
    
    def _save_model_impl(self, filepath: str) -> bool:
        """保存模型实现
        
        Args:
            filepath: 保存路径
            
        Returns:
            是否成功
        """
        try:
            model_data = {
                'model': self.model,
                'vectorizer': self.vectorizer,
                'complexity_labels': self.complexity_labels
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            return True
        except Exception as e:
            logger.error(f"保存复杂度预测模型失败: {e}")
            return False
    
    def _load_model_impl(self, filepath: str) -> bool:
        """加载模型实现
        
        Args:
            filepath: 模型路径
            
        Returns:
            是否成功
        """
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data.get('model')
            self.vectorizer = model_data.get('vectorizer')
            self.complexity_labels = model_data.get('complexity_labels', ['simple', 'medium', 'complex'])
            
            return True
        except Exception as e:
            logger.error(f"加载复杂度预测模型失败: {e}")
            return False

