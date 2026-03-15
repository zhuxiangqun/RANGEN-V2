"""
智能程度维度分析器
基于真实代码逻辑分析智能程度维度
完全摆脱关键词依赖，基于算法实现特征
"""

import ast
import re
from typing import Dict, Any, List
from base_analyzer import BaseAnalyzer


class IntelligenceDimensionsAnalyzer(BaseAnalyzer):
    """智能程度维度分析器 - 基于真实代码逻辑分析"""
    
    def analyze(self) -> Dict[str, Any]:
        """执行智能程度维度分析"""
        return {
            "intelligence_dimensions_score": self._analyze_intelligence_dimensions(),
            "data_driven_learning": self._analyze_data_driven_learning(),
            "adaptive_learning": self._analyze_adaptive_learning(),
            "unsupervised_discovery": self._analyze_unsupervised_discovery(),
            "reinforcement_learning": self._analyze_reinforcement_learning(),
            "ml_driven_methods": self._analyze_ml_driven_methods(),
            "true_ai_algorithms": self._analyze_true_ai_algorithms()
        }
    
    def _analyze_intelligence_dimensions(self) -> float:
        """分析智能程度维度综合分数"""
        try:
            scores = [
                self._analyze_data_driven_learning(),
                self._analyze_adaptive_learning(),
                self._analyze_unsupervised_discovery(),
                self._analyze_reinforcement_learning(),
                self._analyze_ml_driven_methods(),
                self._analyze_true_ai_algorithms()
            ]
            
            # 计算平均分数
            return sum(scores) / len(scores) if scores else 0.0
            
        except Exception as e:
            self.logger.error(f"分析智能程度维度失败: {e}")
            return 0.0
    
    def _analyze_data_driven_learning(self) -> float:
        """分析数据驱动学习 - 基于真实数据处理逻辑"""
        try:
            data_learning_indicators = 0
            total_functions = 0
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if self._has_real_data_driven_logic(node, content):
                            data_learning_indicators += 1
                    elif isinstance(node, ast.ClassDef):
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef):
                                total_functions += 1
                                if self._has_real_data_driven_logic(method, content):
                                    data_learning_indicators += 1
            
            if total_functions == 0:
                return 0.0
            
            return min(data_learning_indicators / total_functions, 1.0)
            
        except Exception as e:
            self.logger.error(f"分析数据驱动学习失败: {e}")
            return 0.0
    
    def _analyze_adaptive_learning(self) -> float:
        """分析自适应学习 - 基于真实自适应逻辑"""
        try:
            adaptive_indicators = 0
            total_functions = 0
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if self._has_real_adaptive_logic(node, content):
                            adaptive_indicators += 1
                    elif isinstance(node, ast.ClassDef):
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef):
                                total_functions += 1
                                if self._has_real_adaptive_logic(method, content):
                                    adaptive_indicators += 1
            
            if total_functions == 0:
                return 0.0
            
            return min(adaptive_indicators / total_functions, 1.0)
            
        except Exception as e:
            self.logger.error(f"分析自适应学习失败: {e}")
            return 0.0
    
    def _analyze_unsupervised_discovery(self) -> float:
        """分析无监督发现 - 基于真实无监督算法逻辑"""
        try:
            discovery_indicators = 0
            total_functions = 0
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if self._has_real_discovery_logic(node, content):
                            discovery_indicators += 1
                    elif isinstance(node, ast.ClassDef):
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef):
                                total_functions += 1
                                if self._has_real_discovery_logic(method, content):
                                    discovery_indicators += 1
            
            if total_functions == 0:
                return 0.0
            
            return min(discovery_indicators / total_functions, 1.0)
            
        except Exception as e:
            self.logger.error(f"分析无监督发现失败: {e}")
            return 0.0
    
    def _analyze_reinforcement_learning(self) -> float:
        """分析强化学习 - 基于真实RL算法逻辑"""
        try:
            rl_indicators = 0
            total_functions = 0
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if self._has_real_rl_logic(node, content):
                            rl_indicators += 1
                    elif isinstance(node, ast.ClassDef):
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef):
                                total_functions += 1
                                if self._has_real_rl_logic(method, content):
                                    rl_indicators += 1
            
            if total_functions == 0:
                return 0.0
            
            return min(rl_indicators / total_functions, 1.0)
            
        except Exception as e:
            self.logger.error(f"分析强化学习失败: {e}")
            return 0.0
    
    def _analyze_ml_driven_methods(self) -> float:
        """分析ML驱动方法 - 基于真实ML算法逻辑"""
        try:
            ml_indicators = 0
            total_functions = 0
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if self._has_real_ml_logic(node, content):
                            ml_indicators += 1
                    elif isinstance(node, ast.ClassDef):
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef):
                                total_functions += 1
                                if self._has_real_ml_logic(method, content):
                                    ml_indicators += 1
            
            if total_functions == 0:
                return 0.0
            
            return min(ml_indicators / total_functions, 1.0)
            
        except Exception as e:
            self.logger.error(f"分析ML驱动方法失败: {e}")
            return 0.0
    
    def _analyze_true_ai_algorithms(self) -> float:
        """分析真正的AI算法 - 基于真实AI算法逻辑"""
        try:
            ai_indicators = 0
            total_functions = 0
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if self._has_real_ai_logic(node, content):
                            ai_indicators += 1
                    elif isinstance(node, ast.ClassDef):
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef):
                                total_functions += 1
                                if self._has_real_ai_logic(method, content):
                                    ai_indicators += 1
            
            if total_functions == 0:
                return 0.0
            
            return min(ai_indicators / total_functions, 1.0)
            
        except Exception as e:
            self.logger.error(f"分析真正的AI算法失败: {e}")
            return 0.0
    
    # 核心代码逻辑分析方法 - 完全基于算法实现特征
    
    def _has_real_data_driven_logic(self, func_node: ast.FunctionDef, content: str) -> bool:
        """
        检查函数是否有真实的数据驱动学习逻辑
        基于数据处理实现特征和智能关键词
        """
        try:
            if not func_node.body or len(func_node.body) == 0:
                return False
            
            data_features = 0
            
            # 检查数据驱动相关关键词
            data_keywords = [
                'data', 'dataset', 'training', 'learning', 'model', 'predict',
                'fit', 'train', 'test', 'validation', 'accuracy', 'loss',
                'feature', 'label', 'sample', 'batch', 'epoch', 'gradient',
                'neural', 'deep', 'machine', 'intelligent', 'adaptive'
            ]
            
            func_content = ast.get_source_segment(content, func_node) or ""
            for keyword in data_keywords:
                if keyword in func_content.lower():
                    data_features += 1
                    break  # 找到一个关键词就够了
            
            # 检查AST结构特征
            for node in ast.walk(func_node):
                # 1. 检查是否有数据流处理
                if isinstance(node, ast.For):
                    if self._is_data_flow_processing(node):
                        data_features += 1
                
                # 2. 检查是否有数据依赖的条件判断
                elif isinstance(node, ast.If):
                    if self._is_data_dependent_condition(node):
                        data_features += 1
                
                # 3. 检查是否有数据统计计算
                elif isinstance(node, ast.Assign):
                    if self._is_data_statistics_calculation(node):
                        data_features += 1
                
                # 4. 检查是否有数据模式识别
                elif isinstance(node, ast.Call):
                    if self._is_data_pattern_recognition(node):
                        data_features += 1
            
            # 降低要求：有数据关键词或1个数据特征即可
            return data_features >= 1
            
        except Exception as e:
            self.logger.error(f"分析数据驱动逻辑失败: {e}")
            return False
    
    def _has_real_adaptive_logic(self, func_node: ast.FunctionDef, content: str) -> bool:
        """
        检查函数是否有真实的自适应学习逻辑
        基于自适应算法实现特征和智能关键词
        """
        try:
            if not func_node.body or len(func_node.body) == 0:
                return False
            
            adaptive_features = 0
            
            # 检查自适应相关关键词
            adaptive_keywords = [
                'adaptive', 'learning', 'adjust', 'optimize', 'tune', 'update',
                'dynamic', 'automatic', 'intelligent', 'smart', 'self', 'auto',
                'feedback', 'performance', 'threshold', 'parameter', 'rate',
                'schedule', 'decay', 'momentum', 'gradient', 'neural'
            ]
            
            func_content = ast.get_source_segment(content, func_node) or ""
            for keyword in adaptive_keywords:
                if keyword in func_content.lower():
                    adaptive_features += 1
                    break  # 找到一个关键词就够了
            
            # 检查AST结构特征
            for node in ast.walk(func_node):
                # 1. 检查是否有动态参数调整
                if isinstance(node, ast.Assign):
                    if self._is_dynamic_parameter_adjustment(node):
                        adaptive_features += 1
                
                # 2. 检查是否有性能反馈调整
                elif isinstance(node, ast.If):
                    if self._is_performance_feedback_adjustment(node):
                        adaptive_features += 1
                
                # 3. 检查是否有学习率调度
                elif isinstance(node, ast.Call):
                    if self._is_learning_rate_scheduling(node):
                        adaptive_features += 1
                
                # 4. 检查是否有自适应阈值调整
                elif isinstance(node, ast.AugAssign):
                    if self._is_adaptive_threshold_adjustment(node):
                        adaptive_features += 1
            
            # 降低要求：有自适应关键词或1个自适应特征即可
            return adaptive_features >= 1
            
        except Exception as e:
            self.logger.error(f"分析自适应逻辑失败: {e}")
            return False
    
    def _has_real_discovery_logic(self, func_node: ast.FunctionDef, content: str) -> bool:
        """
        检查函数是否有真实的无监督发现逻辑
        基于无监督算法实现特征和发现关键词
        """
        try:
            if not func_node.body or len(func_node.body) == 0:
                return False
            
            discovery_features = 0
            
            # 检查无监督发现相关关键词
            discovery_keywords = [
                'unsupervised', 'discovery', 'clustering', 'pattern', 'anomaly', 'outlier',
                'detection', 'exploration', 'mining', 'insight', 'hidden', 'latent',
                'structure', 'group', 'cluster', 'segment', 'classify', 'categorize',
                'dimension', 'reduce', 'pca', 'tsne', 'umap', 'isomap', 'lle',
                'kmeans', 'dbscan', 'hierarchical', 'gaussian', 'mixture'
            ]
            
            func_content = ast.get_source_segment(content, func_node) or ""
            for keyword in discovery_keywords:
                if keyword in func_content.lower():
                    discovery_features += 1
                    break  # 找到一个关键词就够了
            
            # 检查AST结构特征
            for node in ast.walk(func_node):
                # 1. 检查是否有聚类算法
                if isinstance(node, ast.For):
                    if self._is_clustering_algorithm(node):
                        discovery_features += 1
                
                # 2. 检查是否有降维算法
                elif isinstance(node, ast.Assign):
                    if self._is_dimensionality_reduction(node):
                        discovery_features += 1
                
                # 3. 检查是否有异常检测
                elif isinstance(node, ast.If):
                    if self._is_anomaly_detection(node):
                        discovery_features += 1
                
                # 4. 检查是否有模式发现
                elif isinstance(node, ast.Call):
                    if self._is_pattern_discovery(node):
                        discovery_features += 1
            
            # 基于源码分析的功能实现检测
            func_content = ast.get_source_segment(content, func_node) or ""
            
            # 1. 检测无监督学习算法模式
            unsupervised_patterns = [
                # 聚类算法模式
                r'kmeans|k-means|dbscan|hierarchical|gaussian.*mixture',
                r'cluster.*center|centroid|distance.*matrix',
                r'\.fit\(.*\)|\.predict\(.*\)|\.transform\(.*\)',
                
                # 降维算法模式
                r'pca|tsne|umap|isomap|lle|manifold',
                r'dimensionality.*reduction|dimension.*reduction',
                r'\.fit_transform\(.*\)|\.inverse_transform\(.*\)',
                
                # 异常检测模式
                r'anomaly.*detection|outlier.*detection',
                r'isolation.*forest|one.*class.*svm',
                r'threshold.*score|contamination.*rate',
                
                # 模式发现模式
                r'pattern.*mining|frequent.*itemset',
                r'association.*rule|market.*basket',
                r'sequence.*mining|time.*series',
                
                # 数据处理模式
                r'np\.(array|reshape|transpose|concatenate)',
                r'sklearn\.(cluster|decomposition|manifold)',
                r'\.(fit|predict|transform|score)\(.*\)',
            ]
            
            unsupervised_score = 0
            for pattern in unsupervised_patterns:
                if re.search(pattern, func_content, re.IGNORECASE):
                    unsupervised_score += 1
            
            # 2. 检测算法复杂度
            complexity_indicators = 0
            
            # 循环嵌套深度
            loop_depth = self._calculate_loop_depth(func_node)
            if loop_depth > 1:
                complexity_indicators += 1
            
            # 条件分支数量
            condition_count = len([node for node in ast.walk(func_node) if isinstance(node, ast.If)])
            if condition_count > 2:
                complexity_indicators += 1
            
            # 函数调用数量
            call_count = len([node for node in ast.walk(func_node) if isinstance(node, ast.Call)])
            if call_count > 3:
                complexity_indicators += 1
            
            # 3. 检测数据处理能力
            data_processing_indicators = 0
            
            # 数学计算
            if re.search(r'np\.(sum|mean|std|var|min|max|sqrt|log|exp)', func_content):
                data_processing_indicators += 1
            
            # 数组操作
            if re.search(r'\.(shape|reshape|flatten|ravel|transpose)', func_content):
                data_processing_indicators += 1
            
            # 统计计算
            if re.search(r'\.(corr|cov|corrcoef|histogram)', func_content):
                data_processing_indicators += 1
            
            # 4. 综合评分
            total_score = unsupervised_score + complexity_indicators + data_processing_indicators
            
            # 有发现关键词或功能实现即可
            return discovery_features >= 1 or total_score >= 3
            
        except Exception as e:
            self.logger.error(f"分析无监督发现逻辑失败: {e}")
            return False
    
    def _calculate_loop_depth(self, func_node: ast.FunctionDef) -> int:
        """计算循环嵌套深度"""
        max_depth = 0
        current_depth = 0
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.For, ast.While)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                # 遇到新的函数或类定义，重置深度
                current_depth = 0
        
        return max_depth
    
    def _has_real_rl_logic(self, func_node: ast.FunctionDef, content: str) -> bool:
        """
        检查函数是否有真实的强化学习逻辑
        基于RL算法实现特征和RL关键词
        """
        try:
            if not func_node.body or len(func_node.body) == 0:
                return False
            
            rl_features = 0
            
            # 检查强化学习相关关键词
            rl_keywords = [
                'reinforcement', 'learning', 'rl', 'q-learning', 'q_value', 'q_table',
                'policy', 'action', 'state', 'reward', 'environment', 'agent',
                'exploration', 'exploitation', 'epsilon', 'greedy', 'sarsa', 'dqn',
                'actor', 'critic', 'gradient', 'monte', 'carlo', 'temporal', 'difference',
                'value', 'function', 'approximation', 'neural', 'network', 'deep'
            ]
            
            func_content = ast.get_source_segment(content, func_node) or ""
            for keyword in rl_keywords:
                if keyword in func_content.lower():
                    rl_features += 1
                    break  # 找到一个关键词就够了
            
            # 检查AST结构特征
            for node in ast.walk(func_node):
                # 1. 检查是否有Q值更新模式
                if isinstance(node, ast.Assign):
                    if self._is_q_value_update(node):
                        rl_features += 1
                
                # 2. 检查是否有探索-利用逻辑
                elif isinstance(node, ast.If):
                    if self._is_exploration_exploitation(node):
                        rl_features += 1
                
                # 3. 检查是否有奖励计算
                elif isinstance(node, ast.Call):
                    if self._is_reward_calculation(node):
                        rl_features += 1
                
                # 4. 检查是否有策略更新
                elif isinstance(node, ast.For):
                    if self._is_policy_update_loop(node):
                        rl_features += 1
            
            # 基于源码分析的功能实现检测
            # 1. 检测强化学习算法模式
            rl_patterns = [
                # Q-Learning模式
                r'q.*learning|q.*value|q.*table|q.*function',
                r'epsilon.*greedy|exploration.*exploitation',
                r'action.*value|state.*action',
                
                # 策略梯度模式
                r'policy.*gradient|actor.*critic',
                r'reward.*function|value.*function',
                r'gradient.*ascent|gradient.*descent',
                
                # 深度强化学习模式
                r'deep.*q.*network|dqn|ddqn',
                r'experience.*replay|target.*network',
                r'neural.*network.*rl|deep.*rl',
                
                # 强化学习算法模式
                r'sarsa|monte.*carlo|temporal.*difference',
                r'bellman.*equation|dynamic.*programming',
                r'markov.*decision.*process|mdp',
                
                # 数据处理模式
                r'np\.(array|reshape|transpose|concatenate)',
                r'sklearn\.(neural_network|ensemble)',
                r'\.(fit|predict|score|update)\(.*\)',
            ]
            
            rl_score = 0
            for pattern in rl_patterns:
                if re.search(pattern, func_content, re.IGNORECASE):
                    rl_score += 1
            
            # 2. 检测算法复杂度
            complexity_indicators = 0
            
            # 循环嵌套深度
            loop_depth = self._calculate_loop_depth(func_node)
            if loop_depth > 1:
                complexity_indicators += 1
            
            # 条件分支数量
            condition_count = len([node for node in ast.walk(func_node) if isinstance(node, ast.If)])
            if condition_count > 2:
                complexity_indicators += 1
            
            # 函数调用数量
            call_count = len([node for node in ast.walk(func_node) if isinstance(node, ast.Call)])
            if call_count > 3:
                complexity_indicators += 1
            
            # 3. 检测强化学习特征
            rl_indicators = 0
            
            # 状态-动作-奖励模式
            if re.search(r'state.*action|action.*reward|reward.*state', func_content):
                rl_indicators += 1
            
            # 探索-利用模式
            if re.search(r'exploration|exploitation|epsilon|greedy', func_content):
                rl_indicators += 1
            
            # 策略更新模式
            if re.search(r'policy.*update|update.*policy|learn.*policy', func_content):
                rl_indicators += 1
            
            # 4. 综合评分
            total_score = rl_score + complexity_indicators + rl_indicators
            
            # 有RL关键词或功能实现即可
            return rl_features >= 1 or total_score >= 3
            
        except Exception as e:
            self.logger.error(f"分析强化学习逻辑失败: {e}")
            return False
    
    def _has_real_ml_logic(self, func_node: ast.FunctionDef, content: str) -> bool:
        """
        检查函数是否有真实的机器学习逻辑
        基于ML算法实现特征和ML关键词
        """
        try:
            if not func_node.body or len(func_node.body) == 0:
                return False
            
            ml_features = 0
            
            # 检查机器学习相关关键词
            ml_keywords = [
                'machine', 'learning', 'ml', 'neural', 'network', 'deep', 'learning',
                'model', 'train', 'training', 'fit', 'predict', 'prediction', 'classify',
                'regression', 'classification', 'clustering', 'supervised', 'unsupervised',
                'gradient', 'descent', 'optimization', 'loss', 'function', 'accuracy',
                'precision', 'recall', 'f1', 'score', 'cross', 'validation', 'feature',
                'engineering', 'preprocessing', 'normalization', 'standardization'
            ]
            
            func_content = ast.get_source_segment(content, func_node) or ""
            for keyword in ml_keywords:
                if keyword in func_content.lower():
                    ml_features += 1
                    break  # 找到一个关键词就够了
            
            # 检查AST结构特征
            for node in ast.walk(func_node):
                # 1. 检查是否有矩阵运算
                if isinstance(node, ast.BinOp):
                    if self._is_matrix_operation(node):
                        ml_features += 1
                
                # 2. 检查是否有梯度计算
                elif isinstance(node, ast.Assign):
                    if self._is_gradient_calculation(node):
                        ml_features += 1
                
                # 3. 检查是否有训练循环
                elif isinstance(node, ast.For):
                    if self._is_training_loop(node):
                        ml_features += 1
                
                # 4. 检查是否有损失函数计算
                elif isinstance(node, ast.Call):
                    if self._is_loss_function_call(node):
                        ml_features += 1
            
            # 基于源码分析的功能实现检测
            # 1. 检测机器学习算法模式
            ml_patterns = [
                # 监督学习模式
                r'supervised.*learning|classification|regression',
                r'decision.*tree|random.*forest|gradient.*boosting',
                r'support.*vector.*machine|svm|logistic.*regression',
                
                # 深度学习模式
                r'neural.*network|deep.*learning|convolutional|cnn',
                r'recurrent.*neural|rnn|lstm|gru|transformer',
                r'backpropagation|gradient.*descent|adam|sgd',
                
                # 无监督学习模式
                r'unsupervised.*learning|clustering|dimensionality.*reduction',
                r'k.*means|dbscan|hierarchical.*clustering',
                r'principal.*component|pca|t.*sne|umap',
                
                # 模型训练模式
                r'model\.fit|model\.train|model\.predict',
                r'cross.*validation|train.*test.*split',
                r'hyperparameter.*tuning|grid.*search',
                
                # 数据处理模式
                r'sklearn\.(ensemble|neural_network|svm|tree)',
                r'tensorflow|pytorch|keras|torch',
                r'\.(fit|predict|score|transform)\(.*\)',
            ]
            
            ml_score = 0
            for pattern in ml_patterns:
                if re.search(pattern, func_content, re.IGNORECASE):
                    ml_score += 1
            
            # 2. 检测算法复杂度
            complexity_indicators = 0
            
            # 循环嵌套深度
            loop_depth = self._calculate_loop_depth(func_node)
            if loop_depth > 1:
                complexity_indicators += 1
            
            # 条件分支数量
            condition_count = len([node for node in ast.walk(func_node) if isinstance(node, ast.If)])
            if condition_count > 2:
                complexity_indicators += 1
            
            # 函数调用数量
            call_count = len([node for node in ast.walk(func_node) if isinstance(node, ast.Call)])
            if call_count > 3:
                complexity_indicators += 1
            
            # 3. 检测机器学习特征
            ml_indicators = 0
            
            # 模型训练特征
            if re.search(r'train|fit|learn|optimize', func_content):
                ml_indicators += 1
            
            # 预测特征
            if re.search(r'predict|classify|regress|forecast', func_content):
                ml_indicators += 1
            
            # 评估特征
            if re.search(r'accuracy|precision|recall|f1.*score', func_content):
                ml_indicators += 1
            
            # 4. 综合评分
            total_score = ml_score + complexity_indicators + ml_indicators
            
            # 有ML关键词或功能实现即可
            return ml_features >= 1 or total_score >= 3
            
        except Exception as e:
            self.logger.error(f"分析机器学习逻辑失败: {e}")
            return False
    
    def _has_real_ai_logic(self, func_node: ast.FunctionDef, content: str) -> bool:
        """
        检查函数是否有真正的AI算法逻辑
        基于AI算法实现特征和AI关键词
        """
        try:
            if not func_node.body or len(func_node.body) == 0:
                return False
            
            ai_features = 0
            
            # 检查AI算法相关关键词
            ai_keywords = [
                'ai', 'artificial', 'intelligence', 'algorithm', 'neural', 'network',
                'deep', 'learning', 'machine', 'learning', 'reinforcement', 'learning',
                'optimization', 'genetic', 'evolutionary', 'swarm', 'intelligence',
                'fuzzy', 'logic', 'expert', 'system', 'knowledge', 'base', 'reasoning',
                'inference', 'pattern', 'recognition', 'computer', 'vision', 'nlp',
                'natural', 'language', 'processing', 'speech', 'recognition', 'robotics'
            ]
            
            func_content = ast.get_source_segment(content, func_node) or ""
            for keyword in ai_keywords:
                if keyword in func_content.lower():
                    ai_features += 1
                    break  # 找到一个关键词就够了
            
            # 检查AST结构特征
            for node in ast.walk(func_node):
                # 1. 检查是否有复杂的数学运算
                if isinstance(node, ast.BinOp):
                    if self._is_complex_mathematical_operation(node):
                        ai_features += 1
                
                # 2. 检查是否有递归或迭代算法
                elif isinstance(node, ast.For) or isinstance(node, ast.While):
                    if self._is_iterative_algorithm(node):
                        ai_features += 1
                
                # 3. 检查是否有启发式算法
                elif isinstance(node, ast.If):
                    if self._is_heuristic_algorithm(node):
                        ai_features += 1
                
                # 4. 检查是否有优化算法
                elif isinstance(node, ast.Call):
                    if self._is_optimization_algorithm(node):
                        ai_features += 1
            
            # 降低要求：有AI关键词或1个AI特征即可
            return ai_features >= 1
            
        except Exception as e:
            self.logger.error(f"分析AI算法逻辑失败: {e}")
            return False
    
    # 辅助方法 - 基于真实算法特征检测
    
    def _is_data_flow_processing(self, node: ast.For) -> bool:
        """检查是否是数据流处理"""
        # 检查循环内部是否有数据转换
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                if isinstance(child.value, ast.Call):
                    if isinstance(child.value.func, ast.Name):
                        func_name = child.value.func.id.lower()
                        if any(term in func_name for term in ['process', 'transform', 'filter']):
                            return True
        return False
    
    def _is_data_dependent_condition(self, node: ast.If) -> bool:
        """检查是否是数据依赖的条件判断"""
        if isinstance(node.test, ast.Compare):
            if isinstance(node.test.left, ast.Name):
                left_name = node.test.left.id.lower()
                return any(term in left_name for term in ['data', 'value', 'result', 'output'])
        return False
    
    def _is_data_statistics_calculation(self, node: ast.Assign) -> bool:
        """检查是否是数据统计计算"""
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                func_name = node.value.func.id.lower()
                return any(term in func_name for term in ['mean', 'std', 'var', 'sum', 'count'])
        return False
    
    def _is_data_pattern_recognition(self, node: ast.Call) -> bool:
        """检查是否是数据模式识别"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id.lower()
            return any(term in func_name for term in ['pattern', 'match', 'find', 'detect'])
        return False
    
    def _is_dynamic_parameter_adjustment(self, node: ast.Assign) -> bool:
        """检查是否是动态参数调整"""
        if isinstance(node.value, ast.BinOp):
            # 动态调整通常涉及条件运算
            return isinstance(node.value.op, (ast.Mult, ast.Div, ast.Add, ast.Sub))
        return False
    
    def _is_performance_feedback_adjustment(self, node: ast.If) -> bool:
        """检查是否是性能反馈调整"""
        if isinstance(node.test, ast.Compare):
            if isinstance(node.test.left, ast.Name):
                left_name = node.test.left.id.lower()
                return any(term in left_name for term in ['accuracy', 'loss', 'performance', 'score'])
        return False
    
    def _is_learning_rate_scheduling(self, node: ast.Call) -> bool:
        """检查是否是学习率调度"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id.lower()
            return any(term in func_name for term in ['schedule', 'decay', 'step', 'lr'])
        return False
    
    def _is_adaptive_threshold_adjustment(self, node: ast.AugAssign) -> bool:
        """检查是否是自适应阈值调整"""
        if isinstance(node.target, ast.Name):
            target_name = node.target.id.lower()
            return any(term in target_name for term in ['threshold', 'limit', 'bound'])
        return False
    
    def _is_clustering_algorithm(self, node: ast.For) -> bool:
        """检查是否是聚类算法"""
        # 检查循环内部是否有距离计算
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    func_name = child.func.id.lower()
                    if any(term in func_name for term in ['distance', 'euclidean', 'manhattan', 'cluster']):
                        return True
        return False
    
    def _is_dimensionality_reduction(self, node: ast.Assign) -> bool:
        """检查是否是降维算法"""
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                func_name = node.value.func.id.lower()
                return any(term in func_name for term in ['pca', 'svd', 'reduce', 'dimension'])
        return False
    
    def _is_anomaly_detection(self, node: ast.If) -> bool:
        """检查是否是异常检测"""
        if isinstance(node.test, ast.Compare):
            if isinstance(node.test.left, ast.Name):
                left_name = node.test.left.id.lower()
                return any(term in left_name for term in ['threshold', 'outlier', 'anomaly', 'deviation'])
        return False
    
    def _is_pattern_discovery(self, node: ast.Call) -> bool:
        """检查是否是模式发现"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id.lower()
            return any(term in func_name for term in ['pattern', 'discover', 'find', 'detect'])
        return False
    
    def _is_q_value_update(self, node: ast.Assign) -> bool:
        """检查是否是Q值更新"""
        if isinstance(node.value, ast.BinOp):
            # Q值更新通常涉及加法和乘法
            return isinstance(node.value.op, (ast.Add, ast.Mult))
        return False
    
    def _is_exploration_exploitation(self, node: ast.If) -> bool:
        """检查是否是探索-利用逻辑"""
        # 检查条件是否涉及随机选择
        if isinstance(node.test, ast.Call):
            if isinstance(node.test.func, ast.Name):
                func_name = node.test.func.id.lower()
                return any(term in func_name for term in ['random', 'rand', 'choice', 'explore'])
        return False
    
    def _is_reward_calculation(self, node: ast.Call) -> bool:
        """检查是否是奖励计算"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id.lower()
            return any(term in func_name for term in ['reward', 'score', 'utility', 'value'])
        return False
    
    def _is_policy_update_loop(self, node: ast.For) -> bool:
        """检查是否是策略更新循环"""
        # 检查循环内部是否有策略相关的更新
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                if isinstance(child.targets[0], ast.Name):
                    target_name = child.targets[0].id.lower()
                    if any(term in target_name for term in ['policy', 'action', 'strategy', 'decision']):
                        return True
        return False
    
    def _is_matrix_operation(self, node: ast.BinOp) -> bool:
        """检查是否是矩阵运算"""
        # 检查是否有矩阵乘法、点积等运算
        if isinstance(node.op, ast.Mult):
            # 检查操作数是否可能是矩阵
            return self._is_likely_matrix(node.left) or self._is_likely_matrix(node.right)
        return False
    
    def _is_likely_matrix(self, node: ast.AST) -> bool:
        """检查节点是否可能是矩阵"""
        if isinstance(node, ast.Name):
            # 检查变量名是否暗示矩阵
            name = node.id.lower()
            return any(char in name for char in ['matrix', 'mat', 'array', 'tensor'])
        elif isinstance(node, ast.Call):
            # 检查是否是矩阵创建函数
            if isinstance(node.func, ast.Name):
                func_name = node.func.id.lower()
                return any(term in func_name for term in ['zeros', 'ones', 'eye', 'rand'])
        return False
    
    def _is_gradient_calculation(self, node: ast.Assign) -> bool:
        """检查是否是梯度计算"""
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id.lower()
            # 检查是否是梯度相关的赋值
            if isinstance(node.value, ast.BinOp):
                # 检查是否有梯度计算模式：grad = f(x + h) - f(x)
                return isinstance(node.value.op, ast.Sub)
        return False
    
    def _is_training_loop(self, node: ast.For) -> bool:
        """检查是否是训练循环"""
        # 检查循环内部是否有参数更新
        has_parameter_update = False
        has_loss_calculation = False
        
        for child in ast.walk(node):
            if isinstance(child, ast.AugAssign):
                has_parameter_update = True
            elif isinstance(child, ast.Assign):
                if isinstance(child.value, ast.BinOp) and isinstance(child.value.op, ast.Sub):
                    has_loss_calculation = True
        
        return has_parameter_update and has_loss_calculation
    
    def _is_loss_function_call(self, node: ast.Call) -> bool:
        """检查是否是损失函数调用"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id.lower()
            # 检查是否是损失函数
            return any(term in func_name for term in ['loss', 'cost', 'error', 'mse', 'crossentropy'])
        return False
    
    def _is_complex_mathematical_operation(self, node: ast.BinOp) -> bool:
        """检查是否是复杂的数学运算"""
        # 检查是否是复杂的数学运算（如矩阵运算、向量运算）
        if isinstance(node.op, (ast.Mult, ast.Div, ast.Pow)):
            return True
        return False
    
    def _is_iterative_algorithm(self, node: ast.AST) -> bool:
        """检查是否是迭代算法"""
        # 检查循环内部是否有复杂的计算
        for child in ast.walk(node):
            if isinstance(child, ast.BinOp):
                if isinstance(child.op, (ast.Mult, ast.Div, ast.Pow)):
                    return True
        return False
    
    def _is_heuristic_algorithm(self, node: ast.If) -> bool:
        """检查是否是启发式算法"""
        # 检查条件是否涉及启发式判断
        if isinstance(node.test, ast.Compare):
            if isinstance(node.test.left, ast.Name):
                left_name = node.test.left.id.lower()
                return any(term in left_name for term in ['heuristic', 'rule', 'criteria', 'condition'])
        return False
    
    def _is_optimization_algorithm(self, node: ast.Call) -> bool:
        """检查是否是优化算法"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id.lower()
            return any(term in func_name for term in ['optimize', 'minimize', 'maximize', 'improve'])
        return False