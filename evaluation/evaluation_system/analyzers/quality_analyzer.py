"""
质量分析器
分析系统质量指标，包括代码质量、错误率、稳定性等
"""

import re
from typing import Dict, Any, List
from .base_analyzer import BaseAnalyzer

class QualityAnalyzer(BaseAnalyzer):
    """质量分析器"""
    
    def __init__(self):
        super().__init__("QualityAnalyzer")
    
    def analyze(self, log_content: str) -> Dict[str, Any]:
        """分析质量指标"""
        return {
            "error_analysis": self._analyze_errors(log_content),
            "stability": self._analyze_stability(log_content),
            "code_quality": self._analyze_code_quality(log_content),
            "reliability": self._analyze_reliability(log_content),
            "maintainability": self._analyze_maintainability(log_content)
        }
    
    def _analyze_errors(self, log_content: str) -> Dict[str, Any]:
        """分析错误情况"""
        # 提取错误信息
        error_patterns = [
            r"ERROR - (.+)",
            r"错误: (.+)",
            r"失败: (.+)",
            r"异常: (.+)",
            r"Exception: (.+)"
        ]
        
        warning_patterns = [
            r"WARNING - (.+)",
            r"警告: (.+)",
            r"WARN - (.+)"
        ]
        
        errors = self._extract_pattern_matches(log_content, error_patterns)
        warnings = self._extract_pattern_matches(log_content, warning_patterns)
        
        # 分析错误类型
        error_types = self._categorize_errors(errors)
        
        # 计算错误率
        total_log_lines = len(log_content.split('\n'))
        error_rate = len(errors) / total_log_lines if total_log_lines > 0 else 0.0
        warning_rate = len(warnings) / total_log_lines if total_log_lines > 0 else 0.0
        
        return {
            "error_count": len(errors),
            "warning_count": len(warnings),
            "error_rate": error_rate,
            "warning_rate": warning_rate,
            "error_types": error_types,
            "errors": errors[:10],  # 只保留前10个错误
            "warnings": warnings[:10]  # 只保留前10个警告
        }
    
    def _categorize_errors(self, errors: List[str]) -> Dict[str, int]:
        """对错误进行分类"""
        categories = {
            "connection": 0,
            "timeout": 0,
            "validation": 0,
            "permission": 0,
            "resource": 0,
            "data": 0,
            "system": 0,
            "other": 0
        }
        
        for error in errors:
            error_lower = error.lower()
            if any(keyword in error_lower for keyword in ['connection', 'connect', 'network']):
                categories["connection"] += 1
            elif any(keyword in error_lower for keyword in ['timeout', 'time out']):
                categories["timeout"] += 1
            elif any(keyword in error_lower for keyword in ['validation', 'valid', 'invalid']):
                categories["validation"] += 1
            elif any(keyword in error_lower for keyword in ['permission', 'access', 'denied']):
                categories["permission"] += 1
            elif any(keyword in error_lower for keyword in ['memory', 'resource', 'disk']):
                categories["resource"] += 1
            elif any(keyword in error_lower for keyword in ['data', 'format', 'parse']):
                categories["data"] += 1
            elif any(keyword in error_lower for keyword in ['system', 'os', 'platform']):
                categories["system"] += 1
            else:
                categories["other"] += 1
        
        return categories
    
    def _analyze_stability(self, log_content: str) -> Dict[str, Any]:
        """分析系统稳定性"""
        # 提取系统状态信息
        status_patterns = [
            r"系统状态: (.+)",
            r"状态: (.+)",
            r"status: (.+)"
        ]
        
        statuses = self._extract_pattern_matches(log_content, status_patterns)
        
        # 分析状态分布
        status_distribution = {}
        for status in statuses:
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        # 计算稳定性分数
        stability_score = 0.0
        if statuses:
            stable_count = sum(1 for status in statuses if 'stable' in status.lower() or 'running' in status.lower())
            stability_score = stable_count / len(statuses)
        
        # 分析重启次数
        restart_patterns = [
            r"系统重启",
            r"restart",
            r"重新启动"
        ]
        
        restarts = len(self._extract_pattern_matches(log_content, restart_patterns))
        
        return {
            "status_distribution": status_distribution,
            "stability_score": stability_score,
            "restart_count": restarts,
            "total_status_changes": len(statuses)
        }
    
    def _analyze_code_quality(self, log_content: str) -> Dict[str, Any]:
        """分析代码质量"""
        # 提取代码质量相关指标
        quality_patterns = [
            r"质量分数: (\d+\.?\d*)",
            r"quality_score: (\d+\.?\d*)",
            r"代码质量: (\d+\.?\d*)"
        ]
        
        quality_scores = self._extract_numeric_values(log_content, quality_patterns)
        quality_stats = self._calculate_statistics(quality_scores)
        
        # 分析代码复杂度相关日志
        complexity_indicators = [
            r"复杂度",
            r"complexity",
            r"嵌套",
            r"nested"
        ]
        
        complexity_count = len(self._extract_pattern_matches(log_content, complexity_indicators))
        
        # 分析优化相关日志
        optimization_indicators = [
            r"优化",
            r"optimization",
            r"优化完成",
            r"optimized"
        ]
        
        optimization_count = len(self._extract_pattern_matches(log_content, optimization_indicators))
        
        return {
            "quality_stats": quality_stats,
            "avg_quality_score": quality_stats["average"],
            "complexity_indicators": complexity_count,
            "optimization_indicators": optimization_count,
            "quality_trend": self._analyze_quality_trend(quality_scores)
        }
    
    def _analyze_quality_trend(self, quality_scores: List[float]) -> str:
        """分析质量趋势"""
        if len(quality_scores) < 2:
            return "insufficient_data"
        
        # 计算趋势
        first_half = quality_scores[:len(quality_scores)//2]
        second_half = quality_scores[len(quality_scores)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg * 1.05:
            return "improving"
        elif second_avg < first_avg * 0.95:
            return "declining"
        else:
            return "stable"
    
    def _analyze_reliability(self, log_content: str) -> Dict[str, Any]:
        """分析可靠性"""
        # 提取成功/失败信息
        success_patterns = [
            r"成功",
            r"success",
            r"完成",
            r"completed"
        ]
        
        failure_patterns = [
            r"失败",
            r"failure",
            r"错误",
            r"error"
        ]
        
        success_count = len(self._extract_pattern_matches(log_content, success_patterns))
        failure_count = len(self._extract_pattern_matches(log_content, failure_patterns))
        
        # 计算可靠性分数
        total_operations = success_count + failure_count
        reliability_score = success_count / total_operations if total_operations > 0 else 0.0
        
        # 分析恢复能力
        recovery_patterns = [
            r"恢复",
            r"recovery",
            r"重试",
            r"retry"
        ]
        
        recovery_count = len(self._extract_pattern_matches(log_content, recovery_patterns))
        
        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "reliability_score": reliability_score,
            "recovery_count": recovery_count,
            "total_operations": total_operations
        }
    
    def _analyze_maintainability(self, log_content: str) -> Dict[str, Any]:
        """分析可维护性（🚀 增强：识别更多模块化相关的关键字）"""
        # 🚀 增强：提取维护相关指标（包括更多关键字）
        maintenance_patterns = [
            r"维护",
            r"maintenance",
            r"更新",
            r"update",
            r"升级",
            r"upgrade",
            r"系统可维护性",
            r"维护指标",
            r"maintainability"
        ]
        
        maintenance_count = len(self._extract_pattern_matches(log_content, maintenance_patterns))
        
        # 🚀 增强：分析模块化程度（包括更多关键字）
        module_patterns = [
            r"模块",
            r"module",
            r"组件",
            r"component",
            r"模块注册",
            r"模块化设计",
            r"模块化指标",
            r"modularity",
            r"模块化架构"
        ]
        
        module_count = len(self._extract_pattern_matches(log_content, module_patterns))
        
        # 分析文档相关
        # 🚀 修复：改进文档指标匹配模式，确保能匹配到各种格式
        documentation_patterns = [
            r"文档:",  # 🚀 修复：匹配"文档:"格式
            r"文档\s",  # 匹配"文档 "格式
            r"documentation",
            r"注释",
            r"comment",
            r"文档指标",  # 匹配"文档指标"格式
            r"学习数据已保存",  # 🚀 修复：学习数据保存也算文档指标
            r"研究报告"  # 🚀 修复：研究报告也算文档指标
        ]
        
        doc_count = len(self._extract_pattern_matches(log_content, documentation_patterns))
        
        # 🚀 优化：计算可维护性分数（调整阈值，更合理）
        total_indicators = maintenance_count + module_count + doc_count
        maintainability_score = min(1.0, total_indicators / 50.0)  # 50个指标 = 1.0分（更合理）
        
        return {
            "maintenance_indicators": maintenance_count,
            "modularity_indicators": module_count,
            "documentation_indicators": doc_count,
            "maintainability_score": maintainability_score
        }
