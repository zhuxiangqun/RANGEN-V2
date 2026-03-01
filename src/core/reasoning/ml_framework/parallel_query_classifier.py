"""
并行查询分类器 - 基于ML的并行结构检测
"""
from typing import Dict, Any, List, Optional
import logging
import re
from .base_ml_component import BaseMLComponent

logger = logging.getLogger(__name__)


class ParallelQueryClassifier(BaseMLComponent):
    """基于ML的并行查询分类器
    
    检测查询是否包含并行结构，可以并行处理多个独立的查询链。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化并行查询分类器
        
        Args:
            config: 配置字典，包含模型路径、阈值等
        """
        super().__init__(config)
        self.model = None
        self.threshold = config.get("threshold", 0.5) if config else 0.5
        
        # 初始化特征提取器
        self.feature_extractor = QueryFeatureExtractor()
        
        # 🚀 增强：自动加载预训练模型
        from src.core.reasoning.ml_framework.model_auto_loader import auto_load_model
        if not auto_load_model(self, "parallel_query_classifier", config):
            # 如果加载失败，使用规则版本
            self.model = "rule_based"
            self.is_trained = True
            self.logger.info("✅ 使用基于规则的并行查询分类器（初始版本）")
    
    def predict(self, query: str) -> Dict[str, Any]:
        """预测查询是否包含并行结构
        
        Args:
            query: 查询文本
            
        Returns:
            预测结果字典，包含：
            - is_parallel: 是否包含并行结构
            - confidence: 置信度（0-1）
            - suggested_decomposition: 建议的分解方式
            - parallel_groups: 识别的并行组
        """
        if not self.is_trained:
            self.logger.warning("⚠️ 模型未训练，使用默认预测")
            return {
                "is_parallel": False,
                "confidence": 0.0,
                "suggested_decomposition": None,
                "parallel_groups": []
            }
        
        # 提取特征
        features = self.feature_extractor.extract_features(query)
        
        # 使用模型预测
        if self.model == "rule_based" or not self.is_trained:
            # 基于规则的预测（初始版本）
            prediction = self._rule_based_predict(features, query)
        else:
            # ML模型预测
            prediction = self._ml_model_predict(features, query)
        
        return prediction
    
    def _rule_based_predict(self, features: Dict[str, Any], query: str) -> Dict[str, Any]:
        """基于规则的预测（初始版本，后续将被ML模型替代）"""
        query_lower = query.lower()
        
        # 规则1: 检测"and"连接的两个独立条件
        has_and = features.get("has_and_connector", 0) > 0
        num_conditions = features.get("num_condition_clauses", 0)
        
        # 规则2: 检测多个独立实体查询
        num_entities = features.get("num_distinct_entities", 0)
        
        # 规则3: 检测模式匹配
        matches_pattern = features.get("matches_parallel_pattern", False)
        
        # 综合判断
        is_parallel = (has_and and num_conditions >= 2) or (num_entities >= 2) or matches_pattern
        
        # 计算置信度（简单规则，后续用ML模型）
        confidence = 0.7 if is_parallel else 0.3
        
        # 识别并行组
        parallel_groups = self._identify_parallel_groups(query)
        
        return {
            "is_parallel": is_parallel,
            "confidence": confidence,
            "suggested_decomposition": self._suggest_decomposition(query) if is_parallel else None,
            "parallel_groups": parallel_groups
        }
    
    def _ml_model_predict(self, features: Dict[str, Any], query: str = "") -> Dict[str, Any]:
        """ML模型预测"""
        try:
            if not self.is_trained or self.model is None or self.model == "rule_based":
                # 如果模型未训练，回退到规则版本
                return self._rule_based_predict(features, query)
            
            import numpy as np
            
            # 提取特征向量
            feature_vector = np.array([list(features.values())]).reshape(1, -1)
            
            # 标准化（如果scaler存在）
            if hasattr(self, 'scaler') and self.scaler is not None:
                feature_vector = self.scaler.transform(feature_vector)
            
            # 预测
            if hasattr(self.model, 'predict_proba'):
                is_parallel_prob = self.model.predict_proba(feature_vector)[0][1]
            else:
                is_parallel_prob = float(self.model.predict(feature_vector)[0])
            
            is_parallel = is_parallel_prob > self.threshold
            
            # 生成分解建议
            suggested_decomposition = None
            parallel_groups = []
            
            if is_parallel:
                suggested_decomposition = self._generate_decomposition_suggestion(features)
                # 简化：基于特征生成并行组
                if features.get("has_and", 0) > 0 or features.get("has_and_connector", 0) > 0:
                    parallel_groups = self._identify_parallel_groups(query)
            
            return {
                "is_parallel": bool(is_parallel),
                "confidence": float(is_parallel_prob),
                "suggested_decomposition": suggested_decomposition,
                "parallel_groups": parallel_groups,
                "method": "ml_model"
            }
        except Exception as e:
            self.logger.warning(f"⚠️ ML模型预测失败，回退到规则版本: {e}")
            return self._rule_based_predict(features, query)
    
    def _identify_parallel_groups(self, query: str) -> List[str]:
        """识别并行组"""
        groups = []
        query_lower = query.lower()
        
        # 检测"and"连接的独立条件
        if " and " in query_lower or "并且" in query or "而且" in query:
            # 简单的分割（后续可以用更智能的方法）
            parts = re.split(r'\s+and\s+|\s+并且\s+|\s+而且\s+', query, flags=re.IGNORECASE)
            if len(parts) >= 2:
                groups = [f"group_{i+1}" for i in range(len(parts))]
        
        return groups
    
    def _suggest_decomposition(self, query: str) -> Dict[str, Any]:
        """建议分解方式"""
        try:
            features = self.feature_extractor.extract_features(query)
            suggestion = self._generate_decomposition_suggestion(features)
            
            if suggestion:
                return {
                    "method": suggestion.get("type", "split_by_and"),
                    "description": suggestion.get("description", ""),
                    "confidence": suggestion.get("confidence", 0.5),
                    "num_groups": len(self._identify_parallel_groups(query))
                }
            else:
                return {
                    "method": "split_by_and",
                    "num_groups": len(self._identify_parallel_groups(query))
                }
        except Exception as e:
            self.logger.warning(f"生成分解建议失败: {e}")
            return {
                "method": "split_by_and",
                "num_groups": len(self._identify_parallel_groups(query))
            }
    
    def _generate_decomposition_suggestion(self, features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """生成分解建议"""
        try:
            suggestions = []
            
            # 基于特征生成建议
            if features.get("has_and", 0) > 0:
                suggestions.append({
                    "type": "split_by_and",
                    "description": "按'and'分割为独立查询",
                    "confidence": 0.8
                })
            
            if features.get("has_or", 0) > 0:
                suggestions.append({
                    "type": "split_by_or",
                    "description": "按'or'分割为替代查询",
                    "confidence": 0.7
                })
            
            if features.get("question_count", 0) > 1:
                suggestions.append({
                    "type": "split_by_questions",
                    "description": "按问题数量分割",
                    "confidence": 0.6
                })
            
            if suggestions:
                # 返回置信度最高的建议
                best_suggestion = max(suggestions, key=lambda x: x.get("confidence", 0))
                return best_suggestion
            
            return None
        except Exception as e:
            self.logger.warning(f"生成分解建议失败: {e}")
            return None
    
    def train(self, training_data: List[Any], labels: Optional[List[Any]] = None) -> Dict[str, Any]:
        """训练模型
        
        Args:
            training_data: 训练数据（查询文本列表）
            labels: 标签（是否并行，布尔值列表）
            
        Returns:
            训练结果字典
        """
        if labels is None:
            self.logger.error("❌ 监督学习需要标签")
            return {"success": False, "error": "Labels required for supervised learning"}
        
        try:
            import time
            import numpy as np
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            start_time = time.time()
            
            # 提取特征
            self.logger.info(f"📊 提取特征中... ({len(training_data)} 条数据)")
            X = [self.feature_extractor.extract_features(query) for query in training_data]
            
            # 转换为numpy数组
            X_array = np.array([list(features.values()) for features in X])
            y_array = np.array([1 if label else 0 for label in labels])
            
            # 分割训练和测试数据
            test_size = self.config.get("test_size", 0.2)
            random_state = self.config.get("random_state", 42)
            X_train, X_test, y_train, y_test = train_test_split(
                X_array, y_array, test_size=test_size, random_state=random_state, stratify=y_array
            )
            
            # 训练随机森林分类器
            n_estimators = self.config.get("n_estimators", 100)
            max_depth = self.config.get("max_depth", 10)
            
            # 🚀 改进：计算类别权重，处理数据不平衡问题
            from sklearn.utils.class_weight import compute_class_weight
            classes = np.unique(y_train)
            if len(classes) > 1:
                class_weights = compute_class_weight('balanced', classes=classes, y=y_train)
                class_weight_dict = dict(zip(classes, class_weights))
                self.logger.info(f"   类别权重: {class_weight_dict} (用于处理数据不平衡)")
            else:
                class_weight_dict = 'balanced'
                self.logger.warning(f"⚠️ 只有一个类别，使用balanced权重")
            
            self.logger.info(f"🌲 训练随机森林分类器 (n_estimators={n_estimators}, max_depth={max_depth})...")
            self.model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state,
                n_jobs=-1,
                class_weight=class_weight_dict  # 🚀 添加类别权重平衡
            )
            self.model.fit(X_train, y_train)
            self.is_trained = True
            
            # 评估模型
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            training_time = time.time() - start_time
            
            self.logger.info(f"✅ 训练完成！准确率: {accuracy:.3f}, F1: {f1:.3f}, 训练时间: {training_time:.2f}s")
            
            return {
                "success": True,
                "training_samples": len(training_data),
                "test_samples": len(X_test),
                "model_type": "random_forest",
                "metrics": {
                    "accuracy": float(accuracy),
                    "precision": float(precision),
                    "recall": float(recall),
                    "f1_score": float(f1)
                },
                "training_time": training_time
            }
        except ImportError as e:
            self.logger.warning(f"⚠️ sklearn未安装，使用规则版本: {e}")
            return {
                "success": True,
                "training_samples": len(training_data),
                "model_type": "rule_based",
                "note": "sklearn not available, using rule-based classifier"
            }
        except Exception as e:
            self.logger.error(f"❌ 训练失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    def _load_model_impl(self, model_path: str):
        """加载模型的具体实现"""
        try:
            import pickle
            import os
            
            if not os.path.exists(model_path):
                self.logger.warning(f"⚠️ 模型文件不存在: {model_path}")
                return
            
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            self.is_trained = True
            self.logger.info(f"✅ 成功加载模型: {model_path}")
            
        except ImportError:
            self.logger.warning("⚠️ pickle模块不可用，无法加载模型")
        except Exception as e:
            self.logger.error(f"❌ 加载模型失败: {e}")
            raise
    
    def _save_model_impl(self, model_path: str):
        """保存模型的具体实现"""
        try:
            import pickle
            import os
            
            if self.model is None:
                self.logger.warning("⚠️ 模型未训练，无法保存")
                return
            
            # 确保目录存在
            os.makedirs(os.path.dirname(model_path) if os.path.dirname(model_path) else '.', exist_ok=True)
            
            with open(model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            self.logger.info(f"✅ 成功保存模型: {model_path}")
            
        except ImportError:
            self.logger.warning("⚠️ pickle模块不可用，无法保存模型")
        except Exception as e:
            self.logger.error(f"❌ 保存模型失败: {e}")
            raise
    
    def _evaluate_impl(self, test_data: List[Any], test_labels: List[Any]) -> Dict[str, float]:
        """评估模型性能"""
        if not self.is_trained or self.model is None:
            return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}
        
        try:
            import numpy as np
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            # 提取特征
            X = [self.feature_extractor.extract_features(query) for query in test_data]
            X_array = np.array([list(features.values()) for features in X])
            y_array = np.array([1 if label else 0 for label in test_labels])
            
            # 预测
            y_pred = self.model.predict(X_array)
            
            # 计算指标
            accuracy = accuracy_score(y_array, y_pred)
            precision = precision_score(y_array, y_pred, zero_division=0)
            recall = recall_score(y_array, y_pred, zero_division=0)
            f1 = f1_score(y_array, y_pred, zero_division=0)
            
            return {
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1)
            }
        except Exception as e:
            self.logger.error(f"❌ 评估失败: {e}")
            return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}


