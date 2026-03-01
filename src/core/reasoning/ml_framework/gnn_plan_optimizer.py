"""
GNN计划优化器 - 使用图神经网络优化执行计划

初始版本：基于规则的图优化
未来版本：GAT（Graph Attention Network）
"""
import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict, deque
from .base_ml_component import BaseMLComponent

logger = logging.getLogger(__name__)


# 🚀 修复：将SimpleGAT移到模块级别，避免pickle序列化失败
try:
    import torch
    import torch.nn as nn
    
    class SimpleGAT(nn.Module):
        """简单的图注意力网络（模块级别，可被pickle序列化）"""
        def __init__(self, input_dim, hidden_dim=64, num_heads=4, num_layers=2, dropout=0.2):
            super().__init__()
            self.layers = nn.ModuleList()
            self.layers.append(nn.Linear(input_dim, hidden_dim))
            for _ in range(num_layers - 1):
                self.layers.append(nn.Linear(hidden_dim, hidden_dim))
            self.attention = nn.MultiheadAttention(hidden_dim, num_heads, dropout=dropout, batch_first=True)
            self.fc = nn.Linear(hidden_dim, 1)
            self.dropout = nn.Dropout(dropout)
        
        def forward(self, x, adj=None):
            # x shape: (batch, num_nodes, input_dim)
            # 简化：不使用邻接矩阵，使用全连接层
            import torch.nn.functional as F
            for layer in self.layers:
                x = F.relu(layer(x))
                x = self.dropout(x)
            
            # 使用注意力机制
            attn_out, _ = self.attention(x, x, x)
            # 取平均池化
            out = attn_out.mean(dim=1)  # (batch, hidden_dim)
            out = self.fc(out)
            out = torch.sigmoid(out)
            return out.squeeze(-1)
except ImportError:
    SimpleGAT = None


