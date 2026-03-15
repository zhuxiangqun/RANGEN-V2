"""
基础分析器抽象类
定义所有分析器的通用接口和AST/语义分析功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import ast
import logging
import re

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """基础分析器抽象类 - 基于AST和语义分析"""
    
    def __init__(self, python_files: List[str]):
        """
        初始化分析器
        
        Args:
            python_files: Python文件路径列表
        """
        self.python_files = python_files
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """
        执行分析
        
        Returns:
            分析结果字典
        """
        pass
    
    def _read_file_content(self, file_path: str) -> str:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"读取文件失败 {file_path}: {e}")
            return ""
    
    def _parse_ast(self, content: str) -> Optional[ast.AST]:
        """
        解析AST
        
        Args:
            content: 文件内容
            
        Returns:
            AST树
        """
        try:
            return ast.parse(content)
        except Exception as e:
            self.logger.error(f"解析AST失败: {e}")
            return None
    
    def _analyze_function_intelligence_advanced(self, func_node: ast.FunctionDef, content: str) -> bool:
        """
        深度分析函数的智能化程度 - 基于真实算法实现分析
        
        Args:
            func_node: 函数AST节点
            content: 文件内容
            
        Returns:
            是否有真实智能功能
        """
        try:
            # 进行真实算法实现分析
            algorithm_analysis = self._analyze_real_algorithm_implementation(func_node, content)
            return algorithm_analysis['has_real_intelligence']
        except Exception as e:
            self.logger.error(f"分析函数智能程度失败: {e}")
            return False
    
    def _analyze_real_algorithm_implementation(self, func_node: ast.FunctionDef, content: str) -> Dict[str, Any]:
        """
        分析真实算法实现 - 基于实际代码逻辑分析
        
        Args:
            func_node: 函数AST节点
            content: 文件内容
            
        Returns:
            算法实现分析结果
        """
        analysis = {
            'has_real_intelligence': False,
            'algorithm_complexity': 0,
            'mathematical_operations': 0,
            'iterative_processes': 0,
            'optimization_algorithms': 0,
            'learning_algorithms': 0,
            'reasoning_algorithms': 0,
            'data_processing_algorithms': 0,
            'innovation_score': 0.0,
            'real_implementation_score': 0.0
        }
        
        # 分析真实的算法逻辑
        algorithm_logic = self._analyze_real_algorithm_logic(func_node)
        analysis.update(algorithm_logic)
        
        # 分析数学计算和算法复杂度
        math_analysis = self._analyze_mathematical_operations(func_node)
        analysis.update(math_analysis)
        
        # 分析迭代和循环算法
        iteration_analysis = self._analyze_iterative_algorithms(func_node)
        analysis.update(iteration_analysis)
        
        # 分析优化算法
        optimization_analysis = self._analyze_optimization_algorithms(func_node)
        analysis.update(optimization_analysis)
        
        # 分析学习算法
        learning_analysis = self._analyze_learning_algorithms(func_node)
        analysis.update(learning_analysis)
        
        # 分析推理算法
        reasoning_analysis = self._analyze_reasoning_algorithms(func_node)
        analysis.update(reasoning_analysis)
        
        # 分析数据处理算法
        data_processing_analysis = self._analyze_data_processing_algorithms(func_node)
        analysis.update(data_processing_analysis)
        
        # 分析创新性和原创性
        innovation_analysis = self._analyze_algorithm_innovation(func_node, content)
        analysis.update(innovation_analysis)
        
        # 计算真实实现分数 - 更严格的判断标准
        analysis['real_implementation_score'] = self._calculate_real_implementation_score(analysis)
        
        # 只有真正有算法实现才认为是智能的
        analysis['has_real_intelligence'] = (
            analysis['has_real_algorithm'] and 
            analysis['real_implementation_score'] > 0.3 and
            analysis['complexity_indicators'] > 1
        )
        
        return analysis
    
    def _analyze_mathematical_operations(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """分析数学计算操作 - 基于实际代码逻辑分析"""
        math_analysis = {
            'mathematical_operations': 0,
            'complex_math_operations': 0,
            'statistical_operations': 0,
            'linear_algebra_operations': 0,
            'optimization_math': 0,
            'real_algorithm_complexity': 0
        }
        
        # 分析实际的数学计算逻辑
        for node in ast.walk(func_node):
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv)):
                    math_analysis['mathematical_operations'] += 1
                    # 检查是否是复杂的数学表达式
                    if self._is_complex_math_expression(node):
                        math_analysis['complex_math_operations'] += 1
                        math_analysis['real_algorithm_complexity'] += 1
            elif isinstance(node, ast.Call):
                # 检查是否是真正的数学函数调用
                if self._is_real_math_function_call(node):
                    math_analysis['complex_math_operations'] += 1
                    math_analysis['mathematical_operations'] += 1
                    math_analysis['real_algorithm_complexity'] += 1
                elif self._is_real_statistical_function(node):
                    math_analysis['statistical_operations'] += 1
                    math_analysis['mathematical_operations'] += 1
                    math_analysis['real_algorithm_complexity'] += 1
                elif self._is_real_linear_algebra_function(node):
                    math_analysis['linear_algebra_operations'] += 1
                    math_analysis['mathematical_operations'] += 1
                    math_analysis['real_algorithm_complexity'] += 1
                elif self._is_real_optimization_function(node):
                    math_analysis['optimization_math'] += 1
                    math_analysis['mathematical_operations'] += 1
                    math_analysis['real_algorithm_complexity'] += 1
        
        return math_analysis
    
    def _analyze_iterative_algorithms(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """分析迭代算法"""
        iteration_analysis = {
            'iterative_processes': 0,
            'convergence_algorithms': 0,
            'optimization_loops': 0,
            'learning_iterations': 0,
            'algorithm_complexity': 0
        }
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.For, ast.While)):
                iteration_analysis['iterative_processes'] += 1
                iteration_analysis['algorithm_complexity'] += 1
                
                # 检查循环内部是否有收敛条件
                for child in ast.walk(node):
                    if isinstance(child, ast.If):
                        if self._has_convergence_condition(child):
                            iteration_analysis['convergence_algorithms'] += 1
                    
                    # 检查是否有参数更新（学习算法特征）
                    if isinstance(child, ast.Assign):
                        if self._is_parameter_update(child):
                            iteration_analysis['learning_iterations'] += 1
                    
                    # 检查是否有优化操作
                    if isinstance(child, ast.Call):
                        call_name = self._get_call_name(child)
                        if call_name and any(opt_term in call_name.lower() for opt_term in ['optimize', 'minimize', 'maximize', 'gradient', 'update']):
                            iteration_analysis['optimization_loops'] += 1
        
        return iteration_analysis
    
    def _analyze_optimization_algorithms(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """分析优化算法 - 基于实际代码逻辑"""
        optimization_analysis = {
            'optimization_algorithms': 0,
            'gradient_based': 0,
            'heuristic_optimization': 0,
            'constraint_optimization': 0,
            'multi_objective_optimization': 0
        }
        
        # 检查是否有真正的优化算法模式
        has_iterative_optimization = False
        has_gradient_calculation = False
        has_parameter_update = False
        has_convergence_check = False
        has_objective_function = False
        
        for node in ast.walk(func_node):
            # 检查是否有迭代优化循环
            if isinstance(node, (ast.For, ast.While)):
                # 检查循环内部是否有参数更新和收敛检查
                for child in ast.walk(node):
                    if isinstance(child, ast.Assign):
                        # 检查是否是参数更新（如权重更新）
                        if self._is_parameter_update(child):
                            has_parameter_update = True
                            optimization_analysis['optimization_algorithms'] += 1
                    elif isinstance(child, ast.If):
                        # 检查是否有收敛条件
                        if self._is_convergence_condition(child.test):
                            has_convergence_check = True
                            optimization_analysis['optimization_algorithms'] += 1
                
                if has_parameter_update and has_convergence_check:
                    has_iterative_optimization = True
            
            # 检查是否有梯度计算（数学运算模式）
            elif isinstance(node, ast.BinOp):
                if self._is_gradient_calculation(node):
                    has_gradient_calculation = True
                    optimization_analysis['gradient_based'] += 1
                    optimization_analysis['optimization_algorithms'] += 1
            
            # 检查是否有目标函数（函数调用模式）
            elif isinstance(node, ast.Call):
                if self._is_objective_function_call(node):
                    has_objective_function = True
                    optimization_analysis['optimization_algorithms'] += 1
        
        # 根据检测到的模式判断算法类型
        if has_iterative_optimization and has_gradient_calculation:
            optimization_analysis['gradient_based'] += 1
        elif has_iterative_optimization and not has_gradient_calculation:
            optimization_analysis['heuristic_optimization'] += 1
        
        return optimization_analysis
    
    def _analyze_learning_algorithms(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """分析学习算法 - 基于实际代码逻辑"""
        learning_analysis = {
            'learning_algorithms': 0,
            'supervised_learning': 0,
            'unsupervised_learning': 0,
            'reinforcement_learning': 0,
            'neural_networks': 0,
            'parameter_updates': 0
        }
        
        # 检查是否有真正的学习算法模式
        has_forward_pass = False
        has_backward_pass = False
        has_parameter_update = False
        has_loss_calculation = False
        has_activation_function = False
        has_weight_initialization = False
        
        for node in ast.walk(func_node):
            # 检查前向传播模式
            if self._is_forward_pass_pattern(node):
                has_forward_pass = True
                learning_analysis['neural_networks'] += 1
                learning_analysis['learning_algorithms'] += 1
            
            # 检查反向传播模式
            elif self._is_backward_pass_pattern(node):
                has_backward_pass = True
                learning_analysis['neural_networks'] += 1
                learning_analysis['learning_algorithms'] += 1
            
            # 检查参数更新
            elif isinstance(node, ast.Assign):
                if self._is_parameter_update(node):
                    has_parameter_update = True
                    learning_analysis['parameter_updates'] += 1
                    learning_analysis['learning_algorithms'] += 1
            
            # 检查损失函数计算
            elif self._is_loss_calculation(node):
                has_loss_calculation = True
                learning_analysis['learning_algorithms'] += 1
            
            # 检查激活函数
            elif self._is_activation_function(node):
                has_activation_function = True
                learning_analysis['neural_networks'] += 1
            
            # 检查权重初始化
            elif self._is_weight_initialization(node):
                has_weight_initialization = True
                learning_analysis['neural_networks'] += 1
        
        # 根据检测到的模式判断学习类型
        if has_forward_pass and has_backward_pass and has_parameter_update:
            learning_analysis['supervised_learning'] += 1
        elif has_forward_pass and not has_backward_pass:
            learning_analysis['unsupervised_learning'] += 1
        elif has_parameter_update and not has_forward_pass:
            learning_analysis['reinforcement_learning'] += 1
        
        return learning_analysis
    
    def _analyze_reasoning_algorithms(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """分析推理算法"""
        reasoning_analysis = {
            'reasoning_algorithms': 0,
            'logical_reasoning': 0,
            'probabilistic_reasoning': 0,
            'causal_reasoning': 0,
            'abductive_reasoning': 0,
            'deductive_reasoning': 0
        }
        
        logical_keywords = ['logic', 'inference', 'deduction', 'induction', 'premise', 'conclusion']
        probabilistic_keywords = ['probability', 'bayesian', 'likelihood', 'posterior', 'prior', 'uncertainty']
        causal_keywords = ['causal', 'cause', 'effect', 'causality', 'causal_chain']
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                call_name = self._get_call_name(node)
                if call_name:
                    if any(log_term in call_name.lower() for log_term in logical_keywords):
                        reasoning_analysis['logical_reasoning'] += 1
                        reasoning_analysis['reasoning_algorithms'] += 1
                    if any(prob_term in call_name.lower() for prob_term in probabilistic_keywords):
                        reasoning_analysis['probabilistic_reasoning'] += 1
                        reasoning_analysis['reasoning_algorithms'] += 1
                    if any(causal_term in call_name.lower() for causal_term in causal_keywords):
                        reasoning_analysis['causal_reasoning'] += 1
                        reasoning_analysis['reasoning_algorithms'] += 1
        
        return reasoning_analysis
    
    def _analyze_data_processing_algorithms(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """分析数据处理算法"""
        data_analysis = {
            'data_processing_algorithms': 0,
            'feature_engineering': 0,
            'data_transformation': 0,
            'pattern_recognition': 0,
            'signal_processing': 0
        }
        
        feature_keywords = ['feature', 'extract', 'selection', 'engineering', 'preprocessing']
        transform_keywords = ['transform', 'normalize', 'standardize', 'scale', 'encode', 'decode']
        pattern_keywords = ['pattern', 'detect', 'recognize', 'match', 'similarity', 'distance']
        signal_keywords = ['filter', 'fourier', 'wavelet', 'spectrum', 'frequency', 'signal']
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                call_name = self._get_call_name(node)
                if call_name:
                    if any(feat_term in call_name.lower() for feat_term in feature_keywords):
                        data_analysis['feature_engineering'] += 1
                        data_analysis['data_processing_algorithms'] += 1
                    if any(trans_term in call_name.lower() for trans_term in transform_keywords):
                        data_analysis['data_transformation'] += 1
                        data_analysis['data_processing_algorithms'] += 1
                    if any(pat_term in call_name.lower() for pat_term in pattern_keywords):
                        data_analysis['pattern_recognition'] += 1
                        data_analysis['data_processing_algorithms'] += 1
                    if any(sig_term in call_name.lower() for sig_term in signal_keywords):
                        data_analysis['signal_processing'] += 1
                        data_analysis['data_processing_algorithms'] += 1
        
        return data_analysis
    
    def _analyze_algorithm_innovation(self, func_node: ast.FunctionDef, content: str) -> Dict[str, Any]:
        """分析算法创新性"""
        innovation_analysis = {
            'innovation_score': 0.0,
            'original_implementations': 0,
            'novel_approaches': 0,
            'custom_algorithms': 0
        }
        
        # 检查是否有自定义算法实现
        func_name = func_node.name.lower()
        if any(term in func_name for term in ['custom', 'novel', 'original', 'new', 'improved', 'enhanced']):
            innovation_analysis['custom_algorithms'] += 1
        
        # 检查函数复杂度（原创算法通常更复杂）
        complexity_score = self._calculate_function_complexity(func_node)
        if complexity_score > 0.7:
            innovation_analysis['original_implementations'] += 1
        
        # 检查是否有创新的数学方法
        math_operations = self._analyze_mathematical_operations(func_node)
        if math_operations['mathematical_operations'] > 5:
            innovation_analysis['novel_approaches'] += 1
        
        # 计算创新分数
        innovation_analysis['innovation_score'] = (
            innovation_analysis['original_implementations'] * 0.4 +
            innovation_analysis['novel_approaches'] * 0.3 +
            innovation_analysis['custom_algorithms'] * 0.3
        )
        
        return innovation_analysis
    
    def _has_convergence_condition(self, if_node: ast.If) -> bool:
        """检查是否有收敛条件"""
        # 简化的收敛条件检测
        if isinstance(if_node.test, ast.Compare):
            if isinstance(if_node.test.left, ast.Name):
                var_name = if_node.test.left.id.lower()
                if any(term in var_name for term in ['convergence', 'threshold', 'tolerance', 'error', 'delta']):
                    return True
        return False
    
    def _is_parameter_update(self, assign_node: ast.Assign) -> bool:
        """检查是否是参数更新"""
        if isinstance(assign_node.targets[0], ast.Name):
            var_name = assign_node.targets[0].id.lower()
            if any(term in var_name for term in ['weight', 'bias', 'parameter', 'theta', 'w', 'b']):
                return True
        return False
    
    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> float:
        """计算函数复杂度"""
        complexity = 0
        for node in ast.walk(func_node):
            if isinstance(node, ast.If):
                complexity += 1
            elif isinstance(node, (ast.For, ast.While)):
                complexity += 2
            elif isinstance(node, ast.Call):
                complexity += 0.5
            elif isinstance(node, ast.BinOp):
                complexity += 0.1
        
        return min(complexity / 20.0, 1.0)  # 归一化到0-1
    
    def _calculate_real_implementation_score(self, analysis: Dict[str, Any]) -> float:
        """计算真实实现分数"""
        score = 0.0
        
        # 数学操作权重
        score += min(analysis.get('mathematical_operations', 0) / 10.0, 0.2)
        
        # 迭代算法权重
        score += min(analysis.get('iterative_processes', 0) / 5.0, 0.2)
        
        # 优化算法权重
        score += min(analysis.get('optimization_algorithms', 0) / 3.0, 0.2)
        
        # 学习算法权重
        score += min(analysis.get('learning_algorithms', 0) / 3.0, 0.2)
        
        # 推理算法权重
        score += min(analysis.get('reasoning_algorithms', 0) / 3.0, 0.1)
        
        # 数据处理算法权重
        score += min(analysis.get('data_processing_algorithms', 0) / 5.0, 0.1)
        
        return min(score, 1.0)
    
    def _is_complex_math_expression(self, binop_node: ast.BinOp) -> bool:
        """检查是否是复杂的数学表达式"""
        # 检查表达式的复杂度
        complexity = 0
        for node in ast.walk(binop_node):
            if isinstance(node, ast.BinOp):
                complexity += 1
            elif isinstance(node, ast.Call):
                complexity += 2
            elif isinstance(node, ast.Name):
                complexity += 0.5
        
        # 如果表达式包含多个操作和函数调用，认为是复杂的
        return complexity > 3
    
    def _is_real_math_function_call(self, call_node: ast.Call) -> bool:
        """检查是否是真正的数学函数调用"""
        call_name = self._get_call_name(call_node)
        if not call_name:
            return False
        
        # 检查是否来自数学库
        if isinstance(call_node.func, ast.Attribute):
            if isinstance(call_node.func.value, ast.Name):
                module_name = call_node.func.value.id
                if module_name in ['math', 'numpy', 'scipy', 'torch', 'tensorflow']:
                    return True
        
        # 检查是否是真正的数学函数（不是简单的规则）
        real_math_functions = {
            'sqrt', 'log', 'exp', 'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
            'sinh', 'cosh', 'tanh', 'gamma', 'beta', 'erf', 'erfc', 'bessel',
            'fft', 'ifft', 'convolve', 'correlate', 'eigenvals', 'eigenvecs',
            'svd', 'qr', 'lu', 'cholesky', 'det', 'inv', 'pinv', 'norm'
        }
        
        return call_name in real_math_functions
    
    def _is_real_statistical_function(self, call_node: ast.Call) -> bool:
        """检查是否是真正的统计函数"""
        call_name = self._get_call_name(call_node)
        if not call_name:
            return False
        
        # 检查是否来自统计库
        if isinstance(call_node.func, ast.Attribute):
            if isinstance(call_node.func.value, ast.Name):
                module_name = call_node.func.value.id
                if module_name in ['numpy', 'scipy', 'pandas', 'sklearn', 'statsmodels']:
                    return True
        
        # 检查是否是真正的统计函数
        real_stat_functions = {
            'mean', 'std', 'var', 'median', 'quantile', 'percentile',
            'corrcoef', 'cov', 'correlate', 'histogram', 'kde',
            'normaltest', 'ttest', 'chi2_contingency', 'anova',
            'regression', 'fit', 'predict', 'score'
        }
        
        return call_name in real_stat_functions
    
    def _is_real_linear_algebra_function(self, call_node: ast.Call) -> bool:
        """检查是否是真正的线性代数函数"""
        call_name = self._get_call_name(call_node)
        if not call_name:
            return False
        
        # 检查是否来自线性代数库
        if isinstance(call_node.func, ast.Attribute):
            if isinstance(call_node.func.value, ast.Name):
                module_name = call_node.func.value.id
                if module_name in ['numpy', 'scipy', 'torch', 'tensorflow']:
                    return True
        
        # 检查是否是真正的线性代数函数
        real_linalg_functions = {
            'dot', 'matmul', 'tensordot', 'einsum', 'transpose', 'T',
            'eig', 'eigh', 'eigvals', 'eigvalsh', 'svd', 'qr', 'lu',
            'cholesky', 'det', 'inv', 'pinv', 'lstsq', 'solve',
            'norm', 'cond', 'rank', 'trace', 'diag', 'triu', 'tril'
        }
        
        return call_name in real_linalg_functions
    
    def _is_real_optimization_function(self, call_node: ast.Call) -> bool:
        """检查是否是真正的优化函数"""
        call_name = self._get_call_name(call_node)
        if not call_name:
            return False
        
        # 检查是否来自优化库
        if isinstance(call_node.func, ast.Attribute):
            if isinstance(call_node.func.value, ast.Name):
                module_name = call_node.func.value.id
                if module_name in ['scipy', 'sklearn', 'torch', 'tensorflow']:
                    return True
        
        # 检查是否是真正的优化函数
        real_opt_functions = {
            'minimize', 'maximize', 'optimize', 'fmin', 'fmin_cg', 'fmin_bfgs',
            'fmin_powell', 'fmin_slsqp', 'differential_evolution', 'basinhopping',
            'dual_annealing', 'shgo', 'differential_evolution', 'genetic_algorithm',
            'gradient_descent', 'adam', 'rmsprop', 'adagrad', 'momentum'
        }
        
        return call_name in real_opt_functions
    
    def _analyze_real_algorithm_logic(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """分析真实的算法逻辑"""
        algorithm_analysis = {
            'has_real_algorithm': False,
            'algorithm_type': 'none',
            'complexity_indicators': 0,
            'mathematical_rigor': 0,
            'iterative_convergence': 0,
            'parameter_optimization': 0
        }
        
        # 检查是否有真正的算法实现
        has_loops = False
        has_math = False
        has_convergence = False
        has_optimization = False
        
        for node in ast.walk(func_node):
            # 检查循环结构
            if isinstance(node, (ast.For, ast.While)):
                has_loops = True
                # 检查循环内部是否有收敛条件
                if self._has_convergence_logic(node):
                    has_convergence = True
                    algorithm_analysis['iterative_convergence'] += 1
            
            # 检查数学计算
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
                    has_math = True
                    algorithm_analysis['mathematical_rigor'] += 1
            
            # 检查优化逻辑
            if isinstance(node, ast.Call):
                if self._is_real_optimization_function(node):
                    has_optimization = True
                    algorithm_analysis['parameter_optimization'] += 1
        
        # 判断算法类型
        if has_loops and has_math and has_convergence:
            algorithm_analysis['algorithm_type'] = 'iterative_optimization'
            algorithm_analysis['has_real_algorithm'] = True
        elif has_loops and has_math:
            algorithm_analysis['algorithm_type'] = 'iterative_computation'
            algorithm_analysis['has_real_algorithm'] = True
        elif has_math and has_optimization:
            algorithm_analysis['algorithm_type'] = 'mathematical_optimization'
            algorithm_analysis['has_real_algorithm'] = True
        elif has_math:
            algorithm_analysis['algorithm_type'] = 'mathematical_computation'
            algorithm_analysis['has_real_algorithm'] = True
        
        # 计算复杂度指标
        algorithm_analysis['complexity_indicators'] = (
            algorithm_analysis['mathematical_rigor'] +
            algorithm_analysis['iterative_convergence'] +
            algorithm_analysis['parameter_optimization']
        )
        
        return algorithm_analysis
    
    def _has_convergence_logic(self, loop_node) -> bool:
        """检查循环是否有收敛逻辑"""
        for child in ast.walk(loop_node):
            if isinstance(child, ast.If):
                # 检查是否有收敛条件
                if self._is_convergence_condition(child.test):
                    return True
        return False
    
    def _is_gradient_calculation(self, binop_node: ast.BinOp) -> bool:
        """检查是否是梯度计算"""
        # 检查是否是导数计算模式：f(x+h) - f(x) / h
        if isinstance(binop_node.op, ast.Div):
            if isinstance(binop_node.left, ast.BinOp) and isinstance(binop_node.left.op, ast.Sub):
                return True
        
        # 检查是否是梯度下降模式：x - learning_rate * gradient
        if isinstance(binop_node.op, ast.Sub):
            if isinstance(binop_node.right, ast.BinOp) and isinstance(binop_node.right.op, ast.Mult):
                return True
        
        return False
    
    def _is_objective_function_call(self, call_node: ast.Call) -> bool:
        """检查是否是目标函数调用"""
        # 检查是否来自优化库
        if isinstance(call_node.func, ast.Attribute):
            if isinstance(call_node.func.value, ast.Name):
                module_name = call_node.func.value.id
                if module_name in ['scipy', 'sklearn', 'torch', 'tensorflow']:
                    return True
        
        # 检查是否是数学函数调用（可能的目标函数）
        call_name = self._get_call_name(call_node)
        if call_name in ['minimize', 'maximize', 'optimize', 'fmin', 'fmin_cg', 'fmin_bfgs']:
            return True
        
        return False
    
    def _is_convergence_condition(self, test_node) -> bool:
        """检查是否是收敛条件 - 基于代码逻辑"""
        if isinstance(test_node, ast.Compare):
            # 检查是否是比较操作
            if isinstance(test_node.left, ast.Name):
                var_name = test_node.left.id.lower()
                # 检查变量名是否与收敛相关
                convergence_terms = ['error', 'delta', 'diff', 'threshold', 'tolerance', 'convergence']
                if any(term in var_name for term in convergence_terms):
                    return True
            
            # 检查是否是数值比较（如 error < threshold）
            if isinstance(test_node.left, ast.BinOp) and isinstance(test_node.comparators[0], ast.Constant):
                if isinstance(test_node.ops[0], (ast.Lt, ast.LtE)):
                    return True
        
        return False
    
    def _is_forward_pass_pattern(self, node) -> bool:
        """检查是否是前向传播模式"""
        if isinstance(node, ast.Assign):
            # 检查是否是矩阵乘法模式：output = input @ weights + bias
            if isinstance(node.value, ast.BinOp):
                if isinstance(node.value.op, ast.Add):
                    if isinstance(node.value.left, ast.BinOp) and isinstance(node.value.left.op, ast.MatMult):
                        return True
        return False
    
    def _is_backward_pass_pattern(self, node) -> bool:
        """检查是否是反向传播模式"""
        if isinstance(node, ast.Assign):
            # 检查是否是梯度计算模式：grad = error * derivative
            if isinstance(node.value, ast.BinOp):
                if isinstance(node.value.op, ast.Mult):
                    return True
        return False
    
    def _is_loss_calculation(self, node) -> bool:
        """检查是否是损失函数计算"""
        if isinstance(node, ast.Assign):
            # 检查是否是损失计算模式：loss = sum((pred - target) ** 2)
            if isinstance(node.value, ast.Call):
                call_name = self._get_call_name(node.value)
                if call_name in ['sum', 'mean', 'average']:
                    return True
        return False
    
    def _is_activation_function(self, node) -> bool:
        """检查是否是激活函数"""
        if isinstance(node, ast.Call):
            call_name = self._get_call_name(node)
            # 检查是否是激活函数调用
            if call_name in ['tanh', 'sigmoid', 'relu', 'softmax', 'log_softmax']:
                return True
        return False
    
    def _is_weight_initialization(self, node) -> bool:
        """检查是否是权重初始化"""
        if isinstance(node, ast.Assign):
            # 检查是否是权重初始化模式：weights = random.randn(...)
            if isinstance(node.value, ast.Call):
                call_name = self._get_call_name(node.value)
                if call_name in ['randn', 'random', 'uniform', 'normal']:
                    return True
        return False
    
    def _get_call_name(self, call_node: ast.Call) -> str:
        """获取函数调用名称"""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return ""
    
    
    def _detect_patterns_in_file(self, file_path: str, patterns: List[str]) -> int:
        """
        在文件中检测模式 - 完全基于AST深度分析
        
        Args:
            file_path: 文件路径
            patterns: 模式列表（已废弃，保持兼容性）
            
        Returns:
            匹配数量
        """
        content = self._read_file_content(file_path)
        if not content:
            return 0
        
        tree = self._parse_ast(content)
        if not tree:
            return 0
        
        # 完全基于AST深度分析，不依赖关键词匹配
        real_implementation_count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 分析函数是否包含真实的功能实现
                if self._has_real_functionality_implementation(node, content):
                    real_implementation_count += 1
            elif isinstance(node, ast.ClassDef):
                # 分析类是否包含真实的功能实现
                if self._has_real_class_functionality(node, content):
                    real_implementation_count += 1
        
        # 完全基于AST分析结果，不使用关键词匹配
        return real_implementation_count
    
    def _has_real_functionality_implementation(self, func_node: ast.FunctionDef, content: str) -> bool:
        """
        检查函数是否有真实的功能实现 - 基于AST深度分析
        
        Args:
            func_node: 函数AST节点
            content: 文件内容
            
        Returns:
            是否有真实功能实现
        """
        try:
            # 检查函数体是否有实际逻辑
            if not func_node.body or len(func_node.body) == 0:
                return False
            
            # 基于AST深度分析功能实现
            functionality_score = 0
            
            for node in ast.walk(func_node):
                # 1. 数学运算复杂度分析
                if isinstance(node, ast.BinOp):
                    if self._is_complex_math_operation(node):
                        functionality_score += 2
                    else:
                        functionality_score += 1
                elif isinstance(node, ast.UnaryOp):
                    functionality_score += 1
                
                # 2. 比较操作分析
                elif isinstance(node, ast.Compare):
                    if self._is_complex_comparison(node):
                        functionality_score += 2
                    else:
                        functionality_score += 1
                
                # 3. 循环结构分析
                elif isinstance(node, (ast.For, ast.While)):
                    if self._is_complex_loop(node):
                        functionality_score += 3
                    else:
                        functionality_score += 2
                
                # 4. 条件判断分析
                elif isinstance(node, ast.If):
                    if self._is_complex_conditional(node):
                        functionality_score += 2
                    else:
                        functionality_score += 1
                
                # 5. 函数调用分析
                elif isinstance(node, ast.Call):
                    call_complexity = self._analyze_call_complexity(node)
                    functionality_score += call_complexity
                
                # 6. 数据处理分析
                elif isinstance(node, ast.Assign):
                    if self._is_complex_assignment(node):
                        functionality_score += 2
                    elif self._is_data_processing_assignment(node):
                        functionality_score += 1
                
                # 7. 异常处理分析
                elif isinstance(node, ast.Try):
                    functionality_score += 2
                
                # 8. 上下文管理分析
                elif isinstance(node, ast.With):
                    functionality_score += 2
            
            # 需要至少3分才认为是真实功能实现
            return functionality_score >= 3
            
        except Exception as e:
            self.logger.error(f"分析函数功能实现失败: {e}")
            return False
    
    def _is_complex_math_operation(self, node: ast.BinOp) -> bool:
        """检查是否是复杂的数学运算"""
        # 检查运算符复杂度
        complex_ops = {ast.Pow, ast.FloorDiv, ast.Mod}
        if type(node.op) in complex_ops:
            return True
        
        # 检查嵌套运算
        if isinstance(node.left, ast.BinOp) or isinstance(node.right, ast.BinOp):
            return True
        
        return False
    
    def _is_complex_comparison(self, node: ast.Compare) -> bool:
        """检查是否是复杂的比较操作"""
        # 检查比较操作数量
        if len(node.ops) > 1:
            return True
        
        # 检查是否包含函数调用
        for comparator in node.comparators:
            if isinstance(comparator, ast.Call):
                return True
        
        return False
    
    def _is_complex_loop(self, node: Union[ast.For, ast.While]) -> bool:
        """检查是否是复杂的循环"""
        # 检查循环体复杂度
        body_complexity = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                body_complexity += 1
        
        return body_complexity > 1
    
    def _is_complex_conditional(self, node: ast.If) -> bool:
        """检查是否是复杂的条件判断"""
        # 检查条件复杂度
        if isinstance(node.test, (ast.BoolOp, ast.Compare)):
            return True
        
        # 检查是否有elif或else
        if len(node.orelse) > 0:
            return True
        
        return False
    
    def _analyze_call_complexity(self, node: ast.Call) -> int:
        """分析函数调用的复杂度"""
        call_name = self._get_call_name(node)
        
        # 排除简单的打印和日志
        if call_name in ['print', 'logger.info', 'logger.debug', 'logger.warning', 'logger.error']:
            return 0
        
        # 检查参数复杂度
        arg_complexity = 0
        for arg in node.args:
            if isinstance(arg, (ast.Call, ast.ListComp, ast.DictComp, ast.GeneratorExp)):
                arg_complexity += 2
            elif isinstance(arg, (ast.List, ast.Dict, ast.Tuple)):
                arg_complexity += 1
        
        # 基础调用复杂度
        base_complexity = 1
        
        return base_complexity + arg_complexity
    
    def _is_complex_assignment(self, node: ast.Assign) -> bool:
        """检查是否是复杂的赋值操作"""
        # 检查是否是多重赋值
        if len(node.targets) > 1:
            return True
        
        # 检查赋值值是否复杂
        if isinstance(node.value, (ast.Call, ast.ListComp, ast.DictComp, ast.GeneratorExp)):
            return True
        
        # 检查是否是解包赋值
        for target in node.targets:
            if isinstance(target, (ast.Tuple, ast.List)):
                return True
        
        return False
    
    def _has_real_class_functionality(self, class_node: ast.ClassDef, content: str) -> bool:
        """
        检查类是否有真实的功能实现 - 基于代码逻辑分析
        
        Args:
            class_node: 类AST节点
            content: 文件内容
            
        Returns:
            是否有真实功能实现
        """
        try:
            # 检查类是否有方法
            if not class_node.body or len(class_node.body) == 0:
                return False
            
            # 检查类中是否有真实的方法实现
            has_real_methods = False
            for node in class_node.body:
                if isinstance(node, ast.FunctionDef):
                    if self._has_real_functionality_implementation(node, content):
                        has_real_methods = True
                        break
            
            return has_real_methods
            
        except Exception as e:
            self.logger.error(f"分析类功能实现失败: {e}")
            return False
    
    def _is_data_processing_assignment(self, assign_node: ast.Assign) -> bool:
        """
        检查赋值是否是数据处理操作
        
        Args:
            assign_node: 赋值AST节点
            
        Returns:
            是否是数据处理
        """
        try:
            # 检查右侧是否有函数调用
            if isinstance(assign_node.value, ast.Call):
                call_name = self._get_call_name(assign_node.value)
                if call_name and any(term in call_name.lower() for term in [
                    'process', 'transform', 'calculate', 'compute', 'analyze',
                    'parse', 'format', 'convert', 'extract', 'filter'
                ]):
                    return True
            
            # 检查右侧是否有复杂表达式
            if isinstance(assign_node.value, (ast.BinOp, ast.Compare, ast.ListComp, ast.DictComp)):
                return True
            
            return False
            
        except Exception as e:
            return False
    
    def _calculate_file_score(self, matches: int, total_patterns: int, threshold: float = 0.5) -> float:
        """
        计算文件分数
        
        Args:
            matches: 匹配数量
            total_patterns: 总模式数量
            threshold: 阈值
            
        Returns:
            文件分数
        """
        if total_patterns == 0:
            return 0.0
        return min(matches / total_patterns, 1.0)
    
    def _calculate_system_score(self, file_scores: List[float]) -> float:
        """
        计算系统级分数
        
        Args:
            file_scores: 文件分数列表
            
        Returns:
            系统级分数
        """
        if not file_scores:
            return 0.0
        return sum(file_scores) / len(file_scores)