class QueryFeatureExtractor:
    """查询特征提取器"""
    
    def __init__(self):
        """初始化特征提取器"""
        self.logger = logging.getLogger(__name__)
    
    def extract_features(self, query: str) -> Dict[str, Any]:
        """提取查询的机器学习特征
        
        Args:
            query: 查询文本
            
        Returns:
            特征字典
        """
        query_lower = query.lower()
        
        features = {
            # 结构特征
            "has_and_connector": int("并且" in query or "而且" in query or " and " in query_lower),
            "num_condition_clauses": self._count_conditions(query),
            
            # 语法特征
            "query_length": len(query),
            "has_parentheses": int("(" in query and ")" in query),
            
            # 模式特征
            "matches_parallel_pattern": self._match_known_patterns(query),
            
            # 实体类型特征（简单版本，后续可以用NER）
            "num_distinct_entities": self._count_entities(query),
            
            # 依赖关系特征
            "estimated_dependency_depth": self._estimate_dependency_depth(query)
        }
        
        return features
    
    def _count_conditions(self, query: str) -> int:
        """统计条件子句数量"""
        # 简单的统计方法：检测"如果"、"当"等条件词
        condition_keywords = ["如果", "当", "if", "when", "given", "assuming"]
        count = sum(1 for keyword in condition_keywords if keyword.lower() in query.lower())
        return max(count, 1)  # 至少1个
    
    def _match_known_patterns(self, query: str) -> bool:
        """匹配已知的并行模式"""
        patterns = [
            r".*and.*same.*as.*and.*same.*as.*",  # "A and B same as X and Y"
            r".*如果.*并且.*",  # "如果A并且B"
            r".*both.*and.*",  # "both A and B"
        ]
        
        query_lower = query.lower()
        return any(re.search(pattern, query_lower, re.IGNORECASE) for pattern in patterns)
    
    def _count_entities(self, query: str) -> int:
        """统计实体数量（简单版本）"""
        # 检测大写字母开头的词（可能是人名、地名等）
        # 这是一个简单的启发式方法，后续可以用NER模型
        words = query.split()
        capitalized_words = [w for w in words if w and w[0].isupper()]
        return len(set(capitalized_words))
    
    def _estimate_dependency_depth(self, query: str) -> int:
        """估计依赖深度"""
        # 检测嵌套的所有格（X's Y's Z）
        possessive_count = query.count("'s")
        return possessive_count

