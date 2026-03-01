"""
Few-shot模式学习器 - 从少量示例学习新的查询模式

初始版本：基于规则的模式匹配
未来版本：基于Sentence-BERT的模式编码器
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from .base_ml_component import BaseMLComponent

logger = logging.getLogger(__name__)


class FewShotPatternLearner(BaseMLComponent):
    """Few-shot模式学习器
    
    从少量示例（3-5个）学习新的查询模式：
    - 模式识别
    - 模式抽象
    - 模式匹配
    - 模式模板生成
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化Few-shot模式学习器
        
        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 🚀 增强：自动加载预训练模型
        from src.core.reasoning.ml_framework.model_auto_loader import auto_load_model
        if not auto_load_model(self, "fewshot_pattern_learner", config):
            # 如果加载失败，使用规则版本
            self.logger.info("✅ 使用基于规则的少样本模式学习器（初始版本）")
        
        # 模式记忆（存储已知模式的模板）
        self.pattern_memory = {}
        
        # 模式计数器
        self.pattern_count = 0
        
    def predict(self, query: str) -> Dict[str, Any]:
        """识别查询模式
        
        Args:
            query: 查询文本
            
        Returns:
            模式识别结果，包含：
            - matched_pattern: 匹配的模式ID
            - pattern_template: 模式模板
            - confidence: 匹配置信度
            - metadata: 其他元数据
        """
        try:
            # 1. 尝试匹配已知模式
            best_match = self._match_known_patterns(query)
            
            if best_match and best_match["confidence"] > 0.7:
                return {
                    "prediction": {
                        "matched_pattern": best_match["pattern_id"],
                        "pattern_template": best_match["template"],
                        "extracted_variables": best_match["variables"],
                    },
                    "confidence": best_match["confidence"],
                    "metadata": {
                        "query": query,
                        "match_method": "known_pattern",
                    }
                }
            else:
                # 2. 未匹配到已知模式，返回通用模式
                return {
                    "prediction": {
                        "matched_pattern": None,
                        "pattern_template": None,
                        "extracted_variables": {},
                    },
                    "confidence": 0.0,
                    "metadata": {
                        "query": query,
                        "match_method": "no_match",
                    }
                }
                
        except Exception as e:
            self.logger.error(f"模式识别失败: {e}")
            return {
                "prediction": {
                    "matched_pattern": None,
                    "pattern_template": None,
                    "extracted_variables": {},
                },
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }
    
    def learn_from_examples(
        self,
        examples: List[Dict[str, Any]],
        pattern_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """从示例学习新模式
        
        Args:
            examples: 示例列表，每个示例包含：
                - query: 查询文本
                - steps: 推理步骤（可选）
            pattern_name: 模式名称（可选）
            
        Returns:
            学习结果，包含：
                - pattern_id: 模式ID
                - pattern_template: 模式模板
                - confidence: 学习置信度
        """
        try:
            if len(examples) < 2:
                self.logger.warning("⚠️ 示例数量不足，至少需要2个示例")
                return {
                    "pattern_id": None,
                    "pattern_template": None,
                    "confidence": 0.0,
                    "error": "示例数量不足"
                }
            
            # 1. 提取共同模式
            common_pattern = self._extract_common_pattern(examples)
            
            # 2. 生成模式模板
            pattern_template = self._generate_pattern_template(common_pattern, examples)
            
            # 3. 生成模式ID
            pattern_id = pattern_name or f"pattern_{self.pattern_count}"
            self.pattern_count += 1
            
            # 4. 存储模式
            self.pattern_memory[pattern_id] = {
                "template": pattern_template,
                "examples": examples,
                "usage_count": 0,
            }
            
            self.logger.info(f"✅ 学习新模式: {pattern_id}")
            
            return {
                "pattern_id": pattern_id,
                "pattern_template": pattern_template,
                "confidence": 0.8,  # 初始置信度
            }
            
        except Exception as e:
            self.logger.error(f"学习模式失败: {e}")
            return {
                "pattern_id": None,
                "pattern_template": None,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _extract_common_pattern(self, examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取共同模式"""
        queries = [ex["query"] for ex in examples]
        
        # 简单的模式提取：查找共同的关键词和结构
        common_keywords = self._find_common_keywords(queries)
        common_structure = self._find_common_structure(queries)
        
        return {
            "keywords": common_keywords,
            "structure": common_structure,
        }
    
    def _find_common_keywords(self, queries: List[str]) -> List[str]:
        """查找共同关键词"""
        if not queries:
            return []
        
        # 提取所有查询的关键词
        all_keywords = []
        for query in queries:
            words = re.findall(r'\b\w+\b', query.lower())
            all_keywords.append(set(words))
        
        # 找到所有查询都包含的关键词
        common = set.intersection(*all_keywords) if all_keywords else set()
        
        # 过滤停用词
        stop_words = {'the', 'a', 'an', 'is', 'was', 'are', 'were', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from', 'as', 'and', 'or', 'but', 'what', 'who', 'when', 'where', 'why', 'how'}
        common = {w for w in common if w not in stop_words}
        
        return list(common)
    
    def _find_common_structure(self, queries: List[str]) -> str:
        """查找共同结构"""
        # 简单的结构识别：检查是否有共同的问题词和结构
        question_words = ['who', 'what', 'when', 'where', 'why', 'how', 'which']
        
        structures = []
        for query in queries:
            query_lower = query.lower()
            # 检查问题词
            qw = [w for w in question_words if query_lower.startswith(w)]
            if qw:
                structures.append(qw[0])
        
        # 返回最常见的问题词
        if structures:
            from collections import Counter
            most_common = Counter(structures).most_common(1)
            if most_common:
                return most_common[0][0]
        
        return "unknown"
    
    def _generate_pattern_template(
        self,
        common_pattern: Dict[str, Any],
        examples: List[Dict[str, Any]]
    ) -> str:
        """生成模式模板"""
        # 简单的模板生成：使用占位符替换变量部分
        if not examples:
            return ""
        
        # 使用第一个示例作为基础
        base_query = examples[0]["query"]
        
        # 替换共同关键词为占位符
        template = base_query
        for keyword in common_pattern.get("keywords", []):
            # 使用占位符替换关键词
            template = re.sub(r'\b' + keyword + r'\b', f'[{keyword.upper()}]', template, flags=re.IGNORECASE)
        
        return template
    
    def _match_known_patterns(self, query: str) -> Optional[Dict[str, Any]]:
        """匹配已知模式"""
        best_match = None
        best_confidence = 0.0
        
        for pattern_id, pattern_data in self.pattern_memory.items():
            template = pattern_data["template"]
            
            # 简单的模式匹配：检查关键词匹配
            match_result = self._match_pattern(query, template)
            
            if match_result["confidence"] > best_confidence:
                best_confidence = match_result["confidence"]
                best_match = {
                    "pattern_id": pattern_id,
                    "template": template,
                    "variables": match_result["variables"],
                    "confidence": match_result["confidence"],
                }
        
        return best_match
    
    def _match_pattern(self, query: str, template: str) -> Dict[str, Any]:
        """匹配模式和查询"""
        # 简单的匹配：检查关键词重叠
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        template_words = set(re.findall(r'\b\w+\b', template.lower()))
        
        # 移除占位符标记
        template_words = {w for w in template_words if not w.startswith('[') and not w.endswith(']')}
        
        # 计算重叠度
        if template_words:
            overlap = len(query_words & template_words) / len(template_words)
        else:
            overlap = 0.0
        
        return {
            "confidence": overlap,
            "variables": {},  # 未来实现：提取变量值
        }
    
    def train(self, training_data: List[Any], labels: Optional[List[Any]] = None) -> Dict[str, Any]:
        """训练模型（初始版本：TF-IDF + 相似度，未来：Sentence-BERT模型）
        
        Args:
            training_data: 训练数据（模式文本列表）
            labels: 标签（模式类别列表）
            
        Returns:
            训练结果字典
        """
        if labels is None:
            self.logger.error("❌ 监督学习需要标签")
            return {"success": False, "error": "Labels required for supervised learning"}
        
        try:
            import time
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            from sklearn.naive_bayes import MultinomialNB
            from sklearn.pipeline import Pipeline
            
            start_time = time.time()
            
            # 准备数据
            self.logger.info(f"📊 准备训练数据... ({len(training_data)} 条数据)")
            
            # 分割训练和测试数据
            test_size = self.config.get("test_size", 0.2)
            random_state = self.config.get("random_state", 42)
            
            # 🚀 修复：检查数据是否可以进行分层抽样
            # 如果某个类别只有1个样本，无法进行分层抽样，需要跳过分层
            from collections import Counter
            label_counts = Counter(labels)
            can_stratify = all(count >= 2 for count in label_counts.values())
            
            if can_stratify:
                X_train, X_test, y_train, y_test = train_test_split(
                    training_data, labels, test_size=test_size, random_state=random_state, stratify=labels
                )
            else:
                # 如果数据不平衡，跳过分层抽样
                self.logger.warning(f"⚠️ 数据不平衡，某些类别样本数 < 2，跳过分层抽样")
                self.logger.warning(f"   类别分布: {dict(label_counts)}")
                X_train, X_test, y_train, y_test = train_test_split(
                    training_data, labels, test_size=test_size, random_state=random_state
                )
            
            # 🚀 尝试使用Sentence-BERT，如果不可用则使用TF-IDF + 朴素贝叶斯
            use_sentence_bert = self.config.get("use_sentence_bert", True)
            
            try:
                if use_sentence_bert:
                    from sentence_transformers import SentenceTransformer
                    from sklearn.linear_model import LogisticRegression
                    from sklearn.preprocessing import LabelEncoder
                    
                    # 加载Sentence-BERT模型
                    model_name = self.config.get("sentence_bert_model", "all-MiniLM-L6-v2")
                    self.logger.info(f"📚 加载Sentence-BERT模型: {model_name}...")
                    sentence_model = SentenceTransformer(model_name)
                    
                    # 生成嵌入
                    self.logger.info("📊 生成文本嵌入...")
                    X_train_embeddings = sentence_model.encode(X_train, show_progress_bar=False)
                    X_test_embeddings = sentence_model.encode(X_test, show_progress_bar=False)
                    
                    # 标签编码
                    self.label_encoder = LabelEncoder()
                    y_train_encoded = self.label_encoder.fit_transform(y_train)
                    y_test_encoded = self.label_encoder.transform(y_test)
                    
                    # 训练分类器（使用逻辑回归）
                    self.logger.info("🧠 训练逻辑回归分类器...")
                    self.model = LogisticRegression(max_iter=1000, random_state=random_state)
                    self.model.fit(X_train_embeddings, y_train_encoded)
                    
                    # 保存Sentence-BERT模型
                    self.sentence_model = sentence_model
                    self.model_type = "sentence_bert"
                    self.is_trained = True
                    self.logger.info("✅ Sentence-BERT模型训练完成")
                    
            except ImportError:
                # Sentence-Transformers不可用，使用TF-IDF
                self.logger.info("⚠️ Sentence-Transformers不可用，使用TF-IDF + 朴素贝叶斯")
                use_sentence_bert = False
            
            if not use_sentence_bert or not hasattr(self, 'model') or self.model is None:
                # 训练TF-IDF + 朴素贝叶斯分类器（fallback）
                self.logger.info("📚 训练TF-IDF + 朴素贝叶斯分类器...")
                self.model = Pipeline([
                    ('tfidf', TfidfVectorizer(max_features=1000, ngram_range=(1, 2))),
                    ('classifier', MultinomialNB())
                ])
                self.model.fit(X_train, y_train)
                self.model_type = "tfidf_naive_bayes"
                self.is_trained = True
            
            # 评估模型
            if hasattr(self, 'model_type') and self.model_type == "sentence_bert":
                y_pred_encoded = self.model.predict(X_test_embeddings)
                y_pred = self.label_encoder.inverse_transform(y_pred_encoded)
            else:
                y_pred = self.model.predict(X_test)
            
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            
            training_time = time.time() - start_time
            
            self.logger.info(f"✅ 训练完成！准确率: {accuracy:.3f}, F1: {f1:.3f}, 训练时间: {training_time:.2f}s")
            
            return {
                "success": True,
                "training_samples": len(training_data),
                "test_samples": len(X_test),
                "model_type": getattr(self, 'model_type', 'tfidf_naive_bayes'),
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
                "note": "sklearn not available, using rule-based learner"
            }
        except Exception as e:
            self.logger.error(f"❌ 训练失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    def _load_model_impl(self, model_path: str):
        """加载模型"""
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
        """保存模型"""
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
        """评估模型"""
        if not self.is_trained or self.model is None:
            return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}
        
        try:
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            # 预测
            y_pred = self.model.predict(test_data)
            
            # 计算指标
            accuracy = accuracy_score(test_labels, y_pred)
            precision = precision_score(test_labels, y_pred, average='weighted', zero_division=0)
            recall = recall_score(test_labels, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(test_labels, y_pred, average='weighted', zero_division=0)
            
            return {
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1)
            }
        except Exception as e:
            self.logger.error(f"❌ 评估失败: {e}")
            return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