class GNNPlanOptimizer(BaseMLComponent):
    """GNN计划优化器
    
    使用图神经网络优化执行计划：
    - 节点：执行步骤
    - 边：依赖关系
    - 输出：优化建议（合并、并行化、重新排序、拆分）
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化GNN计划优化器
        
        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 🚀 增强：自动加载预训练模型
        from src.core.reasoning.ml_framework.model_auto_loader import auto_load_model
        if not auto_load_model(self, "gnn_plan_optimizer", config):
            # 如果加载失败，使用规则版本
            self.logger.info("✅ 使用基于规则的GNN计划优化器（初始版本）")
        
        # 优化规则（未来：由GNN学习）
        self.optimization_rules = {
            "merge_threshold": 2,  # 如果两个步骤可以合并
            "parallel_threshold": 0.5,  # 并行化阈值
        }
        
    def predict(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """优化执行计划
        
        Args:
            plan: 计划字典，包含：
                - steps: 步骤列表
                - query: 原始查询
                
        Returns:
            预测结果字典，包含：
                - prediction: 优化建议列表
                - confidence: 优化置信度
                - metadata: 其他元数据
        """
        try:
            steps = plan.get("steps", [])
            if not steps:
                return {
                    "prediction": [],
                    "confidence": 0.0,
                    "metadata": {"error": "Empty plan"}
                }
            
            # 1. 构建依赖图
            dependency_graph = self._build_dependency_graph(steps)
            
            # 2. 生成优化建议
            optimization_suggestions = []
            
            # 建议1: 合并步骤
            merge_suggestions = self._suggest_merges(steps, dependency_graph)
            optimization_suggestions.extend(merge_suggestions)
            
            # 建议2: 并行化
            parallel_suggestions = self._suggest_parallelization(steps, dependency_graph)
            optimization_suggestions.extend(parallel_suggestions)
            
            # 建议3: 重新排序
            reorder_suggestions = self._suggest_reordering(steps, dependency_graph)
            optimization_suggestions.extend(reorder_suggestions)
            
            # 建议4: 拆分步骤
            split_suggestions = self._suggest_splits(steps)
            optimization_suggestions.extend(split_suggestions)
            
            return {
                "prediction": optimization_suggestions,
                "confidence": 0.8 if optimization_suggestions else 0.0,
                "metadata": {
                    "num_suggestions": len(optimization_suggestions),
                    "model_version": "rule_based_v1",
                }
            }
            
        except Exception as e:
            self.logger.error(f"计划优化失败: {e}")
            return {
                "prediction": [],
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }
    
    def _build_dependency_graph(self, steps: List[Dict[str, Any]]) -> Dict[int, Set[int]]:
        """构建依赖图"""
        graph = defaultdict(set)
        
        for i, step in enumerate(steps):
            depends_on = step.get("depends_on", [])
            if isinstance(depends_on, list):
                for dep in depends_on:
                    # 解析依赖
                    if isinstance(dep, int):
                        if 0 <= dep < len(steps):
                            graph[i].add(dep)
                    elif isinstance(dep, str):
                        # 尝试从字符串中提取数字
                        nums = re.findall(r'\d+', dep)
                        if nums:
                            dep_idx = int(nums[0]) - 1  # 假设从1开始
                            if 0 <= dep_idx < len(steps):
                                graph[i].add(dep_idx)
        
        return graph
    
    def _suggest_merges(
        self,
        steps: List[Dict[str, Any]],
        dependency_graph: Dict[int, Set[int]]
    ) -> List[Dict[str, Any]]:
        """建议合并步骤"""
        suggestions = []
        
        # 查找可以合并的连续步骤
        for i in range(len(steps) - 1):
            step1 = steps[i]
            step2 = steps[i + 1]
            
            # 如果步骤2只依赖步骤1，且类型相同，可以合并
            if dependency_graph.get(i + 1, set()) == {i}:
                if step1.get("type") == step2.get("type"):
                    suggestions.append({
                        "type": "merge",
                        "steps": [i, i + 1],
                        "reason": "Sequential steps of same type can be merged",
                        "confidence": 0.7,
                    })
        
        return suggestions
    
    def _suggest_parallelization(
        self,
        steps: List[Dict[str, Any]],
        dependency_graph: Dict[int, Set[int]]
    ) -> List[Dict[str, Any]]:
        """建议并行化"""
        suggestions = []
        
        # 查找没有依赖的步骤（可以并行执行）
        independent_steps = []
        for i, step in enumerate(steps):
            if not dependency_graph.get(i, set()):
                independent_steps.append(i)
        
        # 如果有多个独立步骤，建议并行化
        if len(independent_steps) > 1:
            suggestions.append({
                "type": "parallelize",
                "steps": independent_steps,
                "reason": "Multiple independent steps can be executed in parallel",
                "confidence": 0.9,
            })
        
        return suggestions
    
    def _suggest_reordering(
        self,
        steps: List[Dict[str, Any]],
        dependency_graph: Dict[int, Set[int]]
    ) -> List[Dict[str, Any]]:
        """建议重新排序"""
        suggestions = []
        
        # 检查是否有循环依赖
        if self._has_cycle(dependency_graph, len(steps)):
            suggestions.append({
                "type": "reorder",
                "steps": list(range(len(steps))),
                "reason": "Cycle detected, reordering needed",
                "confidence": 0.8,
            })
        
        return suggestions
    
    def _suggest_splits(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """建议拆分步骤"""
        suggestions = []
        
        for i, step in enumerate(steps):
            sub_query = step.get("sub_query", "")
            
            # 如果子查询包含多个问题，建议拆分
            if sub_query.count("?") > 1:
                suggestions.append({
                    "type": "split",
                    "steps": [i],
                    "reason": "Step contains multiple questions, should be split",
                    "confidence": 0.8,
                })
        
        return suggestions
    
    def _has_cycle(self, graph: Dict[int, Set[int]], num_nodes: int) -> bool:
        """检测图中是否有循环"""
        visited = set()
        rec_stack = set()
        
        def dfs(node: int) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in range(num_nodes):
            if node not in visited:
                if dfs(node):
                    return True
        
        return False
    
    def train(self, training_data: List[Any], labels: Optional[List[Any]] = None) -> Dict[str, Any]:
        """训练模型（初始版本：基于图特征的分类器，未来：GAT模型）
        
        Args:
            training_data: 训练数据（计划字典列表）
            labels: 标签（优化建议列表）
            
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
            
            # 提取图特征
            self.logger.info(f"📊 提取图特征中... ({len(training_data)} 条数据)")
            X = []
            y = []
            
            for plan, suggestions in zip(training_data, labels):
                steps = plan.get("steps", [])
                
                # 构建依赖图
                dependency_graph = self._build_dependency_graph(steps)
                
                # 提取图特征
                features = self._extract_graph_features(steps, dependency_graph)
                X.append(list(features.values()))
                
                # 标签：是否有优化建议（简化：只判断是否有建议）
                has_suggestion = 1 if suggestions and len(suggestions) > 0 else 0
                y.append(has_suggestion)
            
            X_array = np.array(X)
            y_array = np.array(y)
            
            # 分割训练和测试数据
            test_size = self.config.get("test_size", 0.2)
            random_state = self.config.get("random_state", 42)
            X_train, X_test, y_train, y_test = train_test_split(
                X_array, y_array, test_size=test_size, random_state=random_state, stratify=y_array
            )
            
            # 🚀 尝试使用PyTorch GAT模型，如果不可用则使用随机森林
            use_gnn = self.config.get("use_gnn", True)
            
            try:
                if use_gnn:
                    import torch
                    import torch.nn as nn
                    import torch.nn.functional as F
                    import torch.optim as optim
                    from torch.utils.data import DataLoader, Dataset
                    
                    # 🚀 修复：使用模块级别的SimpleGAT类
                    if SimpleGAT is None:
                        raise ImportError("PyTorch not available, cannot use GAT model")
                    
                    # 定义步骤特征提取函数
                    def extract_step_features(step):
                        """提取步骤特征"""
                        sub_query = step.get("sub_query", "")
                        return [
                            float(len(sub_query)),
                            float(len(step.get("depends_on", []))),
                            1.0 if step.get("parallel_group") else 0.0,
                            float(step.get("confidence", 0.0)),
                            float(len(sub_query.split())),
                            1.0 if "?" in sub_query else 0.0,
                            1.0 if "who" in sub_query.lower() else 0.0,
                            1.0 if "what" in sub_query.lower() else 0.0,
                            1.0 if "when" in sub_query.lower() else 0.0,
                            1.0 if "where" in sub_query.lower() else 0.0,
                        ]
                    
                    # 准备图数据（将计划转换为图表示）
                    class PlanDataset(Dataset):
                        def __init__(self, plans, labels, extract_fn):
                            self.plans = plans
                            self.labels = labels
                            self.extract_fn = extract_fn
                            
                        def __len__(self):
                            return len(self.plans)
                        
                        def __getitem__(self, idx):
                            plan = self.plans[idx]
                            steps = plan.get("steps", [])
                            
                            # 提取每个步骤的特征
                            node_features = []
                            for step in steps[:20]:  # 最多20个步骤
                                features = self.extract_fn(step)
                                node_features.append(features)
                            
                            # 填充到固定大小
                            feature_dim = 10
                            while len(node_features) < 20:
                                node_features.append([0.0] * feature_dim)
                            
                            # 转换为张量
                            node_features = torch.FloatTensor(node_features[:20])
                            label = torch.FloatTensor([self.labels[idx]])
                            
                            return node_features, label
                    
                    # 创建数据集
                    # 注意：X_train和X_test是特征数组，不是原始计划数据
                    # 需要从training_data中获取原始计划
                    train_plans = [training_data[i] for i in range(len(X_train))]
                    test_plans = [training_data[i] for i in range(len(X_train), len(training_data))]
                    train_dataset = PlanDataset(train_plans, y_train.tolist(), extract_step_features)
                    test_dataset = PlanDataset(test_plans, y_test.tolist(), extract_step_features)
                    
                    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
                    test_loader = DataLoader(test_dataset, batch_size=8, shuffle=False)
                    
                    # 初始化模型
                    input_dim = 10  # 步骤特征维度
                    hidden_dim = self.config.get("hidden_dim", 64)
                    num_heads = self.config.get("num_heads", 4)
                    num_layers = self.config.get("num_layers", 2)
                    model = SimpleGAT(input_dim, hidden_dim, num_heads, num_layers)
                    
                    # 训练参数
                    num_epochs = self.config.get("num_epochs", 30)
                    learning_rate = self.config.get("learning_rate", 0.001)
                    criterion = nn.BCELoss()
                    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
                    
                    self.logger.info(f"🧠 训练GAT模型 (hidden={hidden_dim}, heads={num_heads}, layers={num_layers}, epochs={num_epochs})...")
                    
                    # 训练循环
                    model.train()
                    for epoch in range(num_epochs):
                        total_loss = 0
                        for batch_x, batch_y in train_loader:
                            optimizer.zero_grad()
                            outputs = model(batch_x)
                            loss = criterion(outputs, batch_y.squeeze())
                            loss.backward()
                            optimizer.step()
                            total_loss += loss.item()
                        
                        if (epoch + 1) % 5 == 0:
                            avg_loss = total_loss / len(train_loader)
                            self.logger.debug(f"  Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}")
                    
                    # 评估
                    model.eval()
                    y_pred_list = []
                    with torch.no_grad():
                        for batch_x, _ in test_loader:
                            outputs = model(batch_x)
                            y_pred_list.extend(outputs.cpu().numpy())
                    
                    y_pred_gat = np.array(y_pred_list)
                    y_pred_binary_gat = (y_pred_gat > 0.5).astype(int)
                    
                    self.model = model
                    self.model_type = "gat"
                    self.is_trained = True
                    self.logger.info("✅ GAT模型训练完成")
                    
                    # 🚀 修复：保存GAT模型的预测结果，供后续评估使用
                    y_pred = y_pred_binary_gat
                    
            except ImportError:
                # PyTorch不可用，使用随机森林
                self.logger.info("⚠️ PyTorch不可用，使用随机森林分类器")
                use_gnn = False
            
            if not use_gnn or not hasattr(self, 'model') or self.model is None:
                # 训练随机森林分类器（fallback）
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
                self.model_type = "random_forest"
                self.is_trained = True
            
            # 评估模型
            if not hasattr(self, 'model_type') or self.model_type != "gat":
                # 🚀 修复：只有非GAT模型才需要在这里预测
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
                "model_type": getattr(self, 'model_type', 'random_forest'),
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
                "note": "sklearn not available, using rule-based optimizer"
            }
        except Exception as e:
            self.logger.error(f"❌ 训练失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    def _extract_graph_features(self, steps: List[Dict[str, Any]], dependency_graph: Dict[int, Set[int]]) -> Dict[str, float]:
        """提取图特征"""
        features = {}
        
        # 基本图特征
        features["num_nodes"] = float(len(steps))
        features["num_edges"] = float(sum(len(deps) for deps in dependency_graph.values()))
        features["avg_degree"] = features["num_edges"] / max(features["num_nodes"], 1)
        
        # 依赖深度
        max_depth = 0
        for node in range(len(steps)):
            depth = self._calculate_node_depth(node, dependency_graph, len(steps))
            max_depth = max(max_depth, depth)
        features["max_depth"] = float(max_depth)
        features["avg_depth"] = float(sum(
            self._calculate_node_depth(i, dependency_graph, len(steps)) 
            for i in range(len(steps))
        ) / max(len(steps), 1))
        
        # 是否有循环
        features["has_cycle"] = 1.0 if self._has_cycle(dependency_graph, len(steps)) else 0.0
        
        # 独立节点数（没有依赖的节点）
        independent_nodes = sum(1 for i in range(len(steps)) if not dependency_graph.get(i, set()))
        features["independent_nodes"] = float(independent_nodes)
        features["independent_ratio"] = features["independent_nodes"] / max(features["num_nodes"], 1)
        
        # 并行组数
        parallel_groups = set(step.get("parallel_group") for step in steps if step.get("parallel_group"))
        features["num_parallel_groups"] = float(len(parallel_groups))
        
        return features
    
    def _calculate_node_depth(self, node: int, graph: Dict[int, Set[int]], num_nodes: int) -> int:
        """计算节点的深度（从根节点到该节点的最长路径）"""
        visited = set()
        
        def dfs(n: int) -> int:
            if n in visited:
                return 0
            visited.add(n)
            
            deps = graph.get(n, set())
            if not deps:
                return 0
            
            max_dep_depth = max(dfs(dep) for dep in deps)
            return max_dep_depth + 1
        
        return dfs(node)
    
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
                raise ValueError("模型未训练，无法保存")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(model_path) if os.path.dirname(model_path) else '.', exist_ok=True)
            
            # 🚀 改进：先写入临时文件，成功后再重命名，避免创建0字节文件
            temp_path = model_path + '.tmp'
            with open(temp_path, 'wb') as f:
                pickle.dump(self.model, f)
            
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
            raise
        except Exception as e:
            self.logger.error(f"❌ 保存模型失败: {e}")
            # 🚀 改进：清理临时文件
            temp_path = model_path + '.tmp'
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            # 抛出异常，让BaseMLComponent的save_model方法返回False
            raise
    
    def _evaluate_impl(self, test_data: List[Any], test_labels: List[Any]) -> Dict[str, float]:
        """评估模型"""
        if not self.is_trained or self.model is None:
            return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}
        
        try:
            import numpy as np
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            # 提取特征
            X = []
            y = []
            
            for plan, suggestions in zip(test_data, test_labels):
                steps = plan.get("steps", [])
                dependency_graph = self._build_dependency_graph(steps)
                features = self._extract_graph_features(steps, dependency_graph)
                X.append(list(features.values()))
                
                has_suggestion = 1 if suggestions and len(suggestions) > 0 else 0
                y.append(has_suggestion)
            
            X_array = np.array(X)
            y_array = np.array(y)
            
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

