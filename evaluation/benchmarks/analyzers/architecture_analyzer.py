#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的架构层次分析器
检测架构层次问题、职责不清和依赖关系复杂
"""

import ast
import re
from typing import Dict, List, Any
from base_analyzer import BaseAnalyzer


class ArchitectureAnalyzer(BaseAnalyzer):
    """架构层次分析器 - 简化版"""
    
    def analyze(self) -> Dict[str, Any]:
        """分析架构层次问题"""
        try:
            analysis = {
                'layer_count': self._analyze_layer_count(),
                'responsibility_clarity': self._analyze_responsibility(),
                'dependency_complexity': self._analyze_dependencies(),
                'score': 0.0
            }
            
            # 计算综合分数
            analysis['score'] = self._calculate_architecture_score(analysis)
            return analysis
        except Exception as e:
            self.logger.error(f"架构分析失败: {e}")
            return {
                'layer_count': {'total_layers': 0, 'has_too_many_layers': False},
                'responsibility_clarity': {'total_violations': 0, 'has_severe_violations': False},
                'dependency_complexity': {'total_issues': 0, 'has_severe_dependency_issues': False},
                'score': 0.0
            }
    
    def _analyze_layer_count(self) -> Dict[str, Any]:
        """分析层次数量"""
        layer_count = 0
        
        for file_path in self.python_files[:3]:  # 限制文件数量
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检测表示层
                if re.search(r'class.*?View.*?:|class.*?Controller.*?:', content, re.IGNORECASE):
                    layer_count += 1
                
                # 检测业务层
                if re.search(r'class.*?Service.*?:|class.*?Business.*?:', content, re.IGNORECASE):
                    layer_count += 1
                
                # 检测数据层
                if re.search(r'class.*?Repository.*?:|class.*?DAO.*?:', content, re.IGNORECASE):
                    layer_count += 1
                
                # 检测服务层
                if re.search(r'class.*?Manager.*?:|class.*?Handler.*?:', content, re.IGNORECASE):
                    layer_count += 1
                    
            except Exception:
                continue
        
        return {
            'total_layers': layer_count,
            'has_too_many_layers': layer_count > 6
        }
    
    def _analyze_responsibility(self) -> Dict[str, Any]:
        """分析职责清晰度"""
        violations = 0
        
        for file_path in self.python_files[:3]:  # 限制文件数量
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检测上帝类（方法过多）
                class_matches = re.findall(r'class\s+(\w+).*?:', content)
                for class_name in class_matches:
                    # 计算类中的方法数量
                    class_pattern = rf'class\s+{re.escape(class_name)}.*?:(.*?)(?=class|\Z)'
                    class_content = re.search(class_pattern, content, re.DOTALL)
                    if class_content:
                        method_count = len(re.findall(r'def\s+\w+', class_content.group(1)))
                        if method_count > 15:
                            violations += 1
                    
            except Exception:
                continue
        
        return {
            'total_violations': violations,
            'has_severe_violations': violations > 2
        }
    
    def _analyze_dependencies(self) -> Dict[str, Any]:
        """分析依赖复杂度"""
        dependency_issues = 0
        
        for file_path in self.python_files[:3]:  # 限制文件数量
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检测过多的导入
                import_count = len(re.findall(r'import\s+|from\s+.*?\s+import', content))
                if import_count > 10:
                    dependency_issues += 1
                
                # 检测循环依赖
                if re.search(r'from\s+(\w+)\s+import.*?from\s+\1\s+import', content):
                    dependency_issues += 1
                    
            except Exception:
                continue
        
        return {
            'total_issues': dependency_issues,
            'has_severe_dependency_issues': dependency_issues > 2
        }
    
    def _calculate_architecture_score(self, analysis: Dict[str, Any]) -> float:
        """计算架构分数"""
        score = 0.0
        
        # 层次数量分数
        if analysis['layer_count']['has_too_many_layers']:
            score += 0.3
        
        # 职责清晰度分数
        if analysis['responsibility_clarity']['has_severe_violations']:
            score += 0.4
        
        # 依赖复杂度分数
        if analysis['dependency_complexity']['has_severe_dependency_issues']:
            score += 0.3
        
        return min(score, 1.0)