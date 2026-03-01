"""
逻辑结构解析器 - 解析查询中的逻辑结构（条件、结果、OR分支等）

初始版本：基于规则的解析器
未来版本：基于Transformer的Token分类模型
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from .base_ml_component import BaseMLComponent

logger = logging.getLogger(__name__)


class LogicStructureParser(BaseMLComponent):
    """逻辑结构解析器
    
    解析查询中的逻辑结构，识别：
    - 条件（IF-THEN）
    - 结果（THEN）
    - 替代（OR）
    - AND连接
    - 嵌套结构
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化逻辑结构解析器
        
        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 🚀 增强：自动加载预训练模型
        from src.core.reasoning.ml_framework.model_auto_loader import auto_load_model
        if not auto_load_model(self, "logic_structure_parser", config):
            # 如果加载失败，使用规则版本
            self.logger.info("✅ 使用基于规则的逻辑结构解析器（初始版本）")
        
        # 逻辑关键词模式
        self.condition_patterns = [
            r'\bif\s+(.+?)\s+then\b',
            r'\bwhen\s+(.+?)\s+then\b',
            r'\bwhenever\s+(.+?)\s+then\b',
            r'\bprovided\s+that\s+(.+?)\s+then\b',
        ]
        
        self.result_patterns = [
            r'\bthen\s+(.+?)(?:\s+else|\s+or|$)',
            r'\bwhat\s+is\s+(.+?)(?:\s+if|\s+when|$)',
        ]
        
        self.or_patterns = [
            r'\bor\b',
            r'\balternatively\b',
            r'\botherwise\b',
        ]
        
        self.and_patterns = [
            r'\band\b',
            r'\bplus\b',
            r'\balso\b',
        ]
        
        # 嵌套结构检测
        self.nested_patterns = [
            r'\([^)]+\)',  # 括号
            r'\[[^\]]+\]',  # 方括号
        ]
        
        # 标签映射（用于ML模型）
        self.label_mapping = {}
        
    def predict(self, query: str) -> Dict[str, Any]:
        """解析查询的逻辑结构
        
        Args:
            query: 查询文本
            
        Returns:
            解析结果字典，包含：
            - structure_type: 结构类型（conditional, or_branch, and_chain, simple）
            - conditions: 条件列表
            - results: 结果列表
            - or_branches: OR分支列表
            - and_components: AND组件列表
            - nested_structures: 嵌套结构列表
            - confidence: 置信度（0-1）
            - metadata: 其他元数据
        """
        try:
            query_lower = query.lower()
            
            # 1. 检测条件结构（IF-THEN）
            conditions = self._extract_conditions(query)
            results = self._extract_results(query)
            
            # 2. 检测OR分支
            or_branches = self._extract_or_branches(query)
            
            # 3. 检测AND连接
            and_components = self._extract_and_components(query)
            
            # 4. 检测嵌套结构
            nested_structures = self._extract_nested_structures(query)
            
            # 5. 确定结构类型（如果模型已训练，使用ML模型；否则使用规则）
            if self.is_trained and self.model is not None:
                try:
                    import numpy as np
                    features = self._extract_features_for_training(query)
                    X = np.array([list(features.values())]).reshape(1, -1)
                    pred_idx = self.model.predict(X)[0]
                    
                    # 反向映射标签
                    if hasattr(self, 'label_mapping') and self.label_mapping:
                        idx_to_label = {v: k for k, v in self.label_mapping.items()}
                        structure_type = idx_to_label.get(pred_idx, "simple")
                    else:
                        structure_type = self._determine_structure_type(
                            conditions, results, or_branches, and_components, nested_structures
                        )
                except Exception as e:
                    self.logger.warning(f"⚠️ ML模型预测失败，使用规则版本: {e}")
                    structure_type = self._determine_structure_type(
                        conditions, results, or_branches, and_components, nested_structures
                    )
            else:
                structure_type = self._determine_structure_type(
                    conditions, results, or_branches, and_components, nested_structures
                )
            
            # 6. 计算置信度
            confidence = self._calculate_confidence(
                conditions, results, or_branches, and_components, nested_structures
            )
            
            return {
                "prediction": {
                    "structure_type": structure_type,
                    "conditions": conditions,
                    "results": results,
                    "or_branches": or_branches,
                    "and_components": and_components,
                    "nested_structures": nested_structures,
                },
                "confidence": confidence,
                "metadata": {
                    "query": query,
                    "parser_version": "rule_based_v1",
                }
            }
            
        except Exception as e:
            self.logger.error(f"解析逻辑结构失败: {e}")
            return {
                "prediction": {
                    "structure_type": "simple",
                    "conditions": [],
                    "results": [],
                    "or_branches": [],
                    "and_components": [],
                    "nested_structures": [],
                },
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }
    
    def _extract_conditions(self, query: str) -> List[Dict[str, Any]]:
        """提取条件部分"""
        conditions = []
        query_lower = query.lower()
        
        for pattern in self.condition_patterns:
            matches = re.finditer(pattern, query_lower, re.IGNORECASE)
            for match in matches:
                condition_text = match.group(1).strip()
                conditions.append({
                    "text": condition_text,
                    "start": match.start(),
                    "end": match.end(),
                    "pattern": pattern,
                })
        
        return conditions
    
    def _extract_results(self, query: str) -> List[Dict[str, Any]]:
        """提取结果部分"""
        results = []
        query_lower = query.lower()
        
        for pattern in self.result_patterns:
            matches = re.finditer(pattern, query_lower, re.IGNORECASE)
            for match in matches:
                result_text = match.group(1).strip()
                results.append({
                    "text": result_text,
                    "start": match.start(),
                    "end": match.end(),
                    "pattern": pattern,
                })
        
        return results
    
    def _extract_or_branches(self, query: str) -> List[Dict[str, Any]]:
        """提取OR分支"""
        or_branches = []
        query_lower = query.lower()
        
        # 查找所有OR关键词的位置
        or_positions = []
        for pattern in self.or_patterns:
            matches = re.finditer(r'\b' + pattern + r'\b', query_lower, re.IGNORECASE)
            for match in matches:
                or_positions.append(match.start())
        
        if or_positions:
            # 根据OR位置分割查询
            parts = re.split(r'\b(?:or|alternatively|otherwise)\b', query_lower, flags=re.IGNORECASE)
            for i, part in enumerate(parts):
                if part.strip():
                    or_branches.append({
                        "text": part.strip(),
                        "branch_index": i,
                    })
        
        return or_branches
    
    def _extract_and_components(self, query: str) -> List[Dict[str, Any]]:
        """提取AND连接的组件"""
        and_components = []
        query_lower = query.lower()
        
        # 查找所有AND关键词的位置
        and_positions = []
        for pattern in self.and_patterns:
            matches = re.finditer(r'\b' + pattern + r'\b', query_lower, re.IGNORECASE)
            for match in matches:
                and_positions.append(match.start())
        
        if and_positions:
            # 根据AND位置分割查询
            parts = re.split(r'\b(?:and|plus|also)\b', query_lower, flags=re.IGNORECASE)
            for i, part in enumerate(parts):
                if part.strip():
                    and_components.append({
                        "text": part.strip(),
                        "component_index": i,
                    })
        
        return and_components
    
    def _extract_nested_structures(self, query: str) -> List[Dict[str, Any]]:
        """提取嵌套结构"""
        nested_structures = []
        
        for pattern in self.nested_patterns:
            matches = re.finditer(pattern, query)
            for match in matches:
                nested_structures.append({
                    "text": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "type": "parentheses" if pattern.startswith(r'\(') else "brackets",
                })
        
        return nested_structures
    
    def _determine_structure_type(
        self,
        conditions: List[Dict[str, Any]],
        results: List[Dict[str, Any]],
        or_branches: List[Dict[str, Any]],
        and_components: List[Dict[str, Any]],
        nested_structures: List[Dict[str, Any]]
    ) -> str:
        """确定结构类型"""
        if conditions and results:
            return "conditional"  # IF-THEN结构
        elif len(or_branches) > 1:
            return "or_branch"  # OR分支结构
        elif len(and_components) > 1:
            return "and_chain"  # AND连接结构
        elif nested_structures:
            return "nested"  # 嵌套结构
        else:
            return "simple"  # 简单查询
    
    def _calculate_confidence(
        self,
        conditions: List[Dict[str, Any]],
        results: List[Dict[str, Any]],
        or_branches: List[Dict[str, Any]],
        and_components: List[Dict[str, Any]],
        nested_structures: List[Dict[str, Any]]
    ) -> float:
        """计算解析置信度"""
        confidence = 0.5  # 基础置信度
        
        # 如果找到明确的条件和结果，提高置信度
        if conditions and results:
            confidence = 0.9
        
        # 如果找到OR分支，提高置信度
        if len(or_branches) > 1:
            confidence = max(confidence, 0.8)
        
        # 如果找到AND连接，提高置信度
        if len(and_components) > 1:
            confidence = max(confidence, 0.7)
        
        # 如果找到嵌套结构，稍微提高置信度
        if nested_structures:
            confidence = min(confidence + 0.1, 1.0)
        
        return confidence
    
    def train(self, training_data: List[Any], labels: Optional[List[Any]] = None) -> Dict[str, Any]:
        """训练模型（初始版本：RandomForest分类器，未来：Transformer模型）
        
        Args:
            training_data: 训练数据（查询文本列表）
            labels: 标签（逻辑结构类型列表，如["conditional", "or_branch", "and_chain", "simple"]）
            
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
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
            
            start_time = time.time()
            
            # 提取特征
            self.logger.info(f"📊 提取特征中... ({len(training_data)} 条数据)")
            X = []
            y = []
            
            for query, label in zip(training_data, labels):
                # 提取特征
                features = self._extract_features_for_training(query)
                X.append(list(features.values()))
                y.append(label)
            
            X_array = np.array(X)
            
            # 将标签转换为数字
            unique_labels = sorted(list(set(y)))
            label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
            y_array = np.array([label_to_idx[label] for label in y])
            self.label_mapping = label_to_idx  # 保存标签映射
            
            # 分割训练和测试数据
            test_size = self.config.get("test_size", 0.2)
            random_state = self.config.get("random_state", 42)
            X_train, X_test, y_train, y_test = train_test_split(
                X_array, y_array, test_size=test_size, random_state=random_state, stratify=y_array
            )
            
            # 训练随机森林分类器
            n_estimators = self.config.get("n_estimators", 100)
            max_depth = self.config.get("max_depth", 10)
            
            self.logger.info(f"🌲 训练随机森林分类器 (n_estimators={n_estimators}, max_depth={max_depth})...")
            self.model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state,
                n_jobs=-1
            )
            self.model.fit(X_train, y_train)
            self.is_trained = True
            
            # 评估模型
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
                "model_type": "random_forest",
                "metrics": {
                    "accuracy": float(accuracy),
                    "precision": float(precision),
                    "recall": float(recall),
                    "f1_score": float(f1)
                },
                "training_time": training_time,
                "label_mapping": label_to_idx
            }
        except ImportError as e:
            self.logger.warning(f"⚠️ sklearn未安装，使用规则版本: {e}")
            return {
                "success": True,
                "training_samples": len(training_data),
                "model_type": "rule_based",
                "note": "sklearn not available, using rule-based parser"
            }
        except Exception as e:
            self.logger.error(f"❌ 训练失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    def _extract_features_for_training(self, query: str) -> Dict[str, float]:
        """提取用于训练的特征"""
        query_lower = query.lower()
        features = {}
        
        # 结构特征
        features["has_if"] = 1.0 if "if" in query_lower else 0.0
        features["has_then"] = 1.0 if "then" in query_lower else 0.0
        features["has_or"] = 1.0 if " or " in query_lower else 0.0
        features["has_and"] = 1.0 if " and " in query_lower else 0.0
        features["has_when"] = 1.0 if "when" in query_lower else 0.0
        
        # 计数特征
        features["or_count"] = float(query_lower.count(" or "))
        features["and_count"] = float(query_lower.count(" and "))
        features["if_count"] = float(query_lower.count(" if "))
        
        # 括号特征
        features["has_parentheses"] = 1.0 if "(" in query and ")" in query else 0.0
        features["has_brackets"] = 1.0 if "[" in query and "]" in query else 0.0
        
        # 长度特征
        features["query_length"] = float(len(query))
        features["word_count"] = float(len(query.split()))
        
        # 条件模式匹配
        condition_matches = sum(1 for pattern in self.condition_patterns if re.search(pattern, query_lower))
        features["condition_pattern_matches"] = float(condition_matches)
        
        # OR模式匹配
        or_matches = sum(1 for pattern in self.or_patterns if re.search(pattern, query_lower))
        features["or_pattern_matches"] = float(or_matches)
        
        return features
    
    def _load_model_impl(self, model_path: str):
        """加载模型"""
        try:
            import pickle
            import os
            
            if not os.path.exists(model_path):
                self.logger.warning(f"⚠️ 模型文件不存在: {model_path}")
                return
            
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
                self.model = data.get("model")
                self.label_mapping = data.get("label_mapping", {})
            
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
            
            data = {
                "model": self.model,
                "label_mapping": getattr(self, 'label_mapping', {})
            }
            
            with open(model_path, 'wb') as f:
                pickle.dump(data, f)
            
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
            import numpy as np
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            # 提取特征
            X = [self._extract_features_for_training(query) for query in test_data]
            X_array = np.array([list(features.values()) for features in X])
            
            # 转换标签
            if hasattr(self, 'label_mapping') and self.label_mapping:
                y_array = np.array([self.label_mapping.get(label, 0) for label in test_labels])
            else:
                # 如果没有标签映射，创建临时映射
                unique_labels = sorted(list(set(test_labels)))
                label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
                y_array = np.array([label_to_idx[label] for label in test_labels])
            
            # 预测
            y_pred = self.model.predict(X_array)
            
            # 计算指标
            accuracy = accuracy_score(y_array, y_pred)
            precision = precision_score(y_array, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_array, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_array, y_pred, average='weighted', zero_division=0)
            
            return {
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1)
            }
        except Exception as e:
            self.logger.error(f"❌ 评估失败: {e}")
            return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

