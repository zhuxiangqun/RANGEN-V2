#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的过度设计分析器
检测代码中的过度设计、过度工程化和不必要的复杂性
"""

import ast
import re
from typing import Dict, List, Any
from base_analyzer import BaseAnalyzer


class OverDesignAnalyzer(BaseAnalyzer):
    """过度设计分析器 - 简化版"""
    
    def analyze(self) -> Dict[str, Any]:
        """分析过度设计问题"""
        try:
            analysis = {
                'abstraction_layers': self._analyze_abstraction_layers(),
                'design_patterns': self._analyze_design_patterns(),
                'complexity_score': self._calculate_complexity_score(),
                'over_engineering': self._detect_over_engineering(),
                'score': 0.0
            }
            
            # 计算综合分数
            analysis['score'] = self._calculate_over_design_score(analysis)
            return analysis
        except Exception as e:
            self.logger.error(f"过度设计分析失败: {e}")
            return {
                'abstraction_layers': {'total_layers': 0, 'has_excessive_layers': False},
                'design_patterns': {'unique_patterns': 0, 'has_pattern_overuse': False},
                'complexity_score': {'complexity_score': 0.0, 'has_high_complexity': False},
                'over_engineering': {'over_engineering_score': 0.0, 'has_over_engineering': False},
                'score': 0.0
            }
    
    def _analyze_abstraction_layers(self) -> Dict[str, Any]:
        """分析抽象层数量"""
        layer_count = 0
        
        for file_path in self.python_files[:5]:  # 限制文件数量
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检测抽象层模式
                abstract_patterns = [
                    r'class\s+\w+.*?ABC.*?:',  # 抽象基类
                    r'@abstractmethod',         # 抽象方法
                    r'from\s+abc\s+import',      # ABC导入
                ]
                
                for pattern in abstract_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    layer_count += len(matches)
                    
            except Exception:
                continue
        
        return {
            'total_layers': layer_count,
            'has_excessive_layers': layer_count > 10
        }
    
    def _analyze_design_patterns(self) -> Dict[str, Any]:
        """分析设计模式使用"""
        pattern_count = {}
        
        design_patterns = {
            'factory': ['Factory', 'create_', 'build_'],
            'singleton': ['Singleton', 'get_instance'],
            'observer': ['Observer', 'Subject', 'notify'],
            'strategy': ['Strategy', 'execute'],
            'decorator': ['Decorator', '@'],
        }
        
        for file_path in self.python_files[:3]:  # 限制文件数量
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern_name, keywords in design_patterns.items():
                    count = 0
                    for keyword in keywords:
                        count += len(re.findall(keyword, content, re.IGNORECASE))
                    
                    if count > 0:
                        pattern_count[pattern_name] = pattern_count.get(pattern_name, 0) + count
                        
            except Exception:
                continue
        
        unique_patterns = len(pattern_count)
        return {
            'pattern_count': pattern_count,
            'unique_patterns': unique_patterns,
            'has_pattern_overuse': unique_patterns > 5
        }
    
    def _calculate_complexity_score(self) -> Dict[str, Any]:
        """计算复杂度分数"""
        complexity_indicators = 0
        
        for file_path in self.python_files[:3]:  # 限制文件数量
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 简化的复杂度检测
                if len(content.splitlines()) > 200:
                    complexity_indicators += 1
                
                if content.count('def ') > 20:
                    complexity_indicators += 1
                
                if content.count('class ') > 10:
                    complexity_indicators += 1
                    
            except Exception:
                continue
        
        complexity_score = min(complexity_indicators / 3.0, 1.0)
        return {
            'complexity_score': complexity_score,
            'has_high_complexity': complexity_score > 0.7
        }
    
    def _detect_over_engineering(self) -> Dict[str, Any]:
        """检测过度工程化"""
        over_engineering_indicators = 0
        
        for file_path in self.python_files[:3]:  # 限制文件数量
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检测不必要的抽象
                if re.search(r'class\s+\w+.*?:\s*pass', content):
                    over_engineering_indicators += 1
                
                # 检测过度参数化
                if re.search(r'def\s+\w+\s*\([^)]*,[^)]*,[^)]*,[^)]*,[^)]*,[^)]*\)', content):
                    over_engineering_indicators += 1
                    
            except Exception:
                continue
        
        over_engineering_score = min(over_engineering_indicators / 3.0, 1.0)
        return {
            'over_engineering_score': over_engineering_score,
            'has_over_engineering': over_engineering_score > 0.5
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