#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渐进式过度设计分析器
根据系统负载动态调整检测深度
"""

import ast
import re
import time
from typing import Dict, List, Any
from base_analyzer import BaseAnalyzer


class ProgressiveOverDesignAnalyzer(BaseAnalyzer):
    """渐进式过度设计分析器"""
    
    def __init__(self, python_files: List[str]):
        super().__init__(python_files)
        self.max_analysis_time = 10  # 最大分析时间（秒）
        self.max_files = 5  # 最大文件数
        self.detailed_mode = True  # 详细模式开关
    
    def analyze(self) -> Dict[str, Any]:
        """渐进式分析过度设计问题"""
        start_time = time.time()
        
        try:
            # 基础分析（快速）
            basic_analysis = self._basic_analysis()
            
            # 如果时间允许，进行详细分析
            if time.time() - start_time < self.max_analysis_time and self.detailed_mode:
                detailed_analysis = self._detailed_analysis()
                # 合并结果
                analysis = {**basic_analysis, **detailed_analysis}
            else:
                analysis = basic_analysis
            
            # 计算综合分数
            analysis['score'] = self._calculate_over_design_score(analysis)
            analysis['analysis_mode'] = 'detailed' if self.detailed_mode else 'basic'
            analysis['analysis_time'] = time.time() - start_time
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"渐进式过度设计分析失败: {e}")
            return self._fallback_analysis()
    
    def _basic_analysis(self) -> Dict[str, Any]:
        """基础分析（快速）"""
        layer_count = 0
        pattern_count = 0
        complexity_indicators = 0
        
        # 限制文件数量以提高性能
        files_to_analyze = self.python_files[:self.max_files]
        
        for file_path in files_to_analyze:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 快速检测抽象层
                abstract_patterns = [
                    r'class\s+\w+.*?ABC.*?:',
                    r'@abstractmethod',
                    r'from\s+abc\s+import',
                ]
                
                for pattern in abstract_patterns:
                    layer_count += len(re.findall(pattern, content, re.IGNORECASE))
                
                # 快速检测设计模式
                design_patterns = ['Factory', 'Singleton', 'Observer', 'Strategy', 'Decorator']
                for pattern in design_patterns:
                    if pattern in content:
                        pattern_count += 1
                
                # 快速检测复杂度
                if len(content.splitlines()) > 200:
                    complexity_indicators += 1
                if content.count('def ') > 20:
                    complexity_indicators += 1
                    
            except Exception:
                continue
        
        return {
            'abstraction_layers': {
                'total_layers': layer_count,
                'has_excessive_layers': layer_count > 10
            },
            'design_patterns': {
                'unique_patterns': pattern_count,
                'has_pattern_overuse': pattern_count > 5
            },
            'complexity_score': {
                'complexity_score': min(complexity_indicators / 3.0, 1.0),
                'has_high_complexity': complexity_indicators > 2
            },
            'over_engineering': {
                'over_engineering_score': 0.0,  # 基础模式不检测
                'has_over_engineering': False
            }
        }
    
    def _detailed_analysis(self) -> Dict[str, Any]:
        """详细分析（深度）"""
        over_engineering_indicators = 0
        unnecessary_abstractions = 0
        interface_bloat = 0
        
        files_to_analyze = self.python_files[:self.max_files]
        
        for file_path in files_to_analyze:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # 详细检测过度工程化
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # 检测不必要的抽象
                        if self._is_unnecessary_abstraction(node):
                            unnecessary_abstractions += 1
                        
                        # 检测接口膨胀
                        if self._is_interface_bloated(node):
                            interface_bloat += 1
                    
                    elif isinstance(node, ast.FunctionDef):
                        # 检测过度参数化
                        if len(node.args.args) > 8:
                            over_engineering_indicators += 1
                
                # 检测过度配置
                if re.search(r'config\s*=\s*\{[^}]{200,}\}', content):
                    over_engineering_indicators += 1
                    
            except Exception:
                continue
        
        return {
            'unnecessary_abstractions': {
                'unnecessary_count': unnecessary_abstractions,
                'has_unnecessary_abstractions': unnecessary_abstractions > 3
            },
            'interface_bloat': {
                'bloat_score': min(interface_bloat / 5.0, 1.0),
                'has_interface_bloat': interface_bloat > 2
            },
            'over_engineering': {
                'over_engineering_score': min(over_engineering_indicators / 5.0, 1.0),
                'has_over_engineering': over_engineering_indicators > 3
            }
        }
    
    def _is_unnecessary_abstraction(self, class_node: ast.ClassDef) -> bool:
        """检测不必要的抽象"""
        # 检测空抽象类
        if len(class_node.body) == 0:
            return True
        
        # 检测单方法接口
        methods = [node for node in class_node.body if isinstance(node, ast.FunctionDef)]
        if len(methods) == 1:
            return True
        
        return False
    
    def _is_interface_bloated(self, class_node: ast.ClassDef) -> bool:
        """检测接口膨胀"""
        methods = [node for node in class_node.body if isinstance(node, ast.FunctionDef)]
        return len(methods) > 15
    
    def _fallback_analysis(self) -> Dict[str, Any]:
        """备用分析（最简化）"""
        return {
            'abstraction_layers': {'total_layers': 0, 'has_excessive_layers': False},
            'design_patterns': {'unique_patterns': 0, 'has_pattern_overuse': False},
            'complexity_score': {'complexity_score': 0.0, 'has_high_complexity': False},
            'over_engineering': {'over_engineering_score': 0.0, 'has_over_engineering': False},
            'score': 0.0,
            'analysis_mode': 'fallback',
            'analysis_time': 0.0
        }
    
    def _calculate_over_design_score(self, analysis: Dict[str, Any]) -> float:
        """计算过度设计分数"""
        score = 0.0
        
        # 抽象层分数
        if analysis['abstraction_layers']['has_excessive_layers']:
            score += 0.3
        
        # 设计模式分数
        if analysis['design_patterns']['has_pattern_overuse']:
            score += 0.2
        
        # 复杂度分数
        if analysis['complexity_score']['has_high_complexity']:
            score += 0.3
        
        # 过度工程化分数
        if analysis['over_engineering']['has_over_engineering']:
            score += 0.2
        
        return min(score, 1.0)
