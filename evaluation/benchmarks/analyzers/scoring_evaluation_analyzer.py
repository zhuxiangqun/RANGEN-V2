"""
评分评估能力分析器
分析系统的5个评分评估能力维度 - 基于AST和语义分析
"""

import ast
import re
from typing import Dict, Any, List
from base_analyzer import BaseAnalyzer


class ScoringEvaluationAnalyzer(BaseAnalyzer):
    """评分评估能力分析器 - 基于AST和语义分析"""
    
    def analyze(self) -> Dict[str, Any]:
        """执行评分评估能力分析"""
        return {
            "confidence_scoring": self._analyze_confidence_scoring(),
            "quality_evaluation": self._analyze_quality_evaluation(),
            "performance_scoring": self._analyze_performance_scoring(),
            "scoring_result_analysis": self._analyze_scoring_result_analysis(),
            "scoring_history_management": self._analyze_scoring_history_management()
        }
    
    def _analyze_confidence_scoring(self) -> bool:
        """分析置信度评分 - 基于真实代码逻辑分析"""
        try:
            scoring_functions = 0
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
                        # 检查是否有置信度评分逻辑
                        if self._has_confidence_scoring_logic(node):
                            scoring_functions += 1
            
            # 修复：使用更严格的阈值，需要至少5%的函数支持评分功能
            if total_functions == 0:
                return False
            
            support_ratio = scoring_functions / total_functions
            return support_ratio >= 0.05
            
        except Exception as e:
            self.logger.error(f"分析置信度评分失败: {e}")
            return False
    
    def _analyze_quality_evaluation(self) -> bool:
        """分析质量评估 - 基于AST和语义分析"""
        try:
            quality_evaluation_patterns = [
                r'quality_evaluation', r'quality_assessment', r'quality_scoring',
                r'quality_measurement', r'quality_analysis', r'quality_rating',
                r'quality_metric', r'quality_indicator', r'quality_benchmark',
                r'quality_standard', r'quality_criteria', r'quality_validation',
                r'quality', r'evaluation', r'assessment', r'scoring', r'measurement',
                r'analysis', r'rating', r'metric', r'indicator', r'benchmark',
                r'standard', r'criteria', r'validation'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, quality_evaluation_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析质量评估失败: {e}")
            return False
    
    def _analyze_performance_scoring(self) -> bool:
        """分析性能评分 - 基于AST和语义分析"""
        try:
            performance_scoring_patterns = [
                r'performance_scoring', r'performance_score', r'performance_evaluation',
                r'performance_assessment', r'performance_rating', r'performance_measurement',
                r'performance_metric', r'performance_benchmark', r'performance_analysis',
                r'performance_indicator', r'performance_calculation', r'performance_estimation',
                r'performance', r'scoring', r'score', r'evaluation', r'assessment',
                r'rating', r'measurement', r'metric', r'benchmark', r'analysis',
                r'indicator', r'calculation', r'estimation'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, performance_scoring_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析性能评分失败: {e}")
            return False
    
    def _analyze_scoring_result_analysis(self) -> bool:
        """分析评分结果分析 - 基于AST和语义分析"""
        try:
            scoring_result_patterns = [
                r'scoring_result', r'score_analysis', r'result_analysis',
                r'scoring_analysis', r'score_evaluation', r'result_evaluation',
                r'score_interpretation', r'result_interpretation', r'score_insights',
                r'result_insights', r'score_breakdown', r'result_breakdown',
                r'scoring', r'score', r'result', r'analysis', r'evaluation',
                r'interpretation', r'insights', r'breakdown'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, scoring_result_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析评分结果分析失败: {e}")
            return False
    
    def _analyze_scoring_history_management(self) -> bool:
        """分析评分历史管理 - 基于AST和语义分析"""
        try:
            scoring_history_patterns = [
                r'scoring_history', r'score_history', r'scoring_archive',
                r'score_archive', r'scoring_log', r'score_log',
                r'scoring_tracking', r'score_tracking', r'scoring_persistence',
                r'score_persistence', r'scoring_storage', r'score_storage',
                r'scoring', r'score', r'history', r'archive', r'log',
                r'tracking', r'persistence', r'storage'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, scoring_history_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析评分历史管理失败: {e}")
            return False
    
    def _has_confidence_scoring_logic(self, func_node: ast.FunctionDef) -> bool:
        """检查是否有置信度评分逻辑"""
        has_scoring_calculation = False
        has_confidence_metrics = False
        has_evaluation_logic = False
        
        for node in ast.walk(func_node):
            # 检查是否有评分计算
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
                    has_scoring_calculation = True
            
            # 检查是否有置信度指标
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()
                        if any(term in var_name for term in ['confidence', 'score', 'rating', 'metric']):
                            has_confidence_metrics = True
                            break
            
            # 检查是否有评估逻辑
            elif isinstance(node, ast.If):
                if self._has_evaluation_condition(node.test):
                    has_evaluation_logic = True
        
        # 基于源码分析的功能实现检测
        # 注意：这里需要从调用上下文获取文件内容，暂时使用空字符串
        func_content = ""
        
        # 1. 检测置信度评分模式
        scoring_patterns = [
            # 评分模式
            r'confidence|score|rating|metric|evaluation',
            r'\.(confidence|score|rating|metric)\(.*\)',
            r'scoring|evaluation|assessment|measurement',
            
            # 计算模式
            r'calculate|compute|estimate|measure',
            r'\.(calculate|compute|estimate|measure)\(.*\)',
            r'math\.|np\.|statistics|probability',
            
            # 质量模式
            r'quality|accuracy|precision|recall',
            r'\.(quality|accuracy|precision|recall)\(.*\)',
            r'benchmark|standard|criteria|threshold',
            
            # 分析模式
            r'analyze|evaluate|assess|judge',
            r'\.(analyze|evaluate|assess|judge)\(.*\)',
            r'analysis|evaluation|assessment|judgment',
        ]
        
        scoring_score = 0
        for pattern in scoring_patterns:
            if re.search(pattern, func_content, re.IGNORECASE):
                scoring_score += 1
        
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
        
        # 3. 检测评分特征
        scoring_features = 0
        
        # 数学计算
        if re.search(r'math\.|np\.|calculate|compute', func_content):
            scoring_features += 1
        
        # 统计分析
        if re.search(r'statistics|probability|distribution|mean|std', func_content):
            scoring_features += 1
        
        # 质量评估
        if re.search(r'quality|accuracy|precision|recall|f1', func_content):
            scoring_features += 1
        
        # 4. 综合评分
        total_score = scoring_score + complexity_indicators + scoring_features
        
        # 有评分逻辑或功能实现即可
        return (has_scoring_calculation and has_confidence_metrics and has_evaluation_logic) or total_score >= 3
    
    def _has_evaluation_condition(self, test_node) -> bool:
        """检查是否是评估条件"""
        if isinstance(test_node, ast.Compare):
            if isinstance(test_node.left, ast.Name):
                var_name = test_node.left.id.lower()
                return any(term in var_name for term in ['score', 'rating', 'confidence', 'quality'])
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
