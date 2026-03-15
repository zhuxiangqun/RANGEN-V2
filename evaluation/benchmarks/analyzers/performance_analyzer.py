#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的性能问题分析器
检测代码中的性能问题、并发模型冲突和资源管理问题
"""

import ast
import re
from typing import Dict, List, Any
from base_analyzer import BaseAnalyzer


class PerformanceAnalyzer(BaseAnalyzer):
    """性能问题分析器 - 简化版"""
    
    def analyze(self) -> Dict[str, Any]:
        """分析性能问题"""
        try:
            analysis = {
                'concurrency_model': self._analyze_concurrency_model(),
                'resource_management': self._analyze_resource_management(),
                'performance_bottlenecks': self._detect_bottlenecks(),
                'score': 0.0
            }
            
            # 计算综合分数
            analysis['score'] = self._calculate_performance_score(analysis)
            return analysis
        except Exception as e:
            self.logger.error(f"性能分析失败: {e}")
            return {
                'concurrency_model': {'has_conflicts': False, 'has_mixed_concurrency': False},
                'resource_management': {'total_issues': 0, 'has_severe_issues': False},
                'performance_bottlenecks': {'total_bottlenecks': 0, 'has_severe_bottlenecks': False},
                'score': 0.0
            }
    
    def _analyze_concurrency_model(self) -> Dict[str, Any]:
        """分析并发模型"""
        threading_usage = 0
        asyncio_usage = 0
        
        for file_path in self.python_files[:3]:  # 限制文件数量
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检测线程使用
                if re.search(r'import\s+threading|ThreadPoolExecutor', content):
                    threading_usage += 1
                
                # 检测异步使用
                if re.search(r'import\s+asyncio|async\s+def|await\s+', content):
                    asyncio_usage += 1
                    
            except Exception:
                continue
        
        has_mixed_concurrency = threading_usage > 0 and asyncio_usage > 0
        has_conflicts = has_mixed_concurrency
        
        return {
            'has_conflicts': has_conflicts,
            'has_mixed_concurrency': has_mixed_concurrency
        }
    
    def _analyze_resource_management(self) -> Dict[str, Any]:
        """分析资源管理"""
        resource_issues = 0
        
        for file_path in self.python_files[:3]:  # 限制文件数量
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检测文件句柄问题
                if re.search(r'open\([^)]+\)(?!\s*as\s+)', content):
                    resource_issues += 1
                
                # 检测数据库连接问题
                if re.search(r'connect\([^)]+\)(?!\s*as\s+)', content):
                    resource_issues += 1
                    
            except Exception:
                continue
        
        return {
            'total_issues': resource_issues,
            'has_severe_issues': resource_issues > 2
        }
    
    def _detect_bottlenecks(self) -> Dict[str, Any]:
        """检测性能瓶颈"""
        bottlenecks = 0
        
        for file_path in self.python_files[:3]:  # 限制文件数量
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检测嵌套循环
                if re.search(r'for\s+\w+\s+in\s+[^:]+:\s*\n\s*for\s+\w+\s+in\s+[^:]+:', content):
                    bottlenecks += 1
                
                # 检测昂贵操作
                if re.search(r'\.sort\(\)|\.reverse\(\)', content):
                    bottlenecks += 1
                
                # 检测同步IO
                if re.search(r'open\([^)]+\)|requests\.(get|post)', content):
                    bottlenecks += 1
                    
            except Exception:
                continue
        
        return {
            'total_bottlenecks': bottlenecks,
            'has_severe_bottlenecks': bottlenecks > 2
        }
    
    def _calculate_performance_score(self, analysis: Dict[str, Any]) -> float:
        """计算性能分数"""
        score = 0.0
        
        # 并发模型分数
        if analysis['concurrency_model']['has_conflicts']:
            score += 0.4
        
        # 资源管理分数
        if analysis['resource_management']['has_severe_issues']:
            score += 0.3
        
        # 性能瓶颈分数
        if analysis['performance_bottlenecks']['has_severe_bottlenecks']:
            score += 0.3
        
        return min(score, 1.0)