"""
深度置信度评估模型 - 使用深度学习模型评估步骤结果的置信度

初始版本：基于规则的特征提取和简单模型
未来版本：多模态特征融合的神经网络（LSTM + 注意力机制）
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from .base_ml_component import BaseMLComponent

logger = logging.getLogger(__name__)


# 🚀 修复：将LSTMWithAttention移到模块级别，避免pickle序列化失败
try:
    import torch
    import torch.nn as nn
    
    class LSTMWithAttention(nn.Module):
        """LSTM + 注意力模型（模块级别，可被pickle序列化）"""
        def __init__(self, input_size, hidden_size=64, num_layers=2, dropout=0.2):
            super().__init__()
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                               batch_first=True, dropout=dropout if num_layers > 1 else 0)
            self.attention = nn.MultiheadAttention(hidden_size, num_heads=4, batch_first=True)
            self.fc1 = nn.Linear(hidden_size, 32)
            self.fc2 = nn.Linear(32, 1)
            self.dropout = nn.Dropout(dropout)
            self.relu = nn.ReLU()
            self.sigmoid = nn.Sigmoid()
        
        def forward(self, x):
            # x shape: (batch, seq_len, features)
            # 如果输入是2D，添加序列维度
            if len(x.shape) == 2:
                x = x.unsqueeze(1)  # (batch, 1, features)
            
            lstm_out, _ = self.lstm(x)  # (batch, seq_len, hidden_size)
            attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)  # (batch, seq_len, hidden_size)
            # 取最后一个时间步
            out = attn_out[:, -1, :]  # (batch, hidden_size)
            out = self.fc1(out)
            out = self.relu(out)
            out = self.dropout(out)
            out = self.fc2(out)
            out = self.sigmoid(out)
            return out.squeeze(-1)
except ImportError:
    LSTMWithAttention = None


class DeepConfidenceEstimator(BaseMLComponent):
    """深度置信度评估模型
    
    评估步骤结果的置信度，基于：
    - 查询嵌入
    - 结果嵌入
    - 上下文嵌入
    - 证据质量
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化深度置信度评估模型
        
        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 特征权重（未来：由神经网络学习）
        self.feature_weights = {
            "query_result_similarity": 0.3,
            "evidence_support": 0.3,
            "answer_completeness": 0.2,
            "answer_type_match": 0.1,
            "context_relevance": 0.1,
        }
        
        # 用于ML模型预测的scaler
        self.scaler = None
        
        # 🚀 增强：自动加载预训练模型
        from src.core.reasoning.ml_framework.model_auto_loader import auto_load_model
        if not auto_load_model(self, "deep_confidence_estimator", config):
            # 如果加载失败，使用规则版本
            self.logger.info("✅ 使用基于规则的置信度评估器（初始版本）")
        
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估置信度
        
        Args:
            input_data: 输入数据字典，包含：
                - query: 查询文本
                - answer: 答案文本
                - evidence: 证据列表
                - context: 上下文信息
                
        Returns:
            预测结果字典，包含：
                - prediction: 置信度分数（0-1）
                - confidence: 评估置信度
                - metadata: 特征分数详情
        """
        try:
            query = input_data.get("query", "")
            answer = input_data.get("answer", "")
            evidence = input_data.get("evidence", [])
            context = input_data.get("context", {})
            
            # 1. 提取特征
            features = self._extract_features(query, answer, evidence, context)
            
            # 2. 如果模型已训练，使用ML模型；否则使用规则版本
            if self.is_trained and self.model is not None:
                try:
                    import numpy as np
                    X = np.array([list(features.values())]).reshape(1, -1)
                    
                    # 标准化
                    if hasattr(self, 'scaler') and self.scaler is not None:
                        X_scaled = self.scaler.transform(X)
                    else:
                        X_scaled = X
                    
                    # 预测
                    # 🚀 修复：如果model_type未设置，尝试自动检测
                    if not hasattr(self, 'model_type') or self.model_type is None:
                        # 自动检测模型类型
                        model_class_name = type(self.model).__name__
                        if 'LSTM' in model_class_name or 'Attention' in model_class_name:
                            self.model_type = "lstm_attention"
                            self.logger.debug(f"🔍 自动检测模型类型: {self.model_type} (基于类名: {model_class_name})")
                        elif hasattr(self.model, 'predict'):
                            self.model_type = "mlp_regressor"
                            self.logger.debug(f"🔍 自动检测模型类型: {self.model_type} (基于predict方法)")
                    
                    if hasattr(self, 'model_type') and self.model_type == "lstm_attention":
                        # LSTM模型预测（PyTorch模型，使用forward方法）
                        import torch
                        self.model.eval()
                        with torch.no_grad():
                            X_tensor = torch.FloatTensor(X_scaled).unsqueeze(1)
                            confidence_tensor = self.model(X_tensor)
                            # 🚀 修复：处理tensor输出，转换为numpy标量
                            if isinstance(confidence_tensor, torch.Tensor):
                                confidence = float(confidence_tensor.cpu().numpy()[0])
                            else:
                                confidence = float(confidence_tensor)
                    elif hasattr(self.model, 'predict'):
                        # MLP模型预测（scikit-learn模型，使用predict方法）
                        confidence = self.model.predict(X_scaled)[0]
                        # 🚀 修复：如果model_type未设置，设置为mlp_regressor
                        if not hasattr(self, 'model_type') or self.model_type is None:
                            self.model_type = "mlp_regressor"
                    else:
                        # 其他模型类型，尝试直接调用
                        confidence = 0.5  # 默认值
                        self.logger.warning(f"⚠️ 模型类型未知，无法预测，使用默认置信度0.5 | 模型类: {type(self.model).__name__}")
                    
                    confidence = max(0.0, min(1.0, float(confidence)))  # 限制在[0,1]范围
                    
                    return {
                        "prediction": float(confidence),
                        "confidence": 0.9,
                        "metadata": {
                            "features": features,
                            "model_version": "mlp_v1",
                            "method": "ml_model"
                        }
                    }
                except Exception as e:
                    self.logger.warning(f"⚠️ ML模型预测失败，使用规则版本: {e}")
            
            # Fallback: 使用规则版本
            confidence = self._calculate_confidence(features)
            final_confidence = self._post_process_confidence(confidence, features)
            
            return {
                "prediction": final_confidence,
                "confidence": 0.9,
                "metadata": {
                    "features": features,
                    "raw_confidence": confidence,
                    "model_version": "rule_based_v1",
                    "method": "rule_based"
                }
            }
            
        except Exception as e:
            self.logger.error(f"置信度评估失败: {e}")
            return {
                "prediction": 0.5,
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }
    
    def _extract_features(
        self,
        query: str,
        answer: str,
        evidence: List[Any],  # 🚀 修复：可以是Evidence对象列表或字典列表
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """提取特征"""
        features = {}
        
        # 1. 查询-答案相似度
        features["query_result_similarity"] = self._calculate_query_answer_similarity(query, answer)
        
        # 2. 证据支持度
        features["evidence_support"] = self._calculate_evidence_support(answer, evidence)
        
        # 3. 答案完整性
        features["answer_completeness"] = self._calculate_answer_completeness(answer, query)
        
        # 4. 答案类型匹配
        features["answer_type_match"] = self._calculate_answer_type_match(answer, query)
        
        # 5. 上下文相关性
        features["context_relevance"] = self._calculate_context_relevance(query, context)
        
        return features
    
    def _calculate_query_answer_similarity(self, query: str, answer: str) -> float:
        """计算查询-答案相似度"""
        if not query or not answer:
            return 0.0
        
        query_lower = query.lower()
        answer_lower = answer.lower()
        
        # 提取关键词
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        answer_words = set(re.findall(r'\b\w+\b', answer_lower))
        
        # 移除停用词
        stop_words = {'the', 'a', 'an', 'is', 'was', 'are', 'were', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from', 'as', 'and', 'or', 'but', 'what', 'who', 'when', 'where', 'why', 'how'}
        query_words = {w for w in query_words if w not in stop_words}
        answer_words = {w for w in answer_words if w not in stop_words}
        
        # 计算重叠度
        if query_words:
            overlap = len(query_words & answer_words) / len(query_words)
        else:
            overlap = 0.0
        
        return min(overlap, 1.0)
    
    def _calculate_evidence_support(self, answer: str, evidence: List[Any]) -> float:
        """计算证据支持度
        
        Args:
            answer: 答案文本
            evidence: 证据列表（可以是Evidence对象列表或字典列表）
        """
        if not answer or not evidence:
            return 0.0
        
        answer_lower = answer.lower()
        support_count = 0
        
        for ev in evidence:
            # 🚀 修复：支持Evidence对象和字典两种格式
            if hasattr(ev, 'content'):
                # Evidence对象
                content = ev.content if ev.content else ""
            elif isinstance(ev, dict):
                # 字典格式
                content = ev.get("content", "") or ev.get("text", "")
            else:
                # 其他格式，尝试转换为字符串
                content = str(ev) if ev else ""
            
            if content:
                content_lower = content.lower()
                # 检查答案是否在证据中出现
                if answer_lower in content_lower or any(
                    word in content_lower for word in answer_lower.split() if len(word) > 3
                ):
                    support_count += 1
        
        # 归一化
        if evidence:
            support_score = support_count / len(evidence)
        else:
            support_score = 0.0
        
        return min(support_score, 1.0)
    
    def _calculate_answer_completeness(self, answer: str, query: str) -> float:
        """计算答案完整性"""
        if not answer:
            return 0.0
        
        # 检查答案长度
        if len(answer) < 2:
            return 0.2
        elif len(answer) < 10:
            return 0.5
        elif len(answer) < 50:
            return 0.8
        else:
            return 1.0
    
    def _calculate_answer_type_match(self, answer: str, query: str) -> float:
        """计算答案类型匹配度"""
        if not answer or not query:
            return 0.5
        
        query_lower = query.lower()
        answer_lower = answer.lower()
        
        # 检查查询类型和答案类型是否匹配
        # 人名查询
        if any(word in query_lower for word in ['who', 'name', 'person']):
            # 人名通常包含多个单词，首字母大写
            if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$', answer):
                return 1.0
        
        # 地点查询
        if any(word in query_lower for word in ['where', 'location', 'place', 'city', 'country']):
            # 地点通常首字母大写
            if answer[0].isupper():
                return 0.8
        
        # 数字查询
        if any(word in query_lower for word in ['how many', 'number', 'count', 'when']):
            if re.search(r'\d+', answer):
                return 1.0
        
        return 0.5  # 默认匹配度
    
    def _calculate_context_relevance(self, query: str, context: Dict[str, Any]) -> float:
        """计算上下文相关性"""
        if not context:
            return 0.5
        
        # 简单的相关性检查：上下文是否包含查询关键词
        context_text = str(context).lower()
        query_lower = query.lower()
        
        query_keywords = set(re.findall(r'\b\w+\b', query_lower))
        stop_words = {'the', 'a', 'an', 'is', 'was', 'are', 'were', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from', 'as', 'and', 'or', 'but', 'what', 'who', 'when', 'where', 'why', 'how'}
        query_keywords = {w for w in query_keywords if w not in stop_words and len(w) > 2}
        
        if query_keywords:
            matches = sum(1 for keyword in query_keywords if keyword in context_text)
            relevance = matches / len(query_keywords)
        else:
            relevance = 0.5
        
        return min(relevance, 1.0)
    
    def _calculate_confidence(self, features: Dict[str, float]) -> float:
        """计算置信度（加权平均）"""
        confidence = 0.0
        
        for feature_name, feature_value in features.items():
            weight = self.feature_weights.get(feature_name, 0.0)
            confidence += feature_value * weight
        
        return min(max(confidence, 0.0), 1.0)
    
    def _post_process_confidence(self, confidence: float, features: Dict[str, float]) -> float:
        """后处理置信度（未来：神经网络输出层）"""
        # 简单的后处理：如果所有特征都很低，降低置信度
        if all(v < 0.3 for v in features.values()):
            confidence = confidence * 0.5
        
        # 如果关键特征很高，提高置信度
        if features.get("evidence_support", 0) > 0.8 and features.get("query_result_similarity", 0) > 0.7:
            confidence = min(confidence * 1.1, 1.0)
        
        return confidence
    
    def train(self, training_data: List[Any], labels: Optional[List[Any]] = None) -> Dict[str, Any]:
        """训练模型（初始版本：MLP，未来：LSTM + 注意力机制）"""
        if labels is None:
            self.logger.error("❌ 监督学习需要标签")
            return {"success": False, "error": "Labels required for supervised learning"}
        
        try:
            import time
            import numpy as np
            from sklearn.neural_network import MLPRegressor
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
            from sklearn.preprocessing import StandardScaler
            
            start_time = time.time()
            
            # 提取特征
            self.logger.info(f"📊 提取特征中... ({len(training_data)} 条数据)")
            X = []
            y = []
            
            for data, label in zip(training_data, labels):
                query = data.get("query", "")
                answer = data.get("answer", "")
                evidence = data.get("evidence", [])
                context = data.get("context", {})
                
                features = self._extract_features(query, answer, evidence, context)
                X.append(list(features.values()))
                y.append(float(label))  # 置信度标签 (0-1)
            
            X_array = np.array(X)
            y_array = np.array(y)
            
            # 数据标准化
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_array)
            self.scaler = scaler  # 保存scaler用于预测
            
            # 分割训练和测试数据
            test_size = self.config.get("test_size", 0.2)
            random_state = self.config.get("random_state", 42)
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y_array, test_size=test_size, random_state=random_state
            )
            
            # 🚀 尝试使用PyTorch LSTM + 注意力模型，如果不可用则使用MLP
            use_lstm = self.config.get("use_lstm", True)
            
            try:
                if use_lstm:
                    import torch
                    import torch.nn as nn
                    import torch.optim as optim
                    from torch.utils.data import DataLoader, TensorDataset
                    
                    # 🚀 修复：使用模块级别的LSTMWithAttention类
                    if LSTMWithAttention is None:
                        raise ImportError("PyTorch not available, cannot use LSTM model")
                    
                    # 转换为PyTorch张量
                    X_train_tensor = torch.FloatTensor(X_train).unsqueeze(1)  # (batch, 1, features)
                    X_test_tensor = torch.FloatTensor(X_test).unsqueeze(1)
                    y_train_tensor = torch.FloatTensor(y_train)
                    y_test_tensor = torch.FloatTensor(y_test)
                    
                    # 创建数据加载器
                    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
                    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
                    
                    # 初始化模型
                    input_size = X_train.shape[1]
                    hidden_size = self.config.get("lstm_hidden_size", 64)
                    num_layers = self.config.get("lstm_num_layers", 2)
                    model = LSTMWithAttention(input_size, hidden_size, num_layers)
                    
                    # 训练参数
                    num_epochs = self.config.get("num_epochs", 50)
                    learning_rate = self.config.get("learning_rate", 0.001)
                    criterion = nn.MSELoss()
                    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
                    
                    self.logger.info(f"🧠 训练LSTM + 注意力模型 (hidden={hidden_size}, layers={num_layers}, epochs={num_epochs})...")
                    
                    # 训练循环
                    model.train()
                    for epoch in range(num_epochs):
                        total_loss = 0
                        for batch_x, batch_y in train_loader:
                            optimizer.zero_grad()
                            outputs = model(batch_x)
                            loss = criterion(outputs, batch_y)
                            loss.backward()
                            optimizer.step()
                            total_loss += loss.item()
                        
                        if (epoch + 1) % 10 == 0:
                            avg_loss = total_loss / len(train_loader)
                            self.logger.debug(f"  Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}")
                    
                    # 评估
                    model.eval()
                    with torch.no_grad():
                        y_pred_tensor = model(X_test_tensor)
                        y_pred = y_pred_tensor.cpu().numpy()
                    
                    self.model = model
                    self.model_type = "lstm_attention"
                    self.is_trained = True
                    self.logger.info("✅ LSTM + 注意力模型训练完成")
                    
            except ImportError:
                # PyTorch不可用，使用MLP
                self.logger.info("⚠️ PyTorch不可用，使用MLP回归器")
                use_lstm = False
            
            if not use_lstm or not hasattr(self, 'model') or self.model is None:
                # 训练MLP回归器（fallback）
                hidden_layer_sizes = self.config.get("hidden_layer_sizes", (100, 50))
                max_iter = self.config.get("max_iter", 500)
                learning_rate = self.config.get("learning_rate", 0.001)
                
                self.logger.info(f"🧠 训练MLP回归器 (hidden={hidden_layer_sizes}, max_iter={max_iter})...")
                self.model = MLPRegressor(
                    hidden_layer_sizes=hidden_layer_sizes,
                    max_iter=max_iter,
                    learning_rate_init=learning_rate,
                    random_state=random_state,
                    early_stopping=True,
                    validation_fraction=0.1
                )
                self.model.fit(X_train, y_train)
                self.model_type = "mlp_regressor"
                self.is_trained = True
            
            # 评估模型
            if hasattr(self, 'model_type') and self.model_type == "lstm_attention":
                # LSTM模型已经在训练循环中评估
                import torch
                self.model.eval()
                with torch.no_grad():
                    X_test_tensor = torch.FloatTensor(X_test).unsqueeze(1)
                    y_pred_tensor = self.model(X_test_tensor)
                    y_pred = y_pred_tensor.cpu().numpy()
            else:
                y_pred = self.model.predict(X_test)
            
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            training_time = time.time() - start_time
            
            self.logger.info(f"✅ 训练完成！MSE: {mse:.4f}, MAE: {mae:.4f}, R²: {r2:.4f}, 训练时间: {training_time:.2f}s")
            
            return {
                "success": True,
                "training_samples": len(training_data),
                "test_samples": len(X_test),
                "model_type": getattr(self, 'model_type', 'mlp_regressor'),
                "metrics": {
                    "mse": float(mse),
                    "mae": float(mae),
                    "r2_score": float(r2)
                },
                "training_time": training_time
            }
        except ImportError as e:
            self.logger.warning(f"⚠️ sklearn未安装，使用规则版本: {e}")
            return {
                "success": True,
                "training_samples": len(training_data),
                "model_type": "rule_based",
                "note": "sklearn not available, using rule-based estimator"
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
                data = pickle.load(f)
                self.model = data.get("model")
                self.scaler = data.get("scaler")
                # 🚀 修复：加载模型类型，避免"模型类型未知"警告
                self.model_type = data.get("model_type", None)
            
            # 🚀 修复：如果model_type未保存，尝试自动检测
            if not hasattr(self, 'model_type') or self.model_type is None:
                if self.model is not None:
                    # 尝试检测模型类型
                    model_class_name = type(self.model).__name__
                    if 'LSTM' in model_class_name or 'Attention' in model_class_name:
                        self.model_type = "lstm_attention"
                        self.logger.debug(f"🔍 自动检测模型类型: {self.model_type} (基于类名: {model_class_name})")
                    elif hasattr(self.model, 'predict'):
                        self.model_type = "mlp_regressor"
                        self.logger.debug(f"🔍 自动检测模型类型: {self.model_type} (基于predict方法)")
                    else:
                        self.model_type = "unknown"
                        self.logger.warning(f"⚠️ 无法自动检测模型类型，类名: {model_class_name}")
            
            self.is_trained = True
            self.logger.info(f"✅ 成功加载模型: {model_path} (类型: {getattr(self, 'model_type', 'unknown')})")
            
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
                "scaler": getattr(self, 'scaler', None),
                # 🚀 修复：保存模型类型，避免加载后"模型类型未知"警告
                "model_type": getattr(self, 'model_type', None)
            }
            
            # 🚀 改进：先写入临时文件，成功后再重命名，避免创建0字节文件
            temp_path = model_path + '.tmp'
            with open(temp_path, 'wb') as f:
                pickle.dump(data, f)
            
            # 验证文件大小
            if os.path.getsize(temp_path) == 0:
                os.remove(temp_path)
                raise ValueError("保存的模型文件大小为0，保存失败")
            
            # 成功后再重命名
            if os.path.exists(model_path):
                os.remove(model_path)
            os.rename(temp_path, model_path)
            
            self.logger.info(f"✅ 成功保存模型: {model_path}")
            
        except ImportError:
            self.logger.warning("⚠️ pickle模块不可用，无法保存模型")
        except Exception as e:
            self.logger.error(f"❌ 保存模型失败: {e}")
            # 🚀 改进：清理临时文件
            temp_path = model_path + '.tmp'
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            # 不抛出异常，允许系统继续运行（使用规则版本）
            return
    
    def _evaluate_impl(self, test_data: List[Any], test_labels: List[Any]) -> Dict[str, float]:
        """评估模型"""
        if not self.is_trained or self.model is None:
            return {
                "mse": 0.0,
                "mae": 0.0,
                "r2_score": 0.0,
            }
        
        try:
            import numpy as np
            from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
            
            # 提取特征
            X = []
            y = []
            
            for data, label in zip(test_data, test_labels):
                query = data.get("query", "")
                answer = data.get("answer", "")
                evidence = data.get("evidence", [])
                context = data.get("context", {})
                
                features = self._extract_features(query, answer, evidence, context)
                X.append(list(features.values()))
                y.append(float(label))
            
            X_array = np.array(X)
            y_array = np.array(y)
            
            # 标准化
            if hasattr(self, 'scaler') and self.scaler is not None:
                X_scaled = self.scaler.transform(X_array)
            else:
                X_scaled = X_array
            
            # 预测
            y_pred = self.model.predict(X_scaled)
            
            # 计算指标
            mse = mean_squared_error(y_array, y_pred)
            mae = mean_absolute_error(y_array, y_pred)
            r2 = r2_score(y_array, y_pred)
            
            return {
                "mse": float(mse),
                "mae": float(mae),
                "r2_score": float(r2),
            }
        except Exception as e:
            self.logger.error(f"❌ 评估失败: {e}")
            return {
                "mse": 0.0,
                "mae": 0.0,
                "r2_score": 0.0,
            }

